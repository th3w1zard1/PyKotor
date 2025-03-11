"""Constants used in MDL format."""  # FIXME: delete this file and update everything to use enums.py

from __future__ import annotations

from enum import IntFlag

# Model function pointers for game detection
MODEL_FN_PTR_1_K1_PC = 0x0
MODEL_FN_PTR_1_K1_XBOX = 0x3C
MODEL_FN_PTR_1_K2_PC = 0x98
MODEL_FN_PTR_1_K2_XBOX = 0xA0

# MDX data flags
class MDXFlags(IntFlag):
    """Flags indicating what data is present in MDX file."""
    VERTEX = 0x0001
    NORMAL = 0x0002
    COLOR = 0x0004
    UV1 = 0x0008
    UV2 = 0x0010
    UV3 = 0x0020
    UV4 = 0x0040
    TANGENT = 0x0080

# Node type flags
class NodeFlags(IntFlag):
    """Flags indicating node type and features."""
    DUMMY = 0x0000  # No flags set = dummy node
    HEADER = 0x0001
    LIGHT = 0x0002
    EMITTER = 0x0004
    CAMERA = 0x0008
    REFERENCE = 0x0010
    MESH = 0x0020
    SKIN = 0x0040
    ANIM = 0x0080
    DANGLY = 0x0100
    AABB = 0x0200
    SABER = 0x0400

# Controller types
class ControllerType:
    """Types of animation controllers."""
    POSITION = 8
    ORIENTATION = 20
    SCALE = 36
    ALPHA = 128
    COLOR = 76
    RADIUS = 88
    SHADOW_RADIUS = 96
    VERTICAL_DISPLACEMENT = 100
    MULTIPLIER = 140
    ALPHA_END = 80
    ALPHA_START = 84
    BIRTHRATE = 92
    BOUNCE_CO = 94
    COMBO_TIME = 168
    DRAG = 156
    FRAME_END = 164
    FRAME_START = 160
    GRAV = 152
    LIFE_EXP = 104
    MASS = 148
    P2P_BEZIER2 = 132
    P2P_BEZIER3 = 136
    PARTICLE_ROT = 144
    RAND_VEL = 124
    SIZE_START = 108
    SIZE_END = 112
    SIZE_START_Y = 116
    SIZE_END_Y = 120
    SPREAD = 128
    THRESHOLD = 172
    VELOCITY = 176
    XSIZE = 180
    YSIZE = 184
    BLUR_LENGTH = 188
    LIGHTNING_DELAY = 192
    LIGHTNING_RADIUS = 196
    LIGHTNING_SCALE = 200
    LIGHTNING_STATE = 204
    ALPHA_MID = 208
    COLOR_MID = 212
    PERCENT_START = 216
    PERCENT_MID = 220
    PERCENT_END = 224

# Controller flags
CTRL_FLAG_BEZIER = 0x80

# Emitter flags
class EmitterFlags(IntFlag):
    """Flags controlling emitter behavior."""
    P2P = 0x0001
    P2P_SEL = 0x0002
    AFFECTED_BY_WIND = 0x0004
    TINTED = 0x0008
    BOUNCE = 0x0010
    RANDOM = 0x0020
    INHERIT = 0x0040
    INHERIT_VEL = 0x0080
    INHERIT_LOCAL = 0x0100
    SPLAT = 0x0200
    INHERIT_PART = 0x0400
    DEPTH_TEXTURE = 0x0800

# Render flags
class RenderFlags(IntFlag):
    """Flags controlling rendering behavior."""
    RENDER = 0x0001
    SHADOW = 0x0002
    BEAMING = 0x0004
    RENDER_ENVIRONMENT_MAP = 0x0008
    BACKGROUND_GEOMETRY = 0x0010

# Animation flags
class AnimationFlags(IntFlag):
    """Flags controlling animation behavior."""
    ANIMATE_UV = 0x0001
    ROTATE_TEXTURE = 0x0002

# Constants
MDL_OFFSET = 12  # Base offset for MDL data
NUM_SABER_VERTS = 96  # Number of vertices in lightsaber mesh

# Lightsaber face indices
SABER_FACES = [
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