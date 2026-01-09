"""Panda3D implementation of KotOR engine.

This module provides the main engine class using Panda3D's ShowBase.

References:
----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        /panda3d/panda3d-docs/programming/showbase - ShowBase documentation


"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from direct.showbase.ShowBase import ShowBase

from pykotor.engine.panda3d.materials import Panda3DMaterialManager
from pykotor.engine.panda3d.module_loader import ModuleLoader
from pykotor.engine.panda3d.scene_graph import Panda3DSceneGraph

from panda3d.core import (
    AmbientLight,
    AntialiasAttrib,
    DirectionalLight,
    Vec4,
    loadPrcFileData,
)

if TYPE_CHECKING:
    from panda3d.core import (
        NodePath,
    )


class KotorEngine(ShowBase):
    """Main KotOR engine class using Panda3D.
    
    This class extends ShowBase to provide KotOR-specific functionality.
    
    References:
    ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        /panda3d/panda3d-docs/introduction/tutorial/starting-panda3d - ShowBase
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/Game.ts


    
    Attributes:
    ----------
        scene_root: Root NodePath for KotOR scene content
        scene_graph: Scene graph manager
    """
    
    def __init__(self):
        """Initialize the KotOR engine.
        
        Sets up Panda3D configuration and initializes the rendering system.
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        /panda3d/panda3d-docs/programming/configuration/accessing-config-vars - loadPrcFileData


        """
        # Configure Panda3D before ShowBase initialization
        loadPrcFileData("", "window-title KotOR Engine - PyKotor")
        
        # Window size
        loadPrcFileData("", "win-size 1280 720")
        
        # Frame rate meter for debugging
        loadPrcFileData("", "show-frame-rate-meter true")
        
        # V-sync
        loadPrcFileData("", "sync-video false")
        
        # OpenGL version
        loadPrcFileData("", "gl-version 3 3")
        
        # Notification level
        loadPrcFileData("", "notify-level warning")
        
        # Antialiasing
        loadPrcFileData("", "default-antialias-enable true")
        
        # Initialize ShowBase
        # Reference: /panda3d/panda3d-docs - ShowBase.__init__(self)
        ShowBase.__init__(self)
        
        # Set up antialiasing on the scene
        # Reference: /panda3d/panda3d-docs - render.setAntialias(AntialiasAttrib.MAuto)
        self.render.setAntialias(AntialiasAttrib.MAuto)
        
        # Create scene root for KotOR content
        # References:
        # -  - SceneGraph root
        # - /panda3d/panda3d-docs - NodePath creation
        self.scene_root: NodePath = self.render.attachNewNode("kotor_scene")
        
        # Create scene graph manager
        self.scene_graph: Panda3DSceneGraph = Panda3DSceneGraph("main_scene", self.scene_root)
        self.material_manager: Panda3DMaterialManager = Panda3DMaterialManager(self.loader, Path.cwd())
        
        # Module loader will be initialized when installation is set
        self.module_loader: ModuleLoader | None = None
        
        # Set up default lighting
        #
        self._setup_default_lighting()
        
        # Configure camera
        # References:
        # -  - Camera setup
        # - /panda3d/panda3d-docs - camera.setPos()
        self.camera.setPos(0, -10, 2)
        self.camera.lookAt(0, 0, 0)
        
        print("PyKotorEngine initialized (Panda3D)")
        print(f"Panda3D version: {self.getVersionString()}")
        print(f"OpenGL version: {self.win.getGsg().getDriverVersion()}")
    
    def _setup_default_lighting(self) -> None:
        """Set up default scene lighting.
        
        Creates ambient and directional lights.
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        /panda3d/panda3d-docs - AmbientLight, DirectionalLight


        """
        # Ambient light
        #
        ambient = AmbientLight("ambient_light")
        ambient.setColor(Vec4(0.3, 0.3, 0.3, 1.0))
        self.ambient_light = self.render.attachNewNode(ambient)
        self.scene_root.setLight(self.ambient_light)
        
        # Directional light (sun)
        #
        sun = DirectionalLight("sun_light")
        sun.setColor(Vec4(0.8, 0.8, 0.7, 1.0))
        self.sun_light = self.render.attachNewNode(sun)
        self.sun_light.setHpr(45, -45, 0)
        self.scene_root.setLight(self.sun_light)
    
    def run_game_loop(self) -> None:
        """Start the main game loop.
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        /panda3d/panda3d-docs - base.run()


        """
        print("Starting KotOR Engine main loop...")
        self.run()


def create_engine() -> KotorEngine:
    """Factory function to create a KotorEngine instance.
    
    Returns:
    -------
        Initialized KotorEngine
    
    References:
    ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries


    """
    return KotorEngine()

