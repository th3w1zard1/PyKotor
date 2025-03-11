"""Skin mesh node data structure for MDL format."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from pykotor.resource.formats.mdl.data.nodes.trimesh import MDLTrimeshNode


@dataclass
class MDLSkinWeight:
    """Weight data for a vertex-bone influence."""
    bone_index: int = 0  # Index into bones list
    weight: float = 0.0  # Weight value (0-1)


@dataclass
class MDLSkinNode(MDLTrimeshNode):
    """Skin mesh node in MDL format.

    Skin meshes are used for skeletal animation. They extend the trimesh with
    bone influences and weights that control how vertices deform based on bone
    transformations.
    """

    # Bone data
    bones: List[str] = field(default_factory=list)  # Bone node names
    bone_map: List[int] = field(default_factory=list)  # Maps bone indices to node numbers

    # Vertex weights
    weights: List[List[MDLSkinWeight]] = field(default_factory=list)  # Per-vertex bone weights

    def __post_init__(self):
        """Initialize base class."""
        super().__init__(self.name)

    def get_bone_count(self) -> int:
        """Get number of bones.

        Returns:
            int: Number of bones
        """
        return len(self.bones)

    def get_max_weights_per_vertex(self) -> int:
        """Get maximum number of bone weights per vertex.

        Returns:
            int: Maximum weights per vertex
        """
        return max(len(vertex_weights) for vertex_weights in self.weights) if self.weights else 0

    def get_bone_index(self, bone_name: str) -> int:
        """Get index of a bone by name.

        Args:
            bone_name: Name of bone to find

        Returns:
            int: Index of bone in bones list, or -1 if not found
        """
        try:
            return self.bones.index(bone_name)
        except ValueError:
            return -1

    def get_bone_node_number(self, bone_index: int) -> int:
        """Get node number for a bone index.

        Args:
            bone_index: Index into bones list

        Returns:
            int: Node number from bone map, or -1 if invalid index
        """
        if 0 <= bone_index < len(self.bone_map):
            return self.bone_map[bone_index]
        return -1