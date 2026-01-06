"""Version information for PyKotor CLI."""

from __future__ import annotations

import sys
from importlib.metadata import PackageNotFoundError, version

if sys.version_info >= (3, 8):
    from importlib.metadata import version
else:
    from importlib_metadata import version  # type: ignore[no-redef]


def get_version() -> str:
    """Get the PyKotor package version.

    Returns:
    -------
        The version string from package metadata, or "unknown" if not available.
    """
    try:
        return version("pykotor")
    except PackageNotFoundError:
        # Fallback for development/editable installs
        try:
            from pykotor import __version__  # type: ignore[import-untyped]

            return __version__
        except (ImportError, AttributeError):
            return "unknown"


VERSION = get_version()
