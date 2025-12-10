#!/usr/bin/env python3
"""Script to validate markdown links in wiki documentation.

Scans all markdown files and validates:
- File references exist
- Anchor references exist in target files
- Links are properly formatted
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).parent.parent
WIKI_DIR = REPO_ROOT / "wiki"


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


def validate_all_links() -> dict[str, list[tuple[str, str, int, str]]]:
    """Validate all links in wiki markdown files.
    
    Returns: Dict mapping file_path to list of (link_text, link_url, line_num, error) tuples
    """
    # Collect all files and their headings
    all_files = {}
    all_headings = {}
    
    for md_file in WIKI_DIR.glob("*.md"):
        all_files[md_file.name] = md_file
        content = md_file.read_text(encoding='utf-8')
        all_headings[md_file.name] = extract_headings(content)
    
    # Validate links
    errors = {}
    for md_file in WIKI_DIR.glob("*.md"):
        content = md_file.read_text(encoding='utf-8')
        links = extract_links(content, md_file)
        
        file_errors = []
        for link_text, link_url, line_num in links:
            is_valid, error_msg = validate_link(link_url, md_file, all_files, all_headings)
            if not is_valid:
                file_errors.append((link_text, link_url, line_num, error_msg))
        
        if file_errors:
            errors[str(md_file.relative_to(REPO_ROOT))] = file_errors
    
    return errors


def main():
    """Main entry point."""
    errors = validate_all_links()
    
    if errors:
        print("Broken links found:\n")
        total_errors = 0
        for file_path, file_errors in sorted(errors.items()):
            print(f"{file_path}:")
            for link_text, link_url, line_num, error_msg in file_errors:
                print(f"  Line {line_num}: [{link_text}]({link_url}) - {error_msg}")
                total_errors += 1
            print()
        print(f"Total errors: {total_errors}")
        return 1
    else:
        print("All links are valid!")
        return 0


if __name__ == "__main__":
    exit(main())

