import sys

import click
import logging

from pizzactrl.statemachine import Statemachine, State
from pizzactrl.sb_showcase import STORYBOARD
from pizzactrl.hal_serial import PizzaHAL

logger = logging.getLogger('pizzactrl.main')


@click.command()
@click.option('--move', is_flag=True)
@click.option('--test', is_flag=True, default=False)
@click.option('--debug', is_flag=True, default=False)
@click.option('--loop', is_flag=True, default=False)
def main(move: bool=False, test: bool=False, debug: bool=False, loop: bool=False):
    if debug or test:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    else:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    hal = PizzaHAL()
    sm = Statemachine(hal, STORYBOARD, move=move, loop=loop, test=test)
    
    sm.test = test

    exitcode = 0
    try:
        sm.run()
    finally:
        if sm.state is State.ERROR:
            exitcode = 2
        del sm
        sys.exit(exitcode)


if __name__ == '__main__':
    main()
