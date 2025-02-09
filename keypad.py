import RPi.GPIO as GPIO
from time import sleep

# GPIO Setup
GPIO.setmode(GPIO.BCM)

# Keypad Configuration
COL_1, COL_2, COL_3 = 3, 10, 8
ROW_1, ROW_2, ROW_3, ROW_4 = 2, 11, 9, 7
columns = [COL_1, COL_2, COL_3]
rows = [ROW_1, ROW_2, ROW_3, ROW_4]

# Hook Switch Configuration
SWITCH_PIN = 23  # Hook switch GPIO pin
GPIO.setup(SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Keypad Mapping
KEYPAD = [
    ["1", "2", "3"],
    ["4", "5", "6"],
    ["7", "8", "9"],
    ["*", "0", "#"]
]

# GPIO Setup
for col in columns:
    GPIO.setup(col, GPIO.OUT)
    GPIO.output(col, GPIO.HIGH)

for row in rows:
    GPIO.setup(row, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def poll_for_press():
    """Detects a keypad button press and returns the corresponding key."""
    for col in columns:
        GPIO.output(col, GPIO.LOW)

        for row in rows:
            if GPIO.input(row) == GPIO.LOW:
                x, y = columns.index(col), rows.index(row)
                GPIO.output(col, GPIO.HIGH)
                return KEYPAD[y][x]  # Return the pressed key

        GPIO.output(col, GPIO.HIGH)
    
    return None  # No key pressed

def wait_for_keypress():
    """Blocks execution until a key is pressed, then returns the key."""
    pressed_key = None
    while pressed_key is None:
        pressed_key = poll_for_press()
        sleep(0.1)
    return pressed_key

def is_phone_lifted():
    """Returns True if the phone is off the hook, False if on the hook."""
    return GPIO.input(SWITCH_PIN) == GPIO.HIGH

def wait_for_hook_change(desired_state):
    """Blocks until the hook switch reaches the desired state (True: lifted, False: placed back)."""
    while GPIO.input(SWITCH_PIN) != desired_state:
        sleep(0.1)
