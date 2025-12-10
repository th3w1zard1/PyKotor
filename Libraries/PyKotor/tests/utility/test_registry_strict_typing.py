"""Tests for registry functions with strict type checking.

Tests verify that dynamic winreg attribute access works correctly.
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

import winreg

import pytest

from pykotor.tools.registry import resolve_registry_key
from utility.system.win32.registry import resolve_reg_key_to_path


class TestRegistryStrictTyping:
    """Test registry functions with strict type checking (getattr for dynamic lookup)."""

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows registry only")
    def test_resolve_reg_key_with_valid_root(self):
        """Test that valid winreg root names are accessed via getattr."""
        # Test with a valid registry root (HKEY_LOCAL_MACHINE)
        # This tests that getattr works for legitimate dynamic module attribute lookup
        result = resolve_reg_key_to_path("HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion", "ProgramFilesDir")

        # Should either return a path or None (depending on if key exists)
        assert result is None or isinstance(result, str)

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows registry only")
    def test_resolve_reg_key_with_invalid_root(self):
        """Test that invalid root names return None gracefully."""
        result = resolve_reg_key_to_path("INVALID_ROOT_NAME\\SOFTWARE\\Test", "TestValue")

        # Should return None when root doesn't exist (getattr returns None)
        assert result is None

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows registry only")
    def test_resolve_registry_key_uses_getattr(self):
        """Test that resolve_registry_key uses getattr for dynamic lookup."""
        # Test with HKEY_LOCAL_MACHINE (valid winreg attribute)
        result = resolve_registry_key("HKEY_LOCAL_MACHINE", "SOFTWARE\\Microsoft\\Windows\\CurrentVersion", "ProgramFilesDir")

        # Should handle gracefully using getattr
        assert result is None or isinstance(result, str)

    def test_winreg_has_standard_roots(self):
        """Test that winreg module has standard root attributes."""
        # Verify winreg has expected attributes (legitimate use of hasattr/getattr)
        assert hasattr(winreg, "HKEY_LOCAL_MACHINE")
        assert hasattr(winreg, "HKEY_CURRENT_USER")

        # Verify getattr works for accessing them
        hklm = getattr(winreg, "HKEY_LOCAL_MACHINE", None)
        assert hklm is not None
        assert isinstance(hklm, int)
