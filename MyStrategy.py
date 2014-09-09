from math import pi
import logging

from model.ActionType import ActionType


def log_it(msg, level='info'):
    getattr(logging, level)(msg)


class MyStrategy:

    def __init__(self):
        logging.basicConfig(
            format='%(asctime)s %(levelname)s:%(message)s',
            level=logging.INFO)

    def move(self, me, world, game, move):
        log_it('<<<<<<<<<<<<<<<<<<<<<<<<< TURN %d' % world.tick)
        move.speed_up = -1.0
        move.turn = pi
        move.action = ActionType.STRIKE
        log_it('>>>>>>>>>>>>>>>>>>>>>>>>>')