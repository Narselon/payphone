import RPi.GPIO as GPIO
from datetime import datetime, time as datetime_time  # Rename to avoid conflict
import random
import threading
import pygame
import os
import time  # Add this import
from keypad import GPIO_AVAILABLE
import keyboard  # Add this import at top

# Pin definitions
LIGHT_PIN = 25  # Choose an unused GPIO pin

# Initialize GPIO if available
if GPIO_AVAILABLE:
    GPIO.setup(LIGHT_PIN, GPIO.OUT)
    GPIO.output(LIGHT_PIN, GPIO.LOW)

# Initialize a separate pygame mixer for aux output
pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.mixer.init(devicename="hw:0,0")  # Use default audio device (aux)

class PayPhone:
    def __init__(self, audio_dir="sounds"):
        self.audio_dir = audio_dir
        self.ring_sound = None
        self.adventure_active = False
        self.last_ring_time = time.time()
        self.ring_volume = 1.0  # Full volume
        self.debug_mode = True  # Add debug mode flag
        self.load_sounds()
        
        # Start threads
        self.ring_thread = threading.Thread(target=self._random_ring_controller, daemon=True)
        self.ring_thread.start()
        
        # Setup debug controls
        if self.debug_mode:
            keyboard.on_press_key('r', self._debug_ring_trigger)
            print("Debug mode active - Press 'R' key to test ring")

    def load_sounds(self):
        """Load the ring sound file"""
        ring_path = os.path.join(self.audio_dir, "ring.mp3")
        if os.path.exists(ring_path):
            self.ring_sound = pygame.mixer.Sound(ring_path)
            self.ring_sound.set_volume(self.ring_volume)
            print(f"Ring sound loaded from {ring_path}")
        else:
            print(f"Ring sound not found at {ring_path}")

    def set_light(self, state):
        """Control the payphone light"""
        if GPIO_AVAILABLE:
            GPIO.output(LIGHT_PIN, state)

    def play_ring(self, duration=3):
        """Play the ring sound and control light"""
        if self.ring_sound:
            print("Attempting to play ring sound...")
            self.set_light(GPIO.HIGH)
            self.ring_sound.play()
            time.sleep(duration)
            self.ring_sound.stop()
            self.set_light(GPIO.LOW)
            print("Ring sound completed")

    def _random_ring_controller(self):
        """Background thread to handle random ringing"""
        while True:
            now = datetime.now().time()
            current_time = time.time()
            
            # Debug output
            if datetime_time(14,0) <= now <= datetime_time(17,0):
                print(f"Current time {now} is within ring window")
            
            # Only ring between 2 PM and 5 PM
            if (datetime_time(14,0) <= now <= datetime_time(17,0) and 
                not self.adventure_active and
                current_time - self.last_ring_time >= 300):  # At least 5 minutes since last ring
                
                if random.random() < 0.3:  # Increase chance to 30%
                    print("Triggering random ring...")
                    self.play_ring()
                    self.last_ring_time = current_time
                
            time.sleep(60)  # Check every minute

    def _debug_ring_trigger(self, _):
        """Debug method to trigger ring manually"""
        if self.debug_mode and not self.adventure_active:
            print("Manual ring triggered")
            self.play_ring()

    def start_adventure(self):
        """Called when starting the adventure"""
        self.adventure_active = True
        self.set_light(GPIO.HIGH)

    def stop_adventure(self):
        """Called when ending the adventure"""
        self.adventure_active = False
        self.set_light(GPIO.LOW)

# Create a global instance
payphone = PayPhone()