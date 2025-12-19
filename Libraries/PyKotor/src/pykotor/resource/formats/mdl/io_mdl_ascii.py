from __future__ import annotations

import io
import os
import re

from math import cos, sin, sqrt
from typing import TYPE_CHECKING

from pykotor.common.misc import Color
from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.mdl.mdl_data import (
    MDL,
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
)
from pykotor.resource.formats.mdl.mdl_types import MDLClassification, MDLControllerType, MDLNodeType
from utility.common.geometry import Vector2, Vector3, Vector4

if TYPE_CHECKING:
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
    "position": MDLControllerType.POSITION,
    "orientation": MDLControllerType.ORIENTATION,
    "scale": MDLControllerType.SCALE,
    "alpha": MDLControllerType.ALPHA,
    "color": MDLControllerType.COLOR,
    "radius": MDLControllerType.RADIUS,
    "shadowradius": MDLControllerType.SHADOWRADIUS,
    "verticaldisplacement": MDLControllerType.VERTICALDISPLACEMENT,
    "multiplier": MDLControllerType.MULTIPLIER,
    "alphaEnd": MDLControllerType.ALPHAEND,
    "alphaStart": MDLControllerType.ALPHASTART,
    "birthrate": MDLControllerType.BIRTHRATE,
    "bounce_co": MDLControllerType.BOUNCE_CO,
    "combinetime": MDLControllerType.COMBINETIME,
    "drag": MDLControllerType.DRAG,
    "fps": MDLControllerType.FPS,
    "frameEnd": MDLControllerType.FRAMEEND,
    "frameStart": MDLControllerType.FRAMESTART,
    "grav": MDLControllerType.GRAV,
    "lifeExp": MDLControllerType.LIFEEXP,
    "mass": MDLControllerType.MASS,
    "p2p_bezier2": MDLControllerType.P2P_BEZIER2,
    "p2p_bezier3": MDLControllerType.P2P_BEZIER3,
    "particleRot": MDLControllerType.PARTICLEROT,
    "randvel": MDLControllerType.RANDVEL,
    "sizeStart": MDLControllerType.SIZESTART,
    "sizeEnd": MDLControllerType.SIZEEND,
    "sizeStart_y": MDLControllerType.SIZESTART_Y,
    "sizeEnd_y": MDLControllerType.SIZEEND_Y,
    "spread": MDLControllerType.SPREAD,
    "threshold": MDLControllerType.THRESHOLD,
    "velocity": MDLControllerType.VELOCITY,
    "xsize": MDLControllerType.XSIZE,
    "ysize": MDLControllerType.YSIZE,
    "blurlength": MDLControllerType.BLURLENGTH,
    "lightningDelay": MDLControllerType.LIGHTNINGDELAY,
    "lightningRadius": MDLControllerType.LIGHTNINGRADIUS,
    "lightningScale": MDLControllerType.LIGHTNINGSCALE,
    "lightningSubDiv": MDLControllerType.LIGHTNINGSUBDIV,
    "lightningzigzag": MDLControllerType.LIGHTNINGZIGZAG,
    "alphaMid": MDLControllerType.ALPHAMID,
    "percentStart": MDLControllerType.PERCENTSTART,
    "percentMid": MDLControllerType.PERCENTMID,
    "percentEnd": MDLControllerType.PERCENTEND,
    "sizeMid": MDLControllerType.SIZEMID,
    "sizeMid_y": MDLControllerType.SIZEMID_Y,
    "m_fRandomBirthRate": MDLControllerType.RANDOMBIRTHRATE,
    "targetsize": MDLControllerType.TARGETSIZE,
    "numcontrolpts": MDLControllerType.NUMCONTROLPTS,
    "controlptradius": MDLControllerType.CONTROLPTRADIUS,
    "controlptdelay": MDLControllerType.CONTROLPTDELAY,
    "tangentspread": MDLControllerType.TANGENTSPREAD,
    "tangentlength": MDLControllerType.TANGENTLENGTH,
    "colorMid": MDLControllerType.COLORMID,
    "colorEnd": MDLControllerType.COLOREND,
    "colorStart": MDLControllerType.COLORSTART,
    "detonate": MDLControllerType.DETONATE,
    "selfillumcolor": MDLControllerType.ILLUM_COLOR,
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
    material_raw = getattr(face.material, "value", face.material)
    material_int = int(material_raw) if material_raw is not None else 0

    # Legacy structures may still expose .smoothing_group; prefer explicit value.
    if hasattr(face, "smoothing_group"):
        smoothing = int(getattr(face, "smoothing_group"))
    else:
        smoothing = material_int >> _FACE_SMOOTH_SHIFT

    surface = material_int & _FACE_SURFACE_MASK
    return surface, smoothing


