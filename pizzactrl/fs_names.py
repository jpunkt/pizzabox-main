import os
import logging
from enum import Enum
from uuid import uuid4

from pizzactrl import SOUNDS_PATH

logger = logging.getLogger(__name__)

"""
Paths to files
"""
# Base paths
_STORY_SOUNDS = '/home/pi/sounds/'
_SFX_SOUNDS = 'sounds/'
_REC_FILES = '/home/pi/pizzafiles/'

USB_STICK = _REC_FILES + '.stick'


class FileType(Enum):
    REC = 'r'
    STORY = 's'
    SFX = 'f'


class FileHandle:
    """
    Base class for handles on context-specific paths
    """
    uuid = None

    def __init__(self, name: str, filetype: FileType):
        self.name = name
        self.filetype = filetype
        # Create a uuid and fitting folder if not present
        # All RecFiles for this session will be added to this foldere
        if FileHandle.uuid is None:
            FileHandle.uuid = str(uuid4())
            logger.info(f'generated uuid for session: {FileHandle.uuid}')
            try:
                os.mkdir(_REC_FILES + FileHandle.uuid)
                FileHandle.uuid += '/'
            except OSError:
                FileHandle.uuid = ''

    def __str__(self):
        """
        Return the file path as a string
        """
        return {
            FileType.STORY: lambda: (_STORY_SOUNDS + self.name + '.wav'),
            FileType.SFX: lambda: (SOUNDS_PATH + self.name
                                   + '.wav'),
            FileType.REC: lambda: (_REC_FILES + FileHandle.uuid + self.name)
        }[self.filetype]()


class SfxFile(FileHandle):
    """
    Returns the path to a sound-effect file
    """
    def __init__(self, name: str):
        FileHandle.__init__(self, name, FileType.SFX)


class RecFile(FileHandle):
    """
    Returns the path to a recordable file
    """
    def __init__(self, name: str):
        FileHandle.__init__(self, name, FileType.REC)


class StoryFile(FileHandle):
    """
    Returns the path to a storyboard file
    """
    def __init__(self, name: str):
        FileHandle.__init__(self, name, FileType.STORY)


REC_NAME = RecFile('name.wav')
REC_MY_IBK = RecFile('my_ibk.wav')
REC_PORTRAIT = RecFile('portrait.jpg')
REC_CITY_NAME = RecFile('city_name.wav')
REC_CITY_DESC = RecFile('city_description.wav')
REC_CITY_SOUND = RecFile('city_sound.wav')
REC_DRAW_CITY = RecFile('city_video.h264')
REC_CITY_PHOTO = RecFile('city_drawing.jpg')

SFX_ERROR = SfxFile('error')
SFX_ERROR_DE = SfxFile('error-de')
SFX_ERROR_EN = SfxFile('error-en')
SFX_POST_OK = SfxFile('done')
SFX_SHUTTER = SfxFile('done')
SFX_REC_AUDIO = SfxFile('countdown')
SFX_STOP_REC = SfxFile('done')

SND_SELECT_LANG = StoryFile(name='01')
