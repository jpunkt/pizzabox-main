import sys
import logging

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

from . import hal_serial

hal = hal_serial.PizzaHAL()

def init_all():
    hal.init_sounds()
    hal.init_connection()
    hal.init_camera()


def demo():
    """
    Turn on all lights, flash all LEDs;
    Turn off and reset when button is pressed
    """
    hal_serial.set_light(hal, hal_serial.Lights.FRONTLIGHT, 0, 0, 0, 1, 0)
    hal_serial.set_light(hal, hal_serial.Lights.BACKLIGHT, 0, 0, 0, 1, 0)
    hal_serial.do_it(hal)
    hal_serial.wait_for_input(hal, lambda: None, lambda: None, lambda: None, lambda: None, timeout=0)
    hal_serial.turn_off(hal)
    hal_serial.rewind(hal)
    hal_serial.reset(hal)