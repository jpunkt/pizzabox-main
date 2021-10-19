from enum import Enum, auto


class Activity(Enum):
    WAIT_FOR_INPUT = {'steps': 0}
    PLAY_SOUND = {'sound': None}
    RECORD_SOUND = {'duration': 0.0, 'filename': '', 'cache': False}
    RECORD_VIDEO = {'duration': 0.0, 'filename': ''}
    TAKE_PHOTO = {'filename': ''}
    ADVANCE_UP = {'speed': 0.3, 'direction': True}
    LIGHT_LAYER = {'intensity': 1.0, 'fade': 0.0, 'layer': True}
    LIGHT_BACK = {'intensity': 1.0, 'fade': 0.0}


class Do:
    def __init__(self, activity: Activity, **kwargs):
        self.activity = activity
        self.values = {}
        for key, value in self.activity.value.items():
            self.values[key] = kwargs.get(key, value)


class Chapter:
    """
    A logical storyboard entity, which can be replayed (rewind to start).

    Keeps track of advanced steps on the scrolls.
    """
    def __init__(self, *activities):
        self.activities = activities
        self.pos = 0
        self.move = True
        self.move_ud = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.pos >= len(self.activities):
            raise StopIteration
        act = self.activities[self.pos]
        if act.activity is Activity.ADVANCE_UP:
            self.move_ud += 1
        self.pos += 1
        return act

    def hasnext(self):
        return self.pos < len(self.activities)

    def rewind(self, **kwargs):
        self.move = False
        self.move_ud = 0
        self.pos = 0

    def mobilize(self, **kwargs):
        self.move = True

