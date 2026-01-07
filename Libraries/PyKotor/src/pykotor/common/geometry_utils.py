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

import math
from typing import TYPE_CHECKING, Any, overload

# Runtime imports - these are used in the function bodies
from utility.common.geometry import Matrix4, Vector3, Vector4

if TYPE_CHECKING:
    from numpy import ndarray

    from pykotor.resource.formats.mdl.mdl_data import MDLMesh, MDLSkin


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
        
        if face.v1 >= len(mesh.vertex_uvs) or face.v2 >= len(mesh.vertex_uvs) or face.v3 >= len(mesh.vertex_uvs):
            continue
        
        uv1 = mesh.vertex_uvs[face.v1]
        uv2 = mesh.vertex_uvs[face.v2]
        uv3 = mesh.vertex_uvs[face.v3]
        
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
    result: dict[int, tuple[Vector3, Vector3]] = {}
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
        "has_normals": len(mesh.vertex_normals) > 0 if mesh.vertex_normals is not None else False,
        "has_tangent_space": (len(mesh.vertex_normals) > 0 if mesh.vertex_normals is not None else False) and len(mesh.faces) > 0 and len(mesh.vertex_uvs) > 0,
        "has_lightmap": mesh.has_lightmap and (len(mesh.vertex_uv2) > 0 if mesh.vertex_uv2 is not None else False),
        "has_skinning": isinstance(mesh, MDLSkin) and mesh is not None,
        "has_uv2": len(mesh.vertex_uv2) > 0 if mesh.vertex_uv2 is not None else False,
    }


# GLM-compatible transformation functions
# These provide a GLM-style API for matrix and vector operations

@overload
def translate(v: Vector3, /) -> Matrix4: ...
@overload
def translate(v: Any, /) -> Any: ...
def translate(v: Any, /) -> Any:
    """Create a translation matrix.
    
    Args:
    ----
        v: Translation vector (Vector3).
    
    Returns:
    -------
        Matrix4: Translation matrix.
    """
    if not isinstance(v, Vector3):
        raise TypeError(f"translate requires Vector3, got {type(v)}")
    result = Matrix4(1.0)  # Start with identity matrix
    result._data[3][0] = v.x
    result._data[3][1] = v.y
    result._data[3][2] = v.z
    return result


@overload
def rotate(m: Matrix4, angle: float, axis: Vector3, /) -> Matrix4: ...
@overload
def rotate(m: Any, angle: float, axis: Any, /) -> Any: ...
def rotate(m: Any, angle: float, axis: Any, /) -> Any:
    """Rotate a matrix by angle (radians) around axis.
    
    Args:
    ----
        m: Matrix to rotate.
        angle: Rotation angle in radians.
        axis: Rotation axis (Vector3).
    
    Returns:
    -------
        Matrix4: Rotated matrix.
    """
    if not isinstance(m, Matrix4) or not isinstance(axis, Vector3):
        raise TypeError(f"rotate requires Matrix4, float, Vector3, got {type(m)}, {type(axis)}")
    # Normalize axis
    axis_length = math.sqrt(axis.x**2 + axis.y**2 + axis.z**2)
    if axis_length == 0:
        return Matrix4(m)

    x = axis.x / axis_length
    y = axis.y / axis_length
    z = axis.z / axis_length

    c = math.cos(angle)
    s = math.sin(angle)
    t = 1 - c

    # Rotation matrix
    rot = Matrix4(0.0)
    rot._data[0][0] = t * x * x + c
    rot._data[0][1] = t * x * y + s * z
    rot._data[0][2] = t * x * z - s * y
    rot._data[1][0] = t * x * y - s * z
    rot._data[1][1] = t * y * y + c
    rot._data[1][2] = t * y * z + s * x
    rot._data[2][0] = t * x * z + s * y
    rot._data[2][1] = t * y * z - s * x
    rot._data[2][2] = t * z * z + c

    return m * rot


