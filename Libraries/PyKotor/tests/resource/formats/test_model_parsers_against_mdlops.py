"""Test MDL/MDX models from actual game installations for both K1 and TSL."""

from __future__ import annotations

import difflib
import random
import subprocess
import sys
import tempfile
from pathlib import Path

# Add PyKotor to path (relative to tests/python/)
sys.path.insert(0, "../../vendor/PyKotor/Libraries/PyKotor/src")

try:
    from pykotor.common.misc import Game
    from pykotor.extract.file import FileResource
    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.mdl import read_mdl, write_mdl
    from pykotor.resource.type import ResourceType
    from pykotor.tools.path import find_kotor_paths_from_default
except ImportError as e:
    print(f"Failed to import PyKotor: {e}")
    sys.exit(1)


def find_test_models(
    game: Game,
    max_models: int = 5,
) -> list[tuple[FileResource, FileResource]]:
    """Find MDL/MDX pairs from game installation. Improved for performance and memory."""
    paths = find_kotor_paths_from_default()
    game_paths = paths.get(game, [])
    if not game_paths:
        print(f"No {game} installation found")
        return []

    mdl_dict: dict[str, FileResource] = {}
    mdx_dict: dict[str, FileResource] = {}

    for game_path in game_paths:
        installation = Installation(game_path)
        # Use generator and type filtering for speed, avoid repeated mapping/creation
        for res in installation:
            restype = res.restype()
            if restype == ResourceType.MDL:
                mdl_dict[res.resname()] = res
            elif restype == ResourceType.MDX:
                mdx_dict[res.resname()] = res

    mdl_mdx_pairs: list[tuple[FileResource, FileResource]] = []
    # Only return pairs where both MDL and MDX exist
    for resname, mdl_res in mdl_dict.items():
        mdx_res = mdx_dict.get(resname)
        if mdx_res:
            mdl_mdx_pairs.append((mdl_res, mdx_res))

    return mdl_mdx_pairs


