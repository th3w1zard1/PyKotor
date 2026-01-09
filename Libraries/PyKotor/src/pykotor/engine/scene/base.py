"""Abstract scene graph base classes.

This module defines the abstract interfaces for scene graph management that can be
implemented by any rendering backend (OpenGL, Qt5, Panda3D, etc.).

References:
----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries


"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class FogProperties:
    """Fog rendering properties.
    
    This is backend-agnostic and can be used with any rendering system.
    
    References:
    ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries


    
    Attributes:
    ----------
        enabled: Whether fog is enabled
        color: RGB color of fog (0-1 range)
        near_plane: Distance where fog starts
        far_plane: Distance where fog is fully opaque
    """
    enabled: bool = False
    color: tuple[float, float, float] = (0.5, 0.5, 0.5)
    near_plane: float = 10.0
    far_plane: float = 100.0


class ISceneGraph(ABC):
    """Abstract interface for scene graph management.
    
    This interface defines the contract that all scene graph implementations must follow,
    regardless of the underlying rendering backend (OpenGL, Qt5, Panda3D, etc.).
    
    References:
    ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries


    
    Attributes:
    ----------
        name: Name of this scene graph (e.g., "area_m01aa")
    """
    
    def __init__(self, name: str):
        """Initialize the scene graph.
        
        Args:
        ----
            name: Name of this scene graph
        """
        self.name = name
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all scene graph content.
        
        Removes all models, walkmeshes, and lights from the scene.
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries


        """
        ...
    
    @abstractmethod
    def update(self, dt: float) -> None:
        """Update the scene graph for the current frame.
        
        Args:
        ----
            dt: Delta time since last update (seconds)
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries


        """
        ...
    
    @abstractmethod
    def add_model_root(self, model: Any) -> None:
        """Add a model root to the scene.
        
        Args:
        ----
            model: Backend-specific model object
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries


        """
        ...
    
    @abstractmethod
    def remove_model_root(self, model: Any) -> None:
        """Remove a model root from the scene.
        
        Args:
        ----
            model: Backend-specific model object
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries


        """
        ...
    
    @abstractmethod
    def set_ambient_light_color(self, color: tuple[float, float, float]) -> None:
        """Set the ambient light color.
        
        Args:
        ----
            color: RGB color tuple (0-1 range)
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries


        """
        ...
    
    @abstractmethod
    def add_directional_light(
        self,
        name: str,
        color: tuple[float, float, float],
        direction: tuple[float, float, float]
    ) -> Any:
        """Add a directional light to the scene.
        
        Args:
        ----
            name: Name of the light
            color: RGB color tuple (0-1 range)
            direction: Direction vector the light is pointing
        
        Returns:
        -------
            Backend-specific light object
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries


        """
        ...
    
    @abstractmethod
    def add_point_light(
        self,
        name: str,
        color: tuple[float, float, float],
        position: tuple[float, float, float],
        radius: float
    ) -> Any:
        """Add a point light to the scene.
        
        Args:
        ----
            name: Name of the light
            color: RGB color tuple (0-1 range)
            position: XYZ position of the light
            radius: Maximum range of the light
        
        Returns:
        -------
            Backend-specific light object
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries


        """
        ...
    
    @abstractmethod
    def set_fog(
        self,
        enabled: bool,
        color: tuple[float, float, float] | None = None,
        near: float | None = None,
        far: float | None = None
    ) -> None:
        """Set fog properties for the scene.
        
        Args:
        ----
            enabled: Whether fog is enabled
            color: RGB color of fog (optional)
            near: Distance where fog starts (optional)
            far: Distance where fog is fully opaque (optional)
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries


        """
        ...
    
    @abstractmethod
    def get_fog(self) -> FogProperties:
        """Get current fog properties.
        
        Returns:
        -------
            Current fog properties
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries


        """
        ...

