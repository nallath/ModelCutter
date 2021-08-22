from UM.Message import Message
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.RemoveSceneNodeOperation import RemoveSceneNodeOperation
from UM.Tool import Tool
from UM.Application import Application
from UM.Scene.Selection import Selection
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Event import Event, MouseEvent

from UM.Math.Plane import Plane
from UM.Math.Vector import Vector

from .ChopperToolHandle import ChopperToolHandle
from .PlaneNode import PlaneNode

import numpy
import trimesh

from .TrimeshUtils import replaceSceneNode


class ChopperTool(Tool):
    def __init__(self):
        super().__init__()
        self._previous_view = None

        self._handle = ChopperToolHandle()
        self._handle.setEnabledAxis([self._handle.YAxis])

        self.setExposedProperties("CutDirection")
        self._is_cutting = False
        self._objects_to_cut = []
        self._active_node = None
        self._plane_node = None
        self._cut_direction = "z"

    def getObjectsToCut(self):
        return self._objects_to_cut

    def getActiveNode(self):
        return self._active_node

    def getCutDirection(self):
        return self._cut_direction

    def setCutDirection(self, direction):
        if self._cut_direction != direction:

            self._cut_direction = direction
            self._updatePlaneMesh()
            if self._cut_direction == "z":
                self._handle.setEnabledAxis([self._handle.YAxis])
            elif self._cut_direction == "y":
                self._handle.setEnabledAxis([self._handle.ZAxis])
            elif self._cut_direction == "x":
                self._handle.setEnabledAxis([self._handle.XAxis])
            self.propertyChanged.emit()

    def cutObject(self):
        mesh_data = self._active_node.getMeshData().getTransformed(self._active_node.getWorldTransformation())
        indices = numpy.arange(mesh_data.getVertexCount()).reshape(-1, 3)
        trimesh_mesh = trimesh.base.Trimesh(vertices=mesh_data.getVertices(), faces=indices)

        if not trimesh_mesh.is_watertight:
            Message(title="Unable to cut", text="Unable to cut a model that isn't watertight", message_type=Message.MessageType.WARNING).show()
            return

        plane_position = self._plane_node.getPosition()

        if self._cut_direction == "z":
            plane_normal = [0, 1, 0]
            inverse_plane_normal = [0, -1, 0]
        elif self._cut_direction == "x":
            plane_normal = [1, 0, 0]
            inverse_plane_normal = [-1, 0, 0]
        else:
            plane_normal = [0, 0, 1]
            inverse_plane_normal = [0, 0, -1]

        half_one = trimesh.intersections.slice_mesh_plane(trimesh_mesh, plane_normal= plane_normal, plane_origin=[plane_position.x, plane_position.y, plane_position.z], cap=True)
        half_two = trimesh.intersections.slice_mesh_plane(trimesh_mesh, plane_normal= inverse_plane_normal, plane_origin=[plane_position.x, plane_position.y, plane_position.z], cap=True)
        replaceSceneNode(self._active_node, [half_one, half_two])
        op = GroupedOperation()
        op.addOperation(RemoveSceneNodeOperation(self._active_node))

    def getIsCutting(self):
        return self._is_cutting

    def setIsCutting(self, is_cutting):
        if self._is_cutting is not is_cutting:
            self._is_cutting = is_cutting
            if self._is_cutting:
                # We're now in the process of cutting!
                self._objects_to_cut = Selection.getAllSelectedObjects()
                # TODO: Might want to change this behavior:
                self._active_node = self._objects_to_cut[0]
                self._activateView()
            else:
                self._deactivateView()
            self.propertyChanged.emit()

    def _updatePlaneMesh(self):
        global_container_stack = Application.getInstance().getGlobalContainerStack()
        machine_width = global_container_stack.getProperty("machine_width", "value")
        machine_depth = global_container_stack.getProperty("machine_depth", "value")
        machine_height = global_container_stack.getProperty("machine_height", "value")
        mesh_builder = MeshBuilder()
        if self._cut_direction == "x":
            mesh_builder.addCube(0.1, machine_height, machine_depth)
        elif self._cut_direction == "y":
            mesh_builder.addCube(machine_width, machine_height, 0.1)
        elif self._cut_direction == "z":
            mesh_builder.addCube(machine_width, 0.1, machine_depth)
        self._plane_node.setMeshData(mesh_builder.build())

    def _createPlaneNode(self):
        self._plane_node = PlaneNode()
        self._updatePlaneMesh()

    def _activateView(self):
        # We also have to add a plane Node (Tool handles are drawn on top, so we cant use those)
        if not self._plane_node:
            self._createPlaneNode()
        self._active_node = Selection.getAllSelectedObjects()[0]
        self._objects_to_cut = Selection.getAllSelectedObjects()
        self._handle.setParent(self._plane_node)
        self._handle.setPosition(Vector(0, 0, 0))

        self._plane_node.setParent(Application.getInstance().getController().getScene().getRoot())
        self._plane_node.setPosition(self._active_node.getBoundingBox().center)
        self._previous_view = Application.getInstance().getController().getActiveView().getPluginId()
        Application.getInstance().getController().setActiveView("ModelCutter")

    def _deactivateView(self):
        self._handle.setParent(None)
        if self._plane_node:
            self._plane_node.setParent(None)
        self._objects_to_cut = []
        self._is_cutting = False
        Application.getInstance().getController().setActiveView(self._previous_view)

    def event(self, event):
        super().event(event)
        if event.type == Event.ToolDeactivateEvent:
            self._deactivateView()
        elif event.type == Event.ToolActivateEvent:
            self._activateView()

        if event.type == Event.MousePressEvent and self._controller.getToolsEnabled():
            # Start a translate operation
            if MouseEvent.LeftButton not in event.buttons:
                return False

            id = self._selection_pass.getIdAtPosition(event.x, event.y)
            if not id:
                return True

            if id in self._handle.getEnabledAxis():
                self.setLockedAxis(id)

            if id == self._handle.XAxis:
                self.setDragPlane(Plane(Vector(0, 0, 1), 0))
            elif id == self._handle.YAxis:
                self.setDragPlane(Plane(Vector(0, 0, 1), 0))
            elif id == self._handle.ZAxis:
                self.setDragPlane(Plane(Vector(0, 1, 0), 0))
            else:
                self.setDragPlane(Plane(Vector(0, 1, 0), 0))

        if event.type == Event.MouseMoveEvent:
            # Perform a translate operation

            if not self.getDragPlane():
                return False

            if not self.getDragStart():
                self.setDragStart(event.x, event.y)
                return False

            drag = self.getDragVector(event.x, event.y)
            if drag:
                if self.getLockedAxis() == self._handle.XAxis:
                    drag = drag.set(y=0, z=0)
                elif self.getLockedAxis() == self._handle.YAxis:
                    drag = drag.set(x=0, z=0)
                elif self.getLockedAxis() == self._handle.ZAxis:
                    drag = drag.set(x=0, y=0)

                self._plane_node.translate(drag)

                if self._cut_direction == "z":
                    if self._plane_node.getPosition().y > self._active_node.getBoundingBox().top:
                        new_position = self._plane_node.getPosition().set(y = self._active_node.getBoundingBox().top)
                        self._plane_node.setPosition(new_position)
                    elif self._plane_node.getPosition().y < self._active_node.getBoundingBox().bottom:
                        new_position = self._plane_node.getPosition().set(y=self._active_node.getBoundingBox().bottom)
                        self._plane_node.setPosition(new_position)
                elif self._cut_direction == "y":
                    if self._plane_node.getPosition().z > self._active_node.getBoundingBox().front:
                        new_position = self._plane_node.getPosition().set(z = self._active_node.getBoundingBox().front)
                        self._plane_node.setPosition(new_position)
                    elif self._plane_node.getPosition().z < self._active_node.getBoundingBox().back:
                        new_position = self._plane_node.getPosition().set(z=self._active_node.getBoundingBox().back)
                        self._plane_node.setPosition(new_position)
                elif self._cut_direction == "x":
                    if self._plane_node.getPosition().x > self._active_node.getBoundingBox().right:
                        new_position = self._plane_node.getPosition().set(x = self._active_node.getBoundingBox().right)
                        self._plane_node.setPosition(new_position)
                    elif self._plane_node.getPosition().x < self._active_node.getBoundingBox().left:
                        new_position = self._plane_node.getPosition().set(x=self._active_node.getBoundingBox().left)
                        self._plane_node.setPosition(new_position)

            self.setDragStart(event.x, event.y)

            return True

        if event.type == Event.MouseReleaseEvent:
            # Finish a translate operation
            if self.getDragPlane():
                self.operationStopped.emit(self)
                self._distance = None
                self.propertyChanged.emit()
                self.setLockedAxis(None)
                self.setDragPlane(None)
                self.setDragStart(None, None)
                return True

        return False


