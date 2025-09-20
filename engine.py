import os
import yaml
import keypad
import time
from scene_audio import SceneAudio  # Import the new SceneAudio class
from payphone import payphone  # Import the payphone module

class Scene:
    def __init__(self, id, text, connections, hidden_connections=None, items_granted=None, 
                 items_required=None, timeout_after_audio=False, timeout_seconds=3):
        self.id = id
        self.text = text
        self.connections = connections
        self.hidden_connections = hidden_connections if hidden_connections else {}
        self.items_granted = items_granted if items_granted else []
        self.items_required = items_required if items_required else []
        self.timeout_after_audio = timeout_after_audio  # New flag
        self.timeout_seconds = timeout_seconds  # Configurable timeout duration

    def display(self, inventory):
        print("-" * 50)  
        print(self.text)
        
        # Display available choices
        for key, value in self.connections.items():
            print(f"{key}. {value[0]}")

    def get_next_scene(self, choice, inventory):
        """
        Determine the next scene based on choice and inventory items.
        Supports multiple branching paths based on specific items.
        """
        print(f"DEBUG: get_next_scene called with choice='{choice}', connections={self.connections}")
        
        # Check if the choice is a special hidden connection (like timeout)
        if choice in self.hidden_connections:
            connection = self.hidden_connections[choice]
            print(f"DEBUG: Found hidden connection for '{choice}' -> '{connection}'")
            
            # Handle timeout with item-based branching
            if choice == "timeout" and isinstance(connection, dict):
                print(f"DEBUG: Timeout with item-based branching, inventory: {inventory}")
                
                # Check each item combination to see if player has all required items
                for item_list_str, target_scene in connection.items():
                    required_items = [item.strip() for item in item_list_str.split(',')]
                    print(f"DEBUG: Checking if player has all items: {required_items}")
                    
                    if all(item in inventory for item in required_items):
                        print(f"DEBUG: Player has all required items {required_items}, going to: {target_scene}")
                        return target_scene, None
                
                # If no item combination matches, don't advance (stay in current scene)
                print("DEBUG: Player doesn't have required items for timeout progression, staying in current scene")
                return None, "You need the right items to progress..."
            else:
                # Regular hidden connection (string target)
                return connection, None

        # Check if it's a regular numbered choice
        try:
            choice_index = int(choice)
            print(f"DEBUG: Converted choice to int: {choice_index}")
            
            if choice_index in self.connections:
                print(f"DEBUG: Found connection for choice {choice_index}")
                connection_data = self.connections[choice_index]
                print(f"DEBUG: Connection data: {connection_data}")
                option_text = connection_data[0]
                
                # Handle standard format: [text, target, required_items, alt_scene]
                if len(connection_data) >= 2 and not isinstance(connection_data[1], dict):
                    target_scene_id = connection_data[1]
                    required_items = connection_data[2] if len(connection_data) > 2 else []
                    alt_scene_id = connection_data[3] if len(connection_data) > 3 else None
                    
                    print(f"DEBUG: Standard format - target: {target_scene_id}, required: {required_items}")
                    
                    # Special case for calling without a phone number
                    if target_scene_id == "scene2" and "phone_number" not in inventory:
                        return "no_numbers_scene", None
                    
                    # Check if player has all required items
                    if all(item in inventory for item in required_items):
                        print(f"DEBUG: All required items present, going to: {target_scene_id}")
                        return target_scene_id, None
                    elif alt_scene_id:
                        print(f"DEBUG: Missing items, going to alt scene: {alt_scene_id}")
                        return alt_scene_id, None
                    else:
                        missing_items = [item for item in required_items if item not in inventory]
                        message = f"You can't do that. You need these items: {', '.join(missing_items)}"
                        return None, message
                
                # Handle advanced branching: [text, {item1: scene1, item2: scene2, ..., "default": default_scene}]
                elif len(connection_data) >= 2 and isinstance(connection_data[1], dict):
                    paths = connection_data[1]
                    print(f"DEBUG: Advanced branching format - paths: {paths}")
                    
                    # First check for specific items in inventory that have defined paths
                    for item, scene_id in paths.items():
                        if item in inventory and item != "default":
                            print(f"DEBUG: Found matching item '{item}', going to: {scene_id}")
                            return scene_id, None
                    
                    # If no matching item, use the default path if provided
                    if "default" in paths:
                        print(f"DEBUG: Using default path: {paths['default']}")
                        return paths["default"], None
                    else:
                        return None, "You don't have the right item for this action."
            else:
                print(f"DEBUG: Choice {choice_index} not found in connections")
                
        except ValueError:
            print(f"DEBUG: Choice '{choice}' is not a valid integer")
            pass  # Ignore non-integer choices (except for hidden ones)
        
        # If we get here, check if there's a default action for any button press
        if "default" in self.hidden_connections:
            print(f"DEBUG: Using default hidden connection: {self.hidden_connections['default']}")
            return self.hidden_connections["default"], None
            
        print("DEBUG: No valid choice found, returning invalid choice message")
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
                    items_required=data.get("items_required", []),
                    timeout_after_audio=data.get("timeout_after_audio", False),
                    timeout_seconds=data.get("timeout_seconds", 3)  # Add configurable timeout
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


