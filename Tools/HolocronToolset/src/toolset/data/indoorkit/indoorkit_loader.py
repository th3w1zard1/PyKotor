from __future__ import annotations

import json

from pathlib import Path
from typing import TYPE_CHECKING, Any

from qtpy.QtGui import QColor, QImage, QPainter, QPainterPath

from pykotor.resource.formats.bwm import read_bwm
from pykotor.resource.generics.utd import read_utd
from toolset.data.indoorkit.indoorkit_base import Kit, KitComponent, KitComponentHook, KitDoor, MDLMDXTuple
from toolset.utils.misc import get_nums
from utility.common.geometry import Vector3

if TYPE_CHECKING:
    import os

    from pykotor.resource.formats.bwm import BWM
    from pykotor.resource.generics.utd import UTD


def _recenter_bwm(bwm: "BWM") -> "BWM":
    """Re-center a BWM around (0, 0) so image and hitbox align.
    
    The Indoor Map Builder draws the preview image CENTERED at room.position,
    but translates the walkmesh BY room.position from its original coordinates.
    
    For these to align, the BWM must be centered around (0, 0):
    - If BWM center is at (100, 200) and room.position = (0, 0):
      - Image would be centered at (0, 0)
      - Walkmesh would be centered at (100, 200) after translate
      - MISMATCH! Image and hitbox are in different places.
    
    - After re-centering BWM to (0, 0):
      - Image is centered at room.position
      - Walkmesh is centered at room.position after translate
      - MATCH! Image and hitbox overlap perfectly.
    
    Reference: module_converter.py _recenter_bwm() for implementation details
    Reference: vendor/KotOR.js/src/module/ModuleRoom.ts - rooms use local coords
    Reference: vendor/reone/src/libs/game/object/area.cpp - room positioning
    """
    vertices = list(bwm.vertices())
    if not vertices:
        return bwm
    
    # Calculate current center
    min_x = min(v.x for v in vertices)
    max_x = max(v.x for v in vertices)
    min_y = min(v.y for v in vertices)
    max_y = max(v.y for v in vertices)
    min_z = min(v.z for v in vertices)
    max_z = max(v.z for v in vertices)
    
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    center_z = (min_z + max_z) / 2.0
    
    # Translate all vertices to center around origin
    # Use BWM.translate() which handles all vertices in faces
    bwm.translate(-center_x, -center_y, -center_z)
    
    return bwm


