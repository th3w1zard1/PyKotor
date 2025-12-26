from __future__ import annotations

"""Indoor map workflows (headless helpers).

This module provides **workflow functions** around the core model in
`pykotor.common.indoormap`:
- Build a `.mod` from an `.indoor` file (with explicit on-disk kits)
- Build a `.mod` from an `.indoor` file using implicit `ModuleKit`
- Extract an `.indoor` from a module either:
  - fast-path: embedded `indoormap.txt` payload
  - full reverse-extraction: fit WOK walkmeshes back to kit components

Keep UI/Qt out of this module. Toolset uses these functions indirectly via its UI.
"""

import math

from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING

from loggerplus import RobustLogger
from pykotor.common.indoorkit import Kit, KitComponent
from pykotor.common.indoormap import INDOOR_EMBED_RESREF, INDOOR_EMBED_RESTYPE, IndoorMap, IndoorMapRoom, _RoomTransformMatch
from pykotor.common.misc import Game
from pykotor.common.module import Module, ModuleResource
from pykotor.common.modulekit import ModuleKit, ModuleKitManager
from pykotor.extract.capsule import Capsule
from pykotor.extract.installation import Installation
from pykotor.resource.formats.bwm import BWM, read_bwm
from pykotor.resource.formats.lyt import LYT
from pykotor.resource.generics.are import ARE
from pykotor.resource.generics.ifo import IFO
from pykotor.resource.type import ResourceType
from pykotor.tools.indoorkit import load_kits
from pykotor.tools.module import prioritize_module_files
from pykotor.tools.path import CaseAwarePath
from utility.common.geometry import Vector3

if TYPE_CHECKING:
    import os


def build_mod_from_indoor_file(
    indoor_path: os.PathLike | str,
    *,
    output_mod_path: os.PathLike | str,
    installation_path: os.PathLike | str,
    kits_path: os.PathLike | str,
    game: Game | None,
    module_id: str | None = None,
    loadscreen_path: os.PathLike | str | None = None,
) -> None:
    """Build a `.mod` from an `.indoor` file using **explicit kits** from disk."""
    installation = Installation(CaseAwarePath(installation_path))
    kits = load_kits(kits_path)
    indoor_map = IndoorMap()
    indoor_map.load(Path(indoor_path).read_bytes(), kits)
    if module_id:
        indoor_map.module_id = module_id
    indoor_map.build(installation, kits, output_mod_path, game_override=game, loadscreen_path=loadscreen_path)


def build_mod_from_indoor_file_modulekit(
    indoor_path: os.PathLike | str,
    *,
    output_mod_path: os.PathLike | str,
    installation_path: os.PathLike | str,
    game: Game | None,
    module_id: str | None = None,
    loadscreen_path: os.PathLike | str | None = None,
) -> None:
    """Build a `.mod` from an `.indoor` file using **implicit ModuleKit** (no on-disk kits)."""
    installation = Installation(CaseAwarePath(installation_path))
    module_kit_manager = ModuleKitManager(installation)
    indoor_map = IndoorMap()
    missing = indoor_map.load(Path(indoor_path).read_bytes(), [], module_kit_manager)
    if missing:
        msg = f"Indoor map references missing ModuleKit rooms/components: {missing[:5]}"
        raise ValueError(msg)
    if module_id:
        indoor_map.module_id = module_id
    # For implicit-kit builds, just pass the kits referenced by the rooms (deduped by id).
    kits: list[Kit] = []
    seen: set[str] = set()
    for room in indoor_map.rooms:
        kit = room.component.kit
        if kit.id in seen:
            continue
        seen.add(kit.id)
        kits.append(kit)
    indoor_map.build(installation, kits, output_mod_path, game_override=game, loadscreen_path=loadscreen_path)


def extract_indoor_from_module_as_modulekit(
    module_name: str,
    *,
    installation_path: os.PathLike | str,
    game: Game | None,
    logger: RobustLogger | None = None,
) -> IndoorMap:
    """Extract an `IndoorMap` by treating the module as an implicit kit (`ModuleKit`).

    This is the “implicit-kit extraction” path, used by `kotorcli indoor-extract --implicit-kit`.
    """
    if logger is None:
        logger = RobustLogger()

    module_root = Path(module_name).stem.lower()
    installation = Installation(CaseAwarePath(installation_path))
    module_kit_manager = ModuleKitManager(installation)
    kit = module_kit_manager.get_module_kit(module_root)
    if not kit.ensure_loaded():
        msg = f"Failed to load module '{module_root}' as ModuleKit"
        raise ValueError(msg)

    indoor = IndoorMap(module_id=module_root)
    for comp in kit.components:
        pos = comp.default_position
        indoor.rooms.append(IndoorMapRoom(comp, Vector3(pos.x, pos.y, pos.z), rotation=0.0, flip_x=False, flip_y=False))
    indoor.rebuild_room_connections()
    logger.debug("ModuleKit extraction produced %d room(s) for '%s'", len(indoor.rooms), module_root)
    return indoor


