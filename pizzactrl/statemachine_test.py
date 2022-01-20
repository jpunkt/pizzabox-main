import imp
import sys
import logging

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

from pizzactrl.statemachine import Statemachine
# from pizzactrl.sb_dummy import STORYBOARD
from pizzactrl.sb_showcase import STORYBOARD
from pizzactrl.hal_serial import PizzaHAL, rewind, turn_off

hal = PizzaHAL()
# sm = Statemachine(hal, STORYBOARD, move=True, loop=False, test=True)

sm = Statemachine(hal, STORYBOARD, move=True, loop=False, test=False)