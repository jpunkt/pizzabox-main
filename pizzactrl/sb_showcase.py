from fileinput import filename
from pizzactrl import fs_names
from pizzactrl.storyboard import *

REC_NAME = fs_names.RecFile('name.wav')
REC_CITY = fs_names.RecFile('cityname.wav')
REC_CITY_DESC = fs_names.RecFile('city-desc.wav')
REC_CITY_SOUND = fs_names.RecFile('city-sound.wav')
REC_CITY_VIDEO = fs_names.RecFile('city.h264')

Do_FADE_BLACK = Do(Activity.PARALLEL,
                activities=[
                    Do(Activity.LIGHT_BACK,
                        fade=1.0),
                    Do(Activity.LIGHT_FRONT,
                        fade=1.0)
                ])

Chapter_GOTO_MAIN_MENU =Chapter(
                            Do(Activity.GOTO,
                                chapter=2),
                        skip_flag=True)

Chapter_GOTO_CITY_MENU =Chapter(
                            Do(Activity.GOTO,
                                chapter=4),
                        skip_flag=True)

Chapter_GOTO_ACTIVITY_MENU =Chapter(
                            Do(Activity.GOTO,
                                chapter=13),
                        skip_flag=True)

STORYBOARD = Storyboard(
    Chapter(    # X1 = 0
        Do(Activity.PARALLEL,
        activities=[
            Do(Activity.LIGHT_FRONT,
                w=1.0,
                fade=1.0),
            Do(Activity.LIGHT_BACK,
                fade=0)
        ]),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE01'),
            EN=fs_names.StoryFile('EN01')),
        Do(Activity.PARALLEL,
        activities=[
            Do(Activity.LIGHT_FRONT,
                fade=3.0),
            Do(Activity.LIGHT_BACK,
                w=1.0,
                fade=3.0)
        ]),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE02'),
            EN=fs_names.StoryFile('EN02')),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.SFX_REC_AUDIO),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE03'),
            EN=fs_names.StoryFile('EN03')),
        Do(Activity.WAIT_FOR_INPUT,
            on_red=Select(Option.REPEAT),
            on_green=Select(Option.CONTINUE),
            DE=fs_names.StoryFile('DE04'),
            EN=fs_names.StoryFile('EN04')),
        Do_FADE_BLACK
    ),
    Chapter(    # X1.1 = 1
        Do(Activity.PLAY_SOUND,
            sound=fs_names.SFX_REC_AUDIO),
        Do(Activity.RECORD_SOUND,
            filename=REC_NAME,
            duration=5.0,
            cache=True),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.SFX_STOP_REC),
    ),
    Chapter(    # X2 = 2
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE05'),
            EN=fs_names.StoryFile('EN05')),
        Do(Activity.PLAY_SOUND,
            sound=REC_NAME),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE06'),
            EN=fs_names.StoryFile('EN06')),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE07'),
            EN=fs_names.StoryFile('EN07')),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE08'),
            EN=fs_names.StoryFile('EN08')),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE09'),
            EN=fs_names.StoryFile('EN09')),
        Do(Activity.WAIT_FOR_INPUT,
            on_blue=Select(Option.CONTINUE),    # X3
            on_red=Select(Option.GOTO,          # X9 TODO set chapter number
                         chapter=10),
            on_green=Select(Option.GOTO,        # X14 TODO set chapter number
                         chapter=14),
            on_yellow=Select(Option.CONTINUE,
                         skip_flag=True),       # TODO test!
            on_timeout=Select(Option.REPEAT),
            DE=fs_names.StoryFile('DE10'),
            EN=fs_names.StoryFile('EN10'),
            timeout=12)
    ),
    Chapter(    # X3 = 3
        Do(Activity.PARALLEL,
        activities=[
            Do(Activity.LIGHT_BACK,
                fade=0),
            Do(Activity.LIGHT_FRONT,
                w=1.0,
                fade=2.0),
            Do(Activity.ADVANCE_UP,
                steps=84)
        ]),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE11'),
            EN=fs_names.StoryFile('EN11')),
        Do(Activity.ADVANCE_UP,
            steps=42,
            speed=2),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE12'),
            EN=fs_names.StoryFile('EN12')),
        Do(Activity.PARALLEL,
        activities=[
            Do(Activity.LIGHT_BACK,
                w=1.0,
                fade=1.0),
            Do(Activity.LIGHT_FRONT,
                fade=1.0),
            Do(Activity.ADVANCE_LEFT,
                steps=90)
        ]),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE13'),
            EN=fs_names.StoryFile('EN13')),
        Do(Activity.ADVANCE_UP,
            speed=2),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE14'),
            EN=fs_names.StoryFile('EN14')),
        Do_FADE_BLACK
    ),
    Chapter(    # X3.1 = 4
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE15'),
            EN=fs_names.StoryFile('EN15')),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE16'),
            EN=fs_names.StoryFile('EN16')),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE17'),
            EN=fs_names.StoryFile('EN17')),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE18'),
            EN=fs_names.StoryFile('EN18')),
        Do(Activity.WAIT_FOR_INPUT,
            on_blue=    Select(Option.CONTINUE),  # X4
            on_red=     Select(Option.GOTO,       # X5
                         chapter=7),    
            on_green=   Select(Option.GOTO,       # X6
                         chapter=9),
            on_yellow=  Select(Option.GOTO,       # X2 (main menu)
                         chapter=2),
            on_timeout=Select(Option.REPEAT),
            DE=fs_names.StoryFile('DE19'),
            EN=fs_names.StoryFile('EN19'),
            timeout=12),
    skip_flag=True),
    Chapter(    # X4 = 5
        Do(Activity.PARALLEL,
        activities=[
            Do(Activity.LIGHT_BACK,
                fade=0),
            Do(Activity.LIGHT_FRONT,
                w=1.0,
                fade=2.0),
            Do(Activity.ADVANCE_UP)
        ]),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE20'),
            EN=fs_names.StoryFile('EN20')),
        Do(Activity.PARALLEL,
        activities=[
            Do(Activity.LIGHT_BACK,
                w=1.0,
                fade=2.0),
            Do(Activity.LIGHT_FRONT,
                fade=2.0),
            Do(Activity.ADVANCE_LEFT)
        ]),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE21'),
            EN=fs_names.StoryFile('EN21')),
        Do_FADE_BLACK
    ),
    Chapter_GOTO_CITY_MENU,    # X4.1 = 6
    Chapter(    # X5 = 7
        Do(Activity.PARALLEL,
        activities=[
            Do(Activity.LIGHT_BACK,
                w=1.0,
                fade=3.0),
            Do(Activity.LIGHT_FRONT,
                fade=1.0),
            Do(Activity.ADVANCE_UP),    # TODO Vert07, Hor04
            Do(Activity.ADVANCE_LEFT)
        ]),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE22'),
            EN=fs_names.StoryFile('EN22')),
        Do(Activity.PARALLEL,
        activities=[
            Do(Activity.LIGHT_BACK,
                fade=1.0),
            Do(Activity.LIGHT_FRONT,
                w=1.0,
                fade=1.0),
            Do(Activity.ADVANCE_UP,     # TODO Vert06
                steps=-48,
                speed=3)
        ]),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE23'),
            EN=fs_names.StoryFile('EN23')),
        Do_FADE_BLACK
    ),
    Chapter_GOTO_CITY_MENU,    # X5.1 = 8
    Chapter(    # X6 = 9
        Do(Activity.PARALLEL,
        activities=[
            Do(Activity.LIGHT_BACK,
                w=1.0,
                fade=3.0),
            Do(Activity.LIGHT_FRONT,
                fade=1.0),
            Do(Activity.ADVANCE_UP,
                speed=2),    # TODO Vert07, Hor05
            Do(Activity.ADVANCE_LEFT,
                speed=3)
        ]),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE24'),
            EN=fs_names.StoryFile('EN24')),
        Do(Activity.PARALLEL,
        activities=[
            Do(Activity.LIGHT_BACK,
                fade=1.0),
            Do(Activity.LIGHT_FRONT,
                w=1.0,
                fade=1.0),
            Do(Activity.ADVANCE_UP,
                speed=2),    # TODO Vert08
        ]),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE25'),
            EN=fs_names.StoryFile('EN25')),
        Do_FADE_BLACK
    ),
    Chapter_GOTO_CITY_MENU,     # X6.1 = 10
    Chapter(    # X7 = 11
        Do(Activity.PARALLEL,
        activities=[
            Do(Activity.LIGHT_BACK,
                fade=1.0),
            Do(Activity.LIGHT_FRONT,
                w=1.0,
                fade=1.0),
            Do(Activity.ADVANCE_UP,
                speed=3),    # TODO Vert09
        ]),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE26'),
            EN=fs_names.StoryFile('EN26')),
        Do(Activity.ADVANCE_UP,
            speed=3),    # TODO Vert10
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE27'),
            EN=fs_names.StoryFile('EN27')),
        Do(Activity.WAIT_FOR_INPUT,
            on_red=     Select(Option.REPEAT),    
            on_green=   Select(Option.CONTINUE),
            on_timeout= Select(Option.QUIT),
            timeout=60),
    ),
    Chapter(    # X7.1 = 12
        Do(Activity.PLAY_SOUND,
            sound=fs_names.SFX_REC_AUDIO),
        Do(Activity.RECORD_SOUND,
            filename=REC_CITY,
            duration=5.0,
            cache=True),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.SFX_STOP_REC),
    ),
    Chapter(    # X8 = 13
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE28'),
            EN=fs_names.StoryFile('EN28')),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE29'),
            EN=fs_names.StoryFile('EN29')),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE30'),
            EN=fs_names.StoryFile('EN30')),
        Do(Activity.WAIT_FOR_INPUT,
            on_blue=    Select(Option.CONTINUE),  # X9
            on_red=     Select(Option.GOTO,       # X10
                         chapter=16),    
            on_green=   Select(Option.GOTO,       # X11
                         chapter=20),
            on_yellow=  Select(Option.GOTO,       # X2 (main menu)
                         chapter=2),
            on_timeout=Select(Option.REPEAT),
            DE=fs_names.StoryFile('DE31'),
            EN=fs_names.StoryFile('EN31'),
            timeout=12),
    skip_flag=True),
    Chapter(    # X9 = 14
        Do(Activity.ADVANCE_LEFT),    # TODO Hor06
        Do(Activity.LIGHT_BACK,
            w=1.0,
            fade=1.0),
        Do(Activity.ADVANCE_UP,       # TODO Vert11
            speed=2),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE32'),
            EN=fs_names.StoryFile('EN32')),
        Do(Activity.WAIT_FOR_INPUT,
            on_red=     Select(Option.REPEAT),    
            on_green=   Select(Option.CONTINUE),
            on_timeout=Select(Option.QUIT),
            DE=fs_names.StoryFile('DE33'),
            EN=fs_names.StoryFile('EN33'),
            timeout=60),
        Do_FADE_BLACK
    ),
    Chapter(    # X9.1 = 15
        Do(Activity.PLAY_SOUND,
            sound=fs_names.SFX_REC_AUDIO),
        Do(Activity.RECORD_SOUND,
            filename=REC_CITY_DESC,
            duration=60),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.SFX_STOP_REC),
    ),
    Chapter_GOTO_ACTIVITY_MENU, # X9.2 = 16
    Chapter(    # X10 = 17
        Do(Activity.PARALLEL,
        activities=[
            Do(Activity.LIGHT_BACK,
                w=1.0,
                fade=3.0),
            Do(Activity.LIGHT_FRONT,
                fade=0),
            Do(Activity.ADVANCE_UP,
                speed=3),    # TODO Vert12
        ]),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE34'),
            EN=fs_names.StoryFile('EN34')),
        Do(Activity.WAIT_FOR_INPUT,
            on_red=     Select(Option.REPEAT),    
            on_green=   Select(Option.CONTINUE),
            on_timeout=Select(Option.QUIT),
            DE=fs_names.StoryFile('DE35'),
            EN=fs_names.StoryFile('EN35'),
            timeout=60),
        Do_FADE_BLACK
    ),
    Chapter(    # X10.1 = 18
        Do(Activity.PLAY_SOUND,
            sound=fs_names.SFX_REC_AUDIO),
        Do(Activity.RECORD_SOUND,
            filename=REC_CITY_SOUND,
            duration=60),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.SFX_STOP_REC),
    ),
    Chapter_GOTO_ACTIVITY_MENU, # X10.2 = 19
    Chapter(    # X11 = 20
        Do(Activity.PARALLEL,
        activities=[
            Do(Activity.LIGHT_BACK,
                w=1.0,
                fade=3.0),
            Do(Activity.LIGHT_FRONT,
                fade=0),
            Do(Activity.ADVANCE_UP,
                speed=3),    # TODO Vert13
        ]),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE36'),
            EN=fs_names.StoryFile('EN36')),
        Do(Activity.ADVANCE_UP),    # TODO Vert14
        Do(Activity.WAIT_FOR_INPUT,
            on_red=     Select(Option.REPEAT),    
            on_green=   Select(Option.CONTINUE),
            on_timeout=Select(Option.QUIT),
            DE=fs_names.StoryFile('DE38'),
            EN=fs_names.StoryFile('EN38'),
            timeout=60),
        Do_FADE_BLACK
    ),
    Chapter(    # X11.1 = 21
        Do(Activity.PLAY_SOUND,
            sound=fs_names.SFX_REC_AUDIO),
        Do(Activity.RECORD_VIDEO,
            filename=REC_CITY_VIDEO,
            duration=70),
        Do(Activity.PLAY_SOUND,
            sound=fs_names.SFX_STOP_REC),
    ),
    Chapter(    # X12 = 22
        Do(Activity.PARALLEL,
        activities=[
            Do(Activity.LIGHT_BACK,
                fade=0),
            Do(Activity.LIGHT_FRONT,
                w=1.0,
                fade=3.0),
            Do(Activity.ADVANCE_UP,
                speed=3),    # TODO Vert15
        ]),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE39'),
            EN=fs_names.StoryFile('EN39')),
        Do(Activity.PLAY_SOUND,
            sound=REC_NAME),
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE40'),
            EN=fs_names.StoryFile('EN40')),
        Do_FADE_BLACK,
    ),
    Chapter_GOTO_MAIN_MENU,     # X12.1 = 23
    Chapter(    # X13 = 24
        Do(Activity.PLAY_SOUND,
            DE=fs_names.StoryFile('DE41'),
            EN=fs_names.StoryFile('EN41')),
        Do(Activity.PLAY_SOUND,
                DE=fs_names.StoryFile('DE42'),
                EN=fs_names.StoryFile('EN42')),
        Do(Activity.PLAY_SOUND,
                DE=fs_names.StoryFile('DE43'),
                EN=fs_names.StoryFile('EN43')),
        Do(Activity.PLAY_SOUND,
                DE=fs_names.StoryFile('DE44'),
                EN=fs_names.StoryFile('EN44')),
        Do(Activity.WAIT_FOR_INPUT,
                on_blue=    Select(Option.CONTINUE),  # X14
                on_red=     Select(Option.GOTO,       # X15
                            chapter=16),    
                on_green=   Select(Option.GOTO,       # X16
                            chapter=20),
                on_yellow=  Select(Option.GOTO,       # X17
                            chapter=2),
                on_timeout=Select(Option.REPEAT),
                DE=fs_names.StoryFile('DE45'),
                EN=fs_names.StoryFile('EN45'),
                timeout=12),
    skip_flag=True),
    Chapter(    # X14 = 25
        Do(Activity.LIGHT_FRONT,
            w=1.0,
            fade=1.0),
        Do(Activity.ADVANCE_UP,
            steps=84,
            speed=2),
        Do_FADE_BLACK
    ),
    Chapter(    # X14.1 = 26
        Do(Activity.WAIT_FOR_INPUT,
                on_red=     Select(Option.GOTO,       # X14
                            chapter=25),    
                on_green=   Select(Option.CONTINUE),  # X15
                on_yellow=  Select(Option.GOTO,       # X2
                            chapter=2),
                on_timeout=Select(Option.REPEAT),
                DE=fs_names.StoryFile('DE46'),
                EN=fs_names.StoryFile('EN46'),
                timeout=20),
    ),
    Chapter(    # X15 = 27
        Do(Activity.ADVANCE_UP),
        Do(Activity.LIGHT_FRONT,
            r=1.0),
        Do(Activity.LIGHT_BACK,
            fade=0.3),
        Do(Activity.LIGHT_FRONT,
            g=1.0),
        Do(Activity.LIGHT_BACK,
            fade=0.3),
        Do(Activity.LIGHT_FRONT,
            b=1.0),
        Do(Activity.LIGHT_BACK,
            fade=0.3),
        Do(Activity.LIGHT_FRONT,
            r=1.0),
        Do(Activity.LIGHT_BACK,
            fade=0.3),
        Do(Activity.LIGHT_FRONT,
            g=1.0),
        Do(Activity.LIGHT_BACK,
            fade=0.3),
        Do(Activity.LIGHT_FRONT,
            b=1.0),
        Do(Activity.LIGHT_BACK,
            fade=0.3),
        Do(Activity.LIGHT_FRONT,
            r=1.0),
        Do(Activity.LIGHT_BACK,
            fade=0.3),
        Do(Activity.LIGHT_FRONT,
            g=1.0),
        Do(Activity.LIGHT_BACK,
            fade=0.3),
        Do(Activity.LIGHT_FRONT,
            b=1.0),
        Do(Activity.LIGHT_BACK,
            fade=0.3),
        Do(Activity.LIGHT_FRONT,
            r=1.0),
        Do(Activity.LIGHT_BACK,
            fade=0.3),
        Do(Activity.LIGHT_FRONT,
            g=1.0),
        Do(Activity.LIGHT_BACK,
            fade=0.3),
        Do(Activity.LIGHT_FRONT,
            b=1.0),
        Do(Activity.LIGHT_BACK,
            fade=0.3),
        Do_FADE_BLACK
    ),
    Chapter(    # X15.1 = 28
        Do(Activity.WAIT_FOR_INPUT,
                on_red=     Select(Option.GOTO,       # X15
                            chapter=27),    
                on_green=   Select(Option.CONTINUE),  # X16
                on_yellow=  Select(Option.GOTO,       # X2
                            chapter=2),
                on_timeout=Select(Option.REPEAT),
                DE=fs_names.StoryFile('DE46'),
                EN=fs_names.StoryFile('EN46'),
                timeout=20),
    ),
    Chapter(    # X16 = 29
        Do(Activity.ADVANCE_UP),
        Do(Activity.LIGHT_FRONT,
            r=1.0),
        Do(Activity.LIGHT_BACK,
            fade=1.0),
        Do(Activity.LIGHT_FRONT,
            b=1.0,
            fade=3.0),
        Do(Activity.LIGHT_BACK,
            fade=1.0),
        Do(Activity.LIGHT_FRONT,
            r=1.0,
            fade=3.0),
        Do(Activity.LIGHT_BACK,
            fade=1.0),
        Do_FADE_BLACK,
    ),
    Chapter(    # X16.1 = 30
        Do(Activity.WAIT_FOR_INPUT,
                on_red=     Select(Option.GOTO,       # X16
                            chapter=29),    
                on_green=   Select(Option.CONTINUE),  # X18
                on_yellow=  Select(Option.GOTO,       # X2
                            chapter=2),
                on_timeout=Select(Option.REPEAT),
                DE=fs_names.StoryFile('DE46'),
                EN=fs_names.StoryFile('EN46'),
                timeout=20),
    ),
    Chapter(    # X17 = 31
        Do(Activity.ADVANCE_LEFT),
        Do(Activity.LIGHT_BACK,
            w=1.0,
            fade=1.0),
        Do(Activity.ADVANCE_UP,
            steps=84,
            speed=1)
    ),
    Chapter(    # X17.1 = 32
        Do(Activity.WAIT_FOR_INPUT,
                on_red=     Select(Option.GOTO,       # X17
                            chapter=31),    
                on_green=   Select(Option.GOTO,
                            chapter=25),              # X14
                on_yellow=  Select(Option.GOTO,       # X2
                            chapter=2),
                on_timeout=Select(Option.REPEAT),
                DE=fs_names.StoryFile('DE46'),
                EN=fs_names.StoryFile('EN46'),
                timeout=20),
    )
)