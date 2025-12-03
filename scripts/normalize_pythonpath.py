"""Normalize PYTHONPATH separator for cross-platform compatibility.

This script normalizes PYTHONPATH to use the platform-specific separator.
It can be run before Python starts or imported as a module.

Usage:
    python scripts/normalize_pythonpath.py
    # Or import it in your code before any imports
    import sys
    sys.path.insert(0, 'scripts')
    import normalize_pythonpath
"""

from __future__ import annotations

import os


def normalize_pythonpath() -> None:
    """Normalize PYTHONPATH to use platform-specific separator."""
    pythonpath = os.environ.get("PYTHONPATH")
    if not pythonpath:
        return

    # Determine the correct separator for this platform
    # Windows uses ';', Unix/Linux/macOS use ':'
    correct_sep = os.pathsep

    # Check if normalization is needed
    # If PYTHONPATH contains both separators, prefer the correct one
    has_semicolon = ";" in pythonpath
    has_colon = ":" in pythonpath

    if has_semicolon and has_colon:
        # Mixed separators - this shouldn't happen, but handle it
        # Split by both and rejoin with correct separator
        paths = []
        for sep in [";", ":"]:
            for path in pythonpath.split(sep):
                path = path.strip().strip('"').strip("'")
                if path and path not in paths:
                    paths.append(path)
        pythonpath = correct_sep.join(paths)
    elif has_semicolon and correct_sep == ":":
        # Windows format on Unix - convert to colons
        paths = [p.strip().strip('"').strip("'") for p in pythonpath.split(";") if p.strip()]
        pythonpath = correct_sep.join(paths)
    elif has_colon and correct_sep == ";":
        # Unix format on Windows - convert to semicolons
        paths = [p.strip().strip('"').strip("'") for p in pythonpath.split(":") if p.strip()]
        pythonpath = correct_sep.join(paths)

    # Update environment variable
    os.environ["PYTHONPATH"] = pythonpath


if __name__ == "__main__":
    normalize_pythonpath()
    print(f"PYTHONPATH normalized: {os.environ.get('PYTHONPATH', 'not set')}")
else:
    # Auto-normalize when imported
    normalize_pythonpath()

