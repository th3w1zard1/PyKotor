"""Mesh node data structure for MDL format."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

from pykotor.resource.formats.mdl.data.nodes.node import MDLNode
from utility.common.geometry import Vector2, Vector3

if TYPE_CHECKING:
    from pykotor.common.misc import Color


@dataclass
class MDLMeshNode(MDLNode):
    """Base mesh node in MDL format.

    Mesh nodes contain geometry data including vertices, faces, normals, texture
    coordinates, and material properties. This serves as the base class for more
    specialized mesh types like skinned and animated meshes.
    """

    # Geometry data
    vertices: List[Vector3] = field(default_factory=list)  # Vertex positions
    normals: List[Vector3] = field(default_factory=list)  # Vertex normals
    uv1: List[Vector2] = field(default_factory=list)  # Primary UV coords
    uv2: List[Vector2] = field(default_factory=list)  # Secondary UV coords
    colors: List[Color] = field(default_factory=list)  # Vertex colors

    # Face data
    faces: List[List[int]] = field(default_factory=list)  # Triangle indices
    face_materials: List[int] = field(default_factory=list)  # Material ID per face
    face_normals: List[Vector3] = field(default_factory=list)  # Face normals
    face_distances: List[float] = field(default_factory=list)  # Face plane distances

    # Material properties
    diffuse: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])  # RGB
    ambient: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])  # RGB
    self_illumination: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])  # RGB
    transparency: float = 1.0
    texture: Optional[str] = None  # Primary texture
    texture2: Optional[str] = None  # Secondary texture

    # Render properties
    render: bool = True
    shadow: bool = True
    beaming: bool = False
    render_environment_map: bool = False
    background_geometry: bool = False

    # Animation properties
    animate_uv: bool = False
    uv_direction: Vector2 = field(default_factory=lambda: Vector2(0.0, 0.0))  # UV scroll direction
    uv_jitter: float = 0.0
    uv_jitter_speed: float = 0.0
    rotate_texture: bool = False

    # Lightmap properties
    lightmapped: bool = False

    # TSL-specific properties
    dirt_enabled: bool = False
    dirt_texture: int = 0
    dirt_worldspace: bool = False
    hologram_donotdraw: bool = False

    def __post_init__(self):
        """Initialize base class."""
        super().__init__(self.name)

    def get_vertex_count(self) -> int:
        """Get number of vertices.

        Returns:
            int: Number of vertices
        """
        return len(self.vertices)

    def get_face_count(self) -> int:
        """Get number of faces.

        Returns:
            int: Number of faces
        """
        return len(self.faces)

    def get_bounding_box(self) -> tuple[Vector3, Vector3]:
        """Get axis-aligned bounding box.

        Returns:
            tuple[Vector3, Vector3]: Min and max points
        """
        if not self.vertices:
            return (Vector3(0.0, 0.0, 0.0), Vector3(0.0, 0.0, 0.0))

        min_point = Vector3(float("inf"), float("inf"), float("inf"))
        max_point = Vector3(float("-inf"), float("-inf"), float("-inf"))

        for vertex in self.vertices:
            min_point = Vector3(
                min(min_point.x, vertex.x),
                min(min_point.y, vertex.y),
                min(min_point.z, vertex.z)
            )
            max_point = Vector3(
                max(max_point.x, vertex.x),
                max(max_point.y, vertex.y),
                max(max_point.z, vertex.z)
            )

        return (min_point, max_point)

    def get_bounding_sphere_radius(self) -> float:
        """Get bounding sphere radius.

        Returns:
            float: Radius of bounding sphere centered at origin
        """
        if not self.vertices:
            return 0.0

        # Find maximum distance from origin
        max_dist_sq = 0.0
        for vertex in self.vertices:
            dist_sq = vertex.x * vertex.x + vertex.y * vertex.y + vertex.z * vertex.z
            max_dist_sq = max(max_dist_sq, dist_sq)

        return max_dist_sq ** 0.5

    def get_face_vertices(self, face_index: int) -> List[Vector3]:
        """Get vertices for a face.

        Args:
            face_index: Index of face

        Returns:
            List[Vector3]: List of vertex positions for the face
        """
        if face_index >= len(self.faces):
            return []

        face = self.faces[face_index]
        return [self.vertices[i] for i in face]

    def get_face_normal(self, face_index: int) -> Optional[Vector3]:
        """Get normal vector for a face.

        Args:
            face_index: Index of face

        Returns:
            Optional[Vector3]: Face normal vector or None if not available
        """
        if face_index >= len(self.face_normals):
            return None
        return self.face_normals[face_index]

    def get_vertex_uv(self, vertex_index: int, layer: int = 0) -> Optional[Vector2]:
        """Get UV coordinates for a vertex.

        Args:
            vertex_index: Index of vertex
            layer: UV layer (0=primary, 1=secondary)

        Returns:
            Optional[Vector2]: UV coordinates or None if not available
        """
        if layer == 0 and vertex_index < len(self.uv1):
            return self.uv1[vertex_index]
        elif layer == 1 and vertex_index < len(self.uv2):
            return self.uv2[vertex_index]
        return None

    def get_vertex_color(self, vertex_index: int) -> Optional[Color]:
        """Get color for a vertex.

        Args:
            vertex_index: Index of vertex

        Returns:
            Optional[Color]: Vertex color or None if not available
        """
        if vertex_index >= len(self.colors):
            return None
        return self.colors[vertex_index]