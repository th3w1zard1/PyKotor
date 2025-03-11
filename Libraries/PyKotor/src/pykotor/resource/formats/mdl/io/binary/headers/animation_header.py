from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from typing_extensions import Literal

from pykotor.common.misc import ResRef
from pykotor.resource.formats.mdl.io.binary.headers.geometry_header import _GeometryHeader

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader, BinaryWriter


class _AnimationHeader:
    """Header data for animation sequences.

    Contains metadata about an animation sequence including its duration,
    transition time, and associated events.

    The animation header consists of a geometry header followed by
    animation-specific data like duration and events.

    Attributes:
        geometry (_GeometryHeader): Geometry header for this animation.
        duration (float): Length of animation in seconds.
        transition (float): Transition blend time in seconds.
        root (str): Name of root model/node.
        offset_to_events (int): Offset to event data.
        event_count (int): Number of events.
        event_count2 (int): Duplicate of event_count for validation.
        unknown0 (int): Unknown value.
    """

    SIZE: ClassVar[Literal[136]] = _GeometryHeader.SIZE + 0x38
    """Size of animation header in bytes."""

    def __init__(self):
        self.geometry: _GeometryHeader = _GeometryHeader()
        self.duration: float = 0.0
        self.transition: float = 0.0
        self.name: ResRef = ResRef.from_blank()
        self.offset_to_events: int = 0
        self.event_count: int = 0
        self.event_count2: int = 0
        self.unknown0: int = 0  # FIXME: what does mdlops say about this unknown? we have plenty that we need to fix.

    def read(self, reader: BinaryReader) -> _AnimationHeader:
        """Read animation header data from a binary stream.

        Args:
            reader: Binary reader to read data from.

        Returns:
            The populated animation header instance.
        """
        self.geometry = _GeometryHeader().read(reader)
        self.duration = reader.read_single()
        self.transition = reader.read_single()
        self.name = ResRef(reader.read_terminated_string("\0", 32))
        self.offset_to_events = reader.read_uint32()
        self.event_count = reader.read_uint32()
        self.event_count2 = reader.read_uint32()
        self.unknown0 = reader.read_uint32()  # FIXME: what does mdlops say about this unknown? we have plenty that we need to fix.
        return self

    def write(self, writer: BinaryWriter):
        """Write animation header data to a binary stream.

        Args:
            writer: Binary writer to write data to.
        """
        self.geometry.write(writer)
        writer.write_single(self.duration)
        writer.write_single(self.transition)
        writer.write_string(str(self.name), string_length=32, encoding="ascii")
        writer.write_uint32(self.offset_to_events)
        writer.write_uint32(self.event_count)
        writer.write_uint32(self.event_count2)
        writer.write_uint32(self.unknown0)  # FIXME: what does mdlops say about this unknown? we have plenty that we need to fix.
