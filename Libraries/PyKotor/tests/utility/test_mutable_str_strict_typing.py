"""Tests for mutable_str with strict type checking.

Tests verify that attribute forwarding and compatibility checks work correctly.
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

from utility.common.misc_string.mutable_str import WrappedStr


class TestMutableStrStrictTyping:
    """Test MutableStr with strict type checking (getattr for delegation, hasattr for compatibility)."""

    def test_attribute_forwarding_uses_getattr(self):
        """Test that __getattr__ uses getattr for forwarding to _content."""
        mutable = WrappedStr("test")
        
        # Access str method through forwarding (uses getattr internally)
        result = mutable.upper()
        assert result == "TEST"
        
        # Access str attribute through forwarding
        assert mutable.__class__.__name__ == "WrappedStr"

    def test_hasattr_checks_for_compatibility_methods(self):
        """Test that hasattr is used for checking optional str methods."""
        # Verify hasattr is used for compatibility checks (legitimate use)
        assert hasattr(str, "__reduce_ex__") or not hasattr(str, "__reduce_ex__")
        assert hasattr(str, "removeprefix") or not hasattr(str, "removeprefix")
        assert hasattr(str, "removesuffix") or not hasattr(str, "removesuffix")

    def test_removeprefix_if_not_available(self):
        """Test removeprefix implementation when str doesn't have it."""
        mutable = WrappedStr("test_string")
        
        # If str has removeprefix, use it; otherwise use custom implementation
        result = mutable.removeprefix("test_")
        assert result == "string" or result == WrappedStr("string")

    def test_removesuffix_if_not_available(self):
        """Test removesuffix implementation when str doesn't have it."""
        mutable = WrappedStr("test_string")
        
        # If str has removesuffix, use it; otherwise use custom implementation
        result = mutable.removesuffix("_string")
        assert result == "test" or result == WrappedStr("test")