@overload
def mat4_cast(x: Vector4, /) -> Matrix4: ...
@overload
def mat4_cast(x: Any, /) -> Any: ...
def mat4_cast(x: Any, /) -> Any:
    """Convert a quaternion (Vector4) to a 4x4 rotation matrix.
    
    Args:
    ----
        x: Quaternion as Vector4 (w, x, y, z order expected, but Vector4 is x, y, z, w).
           For quaternions, typically Vector4(w, x, y, z) is used.
    
    Returns:
    -------
        Matrix4: Rotation matrix.
    
    Note:
    ----
        Vector4 stores (x, y, z, w) but quaternions are typically (w, x, y, z).
        This function assumes Vector4 quaternion format is (x, y, z, w).
    """
    if not isinstance(x, Vector4):
        raise TypeError(f"mat4_cast requires Vector4, got {type(x)}")
    result = Matrix4(0.0)

    # Vector4 is (x, y, z, w), quaternion is (w, x, y, z)
    qw, qx, qy, qz = x.w, x.x, x.y, x.z

    result._data[0][0] = 1 - 2 * qy * qy - 2 * qz * qz
    result._data[0][1] = 2 * qx * qy + 2 * qz * qw
    result._data[0][2] = 2 * qx * qz - 2 * qy * qw

    result._data[1][0] = 2 * qx * qy - 2 * qz * qw
    result._data[1][1] = 1 - 2 * qx * qx - 2 * qz * qz
    result._data[1][2] = 2 * qy * qz + 2 * qx * qw

    result._data[2][0] = 2 * qx * qz + 2 * qy * qw
    result._data[2][1] = 2 * qy * qz - 2 * qx * qw
    result._data[2][2] = 1 - 2 * qx * qx - 2 * qy * qy

    return result


@overload
def inverse(m: Matrix4, /) -> Matrix4: ...
@overload
def inverse(m: Any, /) -> Any: ...
def inverse(m: Any, /) -> Any:
    """Calculate the inverse of a matrix.
    
    Args:
    ----
        m: Matrix to invert.
    
    Returns:
    -------
        Matrix4: Inverse matrix, or identity if singular.
    """
    if not isinstance(m, Matrix4):
        raise TypeError(f"inverse requires Matrix4, got {type(m)}")
    # Simple 4x4 matrix inversion using Gaussian elimination
    # For numerical stability, we use a basic implementation
    # In production, numpy.linalg.inv would be preferred but we avoid dependencies
    
    try:
        # Create augmented matrix [M|I]
        aug = [[0.0] * 8 for _ in range(4)]
        for i in range(4):
            for j in range(4):
                aug[i][j] = m._data[i][j]
            aug[i][i + 4] = 1.0
        
        # Gaussian elimination with partial pivoting
        for col in range(4):
            # Find pivot
            max_row = col
            for row in range(col + 1, 4):
                if abs(aug[row][col]) > abs(aug[max_row][col]):
                    max_row = row
            
            # Swap rows
            aug[col], aug[max_row] = aug[max_row], aug[col]
            
            # Check for singular matrix
            if abs(aug[col][col]) < 1e-10:
                return Matrix4(1.0)  # Return identity if singular
            
            # Normalize pivot row
            pivot = aug[col][col]
            for j in range(8):
                aug[col][j] /= pivot
            
            # Eliminate column
            for row in range(4):
                if row != col:
                    factor = aug[row][col]
                    for j in range(8):
                        aug[row][j] -= factor * aug[col][j]
        
        # Extract inverse
        result = Matrix4(0.0)
        for i in range(4):
            for j in range(4):
                result._data[i][j] = aug[i][j + 4]
        
        return result
    except Exception:
        # Return identity matrix if inversion fails
        return Matrix4(1.0)


