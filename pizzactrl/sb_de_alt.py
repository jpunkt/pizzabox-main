from pizzactrl import storyboard, fs_names


STORYBOARD = [
    storyboard.Chapter(     # X2
        storyboard.Do(storyboard.Activity.ADVANCE_UP)   # Bild 2
    ),
    storyboard.Chapter(     # X3
        storyboard.Do(storyboard.Activity.ADVANCE_UP),  # Bild 3
        storyboard.Do(storyboard.Activity.ADVANCE_UP),  # Bild 4
        storyboard.Do(storyboard.Activity.ADVANCE_UP),  # Bild 5
    ),
    storyboard.Chapter(     # X4
        storyboard.Do(storyboard.Activity.ADVANCE_UP),  # Bild 6
        storyboard.Do(storyboard.Activity.ADVANCE_UP)   # Bild 7
    ),
    storyboard.Chapter(     # X6
        storyboard.Do(storyboard.Activity.ADVANCE_UP),
        storyboard.Do(storyboard.Activity.ADVANCE_UP)   # Bild 9
    ),
    storyboard.Chapter(     # X9
        storyboard.Do(storyboard.Activity.ADVANCE_UP)   # Bild 10
    ),
    storyboard.Chapter(     # X10
        storyboard.Do(storyboard.Activity.ADVANCE_UP),   # Bild 11
        storyboard.Do(storyboard.Activity.ADVANCE_UP)   # Bild 12
    ),
    storyboard.Chapter(     # X12
        storyboard.Do(storyboard.Activity.LIGHT_BACK,
                      intensity=1., fade=.5),
        storyboard.Do(storyboard.Activity.PLAY_SOUND,
                      sound=fs_names.StoryFile('33de')),
        storyboard.Do(storyboard.Activity.WAIT_FOR_INPUT),
        storyboard.Do(storyboard.Activity.ADVANCE_UP)   # Bild 13
    ),
    storyboard.Chapter(     # X13
        storyboard.Do(storyboard.Activity.PLAY_SOUND,
                      sound=fs_names.StoryFile('34de')),
        storyboard.Do(storyboard.Activity.LIGHT_BACK,
                      intensity=0., fade=1.),
        storyboard.Do(storyboard.Activity.WAIT_FOR_INPUT),
        storyboard.Do(storyboard.Activity.PLAY_SOUND,
                      sound=fs_names.SFX_REC_AUDIO),
        storyboard.Do(storyboard.Activity.RECORD_SOUND,
                      filename=fs_names.REC_CITY_NAME,
                      duration=7.0),
        storyboard.Do(storyboard.Activity.PLAY_SOUND,
                      sound=fs_names.SFX_STOP_REC),
        storyboard.Do(storyboard.Activity.ADVANCE_UP)   # Bild 14
    ),
    storyboard.Chapter(     # X14
        storyboard.Do(storyboard.Activity.LIGHT_BACK,
                      intensity=1., fade=1.),
        storyboard.Do(storyboard.Activity.PLAY_SOUND,
                      sound=fs_names.StoryFile('35de')),
        storyboard.Do(storyboard.Activity.WAIT_FOR_INPUT),
        storyboard.Do(storyboard.Activity.PLAY_SOUND,
                      sound=fs_names.SFX_REC_AUDIO),
        storyboard.Do(storyboard.Activity.RECORD_SOUND,
                      filename=fs_names.REC_CITY_DESC,
                      duration=60.0),
        storyboard.Do(storyboard.Activity.PLAY_SOUND,
                      sound=fs_names.SFX_STOP_REC),
        storyboard.Do(storyboard.Activity.ADVANCE_UP)   # Bild 15
    ),
    storyboard.Chapter(     # X15
        storyboard.Do(storyboard.Activity.PLAY_SOUND,
                      sound=fs_names.StoryFile('36de')),
        storyboard.Do(storyboard.Activity.WAIT_FOR_INPUT),
        storyboard.Do(storyboard.Activity.PLAY_SOUND,
                      sound=fs_names.SFX_REC_AUDIO),
        storyboard.Do(storyboard.Activity.RECORD_SOUND,
                      filename=fs_names.REC_CITY_SOUND,
                      duration=60.0),
        storyboard.Do(storyboard.Activity.PLAY_SOUND,
                      sound=fs_names.SFX_STOP_REC),
        storyboard.Do(storyboard.Activity.LIGHT_BACK,
                      intensity=0., fade=1.),
        storyboard.Do(storyboard.Activity.ADVANCE_UP)  # Bild 16
    ),
    storyboard.Chapter(     # X16
        storyboard.Do(storyboard.Activity.PLAY_SOUND,
                      sound=fs_names.StoryFile('37de')),
        storyboard.Do(storyboard.Activity.LIGHT_BACK,
                      intensity=1., fade=1.),
        storyboard.Do(storyboard.Activity.PLAY_SOUND,
                      sound=fs_names.StoryFile('38de')),
        storyboard.Do(storyboard.Activity.ADVANCE_UP)  # Bild 17
    ),
    storyboard.Chapter(     # X17
        storyboard.Do(storyboard.Activity.PLAY_SOUND,
                      sound=fs_names.StoryFile('39de')),
        storyboard.Do(storyboard.Activity.LIGHT_BACK,
                      intensity=0., fade=1.),
        storyboard.Do(storyboard.Activity.WAIT_FOR_INPUT),
        storyboard.Do(storyboard.Activity.PLAY_SOUND,
                      sound=fs_names.SFX_REC_AUDIO),
        storyboard.Do(storyboard.Activity.RECORD_VIDEO,
                      filename=fs_names.REC_DRAW_CITY,
                      duration=60.0),
        storyboard.Do(storyboard.Activity.TAKE_PHOTO,
                      filename=fs_names.REC_CITY_PHOTO),
        storyboard.Do(storyboard.Activity.PLAY_SOUND,
                      sound=fs_names.SFX_STOP_REC),

        storyboard.Do(storyboard.Activity.ADVANCE_UP)  # Bild 18
    ),
    storyboard.Chapter(     # X18
        storyboard.Do(storyboard.Activity.LIGHT_BACK,
                      intensity=1., fade=1.),
        storyboard.Do(storyboard.Activity.PLAY_SOUND,
                      sound=fs_names.StoryFile('40de')),
        storyboard.Do(storyboard.Activity.ADVANCE_UP),  # Bild 19
        storyboard.Do(storyboard.Activity.PLAY_SOUND,
                      sound=fs_names.StoryFile('41de')),
        storyboard.Do(storyboard.Activity.LIGHT_BACK,
                      intensity=0., fade=2.)
    )
]