def _create_preview_image_from_bwm(bwm: "BWM") -> QImage:
    """Create a preview image from a walkmesh.
    
    Creates a top-down view of the walkmesh for use as a component preview.
    This method generates an image IDENTICAL to what kit.py generates, then
    mirrors it to match what the Kit loader does when loading from disk.
    
    CRITICAL: Must match kit.py/_generate_component_minimap EXACTLY:
    - 10 pixels per unit scale
    - Format_RGB888 (not RGB32)
    - Minimum 256x256 pixels
    - Y-flip during drawing, then .mirrored() after
    
    Reference: Libraries/PyKotor/src/pykotor/tools/kit.py:_generate_component_minimap
    Reference: module_converter.py _create_preview_image_from_bwm()
    """
    # Collect all vertices to calculate bounding box
    vertices: list[Vector3] = list(bwm.vertices())
    if not vertices:
        # Empty walkmesh - return blank image matching kit.py minimum size
        image = QImage(256, 256, QImage.Format.Format_RGB888)
        image.fill(QColor(0, 0, 0))
        return image.mirrored()  # Mirror to match Kit loader

    # Calculate bounding box (same as kit.py)
    min_x = min(v.x for v in vertices)
    min_y = min(v.y for v in vertices)
    max_x = max(v.x for v in vertices)
    max_y = max(v.y for v in vertices)

    # Add padding (same as kit.py: 5.0 units)
    padding = 5.0
    min_x -= padding
    min_y -= padding
    max_x += padding
    max_y += padding

    # Calculate image dimensions at 10 pixels per unit (matching kit.py exactly)
    PIXELS_PER_UNIT = 10
    width = int((max_x - min_x) * PIXELS_PER_UNIT)
    height = int((max_y - min_y) * PIXELS_PER_UNIT)

    # Ensure minimum size (kit.py uses 256, not 100)
    width = max(width, 256)
    height = max(height, 256)

    # Create image with Format_RGB888 (same as kit.py, NOT RGB32)
    image = QImage(width, height, QImage.Format.Format_RGB888)
    image.fill(QColor(0, 0, 0))

    # Transform from world coordinates to image coordinates
    # Y is flipped because image Y=0 is top, world Y increases upward
    # This matches kit.py exactly
    def world_to_image(v: Vector3) -> tuple[float, float]:
        x = (v.x - min_x) * PIXELS_PER_UNIT
        y = height - (v.y - min_y) * PIXELS_PER_UNIT  # Flip Y
        return x, y

    # Draw walkmesh faces (same logic as kit.py)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    for face in bwm.faces:
        # Determine if face is walkable based on material (same logic as kit.py)
        is_walkable = face.material.value in (1, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 16, 18, 20, 21, 22)
        color = QColor(255, 255, 255) if is_walkable else QColor(128, 128, 128)

        painter.setBrush(color)
        painter.setPen(color)

        # Build path from face vertices
        path = QPainterPath()
        x1, y1 = world_to_image(face.v1)
        x2, y2 = world_to_image(face.v2)
        x3, y3 = world_to_image(face.v3)

        path.moveTo(x1, y1)
        path.lineTo(x2, y2)
        path.lineTo(x3, y3)
        path.closeSubpath()

        painter.drawPath(path)

    painter.end()

    # CRITICAL: Mirror the image to match what Kit loader does!
    # Kit loader: image = QImage(path).mirrored()
    # Without this, the image would be upside down relative to the BWM.
    return image.mirrored()