def handle_timed_input(scene, scene_audio):
    """Handle timed input for a scene"""
    timeout_seconds = getattr(scene, 'timeout_seconds', 3)  # Use scene's timeout or default to 3
    
    print(f"DEBUG: Starting timed input with {timeout_seconds}s timeout")
    print(f"DEBUG: timeout_after_audio = {scene.timeout_after_audio}")
    
    if scene.timeout_after_audio:
        print("DEBUG: Waiting for audio to finish...")
        # Wait for audio to finish
        while scene_audio.is_playing():
            time.sleep(0.1)
            
        print("Audio finished, starting timeout...")
    else:
        print("DEBUG: Starting timeout immediately (no audio wait)")
    
    # Now start the timeout
    start_time = time.time()
    print(f"DEBUG: Timeout started at {start_time}")
    
    # Use threading to handle the timeout properly
    import threading
    choice_result = [None]  # Use list to allow modification in nested function
    
    def get_input():
        try:
            choice = keypad.wait_for_single_keypress()
            if choice:
                choice_result[0] = choice
                print(f"DEBUG: User pressed '{choice}' before timeout")
        except Exception as e:
            print(f"DEBUG: Error getting input: {e}")
    
    # Start input thread
    input_thread = threading.Thread(target=get_input, daemon=True)
    input_thread.start()
    
    # Wait for either timeout or input
    elapsed = 0
    while elapsed < timeout_seconds:
        if choice_result[0] is not None:
            return choice_result[0]
        time.sleep(0.1)
        elapsed = time.time() - start_time
        
        # Debug progress every second
        if int(elapsed) != int(elapsed - 0.1):
            print(f"DEBUG: Timeout progress: {elapsed:.1f}/{timeout_seconds}s")
    
    print("DEBUG: Timeout reached, returning 'timeout'")
    return "timeout"


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
        keypad.wait_for_hook_change(expected_state=True)
        payphone.start_adventure()  # Add this line
        
        # Initialize game state
        current_scene = "intro"  # Start scene
        inventory = set()  # Player inventory
        previous_scene = None  # Track previous scene for invalid choices
        
        # Game loop
        while keypad.is_phone_lifted():
            scene = scenes.get(current_scene)
            if not scene:
                print(f"Error: Scene '{current_scene}' not found! Resetting to intro.")
                current_scene = "hub"
                continue

            # Check if we can enter the scene based on required items
            if not all(item in inventory for item in scene.items_required):
                missing_items = [item for item in scene.items_required if item not in inventory]
                print(f"You can't go there yet. You need: {', '.join(missing_items)}")
                time.sleep(2)  # Give player time to read the message
                
                # Go back to the previous scene if possible, or intro if not
                current_scene = previous_scene if previous_scene else "hub"
                continue
            
            # Play scene audio and wait if needed
            scene_audio.play_scene_audio(current_scene)
            
            # Display the scene with options
            scene.display(inventory)
            
            # Get player input with timeout if specified
            if "timeout" in scene.hidden_connections:
                print(f"DEBUG: Scene {current_scene} has timeout connection")
                choice = handle_timed_input(scene, scene_audio)
                print(f"DEBUG: handle_timed_input returned: '{choice}'")
            else:
                print(f"DEBUG: Scene {current_scene} has no timeout connection, using regular input")
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
                
            # Handle special command for replaying scene audio
            if choice == "#":
                print("\nReplaying scene audio...")
                scene_audio.stop_audio()  # Stop any currently playing audio
                scene_audio.play_scene_audio(current_scene)  # Replay the scene audio
                continue  # Return to scene options

            # Store previous scene for backtracking
            previous_scene = current_scene

            # Get next scene based on user choice
            next_scene, message = scene.get_next_scene(choice, inventory)
            print(f"DEBUG: get_next_scene returned: next_scene='{next_scene}', message='{message}'")

            if next_scene:
                # Grant any items from the current scene before moving on
                for item in scene.items_granted:
                    if item not in inventory:
                        inventory.add(item)
                        print(f"You obtained: {item}!")
                
                # If scene changes, play the new scene audio
                if next_scene != current_scene:
                    scene_audio.stop_audio()  # Stop current audio before changing scenes
                current_scene = next_scene
                print(f"DEBUG: Moving to scene: {current_scene}")
            elif message:
                print(message)
                time.sleep(1.5)  # Give player time to read
            else:
                print("Invalid choice. Try again.")
                time.sleep(1)
        
        # Stop audio when game resets
        scene_audio.stop_audio()
        payphone.stop_adventure()  # Add this line
        print("Game reset. Waiting for phone to be lifted...")


if __name__ == "__main__":
    main()