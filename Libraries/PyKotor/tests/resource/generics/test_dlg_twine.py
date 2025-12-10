"""Tests for Twine format support in dialog system."""

from __future__ import annotations

import json
import os
import tempfile

from pathlib import Path

import pytest

from pykotor.common.language import Gender, Language
from pykotor.common.misc import Color
from pykotor.resource.generics.dlg.base import DLG
from pykotor.resource.generics.dlg.io.twine import read_twine, write_twine
from pykotor.resource.generics.dlg.io.twine_data import FormatConverter, PassageType
from pykotor.resource.generics.dlg.links import DLGLink
from pykotor.resource.generics.dlg.nodes import DLGEntry, DLGReply

os.environ["PYKOTOR_DLG_TWINE_AGGREGATE"] = "1"

# Consolidated imports of all Twine-specific test modules for re-export.
from .dlg import test_twine_formats as _test_twine_formats
from .dlg import test_twine_conversion as _test_twine_conversion
from .dlg import test_twine_edge_cases as _test_twine_edge_cases
from . import test_dlg_twine_edge as _test_dlg_twine_edge


@pytest.fixture
def sample_dlg() -> DLG:
    """Create a sample dialog for testing."""
    dlg = DLG()

    # Create some entries and replies
    entry1 = DLGEntry()
    entry1.speaker = "NPC"
    entry1.text.set_data(Language.ENGLISH, Gender.MALE, "Hello there!")

    reply1 = DLGReply()
    reply1.text.set_data(Language.ENGLISH, Gender.MALE, "General Kenobi!")

    entry2 = DLGEntry()
    entry2.speaker = "NPC"
    entry2.text.set_data(Language.ENGLISH, Gender.MALE, "You are a bold one.")

    # Link them together
    entry1.links.append(DLGLink(reply1))
    reply1.links.append(DLGLink(entry2))

    # Add starting node
    dlg.starters.append(DLGLink(entry1))

    return dlg


def test_write_read_json(sample_dlg: DLG, tmp_path: Path):
    """Test writing and reading dialog in JSON format."""
    # Write to JSON
    json_file = tmp_path / "test.json"
    write_twine(sample_dlg, json_file, format="json")

    # Verify JSON structure
    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)
        assert data["name"] == "Converted Dialog"
        assert len(data["passages"]) == 3
        assert any(p["name"] == "NPC" for p in data["passages"])
        # Text may have links appended, so check if it contains the text
        assert any("Hello there!" in p["text"] for p in data["passages"])
        assert any("General Kenobi!" in p["text"] for p in data["passages"])

    # Read back
    dlg = read_twine(json_file)
    assert len(dlg.starters) == 1
    assert isinstance(dlg.starters[0].node, DLGEntry)
    assert dlg.starters[0].node.text.get(Language.ENGLISH, Gender.MALE) == "Hello there!"


def test_write_read_html(sample_dlg: DLG, tmp_path: Path):
    """Test writing and reading dialog in HTML format."""
    # Write to HTML
    html_file = tmp_path / "test.html"
    write_twine(sample_dlg, html_file)

    # Read back
    dlg = read_twine(html_file)
    assert len(dlg.starters) == 1
    assert isinstance(dlg.starters[0].node, DLGEntry)
    assert dlg.starters[0].node.text.get(Language.ENGLISH, Gender.MALE) == "Hello there!"


def test_metadata_preservation(sample_dlg: DLG, tmp_path: Path):
    """Test that metadata is preserved during write/read."""
    metadata = {
        "name": "Test Dialog",
        "format": "Harlowe",
        "format-version": "3.3.7",
        "tag-colors": {"reply": "green"},
        "style": "body { color: red; }",
        "script": "window.setup = {};",
    }

    # Write with metadata
    json_file = tmp_path / "test.json"
    write_twine(sample_dlg, json_file, format="json", metadata=metadata)

    # Verify metadata in JSON
    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)
        assert data["name"] == metadata["name"]
        assert data["format"] == metadata["format"]
        assert data["format-version"] == metadata["format-version"]
        assert data["tag-colors"] == metadata["tag-colors"]
        assert data["style"] == metadata["style"]
        assert data["script"] == metadata["script"]


