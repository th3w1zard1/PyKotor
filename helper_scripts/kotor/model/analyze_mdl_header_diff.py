#!/usr/bin/env python
"""Analyze MDL header differences between PyKotor and MDLOps output."""

from __future__ import annotations

import struct
import subprocess
import sys
import tempfile

from pathlib import Path

from pykotor.extract.file import ResourceResult

sys.path.insert(0, str(Path(__file__).parents[3] / "Libraries" / "PyKotor" / "src"))

from pykotor.common.misc import Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.mdl import read_mdl, write_mdl
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath, find_kotor_paths_from_default


def hex_dump(data: bytes, start: int, length: int, label: str):
    """Print a hex dump of a portion of data."""
    print(f"\n{label} (0x{start:04X} - 0x{start + length - 1:04X}):")
    for i in range(0, length, 16):
        offset = start + i
        chunk = data[start + i : start + i + 16]
        hex_str = " ".join(f"{b:02X}" for b in chunk)
        ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"  {offset:04X}: {hex_str:<48} {ascii_str}")


def analyze_file_header(data: bytes, label: str):
    """Analyze the 12-byte file header."""
    print(f"\n=== {label} File Header (0x00-0x0B) ===")
    # File header is 12 bytes: 3 uint32s
    magic, mdl_size, mdx_size = struct.unpack_from("<3I", data, 0)
    print(f"  Magic:    0x{magic:08X}")
    print(f"  MDL size: {mdl_size} (0x{mdl_size:X})")
    print(f"  MDX size: {mdx_size} (0x{mdx_size:X})")


def analyze_geometry_header(data: bytes, label: str):
    """Analyze the geometry header at offset 12."""
    print(f"\n=== {label} Geometry Header (0x0C+) ===")
    offset = 12
    func_ptr0 = struct.unpack_from("<I", data, offset)[0]
    func_ptr1 = struct.unpack_from("<I", data, offset + 4)[0]
    model_name = data[offset + 8 : offset + 8 + 32].split(b"\x00")[0].decode("ascii", errors="replace")
    root_node_offset = struct.unpack_from("<I", data, offset + 40)[0]
    node_count = struct.unpack_from("<I", data, offset + 44)[0]

    print(f"  func_ptr0: 0x{func_ptr0:08X}")
    print(f"  func_ptr1: 0x{func_ptr1:08X}")
    print(f"  model_name: '{model_name}'")
    print(f"  root_node_offset: {root_node_offset} (in file: {root_node_offset + 12})")
    print(f"  node_count: {node_count}")

    # Alsocheck unknown fields at 0x30-0x40
    print("\n  Bytes 0x30-0x60:")
    for i in range(0x30, 0x60, 4):
        val = struct.unpack_from("<I", data, i)[0]
        print(f"    0x{i:02X}: {val:10} (0x{val:08X})")


def main():
    model_name = "comm_b_f2"
    game = Game.K1

    # Find paths
    paths: dict[Game, list[CaseAwarePath]] = find_kotor_paths_from_default()
    game_paths = paths.get(game, [])
    if not game_paths:
        print(f"No {game.name} installation found")
        return

    installation: Installation = Installation(game_paths[0])
    mdlops_exe = Path(__file__).parents[3] / "vendor" / "MDLOps" / "mdlops.exe"

    # Get original
    mdl_res: ResourceResult | None = installation.resource(model_name, ResourceType.MDL)
    mdx_res = installation.resource(model_name, ResourceType.MDX)
    assert mdl_res is not None
    assert mdx_res is not None

    orig_mdl = mdl_res.data
    orig_mdx = mdx_res.data

    print(f"Model: {model_name}")
    print(f"Original sizes: MDL={len(orig_mdl)}, MDX={len(orig_mdx)}")

    with tempfile.TemporaryDirectory(prefix="mdl_header_") as td:
        td_path = Path(td)

        # Write original
        orig_mdl_path = td_path / f"{model_name}.mdl"
        orig_mdx_path = td_path / f"{model_name}.mdx"
        orig_mdl_path.write_bytes(orig_mdl)
        orig_mdx_path.write_bytes(orig_mdx)

        # PyKotor roundtrip
        mdl_obj = read_mdl(orig_mdl, source_ext=orig_mdx, file_format=ResourceType.MDL)
        pykotor_mdl_path = td_path / f"{model_name}-pykotor.mdl"
        pykotor_mdx_path = td_path / f"{model_name}-pykotor.mdx"
        write_mdl(mdl_obj, pykotor_mdl_path, ResourceType.MDL, target_ext=pykotor_mdx_path)
        pykotor_mdl = pykotor_mdl_path.read_bytes()
        pykotor_mdx = pykotor_mdx_path.read_bytes()

        # MDLOps roundtrip
        result = subprocess.run([str(mdlops_exe), str(orig_mdl_path)], cwd=str(td_path), capture_output=True, timeout=60)
        ascii_path = td_path / f"{model_name}-ascii.mdl"
        if not ascii_path.exists():
            print(f"MDLOps decompile failed: {result.stderr.decode()}")
            print(f"Files created: {list(td_path.iterdir())}")
            return

        result = subprocess.run([str(mdlops_exe), str(ascii_path), "-k1"], cwd=str(td_path), capture_output=True, timeout=60)

        # Find the output files - MDLOps produces *-k1-bin.mdl files
        files_after = list(td_path.iterdir())
        print(f"Files after MDLOps compile: {[f.name for f in files_after]}")
        
        mdlops_mdl_path = td_path / f"{model_name}-ascii-k1-bin.mdl"
        mdlops_mdx_path = td_path / f"{model_name}-ascii-k1-bin.mdx"
        
        if not mdlops_mdl_path.exists():
            print(f"MDLOps compile failed to produce MDL. stderr: {result.stderr.decode()}")
            return

        mdlops_mdl = mdlops_mdl_path.read_bytes()
        mdlops_mdx = mdlops_mdx_path.read_bytes() if mdlops_mdx_path and mdlops_mdx_path.exists() else b""

        print("\nOutput sizes:")
        print(f"  PyKotor: MDL={len(pykotor_mdl)}, MDX={len(pykotor_mdx)}")
        print(f"  MDLOps:  MDL={len(mdlops_mdl)}, MDX={len(mdlops_mdx)}")

        # Analyze headers
        analyze_file_header(pykotor_mdl, "PyKotor")
        analyze_file_header(mdlops_mdl, "MDLOps")

        analyze_geometry_header(pykotor_mdl, "PyKotor")
        analyze_geometry_header(mdlops_mdl, "MDLOps")

        # Show raw hex comparison of first 256 bytes
        print("\n=== First 256 bytes comparison ===")
        print("\nPyKotor MDL:")
        hex_dump(pykotor_mdl, 0, 256, "PyKotor")
        print("\nMDLOps MDL:")
        hex_dump(mdlops_mdl, 0, 256, "MDLOps")


if __name__ == "__main__":
    main()
