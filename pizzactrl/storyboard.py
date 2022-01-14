from enum import Enum, auto


class Option(Enum):
    """
    Options can be chosen by the user in WAIT_FOR_INPUT
    """
    CONTINUE = {}               # Continue with chapter
    REPEAT = {'rewind': True}   # Repeat chapter from beginning. `rewind=True`: reset scrolls to starting position  
    GOTO = {'chapter': 0}       # Jump to chapter number
    QUIT = {'shutdown': True}   # End playback. `shutdown=True` also powers off box


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
                      'sound': None, 
                      'timeout': 0}
    PLAY_SOUND =     {'sound': None}
    RECORD_SOUND =   {'duration': 10.0, 
                      'filename': '', 
                      'cache': False}
    RECORD_VIDEO =   {'duration': 60.0, 
                      'filename': ''}
    TAKE_PHOTO =     {'filename': ''}
    ADVANCE_UP =     {'steps': 100,          # TODO set right number of steps
                      'direction': True,
                      'horizontal': False}
    ADVANCE_LEFT =   {'steps': 200,          # TODO set right number of steps
                      'direction': True,
                      'horizontal': True}
    LIGHT_LAYER =    {'r': 0,
                      'g': 0,
                      'b': 0,
                      'w': 1.0,
                      'fade': 1.0,
                      'backlight': False}
    LIGHT_BACK =     {'r': 0,
                      'g': 0,
                      'b': 0,
                      'w': 1.0,
                      'fade': 1.0,
                      'backlight': True}


class Do:
    """
    An activity instance. Can override the default settings from `Activity`s
    """
    def __init__(self, activity: Activity, **kwargs):
        self.activity = activity
        self.values = {}
        for key, value in self.activity.value.items():
            self.values[key] = kwargs.get(key, value)


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

    def _update_pos(self, act: Activity):
        """
        Update the positions from the activity.
        Implicitly increments the index.
        """
        self.index += 1
        if act.activity is Activity.ADVANCE_UP:
            self.v_pos += act.values.get('steps', 0)
        elif act.activity is Activity.ADVANCE_LEFT:
            self.h_pos += act.values.get('steps', 0)

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

