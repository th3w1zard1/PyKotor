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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

