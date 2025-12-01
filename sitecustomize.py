"""Site-wide customization for PyKotor project.

This module is automatically imported by Python during initialization.
It normalizes PYTHONPATH to use the platform-specific separator for
cross-platform compatibility.

Python automatically imports this file if it's in:
- The current directory (when Python starts)
- A directory in PYTHONPATH
- The site-packages directory

This ensures PYTHONPATH works correctly on Windows (semicolons) and
Unix/Linux/macOS (colons) regardless of the format in .env file.
"""

from __future__ import annotations

import os


def _normalize_pythonpath() -> None:
    """Normalize PYTHONPATH to use platform-specific separator."""
    pythonpath = os.environ.get("PYTHONPATH")
    if not pythonpath:
        return

    # Determine the correct separator for this platform
    # Windows uses ';', Unix/Linux/macOS use ':'
    correct_sep = os.pathsep

    # Check if normalization is needed
    # If PYTHONPATH contains the wrong separator, convert it
    has_semicolon = ";" in pythonpath
    has_colon = ":" in pythonpath

    if has_semicolon and has_colon:
        # Mixed separators - split by both and rejoin with correct separator
        paths = []
        for sep in [";", ":"]:
            for path in pythonpath.split(sep):
                path = path.strip().strip('"').strip("'")
                if path and path not in paths:
                    paths.append(path)
        pythonpath = correct_sep.join(paths)
    elif has_semicolon and correct_sep == ":":
        # Windows format (semicolons) on Unix - convert to colons
        paths = [p.strip().strip('"').strip("'") for p in pythonpath.split(";") if p.strip()]
        pythonpath = correct_sep.join(paths)
    elif has_colon and correct_sep == ";":
        # Unix format (colons) on Windows - convert to semicolons
        paths = [p.strip().strip('"').strip("'") for p in pythonpath.split(":") if p.strip()]
        pythonpath = correct_sep.join(paths)
    else:
        # Already using correct separator, no normalization needed
        return

    # Update environment variable
    os.environ["PYTHONPATH"] = pythonpath


# Auto-normalize when this module is imported
_normalize_pythonpath()

