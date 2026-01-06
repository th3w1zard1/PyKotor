#!/usr/bin/env python
"""Analyze and compare the file layout between PyKotor and MDLOps outputs.

This script helps identify WHY the file layouts differ, focusing on:
1. Node ordering
2. Node data sizes
3. Vertex data placement (MDL vs MDX)
4. Missing or extra data sections
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
from pykotor.resource.formats.mdl import read_mdl, write_mdl
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath, find_kotor_paths_from_default


def get_uint32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def get_uint16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def scan_nodes(data: bytes, start_offset: int, node_count: int) -> list[dict]:
    """Scan node headers in the binary to extract key info."""
    nodes = []
    offset = start_offset + 12  # Add 12 for file header

    for _ in range(min(node_count, 50)):  # Limit to prevent runaway
        if offset + 80 > len(data):
            break

        node_type = get_uint16(data, offset)
        if node_type == 0 or node_type > 0x1000:
            break  # Invalid node type, stop scanning

        node_id = get_uint16(data, offset + 4)
        name_id = get_uint16(data, offset + 6)
        children_count = get_uint32(data, offset + 48)
        children_offset = get_uint32(data, offset + 52)

        nodes.append(
            {
                "offset": offset,
                "type": node_type,
                "node_id": node_id,
                "name_id": name_id,
                "children_count": children_count,
                "children_offset": children_offset,
            }
        )

        # Calculate approximate node size based on type
        base_size = 80  # Basic node header
        if node_type & 0x20:  # Has mesh
            base_size += 332  # Trimesh header (approximate)
        if node_type & 0x40:  # Skin
            base_size += 100

        offset += base_size

    return nodes


def main():
    model_name = "plc_biglight"  # Simple model for testing
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

    print(f"Model: {model_name}")
    print(f"Original: MDL={len(orig_mdl)}, MDX={len(orig_mdx)}")

    with tempfile.TemporaryDirectory(prefix="mdl_layout_") as td:
        td_path = Path(td)

        orig_mdl_path = td_path / f"{model_name}.mdl"
        orig_mdx_path = td_path / f"{model_name}.mdx"
        orig_mdl_path.write_bytes(orig_mdl)
        if orig_mdx:
            orig_mdx_path.write_bytes(orig_mdx)

        # PyKotor roundtrip
        mdl_obj = read_mdl(orig_mdl, source_ext=orig_mdx or None, file_format=ResourceType.MDL)
        pykotor_mdl_path = td_path / f"{model_name}-pykotor.mdl"
        pykotor_mdx_path = td_path / f"{model_name}-pykotor.mdx"
        write_mdl(mdl_obj, pykotor_mdl_path, ResourceType.MDL, target_ext=pykotor_mdx_path)
        pykotor_mdl = pykotor_mdl_path.read_bytes()
        pykotor_mdx = pykotor_mdx_path.read_bytes()

        # MDLOps roundtrip
        result = subprocess.run(
            [str(mdlops_exe), str(orig_mdl_path)],
            cwd=str(td_path),
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0:
            print(f"MDLOps decompile failed: {result.stderr.decode()}")
            return

        result = subprocess.run(
            [str(mdlops_exe), str(td_path / f"{model_name}-ascii.mdl"), "-k1"],
            cwd=str(td_path),
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0:
            print(f"MDLOps compile failed: {result.stderr.decode()}")
            return

        mdlops_mdl = (td_path / f"{model_name}-ascii-k1-bin.mdl").read_bytes()
        mdlops_mdx = (td_path / f"{model_name}-ascii-k1-bin.mdx").read_bytes()

        print(f"PyKotor: MDL={len(pykotor_mdl)}, MDX={len(pykotor_mdx)}")
        print(f"MDLOps:  MDL={len(mdlops_mdl)}, MDX={len(mdlops_mdx)}")

        # Size differences
        print("\n=== Size Analysis ===")
        mdl_diff = len(pykotor_mdl) - len(mdlops_mdl)
        mdx_diff = len(pykotor_mdx) - len(mdlops_mdx)
        print(f"MDL difference: {mdl_diff:+d} bytes (PyKotor - MDLOps)")
        print(f"MDX difference: {mdx_diff:+d} bytes (PyKotor - MDLOps)")

        # Key header values
        print("\n=== Header Comparison ===")
        pk_root = get_uint32(pykotor_mdl, 52)
        mo_root = get_uint32(mdlops_mdl, 52)
        pk_count = get_uint32(pykotor_mdl, 56)
        mo_count = get_uint32(mdlops_mdl, 56)
        pk_super = get_uint32(pykotor_mdl, 180)
        mo_super = get_uint32(mdlops_mdl, 180)

        print(f"root_node_offset: PyKotor={pk_root}, MDLOps={mo_root}")
        print(f"node_count:       PyKotor={pk_count}, MDLOps={mo_count}")
        print(f"offset_to_super_root: PyKotor={pk_super}, MDLOps={mo_super}")

        # Scan first few nodes
        print("\n=== First 10 Nodes Comparison ===")
        print("PyKotor nodes:")
        pk_nodes = scan_nodes(pykotor_mdl, pk_root, pk_count)
        for n in pk_nodes[:10]:
            print(f"  offset={n['offset']:5d}, type=0x{n['type']:04X}, id={n['node_id']:2d}, name_id={n['name_id']:2d}")

        print("\nMDLOps nodes:")
        mo_nodes = scan_nodes(mdlops_mdl, mo_root, mo_count)
        for n in mo_nodes[:10]:
            print(f"  offset={n['offset']:5d}, type=0x{n['type']:04X}, id={n['node_id']:2d}, name_id={n['name_id']:2d}")

        # Find neck_g in both
        print("\n=== neck_g Node Location ===")
        for nodes, label in [(pk_nodes, "PyKotor"), (mo_nodes, "MDLOps")]:
            for n in nodes:
                if n["name_id"] == 6:  # neck_g has node_id=6 which typically equals name_id
                    print(f"{label}: neck_g at offset {n['offset']}")
                    break

        # Check MDL nodes with trimesh for vertex data
        print("\n=== Trimesh Node Analysis (first 5 mesh nodes) ===")
        mesh_count = 0
        for nodes, data, label in [(pk_nodes, pykotor_mdl, "PyKotor"), (mo_nodes, mdlops_mdl, "MDLOps")]:
            print(f"\n{label}:")
            for n in nodes:
                if n["type"] & 0x20 and mesh_count < 5:  # Has mesh
                    # Read trimesh header fields
                    # Trimesh header starts after base node header (80 bytes)
                    trimesh_offset = n["offset"] + 80
                    if trimesh_offset + 332 <= len(data):
                        # vertices_offset is at trimesh+228
                        vertices_offset = get_uint32(data, trimesh_offset + 228)
                        vertex_count = get_uint32(data, trimesh_offset + 232)
                        # mdx_data_offset is at trimesh+324
                        mdx_offset = get_uint32(data, trimesh_offset + 324)
                        mdx_size = get_uint32(data, trimesh_offset + 328)

                        print(f"  Node type=0x{n['type']:04X} id={n['node_id']:2d}:")
                        print(f"    vertices_offset={vertices_offset}, vertex_count={vertex_count}")
                        print(f"    mdx_data_offset={mdx_offset}, mdx_data_size={mdx_size}")
            mesh_count = 0  # Reset for next iteration


if __name__ == "__main__":
    main()
