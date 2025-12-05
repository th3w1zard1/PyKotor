"""Geometry utilities for KotOR model processing.

This module provides reusable geometry operations that are not specific to any
particular rendering backend. These utilities can be used by any rendering
backend implementation.

References:
----------
    Libraries/PyKotor/src/pykotor/resource/formats/mdl/io_mdl.py:1448-1577 - Tangent space calculation
    vendor/mdlops/MDLOpsM.pm:5470-5596 - Tangent space calculation
    vendor/reone/src/libs/graphics/mesh.cpp:200-280 - Vertex data processing
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# Runtime imports - these are used in the function bodies
from utility.common.geometry import Vector3

if TYPE_CHECKING:
    from pykotor.resource.formats.mdl.mdl_data import MDLMesh


def compute_per_vertex_tangent_space(
    mesh: MDLMesh,
) -> dict[int, tuple[Vector3, Vector3]]:
    """Compute per-vertex tangent and binormal vectors for a mesh.
    
    This function computes tangent space basis vectors for each vertex by:
    1. Computing tangent/bitangent for each face
    2. Accumulating contributions from all faces sharing each vertex
    3. Averaging and normalizing the results
    
    Args:
    ----
        mesh: MDL mesh with vertex positions, UVs, and faces
    
    Returns:
    -------
        Dictionary mapping vertex index to (tangent, binormal) tuple
    
    References:
    ----------
        Libraries/PyKotor/src/pykotor/resource/formats/mdl/io_mdl.py:1449-1578
        vendor/mdlops/MDLOpsM.pm:5470-5596 - Tangent space calculation
        vendor/reone/src/libs/graphics/mesh.cpp:200-280 - Vertex data processing
    """
    from pykotor.resource.formats.mdl.io_mdl import _calculate_face_normal, _calculate_tangent_space
    
    vertex_tangents: dict[int, list[Vector3]] = {}
    vertex_binormals: dict[int, list[Vector3]] = {}
    
    # Compute per-face tangent space
    for face in mesh.faces:
        v1 = mesh.vertex_positions[face.v1]
        v2 = mesh.vertex_positions[face.v2]
        v3 = mesh.vertex_positions[face.v3]
        
        if face.v1 >= len(mesh.vertex_uv) or face.v2 >= len(mesh.vertex_uv) or face.v3 >= len(mesh.vertex_uv):
            continue
        
        uv1 = mesh.vertex_uv[face.v1]
        uv2 = mesh.vertex_uv[face.v2]
        uv3 = mesh.vertex_uv[face.v3]
        
        face_normal, _ = _calculate_face_normal(v1, v2, v3)
        tangent, binormal = _calculate_tangent_space(v1, v2, v3, uv1, uv2, uv3, face_normal)
        
        # Accumulate for each vertex
        for v_idx in [face.v1, face.v2, face.v3]:
            if v_idx not in vertex_tangents:
                vertex_tangents[v_idx] = []
                vertex_binormals[v_idx] = []
            vertex_tangents[v_idx].append(tangent)
            vertex_binormals[v_idx].append(binormal)
    
    # Average accumulated tangents/binormals
    result = {}
    for v_idx in vertex_tangents:
        # Average tangents
        avg_tangent = Vector3(0, 0, 0)
        for t in vertex_tangents[v_idx]:
            avg_tangent = Vector3(avg_tangent.x + t.x, avg_tangent.y + t.y, avg_tangent.z + t.z)
        count = len(vertex_tangents[v_idx])
        avg_tangent = Vector3(avg_tangent.x / count, avg_tangent.y / count, avg_tangent.z / count)
        
        # Normalize
        length = (avg_tangent.x**2 + avg_tangent.y**2 + avg_tangent.z**2) ** 0.5
        if length > 0:
            avg_tangent = Vector3(avg_tangent.x / length, avg_tangent.y / length, avg_tangent.z / length)
        
        # Average binormals
        avg_binormal = Vector3(0, 0, 0)
        for b in vertex_binormals[v_idx]:
            avg_binormal = Vector3(avg_binormal.x + b.x, avg_binormal.y + b.y, avg_binormal.z + b.z)
        avg_binormal = Vector3(avg_binormal.x / count, avg_binormal.y / count, avg_binormal.z / count)
        
        # Normalize
        length = (avg_binormal.x**2 + avg_binormal.y**2 + avg_binormal.z**2) ** 0.5
        if length > 0:
            avg_binormal = Vector3(avg_binormal.x / length, avg_binormal.y / length, avg_binormal.z / length)
        
        result[v_idx] = (avg_tangent, avg_binormal)
    
    return result


def determine_vertex_format_requirements(mesh: MDLMesh) -> dict[str, bool]:
    """Determine what vertex format attributes are needed for a mesh.
    
    This is a backend-agnostic way to determine vertex format requirements
    that can be used by any rendering backend implementation.
    
    Args:
    ----
        mesh: MDL mesh to analyze
    
    Returns:
    -------
        Dictionary with boolean flags for each attribute type:
        - has_normals: True if mesh has vertex normals
        - has_tangent_space: True if tangent space should be computed
        - has_lightmap: True if mesh has lightmap UVs
        - has_skinning: True if mesh has bone weights
        - has_uv2: True if mesh has second UV set
    
    References:
    ----------
        vendor/reone/src/libs/graphics/mesh.cpp:120-150 - Vertex layout
        vendor/KotOR.js/src/three/odyssey/OdysseyModel3D.ts:1169-1197 - Geometry attributes
    """
    return {
        "has_normals": len(mesh.vertex_normals) > 0,
        "has_tangent_space": len(mesh.vertex_normals) > 0 and len(mesh.faces) > 0 and len(mesh.vertex_uv) > 0,
        "has_lightmap": mesh.has_lightmap and len(mesh.vertex_uv2) > 0,
        "has_skinning": mesh.skin is not None,
        "has_uv2": len(mesh.vertex_uv2) > 0,
    }

