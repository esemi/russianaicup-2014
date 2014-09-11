#! /usr/bin/env python
# -*- coding: utf-8 -*-

from math import sqrt
import logging
from random import choice

from model.HockeyistState import HockeyistState
from model.HockeyistType import HockeyistType
from model.ActionType import ActionType


GOAL_SECTOR_RINK_PADDING = 8
DISTANCE_LIMIT_TO_GOAL_SECTOR = 80.
NET_COORD_FACTOR_X = 4
NET_COORD_FACTOR_Y = 15
STRIKE_ANGLE_LIMIT = 0.01
STRIKE_SPEED_LIMIT = 1.
# todo поиграть с константами


def log_it(msg, level='info'):
    getattr(logging, level)(msg)


class MyStrategy:

    def __init__(self):
        logging.basicConfig(
            format='%(asctime)s %(levelname)s:%(message)s',
            level=logging.DEBUG)

    def move(self, me, world, game, move):
        log_it('<<<<<<<<<<<<<<<<<<<<<<<<<')
        self._action_base(me, world, game, move)
        log_it('>>>>>>>>>>>>>>>>>>>>>>>>>')

    def _action_base(self, me, world, game, move):
        """
        _action_base(Hockeyist, World, Game, Move)

        """
        log_it('new move turn %d unit %d (%s)' % (world.tick, me.teammate_index, str((me.x, me.y))))

        # todo выводить хокеиста из замаха если он уже без шайбы

        if me.state == HockeyistState.KNOCKED_DOWN:
            log_it('knocked down state')

        puck = world.puck
        my_player = world.get_my_player()

        log_it("puck player id %d (me %d)" % (puck.owner_player_id, my_player.id))
        if puck.owner_player_id != my_player.id:
            # если шайба не у нас - все игроки несутся её захватывать
            self._action_puck_hunt(me, puck, game, move)
        else:
            # иначе (шайба у наших) игроки пропываются к одному из головых кругов
            if puck.owner_hockeyist_id == me.id:
                self._action_forward(me, move, world, game)
            else:
                self._action_defender(me, move, world, game)

    def _action_forward(self, me, move, world, game):
        """
        _action_forward(Hockeyist, Move)

        """
        log_it("forward action started")
        op_player = world.get_opponent_player()

        sector_coord = self.select_goal_sector(me, op_player, game)
        log_it("sector coord %s" % str(sector_coord))
        strike_coord = self.select_strike_coord(me, world)
        log_it("strike coord %s" % str(strike_coord))

        # todo начинаем поворачиваться раньше, чем достигли голевого сектора
        if me.get_distance_to(*sector_coord) <= DISTANCE_LIMIT_TO_GOAL_SECTOR:
            # если атакер уже может бить - процессим удар по воротам
            log_it('process strike to enemy net')

            # оттормаживаемся в голевом секторе
            cur_speed = self.speed_abs(me)
            if cur_speed > STRIKE_SPEED_LIMIT:
                log_it('speed %.2f - rear turn' % cur_speed)
                move.speed_up = -1.0

            # todo замахиваемся пока враги далеко (но не более лимита и не менее офсета на замах)

            # поворачиваемся к воротам или лупим по ним
            strike_angle = me.get_angle_to(*strike_coord)
            if abs(strike_angle) <= STRIKE_ANGLE_LIMIT:
                # todo замах перед ударом
                log_it("strike puck %.2f" % strike_angle)
                move.action = ActionType.STRIKE
            else:
                log_it("only turn %.2f" % strike_angle)
                move.turn = strike_angle
        else:
            # иначе ведём атакера на рубеж атаки
            log_it("run and turn to goal sector")
            move.speed_up = 1.0
            move.turn = me.get_angle_to(*sector_coord)

    def _action_defender(self, me, move, world, game):
        """
        _action_defender(Hockeyist, Move, World, Game)

        """
        # дефендер движется к ближайшему сопернику и пиздит его
        log_it("defender action started")
        enemys = self.get_enemys(me, world)

        # если один из ближайших противников в зоне досягаемости и не опрокинут - пиздим его клюшкой
        if me.remaining_cooldown_ticks == 0:
            for enemy in enemys:
                if self.unit_in_action_range(me, enemy, game) and enemy.state != HockeyistState.KNOCKED_DOWN:
                    log_it("strike enemy %d" % enemy.id)
                    # todo пиздить только если шайба не у нас и в секторе досягаемости
                    move.action = ActionType.STRIKE
                    break

        # двигаем к нему
        log_it("run and turn to enemy for battle")
        move.speed_up = 1.0
        move.turn = me.get_angle_to_unit(enemys[0])

    def _action_puck_hunt(self, me, puck, game, move):
        """
        _action_base(Hockeyist, Puck, Game, Move)

        """

        log_it("puck hanting started")
        log_it("distance to puck %0.2f (min %0.2f)" % (me.get_distance_to_unit(puck), game.stick_length))
        log_it("angle to puck %0.2f (min %0.2f)" % (me.get_angle_to_unit(puck), (game.stick_sector / 2)))

        # todo идти на защиту ворот (или перед ведущим шайбу хокеистом) если шайба на нашей половине и у врагов
        if self.unit_in_action_range(me, puck, game) and me.remaining_cooldown_ticks == 0:
            # хватаем шайбу
            log_it("take puck")
            move.action = ActionType.TAKE_PUCK
        else:
            # если шайба ещё далеко - двигаемся к ней
            # если шайба в зоне досягаемости, но угол не тот - вертимся
            log_it("run and turn to puck")
            move.speed_up = 1.0
            move.turn = me.get_angle_to_unit(puck)
            # todo пиздить противников по пути к шайбе

    @staticmethod
    def get_enemys(me, world):
        enemys = sorted([(i, me.get_distance_to_unit(i)) for i in world.hockeyists
                         if not i.teammate and i.type != HockeyistType.GOALIE],
                        key=lambda x: x[1])
        return [i[0] for i in enemys]

    @staticmethod
    def unit_in_action_range(unit_from, unit_to, game):
        return unit_from.get_distance_to_unit(unit_to) <= game.stick_length and \
               unit_from.get_angle_to_unit(unit_to) <= (game.stick_sector / 2)

    @staticmethod
    def select_goal_sector(me, op_player, game):
        log_it("select goal sector")
        # todo RELEASE MATH
        # todo уклоняться от встреч с врагами

        sector_top_top_y = game.rink_top + GOAL_SECTOR_RINK_PADDING
        sector_top_bottom_y = op_player.net_top
        sector_bottom_top_y = op_player.net_bottom
        sector_bottom_bottom_y = game.rink_bottom - GOAL_SECTOR_RINK_PADDING

        rink_width = game.rink_right - game.rink_left

        if op_player.net_front > op_player.net_back:
            log_it("left side enemy")
            # top sector
            sector_top_left_x = rink_width / 4
            sector_top_right_x = rink_width / 2

            # bottom sector
            sector_bottom_left_x = rink_width / 4
            sector_bottom_right_x = rink_width / 2
        else:
            log_it("right side enemy")
            # top sector
            sector_top_left_x = rink_width / 2
            sector_top_right_x = rink_width - (rink_width / 4)

            # bottom sector
            sector_bottom_left_x = rink_width / 2
            sector_bottom_right_x = rink_width - (rink_width / 4)

        # считаем координаты центров голового секторов
        top_sector_center_coord = ((sector_top_right_x + sector_top_left_x) / 2,
                                   (sector_top_bottom_y + sector_top_top_y) / 2)
        bottom_sector_center_coord = ((sector_bottom_right_x + sector_bottom_left_x) / 2,
                                      (sector_bottom_top_y + sector_bottom_bottom_y) / 2)

        log_it('top goal sector (%s, %s, %s, %s, %s)' % (sector_top_top_y, sector_top_bottom_y, sector_top_left_x,
                                                         sector_top_right_x, str(top_sector_center_coord)))
        log_it('bottom goal sector (%s, %s, %s, %s, %s)' % (sector_bottom_top_y, sector_bottom_bottom_y,
                                                            sector_bottom_left_x, sector_bottom_right_x,
                                                            str(bottom_sector_center_coord)))

        top_sector_distance = me.get_distance_to(*top_sector_center_coord)
        log_it("distance ot top sector center %.2f" % top_sector_distance)

        bottom_sector_distance = me.get_distance_to(*bottom_sector_center_coord)
        log_it("distance ot bottom sector center %.2f" % bottom_sector_distance)

        if top_sector_distance < bottom_sector_distance:
            return top_sector_center_coord
        elif top_sector_distance == bottom_sector_distance:
            return choice([bottom_sector_center_coord, top_sector_center_coord])
        else:
            return bottom_sector_center_coord


    @staticmethod
    def select_strike_coord(me, world):
        log_it("select strike coord")

        op_player = world.get_opponent_player()

        top_coord_y = op_player.net_top + NET_COORD_FACTOR_Y
        bottom_coord_y = op_player.net_bottom - NET_COORD_FACTOR_Y
        if op_player.net_front > op_player.net_back:
            bottom_coord_x = top_coord_x = op_player.net_front - NET_COORD_FACTOR_X
        else:
            bottom_coord_x = top_coord_x = op_player.net_front + NET_COORD_FACTOR_X
        top_coord = (top_coord_x, top_coord_y)
        bottom_coord = (bottom_coord_x, bottom_coord_y)

        log_it('top strike coord (%s, %s)' % (str((op_player.net_top, op_player.net_bottom, op_player.net_front)),
                                              str(top_coord)))
        log_it('bottom strike coord (%s, %s)' % (str((op_player.net_top, op_player.net_bottom, op_player.net_front)),
                                                 str(bottom_coord)))

        top_distance = me.get_distance_to(*top_coord)
        log_it("distance ot top strike coord %.2f" % top_distance)
        bottom_distance = me.get_distance_to(*bottom_coord)
        log_it("distance ot bottom strike coord %.2f" % bottom_distance)

        if top_distance < bottom_distance:
            return bottom_coord
        else:
            return top_coord

    @staticmethod
    def speed_abs(unit):
        return sqrt(unit.speed_x ** 2 + unit.speed_y ** 2)