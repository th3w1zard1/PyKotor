"""Binary IO for MDL animations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.misc import ResRef
from pykotor.resource.formats.mdl.data.enums import MDLNodeFlags
from pykotor.resource.formats.mdl.data.nodes.anim import MDLAnimation, MDLAnimationEvent, MDLNodeAnimation
from pykotor.resource.formats.mdl.io.binary.headers.animation_header import _AnimationHeader
from pykotor.resource.formats.mdl.io.binary.nodes.node_io import MDLNodeIO

if TYPE_CHECKING:
    from pykotor.common.misc import Game
    from pykotor.common.stream import BinaryReader, BinaryWriter


class MDLAnimationIO:
    """Binary IO operations for MDL animations."""

    @staticmethod
    def read(reader: BinaryReader) -> MDLAnimation:
        """Read animation data from a binary stream.

        Args:
            reader: Binary reader to read from

        Returns:
            The loaded animation
        """
        # Read header
        header = _AnimationHeader().read(reader)

        # Create animation
        anim = MDLAnimation(name=str(header.name))
        anim.length = header.duration
        anim.transtime = header.transition
        anim.animroot = str(header.name)

        # Read events
        reader.seek(header.offset_to_events)
        for _ in range(header.event_count):
            time = reader.read_single()
            name = reader.read_terminated_string("\0", 32)
            anim.events.append(MDLAnimationEvent(time=time, name=name))

        # Read root node
        reader.seek(header.geometry.root_node_offset)
        if header.geometry.node_count > 0:
            root_node = MDLNodeIO.read(reader, str(header.name))
            root_node.node_flags = MDLNodeFlags(root_node.node_flags)  # Convert raw flags to enum
            anim.root_node = root_node

            # Read child nodes
            for _ in range(header.geometry.node_count - 1):
                child = MDLNodeIO.read(reader, "")  # Name will be set in node data
                child.node_flags = MDLNodeFlags(child.node_flags)
                child.parent = root_node
                root_node.children.append(child)

        return anim

    @staticmethod
    def write(writer: BinaryWriter, anim: MDLAnimation, game: Game) -> None:
        """Write animation data to a binary stream.

        Args:
            writer: Binary writer to write to
            anim: Animation to write
            game: Game version (K1/K2) to determine format specifics
        """
        # Write header
        header = _AnimationHeader()
        header.name = ResRef(anim.name)
        header.duration = anim.length
        header.transition = anim.transtime
        header.offset_to_events = _AnimationHeader.SIZE  # Events come after header
        header.event_count = len(anim.events)
        header.event_count2 = len(anim.events)  # Duplicate for validation
        header.geometry.root_node_offset = _AnimationHeader.SIZE + 36 * len(anim.events)  # Nodes come after events
        # Calculate total node count (root + children)
        node_count = 1  # Root node
        if anim.root_node and isinstance(anim.root_node, MDLNodeAnimation):
            node_count += len(anim.root_node.children)
        header.geometry.node_count = node_count
        header.write(writer)

        # Write events
        for event in anim.events:
            writer.write_single(event.time)
            writer.write_string(event.name, string_length=32, padding="\0")

        # Write root node and children
        if anim.root_node and isinstance(anim.root_node, MDLNodeAnimation):
            # Write root node
            MDLNodeIO.write(writer, anim.root_node, game)

            # Write child nodes in order
            for child in anim.root_node.children:
                if isinstance(child, MDLNodeAnimation):
                    MDLNodeIO.write(writer, child, game)

    @staticmethod
    def calc_size(anim: MDLAnimation, game: Game) -> int:
        """Calculate size of animation data in bytes.

        Args:
            anim: Animation to calculate size for
            game: Game version (K1/K2) to determine format specifics

        Returns:
            Size in bytes
        """
        size = 0

        # Header
        size += _AnimationHeader.SIZE

        # Events
        size += 36 * len(anim.events)  # 4 bytes time + 32 bytes name

        # Root node and children
        if anim.root_node and isinstance(anim.root_node, MDLNodeAnimation):
            # Root node size
            size += MDLNodeIO.calc_size(anim.root_node, game)

            # Child node sizes
            for child in anim.root_node.children:
                if isinstance(child, MDLNodeAnimation):
                    size += MDLNodeIO.calc_size(child, game)

        return size
