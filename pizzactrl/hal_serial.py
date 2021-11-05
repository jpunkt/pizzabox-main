import logging
import functools
from time import sleep
from enum import Enum

from typing import Any, List
from scipy.io.wavfile import write as writewav

import sounddevice as sd
import soundfile as sf

from . import gpio_pins

from picamera import PiCamera
from gpiozero import Button

import serial

logger = logging.getLogger(__name__)


# Constants
VIDEO_RES = (1920, 1080)  # Video Resolution
PHOTO_RES = (2592, 1944)  # Photo Resolution
AUDIO_REC_SR = 44100      # Audio Recording Samplerate
SERIAL_DEV = '/dev/serial0'
SERIAL_BAUDRATE = 9600


class SerialCommands(Enum):
    MOTOR_VERT = 'V'
    MOTOR_HOR = 'H'
    BACKLIGHT = 'B'
    FRONTLIGHT = 'F'
    USER_INTERACTION = 'U'
    RECORD = 'C'
    REWIND = 'R'


class PizzaHAL:
    """
    This class holds a represenation of the pizza box hardware and provides
    methods to interact with it.

    - lights upper/lower on/off
    - motor up-down/left-right speed distance
    - scroll up-down/left-right positions
    - lid open/closed detectors
    - user interface buttons

    """

    def __init__(self, serialdev: str = SERIAL_DEV, baudrate: int = SERIAL_BAUDRATE):
        self.serialcon = serial.Serial(serialdev, baudrate=baudrate, timeout=None)

        self.btn_start = Button(gpio_pins.BTN_START)

        self.camera = None
        self.soundcache = {}

        self.blocked = False

    def send_cmd(self, command: SerialCommands, *options):
        self.blocked = True
        opt_str = '+'.join(str(x) for x in options)
        cmd_str = f'{command.value}:{opt_str}\n'
        self.serialcon.write(cmd_str.encode('utf-8'))
        resp = self.serialcon.readline()
        self.blocked = False
        return resp


def blocking(func):
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        hal = kwargs.get('hal', None)
        if hal is not None:
            logger.debug('blocking...')
            while hal.blocked:
                pass
            hal.blocked = True
        func(*args, **kwargs)
        if hal is not None:
            logger.debug('unblocking')
            hal.blocked = False
        sleep(0.1)
    return _wrapper


@blocking
def move_vert(hal: PizzaHAL, steps: int):
    """
    Move the motor controlling the vertical scroll a given distance.

    """
    hal.send_cmd(SerialCommands.MOTOR_VERT, steps)


def move_hor(hal: PizzaHAL, steps: int):
    """
    Move the motor controlling the horizontal scroll a given distance.

    """
    hal.send_cmd(SerialCommands.MOTOR_HOR, steps)


@blocking
def rewind(hal: PizzaHAL):
    """
    Rewind both scrolls.

    """
    hal.send_cmd(SerialCommands.REWIND)


def turn_off(hal: PizzaHAL):
    """
    Turn off everything.
    """
    hal.send_cmd(SerialCommands.BACKLIGHT, 0)
    hal.send_cmd(SerialCommands.FRONTLIGHT, 0)


def wait_for_input(hal: PizzaHAL, go_callback: Any,
                   back_callback: Any, to_callback: Any,
                   timeout=120, **kwargs):
    """
    Blink leds on buttons. Wait until the user presses a button, then execute
    the appropriate callback

    :param hal: The hardware abstraction object
    :param go_callback: called when button 'go' is pressed
    :param back_callback: called whan button 'back' is pressed
    :param to_callback: called on timeout
    :param timeout: inactivity timeout in seconds (default 120)
    """
    resp = hal.send_cmd(SerialCommands.USER_INTERACTION, timeout).strip()
    if resp == b'B':
        go_callback(**kwargs)
    elif resp == b'R':
        back_callback(**kwargs)
    else:
        to_callback(**kwargs)


@blocking
def light_layer(hal: PizzaHAL, intensity: float, fade: float = 0.0, steps: int = 100, **kwargs):
    """
    Turn on the light to illuminate the upper scroll

    :param hal: The hardware abstraction object
    :param fade: float
                Default 0, time in seconds to fade in or out
    :param intensity: float
                Intensity of the light in percent
    :param steps: int
                How many steps for the fade (default: 100)
    """
    hal.send_cmd(SerialCommands.FRONTLIGHT, int(intensity * 100), int(fade * 1000), steps)


@blocking
def backlight(hal: PizzaHAL, intensity: float, fade: float = 0.0,
              steps: int = 100, **kwargs):
    """
    Turn on the backlight

    :param hal: The hardware abstraction object
    :param fade: float
                Default 0, time in seconds to fade in or out
    :param intensity: float
                Intensity of the light in percent
    :param steps: int
                How many steps for the fade (default: 100)
    """
    hal.send_cmd(SerialCommands.BACKLIGHT, int(intensity * 100), int(fade * 1000), steps)

@blocking
def play_sound(hal: PizzaHAL, sound: Any, **kwargs):
    """
    Play a sound.

    :param hal: The hardware abstraction object
    :param sound: The sound to be played
    """
    # Extract data and sampling rate from file
    try:
        data, fs = hal.soundcache.get(str(sound), sf.read(str(sound), dtype='float32'))
        sd.play(data, fs)
        sd.wait()  # Wait until file is done playing
    except KeyboardInterrupt:
        logger.debug('skipped playback')
        # sd.stop()


@blocking
def record_sound(hal: PizzaHAL, filename: Any, duration: int,
                 cache: bool = False, **kwargs):
    """
    Record sound using the microphone

    :param hal: The hardware abstraction object
    :param filename: The path of the file to record to
    :param duration: The time to record in seconds
    :param cache: `True` to save recording to cache. Default is `False`
    """
    myrecording = sd.rec(int(duration * AUDIO_REC_SR),
                         samplerate=AUDIO_REC_SR,
                         channels=2)
    resp = hal.send_cmd(SerialCommands.RECORD, duration).strip()
    if resp == b'I':
        sd.stop()
    else:
        sd.wait()  # Wait until recording is finished
    writewav(str(filename), AUDIO_REC_SR, myrecording)
    if cache:
        hal.soundcache[str(filename)] = (myrecording, AUDIO_REC_SR)


@blocking
def record_video(hal: PizzaHAL, filename: Any, duration: float, **kwargs):
    """
    Record video using the camera

    :param hal: The hardware abstraction object
    :param filename: The path of the file to record to
    :param duration: The time to record in seconds
    """
    hal.camera.resolution = VIDEO_RES
    hal.camera.start_recording(str(filename))
    hal.camera.wait_recording(duration)
    hal.camera.stop_recording()


@blocking
def take_photo(hal: PizzaHAL, filename: Any, **kwargs):
    """
    Take a foto with the camera

    :param hal: The hardware abstraction object
    :param filename: The path of the filename for the foto
    """
    hal.camera.resolution = PHOTO_RES
    hal.camera.capture(str(filename))


@blocking
def init_sounds(hal: PizzaHAL, sounds: List):
    """
    Load prerecorded Sounds into memory

    :param hal:
    :param sounds: A list of sound files
    """
    if hal.soundcache is None:
        hal.soundcache = {}

    for sound in sounds:
        # Extract data and sampling rate from file
        data, fs = sf.read(str(sound), dtype='float32')
        hal.soundcache[str(sound)] = (data, fs)


@blocking
def init_camera(hal: PizzaHAL):
    if hal.camera is None:
        hal.camera = PiCamera(sensor_mode=5)
