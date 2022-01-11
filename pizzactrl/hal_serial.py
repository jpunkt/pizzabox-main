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

SERIAL_DEV = '/dev/serial0' # Serial port to use
SERIAL_BAUDRATE = 115200    # Serial connection baud rate
SERIAL_CONN_TIMEOUT = 60    # Serial connection read timeout


class SerialCommands(Enum):
    HELLO = b'\x00'
    ALREADY_CONNECTED = b'\x01'
    ERROR = b'\x02'
    RECEIVED = b'\x03'

    MOTOR_H = b'H'
    MOTOR_V = b'V'

    BACKLIGHT = b'B'
    FRONTLIGHT = b'F'

    USER_INTERACT = b'U'

    RESP_BLUE = b'X'
    RESP_RED = b'O'
    RESP_YELLOW = b'Y'
    RESP_GREEN = b'N'
  
    RECORD = b'C'
    REWIND = b'R'

    DEBUG_SCROLL = b'S'
    DEBUG_SENSORS = b'Z'

    EOT = b'\n'


class SerialCommunicationError(Exception):
    pass


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

    def __init__(self, serialdev: str = SERIAL_DEV, baudrate: int = SERIAL_BAUDRATE, timeout: float = SERIAL_CONN_TIMEOUT):
        self.serialcon = serial.Serial(serialdev, baudrate=baudrate, timeout=timeout)

        self.btn_start = Button(gpio_pins.BTN_START)

        self.camera = None
        self.soundcache = {}

        self.connected = False

    def init_connection(self):
        self.serialcon.write(SerialCommands.HELLO.value + SerialCommands.EOT.value)
        resp = self.serialcon.read_until()
        if resp == (SerialCommands.HELLO.value + SerialCommands.EOT.value):
            self.serialcon.write(SerialCommands.ALREADY_CONNECTED.value + SerialCommands.EOT.value)
            resp = self.serialcon.read_until()
            if resp == (SerialCommands.ALREADY_CONNECTED.value + SerialCommands.EOT.value):
                logger.info('Serial Connection established')
            elif resp == b'':
                raise SerialCommunicationError('Timeout on initializing connection.')
            else:
                raise SerialCommunicationError(f'Serial Connection received invalid response to ALREADY CONNECTED: {resp}')
        elif resp == (SerialCommands.ALREADY_CONNECTED.value + SerialCommands.EOT.value):
            logger.warn('Serial Connection received ALREADY CONNECTED as response to HELLO. Assuming connection ok.')
        elif resp == b'':
            raise SerialCommunicationError('Timeout on initializing connection.')
        else:
            raise SerialCommunicationError(f'Serial Connection received invalid response to HELLO: {resp}')
        self.connected = True

    def send_cmd(self, command: SerialCommands, *options):
        """
        Send a command and optional options. Options need to be encoded as bytes before passing.
        """
        if not self.connected:
            raise SerialCommunicationError("Serial Communication not initialized. Call `init_connection()` before `send_cmd()`.")
        self.serialcon.write(command.value)
        for o in options:
            self.serialcon.write(o)
        self.serialcon.write(SerialCommands.EOT.value)   
        resp = self.serialcon.read_until()
        # TODO handle errors in response
        return resp


def move_vert(hal: PizzaHAL, steps: int):
    """
    Move the motor controlling the vertical scroll a given distance.

    """
    hal.send_cmd(SerialCommands.MOTOR_V, steps.to_bytes(2, 'little', signed=True))


def move_hor(hal: PizzaHAL, steps: int):
    """
    Move the motor controlling the horizontal scroll a given distance.

    """
    hal.send_cmd(SerialCommands.MOTOR_H, steps.to_bytes(2, 'little', signed=True))


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


def light_layer(hal: PizzaHAL, r: float, g: float, b: float, w: float, fade: float = 0.0, **kwargs):
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
    hal.send_cmd(SerialCommands.FRONTLIGHT, 
                 int(r * 255).to_bytes(1, 'little'),
                 int(g * 255).to_bytes(1, 'little'),
                 int(b * 255).to_bytes(1, 'little'),
                 int(w * 255).to_bytes(1, 'little'), 
                 int(fade * 1000).to_bytes(4, 'little'))


def backlight(hal: PizzaHAL, r: float, g: float, b: float, w: float, fade: float = 0.0, **kwargs):
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
    hal.send_cmd(SerialCommands.BACKLIGHT, 
                 int(r * 255).to_bytes(1, 'little'),
                 int(g * 255).to_bytes(1, 'little'),
                 int(b * 255).to_bytes(1, 'little'),
                 int(w * 255).to_bytes(1, 'little'), 
                 int(fade * 1000).to_bytes(4, 'little'))


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


def record_sound(hal: PizzaHAL, filename: Any, duration: float,
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
    resp = hal.send_cmd(SerialCommands.RECORD, int(duration)).strip()
    if resp == b'I':
        sd.stop()
    else:
        sd.wait()  # Wait until recording is finished
    writewav(str(filename), AUDIO_REC_SR, myrecording)
    if cache:
        hal.soundcache[str(filename)] = (myrecording, AUDIO_REC_SR)


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


def take_photo(hal: PizzaHAL, filename: Any, **kwargs):
    """
    Take a foto with the camera

    :param hal: The hardware abstraction object
    :param filename: The path of the filename for the foto
    """
    hal.camera.resolution = PHOTO_RES
    hal.camera.capture(str(filename))


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


def init_camera(hal: PizzaHAL):
    if hal.camera is None:
        hal.camera = PiCamera(sensor_mode=5)
