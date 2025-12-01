"""Pytest configuration for test_utility tests.

Sets up headless Qt testing and provides common fixtures.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Normalize PYTHONPATH for cross-platform compatibility
_pythonpath = os.environ.get("PYTHONPATH")
if _pythonpath:
    correct_sep = os.pathsep
    if ";" in _pythonpath and correct_sep == ":":
        paths = [p.strip().strip('"').strip("'") for p in _pythonpath.split(";") if p.strip()]
        os.environ["PYTHONPATH"] = correct_sep.join(paths)
    elif ":" in _pythonpath and correct_sep == ";":
        paths = [p.strip().strip('"').strip("'") for p in _pythonpath.split(":") if p.strip()]
        os.environ["PYTHONPATH"] = correct_sep.join(paths)

# Set Qt API before any Qt imports
if "QT_API" not in os.environ:
    os.environ["QT_API"] = "PyQt5"

# Force offscreen (headless) mode for Qt
# This ensures tests don't fail if no display is available (e.g. CI/CD)
# Must be set before any QApplication is instantiated.
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Paths
REPO_ROOT = Path(__file__).parents[2]
LIBS_PATH = REPO_ROOT / "Libraries"
TOOLS_PATH = REPO_ROOT / "Tools"

# Add Libraries
PYKOTOR_PATH = LIBS_PATH / "PyKotor" / "src"
UTILITY_PATH = LIBS_PATH / "Utility" / "src"
PYKOTORGL_PATH = LIBS_PATH / "PyKotorGL" / "src"
TOOLSET_SRC = TOOLS_PATH / "HolocronToolset" / "src"

for path in [PYKOTOR_PATH, UTILITY_PATH, PYKOTORGL_PATH, TOOLSET_SRC]:
    if str(path) not in sys.path:
        sys.path.append(str(path))


# pytest-qt provides qtbot fixture automatically
# No need to define custom fixtures here

