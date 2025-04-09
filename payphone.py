import RPi.GPIO as GPIO
from datetime import datetime, time
import random
import threading
import pygame
import os
from keypad import GPIO_AVAILABLE

# Pin definitions
LIGHT_PIN = 25  # Choose an unused GPIO pin

# Initialize GPIO if available
if GPIO_AVAILABLE:
    GPIO.setup(LIGHT_PIN, GPIO.OUT)
    GPIO.output(LIGHT_PIN, GPIO.LOW)

# Initialize pygame mixer for audio if not already done
if not pygame.mixer.get_init():
    pygame.mixer.init()

class PayPhone:
    def __init__(self, audio_dir="sounds"):
        self.audio_dir = audio_dir
        self.ring_sound = None
        self.adventure_active = False
        self.load_sounds()
        
        # Start random ring thread
        self.ring_thread = threading.Thread(target=self._random_ring_controller, daemon=True)
        self.ring_thread.start()

    def load_sounds(self):
        """Load the ring sound file"""
        ring_path = os.path.join(self.audio_dir, "ring.mp3")
        if os.path.exists(ring_path):
            self.ring_sound = pygame.mixer.Sound(ring_path)
        else:
            print(f"Ring sound not found at {ring_path}")

    def set_light(self, state):
        """Control the payphone light"""
        if GPIO_AVAILABLE:
            GPIO.output(LIGHT_PIN, state)

    def play_ring(self, duration=3):
        """Play the ring sound and control light"""
        if self.ring_sound:
            self.set_light(GPIO.HIGH)
            self.ring_sound.play()
            import time
            time.sleep(duration)
            self.ring_sound.stop()
            self.set_light(GPIO.LOW)

    def _random_ring_controller(self):
        """Background thread to handle random ringing"""
        while True:
            now = datetime.now().time()
            # Only ring between 2 PM and 5 PM
            if (time(914,0) <= now <= time(17,0) and 
                not self.adventure_active):
                if random.random() < 0.1:  # 10% chance to ring
                    self.play_ring()
                import time
                time.sleep(300)  # Check every 5 minutes
            time.sleep(60)

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