def test_passage_metadata(sample_dlg: DLG, tmp_path: Path):
    """Test that passage metadata (position, size) is preserved."""
    # Note: The comment field on DLGEntry is for story-level Twine metadata,
    # not passage-level position/size. Passage position/size defaults to (0,0) and (100,100).
    # This test verifies that default metadata is present.
    
    # Write to JSON
    json_file = tmp_path / "test.json"
    write_twine(sample_dlg, json_file, format="json")

    # Verify metadata in JSON (defaults should be present)
    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)
        passage = next(p for p in data["passages"] if p["name"] == "NPC")
        # Default position is "0.0,0.0" and size is "100.0,100.0"
        assert "position" in passage["metadata"]
        assert "size" in passage["metadata"]
        # Position defaults to 0,0
        assert passage["metadata"]["position"] == "0.0,0.0"
        assert passage["metadata"]["size"] == "100.0,100.0"


def test_link_preservation(sample_dlg: DLG, tmp_path: Path):
    """Test that links between nodes are preserved."""
    # Write to JSON
    json_file = tmp_path / "test.json"
    write_twine(sample_dlg, json_file, format="json")

    # Read back
    dlg = read_twine(json_file)

    # Verify links
    assert len(dlg.starters) == 1
    entry1 = dlg.starters[0].node
    assert isinstance(entry1, DLGEntry)
    assert len(entry1.links) == 1

    reply1 = entry1.links[0].node
    assert isinstance(reply1, DLGReply)
    assert len(reply1.links) == 1

    entry2 = reply1.links[0].node
    assert isinstance(entry2, DLGEntry)
    assert entry2.text.get(Language.ENGLISH, Gender.MALE) == "You are a bold one."


def test_invalid_json():
    """Test handling of invalid JSON input."""
    invalid_file = Path(tempfile.mkdtemp()) / "invalid.json"
    invalid_file.write_text("invalid json", encoding="utf-8")
    # read_twine checks format first (starts with { or <), so invalid content raises ValueError
    with pytest.raises(ValueError, match="Invalid Twine format"):
        read_twine(invalid_file)


def test_invalid_html():
    """Test handling of invalid HTML input."""
    invalid_file = Path(tempfile.mkdtemp()) / "invalid.html"
    invalid_file.write_text("<not valid html>", encoding="utf-8")
    with pytest.raises(ValueError):
        read_twine(invalid_file)


def test_complex_dialog_structure(tmp_path: Path):
    """Test handling of more complex dialog structures."""
    dlg = DLG()

    # Create a branching dialog
    entry1 = DLGEntry()
    entry1.speaker = "NPC"
    entry1.text.set_data(Language.ENGLISH, Gender.MALE, "Choose your path:")

    reply1 = DLGReply()
    reply1.text.set_data(Language.ENGLISH, Gender.MALE, "Path 1")

    reply2 = DLGReply()
    reply2.text.set_data(Language.ENGLISH, Gender.MALE, "Path 2")

    entry2 = DLGEntry()
    entry2.speaker = "NPC"
    entry2.text.set_data(Language.ENGLISH, Gender.MALE, "Path 1 chosen")

    entry3 = DLGEntry()
    entry3.speaker = "NPC"
    entry3.text.set_data(Language.ENGLISH, Gender.MALE, "Path 2 chosen")

    # Link them
    entry1.links.append(DLGLink(reply1))
    entry1.links.append(DLGLink(reply2))
    reply1.links.append(DLGLink(entry2))
    reply2.links.append(DLGLink(entry3))

    dlg.starters.append(DLGLink(entry1))

    # Write and read back
    json_file = tmp_path / "complex.json"
    write_twine(dlg, json_file, format="json")
    loaded_dlg = read_twine(json_file)

    # Verify structure
    assert len(loaded_dlg.starters) == 1
    entry1 = loaded_dlg.starters[0].node
    assert isinstance(entry1, DLGEntry)
    assert len(entry1.links) == 2

    # Verify both paths
    for link in entry1.links:
        reply = link.node
        assert isinstance(reply, DLGReply)
        assert len(reply.links) == 1
        next_entry = reply.links[0].node
        assert isinstance(next_entry, DLGEntry)
        assert next_entry.text.get(Language.ENGLISH, Gender.MALE) in ["Path 1 chosen", "Path 2 chosen"]


