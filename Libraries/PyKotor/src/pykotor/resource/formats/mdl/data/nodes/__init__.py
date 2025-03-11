"""Node data structures for MDL format."""
from __future__ import annotations

from pykotor.resource.formats.mdl.data.nodes.node import MDLNode
from pykotor.resource.formats.mdl.data.nodes.light import MDLLightNode
from pykotor.resource.formats.mdl.data.nodes.emitter import MDLEmitterNode
from pykotor.resource.formats.mdl.data.nodes.reference import MDLReferenceNode
from pykotor.resource.formats.mdl.data.nodes.trimesh import MDLTrimeshNode
from pykotor.resource.formats.mdl.data.nodes.skin import MDLSkinNode
from pykotor.resource.formats.mdl.data.nodes.dangly import MDLDanglyNode
from pykotor.resource.formats.mdl.data.nodes.aabb import MDLAABBNode
from pykotor.resource.formats.mdl.data.nodes.anim import MDLNodeAnimation, MDLAnimationEvent
from pykotor.resource.formats.mdl.data.nodes.saber import MDLSaberNode

__all__ = [
    "MDLNode",
    "MDLLightNode",
    "MDLEmitterNode",
    "MDLReferenceNode",
    "MDLTrimeshNode",
    "MDLSkinNode",
    "MDLDanglyNode",
    "MDLAABBNode",
    "MDLNodeAnimation",
    "MDLAnimationEvent",
    "MDLSaberNode"
]