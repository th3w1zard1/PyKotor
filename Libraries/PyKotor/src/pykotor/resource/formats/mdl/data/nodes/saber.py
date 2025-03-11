"""Lightsaber data structures for MDL format."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

from pykotor.common.misc import Color, ResRef
from pykotor.resource.formats.mdl.data.enums import MDLSaberFlags, MDLSaberType
from pykotor.resource.formats.mdl.data.nodes.trimesh import MDLTrimeshNode

if TYPE_CHECKING:
    from utility.common.geometry import Vector3


@dataclass
class MDLSaberNode(MDLTrimeshNode):
    """Node representing a lightsaber blade.

    Lightsaber nodes are specialized trimesh nodes that contain additional
    data for rendering the blade effect. They inherit all trimesh properties
    and add saber-specific properties.

    In ASCII format, saber nodes are represented as trimesh nodes with a
    "2081__" prefix in their name. When reading ASCII files, these nodes
    are automatically converted to saber nodes.

    The vertex structure is very specific:
    - Two blades, each with 8 vertices
    - Vertices are arranged in a specific pattern for blade effects:
        - outside corners (1 face)
        - inner edge (2 faces)
        - row 2 (3 faces)
        - row one outer edge (4 faces)
    - Blade width is calculated from vertex positions
    - Bioware inverted blade1 geometry

    Attributes:
        vertices: Base mesh vertices
        faces: Face indices into vertices list
        normals: Vertex normals for lighting calculations
        uv1: Primary UV coordinates
        uv2: Secondary UV coordinates (unused in sabers)
        colors: Vertex colors (unused in sabers)
        face_materials: Material ID per face
        face_normals: Face normal vectors
        face_distances: Face plane distances
        diffuse: RGB diffuse color
        ambient: RGB ambient color
        self_illumination: RGB self illumination color
        transparency: Transparency value
        texture: Primary texture
        texture2: Secondary texture (unused in sabers)
        render: Whether to render this node
        shadow: Whether this node casts shadows
        beaming: Always true for sabers
        render_environment_map: Whether to render environment map
        background_geometry: Whether this is background geometry
        animate_uv: Whether to animate UVs
        uv_direction: UV scroll direction
        uv_jitter: UV jitter amount
        uv_jitter_speed: UV jitter speed
        rotate_texture: Whether to rotate texture
        lightmapped: Whether this node is lightmapped
        dirt_enabled: Whether dirt effects are enabled
        dirt_texture: Dirt texture index
        dirt_worldspace: Whether dirt is in world space
        hologram_donotdraw: Whether to skip drawing hologram
        saber_type: Type of lightsaber blade
        saber_color: Color of the blade
        saber_length: Length of blade
        saber_width: Width of blade
        saber_flare_color: Color of flare effect
        saber_flare_radius: Radius of flare effect
        saber_flags: Saber behavior flags
        blur_length: Motion blur trail length
        blur_width: Motion blur trail width
        glow_size: Size of glow effect
        glow_intensity: Intensity of glow effect
        blade_texture: Blade texture resource
        hit_texture: Impact effect texture
        flare_texture: Flare effect texture
        saber_vertices: Vertices used for the saber blade effect
        rotate_with_target: Whether blade rotates with target
        bitmap: Original bitmap name from ASCII format
        render_hint: Original render hint from ASCII format
    """

    # Inherited from MDLTrimeshNode:
    # - All mesh properties (vertices, faces, normals, etc)
    # - All material properties (diffuse, ambient, etc)
    # - All render properties (render, shadow, etc)
    # - All animation properties (animate_uv, etc)
    # - All lightmap properties (lightmapped, etc)
    # - All TSL properties (dirt_enabled, etc)

    # Blade properties
    saber_type: MDLSaberType = MDLSaberType.STANDARD
    saber_color: Color = field(default_factory=lambda: Color.from_rgb_integer(0))
    saber_length: float = 0.0
    saber_width: float = 0.0
    saber_flare_color: Color = field(default_factory=lambda: Color.from_rgb_integer(0))
    saber_flare_radius: float = 0.0
    saber_flags: MDLSaberFlags = field(default_factory=lambda: MDLSaberFlags(0))

    # Effect properties
    blur_length: float = 0.0
    blur_width: float = 0.0
    glow_size: float = 0.0
    glow_intensity: float = 0.0

    # Textures
    blade_texture: ResRef = field(default_factory=ResRef.from_blank)
    hit_texture: ResRef = field(default_factory=ResRef.from_blank)
    flare_texture: ResRef = field(default_factory=ResRef.from_blank)

    # Saber-specific geometry
    saber_vertices: List[Vector3] = field(default_factory=list)
    """Vertices used for the saber blade effect. These are a copy of the base
    vertices that are used for rendering the glowing blade effect. The vertices
    are arranged in a specific pattern:
    - Two blades, each with 8 vertices
    - Vertices are identified by face count:
        - outside corners = 1 face
        - inner edge = 2 faces
        - row 2 = 3 faces
        - row one outer edge = 4 faces
    - Blade width is calculated from vertex positions
    - Note: Bioware inverted blade1 geometry
    """

    # ASCII format properties
    rotate_with_target: bool = False
    """Whether blade rotates with target. Only used in ASCII format."""

    bitmap: Optional[str] = None
    """Original bitmap name from ASCII format."""

    render_hint: int = 0
    """Original render hint from ASCII format."""

    def __post_init__(self) -> None:
        """Initialize base class and set default properties."""
        super().__init__(self.name)
        # Sabers always have beaming enabled
        self.beaming = True
        # Copy vertices to saber vertices if not already set
        if not self.saber_vertices and self.vertices:
            self.saber_vertices = self.vertices.copy()

    def get_blade_width(self) -> float:
        """Calculate blade width from vertex positions.

        Returns:
            float: Width of the blade
        """
        if len(self.vertices) < 5:
            return 0.0
        # Width is distance between vertex 0 and 4
        v0 = self.vertices[0]
        v4 = self.vertices[4]
        return ((v4.x - v0.x) ** 2 + (v4.y - v0.y) ** 2 + (v4.z - v0.z) ** 2) ** 0.5

    def get_blade_vertices(self, blade_index: int) -> List[Vector3]:
        """Get vertices for a specific blade.

        Args:
            blade_index: Index of blade (0 or 1)

        Returns:
            List[Vector3]: List of 8 vertices for the blade
        """
        if blade_index == 0:
            return self.vertices[0:8]
        else:
            return self.vertices[8:16]

    def get_blade_faces(self, blade_index: int) -> List[List[int]]:
        """Get faces for a specific blade.

        Args:
            blade_index: Index of blade (0 or 1)

        Returns:
            List[List[int]]: List of faces for the blade
        """
        if blade_index == 0:
            return [face for face in self.faces if max(face) < 8]
        else:
            return [face for face in self.faces if min(face) >= 8]
