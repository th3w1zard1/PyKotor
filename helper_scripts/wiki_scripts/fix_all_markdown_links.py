#!/usr/bin/env python3
"""Comprehensive script to fix all broken markdown links."""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
WIKI_DIR = REPO_ROOT / "wiki"

# Anchor mappings
ANCHOR_FIXES = {
    "data-types": "gff-data-types",
    "file-structure": "file-structure-overview",
    "file-header": "file-header",
    "byte": "gff-data-types",
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
    "color": "gff-data-types",  # Color doesn't have its own section
    "colors": "gff-data-types",
    "vertex-data-processing": "walkable-adjacencies",  # Closest match
    "tpc-file-format-documentation": "kotor-tpc-file-format-documentation",
    "TPC-File-Format": "kotor-tpc-file-format-documentation",
}

# File mappings for missing files
FILE_FIXES = {
    "RIM-File-Format": "ERF-File-Format",  # RIM is part of ERF
    "RIM-File-Format.md": "ERF-File-Format.md",
}

def fix_links_in_file(file_path: Path) -> int:
    """Fix broken links in a single file."""
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    fixes = 0
    
    # Fix malformed links like [[char](GFF-File-Format#gff-data-types)][GFF-File-Format#char](4)
    # These should be [char](GFF-File-Format#gff-data-types) with size in text
    def fix_malformed_link(match):
        nonlocal fixes
        # Pattern: [[type](file#anchor)][file#type](size)
        inner_link = match.group(1)  # [type](file#anchor)
        outer_link = match.group(2)  # [file#type](size)
        
        # Extract the type name and anchor
        inner_match = re.match(r'\[([^\]]+)\]\(([^\)]+)\)', inner_link)
        if inner_match:
            type_name = inner_match.group(1)
            anchor_url = inner_match.group(2)
            # Extract size from outer link
            size_match = re.search(r'\]\((\d+)\)', outer_link)
            if size_match:
                size = size_match.group(1)
                fixes += 1
                return f"[{type_name}]({anchor_url})"
        
        return match.group(0)
    
    # Fix malformed double-link pattern - remove the outer link part
    pattern1 = r'\[\[([^\]]+)\]\(([^\)]+)\)\]\[[^\]]+\]\((\d+)\)'
    content = re.sub(pattern1, r'[\1](\2)', content)
    
    # Fix anchor references
    def fix_anchor(match):
        nonlocal fixes
        link_text = match.group(1)
        link_url = match.group(2)
        
        if '#' in link_url:
            file_part, anchor_part = link_url.split('#', 1)
            # Fix GFF-File-Format anchors
            if file_part == "GFF-File-Format" and anchor_part in ANCHOR_FIXES:
                new_anchor = ANCHOR_FIXES[anchor_part]
                fixes += 1
                return f"[{link_text}]({file_part}#{new_anchor})"
            # Fix BWM-File-Format anchors
            elif file_part == "BWM-File-Format" and anchor_part in ANCHOR_FIXES:
                new_anchor = ANCHOR_FIXES[anchor_part]
                fixes += 1
                return f"[{link_text}]({file_part}#{new_anchor})"
            # Fix same-file anchors
            elif file_part == "" and anchor_part in ANCHOR_FIXES:
                new_anchor = ANCHOR_FIXES[anchor_part]
                fixes += 1
                return f"[{link_text}](#{new_anchor})"
        else:
            # Fix file references
            if link_url in FILE_FIXES:
                new_file = FILE_FIXES[link_url]
                fixes += 1
                return f"[{link_text}]({new_file})"
            elif f"{link_url}.md" in FILE_FIXES:
                new_file = FILE_FIXES[f"{link_url}.md"]
                fixes += 1
                return f"[{link_text}]({new_file})"
        
        return match.group(0)
    
    # Fix anchor and file references
    pattern2 = r'\[([^\]]+)\]\(([^\)"]+)(?:\s+"[^"]+")?\)'
    content = re.sub(pattern2, fix_anchor, content)
    
    # Fix malformed file references like [cls_atk_*.2da](cls_atk__pattern_pattern)
    # These should point to the actual 2DA file format doc
    pattern3 = r'\[([^\]]+)\]\(cls_atk__pattern_pattern\)'
    content = re.sub(pattern3, r'[\1](2DA-cls_atk__pattern)', content)
    pattern4 = r'\[([^\]]+)\]\(cls_savthr__pattern_pattern\)'
    content = re.sub(pattern4, r'[\1](2DA-cls_savthr__pattern)', content)
    
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        fixes += content.count('[') - original_content.count('[')  # Rough estimate
    
    return fixes


def main():
    """Main entry point."""
    total_fixes = 0
    
    for md_file in WIKI_DIR.glob("*.md"):
        fixes = fix_links_in_file(md_file)
        if fixes > 0:
            print(f"Fixed {fixes} links in {md_file.name}")
            total_fixes += fixes
    
    print(f"\nTotal fixes: {total_fixes}")
    return 0


if __name__ == "__main__":
    exit(main())

