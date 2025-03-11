"""Base interface for MDL node readers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader
    from pykotor.resource.formats.mdl.data.nodes.node import MDLNode


class MDLNodeReader(ABC):
    """Abstract base class for MDL node readers."""

    def __init__(self, reader: BinaryReader, names: list[str], node_by_number: dict[int, MDLNode]):
        """Initialize the node reader.

        Args:
            reader: The reader to use for reading node data
            names: List of names from the MDL file
            node_by_number: Dictionary mapping node numbers to nodes
        """
        self._reader: BinaryReader = reader
        self._names: list[str] = names
        self._node_by_number: dict[int, MDLNode] = node_by_number
        self._isgeometry: bool = False  # true if in model geometry
        self._isanimation: bool = False  # true if in animations
        self._innode: bool = False  # true if currently processing a node
        self._nodenum: int = 0
        self._animnum: int = 0
        self._task: str = ""  # current parsing task (verts, faces, etc.)
        self._count: int = 0  # counter for current task

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
        pass

    @abstractmethod
    def read_children(self, node: MDLNode) -> None:
        """Read child nodes.

        Args:
            node: Parent node to add children to

        Raises:
            MDLReadError: If there is an error reading child nodes
        """
        pass

    @abstractmethod
    def read_properties(self, node: MDLNode) -> None:
        """Read node properties.

        Args:
            node: Node to read properties for

        Raises:
            MDLReadError: If there is an error reading properties
        """
        pass

    @abstractmethod
    def read_geometry(self, node: MDLNode) -> None:
        """Read node geometry data.

        Args:
            node: Node to read geometry for

        Raises:
            MDLReadError: If there is an error reading geometry
        """
        pass

    @abstractmethod
    def read_animation(self, node: MDLNode) -> None:
        """Read node animation data.

        Args:
            node: Node to read animation for

        Raises:
            MDLReadError: If there is an error reading animation
        """
        pass

    @abstractmethod
    def read_header(self, node: MDLNode) -> None:
        """Read the header of a node.

        Args:
            node: Node to read header for

        Raises:
            MDLReadError: If there is an error reading the header
        """
        pass

    @abstractmethod
    def read_subheader(self, node: MDLNode) -> None:
        """Read the subheader of a node.

        Args:
            node: Node to read subheader for

        Raises:
            MDLReadError: If there is an error reading the subheader
        """
        pass

    @abstractmethod
    def read_controllers(self, node: MDLNode) -> None:
        """Read the controllers of a node.

        Args:
            node: Node to read controllers for

        Raises:
            MDLReadError: If there is an error reading controllers
        """
        pass

    @abstractmethod
    def read_controller_data(self, node: MDLNode) -> None:
        """Read the controller data of a node.

        Args:
            node: Node to read controller data for

        Raises:
            MDLReadError: If there is an error reading controller data
        """
        pass

    @abstractmethod
    def read_vertex_coordinates(self, node: MDLNode) -> None:
        """Read the vertex coordinates of a node.

        Args:
            node: Node to read vertex coordinates for

        Raises:
            MDLReadError: If there is an error reading vertex coordinates
        """
        pass

    @abstractmethod
    def read_faces(self, node: MDLNode) -> None:
        """Read the faces of a node.

        Args:
            node: Node to read faces for

        Raises:
            MDLReadError: If there is an error reading faces
        """
        pass

    @abstractmethod
    def read_aabb(self, node: MDLNode) -> None:
        """Read the AABB (Axis-Aligned Bounding Box) of a node.

        Args:
            node: Node to read AABB for

        Raises:
            MDLReadError: If there is an error reading AABB
        """
        pass