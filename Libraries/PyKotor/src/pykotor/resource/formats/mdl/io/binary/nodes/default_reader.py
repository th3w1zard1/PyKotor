"""Default binary reader for unimplemented MDL node types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional

from pykotor.resource.formats.mdl.data.exceptions import MDLReadError
from pykotor.resource.formats.mdl.data.nodes.node import MDLNode
from pykotor.resource.formats.mdl.io.binary.nodes.base_node_reader import MDLBinaryNodeReader

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader


class MDLDefaultBinaryNodeReader(MDLBinaryNodeReader):
    """Default reader for unimplemented node types.

    This reader only reads the common node header and children, ignoring any
    type-specific data. It should only be used as a fallback for node types
    that don't have specific implementations.
    """

    def __init__(self, mdl_reader: BinaryReader, mdx_reader: BinaryReader, names: List[str], node_by_number: Dict[int, MDLNode]):
        """Initialize the reader.

        Args:
            mdl_reader: The reader to use for reading node data
            mdx_reader: The reader to use for reading MDX data (unused)
            names: List of names from the MDL file
            node_by_number: Dictionary mapping node numbers to nodes
        """
        super().__init__(mdl_reader, mdx_reader, names, node_by_number)

    def read_node(self, offset: int, parent: Optional[MDLNode] = None) -> MDLNode:
        """Read a basic node from the file.

        This reader only reads the common node header and children, ignoring any
        type-specific data. It should only be used as a fallback for unimplemented
        node types.

        Args:
            offset: Offset to node data
            parent: Parent node if any

        Returns:
            MDLNode: The loaded node

        Raises:
            MDLReadError: If there is an error reading the node data
        """
        try:
            self._mdl_reader.seek(self.MDL_OFFSET + offset)

            # Read common node header
            type_flags, node_number, name_index, root_offset, parent_offset = self._read_node_header()

            # Create basic node
            name = self._names[name_index]
            node = MDLNode(name)
            node.node_number = node_number

            if parent:
                node.parent = parent

            # Skip type-specific data and read children
            self._read_children(node)

            return node

        except Exception as e:
            raise MDLReadError(f"Error reading node: {str(e)}")
