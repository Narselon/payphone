import sys
import time
import threading
import pygame  # For playing MP3 sounds
import atexit
from threading import Lock

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False  # If running on a PC without GPIO
    from unittest.mock import MagicMock
    GPIO = MagicMock()

if GPIO_AVAILABLE:
    GPIO.setmode(GPIO.BCM)

    # Define GPIO pins
    COLS = [3, 10, 8]
    ROWS = [2, 11, 9, 7]
    SWITCH_PIN = 23  # Hook switch

    # Setup GPIO
    for col in COLS:
        GPIO.setup(col, GPIO.OUT)
        GPIO.output(col, GPIO.HIGH)

    for row in ROWS:
        GPIO.setup(row, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Set up GPIO for the switch with a pull-down resistor
    GPIO.setup(SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    KEYPAD_MAPPING = [
        ["1", "2", "3"],
        ["4", "5", "6"],
        ["7", "8", "9"],
        ["*", "0", "#"]
    ]

# Initialize sound system
pygame.mixer.init()

# Sound configuration
SOUND_DIRECTORY = "sounds/"  # Directory where sound files are stored
KEYPAD_SOUNDS = {
    "1": "key1.mp3",
    "2": "key2.mp3",
    "3": "key3.mp3",
    "4": "key4.mp3",
    "5": "key5.mp3",
    "6": "key6.mp3",
    "7": "key7.mp3",
    "8": "key8.mp3",
    "9": "key9.mp3",
    "0": "key0.mp3",
    "*": "star.mp3",
    "#": "hash.mp3",
    "default": "beep.mp3",  # Default sound if specific key sound is not found
    "r": "ring.mp3",  # Add ring test mapping
}

# Global variables for input handling
keyboard_input = None
input_ready = threading.Event()
phone_on_hook = True  # Track the state of the phone hook
hook_state_changed = threading.Event()
last_keypress_time = 0  # Track the time of the last keypress
KEYPRESS_DELAY = 0.5  # Delay between keypresses in seconds

# Multi-digit input variables
input_buffer = ""
CODE_ENTRY_MODE = False
CODE_TIMEOUT = 3  # Seconds before code entry times out

_input_thread = None
_input_thread_lock = Lock()
_should_stop = False

def keyboard_input_thread():
    global keyboard_input, _should_stop
    
    try:
        while not _should_stop:
            keyboard_input = input().strip().lower()
            if keyboard_input:
                # Handle ring test
                if keyboard_input == 'r':
                    from payphone import payphone
                    payphone.play_ring()
                    continue
                    
                # Handle regular keypad input    
                if len(keyboard_input) == 1:
                    if keyboard_input in KEYPAD_SOUNDS:
                        play_keypad_sound(keyboard_input)
                input_ready.set()
                break
    except (EOFError, KeyboardInterrupt):
        _should_stop = True
