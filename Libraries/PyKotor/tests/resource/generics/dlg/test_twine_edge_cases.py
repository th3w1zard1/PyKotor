"""Edge case tests for Twine format conversion."""

from __future__ import annotations

import json
import os
import tempfile

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if os.environ.get("PYKOTOR_DLG_TWINE_AGGREGATE") != "1":
    pytest.skip(
        "Consolidated into Libraries/PyKotor/tests/resource/generics/test_dlg_twine.py",
        allow_module_level=True,
    )

pytest.skip("Consolidated into Libraries/PyKotor/tests/resource/generics/test_dlg_twine.py", allow_module_level=True)

from pykotor.common.language import Gender, Language
from pykotor.common.misc import Color, ResRef
from pykotor.resource.generics.dlg.base import DLG
from pykotor.resource.generics.dlg.io.twine import read_twine, write_twine
from pykotor.resource.generics.dlg.links import DLGLink
from pykotor.resource.generics.dlg.nodes import DLGEntry, DLGReply

if TYPE_CHECKING:
    from typing import Any


def test_empty_dialog():
    """Test handling of empty dialog."""
    dlg = DLG()

    tmpdir = Path(tempfile.mkdtemp())
    json_path = tmpdir / "empty.json"
    write_twine(dlg, json_path, format="json")
    new_dlg = read_twine(json_path)

    assert len(new_dlg.starters) == 0
    assert len(new_dlg.all_entries()) == 0
    assert len(new_dlg.all_replies()) == 0


def test_unicode_characters():
    """Test handling of Unicode characters."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC 🚀"  # Emoji
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Hello 世界")  # Chinese
    entry.text.set_data(Language.FRENCH, Gender.MALE, "Bonjour 🌍")  # French with emoji
    dlg.starters.append(DLGLink(entry))

    tmpdir = Path(tempfile.mkdtemp())
    json_path = tmpdir / "unicode.json"
    write_twine(dlg, json_path, format="json")
    new_dlg = read_twine(json_path)

    new_entry = new_dlg.starters[0].node
    assert isinstance(new_entry, DLGEntry)
    assert new_entry.speaker == "NPC 🚀"
    assert new_entry.text.get(Language.ENGLISH, Gender.MALE) == "Hello 世界"
    assert new_entry.text.get(Language.FRENCH, Gender.MALE) == "Bonjour 🌍"


def test_special_characters():
    """Test handling of special characters in text and metadata."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC <with> special & chars"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Text with <tags> & special chars")
    dlg.starters.append(DLGLink(entry))

    tmpdir = Path(tempfile.mkdtemp())
    json_path = tmpdir / "special.json"
    write_twine(dlg, json_path, format="json")
    new_dlg = read_twine(json_path)

    new_entry = new_dlg.starters[0].node
    assert isinstance(new_entry, DLGEntry)
    assert new_entry.speaker == "NPC <with> special & chars"
    assert new_entry.text.get(Language.ENGLISH, Gender.MALE) == "Text with <tags> & special chars"


def test_multiple_languages():
    """Test handling of multiple languages."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "English text")
    entry.text.set_data(Language.FRENCH, Gender.MALE, "French text")
    entry.text.set_data(Language.GERMAN, Gender.MALE, "German text")
    dlg.starters.append(DLGLink(entry))

    tmpdir = Path(tempfile.mkdtemp())
    json_path = tmpdir / "multilang.json"
    write_twine(dlg, json_path, format="json")
    new_dlg = read_twine(json_path)

    new_entry = new_dlg.starters[0].node
    assert isinstance(new_entry, DLGEntry)
    assert new_entry.text.get(Language.ENGLISH, Gender.MALE) == "English text"
    assert new_entry.text.get(Language.FRENCH, Gender.MALE) == "French text"
    assert new_entry.text.get(Language.GERMAN, Gender.MALE) == "German text"


def test_kotor_specific_features():
    """Test preservation of KotOR-specific features."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Test")
    entry.animation_id = 123  # animation_id property maps to camera_anim
    entry.camera_angle = 45
    entry.camera_id = 1
    entry.fade_type = 2
    entry.quest = "MainQuest"
    entry.sound = ResRef("voice.wav")
    entry.vo_resref = ResRef("npc_line")
    dlg.starters.append(DLGLink(entry))

    tmpdir = Path(tempfile.mkdtemp())
    json_path = tmpdir / "kotor.json"
    write_twine(dlg, json_path, format="json")
    new_dlg = read_twine(json_path)

    new_entry = new_dlg.starters[0].node
    assert isinstance(new_entry, DLGEntry), "New entry is not a DLGEntry"
    assert new_entry.camera_anim == 123, "Camera animation ID is not 123"
    assert new_entry.camera_angle == 45, "Camera angle is not 45"
    assert new_entry.camera_id == 1, "Camera ID is not 1"
    assert new_entry.fade_type == 2, "Fade type is not 2"
    assert new_entry.quest == "MainQuest", "Quest is not MainQuest"
    assert str(new_entry.sound) == "voice.wav", "Sound is not voice.wav"
    assert str(new_entry.vo_resref) == "npc_line", "VO ResRef is not npc_line"


