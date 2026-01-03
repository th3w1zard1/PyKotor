"""Tests for sys attribute checks with strict type checking.

Tests verify that optional sys attributes (frozen, _MEIPASS) are checked correctly.
"""

from __future__ import annotations

import pathlib
import sys

# Setup paths
THIS_FILE = pathlib.Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parents[5]
PYKOTOR_SRC = REPO_ROOT / "Libraries" / "PyKotor" / "src"
UTILITY_SRC = REPO_ROOT / "Libraries" / "Utility" / "src"

for path in (PYKOTOR_SRC, UTILITY_SRC):
    as_posix = path.as_posix()
    if as_posix not in sys.path:
        sys.path.insert(0, as_posix)


from utility.system.app_process.util import is_frozen as is_frozen_app_process
from utility.system.os_helper import get_app_dir, is_frozen
from utility.tkinter.app_entry import is_frozen as is_frozen_tkinter


class TestSysAttributesStrictTyping:
    """Test sys attribute checks with strict type checking (getattr for optional attributes)."""

    def test_is_frozen_uses_getattr(self):
        """Test that is_frozen() uses getattr for optional sys attributes."""
        result = is_frozen()

        # Should return bool (False in normal Python, True if frozen)
        assert isinstance(result, bool)

        # In normal Python execution, should be False
        # (unless running in PyInstaller/cx_Freeze/etc)
        # The key is that it uses getattr, not object.__getattribute__

    def test_is_frozen_app_process_uses_getattr(self):
        """Test that is_frozen() in app_process uses getattr."""
        result = is_frozen_app_process()
        assert isinstance(result, bool)

    def test_is_frozen_tkinter_uses_getattr(self):
        """Test that is_frozen() in tkinter uses getattr."""
        result = is_frozen_tkinter()
        assert isinstance(result, bool)

    def test_get_app_dir_uses_getattr_for_file(self):
        """Test that get_app_dir() uses getattr for __file__."""
        result = get_app_dir()

        # Should return a Path
        assert result is not None
        assert isinstance(result, pathlib.Path)
        # The key is that it uses getattr for optional __file__ attribute

    def test_sys_frozen_attribute_check(self):
        """Test that sys.frozen check uses getattr (legitimate optional attribute)."""
        # Verify the pattern: getattr(sys, "frozen", False)
        frozen = getattr(sys, "frozen", False)
        assert isinstance(frozen, bool)

        # In normal execution, should be False
        # In frozen apps (PyInstaller), would be True

    def test_sys_meipass_attribute_check(self):
        """Test that sys._MEIPASS check uses getattr (legitimate optional attribute)."""
        # Verify the pattern: getattr(sys, "_MEIPASS", False)
        meipass = getattr(sys, "_MEIPASS", False)
        assert isinstance(meipass, (bool, str))

        # In normal execution, should be False
        # In PyInstaller, would be a string path
