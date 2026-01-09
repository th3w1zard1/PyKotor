"""Backend-agnostic module loading utilities.

This module provides backend-agnostic utilities for loading KotOR modules (LYT/GIT files)
and extracting game object data. The actual rendering/display is handled by backend-specific code.

References:
----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/Game.ts
        Libraries/PyKotor/src/pykotor/resource/formats/lyt - LYT format
        Libraries/PyKotor/src/pykotor/resource/generics/git - GIT format

"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.twoda import TwoDA, read_2da
from pykotor.resource.type import ResourceType
from pykotor.tools import creature

if TYPE_CHECKING:
    from pykotor.common.module import Module
    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.lyt import LYT
    from pykotor.resource.generics.git import GIT

SEARCH_ORDER_2DA: list[SearchLocation] = [SearchLocation.OVERRIDE, SearchLocation.CHITIN]


class ModuleDataLoader:
    """Backend-agnostic module data loader.
    
    This class extracts module data (rooms, doors, creatures, etc.) from LYT/GIT files
    and provides it in a backend-agnostic format. The actual rendering/display is handled
    by backend-specific code.
    
    References:
    ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        Libraries/PyKotorGL/src/pykotor/gl/scene/scene_base.py:207-223 - 2DA loading
        Libraries/PyKotorGL/src/pykotor/gl/scene/scene_base.py:224-315 - Creature loading

    """
    
    def __init__(self, installation: Installation):
        """Initialize the module data loader.
        
        Args:
        ----
            installation: KotOR installation for resource access
        """
        self.installation: Installation = installation
        self.table_doors: TwoDA = TwoDA()
        self.table_placeables: TwoDA = TwoDA()
        self.table_creatures: TwoDA = TwoDA()
        self.table_heads: TwoDA = TwoDA()
        self.table_baseitems: TwoDA = TwoDA()
        self._load_2da_tables()
    
    def _load_2da_tables(self) -> None:
        """Load required 2DA tables from installation."""
        def load_2da(name: str) -> TwoDA:
            resource = self.installation.resource(name, ResourceType.TwoDA, SEARCH_ORDER_2DA)
            if not resource:
                return TwoDA()
            return read_2da(resource.data)
        
        self.table_doors = load_2da("genericdoors")
        self.table_placeables = load_2da("placeables")
        self.table_creatures = load_2da("appearance")
        self.table_heads = load_2da("heads")
        self.table_baseitems = load_2da("baseitems")
    
    def get_module_resources(self, module: Module) -> tuple[GIT | None, LYT | None]:
        """Get GIT and LYT resources from a module.
        
        Args:
        ----
            module: Module to extract resources from
        
        Returns:
        -------
            Tuple of (GIT, LYT) resources, or (None, None) if not found
        """
        git_resource = module.git()
        lyt_resource = module.layout()
        
        git: GIT | None = None
        if git_resource:
            git = git_resource.resource()
        
        layout: LYT | None = None
        if lyt_resource:
            layout = lyt_resource.resource()
        
        return git, layout
    
    def get_creature_model_data(
        self,
        git_creature,
        module: Module,
    ) -> dict[str, str | None]:
        """Get creature model data from GIT creature and module.
        
        Args:
        ----
            git_creature: GITCreature instance
            module: Module containing creature resources
        
        Returns:
        -------
            Dictionary with model names:
            - 'body_model': Body model name
            - 'body_texture': Body texture name
            - 'head_model': Head model name
            - 'head_texture': Head texture name
            - 'rhand_model': Right hand weapon model name
            - 'lhand_model': Left hand weapon model name
            - 'mask_model': Mask model name
        """
        creature_resource = module.creature(str(git_creature.resref))
        if not creature_resource:
            return {
                'body_model': None,
                'body_texture': None,
                'head_model': None,
                'head_texture': None,
                'rhand_model': None,
                'lhand_model': None,
                'mask_model': None,
            }
        
        utc = creature_resource.resource()
        if not utc:
            return {
                'body_model': None,
                'body_texture': None,
                'head_model': None,
                'head_texture': None,
                'rhand_model': None,
                'lhand_model': None,
                'mask_model': None,
            }
        
        body_model, body_texture = creature.get_body_model(
            utc,
            self.installation,
            appearance=self.table_creatures,
            baseitems=self.table_baseitems,
        )
        head_model, head_texture = creature.get_head_model(
            utc,
            self.installation,
            appearance=self.table_creatures,
            heads=self.table_heads,
        )
        rhand_model, lhand_model = creature.get_weapon_models(
            utc,
            self.installation,
            appearance=self.table_creatures,
            baseitems=self.table_baseitems,
        )
        mask_model = creature.get_mask_model(utc, self.installation)
        
        return {
            'body_model': body_model,
            'body_texture': body_texture,
            'head_model': head_model,
            'head_texture': head_texture,
            'rhand_model': rhand_model,
            'lhand_model': lhand_model,
            'mask_model': mask_model,
        }
    
    def get_door_model_name(self, door, module: Module) -> str | None:
        """Get door model name from door and module.
        
        Args:
        ----
            door: GITDoor instance
            module: Module containing door resources
        
        Returns:
        -------
            Door model name, or None if not found
        """
        door_resource = module.door(str(door.resref))
        if not door_resource:
            return None
        
        utd = door_resource.resource()
        if not utd:
            return None
        
        row = self.table_doors.get_row(utd.appearance_id)
        if not row:
            return None
        
        return row.get_string("modelname")
    
    def get_placeable_model_name(self, placeable, module: Module) -> str | None:
        """Get placeable model name from placeable and module.
        
        Args:
        ----
            placeable: GITPlaceable instance
            module: Module containing placeable resources
        
        Returns:
        -------
            Placeable model name, or None if not found
        """
        placeable_resource = module.placeable(str(placeable.resref))
        if not placeable_resource:
            return None
        
        utp = placeable_resource.resource()
        if not utp:
            return None
        
        row = self.table_placeables.get_row(utp.appearance_id)
        if not row:
            return None
        
        return row.get_string("modelname")

