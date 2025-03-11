"""Base class for ASCII MDL node readers."""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Optional, Tuple

from pykotor.common.misc import Color
from pykotor.resource.formats.mdl.data.exceptions import MDLReadError
from pykotor.resource.formats.mdl.io.base.node_reader import MDLNodeReader
from utility.common.geometry import Vector2, Vector3, Vector4

if TYPE_CHECKING:
    from pykotor.resource.formats.mdl.data.nodes.node import MDLNode


class MDLASCIINodeReader(MDLNodeReader):
    """Base class for ASCII MDL node readers."""

    def read_line(self) -> str:
        """Read next non-empty, non-comment line.

        Returns:
            str: The next line of content

        Raises:
            MDLReadError: If EOF is reached
        """
        while True:
            line = self._reader.read_line()
            if not line:
                raise MDLReadError("Unexpected EOF")
            line = line.strip()
            if line and not line.startswith("#"):
                return line

    @abstractmethod
    def read_node(self, parent: Optional[MDLNode] = None) -> MDLNode:
        """Read a node from the file.

        Args:
            parent: Parent node if any

        Returns:
            MDLNode: The loaded node

        Raises:
            MDLReadError: If there is an error reading the node data
        """
        raise NotImplementedError("Each ASCII node type must implement read_node")

    @abstractmethod
    def read_children(self, node: MDLNode) -> None:
        """Read child nodes.

        Args:
            node: Parent node to add children to

        Raises:
            MDLReadError: If there is an error reading child nodes
        """
        raise NotImplementedError("Each ASCII node type must implement read_children")

    @abstractmethod
    def read_properties(self, node: MDLNode) -> None:
        """Read node properties.

        Args:
            node: Node to read properties for

        Raises:
            MDLReadError: If there is an error reading properties
        """
        raise NotImplementedError("Each ASCII node type must implement read_properties")

    @abstractmethod
    def read_geometry(self, node: MDLNode) -> None:
        """Read node geometry data.

        Args:
            node: Node to read geometry for

        Raises:
            MDLReadError: If there is an error reading geometry
        """
        raise NotImplementedError("Each ASCII node type must implement read_geometry")

    @abstractmethod
    def read_animation(self, node: MDLNode) -> None:
        """Read node animation data.

        Args:
            node: Node to read animation for

        Raises:
            MDLReadError: If there is an error reading animation
        """
        raise NotImplementedError("Each ASCII node type must implement read_animation")

    def _parse_vector2(self, line: str) -> Vector2:
        """Parse a Vector2 from a space-separated string.

        Args:
            line: String containing x y components

        Returns:
            Vector2: The parsed vector

        Raises:
            MDLReadError: If the string has invalid format
        """
        try:
            parts = line.split()
            if len(parts) != 2:
                raise ValueError(f"Expected 2 components, got {len(parts)}")
            return Vector2(float(parts[0]), float(parts[1]))
        except Exception as e:
            raise MDLReadError(f"Error parsing Vector2: {str(e)}")

    def _parse_vector3(self, line: str) -> Vector3:
        """Parse a Vector3 from a space-separated string.

        Args:
            line: String containing x y z components

        Returns:
            Vector3: The parsed vector

        Raises:
            MDLReadError: If the string has invalid format
        """
        try:
            parts = line.split()
            if len(parts) != 3:
                raise ValueError(f"Expected 3 components, got {len(parts)}")
            return Vector3(float(parts[0]), float(parts[1]), float(parts[2]))
        except Exception as e:
            raise MDLReadError(f"Error parsing Vector3: {str(e)}")

    def _parse_vector4(self, line: str) -> Vector4:
        """Parse a Vector4 from a space-separated string.

        Args:
            line: String containing x y z w components

        Returns:
            Vector4: The parsed vector

        Raises:
            MDLReadError: If the string has invalid format
        """
        try:
            parts = line.split()
            if len(parts) != 4:
                raise ValueError(f"Expected 4 components, got {len(parts)}")
            return Vector4(float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]))
        except Exception as e:
            raise MDLReadError(f"Error parsing Vector4: {str(e)}")

    def _parse_color(self, line: str) -> Color:
        """Parse a Color from a space-separated string.

        Args:
            line: String containing r g b components (0-255)

        Returns:
            Color: The parsed color

        Raises:
            MDLReadError: If the string has invalid format
        """
        try:
            parts = line.split()
            if len(parts) != 3:
                raise ValueError(f"Expected 3 components, got {len(parts)}")
            return Color(int(parts[0]), int(parts[1]), int(parts[2]))
        except Exception as e:
            raise MDLReadError(f"Error parsing Color: {str(e)}")

    def _parse_color_float(self, line: str) -> Color:
        """Parse a Color from a space-separated string with float components.

        Args:
            line: String containing r g b components (0.0-1.0)

        Returns:
            Color: The parsed color

        Raises:
            MDLReadError: If the string has invalid format
        """
        try:
            parts = line.split()
            if len(parts) != 3:
                raise ValueError(f"Expected 3 components, got {len(parts)}")
            return Color(int(float(parts[0]) * 255), int(float(parts[1]) * 255), int(float(parts[2]) * 255))
        except Exception as e:
            raise MDLReadError(f"Error parsing Color: {str(e)}")

    def _parse_color_alpha(self, line: str) -> Tuple[Color, int]:
        """Parse a Color and alpha from a space-separated string.

        Args:
            line: String containing r g b a components (0-255)

        Returns:
            Tuple of (Color, alpha)

        Raises:
            MDLReadError: If the string has invalid format
        """
        try:
            parts = line.split()
            if len(parts) != 4:
                raise ValueError(f"Expected 4 components, got {len(parts)}")
            return (Color(int(parts[0]), int(parts[1]), int(parts[2])), int(parts[3]))
        except Exception as e:
            raise MDLReadError(f"Error parsing Color+alpha: {str(e)}")

    def _parse_color_alpha_float(self, line: str) -> Tuple[Color, float]:
        """Parse a Color and alpha from a space-separated string with float components.

        Args:
            line: String containing r g b a components (0.0-1.0)

        Returns:
            Tuple of (Color, alpha)

        Raises:
            MDLReadError: If the string has invalid format
        """
        try:
            parts = line.split()
            if len(parts) != 4:
                raise ValueError(f"Expected 4 components, got {len(parts)}")
            return (Color(int(float(parts[0]) * 255), int(float(parts[1]) * 255), int(float(parts[2]) * 255)), float(parts[3]))
        except Exception as e:
            raise MDLReadError(f"Error parsing Color+alpha: {str(e)}")
