#!/usr/bin/env python3
"""Verify that all functions and constants have anchors.

Usage:
    python scripts/verify_anchors.py [--file PATH]
    python scripts/verify_anchors.py --file wiki/NSS-File-Format.md
"""

from __future__ import annotations

import argparse
import re
import sys

from pathlib import Path


def title_to_anchor(title: str) -> str:
    """Convert a title to an anchor ID."""
    anchor = title.lower()
    anchor = re.sub(r'[^\w\s-]', '', anchor)
    anchor = re.sub(r'[-\s]+', '-', anchor)
    return anchor.strip('-')


def verify_anchors(md_path: Path) -> bool:
    """Verify that all functions and constants have anchors.
    
    Returns:
        True if all functions/constants have anchors, False otherwise
    """
    if not md_path.exists():
        print(f"Error: File not found: {md_path}", file=sys.stderr)
        return False
    
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract all functions (may have content before/after the **`...`** pattern)
    funcs = set()
    for match in re.finditer(r'\*\*`(\w+)\([^)]*\)`\*\*', content):
        funcs.add(match.group(1))
    print(f"Total functions: {len(funcs)}")
    
    # Extract all constants (must start with - at beginning of line after stripping)
    consts = set()
    for line in content.split('\n'):
        line_stripped = line.strip()
        const_match = re.match(r'^- `(\w+)`\s*\([^)]+\):', line_stripped)
        if const_match:
            consts.add(const_match.group(1))
    print(f"Total constants: {len(consts)}")
    
    # Extract all anchors
    anchors = set(re.findall(r'<a id="([^"]+)">', content))
    print(f"Total anchors: {len(anchors)}")
    
    # Check which functions/constants are missing anchors
    missing_funcs = []
    for func in funcs:
        anchor = title_to_anchor(func)
        if anchor not in anchors:
            missing_funcs.append((func, anchor))
    
    missing_consts = []
    for const in consts:
        anchor = title_to_anchor(const)
        if anchor not in anchors:
            missing_consts.append((const, anchor))
    
    print(f"\nMissing function anchors: {len(missing_funcs)}")
    if missing_funcs:
        print("First 10 missing:")
        for func, anchor in missing_funcs[:10]:
            print(f"  {func} -> {anchor}")
    
    print(f"\nMissing constant anchors: {len(missing_consts)}")
    if missing_consts:
        print("First 10 missing:")
        for const, anchor in missing_consts[:10]:
            print(f"  {const} -> {anchor}")
    
    # Check TOC entries
    toc_funcs = set(re.findall(r'^\s{4}- \[`(\w+)`\]\(#', content, re.MULTILINE))
    toc_consts = set(re.findall(r'^\s{4}- \[`(\w+)`\]\(#', content, re.MULTILINE))
    print(f"\nTOC function entries: {len(toc_funcs)}")
    print(f"TOC constant entries: {len(toc_consts)}")
    
    if len(missing_funcs) == 0 and len(missing_consts) == 0:
        print("\n✓ All functions and constants have anchors!")
        return True
    else:
        print(f"\n✗ Missing {len(missing_funcs) + len(missing_consts)} anchors total")
        return False


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify that all functions and constants have anchors",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="Path to markdown file (default: wiki/NSS-File-Format.md)"
    )
    
    args = parser.parse_args()
    
    if args.file:
        md_path = Path(args.file)
    else:
        # Default to NSS-File-Format.md
        repo_root = Path(__file__).parent.parent
        md_path = repo_root / "wiki" / "NSS-File-Format.md"
    
    success = verify_anchors(md_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

