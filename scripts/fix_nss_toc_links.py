#!/usr/bin/env python3
"""Fix NSS-File-Format.md TOC links by removing anchors that no longer exist."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
NSS_FILE = REPO_ROOT / "wiki" / "NSS-File-Format.md"


def fix_toc_links() -> int:
    """Remove anchor parts from links in NSS-File-Format.md."""
    content = NSS_FILE.read_text(encoding='utf-8')
    
    # Detect original line ending style and trailing newline state
    has_crlf = '\r\n' in content
    has_trailing_newline = content.endswith('\n') or content.endswith('\r\n')
    line_ending = '\r\n' if has_crlf else '\n'
    
    lines = content.splitlines()
    changes = 0
    
    # Pattern to match links with anchors: [text](File-Name#anchor)
    pattern = r'(\[([^\]]+)\]\(([^#\)]+)#([^\)]+)\))'
    
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
                # Remove the anchor part, keep just the file link
                replacement = f'[{link_text}]({file_part})'
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
