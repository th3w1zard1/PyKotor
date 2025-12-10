"""Tests for GIT serialize() methods with strict type checking.

Tests verify that LocalizedString.stringref and enum.value access work correctly.
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

from pykotor.common.language import LocalizedString
from pykotor.common.misc import ResRef
from pykotor.resource.generics.git import GITDoor, GITTrigger, GITModuleLink


class TestGITSerializeStrictTyping:
    """Test GIT serialize methods with strict type checking (no hasattr/getattr)."""

    def test_git_door_serialize_localized_string_stringref(self):
        """Test that transition_destination.stringref is accessed directly."""
        door = GITDoor()
        door.transition_destination = LocalizedString(12345)
        door.linked_to_flags = GITModuleLink.NoLink
        
        result = door._serialize_instance_data()
        
        # LocalizedString always has stringref attribute - should access directly
        assert result["transition_destination_stringref"] == 12345
        assert isinstance(result["transition_destination_stringref"], int)

    def test_git_door_serialize_linked_to_flags_enum_value(self):
        """Test that linked_to_flags.value is accessed directly."""
        door = GITDoor()
        door.transition_destination = LocalizedString(-1)
        door.linked_to_flags = GITModuleLink.ToDoor
        
        result = door._serialize_instance_data()
        
        # GITModuleLink is IntEnum, always has .value
        assert result["linked_to_flags"] == GITModuleLink.ToDoor.value
        assert isinstance(result["linked_to_flags"], int)

    def test_git_door_serialize_invalid_stringref(self):
        """Test serializing with invalid stringref (-1)."""
        door = GITDoor()
        door.transition_destination = LocalizedString.from_invalid()  # Creates with -1
        door.linked_to_flags = GITModuleLink.NoLink
        
        result = door._serialize_instance_data()
        
        # Should access stringref directly even when -1
        assert result["transition_destination_stringref"] == -1

    def test_git_trigger_serialize_localized_string_stringref(self):
        """Test that GITTrigger transition_destination.stringref works."""
        trigger = GITTrigger()
        trigger.transition_destination = LocalizedString(99999)
        trigger.linked_to_flags = GITModuleLink.ToWaypoint
        
        result = trigger._serialize_instance_data()
        
        # Should access stringref directly
        assert result["transition_destination_stringref"] == 99999
        assert result["linked_to_flags"] == GITModuleLink.ToWaypoint.value

    def test_git_door_serialize_all_fields(self):
        """Test serializing all GITDoor fields."""
        door = GITDoor()
        door.resref = ResRef("testdoor")
        door.bearing = 1.5
        door.tag = "test_tag"
        door.linked_to_module = ResRef("testmod")
        door.linked_to = "test_link"
        door.transition_destination = LocalizedString(54321)
        door.linked_to_flags = GITModuleLink.ToDoor
        
        result = door._serialize_instance_data()
        
        # Verify all fields, especially enum and LocalizedString access
        assert result["resref"] == "testdoor"
        assert result["bearing"] == 1.5
        assert result["tag"] == "test_tag"
        assert result["linked_to_module"] == "testmod"
        assert result["linked_to"] == "test_link"
        assert result["transition_destination_stringref"] == 54321
        assert result["linked_to_flags"] == GITModuleLink.ToDoor.value

