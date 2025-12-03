#!/usr/bin/env python3
"""Check if TXI files exist in installation for specific textures.

Usage:
    python scripts/check_txi_files.py [--installation PATH] [--textures TEXTURE1 TEXTURE2 ...]
    python scripts/check_txi_files.py --installation "C:/Games/KOTOR" --textures lda_bark04 lda_flr11
"""

from __future__ import annotations

import argparse
import os
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).parents[1]
LIBS_PATH = REPO_ROOT / "Libraries"
PYKOTOR_PATH = LIBS_PATH / "PyKotor" / "src"
UTILITY_PATH = LIBS_PATH / "Utility" / "src"

if str(PYKOTOR_PATH) not in sys.path:
    sys.path.insert(0, str(PYKOTOR_PATH))
if str(UTILITY_PATH) not in sys.path:
    sys.path.insert(0, str(UTILITY_PATH))

os.environ["QT_QPA_PLATFORM"] = "offscreen"

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
    
    # Default fallback
    default = Path("C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
    if default.exists():
        return default
    
    raise ValueError("No valid installation path found. Use --installation or set K1_PATH/K2_PATH")


def check_txi_files(installation_path: Path, texture_names: list[str]) -> None:
    """Check if TXI files exist for given textures."""
    inst = Installation(installation_path)
    
    print(f"Checking installation: {installation_path}")
    print(f"Checking {len(texture_names)} textures for TXI files:\n")
    
    found_count = 0
    for tex_name in texture_names:
        locations = inst.locations(
            [ResourceIdentifier(resname=tex_name, restype=ResourceType.TXI)],
            [
                SearchLocation.OVERRIDE,
                SearchLocation.TEXTURES_GUI,
                SearchLocation.TEXTURES_TPA,
                SearchLocation.CHITIN,
            ],
        )
        if locations:
            found_count += 1
            print(f"  ✓ {tex_name}.txi: FOUND")
            for res_ident, loc_list in locations.items():
                for loc in loc_list[:1]:
                    print(f"    - {loc.filepath.name} (in {loc.filepath.parent.name})")
        else:
            print(f"  ✗ {tex_name}.txi: NOT FOUND")
    
    print(f"\nSummary: {found_count}/{len(texture_names)} TXI files found")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check if TXI files exist in installation for specific textures",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--installation", "-i",
        type=str,
        help="Path to KOTOR installation (default: from K1_PATH/K2_PATH env or .env file)"
    )
    parser.add_argument(
        "--textures", "-t",
        nargs="+",
        default=[
            "lda_bark04", "lda_flr11", "lda_grass07", "lda_grate01", "lda_ivy01",
            "lda_leaf02", "lda_lite01", "lda_rock06", "lda_sky0001", "lda_sky0002",
            "lda_sky0003", "lda_sky0004", "lda_sky0005", "lda_trim02", "lda_trim03",
            "lda_trim04", "lda_unwal07", "lda_wall02", "lda_wall03", "lda_wall04",
        ],
        help="List of texture names to check (default: predefined list)"
    )
    
    args = parser.parse_args()
    
    try:
        installation_path = get_installation_path(args.installation)
        check_txi_files(installation_path, args.textures)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

