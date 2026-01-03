#!/usr/bin/env python3
"""Check if missing resources are actually referenced by module models.

Usage:
    python scripts/check_missing_resources.py [--installation PATH] [--module MODULE] [--lightmaps LM1 LM2] [--textures TEX1 TEX2]
    python scripts/check_missing_resources.py --module danm13 --lightmaps m03af_01a_lm13 m03af_03a_lm13
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

from pykotor.common.module import Module  # noqa: E402
from pykotor.extract.installation import Installation  # noqa: E402
from pykotor.tools.model import iterate_lightmaps, iterate_textures  # noqa: E402


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


def check_missing_resources(
    installation_path: Path,
    module_name: str,
    missing_lightmaps: list[str],
    missing_textures: list[str],
) -> None:
    """Check if missing resources are referenced by module models."""
    inst = Installation(installation_path)
    module = Module(module_name, inst, use_dot_mod=False)
    
    all_lightmaps = set()
    all_textures = set()
    
    print(f"Scanning all models in {module_name}...")
    for mdl in module.models():
        try:
            mdl_data = mdl.data()
            if mdl_data is None:
                print(f"  Error getting data for {mdl.identifier()}")
                continue
            for lm in iterate_lightmaps(mdl_data):
                all_lightmaps.add(lm.lower())
            for tex in iterate_textures(mdl_data):
                all_textures.add(tex.lower())
        except Exception as e:
            print(f"  Error processing {mdl.identifier()}: {e}")
    
    print(f"\nTotal lightmaps referenced: {len(all_lightmaps)}")
    print(f"Total textures referenced: {len(all_textures)}")
    
    if missing_lightmaps:
        print("\nChecking if missing lightmaps are referenced:")
        referenced_lms = 0
        for lm in missing_lightmaps:
            if lm.lower() in all_lightmaps:
                print(f"  ✓ {lm}: YES")
                referenced_lms += 1
            else:
                print(f"  ✗ {lm}: NO")
        print(f"\n  Summary: {referenced_lms}/{len(missing_lightmaps)} lightmaps are referenced")
    
    if missing_textures:
        print("\nChecking if missing textures are referenced:")
        referenced_tex = 0
        for tex in missing_textures:
            if tex.lower() in all_textures:
                print(f"  ✓ {tex}: YES")
                referenced_tex += 1
            else:
                print(f"  ✗ {tex}: NO")
        print(f"\n  Summary: {referenced_tex}/{len(missing_textures)} textures are referenced")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check if missing resources are referenced by module models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--installation", "-i",
        type=str,
        help="Path to KOTOR installation (default: from K1_PATH/K2_PATH env or .env file)"
    )
    parser.add_argument(
        "--module", "-m",
        type=str,
        default="danm13",
        help="Module name to check (default: danm13)"
    )
    parser.add_argument(
        "--lightmaps", "-l",
        nargs="+",
        default=[],
        help="List of lightmap names to check"
    )
    parser.add_argument(
        "--textures", "-t",
        nargs="+",
        default=[],
        help="List of texture names to check"
    )
    
    args = parser.parse_args()
    
    if not args.lightmaps and not args.textures:
        # Default lists if nothing provided
        args.lightmaps = [
            "m03af_01a_lm13", "m03af_03a_lm13",
            "m03mg_01a_lm13",
            "m10aa_01a_lm13", "m10ac_28a_lm13",
            "m14ab_02a_lm13",
            "m15aa_01a_lm13",
            "m22aa_03a_lm13", "m22ab_12a_lm13",
            "m28ab_19a_lm13",
            "m33ab_01_lm13",
            "m36aa_01_lm13",
            "m44ab_27a_lm13",
        ]
        args.textures = [
            "h_f_lo01headtest", "i_datapad", "lda_bark04", "lda_flr07", "lda_flr08",
            "lda_flr11", "lda_grass07", "lda_grate01", "lda_ivy01", "lda_leaf02",
            "lda_lite01", "lda_rock06", "lda_sky0001", "lda_sky0002", "lda_sky0003",
            "lda_sky0004", "lda_sky0005", "lda_trim02", "lda_trim03", "lda_trim04",
            "lda_unwal07",
        ]
    
    try:
        installation_path = get_installation_path(args.installation)
        check_missing_resources(
            installation_path,
            args.module,
            args.lightmaps,
            args.textures,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

