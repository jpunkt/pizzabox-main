import sys
import logging

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

from pizzactrl.statemachine import Statemachine

sm = Statemachine(move=True, loop=False, test=True)

