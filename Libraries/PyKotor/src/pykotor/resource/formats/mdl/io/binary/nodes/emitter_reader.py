"""Binary reader for MDL emitter nodes."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from pykotor.resource.formats.mdl.data.exceptions import MDLReadError
from pykotor.resource.formats.mdl.data.nodes.emitter import MDLEmitterNode
from pykotor.resource.formats.mdl.io.binary.nodes.base_node_reader import MDLBinaryNodeReader
from utility.common.geometry import Vector3

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader
    from pykotor.resource.formats.mdl.data.nodes.node import MDLNode


class MDLBinaryEmitterReader(MDLBinaryNodeReader):
    """Reader for binary MDL emitter nodes."""

    def __init__(self, mdl_reader: BinaryReader, mdx_reader: BinaryReader, names: List[str], node_by_number: dict[int, MDLNode]):
        """Initialize the emitter reader.

        Args:
            mdl_reader: Reader for MDL data
            mdx_reader: Reader for MDX data (unused)
            names: List of names from the MDL file
            node_by_number: Dictionary mapping node numbers to nodes
        """
        super().__init__(mdl_reader, mdx_reader, names, node_by_number)

    def read_node(self, offset: int, parent: Optional[MDLNode] = None) -> MDLNode:
        """Read an emitter node from the file.

        Args:
            offset: Offset to node data
            parent: Parent node if any

        Returns:
            MDLNode: The loaded emitter node

        Raises:
            MDLReadError: If there is an error reading the node data
        """
        try:
            self._mdl_reader.seek(self.MDL_OFFSET + offset)

            # Read common node header
            type_flags, node_number, name_index, root_offset, parent_offset = self._read_node_header()

            # Create emitter node
            name = self._names[name_index]
            node = MDLEmitterNode(name)
            node.node_number = node_number

            if parent:
                node.parent = parent

            # Read emission properties
            node.emission_rate = self._mdl_reader.read_single()
            node.lifetime = self._mdl_reader.read_single()
            node.lifetime_random = self._mdl_reader.read_single()
            node.mass = self._mdl_reader.read_single()
            node.mass_random = self._mdl_reader.read_single()
            node.spread = self._mdl_reader.read_single()
            node.velocity = self._mdl_reader.read_single()
            node.velocity_random = self._mdl_reader.read_single()

            # Read blast properties
            node.blast_radius = self._mdl_reader.read_single()
            node.blast_length = self._mdl_reader.read_single()
            node.branch_count = self._mdl_reader.read_uint32()
            node.control_point_smoothing = self._mdl_reader.read_single()

            # Read grid properties
            node.grid_x = self._mdl_reader.read_uint32()
            node.grid_y = self._mdl_reader.read_uint32()
            node.spawn_type = self._mdl_reader.read_uint32()

            # Read script names
            script_index = self._mdl_reader.read_uint32()
            if script_index < len(self._names):
                node.update_script = self._names[script_index]

            script_index = self._mdl_reader.read_uint32()
            if script_index < len(self._names):
                node.render_script = self._names[script_index]

            # Read render properties
            node.blend_mode = self._mdl_reader.read_uint32()

            # Read chunk name
            chunk_index = self._mdl_reader.read_uint32()
            if chunk_index < len(self._names):
                node.chunk_name = self._names[chunk_index]

            # Read flags
            flags = self._mdl_reader.read_uint32()
            node.two_sided_texture = bool(flags & 0x0001)
            node.loop_particles = bool(flags & 0x0002)
            node.frame_blending = bool(flags & 0x0004)

            # Read particle arrays
            size_arr = self._read_array_definition()
            alpha_arr = self._read_array_definition()
            color_start_arr = self._read_array_definition()
            color_end_arr = self._read_array_definition()

            # Read particle flags
            flags = self._mdl_reader.read_uint32()
            node.point_to_point = bool(flags & 0x0001)
            node.point_to_point_select = bool(flags & 0x0002)
            node.affected_by_wind = bool(flags & 0x0004)
            node.tinted = bool(flags & 0x0008)
            node.random_spawn = bool(flags & 0x0010)
            node.inherit = bool(flags & 0x0020)
            node.inherit_local = bool(flags & 0x0040)
            node.splat = bool(flags & 0x0080)
            node.inherit_part = bool(flags & 0x0100)
            node.depth_texture_enabled = bool(flags & 0x0200)

            # Read texture names
            texture_index = self._mdl_reader.read_uint32()
            if texture_index < len(self._names):
                node.texture = self._names[texture_index]

            depth_texture_index = self._mdl_reader.read_uint32()
            if depth_texture_index < len(self._names):
                node.depth_texture = self._names[depth_texture_index]

            # Read size data
            if size_arr.count > 0:
                self._mdl_reader.seek(self.MDL_OFFSET + size_arr.offset)
                node.size = [self._mdl_reader.read_single() for _ in range(2)]
                node.size_random = self._mdl_reader.read_single()
                node.size_change = self._mdl_reader.read_single()

            # Read alpha data
            if alpha_arr.count > 0:
                self._mdl_reader.seek(self.MDL_OFFSET + alpha_arr.offset)
                node.alpha = [self._mdl_reader.read_single() for _ in range(2)]
                node.alpha_random = self._mdl_reader.read_single()

            # Read color data
            if color_start_arr.count > 0:
                self._mdl_reader.seek(self.MDL_OFFSET + color_start_arr.offset)
                node.color_start = [self._mdl_reader.read_single() for _ in range(3)]

            if color_end_arr.count > 0:
                self._mdl_reader.seek(self.MDL_OFFSET + color_end_arr.offset)
                node.color_end = [self._mdl_reader.read_single() for _ in range(3)]
                node.color_random = self._mdl_reader.read_single()

            # Read frame properties
            node.frame_start = self._mdl_reader.read_uint32()
            node.frame_end = self._mdl_reader.read_uint32()
            node.frame_change = self._mdl_reader.read_single()
            node.frame_random = bool(self._mdl_reader.read_uint32())

            # Read physics properties
            x = self._mdl_reader.read_single()
            y = self._mdl_reader.read_single()
            z = self._mdl_reader.read_single()
            node.gravity = Vector3(x, y, z)

            node.drag = self._mdl_reader.read_single()
            node.bounce = self._mdl_reader.read_single()
            node.friction = self._mdl_reader.read_single()

            # Read shape properties
            node.shape_type = self._mdl_reader.read_uint32()
            x = self._mdl_reader.read_single()
            y = self._mdl_reader.read_single()
            z = self._mdl_reader.read_single()
            node.shape_size = Vector3(x, y, z)

            # Read grid dimensions
            node.grid_width = self._mdl_reader.read_single()
            node.grid_height = self._mdl_reader.read_single()

            # Read texture grid
            node.texture_rows = self._mdl_reader.read_uint32()
            node.texture_cols = self._mdl_reader.read_uint32()

            # Read particle limits
            node.max_particles = self._mdl_reader.read_uint32()
            node.dead_space = self._mdl_reader.read_single()

            # Read child nodes
            self._read_children(node)

            return node

        except Exception as e:
            raise MDLReadError(f"Error reading emitter node: {str(e)}")
