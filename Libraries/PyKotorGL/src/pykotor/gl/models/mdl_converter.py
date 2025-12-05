"""Abstract MDL to geometry conversion utilities.

This module provides backend-agnostic geometry conversion utilities that work
with PyKotor's MDL data structures. These utilities can be used by both
OpenGL (PyKotorGL) and Panda3D (PyKotorEngine) implementations.

The actual rendering backend integration (OpenGL buffers, Panda3D GeomNodes)
should be handled in the respective backend modules.

References:
----------
    vendor/reone/src/libs/graphics/mesh.cpp:100-350 - Mesh conversion
    vendor/KotOR.js/src/three/odyssey/OdysseyModel3D.ts:150-400 - Geometry creation
    Libraries/PyKotor/src/pykotor/common/geometry_utils.py - Geometry utilities
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.mdl.mdl_data import MDLMesh, MDLNode
    from utility.common.geometry import Vector2, Vector3


class VertexFormatRequirements:
    """Vertex format requirements for a mesh.
    
    This class encapsulates the vertex format requirements in a backend-agnostic way,
    allowing both OpenGL and Panda3D implementations to determine what attributes
    are needed.
    
    Attributes:
    ----------
        has_normals: True if mesh has vertex normals
        has_tangent_space: True if tangent space should be computed
        has_lightmap: True if mesh has lightmap UVs
        has_skinning: True if mesh has bone weights
        has_uv2: True if mesh has second UV set
    """
    
    def __init__(
        self,
        has_normals: bool,
        has_tangent_space: bool,
        has_lightmap: bool,
        has_skinning: bool,
        has_uv2: bool,
    ):
        self.has_normals = has_normals
        self.has_tangent_space = has_tangent_space
        self.has_lightmap = has_lightmap
        self.has_skinning = has_skinning
        self.has_uv2 = has_uv2
    
    @classmethod
    def from_mesh(cls, mesh: MDLMesh) -> VertexFormatRequirements:
        """Create requirements from an MDL mesh.
        
        Args:
        ----
            mesh: MDL mesh to analyze
        
        Returns:
        -------
            VertexFormatRequirements object
        """
        from pykotor.common.geometry_utils import determine_vertex_format_requirements
        reqs = determine_vertex_format_requirements(mesh)
        return cls(
            has_normals=reqs["has_normals"],
            has_tangent_space=reqs["has_tangent_space"],
            has_lightmap=reqs["has_lightmap"],
            has_skinning=reqs["has_skinning"],
            has_uv2=reqs["has_uv2"],
        )


def get_node_type_priority(mdl_node: "MDLNode") -> int:
    """Get node type priority for conversion order.
    
    Some node types (like skin, dangly, saber) also have mesh data, so we need
    to prioritize which converter to use. Higher priority = converted first.
    
    Args:
    ----
        mdl_node: MDL node to check
    
    Returns:
    -------
        Priority value (higher = more important)
    
    References:
    ----------
        vendor/reone/src/libs/scene/node/model.cpp:62-69 - Node type checking
        vendor/KotOR.js/src/three/odyssey/OdysseyModel3D.ts:987-1004 - Node type priority
    """
    # Priority order (higher = checked first):
    # AABB > Saber > Dangly > Skin > Mesh > Light > Emitter > Reference > Dummy
    if mdl_node.aabb:
        return 8
    if mdl_node.saber:
        return 7
    if mdl_node.dangly:
        return 6
    if mdl_node.skin:
        return 5
    if mdl_node.mesh:
        return 4
    if mdl_node.light:
        return 3
    if mdl_node.emitter:
        return 2
    if mdl_node.reference:
        return 1
    return 0  # Dummy node


def get_node_converter_type(mdl_node: "MDLNode") -> str:
    """Get the converter type string for an MDL node.
    
    Args:
    ----
        mdl_node: MDL node to check
    
    Returns:
    -------
        Converter type string: "aabb", "saber", "dangly", "skin", "mesh", 
        "light", "emitter", "reference", or "dummy"
    
    References:
    ----------
        vendor/reone/src/libs/scene/node/model.cpp:62-69 - Node type checking
    """
    # Check in priority order
    if mdl_node.aabb:
        return "aabb"
    if mdl_node.saber:
        return "saber"
    if mdl_node.dangly:
        return "dangly"
    if mdl_node.skin:
        return "skin"
    if mdl_node.mesh:
        return "mesh"
    if mdl_node.light:
        return "light"
    if mdl_node.emitter:
        return "emitter"
    if mdl_node.reference:
        return "reference"
    return "dummy"


def should_reverse_winding_order(backend: str = "opengl") -> bool:
    """Determine if face winding order should be reversed.
    
    KotOR uses clockwise winding, but different backends may expect different orders.
    
    Args:
    ----
        backend: Backend name ("opengl", "panda3d", "threejs")
    
    Returns:
    -------
        True if winding order should be reversed (KotOR CW -> backend CCW)
    
    References:
    ----------
        vendor/xoreos/src/graphics/mesh.cpp:300 - Winding order reversal
        vendor/KotOR.js/src/three/odyssey/OdysseyModel3D.ts:1169 - No reversal (Three.js handles it)
    """
    # Backend-specific winding order requirements
    # OpenGL and Panda3D typically expect CCW, so we reverse from KotOR's CW
    # Three.js handles it internally, so no reversal needed
    if backend == "threejs":
        return False
    # Default: OpenGL and Panda3D need reversal
    return True

