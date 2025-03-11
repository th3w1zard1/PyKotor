"""Binary reader for MDL AABB nodes."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, cast

from pykotor.resource.formats.mdl.data.exceptions import MDLReadError
from pykotor.resource.formats.mdl.data.nodes.aabb import MDLAABBNode
from pykotor.resource.formats.mdl.io.binary.nodes.base_node_reader import MDLBinaryNodeReader
from utility.common.geometry import Vector3

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader
    from pykotor.resource.formats.mdl.data.nodes.node import MDLNode


class MDLBinaryAABBReader(MDLBinaryNodeReader):
    """Reader for binary MDL AABB nodes."""

    def __init__(self, mdl_reader: BinaryReader, mdx_reader: BinaryReader, names: List[str], node_by_number: dict[int, MDLNode]):
        """Initialize the AABB reader.

        Args:
            mdl_reader: Reader for MDL data
            mdx_reader: Reader for MDX data (unused)
            names: List of names from the MDL file
            node_by_number: Dictionary mapping node numbers to nodes
        """
        super().__init__(mdl_reader, mdx_reader, names, node_by_number)

    def read_node(self, offset: int, parent: Optional[MDLNode] = None) -> MDLNode:
        """Read an AABB node from the file.

        Args:
            offset: Offset to node data
            parent: Parent node if any

        Returns:
            MDLNode: The loaded AABB node

        Raises:
            MDLReadError: If there is an error reading the node data
        """
        try:
            self._mdl_reader.seek(self.MDL_OFFSET + offset)

            # Read common node header
            type_flags, node_number, name_index, root_offset, parent_offset = self._read_node_header()

            # Create AABB node
            name = self._names[name_index]
            node = MDLAABBNode(name)
            node.node_number = node_number

            if parent:
                node.parent = parent

            # Read bounding box
            x = self._mdl_reader.read_single()
            y = self._mdl_reader.read_single()
            z = self._mdl_reader.read_single()
            node.min_point = Vector3(x, y, z)

            x = self._mdl_reader.read_single()
            y = self._mdl_reader.read_single()
            z = self._mdl_reader.read_single()
            node.max_point = Vector3(x, y, z)

            # Read bounding sphere
            x = self._mdl_reader.read_single()
            y = self._mdl_reader.read_single()
            z = self._mdl_reader.read_single()
            node.center = Vector3(x, y, z)
            node.radius = self._mdl_reader.read_single()

            # Read tree structure
            left_offset = self._mdl_reader.read_uint32()
            right_offset = self._mdl_reader.read_uint32()

            # Read leaf flag
            node.is_leaf = bool(self._mdl_reader.read_uint32())

            # Read leaf data if this is a leaf node
            if node.is_leaf:
                # Read face indices array
                face_indices_arr = self._read_array_definition()
                if face_indices_arr.count > 0:
                    self._mdl_reader.seek(self.MDL_OFFSET + face_indices_arr.offset)
                    for _ in range(face_indices_arr.count):
                        index = self._mdl_reader.read_uint32()
                        node.face_indices.append(index)

                # Read faces array
                faces_arr = self._read_array_definition()
                if faces_arr.count > 0:
                    self._mdl_reader.seek(self.MDL_OFFSET + faces_arr.offset)
                    for _ in range(faces_arr.count):
                        face = [self._mdl_reader.read_uint16() for _ in range(3)]
                        node.faces.append(face)

                # Read face normals array
                face_normals_arr = self._read_array_definition()
                if face_normals_arr.count > 0:
                    self._mdl_reader.seek(self.MDL_OFFSET + face_normals_arr.offset)
                    for _ in range(face_normals_arr.count):
                        x = self._mdl_reader.read_single()
                        y = self._mdl_reader.read_single()
                        z = self._mdl_reader.read_single()
                        node.face_normals.append(Vector3(x, y, z))

                # Read face distances array
                face_distances_arr = self._read_array_definition()
                if face_distances_arr.count > 0:
                    self._mdl_reader.seek(self.MDL_OFFSET + face_distances_arr.offset)
                    for _ in range(face_distances_arr.count):
                        distance = self._mdl_reader.read_single()
                        node.face_distances.append(distance)

                # Read vertices array
                vertices_arr = self._read_array_definition()
                if vertices_arr.count > 0:
                    self._mdl_reader.seek(self.MDL_OFFSET + vertices_arr.offset)
                    for _ in range(vertices_arr.count):
                        x = self._mdl_reader.read_single()
                        y = self._mdl_reader.read_single()
                        z = self._mdl_reader.read_single()
                        node.vertices.append(Vector3(x, y, z))

            # Read child nodes if this is not a leaf
            else:
                if left_offset > 0:
                    node.left_node = cast(MDLAABBNode, self.read_node(left_offset, node))
                if right_offset > 0:
                    node.right_node = cast(MDLAABBNode, self.read_node(right_offset, node))

            return node

        except Exception as e:
            raise MDLReadError(f"Error reading AABB node: {str(e)}")
