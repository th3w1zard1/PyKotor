#!/usr/bin/env python3
"""Check door dimensions in a kit JSON file.

Usage:
    python scripts/check_door_dims.py [--file PATH] [--default-width W] [--default-height H]
    python scripts/check_door_dims.py --file tests/test_toolset/test_files/generated_kit/jedienclave.json
"""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


def check_door_dims(
    json_path: Path,
    default_width: float = 2.0,
    default_height: float = 3.0,
) -> None:
    """Check door dimensions in a kit JSON file."""
    if not json_path.exists():
        print(f"Error: JSON file not found: {json_path}", file=sys.stderr)
        sys.exit(1)
    
    data = json.loads(json_path.read_text(encoding="utf-8"))
    doors = data.get("doors", [])
    print(f"File: {json_path}")
    print(f"Total doors: {len(doors)}")
    
    non_default = [
        d for d in doors
        if d.get("width", 0) != default_width or d.get("height", 0) != default_height
    ]
    print(f"Non-default dimensions: {len(non_default)}")
    if non_default:
        print("First 10 non-default doors:")
        for d in non_default[:10]:
            print(f"  {d.get('utd_k1', 'unknown')}: {d.get('width')}x{d.get('height')}")
    
    default_count = len(doors) - len(non_default)
    print(f"\nDefault dimensions ({default_width}x{default_height}): {default_count}")
    
    if default_count == len(doors):
        print("\n⚠ WARNING: All doors are using default dimensions!")
        print("   This suggests door dimension extraction may not be working.")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check door dimensions in a kit JSON file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="Path to kit JSON file (default: tests/test_toolset/test_files/generated_kit/jedienclave.json)"
    )
    parser.add_argument(
        "--default-width",
        type=float,
        default=2.0,
        help="Default door width to check against (default: 2.0)"
    )
    parser.add_argument(
        "--default-height",
        type=float,
        default=3.0,
        help="Default door height to check against (default: 3.0)"
    )
    
    args = parser.parse_args()
    
    if args.file:
        json_path = Path(args.file)
    else:
        # Default path
        repo_root = Path(__file__).parent.parent
        json_path = repo_root / "tests" / "test_toolset" / "test_files" / "generated_kit" / "jedienclave.json"
    
    check_door_dims(json_path, args.default_width, args.default_height)


if __name__ == "__main__":
    main()