def load_kits(  # noqa: C901, PLR0912, PLR0915
    path: os.PathLike | str,
) -> tuple[list[Kit], list[tuple[str, Path, str]]]:
    """Loads kits from a given path.

    Args:
    ----
        path: os.PathLike | str: The path to load kits from

    Returns:
    -------
        tuple[list[Kit], list[tuple[str, Path, str]]]: A tuple containing:
            - A list of loaded Kit objects
            - A list of missing files as tuples of (kit_name, file_path, file_type)

    Processing Logic:
    ----------------
        - Loops through files in the path to load kit data
        - Loads kit JSON and populates Kit object
        - Loads always, textures, lightmaps, skyboxes, doors, components
        - Populates KitComponent hooks from JSON
        - Collects missing files instead of failing fast
        - Adds loaded Kit to return list.
    """
    kits: list[Kit] = []
    missing_files: list[tuple[str, Path, str]] = []  # (kit_name, file_path, file_type)

    kits_path = Path(path).absolute()
    if not kits_path.is_dir():
        kits_path.mkdir(parents=True)
    for file in (
        file
        for file in kits_path.iterdir()
        if file.suffix.lower() == ".json"
    ):
        try:
            kit_json_raw: Any = json.loads(file.read_bytes())
        except json.JSONDecodeError:
            # Skip invalid JSON files
            continue
        
        # Skip files that aren't dicts (e.g., available_kits.json which is a list)
        if not isinstance(kit_json_raw, dict):
            continue
        
        # Skip dicts that don't have required kit fields
        if "name" not in kit_json_raw or "id" not in kit_json_raw:
            continue
        
        kit_json: dict[str, Any] = kit_json_raw
        kit = Kit(kit_json["name"])
        kit_identifier: str = kit_json["id"]

        always_path: Path = kits_path / file.stem / "always"
        if always_path.is_dir():
            for always_file in always_path.iterdir():
                try:
                    kit.always[always_file] = always_file.read_bytes()
                except FileNotFoundError:
                    missing_files.append((kit_json["name"], always_file, "always file"))
                except Exception:
                    # Skip other errors for always files
                    pass

        textures_path: Path = kits_path / file.stem / "textures"
        if textures_path.is_dir():
            for texture_file in (file for file in textures_path.iterdir() if file.suffix.lower() == ".tga"):
                texture: str = texture_file.stem.upper()
                try:
                    kit.textures[texture] = texture_file.read_bytes()
                except FileNotFoundError:
                    missing_files.append((kit_json["name"], texture_file, "texture"))
                except Exception:
                    pass
                txi_path: Path = textures_path / f"{texture}.txi"
                kit.txis[texture] = txi_path.read_bytes() if txi_path.is_file() else b""

        lightmaps_path: Path = kits_path / file.stem / "lightmaps"
        if lightmaps_path.is_dir():
            for lightmap_file in (file for file in lightmaps_path.iterdir() if file.suffix.lower() == ".tga"):
                lightmap: str = lightmap_file.stem.upper()
                try:
                    kit.lightmaps[lightmap] = lightmap_file.read_bytes()
                except FileNotFoundError:
                    missing_files.append((kit_json["name"], lightmap_file, "lightmap"))
                except Exception:
                    pass
                txi_path = lightmaps_path / f"{lightmap_file.stem}.txi"
                kit.txis[lightmap] = txi_path.read_bytes() if txi_path.is_file() else b""

        skyboxes_path: Path = kits_path / file.stem / "skyboxes"
        if skyboxes_path.is_dir():
            for skybox_resref_str in (file.stem.upper() for file in skyboxes_path.iterdir() if file.suffix.lower() == ".mdl"):
                mdl_path: Path = skyboxes_path / f"{skybox_resref_str}.mdl"
                mdx_path: Path = skyboxes_path / f"{skybox_resref_str}.mdx"
                try:
                    mdl, mdx = mdl_path.read_bytes(), mdx_path.read_bytes()
                    kit.skyboxes[skybox_resref_str] = MDLMDXTuple(mdl, mdx)
                except FileNotFoundError:
                    missing_file = mdl_path if not mdl_path.exists() else mdx_path
                    missing_files.append((kit_json["name"], missing_file, "skybox model"))
                except Exception:
                    pass

        doorway_path = kits_path / file.stem / "doorway"
        if doorway_path.is_dir():
            for padding_id in (file.stem for file in doorway_path.iterdir() if file.suffix.lower() == ".mdl"):
                mdl_path = doorway_path / f"{padding_id}.mdl"
                mdx_path = doorway_path / f"{padding_id}.mdx"
                try:
                    mdl = mdl_path.read_bytes()
                    mdx = mdx_path.read_bytes()
                    door_id: int = get_nums(padding_id)[0]
                    padding_size: int = get_nums(padding_id)[1]

                    if padding_id.lower().startswith("side"):
                        if door_id not in kit.side_padding:
                            kit.side_padding[door_id] = {}
                        kit.side_padding[door_id][padding_size] = MDLMDXTuple(mdl, mdx)
                    if padding_id.lower().startswith("top"):
                        if door_id not in kit.top_padding:
                            kit.top_padding[door_id] = {}
                        kit.top_padding[door_id][padding_size] = MDLMDXTuple(mdl, mdx)
                except FileNotFoundError:
                    missing_file = mdl_path if not mdl_path.exists() else mdx_path
                    missing_files.append((kit_json["name"], missing_file, "doorway padding"))
                except Exception:
                    pass

        for door_json in kit_json.get("doors", []):
            utd_k1_path = kits_path / kit_identifier / f'{door_json["utd_k1"]}.utd'
            utd_k2_path = kits_path / kit_identifier / f'{door_json["utd_k2"]}.utd'
            try:
                utd_k1: UTD = read_utd(utd_k1_path)
            except FileNotFoundError:
                missing_files.append((kit_json["name"], utd_k1_path, "door UTD (K1)"))
                continue
            except Exception:
                missing_files.append((kit_json["name"], utd_k1_path, "door UTD (K1) - read error"))
                continue
            
            try:
                utd_k2: UTD = read_utd(utd_k2_path)
            except FileNotFoundError:
                missing_files.append((kit_json["name"], utd_k2_path, "door UTD (K2)"))
                continue
            except Exception:
                missing_files.append((kit_json["name"], utd_k2_path, "door UTD (K2) - read error"))
                continue
            
            width: int = door_json["width"]
            height: int = door_json["height"]
            door = KitDoor(utd_k1, utd_k2, width, height)
            kit.doors.append(door)

        for component_json in kit_json.get("components", []):
            name = component_json["name"]
            component_identifier = component_json["id"]

            component_base_path = kits_path / kit_identifier
            png_path = component_base_path / f"{component_identifier}.png"
            wok_path = component_base_path / f"{component_identifier}.wok"
            mdl_path = component_base_path / f"{component_identifier}.mdl"
            mdx_path = component_base_path / f"{component_identifier}.mdx"

            # Check for missing component files
            missing_component_files = []
            if not png_path.exists():
                missing_component_files.append((png_path, "component image"))
            if not wok_path.exists():
                missing_component_files.append((wok_path, "walkmesh"))
            if not mdl_path.exists():
                missing_component_files.append((mdl_path, "model"))
            if not mdx_path.exists():
                missing_component_files.append((mdx_path, "model extension"))

            # If any files are missing, record them and skip this component
            if missing_component_files:
                for missing_path, file_type in missing_component_files:
                    missing_files.append((kit_json["name"], missing_path, file_type))
                continue

            try:
                bwm: BWM = read_bwm(wok_path)
                # CRITICAL FIX: Re-center the BWM around (0, 0)
                # Game WOKs are stored in world coordinates, but the Indoor Map Builder
                # expects BWMs centered at origin because:
                # - The preview image is drawn CENTERED at room.position
                # - The walkmesh is TRANSLATED by room.position from its original coords
                # Without re-centering, the image and walkmesh end up at different locations!
                # Reference: module_converter.py _recenter_bwm() for implementation details
                bwm = _recenter_bwm(bwm)
                
                # CRITICAL: Regenerate image from recentered BWM to ensure alignment
                # The image on disk was generated from the original (non-recentered) BWM,
                # but we've now recentered the BWM. The image must match the recentered BWM
                # for proper hitbox alignment in the Indoor Map Builder.
                # We regenerate instead of loading from disk to ensure the image bounds
                # exactly match the recentered BWM bounds.
                image = _create_preview_image_from_bwm(bwm)
            except FileNotFoundError:
                missing_files.append((kit_json["name"], wok_path, "walkmesh"))
                continue
            except Exception:
                missing_files.append((kit_json["name"], wok_path, "walkmesh - read error"))
                continue
            except FileNotFoundError:
                missing_files.append((kit_json["name"], wok_path, "walkmesh"))
                continue
            except Exception:
                missing_files.append((kit_json["name"], wok_path, "walkmesh - read error"))
                continue

            try:
                mdl: bytes = mdl_path.read_bytes()
            except FileNotFoundError:
                missing_files.append((kit_json["name"], mdl_path, "model"))
                continue
            except Exception:
                missing_files.append((kit_json["name"], mdl_path, "model - read error"))
                continue

            try:
                mdx: bytes = mdx_path.read_bytes()
            except FileNotFoundError:
                missing_files.append((kit_json["name"], mdx_path, "model extension"))
                continue
            except Exception:
                missing_files.append((kit_json["name"], mdx_path, "model extension - read error"))
                continue

            try:
                component = KitComponent(kit, name, image, bwm, mdl, mdx)

                for hook_json in component_json.get("doorhooks", []):
                    try:
                        position: Vector3 = Vector3(hook_json["x"], hook_json["y"], hook_json["z"])
                        rotation: float = hook_json["rotation"]
                        door: KitDoor = kit.doors[hook_json["door"]]
                        edge: str = hook_json["edge"]
                        hook: KitComponentHook = KitComponentHook(position, rotation, edge, door)
                        component.hooks.append(hook)
                    except (IndexError, KeyError):
                        # Skip invalid door hooks
                        pass

                kit.components.append(component)
            except Exception:
                # Skip component if creation fails
                pass

        kits.append(kit)

    return kits, missing_files
