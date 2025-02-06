import os
import yaml

class Scene:
    def __init__(self, scene_id, title, content, connections, conditions=None):
        self.id = scene_id
        self.title = title
        self.content = content
        self.connections = connections  # list of dicts with label, target, condition, etc.
        self.conditions = conditions or {}

def load_scene_from_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        # Assume YAML front matter is separated by '---'
        parts = f.read().split('---')
        if len(parts) < 3:
            raise ValueError("File format error, expected YAML front matter.")
        metadata = yaml.safe_load(parts[1])
        content = parts[2].strip()
        return Scene(
            scene_id=metadata.get("id"),
            title=metadata.get("title", ""),
            content=content,
            connections=metadata.get("connections", []),
            conditions=metadata.get("conditions", {})
        )

def load_all_scenes(root_dir):
    scenes = {}
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.txt'):
                filepath = os.path.join(dirpath, filename)
                scene = load_scene_from_file(filepath)
                scenes[scene.id] = scene
    return scenes

# Load your scenes
scenes = load_all_scenes('scenes')
