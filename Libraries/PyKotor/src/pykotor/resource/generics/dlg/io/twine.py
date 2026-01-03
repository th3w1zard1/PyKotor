"""Twine format support for dialog system."""

from __future__ import annotations

import json
import re
import uuid

from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from xml.etree import ElementTree as ET

try:
    from defusedxml import ElementTree as _ElementTree

    fromstring = _ElementTree.fromstring
except ImportError:
    fromstring = ET.fromstring

from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.common.misc import Color
from pykotor.resource.generics.dlg.base import DLG
from pykotor.resource.generics.dlg.io.twine_data import FormatConverter, PassageMetadata, PassageType, TwineLink, TwineMetadata, TwinePassage, TwineStory
from pykotor.resource.generics.dlg.links import DLGLink
from pykotor.resource.generics.dlg.nodes import DLGEntry, DLGReply
from utility.common.geometry import Vector2

if TYPE_CHECKING:
    from typing_extensions import Literal, TypeAlias, TypedDict  # pyright: ignore[reportMissingModuleSource]

    Format: TypeAlias = Literal["html", "json"]

    class PassageMetadataDict(TypedDict, total=False):
        position: str
        size: str
        custom: dict[str, str]  # Optional: for storing language variants and other custom data

    class PassageDict(TypedDict):
        name: str
        text: str
        tags: list[str]
        pid: str
        metadata: PassageMetadataDict

    class StoryDict(TypedDict):
        name: str
        ifid: str
        format: str
        format_version: str
        zoom: float
        creator: str
        creator_version: str
        style: str
        script: str
        tag_colors: dict[str, str]
        passages: list[PassageDict]


def read_twine(path: str | Path) -> DLG:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    content: str = path.read_text(encoding="utf-8")
    if content.strip().startswith("{"):
        story = _read_json(content)
    elif content.strip().startswith("<"):
        story = _read_html(content)
    else:
        raise ValueError("Invalid Twine format - must be HTML or JSON")

    return _story_to_dlg(story)


