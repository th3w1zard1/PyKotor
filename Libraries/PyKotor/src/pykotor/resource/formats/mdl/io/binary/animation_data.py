"""Low-level animation data for binary IO."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.misc import Game
from pykotor.resource.formats.mdl.data.event_structure import _EventStructure
from pykotor.resource.formats.mdl.data.nodes.anim import MDLNodeAnimation
from pykotor.resource.formats.mdl.io.binary.headers.animation_header import _AnimationHeader

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader, BinaryWriter


class _Animation:
    """Low-level animation data for binary IO.

    Contains all the data needed to animate a model, including the animation
    header, events, and animated nodes.

    Attributes:
        header (_AnimationHeader): Header containing animation metadata.
        events (list[_EventStructure]): List of events in this animation.
        w_nodes (list[_Node]): List of nodes affected by this animation.
    """

    def __init__(self):
        self.header: _AnimationHeader = _AnimationHeader()
        self.events: list[_EventStructure] = []
        self.w_nodes: list[MDLNodeAnimation] = []

    def read(self, reader: BinaryReader) -> _Animation:
        """Read animation data from a binary stream.

        Args:
            reader: Binary reader to read data from.

        Returns:
            The populated animation instance.
        """
        self.header = _AnimationHeader().read(reader)

        # Read events
        reader.seek(self.header.offset_to_events)
        self.events = [_EventStructure().read(reader) for _ in range(self.header.event_count)]

        # Read nodes starting at root node offset
        reader.seek(self.header.geometry.root_node_offset)
        self.w_nodes = [MDLNodeAnimation().read(reader) for _ in range(self.header.geometry.node_count)]

        return self

    def write(self, writer: BinaryWriter, game: Game):
        """Write animation data to a binary stream.

        Args:
            writer: Binary writer to write data to.
            game: Game version (K1/K2) to determine format specifics.
        """
        self.header.write(writer)
        for event in self.events:
            event.write(writer)
        for node in self.w_nodes:
            node.write(writer, game)

    def events_offset(self) -> int:
        """Get offset to event data relative to animation start.

        Returns:
            int: Offset in bytes.
        """
        # Events always come after header
        return _AnimationHeader.SIZE

    def events_size(self) -> int:
        """Get total size of event data.

        Returns:
            int: Size in bytes.
        """
        return _EventStructure.SIZE * len(self.events)

    def nodes_offset(self) -> int:
        """Get offset to node data relative to animation start.

        Returns:
            int: Offset in bytes.
        """
        # Nodes always come after events
        return self.events_offset() + self.events_size()

    def nodes_size(self) -> int:
        """Get total size of node data.

        Returns:
            int: Size in bytes.
        """
        return sum(node.calc_size(Game.K1) for node in self.w_nodes)

    def size(self) -> int:
        """Get total size of animation data.

        Returns:
            int: Size in bytes.
        """
        return self.nodes_offset() + self.nodes_size()