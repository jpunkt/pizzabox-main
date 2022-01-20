import logging
import os.path

from enum import Enum, auto

from pizzactrl import fs_names
from .storyboard import Language, Storyboard
from .hal_serial import SerialCommunicationError, CommunicationError, PizzaHAL, wait_for_input, play_sound, turn_off

logger = logging.getLogger(__name__)


class FileSystemException(Exception):
    pass


class State(Enum):
    POWER_ON = auto()
    POST = auto()
    IDLE_START = auto()
    LANGUAGE_SELECT = auto()
    PLAY = auto()
    POST_PROCESS = auto()
    REWIND = auto()
    IDLE_END = auto()
    SHUTDOWN = auto()
    ERROR = -1


class Statemachine:
    def __init__(self,
                 hal: PizzaHAL,
                 story: Storyboard,
                 default_lang=Language.NOT_SET,
                 move: bool = False,
                 loop: bool = True,
                 test: bool = False):
        self.hal = hal

        self.LANG = default_lang
        self.lang = None

        self.story = story
        self.story.MOVE = move

        self.test = test
        self.loop = loop
        
        self.state = State.POWER_ON      

    def _next_state(self):
        """
        Set `self.state` to the next state
        """
        try:
            self.state = State(self.state.value + 1)
        except ValueError:
            pass

    def run(self):
        logger.debug(f'Starting Statemachine...')

        choice = {
                State.POWER_ON: self._power_on,
                State.POST: self._post,
                State.IDLE_START: self._idle_start,
                State.LANGUAGE_SELECT: self._lang_select,
                State.PLAY: self._play,
                State.POST_PROCESS: self._post_process,
                State.REWIND: self._rewind,
                State.IDLE_END: self._idle_end
             }
            
        while (self.state is not State.ERROR) and \
                (self.state is not State.SHUTDOWN):
            logger.debug(f'Run(state={self.state})')
            try:
                choice[self.state]()
            except (CommunicationError, SerialCommunicationError) as e:
                self.state = State.ERROR
                logger.error('Communication with microcontroller failed.', e)
            except Exception as e:
                self.state = State.ERROR
                logger.error(e)

        if self.state is State.ERROR:
            logger.debug('An error occurred. Trying to notify user...')
            if self.lang is Language.DE:
                play_sound(self.hal, fs_names.SFX_ERROR_DE)
            elif self.lang is Language.EN:
                play_sound(self.hal, fs_names.SFX_ERROR_EN)
            else:
                play_sound(self.hal, fs_names.SFX_ERROR)

        self._shutdown()

    def _power_on(self):
        """
        Initialize hal callbacks, load sounds
        """
        self.hal.init_sounds()
        self.hal.init_camera()

        self._next_state()

    def _post(self):
        """
        Power on self test.
        """
        if (not self.test) and (not os.path.exists(fs_names.USB_STICK)):
            raise FileSystemException('USB Stick not present!')

        self.hal.init_connection()
        
        # play a sound if everything is alright
        play_sound(self.hal, fs_names.SFX_POST_OK)

        if self.test:
            self.state = State.LANGUAGE_SELECT
        else:
            self._next_state()
        
    def _idle_start(self):
        """
        Device is armed. Wait for user to open the lid
        """
        if self.hal.lid_open:
            self._next_state()

    def _lang_select(self):
        """
        Select language
        """
        def _select_de():
            self.lang = Language.DE
        
        def _select_en():
            self.lang = Language.EN

        def _select_default():
            self.lang = self.LANG

        #sound = self.hal.soundcache.get(fs_names.SND_SELECT_LANG)
        #logger.debug(f'got sound {sound} from soundcache.')

        wait_for_input(self.hal,
                       blue_cb=_select_de,
                       red_cb=_select_en,
                       sound=fs_names.SND_SELECT_LANG,
                       timeout_cb=_select_default)

        self.story.language = self.lang

        logger.debug(f'User selected language={self.lang}')
        self._next_state()

    def _play(self):
        """
        Select language, then run the storyboard
        """
        self.story.hal = self.hal
        fs_names.generate_session_id()

        while self.story.hasnext():
            self.story.play_chapter()
            self.story.advance_chapter()
            
        self._next_state()

    def _post_process(self):
        """
        Post-processing
        """
        # TODO postprocessing - add sound
        # logger.debug('Converting video...')
        # cmdstring = f'MP4Box -add {fs_names.REC_DRAW_CITY} {fs_names.REC_MERGED_VIDEO}'
        # call([cmdstring], shell=True)
        
        self._next_state()
    
    def _rewind(self):
        """
        Rewind all scrolls, post-process videos
        """
        turn_off(self.hal)
        self.story.rewind()

        if self.loop:
            self.state = State.IDLE_START
        else:
            self._next_state()

    def _idle_end(self):
        """
        Initialize shutdown
        """
        self._next_state()

    def _shutdown(self):
        """
        Clean up, end execution
        """
        self.hal.pin_helo1.off()
        del self.hal
        del self.story
