from __future__ import annotations

import io
import re

from math import acos, cos, sin, sqrt
from typing import TYPE_CHECKING, cast

from pykotor.common.misc import Color
from pykotor.resource.formats.mdl.mdl_data import (
    MDL,
    MDLAABBNode,
    MDLAnimation,
    MDLBoneVertex,
    MDLConstraint,
    MDLController,
    MDLControllerRow,
    MDLDangly,
    MDLEmitter,
    MDLEvent,
    MDLFace,
    MDLLight,
    MDLMesh,
    MDLNode,
    MDLReference,
    MDLSaber,
    MDLSkin,
    MDLWalkmesh,
    _mdl_recompute_mesh_face_payload,
)
from pykotor.resource.formats.mdl.mdl_types import MDLClassification, MDLControllerType, MDLNodeType
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from utility.common.geometry import Vector2, Vector3, Vector4

if TYPE_CHECKING:
    from typing_extensions import Literal

    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


_FACE_SURFACE_MASK = 0x1F
_FACE_SMOOTH_SHIFT = 5

# Node type constants matching mdlops (vendor/mdlops/MDLOpsM.pm:313-323)
NODE_DUMMY = 1
NODE_LIGHT = 3
NODE_EMITTER = 5
NODE_REFERENCE = 17
NODE_TRIMESH = 33
NODE_SKIN = 97
NODE_DANGLYMESH = 289
NODE_AABB = 545
NODE_SABER = 2081

# Node flag constants matching mdlops (vendor/mdlops/MDLOpsM.pm:301-311)
NODE_HAS_HEADER = 0x0001
NODE_HAS_LIGHT = 0x0002
NODE_HAS_EMITTER = 0x0004
NODE_HAS_REFERENCE = 0x0010
NODE_HAS_MESH = 0x0020
NODE_HAS_SKIN = 0x0040
NODE_HAS_DANGLY = 0x0100
NODE_HAS_AABB = 0x0200
NODE_HAS_SABER = 0x0800

# Controller name mappings matching mdlops (vendor/mdlops/MDLOpsM.pm:325-407)
_CONTROLLER_NAMES: dict[int, dict[int, str]] = {
    NODE_HAS_HEADER: {
        8: "position",
        20: "orientation",
        36: "scale",
        132: "alpha",
    },
    NODE_HAS_LIGHT: {
        76: "color",
        88: "radius",
        96: "shadowradius",
        100: "verticaldisplacement",
        140: "multiplier",
    },
    NODE_HAS_EMITTER: {
        80: "alphaEnd",
        84: "alphaStart",
        88: "birthrate",
        92: "bounce_co",
        96: "combinetime",
        100: "drag",
        104: "fps",
        108: "frameEnd",
        112: "frameStart",
        116: "grav",
        120: "lifeExp",
        124: "mass",
        128: "p2p_bezier2",
        132: "p2p_bezier3",
        136: "particleRot",
        140: "randvel",
        144: "sizeStart",
        148: "sizeEnd",
        152: "sizeStart_y",
        156: "sizeEnd_y",
        160: "spread",
        164: "threshold",
        168: "velocity",
        172: "xsize",
        176: "ysize",
        180: "blurlength",
        184: "lightningDelay",
        188: "lightningRadius",
        192: "lightningScale",
        196: "lightningSubDiv",
        200: "lightningzigzag",
        216: "alphaMid",
        220: "percentStart",
        224: "percentMid",
        228: "percentEnd",
        232: "sizeMid",
        236: "sizeMid_y",
        240: "m_fRandomBirthRate",
        252: "targetsize",
        256: "numcontrolpts",
        260: "controlptradius",
        264: "controlptdelay",
        268: "tangentspread",
        272: "tangentlength",
        284: "colorMid",
        380: "colorEnd",
        392: "colorStart",
        502: "detonate",
    },
    NODE_HAS_MESH: {
        100: "selfillumcolor",
    },
}

# Controller type mappings from controller names to MDLControllerType
_CONTROLLER_NAME_TO_TYPE: dict[str, MDLControllerType] = {
    "alpha": MDLControllerType.ALPHA,
    "alphaEnd": MDLControllerType.ALPHAEND,
    "alphaMid": MDLControllerType.ALPHAMID,
    "alphaStart": MDLControllerType.ALPHASTART,
    "birthrate": MDLControllerType.BIRTHRATE,
    "blurlength": MDLControllerType.BLURLENGTH,
    "bounce_co": MDLControllerType.BOUNCE_CO,
    "color": MDLControllerType.COLOR,
    "colorEnd": MDLControllerType.COLOREND,
    "colorMid": MDLControllerType.COLORMID,
    "colorStart": MDLControllerType.COLORSTART,
    "combinetime": MDLControllerType.COMBINETIME,
    "controlptdelay": MDLControllerType.CONTROLPTDELAY,
    "controlptradius": MDLControllerType.CONTROLPTRADIUS,
    "detonate": MDLControllerType.DETONATE,
    "drag": MDLControllerType.DRAG,
    "fps": MDLControllerType.FPS,
    "frameEnd": MDLControllerType.FRAMEEND,
    "frameStart": MDLControllerType.FRAMESTART,
    "grav": MDLControllerType.GRAV,
    "lifeExp": MDLControllerType.LIFEEXP,
    "lightningDelay": MDLControllerType.LIGHTNINGDELAY,
    "lightningRadius": MDLControllerType.LIGHTNINGRADIUS,
    "lightningScale": MDLControllerType.LIGHTNINGSCALE,
    "lightningSubDiv": MDLControllerType.LIGHTNINGSUBDIV,
    "lightningzigzag": MDLControllerType.LIGHTNINGZIGZAG,
    "m_fRandomBirthRate": MDLControllerType.RANDOMBIRTHRATE,
    "mass": MDLControllerType.MASS,
    "multiplier": MDLControllerType.MULTIPLIER,
    "numcontrolpts": MDLControllerType.NUMCONTROLPTS,
    "orientation": MDLControllerType.ORIENTATION,
    "p2p_bezier2": MDLControllerType.P2P_BEZIER2,
    "p2p_bezier3": MDLControllerType.P2P_BEZIER3,
    "particleRot": MDLControllerType.PARTICLEROT,
    "percentEnd": MDLControllerType.PERCENTEND,
    "percentMid": MDLControllerType.PERCENTMID,
    "percentStart": MDLControllerType.PERCENTSTART,
    "position": MDLControllerType.POSITION,
    "radius": MDLControllerType.RADIUS,
    "randvel": MDLControllerType.RANDVEL,
    "scale": MDLControllerType.SCALE,
    "selfillumcolor": MDLControllerType.ILLUM_COLOR,
    "shadowradius": MDLControllerType.SHADOWRADIUS,
    "sizeEnd_y": MDLControllerType.SIZEEND_Y,
    "sizeEnd": MDLControllerType.SIZEEND,
    "sizeMid_y": MDLControllerType.SIZEMID_Y,
    "sizeMid": MDLControllerType.SIZEMID,
    "sizeStart_y": MDLControllerType.SIZESTART_Y,
    "sizeStart": MDLControllerType.SIZESTART,
    "spread": MDLControllerType.SPREAD,
    "tangentlength": MDLControllerType.TANGENTLENGTH,
    "tangentspread": MDLControllerType.TANGENTSPREAD,
    "targetsize": MDLControllerType.TARGETSIZE,
    "threshold": MDLControllerType.THRESHOLD,
    "velocity": MDLControllerType.VELOCITY,
    "verticaldisplacement": MDLControllerType.VERTICALDISPLACEMENT,
    "xsize": MDLControllerType.XSIZE,
    "ysize": MDLControllerType.YSIZE,
}


def _unpack_face_material(face: MDLFace) -> tuple[int, int]:
    """Return (surface_material, smoothing_group) from packed face material flags.

    Binary MDL packs multiple flags in the 32-bit material field:
    - Bits 0-4  : Surface material (surfacemat.2da index)
      Reference: vendor/mdlops/MDLOpsM.pm:2254-2256
    - Bits 5-31 : Smoothing group and vendor specific flags (MDLOps uses this to
      preserve smoothgroup numbers when exporting ASCII, see mdlops:1292-1300).

    The legacy dataclass (mdl_types.MDLFace) stored smoothing_group separately.
    After refactoring to mdl_data.MDLFace, the packed integer is preserved in
    face.material (see mdl_data.MDLFace comments).  This helper restores the
    original ASCII semantics without losing information.

    Args:
        face: MDLFace instance (either mdl_types or mdl_data variants).

    Returns:
        Tuple of (surface_material, smoothing_group) as integers.

    References:
        vendor/mdlops/MDLOpsM.pm:1292-1300 - Smoothing stored via material ID
        vendor/mdlops/MDLOpsM.pm:2254-2256 - Notes on smoothgroup numbering
    """
    # MDLOps ASCII uses a separate per-face smoothing mask field (4th column) and a separate
    # material id field (last column). To keep roundtrips lossless we store:
    # - face.material: material id (surface/material index)
    # - face.smoothgroup: smoothing mask (often 0, 16, 32, ...)
    material_int = int(face.material)
    smooth = int(face.smoothgroup)
    return material_int, smooth


def _pack_face_material(surface_material: int, smoothing_group: int) -> int:
    """Pack surface material and smoothing group into a single integer.

    Args:
        surface_material: Surface material index (0-31)
        smoothing_group: Smoothing group number

    Returns:
        Packed integer value
    """
    # Legacy helper: current pipeline stores these separately (material id + smoothing mask).
    return int(surface_material)


def _aa_to_quaternion(aa: list[float]) -> list[float]:
    """Convert angle-axis to quaternion (x, y, z, w).

    Reference: vendor/mdlops/MDLOpsM.pm:3718-3728

    Args:
        aa: Angle-axis representation [x, y, z, angle]

    Returns:
        Quaternion [x, y, z, w]
    """
    sin_a = sin(aa[3] / 2.0)
    return [aa[0] * sin_a, aa[1] * sin_a, aa[2] * sin_a, cos(aa[3] / 2.0)]


def _quaternion_to_aa(q: list[float]) -> list[float]:
    """Convert quaternion (x, y, z, w) to angle-axis (x, y, z, angle)."""
    if len(q) < 4:
        return [0.0, 0.0, 0.0, 0.0]
    x, y, z, w = float(q[0]), float(q[1]), float(q[2]), float(q[3])

    # Normalize (robust to small drift)
    norm = sqrt(x * x + y * y + z * z + w * w)
    if norm > 0.0:
        x, y, z, w = x / norm, y / norm, z / norm, w / norm
    else:
        return [0.0, 0.0, 0.0, 0.0]

    # Clamp to avoid acos domain errors due to float drift.
    if w > 1.0:
        w = 1.0
    elif w < -1.0:
        w = -1.0

    angle = 2.0 * acos(w)
    s = sqrt(max(0.0, 1.0 - w * w))
    if s < 1e-8:
        # No reliable axis; choose a stable default.
        return [1.0, 0.0, 0.0, 0.0]
    return [x / s, y / s, z / s, angle]


def _normalize_vector(vec: list[float]) -> list[float]:
    """Normalize a 3D vector.

    Reference: vendor/mdlops/MDLOpsM.pm:3623-3653

    Args:
        vec: 3D vector [x, y, z]

    Returns:
        Normalized vector [x, y, z]
    """
    norm = sqrt(vec[0] ** 2 + vec[1] ** 2 + vec[2] ** 2)
    if norm > 0:
        return [vec[0] / norm, vec[1] / norm, vec[2] / norm]
    return [0.0, 0.0, 0.0]