def test_model(
    mdl_res: FileResource,
    mdx_res: FileResource,
    mdlops_exe: Path,
) -> tuple[bool, str]:
    """Test a single model with MDLOps and compare with PyKotor output."""
    with tempfile.TemporaryDirectory(prefix="mdl_test_") as td:
        td_path = Path(td)
        # Construct filenames from resname and extension
        mdl_filename = f"{mdl_res.resname()}.{mdl_res.restype().extension}"
        mdx_filename = f"{mdx_res.resname()}.{mdx_res.restype().extension}"
        test_mdl = td_path / mdl_filename
        test_mdx = td_path / mdx_filename

        # Write byte data from FileResource to temporary files
        # This works for both archive-based and file-based resources
        test_mdl.write_bytes(mdl_res.data())
        test_mdx.write_bytes(mdx_res.data())

        # Step 1: Decompile with MDLOps
        try:
            result = subprocess.run(
                [str(mdlops_exe), str(test_mdl)],
                cwd=str(td_path),
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return False, f"MDLOps failed: {result.stdout[:200]}"

            mdlops_ascii_path = td_path / f"{test_mdl.stem}-ascii.mdl"
            if not mdlops_ascii_path.exists():
                return False, "MDLOps succeeded but no ASCII output"

        except subprocess.TimeoutExpired:
            return False, "MDLOps timeout"
        except Exception as e:
            return False, f"MDLOps error: {e}"

        # Step 2: Read MDL with PyKotor and write back to binary
        try:
            # Read the original binary MDL/MDX
            mdl_obj = read_mdl(test_mdl, source_ext=test_mdx, file_format=ResourceType.MDL)
            if mdl_obj is None:
                return False, "PyKotor failed to read MDL"

            # Write PyKotor binary output
            pykotor_mdl = td_path / f"{test_mdl.stem}-pykotor.mdl"
            pykotor_mdx = td_path / f"{test_mdl.stem}-pykotor.mdx"
            write_mdl(mdl_obj, pykotor_mdl, ResourceType.MDL, target_ext=pykotor_mdx)

            if not pykotor_mdl.exists():
                return False, "PyKotor failed to write MDL"

        except Exception as e:
            return False, f"PyKotor error: {e}"

        # Step 3: Decompile PyKotor output with MDLOps
        try:
            result = subprocess.run(
                [str(mdlops_exe), str(pykotor_mdl)],
                cwd=str(td_path),
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return False, f"MDLOps failed on PyKotor output: {result.stdout[:200]}"

            pykotor_ascii_path = td_path / f"{pykotor_mdl.stem}-ascii.mdl"
            if not pykotor_ascii_path.exists():
                return False, "MDLOps succeeded but no ASCII output for PyKotor binary"

        except subprocess.TimeoutExpired:
            return False, "MDLOps timeout on PyKotor output"
        except Exception as e:
            return False, f"MDLOps error on PyKotor output: {e}"

        # Step 4: Compare MDLOps ASCII outputs using unified diff
        try:
            mdlops_ascii = mdlops_ascii_path.read_text(encoding="utf-8", errors="replace")
            pykotor_ascii = pykotor_ascii_path.read_text(encoding="utf-8", errors="replace")

            if mdlops_ascii == pykotor_ascii:
                return True, "OK"

            # Generate unified diff
            diff_lines = list(
                difflib.unified_diff(
                    mdlops_ascii.splitlines(keepends=True),
                    pykotor_ascii.splitlines(keepends=True),
                    fromfile="MDLOps (original)",
                    tofile="MDLOps (PyKotor binary)",
                    lineterm="",
                )
            )

            if diff_lines:
                # Limit diff output to first 50 lines to avoid huge error messages
                diff_preview = "".join(diff_lines[:50])
                if len(diff_lines) > 50:
                    diff_preview += f"\n... ({len(diff_lines) - 50} more lines)"
                return False, f"Mismatch detected:\n{diff_preview}"

            return False, "Files differ but no diff generated"

        except Exception as e:
            return False, f"Comparison error: {e}"


def main():
    # Path relative to tests/python/
    mdlops_exe = Path("vendor/PyKotor/Libraries/PyKotor/src").resolve().parents[3].joinpath("MDLOps/mdlops.exe")
    if not mdlops_exe.exists():
        print(f"MDLOps not found at {mdlops_exe}")
        return

    print("Finding models from game installations...\n")

    # Test K1 models
    print("=" * 60)
    print("K1 (Knights of the Old Republic) Models")
    print("=" * 60)
    k1_models = find_test_models(Game.K1, max_models=50)
    if k1_models:
        print(f"Found {len(k1_models)} K1 models")
        # Randomly sample up to 50 models
        test_count = min(50, len(k1_models))
        random_models = random.sample(k1_models, test_count)
        print(f"Testing {test_count} random models...")
        for mdl_res, mdx_res in random_models:
            model_name = f"{mdl_res.resname()}.{mdl_res.restype().extension}"
            print(f"\nTesting: {model_name}")
            success, msg = test_model(mdl_res, mdx_res, mdlops_exe)
            status = "✓ PASS" if success else f"✗ FAIL: {msg}"
            print(f"  {status}")
    else:
        print("No K1 models found")

    # Test TSL (K2) models
    print("\n" + "=" * 60)
    print("TSL (Knights of the Old Republic II) Models")
    print("=" * 60)
    k2_models = find_test_models(Game.K2, max_models=50)
    if k2_models:
        print(f"Found {len(k2_models)} TSL models")
        # Randomly sample up to 50 models
        test_count = min(50, len(k2_models))
        random_models = random.sample(k2_models, test_count)
        print(f"Testing {test_count} random models...")
        for mdl_res, mdx_res in random_models:
            model_name = f"{mdl_res.resname()}.{mdl_res.restype().extension}"
            print(f"\nTesting: {model_name}")
            success, msg = test_model(mdl_res, mdx_res, mdlops_exe)
            status = "✓ PASS" if success else f"✗ FAIL: {msg}"
            print(f"  {status}")
    else:
        print("No TSL models found")

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"K1 models found: {len(k1_models)}")
    print(f"TSL models found: {len(k2_models)}")


if __name__ == "__main__":
    main()

