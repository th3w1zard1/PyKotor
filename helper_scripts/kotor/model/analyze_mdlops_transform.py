#!/usr/bin/env python
"""Analyze what transformations MDLOps makes during ASCII roundtrip.

This script compares the original binary with MDLOps' recompiled binary
to identify what data MDLOps adds, removes, or transforms.
"""

from __future__ import annotations

import struct
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "Libraries" / "PyKotor" / "src"))

from pykotor.common.misc import Game
from pykotor.extract.file import ResourceResult
from pykotor.extract.installation import Installation
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath, find_kotor_paths_from_default


def get_uint32(data: bytes, offset: int) -> int:
    if offset + 4 > len(data):
        return 0
    return struct.unpack_from("<I", data, offset)[0]


def get_uint16(data: bytes, offset: int) -> int:
    if offset + 2 > len(data):
        return 0
    return struct.unpack_from("<H", data, offset)[0]


def analyze_model(data: bytes, label: str):
    """Print key information about a model binary."""
    print(f"\n=== {label} ===")
    print(f"Total size: {len(data)} bytes")
    
    if len(data) < 100:
        print("File too small to analyze")
        return {}
    
    info = {}
    info["mdl_size"] = get_uint32(data, 4)
    info["mdx_size"] = get_uint32(data, 8)
    info["root_node_offset"] = get_uint32(data, 52)
    info["node_count"] = get_uint32(data, 56)
    info["offset_to_super_root"] = get_uint32(data, 180)
    info["offset_to_name_offsets"] = get_uint32(data, 196)
    info["name_offsets_count"] = get_uint32(data, 200)
    
    print(f"MDL data size: {info['mdl_size']}")
    print(f"MDX size: {info['mdx_size']}")
    print(f"Root node offset: {info['root_node_offset']}")
    print(f"Node count: {info['node_count']}")
    print(f"Offset to super root: {info['offset_to_super_root']}")
    print(f"Offset to name offsets: {info['offset_to_name_offsets']}")
    print(f"Name offsets count: {info['name_offsets_count']}")
    
    # Scan first few nodes
    print("\nFirst 3 nodes:")
    root_offset = info["root_node_offset"]
    if root_offset > 0:
        file_pos = root_offset + 12  # Add file header offset
        if file_pos + 80 <= len(data):
            for i in range(min(3, info["node_count"])):
                node_type = get_uint16(data, file_pos)
                node_id = get_uint16(data, file_pos + 4)
                print(f"  Node {i}: type=0x{node_type:04X}, id={node_id}")
                # Calculate approximate next node (basic heuristic)
                base_size = 80  # Node header
                if node_type & 0x20:  # MESH
                    base_size += 332
                if node_type & 0x40:  # SKIN
                    base_size += 100
                file_pos += base_size
    
    return info


def main():
    model_name = "plc_biglight"  # Simple model
    game = Game.K1

    paths: dict[Game, list[CaseAwarePath]] = find_kotor_paths_from_default()
    game_paths = paths.get(game, [])
    if not game_paths:
        print(f"No {game.name} installation found")
        return

    installation: Installation = Installation(game_paths[0])
    mdlops_exe = Path(__file__).parents[3] / "vendor" / "MDLOps" / "mdlops.exe"

    mdl_res: ResourceResult | None = installation.resource(model_name, ResourceType.MDL)
    mdx_res = installation.resource(model_name, ResourceType.MDX)
    if mdl_res is None:
        print(f"Model {model_name} not found")
        return

    orig_mdl = mdl_res.data
    orig_mdx = mdx_res.data if mdx_res else b""

    with tempfile.TemporaryDirectory(prefix="mdl_transform_") as td:
        td_path = Path(td)

        # Write original files
        orig_mdl_path = td_path / f"{model_name}.mdl"
        orig_mdx_path = td_path / f"{model_name}.mdx"
        orig_mdl_path.write_bytes(orig_mdl)
        if orig_mdx:
            orig_mdx_path.write_bytes(orig_mdx)

        # MDLOps decompile
        result = subprocess.run(
            [str(mdlops_exe), str(orig_mdl_path)],
            cwd=str(td_path),
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0:
            print(f"MDLOps decompile failed: {result.stderr.decode()}")
            return

        ascii_path = td_path / f"{model_name}-ascii.mdl"
        if not ascii_path.exists():
            print(f"MDLOps ASCII not found")
            return

        # Show key parts of ASCII output
        ascii_content = ascii_path.read_text(errors="replace")
        lines = ascii_content.split("\n")
        print("\n=== Key ASCII Lines ===")
        for i, line in enumerate(lines[:50]):
            if any(kw in line.lower() for kw in ["node ", "endnode", "bitmap", "render", "shadow", "beaming", "face ", "vertex ", "verts ", "tverts "]):
                print(f"  {i}: {line.strip()}")

        # MDLOps recompile
        result = subprocess.run(
            [str(mdlops_exe), str(ascii_path), "-k1"],
            cwd=str(td_path),
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0:
            print(f"MDLOps compile failed: {result.stderr.decode()}")
            return

        mdlops_mdl_path = td_path / f"{model_name}-ascii-k1-bin.mdl"
        mdlops_mdx_path = td_path / f"{model_name}-ascii-k1-bin.mdx"
        
        if not mdlops_mdl_path.exists():
            print(f"MDLOps binary not found")
            return

        mdlops_mdl = mdlops_mdl_path.read_bytes()
        mdlops_mdx = mdlops_mdx_path.read_bytes() if mdlops_mdx_path.exists() else b""

        # Compare
        orig_info = analyze_model(orig_mdl, "ORIGINAL")
        mdlops_info = analyze_model(mdlops_mdl, "MDLOps ROUNDTRIP")

        # Size comparison
        print("\n=== Size Comparison ===")
        mdl_diff = len(mdlops_mdl) - len(orig_mdl)
        mdx_diff = len(mdlops_mdx) - len(orig_mdx)
        print(f"MDL: Original={len(orig_mdl)}, MDLOps={len(mdlops_mdl)}, Diff={mdl_diff:+d}")
        print(f"MDX: Original={len(orig_mdx)}, MDLOps={len(mdlops_mdx)}, Diff={mdx_diff:+d}")

        # Identify what's different
        print("\n=== Changes Made by MDLOps ===")
        if orig_info.get("node_count") != mdlops_info.get("node_count"):
            print(f"Node count changed: {orig_info.get('node_count')} -> {mdlops_info.get('node_count')}")
        else:
            print(f"Node count unchanged: {orig_info.get('node_count')}")
        
        if mdl_diff > 0:
            print(f"MDL grew by {mdl_diff} bytes - MDLOps added data")
        elif mdl_diff < 0:
            print(f"MDL shrank by {-mdl_diff} bytes - MDLOps removed data")
        else:
            print("MDL size unchanged")


if __name__ == "__main__":
    main()

