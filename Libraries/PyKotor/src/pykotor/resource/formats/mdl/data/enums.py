"""Enums and flags for MDL format."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, IntFlag, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Literal


class MDLSaberType(IntEnum):
    """Type of lightsaber blade.

    These values are based on the classification flags from the MDL format.
    """

    STANDARD = 0x10
    """Standard lightsaber blade"""

    DOUBLE = 0x20
    """Double-bladed lightsaber"""

    SHORT = 0x40
    """Short lightsaber/shoto"""

    STAFF = 0x80
    """Lightsaber staff/pike"""


class MDLClassification(IntEnum):
    """Model usage classification.

    Determines how the engine treats the model for various purposes like:
    - Collision detection
    - Animation handling
    - Rendering optimizations
    - Physics behavior
    """

    OTHER = 0
    """Default/unknown classification"""

    CHARACTER = auto()
    """NPCs, PCs, and creatures"""

    DOOR = auto()
    """Door models with associated open/close animations"""

    PLACEABLE = auto()
    """Static objects that can be placed in the world"""

    EFFECT = auto()
    """Visual effects and particles"""

    TILE = auto()
    """Terrain/level geometry pieces"""

    GUI = auto()
    """Interface elements"""

    FURNITURE = auto()
    """Static decorative objects"""

    WEAPON = auto()
    """Weapon models"""

    LIGHTSABER = auto()
    """Special case of weapon for lightsabers"""

    ARMOR = auto()
    """Wearable armor models"""

    WAYPOINT = auto()
    """Navigation markers"""

    CAMERA = auto()
    """Camera control objects"""

    REFERENCE = auto()
    """Reference geometry"""


class MDXDataFlags(IntFlag):
    """Flags indicating what vertex data is present in MDX file."""

    VERTICES = 0x0001
    """Vertex positions are present."""

    TEX0_VERTICES = 0x0002
    """Primary UV coordinates are present."""

    TEX1_VERTICES = 0x0004
    """Secondary UV coordinates are present."""

    TEX2_VERTICES = 0x0008
    """Third UV coordinates are present (unconfirmed)."""

    TEX3_VERTICES = 0x0010
    """Fourth UV coordinates are present (unconfirmed)."""

    VERTEX_NORMALS = 0x0020
    """Vertex normals are present."""

    VERTEX_COLORS = 0x0040
    """Vertex colors are present (unconfirmed)."""

    TANGENT_SPACE = 0x0080
    """Tangent space data is present."""

    BONE_WEIGHTS = 0x0800
    """Bone weights for skinning."""

    BONE_INDICES = 0x1000
    """Bone indices for skinning."""


class MDLGeometryType(IntEnum):
    """Model geometry type indicating how it should be rendered."""

    GEOMETRY_UNKNOWN = 0x00
    GEOMETRY_NORMAL = 0x01
    GEOMETRY_SKINNED = 0x02
    GEOMETRY_DANGLY = 0x03
    GEOMETRY_SABER = 0x04
    GEOMETRY_DOOR = 0x05
    GEOMETRY_AABB = 0x06
    GEOMETRY_EMITTER = 0x07
    GEOMETRY_LIGHT = 0x08
    GEOMETRY_CAMERA = 0x09
    GEOMETRY_REFERENCE = 0x0A


class MDLModelType(IntEnum):
    """The type/class of model this MDL file represents (character, door, effect, etc)."""

    INVALID = 0x0000
    EFFECT = 0x0001
    TILE = 0x0002
    CHARACTER = 0x0004
    DOOR = 0x0008
    PLACEABLE = 0x0010
    OTHER = 0x0020
    GUI = 0x0040
    ITEM = 0x0080
    LIGHTSABER = 0x0100
    WAYPOINT = 0x0200
    WEAPON = 0x0400
    FURNITURE = 0x0800
    CREATURE = 0x1000
    PROJECTILE = 0x2000
    AREA_EFFECT = 0x4000
    TRIGGER = 0x8000
    SOUND = 0x10000


class MDLNodeFlags(IntFlag):
    """Node flags indicating what type of data is attached to the node."""

    HAS_HEADER = 0x00000001
    """Node has a header"""

    HAS_LIGHT = 0x00000002
    """Node has light data"""

    HAS_EMITTER = 0x00000004
    """Node has emitter data"""

    HAS_CAMERA = 0x00000008
    """Node has camera data"""

    HAS_REFERENCE = 0x00000010
    """Node has reference data"""

    HAS_MESH = 0x00000020
    """Node has mesh data"""

    HAS_SKIN = 0x00000040
    """Node has skin data"""

    HAS_ANIM = 0x00000080
    """Node has animation data"""

    HAS_DANGLY = 0x00000100
    """Node has dangly mesh data"""

    HAS_AABB = 0x00000200
    """Node has AABB (bounding box) data"""

    HAS_SABER = 0x00000800
    """Node has lightsaber data"""


class MDLComponentType(IntEnum):
    """Types of components that can exist within an MDL model (meshes, lights, emitters, etc)."""

    DUMMY = 1
    """Empty node for hierarchy."""

    LIGHT = 3
    """Light source."""

    EMITTER = 5
    """Particle emitter."""

    REFERENCE = 17
    """Reference to another model."""

    TRIMESH = 33
    """Basic mesh."""

    SKIN = 97
    """Skinned mesh."""

    ANIMMESH = 161
    """Animated mesh."""

    DANGLYMESH = 289
    """Physics-enabled mesh."""

    AABB = 545
    """Axis-aligned bounding box."""

    SABER = 2081
    """Lightsaber blade."""


class MDLControllerType(IntEnum):
    """Controller types for animations."""

    INVALID = -1
    """Invalid controller type."""

    POSITION = 8
    """Position controller."""

    ORIENTATION = 20
    """Orientation controller."""

    SCALE = 36
    """Scale controller."""

    ALPHA = 132
    """Alpha/opacity controller."""

    COLOR = 76
    """Light color controller."""

    RADIUS = 88
    """Light radius controller."""

    SHADOWRADIUS = 96
    """Shadow radius controller."""

    VERTICALDISPLACEMENT = 100
    """Vertical displacement controller."""

    ULTIPLIER = 140
    """Light multiplier controller."""

    ALPHAEND = 80
    """Alpha end controller."""

    ALPHASTART = 84
    """Alpha start controller."""

    BIRTHRATE = 88
    """Birth rate controller."""

    BOUNCE_CO = 92
    """Bounce coefficient controller."""

    COMBINETIME = 96
    """Combine time controller."""

    DRAG = 100
    """Drag controller."""

    FPS = 104
    """Frames per second controller."""

    FRAMEEND = 108
    """End frame controller."""

    FRAMESTART = 112
    """Start frame controller."""

    GRAV = 116
    """Gravity controller."""

    LIFEEXP = 120
    """Life expectancy controller."""

    MASS = 124
    """Mass controller."""

    P2P_BEZIER2 = 128
    """Point-to-point Bezier curve controller (2)."""

    P2P_BEZIER3 = 132
    """Point-to-point Bezier curve controller (3)."""

    PARTICLEROT = 136
    """Particle rotation controller."""

    RANDVEL = 140
    """Random velocity controller."""

    SIZESTART = 144
    """Start size controller."""

    SIZEEND = 148
    """End size controller."""

    SIZESTART_Y = 152
    """Start size Y controller."""

    SIZEEND_Y = 156
    """End size Y controller."""

    SPREAD = 160
    """Spread controller."""

    THRESHOLD = 164
    """Threshold controller."""

    VELOCITY = 168
    """Velocity controller."""

    XSIZE = 172
    """X size controller."""

    YSIZE = 176
    """Y size controller."""

    BLURLENGTH = 180
    """Blur length controller."""

    LIGHTNINGDELAY = 184
    """Lightning delay controller."""

    LIGHTNINGRADIUS = 188
    """Lightning radius controller."""

    LIGHTNINGSCALE = 192
    """Lightning scale controller."""

    LIGHTNINGSUBDIV = 196
    """Lightning subdivision controller."""

    LIGHTNINGZIGZAG = 200
    """Lightning zigzag controller."""

    ALPHAMID = 216
    """Alpha mid controller."""

    PERCENTSTART = 220
    """Percent start controller."""

    PERCENTMID = 224
    """Percent mid controller."""

    PERCENTEND = 228
    """Percent end controller."""

    SIZEMID = 232
    """Size mid controller."""

    SIZEMID_Y = 236
    """Size mid Y controller."""

    RANDOM_BIRTHRATE = 240
    """Random birth rate controller."""

    TARGETSIZE = 252
    """Target size controller."""

    NUM_CONTROL_POINTS = 256
    """Number of control points."""

    CONTROLPT_RADIUS = 260
    """Control point radius."""

    CONTROLPT_DELAY = 264
    """Control point delay."""

    TANGENT_SPREAD = 268
    """Tangent spread controller."""

    TANGENT_LENGTH = 272
    """Tangent length controller."""

    COLORMID = 284
    """Color mid controller."""

    COLOREND = 380
    """Color end controller."""

    COLORSTART = 392
    """Color start controller."""

    DETONATE = 502
    """Detonate controller."""

    SELFILLUMCOLOR = 100
    """Self-illumination color controller."""


class MDLTrimeshProps(IntFlag):
    """Properties for trimesh nodes."""

    NONE = 0x00
    COMPRESSED = 0x02
    """Mesh data is compressed"""

    UNKNOWN = 0x04
    """Unknown flag"""

    TANGENTS = 0x08
    """Has tangent data"""

    BEAMING = 0x10
    """Has beaming effect"""

    RENDER_ENV_MAP = 0x20
    """Should render environment mapping"""


class MDLEmitterType(IntEnum):
    """Types of particle emitters."""

    STATIC = 0
    FIRE = 1
    FOUNTAIN = 2
    LIGHTNING = 3


class MDLRenderType(IntEnum):
    """Particle rendering types."""

    NORMAL = 0
    LINKED = 1
    BILLBOARD_TO_LOCAL_Z = 2
    BILLBOARD_TO_WORLD_Z = 3
    ALIGNED_TO_WORLD_Z = 4
    ALIGNED_TO_PARTICLE_DIR = 5
    MOTION_BLUR = 6


class MDLBlendType(IntEnum):
    """Particle blend modes."""

    NORMAL = 0
    PUNCH = 1
    LIGHTEN = 2
    MULTIPLY = 3


class MDLUpdateType(IntEnum):
    """Particle update modes."""

    FOUNTAIN = 0
    SINGLE = 1
    EXPLOSION = 2
    LIGHTNING = 3


class MDLTrimeshFlags(IntFlag):
    """Additional trimesh flags from xoreos KotOR implementation."""

    TILEFADE = 0x0001
    """Has tile fade"""
    HEAD = 0x0002
    """Is a head mesh"""
    RENDER = 0x0004
    """Should be rendered"""
    SHADOW = 0x0008
    """Casts shadows"""
    BEAMING = 0x0010
    """Has beaming"""
    RENDER_ENV_MAP = 0x0020
    """Should render environment mapping"""
    LIGHTMAP = 0x0040
    """Has lightmap"""
    SKIN = 0x0080
    """Is skinned mesh"""


class MDLLightFlags(IntFlag):
    """Light flags from xoreos KotOR implementation."""

    ENABLED = 0x0001
    """Light is enabled"""
    SHADOW = 0x0002
    """Light casts shadows"""
    FLARE = 0x0004
    """Light has lens flare"""
    FADING = 0x0008
    """Light is fading"""
    AMBIENT = 0x0010
    """Light is ambient only"""


class MDLEmitterFlags(IntFlag):
    """Emitter flags from xoreos KotOR implementation."""

    LOOP = 0x0001
    """Particle system loops"""
    BOUNCE = 0x0002
    """Particles bounce"""
    RANDOM = 0x0004
    """Random initial rotation"""
    INHERIT = 0x0008
    """Inherit parent orientation"""
    INHERIT_VEL = 0x0010
    """Inherit parent velocity"""
    INHERIT_LOCAL = 0x0020
    """Inherit local transform"""
    SPLAT = 0x0040
    """Splat particles on collision"""
    INHERIT_PART = 0x0080
    """Inherit parent particle"""


class MDLSaberFlags(IntFlag):
    """Lightsaber flags from xoreos KotOR implementation."""

    FLARE = 0x0001
    """Has flare effect"""
    DYNAMIC = 0x0002
    """Dynamic lighting"""
    TRAIL = 0x0004
    """Has motion trail"""


class MDLModelFlags(IntFlag):
    """Model classification flags from MDL format."""

    NONE = 0x00
    """No flags set"""

    EFFECT = 0x01
    """Visual effect model"""

    TILE = 0x02
    """Terrain/level geometry piece"""

    CHARACTER = 0x04
    """Character/creature model"""

    DOOR = 0x08
    """Door model"""

    LIGHTSABER = 0x10
    """Lightsaber model"""

    PLACEABLE = 0x20
    """Static placeable object"""

    FLYER = 0x40
    """Flying vehicle/creature"""

    GUI = 0x80  # TODO: check if this is correct, vendor/kotorblender will have the answer.
    """GUI element"""

    ITEM = 0x100  # TODO: check if this is correct, vendor/kotorblender will have the answer.
    """Item model"""


SABER_FACES: list[list[int]] = [
    [5, 4, 0],
    [0, 1, 5],
    [13, 8, 12],
    [8, 13, 9],
    [6, 5, 1],
    [1, 2, 6],
    [10, 9, 13],
    [13, 14, 10],
    [3, 6, 2],
    [6, 3, 7],
    [15, 11, 14],
    [10, 14, 11],
]


class MDLFunctionPointers(IntEnum):
    """Function pointers for different game versions and platforms."""

    MODEL_FN_PTR_1_K1_PC = 4273776
    MODEL_FN_PTR_1_K2_PC = 4285200
    MODEL_FN_PTR_2_K1_PC = 4216096
    MODEL_FN_PTR_2_K2_PC = 4216320
    MODEL_FN_PTR_1_K1_XBOX = 4254992
    MODEL_FN_PTR_2_K1_XBOX = 4255008
    MODEL_FN_PTR_1_K2_XBOX = 4285872
    MODEL_FN_PTR_2_K2_XBOX = 4216016

    ANIM_FN_PTR_1_K1_PC = 4273392
    ANIM_FN_PTR_2_K1_PC = 4451552
    ANIM_FN_PTR_1_K2_PC = 4284816
    ANIM_FN_PTR_2_K2_PC = 4522928
    ANIM_FN_PTR_1_K1_XBOX = 4253536
    ANIM_FN_PTR_2_K1_XBOX = 4573360
    ANIM_FN_PTR_1_K2_XBOX = 4285488
    ANIM_FN_PTR_2_K2_XBOX = 4523088

    MESH_FN_PTR_1_K1_PC = 4216656
    MESH_FN_PTR_2_K1_PC = 4216672
    MESH_FN_PTR_1_K2_PC = 4216880
    MESH_FN_PTR_2_K2_PC = 4216896
    MESH_FN_PTR_1_K1_XBOX = 4267376
    MESH_FN_PTR_2_K1_XBOX = 4264048
    MESH_FN_PTR_1_K2_XBOX = 4216576
    MESH_FN_PTR_2_K2_XBOX = 4216592

    SKIN_FN_PTR_1_K1_PC = 4216592
    SKIN_FN_PTR_1_K2_PC = 4216816
    SKIN_FN_PTR_2_K1_PC = 4216608
    SKIN_FN_PTR_2_K2_PC = 4216832
    SKIN_FN_PTR_1_K1_XBOX = 4264032
    SKIN_FN_PTR_2_K1_XBOX = 4264048
    SKIN_FN_PTR_1_K2_XBOX = 4216512
    SKIN_FN_PTR_2_K2_XBOX = 4216528

    DANGLY_FN_PTR_1_K1_PC = 4216640
    DANGLY_FN_PTR_1_K2_PC = 4216864
    DANGLY_FN_PTR_2_K1_PC = 4216624
    DANGLY_FN_PTR_2_K2_PC = 4216848
    DANGLY_FN_PTR_1_K1_XBOX = 4266736
    DANGLY_FN_PTR_2_K1_XBOX = 4266720
    DANGLY_FN_PTR_1_K2_XBOX = 4216560
    DANGLY_FN_PTR_2_K2_XBOX = 4216544


class MDLAABBFlags(IntFlag):
    """Flags for Axis-Aligned Bounding Box nodes."""

    NO_CHILDREN = 0x00
    POSITIVE_X = 0x01
    POSITIVE_Y = 0x02
    POSITIVE_Z = 0x04
    NEGATIVE_X = 0x08
    NEGATIVE_Y = 0x10
    NEGATIVE_Z = 0x20


@dataclass
class EmitterControllerKey:
    """Dataclass for controller key mapping."""

    offset: int
    name: str
    columns: int


@dataclass
class ControllerKey:
    ctrl_type: int
    num_rows: int
    timekeys_start: int
    values_start: int
    num_columns: int


class MDLControllerConstants:
    """Constants for controller types and properties."""

    NUM_SABER_VERTS: Literal[176] = 0xB0
    CTRL_FLAG_BEZIER: Literal[16] = 0x10

    # Controller key mapping tuples (offset, name, columns)
    EMITTER_CONTROLLER_KEYS: list[EmitterControllerKey] = [
        EmitterControllerKey(80, "alphaend", 1),
        EmitterControllerKey(84, "alphastart", 1),
        EmitterControllerKey(88, "birthrate", 1),
        EmitterControllerKey(92, "bounce_co", 1),
        EmitterControllerKey(96, "combinetime", 1),
        EmitterControllerKey(100, "drag", 1),
        EmitterControllerKey(104, "fps", 1),
        EmitterControllerKey(108, "frameend", 1),
        EmitterControllerKey(112, "framestart", 1),
        EmitterControllerKey(116, "grav", 1),
        EmitterControllerKey(120, "lifeexp", 1),
        EmitterControllerKey(124, "mass", 1),
        EmitterControllerKey(128, "p2p_bezier2", 1),
        EmitterControllerKey(132, "p2p_bezier3", 1),
        EmitterControllerKey(136, "particlerot", 1),
        EmitterControllerKey(140, "randvel", 1),
        EmitterControllerKey(144, "sizestart", 1),
        EmitterControllerKey(148, "sizeend", 1),
        EmitterControllerKey(152, "sizestart_y", 1),
        EmitterControllerKey(156, "sizeend_y", 1),
        EmitterControllerKey(160, "spread", 1),
        EmitterControllerKey(164, "threshold", 1),
        EmitterControllerKey(168, "velocity", 1),
        EmitterControllerKey(172, "xsize", 1),
        EmitterControllerKey(176, "ysize", 1),
        EmitterControllerKey(180, "blurlength", 1),
        EmitterControllerKey(184, "lightningdelay", 1),
        EmitterControllerKey(188, "lightningradius", 1),
        EmitterControllerKey(192, "lightningscale", 1),
        EmitterControllerKey(196, "lightningsubdiv", 1),
        EmitterControllerKey(200, "lightningzigzag", 1),
        EmitterControllerKey(216, "alphamid", 1),
        EmitterControllerKey(220, "percentstart", 1),
        EmitterControllerKey(224, "percentmid", 1),
        EmitterControllerKey(228, "percentend", 1),
        EmitterControllerKey(232, "sizemid", 1),
        EmitterControllerKey(236, "sizemid_y", 1),
        EmitterControllerKey(240, "randombirthrate", 1),
        EmitterControllerKey(252, "targetsize", 1),
        EmitterControllerKey(256, "numcontrolpts", 1),
        EmitterControllerKey(260, "controlptradius", 1),
        EmitterControllerKey(264, "controlptdelay", 1),
        EmitterControllerKey(268, "tangentspread", 1),
        EmitterControllerKey(272, "tangentlength", 1),
        EmitterControllerKey(284, "colormid", 3),
        EmitterControllerKey(380, "colorend", 3),
        EmitterControllerKey(392, "colorstart", 3),
    ]
