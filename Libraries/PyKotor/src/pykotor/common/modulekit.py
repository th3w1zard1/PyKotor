

"""Implicit ModuleKit support (headless).

This mirrors Holocron Toolset's implicit-kit pipeline (ModuleKit) but without any `toolset.*`
or Qt dependencies so it can be used from `pykotor.tools.indoormap` and KotorCLI.

Design rule (repo convention):
- `pykotor.common.*` contains **classes / data models**
- `pykotor.tools.*` contains **functions / workflows**
"""
from __future__ import annotations

import math

from copy import deepcopy
from typing import TYPE_CHECKING

from loggerplus import RobustLogger
from pykotor.common.indoorkit import Kit, KitComponent, KitComponentHook, KitDoor
from pykotor.common.module import Module
from pykotor.resource.formats.bwm import BWM, BWMEdge, BWMFace, read_bwm
from pykotor.resource.generics.utd import UTD
from pykotor.resource.type import ResourceType
from pykotor.tools.kit import _extract_doorhooks_from_bwm  # NOTE: shared logic (function)
from utility.common.geometry import SurfaceMaterial, Vector3

if TYPE_CHECKING:
    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.lyt import LYT, LYTRoom


class ModuleKit(Kit):
    """A Kit generated dynamically from a game module.
    
    This kit is generated lazily from module data and provides components
    that represent the rooms defined in the module's LYT file.
    
    Unlike regular Kits which are loaded from JSON files, ModuleKits are
    created on-demand from module archives and use the module's resources.
    """

    def __init__(
        self,
#        name: str,
        module_root: str,
        installation: Installation,
    ):
        # Use module_root as both the stable id and the display name.
        super().__init__(name=module_root.upper(), kit_id=module_root.lower())
        self.module_root: str = module_root.lower()
        self._installation: Installation = installation
        self._loaded: bool = False
        self._module: Module | None = None

        # Duck-typed marker used by Toolset/CLI to know this kit is module-backed.
        self.is_module_kit: bool = True

    def ensure_loaded(self) -> bool:
        """Lazily load the module components if not already loaded.

        Returns:
            True if components were loaded successfully, False otherwise.
        """
        if self._loaded:
            return bool(self.components)
        self._loaded = True
        try:
            self._load_module_components()
        except Exception:  # noqa: BLE001
            RobustLogger().exception("Failed to load ModuleKit for '%s'", self.module_root)
            return False
        return bool(self.components)

    def _load_module_components(self) -> None:
        """Load components from the module's LYT and resources."""
        # IMPORTANT: use composite module loading (rim/_s.rim/_dlg.erf/.mod) rather than a single
        # capsule file. This matches how real installs load modules and avoids relying on resrefs
        # matching the module root.
        self._module = Module(self.module_root, self._installation, use_dot_mod=True)

        layout_res = self._module.layout()
        if layout_res is None:
            RobustLogger().warning("Module '%s' has no LYT resource", self.module_root)
            return
        lyt_data = layout_res.resource()
        if lyt_data is None:
            RobustLogger().warning("Failed to parse LYT data for module '%s'", self.module_root)
            return

        # Create a default door for hooks
        default_door: KitDoor = self._create_default_door()
        self.doors.append(default_door)

        # Extract rooms from LYT
        lyt_room_to_component: dict[int, KitComponent] = {}
        for room_idx, lyt_room in enumerate(lyt_data.rooms):
            component: KitComponent | None = self._component_from_lyt_room(lyt_room, room_idx, default_door)
            if component is not None:
                self.components.append(component)
                lyt_room_to_component[room_idx] = component

        # Also load any doorhooks from LYT as potential hook points
        self._process_lyt_doorhooks(lyt_data, lyt_room_to_component)

    def _create_default_door(self) -> KitDoor:
        """Create a default door for module components."""
        utd = UTD()
        utd.resref.set_data("sw_door")
        utd.tag = "module_door"
        return KitDoor(utdK1=utd, utdK2=utd, width=2.0, height=3.0)

    def _component_from_lyt_room(
        self,
        lyt_room: LYTRoom,
        idx: int,
        default_door: KitDoor,
    ) -> KitComponent | None:
        """Create a KitComponent from a LYT room definition.

        We intentionally create one component per LYT room, even if model names repeat,
        to keep indoor JSON stable and unambiguous for roundtrips.
        """
        model_name = (lyt_room.model or f"room{idx}").lower()
        component_id = f"{model_name}_{idx}"

        # Try to get the walkmesh (WOK) for this room
        bwm = self._get_room_walkmesh(model_name)
        # Ensure we always have a usable walkmesh with at least one face for
        # collision / snapping logic. Some modules ship with empty or missing
        # WOK data; in that case we fall back to a simple placeholder quad.
        if bwm is None or not bwm.faces:
            bwm = self._create_placeholder_bwm()
        else:
            # Make a deep copy of the BWM so each component has its own instance
            # This prevents issues if multiple rooms share the same model name
            bwm = deepcopy(bwm)

        # IMPORTANT: keep walkmesh and model in the same coordinate space.
        # The model is stored in its own local space and placed in the module via the LYT room position.
        # Module WOKs are commonly authored in room-local space (matching MDL coordinates), so they
        # do NOT need translation.
        #
        # Do NOT bbox-center; many rooms have non-centered origins (e.g. hallways), and bbox-centering
        # shifts collision relative to visuals.
        # bwm.translate(-lyt_room.position.x, -lyt_room.position.y, -lyt_room.position.z)

        # Try to get the model data
        mdl = self._get_room_model(model_name, ResourceType.MDL) or b""
        mdx = self._get_room_model(model_name, ResourceType.MDX) or b""

        # Create display name - include room index to ensure uniqueness
        # This helps distinguish rooms that share the same model name
        if lyt_room.model:
            component_name = f"{model_name.upper()}_{idx}"
        else:
            component_name = f"ROOM{idx}"

        component = KitComponent(kit=self, name=component_name, component_id=component_id, bwm=bwm, mdl=mdl, mdx=mdx)
        # Persist the original room placement so extract/build roundtrips can preserve layout.
        component.default_position = Vector3(lyt_room.position.x, lyt_room.position.y, lyt_room.position.z)  # type: ignore[attr-defined]

        doorhooks = _extract_doorhooks_from_bwm(bwm, num_doors=len(self.doors))

        # Create KitComponentHook objects from extracted doorhooks
        for doorhook in doorhooks:
            position = Vector3(float(doorhook["x"]), float(doorhook["y"]), float(doorhook["z"]))
            rotation = float(doorhook["rotation"])
            door_index = int(doorhook["door"])
            edge = int(doorhook["edge"])

            # Get the door for this hook (use default door if index is invalid)
            if 0 <= door_index < len(self.doors):
                door = self.doors[door_index]
            else:
                door = default_door

            hook = KitComponentHook(position, rotation, edge, door)
            component.hooks.append(hook)

        return component

    def _get_room_walkmesh(self, model_name: str) -> BWM | None:
        """Get the walkmesh for a room from the module.
        
        Returns the BWM exactly as stored in the game files.
        Note: The BWM will be re-centered by _recenter_bwm() before use.
        """
        if self._module is None:
            return None
        res = self._module.resource(model_name, ResourceType.WOK)
        if res is None:
            return None
        data = res.data()
        if not data:
            return None
        if isinstance(data, BWM):
            return data
        try:
            return read_bwm(data)
        except Exception:  # noqa: BLE001
            RobustLogger().warning("Failed to read WOK for '%s' in module '%s'", model_name, self.module_root)
            return None

    def _get_room_model(self, model_name: str, restype: ResourceType) -> bytes | None:
        if self._module is None:
            return None
        res = self._module.resource(model_name, restype)
        if res is None:
            return None
        data = res.data()
        if not data:
            return None
        # ModuleResource.data() returns bytes for capsule-backed files.
        return bytes(data) if isinstance(data, (bytes, bytearray)) else None

    def _create_placeholder_bwm(self) -> BWM:
        """Create a placeholder BWM with a single quad."""
        bwm = BWM()

        # Create a 10x10 unit square walkmesh at origin
        size = 5.0
        v1 = Vector3(-size, -size, 0.0)
        v2 = Vector3(size, -size, 0.0)
        v3 = Vector3(size, size, 0.0)
        v4 = Vector3(-size, size, 0.0)

        face1 = BWMFace(v1, v2, v3)
        face1.material = SurfaceMaterial.STONE
        face2 = BWMFace(v1, v3, v4)
        face2.material = SurfaceMaterial.STONE

        bwm.faces.append(face1)
        bwm.faces.append(face2)

        return bwm

    def _process_lyt_doorhooks(
        self,
        lyt_data: LYT,
        lyt_room_to_component: dict[int, KitComponent],
    ) -> None:
        """Process LYT doorhooks to create component hooks.

        Maps LYT doorhooks (world-space door positions) to KitComponentHook objects
        in local-space coordinates. This enables roundtrip preservation of door placements
        when extracting modules to indoor JSON and rebuilding them.

        Args:
            lyt_data: The LYT data to process.
            lyt_room_to_component: A dictionary mapping LYT room indices to KitComponents.
        """
        if not lyt_data.doorhooks:
            return

        for doorhook in lyt_data.doorhooks:
            room_name_lower: str = doorhook.room.lower()

            # Find the LYT room that matches this doorhook's room name
            lyt_room_match: LYTRoom | None = None
            room_idx: int | None = None
            for idx, lyt_room in enumerate(lyt_data.rooms):
                room_model: str = (lyt_room.model or "").lower()
                if room_model == room_name_lower or room_name_lower == f"room{idx}":
                    lyt_room_match = lyt_room
                    room_idx = idx
                    break

            if lyt_room_match is None or room_idx is None:
                RobustLogger().warning(
                    "Doorhook references room '%s' which doesn't exist in LYT for module '%s'",
                    doorhook.room,
                    self.module_root,
                )
                continue

            # Use the mapping to find the component (handles cases where component creation failed)
            matching_component: KitComponent | None = lyt_room_to_component.get(room_idx)
            if matching_component is None:
                RobustLogger().warning(
                    "Doorhook room '%s' (index %d) has no corresponding component in module '%s' (component creation may have failed)",
                    doorhook.room,
                    room_idx,
                    self.module_root,
                )
                continue

            room_position: Vector3 = matching_component.default_position
            local_position: Vector3 = Vector3(
                doorhook.position.x - room_position.x,
                doorhook.position.y - room_position.y,
                doorhook.position.z - room_position.z,
            )

            euler: Vector3 = doorhook.orientation.to_euler()
            rotation_deg: float = math.degrees(euler.z) % 360
            if rotation_deg < 0:
                rotation_deg += 360

            closest_edge: int | None = self._find_closest_edge(matching_component.bwm, local_position)
            edge_index: int = 0 if closest_edge is None else closest_edge

            door: KitDoor = self.doors[0] if self.doors else self._create_default_door()
            door_name_lower: str = doorhook.door.lower()
            for existing_door in self.doors:
                if (
                    existing_door.utdK1.resref.get().lower() == door_name_lower
                    or existing_door.utdK2.resref.get().lower() == door_name_lower
                ):
                    door = existing_door
                    break

            hook = KitComponentHook(
                position=local_position,
                rotation=rotation_deg,
                edge=edge_index,
                door=door,
            )
            matching_component.hooks.append(hook)

    def _find_closest_edge(
        self,
        bwm: BWM,
        position: Vector3,
    ) -> int | None:
        edges: list[BWMEdge] = bwm.edges()
        if not edges:
            return None

        min_distance: float = float("inf")
        closest_edge_index: int | None = None

        for edge in edges:
            face = edge.face
            # NOTE: `edge.index` is a GLOBAL edge index computed as `face_index * 3 + local_edge_index`.
            local_edge_index: int = edge.index % 3

            if local_edge_index == 0:
                v1 = face.v1
                v2 = face.v2
            elif local_edge_index == 1:
                v1 = face.v2
                v2 = face.v3
            else:  # local_edge_index == 2
                v1 = face.v3
                v2 = face.v1

            edge_vec: Vector3 = Vector3(v2.x - v1.x, v2.y - v1.y, 0.0)
            point_vec: Vector3 = Vector3(position.x - v1.x, position.y - v1.y, 0.0)

            edge_len_sq: float = edge_vec.x * edge_vec.x + edge_vec.y * edge_vec.y
            if edge_len_sq < 1e-6:
                continue

            t: float = max(0.0, min(1.0, (point_vec.x * edge_vec.x + point_vec.y * edge_vec.y) / edge_len_sq))
            closest_point: Vector3 = Vector3(
                v1.x + t * edge_vec.x,
                v1.y + t * edge_vec.y,
                v1.z + t * (v2.z - v1.z),
            )

            dx: float = position.x - closest_point.x
            dy: float = position.y - closest_point.y
            distance: float = math.sqrt(dx * dx + dy * dy)

            if distance < min_distance:
                min_distance = distance
                face_index: int = next((i for i, f in enumerate(bwm.faces) if f is face), -1)
                if face_index == -1:
                    try:
                        face_index = bwm.faces.index(face)
                    except ValueError:
                        continue
                closest_edge_index = face_index * 3 + local_edge_index

        return closest_edge_index


