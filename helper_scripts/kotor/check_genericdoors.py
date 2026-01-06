#!/usr/bin/env python3
"""Check if a 2DA file exists in installation.

Usage:
    python scripts/check_genericdoors.py [--installation PATH] [--2da FILENAME]
    python scripts/check_genericdoors.py --2da genericdoors --installation "C:/Games/KOTOR"
"""

from __future__ import annotations

import argparse
import os
import sys

from pathlib import Path

# Add paths for imports
REPO_ROOT = Path(__file__).parent.parent
PYKOTOR_PATH = REPO_ROOT / "Libraries" / "PyKotor" / "src"
if str(PYKOTOR_PATH) not in sys.path:
    sys.path.insert(0, str(PYKOTOR_PATH))

from pykotor.extract.file import ResourceIdentifier  # noqa: E402
from pykotor.extract.installation import Installation, SearchLocation  # noqa: E402
from pykotor.resource.type import ResourceType  # noqa: E402


def get_installation_path(provided_path: str | None) -> Path:
    """Get installation path from argument, environment variable, or .env file."""
    if provided_path:
        return Path(provided_path)
    
    # Try environment variables
    for env_var in ["K1_PATH", "K2_PATH", "KOTOR_PATH"]:
        env_path = os.environ.get(env_var)
        if env_path and Path(env_path).exists():
            return Path(env_path)
    
    # Try .env file
    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            for env_var in ["K1_PATH", "K2_PATH", "KOTOR_PATH"]:
                if line.startswith(f"{env_var}="):
                    path_str = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if path_str and Path(path_str).exists():
                        return Path(path_str)
    
    raise ValueError("No valid installation path found. Use --installation or set K1_PATH/K2_PATH")


def check_2da_file(installation_path: Path, twoda_name: str) -> None:
    """Check if a 2DA file exists in installation."""
    inst = Installation(installation_path)
    
    print(f"Checking installation: {installation_path}")
    print(f"Looking for 2DA file: {twoda_name}\n")
    
    # Try resource() method
    result = inst.resource(twoda_name, ResourceType.TwoDA)
    if result:
        print(f"✓ Using installation.resource(): Found")
        print(f"  Resource data available: {len(result.data) if result.data else 0} bytes")
    else:
        print(f"✗ Using installation.resource(): Not found")
    
    # Try locations() method
    location_results = inst.locations(
        [ResourceIdentifier(resname=twoda_name, restype=ResourceType.TwoDA)],
        order=[SearchLocation.CHITIN, SearchLocation.OVERRIDE],
    )
    print(f"\nUsing installation.locations(): {len(location_results)} results")
    if location_results:
        for res_ident, loc_list in location_results.items():
            print(f"  Resource: {res_ident}")
            for loc in loc_list:
                print(f"    - {loc.filepath}")
    else:
        print("  No locations found")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check if a 2DA file exists in installation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--installation", "-i",
        type=str,
        help="Path to KOTOR installation (default: from K1_PATH/K2_PATH env or .env file)"
    )
    parser.add_argument(
        "--2da",
        dest="twoda_name",
        type=str,
        default="genericdoors",
        help="2DA file name to check (default: genericdoors)"
    )
    
    args = parser.parse_args()
    
    try:
        installation_path = get_installation_path(args.installation)
        check_2da_file(installation_path, args.twoda_name)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