def _pack_face_material(surface_material: int, smoothing_group: int) -> int:
    """Pack surface material and smoothing group into a single integer.

    Args:
        surface_material: Surface material index (0-31)
        smoothing_group: Smoothing group number

    Returns:
        Packed integer value
    """
    return (smoothing_group << _FACE_SMOOTH_SHIFT) | (surface_material & _FACE_SURFACE_MASK)


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


class MDLAsciiWriter:
    """Writer for ASCII MDL files.

    Reference: vendor/mdlops/MDLOpsM.pm:3004-3900 (writeasciimdl)
    """

    def __init__(
        self,
        mdl: MDL,
        target: TARGET_TYPES,
    ):
        """Initialize the ASCII MDL writer.

        Args:
            mdl: The MDL data to write
            target: The target to write to (file path, stream, or bytes buffer)
        """
        self._mdl = mdl

        # Open the target file/stream for writing
        if isinstance(target, (str, bytes, os.PathLike)):
            self._writer = open(target, "w", encoding="utf-8", newline="\n")
        elif isinstance(target, io.TextIOBase):
            self._writer = target
        elif isinstance(target, (bytearray, io.BytesIO)):
            # For bytearray/bytes, create a StringIO and we'll convert at the end
            self._writer = io.StringIO()
            self._target_bytes = target
        else:
            # Try to treat as file-like object
            self._writer = target

    def write_line(self, indent: int, line: str) -> None:
        """Write a line with indentation."""
        self._writer.write("  " * indent + line + "\n")

    def write(self) -> None:
        """Write MDL data to ASCII format.

        Reference: vendor/mdlops/MDLOpsM.pm:3004-3900 (writeasciimdl)
        """
        mdl = self._mdl
        self.write_line(0, "# ASCII MDL")
        self.write_line(0, "filedependancy unknown.tga")
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
        self.write_line(0, f"bmin {mdl.bmin.x} {mdl.bmin.y} {mdl.bmin.z}")
        self.write_line(0, f"bmax {mdl.bmax.x} {mdl.bmax.y} {mdl.bmax.z}")
        self.write_line(0, f"radius {mdl.radius}")
        self.write_line(0, "")
        self.write_line(0, "beginmodelgeom " + mdl.name)
        self.write_line(0, "")
        self._write_node(1, mdl.root)
        self.write_line(0, "")
        self.write_line(0, "endmodelgeom " + mdl.name)
        self.write_line(0, "")

        # Write animations if any (vendor/mdlops/MDLOpsM.pm:3488-3560)
        if mdl.anims:
            for anim in mdl.anims:
                self._write_animation(anim, mdl.name)

        self.write_line(0, "")
        self.write_line(0, "donemodel " + mdl.name)

        # If writing to bytearray/bytes, convert StringIO to bytes
        if hasattr(self, "_target_bytes"):
            content = self._writer.getvalue()
            if isinstance(self._target_bytes, bytearray):
                self._target_bytes.clear()
                self._target_bytes.extend(content.encode("utf-8"))
            elif isinstance(self._target_bytes, io.BytesIO):
                self._target_bytes.write(content.encode("utf-8"))

    def _write_node(self, indent: int, node: MDLNode) -> None:
        """Write a node and its children."""
        self.write_line(indent, f"node {node.node_type.name.lower()} {node.name}")
        self.write_line(indent, "{")
        self._write_node_data(indent + 1, node)
        self.write_line(indent, "}")

        for child in node.children:
            self._write_node(indent, child)

    def _write_node_data(self, indent: int, node: MDLNode) -> None:
        """Write node data including position, orientation, and controllers."""
        self.write_line(indent, f"parent {node.parent_id}")
        self.write_line(indent, f"position {node.position.x} {node.position.y} {node.position.z}")
        self.write_line(indent, f"orientation {node.orientation.x} {node.orientation.y} {node.orientation.z} {node.orientation.w}")

        if node.mesh:
            self._write_mesh(indent, node.mesh)
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
            self._write_controller(indent, controller)

    def _write_mesh(self, indent: int, mesh: MDLMesh) -> None:
        """Write mesh data."""
        self.write_line(indent, f"ambient {mesh.ambient.r} {mesh.ambient.g} {mesh.ambient.b}")
        self.write_line(indent, f"diffuse {mesh.diffuse.r} {mesh.diffuse.g} {mesh.diffuse.b}")
        self.write_line(indent, f"transparencyhint {mesh.transparency_hint}")
        self.write_line(indent, f"bitmap {mesh.texture_1}")
        if mesh.texture_2:
            self.write_line(indent, f"lightmap {mesh.texture_2}")

        if isinstance(mesh, MDLSkin):
            self._write_skin(indent, mesh)
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
        for i, face in enumerate(mesh.faces):
            surface_material, smoothing_group = _unpack_face_material(face)
            self.write_line(
                indent + 1,
                f"{i} {face.v1} {face.v2} {face.v3} {surface_material} {smoothing_group}",
            )

    def _write_skin(self, indent: int, skin: MDLSkin) -> None:
        """Write skin-specific data."""
        self.write_line(indent, "bones " + str(len(skin.bone_indices)))
        for i, bone_idx in enumerate(skin.bone_indices):
            qbone: Vector4 = skin.qbones[i]
            tbone: Vector3 = skin.tbones[i]
            self.write_line(indent + 1, f"{i} {bone_idx} {qbone.x} {qbone.y} {qbone.z} {qbone.w} {tbone.x} {tbone.y} {tbone.z}")

    def _write_dangly(self, indent: int, dangly: MDLDangly) -> None:
        """Write dangly mesh data."""
        self.write_line(indent, "constraints " + str(len(dangly.constraints)))
        for i, constraint in enumerate(dangly.constraints):
            self.write_line(indent + 1, f"{i} {constraint.type} {constraint.target} {constraint.target_node}")

    def _write_light(self, indent: int, light: MDLLight) -> None:
        """Write light data."""
        self.write_line(indent, f"flareradius {light.flare_radius}")
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
        """Write emitter data."""
        self.write_line(indent, f"deadspace {emitter.dead_space}")
        self.write_line(indent, f"blastradius {emitter.blast_radius}")
        self.write_line(indent, f"blastlength {emitter.blast_length}")
        self.write_line(indent, f"branchcount {emitter.branch_count}")
        self.write_line(indent, f"controlpointsmoothing {emitter.control_point_smoothing}")
        self.write_line(indent, f"xgrid {emitter.x_grid}")
        self.write_line(indent, f"ygrid {emitter.y_grid}")
        # mdlops writes render/update/blend as strings (vendor/mdlops/MDLOpsM.pm:3279-3281)
        self.write_line(indent, f"render {emitter.render}")
        self.write_line(indent, f"update {emitter.update}")
        self.write_line(indent, f"blend {emitter.blend}")
        self.write_line(indent, f"texture {emitter.texture}")
        self.write_line(indent, f"chunkname {emitter.chunk_name}")
        # mdlops writes twosidedtex as integer (vendor/mdlops/MDLOpsM.pm:3286)
        self.write_line(indent, f"twosidedtex {emitter.two_sided_texture}")
        # mdlops writes loop as integer (vendor/mdlops/MDLOpsM.pm:3287)
        self.write_line(indent, f"loop {emitter.loop}")
        self.write_line(indent, f"renderorder {emitter.render_order}")
        # mdlops writes m_bFrameBlending as integer (vendor/mdlops/MDLOpsM.pm:3289)
        self.write_line(indent, f"m_bFrameBlending {emitter.frame_blender}")
        # mdlops writes m_sDepthTextureName as string (vendor/mdlops/MDLOpsM.pm:3290)
        if emitter.depth_texture:
            self.write_line(indent, f"m_sDepthTextureName {emitter.depth_texture}")

    def _write_reference(self, indent: int, reference: MDLReference) -> None:
        """Write reference data."""
        self.write_line(indent, f"refmodel {reference.model}")
        if reference.reattachable:
            self.write_line(indent, "reattachable")

    def _write_saber(self, indent: int, saber: MDLSaber) -> None:
        """Write saber data."""
        self.write_line(indent, f"sabertype {saber.saber_type}")
        self.write_line(indent, f"sabercolor {saber.saber_color}")
        self.write_line(indent, f"saberlength {saber.saber_length}")
        self.write_line(indent, f"saberwidth {saber.saber_width}")
        self.write_line(indent, f"saberflarecolor {saber.saber_flare_color}")
        self.write_line(indent, f"saberflareradius {saber.saber_flare_radius}")

    def _write_walkmesh(self, indent: int, walkmesh: MDLWalkmesh) -> None:
        """Write walkmesh data."""
        self.write_line(indent, "aabb " + str(len(walkmesh.aabbs)))
        for i, aabb in enumerate(walkmesh.aabbs):
            self.write_line(indent + 1, f"{i} {aabb.position.x} {aabb.position.y} {aabb.position.z}")

    def _write_controller(self, indent: int, controller: MDLController) -> None:
        """Write controller data."""
        if not controller.rows:
            return

        # Map controller type to name
        controller_name_map = {
            MDLControllerType.POSITION: "positionkey",
            MDLControllerType.ORIENTATION: "orientationkey",
            MDLControllerType.SCALE: "scalekey",
            MDLControllerType.COLOR: "colorkey",
            MDLControllerType.RADIUS: "radiuskey",
            MDLControllerType.SHADOWRADIUS: "shadowradiuskey",
            MDLControllerType.VERTICALDISPLACEMENT: "verticaldisplacementkey",
            MDLControllerType.MULTIPLIER: "multiplierkey",
            MDLControllerType.ALPHAEND: "alphaendkey",
            MDLControllerType.ALPHASTART: "alphastartkey",
            MDLControllerType.BIRTHRATE: "birthratekey",
            MDLControllerType.BOUNCECO: "bouncecokey",
            MDLControllerType.COMBINETIME: "combineetimekey",
            MDLControllerType.DRAG: "dragkey",
            MDLControllerType.FOCUSZONETX: "focuszonetxkey",
            MDLControllerType.FOCUSZONETY: "focuszonetykey",
            MDLControllerType.FRAME: "framekey",
            MDLControllerType.GRAV: "gravkey",
            MDLControllerType.LIFEEXP: "lifeexpkey",
            MDLControllerType.MASS: "masskey",
            MDLControllerType.P2P_BEZIER2: "p2p_bezier2key",
            MDLControllerType.P2P_BEZIER3: "p2p_bezier3key",
            MDLControllerType.PARTICLEROTX: "particlerotxkey",
            MDLControllerType.PARTICLEROTY: "particlerotykey",
            MDLControllerType.PARTICLEROTZ: "particlerotzkey",
            MDLControllerType.RANDVELX: "randvelxkey",
            MDLControllerType.RANDVELY: "randvelykey",
            MDLControllerType.RANDVELZ: "randvelzkey",
            MDLControllerType.SIZESTART: "sizestartkey",
            MDLControllerType.SIZEEND: "sizeendkey",
            MDLControllerType.SIZESTART_Y: "sizestart_ykey",
            MDLControllerType.SIZEEND_Y: "sizeend_ykey",
            MDLControllerType.SPREAD: "spreadkey",
            MDLControllerType.THRESHOLD: "thresholdkey",
            MDLControllerType.VELOCITY: "velocitykey",
            MDLControllerType.XSIZE: "xsizekey",
            MDLControllerType.YSIZE: "ysizekey",
            MDLControllerType.BLUR: "blurkey",
            MDLControllerType.LIGHTNINGDELAY: "lightningdelaykey",
            MDLControllerType.LIGHTNINGRADIUS: "lightningradiuskey",
            MDLControllerType.LIGHTNINGSCALE: "lightningscalekey",
            MDLControllerType.DETONATE: "detonatekey",
            MDLControllerType.ALPHAMID: "alphamidkey",
            MDLControllerType.SIZEMID: "sizemidkey",
            MDLControllerType.SIZEMID_Y: "sizemid_ykey",
            MDLControllerType.BOUNCE_CO: "bounce_cokey",
            MDLControllerType.RANDOMVELX: "randomvelxkey",
            MDLControllerType.RANDOMVELY: "randomvelykey",
            MDLControllerType.RANDOMVELZ: "randomvelzkey",
            MDLControllerType.TILING: "tilingkey",
            MDLControllerType.ILLUM: "illumkey",
            MDLControllerType.ILLUM_COLOR: "selfillumcolorkey",
            MDLControllerType.ALPHA: "alphakey",
        }

        controller_name = controller_name_map.get(controller.controller_type, "unknownkey")
        if controller.is_bezier:
            controller_name = controller_name.replace("key", "bezierkey")

        self.write_line(indent, controller_name)
        for row in controller.rows:
            data_str = " ".join(str(d) for d in row.data)
            self.write_line(indent + 1, f"{row.time} {data_str}")
        self.write_line(indent, "endlist")

    def _write_animation(self, anim: MDLAnimation, model_name: str) -> None:
        """Write animation data.

        Reference: vendor/mdlops/MDLOpsM.pm:3488-3560
        """
        self.write_line(0, "")
        self.write_line(0, f"newanim {anim.name} {model_name}")
        self.write_line(1, f"length {anim.anim_length:.7g}")
        self.write_line(1, f"transtime {anim.transition_length:.7g}")
        if anim.root_model:
            self.write_line(1, f"animroot {anim.root_model}")

        # Write events (vendor/mdlops/MDLOpsM.pm:3496-3503)
        if anim.events:
            for event in anim.events:
                self.write_line(1, f"event {event.activation_time:.7g} {event.name}")

        # Write animation nodes (vendor/mdlops/MDLOpsM.pm:3504-3555)
        # Animation nodes are written as "node dummy <node_name>" with controllers
        # We need to traverse the animation's root node hierarchy
        if anim.root and anim.root.name:
            self._write_animation_node(1, anim.root)

        self.write_line(0, "")
        self.write_line(0, f"doneanim {anim.name} {model_name}")

    def _write_animation_node(self, indent: int, node: MDLNode) -> None:
        """Write an animation node with its controllers.

        Reference: vendor/mdlops/MDLOpsM.pm:3507-3554
        Animation nodes are written as "node dummy <node_name>" regardless of actual type.
        """
        # Animation nodes are always written as "dummy" type (vendor/mdlops/MDLOpsM.pm:3507)
        self.write_line(indent, f"node dummy {node.name}")

        # Write parent if this node has one (we need to find parent name from model)
        # For now, we'll skip parent writing as it requires model node mapping
        # This is a limitation - in MDLOps, animation nodes reference model nodes by index

        # Write controllers (vendor/mdlops/MDLOpsM.pm:3510-3553)
        for controller in node.controllers:
            self._write_controller(indent + 1, controller)

        # Write children
        for child in node.children:
            self._write_animation_node(indent, child)

        self.write_line(indent, "endnode")


