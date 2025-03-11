"""Binary IO for MDL nodes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.mdl.data.enums import MDLNodeFlags
from pykotor.resource.formats.mdl.data.exceptions import MDLReadError
from pykotor.resource.formats.mdl.data.nodes.anim import MDLNodeAnimation, MDLPositionKeyframe, MDLRotationKeyframe
from utility.common.geometry import Vector3, Vector4

if TYPE_CHECKING:
    from pykotor.common.misc import Game
    from pykotor.common.stream import BinaryReader, BinaryWriter


class MDLNodeIO:
    """Binary IO operations for MDL nodes."""

    @staticmethod
    def read(reader: BinaryReader, name: str) -> MDLNodeAnimation:
        """Read node data from a binary stream.

        Args:
            reader: Binary reader to read from
            name: Name of the node

        Returns:
            The loaded node

        Raises:
            MDLReadError: If there is an error reading the node
        """
        try:
            node = MDLNodeAnimation(name=name)

            # Read node header
            reader.skip(8)  # Skip function pointers
            node.node_flags = MDLNodeFlags(reader.read_uint16())
            node.node_number = reader.read_uint16()
            name_index = reader.read_uint16()
            reader.skip(2)  # padding
            root_offset = reader.read_uint32()
            parent_offset = reader.read_uint32()

            # Read position and orientation
            node.position = [reader.read_single() for _ in range(3)]
            node.orientation = [reader.read_single() for _ in range(4)]

            # Read position keyframes
            pos_count = reader.read_uint32()
            if pos_count > 0:
                for _ in range(pos_count):
                    time = reader.read_single()
                    x = reader.read_single()
                    y = reader.read_single()
                    z = reader.read_single()
                    node.position_keyframes.append(
                        MDLPositionKeyframe(time, Vector3(x, y, z))
                    )

            # Read orientation keyframes
            orient_count = reader.read_uint32()
            if orient_count > 0:
                for _ in range(orient_count):
                    time = reader.read_single()
                    x = reader.read_single()
                    y = reader.read_single()
                    z = reader.read_single()
                    w = reader.read_single()
                    node.rotation_keyframes.append(
                        MDLRotationKeyframe(time, Vector4(x, y, z, w))
                    )

            return node

        except Exception as e:
            raise MDLReadError(f"Error reading node: {str(e)}")

    @staticmethod
    def write(writer: BinaryWriter, node: MDLNodeAnimation, game: Game) -> None:
        """Write node data to a binary stream.

        Args:
            writer: Binary writer to write to
            node: Node to write
            game: Game version (K1/K2) to determine format specifics

        Raises:
            MDLReadError: If there is an error writing the node
        """
        try:
            # Write node header
            writer.write_uint32(0)  # Function pointer 1
            writer.write_uint32(0)  # Function pointer 2
            writer.write_uint16(node.node_flags)
            writer.write_uint16(node.node_number)
            writer.write_uint16(0)  # Name index written later
            writer.write_uint16(0)  # Padding
            writer.write_uint32(0)  # Root offset written later
            writer.write_uint32(0)  # Parent offset written later

            # Write position and orientation
            for x in node.position:
                writer.write_single(x)
            for x in node.orientation:
                writer.write_single(x)

            # Write position keyframes
            writer.write_uint32(len(node.position_keyframes))
            for keyframe in node.position_keyframes:
                writer.write_single(keyframe.time)
                writer.write_single(keyframe.position.x)
                writer.write_single(keyframe.position.y)
                writer.write_single(keyframe.position.z)

            # Write orientation keyframes
            writer.write_uint32(len(node.rotation_keyframes))
            for keyframe in node.rotation_keyframes:
                writer.write_single(keyframe.time)
                writer.write_single(keyframe.rotation.x)
                writer.write_single(keyframe.rotation.y)
                writer.write_single(keyframe.rotation.z)
                writer.write_single(keyframe.rotation.w)

        except Exception as e:
            raise MDLReadError(f"Error writing node: {str(e)}")

    @staticmethod
    def calc_size(node: MDLNodeAnimation, game: Game) -> int:
        """Calculate size of node data in bytes.

        Args:
            node: Node to calculate size for
            game: Game version (K1/K2) to determine format specifics

        Returns:
            Size in bytes
        """
        size = 0

        # Node header
        size += 24

        # Position and orientation
        size += 28  # 3 floats + 4 floats

        # Controller data
        size += 4  # Position controller count
        size += len(node.position_keyframes) * 16  # time + x,y,z per frame

        size += 4  # Orientation controller count
        size += len(node.rotation_keyframes) * 20  # time + x,y,z,w per frame

        return size
