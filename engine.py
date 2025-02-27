import os
import yaml
import keypad
import time

class Scene:
    def __init__(self, id, text, connections, hidden_connections=None, items_granted=None, items_required=None):
        self.id = id
        self.text = text
        self.connections = connections
        self.hidden_connections = hidden_connections if hidden_connections else {}
        self.items_granted = items_granted if items_granted else []
        self.items_required = items_required if items_required else []

    def display(self, inventory):
        # Clear the screen first to avoid duplicate display
        # print("\033[H\033[J", end="")  # This clears the screen on ANSI-compatible terminals
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
        Determine the next scene based on choice and check item requirements.
        Returns the next scene ID or None if the choice is invalid.
        Also returns a message if inventory requirements aren't met.
        """
        # Check if the choice is a special hidden connection
        if choice in self.hidden_connections:
            return self.hidden_connections[choice], None

        # Check if it's a regular numbered choice
        try:
            choice_index = int(choice)
            if choice_index in self.connections:
                # Get target scene and check required items
                target_scene_id = self.connections[choice_index][1]  # [1] is the scene ID
                required_items = self.connections[choice_index][2] if len(self.connections[choice_index]) > 2 else []
                
                # Special case for calling someone without a phone number
                if target_scene_id == "scene2" and "phone_number" not in inventory:
                    return "no_numbers_scene", None
                
                # Check if the player has all required items
                if all(item in inventory for item in required_items):
                    return target_scene_id, None
                else:
                    missing_items = [item for item in required_items if item not in inventory]
                    message = f"You can't do that. You need these items: {', '.join(missing_items)}"
                    return None, message
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
                        # If the value is a string, it's just a scene ID
                        if isinstance(value, str):
                            formatted_connections[int(key)] = [f"Go to {value}", value, []]
                        # If it's a list/dict, it might contain more info
                        elif isinstance(value, list) and len(value) >= 2:
                            formatted_connections[int(key)] = [value[0], value[1], value[2] if len(value) > 2 else []]
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
    print("\nGame Controls:")
    print("- Use number keys to select options")
    print("- Press 'h' at any time to hang up the phone")
    print("- Press '*' followed by a sequence and '#' to enter codes")
    print("- Press '#' to view your inventory")
    print("\nWaiting for phone to be lifted...")
    
    while True:
        # Wait for the phone to be lifted to start/restart the game
        keypad.wait_for_hook_change(expected_state=True)  # Wait for off-hook
        
        # Initialize game state
        current_scene = "intro"  # Start scene
        inventory = set()  # Player inventory
        input_buffer = ""  # Buffer for multi-digit inputs
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
            
            # Store the current scene as previous for backtracking if needed
            previous_scene = current_scene
            
            # Display the scene with options
            scene.display(inventory)
            
            # Grant items from the scene
            for item in scene.items_granted:
                if item not in inventory:
                    inventory.add(item)
                    print(f"You obtained: {item}!")
            
            # Get player input
            choice = keypad.wait_for_keypress()
            
            # If the hook state changed (phone hung up), break the game loop
            if not keypad.is_phone_lifted() or choice is None:
                print("Phone hung up. Game reset.")
                break
            
            # Check for hang-up command
            if choice == 'h' or choice == 'H':
                print("Phone hung up. Resetting game...")
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
                keypad.wait_for_keypress()
                
                # Redisplay the scene without incrementing it
                continue
                
            # Handle multi-digit input
            if choice == "*":
                # Allow for sequence input (for codes)
                print("Enter sequence (press # when done):")
                sequence = ""
                while keypad.is_phone_lifted():
                    digit = keypad.wait_for_keypress()
                    if digit is None:  # Check if phone was hung up
                        break
                    if digit == "#":
                        break
                    elif digit in "0123456789":
                        sequence += digit
                        print(digit, end="", flush=True)
                print()  # New line after sequence
                choice = sequence
                
                # If phone was hung up during sequence entry, break the game loop
                if not keypad.is_phone_lifted():
                    print("Phone hung up. Game reset.")
                    break

            # Get next scene based on user choice
            next_scene, message = scene.get_next_scene(choice, inventory)

            if next_scene:
                current_scene = next_scene
            elif message:
                print(message)
                time.sleep(1.5)  # Give player time to read
            else:
                print("Invalid choice. Try again.")
                time.sleep(1)
        
        print("Game reset. Waiting for phone to be lifted...")


if __name__ == "__main__":
    main()