from __future__ import annotations

"""Indoor-kit workflows (headless).

This module loads Holocron Toolset kit folders from disk into the headless data model in
`pykotor.common.indoorkit`.

Qt/Toolset specifics:
- Toolset may show previews; that lives in Toolset code (Qt) and should not be added here.
- This module focuses on deterministic parsing and optional “missing file” reporting.
"""

import json
import re

from pathlib import Path
from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader
from pykotor.common.indoorkit import Kit, KitComponent, KitComponentHook, KitDoor, MDLMDXTuple
from pykotor.resource.formats.bwm import read_bwm
from pykotor.resource.generics.utd import read_utd
from utility.common.geometry import Vector3

if TYPE_CHECKING:
    import os

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


def load_kits_with_missing_files(
    path: "os.PathLike | str",
) -> tuple[list[Kit], list[tuple[str, Path, str]]]:
    """Load kits and also return a list of missing/invalid referenced files.

    This mirrors the Toolset's historical `load_kits()` behavior (minus Qt preview loading),
    so Toolset UI can report missing resources while keeping all non-Qt logic in PyKotor.
    """
    kits: list[Kit] = []
    missing_files: list[tuple[str, Path, str]] = []

    kits_path = Path(path).absolute()
    if not kits_path.is_dir():
        kits_path.mkdir(parents=True)

    for file in (f for f in kits_path.iterdir() if f.suffix.lower() == ".json"):
        try:
            kit_json_raw = json.loads(BinaryReader.load_file(file))
        except Exception:
            continue
        if not isinstance(kit_json_raw, dict):
            continue
        if "name" not in kit_json_raw:
            continue

        kit_id = str(kit_json_raw.get("id") or file.stem)
        kit_name = str(kit_json_raw["name"])
        kit = Kit(kit_name, kit_id)

        always_path = kits_path / kit_id / "always"
        if always_path.is_dir():
            for always_file in always_path.iterdir():
                try:
                    kit.always[always_file] = BinaryReader.load_file(always_file)
                except FileNotFoundError:
                    missing_files.append((kit_name, always_file, "always file"))

        textures_path = kits_path / kit_id / "textures"
        if textures_path.is_dir():
            for texture_file in (f for f in textures_path.iterdir() if f.suffix.lower() == ".tga"):
                texture = texture_file.stem.upper()
                try:
                    kit.textures[texture] = BinaryReader.load_file(texture_file)
                except FileNotFoundError:
                    missing_files.append((kit_name, texture_file, "texture"))
                txi_path = textures_path / f"{texture}.txi"
                kit.txis[texture] = BinaryReader.load_file(txi_path) if txi_path.is_file() else b""

        lightmaps_path = kits_path / kit_id / "lightmaps"
        if lightmaps_path.is_dir():
            for lightmap_file in (f for f in lightmaps_path.iterdir() if f.suffix.lower() == ".tga"):
                lightmap = lightmap_file.stem.upper()
                try:
                    kit.lightmaps[lightmap] = BinaryReader.load_file(lightmap_file)
                except FileNotFoundError:
                    missing_files.append((kit_name, lightmap_file, "lightmap"))
                txi_path = lightmaps_path / f"{lightmap_file.stem}.txi"
                kit.txis[lightmap] = BinaryReader.load_file(txi_path) if txi_path.is_file() else b""

        skyboxes_path = kits_path / kit_id / "skyboxes"
        if skyboxes_path.is_dir():
            for skybox_resref_str in (f.stem.upper() for f in skyboxes_path.iterdir() if f.suffix.lower() == ".mdl"):
                mdl_path = skyboxes_path / f"{skybox_resref_str}.mdl"
                mdx_path = skyboxes_path / f"{skybox_resref_str}.mdx"
                if not mdl_path.is_file():
                    missing_files.append((kit_name, mdl_path, "skybox model"))
                    continue
                if not mdx_path.is_file():
                    missing_files.append((kit_name, mdx_path, "skybox model"))
                    continue
                kit.skyboxes[skybox_resref_str] = MDLMDXTuple(BinaryReader.load_file(mdl_path), BinaryReader.load_file(mdx_path))

        doorway_path = kits_path / kit_id / "doorway"
        if doorway_path.is_dir():
            for padding_id in (f.stem for f in doorway_path.iterdir() if f.suffix.lower() == ".mdl"):
                mdl_path = doorway_path / f"{padding_id}.mdl"
                mdx_path = doorway_path / f"{padding_id}.mdx"
                if not mdl_path.is_file():
                    missing_files.append((kit_name, mdl_path, "doorway padding"))
                    continue
                if not mdx_path.is_file():
                    missing_files.append((kit_name, mdx_path, "doorway padding"))
                    continue
                nums = _get_nums(padding_id)
                if len(nums) < 2:
                    continue
                door_id, padding_size = nums[0], nums[1]
                tuple_val = MDLMDXTuple(BinaryReader.load_file(mdl_path), BinaryReader.load_file(mdx_path))
                if padding_id.lower().startswith("side"):
                    kit.side_padding.setdefault(door_id, {})[padding_size] = tuple_val
                if padding_id.lower().startswith("top"):
                    kit.top_padding.setdefault(door_id, {})[padding_size] = tuple_val

        for door_json in kit_json_raw.get("doors", []):
            try:
                utd_k1_path = kits_path / kit_id / f'{door_json["utd_k1"]}.utd'
                utd_k2_path = kits_path / kit_id / f'{door_json["utd_k2"]}.utd'
                utd_k1 = read_utd(utd_k1_path)
                utd_k2 = read_utd(utd_k2_path)
            except FileNotFoundError as e:
                missing_files.append((kit_name, Path(e.filename or ""), "door utd"))
                continue
            door = KitDoor(utd_k1, utd_k2, door_json["width"], door_json["height"])
            kit.doors.append(door)

        for component_json in kit_json_raw.get("components", []):
            try:
                name = component_json["name"]
                component_id = component_json["id"]
            except Exception:
                continue

            base = kits_path / kit_id
            wok_path = base / f"{component_id}.wok"
            mdl_path = base / f"{component_id}.mdl"
            mdx_path = base / f"{component_id}.mdx"
            if not wok_path.is_file():
                missing_files.append((kit_name, wok_path, "walkmesh"))
                continue
            if not mdl_path.is_file():
                missing_files.append((kit_name, mdl_path, "model"))
                continue
            if not mdx_path.is_file():
                missing_files.append((kit_name, mdx_path, "model extension"))
                continue

            bwm = read_bwm(wok_path)
            mdl = BinaryReader.load_file(mdl_path)
            mdx = BinaryReader.load_file(mdx_path)
            component = KitComponent(kit, name, component_id, bwm, mdl, mdx)

            for hook_json in component_json.get("doorhooks", []):
                try:
                    position = Vector3(hook_json["x"], hook_json["y"], hook_json["z"])
                    rotation = hook_json["rotation"]
                    door = kit.doors[hook_json["door"]]
                    edge = int(hook_json["edge"])
                except Exception:
                    continue
                component.hooks.append(KitComponentHook(position, rotation, edge, door))

            kit.components.append(component)

        kits.append(kit)

    return kits, missing_files


