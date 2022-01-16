import logging
import os.path

from typing import Any

from time import sleep

from enum import Enum, auto
from subprocess import call

from pizzactrl import fs_names, sb_dummy
from pizzactrl.hal import ScrollSensor
from .storyboard import Activity, Select, Option
from .hal_serial import SerialCommunicationError, PizzaHAL, play_sound, take_photo, record_video, record_sound, turn_off, wait_for_input, \
                 set_light, set_movement, rewind
from pizzactrl import storyboard

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


# Map Activities to function calls
ACTIVITY_SELECTOR = {
                        Activity.PLAY_SOUND: play_sound,
                        Activity.RECORD_SOUND: record_sound,
                        Activity.RECORD_VIDEO: record_video,
                        Activity.TAKE_PHOTO: take_photo,
                        Activity.LIGHT_LAYER: set_light,
                        Activity.LIGHT_BACK: set_light,
                        Activity.ADVANCE_UP: set_movement,
                        Activity.ADVANCE_LEFT: set_movement
                    }


class Statemachine:
    def __init__(self,
                 story_de: Any=None,
                 story_en: Any=None,
                 move: bool = False,
                 loop: bool = True,
                 test: bool = False):
        self.state = State.POWER_ON
        self.hal = PizzaHAL()

        self.chapter = 0            # The storyboard index of the current chapter to play
        self.next_chapter = 0       # The storyboard index of the next chapter to play
        self.chapter_set = False    # `True` if the next chapter has been set

        self.story = None
        self.story_de = story_de
        self.story_en = story_en
        
        self.lang = Language.NOT_SET
        
        self.MOVE = move          # self.move is reset to this value
        self.move = self.MOVE
        
        self.test = test
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
        
        # TODO enable lid sensor
        # self.hal.lid_sensor.when_pressed = self._lid_open
        # self.hal.lid_sensor.when_released = self._lid_closed
        
        self.hal.init_sounds(load_sounds())
        self.hal.init_camera()

        self.state = State.POST

    def _post(self):
        """
        Power on self test.
        """

        logger.debug(f'post')

        if (not self.test) and (not os.path.exists(fs_names.USB_STICK)):
            logger.warning('USB-Stick not found.')
            self.state = State.ERROR
            return

        # TODO set RPi_HELO pins, wait for response

        # Callback for start when blue button is held
        # self.hal.btn_start.when_activated = self._start_or_rewind
        # logger.debug('start button callback activated')

        try:
            self.hal.init_connection()
        except SerialCommunicationError as e:
            self.state = State.ERROR
            logger.exception(e)
            return

        # play a sound if everything is alright
        play_sound(self.hal, fs_names.SFX_POST_OK)

        if self.test:
            self.state = State.PLAY
            logger.debug('play')
        else:
            self.state = State.IDLE_START
            logger.debug('idle_start')
        

    def _idle_start(self):
        """
        Device is armed. Wait for user to press start button
        """
        pass

    def _play(self):
        """
        Select language, then run the storyboard
        """
        logger.debug(f'play')
        if self.test:
            self.story = sb_dummy.STORYBOARD
        else:
            # TODO reenable language selection
            self.story = self.story_en

        while self.chapter is not None:
            self._play_chapter()
            self._advance_chapter()
            
        self.state = State.REWIND

    def _option_callback(self, selection: Select):
        """
        Return a callback for the appropriate option and parameters.
        Callbacks set the properties of `Statemachine` to determine it's behaviour.
        """
        rewind = selection.values.get('rewind', Option.REPEAT.value['rewind'])
        next_chapter = selection.values.get('chapter', Option.GOTO.value['chapter'])
        shutdown = selection.values.get('shutdown', Option.QUIT.value['shutdown'])
        
        def _continue(**kwargs):
            """
            Continue in the Storyboard. Prepare advancing to the next chapter.
            """
            self.move = self.MOVE
            self.chapter_set = True
            if len(self.story) > (self.chapter + 1):
                self.next_chapter = self.chapter + 1
            else:
                self.next_chapter = None

        def _repeat(**kwargs):
            """
            Repeat the current chapter. Do not rewind if the selection says so.
            """
            self.chapter_set = True
            self.move = rewind
            self.next_chapter = self.chapter
        
        def _goto(**kwargs):
            """
            Jump to a specified chapter.
            """
            self.chapter_set = True
            self.move = self.MOVE
            self.next_chapter = next_chapter

        def _quit(**kwargs):
            self.chapter_set = True
            self.move = self.MOVE
            self.loop = not shutdown
            self.next_chapter = None

        return {
                   Option.CONTINUE: _continue,
                   Option.REPEAT: _repeat,
                   Option.GOTO: _goto,
                   Option.QUIT: _quit,
                   None: None
               }[selection.option]

    def _play_chapter(self):
        """
        Play the chapter specified by self.chapter
        """
        logger.debug(f'playing chapter {self.chapter}')

        if self.chapter < len(self.story):
            chapter = self.story[self.chapter]

            while chapter.hasnext():
                act = next(chapter)
                logger.debug(f'next activity {act.activity}')
                if act.activity is Activity.WAIT_FOR_INPUT:
                    wait_for_input(hal=self.hal,
                                blue_cb = self._option_callback(act.values['on_blue']),
                                red_cb = self._option_callback(act.values['on_red']),
                                yellow_cb = self._option_callback(act.values['on_yellow']),
                                green_cb = self._option_callback(act.values['on_green']),
                                timeout_cb = self._option_callback(act.values['on_timeout']),
                                **act.values)
                else:
                    try:
                        ACTIVITY_SELECTOR[act.activity](self.hal, **act.values)
                    except KeyError:
                        logger.exception('Caught KeyError, ignoring...')
                        pass
            
            if not self.chapter_set:
                self.chapter_set = True
                self.next_chapter = self.chapter + 1

        else:
            self.next_chapter = None
    
    def _advance_chapter(self):
        """
        Update chapters and move the scrolls.
        Update self.chapter to self.next_chapter
        """
        if self.chapter_set and (self.next_chapter is not None):
            diff = self.next_chapter - self.chapter
            h_steps = 0
            v_steps = 0
            if diff < 0:
                """
                Rewind all chapters up to target
                """
                for ch in self.story[self.next_chapter:self.chapter]:
                    steps = ch.rewind()
                    h_steps += steps['h_steps']
                    v_steps += steps['v_steps']

            elif diff > 0:
                """
                Skip all chapters up to target
                """
                for ch in self.story[self.chapter:self.next_chapter]:
                    steps = ch.skip()
                    h_steps += steps['h_steps']
                    v_steps += steps['v_steps']
            else:
                """
                Rewind current chapter
                """
                steps = self.story[self.chapter].rewind()
                h_steps = steps['h_steps']
                v_steps = steps['v_steps']

            if self.move:
                set_movement(self.hal, h_steps, True)
                set_movement(self.hal, v_steps, False)

        logger.debug(f'Setting chapter (cur: {self.chapter}) to {self.next_chapter}.')
        self.chapter = self.next_chapter
        self.chapter_set = False

    def _rewind(self):
        """
        Rewind all scrolls, post-process videos
        """
        # TODO postprocessing - add sound
        # logger.debug('Converting video...')
        # cmdstring = f'MP4Box -add {fs_names.REC_DRAW_CITY} {fs_names.REC_MERGED_VIDEO}'
        # call([cmdstring], shell=True)

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
