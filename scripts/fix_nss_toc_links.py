#!/usr/bin/env python3
"""Fix NSS-File-Format.md TOC links by removing anchors that no longer exist."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
NSS_FILE = REPO_ROOT / "wiki" / "NSS-File-Format.md"


def normalize_anchor(text: str) -> str:
    """Normalize anchor text to match GitHub's anchor generation."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    text = text.strip('-')
    return text


def extract_headings(content: str) -> set[str]:
    """Extract all heading anchors from content."""
    headings = set()
    for line in content.splitlines():
        # Check for HTML anchors
        html_anchor_match = re.search(r'<a\s+id="([^"]+)"', line)
        if html_anchor_match:
            headings.add(html_anchor_match.group(1))
        
        # Check for markdown headings
        match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
        if match:
            heading_text = match.group(2).strip()
            heading_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', heading_text)
            heading_text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', heading_text)
            heading_text = re.sub(r'\*([^\*]+)\*', r'\1', heading_text)
            heading_text = re.sub(r'`([^`]+)`', r'\1', heading_text)
            anchor = normalize_anchor(heading_text)
            headings.add(anchor)
    return headings


def fix_toc_links() -> int:
    """Remove anchor parts from links in NSS-File-Format.md."""
    content = NSS_FILE.read_text(encoding='utf-8')
    
    # Extract all valid headings
    valid_headings = extract_headings(content)
    
    # Detect original line ending style and trailing newline state
    has_crlf = '\r\n' in content
    has_trailing_newline = content.endswith('\n') or content.endswith('\r\n')
    line_ending = '\r\n' if has_crlf else '\n'
    
    lines = content.splitlines()
    changes = 0
    
    # Pattern to match links with anchors: [text](File-Name#anchor) or [text](#anchor)
    pattern = r'(\[([^\]]+)\]\(([^#\)]*)#([^\)]+)\))'
    
    for i, line in enumerate(lines):
        # Find all matches in this line
        matches = list(re.finditer(pattern, line))
        if matches:
            new_line = line
            # Process in reverse to maintain positions
            for match in reversed(matches):
                full_match = match.group(1)
                link_text = match.group(2)
                file_part = match.group(3)
                anchor_part = match.group(4)
                
                # Normalize anchor for comparison
                normalized_anchor = normalize_anchor(anchor_part)
                
                # Check if anchor exists in valid headings
                if normalized_anchor in valid_headings:
                    # Valid anchor, keep the link as-is
                    continue
                
                # Invalid anchor - remove it
                if file_part:
                    # Link to external file - remove anchor, keep file link
                    replacement = f'[{link_text}]({file_part})'
                else:
                    # Anchor-only link - remove the link entirely, keep just text
                    replacement = link_text
                
                new_line = new_line[:match.start()] + replacement + new_line[match.end():]
            
            if new_line != line:
                lines[i] = new_line
                changes += 1
    
    if changes > 0:
        # Reconstruct file with original line endings and trailing newline state
        reconstructed = line_ending.join(lines)
        if has_trailing_newline:
            reconstructed += line_ending
        # Use binary mode to preserve exact line endings
        NSS_FILE.write_bytes(reconstructed.encode('utf-8'))
    
    return changes


def main() -> None:
    """Main entry point."""
    changes = fix_toc_links()
    if changes > 0:
        print(f"Fixed {NSS_FILE.name}: {changes} links updated (anchors removed)")
    else:
        print(f"No changes needed in {NSS_FILE.name}")


if __name__ == "__main__":
    main()
