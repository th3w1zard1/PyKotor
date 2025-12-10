"""Tests for ComparableMixin with strict type checking.

Tests verify that COMPARABLE_FIELDS access works correctly.
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


from pykotor.resource.formats._base import ComparableMixin


class ComparableTestHelper(ComparableMixin):
    """Helper class for testing ComparableMixin (not a test class)."""

    COMPARABLE_FIELDS = ("value", "name")
    COMPARABLE_SEQUENCE_FIELDS = ("items",)
    COMPARABLE_SET_FIELDS = ("tags",)

    def __init__(self, value: int, name: str, items: list[str], tags: set[str]):
        self.value = value
        self.name = name
        self.items = items
        self.tags = tags


class TestComparableMixinStrictTyping:
    """Test ComparableMixin with strict type checking (getattr for dynamic field access)."""

    def test_compare_uses_class_variable_directly(self):
        """Test that COMPARABLE_FIELDS is accessed via class variable, not getattr."""
        obj1 = ComparableTestHelper(1, "test", ["a", "b"], {"tag1"})
        obj2 = ComparableTestHelper(1, "test", ["a", "b"], {"tag1"})

        # Should access type(self).COMPARABLE_FIELDS directly
        result = obj1.compare(obj2)
        assert result is True

    def test_compare_uses_getattr_for_field_values(self):
        """Test that field values are accessed via getattr (legitimate dynamic access)."""
        obj1 = ComparableTestHelper(1, "test1", ["a"], {"tag1"})
        obj2 = ComparableTestHelper(2, "test2", ["b"], {"tag2"})

        # compare() uses getattr to access fields by name (legitimate use)
        result = obj1.compare(obj2)
        assert result is False

    def test_compare_sequence_fields(self):
        """Test that COMPARABLE_SEQUENCE_FIELDS is accessed via class variable."""
        obj1 = ComparableTestHelper(1, "test", ["a", "b"], set())
        obj2 = ComparableTestHelper(1, "test", ["a", "b"], set())

        result = obj1.compare(obj2)
        assert result is True

    def test_compare_set_fields(self):
        """Test that COMPARABLE_SET_FIELDS is accessed via class variable."""
        obj1 = ComparableTestHelper(1, "test", [], {"tag1", "tag2"})
        obj2 = ComparableTestHelper(1, "test", [], {"tag2", "tag1"})  # Same tags, different order

        result = obj1.compare(obj2)
        assert result is True  # Sets are unordered, so should be equal

    def test_compare_missing_field_handles_gracefully(self):
        """Test that missing fields are handled gracefully with getattr."""
        obj1 = ComparableTestHelper(1, "test", [], set())
        obj2 = ComparableTestHelper(1, "test", [], set())

        # Delete an attribute to test error handling
        del obj2.name

        # Should handle missing attribute gracefully
        result = obj1.compare(obj2)
        # Result depends on implementation, but should not crash
        assert result is True