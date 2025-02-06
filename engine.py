from scene import Scene

# Your scenes dictionary
scenes = {
    "intro": Scene(
        id="intro",
        text="You wake up in a dark room.\n1. Jump in the pit.\n2. Call your uncle",
        connections=["scene1", "scene2"],
    ),
    "scene1": Scene(
        id="scene1",
        text="You fall in a pit.\n1. Call for help",
        connections=["scene3"],
    ),
    "scene2": Scene(
        id="scene2",
        text="You try to call your uncle.\n1. You take out your phone and it slips out of your hand. In an effort to catch it, you fall into a pit.",
        connections=["scene3"],
    ),
    "scene3": Scene(
        id="scene3",
        text="You find your uncle in the pit.\n1. Restart",
        connections=["intro"],  # Loop back to the intro
    ),
}


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
