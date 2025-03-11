"""Binary reader for MDL light nodes."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from pykotor.resource.formats.mdl.data.exceptions import MDLReadError
from pykotor.resource.formats.mdl.data.nodes.light import MDLLightNode
from pykotor.resource.formats.mdl.io.binary.nodes.base_node_reader import MDLBinaryNodeReader

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader
    from pykotor.resource.formats.mdl.data.nodes.node import MDLNode


class MDLBinaryLightReader(MDLBinaryNodeReader):
    """Reader for binary MDL light nodes."""

    def __init__(self, mdl_reader: BinaryReader, mdx_reader: BinaryReader, names: List[str], node_by_number: dict[int, MDLNode]):
        """Initialize the light reader.

        Args:
            mdl_reader: Reader for MDL data
            mdx_reader: Reader for MDX data (unused)
            names: List of names from the MDL file
            node_by_number: Dictionary mapping node numbers to nodes
        """
        super().__init__(mdl_reader, mdx_reader, names, node_by_number)

    def read_node(self, offset: int, parent: Optional[MDLNode] = None) -> MDLNode:
        """Read a light node from the file.

        Args:
            offset: Offset to node data
            parent: Parent node if any

        Returns:
            MDLNode: The loaded light node

        Raises:
            MDLReadError: If there is an error reading the node data
        """
        try:
            self._mdl_reader.seek(self.MDL_OFFSET + offset)

            # Read common node header
            type_flags, node_number, name_index, root_offset, parent_offset = self._read_node_header()

            # Create light node
            name = self._names[name_index]
            node = MDLLightNode(name)
            node.node_number = node_number

            if parent:
                node.parent = parent

            # Read light properties
            node.flare_radius = self._mdl_reader.read_single()
            node.multiplier = self._mdl_reader.read_single()
            node.light_priority = self._mdl_reader.read_uint32()
            node.ambient_only = bool(self._mdl_reader.read_uint32())
            node.light_type = self._mdl_reader.read_uint32()  # Changed from dynamic_type
            node.affect_dynamic = bool(self._mdl_reader.read_uint32())
            node.shadow = bool(self._mdl_reader.read_uint32())
            node.has_flare = bool(self._mdl_reader.read_uint32())
            node.fading_light = bool(self._mdl_reader.read_uint32())

            # Read spotlight properties
            node.inner_angle = self._mdl_reader.read_single()
            node.outer_angle = self._mdl_reader.read_single()
            node.spot_falloff = self._mdl_reader.read_single()

            # Read light colors
            r = self._mdl_reader.read_single()
            g = self._mdl_reader.read_single()
            b = self._mdl_reader.read_single()
            node.color = [r, g, b]

            # Read ambient color
            r = self._mdl_reader.read_single()
            g = self._mdl_reader.read_single()
            b = self._mdl_reader.read_single()
            node.ambient_color = [r, g, b]

            # Read light radius and fade properties
            node.radius = self._mdl_reader.read_single()
            node.fade_amt = self._mdl_reader.read_single()
            node.fade_radius = self._mdl_reader.read_single()

            # Read animation properties
            node.period = self._mdl_reader.read_single()
            node.interval = self._mdl_reader.read_single()
            node.phase = self._mdl_reader.read_single()

            # Read flare data
            flare_sizes_arr = self._read_array_definition()
            flare_positions_arr = self._read_array_definition()
            flare_colors_arr = self._read_array_definition()
            texture_names_arr = self._read_array_definition()

            # Read flare sizes
            if flare_sizes_arr.count > 0:
                self._mdl_reader.seek(self.MDL_OFFSET + flare_sizes_arr.offset)
                node.flare_sizes = [self._mdl_reader.read_single() for _ in range(flare_sizes_arr.count)]

            # Read flare positions
            if flare_positions_arr.count > 0:
                self._mdl_reader.seek(self.MDL_OFFSET + flare_positions_arr.offset)
                node.flare_positions = [self._mdl_reader.read_single() for _ in range(flare_positions_arr.count)]

            # Read flare colors
            if flare_colors_arr.count > 0:
                self._mdl_reader.seek(self.MDL_OFFSET + flare_colors_arr.offset)
                colors = []
                for _ in range(flare_colors_arr.count // 3):
                    r = self._mdl_reader.read_single()
                    g = self._mdl_reader.read_single()
                    b = self._mdl_reader.read_single()
                    colors.append([r, g, b])
                node.flare_color_shifts = colors

            # Read texture names
            if texture_names_arr.count > 0:
                self._mdl_reader.seek(self.MDL_OFFSET + texture_names_arr.offset)
                for _ in range(texture_names_arr.count):
                    name_index = self._mdl_reader.read_uint32()
                    if name_index < len(self._names):
                        node.flare_textures.append(self._names[name_index])

            # Read flags
            flags = self._mdl_reader.read_uint32()
            node.dynamic = bool(flags & 0x0001)
            node.affect_dynamic = bool(flags & 0x0002)
            node.hologram_effect = bool(flags & 0x0004)

            # Read child nodes
            self._read_children(node)

            return node

        except Exception as e:
            raise MDLReadError(f"Error reading light node: {str(e)}")