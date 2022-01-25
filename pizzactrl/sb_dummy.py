from fileinput import filename
from pizzactrl import fs_names
from pizzactrl.storyboard import *

STORYBOARD = Storyboard(
    Chapter(
        Do(Activity.PLAY_SOUND,
            sound=fs_names.SFX_REC_AUDIO),
        Do(Activity.RECORD_VIDEO,
            filename=fs_names.RecFile('my_video.h264'),
            duration=10),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.SFX_STOP_REC)
    )
)
