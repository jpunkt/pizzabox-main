import logging

from time import sleep
from enum import Enum

from typing import Any, List, Iterable
from scipy.io.wavfile import write as writewav

import sounddevice as sd
import soundfile as sf

import pygame.mixer as mx

from picamera import PiCamera
from gpiozero import Button, DigitalOutputDevice, DigitalInputDevice

import serial

from .gpio_pins import *

logger = logging.getLogger(__name__)


# Constants
VIDEO_RES = (1920, 1080)  # Video Resolution
PHOTO_RES = (2592, 1944)  # Photo Resolution
AUDIO_REC_SR = 44100      # Audio Recording Samplerate

SERIAL_DEV = '/dev/serial0' # Serial port to use
SERIAL_BAUDRATE = 115200    # Serial connection baud rate
SERIAL_CONN_TIMEOUT = 0.2     # Serial connection read timeout
HELO_TIMEOUT = 20


class Lights(Enum):
    BACKLIGHT = 0
    FRONTLIGHT = 1


class Scrolls(Enum):
    HORIZONTAL = 0
    VERTICAL = 1


class SerialCommands(Enum):
    HELLO = b'\x00'
    ALREADY_CONNECTED = b'\x01'
    ERROR = b'\x02'
    RECEIVED = b'\x03'
    ABORT = b'\x63'     # 99 decimal

    SET_MOVEMENT = b'M'
    SET_LIGHT = b'L'

    DO_IT = b'D'

    USER_INTERACT = b'U'
    RECORD = b'C'

    REWIND = b'R'

    DEBUG_SCROLL = b'S'
    DEBUG_SENSORS = b'Z'

    EOT = b'\n'


class CommunicationError(Exception):
    pass


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

        # Lid switch with pull-up. is_pressed = True when lid is open
        self.lid_switch = Button(LID_SWITCH)
        self.pin_helo1 = DigitalOutputDevice(HELO1)
        self.pin_helo2 = DigitalInputDevice(HELO2)

        self.camera = None
        self.soundcache = {}

        self.connected = False

    @property
    def lid_open(self) -> bool:
        """
        Returns True when the lid is open
        """
        return self.lid_switch.is_pressed

    def init_connection(self):
        """
        Set HELO1 pin to `High`, wait for HELO2 to be set `High` by microcontroller.
        
        Then perform serial handshake.
        """
        self.pin_helo1.on()
        timer = 0
        while (not self.pin_helo2.value) and (timer < HELO_TIMEOUT):
            sleep(0.1)
            timer += 1
            if not (timer % 100):
                logger.info(f'Waiting for connection ({timer / 10}s)')
        
        if not self.pin_helo2.value:
            raise CommunicationError('Microcontroller did not respond to HELO pin.')

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
                self.soundcache[str(sound)] = mx.Sound(str(sound))

    def init_camera(self):
        if self.camera is None:
            self.camera = PiCamera(sensor_mode=5)

    def play_sound(self, sound: str):
        s = self.soundcache.get(sound, mx.Sound(sound))
        s.play()

    def stop_sound(self):
        if mx.get_busy():
            mx.stop()

    def send_cmd(self, command: SerialCommands, *options, ignore_lid: bool=False):
        """
        Send a command and optional options. Options need to be encoded as bytes before passing.

        This function is blocking.

        Returns the response from the microcontroller or `None` if the lid was closed and `ignore_lid` is `False`.
        
        Raises a SerialCommunicationError if serial connection was not initialized or a response other than
        SerialCommands.RECEIVED was received.
        
        Raises a CommunicationError if the HELO2 pin goes low while waiting for response.
        """
        if not self.connected:
            raise SerialCommunicationError("Serial Communication not initialized. Call `init_connection()` before `send_cmd()`.")

        self.serialcon.write(command.value)
        for o in options:
            self.serialcon.write(o)
        
        self.serialcon.write(SerialCommands.EOT.value)   
        resp = b''
        while resp is b'':
            # If serial communication timeout occurs, response is empty.
            # Read again to allow for longer waiting times
            if not self.pin_helo2.value:
                raise CommunicationError('Pin HELO2 LOW. Microcontroller in error state or lost connection.')
            if (not ignore_lid) and (not self.lid_open):
                logger.info('Lid closed while processing command. Returning None.')
                return None
            resp = self.serialcon.read_until()

        logger.debug(f'hal.send_cmd() received {resp}')

        if not resp.startswith(SerialCommands.RECEIVED.value):
            raise SerialCommunicationError(f'Serial Communication received unexpected response: {resp}')
        
        return resp

    def flush_serial(self):
        self.serialcon.read_all()


