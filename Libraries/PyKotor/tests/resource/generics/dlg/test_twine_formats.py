"""Tests for Twine format-specific features."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, cast
from xml.etree import ElementTree

import pytest

from pykotor.common.language import Gender, Language
from pykotor.resource.generics.dlg.base import DLG
from pykotor.resource.generics.dlg.links import DLGLink
from pykotor.resource.generics.dlg.nodes import DLGEntry, DLGReply
from pykotor.resource.generics.dlg.io.twine import read_twine, write_twine

if TYPE_CHECKING:
    from typing import Any


def test_html_structure():
    """Test HTML format structure."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Hello!")
    dlg.starters.append(DLGLink(entry))

    tmpdir = Path(tempfile.mkdtemp())
    html_path = tmpdir / "test.html"
    write_twine(dlg, html_path, format="html")

    content = html_path.read_text(encoding="utf-8")
    root = ElementTree.fromstring(content)

    assert root.tag == "html"
    story_data = root.find(".//tw-storydata")
    assert story_data is not None

    passage = story_data.find(".//tw-passagedata")
    assert passage is not None
    assert passage.get("name") == "NPC"
    assert passage.text == "Hello!"


def test_html_style_script():
    """Test HTML style and script preservation."""
    metadata = {
        "style": "body { color: red; }",
        "script": "window.setup = {};",
    }

    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Test")
    dlg.starters.append(DLGLink(entry))

    tmpdir = Path(tempfile.mkdtemp())
    html_path = tmpdir / "style.html"
    write_twine(dlg, html_path, format="html", metadata=metadata)

    content = html_path.read_text(encoding="utf-8")
    root = ElementTree.fromstring(content)

    style = root.find(".//style[@type='text/twine-css']")
    assert style is not None
    assert style.text == metadata["style"]

    script = root.find(".//script[@type='text/twine-javascript']")
    assert script is not None
    assert script.text == metadata["script"]


def test_html_tag_colors():
    """Test HTML tag color preservation."""
    metadata = {
        "tag-colors": {
            "entry": "green",
            "reply": "blue",
        },
    }

    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Test")
    dlg.starters.append(DLGLink(entry))

    tmpdir = Path(tempfile.mkdtemp())
    html_path = tmpdir / "tags.html"
    write_twine(dlg, html_path, format="html", metadata=metadata)

    content = html_path.read_text(encoding="utf-8")
    root = ElementTree.fromstring(content)

    tags = root.findall(".//tw-tag")
    tag_colors = {tag.get("name"): tag.get("color") for tag in tags}
    assert tag_colors == metadata["tag-colors"]


def test_json_structure():
    """Test JSON format structure."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Hello!")
    dlg.starters.append(DLGLink(entry))

    tmpdir = Path(tempfile.mkdtemp())
    json_path = tmpdir / "test.json"
    write_twine(dlg, json_path, format="json")

    data: dict[str, Any] = json.loads(json_path.read_text(encoding="utf-8"))
    assert "name" in data
    assert "passages" in data
    assert isinstance(data["passages"], list)

    passage = data["passages"][0]
    assert passage["name"] == "NPC"
    assert passage["text"] == "Hello!"
    assert "tags" in passage
    assert "metadata" in passage


def test_json_metadata():
    """Test JSON metadata preservation."""
    metadata = {
        "name": "Test Story",
        "format": "Harlowe",
        "format-version": "3.3.7",
        "tag-colors": {"reply": "green"},
        "style": "body { color: red; }",
        "script": "window.setup = {};",
        "zoom": 1.5,
        "creator": "PyKotor",
        "creator-version": "1.0.0",
    }

    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Test")
    dlg.starters.append(DLGLink(entry))

    tmpdir = Path(tempfile.mkdtemp())
    json_path = tmpdir / "meta.json"
    write_twine(dlg, json_path, format="json", metadata=metadata)

    data: dict[str, Any] = json.loads(json_path.read_text(encoding="utf-8"))
    for key, value in metadata.items():
        assert data[key.replace("_", "-")] == value


def test_format_detection():
    """Test format detection from content."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Test")
    dlg.starters.append(DLGLink(entry))

    tmpdir = Path(tempfile.mkdtemp())
    json_path = tmpdir / "detect.txt"
    write_twine(dlg, json_path, format="json")
    new_dlg = read_twine(json_path)
    assert len(new_dlg.starters) == 1

    html_path = tmpdir / "detect.html"
    write_twine(dlg, html_path, format="html")
    new_dlg = read_twine(html_path)
    assert len(new_dlg.starters) == 1


