"""Data structures and exceptions for MDL format."""
from __future__ import annotations

from pykotor.resource.formats.mdl.data.exceptions import (
    MDLError,
    MDLFormatError,
    MDLVersionError,
    MDLValidationError,
    MDLReadError,
    MDLWriteError,
    MDLNodeError,
    MDLControllerError,
    MDLGeometryError,
    MDLAnimationError
)

from pykotor.resource.formats.mdl.data.nodes import (
    MDLNode,
    MDLLightNode,
    MDLEmitterNode,
    MDLReferenceNode,
    MDLTrimeshNode,
    MDLSkinNode,
    MDLDanglyNode,
    MDLAABBNode,
    MDLNodeAnimation,
    MDLAnimationEvent
)

__all__ = [
    # Exceptions
    "MDLError",
    "MDLFormatError",
    "MDLVersionError",
    "MDLValidationError",
    "MDLReadError",
    "MDLWriteError",
    "MDLNodeError",
    "MDLControllerError",
    "MDLGeometryError",
    "MDLAnimationError",

    # Node types
    "MDLNode",
    "MDLLightNode",
    "MDLEmitterNode",
    "MDLReferenceNode",
    "MDLTrimeshNode",
    "MDLSkinNode",
    "MDLDanglyNode",
    "MDLAABBNode",
    "MDLNodeAnimation",
    "MDLAnimationEvent"
]