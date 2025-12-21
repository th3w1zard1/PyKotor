#!/usr/bin/env python
"""Test runner for all MDL tests with proper path setup."""
import sys
from pathlib import Path

# Add paths
THIS_DIR = Path(__file__).parent
SRC_DIR = THIS_DIR / "src"
UTILITY_DIR = THIS_DIR.parents[1] / "Utility" / "src"

sys.path.insert(0, str(SRC_DIR))
if UTILITY_DIR.exists():
    sys.path.insert(0, str(UTILITY_DIR))

# Now run pytest
import pytest

if __name__ == "__main__":
    test_files = [
        "tests/resource/formats/test_mdl.py",
        "tests/resource/formats/test_mdl_ascii.py",
        "tests/resource/formats/test_mdl_roundtrip.py",
        "tests/resource/formats/test_mdl_comprehensive.py",
    ]
    
    # Also check for test_mdl_editor.py
    editor_test = THIS_DIR.parents[2] / "Tools" / "HolocronToolset" / "tests" / "gui" / "editors" / "test_mdl_editor.py"
    if editor_test.exists():
        test_files.append(str(editor_test.relative_to(THIS_DIR.parents[2])))
    
    exit_code = pytest.main(["-v", "--tb=short"] + test_files)
    sys.exit(exit_code)


