import yaml
from scene import Scene

# Load scenes from a YAML file
def load_scenes(filename: str) -> dict:
    with open(filename, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    
    scenes = {}
    for scene_id, scene_data in data["scenes"].items():
        scenes[scene_id] = Scene(
            id=scene_data["id"],
            text=scene_data["text"],
            connections=scene_data["connections"]
        )
    
    return scenes

# Load the scenes dynamically
scenes = load_scenes("story.yaml")


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


next_scene = explore("intro")
while True:
    next_scene = explore(next_scene)
