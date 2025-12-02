"""Utility library for general-purpose functions.

This library contains utility functions that are not specific to KOTOR.
KOTOR-specific utilities should be in Libraries/PyKotor/src/pykotor/tools.
"""

from utility.fonts import (
    get_font_paths,
    get_font_paths_linux,
    get_font_paths_macos,
    get_font_paths_windows,
)

__all__ = [
    "get_font_paths",
    "get_font_paths_linux",
    "get_font_paths_macos",
    "get_font_paths_windows",
]

