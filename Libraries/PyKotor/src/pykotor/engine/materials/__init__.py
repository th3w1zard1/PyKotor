"""Abstract material system interfaces.

This package defines backend-agnostic interfaces for material handling that can
be implemented by different rendering engines (OpenGL, Qt5, Panda3D, etc.).

References:
----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries


"""

from __future__ import annotations

from pykotor.engine.materials.base import IMaterial, IMaterialManager

__all__ = [
    "IMaterial",
    "IMaterialManager",
]

