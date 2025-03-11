from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader, BinaryWriter


class _EventStructure:
    """Event data for animation sequences.

    Events are markers in an animation sequence that trigger effects or
    actions at specific times, like footstep sounds or particle effects.
    """

    SIZE: ClassVar[Literal[36]] = 0x24
    """Size of event structure in bytes."""

    def __init__(self):
        self.activation_time: float = 0.0
        """Time in seconds when event triggers."""
        self.event_name: str = ""
        """Name/identifier of the event."""


    def read(self, reader: BinaryReader) -> _EventStructure:
        """Read event data from a binary stream.

        Args:
            reader: Binary reader to read data from.

        Returns:
            The populated event structure instance.
        """
        self.activation_time = reader.read_single()
        self.event_name = reader.read_terminated_string("\0", 32)
        return self

    def write(self, writer: BinaryWriter):
        """Write event data to a binary stream.

        Args:
            writer: Binary writer to write data to.
        """
        writer.write_single(self.activation_time)
        writer.write_string(self.event_name, string_length=32, encoding="ascii")