def set_movement(hal: PizzaHAL, 
         scroll: Scrolls,
         steps: int,
         speed: int,
         **kwargs):
    """
    Move the motor controlling the vertical scroll a given distance.

    """
    scroll = int(scroll.value)
    hal.send_cmd(SerialCommands.SET_MOVEMENT,
                 scroll.to_bytes(1, 'little', signed=False),
                 steps.to_bytes(2, 'little', signed=True),
                 speed.to_bytes(1, 'little', signed=False))


def rewind(hal: PizzaHAL, **kwargs):
    """
    Rewind both scrolls.

    """
    hal.send_cmd(SerialCommands.REWIND, ignore_lid=True)


def turn_off(hal: PizzaHAL, **kwargs):
    """
    Turn off the lights.
    """
    set_light(hal, Lights.BACKLIGHT, 0, 0, 0, 0, 0, ignore_lid=True)
    set_light(hal, Lights.FRONTLIGHT, 0, 0, 0, 0, 0, ignore_lid=True)
    do_it(hal, ignore_lid=True)


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
        logger.debug(f'Waiting for user, playing sound {sound}.')
        hal.play_sound(str(sound))

    resp = hal.send_cmd(SerialCommands.USER_INTERACT, bitmask.to_bytes(1, 'little', signed=False), timeout.to_bytes(4, 'little', signed=False))

    if sound is not None:
        hal.stop_sound()
    
    if resp is None:
        # lid was closed by user
        logger.info('Lid closed during wait_for_input(). Sending ABORT.')
        hal.send_cmd(SerialCommands.ABORT, ignore_lid=True)
        hal.flush_serial()
        return

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


def set_light(hal: PizzaHAL,
          light: Lights,
          r: float, 
          g: float, 
          b: float, 
          w: float, 
          fade: float = 0.0,
          **kwargs):
    """
    Turn on the light to illuminate the upper scroll

    :param hal: The hardware abstraction object
    :param fade: float
                Default 0, time in seconds to fade in or out
    """
    # convert color to 32bit number
    color = (int(w * 255) << 24) | (int(b * 255) << 16) | (int(g * 255) << 8) | (int(r * 255))

    hal.send_cmd(SerialCommands.SET_LIGHT,
                 int(light.value).to_bytes(1, 'little'), 
                 int(color).to_bytes(4, 'little'), 
                 int(fade * 1000).to_bytes(4, 'little'),
                 ignore_lid=kwargs.get('ignore_lid', False))


def do_it(hal: PizzaHAL, ignore_lid: bool=False, **kwargs):
    """
    Execute set commands
    """
    if hal.send_cmd(SerialCommands.DO_IT, ignore_lid=ignore_lid) is None:
        logger.info('Lid closed during do_it(). Sending ABORT.')
        hal.send_cmd(SerialCommands.ABORT, ignore_lid=True)
        hal.flush_serial()


def play_sound(hal: PizzaHAL, sound: Any, **kwargs):
    """
    Play a sound (blocking).

    :param hal: The hardware abstraction object
    :param sound: The sound to be played
    """
    # Extract data and sampling rate from file
    try:
        hal.play_sound(str(sound))
        while mx.get_busy() and hal.lid_open:
            pass
        if not hal.lid_open:
            hal.stop_sound()

    except KeyboardInterrupt:
        hal.stop_sound()
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

