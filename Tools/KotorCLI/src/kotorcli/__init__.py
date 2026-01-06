"""KotorCLI compatibility shim package.

This package forwards to PyKotor CLI for backwards compatibility.
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


__version__ = _get_version()
