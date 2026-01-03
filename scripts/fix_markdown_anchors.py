#!/usr/bin/env python3
"""Script to fix common broken anchor references in markdown files."""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
WIKI_DIR = REPO_ROOT / "wiki"

# Common anchor mappings - maps broken anchor to correct anchor
ANCHOR_FIXES = {
    # GFF-File-Format.md anchor fixes
    "data-types": "gff-data-types",
    "file-structure": "file-structure-overview",
    "file-header": "file-header",
    "byte": "gff-data-types",  # Points to the types section
    "char": "gff-data-types",
    "float": "gff-data-types",
    "double": "gff-data-types",
    "cexostring": "gff-data-types",
    "localizedstring": "gff-data-types",
    "resref": "gff-data-types",
    "vector": "gff-data-types",
    "word": "gff-data-types",
    "short": "gff-data-types",
    "dword": "gff-data-types",
    "int": "gff-data-types",
    # TPC-File-Format.md
    "TPC-File-Format": "tpc-file-format-documentation",
}

def fix_anchors_in_file(file_path: Path) -> int:
    """Fix broken anchors in a single file.
    
    Returns: Number of fixes made
    """
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    fixes = 0
    
    # Pattern matches [text](file#anchor) or [text](#anchor)
    def replace_anchor(match):
        nonlocal fixes
        link_text = match.group(1)
        link_url = match.group(2)
        
        if '#' in link_url:
            file_part, anchor_part = link_url.split('#', 1)
            # Only fix if pointing to GFF-File-Format
            if file_part == "GFF-File-Format" and anchor_part in ANCHOR_FIXES:
                new_anchor = ANCHOR_FIXES[anchor_part]
                fixes += 1
                return f"[{link_text}]({file_part}#{new_anchor})"
            # Fix TPC-File-Format anchor
            elif file_part == "" and anchor_part in ANCHOR_FIXES:
                new_anchor = ANCHOR_FIXES[anchor_part]
                fixes += 1
                return f"[{link_text}](#{new_anchor})"
        
        return match.group(0)
    
    # Replace anchors in markdown links
    pattern = r'\[([^\]]+)\]\(([^\)"]+)(?:\s+"[^"]+")?\)'
    content = re.sub(pattern, replace_anchor, content)
    
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
    
    return fixes


def main():
    """Main entry point."""
    total_fixes = 0
    
    for md_file in WIKI_DIR.glob("*.md"):
        fixes = fix_anchors_in_file(md_file)
        if fixes > 0:
            print(f"Fixed {fixes} anchors in {md_file.name}")
            total_fixes += fixes
    
    print(f"\nTotal fixes: {total_fixes}")
    return 0


if __name__ == "__main__":
    exit(main())

