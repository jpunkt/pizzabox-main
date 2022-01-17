from pizzactrl import fs_names
from pizzactrl.storyboard import *

STORYBOARD = Storyboard(
    Chapter(  # Chapter 0
        Do(Activity.PARALLEL,
           activities = [
                Do(Activity.ADVANCE_UP, steps=30),
                Do(Activity.LIGHT_BACK, r=0, g=0, b=0, w=1.0, fade=1.0),
           ]),
        Do(Activity.WAIT_FOR_INPUT,
           on_blue=Select(Option.CONTINUE),
           on_red=Select(Option.REPEAT)),
        Do(Activity.LIGHT_BACK)         # Fade out
    ),
    Chapter(  # Chapter 1
        Do(Activity.PARALLEL,
           activities = [
                Do(Activity.LIGHT_FRONT, r=1.0, fade=2.0),
                Do(Activity.ADVANCE_LEFT, steps=50),
                Do(Activity.ADVANCE_UP, steps=25)
           ]),
        Do(Activity.WAIT_FOR_INPUT,
           on_blue=Select(Option.CONTINUE),
           on_red=Select(Option.REPEAT),
           on_yellow=Select(Option.GOTO, chapter=0),
           on_green=Select(Option.QUIT)),
        Do(Activity.LIGHT_FRONT)        # Fade out
    ),
    Chapter(  # Chapter 2
        Do(Activity.LIGHT_BACK, b=1., fade=2.0),
        Do(Activity.ADVANCE_LEFT, steps=-50),
        Do(Activity.ADVANCE_UP, steps=-20),
        Do(Activity.LIGHT_BACK)
    ),
    Chapter(  # Chapter 3
        Do(Activity.LIGHT_FRONT, r=1., g=1., fade=2.0),
        Do(Activity.ADVANCE_LEFT, steps=50),
        Do(Activity.ADVANCE_UP, steps=50),
        Do(Activity.LIGHT_FRONT, fade=5.0),
        Do(Activity.WAIT_FOR_INPUT,
           on_blue=Select(Option.CONTINUE),
           on_red=Select(Option.REPEAT),
           on_yellow=Select(Option.GOTO, chapter=0),
           on_green=Select(Option.QUIT))
    )
)
