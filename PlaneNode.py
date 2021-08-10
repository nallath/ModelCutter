from UM.Mesh.MeshBuilder import MeshBuilder  # To create the billboard quad
from UM.View.GL.OpenGL import OpenGL
from UM.Scene.SceneNode import SceneNode
from UM.Resources import Resources

class PlaneNode(SceneNode):
    def __init__(self, parent = None):
        super().__init__(parent)
        self._shader = None

    def render(self, renderer):
        renderer.queueNode(self)