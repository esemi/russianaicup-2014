#! /usr/bin/env python
# -*- coding: utf-8 -*-


import logging

from model.HockeyistState import HockeyistState
from model.HockeyistType import HockeyistType
from model.ActionType import ActionType


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

        puck = world.puck
        my_player = world.get_my_player()

        log_it("puck player id %d (me %d)" % (puck.owner_player_id, my_player.id))
        if puck.owner_player_id != my_player.id:
            # если шайба не у нас - все игроки несутся её захватывать
            self._action_puck_hunt(me, puck, game, move)
        else:
            # иначе (шайба у наших) игроки пропываются к одному из головых кругов
            if puck.owner_hockeyist_id == me.id:
                # ходит нападающий
                self._action_forward(me, move)
            else:
                # ходит защитник
                self._action_defender(me, move, world, game)
                pass

    def _action_forward(self, me, move):
        """
        _action_forward(Hockeyist, Move)

        """
        log_it("forward action started")
        pass

    def _action_defender(self, me, move, world, game):
        """
        _action_defender(Hockeyist, Move, World)

        """
        # дефендер движется к ближайшему сопернику и пиздит его
        log_it("defender action started")
        enemys = self.get_enemys(me, world)

        # если один из ближайших противников в зоне досягаемости и не опрокинут - пиздим его клюшкой
        for enemy in enemys:
            if self.unit_in_action_range(me, enemy, game) and enemy.state != HockeyistState.KNOCKED_DOWN:
                log_it("strike enemy %d" % enemy.id)
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

        # todo пиздить противников по пути к шайбе
        # todo не обгонять шайбу
        if self.unit_in_action_range(me, puck, game):
            # хватаем шайбу
            log_it("take puck")
            move.action = ActionType.TAKE_PUCK
        else:
            # если шайба ещё далеко - двигаемся к ней
            # если шайба в зоне досягаемости, но угол не тот - вертимся
            log_it("run and turn to puck")
            move.speed_up = 1.0
            move.turn = me.get_angle_to_unit(puck)

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