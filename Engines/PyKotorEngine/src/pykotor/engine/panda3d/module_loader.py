"""Module loading for KotOR areas.

This module provides functionality to load KotOR modules (LYT/GIT files)
and render them in the Panda3D engine.

References:
----------
    vendor/reone/src/libs/scene/di/module.cpp - Module loading
    vendor/KotOR.js/src/Game.ts - Module rendering
    Libraries/PyKotor/src/pykotor/resource/formats/lyt - LYT format
    Libraries/PyKotor/src/pykotor/resource/generics/git - GIT format
"""

from __future__ import annotations

import math

from typing import TYPE_CHECKING, Any

from panda3d.core import LQuaternion, NodePath

from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.twoda import TwoDA, read_2da
from pykotor.resource.type import ResourceType
from pykotor.tools import creature

if TYPE_CHECKING:
    from pykotor.common.module import Module
    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.lyt import LYT
    from pykotor.resource.generics.git import GIT

SEARCH_ORDER_2DA = [SearchLocation.OVERRIDE, SearchLocation.CHITIN]
SEARCH_ORDER = [SearchLocation.OVERRIDE, SearchLocation.CHITIN]


class ModuleLoader:
    """Loads KotOR modules (LYT/GIT) into Panda3D scene.
    
    This class handles loading of module layouts, rooms, doors, placeables,
    creatures, and other game objects from LYT and GIT files.
    
    References:
    ----------
        vendor/reone/src/libs/scene/di/module.cpp:50-200 - Module loading
        vendor/KotOR.js/src/Game.ts:100-300 - Module rendering
    """
    
    def __init__(
        self,
        installation: Installation,
        mdl_loader: MDLLoader,  # MDLLoader instance
        texture_loader: Any,  # Function to load TPC textures
    ):
        """Initialize the module loader.
        
        Args:
        ----
            installation: KotOR installation for resource access
            mdl_loader: MDL loader instance for loading models
            texture_loader: Function to load TPC textures
        """
        self.installation = installation
        self._mdl_loader = mdl_loader
        self._texture_loader = texture_loader
        
        # Load 2DA tables
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
    
    def load_module(self, module: Module, root: NodePath) -> None:
        """Load a module and all its content into the scene.
        
        Args:
        ----
            module: Module to load
            root: Root NodePath to attach module content to
        
        References:
        ----------
            vendor/reone/src/libs/scene/di/module.cpp:100-150 - Module loading
        """
        # Load GIT/LYT
        git_resource = module.git()
        lyt_resource = module.layout()
        if git_resource is None or lyt_resource is None:
            return
        
        git = git_resource.resource()
        layout = lyt_resource.resource()
        
        if layout is None:
            return
        
        # Load rooms
        self._load_rooms(layout, root, module)
        
        if git is None:
            return
        
        # Load GIT objects
        self._load_cameras(git, root)
        self._load_creatures(git, root, module)
        self._load_doors(git, root, module)
        self._load_encounters(git, root)
        self._load_placeables(git, root, module)
        self._load_sounds(git, root)
        self._load_stores(git, root)
        self._load_triggers(git, root)
        self._load_waypoints(git, root)
    
    def _load_rooms(self, layout: LYT, root: NodePath, module: Module) -> None:
        """Load room models from layout.
        
        References:
        ----------
            vendor/reone/src/libs/scene/di/module.cpp:150-180 - Room loading
        """
        for room in layout.rooms:
            room_node = self._load_model(room.model)
            if room_node:
                room_node.reparentTo(root)
                room_node.setPos(room.position.x, room.position.y, room.position.z)
    
    def _load_doors(self, git: GIT, root: NodePath, module: Module) -> None:
        """Load door models from GIT.
        
        References:
        ----------
            vendor/reone/src/libs/scene/di/module.cpp:200-250 - Door loading
        """
        for door in git.doors:
            door_resource = module.door(str(door.resref))
            if door_resource:
                utd = door_resource.resource()
                if utd:
                    model_name = self.table_doors.get_row(utd.appearance_id).get_string("modelname")
                    door_node = self._load_model(model_name)
                    if door_node:
                        door_node.reparentTo(root)
                        door_node.setPos(door.position.x, door.position.y, door.position.z)
                        door_node.setH(door.bearing)
    
    def _load_placeables(self, git: GIT, root: NodePath, module: Module) -> None:
        """Load placeable models from GIT."""
        for placeable in git.placeables:
            placeable_resource = module.placeable(str(placeable.resref))
            if placeable_resource:
                utp = placeable_resource.resource()
                if utp:
                    model_name = self.table_placeables.get_row(utp.appearance_id).get_string("modelname")
                    placeable_node = self._load_model(model_name)
                    if placeable_node:
                        placeable_node.reparentTo(root)
                        placeable_node.setPos(placeable.position.x, placeable.position.y, placeable.position.z)
                        placeable_node.setH(placeable.bearing)
    
    def _load_creatures(self, git: GIT, root: NodePath, module: Module) -> None:
        """Load creature models from GIT."""
        for git_creature in git.creatures:
            creature_resource = module.creature(str(git_creature.resref))
            if creature_resource:
                utc = creature_resource.resource()
                if utc:
                    # Get body model
                    body_model, body_tex = creature.get_body_model(
                        utc, self.installation,
                        appearance=self.table_creatures,
                        baseitems=self.table_baseitems
                    )
                    
                    if body_model:
                        creature_node = self._load_model(body_model)
                        if creature_node:
                            creature_node.reparentTo(root)
                            creature_node.setPos(
                                git_creature.position.x,
                                git_creature.position.y,
                                git_creature.position.z
                            )
                            creature_node.setH(git_creature.bearing)
                            
                            if body_tex:
                                self._load_texture(body_tex, creature_node)
                            
                            # Load head if present
                            head_model, head_tex = creature.get_head_model(
                                utc, self.installation,
                                appearance=self.table_creatures,
                                heads=self.table_heads
                            )
                            
                            if head_model and head_model.strip():
                                head_hook = creature_node.find("**/headhook")
                                if not head_hook.isEmpty():
                                    head_node = self._load_model(head_model)
                                    if head_node:
                                        head_node.reparentTo(head_hook)
                                        if head_tex and head_tex.strip():
                                            self._load_texture(head_tex, head_node)
    
    def _load_cameras(self, git: GIT, root: NodePath) -> None:
        """Load camera nodes from GIT."""
        for i, camera in enumerate(git.cameras):
            camera_node = root.attachNewNode(f"camera_{i}")
            camera_node.setPos(camera.position.x, camera.position.y, camera.position.z + camera.height)
            quat = LQuaternion(camera.orientation.w, camera.orientation.x, camera.orientation.y, camera.orientation.z)
            euler = quat.getHpr()
            camera_node.setHpr(
                euler[1],  # Pitch
                euler[2] - 90 + math.degrees(camera.pitch),  # Yaw
                -euler[0] + 90,  # Roll
            )
    
    def _load_sounds(self, git: GIT, root: NodePath) -> None:
        """Load sound nodes from GIT."""
        for sound in git.sounds:
            sound_node = root.attachNewNode(sound.resref + ".uts")
            sound_node.setPos(sound.position.x, sound.position.y, sound.position.z)
    
    def _load_triggers(self, git: GIT, root: NodePath) -> None:
        """Load trigger nodes from GIT."""
        for trigger in git.triggers:
            trigger_node = root.attachNewNode(trigger.resref + ".utt")
            trigger_node.setPos(trigger.position.x, trigger.position.y, trigger.position.z)
    
    def _load_encounters(self, git: GIT, root: NodePath) -> None:
        """Load encounter nodes from GIT."""
        for encounter in git.encounters:
            encounter_node = root.attachNewNode(encounter.resref + ".ute")
            encounter_node.setPos(encounter.position.x, encounter.position.y, encounter.position.z)
    
    def _load_waypoints(self, git: GIT, root: NodePath) -> None:
        """Load waypoint nodes from GIT."""
        for waypoint in git.waypoints:
            waypoint_node = root.attachNewNode(waypoint.resref + ".utw")
            waypoint_node.setPos(waypoint.position.x, waypoint.position.y, waypoint.position.z)
    
    def _load_stores(self, git: GIT, root: NodePath) -> None:
        """Load store nodes from GIT."""
        for store in git.stores:
            store_node = root.attachNewNode(store.resref + ".utm")
            store_node.setPos(store.position.x, store.position.y, store.position.z)
    
    def _load_model(self, name: str) -> NodePath | None:
        """Load MDL from installation.
        
        References:
        ----------
            vendor/reone/src/libs/resource/provider/models.cpp:50-100
        """
        mdl = self.installation.resource(name, ResourceType.MDL, SEARCH_ORDER)
        mdx = self.installation.resource(name, ResourceType.MDX, SEARCH_ORDER)
        if mdl is not None and mdx is not None:
            # Use MDLLoader to load the model
            # Get file paths from resources
            mdl_path = None
            mdx_path = None
            
            # Try to get filepath from resource
            if hasattr(mdl, 'filepath') and mdl.filepath():
                mdl_path = str(mdl.filepath())
            elif hasattr(mdl, 'path'):
                mdl_path = str(mdl.path)
            else:
                # Fallback: construct path from resource identifier
                mdl_path = name + ".mdl"
            
            if hasattr(mdx, 'filepath') and mdx.filepath():
                mdx_path = str(mdx.filepath())
            elif hasattr(mdx, 'path'):
                mdx_path = str(mdx.path)
            else:
                mdx_path = name + ".mdx"
            
            # Load using MDLLoader
            return self._mdl_loader.load(mdl_path, mdx_path)
        
        return None
    
    def _load_texture(self, name: str, model: NodePath) -> None:
        """Load TPC from installation and apply to model."""
        tpc = self.installation.texture(
            name,
            [
                SearchLocation.CUSTOM_MODULES,
                SearchLocation.OVERRIDE,
                SearchLocation.TEXTURES_TPA,
                SearchLocation.CHITIN,
            ],
            capsules=None,  # TODO: Get from module
        )
        if tpc is not None:
            tex = self._texture_loader(tpc)
            if tex:
                # Apply texture to all child nodes
                for child in model.getChildren():
                    child.setTexture(tex, 1)
                # Also apply to parent node
                model.setTexture(tex, 1)

