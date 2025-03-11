"""Model data structures for MDL format."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

from pykotor.resource.formats.mdl.data.enums import MDLClassification
from pykotor.resource.formats.mdl.data.nodes.mesh import MDLMeshNode
from pykotor.resource.type import ResourceType
from utility.common.geometry import Vector3

if TYPE_CHECKING:
    from pykotor.resource.formats.mdl.data.animation import _Animation as MDLAnimation
    from pykotor.resource.formats.mdl.data.nodes.node import MDLNode


@dataclass
class MDL:
    """Represents a MDL/MDX file.

    The top-level container for all model data including geometry,
    animations, and hierarchy.

    Attributes:
        root (MDLNode): The root node of the model hierarchy.
        anims (list[MDLAnimation]): The animations stored in the model.
        name (ResRef): The model name.
        type (str): The model type identifier.
        fog (bool): If fog affects the model.
        supermodel (ResRef): Name of another model resource to inherit from.
        classification (MDLClassification): Model usage classification.
    """

    BINARY_TYPE = ResourceType.MDL

    # Basic properties
    root: Optional[MDLNode] = None
    nodes: List[MDLNode] = field(default_factory=list)
    anims: List[MDLAnimation] = field(default_factory=list)
    name: str = ""
    type: str = ""
    affected_by_fog: bool = False
    supermodel: str = ""
    classification: MDLClassification = MDLClassification.OTHER
    subclassification: int = 0
    animroot: int = 0
    animation_scale: float = 1.0
    supermodel_root: int = 0

    # Geometry bounds
    bounding_min: Vector3 = field(default_factory=lambda: Vector3(0, 0, 0))
    bounding_max: Vector3 = field(default_factory=lambda: Vector3(0, 0, 0))
    radius: float = 0.0

    def get(self, node_name: str) -> Optional[MDLNode]:
        """Gets a node by name from the tree.

        Args:
            node_name: The name of the node to retrieve.

        Returns:
            The node with the matching name or None.
        """
        if not self.root:
            return None

        scan: deque[MDLNode] = deque([self.root])
        while scan:
            node = scan.popleft()
            if node.name == node_name:
                return node
            scan.extend(node.children)
        return None

    def all_nodes(self) -> List[MDLNode]:
        """Returns all nodes in the tree including children recursively.

        Returns:
            List of all nodes in the model hierarchy.
        """
        if self.root is None:
            return []

        nodes: List[MDLNode] = []
        scan: deque[MDLNode] = deque([self.root])
        while scan:
            node = scan.popleft()
            nodes.append(node)
            scan.extend(node.children)
        return nodes

    def find_parent(self, child: MDLNode) -> Optional[MDLNode]:
        """Find the parent node of the given child node.

        Args:
            child: The child node to find the parent for.

        Returns:
            The parent node of the given child or None if not found.
        """
        for node in self.all_nodes():
            if child in node.children:
                return node
        return None

    def global_position(self, node: MDLNode) -> Vector3:
        """Returns the global position of a node by traversing up the parent chain.

        Args:
            node: The node to get the global position for.

        Returns:
            The global position of the node.
        """
        position = Vector3(node.position[0], node.position[1], node.position[2])
        parent: MDLNode | None = self.find_parent(node)
        while parent is not None:
            parent_pos = Vector3(parent.position[0], parent.position[1], parent.position[2])
            position += parent_pos
            parent = self.find_parent(parent)
        return position

    def get_by_node_id(self, node_id: int) -> MDLNode:
        """Get node by node id.

        Args:
            node_id: The id of the node to retrieve.

        Returns:
            The node with matching id.

        Raises:
            ValueError: If no node with the given id exists.
        """
        for node in self.all_nodes():
            if node.node_number == node_id:
                return node
        raise ValueError(f"No node with id {node_id}")

    def all_textures(self) -> set[str]:
        """Returns all unique texture names used in the scene.

        Returns:
            Set of all texture names used in meshes.
        """
        textures = set()
        for node in self.all_nodes():
            if isinstance(node, MDLMeshNode) and node.texture and node.texture != "NULL":
                textures.add(node.texture)
        return textures

    def all_lightmaps(self) -> set[str]:
        """Returns a set of all lightmap textures used in the scene.

        Returns:
            Set of all lightmap texture names used in nodes.
        """
        lightmaps = set()
        for node in self.all_nodes():
            if isinstance(node, MDLMeshNode) and node.texture2 and node.texture2 != "NULL":
                lightmaps.add(node.texture2)
        return lightmaps
