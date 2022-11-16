from fileinput import filename
from pizzactrl import fs_names
from pizzactrl.storyboard import *

STORYBOARD = Storyboard(
    # Chapter(
    #     Do(Activity.WAIT_FOR_INPUT,
    #         on_blue=Select(Option.CONTINUE))
    # ),
    Chapter(
        Do(Activity.PLAY_SOUND,
            sound=fs_names.SFX_REC_AUDIO),
        Do(Activity.RECORD_SOUND,
            filename=fs_names.RecFile('my_audio.wav'),
            cache=True,
            duration=10),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.SFX_STOP_REC)
    ),
    Chapter(
        Do(Activity.PLAY_SOUND,
            sound=fs_names.SFX_REC_AUDIO),
        Do(Activity.RECORD_VIDEO,
            filename=fs_names.RecFile('my_video.h264'),
            sound=fs_names.RecFile('my_audio.wav'),
            duration=5),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.SFX_STOP_REC)
    ),
    Chapter(
        Do(Activity.PLAY_SOUND,
            sound=fs_names.SFX_REC_AUDIO),
        Do(Activity.RECORD_SOUND,
            filename=fs_names.RecFile('my_audio2.wav'),
            cache=True,
            duration=10),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.SFX_STOP_REC)
    ),
    # Chapter(
    #     Do(Activity.PLAY_SOUND,
    #         sound=fs_names.SFX_REC_AUDIO),
    #     Do(Activity.RECORD_VIDEO,
    #         filename=fs_names.RecFile('my_video2.h264'),
    #         sound=fs_names.RecFile('my_audio2.wav'),
    #         duration=5),
    #     Do(Activity.PLAY_SOUND,
    #         sound=fs_names.SFX_STOP_REC)
    # )
)
