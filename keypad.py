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
hook_state_changed = threading.Event()
last_keypress_time = 0  # Track the time of the last keypress
KEYPRESS_DELAY = 0.5  # Delay between keypresses in seconds

def poll_gpio():
    """Checks for a key press on the physical keypad."""
    if not GPIO_AVAILABLE:
        return None
        
    for col_index, col in enumerate(COLS):
        GPIO.output(col, GPIO.LOW)
        for row_index, row in enumerate(ROWS):
            if GPIO.input(row) == GPIO.LOW:
                GPIO.output(col, GPIO.HIGH)
                time.sleep(0.2)  # Debounce
                return KEYPAD_MAPPING[row_index][col_index]
        GPIO.output(col, GPIO.HIGH)
    return None

def keyboard_input_thread():
    """Thread function to handle keyboard input."""
    global keyboard_input
    keyboard_input = input("").strip()
    input_ready.set()

def hook_monitoring_thread():
    """Thread function to continuously monitor the hook state."""
    global phone_on_hook
    
    if not GPIO_AVAILABLE:
        return
        
    while True:
        # Phone lifted off the hook (switch pressed)
        if GPIO.input(SWITCH_PIN) == GPIO.LOW and phone_on_hook:
            print("Phone lifted off the hook")
            phone_on_hook = False
            hook_state_changed.set()
        
        # Phone placed back on the hook
        elif GPIO.input(SWITCH_PIN) == GPIO.HIGH and not phone_on_hook:
            print("Phone placed back on the hook")
            phone_on_hook = True
            hook_state_changed.set()
            
        time.sleep(0.1)  # Small delay to prevent CPU hogging

def start_hook_monitoring():
    """Starts the hook monitoring thread."""
    if GPIO_AVAILABLE:
        hook_thread = threading.Thread(target=hook_monitoring_thread)
        hook_thread.daemon = True
        hook_thread.start()

def is_phone_lifted():
    """Returns True if the phone is off the hook."""
    global phone_on_hook
    
    if GPIO_AVAILABLE:
        # Read directly from the GPIO pin for immediate status
        return GPIO.input(SWITCH_PIN) == GPIO.LOW
    else:
        # For simulation, provide a way to toggle state with 'h' key
        if keyboard_input and keyboard_input.lower() == 'h':
            phone_on_hook = not phone_on_hook
            print(f"Simulated phone {'lifted' if not phone_on_hook else 'placed back'}")
            return not phone_on_hook
        return not phone_on_hook  # Return the current simulated state

def wait_for_keypress(buffer=None):
    """
    Waits for a key press from either the GPIO keypad or keyboard.
    Supports a buffer for multi-digit inputs.
    
    Args:
        buffer: Optional string buffer for multi-digit inputs
    """
    global keyboard_input, hook_state_changed, phone_on_hook, last_keypress_time
    
    # Check for keypress delay to prevent accidental skipping
    current_time = time.time()
    if current_time - last_keypress_time < KEYPRESS_DELAY:
        time.sleep(KEYPRESS_DELAY - (current_time - last_keypress_time))
    
    if buffer:
        print(f"Current buffer: {buffer}")
    
    # Reset the hook state change event
    hook_state_changed.clear()
    
    if GPIO_AVAILABLE:
        # Check if there's something in the buffer first
        if buffer:
            last_keypress_time = time.time()
            return buffer
            
        # Poll the GPIO keypad until key press or hook state change
        while True:
            # Check if the hook state has changed
            if hook_state_changed.is_set() or not is_phone_lifted():
                return None  # Return None immediately if hook state changed or phone is on hook
                
            key = poll_gpio()
            if key:
                print(f"GPIO Keypad Pressed: {key}")
                last_keypress_time = time.time()
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
        
        # Wait for input with timeout to check for hook changes
        while not input_ready.is_set():
            # Allow simulated hook state changes with 'h' key
            if keyboard_input and keyboard_input.lower() == 'h':
                phone_on_hook = not phone_on_hook
                print(f"Simulated phone {'lifted' if not phone_on_hook else 'placed back'}")
                hook_state_changed.set()
                return None  # Return None to indicate hook state change
                
            # Check if simulated phone is on hook
            if phone_on_hook:
                return None  # Return None if phone is on hook
                
            time.sleep(0.1)
            
        key = keyboard_input
        # Handle empty input
        if not key:
            last_keypress_time = time.time()
            return "1"  # Default to 1 if empty
        
        last_keypress_time = time.time()
        return key

def wait_for_hook_change(expected_state):
    """
    Waits for the hook to change to the expected state.
    expected_state: True to wait for phone to be lifted (off hook)
                    False to wait for phone to be placed back (on hook)
    
    Returns:
        True if the state changed as expected
        False if bypassed by keyboard input
    """
    global phone_on_hook, keyboard_input, input_ready
    
    if GPIO_AVAILABLE:
        # In GPIO mode, continuously monitor until we see the expected state
        target_gpio_state = GPIO.LOW if expected_state else GPIO.HIGH
        
        # Start a keyboard interrupt thread to allow bypassing
        keyboard_input = None
        input_ready.clear()
        
        input_thread = threading.Thread(target=keyboard_input_thread)
        input_thread.daemon = True
        input_thread.start()
        
        while GPIO.input(SWITCH_PIN) != target_gpio_state:
            # Check for keyboard bypass
            if input_ready.is_set():
                print("Keyboard interrupt detected, bypassing hook wait")
                # Update state to match expected since we're bypassing
                phone_on_hook = not expected_state
                return False  # Indicate this was bypassed
                
            time.sleep(0.1)
            
        # Update the global state
        phone_on_hook = not expected_state
        
        if expected_state:
            print("Phone lifted off the hook")
        else:
            print("Phone placed back on the hook")
        
        return True  # Indicate the state changed as expected
    else:
        # For PC simulation, use keyboard input
        message = "Press Enter to simulate lifting the phone" if expected_state else "Press Enter to simulate placing the phone back"
        print(message + " (or type 'skip' to bypass): ")
        
        response = input().strip().lower()
        if response == 'skip':
            # Just update the state and continue
            phone_on_hook = not expected_state
            print(f"Bypassed: Assuming phone {'lifted off' if expected_state else 'placed back on'} the hook")
            return False
        else:
            phone_on_hook = not expected_state
            print(f"Simulated phone {'lifted off' if expected_state else 'placed back on'} the hook")
            return True

# Start the hook monitoring thread when this module is imported
if GPIO_AVAILABLE:
    start_hook_monitoring()