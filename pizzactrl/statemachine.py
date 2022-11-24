import logging
import os.path
from pathlib import Path
import subprocess

from typing import Union
from enum import Enum, auto

from time import time

from pizzactrl import fs_names
from .storyboard import Language, Storyboard
from .hal_serial import KEYSTONE_COORDS, SerialCommunicationError, \
                        CommunicationError, PizzaHAL, \
                        wait_for_input, play_sound, turn_off, reset

logger = logging.getLogger(__name__)


class FileSystemException(Exception):
    pass


class State(Enum):
    POWER_ON = auto()
    POST = auto()
    IDLE_START = auto()
    LANGUAGE_SELECT = auto()
    PLAY = auto()
    REWIND = auto()
    POST_PROCESS = auto()
    IDLE_END = auto()
    SHUTDOWN = auto()
    ERROR = -1


class Statemachine:
    """
    Use `lang_select = 3` for 3 languages.
    `lang_select = True | 1 | 2` will enable language selection for 2 languages
    """
    def __init__(self,
                 hal: PizzaHAL,
                 story: Storyboard,
                 default_lang=Language.NOT_SET,
                 lang_select: Union[bool,int] = True,
                 loop: bool=True,
                 test: bool=False,
                 move: bool=True):
        self.hal = hal

        self.lang_select = lang_select
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
                State.IDLE_END: self._idle_end,
                State.SHUTDOWN: self._shutdown
             }
            
        while (self.state is not State.SHUTDOWN) and (self.state is not State.ERROR):
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
        if self.lang_select:
            def _select_de():
                self.lang = Language.DE
            
            def _select_en():
                self.lang = Language.EN

            def _select_tr():
                self.lang = Language.TR

            def _select_default():
                self.lang = self.LANG

            if self.lang_select > 2:
                wait_for_input(self.hal,
                            blue_cb=_select_de,
                            red_cb=_select_en,
                            green_cb=_select_tr,
                            sound=fs_names.SND_SELECT_LANG,
                            timeout_cb=_select_default)
            else:
                wait_for_input(self.hal,
                            red_cb=_select_de,
                            green_cb=_select_en,
                            sound=fs_names.SND_SELECT_LANG,
                            timeout_cb=_select_default)
        else:
            """
            Skip language selection
            """
            self.lang = self.LANG

        self.story.language = self.lang

        logger.debug(f'User selected language={self.lang}')
        self._next_state()

    def _play(self):
        """
        Select language, then run the storyboard
        """
        self.story.hal = self.hal
        fs_names.generate_session_id()

        while self.story.hasnext() and self.hal.lid_open:
            self.story.play_chapter()
            self.story.advance_chapter()
            
        self._next_state()

    def _post_process(self):
        """
        Post-processing
        """
        logger.debug('Converting video...')
        
        for fname in self.story.videofiles:
            if not Path(fname).exists():
                logger.debug(f'Video file {fname} does not exist.')
                continue

            start_time = time()
            fnew = fname.split('.')[0] + '.mov'
            logger.debug(f'Converting {fname} to {fnew} ...')
            # cmd = ['MP4Box', '-add', fname, fnew]
            # ffmpeg -hide_banner -i <input.h264> -lavfi "rotate=PI[rotated];[rotated]perspective=x0=370:y0=42:x1=1581:y1=0:x2=485:y2=993:x3=1414:y3=700:interpolation=cubic" <output.mp4>
            filter_string = f'''rotate=PI[rotated];[rotated]perspective='
                                x0={KEYSTONE_COORDS[0][0]}:y0={KEYSTONE_COORDS[0][1]}:'
                                x1={KEYSTONE_COORDS[1][0]}:y1={KEYSTONE_COORDS[1][1]}:'
                                x2={KEYSTONE_COORDS[2][0]}:y2={KEYSTONE_COORDS[2][1]}:'
                                x3={KEYSTONE_COORDS[3][0]}:y3={KEYSTONE_COORDS[3][1]}:'
                                interpolation=cubic'''
            cmd = ['ffmpeg', 
                   '-hide_banner', '-y',
                   '-framerate', '30',           # Original .h264 video has 29.97fps (according to vlc), but 30fps works better
                   '-i', fname, 
                   '-codec:v', 'h264_v4l2m2m',   # Uses hardware support, makes conversion faster
                   '-b:v', '4M',                 # Reduces artefacts 
                   '-lavfi', filter_string,
                   fnew]
            subprocess.run(cmd)
            logger.debug(f'Video conversion took {time() - start_time}s')

        self.hal.flush_serial()
        self._next_state()
    
    def _rewind(self):
        """
        Rewind all scrolls, post-process videos
        """
        turn_off(self.hal)
        self.story.skip_flag = False
        self.story.rewind()
        self._next_state()
        
    def _idle_end(self):
        """
        Initialize shutdown or go back to POST if `self.loop=True`
        """
        reset(self.hal)
        logger.debug('Turning off HELO1...')
        self.hal.helo1 = False

        logger.debug(f'statemachine.loop={self.loop}')
        if self.loop:
            self.state = State.POST
        else:
            logger.debug('Setting state to shutdown')
            self.state = State.SHUTDOWN

    def _shutdown(self):
        """
        Clean up, end execution
        """
        del self.hal
        del self.story
        self.state = None
        
