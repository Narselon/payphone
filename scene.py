class Scene:
    def __init__(self, id: str, text: str, connections=None):
        self.id = id
        # self.audio = audio
        self.text = text
        # connections can be a list of IDs or even a dict mapping choice names to IDs
        self.connections = connections if connections is not None else []

    def add_connection(self, scene_id):
        self.connections.append(scene_id)
