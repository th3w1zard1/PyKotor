"""Base node data structure for MDL format."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pykotor.resource.formats.mdl.data.enums import MDLNodeFlags


@dataclass
class MDLNode:  # TODO: store root node here.
    """Base node class for MDL format."""

    name: str
    node_number: int = -1
    node_flags: MDLNodeFlags = field(default_factory=lambda: MDLNodeFlags(0))
    parent: Optional[MDLNode] = None
    children: List[MDLNode] = field(default_factory=list)

    # Position and orientation
    position: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    orientation: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 1.0])  # Quaternion [x,y,z,w]

    # Controller data
    position_controllers: List[List[float]] = field(default_factory=list)
    orientation_controllers: List[List[float]] = field(default_factory=list)

    def add_child(self, child: MDLNode) -> None:
        """Add a child node.

        Args:
            child: Node to add as child
        """
        child.parent = self
        self.children.append(child)

    def remove_child(self, child: MDLNode) -> None:
        """Remove a child node.

        Args:
            child: Node to remove
        """
        if child in self.children:
            child.parent = None
            self.children.remove(child)

    def get_root(self) -> MDLNode:
        """Get the root node.

        Returns:
            MDLNode: Root node
        """
        current = self
        while current.parent is not None:
            current = current.parent
        return current

    def get_path(self) -> str:
        """Get the node path from root.

        Returns:
            str: Node path (e.g. "root/body/arm")
        """
        path = []
        current = self
        while current is not None:
            path.append(current.name)
            current = current.parent
        return "/".join(reversed(path))

    def find_child(self, name: str) -> Optional[MDLNode]:
        """Find a child node by name.

        Args:
            name: Name of node to find

        Returns:
            Optional[MDLNode]: Found node or None
        """
        for child in self.children:
            if child.name == name:
                return child
        return None

    def find_descendant(self, name: str) -> Optional[MDLNode]:
        """Find a descendant node by name.

        Args:
            name: Name of node to find

        Returns:
            Optional[MDLNode]: Found node or None
        """
        if self.name == name:
            return self

        for child in self.children:
            found = child.find_descendant(name)
            if found is not None:
                return found

        return None
