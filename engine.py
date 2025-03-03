import os
import yaml
import keypad
import time
from scene_audio import SceneAudio  # Import the new SceneAudio class

class Scene:
    def __init__(self, id, text, connections, hidden_connections=None, items_granted=None, items_required=None):
        self.id = id
        self.text = text
        self.connections = connections
        self.hidden_connections = hidden_connections if hidden_connections else {}
        self.items_granted = items_granted if items_granted else []
        self.items_required = items_required if items_required else []

    def display(self, inventory):
        print("-" * 50)  
        print(self.text)
        
        # Display inventory if it's not empty
        if inventory:
            print("\nInventory:", ", ".join(inventory))
        
        # Display available choices
        for key, value in self.connections.items():
            print(f"{key}. {value[0]}")

    def get_next_scene(self, choice, inventory):
        """
        Determine the next scene based on choice and inventory items.
        Supports multiple branching paths based on specific items.
        """
        # Check if the choice is a special hidden connection
        if choice in self.hidden_connections:
            return self.hidden_connections[choice], None

        # Check if it's a regular numbered choice
        try:
            choice_index = int(choice)
            if choice_index in self.connections:
                connection_data = self.connections[choice_index]
                option_text = connection_data[0]
                
                # Handle standard format: [text, target, required_items, alt_scene]
                if len(connection_data) >= 2 and not isinstance(connection_data[1], dict):
                    target_scene_id = connection_data[1]
                    required_items = connection_data[2] if len(connection_data) > 2 else []
                    alt_scene_id = connection_data[3] if len(connection_data) > 3 else None
                    
                    # Special case for calling without a phone number
                    if target_scene_id == "scene2" and "phone_number" not in inventory:
                        return "no_numbers_scene", None
                    
                    # Check if player has all required items
                    if all(item in inventory for item in required_items):
                        return target_scene_id, None
                    elif alt_scene_id:
                        return alt_scene_id, None
                    else:
                        missing_items = [item for item in required_items if item not in inventory]
                        message = f"You can't do that. You need these items: {', '.join(missing_items)}"
                        return None, message
                
                # Handle advanced branching: [text, {item1: scene1, item2: scene2, ..., "default": default_scene}]
                elif len(connection_data) >= 2 and isinstance(connection_data[1], dict):
                    paths = connection_data[1]
                    
                    # First check for specific items in inventory that have defined paths
                    for item, scene_id in paths.items():
                        if item in inventory and item != "default":
                            return scene_id, None
                    
                    # If no matching item, use the default path if provided
                    if "default" in paths:
                        return paths["default"], None
                    else:
                        return None, "You don't have the right item for this action."
        except ValueError:
            pass  # Ignore non-integer choices (except for hidden ones)
            
        return None, "Invalid choice. Try again."


def load_scenes():
    """Loads scenes from YAML files in the 'story' directory and its subdirectories."""
    scenes = {}
    
    # Debug: Check if the story directory exists
    if not os.path.exists("story"):
        print("ERROR: 'story' directory not found!")
        story_dir = "story"
        os.makedirs(story_dir, exist_ok=True)
        print(f"Created directory: {story_dir}")
        return scenes
    
    # Debug: List all files in story directory
    print(f"Files in story directory: {os.listdir('story')}")
    
    # Function to process a YAML file
    def process_yaml_file(filepath):
        try:
            with open(filepath, "r") as file:
                data = yaml.safe_load(file)
                
                # Process connections: transform from dictionary to more structured format
                formatted_connections = {}
                
                # Handle different connection formats
                if isinstance(data["connections"], dict):
                    for key, value in data["connections"].items():
                        key_int = int(key)
                        
                        # If the value is a string, it's just a scene ID
                        if isinstance(value, str):
                            formatted_connections[key_int] = [f"Go to {value}", value, []]
                        
                        # If it's a list, it might be standard format or contain a dict for branching
                        elif isinstance(value, list):
                            if len(value) >= 2 and isinstance(value[1], dict):
                                # This is the advanced branching format
                                formatted_connections[key_int] = value
                            else:
                                # This is the standard format
                                option_text = value[0]
                                target_scene = value[1]
                                required_items = value[2] if len(value) > 2 else []
                                alt_scene = value[3] if len(value) > 3 else None
                                formatted_connections[key_int] = [option_text, target_scene, required_items, alt_scene]
                        
                        # If it's a dict directly, it's the branching format
                        elif isinstance(value, dict) and "text" in value and "paths" in value:
                            formatted_connections[key_int] = [value["text"], value["paths"]]
                            
                elif isinstance(data["connections"], list):
                    # Simple list format [scene1, scene2, ...]
                    for i, scene_id in enumerate(data["connections"], 1):
                        formatted_connections[i] = [f"Go to {scene_id}", scene_id, []]
                
                scenes[data["id"]] = Scene(
                    id=data["id"],
                    text=data["text"],
                    connections=formatted_connections,
                    hidden_connections=data.get("hidden_connections", {}),
                    items_granted=data.get("items_granted", []),
                    items_required=data.get("items_required", [])
                )
                print(f"Loaded scene: {data['id']} from {filepath}")
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
    
    # Recursively walk through directories
    for root, dirs, files in os.walk("story"):
        for file in files:
            if file.endswith(".yaml"):
                filepath = os.path.join(root, file)
                process_yaml_file(filepath)
    
    # Add custom scene for when player has no phone numbers
    scenes["no_numbers_scene"] = Scene(
        id="no_numbers_scene",
        text="You look at your phone but there are no numbers saved in your contacts. You need to find a phone number first.",
        connections={1: ["Go back", "intro", []]}
    )
    
    return scenes


