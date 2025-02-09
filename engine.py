import yaml
import os
from scene import Scene
#from keypad import wait_for_keypress, is_phone_lifted, wait_for_hook_change

SCENE_DIR = "story"  # Root directory for scene files

def load_scenes(scene_dir: str) -> dict:
    scenes = {}

    # Walk through all subdirectories
    for root, _, files in os.walk(scene_dir):
        for filename in files:
            if filename.endswith(".yaml"):  # Process only YAML files
                filepath = os.path.join(root, filename)
                with open(filepath, "r", encoding="utf-8") as file:
                    scene_data = yaml.safe_load(file)

                    # Handle hidden options (default to empty if not defined)
                    hidden_options = scene_data.get("hidden_options", {})

                    scenes[scene_data["id"]] = Scene(
                        id=scene_data["id"],
                        text=scene_data["text"],
                        connections=scene_data["connections"]
                    )
                    setattr(scenes[scene_data["id"]], "hidden_options", hidden_options)
    return scenes

# Load scenes dynamically from the hierarchical structure
scenes = load_scenes(SCENE_DIR)


def explore(scene_id: str) -> str:
    """
    Takes in a scene_id, plays the scene for the user, then returns
    the scene_id of the choice they made.
    """
    scene = scenes.get(scene_id)
    if scene is None:
        print("Invalid scene ID:", scene_id)
        return "intro"  # Prevent crashing

    print(scene.text)


    is_valid = False
    next_choice = "intro"
    while not is_valid:
        player_choice = input("Make your choice: ")
        
        # Check if input matches a hidden option (e.g., a secret code)
        if hasattr(scene, "hidden_options") and player_choice in scene.hidden_options:
            return scene.hidden_options[player_choice]
        
        try:
            int_choice = int(player_choice) - 1
            if 0 <= int_choice < len(scene.connections):
                is_valid = True
                next_choice = scene.connections[int_choice]
            else:
                print("That's not a valid choice. Try again.")
        except ValueError:
            print("Please enter a valid number.")

    return next_choice

#game loop
#for use before running on payphone
next_scene = explore("intro")
while True:
    next_scene = explore(next_scene)

#code below for hook implementation
#while True:
#    print("Waiting for phone to be lifted to start the game...")
#    wait_for_hook_change(True)  # Wait for the phone to be lifted
#    print("Game started!")
    
#    next_scene = "intro"
#    while is_phone_lifted():  # Keep playing while phone is lifted
#        next_scene = explore(next_scene)
    
#    print("Phone placed back. Game over.")
#    wait_for_hook_change(False)  # Wait for the phone to be placed back