def perspective(fovy: float, aspect: float, near: float, far: float, /) -> Matrix4:
    """Create a perspective projection matrix.
    
    Args:
    ----
        fovy: Field of view in degrees.
        aspect: Aspect ratio (width/height).
        near: Near clipping plane.
        far: Far clipping plane.
    
    Returns:
    -------
        Matrix4: Perspective projection matrix.
    """
    result = Matrix4(0.0)

    fov_rad = math.radians(fovy)
    tan_half_fov = math.tan(fov_rad / 2.0)

    result._data[0][0] = 1.0 / (aspect * tan_half_fov)
    result._data[1][1] = 1.0 / tan_half_fov
    result._data[2][2] = -(far + near) / (far - near)
    result._data[2][3] = -1.0
    result._data[3][2] = -(2.0 * far * near) / (far - near)

    return result


@overload
def normalize(x: Vector3, /) -> Vector3: ...
@overload
def normalize(x: Any, /) -> Any: ...
def normalize(x: Any, /) -> Any:
    """Normalize a vector.
    
    Args:
    ----
        x: Vector to normalize (Vector3).
    
    Returns:
    -------
        Vector3: Normalized vector.
    """
    if not isinstance(x, Vector3):
        raise TypeError(f"normalize requires Vector3, got {type(x)}")
    v = x
    length_val = math.sqrt(v.x**2 + v.y**2 + v.z**2)
    if length_val == 0:
        return Vector3(0, 0, 0)
    return Vector3(v.x / length_val, v.y / length_val, v.z / length_val)


@overload
def cross(x: Vector3, y: Vector3, /) -> Vector3: ...
@overload
def cross(x: Any, y: Any, /) -> Any: ...
def cross(x: Any, y: Any, /) -> Any:
    """Calculate the cross product of two vectors.
    
    Args:
    ----
        x: First vector (Vector3).
        y: Second vector (Vector3).
    
    Returns:
    -------
        Vector3: Cross product.
    """
    if isinstance(x, Vector3) and isinstance(y, Vector3):
        return Vector3(
            x.y * y.z - x.z * y.y,
            x.z * y.x - x.x * y.z,
            x.x * y.y - x.y * y.x,
        )
    raise TypeError(f"Unsupported types for cross: {type(x)}, {type(y)}")


