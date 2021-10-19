# GPIO pin definitions

BTN_BACK_GPIO = 14                    # "Back" button (user input)
BTN_FORWARD_GPIO = 18                 # "Forward" button (user input)

LED_BACK_BTN = 15                   # LED in back-button
LED_FWD_BTN = 23                    # LED in forward-button

# LID_SWITCH = 18                      # "Lid open" detector switch on front

LED_LAYER = 12                       # LED-strip for top layer
LED_BACKLIGHT = 13                   # LED-strip for backlight

MOTOR_CTRL_LR = (8, 7, 10)        # Motor controller 1 (in1, in2, enable)
MOTOR_CTRL_UPDOWN = (9, 11, 25)   # Motor controller 2 (in1, in2, enable)

SCROLL_UPDOWN_SENSORS = (22, 27)  # Feed/Direction sensors
SCROLL_UPDOWN_ENDSTOP = 20          # End of Tape

SCROLL_LR_SENSORS = (6, 5)         # Feed/Direction sensors
SCROLL_LR_ENDSTOP = 16               # End of Tape
