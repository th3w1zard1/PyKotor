"""Tests for markdown documentation validation.

Validates:
- markdownlint compliance
- All link references are valid and clickable
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent
WIKI_DIR = REPO_ROOT / "wiki"
MARKDOWNLINT_CONFIG = REPO_ROOT / ".markdownlint-cli2.jsonc"


def extract_links(content: str, file_path: Path) -> list[tuple[str, str, int]]:
    """Extract all markdown links from content.
    
    Returns: List of (link_text, link_url, line_number) tuples
    """
    links = []
    # Pattern matches [text](url) and [text](url "title")
    pattern = r'\[([^\]]+)\]\(([^\)"]+)(?:\s+"[^"]+")?\)'
    
    for line_num, line in enumerate(content.splitlines(), 1):
        for match in re.finditer(pattern, line):
            link_text = match.group(1)
            link_url = match.group(2)
            links.append((link_text, link_url, line_num))
    
    return links


def normalize_anchor(text: str) -> str:
    """Normalize anchor text to match GitHub's anchor generation."""
    # Convert to lowercase
    text = text.lower()
    # Replace spaces and special chars with hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    # Remove leading/trailing hyphens
    text = text.strip('-')
    return text


def extract_headings(content: str) -> dict[str, int]:
    """Extract all headings and their line numbers.
    
    Returns: Dict mapping normalized anchor to line number
    """
    headings = {}
    for line_num, line in enumerate(content.splitlines(), 1):
        # Match HTML anchors: <a id="anchor"></a>
        html_anchor_match = re.search(r'<a\s+id="([^"]+)"', line)
        if html_anchor_match:
            anchor = html_anchor_match.group(1)
            headings[anchor] = line_num
        
        # Match markdown headings: # Heading, ## Heading, etc.
        match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
        if match:
            heading_text = match.group(2).strip()
            # Remove any inline markdown formatting
            heading_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', heading_text)
            heading_text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', heading_text)
            heading_text = re.sub(r'\*([^\*]+)\*', r'\1', heading_text)
            heading_text = re.sub(r'`([^`]+)`', r'\1', heading_text)
            anchor = normalize_anchor(heading_text)
            headings[anchor] = line_num
    return headings


def validate_link(link_url: str, source_file: Path, all_files: dict[str, Path], all_headings: dict[str, dict[str, int]]) -> tuple[bool, str]:
    """Validate a single link.
    
    Returns: (is_valid, error_message)
    """
    # Skip external URLs
    parsed = urlparse(link_url)
    if parsed.scheme in ('http', 'https', 'mailto'):
        return True, ""
    
    # Split into file and anchor parts
    if '#' in link_url:
        file_part, anchor_part = link_url.split('#', 1)
    else:
        file_part = link_url
        anchor_part = None
    
    # Resolve file path
    if file_part:
        # Handle relative paths
        if file_part.startswith('./'):
            file_part = file_part[2:]
        
        target_file = None
        # Try as-is first (already in wiki directory)
        if (WIKI_DIR / file_part).exists():
            target_file = WIKI_DIR / file_part
        # Try with .md extension
        elif (WIKI_DIR / f"{file_part}.md").exists():
            target_file = WIKI_DIR / f"{file_part}.md"
        # Try relative to source file
        elif (source_file.parent / file_part).exists():
            target_file = source_file.parent / file_part
        elif (source_file.parent / f"{file_part}.md").exists():
            target_file = source_file.parent / f"{file_part}.md"
        
        if not target_file:
            return False, f"Target file not found: {file_part}"
        
        file_key = target_file.name
    else:
        # Same-file anchor reference
        file_key = source_file.name
        target_file = source_file
    
    # Validate anchor if present
    if anchor_part:
        normalized_anchor = normalize_anchor(anchor_part)
        if file_key in all_headings:
            if normalized_anchor not in all_headings[file_key]:
                # Try to find similar anchors
                similar = [h for h in all_headings[file_key].keys() if normalized_anchor in h or h in normalized_anchor]
                if similar:
                    return False, f"Anchor not found (similar: {similar[0]})"
                return False, f"Anchor not found: #{anchor_part}"
    
    return True, ""


@pytest.fixture(scope="module")
def wiki_files() -> dict[str, Path]:
    """Collect all wiki markdown files."""
    return {f.name: f for f in WIKI_DIR.glob("*.md")}


