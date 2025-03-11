"""Walkmesh/AABB data structures for MDL format."""

from __future__ import annotations

from dataclasses import dataclass, field

from utility.common.geometry import Vector3


@dataclass
class MDLWalkmesh:
    """Axis-aligned bounding box (AABB) data for collision detection.

    This represents the collision geometry used for walkmesh/pathfinding
    and physics calculations. The data is stored as a binary space partitioning
    (BSP) tree of axis-aligned bounding boxes.

    Attributes:
        nodes (list[AABBNode]): List of AABB tree nodes.
        faces (list[AABBFace]): List of collision faces.
        vertices (list[Vector3]): List of vertex positions.
    """

    nodes: list[AABBNode] = field(default_factory=list)
    faces: list[AABBFace] = field(default_factory=list)
    vertices: list[Vector3] = field(default_factory=list)


@dataclass
class AABBNode:
    """Node in the AABB tree hierarchy.

    Each node represents a bounding box in 3D space. Leaf nodes contain
    actual collision geometry while internal nodes are used for spatial
    partitioning.

    Attributes:
        min_point (Vector3): Minimum point of bounding box.
        max_point (Vector3): Maximum point of bounding box.
        plane_type (int): Splitting plane type (0=X, 1=Y, 2=Z).
        plane_distance (float): Distance of splitting plane from origin.
        left_child (int): Index of left child node (-1 if leaf).
        right_child (int): Index of right child node (-1 if leaf).
        face_start (int): Starting index into face list (leaf nodes only).
        face_count (int): Number of faces in this node (leaf nodes only).
    """

    min_point: Vector3 = field(default_factory=Vector3.from_null)
    max_point: Vector3 = field(default_factory=Vector3.from_null)
    plane_type: int = 0
    plane_distance: float = 0.0
    left_child: int = -1
    right_child: int = -1
    face_start: int = 0
    face_count: int = 0


@dataclass
class AABBFace:
    """Triangle face used for collision detection.

    Attributes:
        vertex_indices (list[int]): Indices into vertex list defining triangle.
        material (int): Material/surface type for physics/sound.
        plane_normal (Vector3): Face normal for collision response.
        plane_distance (float): Distance from origin to face plane.
    """

    vertex_indices: list[int] = field(default_factory=lambda: [0, 0, 0])
    material: int = 0
    plane_normal: Vector3 = field(default_factory=Vector3.from_null)
    plane_distance: float = 0.0
