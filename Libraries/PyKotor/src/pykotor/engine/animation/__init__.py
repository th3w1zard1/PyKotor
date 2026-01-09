"""Abstract animation system interfaces.

This module provides abstract base classes for animation that can be implemented
by different rendering backends.

References:
----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/odyssey/controllers


"""

from __future__ import annotations

from pykotor.engine.animation.base import (
    IAnimationController,
    IAnimationState,
    IAnimationManager,
)

__all__ = [
    "IAnimationController",
    "IAnimationState",
    "IAnimationManager",
]

