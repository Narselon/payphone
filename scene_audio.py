import pygame
import os

# Initialize pygame mixer if not already initialized
if not pygame.mixer.get_init():
    pygame.mixer.init()

class SceneAudio:
    def __init__(self, audio_dir="scene_audio"):
        self.audio_dir = audio_dir
        self.current_scene_sound = None
        
        # Create audio directory if it doesn't exist
        os.makedirs(audio_dir, exist_ok=True)
        
    def play_scene_audio(self, scene_id):
        """
        Plays audio associated with a scene.
        Follows naming convention: scene_id.mp3
        """
        # Stop any currently playing scene audio
        if self.current_scene_sound and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            
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