@overload
def decompose(modelMatrix: Matrix4, scale: Vector3, orientation: Vector4, translation: Vector3, skew: Vector3, perspective_vec: Vector4, /) -> bool: ...
@overload
def decompose(modelMatrix: Any, scale: Any, orientation: Any, translation: Any, skew: Any, perspective_vec: Any, /) -> bool: ...
def decompose(
    modelMatrix: Any,
    scale: Any,
    orientation: Any,
    translation: Any,
    skew: Any,
    perspective_vec: Any,
    /,
) -> bool:
    """Decompose a transformation matrix into its components.
    
    Args:
    ----
        modelMatrix: The transformation matrix to decompose.
        scale: Output scale vector (Vector3).
        orientation: Output rotation quaternion (Vector4, as x, y, z, w).
        translation: Output translation vector (Vector3).
        skew: Output skew vector (Vector3, not implemented).
        perspective_vec: Output perspective vector (Vector4, not implemented).
    
    Returns:
    -------
        bool: True if decomposition was successful.
    """
    if (
        not isinstance(modelMatrix, Matrix4)
        or not isinstance(scale, Vector3)
        or not isinstance(orientation, Vector4)
        or not isinstance(translation, Vector3)
        or not isinstance(skew, Vector3)
        or not isinstance(perspective_vec, Vector4)
    ):
        raise TypeError("decompose requires Matrix4, Vector3, Vector4, Vector3, Vector3, Vector4 arguments")
    m = modelMatrix._data

    # Extract translation
    translation.x = float(m[3][0])
    translation.y = float(m[3][1])
    translation.z = float(m[3][2])

    # Extract scale
    scale_x = math.sqrt(m[0][0] ** 2 + m[0][1] ** 2 + m[0][2] ** 2)
    scale_y = math.sqrt(m[1][0] ** 2 + m[1][1] ** 2 + m[1][2] ** 2)
    scale_z = math.sqrt(m[2][0] ** 2 + m[2][1] ** 2 + m[2][2] ** 2)

    scale.x = scale_x
    scale.y = scale_y
    scale.z = scale_z

    # Normalize matrix to extract rotation
    if scale_x == 0 or scale_y == 0 or scale_z == 0:
        orientation.x = 0.0
        orientation.y = 0.0
        orientation.z = 0.0
        orientation.w = 1.0
        return True

    rot_matrix = [
        [m[0][0] / scale_x, m[0][1] / scale_x, m[0][2] / scale_x],
        [m[1][0] / scale_y, m[1][1] / scale_y, m[1][2] / scale_y],
        [m[2][0] / scale_z, m[2][1] / scale_z, m[2][2] / scale_z],
    ]

    # Convert rotation matrix to quaternion
    trace = rot_matrix[0][0] + rot_matrix[1][1] + rot_matrix[2][2]

    if trace > 0:
        s = math.sqrt(trace + 1.0) * 2
        orientation.w = 0.25 * s
        orientation.x = (rot_matrix[2][1] - rot_matrix[1][2]) / s
        orientation.y = (rot_matrix[0][2] - rot_matrix[2][0]) / s
        orientation.z = (rot_matrix[1][0] - rot_matrix[0][1]) / s
    elif rot_matrix[0][0] > rot_matrix[1][1] and rot_matrix[0][0] > rot_matrix[2][2]:
        s = math.sqrt(1.0 + rot_matrix[0][0] - rot_matrix[1][1] - rot_matrix[2][2]) * 2
        orientation.w = (rot_matrix[2][1] - rot_matrix[1][2]) / s
        orientation.x = 0.25 * s
        orientation.y = (rot_matrix[0][1] + rot_matrix[1][0]) / s
        orientation.z = (rot_matrix[0][2] + rot_matrix[2][0]) / s
    elif rot_matrix[1][1] > rot_matrix[2][2]:
        s = math.sqrt(1.0 + rot_matrix[1][1] - rot_matrix[0][0] - rot_matrix[2][2]) * 2
        orientation.w = (rot_matrix[0][2] - rot_matrix[2][0]) / s
        orientation.x = (rot_matrix[0][1] + rot_matrix[1][0]) / s
        orientation.y = 0.25 * s
        orientation.z = (rot_matrix[1][2] + rot_matrix[2][1]) / s
    else:
        s = math.sqrt(1.0 + rot_matrix[2][2] - rot_matrix[0][0] - rot_matrix[1][1]) * 2
        orientation.w = (rot_matrix[1][0] - rot_matrix[0][1]) / s
        orientation.x = (rot_matrix[0][2] + rot_matrix[2][0]) / s
        orientation.y = (rot_matrix[1][2] + rot_matrix[2][1]) / s
        orientation.z = 0.25 * s

    return True


@overload
def eulerAngles(x: Vector4, /) -> Vector3: ...
@overload
def eulerAngles(x: Any, /) -> Any: ...
def eulerAngles(x: Any, /) -> Any:
    """Convert a quaternion (Vector4) to Euler angles (in radians).
    
    Args:
    ----
        x: Quaternion as Vector4 (x, y, z, w format).
    
    Returns:
    -------
        Vector3: Euler angles (roll, pitch, yaw) in radians.
    """
    if not isinstance(x, Vector4):
        raise TypeError(f"eulerAngles requires Vector4, got {type(x)}")
    q = x
    # Roll (x-axis rotation)
    sinr_cosp = 2 * (q.w * q.x + q.y * q.z)
    cosr_cosp = 1 - 2 * (q.x * q.x + q.y * q.y)
    roll = math.atan2(sinr_cosp, cosr_cosp)

    # Pitch (y-axis rotation)
    sinp = 2 * (q.w * q.y - q.z * q.x)
    if abs(sinp) >= 1:
        pitch = math.copysign(math.pi / 2, sinp)
    else:
        pitch = math.asin(sinp)

    # Yaw (z-axis rotation)
    siny_cosp = 2 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
    yaw = math.atan2(siny_cosp, cosy_cosp)

    return Vector3(roll, pitch, yaw)