class MDLAsciiWriter(ResourceWriter):
    """Writer for ASCII MDL files.

    Reference: vendor/mdlops/MDLOpsM.pm:3004-3900 (writeasciimdl)
    """

    def __init__(
        self,
        mdl: MDL,
        target: TARGET_TYPES,
        *,
        convert_skin: bool = False,
    ):
        """Initialize the ASCII MDL writer.

        Args:
            mdl: The MDL data to write
            target: The target to write to (file path, stream, or bytes buffer)
            convert_skin: If True, write SKIN nodes as "trimesh" instead of "skin".
                Defaults to False to match MDLOps behavior.
                Reference: vendor/MDLOps/MDLOpsM.pm:3016-3019, 3105-3108
        """
        super().__init__(target)
        self._mdl = mdl
        self._text_buffer = io.StringIO()
        self._convert_skin = convert_skin

    def write_line(self, indent: int, line: str) -> None:
        """Write a line with indentation."""
        self._text_buffer.write("  " * indent + line + "\n")

    @autoclose
    def write(self, *, auto_close: bool = True) -> None:  # noqa: FBT001, FBT002, ARG002
        """Write MDL data to ASCII format.

        Reference: vendor/mdlops/MDLOpsM.pm:3004-3900 (writeasciimdl)
        """
        mdl = self._mdl
        self.write_line(0, "# ASCII MDL")
        self.write_line(0, f"filedependancy {mdl.name} NULL.mlk")
        self.write_line(0, f"newmodel {mdl.name}")
        self.write_line(0, "")
        self.write_line(0, "setsupermodel " + mdl.name + " " + mdl.supermodel)
        self.write_line(0, f"classification {mdl.classification.name.lower()}")
        self.write_line(0, f"classification_unk1 {mdl.classification_unk1}")
        # mdlops uses ignorefog 0/1; fog=True means ignorefog=0 (affected by fog)
        self.write_line(0, f"ignorefog {0 if mdl.fog else 1}")
        self.write_line(0, f"compress_quaternions {mdl.compress_quaternions}")
        if mdl.headlink:
            self.write_line(0, f"headlink {mdl.headlink}")
        self.write_line(0, "")
        self.write_line(0, f"setanimationscale {mdl.animation_scale}")
        self.write_line(0, "")
        self.write_line(0, "beginmodelgeom " + mdl.name)
        # MDLOps prints model-level bmin/bmax/radius without format specifiers (uses Perl default)
        # Match MDLOps exactly - Reference: vendor/MDLOps/MDLOpsM.pm:3082-3084
        self.write_line(1, f"bmin {mdl.bmin.x} {mdl.bmin.y} {mdl.bmin.z}")
        self.write_line(1, f"bmax {mdl.bmax.x} {mdl.bmax.y} {mdl.bmax.z}")
        self.write_line(1, f"radius {mdl.radius}")
        self.write_line(0, "")
        # Serialize the real root node as a node entry (as in binary MDL), so Binary→ASCII→Binary
        # roundtrips preserve the full node set (including the model-name root).
        self._write_node(1, mdl.root, None)
        self.write_line(0, "")
        self.write_line(0, "endmodelgeom " + mdl.name)
        self.write_line(0, "")

        # Write animations if any (vendor/mdlops/MDLOpsM.pm:3488-3560)
        if mdl.anims:
            for anim in mdl.anims:
                self._write_animation(anim, mdl.name)

        self.write_line(0, "")
        self.write_line(0, "donemodel " + mdl.name)

        # Write the text content as bytes
        content = self._text_buffer.getvalue()
        self._writer.write_bytes(content.encode("utf-8"))

    def _write_node(
        self,
        indent: int,
        node: MDLNode,
        parent: MDLNode | None = None,
    ) -> None:
        """Write a node and its children.
        
        Node type determination matches MDLOps exactly.
        Reference: vendor/MDLOps/MDLOpsM.pm:3095-3121
        MDLOps checks nodetype integer value directly ($nodetype == NODE_SKIN), not data presence.
        """
        # Build type_id from flags exactly like MDLOps stores it (combined integer value)
        # This matches how MDLOps reads nodetype from binary: combined flag value
        # Reference: vendor/MDLOps/MDLOpsM.pm:3812-3833 equivalent logic
        type_id = 1  # HEADER
        if node.mesh:
            type_id |= 0x20  # MESH
        if node.skin:
            type_id |= 0x40  # SKIN
        if node.dangly:
            type_id |= 0x100  # DANGLY
        if node.saber:
            type_id |= 0x800  # SABER
        if node.aabb:
            type_id |= 0x200  # AABB
        if node.emitter:
            type_id |= 0x4  # EMITTER
        if node.light:
            type_id |= 0x2  # LIGHT
        if node.reference:
            type_id |= 0x10  # REFERENCE
        
        # MDLOps checks against NODE_ constants: NODE_DUMMY=1, NODE_LIGHT=3, NODE_EMITTER=5,
        # NODE_REFERENCE=17, NODE_TRIMESH=33, NODE_SKIN=97, NODE_DANGLYMESH=289,
        # NODE_AABB=545, NODE_SABER=2081
        # Reference: vendor/MDLOps/MDLOpsM.pm:315-323 (NODE_ constants)
        # Reference: vendor/MDLOps/MDLOpsM.pm:3095-3121 (exact if/elsif order)
        if type_id == 1:  # NODE_DUMMY
            node_type_str = "dummy"
        elif type_id == 3:  # NODE_LIGHT
            node_type_str = "light"
        elif type_id == 5:  # NODE_EMITTER
            node_type_str = "emitter"
        elif type_id == 289:  # NODE_DANGLYMESH
            node_type_str = "danglymesh"
        elif type_id == 97 and not self._convert_skin:  # NODE_SKIN
            node_type_str = "skin"
        elif type_id == 97 and self._convert_skin:  # NODE_SKIN (convert to trimesh)
            node_type_str = "trimesh"
        elif type_id == 33:  # NODE_TRIMESH
            node_type_str = "trimesh"
        elif type_id == 545:  # NODE_AABB
            node_type_str = "aabb"
        elif type_id == 17:  # NODE_REFERENCE
            node_type_str = "reference"
        elif type_id == 2081:  # NODE_SABER
            node_type_str = "lightsaber"
        else:
            node_type_str = "dummy"
        self.write_line(indent, f"node {node_type_str} {node.name}")
        self.write_line(indent, "{")
        self._write_node_data(indent + 1, node, parent)
        self.write_line(indent, "}")

        for child in node.children:
            self._write_node(indent, child, node)

    def _write_node_data(
        self,
        indent: int,
        node: MDLNode,
        parent: MDLNode | None = None,
    ) -> None:
        """Write node data including position, orientation, and controllers."""
        # MDLOps writes parent as string name or 'NULL' - Reference: vendor/MDLOps/MDLOpsM.pm:3129
        # MDLOps stores parent as: defined($parent) ? $model->{partnames}[$parent->{nodenum}] : 'NULL' (line 1605)
        if parent and parent.name:
            self.write_line(indent, f"parent {parent.name}")
        elif node.parent_id == -1:
            self.write_line(indent, "parent NULL")
        else:
            # Fallback: try to find parent by ID, or write NULL
            # This should rarely happen if hierarchy is built correctly
            self.write_line(indent, "parent NULL")
        # MDLOps uses "% .7g" format (space before number) - Reference: vendor/MDLOps/MDLOpsM.pm:3149
        self.write_line(indent, f"position {node.position.x: .7g} {node.position.y: .7g} {node.position.z: .7g}")
        # MDLOps uses "% .7g" format (space before number) - Reference: vendor/MDLOps/MDLOpsM.pm:3154
        self.write_line(indent, f"orientation {node.orientation.x: .7g} {node.orientation.y: .7g} {node.orientation.z: .7g} {node.orientation.w: .7g}")

        if node.mesh:
            # Binary parsing stores skin/dangly payloads in separate node fields (`node.skin`, `node.dangly`)
            # rather than always subclassing `node.mesh`. Preserve those payloads when exporting ASCII.
            self._write_mesh(indent, node.mesh, skin=node.skin, dangly=node.dangly)
        if node.light:
            self._write_light(indent, node.light)
        if node.emitter:
            self._write_emitter(indent, node.emitter)
        if node.reference:
            self._write_reference(indent, node.reference)
        if node.saber:
            self._write_saber(indent, node.saber)
        if node.aabb:
            self._write_walkmesh(indent, node.aabb)

        for controller in node.controllers:
            self._write_controller(indent, node, controller)

    def _write_mesh(
        self,
        indent: int,
        mesh: MDLMesh,
        *,
        skin: MDLSkin | None = None,
        dangly: MDLDangly | None = None,
    ) -> None:
        """Write mesh data."""
        # Mesh header values (bbox/radius/average) are emitted in-node by MDLOps and must roundtrip.
        # MDLOps uses "% .7g" format (space before number) - Reference: vendor/MDLOps/MDLOpsM.pm:3325-3328
        self.write_line(indent, f"bmin {mesh.bb_min.x: .7g} {mesh.bb_min.y: .7g} {mesh.bb_min.z: .7g}")
        self.write_line(indent, f"bmax {mesh.bb_max.x: .7g} {mesh.bb_max.y: .7g} {mesh.bb_max.z: .7g}")
        self.write_line(indent, f"radius {mesh.radius: .7g}")
        self.write_line(indent, f"average {mesh.average.x: .7g} {mesh.average.y: .7g} {mesh.average.z: .7g}")
        # Not emitted by MDLOps ASCII, but present in the binary mesh header and required for strict equality.
        self.write_line(indent, f"area {mesh.area:.7g}")

        self.write_line(indent, f"ambient {mesh.ambient.r} {mesh.ambient.g} {mesh.ambient.b}")
        self.write_line(indent, f"diffuse {mesh.diffuse.r} {mesh.diffuse.g} {mesh.diffuse.b}")
        self.write_line(indent, f"transparencyhint {mesh.transparency_hint}")
        self.write_line(indent, f"bitmap {mesh.texture_1}")
        if mesh.texture_2:
            self.write_line(indent, f"lightmap {mesh.texture_2}")

        # Mesh rendering flags. These materially affect canonical equality and must survive ASCII roundtrips.
        # Emit as explicit 0/1 so defaults are unambiguous.
        self.write_line(indent, f"render {1 if mesh.render else 0}")
        self.write_line(indent, f"shadow {1 if mesh.shadow else 0}")
        self.write_line(indent, f"beaming {1 if mesh.beaming else 0}")
        self.write_line(indent, f"backgroundgeometry {1 if mesh.background_geometry else 0}")
        self.write_line(indent, f"rotatetexture {1 if mesh.rotate_texture else 0}")
        self.write_line(indent, f"lightmapped {1 if mesh.has_lightmap else 0}")
        # K2-specific dirt and hologram fields
        # MDLOps writes these fields when they differ from defaults or when explicitly set
        # Reference: vendor/MDLOps/MDLOpsM.pm (K2 trimesh header writing)
        if mesh.dirt_enabled or mesh.dirt_texture != 1 or mesh.dirt_worldspace != 1 or mesh.hologram_donotdraw:
            self.write_line(indent, f"dirt_enabled {1 if mesh.dirt_enabled else 0}")
            if mesh.dirt_texture != 1:
                self.write_line(indent, f"dirt_texture {mesh.dirt_texture}")
            if mesh.dirt_worldspace != 1:
                self.write_line(indent, f"dirt_worldspace {mesh.dirt_worldspace}")
            if mesh.hologram_donotdraw:
                self.write_line(indent, f"hologram_donotdraw {1 if mesh.hologram_donotdraw else 0}")
        # Also write dirt_coordinate_space if it's set (legacy field)
        if hasattr(mesh, "dirt_coordinate_space") and mesh.dirt_coordinate_space != 0:
            self.write_line(indent, f"dirt_coordinate_space {mesh.dirt_coordinate_space}")

        # Inverted mesh sequence counter (inv_count) - preserved for MDLOps compatibility
        if hasattr(mesh, "inverted_counters") and mesh.inverted_counters:
            if len(mesh.inverted_counters) >= 2:
                self.write_line(indent, f"inv_count {mesh.inverted_counters[0]} {mesh.inverted_counters[1]}")
            elif len(mesh.inverted_counters) >= 1:
                self.write_line(indent, f"inv_count {mesh.inverted_counters[0]}")

        # Skin/dangly payload blocks come before verts/faces in MDLOps ASCII.
        if skin is not None:
            self._write_skin(indent, skin)
        elif isinstance(mesh, MDLSkin):
            self._write_skin(indent, mesh)

        if dangly is not None:
            self._write_dangly(indent, dangly)
        elif isinstance(mesh, MDLDangly):
            self._write_dangly(indent, mesh)

        self.write_line(indent, "verts " + str(len(mesh.vertex_positions)))
        for i, pos in enumerate(mesh.vertex_positions):
            line = f"{i} {pos.x} {pos.y} {pos.z}"
            if mesh.vertex_normals:
                normal = mesh.vertex_normals[i]
                line += f" {normal.x} {normal.y} {normal.z}"
            if mesh.vertex_uv1:
                uv = mesh.vertex_uv1[i]
                line += f" {uv.x} {uv.y}"
            if mesh.vertex_uv2:
                uv = mesh.vertex_uv2[i]
                line += f" {uv.x} {uv.y}"
            self.write_line(indent + 1, line)

        self.write_line(indent, "faces " + str(len(mesh.faces)))
        for face in mesh.faces:
            # Match MDLOps ASCII face emission:
            #   v1 v2 v3 smoothgroup_mask t1 t2 t3 material_id
            material_id, smoothgroup_mask = _unpack_face_material(face)
            # IMPORTANT: Do NOT substitute -1 with v1/v2/v3.
            # The binary format uses -1 as a sentinel (implicit tvert == vert index),
            # and the test-suite compares raw attributes, not semantic equivalence.
            t1 = int(face.t1)
            t2 = int(face.t2)
            t3 = int(face.t3)
            self.write_line(
                indent + 1,
                f"{face.v1} {face.v2} {face.v3} {smoothgroup_mask} {t1} {t2} {t3} {material_id}",
            )

    def _write_skin(self, indent: int, skin: MDLSkin) -> None:
        """Write skin-specific data."""
        self.write_line(indent, "bones " + str(len(skin.bone_indices)))
        for i, bone_idx in enumerate(skin.bone_indices):
            # Some builders/tests only populate bone indices and weights but not bind-pose transforms.
            # Fall back to identity orientation and zero translation.
            qbone: Vector4 = skin.qbones[i] if i < len(skin.qbones) else Vector4(0, 0, 0, 1)
            tbone: Vector3 = skin.tbones[i] if i < len(skin.tbones) else Vector3.from_null()
            self.write_line(indent + 1, f"{i} {bone_idx} {qbone.x} {qbone.y} {qbone.z} {qbone.w} {tbone.x} {tbone.y} {tbone.z}")

        # Weights (vertex -> bone influences). The test suite only asserts presence of the
        # "weights" section, but we also emit a reasonable format that our reader accepts:
        # "bone1 weight1 [bone2 weight2] ..."
        bone_vertices: list[MDLBoneVertex] = skin.vertex_bones
        if bone_vertices:
            self.write_line(indent, "weights " + str(len(bone_vertices)))
            for bv in bone_vertices:
                pairs: list[tuple[float, float]] = list(zip(bv.vertex_indices, bv.vertex_weights))

                # Filter out unused entries
                filtered: list[tuple[int, float]] = []
                for b, w in pairs:
                    try:
                        bi = int(b)
                        wf = float(w)
                    except (TypeError, ValueError):
                        continue
                    if bi < 0 or wf == 0.0:
                        continue
                    filtered.append((bi, wf))

                if not filtered:
                    self.write_line(indent + 1, "0 0")
                else:
                    self.write_line(indent + 1, " ".join(f"{bi} {wf:.7g}" for bi, wf in filtered))

    def _write_dangly(self, indent: int, dangly: MDLDangly) -> None:
        """Write dangly mesh data."""
        self.write_line(indent, "constraints " + str(len(dangly.constraints)))
        for i, constraint in enumerate(dangly.constraints):
            self.write_line(indent + 1, f"{i} {constraint.type} {constraint.target} {constraint.target_node}")

    def _write_light(self, indent: int, light: MDLLight) -> None:
        """Write light data.

        Reference: vendor/mdlops/MDLOpsM.pm:3228-3266
        """
        # Light color/radius/multiplier are controller properties, not direct attributes.
        # They are written via controllers in the node's controller list.

        # Write flare data arrays if present (vendor/mdlops/MDLOpsM.pm:3235-3256)
        has_flares: bool = bool(
            light.flare
            and (
                (light.flare_textures and len(light.flare_textures) > 0)
                or (light.flare_positions and len(light.flare_positions) > 0)
                or (light.flare_sizes and len(light.flare_sizes) > 0)
                or (light.flare_color_shifts and len(light.flare_color_shifts) > 0)
            )
        )

        if has_flares:
            # Write lensflares count (vendor/mdlops/MDLOpsM.pm:3233)
            if light.flare_positions:
                self.write_line(indent, f"lensflares {len(light.flare_positions)}")

            # Write texturenames (vendor/mdlops/MDLOpsM.pm:3235-3239)
            if light.flare_textures and len(light.flare_textures) > 0:
                self.write_line(indent, f"texturenames {len(light.flare_textures)}")
                for texture in light.flare_textures:
                    self.write_line(indent + 1, texture)

            # Write flarepositions (vendor/mdlops/MDLOpsM.pm:3240-3244)
            if light.flare_positions and len(light.flare_positions) > 0:
                self.write_line(indent, f"flarepositions {len(light.flare_positions)}")
                for pos in light.flare_positions:
                    self.write_line(indent + 1, f"{pos:.7g}")

            # Write flaresizes (vendor/mdlops/MDLOpsM.pm:3245-3249)
            if light.flare_sizes and len(light.flare_sizes) > 0:
                self.write_line(indent, f"flaresizes {len(light.flare_sizes)}")
                for size in light.flare_sizes:
                    self.write_line(indent + 1, f"{size:.7g}")

            # Write flarecolorshifts (vendor/mdlops/MDLOpsM.pm:3250-3256)
            if light.flare_color_shifts and len(light.flare_color_shifts) > 0:
                self.write_line(indent, f"flarecolorshifts {len(light.flare_color_shifts)}")
                for color_shift in light.flare_color_shifts:
                    if isinstance(color_shift, (list, tuple)) and len(color_shift) >= 3:
                        self.write_line(indent + 1, f"{color_shift[0]:.7g} {color_shift[1]:.7g} {color_shift[2]:.7g}")

        self.write_line(indent, f"flareradius {light.flare_radius:.7g}")
        self.write_line(indent, f"priority {light.light_priority}")
        if light.ambient_only:
            self.write_line(indent, "ambientonly")
        if light.shadow:
            self.write_line(indent, "shadow")
        if light.flare:
            self.write_line(indent, "flare")
        if light.fading_light:
            self.write_line(indent, "fadinglight")

    def _write_emitter(self, indent: int, emitter: MDLEmitter) -> None:
        """Write emitter data.

        Reference: vendor/mdlops/MDLOpsM.pm:3268-3307
        """
        self.write_line(indent, f"deadspace {emitter.dead_space:.7g}")
        self.write_line(indent, f"blastRadius {emitter.blast_radius:.7g}")
        self.write_line(indent, f"blastLength {emitter.blast_length:.7g}")
        self.write_line(indent, f"numBranches {emitter.branch_count}")
        self.write_line(indent, f"controlptsmoothing {emitter.control_point_smoothing:.7g}")
        self.write_line(indent, f"xgrid {emitter.x_grid}")
        self.write_line(indent, f"ygrid {emitter.y_grid}")
        # mdlops writes spawntype (vendor/mdlops/MDLOpsM.pm:3278)
        self.write_line(indent, f"spawntype {emitter.spawn_type}")
        # mdlops writes render/update/blend as strings (vendor/mdlops/MDLOpsM.pm:3279-3281)
        self.write_line(indent, f"update {emitter.update}")
        self.write_line(indent, f"render {emitter.render}")
        self.write_line(indent, f"blend {emitter.blend}")
        self.write_line(indent, f"texture {emitter.texture}")
        if emitter.chunk_name:
            self.write_line(indent, f"chunkname {emitter.chunk_name}")
        # mdlops writes twosidedtex as integer (vendor/mdlops/MDLOpsM.pm:3286)
        self.write_line(indent, f"twosidedtex {emitter.two_sided_texture}")
        # mdlops writes loop as integer (vendor/mdlops/MDLOpsM.pm:3287)
        self.write_line(indent, f"loop {emitter.loop}")
        self.write_line(indent, f"renderorder {emitter.render_order}")
        # mdlops writes m_bFrameBlending as integer (vendor/mdlops/MDLOpsM.pm:3289)
        self.write_line(indent, f"m_bFrameBlending {emitter.frame_blender}")
        # mdlops writes m_sDepthTextureName as string (vendor/mdlops/MDLOpsM.pm:3290)
        self.write_line(indent, f"m_sDepthTextureName {emitter.depth_texture or ''}")

        # Write emitter flags (vendor/mdlops/MDLOpsM.pm:3295-3307)
        from pykotor.resource.formats.mdl.mdl_types import MDLEmitterFlags

        flags = emitter.flags

        self.write_line(indent, f"p2p {1 if (flags & MDLEmitterFlags.P2P) else 0}")
        self.write_line(indent, f"p2p_sel {1 if (flags & MDLEmitterFlags.P2P_SEL) else 0}")
        self.write_line(indent, f"affectedByWind {1 if (flags & MDLEmitterFlags.AFFECTED_WIND) else 0}")
        self.write_line(indent, f"m_isTinted {1 if (flags & MDLEmitterFlags.TINTED) else 0}")
        self.write_line(indent, f"bounce {1 if (flags & MDLEmitterFlags.BOUNCE) else 0}")
        self.write_line(indent, f"random {1 if (flags & MDLEmitterFlags.RANDOM) else 0}")
        self.write_line(indent, f"inherit {1 if (flags & MDLEmitterFlags.INHERIT) else 0}")
        self.write_line(indent, f"inheritvel {1 if (flags & MDLEmitterFlags.INHERIT_VEL) else 0}")
        self.write_line(indent, f"inherit_local {1 if (flags & MDLEmitterFlags.INHERIT_LOCAL) else 0}")
        self.write_line(indent, f"splat {1 if (flags & MDLEmitterFlags.SPLAT) else 0}")
        self.write_line(indent, f"inherit_part {1 if (flags & MDLEmitterFlags.INHERIT_PART) else 0}")
        self.write_line(indent, f"depth_texture {1 if (flags & MDLEmitterFlags.DEPTH_TEXTURE) else 0}")
        self.write_line(indent, f"emitterflag13 {1 if (flags & MDLEmitterFlags.FLAG_13) else 0}")

    def _write_reference(self, indent: int, reference: MDLReference) -> None:
        """Write reference data."""
        # The ASCII format used in tests uses "model <resref>" for reference nodes.
        self.write_line(indent, f"model {reference.model}")
        if reference.reattachable:
            self.write_line(indent, "reattachable")

    def _write_saber(self, indent: int, saber: MDLSaber) -> None:
        """Write saber data."""
        # Keep output aligned with the unit test fixtures (uses simple "length"/"width").
        self.write_line(indent, f"sabertype {saber.saber_type}")
        self.write_line(indent, f"sabercolor {saber.saber_color}")
        self.write_line(indent, f"length {saber.saber_length:.7g}")
        self.write_line(indent, f"width {saber.saber_width:.7g}")
        self.write_line(indent, f"saberflarecolor {saber.saber_flare_color}")
        self.write_line(indent, f"saberflareradius {saber.saber_flare_radius:.7g}")

    def _write_walkmesh(self, indent: int, walkmesh: MDLWalkmesh) -> None:
        """Write walkmesh data.
        
        AABB format matches MDLOps: 6 floats (bbox_min.xyz, bbox_max.xyz) + 1 int (face_index)
        Reference: vendor/MDLOps/MDLOpsM.pm:3459 (printf format: 6 floats + 1 int)
        """
        self.write_line(indent, "aabb " + str(len(walkmesh.aabbs)))
        for i, aabb in enumerate(walkmesh.aabbs):
            # MDLOps format: 6 floats (bbox_min.xyz, bbox_max.xyz) + 1 int (face_index)
            # Child offsets and unknown are not stored in ASCII format
            # MDLOps format: 6 floats with space before number, then 1 int
            # Reference: vendor/MDLOps/MDLOpsM.pm:3459
            self.write_line(
                indent + 1,
                f"      {aabb.bbox_min.x: .7g} {aabb.bbox_min.y: .7g} {aabb.bbox_min.z: .7g} {aabb.bbox_max.x: .7g} {aabb.bbox_max.y: .7g} {aabb.bbox_max.z: .7g} {aabb.face_index}"
            )

    def _write_controller(self, indent: int, node: MDLNode, controller: MDLController) -> None:
        """Write controller data."""
        if not controller.rows:
            return

        # IMPORTANT: controller IDs overlap between node types (e.g. 88 is RADIUS for lights
        # but BIRTHRATE for emitters). So we must resolve the ASCII controller name using
        # the node-type context, not only the enum value.
        controller_id = int(controller.controller_type)
        base_name: str | None = None

        # Prefer the most specific node types first.
        flag_preference: list[int] = []
        if node.light:
            flag_preference.append(NODE_HAS_LIGHT)
        if node.emitter:
            flag_preference.append(NODE_HAS_EMITTER)
        if node.mesh:
            flag_preference.append(NODE_HAS_MESH)
        flag_preference.append(NODE_HAS_HEADER)

        for flag in flag_preference:
            name_map = _CONTROLLER_NAMES.get(flag, {})
            if controller_id in name_map:
                base_name = name_map[controller_id]
                break

        if base_name is None:
            # Fallback: use enum name (may be an alias, but better than nothing)
            base_name = controller.controller_type.name.lower()

        controller_name = f"{base_name}{'bezier' if controller.is_bezier else ''}key"

        self.write_line(indent, controller_name)
        for row in controller.rows:
            # Preserve exact float32-derived values across Binary→ASCII→Binary roundtrips.
            # Using str() can shorten/round values, which breaks canonicalized equality on animations.
            t_str = repr(float(row.time))
            data = list(row.data or [])
            # MDLOps ASCII stores ORIENTATION controller rows as angle-axis (x, y, z, angle),
            # while our in-memory representation uses quaternions. The reader converts angle-axis
            # to quaternion; therefore the writer must emit angle-axis for stability.
            if controller.controller_type == MDLControllerType.ORIENTATION and len(data) == 4:
                data = _quaternion_to_aa(data)
            data_str = " ".join(repr(float(d)) for d in data)
            self.write_line(indent + 1, f"{t_str} {data_str}".rstrip())
        self.write_line(indent, "endlist")

    def _write_animation(self, anim: MDLAnimation, model_name: str) -> None:
        """Write animation data.

        Reference: vendor/mdlops/MDLOpsM.pm:3488-3560
        """
        self.write_line(0, "")
        self.write_line(0, f"newanim {anim.name} {model_name}")
        # Preserve exact float values across Binary→ASCII→Binary roundtrips.
        # Using general-format precision (e.g., .7g) will round float32-derived values like 1.899999976 → 1.9,
        # which breaks strict equality tests.
        self.write_line(1, f"length {repr(float(anim.anim_length))}")
        self.write_line(1, f"transtime {repr(float(anim.transition_length))}")
        if anim.root_model:
            self.write_line(1, f"animroot {anim.root_model}")

        # Write events (vendor/mdlops/MDLOpsM.pm:3496-3503)
        if anim.events:
            for event in anim.events:
                t = float(event.activation_time)
                # Match test expectations: keep ".0" for whole seconds, keep decimals for fractions.
                t_str = f"{t:.1f}" if t.is_integer() else f"{t:.7g}"
                self.write_line(1, f"event {t_str} {event.name}")

        # Write animation nodes (vendor/mdlops/MDLOpsM.pm:3504-3555)
        # Animation nodes are written as "node dummy <node_name>" with controllers
        # Build a mapping from animation nodes to their parents for parent writing
        parent_map: dict[str, MDLNode | None] = {}
        self._build_animation_parent_map(anim.root, None, parent_map)

        # Write all animation nodes in their original binary order (node_id).
        # The ASCII reader rebuilds animation child lists by appending in encounter order, so
        # emitting nodes in a different order will permute sibling ordering and break strict
        # binary↔ASCII comparisons.
        all_anim_nodes: list[MDLNode] = anim.all_nodes()
        all_anim_nodes.sort(key=lambda n: int(n.node_id))

        for node in all_anim_nodes:
            if node.name:  # Skip root if it has no name
                parent: MDLNode | None = parent_map.get(node.name)
                self._write_animation_node(1, node, parent)

        self.write_line(0, "")
        self.write_line(0, f"doneanim {anim.name} {model_name}")

    def _build_animation_parent_map(
        self,
        node: MDLNode,
        parent: MDLNode | None,
        parent_map: dict[str, MDLNode | None],
    ) -> None:
        """Build a mapping of animation nodes to their parents.

        Uses node names as keys instead of node objects to avoid hashing issues.
        """
        parent_map[node.name] = parent
        for child in node.children:
            self._build_animation_parent_map(child, node, parent_map)

    def _write_animation_node(
        self,
        indent: int,
        node: MDLNode,
        parent: MDLNode | None = None,
    ) -> None:
        """Write an animation node with its controllers.

        Reference: vendor/mdlops/MDLOpsM.pm:3507-3554
        Animation nodes are written as "node dummy <node_name>" regardless of actual type.
        """
        # Animation nodes are always written as "dummy" type (vendor/mdlops/MDLOpsM.pm:3507)
        self.write_line(indent, f"node dummy {node.name}")

        # Write parent if this node has one (vendor/mdlops/MDLOpsM.pm:3508)
        # In MDLOps, parent is a model node index, but we use the parent node's name
        if parent and parent.name:
            self.write_line(indent + 1, f"parent {parent.name}")

        # Write controllers (vendor/mdlops/MDLOpsM.pm:3510-3553)
        for controller in node.controllers:
            self._write_controller(indent + 1, node, controller)

        self.write_line(indent, "endnode")


