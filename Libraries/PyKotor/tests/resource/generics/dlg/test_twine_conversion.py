"""Tests for Twine format conversion."""

from __future__ import annotations

import json
import tempfile

from pathlib import Path
from typing import TYPE_CHECKING

import os
import pytest

if os.environ.get("PYKOTOR_DLG_TWINE_AGGREGATE") != "1":
    pytest.skip(
        "Consolidated into Libraries/PyKotor/tests/resource/generics/test_dlg_twine.py",
        allow_module_level=True,
    )

from pykotor.common.language import Gender, Language
from pykotor.common.misc import Color, ResRef
from pykotor.resource.generics.dlg.base import DLG
from pykotor.resource.generics.dlg.io.twine import read_twine, write_twine
from pykotor.resource.generics.dlg.io.twine_data import (
    FormatConverter,
    PassageMetadata,
    PassageType,
    TwineLink,
    TwineMetadata,
    TwinePassage,
    TwineStory,
)
from pykotor.resource.generics.dlg.links import DLGLink
from pykotor.resource.generics.dlg.nodes import DLGEntry, DLGReply
from utility.common.geometry import Vector2

if TYPE_CHECKING:
    from typing import Any


def test_story_to_dlg_basic():
    """Test basic conversion from TwineStory to DLG."""
    # Create a simple story
    story = TwineStory(
        metadata=TwineMetadata(name="Test Story"),
        passages=[
            TwinePassage(
                name="NPC",
                text="Hello there!",
                type=PassageType.ENTRY,
                pid="1",
                metadata=PassageMetadata(
                    position=Vector2(100, 100),
                    size=Vector2(100, 100),
                ),
            ),
            TwinePassage(
                name="Reply_1",
                text="General Kenobi!",
                type=PassageType.REPLY,
                pid="2",
                metadata=PassageMetadata(
                    position=Vector2(200, 100),
                    size=Vector2(100, 100),
                ),
            ),
        ],
        start_pid="1",
    )

    # Add link
    story.passages[0].links.append(TwineLink(text="Continue", target="Reply_1"))

    # Convert to DLG
    converter = FormatConverter()
    dlg = converter._story_to_dlg(story)

    # Verify structure
    assert len(dlg.starters) == 1
    entry = dlg.starters[0].node
    assert isinstance(entry, DLGEntry)
    assert entry.speaker == "NPC"
    assert entry.text.get(Language.ENGLISH, Gender.MALE) == "Hello there!"

    assert len(entry.links) == 1
    reply = entry.links[0].node
    assert isinstance(reply, DLGReply)
    assert reply.text.get(Language.ENGLISH, Gender.MALE) == "General Kenobi!"


def test_dlg_to_story_basic():
    """Test basic conversion from DLG to TwineStory."""
    # Create a simple dialog
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Hello there!")

    reply = DLGReply()
    reply.text.set_data(Language.ENGLISH, Gender.MALE, "General Kenobi!")

    entry.links.append(DLGLink(reply))
    dlg.starters.append(DLGLink(entry))

    # Convert to TwineStory
    converter = FormatConverter()
    story = converter._dlg_to_story(dlg)

    # Verify structure
    assert len(story.passages) == 2
    entry_passage = story.start_passage
    assert entry_passage is not None
    assert entry_passage.name == "NPC"
    assert entry_passage.text == "Hello there!"
    assert entry_passage.type == PassageType.ENTRY

    assert len(entry_passage.links) == 1
    reply_passage = next(p for p in story.passages if p.type == PassageType.REPLY)
    assert reply_passage.text == "General Kenobi!"


def test_metadata_preservation():
    """Test preservation of metadata during conversion."""
    # Create a story with metadata
    story = TwineStory(
        metadata=TwineMetadata(
            name="Test Story",
            style="body { color: red; }",
            script="window.setup = {};",
            tag_colors={"reply": Color.GREEN},
            format="Harlowe",
            format_version="3.3.7",
            creator="PyKotor",
            creator_version="1.0.0",
            zoom=1.0,
        ),
        passages=[
            TwinePassage(
                name="NPC",
                text="Test",
                type=PassageType.ENTRY,
                pid="1",
                metadata=PassageMetadata(
                    position=Vector2(100, 100),
                    size=Vector2(100, 100),
                    camera_angle=45,
                    animation_id=123,
                ),
            ),
        ],
        start_pid="1",
    )

    # Convert to DLG and back
    converter = FormatConverter()
    dlg = converter._story_to_dlg(story)
    new_story = converter._dlg_to_story(dlg)

    # Verify metadata preserved
    assert new_story.metadata.style == story.metadata.style
    assert new_story.metadata.script == story.metadata.script
    assert new_story.metadata.tag_colors == story.metadata.tag_colors

    # Verify passage metadata preserved
    new_passage = new_story.start_passage
    assert new_passage is not None
    assert new_passage.metadata.camera_angle == story.passages[0].metadata.camera_angle
    assert new_passage.metadata.animation_id == story.passages[0].metadata.animation_id


