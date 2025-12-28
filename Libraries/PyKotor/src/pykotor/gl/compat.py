"""Compatibility layer for OpenGL backends.

PyKotor's OpenGL support is PyOpenGL-based.
"""

from __future__ import annotations

from functools import lru_cache
from types import SimpleNamespace
from typing import Any, Callable


class MissingPyOpenGLError(RuntimeError):
    """Raised when PyOpenGL-dependent functionality is requested without PyOpenGL installed."""


@lru_cache(maxsize=1)
def has_pyopengl() -> bool:
    """Return True when PyOpenGL is importable."""
    try:
        import OpenGL  # noqa: F401
    except Exception:  # noqa: BLE001
        return False
    return True


def require_pyopengl(usage: str = "OpenGL rendering") -> None:
    """Raise a clear error if PyOpenGL is required but missing."""
    if not has_pyopengl():
        raise MissingPyOpenGLError(
            f"PyOpenGL is required for {usage}. Install PyOpenGL."
        )


def safe_gl_error_module():
    """Return the OpenGL.error module when available, otherwise a shim with NullFunctionError."""
    if has_pyopengl():
        from OpenGL import error as gl_error  # noqa: F401
        return gl_error
    return SimpleNamespace(NullFunctionError=MissingPyOpenGLError)


def missing_gl_func(name: str) -> Callable[..., Any]:
    """Create a stub that raises a helpful error when a GL function is unavailable."""

    def _missing(*_args: Any, **_kwargs: Any) -> None:
        raise MissingPyOpenGLError(
            f"PyOpenGL function '{name}' is unavailable because PyOpenGL is not installed. "
            f"Install PyOpenGL."
        )

    return _missing


def missing_constant(_name: str) -> int:
    """Return a neutral constant value for missing GL enums."""
    return 0


# Scene-specific OpenGL imports
HAS_PYOPENGL = has_pyopengl()

if HAS_PYOPENGL:
    from OpenGL.GL import glReadPixels  # pyright: ignore[reportMissingImports]
    from OpenGL.raw.GL.ARB.vertex_shader import GL_FLOAT  # pyright: ignore[reportMissingImports]
    from OpenGL.raw.GL.VERSION.GL_1_0 import (  # pyright: ignore[reportMissingImports]
        GL_BLEND,
        GL_COLOR_BUFFER_BIT,
        GL_CULL_FACE,
        GL_DEPTH_TEST,
        GL_DEPTH_BUFFER_BIT,
        GL_DEPTH_COMPONENT,
        GL_ONE_MINUS_SRC_ALPHA,
        GL_SRC_ALPHA,
        glClear,
        glClearColor,
        glBlendFunc,
        glDepthFunc,
        glDisable,
        glEnable,
    )
    from OpenGL.raw.GL.VERSION.GL_1_0 import GL_LEQUAL  # pyright: ignore[reportMissingImports]
    from OpenGL.raw.GL.VERSION.GL_1_2 import GL_BGRA, GL_UNSIGNED_INT_8_8_8_8  # pyright: ignore[reportMissingImports]
else:
    glReadPixels = missing_gl_func("glReadPixels")
    glClear = missing_gl_func("glClear")
    glClearColor = missing_gl_func("glClearColor")
    glBlendFunc = missing_gl_func("glBlendFunc")
    glDepthFunc = missing_gl_func("glDepthFunc")
    glDisable = missing_gl_func("glDisable")
    glEnable = missing_gl_func("glEnable")
    GL_BLEND = missing_constant("GL_BLEND")
    GL_COLOR_BUFFER_BIT = missing_constant("GL_COLOR_BUFFER_BIT")
    GL_CULL_FACE = missing_constant("GL_CULL_FACE")
    GL_DEPTH_TEST = missing_constant("GL_DEPTH_TEST")
    GL_DEPTH_BUFFER_BIT = missing_constant("GL_DEPTH_BUFFER_BIT")
    GL_DEPTH_COMPONENT = missing_constant("GL_DEPTH_COMPONENT")
    GL_SRC_ALPHA = missing_constant("GL_SRC_ALPHA")
    GL_ONE_MINUS_SRC_ALPHA = missing_constant("GL_ONE_MINUS_SRC_ALPHA")
    GL_LEQUAL = missing_constant("GL_LEQUAL")
    GL_FLOAT = missing_constant("GL_FLOAT")
    GL_BGRA = missing_constant("GL_BGRA")
    GL_UNSIGNED_INT_8_8_8_8 = missing_constant("GL_UNSIGNED_INT_8_8_8_8")
