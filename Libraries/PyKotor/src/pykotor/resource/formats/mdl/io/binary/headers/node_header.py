"""Node header data structures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Literal

from pykotor.resource.formats.mdl.data.enums import MDLComponentType
from utility.common.geometry import Vector3, Vector4

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader, BinaryWriter


from pykotor.resource.formats.mdl.data.exceptions import NodeHeaderError


class InvalidNodeDataError(NodeHeaderError):
    """Raised when node data is invalid or corrupted."""


class NodeBasicFieldsError(NodeHeaderError):
    """Raised when there's an error reading/writing basic node fields."""


class NodePositionError(NodeHeaderError):
    """Raised when there's an error with position/orientation data."""


class NodeHierarchyError(NodeHeaderError):
    """Raised when there's an error with node hierarchy data."""


class NodeControllerError(NodeHeaderError):
    """Raised when there's an error with controller data."""


@dataclass
class _NodeHeader:
    """Header data for model nodes.

    A node represents a single object in the model hierarchy, which can be
    a mesh, light, emitter, or other type of object. The node header contains
    basic information about the node's position in the hierarchy and any
    attached data.

    Attributes:
        type_id (MDLComponentType): Enum representing the type of node (mesh, light, emitter, etc).
        name_index (int): Index into name table.
        node_id (int): Unique node identifier.
        padding0 (int): Padding for alignment.
        offset_to_root (int): Offset to root node.
        offset_to_parent (int): Offset to parent node.
        position (Vector3): Node position relative to parent.
        orientation (Vector4): Node orientation as quaternion (w,x,y,z).
        offset_to_children (int): Offset to child node array.
        children_count (int): Number of child nodes.
        children_count2 (int): ???.
        offset_to_controllers (int): Offset to controller array.
        controller_count (int): Number of controllers.
        controller_count2 (int): ???.
        offset_to_controller_data (int): Offset to controller data.
        controller_data_length (int): Length of controller data in bytes.
        controller_data_length2 (int): ???.
    """

    SIZE: ClassVar[Literal[80]] = 0x50
    """Size of node header in bytes."""

    type_id: MDLComponentType = MDLComponentType.DUMMY
    name_index: int = 0
    node_id: int = 0
    padding0: int = 0
    offset_to_root: int = 0
    offset_to_parent: int = 0
    position: Vector3 = Vector3.from_null()
    orientation: Vector4 = Vector4(0, 0, 0, 1)  # Default to identity quaternion
    offset_to_children: int = 0
    children_count: int = 0
    children_count2: int = 0
    offset_to_controllers: int = 0
    controller_count: int = 0
    controller_count2: int = 0
    offset_to_controller_data: int = 0
    controller_data_length: int = 0
    controller_data_length2: int = 0

    def read(self, reader: BinaryReader) -> _NodeHeader:
        """Read node header data from a binary stream.

        Args:
            reader: Binary reader to read data from.

        Returns:
            The populated node header instance.

        Raises:
            InvalidNodeDataError: If the data read is invalid or corrupted.
        """
        try:
            # Read header fields
            self._read_basic_fields(reader)
            self._read_position_orientation(reader)
            self._read_hierarchy_fields(reader)
            self._read_controller_fields(reader)
            return self
        except Exception as e:
            raise InvalidNodeDataError(f"Failed to read node header: {str(e)}") from e

    def write(self, writer: BinaryWriter):
        """Write node header data to a binary stream.

        Args:
            writer: Binary writer to write data to.

        Raises:
            InvalidNodeDataError: If there's an error writing the data.
        """
        try:
            # Write header fields
            self._write_basic_fields(writer)
            self._write_position_orientation(writer)
            self._write_hierarchy_fields(writer)
            self._write_controller_fields(writer)
        except Exception as e:
            raise InvalidNodeDataError(f"Failed to write node header: {str(e)}") from e

    def _read_basic_fields(self, reader: BinaryReader):
        """Read basic header fields."""
        try:
            self.type_id = MDLComponentType(reader.read_uint16())
            self.node_id = reader.read_uint16()
            self.name_index = reader.read_uint16()
            self.padding0 = reader.read_uint16()
            self.offset_to_root = reader.read_uint32()
            self.offset_to_parent = reader.read_uint32()
        except Exception as e:
            raise NodeBasicFieldsError(f"Failed to read basic node fields at position {reader.position}. " f"Error: {str(e)}") from e

    def _read_position_orientation(self, reader: BinaryReader):
        """Read position and orientation data."""
        try:
            self.position = reader.read_vector3()
            self.orientation = reader.read_vector4()
        except Exception as e:
            raise NodePositionError(f"Failed to read position/orientation data at position {reader.position}. " f"Error: {str(e)}") from e

    def _read_hierarchy_fields(self, reader: BinaryReader):
        """Read hierarchy-related fields."""
        try:
            self.offset_to_children = reader.read_uint32()
            self.children_count = reader.read_uint32()
            self.children_count2 = reader.read_uint32()
        except Exception as e:
            raise NodeHierarchyError(f"Failed to read hierarchy fields at position {reader.position}. " f"Error: {str(e)}") from e

    def _read_controller_fields(self, reader: BinaryReader):
        """Read controller-related fields."""
        try:
            self.offset_to_controllers = reader.read_uint32()
            self.controller_count = reader.read_uint32()
            self.controller_count2 = reader.read_uint32()
            self.offset_to_controller_data = reader.read_uint32()
            self.controller_data_length = reader.read_uint32()
            self.controller_data_length2 = reader.read_uint32()
        except Exception as e:
            raise NodeControllerError(f"Failed to read controller fields at position {reader.position}. " f"Error: {str(e)}") from e

    def _write_basic_fields(self, writer: BinaryWriter):
        """Write basic header fields."""
        try:
            writer.write_uint16(self.type_id.value)
            writer.write_uint16(self.node_id)
            writer.write_uint16(self.name_index)
            writer.write_uint16(self.padding0)
            writer.write_uint32(self.offset_to_root)
            writer.write_uint32(self.offset_to_parent)
        except Exception as e:
            raise NodeBasicFieldsError(f"Failed to write basic node fields at position {writer.position}. " f"Error: {str(e)}") from e

    def _write_position_orientation(self, writer: BinaryWriter):
        """Write position and orientation data."""
        try:
            writer.write_vector3(self.position)
            writer.write_single(self.orientation.w)
            writer.write_single(self.orientation.x)
            writer.write_single(self.orientation.y)
            writer.write_single(self.orientation.z)
        except Exception as e:
            raise NodePositionError(f"Failed to write position/orientation data at position {writer.position}. " f"Error: {str(e)}") from e

    def _write_hierarchy_fields(self, writer: BinaryWriter):
        """Write hierarchy-related fields."""
        try:
            writer.write_uint32(self.offset_to_children)
            writer.write_uint32(self.children_count)
            writer.write_uint32(self.children_count2)
        except Exception as e:
            raise NodeHierarchyError(f"Failed to write hierarchy fields at position {writer.position}. " f"Error: {str(e)}") from e

    def _write_controller_fields(self, writer: BinaryWriter):
        """Write controller-related fields."""
        try:
            writer.write_uint32(self.offset_to_controllers)
            writer.write_uint32(self.controller_count)
            writer.write_uint32(self.controller_count2)
            writer.write_uint32(self.offset_to_controller_data)
            writer.write_uint32(self.controller_data_length)
            writer.write_uint32(self.controller_data_length2)
        except Exception as e:
            raise NodeControllerError(f"Failed to write controller fields at position {writer.position}. " f"Error: {str(e)}") from e
