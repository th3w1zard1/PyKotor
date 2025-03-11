"""ASCII reader for MDL animation nodes and data."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from pykotor.resource.formats.mdl.data.exceptions import MDLReadError
from pykotor.resource.formats.mdl.data.nodes.anim import (
    MDLAnimation,
    MDLAnimationEvent,
    MDLNodeAnimation,
    MDLPositionKeyframe,
    MDLRotationKeyframe,
    MDLScaleKeyframe,
)
from pykotor.resource.formats.mdl.io.ascii.nodes.base_node_reader import MDLASCIINodeReader
from utility.common.geometry import Vector3, Vector4

if TYPE_CHECKING:
    from pykotor.resource.formats.mdl.data.nodes.node import MDLNode


class MDLASCIIAnimationReader(MDLASCIINodeReader):
    """Reader for ASCII MDL animation nodes and data."""

    def read_node(self, parent: Optional[MDLNode] = None) -> MDLNodeAnimation:
        """Read an animation node from the file.

        Args:
            parent: Parent node if any

        Returns:
            MDLNodeAnimation: The loaded animation node

        Raises:
            MDLReadError: If there is an error reading the node data
        """
        try:
            # Read node header
            line = self.read_line()
            if not line.startswith("node "):
                raise MDLReadError(f"Expected node header, got: {line}")

            # Parse node name and number
            parts = line.split()
            if len(parts) != 4:
                raise MDLReadError(f"Invalid node header format: {line}")
            name = parts[2]
            node_number = int(parts[3])

            # Create animation node
            node = MDLNodeAnimation(name)
            node.node_number = node_number

            if parent:
                node.parent = parent

            # Read node sections
            while True:
                line = self.read_line()
                if line == "endnode":
                    break

                if line.startswith("beginproperties"):
                    self.read_properties(node)
                elif line.startswith("beginmodelgeom"):
                    self.read_geometry(node)
                elif line.startswith("beginanimation"):
                    self.read_animation(node)
                elif line.startswith("beginchildren"):
                    self.read_children(node)

            return node

        except Exception as e:
            raise MDLReadError(f"Error reading animation node: {str(e)}")

    def read_header(self, node: MDLNode) -> None:
        """Read the header of a node.

        Args:
            node: Node to read header for

        Raises:
            MDLReadError: If there is an error reading the header
        """
        pass  # ASCII does not have a binary header to read

    def read_subheader(self, node: MDLNode) -> None:
        """Read the subheader of a node.

        Args:
            node: Node to read subheader for

        Raises:
            MDLReadError: If there is an error reading the subheader
        """
        pass  # ASCII does not have a binary subheader to read

    def read_controllers(self, node: MDLNode) -> None:
        """Read the controllers of a node.

        Args:
            node: Node to read controllers for

        Raises:
            MDLReadError: If there is an error reading controllers
        """
        pass  # ASCII does not have binary controllers to read

    def read_controller_data(self, node: MDLNode) -> None:
        """Read the controller data of a node.

        Args:
            node: Node to read controller data for

        Raises:
            MDLReadError: If there is an error reading controller data
        """
        pass  # ASCII does not have binary controller data to read

    def read_vertex_coordinates(self, node: MDLNode) -> None:
        """Read the vertex coordinates of a node.

        Args:
            node: Node to read vertex coordinates for

        Raises:
            MDLReadError: If there is an error reading vertex coordinates
        """
        pass  # Animation nodes do not have vertex coordinates

    def read_faces(self, node: MDLNode) -> None:
        """Read the faces of a node.

        Args:
            node: Node to read faces for

        Raises:
            MDLReadError: If there is an error reading faces
        """
        pass  # Animation nodes do not have faces

    def read_aabb(self, node: MDLNode) -> None:
        """Read the AABB (Axis-Aligned Bounding Box) of a node.

        Args:
            node: Node to read AABB for

        Raises:
            MDLReadError: If there is an error reading AABB
        """
        pass  # ASCII does not have binary AABB data to read

    def read_properties(self, node: MDLNode) -> None:
        """Read node properties.

        Args:
            node: Node to read properties for

        Raises:
            MDLReadError: If there is an error reading properties
        """
        try:
            while True:
                line = self.read_line()
                if line.startswith("endproperties"):
                    break

                if line.startswith("position"):
                    vec = self._parse_vector3(line)
                    node.position = [vec.x, vec.y, vec.z]
                elif line.startswith("orientation"):
                    vec = self._parse_vector4(line)
                    node.orientation = [vec.x, vec.y, vec.z, vec.w]

        except Exception as e:
            raise MDLReadError(f"Error reading animation properties: {str(e)}")

    def read_geometry(self, node: MDLNode) -> None:
        """Read node geometry data.

        Args:
            node: Node to read geometry for

        Raises:
            MDLReadError: If there is an error reading geometry
        """
        try:
            # Animation nodes don't have geometry, skip to end
            while True:
                line = self.read_line()
                if line.startswith("endmodelgeom"):
                    break

        except Exception as e:
            raise MDLReadError(f"Error reading animation geometry: {str(e)}")

    def read_animation(self, node: MDLNode) -> None:
        """Read node animation data.

        Args:
            node: Node to read animation for

        Raises:
            MDLReadError: If there is an error reading animation
        """
        try:
            if not isinstance(node, MDLNodeAnimation):
                return

            while True:
                line = self.read_line()
                if line.startswith("endanimation"):
                    break

                # Parse controllers
                if line.startswith("positionkey "):
                    count = int(line.split()[1])
                    node.position_keyframes = self._read_position_keyframes(count)
                elif line.startswith("orientationkey "):
                    count = int(line.split()[1])
                    node.rotation_keyframes = self._read_rotation_keyframes(count)
                elif line.startswith("scalekey "):
                    count = int(line.split()[1])
                    node.scale_keyframes = self._read_scale_keyframes(count)
                elif line.startswith("alphakey "):
                    count = int(line.split()[1])
                    # Ignore alpha keyframes for now
                    self._read_generic_keyframes(count, 1)
                elif line.startswith("colorkey "):
                    count = int(line.split()[1])
                    # Ignore color keyframes for now
                    self._read_generic_keyframes(count, 3)
                elif line.startswith("radiuskey "):
                    count = int(line.split()[1])
                    # Ignore radius keyframes for now
                    self._read_generic_keyframes(count, 1)
                elif line.startswith("multiplierkey "):
                    count = int(line.split()[1])
                    # Ignore multiplier keyframes for now
                    self._read_generic_keyframes(count, 1)

        except Exception as e:
            raise MDLReadError(f"Error reading animation data: {str(e)}")

    def read_children(self, node: MDLNode) -> None:
        """Read child nodes.

        Args:
            node: Parent node to add children to

        Raises:
            MDLReadError: If there is an error reading child nodes
        """
        try:
            while True:
                # Peek at next line
                pos = self._reader.tell()
                line = self.read_line()
                if not line.startswith("node "):
                    self._reader.seek(pos)
                    break

                # Read child node
                child = self.read_node(node)
                node.add_child(child)

        except Exception as e:
            raise MDLReadError(f"Error reading child nodes: {str(e)}")

    def read_animation_header(self) -> MDLAnimation:
        """Read animation header data.

        Returns:
            MDLAnimation: The loaded animation

        Raises:
            MDLReadError: If there is an error reading the animation data
        """
        try:
            # Read animation header
            line = self.read_line()
            if not line.startswith("newanim "):
                raise MDLReadError(f"Expected newanim, got: {line}")

            # Parse animation name
            parts = line.split()
            if len(parts) != 3:
                raise MDLReadError(f"Invalid newanim format: {line}")
            name = parts[1]
            length = float(parts[2])

            # Create animation
            anim = MDLAnimation(name=name, length=length)

            # Read animation properties
            while True:
                line = self.read_line()
                if line == "doneanim":
                    break

                if line.startswith("transtime "):
                    anim.transtime = float(line.split()[1])
                elif line.startswith("animroot "):
                    anim.animroot = line.split(None, 1)[1]
                elif line.startswith("event "):
                    parts = line.split()
                    if len(parts) != 3:
                        raise MDLReadError(f"Invalid event format: {line}")
                    time = float(parts[1])
                    event_name = parts[2]
                    anim.events.append(MDLAnimationEvent(time=time, name=event_name))
                elif line.startswith("node "):
                    # Found root node, rewind and read it
                    self._reader.seek(self._reader.tell() - len(line) - 1)
                    root_node = self.read_node()
                    anim.root_node = root_node
                else:
                    raise MDLReadError(f"Unknown animation line: {line}")

            return anim

        except Exception as e:
            raise MDLReadError(f"Error reading animation header: {str(e)}")

    def _read_position_keyframes(self, count: int) -> List[MDLPositionKeyframe]:
        """Read position keyframe data.

        Args:
            count: Number of keyframes to read

        Returns:
            List of position keyframes
        """
        keyframes = []
        for _ in range(count):
            line = self.read_line()
            parts = line.split()
            if len(parts) != 4:
                raise MDLReadError(f"Invalid position keyframe format: {line}")

            time = float(parts[0])
            position = Vector3(float(parts[1]), float(parts[2]), float(parts[3]))
            keyframes.append(MDLPositionKeyframe(time, position))

        return keyframes

    def _read_rotation_keyframes(self, count: int) -> List[MDLRotationKeyframe]:
        """Read rotation keyframe data.

        Args:
            count: Number of keyframes to read

        Returns:
            List of rotation keyframes
        """
        keyframes = []
        for _ in range(count):
            line = self.read_line()
            parts = line.split()
            if len(parts) != 5:
                raise MDLReadError(f"Invalid rotation keyframe format: {line}")

            time = float(parts[0])
            rotation = Vector4(float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4]))
            keyframes.append(MDLRotationKeyframe(time, rotation))

        return keyframes

    def _read_scale_keyframes(self, count: int) -> List[MDLScaleKeyframe]:
        """Read scale keyframe data.

        Args:
            count: Number of keyframes to read

        Returns:
            List of scale keyframes
        """
        keyframes = []
        for _ in range(count):
            line = self.read_line()
            parts = line.split()
            if len(parts) not in [2, 4]:
                raise MDLReadError(f"Invalid scale keyframe format: {line}")

            time = float(parts[0])
            if len(parts) == 2:
                # Uniform scale
                scale = Vector3(float(parts[1]), float(parts[1]), float(parts[1]))
            else:
                # Non-uniform scale
                scale = Vector3(float(parts[1]), float(parts[2]), float(parts[3]))

            keyframes.append(MDLScaleKeyframe(time, scale))

        return keyframes

    def _read_generic_keyframes(self, count: int, num_values: int) -> List[List[float]]:
        """Read generic keyframe data.

        Args:
            count: Number of keyframes to read
            num_values: Number of values per keyframe

        Returns:
            List of keyframes
        """
        keyframes = []
        for _ in range(count):
            line = self.read_line()
            parts = line.split()
            if len(parts) != num_values + 1:
                raise MDLReadError(f"Invalid generic keyframe format: {line}")

            keyframes.append([float(x) for x in parts])

        return keyframes