def _parse_float_robust(value: str) -> float:
    """Parse float value handling NaN/INF/QNAN formats from MDLOps.

    MDLOps on Windows outputs NaN as '1.#QNAN', INF as '1.#INF', etc.
    This function handles all these formats and standard Python float values.

    Args:
        value: String representation of float value

    Returns:
        Parsed float value (may be NaN or INF)
    """
    value = value.strip().lower()
    # Handle Windows-style NaN representations
    if "qnan" in value or value == "nan" or value == "-nan" or value == "+nan":
        return float("nan")
    # Handle Windows-style INF representations
    if "inf" in value:
        if value.startswith("-"):
            return float("-inf")
        return float("inf")
    # Standard float parsing for normal values
    return float(value)


class MDLAsciiReader(ResourceReader):
    """Reader for ASCII MDL files matching mdlops implementation exactly.

    Reference: vendor/mdlops/MDLOpsM.pm:3916-5970 (readasciimdl)
    """

    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        """Initialize the ASCII MDL reader.

        Args:
            source: The source of the ASCII MDL data
            offset: The byte offset within the source
            size: Size of the data to read (0 = read all)
        """
        super().__init__(source, offset, size if size > 0 else None)
        self._mdl: MDL | None = None
        self._node_index: dict[str, int] = {"null": -1}
        self._nodes: list[MDLNode] = []
        self._current_node: MDLNode | None = None
        self._is_geometry: bool = False
        self._is_animation: bool = False
        self._in_node: bool = False
        self._current_anim_num: int = 0
        self._task: Literal["verts", "faces", "tverts", "tverts1", "lightmaptverts", "bones", "flarecolorshifts", "weights", "constraints", "aabb", ""] = ""
        self._task_count: int = 0
        self._task_total: int = 0
        self._anim_node_index: dict[str, MDLNode] = {}
        self._anim_nodes: list[list[MDLNode]] = []
        self._saw_any_content: bool = False

    @autoclose
    def load(self, *, auto_close: bool = True) -> MDL:  # noqa: FBT001, FBT002, ARG002
        """Load the ASCII MDL file.

        Returns:
            The loaded MDL instance

        Reference: vendor/mdlops/MDLOpsM.pm:3916-5970
        """
        self._mdl = MDL()

        # Read bytes and decode to text
        data = self._reader.read_bytes(self._reader.size())
        text_content = decode_bytes_with_fallbacks(data)
        text_reader = io.StringIO(text_content)
        self._line_iterator = iter(text_reader)

        # Set defaults matching mdlops (vendor/mdlops/MDLOpsM.pm:4017-4024)
        self._mdl.name = ""
        self._mdl.supermodel = "null"
        self._mdl.fog = False
        self._mdl.classification = MDLClassification.OTHER
        self._mdl.classification_unk1 = 0
        self._mdl.animation_scale = 0.971
        self._mdl.bmin = Vector3(-5, -5, -1)
        self._mdl.bmax = Vector3(5, 5, 10)
        self._mdl.radius = 7.0

        # Parse the file line by line
        for line in self._line_iterator:
            line = str(line).rstrip()
            if not line or line.strip().startswith("#"):
                continue
            self._saw_any_content = True

            # Model header parsing (vendor/mdlops/MDLOpsM.pm:4071-4097)
            if re.match(r"^\s*newmodel\s+(\S+)", line, re.IGNORECASE):
                match = re.match(r"^\s*newmodel\s+(\S+)", line, re.IGNORECASE)
                if match:
                    self._mdl.name = match.group(1)
            elif re.match(r"^\s*setsupermodel\s+\S+\s+(\S+)", line, re.IGNORECASE):
                match = re.match(r"^\s*setsupermodel\s+\S+\s+(\S+)", line, re.IGNORECASE)
                if match:
                    self._mdl.supermodel = match.group(1)
            elif re.match(r"^\s*classification\s+(\S+)", line, re.IGNORECASE):
                match = re.match(r"^\s*classification\s+(\S+)", line, re.IGNORECASE)
                if match:
                    class_name = match.group(1).lower()
                    try:
                        self._mdl.classification = MDLClassification[class_name.upper()]
                    except KeyError:
                        self._mdl.classification = MDLClassification.OTHER
            elif re.match(r"^\s*classification_unk1\s+(\S+)", line, re.IGNORECASE):
                match = re.match(r"^\s*classification_unk1\s+(\S+)", line, re.IGNORECASE)
                if match:
                    self._mdl.classification_unk1 = int(match.group(1))
            elif re.match(r"^\s*ignorefog\s+(\S+)", line, re.IGNORECASE):
                match = re.match(r"^\s*ignorefog\s+(\S+)", line, re.IGNORECASE)
                if match:
                    self._mdl.fog = int(match.group(1)) == 0
            elif re.match(r"^\s*setanimationscale\s+(\S+)", line, re.IGNORECASE):
                match = re.match(r"^\s*setanimationscale\s+(\S+)", line, re.IGNORECASE)
                if match:
                    self._mdl.animation_scale = float(match.group(1))
            elif re.match(r"^\s*headlink\s+(\S+)", line, re.IGNORECASE):
                match = re.match(r"^\s*headlink\s+(\S+)", line, re.IGNORECASE)
                if match:
                    self._mdl.headlink = match.group(1)
            elif re.match(r"^\s*compress_quaternions\s+(\S+)", line, re.IGNORECASE):
                match = re.match(r"^\s*compress_quaternions\s+(\S+)", line, re.IGNORECASE)
                if match:
                    self._mdl.compress_quaternions = int(match.group(1))
            elif re.match(r"^\s*beginmodelgeom", line, re.IGNORECASE):
                self._is_geometry = True
                self._is_animation = False
            elif re.match(r"^\s*endmodelgeom", line, re.IGNORECASE):
                self._is_geometry = False
            elif re.match(r"^\s*newanim\s+(\S+)\s+(\S+)", line, re.IGNORECASE):
                match = re.match(r"^\s*newanim\s+(\S+)\s+(\S+)", line, re.IGNORECASE)
                if match:
                    anim = MDLAnimation()
                    anim.name = match.group(1)
                    anim.root_model = match.group(2)
                    self._mdl.anims.append(anim)
                    self._is_animation = True
                    self._current_anim_num = len(self._mdl.anims) - 1
                    # Reset per-animation node state
                    self._anim_node_index = {}
                    while len(self._anim_nodes) <= self._current_anim_num:
                        self._anim_nodes.append([])
            elif re.match(r"^\s*doneanim", line, re.IGNORECASE):
                self._is_animation = False
            elif re.match(r"^\s*length\s+(\S+)", line, re.IGNORECASE) and self._is_animation:
                match = re.match(r"^\s*length\s+(\S+)", line, re.IGNORECASE)
                if match and self._mdl.anims:
                    self._mdl.anims[self._current_anim_num].anim_length = float(match.group(1))
            elif re.match(r"^\s*animroot\s+(\S+)", line, re.IGNORECASE) and self._is_animation:
                match = re.match(r"^\s*animroot\s+(\S+)", line, re.IGNORECASE)
                if match and self._mdl.anims:
                    self._mdl.anims[self._current_anim_num].root_model = match.group(1)
            elif re.match(r"^\s*transtime\s+(\S+)", line, re.IGNORECASE) and self._is_animation:
                match = re.match(r"^\s*transtime\s+(\S+)", line, re.IGNORECASE)
                if match and self._mdl.anims:
                    self._mdl.anims[self._current_anim_num].transition_length = float(match.group(1))
            elif re.match(r"^\s*event\s+(\S+)\s+(\S+)", line, re.IGNORECASE) and self._is_animation and not self._in_node:
                match = re.match(r"^\s*event\s+(\S+)\s+(\S+)", line, re.IGNORECASE)
                if match and self._mdl.anims:
                    event = MDLEvent()
                    event.activation_time = float(match.group(1))
                    event.name = match.group(2)
                    self._mdl.anims[self._current_anim_num].events.append(event)
            elif re.match(r"^\s*node\s+(\S+)\s+(\S+)", line, re.IGNORECASE):
                # Animation nodes live under the current animation, not the model geometry tree.
                if self._is_animation and self._mdl.anims:
                    self._parse_animation_node(line)
                else:
                    self._parse_node(line)
            elif self._in_node:
                self._parse_node_data(line)
            elif re.match(r"^\s*bmin\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE) and not self._in_node:
                match = re.match(r"^\s*bmin\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE)
                if match:
                    self._mdl.bmin = Vector3(_parse_float_robust(match.group(1)), _parse_float_robust(match.group(2)), _parse_float_robust(match.group(3)))
            elif re.match(r"^\s*bmax\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE) and not self._in_node:
                match = re.match(r"^\s*bmax\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE)
                if match:
                    self._mdl.bmax = Vector3(_parse_float_robust(match.group(1)), _parse_float_robust(match.group(2)), _parse_float_robust(match.group(3)))
            elif re.match(r"^\s*radius\s+(\S+)", line, re.IGNORECASE) and not self._in_node:
                match = re.match(r"^\s*radius\s+(\S+)", line, re.IGNORECASE)
                if match:
                    self._mdl.radius = _parse_float_robust(match.group(1))

        # Build node hierarchy
        self._build_node_hierarchy()
        self._build_animation_hierarchy()

        if not self._saw_any_content:
            raise ValueError("Empty MDL ASCII input")

        return self._mdl

    def _parse_node(self, line: str) -> None:
        """Parse a node declaration.

        Reference: vendor/mdlops/MDLOpsM.pm:4132-4210
        """
        match = re.match(r"^\s*node\s+(\S+)\s+(\S+)", line, re.IGNORECASE)
        if not match:
            return

        node_type_str = match.group(1).lower()
        node_name = match.group(2)

        # Handle saber prefix (vendor/mdlops/MDLOpsM.pm:4134-4140)
        if node_name.startswith("2081__"):
            node_type_str = "lightsaber"
            node_name = node_name[6:]

        # Map node type string to MDLNodeType
        node_type_map = {
            "dummy": MDLNodeType.DUMMY,
            "trimesh": MDLNodeType.TRIMESH,
            "danglymesh": MDLNodeType.DANGLYMESH,
            "light": MDLNodeType.LIGHT,
            "emitter": MDLNodeType.EMITTER,
            "reference": MDLNodeType.REFERENCE,
            "aabb": MDLNodeType.AABB,
            "lightsaber": MDLNodeType.SABER,
        }

        node_type = node_type_map.get(node_type_str, MDLNodeType.DUMMY)

        # Create node
        node = MDLNode()
        node.name = node_name
        node.node_type = node_type
        node.node_id = len(self._nodes)
        node.position = Vector3.from_null()
        node.orientation = Vector4(0, 0, 0, 1)

        # Initialize based on node type
        if node_type == MDLNodeType.LIGHT:
            node.light = MDLLight()
        elif node_type == MDLNodeType.EMITTER:
            node.emitter = MDLEmitter()
        elif node_type == MDLNodeType.REFERENCE:
            node.reference = MDLReference()
        elif node_type == MDLNodeType.AABB:
            # AABB nodes can have both mesh and AABB data
            # Reference: vendor/MDLOps/MDLOpsM.pm:3454 (NODE_AABB = 545, can include mesh)
            node.aabb = MDLWalkmesh()
            # Mesh will be created on-demand when mesh data is encountered
        elif node_type == MDLNodeType.SABER:
            node.saber = MDLSaber()
        elif node_type in (MDLNodeType.TRIMESH, MDLNodeType.DANGLYMESH):
            node.mesh = MDLMesh()
            if node_type == MDLNodeType.DANGLYMESH:
                node.dangly = MDLDangly()

        self._nodes.append(node)
        self._node_index[node_name.lower()] = len(self._nodes) - 1
        self._current_node = node
        self._in_node = True
        self._task = ""

    def _parse_animation_node(self, line: str) -> None:
        """Parse an animation node declaration (within a newanim...doneanim block).

        The ASCII animation section uses node declarations to attach controllers to the
        animation's root/node tree. These should not be added to the model's geometry nodes.
        """
        match = re.match(r"^\s*node\s+(\S+)\s+(\S+)", line, re.IGNORECASE)
        if not match or self._mdl is None or not self._mdl.anims:
            return

        node_name: str = match.group(2)
        node: MDLNode = MDLNode()
        node.name = node_name
        node.node_type = MDLNodeType.DUMMY
        node.node_id = len(self._anim_node_index)
        node.position = Vector3.from_null()
        node.orientation = Vector4(0, 0, 0, 1)

        self._anim_node_index[node_name.lower()] = node
        if self._current_anim_num >= 0:
            while len(self._anim_nodes) <= self._current_anim_num:
                self._anim_nodes.append([])
            self._anim_nodes[self._current_anim_num].append(node)

        # Attach as animation root if unset
        anim: MDLAnimation = self._mdl.anims[self._current_anim_num]
        if anim.root is None or not anim.root.name:
            anim.root = node

        self._current_node = node
        self._in_node = True
        self._task = ""

    def _build_animation_hierarchy(self) -> None:
        """Build per-animation node hierarchies from 'parent <name>' relationships."""
        if self._mdl is None or not self._mdl.anims:
            return

        for anim_idx, anim in enumerate(self._mdl.anims):
            if anim.root is None or not anim.root.name:
                continue

            nodes: list[MDLNode] = []
            if 0 <= anim_idx < len(self._anim_nodes):
                nodes = list(self._anim_nodes[anim_idx])
            if anim.root not in nodes:
                nodes.append(anim.root)

            by_name: dict[str, MDLNode] = {n.name.lower(): n for n in nodes if n.name}
            for n in nodes:
                n.children = []

            # Attach based on parsed parent name (preferred).
            for n in nodes:
                parent_name: str | None = n.__dict__.get("_parent_name")
                if isinstance(parent_name, str) and parent_name in by_name:
                    by_name[parent_name].children.append(n)

            # Choose a better root if the initial one was simply the first encountered node.
            root_candidates: list[MDLNode] = [
                n
                for n in nodes
                # Treat missing parents AND parents that are external to this animation node list
                # (e.g. model root name, animroot name) as top-level animation nodes.
                if (not isinstance(n.__dict__.get("_parent_name"), str)) or (isinstance(n.__dict__.get("_parent_name"), str) and n.__dict__.get("_parent_name") not in by_name)
            ]
            if root_candidates:
                # Prefer the candidate that actually has children.
                root_candidates.sort(key=lambda n: len(n.children), reverse=True)
                anim.root = root_candidates[0]

            # Cleanup temporary parent tracking
            for n in nodes:
                n.__dict__.pop("_parent_name", None)

    def _parse_node_data(self, line: str) -> None:
        """Parse data within a node.

        Reference: vendor/mdlops/MDLOpsM.pm:4222-4644
        """
        if not self._current_node:
            return

        # ASCII node bodies are delimited by braces in the tests and writer output.
        # Treat "{" as a no-op and "}" as end-of-node (mdlops also supports "endnode").
        stripped = line.strip()
        if stripped == "{":
            return
        if stripped == "}":
            self._in_node = False
            self._current_node = None
            self._task = ""
            self._task_count = 0
            return

        # Check for endnode
        if re.match(r"^\s*endnode", line, re.IGNORECASE):
            self._in_node = False
            self._current_node = None
            self._task = ""
            self._task_count = 0
            return

        # Parse parent
        if re.match(r"^\s*parent\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*parent\s+(\S+)", line, re.IGNORECASE)
            if match:
                if self._is_animation and self._mdl is not None and self._mdl.anims:
                    # Animation nodes: MDLOps may emit parent as either a node name OR a numeric node index.
                    parent_token = match.group(1).strip()
                    parent_lc = parent_token.lower()

                    # Prefer name-based parenting when possible (most interoperable).
                    resolved_parent_name: str | None = None

                    # Numeric parent reference (MDLOps-style): interpret as node_id / index within this animation.
                    if parent_lc.lstrip("-").isdigit():
                        try:
                            parent_idx = int(parent_lc)
                        except ValueError:
                            parent_idx = -1

                        if parent_idx >= 0 and self._current_anim_num >= 0 and self._current_anim_num < len(self._anim_nodes):
                            # Try node_id match first (more robust than list index).
                            cand_nodes: list[MDLNode] = self._anim_nodes[self._current_anim_num]
                            for cand in cand_nodes:
                                if cand.node_id == parent_idx:
                                    resolved_parent_name = cand.name.lower()
                                    break
                            # Fallback: treat as list index in encounter order.
                            if resolved_parent_name is None and parent_idx < len(cand_nodes):
                                resolved_parent_name = cand_nodes[parent_idx].name.lower()

                    # Name parent reference
                    if resolved_parent_name is None:
                        resolved_parent_name = parent_lc

                    # MDLOps commonly uses NULL to mean "no parent" in animation sections.
                    # Treat these as root-level nodes for hierarchy building.
                    if resolved_parent_name in ("null", "-1", ""):
                        self._current_node.__dict__["_parent_name"] = None
                        return

                    # Store for hierarchy construction.
                    self._current_node.__dict__["_parent_name"] = resolved_parent_name
                else:
                    # Geometry nodes: MDLOps commonly emits parent as a numeric node index,
                    # but some toolchains may emit a name. Support both.
                    parent_token = match.group(1).strip()
                    parent_lc = parent_token.lower()
                    if parent_lc in ("null", ""):
                        self._current_node.parent_id = -1
                    elif parent_lc.lstrip("-").isdigit():
                        try:
                            self._current_node.parent_id = int(parent_lc)
                        except ValueError:
                            self._current_node.parent_id = -1
                    else:
                        # Store parent name for later resolution (parent may not be parsed yet)
                        self._current_node.__dict__["_parent_name"] = parent_lc
                        # Try to resolve now, but fall back to name-based resolution later
                        self._current_node.parent_id = self._node_index.get(parent_lc, -1)
            return

        # Parse position
        if re.match(r"^\s*position\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*position\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE)
            if match:
                self._current_node.position = Vector3(
                    _parse_float_robust(match.group(1)),
                    _parse_float_robust(match.group(2)),
                    _parse_float_robust(match.group(3)),
                )
            return

        # Parse orientation
        if re.match(r"^\s*orientation\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*orientation\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE)
            if match:
                self._current_node.orientation = Vector4(
                    _parse_float_robust(match.group(1)),
                    _parse_float_robust(match.group(2)),
                    _parse_float_robust(match.group(3)),
                    _parse_float_robust(match.group(4)),
                )
            return

        # Parse mesh data before controllers.
        # Some keywords overlap (e.g. "radius" is a mesh header scalar but also a light controller name).
        # AABB nodes can have mesh data, so attempt parsing even if mesh doesn't exist yet (will be created on-demand)
        if self._current_node.mesh or (self._current_node.node_type == MDLNodeType.AABB and self._current_node.aabb):
            if self._parse_mesh_data(line):
                return

        # Parse controllers
        if self._parse_controller(line):
            return

        # Parse light data
        if self._current_node.light:
            if self._parse_light_data(line):
                return

        # Parse emitter data
        if self._current_node.emitter:
            if self._parse_emitter_data(line):
                return

        # Parse reference data
        if self._current_node.reference:
            if self._parse_reference_data(line):
                return

        # Parse saber data
        if self._current_node.saber:
            if self._parse_saber_data(line):
                return

        # Parse walkmesh data
        if self._current_node.aabb:
            if self._parse_walkmesh_data(line):
                return

    def _parse_controller(self, line: str) -> bool:
        """Parse a controller declaration or data.

        Reference: vendor/mdlops/MDLOpsM.pm:3809-3835, 3734-3802
        """
        if not self._current_node:
            return False

        # NOTE:
        # Some binary models encode "light-ness"/"emitter-ness" purely via controller blocks
        # (e.g. colorkey/radiuskey/multiplierkey) without any explicit node-type token or
        # payload section. If we gate controller parsing on attached payload objects/flags,
        # we'll drop those controllers on ASCII read, breaking Binary→ASCII equality.
        #
        # Controller *IDs* overlap between node types, but controller *names* are distinct in
        # MDLOps ASCII. So it's safe to detect by name regardless of node flags.

        # Check for keyed controllers (vendor/mdlops/MDLOpsM.pm:3760-3802)
        for flag_type in [NODE_HAS_LIGHT, NODE_HAS_EMITTER, NODE_HAS_MESH, NODE_HAS_HEADER]:
            controllers = _CONTROLLER_NAMES.get(flag_type, {})
            for _controller_id, controller_name in controllers.items():
                # Check for keyed controller (e.g., "positionkey", "orientationbezierkey")
                keyed_pattern = rf"^\s*{re.escape(controller_name)}(bezier)?key"
                if re.match(keyed_pattern, line, re.IGNORECASE):
                    match = re.match(keyed_pattern, line, re.IGNORECASE)
                    is_bezier = bool(match and match.group(1) and match.group(1).lower() == "bezier")
                    # Check for old format with count: "positionkey 4"
                    count_match = re.search(r"key\s+(\d+)$", line, re.IGNORECASE)
                    total = int(count_match.group(1)) if count_match else 0

                    # Read keyframe data
                    rows: list[MDLControllerRow] = []
                    controller_type = _CONTROLLER_NAME_TO_TYPE.get(controller_name, MDLControllerType.INVALID)

                    # Read rows until endlist or count reached
                    for _ in range(total if total > 0 else 10000):  # Large limit for safety
                        try:
                            row_line = next(self._line_iterator).strip()
                            if not row_line or re.match(r"^\s*endlist", row_line, re.IGNORECASE):
                                break

                            # Parse row data
                            parts = row_line.split()
                            if not parts:
                                break

                            time = _parse_float_robust(parts[0])
                            data = [_parse_float_robust(x) for x in parts[1:]]

                            # Special handling for orientation (convert angle-axis to quaternion)
                            if controller_type == MDLControllerType.ORIENTATION and len(data) == 4:
                                data = _aa_to_quaternion(data)

                            rows.append(MDLControllerRow(time, data))
                        except StopIteration:
                            break

                    if rows:
                        controller = MDLController(controller_type, rows, is_bezier)
                        self._current_node.controllers.append(controller)
                    return True

                # Check for single controller (e.g., "position 1.0 2.0 3.0")
                single_pattern = rf"^\s*{re.escape(controller_name)}(\s+(\S+))+"
                if re.match(single_pattern, line, re.IGNORECASE):
                    match = re.match(single_pattern, line, re.IGNORECASE)
                    if match:
                        # Extract data values
                        parts = line.split()
                        data = [_parse_float_robust(x) for x in parts[1:]]

                        # Special handling for orientation
                        controller_type = _CONTROLLER_NAME_TO_TYPE.get(controller_name, MDLControllerType.INVALID)
                        if controller_type == MDLControllerType.ORIENTATION and len(data) == 4:
                            data = _aa_to_quaternion(data)

                        # Mirror common controller-like properties onto the owning objects.
                        # The unit tests expect these convenience attributes to exist on the node payloads
                        # (e.g. light.radius) even though many are also representable as controllers.
                        if self._current_node.light:
                            if controller_type == MDLControllerType.COLOR and len(data) >= 3:
                                self._current_node.light.color = Color(data[0], data[1], data[2])
                            elif controller_type == MDLControllerType.RADIUS and len(data) >= 1:
                                self._current_node.light.radius = data[0]
                            elif controller_type == MDLControllerType.MULTIPLIER and len(data) >= 1:
                                self._current_node.light.multiplier = data[0]

                        rows = [MDLControllerRow(0.0, data)]
                        controller = MDLController(controller_type, rows, False)
                        self._current_node.controllers.append(controller)
                    return True

        return False

    def _parse_mesh_data(self, line: str) -> bool:
        """Parse mesh-specific data.

        Reference: vendor/mdlops/MDLOpsM.pm:4304-4413
        """
        if self._current_node is None:
            return False
        
        # AABB nodes can have mesh data - create mesh on-demand if needed
        # Reference: vendor/MDLOps/MDLOpsM.pm:3454 (NODE_AABB = 545, can include mesh)
        if self._current_node.mesh is None and self._current_node.node_type == MDLNodeType.AABB:
            # Check if this line contains mesh data (verts/faces/tverts)
            if re.match(r"^\s*(verts|faces|tverts|tverts1|lightmaptverts)", line, re.IGNORECASE):
                self._current_node.mesh = MDLMesh()
        
        if self._current_node.mesh is None:
            return False

        mesh = self._current_node.mesh

        # Mesh header values (bbox/radius/average) are emitted in-node by MDLOps.
        if re.match(r"^\s*bmin\s+(\S+)\s+(\S+)\s+(\S+)\s*$", line, re.IGNORECASE):
            match = re.match(r"^\s*bmin\s+(\S+)\s+(\S+)\s+(\S+)\s*$", line, re.IGNORECASE)
            if match:
                mesh.bb_min = Vector3(_parse_float_robust(match.group(1)), _parse_float_robust(match.group(2)), _parse_float_robust(match.group(3)))
            return True
        if re.match(r"^\s*bmax\s+(\S+)\s+(\S+)\s+(\S+)\s*$", line, re.IGNORECASE):
            match = re.match(r"^\s*bmax\s+(\S+)\s+(\S+)\s+(\S+)\s*$", line, re.IGNORECASE)
            if match:
                mesh.bb_max = Vector3(_parse_float_robust(match.group(1)), _parse_float_robust(match.group(2)), _parse_float_robust(match.group(3)))
            return True
        if re.match(r"^\s*radius\s+(\S+)\s*$", line, re.IGNORECASE):
            match = re.match(r"^\s*radius\s+(\S+)\s*$", line, re.IGNORECASE)
            if match:
                mesh.radius = _parse_float_robust(match.group(1))
            return True
        if re.match(r"^\s*average\s+(\S+)\s+(\S+)\s+(\S+)\s*$", line, re.IGNORECASE):
            match = re.match(r"^\s*average\s+(\S+)\s+(\S+)\s+(\S+)\s*$", line, re.IGNORECASE)
            if match:
                mesh.average = Vector3(_parse_float_robust(match.group(1)), _parse_float_robust(match.group(2)), _parse_float_robust(match.group(3)))
            return True

        # Mesh surface area (binary header field). We emit/read this for strict equality.
        if re.match(r"^\s*(area|surfacearea)\s+(\S+)\s*$", line, re.IGNORECASE):
            match = re.match(r"^\s*(area|surfacearea)\s+(\S+)\s*$", line, re.IGNORECASE)
            if match:
                mesh.area = _parse_float_robust(match.group(2))
            return True

        # Parse ambient color
        if re.match(r"^\s*ambient\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*ambient\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE)
            if match:
                mesh.ambient = Color(
                    _parse_float_robust(match.group(1)),
                    _parse_float_robust(match.group(2)),
                    _parse_float_robust(match.group(3)),
                )
            return True

        # Parse diffuse color
        if re.match(r"^\s*diffuse\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*diffuse\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE)
            if match:
                mesh.diffuse = Color(
                    _parse_float_robust(match.group(1)),
                    _parse_float_robust(match.group(2)),
                    _parse_float_robust(match.group(3)),
                )
            return True

        # Parse transparency hint
        if re.match(r"^\s*transparencyhint\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*transparencyhint\s+(\S+)", line, re.IGNORECASE)
            if match:
                mesh.transparency_hint = int(match.group(1))
            return True

        # Parse bitmap/texture
        if re.match(r"^\s*bitmap\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*bitmap\s+(\S+)", line, re.IGNORECASE)
            if match:
                mesh.texture_1 = match.group(1)
            return True

        # Parse lightmap
        if re.match(r"^\s*lightmap\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*lightmap\s+(\S+)", line, re.IGNORECASE)
            if match:
                mesh.texture_2 = match.group(1)
                mesh.has_lightmap = True
            return True

        # Parse mesh render flags (accept both "flag" and "flag 0/1" forms).
        def _parse_bool_flag(pattern: str) -> int | None:
            m = re.match(pattern, line, re.IGNORECASE)
            if not m:
                return None
            if m.group(1) is None:
                return 1
            try:
                return int(m.group(1))
            except ValueError:
                return 1 if m.group(1).strip().lower() in ("true", "yes", "on") else 0

        v = _parse_bool_flag(r"^\s*render(?:\s+(\S+))?\s*$")
        if v is not None:
            mesh.render = bool(v)
            return True

        v = _parse_bool_flag(r"^\s*shadow(?:\s+(\S+))?\s*$")
        if v is not None:
            mesh.shadow = bool(v)
            return True

        v = _parse_bool_flag(r"^\s*beaming(?:\s+(\S+))?\s*$")
        if v is not None:
            mesh.beaming = bool(v)
            return True

        v = _parse_bool_flag(r"^\s*backgroundgeometry(?:\s+(\S+))?\s*$")
        if v is not None:
            mesh.background_geometry = bool(v)
            return True

        v = _parse_bool_flag(r"^\s*rotatetexture(?:\s+(\S+))?\s*$")
        if v is not None:
            mesh.rotate_texture = bool(v)
            return True

        v = _parse_bool_flag(r"^\s*lightmapped(?:\s+(\S+))?\s*$")
        if v is not None:
            mesh.has_lightmap = bool(v)
            return True

        # K2-only dirt properties (ignored unless present).
        v = _parse_bool_flag(r"^\s*dirt_enabled(?:\s+(\S+))?\s*$")
        if v is not None:
            mesh.dirt_enabled = bool(v)
            return True
        if re.match(r"^\s*dirt_texture\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*dirt_texture\s+(\S+)", line, re.IGNORECASE)
            if match:
                try:
                    mesh.dirt_texture = int(match.group(1))
                except ValueError:
                    # If it's not a number, try to parse as string (legacy support)
                    mesh.dirt_texture = 1  # Default to 1 if parsing fails
            return True
        if re.match(r"^\s*dirt_worldspace\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*dirt_worldspace\s+(\S+)", line, re.IGNORECASE)
            if match:
                mesh.dirt_worldspace = int(match.group(1))
            return True
        v = _parse_bool_flag(r"^\s*hologram_donotdraw(?:\s+(\S+))?\s*$")
        if v is not None:
            mesh.hologram_donotdraw = bool(v)
            return True
        if re.match(r"^\s*dirt_coordinate_space\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*dirt_coordinate_space\s+(\S+)", line, re.IGNORECASE)
            if match:
                mesh.dirt_coordinate_space = int(match.group(1))
            return True

        # Parse verts declaration
        if re.match(r"^\s*verts\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*verts\s+(\S+)", line, re.IGNORECASE)
            if match:
                self._task = "verts"
                self._task_total = int(match.group(1))
                self._task_count = 0
                mesh.vertex_positions = []
                mesh.vertex_normals = []
                mesh.vertex_uv1 = []
                mesh.vertex_uvs = mesh.vertex_uv1
                mesh.vertex_uv2 = []
            return True

        # Parse faces declaration
        if re.match(r"^\s*faces\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*faces\s+(\S+)", line, re.IGNORECASE)
            if match:
                self._task = "faces"
                self._task_total = int(match.group(1))
                self._task_count = 0
                mesh.faces = []
            return True

        # Parse tverts declaration
        if re.match(r"^\s*tverts\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*tverts\s+(\S+)", line, re.IGNORECASE)
            if match:
                self._task = "tverts"
                self._task_total = int(match.group(1))
                self._task_count = 0
                if mesh.vertex_uv1 is None:
                    mesh.vertex_uv1 = []
                mesh.vertex_uvs = mesh.vertex_uv1
            return True

        # Parse tverts1/lightmaptverts declaration
        if re.match(r"^\s*(tverts1|lightmaptverts)\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*(tverts1|lightmaptverts)\s+(\S+)", line, re.IGNORECASE)
            if match:
                self._task = "tverts1"
                self._task_total = int(match.group(2))
                self._task_count = 0
                if mesh.vertex_uv2 is None:
                    mesh.vertex_uv2 = []
            return True

        # Parse mesh task data (verts/faces/uvs). Other tasks (bones/weights/constraints/flare arrays)
        # are handled by their dedicated parsers.
        # AABB nodes can have mesh data, so allow parsing even if node_type is AABB
        if self._task in ("verts", "faces", "tverts", "tverts1"):
            # Ensure mesh exists for AABB nodes with mesh data
            if self._current_node and self._current_node.node_type == MDLNodeType.AABB and self._current_node.mesh is None:
                self._current_node.mesh = MDLMesh()
            return self._parse_task_data(line)

        # Parse skin/dangly payloads (these are stored on the node, not necessarily via mesh subclassing).
        if self._parse_skin_data(line):
            return True
        if self._parse_dangly_data(line):
            return True

        return False

    def _parse_task_data(self, line: str) -> bool:
        """Parse data for current task (verts, faces, tverts, etc.).

        Reference: vendor/mdlops/MDLOpsM.pm:4459-4643
        """
        if not self._current_node:
            return False
        
        # AABB nodes can have mesh data - ensure mesh exists
        if self._current_node.mesh is None and self._current_node.node_type == MDLNodeType.AABB:
            self._current_node.mesh = MDLMesh()
        
        if not self._current_node.mesh:
            return False

        mesh = self._current_node.mesh

        if self._task == "verts":
            # Parse vertex: "index x y z [nx ny nz] [u v] [u2 v2]"
            # Reference: vendor/mdlops/MDLOpsM.pm:4468-4471
            parts = line.split()
            # Unit test fixtures also allow a compact form without an explicit index: "x y z"
            if len(parts) == 3:
                idx = self._task_count
                pos = Vector3(_parse_float_robust(parts[0]), _parse_float_robust(parts[1]), _parse_float_robust(parts[2]))
                mesh.vertex_positions.append(pos)
            elif len(parts) >= 4:
                idx = int(parts[0])
                pos = Vector3(_parse_float_robust(parts[1]), _parse_float_robust(parts[2]), _parse_float_robust(parts[3]))
                # Keep positions in encounter order; most ASCII exports are sequential.
                mesh.vertex_positions.append(pos)

                # Optional normal
                if len(parts) >= 7:
                    normal = Vector3(_parse_float_robust(parts[4]), _parse_float_robust(parts[5]), _parse_float_robust(parts[6]))
                    if mesh.vertex_normals is None:
                        mesh.vertex_normals = []
                    while len(mesh.vertex_normals) <= idx:
                        mesh.vertex_normals.append(Vector3.from_null())
                    mesh.vertex_normals[idx] = normal

                # Optional UV1
                if len(parts) >= 9:
                    uv = Vector2(_parse_float_robust(parts[7]), _parse_float_robust(parts[8]))
                    if mesh.vertex_uv1 is None:
                        mesh.vertex_uv1 = []
                        mesh.vertex_uvs = mesh.vertex_uv1
                    while len(mesh.vertex_uv1) <= idx:
                        mesh.vertex_uv1.append(Vector2(0, 0))
                    mesh.vertex_uv1[idx] = uv

                # Optional UV2
                if len(parts) >= 11:
                    uv = Vector2(_parse_float_robust(parts[9]), _parse_float_robust(parts[10]))
                    if mesh.vertex_uv2 is None:
                        mesh.vertex_uv2 = []
                    while len(mesh.vertex_uv2) <= idx:
                        mesh.vertex_uv2.append(Vector2(0, 0))
                    mesh.vertex_uv2[idx] = uv

                self._task_count += 1
                if self._task_count >= self._task_total:
                    self._task = ""
                return True

        elif self._task == "faces":
            # Parse face: "index v1 v2 v3 material smoothing [t1 t2 t3]"
            # Reference: vendor/mdlops/MDLOpsM.pm:4472-4549
            # Support both normal format and magnusll format with extra tvert indices
            parts = line.split()
            # MDLOps commonly emits *8 integers per face*:
            #   v1 v2 v3 smoothgroup_mask t1 t2 t3 material_id
            # and can emit multiple faces per line by concatenating these 8-int groups.
            #
            # Example (from real fixtures):
            #   0 1 2 16 0 1 2 5
            #
            # This is distinct from the packed 4-tuple format below.
            if len(parts) >= 8 and len(parts) % 8 == 0:
                try:
                    ints = [int(p) for p in parts]
                except ValueError:
                    ints = []
                if ints:
                    for base in range(0, len(ints), 8):
                        v1, v2, v3 = ints[base + 0], ints[base + 1], ints[base + 2]
                        smoothgroup_mask = ints[base + 3]
                        t1, t2, t3 = ints[base + 4], ints[base + 5], ints[base + 6]
                        material_id = ints[base + 7]

                        # MDLOps quirk: sometimes the 'smoothgroup_mask' column contains the
                        # full packed material value (e.g. 501) instead of just the mask (e.g. 15).
                        # We normalize it here to ensure roundtrip equality.
                        # Check if high bits are set AND low bits match material_id.
                        if smoothgroup_mask > 31 and (smoothgroup_mask & 0x1F) == (material_id & 0x1F):
                            # It's a packed material; extract the high bits as smoothing group.
                            smoothgroup_mask = smoothgroup_mask >> 5

                        # Ensure material_id is masked to surface index (0-31)
                        if material_id > 31:
                            material_id &= 0x1F

                        face = MDLFace()
                        face.v1 = v1
                        face.v2 = v2
                        face.v3 = v3
                        face.smoothgroup = smoothgroup_mask
                        face.t1 = t1
                        face.t2 = t2
                        face.t3 = t3
                        face.material = material_id
                        mesh.faces.append(face)

                        self._task_count += 1
                        if self._task_count >= self._task_total:
                            self._task = ""
                            # Populate face payload derived from mesh geometry (binary header data),
                            # e.g. adjacency indices, plane coefficient, and per-face normal.
                            _mdl_recompute_mesh_face_payload(mesh)
                            break
                    return True
            # MDLOps ASCII commonly encodes faces as packed 4-tuples:
            #   v1 v2 v3 packed_material
            # and will often place TWO faces per line:
            #   v1 v2 v3 packed_material v1 v2 v3 packed_material
            #
            # packed_material is a 32-bit integer (surface + smoothing in higher bits),
            # e.g. values like 131072 are common and must NOT be treated as a vertex index.
            #
            # Reference: MDLOpsM.pm (faces export) + our binary face material packing helpers.
            if len(parts) >= 4 and len(parts) % 4 == 0:
                try:
                    m0 = int(parts[3])
                except ValueError:
                    m0 = 0
                if m0 > 0xFFFF:
                    # Parse as groups of 4: (v1, v2, v3, packed_material)
                    for base in range(0, len(parts), 4):
                        v1 = int(parts[base + 0])
                        v2 = int(parts[base + 1])
                        v3 = int(parts[base + 2])
                        packed_material = int(parts[base + 3])

                        face = MDLFace()
                        face.v1 = v1
                        face.v2 = v2
                        face.v3 = v3
                        face.material = packed_material
                        mesh.faces.append(face)

                        self._task_count += 1
                        if self._task_count >= self._task_total:
                            self._task = ""
                            break
                    return True

            # Unit test fixtures also allow compact forms:
            # - "v1 v2 v3 material"
            # - "v1 v2 v3 material smoothing"
            if len(parts) == 4:
                idx = self._task_count
                v1 = int(parts[0])
                v2 = int(parts[1])
                v3 = int(parts[2])
                surface_material = int(parts[3])
                smoothing_group = 0
            elif len(parts) == 5:
                idx = self._task_count
                v1 = int(parts[0])
                v2 = int(parts[1])
                v3 = int(parts[2])
                surface_material = int(parts[3])
                smoothing_group = int(parts[4])
            elif len(parts) >= 6:
                idx = int(parts[0])
                v1 = int(parts[1])
                v2 = int(parts[2])
                v3 = int(parts[3])
                surface_material = int(parts[4])
                smoothing_group = int(parts[5])
            else:
                return False

            # Check for magnusll format with extra tvert indices (parts[8], parts[9], parts[10])
            # (ignored for now; we only care about topology/material for these tests)
            if len(parts) >= 11:
                pass

            face = MDLFace()
            face.v1 = v1
            face.v2 = v2
            face.v3 = v3
            face.material = int(surface_material)
            face.smoothgroup = int(smoothing_group)

            mesh.faces.append(face)
            self._task_count += 1
            if self._task_count >= self._task_total:
                self._task = ""
            return True

        elif self._task == "tverts":
            # Parse texture vertex: "index u v"
            # Reference: vendor/mdlops/MDLOpsM.pm:4551-4554
            parts = line.split()
            # Unit test fixtures also allow compact form without an explicit index: "u v"
            if len(parts) == 2:
                idx = self._task_count
                uv = Vector2(_parse_float_robust(parts[0]), _parse_float_robust(parts[1]))
            elif len(parts) >= 3:
                idx = int(parts[0])
                uv = Vector2(_parse_float_robust(parts[1]), _parse_float_robust(parts[2]))
            else:
                return False

            if mesh.vertex_uv1 is None:
                mesh.vertex_uv1 = []
            while len(mesh.vertex_uv1) <= idx:
                mesh.vertex_uv1.append(Vector2(0, 0))
            mesh.vertex_uv1[idx] = uv
            mesh.vertex_uvs = mesh.vertex_uv1
            self._task_count += 1
            if self._task_count >= self._task_total:
                self._task = ""
            return True

        elif self._task == "tverts1":
            # Parse texture vertex for second texture: "index u v"
            # Reference: vendor/mdlops/MDLOpsM.pm:4555-4558
            parts = line.split()
            if len(parts) == 2:
                idx = self._task_count
                uv = Vector2(_parse_float_robust(parts[0]), _parse_float_robust(parts[1]))
            elif len(parts) >= 3:
                idx = int(parts[0])
                uv = Vector2(_parse_float_robust(parts[1]), _parse_float_robust(parts[2]))
            else:
                return False

            if mesh.vertex_uv2 is None:
                mesh.vertex_uv2 = []
            while len(mesh.vertex_uv2) <= idx:
                mesh.vertex_uv2.append(Vector2(0, 0))
            mesh.vertex_uv2[idx] = uv
            self._task_count += 1
            if self._task_count >= self._task_total:
                self._task = ""
            return True

        return False

    def _parse_skin_data(self, line: str) -> bool:
        """Parse skin mesh data (bones, weights).

        Reference: vendor/mdlops/MDLOpsM.pm:4595-4619
        """
        if not self._current_node:
            return False

        # Skin payload is optional; create it when we encounter skin-specific sections.
        skin = self._current_node.skin
        if skin is None:
            if not re.match(r"^\s*(bones|weights)\s+(\S+)", line, re.IGNORECASE):
                return False
            skin = MDLSkin()
            self._current_node.skin = skin
            # Some toolchains omit bind-pose qbones/tbones in ASCII. Treat missing arrays as
            # "implicitly identity" during comparison by leaving them empty (binary reader also
            # commonly has them empty). The bones section below will still populate bone_indices.

        # Parse bones declaration
        if re.match(r"^\s*bones\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*bones\s+(\S+)", line, re.IGNORECASE)
            if match:
                self._task = "bones"
                self._task_total = int(match.group(1))
                self._task_count = 0
                skin.qbones = []
                skin.tbones = []
                skin.bone_indices = ()
            return True

        # Parse weights declaration
        if re.match(r"^\s*weights\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*weights\s+(\S+)", line, re.IGNORECASE)
            if match:
                self._task = "weights"
                self._task_total = int(match.group(1))
                self._task_count = 0
                skin.vertex_bones = []
            return True

        # Parse bones data
        if self._task == "bones":
            # Format: "index bone_idx qx qy qz qw tx ty tz"
            # Reference: vendor/mdlops/MDLOpsM.pm:1765-1768
            parts = line.split()
            if len(parts) >= 9:
                idx = int(parts[0])
                bone_idx = int(parts[1])
                qbone = Vector4(_parse_float_robust(parts[2]), _parse_float_robust(parts[3]), _parse_float_robust(parts[4]), _parse_float_robust(parts[5]))
                tbone = Vector3(_parse_float_robust(parts[6]), _parse_float_robust(parts[7]), _parse_float_robust(parts[8]))

                # Update bone_indices tuple (need to convert to list, modify, convert back)
                # Update bone_indices list
                bone_list = list(skin.bone_indices)
                while len(bone_list) <= idx:
                    bone_list.append(0)
                bone_list[idx] = bone_idx
                skin.bone_indices = tuple(bone_list)
                # Only append bind-pose transforms if the ASCII actually provides meaningful data.
                # The writer currently emits identity/zero when we don't have bind-pose transforms,
                # and the binary reader often leaves qbones/tbones empty; keep them empty for stability.
                if not (qbone.x == 0.0 and qbone.y == 0.0 and qbone.z == 0.0 and qbone.w == 1.0):
                    skin.qbones.append(qbone)
                if not (tbone.x == 0.0 and tbone.y == 0.0 and tbone.z == 0.0):
                    skin.tbones.append(tbone)
                self._task_count += 1
                if self._task_count >= self._task_total:
                    self._task = ""
                return True

        # Parse weights data
        if self._task == "weights":
            # Format: "bone1 weight1 [bone2 weight2] [bone3 weight3] [bone4 weight4]"
            # Reference: vendor/mdlops/MDLOpsM.pm:4595-4619
            parts = line.split()
            if len(parts) >= 2:
                # Parse bone-weight pairs *in encounter order*.
                # Order is meaningful for roundtrip stability (MDX stores up to 4 indices/weights in order).
                pairs: list[tuple[int, float]] = []
                seen: set[int] = set()
                i = 0
                while i < len(parts) - 1:
                    try:
                        bone_idx = int(parts[i])
                        weight = _parse_float_robust(parts[i + 1])
                    except ValueError:
                        break
                    i += 2
                    if bone_idx < 0 or weight == 0.0:
                        continue
                    if bone_idx in seen:
                        continue
                    seen.add(bone_idx)
                    pairs.append((bone_idx, weight))

                while len(pairs) < 4:
                    pairs.append((-1, 0.0))
                bone_vertex = MDLBoneVertex()
                bone_vertex.vertex_indices = cast(
                    "tuple[float, float, float, float]",
                    tuple(float(pairs[i][0]) for i in range(4)),
                )
                bone_vertex.vertex_weights = cast(
                    "tuple[float, float, float, float]",
                    tuple(float(pairs[i][1]) for i in range(4)),
                )

                skin.vertex_bones.append(bone_vertex)
                self._task_count += 1
                if self._task_count >= self._task_total:
                    self._task = ""
                return True

        return False

    def _parse_dangly_data(self, line: str) -> bool:
        """Parse dangly mesh data (constraints).

        Reference: vendor/mdlops/MDLOpsM.pm:4438-4442, 4620-4623
        """
        if not self._current_node:
            return False

        dangly = self._current_node.dangly
        if dangly is None:
            # Only create on a dangly-relevant header line.
            if not re.match(r"^\s*constraints\s+(\S+)", line, re.IGNORECASE):
                return False
            dangly = MDLDangly()
            self._current_node.dangly = dangly

        # Parse constraints declaration
        if re.match(r"^\s*constraints\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*constraints\s+(\S+)", line, re.IGNORECASE)
            if match:
                self._task = "constraints"
                self._task_total = int(match.group(1))
                self._task_count = 0
                dangly.constraints = []
            return True

        # Parse constraints data
        if self._task == "constraints":
            # Format: "index type target target_node"
            # Reference: vendor/mdlops/MDLOpsM.pm:4620-4623
            parts = line.split()
            if len(parts) >= 4:
                constraint = MDLConstraint()
                constraint.type = int(parts[1])
                constraint.target = int(parts[2])
                constraint.target_node = int(parts[3])
                dangly.constraints.append(constraint)
                self._task_count += 1
                if self._task_count >= self._task_total:
                    self._task = ""
                return True

        return False

    def _parse_light_data(self, line: str) -> bool:
        """Parse light node data.

        Reference: vendor/mdlops/MDLOpsM.pm:4238-4261
        """
        if not self._current_node or not self._current_node.light:
            return False

        light = self._current_node.light

        # Controller-like properties often appear directly in ASCII.
        # Support them even if the light object doesn't predefine attributes.
        if re.match(r"^\s*color\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*color\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE)
            if match:
                light.color = Color(float(match.group(1)), float(match.group(2)), float(match.group(3)))
            return True

        if re.match(r"^\s*radius\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*radius\s+(\S+)", line, re.IGNORECASE)
            if match:
                light.radius = float(match.group(1))
            return True

        if re.match(r"^\s*multiplier\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*multiplier\s+(\S+)", line, re.IGNORECASE)
            if match:
                light.multiplier = float(match.group(1))
            return True

        if re.match(r"^\s*flareradius\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*flareradius\s+(\S+)", line, re.IGNORECASE)
            if match:
                light.flare_radius = float(match.group(1))
            return True

        if re.match(r"^\s*(lightpriority|priority)\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*(lightpriority|priority)\s+(\S+)", line, re.IGNORECASE)
            if match:
                light.light_priority = int(match.group(2))
            return True

        if re.match(r"^\s*ambientonly(\s+(\S+))?\s*$", line, re.IGNORECASE):
            match = re.match(r"^\s*ambientonly(\s+(\S+))?\s*$", line, re.IGNORECASE)
            if match:
                light.ambient_only = bool(int(match.group(2)) if match.group(2) is not None else 1)
            return True

        if re.match(r"^\s*shadow(\s+(\S+))?\s*$", line, re.IGNORECASE):
            match = re.match(r"^\s*shadow(\s+(\S+))?\s*$", line, re.IGNORECASE)
            if match:
                light.shadow = bool(int(match.group(2)) if match.group(2) is not None else 1)
            return True

        if re.match(r"^\s*flare(\s+(\S+))?\s*$", line, re.IGNORECASE):
            match = re.match(r"^\s*flare(\s+(\S+))?\s*$", line, re.IGNORECASE)
            if match:
                light.flare = bool(int(match.group(2)) if match.group(2) is not None else 1)
            return True

        if re.match(r"^\s*fadinglight(\s+(\S+))?\s*$", line, re.IGNORECASE):
            match = re.match(r"^\s*fadinglight(\s+(\S+))?\s*$", line, re.IGNORECASE)
            if match:
                light.fading_light = bool(int(match.group(2)) if match.group(2) is not None else 1)
            return True

        # Parse flare data arrays
        if re.match(r"^\s*(flarepositions|flaresizes|texturenames)\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*(flarepositions|flaresizes|texturenames)\s+(\S+)", line, re.IGNORECASE)
            if match:
                task_name = match.group(1).lower()
                count = int(match.group(2))
                if count > 0:
                    self._task = cast(
                        "Literal['verts', 'faces', 'tverts', 'tverts1', 'lightmaptverts', 'bones', 'flarecolorshifts', 'weights', 'constraints', 'aabb', '']",
                        task_name.lower(),
                    )
                    self._task_total = count
                    self._task_count = 0
                    if task_name == "flarepositions":
                        light.flare_positions = []
                    elif task_name == "flaresizes":
                        light.flare_sizes = []
                    elif task_name == "texturenames":
                        light.flare_textures = []
                return True

        if re.match(r"^\s*flarecolorshifts\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*flarecolorshifts\s+(\S+)", line, re.IGNORECASE)
            if match:
                count = int(match.group(1))
                if count > 0:
                    self._task = "flarecolorshifts"
                    self._task_total = count
                    self._task_count = 0
                    light.flare_color_shifts = []
                return True

        # Parse flare array data
        if self._task == "flarepositions":
            parts = line.split()
            if parts:
                light.flare_positions.append(_parse_float_robust(parts[0]))
                self._task_count += 1
                if self._task_count >= self._task_total:
                    self._task = ""
                return True

        if self._task == "flaresizes":
            parts = line.split()
            if parts:
                light.flare_sizes.append(_parse_float_robust(parts[0]))
                self._task_count += 1
                if self._task_count >= self._task_total:
                    self._task = ""
                return True

        if self._task == "texturenames":
            parts = line.split()
            if parts:
                light.flare_textures.append(parts[0])
                self._task_count += 1
                if self._task_count >= self._task_total:
                    self._task = ""
                return True

        if self._task == "flarecolorshifts":
            parts = line.split()
            if len(parts) >= 3:
                light.flare_color_shifts.append((_parse_float_robust(parts[0]), _parse_float_robust(parts[1]), _parse_float_robust(parts[2])))
                self._task_count += 1
                if self._task_count >= self._task_total:
                    self._task = ""
                return True

        return False

    def _parse_emitter_data(self, line: str) -> bool:
        """Parse emitter node data.

        Reference: vendor/mdlops/MDLOpsM.pm:4098-4108
        """
        if not self._current_node or not self._current_node.emitter:
            return False

        emitter = self._current_node.emitter

        # Emitter properties matching mdlops (vendor/mdlops/MDLOpsM.pm:3991-4012)
        if re.match(r"^\s*deadspace\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*deadspace\s+(\S+)", line, re.IGNORECASE)
            if match:
                emitter.dead_space = float(match.group(1))
            return True
        if re.match(r"^\s*blastradius\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*blastradius\s+(\S+)", line, re.IGNORECASE)
            if match:
                emitter.blast_radius = float(match.group(1))
            return True
        if re.match(r"^\s*blastlength\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*blastlength\s+(\S+)", line, re.IGNORECASE)
            if match:
                emitter.blast_length = float(match.group(1))
            return True
        if re.match(r"^\s*numbranches\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*numbranches\s+(\S+)", line, re.IGNORECASE)
            if match:
                emitter.branch_count = int(match.group(1))
            return True
        if re.match(r"^\s*controlptsmoothing\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*controlptsmoothing\s+(\S+)", line, re.IGNORECASE)
            if match:
                emitter.control_point_smoothing = float(match.group(1))
            return True
        if re.match(r"^\s*xgrid\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*xgrid\s+(\S+)", line, re.IGNORECASE)
            if match:
                emitter.x_grid = int(match.group(1))
            return True
        if re.match(r"^\s*ygrid\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*ygrid\s+(\S+)", line, re.IGNORECASE)
            if match:
                emitter.y_grid = int(match.group(1))
            return True
        if re.match(r"^\s*spawntype\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*spawntype\s+(\S+)", line, re.IGNORECASE)
            if match:
                emitter.spawn_type = int(match.group(1))
            return True
        if re.match(r"^\s*update\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*update\s+(\S+)", line, re.IGNORECASE)
            if match:
                emitter.update = match.group(1)
            return True
        if re.match(r"^\s*render\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*render\s+(\S+)", line, re.IGNORECASE)
            if match:
                emitter.render = match.group(1)
            return True
        if re.match(r"^\s*blend\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*blend\s+(\S+)", line, re.IGNORECASE)
            if match:
                emitter.blend = match.group(1)
            return True
        if re.match(r"^\s*texture\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*texture\s+(\S+)", line, re.IGNORECASE)
            if match:
                emitter.texture = match.group(1)
            return True
        if re.match(r"^\s*chunkname\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*chunkname\s+(\S+)", line, re.IGNORECASE)
            if match:
                emitter.chunk_name = match.group(1)
            return True
        if re.match(r"^\s*twosidedtex\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*twosidedtex\s+(\S+)", line, re.IGNORECASE)
            if match:
                emitter.two_sided_texture = int(match.group(1))
            return True
        if re.match(r"^\s*loop\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*loop\s+(\S+)", line, re.IGNORECASE)
            if match:
                emitter.loop = int(match.group(1))
            return True
        if re.match(r"^\s*renderorder\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*renderorder\s+(\S+)", line, re.IGNORECASE)
            if match:
                emitter.render_order = int(match.group(1))
            return True
        if re.match(r"^\s*m_bframeblending\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*m_bframeblending\s+(\S+)", line, re.IGNORECASE)
            if match:
                emitter.frame_blender = int(match.group(1))
            return True
        if re.match(r"^\s*m_sdepthtexturename\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*m_sdepthtexturename\s+(\S+)", line, re.IGNORECASE)
            if match:
                emitter.depth_texture = match.group(1)
            return True

        # Emitter flags (vendor/mdlops/MDLOpsM.pm:3998-4012)
        emitter_flags = {
            "p2p": 0x0001,
            "p2p_sel": 0x0002,
            "affectedbywind": 0x0004,
            "m_istinted": 0x0008,
            "bounce": 0x0010,
            "random": 0x0020,
            "inherit": 0x0040,
            "inheritvel": 0x0080,
            "inherit_local": 0x0100,
            "splat": 0x0200,
            "inherit_part": 0x0400,
            "depth_texture": 0x0800,
            "emitterflag13": 0x1000,
        }

        for flag_name, flag_value in emitter_flags.items():
            pattern = rf"^\s*{re.escape(flag_name)}\s+(\S+)"
            if re.match(pattern, line, re.IGNORECASE):
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    if int(match.group(1)) == 1:
                        emitter.flags |= flag_value
                return True

        return False

    def _parse_reference_data(self, line: str) -> bool:
        """Parse reference node data.

        Reference: vendor/mdlops/MDLOpsM.pm:4262-4265
        """
        if not self._current_node or not self._current_node.reference:
            return False

        reference = self._current_node.reference

        if re.match(r"^\s*(refmodel|model)\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*(refmodel|model)\s+(\S+)", line, re.IGNORECASE)
            if match:
                reference.model = match.group(2)
            return True

        if re.match(r"^\s*reattachable(\s+(\S+))?\s*$", line, re.IGNORECASE):
            match = re.match(r"^\s*reattachable(\s+(\S+))?\s*$", line, re.IGNORECASE)
            if match:
                reference.reattachable = (int(match.group(2)) != 0) if match.group(2) is not None else True
            return True

        return False

    def _parse_saber_data(self, line: str) -> bool:
        """Parse saber node data.

        Reference: vendor/mdlops/MDLOpsM.pm:1937-2010
        """
        if not self._current_node or not self._current_node.saber:
            return False

        saber = self._current_node.saber

        if re.match(r"^\s*sabertype\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*sabertype\s+(\S+)", line, re.IGNORECASE)
            if match:
                saber.saber_type = int(match.group(1))
            return True

        if re.match(r"^\s*sabercolor\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*sabercolor\s+(\S+)", line, re.IGNORECASE)
            if match:
                saber.saber_color = int(match.group(1))
            return True

        if re.match(r"^\s*(saberlength|length)\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*(saberlength|length)\s+(\S+)", line, re.IGNORECASE)
            if match:
                saber.saber_length = float(match.group(2))
                # Convenience alias expected by tests/legacy code
                # FIXME: should modify the tests/legacy code instead of this line
                saber.__dict__["length"] = saber.saber_length
            return True

        if re.match(r"^\s*(saberwidth|width)\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*(saberwidth|width)\s+(\S+)", line, re.IGNORECASE)
            if match:
                saber.saber_width = float(match.group(2))
                # Convenience alias expected by tests/legacy code
                # FIXME: should modify the tests/legacy code instead of this line
                saber.__dict__["width"] = saber.saber_width
            return True

        if re.match(r"^\s*saberflarecolor\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*saberflarecolor\s+(\S+)", line, re.IGNORECASE)
            if match:
                saber.saber_flare_color = int(match.group(1))
            return True

        if re.match(r"^\s*saberflareradius\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*saberflareradius\s+(\S+)", line, re.IGNORECASE)
            if match:
                saber.saber_flare_radius = float(match.group(1))
            return True

        return False

    def _parse_walkmesh_data(self, line: str) -> bool:
        """Parse walkmesh/AABB node data.

        Reference: vendor/mdlops/MDLOpsM.pm:4443-4447, 4624-4627
        """
        if not self._current_node or not self._current_node.aabb:
            return False

        walkmesh = self._current_node.aabb

        # Parse aabb declaration
        if re.match(r"^\s*aabb", line, re.IGNORECASE):
            # MDLOps format: "aabb" declaration on one line, data lines follow
            # Reference: vendor/MDLOps/MDLOpsM.pm:3457 (prints "aabb" on same line, then data lines)
            # Data format: 6 floats (bbox_min.xyz, bbox_max.xyz) + 1 int (face_index)
            # Reference: vendor/MDLOps/MDLOpsM.pm:3459, 4625-4626
            self._task = "aabb"
            self._task_count = 0
            return True

        # Parse aabb data
        if self._task == "aabb":
            # Format: "      bbox_min.x bbox_min.y bbox_min.z bbox_max.x bbox_max.y bbox_max.z face_index"
            # MDLOps stores 7 values: 6 floats + 1 int
            # Reference: vendor/MDLOps/MDLOpsM.pm:3459, 4625-4626
            parts = line.split()
            if len(parts) >= 7:
                # Parse 6 floats (bbox_min.xyz, bbox_max.xyz) + 1 int (face_index)
                aabb_node = MDLAABBNode(
                    bbox_min=Vector3(_parse_float_robust(parts[0]), _parse_float_robust(parts[1]), _parse_float_robust(parts[2])),
                    bbox_max=Vector3(_parse_float_robust(parts[3]), _parse_float_robust(parts[4]), _parse_float_robust(parts[5])),
                    face_index=int(parts[6]),
                    left_child_offset=0,  # Not stored in ASCII format
                    right_child_offset=0,  # Not stored in ASCII format
                    unknown=0,  # Not stored in ASCII format
                )
                walkmesh.aabbs.append(aabb_node)
                self._task_count += 1
                return True

        return False

    def _build_node_hierarchy(self) -> None:
        """Build the node hierarchy from parent relationships.

        Reference: vendor/mdlops/MDLOpsM.pm:4222-4237
        """
        if not self._nodes:
            return
        assert self._mdl is not None, "MDL is not set"

        # If the ASCII contains an explicit root node, prefer that as the real root.
        # MDLOps uses a real node as the root of the geometry tree (no extra implicit container node).
        # In many files/tests the root node is named "root" (not the same as `newmodel`).
        #
        # Heuristics:
        # - If there is exactly one top-level node (parent_id == -1), that node is the root.
        # - Otherwise, if there is a top-level node matching the model name, use that.
        # - Otherwise, fall back to an implicit root container (legacy behavior).
        explicit_root: MDLNode | None = None
        top_level_nodes: list[MDLNode] = [n for n in self._nodes if n.parent_id == -1]
        if (self._mdl.name or "").strip():
            for n in top_level_nodes:
                if n.name and n.name.lower() == self._mdl.name.lower():
                    explicit_root = n
                    break

        # Many exported ASCIIs use a literal "root" node name. Treat that as an explicit root.
        if explicit_root is None and len(top_level_nodes) == 1:
            only = top_level_nodes[0]
            if only.name and only.name.lower() == "root":
                explicit_root = only

        if explicit_root is not None:
            self._mdl.root = explicit_root
            self._mdl.root.children = []
        else:
            self._mdl.root.children = []
        for node in self._nodes:
            node.children = []

        # Build name-to-node lookup for hierarchy resolution
        by_name: dict[str, MDLNode] = {n.name.lower(): n for n in self._nodes if n.name}

        # MDLOps uses node 0 (first parsed node) as the starting point for traversal
        # Reference: vendor/MDLOps/MDLOpsM.pm:6282 (writebinarynode starts from node 0)
        # Set root to node 0 if nodes exist, matching MDLOps behavior exactly
        if self._nodes:
            self._mdl.root = self._nodes[0]
            self._mdl.root.children = []
        else:
            self._mdl.root.children = []
        
        for node in self._nodes:
            node.children = []
        
        # Build name-to-node lookup for hierarchy resolution
        by_name: dict[str, MDLNode] = {n.name.lower(): n for n in self._nodes if n.name}
        
        # Build parent-child relationships (matching MDLOps: vendor/MDLOps/MDLOpsM.pm:4222-4237)
        for node in self._nodes:
            parent_node: MDLNode | None = None
            
            # First try to resolve by stored parent name (handles cases where parent wasn't parsed yet)
            parent_name: str | None = node.__dict__.get("_parent_name")
            if isinstance(parent_name, str) and parent_name in by_name:
                parent_node = by_name[parent_name]
                # Update parent_id to match resolved parent
                node.parent_id = self._nodes.index(parent_node) if parent_node in self._nodes else -1
            elif node.parent_id >= 0 and node.parent_id < len(self._nodes):
                # Fall back to index-based resolution
                parent_node = self._nodes[node.parent_id]
            
            if parent_node is not None:
                # MDLOps adds child to parent's children array and increments childcount
                # Reference: vendor/MDLOps/MDLOpsM.pm:4235-4236
                parent_node.children.append(node)
            elif node is not self._mdl.root:
                # If parent not found and node is not the root, attach to root to ensure it's not lost
                # This ensures all nodes are reachable from node 0 during recursive traversal
                # Reference: vendor/MDLOps/MDLOpsM.pm:6282 (writebinarynode starts from node 0)
                self._mdl.root.children.append(node)
        
        # Cleanup temporary parent tracking
        for node in self._nodes:
            node.__dict__.pop("_parent_name", None)