def test_twine_specific_features():
    """Test preservation of Twine-specific features."""
    metadata: dict[str, Any] = {
        "name": "Test Story",
        "format": "Harlowe",
        "format-version": "3.3.7",
        "tag-colors": {"reply": Color.GREEN},
        "style": "body { color: red; }",
        "script": "window.setup = {};",
        "zoom": 1.5,
    }

    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Test")
    dlg.starters.append(DLGLink(entry))

    tmpdir = Path(tempfile.mkdtemp())
    json_path = tmpdir / "twine_meta.json"
    write_twine(dlg, json_path, format="json", metadata=metadata)

    with open(json_path, encoding="utf-8") as f2:
        data: dict[str, Any] = json.load(f2)
        assert data["name"] == metadata["name"]
        assert data["format"] == metadata["format"]
        assert data["format-version"] == metadata["format-version"]
        # tag-colors is stored as string representation, compare string values
        assert data["tag-colors"]["reply"] == str(metadata["tag-colors"]["reply"])
        assert data["style"] == metadata["style"]
        assert data["script"] == metadata["script"]
        assert data["zoom"] == metadata["zoom"]


def test_large_dialog():
    """Test handling of large dialog structures."""
    import sys
    # Increase recursion limit for this test
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(3000)
    try:
        dlg = DLG()
        prev_entry = None

        # Create a long chain of 1000 nodes
        for i in range(1000):
            entry = DLGEntry()
            entry.speaker = f"NPC{i}"
            entry.text.set_data(Language.ENGLISH, Gender.MALE, f"Text {i}")

            if prev_entry is None:
                dlg.starters.append(DLGLink(entry))
            else:
                reply = DLGReply()
                reply.text.set_data(Language.ENGLISH, Gender.MALE, f"Reply {i}")
                prev_entry.links.append(DLGLink(reply))
                reply.links.append(DLGLink(entry))

            prev_entry = entry

        tmpdir = Path(tempfile.mkdtemp())
        json_path = tmpdir / "large.json"
        write_twine(dlg, json_path, format="json")
        new_dlg = read_twine(json_path)

        assert len(new_dlg.all_entries()) == 1000
        assert len(new_dlg.all_replies()) == 999
    finally:
        sys.setrecursionlimit(old_limit)


def test_missing_fields():
    """Test handling of missing fields in Twine format."""
    # Create minimal JSON - add tags so passage is recognized as entry
    minimal_json = {
        "passages": [
            {
                "name": "Start",
                "text": "Some text",
                "pid": "1",
                "tags": ["entry"]  # Add tag so it's recognized as entry
                # Missing metadata, etc.
            }
        ],
        "startnode": "1"  # Add startnode so it's used
    }

    tmpdir = Path(tempfile.mkdtemp())
    json_path = tmpdir / "missing.json"
    json_path.write_text(json.dumps(minimal_json), encoding="utf-8")
    dlg = read_twine(json_path)
    assert len(dlg.all_entries()) + len(dlg.all_replies()) > 0


