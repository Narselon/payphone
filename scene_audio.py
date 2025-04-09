import pygame
import os
import time

# Initialize pygame mixer if not already initialized
if not pygame.mixer.get_init():
    pygame.mixer.init()

class SceneAudio:
    def __init__(self, audio_dir="scene_audio", sounds_dir="sounds"):
        self.audio_dir = audio_dir
        self.sounds_dir = sounds_dir
        self.current_scene_sound = None
        
        # Initialize the mixer specifically for AIY voice hat
        pygame.mixer.init(channels=2, device="aiy-voice-hat")
        
        # Create directories if they don't exist
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(sounds_dir, exist_ok=True)
        
    def play_key_beep(self, *args, **kwargs):
        """
        Play a short beep sound before scene audio.
        Uses the default beep from keypad sounds.
        Accepts optional arguments to make it flexible
        Skips beep for initial scenes or hook toggles
        """
        # Check if scene is one that should skip beep
        if kwargs.get('skip_beep', False):
            return
        
        try:
            beep_path = os.path.join(self.sounds_dir, "beep.mp3")
            if os.path.exists(beep_path):
                # Create a separate mixer channel for the beep
                beep_channel = pygame.mixer.Channel(1)  # Use a different channel than keypad sounds
                beep_sound = pygame.mixer.Sound(beep_path)
                beep_channel.play(beep_sound)
                
                # Short delay to ensure beep plays before scene audio
                time.sleep(0.2)
            else:
                print(f"Beep sound not found at {beep_path}")
        except Exception as e:
            print(f"Error playing beep sound: {e}")
        
    def play_scene_audio(self, scene_id):
        """
        Plays audio associated with a scene.
        Follows naming convention: scene_id.mp3
        Plays a key beep before scene audio
        """
        # Stop any currently playing scene audio
        if self.current_scene_sound and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        
        # Special scenes or states where we want to skip the beep
        skip_beep_scenes = ['intro', 'no_numbers_scene']
        
        # Play key beep first - with option to skip
        self.play_key_beep(skip_beep=scene_id in skip_beep_scenes)
            
        # Try to load and play the scene audio
        audio_path = os.path.join(self.audio_dir, f"{scene_id}.mp3")
        
        try:
            if os.path.exists(audio_path):
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()
                print(f"Playing audio for scene: {scene_id}")
                self.current_scene_sound = scene_id
            else:
                print(f"Audio file not found for scene: {scene_id}")
                self.current_scene_sound = None
        except Exception as e:
            print(f"Error playing scene audio: {e}")
            self.current_scene_sound = None
            
    def stop_audio(self):
        """Stops any currently playing scene audio"""
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            self.current_scene_sound = None