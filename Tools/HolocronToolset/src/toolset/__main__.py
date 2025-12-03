#!/usr/bin/env python3
from __future__ import annotations

import sys

from pathlib import Path


# Set up paths BEFORE importing anything that might import loggerplus (which depends on utility)
# This is critical for both frozen and non-frozen builds
def setup_paths():
    """Set up sys.path for local modules."""
    file_path = Path(__file__).resolve()
    repo_root = file_path.parents[4]  # Go up to repo root
    
    paths_to_add = [
        file_path.parent.parent,  # ./Tools/HolocronToolset/src/
        repo_root / "Tools" / "KotorDiff" / "src",  # ./Tools/KotorDiff/src/
        repo_root / "Libraries" / "PyKotor" / "src",  # ./Libraries/PyKotor/src/ (contains both pykotor and utility namespaces)
        repo_root / "Libraries" / "PyKotorGL" / "src",  # ./Libraries/PyKotorGL/src/
    ]
    
    for path in paths_to_add:
        path_str = str(path)
        if path.exists() and path_str not in sys.path:
            sys.path.insert(0, path_str)

# Always set up paths first
setup_paths()

try:
    from toolset.main_app import main
except ImportError:
    # If import fails, paths might not be set correctly, try again
    setup_paths()
    from toolset.main_app import main

from toolset.main_init import main_init  # noqa: E402

if __name__ == "__main__":
    main_init()
    main()
