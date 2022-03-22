from email.policy import default
import sys

import click
import logging

from pizzactrl.statemachine import Statemachine, State
from pizzactrl.sb_linz import STORYBOARD
from pizzactrl.hal_serial import PizzaHAL

logger = logging.getLogger('pizzactrl.main')


@click.command()
@click.option('--test', is_flag=True, default=False)
@click.option('--debug', is_flag=True, default=False)
@click.option('--loop', is_flag=True, default=False)
@click.option('--no-lang', is_flag=True, default=True)
def main(test: bool=False, debug: bool=False, loop: bool=False, no_lang: bool=True):
    if debug or test:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    else:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    hal = PizzaHAL()
    sm = Statemachine(hal, STORYBOARD, loop=loop, test=test, lang_select=no_lang)
    
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