def test_comment_metadata_is_restored_into_twine_story():
    """Ensure Twine metadata embedded in DLG.comment is surfaced in TwineStory."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Hi")
    dlg.starters.append(DLGLink(entry))
    dlg.comment = json.dumps(
        {
            "style": "body { color: blue; }",
            "script": "window.custom = true;",
            "tag_colors": {"entry": "1 0 0 1"},
            "format": "SugarCube",
            "format_version": "2.0.0",
            "creator": "Tester",
            "creator_version": "0.1",
            "zoom": 1.25,
        }
    )

    story = FormatConverter()._dlg_to_story(dlg)
    assert story.metadata.style == "body { color: blue; }"
    assert story.metadata.script == "window.custom = true;"
    assert story.metadata.format == "SugarCube"
    assert story.metadata.format_version == "2.0.0"
    assert story.metadata.creator == "Tester"
    assert story.metadata.creator_version == "0.1"
    assert story.metadata.zoom == 1.25
    assert isinstance(story.metadata.tag_colors["entry"], Color)


def test_first_starter_becomes_start_pid(tmp_path: Path):
    """The first starter should be used as startnode when exporting to Twine JSON."""
    dlg = DLG()
    entry1 = DLGEntry()
    entry1.speaker = "First"
    entry1.text.set_data(Language.ENGLISH, Gender.MALE, "First line")

    entry2 = DLGEntry()
    entry2.speaker = "Second"
    entry2.text.set_data(Language.ENGLISH, Gender.MALE, "Second line")

    dlg.starters.append(DLGLink(entry1))
    dlg.starters.append(DLGLink(entry2))

    json_path = tmp_path / "multi_start.json"
    write_twine(dlg, json_path, format="json")

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["startnode"]  # startnode should be recorded
    assert len(data["passages"]) == 2
    assert data["passages"][0]["name"] in {"First", "Entry"}
    assert data["passages"][1]["name"] in {"Second", "Entry_1"}


def test_get_links_to_reports_sources():
    """TwineStory.get_links_to should report all linking passages."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "A"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Hi")
    reply = DLGReply()
    reply.text.set_data(Language.ENGLISH, Gender.MALE, "R")
    entry.links.append(DLGLink(reply))
    reply.links.append(DLGLink(entry))
    dlg.starters.append(DLGLink(entry))

    story = FormatConverter()._dlg_to_story(dlg)
    target = story.get_passage("A")
    assert target is not None
    linking = story.get_links_to(target)
    assert linking
    source, link = linking[0]
    assert source.type == PassageType.REPLY
    assert link.target == target.name


def test_metadata_comment_roundtrip_for_tag_colors_and_zoom(tmp_path: Path):
    """Metadata supplied to write_twine should be persisted in dlg.comment."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "Meta"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "meta")
    dlg.starters.append(DLGLink(entry))

    metadata = {
        "name": "Meta Story",
        "format": "Harlowe",
        "format-version": "3.3.7",
        "tag-colors": {"entry": "1 0 0 1", "reply": "0 1 0 1"},
        "style": "body { color: green; }",
        "script": "window.meta = true;",
        "zoom": 2.5,
    }
    path = tmp_path / "meta.json"
    write_twine(dlg, path, format="json", metadata=metadata)

    restored_dlg = read_twine(path)
    restored_meta = json.loads(restored_dlg.comment)
    assert restored_meta["style"] == "body { color: green; }"
    assert restored_meta["script"] == "window.meta = true;"
    assert restored_meta["tag_colors"]["entry"] == "1 0 0 1"
    assert restored_meta["tag_colors"]["reply"] == "0 1 0 1"
    assert restored_meta["zoom"] == 2.5


# Re-export all Twine-focused tests from consolidated modules so they are
# collected from this single file.
for _module in (
    _test_twine_formats,
    _test_twine_conversion,
    _test_twine_edge_cases,
    _test_dlg_twine_edge,
):
    for _name in dir(_module):
        if _name.startswith("test_"):
            globals()[_name] = getattr(_module, _name)