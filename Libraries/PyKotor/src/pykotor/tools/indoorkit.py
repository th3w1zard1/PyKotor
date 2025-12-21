from __future__ import annotations

import json
import re

from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.bwm import read_bwm
from pykotor.resource.generics.utd import read_utd
from utility.common.geometry import Vector3
from utility.common.more_collections import CaseInsensitiveDict

if TYPE_CHECKING:
    import os

    from pykotor.resource.formats.bwm import BWM
    from pykotor.resource.generics.utd import UTD


class Kit:
    """Holocron indoor kit data (headless).

    This is a migrated, headless version of `toolset.data.indoorkit.Kit` suitable for library/CLI use.
    """

    def __init__(self, name: str, kit_id: str):
        self.name: str = name
        self.id: str = kit_id
        self.components: list[KitComponent] = []
        self.doors: list[KitDoor] = []
        self.textures: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.lightmaps: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.txis: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.always: dict[Path, bytes] = {}
        self.side_padding: dict[int, dict[int, MDLMDXTuple]] = {}
        self.top_padding: dict[int, dict[int, MDLMDXTuple]] = {}
        self.skyboxes: dict[str, MDLMDXTuple] = {}


class KitComponent:
    def __init__(self, kit: Kit, name: str, component_id: str, bwm: "BWM", mdl: bytes, mdx: bytes):
        self.kit: Kit = kit
        self.id: str = component_id
        self.name: str = name
        self.hooks: list[KitComponentHook] = []

        self.bwm: "BWM" = bwm
        self.mdl: bytes = mdl
        self.mdx: bytes = mdx


class KitComponentHook:
    def __init__(self, position: Vector3, rotation: float, edge: int, door: "KitDoor"):
        self.position: Vector3 = position
        self.rotation: float = rotation
        self.edge: int = edge
        self.door: KitDoor = door


class KitDoor:
    def __init__(self, utd_k1: "UTD", utd_k2: "UTD", width: float, height: float):
        self.utdK1: UTD = utd_k1
        self.utdK2: UTD = utd_k2
        self.width: float = width
        self.height: float = height


class MDLMDXTuple(NamedTuple):
    mdl: bytes
    mdx: bytes


_NUM_RE = re.compile(r"(\d+)")


def _get_nums(s: str) -> list[int]:
    """Extract integers from a string in order (Toolset-compatible)."""
    return [int(m.group(1)) for m in _NUM_RE.finditer(s)]


def load_kits(path: "os.PathLike | str") -> list[Kit]:
    """Load Holocron indoor kits from disk (headless).

    Expected layout matches Holocron Toolset kits:
    - `<kits>/<kit_id>.json`
    - `<kits>/<kit_id>/...` (folders with resources)
    """
    kits: list[Kit] = []

    kits_path = Path(path)
    if not kits_path.is_dir():
        kits_path.mkdir(parents=True)

    for file in (f for f in kits_path.iterdir() if f.suffix.lower() == ".json"):
        kit_json = json.loads(BinaryReader.load_file(file))
        kit_id = kit_json.get("id") or file.stem
        kit = Kit(kit_json["name"], kit_id)

        always_path = kits_path / kit_id / "always"
        if always_path.is_dir():
            for always_file in always_path.iterdir():
                kit.always[always_file] = BinaryReader.load_file(always_file)

        textures_path = kits_path / kit_id / "textures"
        if textures_path.is_dir():
            for texture_file in (f for f in textures_path.iterdir() if f.suffix.lower() == ".tga"):
                texture = texture_file.stem.upper()
                kit.textures[texture] = BinaryReader.load_file(textures_path / f"{texture}.tga")
                txi_path = textures_path / f"{texture}.txi"
                kit.txis[texture] = BinaryReader.load_file(txi_path) if txi_path.is_file() else b""

        lightmaps_path = kits_path / kit_id / "lightmaps"
        if lightmaps_path.is_dir():
            for lightmap_file in (f for f in lightmaps_path.iterdir() if f.suffix.lower() == ".tga"):
                lightmap = lightmap_file.stem.upper()
                kit.lightmaps[lightmap] = BinaryReader.load_file(lightmaps_path / f"{lightmap}.tga")
                txi_path = lightmaps_path / f"{lightmap_file.stem}.txi"
                kit.txis[lightmap] = BinaryReader.load_file(txi_path) if txi_path.is_file() else b""

        skyboxes_path = kits_path / kit_id / "skyboxes"
        if skyboxes_path.is_dir():
            for skybox_resref_str in (f.stem.upper() for f in skyboxes_path.iterdir() if f.suffix.lower() == ".mdl"):
                mdl_path = skyboxes_path / f"{skybox_resref_str}.mdl"
                mdx_path = skyboxes_path / f"{skybox_resref_str}.mdx"
                mdl, mdx = BinaryReader.load_file(mdl_path), BinaryReader.load_file(mdx_path)
                kit.skyboxes[skybox_resref_str] = MDLMDXTuple(mdl, mdx)

        doorway_path = kits_path / kit_id / "doorway"
        if doorway_path.is_dir():
            for padding_id in (f.stem for f in doorway_path.iterdir() if f.suffix.lower() == ".mdl"):
                mdl_path = doorway_path / f"{padding_id}.mdl"
                mdx_path = doorway_path / f"{padding_id}.mdx"
                mdl, mdx = BinaryReader.load_file(mdl_path), BinaryReader.load_file(mdx_path)
                nums = _get_nums(padding_id)
                if len(nums) < 2:
                    continue
                door_id, padding_size = nums[0], nums[1]

                if padding_id.lower().startswith("side"):
                    if door_id not in kit.side_padding:
                        kit.side_padding[door_id] = {}
                    kit.side_padding[door_id][padding_size] = MDLMDXTuple(mdl, mdx)
                if padding_id.lower().startswith("top"):
                    if door_id not in kit.top_padding:
                        kit.top_padding[door_id] = {}
                    kit.top_padding[door_id][padding_size] = MDLMDXTuple(mdl, mdx)

        for door_json in kit_json.get("doors", []):
            utd_k1 = read_utd(kits_path / kit_id / f'{door_json["utd_k1"]}.utd')
            utd_k2 = read_utd(kits_path / kit_id / f'{door_json["utd_k2"]}.utd')
            door = KitDoor(utd_k1, utd_k2, door_json["width"], door_json["height"])
            kit.doors.append(door)

        for component_json in kit_json.get("components", []):
            name = component_json["name"]
            component_id = component_json["id"]
            bwm = read_bwm(kits_path / kit_id / f"{component_id}.wok")
            mdl = BinaryReader.load_file(kits_path / kit_id / f"{component_id}.mdl")
            mdx = BinaryReader.load_file(kits_path / kit_id / f"{component_id}.mdx")
            component = KitComponent(kit, name, component_id, bwm, mdl, mdx)

            for hook_json in component_json.get("doorhooks", []):
                position = Vector3(hook_json["x"], hook_json["y"], hook_json["z"])
                rotation = hook_json["rotation"]
                door = kit.doors[hook_json["door"]]
                edge = hook_json["edge"]
                component.hooks.append(KitComponentHook(position, rotation, edge, door))

            kit.components.append(component)

        kits.append(kit)

    return kits