def test_invalid_html():
    """Test handling of invalid HTML."""
    tmpdir = Path(tempfile.mkdtemp())
    bad_html = tmpdir / "bad.html"
    bad_html.write_text("<html></html>", encoding="utf-8")
    with pytest.raises(ValueError, match="No story data found"):
        read_twine(bad_html)

    bad_html2 = tmpdir / "bad2.html"
    bad_html2.write_text("<not valid xml>", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid HTML"):
        read_twine(bad_html2)


def test_invalid_json():
    """Test handling of invalid JSON."""
    tmpdir = Path(tempfile.mkdtemp())
    bad_json = tmpdir / "bad.json"
    bad_json.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        read_twine(bad_json)

    empty_json = tmpdir / "empty.json"
    empty_json.write_text(json.dumps({}), encoding="utf-8")
    dlg = read_twine(empty_json)
    assert len(dlg.starters) == 0


def test_format_conversion():
    """Test conversion between formats."""
    dlg = DLG()
    entry = DLGEntry()
    entry.speaker = "NPC"
    entry.text.set_data(Language.ENGLISH, Gender.MALE, "Test")
    dlg.starters.append(DLGLink(entry))

    metadata = {
        "style": "body { color: red; }",
        "script": "window.setup = {};",
        "tag-colors": {"reply": "green"},
    }

    tmpdir = Path(tempfile.mkdtemp())
    html_path = tmpdir / "format.html"
    write_twine(dlg, html_path, format="html", metadata=metadata)
    html_dlg = read_twine(html_path)

    json_path = tmpdir / "format.json"
    write_twine(html_dlg, json_path, format="json")
    json_dlg = read_twine(json_path)

    assert len(json_dlg.starters) == 1
    json_entry = json_dlg.starters[0].node
    assert isinstance(json_entry, DLGEntry)
    assert json_entry.speaker == "NPC"
    assert json_entry.text.get(Language.ENGLISH, Gender.MALE) == "Test"

    json_path2 = tmpdir / "format2.json"
    write_twine(dlg, json_path2, format="json", metadata=metadata)
    json_dlg2 = read_twine(json_path2)

    html_path2 = tmpdir / "format2.html"
    write_twine(json_dlg2, html_path2, format="html")
    html_dlg = read_twine(html_path2)

    assert len(html_dlg.starters) == 1
    html_entry = html_dlg.starters[0].node
    assert isinstance(html_entry, DLGEntry)
    assert html_entry.speaker == "NPC"
    assert html_entry.text.get(Language.ENGLISH, Gender.MALE) == "Test"


def test_link_syntax():
    """Test Twine link syntax handling."""
    # Create a dialog with various link types
    dlg = DLG()

    entry1 = DLGEntry()
    entry1.speaker = "NPC1"
    entry1.text.set_data(Language.ENGLISH, Gender.MALE, "First")

    entry2 = DLGEntry()
    entry2.speaker = "NPC2"
    entry2.text.set_data(Language.ENGLISH, Gender.MALE, "Second")

    reply = DLGReply()
    reply.text.set_data(Language.ENGLISH, Gender.MALE, "Reply")

    # Create links
    entry1.links.append(DLGLink(reply))
    reply.links.append(DLGLink(entry2))
    dlg.starters.append(DLGLink(entry1))

    tmpdir = Path(tempfile.mkdtemp())
    json_path = tmpdir / "links.json"
    write_twine(dlg, json_path, format="json")

    data: dict[str, Any] = json.loads(json_path.read_text(encoding="utf-8"))
    passages = cast(list[dict[str, Any]], data["passages"])

    entry1_passage = next(p for p in passages if p["name"] == "NPC1")
    entry1_text: str = str(entry1_passage.get("text") or "")
    assert "[[Continue->Reply_1]]" in entry1_text

    reply_passage = next(p for p in passages if p["name"] == "Reply_1")
    reply_text: str = str(reply_passage.get("text") or "")
    assert "[[Continue->NPC2]]" in reply_text

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html") as html_file:
        write_twine(dlg, html_file.name, format="html")

        # Verify HTML links
        with open(html_file.name, encoding="utf-8") as f:
            content = f.read()
            root = ElementTree.fromstring(content)

            # Find entry1's passage
            entry1_passage = root.find(".//tw-passagedata[@name='NPC1']")
            assert entry1_passage is not None
            assert "[[Continue->Reply_1]]" in str(entry1_passage.text or "")

            # Find reply's passage
            reply_passage = root.find(".//tw-passagedata[contains(@tags,'reply')]")
            assert reply_passage is not None
            assert "[[Continue->NPC2]]" in str(reply_passage.text or "")
