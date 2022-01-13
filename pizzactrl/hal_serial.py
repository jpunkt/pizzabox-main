import logging
import functools
import threading
from time import sleep
from enum import Enum

from typing import Any, List
from scipy.io.wavfile import write as writewav

import sounddevice as sd
import soundfile as sf

import pygame.mixer as mx

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
    
    def init_sounds(self, sounds: List=None):
        """
        Load prerecorded Sounds into memory

        :param hal:
        :param sounds: A list of sound files
        """
        if self.soundcache is None:
            self.soundcache = {}

        if not mx.get_init():
            mx.init()

        if sounds is not None:
            for sound in sounds:
                # Extract data and sampling rate from file
                # data, fs = sf.read(str(sound), dtype='float32')
                # self.soundcache[str(sound)] = (data, fs)
                self.soundcache[str(sound)] = mx.Sound(sound)

    def init_camera(self):
        if self.camera is None:
            self.camera = PiCamera(sensor_mode=5)

    def play_sound(self, sound: str):
        s = self.soundcache.get(sound, mx.Sound(sound))
        s.play()

    def stop_sound(self):
        if mx.get_busy():
            mx.stop()

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
        
        while resp == b'':
            # If serial communication timeout occurs, response is empty.
            # Read again to allow for longer waiting times
            resp = self.serialcon.read_until()

        if not resp.startswith(SerialCommands.RECEIVED.value):
            raise SerialCommunicationError(f'Serial Communication received unexpected response: {resp}')
        
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


def wait_for_input(hal: PizzaHAL,
                   blue_cb: Any = None,
                   red_cb: Any = None,
                   yellow_cb: Any = None,
                   green_cb: Any = None,
                   timeout_cb: Any = None,
                   sound: Any = None,
                   timeout=120, **kwargs):
    """
    Blink leds on buttons. Wait until the user presses a button, then execute
    the appropriate callback. If a callback is not defined, the button is not
    used.
    Optionally plays sound which can be interrupted by user input.

    :param hal: The hardware abstraction object
    :param blue_cb:    Callback for blue button press
    :param red_cb:     Callback for red button press
    :param yellow_cb:  Callback for yellow button press
    :param green_cb:   Callback for green button press
    :param timeout_cb: Callback for no button press
    :param sound:      Name of sound file to play until user presses a button
    :param timeout:    Time to wait before abort. 0 to wait forever
    """
    if timeout is not None:
        timeout *= 1000
    else:
        timeout = 0

    bitmask = (1 if blue_cb else 0) | \
              (2 if red_cb else 0) | \
              (4 if yellow_cb else 0) | \
              (8 if green_cb else 0)

    if sound is not None:
        hal.play_sound(sound)

    resp = hal.send_cmd(SerialCommands.USER_INTERACT, bitmask.to_bytes(1, 'little', signed=False), timeout.to_bytes(4, 'little', signed=False))

    if sound is not None:
        hal.stop_sound()
    
    if len(resp) != 3:
        raise SerialCommunicationError(f'USER_INTERACTION expects 3 bytes, received {resp}')
    
    resp = resp[1]
    if resp == 1:
        blue_cb(**kwargs)
    elif resp == 2:
        red_cb(**kwargs)
    elif resp == 4:
        yellow_cb(**kwargs)
    elif resp == 8:
        green_cb(**kwargs)
    elif timeout_cb is not None:
        timeout_cb(**kwargs)


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
    Play a sound (blocking).

    :param hal: The hardware abstraction object
    :param sound: The sound to be played
    """
    # Extract data and sampling rate from file
    try:
        hal.play_sound(sound)
        while mx.get_busy():
            pass
    except KeyboardInterrupt:
        mx.stop()
        logger.debug('skipped playback')


def record_sound(hal: PizzaHAL, filename: Any, 
                 duration: float,
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
    
    hal.send_cmd(SerialCommands.RECORD, int(duration*1000).to_bytes(4, 'little', signed=False))

    sd.stop()
    
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

