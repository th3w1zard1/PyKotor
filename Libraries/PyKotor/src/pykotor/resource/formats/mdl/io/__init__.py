"""IO operations for MDL format."""
from __future__ import annotations

from pykotor.resource.formats.mdl.io.binary import (
    MDLBinaryNodeReader,
    ArrayDefinition,
    MDLBinaryLightReader,
    MDLBinaryEmitterReader,
    MDLBinaryReferenceReader,
    MDLBinaryTrimeshReader,
    MDLBinarySkinReader,
    MDLBinaryDanglyReader,
    MDLBinaryAABBReader,
    MDLBinaryAnimationReader,
    MDLDefaultBinaryNodeReader,
    MDLBinaryNodeReaderFactory
)

__all__ = [
    # Binary readers
    "MDLBinaryNodeReader",
    "ArrayDefinition",
    "MDLBinaryLightReader",
    "MDLBinaryEmitterReader",
    "MDLBinaryReferenceReader",
    "MDLBinaryTrimeshReader",
    "MDLBinarySkinReader",
    "MDLBinaryDanglyReader",
    "MDLBinaryAABBReader",
    "MDLBinaryAnimationReader",
    "MDLDefaultBinaryNodeReader",
    "MDLBinaryNodeReaderFactory"
]