def test_circular_references():
    """Test handling of circular references."""
    # Create a dialog with circular reference
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "First")

    reply = DLGReply()
    reply.text.set_data(Language.ENGLISH, Gender.MALE, "Back to start")

    # Create circular reference
    entry.links.append(DLGLink(reply))
    reply.links.append(DLGLink(entry))
    dlg.starters.append(DLGLink(entry))

    # Convert to TwineStory and back
    converter = FormatConverter()
    story = converter._dlg_to_story(dlg)
    new_dlg = converter._story_to_dlg(story)

    # Verify structure preserved
    assert len(new_dlg.starters) == 1
    new_entry = new_dlg.starters[0].node
    assert isinstance(new_entry, DLGEntry)
    assert len(new_entry.links) == 1

    new_reply = new_entry.links[0].node
    assert isinstance(new_reply, DLGReply)
    assert len(new_reply.links) == 1
    assert isinstance(new_reply.links[0].node, DLGEntry)


def test_json_format():
    """Test reading/writing JSON format."""
    # Create a simple dialog
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Hello!")
    dlg.starters.append(DLGLink(entry))

    tmpdir = Path(tempfile.mkdtemp())
    json_path = tmpdir / "test.json"
    write_twine(dlg, json_path, format="json")

    with open(json_path, encoding="utf-8") as f2:
        data: dict[str, Any] = json.load(f2)
        assert "name" in data
        assert "passages" in data
        assert len(data["passages"]) == 1
        assert data["passages"][0]["name"] == "NPC"
        assert data["passages"][0]["text"] == "Hello!"

    new_dlg = read_twine(json_path)
    assert len(new_dlg.starters) == 1
    new_entry = new_dlg.starters[0].node
    assert isinstance(new_entry, DLGEntry)
    assert new_entry.speaker == "NPC"
    assert new_entry.text.get(Language.ENGLISH, Gender.MALE) == "Hello!"


def test_html_format():
    """Test reading/writing HTML format."""
    # Create a simple dialog
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Hello!")
    dlg.starters.append(DLGLink(entry))

    tmpdir = Path(tempfile.mkdtemp())
    html_path = tmpdir / "test.html"
    write_twine(dlg, html_path, format="html")

    new_dlg = read_twine(html_path)
    assert len(new_dlg.starters) == 1
    new_entry = new_dlg.starters[0].node
    assert isinstance(new_entry, DLGEntry)
    assert new_entry.speaker == "NPC"
    assert new_entry.text.get(Language.ENGLISH, Gender.MALE) == "Hello!"


def test_invalid_formats():
    """Test handling of invalid formats."""
    dlg = DLG()

    # Invalid format
    with pytest.raises(ValueError):
        write_twine(dlg, "test.txt", format="invalid")  # type: ignore

    # Invalid JSON
    tmpdir = Path(tempfile.mkdtemp())
    bad_json = tmpdir / "invalid.json"
    bad_json.write_text("invalid json", encoding="utf-8")
    with pytest.raises(ValueError):
        read_twine(bad_json)

    # Invalid HTML
    bad_html = tmpdir / "invalid.html"
    bad_html.write_text("<not valid html>", encoding="utf-8")
    with pytest.raises(ValueError):
        read_twine(bad_html)


def test_complex_dialog():
    """Test handling of complex dialog structures."""
    # Create a branching dialog
    dlg = DLG()

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

    # Convert to TwineStory and back
    tmpdir = Path(tempfile.mkdtemp())
    json_path = tmpdir / "complex.json"
    write_twine(dlg, json_path, format="json")
    new_dlg = read_twine(json_path)

    # Verify structure preserved
    assert len(new_dlg.starters) == 1
    new_entry1 = new_dlg.starters[0].node
    assert isinstance(new_entry1, DLGEntry)
    assert len(new_entry1.links) == 2

    # Verify both paths
    for link in new_entry1.links:
        reply = link.node
        assert isinstance(reply, DLGReply)
        assert len(reply.links) == 1
        next_entry = reply.links[0].node
        assert isinstance(next_entry, DLGEntry)
        assert next_entry.text.get(Language.ENGLISH, Gender.MALE) in [
            "Path 1 chosen",
            "Path 2 chosen",
        ]


