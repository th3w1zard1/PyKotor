"""Binary reader for lightsaber nodes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.misc import Color, ResRef
from pykotor.resource.formats.mdl.data.enums import MDLNodeFlags, MDLSaberFlags, MDLSaberType
from pykotor.resource.formats.mdl.data.nodes.saber import MDLSaber, MDLSaberNode
from pykotor.resource.formats.mdl.io.binary.nodes.base_node_reader import MDLBinaryNodeReader
from utility.common.geometry import Vector3

if TYPE_CHECKING:
    from pykotor.resource.formats.mdl.data.nodes.node import MDLNode


class MDLBinarySaberReader(MDLBinaryNodeReader):
    """Binary reader for lightsaber nodes."""

    # Saber node header offsets
    SABER_HEADER_OFFSET = 92
    VERTEX_DATA_OFFSET = 12  # Additional offset for vertex data

    def read_node(
        self,
        parent: MDLNode | None = None,
        offset: int = 0,
    ) -> MDLNode:
        """Read a lightsaber node from the MDL file.

        Args:
            parent: Parent node if any
            offset: Offset to node data

        Returns:
            The loaded saber node

        Raises:
            MDLReadError: If there is an error reading the node data
        """
        # Create saber node
        node = MDLSaberNode(self._names[0])  # Name set in read_header

        # Read all node data
        self.read_header(node)
        self.read_subheader(node)
        self.read_controllers(node)
        self.read_controller_data(node)
        self.read_vertex_coordinates(node)
        self.read_faces(node)

        # Read child nodes
        self.read_children(node)

        return node

    def read_header(self, node: MDLNode) -> None:
        """Read the header of a node.

        Args:
            node: Node to read header for
        """
        type_flags, node_number, name_index, root_offset, parent_offset = self._read_node_header()
        node.name = self._names[name_index]
        node.node_number = node_number
        node.node_flags = MDLNodeFlags(type_flags)
        self._node_by_number[node_number] = node

    def read_subheader(self, node: MDLNode) -> None:
        """Read the subheader of a node.

        Args:
            node: Node to read subheader for
        """
        if not isinstance(node, MDLSaberNode):
            return

        # Read saber properties
        self._reader.seek(self.SABER_HEADER_OFFSET)

        saber = MDLSaber()
        saber.saber_type = MDLSaberType(self._reader.read_uint32())
        saber.saber_flags = MDLSaberFlags(self._reader.read_uint32())

        # Read blade properties
        saber.saber_length = self._reader.read_single()
        saber.saber_width = self._reader.read_single()
        saber.saber_color = Color.from_rgb_integer(self._reader.read_uint32())
        saber.saber_flare_radius = self._reader.read_single()
        saber.saber_flare_color = Color.from_rgb_integer(self._reader.read_uint32())

        # Read effect properties
        saber.blur_length = self._reader.read_single()
        saber.blur_width = self._reader.read_single()
        saber.glow_size = self._reader.read_single()
        saber.glow_intensity = self._reader.read_single()

        # Read textures
        saber.blade_texture = ResRef(self._reader.read_string(16))
        saber.hit_texture = ResRef(self._reader.read_string(16))
        saber.flare_texture = ResRef(self._reader.read_string(16))

        node.saber = saber

    def read_controllers(self, node: MDLNode) -> None:
        """Read the controllers of a node.

        Args:
            node: Node to read controllers for
        """
        # Animation controllers are handled by base animation node
        pass

    def read_controller_data(self, node: MDLNode) -> None:
        """Read the controller data of a node.

        Args:
            node: Node to read controller data for
        """
        # Animation controller data is handled by base animation node
        pass

    def read_vertex_coordinates(self, node: MDLNode) -> None:
        """Read the vertex coordinates of a node.

        Args:
            node: Node to read vertex coordinates for
        """
        if not isinstance(node, MDLSaberNode):
            return

        # Read vertex data
        vertex_count = self._reader.read_uint32()
        vertex_offset = self._reader.read_uint32()

        # Read vertices
        old_pos = self._reader.tell()
        self._reader.seek(vertex_offset + self.VERTEX_DATA_OFFSET)

        vertices: list[Vector3] = []
        for _ in range(vertex_count):
            x = self._reader.read_single()
            y = self._reader.read_single()
            z = self._reader.read_single()
            vertices.append(Vector3(x, y, z))
        node.vertices = vertices

        # Read saber vertices
        saber_vertex_offset = self._reader.read_uint32()
        self._reader.seek(saber_vertex_offset + self.VERTEX_DATA_OFFSET)

        saber_vertices: list[Vector3] = []
        for _ in range(vertex_count):
            x = self._reader.read_single()
            y = self._reader.read_single()
            z = self._reader.read_single()
            saber_vertices.append(Vector3(x, y, z))
        node.saber_vertices = saber_vertices

        # Read texture coordinates if present
        texture_count = self._reader.read_uint32()
        if texture_count > 0:
            uv_offset = self._reader.read_uint32()
            self._reader.seek(uv_offset + self.VERTEX_DATA_OFFSET)

            uvs: list[tuple[float, float]] = []
            for _ in range(vertex_count):
                u = self._reader.read_single()
                v = self._reader.read_single()
                uvs.append((u, v))
            node.uvs = uvs

        # Read normals
        normal_offset = self._reader.read_uint32()
        self._reader.seek(normal_offset + self.VERTEX_DATA_OFFSET)

        normals: list[Vector3] = []
        for _ in range(vertex_count):
            x = self._reader.read_single()
            y = self._reader.read_single()
            z = self._reader.read_single()
            normals.append(Vector3(x, y, z))
        node.normals = normals

        # Restore position
        self._reader.seek(old_pos)

    def read_faces(self, node: MDLNode) -> None:
        """Read the faces of a node.

        Args:
            node: Node to read faces for
        """
        if not isinstance(node, MDLSaberNode):
            return

        face_count = self._reader.read_uint32()
        face_offset = self._reader.read_uint32()

        self._reader.seek(face_offset + self.VERTEX_DATA_OFFSET)
        faces: list[list[int]] = []
        for _ in range(face_count):
            v1 = self._reader.read_uint32()
            v2 = self._reader.read_uint32()
            v3 = self._reader.read_uint32()
            faces.append([v1, v2, v3])
        node.faces = faces

    def read_aabb(self, node: MDLNode) -> None:
        """Read the AABB of a node.

        Args:
            node: Node to read AABB for
        """
        # Saber nodes don't have AABB data
        pass