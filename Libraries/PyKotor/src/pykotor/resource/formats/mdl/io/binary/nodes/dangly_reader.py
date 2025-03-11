"""Binary reader for MDL dangly mesh nodes."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, cast

from pykotor.resource.formats.mdl.data.exceptions import MDLReadError
from pykotor.resource.formats.mdl.data.nodes.dangly import MDLDanglyNode
from pykotor.resource.formats.mdl.io.binary.nodes.trimesh_reader import MDLBinaryTrimeshReader
from utility.common.geometry import Vector3

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader
    from pykotor.resource.formats.mdl.data.nodes.node import MDLNode


class MDLBinaryDanglyReader(MDLBinaryTrimeshReader):
    """Reader for binary MDL dangly mesh nodes."""

    def __init__(self, mdl_reader: BinaryReader, mdx_reader: BinaryReader, names: List[str], node_by_number: dict[int, MDLNode]):
        """Initialize the dangly mesh reader.

        Args:
            mdl_reader: Reader for MDL data
            mdx_reader: Reader for MDX data
            names: List of names from the MDL file
            node_by_number: Dictionary mapping node numbers to nodes
        """
        super().__init__(mdl_reader, mdx_reader, names, node_by_number)

    def read_node(self, offset: int, parent: Optional[MDLNode] = None) -> MDLNode:
        """Read a dangly mesh node from the file.

        Args:
            offset: Offset to node data
            parent: Parent node if any

        Returns:
            MDLNode: The loaded dangly mesh node

        Raises:
            MDLReadError: If there is an error reading the node data
        """
        try:
            # First read base trimesh data
            base_node = super().read_node(offset, parent)
            trimesh_node = cast(MDLDanglyNode, base_node)
            trimesh_node.__class__ = MDLDanglyNode  # HACK:

            # Convert to dangly node
            dangly_node = MDLDanglyNode(trimesh_node.name)
            dangly_node.node_number = trimesh_node.node_number
            dangly_node.parent = trimesh_node.parent
            dangly_node.children = trimesh_node.children

            # Copy trimesh properties
            dangly_node.vertices = trimesh_node.vertices
            dangly_node.normals = trimesh_node.normals
            dangly_node.uv1 = trimesh_node.uv1
            dangly_node.uv2 = trimesh_node.uv2
            dangly_node.colors = trimesh_node.colors
            dangly_node.faces = trimesh_node.faces
            dangly_node.face_materials = trimesh_node.face_materials
            dangly_node.face_normals = trimesh_node.face_normals
            dangly_node.face_distances = trimesh_node.face_distances
            dangly_node.diffuse = trimesh_node.diffuse
            dangly_node.ambient = trimesh_node.ambient
            dangly_node.self_illumination = trimesh_node.self_illumination
            dangly_node.transparency = trimesh_node.transparency
            dangly_node.texture = trimesh_node.texture
            dangly_node.texture2 = trimesh_node.texture2
            dangly_node.render = trimesh_node.render
            dangly_node.shadow = trimesh_node.shadow
            dangly_node.beaming = trimesh_node.beaming
            dangly_node.render_environment_map = trimesh_node.render_environment_map
            dangly_node.background_geometry = trimesh_node.background_geometry
            dangly_node.animate_uv = trimesh_node.animate_uv
            dangly_node.uv_direction = trimesh_node.uv_direction
            dangly_node.uv_jitter = trimesh_node.uv_jitter
            dangly_node.uv_jitter_speed = trimesh_node.uv_jitter_speed
            dangly_node.rotate_texture = trimesh_node.rotate_texture
            dangly_node.lightmapped = trimesh_node.lightmapped
            dangly_node.dirt_enabled = trimesh_node.dirt_enabled
            dangly_node.dirt_texture = trimesh_node.dirt_texture
            dangly_node.dirt_worldspace = trimesh_node.dirt_worldspace
            dangly_node.hologram_donotdraw = trimesh_node.hologram_donotdraw

            # Read dangly-specific data
            self._mdl_reader.seek(self.MDL_OFFSET + offset)

            # Skip trimesh data to get to dangly data
            self._mdl_reader.skip(0x158)  # Size of trimesh header

            # Read displacement limits
            dangly_node.displacement_max = self._mdl_reader.read_single()
            dangly_node.displacement_min = self._mdl_reader.read_single()
            dangly_node.period = self._mdl_reader.read_single()
            dangly_node.tightness = self._mdl_reader.read_single()

            # Read force properties
            x = self._mdl_reader.read_single()
            y = self._mdl_reader.read_single()
            z = self._mdl_reader.read_single()
            dangly_node.force_point = Vector3(x, y, z)
            dangly_node.force_radius = self._mdl_reader.read_single()
            dangly_node.force_type = self._mdl_reader.read_uint32()

            # Read constraint flags
            flags = self._mdl_reader.read_uint32()
            dangly_node.constrain_x = bool(flags & 0x0001)
            dangly_node.constrain_y = bool(flags & 0x0002)
            dangly_node.constrain_z = bool(flags & 0x0004)

            # Read vertex data arrays
            displacement_arr = self._read_array_definition()
            constraints_arr = self._read_array_definition()
            displacement_map_arr = self._read_array_definition()

            # Read displacement values
            if displacement_arr.count > 0:
                self._mdl_reader.seek(self.MDL_OFFSET + displacement_arr.offset)
                for _ in range(displacement_arr.count):
                    value = self._mdl_reader.read_single()
                    dangly_node.displacement.append(value)

            # Read constraint vectors
            if constraints_arr.count > 0:
                self._mdl_reader.seek(self.MDL_OFFSET + constraints_arr.offset)
                for _ in range(constraints_arr.count):
                    x = self._mdl_reader.read_single()
                    y = self._mdl_reader.read_single()
                    z = self._mdl_reader.read_single()
                    dangly_node.constraints.append(Vector3(x, y, z))

            # Read displacement map values
            if displacement_map_arr.count > 0:
                self._mdl_reader.seek(self.MDL_OFFSET + displacement_map_arr.offset)
                for _ in range(displacement_map_arr.count):
                    value = self._mdl_reader.read_single()
                    dangly_node.displacement_map.append(value)

            return dangly_node

        except Exception as e:
            raise MDLReadError(f"Error reading dangly mesh node: {str(e)}")
