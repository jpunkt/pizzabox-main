import sys
import logging

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

from . import hal_serial

hal = hal_serial.PizzaHAL()

