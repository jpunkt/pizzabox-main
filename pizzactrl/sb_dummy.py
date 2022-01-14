from pizzactrl import fs_names
from pizzactrl.storyboard import *

STORYBOARD = [
    Chapter(
        Do(Activity.ADVANCE_UP,
           steps=50),
        Do(Activity.LIGHT_BACK,   # Bild 1
           intensity=1.0, fade=1.0),
        Do(Activity.WAIT_FOR_INPUT,
           on_blue=Select(Option.CONTINUE),
           on_red=Select(Option.REPEAT))
    ),
    Chapter(
        Do(Activity.ADVANCE_LEFT,
           steps=100),
        Do(Activity.ADVANCE_UP,
           steps=50),
        Do(Activity.WAIT_FOR_INPUT,
           on_blue=Select(Option.CONTINUE),
           on_red=Select(Option.REPEAT),
           on_yellow=Select(Option.GOTO, chapter=0),
           on_green=Select(Option.QUIT))
    ),
    Chapter(
        Do(Activity.ADVANCE_LEFT,
           steps=-50),
        Do(Activity.ADVANCE_UP,
           steps=-20)
    ),
    Chapter(
        Do(Activity.ADVANCE_LEFT,
           steps=100),
        Do(Activity.ADVANCE_UP,
           steps=50),
        Do(Activity.WAIT_FOR_INPUT,
           on_blue=Select(Option.CONTINUE),
           on_red=Select(Option.REPEAT),
           on_yellow=Select(Option.GOTO, chapter=0),
           on_green=Select(Option.QUIT))
    )
]
