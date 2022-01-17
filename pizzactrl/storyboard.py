import logging
from enum import Enum, auto
from threading import active_count
from typing import List, Any

from pizzactrl.hal_serial import Lights, Scrolls, SerialCommands, PizzaHAL, \
                                 do_it, play_sound, take_photo, record_video, \
                                 record_sound, turn_off, wait_for_input, \
                                 set_light, set_movement, rewind

logger = logging.getLogger(__name__)


class ConfigurationException(Exception):
    pass


class Language(Enum):
    NOT_SET = 'NA'
    DE = 'DE'
    EN = 'EN'


class Option(Enum):
    """
    Options can be chosen by the user in WAIT_FOR_INPUT
    """
    CONTINUE = {}               # Continue with chapter
    REPEAT = {'rewind': True}   # Repeat chapter from beginning. `rewind=True`: reset scrolls to starting position  
    GOTO = {'chapter': 0}       # Jump to chapter number
    QUIT = {'quit': True}       # End playback.


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
    WAIT_FOR_INPUT = {'on_blue': Select(Option.CONTINUE), 
                      'on_red': Select(Option.REPEAT), 
                      'on_yellow': Select(None), 
                      'on_green': Select(None), 
                      'on_timeout': Select(Option.QUIT),
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
    ADVANCE_UP =     {'steps': 100,
                      'scroll': Scrolls.VERTICAL}
    ADVANCE_LEFT =   {'steps': 200,
                      'scroll': Scrolls.HORIZONTAL}
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
    def __init__(self, *activities):
        self.activities = activities
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


def _get_sound(language, **kwargs):
    """
    Select the right sound depending on the language
    """
    sound = kwargs.get(language, kwargs.get(Language.NOT_SET.value, None))
    if sound is None:
        logger.debug(f'_get_sound(language={language}) Could not find sound, returning None.')
    
    return sound


class Storyboard:
    def __init__(self, *story: List[Do]) -> None:
        self.story = story
        self.hal = None

        self._index = 0            # The storyboard index of the current chapter to play
        self._next_chapter = 0       # The storyboard index of the next chapter to play
        self._chapter_set = False    # `True` if the next chapter has been set

        self.MOVE = False          # self.move is reset to this value
        self._move = self.MOVE

        self._lang = Language.NOT_SET

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
        # rewind = selection.values.get('rewind', Option.REPEAT.value['rewind'])
        # next_chapter = selection.values.get('chapter', Option.GOTO.value['chapter'])
        # shutdown = selection.values.get('shutdown', Option.QUIT.value['shutdown'])
        
        def _continue(**kwargs):
            """
            Continue in the Storyboard. Prepare advancing to the next chapter.
            """
            logger.debug('User selected continue')
            if len(self.story) > (self._index + 1):
                self.next_chapter = self._index + 1
            else:
                self.next_chapter = None
        
        def _repeat(rewind: bool=None, **kwargs):
            """
            Repeat the current chapter. Do not rewind if the selection says so.
            """
            logger.debug('User selected repeat')
            self.next_chapter = self._index
            self.move = rewind
        
        def _goto(next_chapter: int=None, **kwargs):
            """
            Jump to a specified chapter.
            """
            logger.debug(f'User selected goto {next_chapter}')
            self.next_chapter = next_chapter

        def _quit(**kwargs):
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
            play_sound(hal, sound=_get_sound(language=self.language, **kwargs), **kwargs)

        def _wait_for_input(hal, sound=None, **kwargs):
            """
            Handle Activity.WAIT_FOR_INPUT
            """
            logger.debug(f'Storyboard._wait_for_input({kwargs})')
            wait_for_input(hal=hal,
                        blue_cb = self._option_callback(kwargs['on_blue']),
                        red_cb = self._option_callback(kwargs['on_red']),
                        yellow_cb = self._option_callback(kwargs['on_yellow']),
                        green_cb = self._option_callback(kwargs['on_green']),
                        timeout_cb = self._option_callback(kwargs['on_timeout']),
                        sound = _get_sound(language=self.language, **kwargs),
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
            set_movement(hal, **kwargs)
            if do_now:
                do_it(hal)

        def _light(hal, do_now=True, **kwargs):
            logger.debug(f'Storyboard._light({kwargs})')
            set_light(hal, **kwargs)
            if do_now:
                do_it(hal)

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
            Activity.RECORD_VIDEO: record_video,
            Activity.TAKE_PHOTO: take_photo,
            Activity.LIGHT_FRONT: _light,
            Activity.LIGHT_BACK: _light,
            Activity.ADVANCE_UP: _move,
            Activity.ADVANCE_LEFT: _move,
        }

        if self._index < len(self.story):
            chapter = self.story[self._index]

            while chapter.hasnext():
                act = next(chapter)
                logger.debug(f'next activity {act.activity}')
                try:
                    self.ACTIVITY_SELECTOR[act.activity](self.hal, **act.values)
                except KeyError as e:
                    raise ConfigurationException('Missing handler for {act.activity}', e)
            
            if not self._chapter_set:
                self._chapter_set = True
                self._next_chapter = self._index + 1

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

            if self.move:
                set_movement(self.hal, scroll=Scrolls.HORIZONTAL, steps=h_steps)
                set_movement(self.hal, scroll=Scrolls.VERTICAL, steps=v_steps)
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
