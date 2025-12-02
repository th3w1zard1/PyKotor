#!/usr/bin/env python3
"""Verify that all sections are in the TOC.

Usage:
    python scripts/verify_toc.py [--file PATH]
    python scripts/verify_toc.py --file wiki/NSS-File-Format.md
"""

from __future__ import annotations

import argparse
import re
import sys

from pathlib import Path


def verify_toc(md_path: Path) -> bool:
    """Verify that all sections in a markdown file are in the TOC.
    
    Returns:
        True if all sections are in TOC, False otherwise
    """
    if not md_path.exists():
        print(f"Error: File not found: {md_path}", file=sys.stderr)
        return False
    
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract all sections
    sections = re.findall(r'^###? (.+)$', content, re.MULTILINE)
    
    # Extract TOC entries
    toc_entries = re.findall(r'^\s*- \[(.+?)\]\(#', content, re.MULTILINE)
    
    print(f"File: {md_path}")
    print(f"Total sections: {len(sections)}")
    print(f"Total TOC entries: {len(toc_entries)}")
    print(f"Difference: {len(sections) - len(toc_entries)}")
    
    # Find missing sections
    section_set = set(sections)
    toc_set = set(toc_entries)
    missing = section_set - toc_set
    
    if missing:
        print(f"\nMissing from TOC ({len(missing)}):")
        for section in sorted(missing):
            print(f"  - {section}")
    else:
        print("\n✓ All sections are in the TOC!")
    
    # Find extra TOC entries
    extra = toc_set - section_set
    if extra:
        print(f"\nExtra TOC entries ({len(extra)}):")
        for entry in sorted(extra):
            print(f"  - {entry}")
    
    return len(missing) == 0


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify that all sections in a markdown file are in the TOC",
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
    
    success = verify_toc(md_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

