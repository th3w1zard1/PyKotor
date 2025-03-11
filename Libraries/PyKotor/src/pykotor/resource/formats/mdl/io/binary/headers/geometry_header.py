from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from pykotor.common.misc import ResRef

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader, BinaryWriter


class _GeometryHeader:
    """Header data for model geometry.

    The geometry header contains basic information about the model's structure,
    including function pointers, model name, and node hierarchy details.

    Attributes:
        function_pointer0 (int): First function pointer.
        function_pointer1 (int): Second function pointer.
        model_name (ResRef): Name of the model.
        root_node_offset (int): Offset to root node.
        node_count (int): Number of nodes.
        unknown0 (bytes): Unknown data.
        geometry_type (int): Type of geometry.
        padding (bytes): Padding for alignment.
    """

    SIZE: ClassVar[Literal[80]] = 0x50
    """Size of geometry header in bytes."""

    # Function pointers for different model types
    K1_FUNCTION_POINTER0: ClassVar[Literal[4273776]] = 0x413670
    """Kotor 1 function pointer 0."""
    K2_FUNCTION_POINTER0: ClassVar[Literal[4285200]] = 0x416310
    """Kotor 2 function pointer 0."""
    K1_ANIM_FUNCTION_POINTER0: ClassVar[Literal[4273392]] = 0x4134F0
    """Kotor 1 animation function pointer 0."""
    K2_ANIM_FUNCTION_POINTER0: ClassVar[Literal[4284816]] = 0x416190
    """Kotor 2 animation function pointer 0."""

    K1_FUNCTION_POINTER1: ClassVar[Literal[4216096]] = 0x405520
    """Kotor 1 function pointer 1."""
    K2_FUNCTION_POINTER1: ClassVar[Literal[4216320]] = 0x405600
    """Kotor 2 function pointer 1."""
    K1_ANIM_FUNCTION_POINTER1: ClassVar[Literal[4451552]] = 0x43ECE0
    """Kotor 1 animation function pointer 1."""
    K2_ANIM_FUNCTION_POINTER1: ClassVar[Literal[4522928]] = 0x4503B0
    """Kotor 2 animation function pointer 1."""

    # Geometry types
    GEOM_TYPE_ROOT: ClassVar[Literal[2]] = 2
    """Root geometry type."""
    GEOM_TYPE_ANIM: ClassVar[Literal[5]] = 5
    """Animation geometry type."""

    def __init__(self):
        self.function_pointer0: int = 0
        self.function_pointer1: int = 0
        self.model_name: ResRef = ResRef.from_blank()
        self.root_node_offset: int = 0
        self.node_count: int = 0
        self.unknown0: bytes = b"\x00" * 28  # 28 bytes of unknown data  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.
        self.geometry_type: int = 0
        self.padding: bytes = b"\x00" * 3  # 3 bytes padding  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.

    def read(self, reader: BinaryReader) -> _GeometryHeader:
        """Read geometry header data from a binary stream.

        Args:
            reader: Binary reader to read data from.

        Returns:
            The populated geometry header instance.
        """
        self.function_pointer0 = reader.read_uint32()
        self.function_pointer1 = reader.read_uint32()
        self.model_name = ResRef(reader.read_terminated_string("\0", 32))
        self.root_node_offset = reader.read_uint32()
        self.node_count = reader.read_uint32()
        self.unknown0 = reader.read_bytes(28)  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.
        self.geometry_type = reader.read_uint8()
        self.padding = reader.read_bytes(3)
        return self

    def write(self, writer: BinaryWriter):
        """Write geometry header data to a binary stream.

        Args:
            writer: Binary writer to write data to.
        """
        writer.write_uint32(self.function_pointer0)
        writer.write_uint32(self.function_pointer1)
        writer.write_string(self.model_name, string_length=32, encoding="ascii")
        writer.write_uint32(self.root_node_offset)
        writer.write_uint32(self.node_count)
        writer.write_bytes(self.unknown0)  # TODO: look into vendor/mdlops, vendor/reone, vendor/kotorblender to figure out what this is.
        writer.write_uint8(self.geometry_type)
        writer.write_bytes(self.padding)
