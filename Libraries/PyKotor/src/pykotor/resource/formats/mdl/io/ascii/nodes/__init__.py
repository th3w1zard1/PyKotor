from __future__ import annotations

from pykotor.resource.formats.mdl.io.ascii.nodes.base_node_reader import MDLASCIINodeReader
from pykotor.resource.formats.mdl.io.ascii.nodes.anim_reader import MDLASCIIAnimationReader
from pykotor.resource.formats.mdl.io.ascii.nodes.light_reader import MDLASCIILightReader
from pykotor.resource.formats.mdl.io.ascii.nodes.emitter_reader import MDLASCIIEmitterReader
from pykotor.resource.formats.mdl.io.ascii.nodes.reference_reader import MDLASCIIReferenceReader
from pykotor.resource.formats.mdl.io.ascii.nodes.skin_reader import MDLASCIISkinReader
from pykotor.resource.formats.mdl.io.ascii.nodes.dangly_reader import MDLASCIIDanglyReader
from pykotor.resource.formats.mdl.io.ascii.nodes.aabb_reader import MDLASCIIAABBReader
from pykotor.resource.formats.mdl.io.ascii.nodes.trimesh_reader import MDLASCIITrimeshReader
from pykotor.resource.formats.mdl.io.ascii.nodes.saber_reader import MDLASCIISaberReader

__all__ = [
    "MDLASCIINodeReader",
    "MDLASCIIAnimationReader",
    "MDLASCIILightReader",
    "MDLASCIIEmitterReader",
    "MDLASCIIReferenceReader",
    "MDLASCIISkinReader",
    "MDLASCIIDanglyReader",
    "MDLASCIIAABBReader",
    "MDLASCIISaberReader"
]
