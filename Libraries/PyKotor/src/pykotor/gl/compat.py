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
        import OpenGL  # pragma: no cover
    except ModuleNotFoundError:
        return False
    return True


@lru_cache(maxsize=1)
def has_moderngl() -> bool:
    """Return True when moderngl is importable."""
    try:
        import moderngl  # pragma: no cover
    except ModuleNotFoundError:
        return False
    return True


def require_pyopengl(usage: str = "OpenGL rendering") -> None:
    """Raise a clear error if PyOpenGL is required but missing."""
    if not has_pyopengl():
        raise MissingPyOpenGLError(
            f"PyOpenGL is required for {usage}. Install PyOpenGL or switch to the ModernGL backend."
        )


def safe_gl_error_module():
    """Return the OpenGL.error module when available, otherwise a shim with NullFunctionError."""
    if has_pyopengl():
        from OpenGL import error as gl_error  # pragma: no cover

        return gl_error
    return SimpleNamespace(NullFunctionError=MissingPyOpenGLError)


def missing_gl_func(name: str) -> Callable[..., Any]:
    """Create a stub that raises a helpful error when a GL function is unavailable."""

    def _missing(*_args: Any, **_kwargs: Any) -> None:
        raise MissingPyOpenGLError(
            f"PyOpenGL function '{name}' is unavailable because PyOpenGL is not installed. "
            f"Install PyOpenGL or use the ModernGL renderer instead."
        )

    return _missing


def missing_constant(_name: str) -> int:
    """Return a neutral constant value for missing GL enums."""
    return 0

