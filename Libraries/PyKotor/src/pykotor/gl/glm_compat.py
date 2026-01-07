"""GLM compatibility layer using PyKotor geometry classes.

This module provides a PyGLM-compatible API by aliasing PyKotor's geometry classes
and utility functions. It supports PyPy and works without PyGLM.

Note: All classes intentionally use lowercase names to match PyGLM's API.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

# Import geometry classes and alias to lowercase (GLM-compatible names)
from utility.common.geometry import Matrix4, Vector2, Vector3, Vector4

# Import GLM-compatible functions
from pykotor.common.geometry_utils import (
    cross,
    decompose,
    eulerAngles,
    inverse,
    length,
    mat4_cast,
    normalize,
    perspective,
    rotate,
    translate,
    unProject,
    value_ptr,
)

# GLM-compatible aliases (lowercase)
vec2 = Vector2  # noqa: N801
vec3 = Vector3  # noqa: N801
vec4 = Vector4  # noqa: N801
quat = Vector4  # noqa: N801 - Quaternions use Vector4 (x, y, z, w format)
mat4 = Matrix4  # noqa: N801

# Re-export all functions
__all__ = [
    "vec2",
    "vec3",
    "vec4",
    "quat",
    "mat4",
    "translate",
    "rotate",
    "mat4_cast",
    "inverse",
    "perspective",
    "normalize",
    "cross",
    "decompose",
    "eulerAngles",
    "value_ptr",
    "unProject",
    "length",
]

# Try to import PyGLM if available (for optional performance improvements)
if not TYPE_CHECKING and importlib.util.find_spec("pyglm"):  # type: ignore[attr-defined]
    try:
        from pyglm.glm import (  # pyright: ignore[reportUnreachable]
            inverse as _pyglm_inverse,
            mat4 as _pyglm_mat4,
            quat as _pyglm_quat,
            vec3 as _pyglm_vec3,
            vec4 as _pyglm_vec4,
        )
        # Use PyGLM if available (better performance)
        vec3 = _pyglm_vec3  # type: ignore[assignment]
        vec4 = _pyglm_vec4  # type: ignore[assignment]
        quat = _pyglm_quat  # type: ignore[assignment]
        mat4 = _pyglm_mat4  # type: ignore[assignment]
        inverse = _pyglm_inverse  # type: ignore[assignment]
    except ImportError:
        from loggerplus import RobustLogger

        RobustLogger().debug("PyGLM not found, using PyKotor geometry classes")
        pass
