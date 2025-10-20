import sys
import time
import threading
import pygame  # For playing MP3 sounds
import atexit
from threading import Lock
from threading import Event
import os

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

def play_keypad_sound(key):
    """Play sound associated with keypad press"""
    try:
        # Get sound file name for the key
        sound_file = KEYPAD_SOUNDS.get(key, KEYPAD_SOUNDS["default"])
        sound_path = os.path.join(SOUND_DIRECTORY, sound_file)
        
        if os.path.exists(sound_path):
            sound = pygame.mixer.Sound(sound_path)
            sound.play()
            time.sleep(0.1)  # Short delay to prevent sound overlap
            print(f"Playing sound for key: {key}")
        else:
            print(f"Sound file not found: {sound_path}")
            
    except Exception as e:
        print(f"Error playing keypad sound: {e}")

# Global variables for input handling
keyboard_input = None
input_ready = threading.Event()
phone_on_hook = True  # Track the state of the phone hook
hook_state_changed = threading.Event()
last_keypress_time = 0  # Track the time of the last keypress
last_key_pressed = None  # Track the last key pressed
KEYPRESS_DELAY = 0.3  # Delay between keypresses in seconds (increased debounce)

# Multi-digit input variables
input_buffer = ""
CODE_ENTRY_MODE = False
CODE_TIMEOUT = 3  # Seconds before code entry times out

_input_thread = None
_input_thread_lock = Lock()
_should_stop = False

phone_on_hook = True
hook_state_changed = Event()

def wait_for_hook_change(expected_state):
    """Waits for the hook to change to the expected state."""
    global phone_on_hook, keyboard_input, input_ready
    
    if GPIO_AVAILABLE:
        target_gpio_state = GPIO.LOW if expected_state else GPIO.HIGH
        
        while GPIO.input(SWITCH_PIN) != target_gpio_state:
            if input_ready.is_set():
                print("Keyboard interrupt detected")
                phone_on_hook = not expected_state
                return False
            time.sleep(0.1)
            
        phone_on_hook = not expected_state
        print("Phone " + ("lifted off" if expected_state else "placed back on") + " the hook")
        return True
        
    else:
        # PC simulation code
        message = "Press Enter to simulate lifting the phone" if expected_state else "Press Enter to simulate placing the phone back"
        print(message + " (or type 'skip' to bypass): ")
        
        try:
            response = input().strip().lower()
            if response == 'skip':
                phone_on_hook = not expected_state
                print(f"Bypassed: Assuming phone {'lifted off' if expected_state else 'placed back on'} the hook")
                return False
            else:
                phone_on_hook = not expected_state
                print(f"Simulated phone {'lifted off' if expected_state else 'placed back on'} the hook")
                return True
        except (KeyboardInterrupt, EOFError):
            return False

def is_phone_lifted():
    """Returns True if phone is off hook, False otherwise."""
    global phone_on_hook
    return not phone_on_hook

def keyboard_input_thread():
    """Thread function to handle keyboard input."""
    global keyboard_input, _should_stop, last_keypress_time, last_key_pressed
    
    try:
        while not _should_stop:
            current_time = time.time()
            
            # Check GPIO keypad first if available
            if GPIO_AVAILABLE:
                # Check each column
                for col_num, col_pin in enumerate(COLS):
                    GPIO.output(col_pin, GPIO.LOW)  # Set column low
                    time.sleep(0.01)  # Add delay for GPIO to settle
                    
                    # Check each row
                    for row_num, row_pin in enumerate(ROWS):
                        if GPIO.input(row_pin) == GPIO.LOW:  # Key pressed
                            key = KEYPAD_MAPPING[row_num][col_num]
                            
                            # Debounce check - ignore if same key pressed too quickly
                            if key == last_key_pressed and current_time - last_keypress_time < KEYPRESS_DELAY:
                                GPIO.output(col_pin, GPIO.HIGH)
                                continue
                                
                            keyboard_input = key
                            print(f"Keypad press detected: {keyboard_input}")
                            play_keypad_sound(keyboard_input)
                            input_ready.set()
                            last_keypress_time = current_time
                            last_key_pressed = key
                            
                            # Wait for key release
                            while GPIO.input(row_pin) == GPIO.LOW:
                                time.sleep(0.05)
                            
                            GPIO.output(col_pin, GPIO.HIGH)
                            time.sleep(0.2)  # Delay after key release
                            return  # Exit after handling keypress
                            
                    GPIO.output(col_pin, GPIO.HIGH)
                time.sleep(0.01)
                    
            else:
                # Fallback to keyboard input if no GPIO
                keyboard_input = input().strip().lower()
                if keyboard_input and len(keyboard_input) == 1:
                    if keyboard_input in KEYPAD_SOUNDS:
                        play_keypad_sound(keyboard_input)
                    input_ready.set()
                    break
                    
    except (EOFError, KeyboardInterrupt):
        _should_stop = True

# Add these new functions

def wait_for_single_keypress():
    """Wait for a single keypress and return it."""
    global keyboard_input, input_ready, _input_thread, _should_stop
    
    with _input_thread_lock:
        # Reset states
        keyboard_input = None
        input_ready.clear()
        _should_stop = False
        
        # Start new input thread if needed
        if not _input_thread or not _input_thread.is_alive():
            _input_thread = threading.Thread(target=keyboard_input_thread, daemon=True)
            _input_thread.start()
    
    # Wait for input with periodic hook checks
    while True:
        if input_ready.wait(timeout=0.1):  # Check every 100ms
            return keyboard_input
        # Check if phone has been hung up
        if GPIO_AVAILABLE:
            if GPIO.input(SWITCH_PIN) == GPIO.HIGH:  # Phone is on hook
                return None
        else:
            # For non-GPIO, we can't check hook state continuously
            break
    
    return keyboard_input

def wait_for_keypress():
    """Wait for keypress and handle special inputs."""
    global CODE_ENTRY_MODE, input_buffer
    
    while True:
        key = wait_for_single_keypress()
        
        # Handle None/invalid input
        if key is None:
            return None
            
        # Handle code entry mode
        if CODE_ENTRY_MODE:
            if key == '#':
                # End code entry
                CODE_ENTRY_MODE = False
                code = input_buffer
                input_buffer = ""
                print(f"Code entry complete: {code}")
                return code
            elif key == '*':
                # Cancel code entry
                print("Code entry cancelled")
                CODE_ENTRY_MODE = False
                input_buffer = ""
                continue
            else:
                # Add to code buffer
                input_buffer += key
                print(f"Code buffer: {input_buffer}")
                continue
                
        # Not in code entry mode
        # Start code entry mode
        if key == '*':
            print("Starting code entry mode")
            CODE_ENTRY_MODE = True
            input_buffer = ""
            continue
            
        return key