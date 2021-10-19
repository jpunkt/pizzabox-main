import logging
import os.path
import threading

from typing import Any

from time import sleep

from enum import Enum, auto

from pizzactrl import fs_names, sb_dummy, sb_de_alt
from .storyboard import Activity

from .hal import play_sound, take_photo, record_video, record_sound, turn_off, \
                 PizzaHAL, init_camera, init_sounds, wait_for_input, \
                 light_layer, backlight, advance, rewind

logger = logging.getLogger(__name__)


class State(Enum):
    POWER_ON = auto()
    POST = auto()
    IDLE_START = auto()
    PLAY = auto()
    PAUSE = auto()
    IDLE_END = auto()
    SHUTDOWN = auto()
    ERROR = -1


class Language(Enum):
    NOT_SET = auto()
    DE = auto()
    EN = auto()


def load_sounds():
    """
    Load all prerecorded Sounds from the cache

    :returns a list of sound file names
    """
    soundcache = [
        fs_names.SFX_SHUTTER,
        fs_names.SFX_ERROR,
        fs_names.SFX_POST_OK,
        fs_names.SND_SELECT_LANG
    ]
    return soundcache


class Statemachine:
    def __init__(self,
                 story_de: Any=None,
                 story_en: Any=None,
                 move: bool = False):
        self.state = State.POWER_ON
        self.hal = PizzaHAL()
        self.story = None
        self.story_de = story_de
        self.story_en = story_en
        self.alt = False
        self.lang = Language.NOT_SET
        self.move = move
        self.test = False

    def run(self):
        logger.debug(f'Run(state={self.state})')
        choice = {
                State.POWER_ON: self._power_on,
                State.POST: self._post,
                State.IDLE_START: self._idle_start,
                State.PLAY: self._play,
                State.IDLE_END: self._idle_end
             }
        while (self.state is not State.ERROR) and \
                (self.state is not State.SHUTDOWN):
            choice[self.state]()

        if self.state is State.ERROR:
            logger.debug('An error occurred. Trying to notify user...')
            if self.lang is Language.DE:
                play_sound(self.hal, fs_names.SFX_ERROR_DE)
            elif self.lang is Language.EN:
                play_sound(self.hal, fs_names.SFX_ERROR_EN)
            else:
                play_sound(self.hal, fs_names.SFX_ERROR)

        self._shutdown()

    def _lang_de(self, **kwargs):
        logger.info(f'select language german')
        self.lang = Language.DE
        self.story = self.story_de

    def _lang_en(self, **kwargs):
        logger.info(f'select language english')
        self.lang = Language.EN
        self.story = self.story_en

    def _power_on(self):
        """
        Initialize hal callbacks, load sounds
        """
        logger.debug(f'power on')
        # self.hal.lid_sensor.when_pressed = self._lid_open
        # self.hal.lid_sensor.when_released = self._lid_closed
        init_sounds(self.hal, load_sounds())
        init_camera(self.hal)
        self.state = State.POST

    def _post(self):
        """
        Power on self test.
        """
        logger.debug(f'post')
        # check scroll positions and rewind if necessary
        turn_off(self.hal)

        rewind(self.hal.motor_ud, self.hal.ud_sensor)

        if not os.path.exists(fs_names.USB_STICK):
            logger.warning('USB-Stick not found.')
            self.state = State.ERROR
            return

        # play a sound if everything is alright
        play_sound(self.hal, fs_names.SFX_POST_OK)

        # Callback for start when blue button is held
        self.hal.btn_forward.when_deactivated = self._start

        self.state = State.IDLE_START

    def _idle_start(self):
        """
        Device is armed. Wait for user to hold blue button to start
        """
        pass

    def _start(self):
        """
        Start playback when blue button is held for 3s
        """
        t = 0.
        while (self.hal.btn_forward.inactive_time < 3.0) and \
                not self.hal.btn_forward.is_active:
            t = self.hal.btn_forward.inactive_time

        if t > 3.0:
            self.hal.btn_forward.when_deactivated = None
            if not self.hal.btn_back.is_active:
                self.alt = True
            self.state = State.PLAY

    def _play(self):
        """
        Run the storyboard
        """
        logger.debug(f'play')
        if not self.alt:
            play_sound(self.hal, fs_names.SND_SELECT_LANG)
            wait_for_input(self.hal,
                           self._lang_de,
                           self._lang_en)

            sleep(0.5)
        else:
            self.story = sb_de_alt.STORYBOARD

        try:
            if self.story is None:
                self.story = sb_dummy.STORYBOARD
        except AttributeError:
            pass
        finally:
            if self.test:
                self.story = sb_dummy.STORYBOARD

        for chapter in iter(self.story):
            logger.debug(f'playing chapter {chapter}')
            while chapter.hasnext():
                act = next(chapter)
                logger.debug(f'next activity {act.activity}')
                if act.activity is Activity.WAIT_FOR_INPUT:
                    wait_for_input(hal=self.hal,
                                   go_callback=chapter.mobilize,
                                   back_callback=chapter.rewind)
                elif act.activity is Activity.ADVANCE_UP:
                    if chapter.move and self.move:
                        logger.debug(
                            f'advance{advance}({self.hal.motor_ud}, '
                            f'{self.hal.ud_sensor})')
                        advance(motor=self.hal.motor_ud,
                                sensor=self.hal.ud_sensor)
                    elif not self.move:
                        play_sound(self.hal, fs_names.StoryFile('stop'))
                else:
                    try:
                        {
                            Activity.PLAY_SOUND: play_sound,
                            Activity.RECORD_SOUND: record_sound,
                            Activity.RECORD_VIDEO: record_video,
                            Activity.TAKE_PHOTO: take_photo,
                            Activity.LIGHT_LAYER: light_layer,
                            Activity.LIGHT_BACK: backlight,
                            # Activity.ADVANCE_UP: noop

                        }[act.activity](self.hal, **act.values)
                    except KeyError:
                        logger.exception('Caught KeyError, ignoring...')
                        pass

        self.state = State.IDLE_END

    def _idle_end(self):
        """
        Initialize shutdown
        """
        if self.move:
            rewind(self.hal.motor_ud, self.hal.ud_sensor)

        self.state = State.SHUTDOWN

    def _shutdown(self):
        """
        Clean up, end execution
        """
        logger.debug('shutdown')

        turn_off(self.hal)

        del self.hal
