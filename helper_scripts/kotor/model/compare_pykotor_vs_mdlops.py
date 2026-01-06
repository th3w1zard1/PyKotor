#!/usr/bin/env python
"""Compare PyKotor binary output vs MDLOps binary output for a model.

This script:
1. Reads an original MDL/MDX with PyKotor
2. Writes it back with PyKotor
3. Uses MDLOps to decompile original to ASCII, then recompile to binary
4. Compares PyKotor output vs MDLOps output byte-by-byte
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "Libraries" / "PyKotor" / "src"))

from pykotor.common.misc import Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.mdl import read_mdl, write_mdl
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath, find_kotor_paths_from_default
from pykotor.extract.file import ResourceResult


def find_mdlops_exe() -> Path | None:
    """Find mdlops.exe in vendor directory."""
    # scripts/kotor/model/ -> repo root is 3 levels up
    repo_root = Path(__file__).parents[3]
    mdlops_path = repo_root / "vendor" / "MDLOps" / "mdlops.exe"
    if mdlops_path.exists():
        return mdlops_path
    return None


def compare_binaries(a: bytes, b: bytes, name: str, verbose: bool = False) -> list[str]:
    """Compare two binary blobs and return list of differences."""
    import struct
    
    diffs = []
    if len(a) != len(b):
        diffs.append(f"{name} size mismatch: {len(a)} vs {len(b)}")
    
    min_len = min(len(a), len(b))
    diff_count = 0
    first_diff_offset = None
    diff_ranges = []
    current_range_start = None
    
    for i in range(min_len):
        if a[i] != b[i]:
            diff_count += 1
            if first_diff_offset is None:
                first_diff_offset = i
            if current_range_start is None:
                current_range_start = i
        else:
            if current_range_start is not None:
                diff_ranges.append((current_range_start, i - 1))
                current_range_start = None
    
    if current_range_start is not None:
        diff_ranges.append((current_range_start, min_len - 1))
    
    if diff_count > 0:
        diffs.append(f"{name} has {diff_count} byte differences (first at offset 0x{first_diff_offset:X})")
        
        if verbose:
            for start, end in diff_ranges[:10]:
                length = end - start + 1
                diffs.append(f"  Diff range: 0x{start:X}-0x{end:X} ({length} bytes)")
                # Show first 8 bytes of each range
                show_bytes = min(8, length)
                a_bytes = " ".join(f"{a[start+j]:02X}" for j in range(show_bytes))
                b_bytes = " ".join(f"{b[start+j]:02X}" for j in range(show_bytes))
                diffs.append(f"    PyKotor:  {a_bytes}")
                diffs.append(f"    MDLOps:   {b_bytes}")
    
    return diffs


def compare_model(
    model_name: str,
    game: Game,
    mdlops_exe: Path,
    verbose: bool = False,
) -> tuple[bool, list[str]]:
    """Compare PyKotor vs MDLOps output for a model.

    Returns (success, list of difference messages).
    """
    messages: list[str] = []

    # Find game installation
    paths: dict[Game, list[CaseAwarePath]] = find_kotor_paths_from_default()
    game_paths: list[CaseAwarePath] = paths.get(game, [])
    if not game_paths:
        return False, [f"No {game.name} installation found"]

    installation: Installation = Installation(game_paths[0])

    # Get model resources
    mdl_res: ResourceResult | None = installation.resource(model_name, ResourceType.MDL)
    mdx_res: ResourceResult | None = installation.resource(model_name, ResourceType.MDX)

    if mdl_res is None:
        return False, [f"MDL resource '{model_name}' not found"]
    if mdx_res is None:
        return False, [f"MDX resource '{model_name}' not found"]

    orig_mdl = mdl_res.data
    orig_mdx = mdx_res.data

    if verbose:
        print(f"Original MDL: {len(orig_mdl)} bytes")
        print(f"Original MDX: {len(orig_mdx)} bytes")

    with tempfile.TemporaryDirectory(prefix="mdl_compare_") as td:
        td_path = Path(td)

        # Write original to temp dir
        orig_mdl_path = td_path / f"{model_name}.mdl"
        orig_mdx_path = td_path / f"{model_name}.mdx"
        orig_mdl_path.write_bytes(orig_mdl)
        orig_mdx_path.write_bytes(orig_mdx)

        # Step 1: Read with PyKotor and write back
        try:
            mdl_obj = read_mdl(orig_mdl, source_ext=orig_mdx, file_format=ResourceType.MDL)
        except Exception as e:
            return False, [f"PyKotor read failed: {e}"]

        pykotor_mdl_path = td_path / f"{model_name}-pykotor.mdl"
        pykotor_mdx_path = td_path / f"{model_name}-pykotor.mdx"

        try:
            write_mdl(mdl_obj, pykotor_mdl_path, ResourceType.MDL, target_ext=pykotor_mdx_path)
        except Exception as e:
            return False, [f"PyKotor write failed: {e}"]

        pykotor_mdl = pykotor_mdl_path.read_bytes()
        pykotor_mdx = pykotor_mdx_path.read_bytes()

        if verbose:
            print(f"PyKotor MDL: {len(pykotor_mdl)} bytes")
            print(f"PyKotor MDX: {len(pykotor_mdx)} bytes")

        # Step 2: Use MDLOps to decompile original to ASCII
        result = subprocess.run(
            [str(mdlops_exe), str(orig_mdl_path)],
            cwd=str(td_path),
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            return False, [f"MDLOps decompile failed: {result.stderr}"]

        ascii_path = td_path / f"{model_name}-ascii.mdl"
        if not ascii_path.exists():
            return False, ["MDLOps did not produce ASCII output"]

        # Step 3: Use MDLOps to recompile ASCII to binary
        mdlops_args = [str(mdlops_exe), str(ascii_path)]
        if game == Game.K1:
            mdlops_args.append("-k1")
        elif game == Game.K2:
            mdlops_args.append("-k2")

        result = subprocess.run(
            mdlops_args,
            cwd=str(td_path),
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            return False, [f"MDLOps recompile failed: {result.stderr}"]

        # MDLOps output files - MDLOps creates *-ascii-{k1|k2}-bin.{mdl|mdx}
        game_suffix = "k1" if game == Game.K1 else "k2"
        mdlops_mdl_path = td_path / f"{model_name}-ascii-{game_suffix}-bin.mdl"
        mdlops_mdx_path = td_path / f"{model_name}-ascii-{game_suffix}-bin.mdx"
        
        if not mdlops_mdl_path.exists():
            # List files for debugging
            files = [f.name for f in td_path.iterdir()]
            return False, [f"MDLOps did not produce binary output. Files in dir: {files}"]

        mdlops_mdl = mdlops_mdl_path.read_bytes()
        mdlops_mdx = mdlops_mdx_path.read_bytes() if mdlops_mdx_path.exists() else b""

        if verbose:
            print(f"MDLOps MDL: {len(mdlops_mdl)} bytes")
            print(f"MDLOps MDX: {len(mdlops_mdx)} bytes")

        # Step 4: Compare PyKotor vs MDLOps
        diffs = []
        diffs.extend(compare_binaries(pykotor_mdl, mdlops_mdl, "MDL", verbose))
        diffs.extend(compare_binaries(pykotor_mdx, mdlops_mdx, "MDX", verbose))

        if diffs:
            messages.extend(diffs)

            # Additional analysis
            messages.append("\nSize comparison:")
            messages.append(f"  Original MDL: {len(orig_mdl)}, MDX: {len(orig_mdx)}")
            messages.append(f"  PyKotor  MDL: {len(pykotor_mdl)}, MDX: {len(pykotor_mdx)}")
            messages.append(f"  MDLOps   MDL: {len(mdlops_mdl)}, MDX: {len(mdlops_mdx)}")
            messages.append(f"  PyKotor vs MDLOps MDL diff: {len(pykotor_mdl) - len(mdlops_mdl)}")
            messages.append(f"  PyKotor vs MDLOps MDX diff: {len(pykotor_mdx) - len(mdlops_mdx)}")

            return False, messages

        return True, ["Binary output matches MDLOps"]


def main():
    parser = argparse.ArgumentParser(description="Compare PyKotor vs MDLOps model output")
    parser.add_argument("model_name", help="Model name (without extension)")
    parser.add_argument("-g", "--game", choices=["k1", "k2"], default="k1", help="Game version")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    game = Game.K1 if args.game == "k1" else Game.K2

    mdlops_exe = find_mdlops_exe()
    if mdlops_exe is None:
        print("ERROR: mdlops.exe not found in vendor/MDLOps/")
        sys.exit(1)

    print(f"Comparing model '{args.model_name}' ({game.name})...")
    success, messages = compare_model(args.model_name, game, mdlops_exe, args.verbose)

    for msg in messages:
        print(msg)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
