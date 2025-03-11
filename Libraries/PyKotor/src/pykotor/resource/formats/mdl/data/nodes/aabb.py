"""AABB node data structure for MDL format."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pykotor.resource.formats.mdl.data.nodes.node import MDLNode
from utility.common.geometry import Vector3


@dataclass
class MDLAABBNode(MDLNode):
    """AABB (Axis-Aligned Bounding Box) node in MDL format.

    AABB nodes are used for collision detection and spatial queries. They store
    a hierarchy of axis-aligned bounding boxes that can be used for efficient
    intersection tests and visibility culling.
    """

    # Bounding box
    min_point: Vector3 = field(default_factory=lambda: Vector3(0.0, 0.0, 0.0))  # Minimum corner
    max_point: Vector3 = field(default_factory=lambda: Vector3(0.0, 0.0, 0.0))  # Maximum corner

    # Bounding sphere
    center: Vector3 = field(default_factory=lambda: Vector3(0.0, 0.0, 0.0))  # Sphere center
    radius: float = 0.0  # Sphere radius

    # Tree structure
    left_node: Optional[MDLAABBNode] = None  # Left child node
    right_node: Optional[MDLAABBNode] = None  # Right child node
    is_leaf: bool = True  # Whether this is a leaf node

    # Leaf data (only valid if is_leaf is True)
    face_indices: List[int] = field(default_factory=list)  # Indices into model's face list
    faces: List[List[int]] = field(default_factory=list)  # Triangle indices
    face_normals: List[Vector3] = field(default_factory=list)  # Face normal vectors
    face_distances: List[float] = field(default_factory=list)  # Face plane distances
    vertices: List[Vector3] = field(default_factory=list)  # Vertex positions

    def __post_init__(self):
        """Initialize base class."""
        super().__init__(self.name)

    def contains_point(self, point: Vector3) -> bool:
        """Test if point is inside AABB.

        Args:
            point: Point to test

        Returns:
            bool: True if point is inside box
        """
        return self.min_point.x <= point.x <= self.max_point.x and self.min_point.y <= point.y <= self.max_point.y and self.min_point.z <= point.z <= self.max_point.z

    def intersects_box(self, min_point: Vector3, max_point: Vector3) -> bool:
        """Test if AABB intersects another AABB.

        Args:
            min_point: Minimum corner of other box
            max_point: Maximum corner of other box

        Returns:
            bool: True if boxes intersect
        """
        return (
            self.min_point.x <= max_point.x
            and self.max_point.x >= min_point.x
            and self.min_point.y <= max_point.y
            and self.max_point.y >= min_point.y
            and self.min_point.z <= max_point.z
            and self.max_point.z >= min_point.z
        )

    def get_size(self) -> Vector3:
        """Get size of AABB.

        Returns:
            Vector3: Size vector
        """
        return Vector3(self.max_point.x - self.min_point.x, self.max_point.y - self.min_point.y, self.max_point.z - self.min_point.z)

    def get_volume(self) -> float:
        """Get volume of AABB.

        Returns:
            float: Volume in cubic units
        """
        size = self.get_size()
        return size.x * size.y * size.z

    def get_surface_area(self) -> float:
        """Get surface area of AABB.

        Returns:
            float: Surface area in square units
        """
        size = self.get_size()
        return 2.0 * (size.x * size.y + size.x * size.z + size.y * size.z)

    def expand(self, point: Vector3) -> None:
        """Expand AABB to include point.

        Args:
            point: Point to include
        """
        self.min_point = Vector3(min(self.min_point.x, point.x), min(self.min_point.y, point.y), min(self.min_point.z, point.z))
        self.max_point = Vector3(max(self.max_point.x, point.x), max(self.max_point.y, point.y), max(self.max_point.z, point.z))
        # Update bounding sphere
        self.center = Vector3((self.min_point.x + self.max_point.x) * 0.5, (self.min_point.y + self.max_point.y) * 0.5, (self.min_point.z + self.max_point.z) * 0.5)
        size = self.get_size()
        self.radius = (size.x * size.x + size.y * size.y + size.z * size.z) ** 0.5 * 0.5

    def get_closest_point(self, point: Vector3) -> Vector3:
        """Get closest point on AABB to given point.

        Args:
            point: Point to find closest point to

        Returns:
            Vector3: Closest point on AABB
        """
        return Vector3(
            max(self.min_point.x, min(point.x, self.max_point.x)), max(self.min_point.y, min(point.y, self.max_point.y)), max(self.min_point.z, min(point.z, self.max_point.z))
        )