class MDLAsciiReader:
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
        # Open the file and seek to offset
        if isinstance(source, (str, bytes)):
            with open(source, "r", encoding="utf-8", errors="ignore") as f:
                if offset > 0:
                    f.seek(offset)
                content = f.read(size if size > 0 else None)
                self._reader = io.StringIO(content)
        elif isinstance(source, io.TextIOBase):
            self._reader = source
            if offset > 0:
                self._reader.seek(offset)
        else:
            # Try to read as binary and decode
            reader = BinaryReader.from_auto(source, offset)
            content = reader.read_bytes(size if size > 0 else reader.size())
            self._reader = io.StringIO(content.decode("utf-8", errors="ignore"))

        self._mdl: MDL = MDL()
        self._node_index: dict[str, int] = {"null": -1}
        self._nodes: list[MDLNode] = []
        self._current_node: MDLNode | None = None
        self._is_geometry = False
        self._is_animation = False
        self._in_node = False
        self._current_anim_num = 0
        self._task = ""
        self._task_count = 0
        self._task_total = 0

    def load(self) -> MDL:
        """Load the ASCII MDL file.

        Returns:
            The loaded MDL instance

        Reference: vendor/mdlops/MDLOpsM.pm:3916-5970
        """
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
        for line in self._reader:
            line = line.rstrip()
            if not line or line.strip().startswith("#"):
                continue

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
                self._parse_node(line)
            elif self._in_node:
                self._parse_node_data(line)
            elif re.match(r"^\s*bmin\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE) and not self._in_node:
                match = re.match(r"^\s*bmin\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE)
                if match:
                    self._mdl.bmin = Vector3(float(match.group(1)), float(match.group(2)), float(match.group(3)))
            elif re.match(r"^\s*bmax\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE) and not self._in_node:
                match = re.match(r"^\s*bmax\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE)
                if match:
                    self._mdl.bmax = Vector3(float(match.group(1)), float(match.group(2)), float(match.group(3)))
            elif re.match(r"^\s*radius\s+(\S+)", line, re.IGNORECASE) and not self._in_node:
                match = re.match(r"^\s*radius\s+(\S+)", line, re.IGNORECASE)
                if match:
                    self._mdl.radius = float(match.group(1))

        # Build node hierarchy
        self._build_node_hierarchy()

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
            node.aabb = MDLWalkmesh()
        elif node_type == MDLNodeType.SABER:
            node.saber = MDLSaber()
        elif node_type in (MDLNodeType.TRIMESH, MDLNodeType.DANGLYMESH):
            node.mesh = MDLMesh()
            if node_type == MDLNodeType.DANGLYMESH:
                node.mesh = MDLDangly()

        self._nodes.append(node)
        self._node_index[node_name.lower()] = len(self._nodes) - 1
        self._current_node = node
        self._in_node = True
        self._task = ""

    def _parse_node_data(self, line: str) -> None:
        """Parse data within a node.

        Reference: vendor/mdlops/MDLOpsM.pm:4222-4644
        """
        if not self._current_node:
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
                parent_name = match.group(1).lower()
                self._current_node.parent_id = self._node_index.get(parent_name, -1)
            return

        # Parse position
        if re.match(r"^\s*position\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*position\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE)
            if match:
                self._current_node.position = Vector3(
                    float(match.group(1)),
                    float(match.group(2)),
                    float(match.group(3)),
                )
            return

        # Parse orientation
        if re.match(r"^\s*orientation\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*orientation\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE)
            if match:
                self._current_node.orientation = Vector4(
                    float(match.group(1)),
                    float(match.group(2)),
                    float(match.group(3)),
                    float(match.group(4)),
                )
            return

        # Parse controllers
        if self._parse_controller(line):
            return

        # Parse mesh data
        if self._current_node.mesh:
            if self._parse_mesh_data(line):
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

        # Get node type flags
        node_flags = self._current_node.get_flags()
        node_type_value = int(node_flags)

        # Check for keyed controllers (vendor/mdlops/MDLOpsM.pm:3760-3802)
        for flag_type in [NODE_HAS_LIGHT, NODE_HAS_EMITTER, NODE_HAS_MESH, NODE_HAS_HEADER]:
            if node_type_value & flag_type:
                controllers = _CONTROLLER_NAMES.get(flag_type, {})
                for controller_id, controller_name in controllers.items():
                    # Check for keyed controller (e.g., "positionkey", "orientationbezierkey")
                    keyed_pattern = rf"^\s*{re.escape(controller_name)}(bezier)?key"
                    if re.match(keyed_pattern, line, re.IGNORECASE):
                        match = re.match(keyed_pattern, line, re.IGNORECASE)
                        is_bezier = match and match.group(1) and match.group(1).lower() == "bezier"
                        # Check for old format with count: "positionkey 4"
                        count_match = re.search(r"key\s+(\d+)$", line, re.IGNORECASE)
                        total = int(count_match.group(1)) if count_match else 0

                        # Read keyframe data
                        rows: list[MDLControllerRow] = []
                        controller_type = _CONTROLLER_NAME_TO_TYPE.get(controller_name, MDLControllerType.INVALID)

                        # Read rows until endlist or count reached
                        for _ in range(total if total > 0 else 10000):  # Large limit for safety
                            try:
                                row_line = next(self._reader).strip()
                                if not row_line or re.match(r"^\s*endlist", row_line, re.IGNORECASE):
                                    break

                                # Parse row data
                                parts = row_line.split()
                                if not parts:
                                    break

                                time = float(parts[0])
                                data = [float(x) for x in parts[1:]]

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
                            data = [float(x) for x in parts[1:]]

                            # Special handling for orientation
                            controller_type = _CONTROLLER_NAME_TO_TYPE.get(controller_name, MDLControllerType.INVALID)
                            if controller_type == MDLControllerType.ORIENTATION and len(data) == 4:
                                data = _aa_to_quaternion(data)

                            rows = [MDLControllerRow(0.0, data)]
                            controller = MDLController(controller_type, rows, False)
                            self._current_node.controllers.append(controller)
                        return True

        return False

    def _parse_mesh_data(self, line: str) -> bool:
        """Parse mesh-specific data.

        Reference: vendor/mdlops/MDLOpsM.pm:4304-4413
        """
        if not self._current_node or not self._current_node.mesh:
            return False

        mesh = self._current_node.mesh

        # Parse ambient color
        if re.match(r"^\s*ambient\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*ambient\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE)
            if match:
                mesh.ambient = Color(
                    float(match.group(1)),
                    float(match.group(2)),
                    float(match.group(3)),
                )
            return True

        # Parse diffuse color
        if re.match(r"^\s*diffuse\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*diffuse\s+(\S+)\s+(\S+)\s+(\S+)", line, re.IGNORECASE)
            if match:
                mesh.diffuse = Color(
                    float(match.group(1)),
                    float(match.group(2)),
                    float(match.group(3)),
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

        # Parse task data (verts, faces, tverts)
        if self._task:
            return self._parse_task_data(line)

        # Parse skin data
        if isinstance(mesh, MDLSkin):
            if self._parse_skin_data(line):
                return True

        # Parse dangly data
        if isinstance(mesh, MDLDangly):
            if self._parse_dangly_data(line):
                return True

        return False

    def _parse_task_data(self, line: str) -> bool:
        """Parse data for current task (verts, faces, tverts, etc.).

        Reference: vendor/mdlops/MDLOpsM.pm:4459-4643
        """
        if not self._current_node or not self._current_node.mesh:
            return False

        mesh = self._current_node.mesh

        if self._task == "verts":
            # Parse vertex: "index x y z [nx ny nz] [u v] [u2 v2]"
            # Reference: vendor/mdlops/MDLOpsM.pm:4468-4471
            parts = line.split()
            if len(parts) >= 4:
                idx = int(parts[0])
                pos = Vector3(float(parts[1]), float(parts[2]), float(parts[3]))
                mesh.vertex_positions.append(pos)

                # Optional normal
                if len(parts) >= 7:
                    normal = Vector3(float(parts[4]), float(parts[5]), float(parts[6]))
                    if mesh.vertex_normals is None:
                        mesh.vertex_normals = []
                    while len(mesh.vertex_normals) <= idx:
                        mesh.vertex_normals.append(Vector3.from_null())
                    mesh.vertex_normals[idx] = normal

                # Optional UV1
                if len(parts) >= 9:
                    uv = Vector2(float(parts[7]), float(parts[8]))
                    if mesh.vertex_uv1 is None:
                        mesh.vertex_uv1 = []
                    while len(mesh.vertex_uv1) <= idx:
                        mesh.vertex_uv1.append(Vector2(0, 0))
                    mesh.vertex_uv1[idx] = uv

                # Optional UV2
                if len(parts) >= 11:
                    uv = Vector2(float(parts[9]), float(parts[10]))
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
            if len(parts) >= 6:
                idx = int(parts[0])
                v1 = int(parts[1])
                v2 = int(parts[2])
                v3 = int(parts[3])
                surface_material = int(parts[4])
                smoothing_group = int(parts[5])

                # Check for magnusll format with extra tvert indices (parts[8], parts[9], parts[10])
                if len(parts) >= 11:
                    # magnusll format - ignore extra indices for now
                    pass

                face = MDLFace()
                face.v1 = v1
                face.v2 = v2
                face.v3 = v3
                face.material = _pack_face_material(surface_material, smoothing_group)

                mesh.faces.append(face)
                self._task_count += 1
                if self._task_count >= self._task_total:
                    self._task = ""
                return True

        elif self._task == "tverts":
            # Parse texture vertex: "index u v"
            # Reference: vendor/mdlops/MDLOpsM.pm:4551-4554
            parts = line.split()
            if len(parts) >= 3:
                idx = int(parts[0])
                uv = Vector2(float(parts[1]), float(parts[2]))
                if mesh.vertex_uv1 is None:
                    mesh.vertex_uv1 = []
                while len(mesh.vertex_uv1) <= idx:
                    mesh.vertex_uv1.append(Vector2(0, 0))
                mesh.vertex_uv1[idx] = uv
                self._task_count += 1
                if self._task_count >= self._task_total:
                    self._task = ""
                return True

        elif self._task == "tverts1":
            # Parse texture vertex for second texture: "index u v"
            # Reference: vendor/mdlops/MDLOpsM.pm:4555-4558
            parts = line.split()
            if len(parts) >= 3:
                idx = int(parts[0])
                uv = Vector2(float(parts[1]), float(parts[2]))
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
        if not self._current_node or not isinstance(self._current_node.mesh, MDLSkin):
            return False

        skin = self._current_node.mesh

        # Parse bones declaration
        if re.match(r"^\s*bones\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*bones\s+(\S+)", line, re.IGNORECASE)
            if match:
                self._task = "bones"
                self._task_total = int(match.group(1))
                self._task_count = 0
                skin.qbones = []
                skin.tbones = []
                skin.bone_indices = []
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
                qbone = Vector4(float(parts[2]), float(parts[3]), float(parts[4]), float(parts[5]))
                tbone = Vector3(float(parts[6]), float(parts[7]), float(parts[8]))

                # Update bone_indices tuple (need to convert to list, modify, convert back)
                # Update bone_indices list
                if not hasattr(skin, 'bone_indices') or skin.bone_indices is None:
                    skin.bone_indices = []
                bone_list = list(skin.bone_indices) if isinstance(skin.bone_indices, (list, tuple)) else []
                while len(bone_list) <= idx:
                    bone_list.append(0)
                bone_list[idx] = bone_idx
                skin.bone_indices = bone_list

                if not hasattr(skin, 'qbones') or skin.qbones is None:
                    skin.qbones = []
                if not hasattr(skin, 'tbones') or skin.tbones is None:
                    skin.tbones = []
                skin.qbones.append(qbone)
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
                # Parse bone-weight pairs
                bone_hash: dict[int, float] = {}
                i = 0
                while i < len(parts) - 1:
                    bone_idx = int(parts[i])
                    weight = float(parts[i + 1])
                    bone_hash[bone_idx] = weight
                    i += 2
                    if i >= len(parts) - 1:
                        break

                # Sort by bone index and create bone vertex
                sorted_bones = sorted(bone_hash.keys())
                bone_vertex = MDLBoneVertex()
                bone_vertex.vertex_indices = tuple(float(b) if b in sorted_bones[:4] else -1.0 for b in range(4))
                bone_vertex.vertex_weights = tuple(bone_hash.get(sorted_bones[i], 0.0) if i < len(sorted_bones) else 0.0 for i in range(4))

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
        if not self._current_node or not isinstance(self._current_node.mesh, MDLDangly):
            return False

        dangly = self._current_node.mesh

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

        if re.match(r"^\s*flareradius\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*flareradius\s+(\S+)", line, re.IGNORECASE)
            if match:
                light.flare_radius = float(match.group(1))
            return True

        if re.match(r"^\s*lightpriority\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*lightpriority\s+(\S+)", line, re.IGNORECASE)
            if match:
                light.light_priority = int(match.group(1))
            return True

        if re.match(r"^\s*ambientonly\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*ambientonly\s+(\S+)", line, re.IGNORECASE)
            if match:
                light.ambient_only = int(match.group(1))
            return True

        if re.match(r"^\s*shadow\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*shadow\s+(\S+)", line, re.IGNORECASE)
            if match:
                light.shadow = int(match.group(1))
            return True

        if re.match(r"^\s*flare\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*flare\s+(\S+)", line, re.IGNORECASE)
            if match:
                light.flare = int(match.group(1))
            return True

        if re.match(r"^\s*fadinglight\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*fadinglight\s+(\S+)", line, re.IGNORECASE)
            if match:
                light.fading_light = int(match.group(1))
            return True

        # Parse flare data arrays
        if re.match(r"^\s*(flarepositions|flaresizes|texturenames)\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*(flarepositions|flaresizes|texturenames)\s+(\S+)", line, re.IGNORECASE)
            if match:
                task_name = match.group(1).lower()
                count = int(match.group(2))
                if count > 0:
                    self._task = task_name
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
                light.flare_positions.append(float(parts[0]))
                self._task_count += 1
                if self._task_count >= self._task_total:
                    self._task = ""
                return True

        if self._task == "flaresizes":
            parts = line.split()
            if parts:
                light.flare_sizes.append(float(parts[0]))
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
                light.flare_color_shifts.append([float(parts[0]), float(parts[1]), float(parts[2])])
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
        emitter_props = {
            "deadspace": ("dead_space", float),
            "blastradius": ("blast_radius", float),
            "blastlength": ("blast_length", float),
            "numbranches": ("branch_count", int),
            "controlptsmoothing": ("control_point_smoothing", float),
            "xgrid": ("x_grid", int),
            "ygrid": ("y_grid", int),
            "spawntype": ("spawn_type", int),
            "update": ("update", str),
            "render": ("render", str),
            "blend": ("blend", str),
            "texture": ("texture", str),
            "chunkname": ("chunk_name", str),
            "twosidedtex": ("two_sided_texture", int),
            "loop": ("loop", int),
            "renderorder": ("render_order", int),
            "m_bframeblending": ("frame_blender", int),
            "m_sdepthtexturename": ("depth_texture", str),
        }

        for prop_name, (attr_name, attr_type) in emitter_props.items():
            pattern = rf"^\s*{re.escape(prop_name)}\s+(\S+)"
            if re.match(pattern, line, re.IGNORECASE):
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    value = match.group(1)
                    if attr_type is int:
                        setattr(emitter, attr_name, int(value))
                    elif attr_type is float:
                        setattr(emitter, attr_name, float(value))
                    else:
                        setattr(emitter, attr_name, value)
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

        if re.match(r"^\s*refmodel\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*refmodel\s+(\S+)", line, re.IGNORECASE)
            if match:
                reference.model = match.group(1)
            return True

        if re.match(r"^\s*reattachable\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*reattachable\s+(\S+)", line, re.IGNORECASE)
            if match:
                reference.reattachable = int(match.group(1)) != 0
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

        if re.match(r"^\s*saberlength\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*saberlength\s+(\S+)", line, re.IGNORECASE)
            if match:
                saber.saber_length = float(match.group(1))
            return True

        if re.match(r"^\s*saberwidth\s+(\S+)", line, re.IGNORECASE):
            match = re.match(r"^\s*saberwidth\s+(\S+)", line, re.IGNORECASE)
            if match:
                saber.saber_width = float(match.group(1))
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
            # Check if line has data: "aabb index x y z ..."
            parts = line.split()
            if len(parts) >= 8:
                # Has data on same line
                aabb_node = MDLNode()
                aabb_node.position = Vector3(float(parts[2]), float(parts[3]), float(parts[4]))
                walkmesh.aabbs.append(aabb_node)
                self._task = "aabb"
                self._task_count = 1
            else:
                # Just declaration, data follows
                self._task = "aabb"
                self._task_count = 0
            return True

        # Parse aabb data
        if self._task == "aabb":
            # Format: "index x y z msp plane left right"
            # Reference: vendor/mdlops/MDLOpsM.pm:4624-4627
            parts = line.split()
            if len(parts) >= 8:
                aabb_node = MDLNode()
                aabb_node.position = Vector3(float(parts[1]), float(parts[2]), float(parts[3]))
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

        # Set root node (first node or node with parent_id == -1)
        root_node = None
        for node in self._nodes:
            if node.parent_id == -1:
                root_node = node
                break

        if not root_node and self._nodes:
            root_node = self._nodes[0]
            root_node.parent_id = -1

        if root_node:
            self._mdl.root = root_node

        # Build parent-child relationships
        for node in self._nodes:
            if node.parent_id >= 0 and node.parent_id < len(self._nodes):
                parent = self._nodes[node.parent_id]
                parent.children.append(node)
