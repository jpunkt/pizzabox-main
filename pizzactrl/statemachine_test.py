import imp
import sys
import logging

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

from pizzactrl.statemachine import Statemachine
# from pizzactrl.sb_dummy import STORYBOARD
from pizzactrl.sb_dummy import STORYBOARD
from pizzactrl.hal_serial import PizzaHAL, rewind, turn_off

hal = PizzaHAL()

sm = Statemachine(hal, STORYBOARD, loop=False, test=False)