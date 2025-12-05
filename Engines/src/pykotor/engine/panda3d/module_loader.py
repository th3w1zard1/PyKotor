"""Panda3D-specific module loading and rendering.

This module provides Panda3D-specific functionality to render KotOR modules
(LYT/GIT files) into Panda3D NodePaths. It uses backend-agnostic module loading
utilities from Libraries/PyKotor.

References:
----------
    vendor/reone/src/libs/scene/di/module.cpp - Module loading
    vendor/KotOR.js/src/Game.ts - Module rendering
    Libraries/PyKotor/src/pykotor/common/module_loader.py - Backend-agnostic loading
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from panda3d.core import LQuaternion, NodePath  # pyright: ignore[reportMissingImports]

from pykotor.common.module_loader import ModuleDataLoader
from pykotor.resource.generics.git import GIT
from pykotor.extract.installation import SearchLocation
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.common.module import Module
    from pykotor.extract.installation import Installation

SEARCH_ORDER = [SearchLocation.OVERRIDE, SearchLocation.CHITIN]


class ModuleLoader:
    """Panda3D-specific module loader and renderer.
    
    This class handles rendering KotOR modules (LYT/GIT files) into Panda3D NodePaths.
    It uses ModuleDataLoader for backend-agnostic data extraction.
    
    References:
    ----------
        vendor/reone/src/libs/scene/di/module.cpp:50-200 - Module loading
        vendor/KotOR.js/src/Game.ts:100-300 - Module rendering
        Libraries/PyKotor/src/pykotor/common/module_loader.py - Data extraction
    """
    
    def __init__(
        self,
        installation: Installation,
        mdl_loader: Any,  # MDLLoader instance from pykotor.engine.panda3d.mdl_loader
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
        self._data_loader = ModuleDataLoader(installation)
    
    def load_module(self, module: Module, root: NodePath) -> None:
        """Load a module and all its content into the Panda3D scene.
        
        Args:
        ----
            module: Module to load
            root: Root NodePath to attach module content to
        
        References:
        ----------
            vendor/reone/src/libs/scene/di/module.cpp:100-150 - Module loading
        """
        # Get module resources using backend-agnostic loader
        git, layout = self._data_loader.get_module_resources(module)
        
        if layout is None:
            return
        
        # Load rooms
        self._load_rooms(layout, root)
        
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
    
    def _load_rooms(self, layout, root: NodePath) -> None:
        """Load room models from layout into Panda3D scene.
        
        References:
        ----------
            vendor/reone/src/libs/scene/di/module.cpp:150-180 - Room loading
        """
        for room in layout.rooms:
            room_node = self._load_model(room.model)
            if room_node:
                room_node.reparentTo(root)
                room_node.setPos(room.position.x, room.position.y, room.position.z)
    
    def _load_doors(self, git, root: NodePath, module: Module) -> None:
        """Load door models from GIT into Panda3D scene.
        
        References:
        ----------
            vendor/reone/src/libs/scene/di/module.cpp:200-250 - Door loading
        """
        for door in git.doors:
            model_name = self._data_loader.get_door_model_name(door, module)
            if model_name:
                door_node = self._load_model(model_name)
                if door_node:
                    door_node.reparentTo(root)
                    door_node.setPos(door.position.x, door.position.y, door.position.z)
                    door_node.setH(door.bearing)
    
    def _load_placeables(self, git, root: NodePath, module: Module) -> None:
        """Load placeable models from GIT into Panda3D scene."""
        for placeable in git.placeables:
            model_name = self._data_loader.get_placeable_model_name(placeable, module)
            if model_name:
                placeable_node = self._load_model(model_name)
                if placeable_node:
                    placeable_node.reparentTo(root)
                    placeable_node.setPos(placeable.position.x, placeable.position.y, placeable.position.z)
                    placeable_node.setH(placeable.bearing)
    
    def _load_creatures(self, git, root: NodePath, module: Module) -> None:
        """Load creature models from GIT into Panda3D scene."""
        for git_creature in git.creatures:
            # Get creature model data using backend-agnostic loader
            model_data = self._data_loader.get_creature_model_data(git_creature, module)
            
            body_model = model_data.get('body_model')
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
                    
                    body_tex = model_data.get('body_texture')
                    if body_tex:
                        self._load_texture(body_tex, creature_node)
                    
                    # Load head if present
                    head_model = model_data.get('head_model')
                    if head_model and head_model.strip():
                        head_hook = creature_node.find("**/headhook")
                        if not head_hook.isEmpty():
                            head_node = self._load_model(head_model)
                            if head_node:
                                head_node.reparentTo(head_hook)
                                head_tex = model_data.get('head_texture')
                                if head_tex and head_tex.strip():
                                    self._load_texture(head_tex, head_node)
    
    def _load_cameras(self, git, root: NodePath) -> None:
        """Load camera nodes from GIT.
        
        References:
        ----------
            vendor/reone/src/libs/scene/di/module.cpp:300-350 - Camera loading
            Libraries/PyKotor/src/pykotor/resource/generics/git.py:345-450 - GITCamera structure
        """
        for i, camera in enumerate(git.cameras):
            camera_node = root.attachNewNode(f"camera_{i}")
            camera_node.setPos(camera.position.x, camera.position.y, camera.position.z + camera.height)
            
            # Convert KotOR quaternion (w, x, y, z) to Panda3D LQuaternion
            # GITCamera.orientation is Vector4 with (x, y, z, w) components
            quat = LQuaternion(camera.orientation.w, camera.orientation.x, camera.orientation.y, camera.orientation.z)
            
            # getHpr() returns (Heading, Pitch, Roll) as (euler[0], euler[1], euler[2])
            # setHpr() expects (Heading, Pitch, Roll) in the same order
            euler = quat.getHpr()
            camera_node.setHpr(euler[0], euler[1], euler[2])
    
    def _load_sounds(self, git, root: NodePath) -> None:
        """Load sound nodes from GIT."""
        for sound in git.sounds:
            sound_node = root.attachNewNode(sound.resref + ".uts")
            sound_node.setPos(sound.position.x, sound.position.y, sound.position.z)
    
    def _load_triggers(self, git, root: NodePath) -> None:
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
                model.setTexture(tex, 1