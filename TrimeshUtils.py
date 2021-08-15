import numpy
import trimesh

from UM.Math.AxisAlignedBox import AxisAlignedBox
from UM.Mesh.MeshData import MeshData, calculateNormalsFromIndexedVertices
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.RemoveSceneNodeOperation import RemoveSceneNodeOperation
from UM.Scene.Selection import Selection

from cura.Scene.BuildPlateDecorator import BuildPlateDecorator
from cura.Scene.CuraSceneNode import CuraSceneNode
from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator

from .SetTransformMatrixOperation import SetTransformMatrixOperation
from .SetParentOperationSimplified import SetParentOperationSimplified


def replaceSceneNode(existing_node, trimeshes) -> None:
    name = existing_node.getName()
    file_name = existing_node.getMeshData().getFileName()
    transformation = existing_node.getWorldTransformation()
    parent = existing_node.getParent()
    extruder_id = existing_node.callDecoration("getActiveExtruder")
    build_plate = existing_node.callDecoration("getBuildPlateNumber")
    selected = Selection.isSelected(existing_node)

    children = existing_node.getChildren()
    new_nodes = []

    op = GroupedOperation()
    op.addOperation(RemoveSceneNodeOperation(existing_node))

    for i, tri_node in enumerate(trimeshes):
        mesh_data = fromTrimeshToCuraMesh(tri_node, file_name)

        new_node = CuraSceneNode()
        new_node.setSelectable(True)
        new_node.setMeshData(mesh_data)
        new_node.setName(name if i == 0 else "%s %d" % (name, i))
        new_node.callDecoration("setActiveExtruder", extruder_id)
        new_node.addDecorator(BuildPlateDecorator(build_plate))
        new_node.addDecorator(SliceableObjectDecorator())

        op.addOperation(AddSceneNodeOperation(new_node, parent))
        op.addOperation(SetTransformMatrixOperation(new_node, transformation))

        new_nodes.append(new_node)

        if selected:
            Selection.add(new_node)

    for child in children:
        mesh_data = child.getMeshData()
        if not mesh_data:
            continue
        child_bounding_box = mesh_data.getTransformed(child.getWorldTransformation()).getExtents()
        if not child_bounding_box:
            continue
        new_parent = None
        for potential_parent in new_nodes:
            parent_mesh_data = potential_parent.getMeshData()
            if not parent_mesh_data:
                continue
            parent_bounding_box = parent_mesh_data.getTransformed(
                potential_parent.getWorldTransformation()).getExtents()
            if not parent_bounding_box:
                continue
            intersection = child_bounding_box.intersectsBox(parent_bounding_box)
            if intersection != AxisAlignedBox.IntersectionResult.NoIntersection:
                new_parent = potential_parent
                break
        if not new_parent:
            new_parent = new_nodes[0]
        op.addOperation(SetParentOperationSimplified(child, new_parent))

    op.push()


def fromTrimeshToCuraMesh(tri_node: trimesh.base.Trimesh, file_name: str = "") -> MeshData:
    tri_faces = tri_node.faces
    tri_vertices = tri_node.vertices

    indices = []
    vertices = []

    index_count = 0
    face_count = 0
    for tri_face in tri_faces:
        face = []
        for tri_index in tri_face:
            vertices.append(tri_vertices[tri_index])
            face.append(index_count)
            index_count += 1
        indices.append(face)
        face_count += 1

    vertices = numpy.asarray(vertices, dtype=numpy.float32)
    indices = numpy.asarray(indices, dtype=numpy.int32)
    normals = calculateNormalsFromIndexedVertices(vertices, indices, face_count)

    mesh_data = MeshData(file_name=file_name, vertices=vertices, indices=indices, normals=normals)
    return mesh_data