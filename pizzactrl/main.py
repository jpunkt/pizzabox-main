import sys

import click
import logging

from .statemachine import Statemachine, State
from . import sb_de, sb_en

logger = logging.getLogger('pizzactrl.main')


@click.command()
@click.option('--move', is_flag=True)
@click.option('--test', is_flag=True, default=False)
@click.option('--debug', is_flag=True, default=False)
def main(move: bool=False, test: bool=False, debug: bool=False):
    if debug or test:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    else:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    sm = Statemachine(story_de=sb_de.STORYBOARD,
                      story_en=sb_en.STORYBOARD,
                      move=move)
    sm.test = test

    exitcode = 0
    try:
        sm.run()
    except Exception:
        logger.exception('An Error occurred while running the statemachine')
        exitcode = 1
    finally:
        if sm.state is State.ERROR:
            exitcode = 2
        del sm
        sys.exit(exitcode)


@click.command()
@click.option('--time', help='Safety deactivation time', type=float,
              default=13.2)
def rewind(time: float):
    from . import hal
    pizza = hal.PizzaHAL()
    hal.rewind(pizza.motor_ud, pizza.ud_sensor, max_time=time)
    hal.turn_off(pizza)
    del pizza


if __name__ == '__main__':
    main()
