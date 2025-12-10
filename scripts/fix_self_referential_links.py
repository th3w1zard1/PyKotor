#!/usr/bin/env python3
"""Fix self-referential links in markdown files.

Removes links that point to the same section within the same file.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
WIKI_DIR = REPO_ROOT / "wiki"


def normalize_anchor(text: str) -> str:
    """Normalize anchor text to match GitHub's anchor generation."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    text = text.strip('-')
    return text


def extract_headings(content: str) -> dict[str, int]:
    """Extract all headings and their line numbers."""
    headings = {}
    for line_num, line in enumerate(content.splitlines(), 1):
        html_anchor_match = re.search(r'<a\s+id="([^"]+)"', line)
        if html_anchor_match:
            anchor = html_anchor_match.group(1)
            headings[anchor] = line_num
        
        match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
        if match:
            heading_text = match.group(2).strip()
            heading_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', heading_text)
            heading_text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', heading_text)
            heading_text = re.sub(r'\*([^\*]+)\*', r'\1', heading_text)
            heading_text = re.sub(r'`([^`]+)`', r'\1', heading_text)
            anchor = normalize_anchor(heading_text)
            headings[anchor] = line_num
    return headings


def extract_links(content: str) -> list[tuple[str, str, int]]:
    """Extract all markdown links from content."""
    links = []
    pattern = r'\[([^\]]+)\]\(([^\)"]+)(?:\s+"[^"]+")?\)'
    
    for line_num, line in enumerate(content.splitlines(), 1):
        for match in re.finditer(pattern, line):
            link_text = match.group(1)
            link_url = match.group(2)
            links.append((link_text, link_url, line_num))
    
    return links


def fix_self_referential_links(filepath: Path) -> int:
    """Fix self-referential links in a markdown file."""
    content = filepath.read_text(encoding='utf-8')
    
    # Detect original line ending style and trailing newline state
    has_crlf = '\r\n' in content
    has_trailing_newline = content.endswith('\n') or content.endswith('\r\n')
    line_ending = '\r\n' if has_crlf else '\n'
    
    headings = extract_headings(content)
    links = extract_links(content)
    
    lines = content.splitlines()
    changes = 0
    
    # Process links in reverse order to maintain line numbers
    for link_text, link_url, line_num in reversed(links):
        # Skip external URLs
        if link_url.startswith(('http://', 'https://', 'mailto:')):
            continue
        
        # Check if it's a same-file anchor reference
        if '#' in link_url:
            file_part, anchor_part = link_url.split('#', 1)
        else:
            file_part = link_url
            anchor_part = None
        
        # Check if it points to the same file
        if not file_part or file_part == filepath.stem or file_part == filepath.name:
            if anchor_part:
                normalized_anchor = normalize_anchor(anchor_part)
                if normalized_anchor in headings:
                    target_line = headings[normalized_anchor]
                    # If link is within 10 lines of heading, it's self-referential
                    if abs(line_num - target_line) <= 10:
                        # Replace the link with just the text
                        line = lines[line_num - 1]
                        # Find and replace the link
                        pattern = re.escape(f'[{link_text}]({link_url})')
                        # Use lambda to avoid regex backreference interpretation in link_text
                        new_line = re.sub(pattern, lambda m: link_text, line)
                        if new_line != line:
                            lines[line_num - 1] = new_line
                            changes += 1
    
    if changes > 0:
        # Reconstruct file with original line endings and trailing newline state
        reconstructed = line_ending.join(lines)
        if has_trailing_newline:
            reconstructed += line_ending
        # Use binary mode to preserve exact line endings
        filepath.write_bytes(reconstructed.encode('utf-8'))
    
    return changes


def main() -> None:
    """Main entry point."""
    total_changes = 0
    processed_files = 0
    
    for md_file in sorted(WIKI_DIR.glob("*.md")):
        changes = fix_self_referential_links(md_file)
        if changes > 0:
            print(f"Fixed {md_file.name}: {changes} self-referential links removed")
            processed_files += 1
            total_changes += changes
    
    print(f"\nTotal: {processed_files} file(s) processed, {total_changes} self-referential link(s) removed")


if __name__ == "__main__":
    main()

