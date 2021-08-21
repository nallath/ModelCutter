from UM.Scene.SceneNode import SceneNode

class PlaneNode(SceneNode):
    def __init__(self, parent = None):
        super().__init__(parent)
        self._shader = None

    def render(self, renderer):
        renderer.queueNode(self)