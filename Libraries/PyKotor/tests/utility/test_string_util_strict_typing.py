"""Tests for string_util with strict type checking.

Tests verify that WrappedStr.__setattr__ immutability check works correctly.
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

import pytest

from utility.string_util import WrappedStr


class TestStringUtilStrictTyping:
    """Test WrappedStr with strict type checking (hasattr for immutability check)."""

    def test_setattr_prevents_modifying_existing_attribute(self):
        """Test that __setattr__ prevents modifying existing _content attribute."""
        wrapped = WrappedStr("test")

        # Should raise RuntimeError when trying to modify existing attribute
        with pytest.raises(RuntimeError, match="is immutable"):
            wrapped._content = "modified"

    def test_setattr_allows_setting_new_attribute(self):
        """Test that __setattr__ allows setting new attributes."""
        wrapped = WrappedStr("test")

        # Should allow setting new attributes
        wrapped.new_attr = "value"
        assert wrapped.new_attr == "value"

    def test_setattr_uses_hasattr_for_immutability_check(self):
        """Test that immutability check uses hasattr (legitimate use case)."""
        wrapped = WrappedStr("test")

        # Verify _content exists (should be checked via hasattr in __setattr__)
        assert hasattr(wrapped, "_content")

        # Attempting to modify should fail
        with pytest.raises(RuntimeError):
            wrapped._content = "new"

    def test_immutability_check_works_with_slots(self):
        """Test that immutability check works correctly with __slots__."""
        wrapped = WrappedStr("test")

        # _content is in __slots__, should be detected as existing
        assert "_content" in WrappedStr.__slots__

        # Should prevent modification
        with pytest.raises(RuntimeError, match="immutable"):
            wrapped._content = "changed"
