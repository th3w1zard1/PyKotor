from __future__ import annotations

try:
    from .fastmath import available, transform_bounds
except Exception:  # noqa: BLE001
    def available() -> bool:  # type: ignore[override]
        return False

    def transform_bounds(*args, **kwargs):  # type: ignore[override]
        raise RuntimeError("pykotor.gl.native.fastmath is unavailable")

__all__ = ["available", "transform_bounds"]