def extract_indoor_from_module_files(
    module_files: list[os.PathLike | str],
    *,
    output_indoor_path: os.PathLike | str,
) -> bool:
    """Extract embedded `.indoor` JSON from module containers.

    Uses canonical composite module loading priority:
    - `.mod` files are prioritized first
    - If no `.mod` exists, combines `.rim`, `_s.rim`, and `_dlg.erf` files

    Returns True if embedded data was found and written.
    """
    output_indoor_path_obj = Path(output_indoor_path).absolute()
    # Use canonical composite module loading priority logic
    prioritized_files = prioritize_module_files(module_files)

    for container in prioritized_files:
        try:
            # Check if it's a capsule file we can read
            if container.suffix.lower() in {".mod", ".erf", ".rim", ".sav", ".hak"}:
                cap = Capsule(container)
                if cap.contains(INDOOR_EMBED_RESREF, INDOOR_EMBED_RESTYPE):
                    data = cap.resource(INDOOR_EMBED_RESREF, INDOOR_EMBED_RESTYPE)
                    if data is None:
                        raise ValueError(f"Embedded indoor data not found in {container}")
                    output_indoor_path_obj.write_bytes(data)
                    return True
        except Exception:  # noqa: BLE001
            continue
    return False


def _centroid(points: list[Vector3]) -> Vector3:
    if not points:
        return Vector3.from_null()
    sx = sum(p.x for p in points)
    sy = sum(p.y for p in points)
    sz = sum(p.z for p in points)
    n = float(len(points))
    return Vector3(sx / n, sy / n, sz / n)


def _apply_flip(points: list[Vector3], flip_x: bool, flip_y: bool) -> list[Vector3]:
    if not flip_x and not flip_y:
        return [Vector3(p.x, p.y, p.z) for p in points]
    out: list[Vector3] = []
    for p in points:
        out.append(Vector3(-p.x if flip_x else p.x, -p.y if flip_y else p.y, p.z))
    return out


def _apply_rotate_z(
    points: list[Vector3],
    rotation_deg: float,
) -> list[Vector3]:
    if abs(rotation_deg) < 1e-12:
        return [Vector3(p.x, p.y, p.z) for p in points]
    cos = math.cos(math.radians(rotation_deg))
    sin = math.sin(math.radians(rotation_deg))
    out: list[Vector3] = []
    for p in points:
        out.append(Vector3(p.x * cos - p.y * sin, p.x * sin + p.y * cos, p.z))
    return out


def _apply_translate(
    points: list[Vector3],
    translation: Vector3,
) -> list[Vector3]:
    if translation.x == 0 and translation.y == 0 and translation.z == 0:
        return [Vector3(p.x, p.y, p.z) for p in points]
    return [Vector3(p.x + translation.x, p.y + translation.y, p.z + translation.z) for p in points]


def _rms_error(a: list[Vector3], b: list[Vector3]) -> float:
    if len(a) != len(b) or not a:
        return float("inf")
    acc = 0.0
    for p, q in zip(a, b):
        dx = p.x - q.x
        dy = p.y - q.y
        dz = p.z - q.z
        acc += dx * dx + dy * dy + dz * dz
    return math.sqrt(acc / float(len(a)))


