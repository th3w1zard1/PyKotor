"""Abstract scene graph interfaces.

This module provides abstract base classes for scene graph management that can be
implemented by different rendering backends.

References:
----------
        Based on swkotor.exe scene graph:
        - Scene management and rendering pipeline
        - Area loading and room visibility (VIS files)
        - Original BioWare engine binaries (swkotor.exe, swkotor2.exe)


"""

from __future__ import annotations

from pykotor.engine.scene.base import ISceneGraph, FogProperties

__all__ = [
    "ISceneGraph",
    "FogProperties",
]

