from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from utility.common.geometry import Vector3

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader, BinaryWriter


class _Face:
    """Face data for mesh geometry.

    A face represents a triangle in the mesh, defined by three vertex indices
    and additional properties like material and adjacency information.

    Attributes:
        SIZE (ClassVar[Literal[32]]): Size of face structure in bytes.
        normal (Vector3): Face normal vector.
        plane_coefficient (float): Distance from origin to plane.
        material (int): Material/surface type index.
        adjacent1 (int): Index of adjacent face 1.
        adjacent2 (int): Index of adjacent face 2.
        adjacent3 (int): Index of adjacent face 3.
        vertex1 (int): Index of first vertex.
        vertex2 (int): Index of second vertex.
        vertex3 (int): Index of third vertex.
    """

    SIZE: ClassVar[Literal[32]] = 32
    """Size of face structure in bytes."""

    def __init__(self):
        self.normal: Vector3 = Vector3.from_null()
        self.plane_coefficient: float = 0.0
        self.material: int = 0
        self.adjacent1: int = 0
        self.adjacent2: int = 0
        self.adjacent3: int = 0
        self.vertex1: int = 0
        self.vertex2: int = 0
        self.vertex3: int = 0

    def read(self, reader: BinaryReader) -> _Face:
        """Read face data from a binary stream.

        Args:
            reader: Binary reader to read data from.

        Returns:
            The populated face instance.
        """
        self.normal = reader.read_vector3()
        self.plane_coefficient = reader.read_single()
        self.material = reader.read_uint32()
        self.adjacent1 = reader.read_uint16()
        self.adjacent2 = reader.read_uint16()
        self.adjacent3 = reader.read_uint16()
        self.vertex1 = reader.read_uint16()
        self.vertex2 = reader.read_uint16()
        self.vertex3 = reader.read_uint16()
        return self

    def write(self, writer: BinaryWriter):
        """Write face data to a binary stream.

        Args:
            writer: Binary writer to write data to.
        """
        writer.write_vector3(self.normal)
        writer.write_single(self.plane_coefficient)
        writer.write_uint32(self.material)
        writer.write_uint16(self.adjacent1)
        writer.write_uint16(self.adjacent2)
        writer.write_uint16(self.adjacent3)
        writer.write_uint16(self.vertex1)
        writer.write_uint16(self.vertex2)
        writer.write_uint16(self.vertex3)
