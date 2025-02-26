import sys
import time
import threading

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

# Global variables for input handling
keyboard_input = None
input_ready = threading.Event()
phone_on_hook = True  # Track the state of the phone hook

def poll_gpio():
    """Checks for a key press on the physical keypad."""
    if not GPIO_AVAILABLE:
        return None
        
    for col_index, col in enumerate(COLS):
        GPIO.output(col, GPIO.LOW)
        for row_index, row in enumerate(ROWS):
            if GPIO.input(row) == GPIO.LOW:
                GPIO.output(col, GPIO.HIGH)
                return KEYPAD_MAPPING[row_index][col_index]
        GPIO.output(col, GPIO.HIGH)
    return None

def keyboard_input_thread():
    """Thread function to handle keyboard input."""
    global keyboard_input
    keyboard_input = input("").strip()
    input_ready.set()

def check_hook_state():
    """Checks and updates the phone hook state, returns True if state changed."""
    global phone_on_hook
    
    if not GPIO_AVAILABLE:
        return False  # No state change in simulation mode
    
    # Phone lifted off the hook (switch pressed)
    if GPIO.input(SWITCH_PIN) == GPIO.LOW and phone_on_hook:
        print("Phone lifted off the hook")
        phone_on_hook = False
        return True
    
    # Phone placed back on the hook
    elif GPIO.input(SWITCH_PIN) == GPIO.HIGH and not phone_on_hook:
        print("Phone placed back on the hook")
        phone_on_hook = True
        return True
        
    return False  # No state change

def is_phone_lifted():
    """Returns True if the phone is off the hook."""
    global phone_on_hook
    
    if GPIO_AVAILABLE:
        # Update the state first to ensure accuracy
        check_hook_state()
        return not phone_on_hook
    else:
        return True  # Assume phone is lifted for PC testing

def wait_for_keypress(buffer=None):
    """
    Waits for a key press from either the GPIO keypad or keyboard.
    Supports a buffer for multi-digit inputs.
    
    Args:
        buffer: Optional string buffer for multi-digit inputs
    """
    global keyboard_input
    
    if buffer:
        print(f"Current buffer: {buffer}")
    
    if GPIO_AVAILABLE:
        # Check if there's something in the buffer first
        if buffer:
            result = buffer
            return result
            
        # Poll the GPIO keypad
        while True:
            # Check hook state first
            if check_hook_state() and not is_phone_lifted():
                return None  # Return None if phone is hung up
                
            key = poll_gpio()
            if key:
                print(f"GPIO Keypad Pressed: {key}")
                time.sleep(0.2)  # Debounce
                return key
                
            # Brief pause to prevent CPU hogging
            time.sleep(0.05)
    else:
        # PC keyboard input
        keyboard_input = None
        input_ready.clear()
        
        # Start input thread
        input_thread = threading.Thread(target=keyboard_input_thread)
        input_thread.daemon = True
        input_thread.start()
        
        # Wait for input with periodic checks for hook status
        while not input_ready.is_set():
            # Simulate checking if phone is on hook
            time.sleep(0.1)
            
        key = keyboard_input
        # Allow for 'h' key to simulate hanging up
        if key and (key.lower() == 'h' or key == ''):
            return 'h'
        return key if key else "1"  # Default to 1 if empty

def wait_for_hook_change(expected_state):
    """Waits for the hook to be lifted or placed back."""
    global phone_on_hook
    
    if GPIO_AVAILABLE:
        # The expected_state argument indicates:
        # True: waiting for phone to be lifted (switch pressed, GPIO.LOW)
        # False: waiting for phone to be placed back (switch released, GPIO.HIGH)
        
        switch_state = GPIO.LOW if expected_state else GPIO.HIGH
        
        while GPIO.input(SWITCH_PIN) != switch_state:
            time.sleep(0.1)
            
        # Update the tracked state
        phone_on_hook = not expected_state
        
        if expected_state:
            print("Phone lifted off the hook")
        else:
            print("Phone placed back on the hook")
    else:
        if not expected_state:
            input("Press Enter to simulate placing the phone back.")
        else:
            input("Press Enter to simulate lifting the phone.")
        
        # Update the tracked state for simulation
        phone_on_hook = not expected_state