@pytest.fixture(scope="module")
def wiki_headings(wiki_files: dict[str, Path]) -> dict[str, dict[str, int]]:
    """Extract all headings from wiki files."""
    headings = {}
    for md_file in wiki_files.values():
        content = md_file.read_text(encoding='utf-8')
        headings[md_file.name] = extract_headings(content)
    return headings


def test_markdownlint_compliance():
    """Test that all wiki markdown files pass markdownlint."""
    if not MARKDOWNLINT_CONFIG.exists():
        pytest.skip(f"markdownlint config not found: {MARKDOWNLINT_CONFIG}")
    
    # Use shell=True on Windows to find npx in PATH
    import sys
    shell = sys.platform == "win32"
    
    result = subprocess.run(
        ["npx", "--yes", "markdownlint-cli2", "wiki/*.md", "--config", str(MARKDOWNLINT_CONFIG)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        shell=shell,
    )
    
    if result.returncode != 0:
        # Extract error summary
        error_lines = [line for line in result.stdout.splitlines() if "error" in line.lower()]
        error_summary = "\n".join(error_lines[:50])  # Show first 50 errors
        pytest.fail(f"markdownlint found errors:\n{error_summary}\n\nRun: npx markdownlint-cli2 'wiki/*.md' --fix --config .markdownlint-cli2.jsonc")


def test_wiki_files_exist(wiki_files: dict[str, Path]):
    """Test that wiki directory contains markdown files."""
    assert len(wiki_files) > 0, "No markdown files found in wiki directory"


@pytest.mark.parametrize("md_file", [pytest.param(f, id=f.name) for f in (REPO_ROOT / "wiki").glob("*.md")])
def test_markdown_links_valid(md_file: Path, wiki_files: dict[str, Path], wiki_headings: dict[str, dict[str, int]]):
    """Test that all links in a markdown file are valid.
    
    This test validates:
    - File references exist
    - Anchor references exist in target files
    - Links are properly formatted
    """
    content = md_file.read_text(encoding='utf-8')
    links = extract_links(content, md_file)
    
    errors = []
    for link_text, link_url, line_num in links:
        is_valid, error_msg = validate_link(link_url, md_file, wiki_files, wiki_headings)
        if not is_valid:
            errors.append(f"Line {line_num}: [{link_text}]({link_url}) - {error_msg}")
    
    if errors:
        error_summary = "\n".join(errors[:20])  # Show first 20 errors per file
        if len(errors) > 20:
            error_summary += f"\n... and {len(errors) - 20} more errors"
        pytest.fail(f"Invalid links in {md_file.name}:\n{error_summary}")


def test_all_links_clickable(wiki_files: dict[str, Path], wiki_headings: dict[str, dict[str, int]]):
    """Test that all links are clickable (files exist and anchors are valid)."""
    all_errors = []
    
    for md_file in wiki_files.values():
        content = md_file.read_text(encoding='utf-8')
        links = extract_links(content, md_file)
        
        for link_text, link_url, line_num in links:
            # Skip external URLs
            parsed = urlparse(link_url)
            if parsed.scheme in ('http', 'https', 'mailto'):
                continue
            
            is_valid, error_msg = validate_link(link_url, md_file, wiki_files, wiki_headings)
            if not is_valid:
                all_errors.append(f"{md_file.name}:{line_num} [{link_text}]({link_url}) - {error_msg}")
    
    if all_errors:
        error_summary = "\n".join(all_errors[:100])  # Show first 100 errors
        if len(all_errors) > 100:
            error_summary += f"\n... and {len(all_errors) - 100} more errors"
        pytest.fail(f"Found {len(all_errors)} invalid links:\n{error_summary}")


# Overly common words that should NOT be hyperlinked to generic GFF anchors
# These are common English words that were incorrectly linked
OVERLY_BROAD_PATTERNS = [
    # Pattern: (link_text_pattern, forbidden_url_patterns, description)
    # link_text_pattern is a regex that matches the link text
    # forbidden_url_patterns is a list of regex patterns for URLs that should not be used
    (
        r"^(type|types)$",
        [
            r"GFF-File-Format#data-types",
            r"GFF-File-Format#gff-data-types",
        ],
        "Common word 'type' should not be linked to generic GFF data-types anchor",
    ),
    (
        r"^(value|values)$",
        [
            r"GFF-File-Format#data-types",
            r"GFF-File-Format#gff-data-types",
        ],
        "Common word 'value' should not be linked to generic GFF data-types anchor",
    ),
    (
        r"^(field|fields)$",
        [
            r"GFF-File-Format#file-structure",
            r"GFF-File-Format#file-structure-overview",
        ],
        "Common word 'field' should not be linked to generic GFF file-structure anchor",
    ),
    (
        r"^(format|formats)$",
        [
            r"GFF-File-Format$",  # Just GFF-File-Format without anchor
        ],
        "Common word 'format' should not be linked to generic GFF-File-Format",
    ),
    (
        r"^(file|files)$",
        [
            r"GFF-File-Format$",  # Just GFF-File-Format without anchor
        ],
        "Common word 'file' should not be linked to generic GFF-File-Format",
    ),
    (
        r"^data$",
        [
            r"GFF-File-Format#file-structure",
            r"GFF-File-Format#file-structure-overview",
        ],
        "Common word 'data' should not be linked to generic GFF file-structure anchor",
    ),
    (
        r"^(structure|structures)$",
        [
            r"GFF-File-Format#file-structure",
            r"GFF-File-Format#file-structure-overview",
        ],
        "Common word 'structure' should not be linked to generic GFF file-structure anchor",
    ),
    (
        r"^(string|strings)$",
        [
            r"GFF-File-Format#cexostring",
            r"GFF-File-Format#gff-data-types",
        ],
        "Common word 'string' should not be linked to generic GFF cexostring anchor",
    ),
    (
        r"^(array|arrays)$",
        [
            r"2DA-File-Format$",  # Just 2DA-File-Format without anchor
        ],
        "Common word 'array' should not be linked to generic 2DA-File-Format",
    ),
    (
        r"^(index|indexes|indices)$",
        [
            r"2DA-File-Format#row-labels",
        ],
        "Common word 'index' should not be linked to generic 2DA row-labels anchor",
    ),
    (
        r"^(vector|vectors)$",
        [
            r"GFF-File-Format#vector",
            r"GFF-File-Format#gff-data-types",
        ],
        "Common word 'vector' should not be linked to generic GFF vector anchor",
    ),
    (
        r"^(color|colors)$",
        [
            r"GFF-File-Format#color",
            r"GFF-File-Format#gff-data-types",
        ],
        "Common word 'color' should not be linked to generic GFF color anchor",
    ),
    (
        r"^count$",
        [
            r"GFF-File-Format#file-structure",
            r"GFF-File-Format#file-structure-overview",
        ],
        "Common word 'count' should not be linked to generic GFF file-structure anchor",
    ),
    (
        r"^size$",
        [
            r"GFF-File-Format#file-structure",
            r"GFF-File-Format#file-structure-overview",
        ],
        "Common word 'size' should not be linked to generic GFF file-structure anchor",
    ),
    (
        r"^(offset|offsets)$",
        [
            r"GFF-File-Format#file-structure",
            r"GFF-File-Format#file-structure-overview",
        ],
        "Common word 'offset' should not be linked to generic GFF file-structure anchor",
    ),
    (
        r"^(pointer|pointers)$",
        [
            r"GFF-File-Format#file-structure",
            r"GFF-File-Format#file-structure-overview",
        ],
        "Common word 'pointer' should not be linked to generic GFF file-structure anchor",
    ),
    (
        r"^(header|headers)$",
        [
            r"GFF-File-Format#file-header",
        ],
        "Common word 'header' should not be linked to generic GFF file-header anchor",
    ),
    (
        r"^(flag|flags)$",
        [
            r"GFF-File-Format#data-types",
        ],
        "Common word 'flag' should not be linked to generic GFF data-types anchor",
    ),
    (
        r"^(bit|bits)$",
        [
            r"GFF-File-Format#data-types",
            r"GFF-File-Format#gff-data-types",
        ],
        "Common word 'bit' should not be linked to generic GFF data-types anchor (unless in technical context like '32-bit')",
    ),
    (
        r"^(mask|masks|bitmask|bitmasks)$",
        [
            r"GFF-File-Format#data-types",
        ],
        "Common word 'mask' should not be linked to generic GFF data-types anchor",
    ),
    (
        r"^(matrix|matrices)$",
        [
            r"BWM-File-Format#vertex-data-processing",
        ],
        "Common word 'matrix' should not be linked to generic BWM vertex-data-processing anchor",
    ),
    (
        r"^(coordinate|coordinates)$",
        [
            r"GFF-File-Format#are-area",
        ],
        "Common word 'coordinate' should not be linked to generic GFF are-area anchor",
    ),
    (
        r"^(position|positions)$",
        [
            r"MDL-MDX-File-Format#node-header",
        ],
        "Common word 'position' should not be linked to generic MDL-MDX node-header anchor",
    ),
    (
        r"^(orientation|orientations)$",
        [
            r"MDL-MDX-File-Format#node-header",
        ],
        "Common word 'orientation' should not be linked to generic MDL-MDX node-header anchor",
    ),
    (
        r"^(rotation|rotations)$",
        [
            r"MDL-MDX-File-Format#node-header",
        ],
        "Common word 'rotation' should not be linked to generic MDL-MDX node-header anchor",
    ),
    (
        r"^(transformation|transformations)$",
        [
            r"BWM-File-Format#vertex-data-processing",
        ],
        "Common word 'transformation' should not be linked to generic BWM vertex-data-processing anchor",
    ),
    (
        r"^scale$",
        [
            r"MDL-MDX-File-Format#node-header",
        ],
        "Common word 'scale' should not be linked to generic MDL-MDX node-header anchor",
    ),
]


def is_legitimate_technical_use(link_text: str, link_url: str, line_content: str) -> bool:
    """Check if a link is a legitimate technical use rather than an overly broad link.
    
    Returns True if the link should be allowed (e.g., "32-bit", "4-byte", compound terms).
    """
    # Allow compound terms with numbers (e.g., "32-bit", "16-bit", "8-bit", "4-byte")
    if re.search(r'\d+[- ](bit|byte|word|dword)', link_text, re.IGNORECASE):
        return True
    
    # Allow compound terms (e.g., "file format", "data type", "file structure")
    compound_patterns = [
        r'\b(file|data|format|structure|type|value|field|count|size|index|flag|bit|mask|array|string|vector|matrix|coordinate|position|orientation|rotation|transformation|scale|color|header|offset|pointer)\s+(format|file|data|structure|type|value|field|count|size|index|flag|bit|mask|array|string|vector|matrix|coordinate|position|orientation|rotation|transformation|scale|color|header|offset|pointer)\b',
    ]
    for pattern in compound_patterns:
        if re.search(pattern, line_content, re.IGNORECASE):
            return True
    
    # Allow links in code blocks or inline code (they're already protected by the script)
    if '`' in line_content:
        return True
    
    return False


@pytest.mark.parametrize("md_file", [pytest.param(f, id=f.name) for f in (REPO_ROOT / "wiki").glob("*.md")])
def test_no_overly_broad_hyperlinks(md_file: Path):
    """Test that overly common words are not incorrectly hyperlinked.
    
    This test ensures that common English words like "type", "value", "field", etc.
    are not hyperlinked to generic anchors like GFF-File-Format#data-types.
    
    Legitimate technical uses (e.g., "32-bit", "4-byte", compound terms) are allowed.
    """
    content = md_file.read_text(encoding='utf-8')
    links = extract_links(content, md_file)
    
    errors = []
    for link_text, link_url, line_num in links:
        # Skip external URLs
        parsed = urlparse(link_url)
        if parsed.scheme in ('http', 'https', 'mailto'):
            continue
        
        # Get the line content for context checking
        lines = content.splitlines()
        line_content = lines[line_num - 1] if line_num <= len(lines) else ""
        
        # Check each pattern
        for text_pattern, forbidden_urls, description in OVERLY_BROAD_PATTERNS:
            if re.match(text_pattern, link_text, re.IGNORECASE):
                # Check if this matches any forbidden URL pattern
                for forbidden_url in forbidden_urls:
                    if re.search(forbidden_url, link_url):
                        # Check if it's a legitimate technical use
                        if not is_legitimate_technical_use(link_text, link_url, line_content):
                            errors.append(
                                f"Line {line_num}: [{link_text}]({link_url}) - {description}"
                            )
                        break
    
    if errors:
        error_summary = "\n".join(errors[:50])  # Show first 50 errors per file
        if len(errors) > 50:
            error_summary += f"\n... and {len(errors) - 50} more errors"
        pytest.fail(
            f"Found {len(errors)} overly broad hyperlinks in {md_file.name}:\n{error_summary}\n\n"
            f"These common words should not be linked to generic anchors. "
            f"Run: python scripts/revert_overly_broad_links.py to fix."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