class ModuleKitManager:
    """Manages lazy loading of ModuleKits from an installation.

    Provides methods to list available modules and convert them to kits
    on demand. Only loads module data when a specific module is selected.
    """
    def __init__(self, installation: Installation):
        self._installation: Installation = installation
        self._cache: dict[str, ModuleKit] = {}
        self._module_names: dict[str, str | None] | None = None

    def get_module_names(self) -> dict[str, str | None]:
        """Get dictionary mapping module filenames to display names.

        Uses the installation's module_names method for display names.

        Returns:
            Dict mapping module filename to display name (or None).
        """
        if self._module_names is None:
            self._module_names = self._installation.module_names(use_hardcoded=True)
        return self._module_names

    def get_module_roots(self) -> list[str]:
        """Get list of unique module roots from the installation.

        Returns:
            List of module root names (without extensions).
        """
        seen_roots: set[str] = set()
        roots: list[str] = []

        for module_filename in self.get_module_names():
            root = self._installation.get_module_root(module_filename)
            if root not in seen_roots:
                seen_roots.add(root)
                roots.append(root)

        return sorted(roots)

    def get_module_display_name(self, module_root: str) -> str:
        """Get the display name for a module root.

        Args:
            module_root: The module root name.

        Returns:
            Display name combining root and area name if available.
        """
        module_names: dict[str, str | None] = self.get_module_names()
        for ext in (".mod", "_s.rim", ".rim", "_dlg.erf", "_adx.rim", "_a.rim"):
            filename: str = f"{module_root}{ext}"
            if filename not in module_names:
                continue
            area_name: str | None = module_names[filename]
            if area_name is None:
                continue
            return f"{module_root.upper()} - {area_name}"

        return module_root.upper()

    def get_module_kit(self, module_root: str) -> ModuleKit:
        """Get or create a ModuleKit for the specified module.

        Kits are cached so repeated requests for the same module return
        the same kit instance.

        Args:
            module_root: The module root name (e.g., "danm13").

        Returns:
            A ModuleKit for the specified module.
        """
        key: str = module_root.lower()
        if key not in self._cache:
            self._cache[key] = ModuleKit(
                module_root=key,
                installation=self._installation,
            )
        return self._cache[key]

    def clear_cache(self) -> None:
        """Clear the kit cache to free memory."""
        self._cache.clear()
        self._module_names = None

    def is_kit_valid(self, module_root: str) -> bool:
        """Check if a module kit is valid."""
        return module_root.lower() in self._cache