def test_language_variants_roundtrip():
    """Ensure localized strings survive DLG -> Twine -> DLG conversions."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Hello")
    entry.text.set_data(Language.FRENCH, Gender.FEMALE, "Salut")
    entry.text.set_data(Language.GERMAN, Gender.MALE, "Guten Tag")
    dlg.starters.append(DLGLink(entry))

    converter = FormatConverter()
    story = converter._dlg_to_story(dlg)
    passage = story.start_passage
    assert passage is not None
    assert passage.metadata.custom.get("text_french_1") == "Salut"
    assert passage.metadata.custom.get("text_german_0") == "Guten Tag"

    restored = converter._story_to_dlg(story)
    restored_entry = restored.starters[0].node
    assert isinstance(restored_entry, DLGEntry)
    assert restored_entry.text.get(Language.FRENCH, Gender.FEMALE) == "Salut"
    assert restored_entry.text.get(Language.GERMAN, Gender.MALE) == "Guten Tag"


def test_kotor_metadata_roundtrip_with_optional_fields():
    """Verify KotOR-specific metadata survives format conversion."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Metadata")
    entry.camera_anim = 321
    entry.camera_angle = 33
    entry.camera_id = 7
    entry.fade_type = 4
    entry.quest = "SideQuest"
    entry.sound = ResRef("snd")
    entry.vo_resref = ResRef("vo_line")
    dlg.starters.append(DLGLink(entry))

    converter = FormatConverter()
    story = converter._dlg_to_story(dlg)
    passage = story.start_passage
    assert passage is not None
    assert passage.metadata.animation_id == 321
    assert passage.metadata.camera_angle == 33
    assert passage.metadata.camera_id == 7
    assert passage.metadata.fade_type == 4
    assert passage.metadata.quest == "SideQuest"
    assert passage.metadata.sound == "snd"
    assert passage.metadata.vo_resref == "vo_line"

    restored = converter._story_to_dlg(story)
    restored_entry = restored.starters[0].node
    assert isinstance(restored_entry, DLGEntry)
    assert restored_entry.camera_anim == 321
    assert restored_entry.camera_angle == 33
    assert restored_entry.camera_id == 7
    assert restored_entry.fade_type == 4
    assert restored_entry.quest == "SideQuest"
    assert str(restored_entry.sound) == "snd"
    assert str(restored_entry.vo_resref) == "vo_line"


def test_format_converter_store_restore_metadata_roundtrip():
    """Explicitly validate FormatConverter metadata helpers."""
    converter = FormatConverter()
    passage = TwinePassage(
        name="Start",
        text="Hi",
        type=PassageType.ENTRY,
        pid="1",
        metadata=PassageMetadata(),
    )
    node = DLGEntry()
    node.camera_anim = 9
    node.camera_angle = 11
    node.camera_id = 13
    node.fade_type = 2
    node.quest = "MetaQuest"
    node.sound = ResRef("snd_meta")
    node.vo_resref = ResRef("vo_meta")

    converter.store_kotor_metadata(passage, node)
    restored_node = DLGEntry()
    converter.restore_kotor_metadata(restored_node, passage)

    assert passage.metadata.animation_id == 9
    assert passage.metadata.camera_angle == 11
    assert passage.metadata.camera_id == 13
    assert passage.metadata.fade_type == 2
    assert passage.metadata.quest == "MetaQuest"
    assert passage.metadata.sound == "snd_meta"
    assert passage.metadata.vo_resref == "vo_meta"
    assert restored_node.camera_anim == 9
    assert restored_node.camera_angle == 11
    assert restored_node.camera_id == 13
    assert restored_node.fade_type == 2
    assert restored_node.quest == "MetaQuest"
    assert str(restored_node.sound) == "snd_meta"
    assert str(restored_node.vo_resref) == "vo_meta"


def test_dlg_to_story_assigns_unique_names_and_child_flags():
    """Ensure unique passage names and link metadata are retained."""
    dlg = DLG()
    entry1 = DLGEntry()
    entry1.speaker = "NPC"
    entry1.text.set_data(Language.ENGLISH, Gender.MALE, "Line1")

    entry2 = DLGEntry()
    entry2.speaker = "NPC"
    entry2.text.set_data(Language.ENGLISH, Gender.MALE, "Line2")

    reply = DLGReply()
    reply.text.set_data(Language.ENGLISH, Gender.MALE, "Reply")
    link_child = DLGLink(node=entry2, list_index=0)
    link_child.is_child = True
    link_child.active1 = ResRef("cond_script")

    entry1.links.append(DLGLink(node=reply, list_index=0))
    reply.links.append(link_child)
    dlg.starters.append(DLGLink(entry1))

    story = FormatConverter()._dlg_to_story(dlg)
    names = {p.name for p in story.passages}
    assert "NPC" in names
    assert "NPC_1" in names  # second entry should be suffixed

    entry_passage = next(p for p in story.passages if p.type == PassageType.ENTRY and p.name == "NPC")
    reply_passage = next(p for p in story.passages if p.type == PassageType.REPLY)
    assert reply_passage.links
    link = reply_passage.links[0]
    assert link.is_child is True
    assert link.active_script == "cond_script"
    assert story.start_pid == entry_passage.pid


def test_restore_twine_metadata_with_invalid_json_is_safe():
    """Invalid dialog.comment should not crash metadata restoration."""
    dlg = DLG()
    dlg.comment = "{not valid json"
    story = TwineStory(metadata=TwineMetadata(name="Test"), passages=[])
    FormatConverter().restore_twine_metadata(dlg, story)
    assert story.metadata.style == ""
    assert story.metadata.script == ""