"""Geometry data structures for MDL format."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pykotor.common.misc import Color, ResRef
from utility.common.geometry import SurfaceMaterial, Vector3

if TYPE_CHECKING:
    from utility.common.geometry import Vector2, Vector4


@dataclass
class MDLBoneVertex:
    """Vertex bone weight data for skinned meshes.

    Attributes:
        vertex_weights (tuple[float, float, float, float]): Weight values for up to 4 bones.
        vertex_indices (tuple[float, float, float, float]): Bone indices for up to 4 bones.
    """

    vertex_weights: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    vertex_indices: tuple[float, float, float, float] = (-1.0, -1.0, -1.0, -1.0)


@dataclass
class MDLFace:
    """Triangle face data for meshes.

    Attributes:
        v1 (int): First vertex index.
        v2 (int): Second vertex index.
        v3 (int): Third vertex index.
        material (SurfaceMaterial): Surface material type.
        smoothing_group (int): Smoothing group ID.
        surface_light (int): Surface light value.
        plane_distance (float): Distance along face normal.
        normal (Vector3): Face normal vector.
        a1 (int): First adjacent face index.
        a2 (int): Second adjacent face index.
        a3 (int): Third adjacent face index.
        coefficient (int): Plane coefficient.
    """

    v1: int = 0
    v2: int = 0
    v3: int = 0
    material: SurfaceMaterial = SurfaceMaterial.GRASS
    smoothing_group: int = 0
    surface_light: int = 0
    plane_distance: float = 0.0
    normal: Vector3 = field(default_factory=Vector3.from_null)
    a1: int = 0
    a2: int = 0
    a3: int = 0
    coefficient: int = 0


@dataclass
class MDLConstraint:
    """Constraint data that can be attached to a node.

    Attributes:
        name (str): Constraint name.
        type (int): Constraint type.
        target (int): Target value.
        target_node (int): Target node ID.
    """

    name: str = ""
    type: int = 0
    target: int = 0
    target_node: int = 0


@dataclass
class MDLMesh:
    """Mesh data that can be attached to a node.

    Attributes:
        faces (list[MDLFace]): Triangle faces.
        diffuse (Color): Diffuse color.
        ambient (Color): Ambient color.
        transparency_hint (int): Transparency settings.
        texture_1 (ResRef): Primary texture name.
        texture_2 (ResRef): Secondary texture name.
        animate_uv (bool): Whether UVs are animated.
        uv_direction_x (float): UV animation X direction.
        uv_direction_y (float): UV animation Y direction.
        uv_jitter (float): UV jitter amount.
        uv_jitter_speed (float): UV jitter speed.
        radius (float): Bounding sphere radius.
        bb_min (Vector3): Bounding box minimum.
        bb_max (Vector3): Bounding box maximum.
        average (Vector3): Average vertex position.
        area (float): Total surface area.
        has_lightmap (bool): Whether mesh has lightmap.
        rotate_texture (bool): Whether textures should rotate.
        background_geometry (bool): Whether mesh is background geometry.
        shadow (bool): Whether mesh casts shadows.
        beaming (bool): Whether mesh has beaming effect.
        render (bool): Whether mesh should be rendered.
        vertex_positions (list[Vector3]): Vertex positions.
        vertex_normals (list[Vector3] | None): Vertex normals.
        vertex_uv1 (list[Vector2] | None): Primary UV coordinates.
        vertex_uv2 (list[Vector2] | None): Secondary UV coordinates.
        dirt_enabled (bool): Whether dirt mapping is enabled.
        dirt_texture (ResRef): Dirt texture name.
        dirt_coordinate_space (int): Dirt coordinate space.
        hide_in_hologram (bool): Whether to hide in hologram view.
    """

    faces: list[MDLFace] = field(default_factory=list)
    diffuse: Color = field(default_factory=lambda: Color.WHITE)
    ambient: Color = field(default_factory=lambda: Color.WHITE)
    transparency_hint: int = 0
    texture_1: ResRef = ResRef.from_blank()
    texture_2: ResRef = ResRef.from_blank()
    animate_uv: bool = False
    uv_direction_x: float = 0.0
    uv_direction_y: float = 0.0
    uv_jitter: float = 0.0
    uv_jitter_speed: float = 0.0
    radius: float = 0.0
    bb_min: Vector3 = field(default_factory=Vector3.from_null)
    bb_max: Vector3 = field(default_factory=Vector3.from_null)
    average: Vector3 = field(default_factory=Vector3.from_null)
    area: float = 0.0
    has_lightmap: bool = False
    rotate_texture: bool = False
    background_geometry: bool = False
    shadow: bool = False
    beaming: bool = False
    render: bool = True
    vertex_positions: list[Vector3] = field(default_factory=list)
    vertex_normals: list[Vector3] | None = None
    vertex_uv1: list[Vector2] | None = None
    vertex_uv2: list[Vector2] | None = None
    dirt_enabled: bool = False
    dirt_texture: ResRef = ResRef.from_blank()
    dirt_coordinate_space: int = 0
    hide_in_hologram: bool = False


@dataclass
class MDLSkin(MDLMesh):
    """Skin data that can be attached to a node.

    Attributes:
        bone_indices (list[int]): Indices into bone array.
        qbones (list[Vector4]): Bone quaternion rotations.
        tbones (list[Vector3]): Bone translations.
        bonemap (list[int]): Bone mapping indices.
        vertex_bones (list[MDLBoneVertex]): Per-vertex bone weights.
    """

    bone_indices: list[int] = field(default_factory=list)
    qbones: list[Vector4] = field(default_factory=list)
    tbones: list[Vector3] = field(default_factory=list)
    bonemap: list[int] = field(default_factory=list)
    vertex_bones: list[MDLBoneVertex] = field(default_factory=list)


@dataclass
class MDLDangly(MDLMesh):
    """Dangly data that can be attached to a node.

    Attributes:
        constraints (list[MDLConstraint]): Physics constraints.
        displacement (float): Displacement amount.
        tightness (float): Spring tightness.
        period (float): Animation period.
    """

    constraints: list[MDLConstraint] = field(default_factory=list)
    displacement: float = 0.0
    tightness: float = 0.0
    period: float = 0.0