@overload
def value_ptr(x: Matrix4, /) -> ndarray: ...
@overload
def value_ptr(x: Vector3, /) -> ndarray: ...
@overload
def value_ptr(x: Vector4, /) -> ndarray: ...
@overload
def value_ptr(x: Any, /) -> Any: ...
def value_ptr(x: Any, /) -> Any:
    """Get a pointer to the underlying data (returns flattened numpy array).
    
    This function requires numpy and is primarily for OpenGL interop.
    
    Args:
    ----
        x: Matrix or vector to get pointer from.
    
    Returns:
    -------
        np.ndarray: Flattened array of the data.
    
    Raises:
    ------
        ImportError: If numpy is not available.
    """
    try:
        import numpy as np
    except ImportError as e:
        raise ImportError("value_ptr requires numpy to be installed") from e
    
    if isinstance(x, Matrix4):
        # OpenGL expects column-major order
        # Convert row-major to column-major
        col_major = [[x._data[i][j] for i in range(4)] for j in range(4)]
        flat = [col_major[i][j] for i in range(4) for j in range(4)]
        return np.ascontiguousarray(np.array(flat, dtype=np.float32))
    if isinstance(x, Vector3):
        return np.ascontiguousarray(np.array([x.x, x.y, x.z], dtype=np.float32))
    if isinstance(x, Vector4):
        return np.ascontiguousarray(np.array([x.x, x.y, x.z, x.w], dtype=np.float32))
    raise TypeError(f"value_ptr requires Matrix4, Vector3, or Vector4, got {type(x)}")


@overload
def unProject(obj: Vector3, model: Matrix4, proj: Matrix4, viewport: Vector4, /) -> Vector3: ...
@overload
def unProject(obj: Any, model: Any, proj: Any, viewport: Any, /) -> Any: ...
def unProject(obj: Any, model: Any, proj: Any, viewport: Any, /) -> Any:
    """Unproject a window coordinate to world coordinates.
    
    Args:
    ----
        obj: Window coordinates (Vector3, where z is depth).
        model: Model-view matrix (Matrix4).
        proj: Projection matrix (Matrix4).
        viewport: Viewport as Vector4 (x, y, width, height).
    
    Returns:
    -------
        Vector3: World coordinates.
    """
    if (
        not isinstance(obj, Vector3)
        or not isinstance(model, Matrix4)
        or not isinstance(proj, Matrix4)
        or not isinstance(viewport, Vector4)
    ):
        raise TypeError(f"unProject requires Vector3, Matrix4, Matrix4, Vector4, got {type(obj)}, {type(model)}, {type(proj)}, {type(viewport)}")
    win = obj
    # Compute the inverse of model * projection
    m: Matrix4 = proj * model  # type: ignore[assignment]
    inv_m: Matrix4 = inverse(m)

    # Normalize window coordinates to NDC [-1, 1]
    ndc = Vector4(
        (win.x - viewport.x) / viewport.z * 2.0 - 1.0,
        (win.y - viewport.y) / viewport.w * 2.0 - 1.0,
        2.0 * win.z - 1.0,
        1.0,
    )

    # Transform NDC to world coordinates
    world: Vector4 = inv_m * ndc  # type: ignore[assignment]

    # Perspective divide
    if world.w != 0:
        world.x /= world.w
        world.y /= world.w
        world.z /= world.w

    return Vector3(world.x, world.y, world.z)


@overload
def length(x: Vector3, /) -> float: ...
@overload
def length(x: Any, /) -> Any: ...
def length(x: Any, /) -> Any:
    """Calculate the length (magnitude) of a vector.
    
    Args:
    ----
        x: Vector (Vector3).
    
    Returns:
    -------
        float: Vector length.
    """
    if not isinstance(x, Vector3):
        raise TypeError(f"length requires Vector3, got {type(x)}")
    return math.sqrt(x.x**2 + x.y**2 + x.z**2)

