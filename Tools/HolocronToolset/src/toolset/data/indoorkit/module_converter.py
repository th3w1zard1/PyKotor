"""Module to Kit converter for Indoor Map Builder.

Converts game modules into kit-like components that can be used in the
Indoor Map Builder. This allows reusing existing module layouts without
requiring pre-built kit files.

References:
    Libraries/PyKotor/src/pykotor/common/module.py (Module class)
    Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py (LYT structure)
"""
from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from loggerplus import RobustLogger
from qtpy.QtGui import QColor, QImage, QPainter

from pykotor.common.module import Module
from pykotor.resource.formats.bwm.bwm_data import BWM, BWMFace
from pykotor.resource.generics.utd import UTD
from pykotor.resource.type import ResourceType
from toolset.data.indoorkit.indoorkit_base import Kit, KitComponent, KitDoor
from utility.common.geometry import SurfaceMaterial, Vector3

if TYPE_CHECKING:

    from pykotor.resource.formats.lyt.lyt_data import LYT, LYTRoom
    from toolset.data.installation import HTInstallation


class ModuleKit(Kit):
    """A Kit generated dynamically from a game module.
    
    This kit is generated lazily from module data and provides components
    that represent the rooms defined in the module's LYT file.
    
    Unlike regular Kits which are loaded from JSON files, ModuleKits are
    created on-demand from module archives and use the module's resources.
    """

    def __init__(
        self,
        name: str,
        module_root: str,
        installation: HTInstallation,
    ):
        super().__init__(name)
        self.module_root: str = module_root
        self._installation: HTInstallation = installation
        self._loaded: bool = False
        self._module: Module | None = None

        # Module-specific metadata
        self.is_module_kit: bool = True
        self.source_module: str = module_root

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
            return bool(self.components)
        except Exception:  # noqa: BLE001
            RobustLogger().exception(f"Failed to load module kit for '{self.module_root}'")
            return False

    def _load_module_components(self):
        """Load components from the module's LYT and resources."""
        # Load the module
        try:
            self._module = Module(self.module_root, self._installation, use_dot_mod=True)
        except Exception:  # noqa: BLE001
            RobustLogger().warning(f"Module '{self.module_root}' failed to load")
            return

        # Get the LYT resource
        lyt_resource = self._module.layout()
        if lyt_resource is None:
            RobustLogger().warning(f"Module '{self.module_root}' has no LYT resource")
            return

        lyt_data = lyt_resource.resource()
        if lyt_data is None:
            RobustLogger().warning(f"Failed to load LYT data for module '{self.module_root}'")
            return

        # Create a default door for hooks
        default_door = self._create_default_door()
        self.doors.append(default_door)

        # Extract rooms from LYT
        for room_idx, lyt_room in enumerate(lyt_data.rooms):
            component = self._create_component_from_lyt_room(lyt_room, room_idx, default_door)
            if component is not None:
                self.components.append(component)

        # Also load any doorhooks from LYT as potential hook points
        self._process_lyt_doorhooks(lyt_data)

    def _create_default_door(self) -> KitDoor:
        """Create a default door for module components."""
        utd = UTD()
        utd.resref.set_data("sw_door")
        utd.tag = "module_door"
        return KitDoor(utd, utd, 2.0, 3.0)

    def _create_component_from_lyt_room(
        self,
        lyt_room: LYTRoom,
        room_idx: int,
        default_door: KitDoor,
    ) -> KitComponent | None:
        """Create a KitComponent from a LYT room definition.
        
        Args:
            lyt_room: The LYT room data.
            room_idx: Index of the room for naming.
            default_door: Default door to use for hooks.
        
        Returns:
            A KitComponent or None if creation fails.
        """
        model_name = lyt_room.model.lower() if lyt_room.model else f"room{room_idx}"

        # Try to get the walkmesh (WOK) for this room
        bwm = self._get_room_walkmesh(model_name)
        # Ensure we always have a usable walkmesh with at least one face for
        # collision / snapping logic. Some modules ship with empty or missing
        # WOK data; in that case we fall back to a simple placeholder quad.
        if bwm is None or not bwm.faces:
            bwm = self._create_placeholder_bwm(lyt_room.position)
        else:
            # Make a deep copy of the BWM so each component has its own instance
            # This prevents issues if multiple rooms share the same model name
            bwm = deepcopy(bwm)

        # Try to get the model data
        mdl_data = self._get_room_model(model_name)
        mdx_data = self._get_room_model_ext(model_name)

        if mdl_data is None:
            mdl_data = b""
        if mdx_data is None:
            mdx_data = b""

        # Create a preview image from the walkmesh
        # Each component gets its own image generated from its own BWM copy
        image = self._create_preview_image_from_bwm(bwm)

        # Create display name - include room index to ensure uniqueness
        # This helps distinguish rooms that share the same model name
        if lyt_room.model:
            display_name = f"{model_name.upper()}_{room_idx}"
        else:
            display_name = f"ROOM{room_idx}"

        component = KitComponent(self, display_name, image, bwm, mdl_data, mdx_data)

        # Add hook at room position (simplified - real hooks would need doorhook data)
        # For now, we don't add hooks since modules have complex door systems

        return component

    def _get_room_walkmesh(self, model_name: str) -> BWM | None:
        """Get the walkmesh for a room from the module.
        
        Returns the BWM exactly as stored in the game files, without modification.
        Game WOKs are in local room coordinates - the same format that kit.py
        extracts and that the Kit loader expects.
        
        Reference: indoorkit.py loads BWM with read_bwm() without any centering.
        """
        if self._module is None:
            return None

        # Try to find the WOK resource
        wok_resource = self._module.resource(model_name, ResourceType.WOK)
        if wok_resource is None:
            return None

        data = wok_resource.data()
        if data is None:
            return None

        try:
            from pykotor.resource.formats.bwm import read_bwm  # pyright: ignore[reportMissingImports]
            bwm = read_bwm(data)
        except Exception:  # noqa: BLE001
            RobustLogger().warning(f"Failed to read WOK for '{model_name}'")
            return None
        else:
            # Return BWM as-is - no re-centering needed
            # Game WOKs are already in local coordinates, same as kit.py extracts
            return bwm

    def _get_room_model(self, model_name: str) -> bytes | None:
        """Get the MDL data for a room from the module."""
        if self._module is None:
            return None

        mdl_resource = self._module.resource(model_name, ResourceType.MDL)
        if mdl_resource is None:
            return None

        return mdl_resource.data()

    def _get_room_model_ext(self, model_name: str) -> bytes | None:
        """Get the MDX data for a room from the module."""
        if self._module is None:
            return None

        mdx_resource = self._module.resource(model_name, ResourceType.MDX)
        if mdx_resource is None:
            return None

        return mdx_resource.data()

    def _create_placeholder_bwm(self, position: Vector3) -> BWM:
        """Create a placeholder BWM with a single quad."""
        bwm = BWM()

        # Create a 10x10 unit square walkmesh at origin
        size = 5.0
        v1 = Vector3(-size, -size, 0)
        v2 = Vector3(size, -size, 0)
        v3 = Vector3(size, size, 0)
        v4 = Vector3(-size, size, 0)

        face1 = BWMFace(v1, v2, v3)
        face1.material = SurfaceMaterial.STONE
        face2 = BWMFace(v1, v3, v4)
        face2.material = SurfaceMaterial.STONE

        bwm.faces.append(face1)
        bwm.faces.append(face2)

        return bwm

    def _create_preview_image_from_bwm(self, bwm: BWM) -> QImage:
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
        Reference: indoorkit.py line 161: image = QImage(...).mirrored()
        """
        from qtpy.QtGui import QPainterPath

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

        # Calculate image dimensions at 10 pixels per unit (matching kit.py)
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

    def _process_lyt_doorhooks(self, lyt_data: LYT):
        """Process LYT doorhooks to create component hooks.
        
        For now, this is a placeholder. Full implementation would need to
        map doorhooks to their corresponding rooms and create proper
        KitComponentHook objects.
        """
        # LYT doorhooks contain information about where doors connect rooms
        # This is complex and would require matching doorhooks to rooms
        # For simplicity, we'll leave hooks empty for module-derived components


class ModuleKitManager:
    """Manages lazy loading of ModuleKits from an installation.
    
    Provides methods to list available modules and convert them to kits
    on demand. Only loads module data when a specific module is selected.
    """

    def __init__(self, installation: HTInstallation):
        self._installation: HTInstallation = installation
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
        module_names = self.get_module_names()

        # Try to find the display name from various extensions
        for ext in [".rim", ".mod", "_s.rim"]:
            filename = f"{module_root}{ext}"
            if filename in module_names:
                area_name = module_names[filename]
                if area_name:
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
        if module_root not in self._cache:
            display_name = self.get_module_display_name(module_root)
            kit = ModuleKit(display_name, module_root, self._installation)
            self._cache[module_root] = kit

        return self._cache[module_root]

    def clear_cache(self):
        """Clear the kit cache to free memory."""
        self._cache.clear()
        self._module_names = None