def test_create_new_dlg_from_scratch():
    """Test creating a new DLG file from Twine with zero KOTOR metadata.
    
    This tests that users can create brand new .dlg files using the Twine editor
    without needing any existing KOTOR metadata. All fields should be initialized
    with appropriate defaults.
    """
    # Create a minimal Twine JSON with no KOTOR metadata
    twine_json = {
        "name": "New Dialog",
        "format": "Harlowe",
        "format-version": "3.3.7",
        "startnode": "1",
        "passages": [
            {
                "name": "Entry1",
                "text": "Hello, player! [[Reply1]]",  # Link to reply
                "pid": "1",
                "tags": ["entry"],
                "metadata": {
                    "position": "0,0",
                    "size": "100,100"
                    # No custom metadata = no KOTOR metadata
                }
            },
            {
                "name": "Reply1",
                "text": "Hello! [[Entry2]]",  # Links are embedded in text in Twine format
                "pid": "2",
                "tags": ["reply"],
                "metadata": {
                    "position": "200,0",
                    "size": "100,100"
                    # No custom metadata = no KOTOR metadata
                }
            },
            {
                "name": "Entry2",
                "text": "How can I help you?",
                "pid": "3",
                "tags": ["entry"],
                "metadata": {
                    "position": "0,200",
                    "size": "100,100"
                    # No custom metadata = no KOTOR metadata
                }
            }
        ]
    }
    
    tmpdir = Path(tempfile.mkdtemp())
    json_path = tmpdir / "new_dialog.json"
    json_path.write_text(json.dumps(twine_json), encoding="utf-8")
    
    # Read and convert to DLG
    dlg = read_twine(json_path)
    
    # Verify DLG was created successfully
    assert dlg is not None
    assert len(dlg.starters) > 0, "Should have at least one starter node"
    
    # Verify entries were created with proper defaults
    entries = dlg.all_entries()
    assert len(entries) == 2, "Should have 2 entries"
    
    entry1 = entries[0]
    assert isinstance(entry1, DLGEntry)
    # Text may contain link syntax [[Reply1]], which is expected in Twine format
    text1 = entry1.text.get(Language.ENGLISH, Gender.MALE) or ""
    assert "Hello, player!" in text1, f"Text should contain 'Hello, player!', got: {text1}"
    assert entry1.speaker == "Entry1"
    # Verify defaults for new files (should be None for optional fields)
    assert entry1.camera_anim is None, "camera_anim should be None for new files with no metadata"
    assert entry1.camera_id is None, "camera_id should be None for new files with no metadata"
    assert entry1.camera_angle == 0, "camera_angle should default to 0"
    assert entry1.fade_type == 0, "fade_type should default to 0"
    assert entry1.quest == "", "quest should default to empty string"
    assert str(entry1.sound) == "", "sound should default to blank ResRef"
    assert str(entry1.vo_resref) == "", "vo_resref should default to blank ResRef"
    
    # Verify replies were created with proper defaults
    replies = dlg.all_replies()
    assert len(replies) == 1, "Should have 1 reply"
    
    reply1 = replies[0]
    assert isinstance(reply1, DLGReply)
    reply_text = reply1.text.get(Language.ENGLISH, Gender.MALE) or ""
    assert "Hello!" in reply_text, f"Text should contain 'Hello!', got: {reply_text}"
    # Verify defaults for new files
    assert reply1.camera_anim is None, "camera_anim should be None for new files with no metadata"
    assert reply1.camera_id is None, "camera_id should be None for new files with no metadata"
    assert reply1.camera_angle == 0, "camera_angle should default to 0"
    
    # Verify links were preserved
    assert len(reply1.links) == 1, "Reply should have 1 link"
    # Find Entry2 by checking all entries
    entry2 = None
    for entry in entries:
        entry_text = entry.text.get(Language.ENGLISH, Gender.MALE) or ""
        if "How can I help you?" in entry_text:
            entry2 = entry
            break
    assert entry2 is not None, "Entry2 should exist"
    assert reply1.links[0].node == entry2, "Link should point to Entry2"
    
    # Test round-trip: write and read back
    json_path2 = tmpdir / "new_dialog2.json"
    write_twine(dlg, json_path2, format="json")
    dlg2 = read_twine(json_path2)
    
    # Verify round-trip preserves structure
    assert len(dlg2.all_entries()) == 2
    assert len(dlg2.all_replies()) == 1
    text_after_roundtrip = dlg2.all_entries()[0].text.get(Language.ENGLISH, Gender.MALE) or ""
    assert "Hello, player!" in text_after_roundtrip, f"Text should contain 'Hello, player!', got: {text_after_roundtrip}"


def test_duplicate_passage_names():
    """Test handling of duplicate passage names."""
    dlg = DLG()

    # Create entries with same speaker name
    entry1 = DLGEntry()
    entry1.speaker = "NPC"
    entry1.text.set_data(Language.ENGLISH, Gender.MALE, "First")

    entry2 = DLGEntry()
    entry2.speaker = "NPC"  # Same speaker name
    entry2.text.set_data(Language.ENGLISH, Gender.MALE, "Second")

    reply = DLGReply()
    reply.text.set_data(Language.ENGLISH, Gender.MALE, "Reply")

    # Link them
    entry1.links.append(DLGLink(reply))
    reply.links.append(DLGLink(entry2))
    dlg.starters.append(DLGLink(entry1))

    tmpdir = Path(tempfile.mkdtemp())
    json_path = tmpdir / "dup.json"
    write_twine(dlg, json_path, format="json")
    new_dlg = read_twine(json_path)

    assert len(new_dlg.all_entries()) == 2
    assert len(new_dlg.all_replies()) == 1