def infer_room_transform(
    base_vertices: list[Vector3],
    instance_vertices: list[Vector3],
    *,
    max_rms: float = 1e-3,
) -> tuple[bool, bool, float, Vector3, float] | None:
    """Infer (flip_x, flip_y, rotation_deg, translation) mapping base->instance.

    Assumes the instance was produced as:
      base -> flip_x/flip_y -> rotate around Z (degrees) -> translate (x,y,z)

    This is the same transform pipeline used by the indoor builder.

    Notes:
    - Uses an orthogonal Procrustes solve in 2D (XY) with assumed vertex correspondence order.
    - Returns the best match under `max_rms`, or None if no candidate meets tolerance.
    """
    if len(base_vertices) != len(instance_vertices) or not base_vertices:
        return None

    _base_centroid: Vector3 = _centroid(base_vertices)
    inst_centroid: Vector3 = _centroid(instance_vertices)

    best: tuple[bool, bool, float, Vector3, float] | None = None

    for flip_x in (False, True):
        for flip_y in (False, True):
            flipped = _apply_flip(base_vertices, flip_x, flip_y)
            flipped_centroid = _centroid(flipped)

            # Center the points
            a_sum = 0.0
            b_sum = 0.0
            for p, q in zip(flipped, instance_vertices):
                px = p.x - flipped_centroid.x
                py = p.y - flipped_centroid.y
                qx = q.x - inst_centroid.x
                qy = q.y - inst_centroid.y
                a_sum += px * qx + py * qy
                b_sum += px * qy - py * qx

            rotation_deg = math.degrees(math.atan2(b_sum, a_sum))

            # Translation: inst_centroid - R * flipped_centroid
            rot_centroid = _apply_rotate_z([flipped_centroid], rotation_deg)[0]
            translation = Vector3(inst_centroid.x - rot_centroid.x, inst_centroid.y - rot_centroid.y, inst_centroid.z - rot_centroid.z)

            transformed = _apply_translate(_apply_rotate_z(flipped, rotation_deg), translation)
            err = _rms_error(transformed, instance_vertices)
            if err <= max_rms and (best is None or err < best[4]):
                best = (flip_x, flip_y, rotation_deg, translation, err)

    return best


def infer_room_transform_bwm(
    base_bwm: BWM,
    instance_bwm: BWM,
    *,
    max_rms: float = 1e-3,
) -> tuple[bool, bool, float, Vector3, float] | None:
    """Infer transform between BWMs while accounting for BWM.flip() face/vertex reordering.

    BWM.flip() (when x XOR y) reverses face winding by swapping v1<->v3 per face, which changes
    the vertex iteration order produced by `BWM.vertices()`. For reverse-extraction we need to
    consider that when inferring transforms, otherwise odd-flip cases frequently fail.
    """
    if not base_bwm.faces or not instance_bwm.faces:
        return None

    best: tuple[bool, bool, float, Vector3, float] | None = None

    instance_vertices = instance_bwm.vertices()
    if not instance_vertices:
        return None

    for flip_x in (False, True):
        for flip_y in (False, True):
            base_copy = deepcopy(base_bwm)
            base_copy.flip(flip_x, flip_y)
            base_vertices = base_copy.vertices()
            inferred = infer_room_transform(base_vertices, instance_vertices, max_rms=max_rms)
            if inferred is None:
                continue
            if best is None or inferred[4] < best[4]:
                best = (flip_x, flip_y, inferred[2], inferred[3], inferred[4])

    return best