def write_twine(
    dlg: DLG,
    path: str | Path,
    fmt: Format | None = None,
    *,
    format: Format | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Write a dialog to Twine format.

    If no format is provided, infer from file extension: ``.json`` -> JSON, otherwise
    HTML. ``format`` is accepted as an alias for backward compatibility.
    """
    path = Path(path)
    # `format` is a legacy alias; prefer `fmt` when both are provided.
    chosen_fmt: Format | None = fmt or format
    inferred_fmt: Format = chosen_fmt or ("json" if path.suffix.lower() == ".json" else "html")

    story: TwineStory = _dlg_to_story(dlg, metadata)

    if inferred_fmt == "json":
        _write_json(story, path)
    elif inferred_fmt == "html":
        _write_html(story, path)
    else:
        raise ValueError(f"Invalid format: {inferred_fmt}")


def _read_json(content: str) -> TwineStory:
    try:
        data: dict[str, Any] = json.loads(content)
    except json.JSONDecodeError as exc:
        # Preserve legacy API: invalid JSON raises ValueError for callers/tests.
        raise ValueError("Invalid JSON") from exc

    # Create metadata
    twine_metadata: TwineMetadata = TwineMetadata(
        name=data.get("name", "Converted Dialog"),
        ifid=data.get("ifid", str(uuid.uuid4())),
        format=data.get("format", "Harlowe"),
        format_version=data.get("format-version", "3.3.7"),
        zoom=float(data.get("zoom", 1.0)),
        creator=data.get("creator", "PyKotor"),
        creator_version=data.get("creator-version", "1.0.0"),
        style=data.get("style", ""),
        script=data.get("script", ""),
        tag_colors=data.get("tag-colors", {}),
    )

    # Create passages
    passages: list[TwinePassage] = []
    p_data: dict[str, Any] = data.get("passages", [])
    for p_data in data.get("passages", []):
        # Determine passage type
        tags: list[str] = p_data.get("tags", [])
        p_type: PassageType = PassageType.ENTRY if "entry" in tags else PassageType.REPLY

        # Parse metadata
        p_meta: dict[str, Any] = p_data.get("metadata", {})
        position: list[str] = p_meta.get("position", "0,0").split(",")
        size: list[str] = p_meta.get("size", "100,100").split(",")
        passage_metadata: PassageMetadata = PassageMetadata(
            position=Vector2(float(position[0]), float(position[1])),
            size=Vector2(float(size[0]), float(size[1])),
        )
        
        # Restore KotOR-specific metadata and custom metadata from custom dict
        if "custom" in p_meta and isinstance(p_meta["custom"], dict):
            custom_data = p_meta["custom"]
            # Restore KotOR-specific fields
            if "animation_id" in custom_data:
                try:
                    passage_metadata.animation_id = int(custom_data["animation_id"])
                except (ValueError, TypeError):
                    pass
            if "camera_angle" in custom_data:
                try:
                    passage_metadata.camera_angle = int(custom_data["camera_angle"])
                except (ValueError, TypeError):
                    pass
            if "camera_id" in custom_data:
                try:
                    camera_id_val = custom_data["camera_id"]
                    # Handle both string and int values, None means not set
                    if camera_id_val is None or camera_id_val == "":
                        passage_metadata.camera_id = None
                    else:
                        passage_metadata.camera_id = int(camera_id_val)
                except (ValueError, TypeError):
                    pass
            if "fade_type" in custom_data:
                try:
                    passage_metadata.fade_type = int(custom_data["fade_type"])
                except (ValueError, TypeError):
                    pass
            if "quest" in custom_data:
                passage_metadata.quest = str(custom_data["quest"])
            if "sound" in custom_data:
                passage_metadata.sound = str(custom_data["sound"]) if custom_data["sound"] else ""
            if "vo_resref" in custom_data:
                passage_metadata.vo_resref = str(custom_data["vo_resref"]) if custom_data["vo_resref"] else ""
            if "speaker" in custom_data:
                passage_metadata.speaker = str(custom_data["speaker"])
            
            # Store remaining custom metadata (e.g., language variants) that aren't KotOR-specific fields
            kotorf_fields = {"animation_id", "camera_angle", "camera_id", "fade_type", "quest", "sound", "vo_resref", "speaker"}
            for key, value in custom_data.items():
                if key not in kotorf_fields:
                    passage_metadata.custom[key] = str(value)

        # Create passage
        passage: TwinePassage = TwinePassage(
            name=p_data.get("name", ""),
            text=p_data.get("text", ""),
            type=p_type,
            pid=p_data.get("pid", str(uuid.uuid4())),
            tags=tags,
            metadata=passage_metadata,
        )

        # Parse links
        link_pattern: str = r"\[\[(.*?)(?:->(.+?))?\]\]"
        for match in re.finditer(link_pattern, passage.text):
            display: str = match.group(1)
            target: str = match.group(2) or display
            passage.links.append(TwineLink(text=display, target=target))

        passages.append(passage)

    story = TwineStory(
        metadata=twine_metadata,
        passages=passages,
        start_pid=data.get("startnode", ""),
    )

    # Fallback: if start_pid missing, prefer first entry passage
    if not story.start_pid and story.get_entries():
        story.start_pid = story.get_entries()[0].pid

    return story


def _read_html(content: str) -> TwineStory:
    try:
        root: ET.Element = fromstring(content)
    except ET.ParseError as e:
        raise ValueError(f"Invalid HTML: {e}") from e

    story_data: ET.Element | None = root.find(".//tw-storydata")
    if story_data is None:
        raise ValueError("No story data found in HTML")

    # Create metadata
    twine_metadata: TwineMetadata = TwineMetadata(
        name=story_data.get("name", "Converted Dialog"),
        ifid=story_data.get("ifid", str(uuid.uuid4())),
        format=story_data.get("format", "Harlowe"),
        format_version=story_data.get("format-version", "3.3.7"),
        zoom=float(story_data.get("zoom", 1.0)),
        creator=story_data.get("creator", "PyKotor"),
        creator_version=story_data.get("creator-version", "1.0.0"),
    )

    # Get style/script
    style: ET.Element | None = story_data.find(".//style[@type='text/twine-css']")
    if style is not None and style.text:
        twine_metadata.style = style.text

    script: ET.Element | None = story_data.find(".//script[@type='text/twine-javascript']")
    if script is not None and script.text:
        twine_metadata.script = script.text

    # Get tag colors
    for tag in story_data.findall(".//tw-tag"):
        name: str = tag.get("name", "").strip()
        color: str = tag.get("color", "").strip()
        if not name:
            continue
        if not color:
            continue

        twine_metadata.tag_colors[name] = Color.from_hex_string(color)

    # Create passages
    passages: list[TwinePassage] = []
    for p_data in story_data.findall(".//tw-passagedata"):
        # Determine passage type
        tags: list[str] = p_data.get("tags", "").split()
        p_type: PassageType = PassageType.ENTRY if "entry" in tags else PassageType.REPLY

        # Parse position/size
        position: list[str] = p_data.get("position", "0,0").split(",")
        size: list[str] = p_data.get("size", "100,100").split(",")
        passage_metadata: PassageMetadata = PassageMetadata(
            position=Vector2(float(position[0]), float(position[1])),
            size=Vector2(float(size[0]), float(size[1])),
        )
        
        # Restore custom metadata from data-custom attribute
        custom_data = p_data.get("data-custom")
        if custom_data:
            try:
                custom_dict = json.loads(custom_data)
                if isinstance(custom_dict, dict):
                    # Extract KotOR-specific fields from custom dict (same as JSON format)
                    if "animation_id" in custom_dict:
                        try:
                            passage_metadata.animation_id = int(custom_dict["animation_id"])
                        except (ValueError, TypeError):
                            pass
                    if "camera_angle" in custom_dict:
                        try:
                            passage_metadata.camera_angle = int(custom_dict["camera_angle"])
                        except (ValueError, TypeError):
                            pass
                    if "camera_id" in custom_dict:
                        try:
                            camera_id_val = custom_dict["camera_id"]
                            if camera_id_val is None or camera_id_val == "":
                                passage_metadata.camera_id = None
                            else:
                                passage_metadata.camera_id = int(camera_id_val)
                        except (ValueError, TypeError):
                            pass
                    if "fade_type" in custom_dict:
                        try:
                            passage_metadata.fade_type = int(custom_dict["fade_type"])
                        except (ValueError, TypeError):
                            pass
                    if "quest" in custom_dict:
                        passage_metadata.quest = str(custom_dict["quest"])
                    if "sound" in custom_dict:
                        passage_metadata.sound = str(custom_dict["sound"]) if custom_dict["sound"] else ""
                    if "vo_resref" in custom_dict:
                        passage_metadata.vo_resref = str(custom_dict["vo_resref"]) if custom_dict["vo_resref"] else ""
                    if "speaker" in custom_dict:
                        passage_metadata.speaker = str(custom_dict["speaker"])
                    
                    # Store remaining custom metadata that aren't KotOR-specific fields
                    kotorf_fields = {"animation_id", "camera_angle", "camera_id", "fade_type", "quest", "sound", "vo_resref", "speaker"}
                    for key, value in custom_dict.items():
                        if key not in kotorf_fields:
                            passage_metadata.custom[key] = str(value)
            except (json.JSONDecodeError, ValueError):
                # Skip invalid JSON
                pass

        # Create passage
        passage = TwinePassage(
            name=p_data.get("name", ""),
            text=p_data.text or "",
            type=p_type,
            pid=p_data.get("pid", str(uuid.uuid4())),
            tags=tags,
            metadata=passage_metadata,
        )

        # Parse links
        link_pattern: str = r"\[\[(.*?)(?:->(.+?))?\]\]"
        for match in re.finditer(link_pattern, passage.text):
            display: str = match.group(1)
            target: str = match.group(2) or display
            passage.links.append(TwineLink(text=display, target=target))

        passages.append(passage)

    story = TwineStory(
        metadata=twine_metadata,
        passages=passages,
        start_pid=story_data.get("startnode", ""),
    )

    if not story.start_pid and story.get_entries():
        story.start_pid = story.get_entries()[0].pid

    return story


def _write_json(
    story: TwineStory,
    path: Path,
) -> None:
    """Write a Twine story to JSON format.

    Args:
    ----
        story: The story to write
        path: Path to write to
    """
    data: dict[str, Any] = {
        "name": story.metadata.name,
        "ifid": story.metadata.ifid,
        "format": story.metadata.format,
        "format-version": story.metadata.format_version,
        "zoom": story.metadata.zoom,
        "creator": story.metadata.creator,
        "creator-version": story.metadata.creator_version,
        "style": story.metadata.style,
        "script": story.metadata.script,
        "tag-colors": {k: str(v) for k, v in story.metadata.tag_colors.items()},
        "startnode": story.start_pid,
        "passages": [],
    }

    for passage in story.passages:
        # Embed links into text in Twine format: [[text->target]] or [[target]]
        text_with_links = passage.text
        if passage.links:
            link_texts = []
            for link in passage.links:
                if link.target:
                    if link.text and link.text != link.target:
                        link_texts.append(f"[[{link.text}->{link.target}]]")
                    else:
                        link_texts.append(f"[[{link.target}]]")
            if link_texts:
                # Append links to the text (Twine convention is to append links at the end)
                text_with_links = passage.text + (" " if passage.text else "") + " ".join(link_texts)
        
        metadata_dict: PassageMetadataDict = {
            "position": f"{passage.metadata.position.x},{passage.metadata.position.y}",
            "size": f"{passage.metadata.size.x},{passage.metadata.size.y}",
        }
        
        # Include KotOR-specific metadata fields in custom dict
        kotorf_metadata: dict[str, str] = {}
        if passage.metadata.animation_id != 0:
            kotorf_metadata["animation_id"] = str(passage.metadata.animation_id)
        if passage.metadata.camera_angle != 0:
            kotorf_metadata["camera_angle"] = str(passage.metadata.camera_angle)
        # camera_id can be None, 0, or a positive value - only store if not None and not 0
        if passage.metadata.camera_id is not None and passage.metadata.camera_id != 0:
            kotorf_metadata["camera_id"] = str(passage.metadata.camera_id)
        if passage.metadata.fade_type != 0:
            kotorf_metadata["fade_type"] = str(passage.metadata.fade_type)
        if passage.metadata.quest:
            kotorf_metadata["quest"] = passage.metadata.quest
        if passage.metadata.sound:
            kotorf_metadata["sound"] = str(passage.metadata.sound)
        if passage.metadata.vo_resref:
            kotorf_metadata["vo_resref"] = str(passage.metadata.vo_resref)
        if passage.metadata.speaker:
            kotorf_metadata["speaker"] = passage.metadata.speaker
        
        # Merge with existing custom metadata (e.g., language variants)
        if passage.metadata.custom:
            kotorf_metadata.update(passage.metadata.custom)
        
        if kotorf_metadata:
            metadata_dict["custom"] = kotorf_metadata
        
        p_data: PassageDict = {
            "name": passage.name,
            "text": text_with_links,
            "tags": passage.tags,
            "pid": passage.pid,
            "metadata": metadata_dict,
        }
        data["passages"].append(p_data)

    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _write_html(
    story: TwineStory,
    path: Path,
) -> None:
    root: ET.Element = ET.Element("html")
    story_data: ET.Element = ET.SubElement(root, "tw-storydata")

    # Set story metadata
    story_data.set("name", story.metadata.name)
    story_data.set("ifid", story.metadata.ifid)
    story_data.set("format", story.metadata.format)
    story_data.set("format-version", story.metadata.format_version)
    story_data.set("zoom", str(story.metadata.zoom))
    story_data.set("creator", story.metadata.creator)
    story_data.set("creator-version", story.metadata.creator_version)

    # Add style/script
    if story.metadata.style:
        style: ET.Element = ET.SubElement(story_data, "style")
        style.set("role", "stylesheet")
        style.set("id", "twine-user-stylesheet")
        style.set("type", "text/twine-css")
        style.text = story.metadata.style

    if story.metadata.script:
        script: ET.Element = ET.SubElement(story_data, "script")
        script.set("role", "script")
        script.set("id", "twine-user-script")
        script.set("type", "text/twine-javascript")
        script.text = story.metadata.script

    # Add tag colors
    for name, color in story.metadata.tag_colors.items():
        tag: ET.Element = ET.SubElement(story_data, "tw-tag")
        tag.set("name", name)
        tag.set("color", str(color))

    # Add passages
    for passage in story.passages:
        p_data: ET.Element = ET.SubElement(story_data, "tw-passagedata")
        p_data.set("name", passage.name)
        p_data.set("tags", " ".join(passage.tags))
        p_data.set("pid", passage.pid)
        p_data.set(
            "position",
            f"{passage.metadata.position.x},{passage.metadata.position.y}",
        )
        p_data.set(
            "size",
            f"{passage.metadata.size.x},{passage.metadata.size.y}",
        )
        # Store custom metadata (e.g., language variants and KotOR fields) as JSON in data attribute
        custom_payload: dict[str, Any] = dict(passage.metadata.custom)
        if passage.metadata.animation_id != 0:
            custom_payload["animation_id"] = str(passage.metadata.animation_id)
        if passage.metadata.camera_angle != 0:
            custom_payload["camera_angle"] = str(passage.metadata.camera_angle)
        if passage.metadata.camera_id is not None and passage.metadata.camera_id != 0:
            custom_payload["camera_id"] = str(passage.metadata.camera_id)
        if passage.metadata.fade_type != 0:
            custom_payload["fade_type"] = str(passage.metadata.fade_type)
        if passage.metadata.quest:
            custom_payload["quest"] = passage.metadata.quest
        if passage.metadata.sound:
            custom_payload["sound"] = passage.metadata.sound
        if passage.metadata.vo_resref:
            custom_payload["vo_resref"] = passage.metadata.vo_resref
        if passage.metadata.speaker:
            custom_payload["speaker"] = passage.metadata.speaker

        if custom_payload:
            p_data.set("data-custom", json.dumps(custom_payload))
        
        # Embed links into text in Twine format: [[text->target]] or [[target]]
        text_with_links = passage.text
        if passage.links:
            link_texts = []
            for link in passage.links:
                if link.target:
                    if link.text and link.text != link.target:
                        link_texts.append(f"[[{link.text}->{link.target}]]")
                    else:
                        link_texts.append(f"[[{link.target}]]")
            if link_texts:
                # Append links to the text (Twine convention is to append links at the end)
                text_with_links = passage.text + (" " if passage.text else "") + " ".join(link_texts)
        
        p_data.text = text_with_links

    # Mark starting passage if known
    if story.start_pid:
        story_data.set("startnode", story.start_pid)

    tree: ET.ElementTree = ET.ElementTree(root)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def _story_to_dlg(story: TwineStory) -> DLG:
    dlg: DLG = DLG()
    converter: FormatConverter = FormatConverter()

    # Track created nodes
    nodes: dict[str, DLGEntry | DLGReply] = {}

    # First pass: Create nodes
    for passage in story.passages:
        if passage.type == PassageType.ENTRY:
            node = DLGEntry()
            node.speaker = passage.name
        else:
            node = DLGReply()

        # Set text - restore all language/gender combinations from custom metadata
        node.text = LocalizedString(-1)
        node.text.set_data(Language.ENGLISH, Gender.MALE, passage.text)
        
        # Restore additional language variants from custom metadata
        for key, value in passage.metadata.custom.items():
            if key.startswith("text_") and isinstance(value, str):
                # Parse key format: "text_language_gender" (e.g., "text_french_0")
                parts = key.split("_")
                if len(parts) == 3 and parts[0] == "text":
                    try:
                        lang_name = parts[1].upper()
                        gender_val = int(parts[2])
                        # Try to find matching Language enum
                        for lang in Language:
                            if lang.name == lang_name:
                                node.text.set_data(lang, Gender(gender_val), value)
                                break
                    except (ValueError, KeyError):
                        # Skip invalid language/gender combinations
                        continue

        # Restore metadata from passage to node
        converter.restore_kotor_metadata(node, passage)

        nodes[passage.name] = node

    # Second pass: Create links
    for passage in story.passages:
        source: DLGEntry | DLGReply = nodes[passage.name]
        for link in passage.links:
            if link.target not in nodes:
                continue

            target: DLGEntry | DLGReply = nodes[link.target]
            source.links.append(DLGLink(target))  # pyright: ignore[reportArgumentType]

    # Set starting node
    if story.start_passage and story.start_passage.name in nodes:
        dlg.starters.append(DLGLink(nodes[story.start_passage.name]))  # pyright: ignore[reportArgumentType]

    # Store Twine metadata
    converter.store_twine_metadata(story, dlg)

    return dlg


def _dlg_to_story(
    dlg: DLG,
    metadata: dict[str, Any] | None = None,
) -> TwineStory:
    # Create metadata
    meta: dict[str, Any] = metadata or {}
    raw_zoom = meta.get("zoom", 1.0)
    try:
        zoom_val = float(raw_zoom)
    except (TypeError, ValueError):
        zoom_val = 1.0

    tag_colors_raw = meta.get("tag-colors", {})
    tag_colors_val = tag_colors_raw if isinstance(tag_colors_raw, dict) else {}

    story_meta: TwineMetadata = TwineMetadata(
        name=meta.get("name", "Converted Dialog"),
        ifid=meta.get("ifid", str(uuid.uuid4())),
        format=meta.get("format", "Harlowe"),
        format_version=meta.get("format-version", "3.3.7"),
        zoom=zoom_val,
        creator=meta.get("creator", "PyKotor"),
        creator_version=meta.get("creator-version", "1.0.0"),
        style=meta.get("style", ""),
        script=meta.get("script", ""),
        tag_colors=tag_colors_val,
    )

    story: TwineStory = TwineStory(metadata=story_meta, passages=[])
    converter: FormatConverter = FormatConverter()

    # Track processed nodes to handle cycles without recursion depth issues
    processed: set[DLGEntry | DLGReply] = set()
    node_to_passage: dict[DLGEntry | DLGReply, TwinePassage] = {}
    name_registry: dict[str, int] = {}
    node_names: dict[DLGEntry | DLGReply, str] = {}

    def _assign_name(node: DLGEntry | DLGReply) -> str:
        """Assign a unique, stable passage name for a node."""
        if node in node_names:
            return node_names[node]

        base = node.speaker if isinstance(node, DLGEntry) and node.speaker else "Entry" if isinstance(node, DLGEntry) else "Reply"
        count = name_registry.get(base, 0)
        name_registry[base] = count + 1
        name = base if count == 0 else f"{base}_{count}"
        node_names[node] = name
        return name

    def _ensure_passage(node: DLGEntry | DLGReply, pid: str) -> TwinePassage:
        """Create a passage for the node if it does not exist yet."""
        if node in node_to_passage:
            return node_to_passage[node]

        # Get primary text (English, Male) for main passage text
        primary_text = node.text.get(Language.ENGLISH, Gender.MALE) or ""
        
        passage: TwinePassage = TwinePassage(
            name=_assign_name(node),
            text=primary_text,
            type=PassageType.ENTRY if isinstance(node, DLGEntry) else PassageType.REPLY,
            pid=pid,
            tags=["entry"] if isinstance(node, DLGEntry) else ["reply"],
        )
        
        # Store all language/gender combinations in custom metadata
        if node.text.stringref == -1:  # Only store if using custom strings, not TLK reference
            for language, gender, text in node.text:
                if text:  # Only store non-empty strings
                    key = f"text_{language.name.lower()}_{gender.value}"
                    passage.metadata.custom[key] = text
        
        converter.store_kotor_metadata(passage, node)
        node_to_passage[node] = passage
        story.passages.append(passage)
        return passage

    # Process all nodes starting from starters using an explicit stack to avoid recursion limits
    for i, link in enumerate(dlg.starters):
        if link.node is None:
            continue

        stack: list[tuple["DLGEntry | DLGReply", str]] = [(cast("DLGEntry | DLGReply", link.node), str(i + 1))]
        start_passage: TwinePassage | None = None

        while stack:
            current_node, pid = stack.pop()
            passage = _ensure_passage(current_node, pid)

            if current_node not in processed:
                processed.add(current_node)

                for child_link in current_node.links:
                    if child_link.node is None:
                        continue

                    target_node = child_link.node
                    target_pid = str(uuid.uuid4())
                    target_passage = _ensure_passage(cast("DLGEntry | DLGReply", target_node), target_pid)

                    passage.links.append(
                        TwineLink(
                            text="Continue",
                            target=target_passage.name,
                            is_child=child_link.is_child,
                            active_script=str(child_link.active1),
                        ),
                    )

                    if target_node not in processed:
                        stack.append((cast("DLGEntry | DLGReply", target_node), target_pid))

            if start_passage is None:
                start_passage = passage

        if i == 0 and start_passage is not None:
            story.start_pid = start_passage.pid

    # Restore Twine metadata
    converter.restore_twine_metadata(dlg, story)

    return story