def test_empty_text():
    """Test handling of empty or None text."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    # Don't set any text
    dlg.starters.append(DLGLink(entry))

    tmpdir = Path(tempfile.mkdtemp())
    json_path = tmpdir / "empty_text.json"
    write_twine(dlg, json_path, format="json")
    new_dlg = read_twine(json_path)

    new_entry = new_dlg.starters[0].node
    assert isinstance(new_entry, DLGEntry)
    assert new_entry.text.get(Language.ENGLISH, Gender.MALE) == ""


def test_invalid_metadata():
    """Test handling of invalid metadata."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Test")
    dlg.starters.append(DLGLink(entry))

    # Invalid metadata
    invalid_metadata = {
        "zoom": "not a number",  # Should be float
        "tag-colors": "not a dict",  # Should be dict
    }

    tmpdir = Path(tempfile.mkdtemp())
    json_path = tmpdir / "invalid_meta.json"
    write_twine(dlg, json_path, format="json", metadata=invalid_metadata)
    new_dlg = read_twine(json_path)
    assert len(new_dlg.starters) == 1


def test_file_not_found():
    """Test handling of non-existent files."""
    with pytest.raises(FileNotFoundError):
        read_twine("nonexistent.json")

    with pytest.raises(FileNotFoundError):
        read_twine("nonexistent.html")


def test_invalid_custom_metadata_is_ignored(tmp_path: Path):
    """Gracefully ignore malformed custom metadata blocks."""
    broken_json = {
        "passages": [
            {
                "name": "Start",
                "text": "Hello",
                "pid": "1",
                "tags": ["entry"],
                "metadata": {"custom": "not-a-dict"},
            }
        ],
        "startnode": "1",
    }
    json_path = tmp_path / "broken.json"
    json_path.write_text(json.dumps(broken_json), encoding="utf-8")

    dlg = read_twine(json_path)
    assert len(dlg.all_entries()) == 1
    assert dlg.starters  # starter still created


def test_missing_startnode_still_loads_passages(tmp_path: Path):
    """Ensure dialogs without startnode are still parsed without crashing."""
    content = {
        "passages": [
            {"name": "EntryOnly", "text": "Hi", "pid": "1", "tags": ["entry"]},
        ]
    }
    path = tmp_path / "nostart.json"
    path.write_text(json.dumps(content), encoding="utf-8")
    dlg = read_twine(path)

    assert len(dlg.all_entries()) == 1
    # Current converter picks the first passage as a starter when startnode is absent.
    assert len(dlg.starters) == 1


def test_dangling_link_targets_are_dropped(tmp_path: Path):
    """Drop links that reference non-existent passages instead of raising."""
    content = {
        "startnode": "1",
        "passages": [
            {
                "name": "Entry1",
                "text": "Has bad link [[Missing]]",
                "pid": "1",
                "tags": ["entry"],
            },
        ],
    }
    path = tmp_path / "dangling.json"
    path.write_text(json.dumps(content), encoding="utf-8")

    dlg = read_twine(path)
    assert len(dlg.all_entries()) == 1
    entry = dlg.all_entries()[0]
    assert isinstance(entry, DLGEntry)
    assert entry.links == []


def test_read_twine_rejects_empty_or_missing_storydata(tmp_path: Path):
    """Blank files or HTML without story data should error clearly."""
    empty_path = tmp_path / "empty.txt"
    empty_path.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid Twine format"):
        read_twine(empty_path)

    bad_html = tmp_path / "nostory.html"
    bad_html.write_text("<html><head></head><body></body></html>", encoding="utf-8")
    with pytest.raises(ValueError, match="No story data found"):
        read_twine(bad_html)


def test_language_variants_roundtrip_via_html(tmp_path: Path):
    """Ensure multi-language content survives HTML write/read."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "Polyglot"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Hello")
    entry.text.set_data(Language.SPANISH, Gender.FEMALE, "Hola")
    entry.text.set_data(Language.GERMAN, Gender.MALE, "Guten Tag")
    dlg.starters.append(DLGLink(entry))

    html_path = tmp_path / "lang.html"
    write_twine(dlg, html_path, format="html")
    restored = read_twine(html_path)
    restored_entry = restored.starters[0].node
    assert isinstance(restored_entry, DLGEntry)
    assert restored_entry.text.get(Language.ENGLISH, Gender.MALE) == "Hello"
    assert restored_entry.text.get(Language.SPANISH, Gender.FEMALE) == "Hola"
    assert restored_entry.text.get(Language.GERMAN, Gender.MALE) == "Guten Tag"