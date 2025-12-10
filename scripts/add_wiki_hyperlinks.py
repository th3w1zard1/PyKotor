#!/usr/bin/env python3
"""
Comprehensive wiki hyperlink addition tool.

This script systematically adds hyperlinks to KotOR terminology across all wiki files.
It is fully idempotent and can be run multiple times safely.

Usage:
    python scripts/add_wiki_hyperlinks.py [OPTIONS]

Examples:
    # Process all files in wiki directory
    python scripts/add_wiki_hyperlinks.py

    # Dry run to see what would change
    python scripts/add_wiki_hyperlinks.py --dry-run

    # Process only specific files
    python scripts/add_wiki_hyperlinks.py --files wiki/2DA-File-Format.md wiki/GFF-File-Format.md

    # Process with verbose output
    python scripts/add_wiki_hyperlinks.py --verbose

    # Skip certain categories
    python scripts/add_wiki_hyperlinks.py --exclude technical-terms --exclude data-types
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from collections.abc import Callable, Sequence
from enum import Enum
from pathlib import Path
from typing import NamedTuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


class LinkCategory(Enum):
    """Categories of link replacements."""

    CROSS_REFERENCES = "cross-references"
    FILE_FORMATS = "file-formats"
    DATA_TYPES = "data-types"
    TECHNICAL_TERMS = "technical-terms"
    GAME_TERMS = "game-terms"
    TEMPLATES = "templates"
    WIKIPEDIA_REPLACEMENTS = "wikipedia-replacements"
    FINAL_LINKS = "final-links"


class ReplacementRule(NamedTuple):
    """A single replacement rule."""

    pattern: str
    replacement: str
    category: LinkCategory
    priority: int = 0  # Higher priority rules are applied first
    context_check: Callable[[str, int, int], bool] | None = None


def _is_in_code(text: str, pos: int) -> bool:
    """Check if position is in code block or inline code."""
    before = text[:pos]
    code_blocks = len(re.findall(r"```", before))
    if code_blocks % 2 == 1:
        return True
    before_ticks = before.count("`")
    return before_ticks % 2 == 1


def is_already_linked(text: str, pos: int) -> bool:
    """Check if position is already in a markdown link."""
    before = text[max(0, pos - 200) : pos]
    after = text[pos : min(len(text), pos + 200)]
    combined = before + after
    for match in re.finditer(r"\[([^\]]*)\]\(([^)]*)\)", combined):
        link_start = match.start() + max(0, pos - 200)
        link_end = match.end() + max(0, pos - 200)
        if link_start <= pos <= link_end:
            return True
    return False


def should_skip_compound_term(text: str, start: int, end: int) -> bool:
    """Check if term is part of a compound term that should be skipped."""
    before = text[max(0, start - 30) : start]
    after = text[end : min(len(text), end + 30)]
    # Skip if part of compound terms like "walkmesh" (don't link "mesh" in "walkmesh")
    compound_patterns = [
        r"\b(walk|room|super|child|parent|root|file|data|format|structure|type|value|field|count|size|index|flag|bit|mask|array|string|vector|matrix|coordinate|position|orientation|rotation|transformation|scale|color|header|offset|pointer)\s+(format|file|data|structure|type|value|field|count|size|index|flag|bit|mask|array|string|vector|matrix|coordinate|position|orientation|rotation|transformation|scale|color|header|offset|pointer)\b",
    ]
    combined = before + after
    return any(re.search(pattern, combined, re.IGNORECASE) for pattern in compound_patterns)


# Define all replacement rules organized by category
REPLACEMENT_RULES: list[ReplacementRule] = []

# Cross-references between related formats
REPLACEMENT_RULES.extend([
    ReplacementRule(r"\bBWM\b(?!\s*\([^)]*\))", "[BWM](BWM-File-Format)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\bWOK\b(?!\s*\([^)]*\))", "[WOK](BWM-File-Format)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\bPWK\b(?!\s*\([^)]*\))", "[PWK](BWM-File-Format)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\bDWK\b(?!\s*\([^)]*\))", "[DWK](BWM-File-Format)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\bwalkmesh\b(?!\s*\([^)]*\))", "[walkmesh](BWM-File-Format)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\bwalkmeshes\b(?!\s*\([^)]*\))", "[walkmeshes](BWM-File-Format)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\bAABB\b(?!\s*\([^)]*\))", "[AABB](BWM-File-Format#aabb-tree)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\bAABB tree\b(?!\s*\([^)]*\))", "[AABB tree](BWM-File-Format#aabb-tree)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\bAABB trees\b(?!\s*\([^)]*\))", "[AABB trees](BWM-File-Format#aabb-tree)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\bMDL\b(?!\s*\([^)]*\))", "[MDL](MDL-MDX-File-Format)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\bMDX\b(?!\s*\([^)]*\))", "[MDX](MDL-MDX-File-Format)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\bMDL file\b(?!\s*\([^)]*\))", "[MDL file](MDL-MDX-File-Format)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\bMDX file\b(?!\s*\([^)]*\))", "[MDX file](MDL-MDX-File-Format)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\bMDL files\b(?!\s*\([^)]*\))", "[MDL files](MDL-MDX-File-Format)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\bMDX files\b(?!\s*\([^)]*\))", "[MDX files](MDL-MDX-File-Format)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\bLYT\b(?!\s*\([^)]*\))", "[LYT](LYT-File-Format)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\bLYT file\b(?!\s*\([^)]*\))", "[LYT file](LYT-File-Format)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\bLYT files\b(?!\s*\([^)]*\))", "[LYT files](LYT-File-Format)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\blayout file\b(?!\s*\([^)]*\))", "[layout file](LYT-File-Format)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\blayout files\b(?!\s*\([^)]*\))", "[layout files](LYT-File-Format)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\broom model\b(?!\s*\([^)]*\))", "[room model](LYT-File-Format#room-definitions)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\broom models\b(?!\s*\([^)]*\))", "[room models](LYT-File-Format#room-definitions)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\bwalkable face\b(?!\s*\([^)]*\))", "[walkable face](BWM-File-Format#faces)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\bwalkable faces\b(?!\s*\([^)]*\))", "[walkable faces](BWM-File-Format#faces)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\badjacency\b(?!\s*\([^)]*\))", "[adjacency](BWM-File-Format#walkable-adjacencies)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\badjacencies\b(?!\s*\([^)]*\))", "[adjacencies](BWM-File-Format#walkable-adjacencies)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\bedge\b(?!\s*\([^)]*\))", "[edge](BWM-File-Format#edges)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\bedges\b(?!\s*\([^)]*\))", "[edges](BWM-File-Format#edges)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\bperimeter\b(?!\s*\([^)]*\))", "[perimeter](BWM-File-Format#perimeters)", LinkCategory.CROSS_REFERENCES, priority=10),
    ReplacementRule(r"\bperimeters\b(?!\s*\([^)]*\))", "[perimeters](BWM-File-Format#perimeters)", LinkCategory.CROSS_REFERENCES, priority=10),
    # Model-related terms (context-sensitive)
    ReplacementRule(r"\bmodel\b(?!\s*\([^)]*\))", "[model](MDL-MDX-File-Format)", LinkCategory.CROSS_REFERENCES, priority=5, context_check=should_skip_compound_term),
    ReplacementRule(r"\bmodels\b(?!\s*\([^)]*\))", "[models](MDL-MDX-File-Format)", LinkCategory.CROSS_REFERENCES, priority=5, context_check=should_skip_compound_term),
    ReplacementRule(r"\bgeometry\b(?!\s*\([^)]*\))", "[geometry](MDL-MDX-File-Format#geometry-header)", LinkCategory.CROSS_REFERENCES, priority=5),
    ReplacementRule(r"\bvertex\b(?!\s*\([^)]*\))", "[vertex](MDL-MDX-File-Format#vertex-structure)", LinkCategory.CROSS_REFERENCES, priority=5),
    ReplacementRule(r"\bvertices\b(?!\s*\([^)]*\))", "[vertices](MDL-MDX-File-Format#vertex-structure)", LinkCategory.CROSS_REFERENCES, priority=5),
    ReplacementRule(r"\bface\b(?!\s*\([^)]*\))", "[face](MDL-MDX-File-Format#face-structure)", LinkCategory.CROSS_REFERENCES, priority=5),
    ReplacementRule(r"\bfaces\b(?!\s*\([^)]*\))", "[faces](MDL-MDX-File-Format#face-structure)", LinkCategory.CROSS_REFERENCES, priority=5),
    ReplacementRule(r"\bmesh\b(?!\s*\([^)]*\))", "[mesh](MDL-MDX-File-Format#trimesh-header)", LinkCategory.CROSS_REFERENCES, priority=5, context_check=should_skip_compound_term),
    ReplacementRule(r"\bmeshes\b(?!\s*\([^)]*\))", "[meshes](MDL-MDX-File-Format#trimesh-header)", LinkCategory.CROSS_REFERENCES, priority=5, context_check=should_skip_compound_term),
    ReplacementRule(r"\bnode\b(?!\s*\([^)]*\))", "[node](MDL-MDX-File-Format#node-structures)", LinkCategory.CROSS_REFERENCES, priority=5),
    ReplacementRule(r"\bnodes\b(?!\s*\([^)]*\))", "[nodes](MDL-MDX-File-Format#node-structures)", LinkCategory.CROSS_REFERENCES, priority=5),
    ReplacementRule(r"\banimation\b(?!\s*\([^)]*\))", "[animation](MDL-MDX-File-Format#animation-header)", LinkCategory.CROSS_REFERENCES, priority=5),
    ReplacementRule(r"\banimations\b(?!\s*\([^)]*\))", "[animations](MDL-MDX-File-Format#animation-header)", LinkCategory.CROSS_REFERENCES, priority=5),
    ReplacementRule(r"\bcontroller\b(?!\s*\([^)]*\))", "[controller](MDL-MDX-File-Format#controllers)", LinkCategory.CROSS_REFERENCES, priority=5),
    ReplacementRule(r"\bcontrollers\b(?!\s*\([^)]*\))", "[controllers](MDL-MDX-File-Format#controllers)", LinkCategory.CROSS_REFERENCES, priority=5),
    ReplacementRule(r"\bkeyframe\b(?!\s*\([^)]*\))", "[keyframe](MDL-MDX-File-Format#controller-structure)", LinkCategory.CROSS_REFERENCES, priority=5),
    ReplacementRule(r"\bkeyframes\b(?!\s*\([^)]*\))", "[keyframes](MDL-MDX-File-Format#controller-structure)", LinkCategory.CROSS_REFERENCES, priority=5),
    ReplacementRule(r"\bmaterial\b(?!\s*\([^)]*\))", "[material](MDL-MDX-File-Format#trimesh-header)", LinkCategory.CROSS_REFERENCES, priority=5),
    ReplacementRule(r"\bmaterials\b(?!\s*\([^)]*\))", "[materials](MDL-MDX-File-Format#trimesh-header)", LinkCategory.CROSS_REFERENCES, priority=5),
    ReplacementRule(r"\btexture\b(?!\s*\([^)]*\))", "[texture](TPC-File-Format)", LinkCategory.CROSS_REFERENCES, priority=5),
    ReplacementRule(r"\btextures\b(?!\s*\([^)]*\))", "[textures](TPC-File-Format)", LinkCategory.CROSS_REFERENCES, priority=5),
])

# File format abbreviations
REPLACEMENT_RULES.extend([
    ReplacementRule(r"\bGFF\b(?!\s*\([^)]*\))", "[GFF](GFF-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bARE\b(?!\s*\([^)]*\))", "[ARE](GFF-File-Format#are-area)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bIFO\b(?!\s*\([^)]*\))", "[IFO](GFF-File-Format#ifo-module-info)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bGIT\b(?!\s*\([^)]*\))", "[GIT](GFF-File-Format#git-game-instance-template)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bUTC\b(?!\s*\([^)]*\))", "[UTC](GFF-File-Format#utc-creature)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bUTI\b(?!\s*\([^)]*\))", "[UTI](GFF-File-Format#uti-item)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bUTP\b(?!\s*\([^)]*\))", "[UTP](GFF-File-Format#utp-placeable)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bUTD\b(?!\s*\([^)]*\))", "[UTD](GFF-File-Format#utd-door)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bUTE\b(?!\s*\([^)]*\))", "[UTE](GFF-File-Format#ute-encounter)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bUTM\b(?!\s*\([^)]*\))", "[UTM](GFF-File-Format#utm-merchant)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bUTT\b(?!\s*\([^)]*\))", "[UTT](GFF-File-Format#utt-trigger)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bUTW\b(?!\s*\([^)]*\))", "[UTW](GFF-File-Format#utw-waypoint)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bUTS\b(?!\s*\([^)]*\))", "[UTS](GFF-File-Format#uts-sound)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bDLG\b(?!\s*\([^)]*\))", "[DLG](GFF-File-Format#dlg-dialogue)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bJRL\b(?!\s*\([^)]*\))", "[JRL](GFF-File-Format#jrl-journal)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bPTH\b(?!\s*\([^)]*\))", "[PTH](GFF-File-Format#pth-path)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bGUI\b(?!\s*\([^)]*\))", "[GUI](GFF-File-Format#gui-graphical-user-interface)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\b2DA\b(?!\s*\([^)]*\))", "[2DA](2DA-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bTLK\b(?!\s*\([^)]*\))", "[TLK](TLK-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bTPC\b(?!\s*\([^)]*\))", "[TPC](TPC-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bTXI\b(?!\s*\([^)]*\))", "[TXI](TXI-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bNCS\b(?!\s*\([^)]*\))", "[NCS](NCS-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bNSS\b(?!\s*\([^)]*\))", "[NSS](NSS-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bERF\b(?!\s*\([^)]*\))", "[ERF](ERF-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bKEY\b(?!\s*\([^)]*\))", "[KEY](KEY-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bBIF\b(?!\s*\([^)]*\))", "[BIF](BIF-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bSSF\b(?!\s*\([^)]*\))", "[SSF](SSF-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bPLT\b(?!\s*\([^)]*\))", "[PLT](PLT-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bVIS\b(?!\s*\([^)]*\))", "[VIS](VIS-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bLIP\b(?!\s*\([^)]*\))", "[LIP](LIP-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bWAV\b(?!\s*\([^)]*\))", "[WAV](WAV-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
])

# Data types
REPLACEMENT_RULES.extend([
    ReplacementRule(r"\bResRef\b(?!\s*\([^)]*\))", "[ResRef](GFF-File-Format#resref)", LinkCategory.DATA_TYPES, priority=10),
    ReplacementRule(r"\bStrRef\b(?!\s*\([^)]*\))", "[StrRef](TLK-File-Format#string-references-strref)", LinkCategory.DATA_TYPES, priority=10),
    ReplacementRule(r"\bCExoString\b(?!\s*\([^)]*\))", "[CExoString](GFF-File-Format#cexostring)", LinkCategory.DATA_TYPES, priority=10),
    ReplacementRule(r"\bCExoLocString\b(?!\s*\([^)]*\))", "[CExoLocString](GFF-File-Format#localizedstring)", LinkCategory.DATA_TYPES, priority=10),
    ReplacementRule(r"\buint32\b(?!\s*\([^)]*\))", "[uint32](GFF-File-Format#dword)", LinkCategory.DATA_TYPES, priority=5),
    ReplacementRule(r"\buint16\b(?!\s*\([^)]*\))", "[uint16](GFF-File-Format#word)", LinkCategory.DATA_TYPES, priority=5),
    ReplacementRule(r"\buint8\b(?!\s*\([^)]*\))", "[uint8](GFF-File-Format#byte)", LinkCategory.DATA_TYPES, priority=5),
    ReplacementRule(r"\bint32\b(?!\s*\([^)]*\))", "[int32](GFF-File-Format#int)", LinkCategory.DATA_TYPES, priority=5),
    ReplacementRule(r"\bint16\b(?!\s*\([^)]*\))", "[int16](GFF-File-Format#short)", LinkCategory.DATA_TYPES, priority=5),
    ReplacementRule(r"\bfloat32\b(?!\s*\([^)]*\))", "[float32](GFF-File-Format#float)", LinkCategory.DATA_TYPES, priority=5),
    ReplacementRule(r"\bfloat\b(?!\s*\([^)]*\))", "[float](GFF-File-Format#float)", LinkCategory.DATA_TYPES, priority=5),
    ReplacementRule(r"\bdouble\b(?!\s*\([^)]*\))", "[double](GFF-File-Format#double)", LinkCategory.DATA_TYPES, priority=5),
    ReplacementRule(r"\bchar\b(?!\s*\([^)]*\))", "[char](GFF-File-Format#char)", LinkCategory.DATA_TYPES, priority=5),
    ReplacementRule(r"\bbyte\b(?!\s*\([^)]*\))", "[byte](GFF-File-Format#byte)", LinkCategory.DATA_TYPES, priority=5),
    ReplacementRule(r"\bByte\b(?!\s*\([^)]*\))", "[Byte](GFF-File-Format#byte)", LinkCategory.DATA_TYPES, priority=5),
])

# Technical terms
REPLACEMENT_RULES.extend([
    ReplacementRule(r"\bnull byte\b(?!\s*\([^)]*\))", "[null byte](https://en.cppreference.com/w/c/string/byte)", LinkCategory.TECHNICAL_TERMS, priority=10),
    ReplacementRule(r"\bnull terminator\b(?!\s*\([^)]*\))", "[null terminator](https://en.cppreference.com/w/c/string/byte)", LinkCategory.TECHNICAL_TERMS, priority=10),
    ReplacementRule(r"\bnull-terminated string\b(?!\s*\([^)]*\))", "[null-terminated string](https://en.cppreference.com/w/c/string/byte)", LinkCategory.TECHNICAL_TERMS, priority=10),
    ReplacementRule(r"\bnull-terminated\b(?!\s*\([^)]*\))", "[null-terminated](https://en.cppreference.com/w/c/string/byte)", LinkCategory.TECHNICAL_TERMS, priority=10),
    # REMOVED: Overly broad rules for common words that match in inappropriate contexts
    # These were causing false positives (e.g., "type", "value", "field", "format", "file", "data", 
    # "header", "offset", "pointer", "count", "size", "index", "flag", "bit", "mask", "array", 
    # "string", "vector", "matrix", "coordinate", "position", "orientation", "rotation", 
    # "transformation", "scale", "color", "structure", etc.)
    # Only link these terms when they appear in specific technical contexts or compound terms
])

# Game-specific terms
REPLACEMENT_RULES.extend([
    ReplacementRule(r"\bcreature template\b(?!\s*\([^)]*\))", "[creature template](GFF-File-Format#utc-creature)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bcreature templates\b(?!\s*\([^)]*\))", "[creature templates](GFF-File-Format#utc-creature)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bitem template\b(?!\s*\([^)]*\))", "[item template](GFF-File-Format#uti-item)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bitem templates\b(?!\s*\([^)]*\))", "[item templates](GFF-File-Format#uti-item)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bplaceable template\b(?!\s*\([^)]*\))", "[placeable template](GFF-File-Format#utp-placeable)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bplaceable templates\b(?!\s*\([^)]*\))", "[placeable templates](GFF-File-Format#utp-placeable)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bdialogue tree\b(?!\s*\([^)]*\))", "[dialogue tree](GFF-File-Format#dlg-dialogue)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bdialogue trees\b(?!\s*\([^)]*\))", "[dialogue trees](GFF-File-Format#dlg-dialogue)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bjournal entry\b(?!\s*\([^)]*\))", "[journal entry](GFF-File-Format#jrl-journal)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bjournal entries\b(?!\s*\([^)]*\))", "[journal entries](GFF-File-Format#jrl-journal)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\barea property\b(?!\s*\([^)]*\))", "[area property](GFF-File-Format#are-area)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\barea properties\b(?!\s*\([^)]*\))", "[area properties](GFF-File-Format#are-area)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bmodule info\b(?!\s*\([^)]*\))", "[module info](GFF-File-Format#ifo-module-info)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bdoor template\b(?!\s*\([^)]*\))", "[door template](GFF-File-Format#utd-door)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bdoor templates\b(?!\s*\([^)]*\))", "[door templates](GFF-File-Format#utd-door)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bencounter template\b(?!\s*\([^)]*\))", "[encounter template](GFF-File-Format#ute-encounter)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bencounter templates\b(?!\s*\([^)]*\))", "[encounter templates](GFF-File-Format#ute-encounter)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bmerchant template\b(?!\s*\([^)]*\))", "[merchant template](GFF-File-Format#utm-merchant)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bmerchant templates\b(?!\s*\([^)]*\))", "[merchant templates](GFF-File-Format#utm-merchant)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\btrigger template\b(?!\s*\([^)]*\))", "[trigger template](GFF-File-Format#utt-trigger)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\btrigger templates\b(?!\s*\([^)]*\))", "[trigger templates](GFF-File-Format#utt-trigger)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bwaypoint template\b(?!\s*\([^)]*\))", "[waypoint template](GFF-File-Format#utw-waypoint)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bwaypoint templates\b(?!\s*\([^)]*\))", "[waypoint templates](GFF-File-Format#utw-waypoint)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bsound object template\b(?!\s*\([^)]*\))", "[sound object template](GFF-File-Format#uts-sound)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bsound object templates\b(?!\s*\([^)]*\))", "[sound object templates](GFF-File-Format#uts-sound)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bgame instance template\b(?!\s*\([^)]*\))", "[game instance template](GFF-File-Format#git-game-instance-template)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bgame instance templates\b(?!\s*\([^)]*\))", "[game instance templates](GFF-File-Format#git-game-instance-template)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bTPC texture file\b(?!\s*\([^)]*\))", "[TPC texture file](TPC-File-Format)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bTPC texture files\b(?!\s*\([^)]*\))", "[TPC texture files](TPC-File-Format)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bTXI texture info file\b(?!\s*\([^)]*\))", "[TXI texture info file](TXI-File-Format)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bTXI texture info files\b(?!\s*\([^)]*\))", "[TXI texture info files](TXI-File-Format)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bGFF ARE file\b(?!\s*\([^)]*\))", "[GFF ARE file](GFF-File-Format#are-area)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bGFF ARE files\b(?!\s*\([^)]*\))", "[GFF ARE files](GFF-File-Format#are-area)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bsound set file\b(?!\s*\([^)]*\))", "[sound set file](SSF-File-Format)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bsound set files\b(?!\s*\([^)]*\))", "[sound set files](SSF-File-Format)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bwalkable surfaces?\b(?!\s*\([^)]*\))", "[walkable surfaces](BWM-File-Format)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\btexture files?\b(?!\s*\([^)]*\))", "[texture files](TPC-File-Format)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\btexture info files?\b(?!\s*\([^)]*\))", "[texture info files](TXI-File-Format)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bvoice-over files?\b(?!\s*\([^)]*\))", "[voice-over files](WAV-File-Format)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\blip sync files?\b(?!\s*\([^)]*\))", "[lip sync files](LIP-File-Format)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bmodule archives?\b(?!\s*\([^)]*\))", "[module archives](ERF-File-Format)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bsave game archives?\b(?!\s*\([^)]*\))", "[save game archives](ERF-File-Format)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bBIF archives?\b(?!\s*\([^)]*\))", "[BIF archives](BIF-File-Format)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bvisibility files?\b(?!\s*\([^)]*\))", "[visibility files](VIS-File-Format)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bVIS files?\b(?!\s*\([^)]*\))", "[VIS files](VIS-File-Format)", LinkCategory.GAME_TERMS, priority=10),
])

# File format file references
REPLACEMENT_RULES.extend([
    ReplacementRule(r"\b2DA file\b(?!\s*\([^)]*\))", "[2DA file](2DA-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\b2DA files\b(?!\s*\([^)]*\))", "[2DA files](2DA-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bGFF file\b(?!\s*\([^)]*\))", "[GFF file](GFF-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bGFF files\b(?!\s*\([^)]*\))", "[GFF files](GFF-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bTLK file\b(?!\s*\([^)]*\))", "[TLK file](TLK-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bTLK files\b(?!\s*\([^)]*\))", "[TLK files](TLK-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bBWM file\b(?!\s*\([^)]*\))", "[BWM file](BWM-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bBWM files\b(?!\s*\([^)]*\))", "[BWM files](BWM-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bWOK file\b(?!\s*\([^)]*\))", "[WOK file](BWM-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bWOK files\b(?!\s*\([^)]*\))", "[WOK files](BWM-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bTPC file\b(?!\s*\([^)]*\))", "[TPC file](TPC-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bTPC files\b(?!\s*\([^)]*\))", "[TPC files](TPC-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bTXI file\b(?!\s*\([^)]*\))", "[TXI file](TXI-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bTXI files\b(?!\s*\([^)]*\))", "[TXI files](TXI-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bWAV file\b(?!\s*\([^)]*\))", "[WAV file](WAV-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bWAV files\b(?!\s*\([^)]*\))", "[WAV files](WAV-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bLIP file\b(?!\s*\([^)]*\))", "[LIP file](LIP-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bLIP files\b(?!\s*\([^)]*\))", "[LIP files](LIP-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bNCS file\b(?!\s*\([^)]*\))", "[NCS file](NCS-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bNCS files\b(?!\s*\([^)]*\))", "[NCS files](NCS-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bNSS file\b(?!\s*\([^)]*\))", "[NSS file](NSS-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bNSS files\b(?!\s*\([^)]*\))", "[NSS files](NSS-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bERF file\b(?!\s*\([^)]*\))", "[ERF file](ERF-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bERF files\b(?!\s*\([^)]*\))", "[ERF files](ERF-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bKEY file\b(?!\s*\([^)]*\))", "[KEY file](KEY-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bKEY files\b(?!\s*\([^)]*\))", "[KEY files](KEY-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bBIF file\b(?!\s*\([^)]*\))", "[BIF file](BIF-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bBIF files\b(?!\s*\([^)]*\))", "[BIF files](BIF-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bSSF file\b(?!\s*\([^)]*\))", "[SSF file](SSF-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bSSF files\b(?!\s*\([^)]*\))", "[SSF files](SSF-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bPLT file\b(?!\s*\([^)]*\))", "[PLT file](PLT-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bPLT files\b(?!\s*\([^)]*\))", "[PLT files](PLT-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bLYT file\b(?!\s*\([^)]*\))", "[LYT file](LYT-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bLYT files\b(?!\s*\([^)]*\))", "[LYT files](LYT-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bVIS file\b(?!\s*\([^)]*\))", "[VIS file](VIS-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bVIS files\b(?!\s*\([^)]*\))", "[VIS files](VIS-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bLTR file\b(?!\s*\([^)]*\))", "[LTR file](LTR-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"\bLTR files\b(?!\s*\([^)]*\))", "[LTR files](LTR-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"`dialog\.tlk`", "[`dialog.tlk`](TLK-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
    ReplacementRule(r"`chitin\.key`", "[`chitin.key`](KEY-File-Format)", LinkCategory.FILE_FORMATS, priority=10),
])

# Wikipedia replacements (must come before other rules that might create Wikipedia links)
REPLACEMENT_RULES.extend([
    ReplacementRule(r"\[null byte\]\(https://en\.wikipedia\.org/wiki/Null-terminated_string\)", "[null byte](https://en.cppreference.com/w/c/string/byte)", LinkCategory.WIKIPEDIA_REPLACEMENTS, priority=20),
    ReplacementRule(r"\[null terminator\]\(https://en\.wikipedia\.org/wiki/Null-terminated_string\)", "[null terminator](https://en.cppreference.com/w/c/string/byte)", LinkCategory.WIKIPEDIA_REPLACEMENTS, priority=20),
    ReplacementRule(r"\[null-terminated string\]\(https://en\.wikipedia\.org/wiki/Null-terminated_string\)", "[null-terminated string](https://en.cppreference.com/w/c/string/byte)", LinkCategory.WIKIPEDIA_REPLACEMENTS, priority=20),
    ReplacementRule(r"\[null-terminated\]\(https://en\.wikipedia\.org/wiki/Null-terminated_string\)", "[null-terminated](https://en.cppreference.com/w/c/string/byte)", LinkCategory.WIKIPEDIA_REPLACEMENTS, priority=20),
    # Replace "Archive file" Wikipedia link - keep as is (no better source for general concept)
    # Replace "Binary file" Wikipedia link - keep as is (no better source for general concept)
    # Replace "Modular programming" Wikipedia link - keep as is (no better source for general concept)
    # Endianness, IEEE 754, ASCII are fundamental CS concepts - Wikipedia is acceptable
])

# Final comprehensive links
REPLACEMENT_RULES.extend([
    ReplacementRule(r"\brow_count\b(?!\s*\([^)]*\))", "[row_count](2DA-File-Format#row-labels)", LinkCategory.FINAL_LINKS, priority=5),
    ReplacementRule(r"\bcolumn_count\b(?!\s*\([^)]*\))", "[column_count](2DA-File-Format#column-headers)", LinkCategory.FINAL_LINKS, priority=5),
    ReplacementRule(r"\bcell_data\b(?!\s*\([^)]*\))", "[cell_data](2DA-File-Format#cell-data-string-table)", LinkCategory.FINAL_LINKS, priority=5),
    ReplacementRule(r"\bcell_data_size\b(?!\s*\([^)]*\))", "[cell_data_size](2DA-File-Format#cell-data-string-table)", LinkCategory.FINAL_LINKS, priority=5),
    ReplacementRule(r"\btab character\b(?!\s*\([^)]*\))", "[tab character](2DA-File-Format#column-headers)", LinkCategory.FINAL_LINKS, priority=5),
    ReplacementRule(r"\btab-terminated\b(?!\s*\([^)]*\))", "[tab-terminated](2DA-File-Format#column-headers)", LinkCategory.FINAL_LINKS, priority=5),
    ReplacementRule(r"\brow-major order\b(?!\s*\([^)]*\))", "[row-major order](2DA-File-Format#cell-offsets)", LinkCategory.FINAL_LINKS, priority=5),
    ReplacementRule(r"\bcolumn-major order\b(?!\s*\([^)]*\))", "[column-major order](2DA-File-Format#cell-offsets)", LinkCategory.FINAL_LINKS, priority=5),
    ReplacementRule(r"\blittle-endian\b(?!\s*\([^)]*\))", "[little-endian](https://en.wikipedia.org/wiki/Endianness)", LinkCategory.FINAL_LINKS, priority=5),
    ReplacementRule(r"\bbig-endian\b(?!\s*\([^)]*\))", "[big-endian](https://en.wikipedia.org/wiki/Endianness)", LinkCategory.FINAL_LINKS, priority=5),
    ReplacementRule(r"\bdialog\.tlk\b(?!\s*\([^)]*\))", "[dialog.tlk](TLK-File-Format)", LinkCategory.FINAL_LINKS, priority=5),
    ReplacementRule(r"\bchitin\.key\b(?!\s*\([^)]*\))", "[chitin.key](KEY-File-Format)", LinkCategory.FINAL_LINKS, priority=5),
    ReplacementRule(r"\bTalkTable\b(?!\s*\([^)]*\))", "[TalkTable](TLK-File-Format)", LinkCategory.FINAL_LINKS, priority=5),
    ReplacementRule(r"\bTalk Table\b(?!\s*\([^)]*\))", "[Talk Table](TLK-File-Format)", LinkCategory.FINAL_LINKS, priority=5),
    ReplacementRule(r"\bTwo-Dimensional Array\b(?!\s*\([^)]*\))", "[Two-Dimensional Array](2DA-File-Format)", LinkCategory.FINAL_LINKS, priority=5),
    ReplacementRule(r"\bstring reference\b(?!\s*\([^)]*\))", "[string reference](TLK-File-Format#string-references-strref)", LinkCategory.FINAL_LINKS, priority=5),
    ReplacementRule(r"\bstring references\b(?!\s*\([^)]*\))", "[string references](TLK-File-Format#string-references-strref)", LinkCategory.FINAL_LINKS, priority=5),
    ReplacementRule(r"\bresource reference\b(?!\s*\([^)]*\))", "[resource reference](GFF-File-Format#resref)", LinkCategory.FINAL_LINKS, priority=5),
    ReplacementRule(r"\bresource references\b(?!\s*\([^)]*\))", "[resource references](GFF-File-Format#resref)", LinkCategory.FINAL_LINKS, priority=5),
])

# Additional common terms that should be linked
REPLACEMENT_RULES.extend([
    ReplacementRule(r"\barchive containers?\b(?!\s*\([^)]*\))", "[archive containers](ERF-File-Format)", LinkCategory.GAME_TERMS, priority=8),
    ReplacementRule(r"\bself-contained archives?\b(?!\s*\([^)]*\))", "[self-contained archives](ERF-File-Format)", LinkCategory.GAME_TERMS, priority=8),
    ReplacementRule(r"\bmodule archives?\b(?!\s*\([^)]*\))", "[module archives](ERF-File-Format)", LinkCategory.GAME_TERMS, priority=8),
    ReplacementRule(r"\bsave game archives?\b(?!\s*\([^)]*\))", "[save game archives](ERF-File-Format)", LinkCategory.GAME_TERMS, priority=8),
    # Compression and encoding terms
    ReplacementRule(r"\bcompression\b(?!\s*\([^)]*\))", "[compression](BIF-File-Format#bzf-compression)", LinkCategory.TECHNICAL_TERMS, priority=5),
    ReplacementRule(r"\bbounding box\b(?!\s*\([^)]*\))", "[bounding box](MDL-MDX-File-Format#model-header)", LinkCategory.TECHNICAL_TERMS, priority=5),
    ReplacementRule(r"\bbounding boxes\b(?!\s*\([^)]*\))", "[bounding boxes](MDL-MDX-File-Format#model-header)", LinkCategory.TECHNICAL_TERMS, priority=5),
    ReplacementRule(r"\bocclusion culling\b(?!\s*\([^)]*\))", "[occlusion culling](VIS-File-Format)", LinkCategory.TECHNICAL_TERMS, priority=5),
    # Keep Wikipedia links for fundamental CS concepts (endianness, ASCII, IEEE 754, binary file, modular programming)
    # These are well-established concepts where Wikipedia is the best free online source
])

# 2DA file references
REPLACEMENT_RULES.extend([
    ReplacementRule(r"\bappearance\.2da\b", "[appearance.2da](2DA-appearance)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bbaseitems\.2da\b", "[baseitems.2da](2DA-baseitems)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bclasses\.2da\b", "[classes.2da](2DA-classes)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bfeat\.2da\b", "[feat.2da](2DA-feat)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bskills\.2da\b", "[skills.2da](2DA-skills)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bspells\.2da\b", "[spells.2da](2DA-spells)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bplaceables\.2da\b", "[placeables.2da](2DA-placeables)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bportraits\.2da\b", "[portraits.2da](2DA-portraits)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bracialtypes\.2da\b", "[racialtypes.2da](2DA-racialtypes)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bitempropdef\.2da\b", "[itempropdef.2da](2DA-itempropdef)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\btraps\.2da\b", "[traps.2da](2DA-traps)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bsoundset\.2da\b", "[soundset.2da](2DA-soundset)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bvisualeffects\.2da\b", "[visualeffects.2da](2DA-visualeffects)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bgenericdoors\.2da\b", "[genericdoors.2da](2DA-genericdoors)", LinkCategory.GAME_TERMS, priority=10),
    ReplacementRule(r"\bdoortypes\.2da\b", "[doortypes.2da](2DA-doortypes)", LinkCategory.GAME_TERMS, priority=10),
])


def should_skip_file(filename: str, skip_patterns: Sequence[str] | None = None) -> bool:
    """Check if file should be skipped."""
    if skip_patterns is None:
        skip_patterns = ["Bioware-Aurora-", "fix_ini_comments.py"]
    return any(pattern in filename for pattern in skip_patterns)


def process_file(
    filepath: Path,
    rules: Sequence[ReplacementRule],
    dry_run: bool = False,
    verbose: bool = False,
) -> tuple[int, int]:
    """
    Process a single file.

    Returns:
        Tuple of (changes_made, replacements_count)
    """
    try:
        content = filepath.read_text(encoding="utf-8")
        original = content
        changes = 0
        replacements = 0

        # Sort rules by priority (higher first), then apply
        sorted_rules = sorted(rules, key=lambda r: r.priority, reverse=True)

        for rule in sorted_rules:
            matches = list(re.finditer(rule.pattern, content, re.IGNORECASE))
            for match in reversed(matches):
                start, end = match.span()

                # Skip if in code block
                if _is_in_code(content, start):
                    continue

                # Skip if already linked
                if is_already_linked(content, start):
                    continue

                # Skip if part of file extension
                before = content[max(0, start - 10) : start]
                if "." in before and not before.strip().endswith(" "):
                    continue

                # Skip if in inline code
                if "`" in before or "`" in content[end : min(len(content), end + 10)]:
                    continue

                # Apply context check if provided
                if rule.context_check and rule.context_check(content, start, end):
                    continue

                # Replace
                content = content[:start] + rule.replacement + content[end:]
                changes += 1
                replacements += 1

                if verbose:
                    logger.debug(f"  Replaced '{match.group()}' with '{rule.replacement}' at position {start}")

        if content != original:
            if not dry_run:
                filepath.write_text(content, encoding="utf-8")
            return (1, replacements)
        return (0, 0)
    except Exception as e:
        logger.error(f"Error processing {filepath.name}: {e}", exc_info=verbose)
        return (0, 0)


def get_files_to_process(
    wiki_dir: Path,
    file_patterns: Sequence[str] | None = None,
    skip_patterns: Sequence[str] | None = None,
) -> list[Path]:
    """Get list of files to process."""
    if file_patterns:
        files = []
        for pattern in file_patterns:
            path = Path(pattern)
            if path.is_absolute() or "/" in pattern or "\\" in pattern:
                # Absolute path or relative path with directory
                if path.exists() and path.suffix == ".md":
                    files.append(path)
            else:
                # Just filename, search in wiki_dir
                found = list(wiki_dir.glob(pattern))
                files.extend(found)
        return sorted(set(files))

    # Process all .md files in wiki_dir
    all_files = sorted(wiki_dir.glob("*.md"))
    return [f for f in all_files if not should_skip_file(f.name, skip_patterns)]


def filter_rules_by_category(
    rules: Sequence[ReplacementRule],
    include_categories: Sequence[LinkCategory] | None = None,
    exclude_categories: Sequence[LinkCategory] | None = None,
) -> list[ReplacementRule]:
    """Filter rules by category."""
    filtered = list(rules)

    if include_categories:
        filtered = [r for r in filtered if r.category in include_categories]

    if exclude_categories:
        filtered = [r for r in filtered if r.category not in exclude_categories]

    return filtered


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Add comprehensive hyperlinks to KotOR terminology across wiki files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--wiki-dir",
        type=Path,
        default=Path("wiki"),
        help="Directory containing wiki markdown files (default: wiki)",
    )
    parser.add_argument(
        "--files",
        nargs="+",
        help="Specific files to process (default: all .md files in wiki-dir)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress non-error output",
    )
    parser.add_argument(
        "--include",
        nargs="+",
        choices=[cat.value for cat in LinkCategory],
        help="Only process these categories of links",
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        choices=[cat.value for cat in LinkCategory],
        help="Skip these categories of links",
    )
    parser.add_argument(
        "--skip-patterns",
        nargs="+",
        default=["Bioware-Aurora-", "fix_ini_comments.py"],
        help="Filename patterns to skip (default: Bioware-Aurora-, fix_ini_comments.py)",
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
    elif args.quiet:
        logger.setLevel(logging.ERROR)

    wiki_dir = args.wiki_dir.resolve()
    if not wiki_dir.exists():
        logger.error(f"Wiki directory does not exist: {wiki_dir}")
        return 1

    if not wiki_dir.is_dir():
        logger.error(f"Wiki path is not a directory: {wiki_dir}")
        return 1

    # Filter rules by category
    include_categories = (
        [LinkCategory(cat) for cat in args.include] if args.include else None
    )
    exclude_categories = (
        [LinkCategory(cat) for cat in args.exclude] if args.exclude else None
    )
    rules = filter_rules_by_category(
        REPLACEMENT_RULES, include_categories, exclude_categories
    )

    if not rules:
        logger.warning("No rules to apply after filtering")
        return 0

    # Get files to process
    files_to_process = get_files_to_process(
        wiki_dir, args.files, args.skip_patterns
    )

    if not files_to_process:
        logger.warning("No files to process")
        return 0

    if args.verbose:
        logger.info(f"Processing {len(files_to_process)} file(s) with {len(rules)} rule(s)")

    if args.dry_run:
        logger.info("DRY RUN MODE - No files will be modified")

    # Process files
    total_changes = 0
    total_replacements = 0
    processed_files = 0

    for md_file in files_to_process:
        if should_skip_file(md_file.name, args.skip_patterns):
            continue

        if args.verbose:
            logger.debug(f"Processing {md_file.name}...")

        files_changed, replacements = process_file(
            md_file, rules, dry_run=args.dry_run, verbose=args.verbose
        )

        if files_changed > 0:
            if not args.quiet:
                logger.info(f"Processed {md_file.name}: {replacements} replacements")
            processed_files += 1
            total_changes += files_changed
            total_replacements += replacements

    if not args.quiet:
        logger.info(
            f"\nTotal: {processed_files} file(s) processed, {total_replacements} replacement(s) made"
        )

    if args.dry_run and total_replacements > 0:
        logger.info(f"\nDry run complete. {total_replacements} replacement(s) would be made.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
