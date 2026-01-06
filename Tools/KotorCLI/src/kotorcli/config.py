"""KotorCLI config compatibility shim.

This module is kept for backwards compatibility.
Version information is now retrieved from package metadata.
"""

from __future__ import annotations

import sys
from importlib.metadata import PackageNotFoundError, version

if sys.version_info >= (3, 8):
    from importlib.metadata import version
else:
    from importlib_metadata import version  # type: ignore[no-redef]


def _get_version() -> str:
    """Get the kotorcli package version."""
    try:
        return version("kotorcli")
    except PackageNotFoundError:
        # Fallback: try to get pykotor version
        try:
            return version("pykotor")
        except PackageNotFoundError:
            return "unknown"


VERSION = _get_version()
