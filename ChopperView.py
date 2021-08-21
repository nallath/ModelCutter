from typing import cast

from UM.View.View import View
from UM.View.GL.OpenGL import OpenGL
from UM.Resources import Resources
from UM.Math.Color import Color
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Application import Application

from .ChopperTool import ChopperTool


class ChopperView(View):
    def __init__(self):
        super().__init__()
        self._objects_to_cut = []
        self._active_node = None
        self._active_node_shader = None
        self._inactive_node_shader = None
        self._ghost_node_shader = None

    def beginRendering(self):
        scene = self.getController().getScene()
        renderer = self.getRenderer()
        # Create two materials; an active material (normal) and a deactive material (slightly transparent)
        if not self._active_node_shader:
            self._active_node_shader = OpenGL.getInstance().createShaderProgram(
                Resources.getPath(Resources.Shaders, "object.shader"))
            self._active_node_shader.setUniformValue("u_ambientColor", Color(0.3, 0.3, 0.3, 1.0))
            self._active_node_shader.setUniformValue("u_diffuseColor", Color(1.0, 0.79, 0.14, 1.0))
            self._active_node_shader.setUniformValue("u_shininess", 50.0)

        if not self._inactive_node_shader:
            self._inactive_node_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "object.shader"))
            self._inactive_node_shader.setUniformValue("u_ambientColor", Color(0.3, 0.3, 0.3, 1.0))
            self._inactive_node_shader.setUniformValue("u_diffuseColor", Color(0.1, 0.1, 0.1, 0.1))
            self._inactive_node_shader.setUniformValue("u_opacity", 0.2)

        if not self._ghost_node_shader:
            self._ghost_node_shader = OpenGL.getInstance().createShaderProgram(
                Resources.getPath(Resources.Shaders, "color.shader"))
            self._ghost_node_shader.setUniformValue("u_color", Color(*Application.getInstance().getTheme().getColor("layerview_ghost").getRgb()))

        # Note that this view is only active when the ChopperTool is active.
        tool = cast(ChopperTool, self.getController().getActiveTool())
        active_node = tool.getActiveNode()
        for node in DepthFirstIterator(scene.getRoot()):
            if node in tool.getObjectsToCut():
                if node == active_node:
                    renderer.queueNode(node, shader=self._active_node_shader)
                else:
                    renderer.queueNode(node, shader=self._inactive_node_shader)
            else:
                if node.callDecoration("isSliceable"):
                    # Render all nodes that are slicable but aren't being cut transparent
                    renderer.queueNode(node, shader = self._ghost_node_shader, transparent = True)
                else:
                    node.render(renderer)