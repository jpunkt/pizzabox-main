import logging
from enum import Enum, auto
from threading import active_count
from typing import List, Any

from pizzactrl.hal_serial import Lights, Scrolls, \
                                 do_it, play_sound, take_photo, record_video, \
                                 record_sound, wait_for_input, \
                                 set_light, set_movement, rewind

logger = logging.getLogger(__name__)


class ConfigurationException(Exception):
    pass


class Language(Enum):
    NOT_SET = 'sound'
    DE = 'DE'
    EN = 'EN'


class Option(Enum):
    """
    Options can be chosen by the user in WAIT_FOR_INPUT
    """
    CONTINUE =  {'skip_flag': None}     # Continue with chapter. Set `skip_flag=True` to skip all chapters marked with `skip_flag`
    REPEAT =    {'rewind': True}        # Repeat chapter from beginning. `rewind=True`: reset scrolls to starting position  
    GOTO =      {'chapter': 0,
                 'skip_flag': None}     # Jump to chapter number
    QUIT = {}                           # End playback. Will cause restart if `statemachine.loop=True`


class Select:
    """
    An option instance. Can override the default settings from `Option`s
    """
    def __init__(self, option: Option, **kwargs):
        self.option = option
        self.values = {}
        if option is not None:
            for key, value in self.option.value.items():
                self.values[key] = kwargs.get(key, value)


class Activity(Enum):
    """
    Things the box can do
    """
    WAIT_FOR_INPUT = {'on_blue': Select(None), 
                      'on_red': Select(None), 
                      'on_yellow': Select(None), 
                      'on_green': Select(None), 
                      'on_timeout': Select(None),
                      Language.NOT_SET.value: None,
                      Language.DE.value: None,
                      Language.EN.value: None, 
                      'timeout': 0}
    PLAY_SOUND =     {Language.NOT_SET.value: None, 
                      Language.DE.value: None,
                      Language.EN.value: None}
    RECORD_SOUND =   {'duration': 10.0, 
                      'filename': '', 
                      'cache': False}
    RECORD_VIDEO =   {'duration': 60.0, 
                      'filename': ''}
    TAKE_PHOTO =     {'filename': ''}
    ADVANCE_UP =     {'steps': 43,
                      'scroll': Scrolls.VERTICAL,
                      'speed': 3}
    ADVANCE_LEFT =   {'steps': 92,
                      'scroll': Scrolls.HORIZONTAL,
                      'speed': 2}
    LIGHT_FRONT =    {'r': 0,
                      'g': 0,
                      'b': 0,
                      'w': 0,
                      'fade': 1.0,
                      'light': Lights.FRONTLIGHT}
    LIGHT_BACK =     {'r': 0,
                      'g': 0,
                      'b': 0,
                      'w': 0,
                      'fade': 1.0,
                      'light': Lights.BACKLIGHT}
    PARALLEL =       {'activities': []}
    GOTO =           {'index': 0}


class Do:
    """
    An activity instance. Can override the default settings from `Activity`s
    """
    def __init__(self, activity: Activity, **kwargs):
        self.activity = activity
        self.values = {}
        for key, value in self.activity.value.items():
            self.values[key] = kwargs.get(key, value)

    def __repr__(self) -> str:
        return f'{self.activity.name}({self.values})'

    def __str__(self) -> str:
        return f'{self.activity.name}({self.values})'

    def get_steps(self):
        """
        Returns the number of steps this activity makes.
        returns: h_steps, v_steps
        """
        h_steps = 0
        v_steps = 0
        if self.activity is Activity.ADVANCE_UP:
            v_steps += self.values['steps']
        elif self.activity is Activity.ADVANCE_LEFT:
            h_steps += self.values['steps']
        elif self.activity is Activity.PARALLEL:
            for act in self.values['activities']:
                h, v = act.get_steps()
                h_steps += h
                v_steps += v
        return h_steps, v_steps


class Chapter:
    """
    A logical storyboard entity, which can be replayed (rewind to start) 
    or skipped (do all movements at once).

    Keeps track of advanced steps on the scrolls.
    """
    def __init__(self, *activities, skip_flag: bool=False):
        self.activities = activities
        self.skip_flag = skip_flag
        self.index = 0
        self.h_pos = 0
        self.v_pos = 0
        
    def __iter__(self):
        return self

    def __next__(self):
        if self.index >= len(self.activities):
            raise StopIteration
        
        act = self.activities[self.index]
        self._update_pos(act)
        return act

    def _update_pos(self, act: Do):
        """
        Update the positions from the activity.
        Implicitly increments the index.
        """
        self.index += 1
        h, v = act.get_steps()
        self.h_pos += h
        self.v_pos += v

    def hasnext(self):
        """
        Returns True if the chapter has more activities
        """
        return self.index < len(self.activities)

    def rewind(self, **kwargs):
        """
        Reset the position to zero. Return how many steps are needed to rewind the scrolls
        """
        self.index = 0
        h_pos = self.h_pos
        v_pos = self.v_pos
        self.h_pos = 0
        self.v_pos = 0
        return {'h_steps': -h_pos, 'v_steps': -v_pos}

    def skip(self, **kwargs):
        """
        Skip chapter. Returns all movements necessary to advance scrolls.
        """
        h_pos = self.h_pos
        v_pos = self.v_pos
        for act in self.activities[self.index:]:
            self._update_pos(act)
        return {'h_steps': self.h_pos - h_pos, 'v_steps': self.v_pos - v_pos}


