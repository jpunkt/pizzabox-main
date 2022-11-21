from fileinput import filename
from pizzactrl import fs_names
from pizzactrl.storyboard import *

STORYBOARD = Storyboard(
    Chapter(
        Do(Activity.PARALLEL,
            activities=[
                Do(Activity.LIGHT_FRONT,
                    w=1,
                    fade=3.0),
                Do(Activity.ADVANCE_LEFT,
                    steps=1,
                    speed=3),
                Do(Activity.ADVANCE_UP,
                    steps=1,
                    speed=4)
            ]),
        Do(Activity.WAIT_FOR_INPUT,
            on_red=Select(Option.REPEAT),
            on_green=Select(Option.CONTINUE))
        ),
    Chapter(
        Do(Activity.PARALLEL,
            activities=[
                Do(Activity.LIGHT_FRONT,
                    w=0,
                    fade=1.0)
            ]),
        )
    # Chapter(
    #     Do(Activity.PLAY_SOUND,
    #         DE=fs_names.StoryFile('german'),
    #         EN=fs_names.StoryFile('englisch'),
    #         TR=fs_names.StoryFile('turkisch'))
    # Chapter(
    #     Do(Activity.PLAY_SOUND,
    #         sound=fs_names.SFX_REC_AUDIO),
    #     Do(Activity.RECORD_VIDEO,
    #         filename=fs_names.RecFile('my_video.h264'),
    #         sound=fs_names.RecFile('my_audio.wav'),
    #         duration=5),
    #     Do(Activity.PLAY_SOUND,
    #         sound=fs_names.SFX_STOP_REC)
    # ),
    # Chapter(
    #     Do(Activity.PLAY_SOUND,
    #         sound=fs_names.SFX_REC_AUDIO),
    #     Do(Activity.RECORD_SOUND,
    #         filename=fs_names.RecFile('my_audio2.wav'),
    #         cache=True,
    #         duration=10),
    #     Do(Activity.PLAY_SOUND,
    #         sound=fs_names.SFX_STOP_REC)
    # ),
    # Chapter(
    #     Do(Activity.PLAY_SOUND,
    #         sound=fs_names.SFX_REC_AUDIO),
    #     Do(Activity.RECORD_VIDEO,
    #         filename=fs_names.RecFile('my_video2.h264'),
    #         sound=fs_names.RecFile('my_audio2.wav'),
    #         duration=5),
    #     Do(Activity.PLAY_SOUND,
    #         sound=fs_names.SFX_STOP_REC)
    #)
)