def main():
    scenes = load_scenes()
    print(f"DEBUG: Loaded scenes = {scenes.keys()}")
    
    # Initialize scene audio
    scene_audio = SceneAudio()
    
    print("\nGame Controls:")
    print("- Use number keys to select options")
    print("- Press 'h' at any time to hang up the phone")
    print("- Press '*' to start entering a code, then enter your code and press '#' when done")
    print("- Press '#' to view your inventory")
    print("\nWaiting for phone to be lifted...")
    
    # Check if sounds directory exists, create if not
    if not os.path.exists("sounds"):
        os.makedirs("sounds", exist_ok=True)
        print("Created 'sounds' directory. Please add mp3 files for each keypad key.")
    
    # Make sure scene_audio directory exists 
    if not os.path.exists("scene_audio"):
        os.makedirs("scene_audio", exist_ok=True)
        print("Created 'scene_audio' directory. Please add mp3 files for each scene (format: scene_id.mp3)")
    
    while True:
        # Wait for the phone to be lifted to start/restart the game
        keypad.wait_for_hook_change(expected_state=True)  # Wait for off-hook
        
        # Initialize game state
        current_scene = "intro"  # Start scene
        inventory = set()  # Player inventory
        previous_scene = None  # Track previous scene for invalid choices
        
        # Game loop
        while keypad.is_phone_lifted():
            scene = scenes.get(current_scene)
            if not scene:
                print(f"Error: Scene '{current_scene}' not found! Resetting to intro.")
                current_scene = "intro"
                continue

            # Check if we can enter the scene based on required items
            if not all(item in inventory for item in scene.items_required):
                missing_items = [item for item in scene.items_required if item not in inventory]
                print(f"You can't go there yet. You need: {', '.join(missing_items)}")
                time.sleep(2)  # Give player time to read the message
                
                # Go back to the previous scene if possible, or intro if not
                current_scene = previous_scene if previous_scene else "intro"
                continue
            
            # Play scene audio
            scene_audio.play_scene_audio(current_scene)
            
            # Store the current scene as previous for backtracking if needed
            previous_scene = current_scene
            
            # Display the scene with options
            scene.display(inventory)
            
            # Grant items from the scene
            for item in scene.items_granted:
                if item not in inventory:
                    inventory.add(item)
                    print(f"You obtained: {item}!")
            
            # Get player input - using the new wait_for_keypress that handles code entry
            choice = keypad.wait_for_keypress()
            
            # If the hook state changed (phone hung up), break the game loop
            if not keypad.is_phone_lifted() or choice is None:
                print("Phone hung up. Game reset.")
                scene_audio.stop_audio()  # Stop any playing audio
                break
            
            # Check for hang-up command
            if choice == 'h' or choice == 'H':
                print("Phone hung up. Resetting game...")
                scene_audio.stop_audio()  # Stop any playing audio
                break
                
            # Handle special command for showing inventory
            if choice == "#":
                print("\nInventory:")
                if inventory:
                    for item in inventory:
                        print(f"- {item}")
                else:
                    print("Empty")
                print("\nPress any key to continue...")
                keypad.wait_for_single_keypress()
                
                # Redisplay the scene without incrementing it
                continue

            # Get next scene based on user choice
            next_scene, message = scene.get_next_scene(choice, inventory)

            if next_scene:
                # If scene changes, play the new scene audio
                if next_scene != current_scene:
                    scene_audio.stop_audio()  # Stop current audio before changing scenes
                current_scene = next_scene
            elif message:
                print(message)
                time.sleep(1.5)  # Give player time to read
            else:
                print("Invalid choice. Try again.")
                time.sleep(1)
        
        # Stop audio when game resets
        scene_audio.stop_audio()
        print("Game reset. Waiting for phone to be lifted...")


if __name__ == "__main__":
    main()