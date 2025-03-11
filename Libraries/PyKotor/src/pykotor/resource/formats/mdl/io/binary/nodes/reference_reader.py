"""Binary reader for MDL reference nodes."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from pykotor.resource.formats.mdl.data.exceptions import MDLReadError
from pykotor.resource.formats.mdl.data.nodes.reference import MDLReferenceNode
from pykotor.resource.formats.mdl.io.binary.nodes.base_node_reader import MDLBinaryNodeReader
from utility.common.geometry import Vector3

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader
    from pykotor.resource.formats.mdl.data.nodes.node import MDLNode


class MDLBinaryReferenceReader(MDLBinaryNodeReader):
    """Reader for binary MDL reference nodes."""

    def __init__(self, mdl_reader: BinaryReader, mdx_reader: BinaryReader, names: List[str], node_by_number: dict[int, MDLNode]):
        """Initialize the reference reader.

        Args:
            mdl_reader: Reader for MDL data
            mdx_reader: Reader for MDX data (unused)
            names: List of names from the MDL file
            node_by_number: Dictionary mapping node numbers to nodes
        """
        super().__init__(mdl_reader, mdx_reader, names, node_by_number)

    def read_node(self, offset: int, parent: Optional[MDLNode] = None) -> MDLNode:
        """Read a reference node from the file.

        Args:
            offset: Offset to node data
            parent: Parent node if any

        Returns:
            MDLNode: The loaded reference node

        Raises:
            MDLReadError: If there is an error reading the node data
        """
        try:
            self._mdl_reader.seek(self.MDL_OFFSET + offset)

            # Read common node header
            type_flags, node_number, name_index, root_offset, parent_offset = self._read_node_header()

            # Create reference node
            name = self._names[name_index]
            node = MDLReferenceNode(name)
            node.node_number = node_number

            if parent:
                node.parent = parent

            # Read reference targets
            model_name_index = self._mdl_reader.read_uint32()
            node_name_index = self._mdl_reader.read_uint32()

            if model_name_index < len(self._names):
                node.ref_model = self._names[model_name_index]
            if node_name_index < len(self._names):
                node.ref_node = self._names[node_name_index]

            # Read transform
            x = self._mdl_reader.read_single()
            y = self._mdl_reader.read_single()
            z = self._mdl_reader.read_single()
            node.position = Vector3(x, y, z)

            qx = self._mdl_reader.read_single()
            qy = self._mdl_reader.read_single()
            qz = self._mdl_reader.read_single()
            qw = self._mdl_reader.read_single()
            node.orientation = [qx, qy, qz, qw]

            x = self._mdl_reader.read_single()
            y = self._mdl_reader.read_single()
            z = self._mdl_reader.read_single()
            node.scale = Vector3(x, y, z)

            # Read reattach flags
            flags = self._mdl_reader.read_uint32()
            node.reattach_mesh = bool(flags & 0x0001)
            node.reattach_anim = bool(flags & 0x0002)
            node.reattach_walkmesh = bool(flags & 0x0004)
            node.reattach_dangly = bool(flags & 0x0008)
            node.reattach_skin = bool(flags & 0x0010)
            node.reattach_aabb = bool(flags & 0x0020)

            # Read child nodes
            self._read_children(node)

            return node

        except Exception as e:
            raise MDLReadError(f"Error reading reference node: {str(e)}")