def _get_sound(language: Language, **kwargs):
    """
    Select the right sound depending on the language
    """
    sound = kwargs.get(language.value, None)

    if sound is None:
        # internationalized language may be None, so check this twice
        sound = kwargs.get(Language.NOT_SET.value, None)

    logger.debug(f'_get_sound(language={language})={sound}')
    
    return sound


class Storyboard:
    def __init__(self, *story: List[Chapter]) -> None:
        self.story = story
        self.hal = None

        self._index = 0            # The storyboard index of the current chapter to play
        self._next_chapter = 0       # The storyboard index of the next chapter to play
        self._chapter_set = False    # `True` if the next chapter has been set

        self.skip_flag = False     # Set `True` to skip chapters marked with skip_flag

        self.MOVE = True           # self.move is reset to this value
        self._move = self.MOVE

        self._lang = Language.NOT_SET

        self.videos = []

        self.ACTIVITY_SELECTOR = None

    @property
    def move(self) -> bool:
        return self._move

    @move.setter
    def move(self, move: bool):
        if move is None:
            self._move = self.MOVE
        else:
            self._move = move

    @property
    def language(self) -> Language:
        return self._lang

    @language.setter
    def language(self, language: Language):
        self._lang = language

    @property
    def next_chapter(self):
        return self._next_chapter

    @next_chapter.setter
    def next_chapter(self, next_chapter):
        self._chapter_set = True
        self.move = None   # Reset to default value
        self._next_chapter = next_chapter

    def hasnext(self):
        return self._index is not None

    def _option_callback(self, selection: Select):
        """
        Return a callback for the appropriate option and parameters.
        Callbacks set the properties of `Statemachine` to determine it's behaviour.
        """
        _rewind = selection.values.get('rewind', None)
        _next_chapter = selection.values.get('chapter', None)
        _skip_flag = selection.values.get('skip_flag', None)
        
        def _continue():
            """
            Continue in the Storyboard. Prepare advancing to the next chapter.
            """
            logger.debug('User selected continue')
            if len(self.story) > (self._index + 1):
                self.next_chapter = self._index + 1
                if _skip_flag is not None:
                    self.skip_flag = _skip_flag
            else:
                self.next_chapter = None
        
        def _repeat():
            """
            Repeat the current chapter. Do not rewind if the selection says so.
            """
            logger.debug('User selected repeat')
            self.next_chapter = self._index
            self.move = _rewind
        
        def _goto():
            """
            Jump to a specified chapter.
            """
            logger.debug(f'User selected goto {_next_chapter}')
            self.next_chapter = _next_chapter
            if _skip_flag is not None:
                self.skip_flag = _skip_flag

        def _quit():
            logger.debug('User selected quit')
            self.next_chapter = None

        return {
                   Option.CONTINUE: _continue,
                   Option.REPEAT: _repeat,
                   Option.GOTO: _goto,
                   Option.QUIT: _quit,
                   None: None
               }[selection.option]

    def play_chapter(self):
        """
        Play the chapter specified by self.chapter
        """
        logger.debug(f'playing chapter {self._index}')

        if self.hal is None:
            raise ConfigurationException('Set Storyboard.hal before calling Storyboard.play_chapter()')

        if self._index is None:
            # Reached end of story
            return

        def _play_sound(hal, **kwargs):
            """
            Handle Activity.PLAY_SOUND
            """
            logger.debug(f'Storyboard._play_sound({kwargs})')
            play_sound(hal, sound=_get_sound(language=self.language, **kwargs))

        def _wait_for_input(hal, sound=None, **kwargs):
            """
            Handle Activity.WAIT_FOR_INPUT
            """
            logger.debug(f'Storyboard._wait_for_input({kwargs})')
            
            kwargs['sound'] = _get_sound(language=self.language, **kwargs)

            wait_for_input(hal=hal,
                        blue_cb = self._option_callback(kwargs['on_blue']),
                        red_cb = self._option_callback(kwargs['on_red']),
                        yellow_cb = self._option_callback(kwargs['on_yellow']),
                        green_cb = self._option_callback(kwargs['on_green']),
                        timeout_cb = self._option_callback(kwargs['on_timeout']),
                        **kwargs)

        def _parallel(hal, activities: List[Do], **kwargs):
            """
            Handle Activity.PARALLEL
            """
            logger.debug(f'Storyboard._parallel({activities})')
            for paract in activities:
                self.ACTIVITY_SELECTOR[paract.activity](hal, do_now=False, **paract.values)   
            do_it(self.hal)

        def _move(hal, do_now=True, **kwargs):
            logger.debug(f'Storyboard._move({kwargs})')
            if not self.move:
                return
            set_movement(hal, **kwargs)
            if do_now:
                do_it(hal)

        def _light(hal, do_now=True, **kwargs):
            logger.debug(f'Storyboard._light({kwargs})')
            set_light(hal, **kwargs)
            if do_now:
                do_it(hal)

        def _record_video(hal, filename=None, **kwargs):
            logger.debug(f'Storyboard._record_video(filename={filename}, {kwargs})')
            record_video(hal, filename=filename, **kwargs)
            self.videos.append(str(filename))

        def _goto(hal, index:int, **kwargs):
            """
            Set the next chapter
            """
            logger.debug(f'Storyboard._goto({kwargs})')
            self.next_chapter = index

        self.ACTIVITY_SELECTOR = {
            Activity.PLAY_SOUND: _play_sound,
            Activity.WAIT_FOR_INPUT: _wait_for_input,
            Activity.PARALLEL: _parallel,
            Activity.GOTO: _goto,
            Activity.RECORD_SOUND: record_sound,
            Activity.RECORD_VIDEO: _record_video,
            Activity.TAKE_PHOTO: take_photo,
            Activity.LIGHT_FRONT: _light,
            Activity.LIGHT_BACK: _light,
            Activity.ADVANCE_UP: _move,
            Activity.ADVANCE_LEFT: _move,
        }

        if self._index < len(self.story):
            chapter = self.story[self._index]
            if self.skip_flag and chapter.skip_flag:
                # Skip all chapters marked with skip_flag
                self.next_chapter = self._index + 1
                self._chapter_set = True
                return

            while chapter.hasnext() and self.hal.lid_open:
                act = next(chapter)
                logger.debug(f'next activity {act.activity}')
                try:
                    self.ACTIVITY_SELECTOR[act.activity](self.hal, **act.values)
                except KeyError as e:
                    raise ConfigurationException(f'Missing handler for {act.activity}', e)
            
            if not self._chapter_set:
                self._chapter_set = True
                if self._index < (len(self.story) - 1):
                    self._next_chapter = self._index + 1
                else:
                    self._next_chapter = None

        else:
            self._next_chapter = None
    
    def advance_chapter(self):
        """
        Update chapters and move the scrolls.
        Update self.chapter to self.next_chapter
        """
        if not self._chapter_set:
            return
        elif self._index is None:
            return
        elif self._next_chapter is not None:
            diff = self._next_chapter - self._index
            h_steps = 0
            v_steps = 0
            if diff < 0:
                """
                Rewind all chapters up to target
                """
                for ch in self.story[self._next_chapter:self._index]:
                    steps = ch.rewind()
                    h_steps += steps['h_steps']
                    v_steps += steps['v_steps']
            elif diff > 0:
                """
                Skip all chapters up to target
                """
                for ch in self.story[self._index:self._next_chapter]:
                    logger.debug(f'Queueing chapter {ch} for skipping')
                    steps = ch.skip()
                    h_steps += steps['h_steps']
                    v_steps += steps['v_steps']
            else:
                """
                Rewind current chapter
                """
                steps = self.story[self._index].rewind()
                h_steps = steps['h_steps']
                v_steps = steps['v_steps']

            logger.debug(f'storyboard.move={self.move} and h_steps={h_steps}, v_steps={v_steps}.')
            if self.move and ((h_steps != 0) or (v_steps != 0)):
                set_movement(self.hal, scroll=Scrolls.HORIZONTAL, steps=h_steps, speed=4)
                set_movement(self.hal, scroll=Scrolls.VERTICAL, steps=v_steps, speed=4)
                do_it(self.hal)

        logger.debug(f'Setting chapter (cur: {self._index}) to {self._next_chapter}.')
        self._index = self._next_chapter
        self._chapter_set = False

    def rewind(self):
        if self.hal is None:
            raise ConfigurationException('Set Storyboard.hal before calling Storyboard.rewind()')

        if self.move:
            rewind(self.hal)

        for chapter in self.story:
            chapter.rewind()

        self._index = self._next_chapter = 0
