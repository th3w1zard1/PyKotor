"""Base class for binary MDL node readers."""
from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pykotor.resource.formats.mdl.data.exceptions import MDLReadError
from pykotor.resource.formats.mdl.io.base.node_reader import MDLNodeReader

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader
    from pykotor.resource.formats.mdl.data.nodes.node import MDLNode


@dataclass
class ArrayDefinition:
    """Array definition in MDL format."""
    offset: int
    count: int
    count2: int  # Should match count, used for validation


class MDLBinaryNodeReader(MDLNodeReader):
    """Base class for binary MDL node readers."""

    # Standard MDL header size
    MDL_OFFSET: int = 12

    # Function pointer size
    FUNC_PTR_SIZE: int = 8

    def __init__(self, mdl_reader: BinaryReader, mdx_reader: BinaryReader, names: list[str], node_by_number: dict[int, MDLNode]):
        """Initialize the node reader.

        Args:
            mdl_reader: The reader to use for reading node data
            mdx_reader: The reader to use for reading MDX data
            names: List of names from the MDL file
            node_by_number: Dictionary mapping node numbers to nodes
        """
        super().__init__(mdl_reader, names, node_by_number)
        self._mdx_reader: BinaryReader = mdx_reader

    @abstractmethod
    def read_node(self, parent: MDLNode | None = None, offset: int = 0) -> MDLNode:
        """Read a node from the file.

        Args:
            parent: Parent node if any

        Returns:
            MDLNode: The loaded node

        Raises:
            MDLReadError: If there is an error reading the node data
        """

    def read_properties(self, node: MDLNode) -> None:
        """Read node properties.

        Args:
            node: Node to read properties for

        Raises:
            MDLReadError: If there is an error reading properties
        """

    def read_geometry(self, node: MDLNode) -> None:
        """Read node geometry data.

        Args:
            node: Node to read geometry for

        Raises:
            MDLReadError: If there is an error reading geometry
        """

    def read_animation(self, node: MDLNode) -> None:
        """Read node animation data.

        Args:
            node: Node to read animation for

        Raises:
            MDLReadError: If there is an error reading animation
        """

    def _read_node_header(self) -> tuple[int, int, int, int, int]:
        """Read common node header data.

        Returns:
            tuple: (type_flags, node_number, name_index, root_offset, parent_offset)

        Raises:
            MDLReadError: If there is an error reading the header
        """
        try:
            # Skip function pointers
            self._reader.skip(self.FUNC_PTR_SIZE)

            # Read node header
            type_flags = self._reader.read_uint16()
            node_number = self._reader.read_uint16()
            name_index = self._reader.read_uint16()
            self._reader.skip(2)  # padding
            root_offset = self._reader.read_uint32()
            parent_offset = self._reader.read_uint32()

            if name_index >= len(self._names):
                raise MDLReadError(f"Invalid name index {name_index}, max is {len(self._names)-1}")

            return type_flags, node_number, name_index, root_offset, parent_offset

        except Exception as e:
            raise MDLReadError(f"Error reading node header: {str(e)}")

    def _read_array_definition(self) -> ArrayDefinition:
        """Read an array definition.

        Returns:
            ArrayDefinition: The array definition

        Raises:
            MDLReadError: If there is an error reading the array definition
        """
        try:
            offset = self._reader.read_uint32()
            count1 = self._reader.read_uint32()
            count2 = self._reader.read_uint32()

            if count1 != count2:
                raise MDLReadError(f"Array count mismatch: count1={count1}, count2={count2}")

            if offset < 0:
                raise MDLReadError(f"Invalid array offset: {offset}")

            if count1 < 0:
                raise MDLReadError(f"Invalid array count: {count1}")

            return ArrayDefinition(offset, count1, count2)

        except Exception as e:
            raise MDLReadError(f"Error reading array definition: {str(e)}")

    def read_children(self, node: MDLNode) -> None:
        """Read child nodes.

        Args:
            node: Parent node to add children to

        Raises:
            MDLReadError: If there is an error reading child nodes
        """
        try:
            children_arr = self._read_array_definition()

            if children_arr.count > 0:
                old_pos = self._reader.tell()
                self._reader.seek(self.MDL_OFFSET + children_arr.offset)
                child_offsets = [self._reader.read_uint32() for _ in range(children_arr.count)]

                # Import here to avoid circular imports
                from pykotor.resource.formats.mdl.io.binary.nodes.node_factory import MDLBinaryNodeReaderFactory
                factory = MDLBinaryNodeReaderFactory(self._reader, self._mdx_reader, self._names, self._node_by_number)

                for child_offset in child_offsets:
                    # Read child node header to get type
                    self._reader.seek(self.MDL_OFFSET + child_offset)
                    self._reader.skip(self.FUNC_PTR_SIZE)  # Skip function pointers
                    type_flags = self._reader.read_uint16()
                    self._reader.seek(self.MDL_OFFSET + child_offset)  # Reset position

                    # Create appropriate reader and read child node
                    reader = factory.create_reader(type_flags)
                    child = reader.read_node(node)
                    node.add_child(child)

                self._reader.seek(old_pos)

        except Exception as e:
            raise MDLReadError(f"Error reading child nodes: {str(e)}")