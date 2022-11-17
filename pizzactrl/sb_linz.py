from pizzactrl import fs_names
from pizzactrl.storyboard import *

REC_NAME = fs_names.RecFile('name.wav')
REC_VIDEO = fs_names.RecFile('malen.h264')

Do_FADE_BLACK = Do(Activity.PARALLEL,
                activities=[
                    Do(Activity.LIGHT_BACK,
                        fade=1.0),
                    Do(Activity.LIGHT_FRONT,
                        fade=1.0)
                ])

STORYBOARD = Storyboard(
    Chapter(    # 0. Startposition
        Do(Activity.ADVANCE_UP,
            steps=-5,
            speed=2),
        Do(Activity.ADVANCE_LEFT,
            steps=8,
            speed=2)
    ),
    Chapter(    # 1. Beginn
        Do(Activity.LIGHT_FRONT, 
            w=1.0, 
            fade=1.0),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.StoryFile('01')),
        Do(Activity.WAIT_FOR_INPUT,
            on_blue=Select(Option.CONTINUE))
    ),
    Chapter(
        Do(Activity.PLAY_SOUND,
            sound=fs_names.StoryFile('02')),
        Do(Activity.LIGHT_FRONT, 
            fade=1.0),
        Do(Activity.WAIT_FOR_INPUT,
            on_blue=Select(Option.CONTINUE))
    ),
    Chapter(
        Do(Activity.ADVANCE_UP),
        Do(Activity.LIGHT_BACK,
            r=0.15,
            b=0.6, 
            fade=1.0),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.StoryFile('03')),
        Do(Activity.WAIT_FOR_INPUT,
            on_yellow=Select(Option.CONTINUE))
    ),
    Chapter(    # 2. Spiegel 1
        Do(Activity.LIGHT_BACK,
            w=1.0, 
            fade=1.0),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.StoryFile('04')),
        Do(Activity.WAIT_FOR_INPUT,
            on_red=Select(Option.CONTINUE)),
    ),
    Chapter(    # 3. Schneewittchen
        Do(Activity.LIGHT_BACK,
            fade=0),
        Do(Activity.PARALLEL,
        activities=[
            Do(Activity.ADVANCE_UP),
            Do(Activity.ADVANCE_LEFT)
        ]),
        Do(Activity.LIGHT_BACK,
            w=1.0,
            fade=1.0),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.StoryFile('05')),
        Do(Activity.WAIT_FOR_INPUT,
            on_red=Select(Option.CONTINUE))
    ),
    Chapter(    # 3.1 Schneewittchen + Zwergin
        Do(Activity.LIGHT_BACK,
            fade=0),
        Do(Activity.ADVANCE_UP),
        Do(Activity.LIGHT_BACK,
            w=1.0,
            fade=1.0),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.StoryFile('06')),
        Do(Activity.WAIT_FOR_INPUT,
            on_blue=Select(Option.CONTINUE))
    ),
    Chapter(    # 4. Rapunzel
        Do(Activity.LIGHT_BACK,
            fade=0),
        Do(Activity.PARALLEL,
        activities=[
            Do(Activity.ADVANCE_UP),
            Do(Activity.ADVANCE_LEFT)
        ]),
        Do(Activity.LIGHT_BACK,
            w=1.0,
            fade=1.0),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.StoryFile('07')),
        Do(Activity.WAIT_FOR_INPUT,
            on_green=Select(Option.CONTINUE))
    ),
    Chapter(    # 5. Froschkönig
        Do(Activity.LIGHT_BACK,
            fade=0),
        Do(Activity.PARALLEL,
        activities=[
            Do(Activity.ADVANCE_UP),
            Do(Activity.ADVANCE_LEFT)
        ]),
        Do(Activity.LIGHT_BACK,
            w=1.0,
            fade=0),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.StoryFile('08')),
        Do(Activity.WAIT_FOR_INPUT,
            on_green=Select(Option.CONTINUE))
    ),
    Chapter(    # 5.1 Froschprinzessin
        Do(Activity.LIGHT_BACK,
            g=1.0,
            fade=1.0),
        Do(Activity.LIGHT_FRONT,   # kurze pause
            fade=1.0),
        Do(Activity.LIGHT_BACK,
            fade=0),
        Do(Activity.ADVANCE_UP),
        Do(Activity.LIGHT_BACK,
            g=1.0,
            fade=1.0),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.StoryFile('09')),
        Do(Activity.WAIT_FOR_INPUT,
            on_blue=Select(Option.CONTINUE))
    ),
    Chapter(    # 6. Der böse Wolf
        Do(Activity.LIGHT_BACK,
            fade=0),
        Do(Activity.PARALLEL,
        activities=[
            Do(Activity.ADVANCE_UP),
            Do(Activity.ADVANCE_LEFT)
        ]),
        Do(Activity.LIGHT_BACK,
            r=1.0,
            fade=1.0),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.StoryFile('10')),
        Do(Activity.WAIT_FOR_INPUT,
            on_red=Select(Option.CONTINUE))
    ),
    Chapter(    # 6.1 Wolf enttarnt
        Do(Activity.LIGHT_BACK,
            w=1.0,
            fade=1.0),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.StoryFile('11')),
        Do(Activity.WAIT_FOR_INPUT,
            on_blue=Select(Option.CONTINUE))
    ),
    Chapter(    # 7. Spiegel 4 + Dornröschen
        Do(Activity.LIGHT_BACK,
            fade=0),
        Do(Activity.PARALLEL,
        activities=[
            Do(Activity.ADVANCE_UP),
            Do(Activity.ADVANCE_LEFT)
        ]),
        Do(Activity.LIGHT_BACK,
            r=0.15,
            b=0.6, 
            fade=1.0),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.StoryFile('12')),
        Do(Activity.WAIT_FOR_INPUT,
            on_yellow=Select(Option.CONTINUE))
    ),
    Chapter(    # 8.1 Dornröschen aufwachen
        Do(Activity.LIGHT_BACK,
            w=1.0, 
            fade=1.0),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.StoryFile('13')),
        Do(Activity.WAIT_FOR_INPUT,
            on_yellow=Select(Option.CONTINUE))
    ),
    Chapter(    # 9. Zurück zuhause
        Do(Activity.LIGHT_BACK,
            fade=0),
        Do(Activity.PARALLEL,
        activities=[
            Do(Activity.ADVANCE_UP),
            Do(Activity.ADVANCE_LEFT)
        ]),
        Do(Activity.LIGHT_BACK,
            r=0.15,
            b=0.6, 
            fade=1.0),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.StoryFile('14')),
        Do(Activity.WAIT_FOR_INPUT,
            on_blue=Select(Option.CONTINUE))
    ),
    Chapter(     # 9.1 Freunde
        Do(Activity.LIGHT_BACK,
            fade=0),
        Do(Activity.ADVANCE_UP),
        Do(Activity.LIGHT_BACK,
            r=0.15,
            b=0.6, 
            fade=1.0),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.StoryFile('15')),
        Do(Activity.WAIT_FOR_INPUT,
            on_blue=Select(Option.CONTINUE))
    ),
    Chapter(     # Lightshow
        Do(Activity.LIGHT_BACK,
            r=0.8,
            fade=0.5),
        Do(Activity.LIGHT_BACK,
            g=0.8,
            fade=0.5),
        Do(Activity.LIGHT_BACK,
            b=0.8,
            fade=0.5),
        Do(Activity.LIGHT_BACK,
            r=0.8,
            fade=0.5),
        Do(Activity.LIGHT_BACK,
            g=0.8,
            fade=0.5),
        Do(Activity.LIGHT_BACK,
            b=0.8,
            fade=0.5),
        Do(Activity.LIGHT_BACK,
            w=1.0,
            fade=0.5)        
        ),
    Chapter(
        Do(Activity.PLAY_SOUND,
            sound=fs_names.StoryFile('16')),
        Do(Activity.LIGHT_BACK,
            fade=2.0),
    )
)