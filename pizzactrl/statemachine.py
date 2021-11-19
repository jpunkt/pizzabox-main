import logging
import os.path

from typing import Any

from time import sleep

from enum import Enum, auto
from subprocess import call

from pizzactrl import fs_names, sb_dummy
from .storyboard import Activity
from .hal_serial import play_sound, take_photo, record_video, record_sound, turn_off, \
                 PizzaHAL, init_camera, init_sounds, wait_for_input, \
                 light_layer, backlight, move_vert, move_hor, rewind

logger = logging.getLogger(__name__)


class State(Enum):
    POWER_ON = auto()
    POST = auto()
    IDLE_START = auto()
    PLAY = auto()
    PAUSE = auto()
    REWIND = auto()
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
                 move: bool = False,
                 loop: bool = True):
        self.state = State.POWER_ON
        self.hal = PizzaHAL()
        self.story = None
        self.story_de = story_de
        self.story_en = story_en
        self.alt = False
        self.lang = Language.NOT_SET
        self.move = move
        self.test = False
        self.loop = loop

    def run(self):
        logger.debug(f'Run(state={self.state})')
        choice = {
                State.POWER_ON: self._power_on,
                State.POST: self._post,
                State.IDLE_START: self._idle_start,
                State.PLAY: self._play,
                State.REWIND: self._rewind,
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

        if not os.path.exists(fs_names.USB_STICK):
            logger.warning('USB-Stick not found.')
            self.state = State.ERROR
            return

        # Callback for start when blue button is held
        self.hal.btn_start.when_activated = self._start_or_rewind
        logger.debug('start button callback activated')

        # play a sound if everything is alright
        play_sound(self.hal, fs_names.SFX_POST_OK)

        self.state = State.IDLE_START
        logger.debug('idle_start')

    def _idle_start(self):
        """
        Device is armed. Wait for user to press start button
        """
        pass

    def _start_or_rewind(self):
        """
        Callback function.

        If statemachine is in idle state, start playback when start
        button is pressed (released).

        If statemachine is playing, trigger rewind and start fresh
        """
        if self.state == State.IDLE_START:
            self.state = State.PLAY
            return
        if self.state == State.PLAY:
            self.state = State.REWIND

    def _play(self):
        """
        Run the storyboard
        """
        logger.debug(f'play')
        if self.test:
            self.story = sb_dummy.STORYBOARD
        else:
            # TODO reenable language selection
            self.story = self.story_en

        for chapter in iter(self.story):
            logger.debug(f'playing chapter {chapter}')
            while chapter.hasnext():
                act = next(chapter)
                logger.debug(f'next activity {act.activity}')
                if act.activity is Activity.WAIT_FOR_INPUT:
                    wait_for_input(hal=self.hal,
                                   go_callback=chapter.mobilize,
                                   back_callback=chapter.rewind,
                                   to_callback=self._start_or_rewind)
                # elif act.activity is Activity.ADVANCE_UP:
                #     if chapter.move and self.move:
                #         logger.debug(
                #             f'advance({self.hal.motor_ud}, '
                #             f'{self.hal.ud_sensor})')
                #         advance(motor=self.hal.motor_ud,
                #                 sensor=self.hal.ud_sensor)
                #     elif not self.move:
                #         play_sound(self.hal, fs_names.StoryFile('stop'))
                else:
                    try:
                        {
                            Activity.PLAY_SOUND: play_sound,
                            Activity.RECORD_SOUND: record_sound,
                            Activity.RECORD_VIDEO: record_video,
                            Activity.TAKE_PHOTO: take_photo,
                            Activity.LIGHT_LAYER: light_layer,
                            Activity.LIGHT_BACK: backlight,
                            # Activity.ADVANCE_UP: move_vert,
                            # Activity.ADVANCE_LEFT: move_hor
                        }[act.activity](self.hal, **act.values)
                    except KeyError:
                        logger.exception('Caught KeyError, ignoring...')
                        pass

        self.state = State.REWIND

    def _rewind(self):
        """
        Rewind all scrolls, post-process videos
        """
        # postprocessing
        logger.debug('Converting video...')
        cmdstring = f'MP4Box -add {fs_names.REC_DRAW_CITY} {fs_names.REC_MERGED_VIDEO}'
        call([cmdstring], shell=True)

        logger.debug('Rewinding...')
        if self.move:
            rewind(self.hal)
        for chapter in self.story:
            chapter.rewind()

        if self.loop:
            self.state = State.IDLE_START
        else:
            self.state = State.IDLE_END

    def _idle_end(self):
        """
        Initialize shutdown
        """
        self.state = State.SHUTDOWN

    def _shutdown(self):
        """
        Clean up, end execution
        """
        logger.debug('shutdown')

        turn_off(self.hal)

        del self.hal