def extract_indoor_from_module_name(
    module_name: str,
    *,
    installation_path: os.PathLike | str,
    kits_path: os.PathLike | str,
    game: Game | None,
    strict: bool = True,
    max_rms: float = 1e-3,
    logger: RobustLogger | None = None,
    module_kit_manager: ModuleKitManager | None = None,
) -> IndoorMap:
    """Reverse-engineer a `.indoor` map from a module by matching room WOKs back to kit components.

    This is the "full" extraction mode (no reliance on embedded `indoormap.txt`).
    It attempts to reconstruct:
    - room positions (from LYT)
    - room rotations + flip flags (by fitting kit-component walkmesh vertices to room WOK vertices)
    - module lighting/name/warp (from ARE/IFO when present)

    Args:
    ----
        module_name (str): The name of the module to extract the indoor map from.
        installation_path (os.PathLike | str): The path to the installation.
        kits_path (os.PathLike | str): The path to the kits.
        game (Game | None): The game to extract the indoor map for.
        strict (bool): Whether to raise an error if any LYT room cannot be matched to a kit component.
        max_rms (float): The maximum RMS error allowed for a match.
        logger (RobustLogger | None): The logger to use.
        module_kit_manager (ModuleKitManager | None): The module kit manager to use.

    Returns:
    -------
        IndoorMap: The extracted indoor map.

    Processing Logic:
    ----------------
        - Loads the module from the installation path.
        - Loads the kits from the kits path.
        - Loads the module kit manager from the module kit manager path.
        - Loads the module from the module name.
        - Loads the LYT from the module.
        - Loads the ARE from the module.
        - Loads the IFO from the module.
        - Builds the indoor map.
        - Returns the indoor map.
    """
    if logger is None:
        logger = RobustLogger()

    installation: Installation = Installation(CaseAwarePath(installation_path))
    kits: list[Kit] = []
    if str(kits_path):
        kits = load_kits(kits_path)
    if module_kit_manager is not None:
        module_root: str = Installation.get_module_root(module_name)
        mk: ModuleKit = module_kit_manager.get_module_kit(module_root)
        if mk.ensure_loaded():
            kits.append(mk)

    module = Module(module_name, installation, use_dot_mod=True)
    lyt_res: ModuleResource[LYT] | None = module.layout()
    if lyt_res is None or lyt_res.resource() is None:
        raise ValueError(f"Module '{module_name}' has no LYT layout; cannot extract rooms.")
    lyt: LYT | None = lyt_res.resource()
    if lyt is None:
        raise ValueError(f"Module '{module_name}' has no LYT layout; cannot extract rooms.")

    are_res: ModuleResource[ARE] | None = module.are()
    are: ARE | None = None if are_res is None else are_res.resource()
    ifo_res: ModuleResource[IFO] | None = module.ifo()
    ifo: IFO | None = None if ifo_res is None else ifo_res.resource()

    indoor: IndoorMap = IndoorMap()
    indoor.module_id = module.module_id() or "test01"
    if are is not None:
        indoor.name = are.name
        indoor.lighting = are.dynamic_light
    if ifo is not None:
        indoor.warp_point = ifo.entry_position

    # Build candidate pool once; prefilter by vertex count.
    components: list[KitComponent] = [comp for kit in kits for comp in kit.components]
    by_vert_count: dict[int, list[KitComponent]] = {}
    for comp in components:
        vcount = len(comp.bwm.vertices())
        by_vert_count.setdefault(vcount, []).append(comp)

    unmatched: list[str] = []

    for room in lyt.rooms:
        model_name: str = room.model

        # Skip known builder sky room; we attempt to infer skybox later.
        if model_name.lower() == f"{indoor.module_id}_sky".lower():
            continue

        wok_res: ModuleResource[bytes] | None = module.resource(model_name, ResourceType.WOK)
        if wok_res is None:
            unmatched.append(model_name)
            continue
        wok_data: bytes | None = wok_res.data()
        if wok_data is None:
            unmatched.append(model_name)
            continue
        instance_bwm: BWM = read_bwm(wok_data)
        instance_vertices: list[Vector3] = instance_bwm.vertices()
        candidates: list[KitComponent] = by_vert_count.get(len(instance_vertices), [])
        if not candidates:
            unmatched.append(model_name)
            continue

        best_match: _RoomTransformMatch | None = None
        for comp in candidates:
            inferred = infer_room_transform_bwm(comp.bwm, instance_bwm, max_rms=max_rms)
            if inferred is None:
                continue
            flip_x, flip_y, rot_deg, translation, err = inferred
            match = _RoomTransformMatch(comp, flip_x, flip_y, rot_deg, translation, err)
            if best_match is None or match.rms_error < best_match.rms_error:
                best_match = match

        if best_match is None:
            unmatched.append(model_name)
            continue

        room_obj = IndoorMapRoom(
            best_match.component,
            position=Vector3(room.position.x, room.position.y, room.position.z),
            rotation=best_match.rotation_deg,
            flip_x=best_match.flip_x,
            flip_y=best_match.flip_y,
        )

        # If the fitted translation doesn't match LYT position closely, treat it as a walkmesh override
        # and force the indoor room position to LYT position (source of truth for placement).
        # We also store an override walkmesh in local space so a rebuild reproduces the original WOK.
        pos_from_fit: Vector3 = best_match.translation
        lyt_pos: Vector3 = Vector3(room.position.x, room.position.y, room.position.z)
        if pos_from_fit.distance(lyt_pos) > 1e-3:
            # compute local override by inverting the transform
            override: BWM = deepcopy(instance_bwm)
            override.translate(-lyt_pos.x, -lyt_pos.y, -lyt_pos.z)
            override.rotate(-best_match.rotation_deg)
            override.flip(best_match.flip_x, best_match.flip_y)
            room_obj.walkmesh_override = override

        indoor.rooms.append(room_obj)

    if unmatched:
        msg = f"Failed to match {len(unmatched)} LYT room(s) to any kit component: {', '.join(unmatched[:10])}"
        if strict:
            raise ValueError(msg)
        logger.warning(msg)

    indoor.rebuild_room_connections()
    return indoor
