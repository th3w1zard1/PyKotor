#!/usr/bin/env python
"""Detailed analysis of MDL/MDX differences between PyKotor and MDLOps."""

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


def hex_line(data: bytes, start: int, length: int = 16) -> str:
    """Format a single line of hex dump."""
    chunk = data[start : start + length]
    hex_str = " ".join(f"{b:02X}" for b in chunk)
    return f"{start:06X}: {hex_str}"


def analyze_node_at_offset(data: bytes, offset: int, label: str) -> dict:
    """Analyze a node header at a given offset."""
    result = {}
    # Node header: 80 bytes
    # ushort type_id, ushort padding0, ushort node_id, ushort name_id
    # uint32 offset_to_root, offset_to_parent
    # float[3] position, float[4] orientation
    # uint32 offset_to_children, children_count, children_count2
    # uint32 offset_to_controllers, controller_count, controller_count2
    # uint32 offset_to_controller_data, controller_data_length, controller_data_length2

    result["type_id"] = struct.unpack_from("<H", data, offset)[0]
    result["node_id"] = struct.unpack_from("<H", data, offset + 4)[0]
    result["name_id"] = struct.unpack_from("<H", data, offset + 6)[0]
    result["offset_to_root"] = struct.unpack_from("<I", data, offset + 8)[0]
    result["offset_to_parent"] = struct.unpack_from("<I", data, offset + 12)[0]
    result["position"] = struct.unpack_from("<fff", data, offset + 16)
    result["orientation"] = struct.unpack_from("<ffff", data, offset + 28)
    result["offset_to_children"] = struct.unpack_from("<I", data, offset + 44)[0]
    result["children_count"] = struct.unpack_from("<I", data, offset + 48)[0]
    result["offset_to_controllers"] = struct.unpack_from("<I", data, offset + 56)[0]
    result["controller_count"] = struct.unpack_from("<I", data, offset + 60)[0]
    result["offset_to_controller_data"] = struct.unpack_from("<I", data, offset + 68)[0]
    result["controller_data_length"] = struct.unpack_from("<I", data, offset + 72)[0]

    return result


def analyze_trimesh_at_offset(data: bytes, offset: int, label: str) -> dict:
    """Analyze a trimesh header at a given offset (after node header)."""
    result = {}
    # Trimesh header key offsets (relative to trimesh header start, which is after 80-byte node header)
    # Based on MDLOps structs:
    # offset_to_faces at subhead offset 228
    # face_count at subhead offset 232
    # vertices_offset at subhead offset 248
    # vertex_count at subhead offset 252
    # mdx_data_size at subhead offset 308
    # mdx_data_bitmap at subhead offset 312

    result["offset_to_faces"] = struct.unpack_from("<I", data, offset + 228)[0]
    result["face_count"] = struct.unpack_from("<I", data, offset + 232)[0]
    result["vertices_offset"] = struct.unpack_from("<I", data, offset + 248)[0]
    result["vertex_count"] = struct.unpack_from("<I", data, offset + 252)[0]
    result["texture1"] = data[offset + 52 : offset + 52 + 32].split(b"\x00")[0].decode("ascii", errors="replace")
    result["texture2"] = data[offset + 84 : offset + 84 + 32].split(b"\x00")[0].decode("ascii", errors="replace")
    result["mdx_data_size"] = struct.unpack_from("<I", data, offset + 308)[0]
    result["mdx_data_bitmap"] = struct.unpack_from("<I", data, offset + 312)[0]
    result["mdx_data_offset"] = struct.unpack_from("<I", data, offset + 316)[0]
    result["mdx_vertex_offset"] = struct.unpack_from("<I", data, offset + 320)[0]

    return result


def find_root_node_offset(data: bytes) -> int:
    """Find the root node offset from the geometry header."""
    # At file offset 12 + 40 = 52 (geometry header has func_ptr0, func_ptr1, model_name[32], root_node_offset)
    return struct.unpack_from("<I", data, 52)[0]


def get_node_count(data: bytes) -> int:
    """Get node count from geometry header."""
    return struct.unpack_from("<I", data, 56)[0]


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
    print(f"Original: MDL={len(orig_mdl)}, MDX={len(orig_mdx)}")

    with tempfile.TemporaryDirectory(prefix="mdl_analyze_") as td:
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
            return

        result = subprocess.run([str(mdlops_exe), str(ascii_path), "-k1"], cwd=str(td_path), capture_output=True, timeout=60)
        mdlops_mdl_path = td_path / f"{model_name}-ascii-k1-bin.mdl"
        mdlops_mdx_path = td_path / f"{model_name}-ascii-k1-bin.mdx"

        if not mdlops_mdl_path.exists():
            print(f"MDLOps compile failed: {result.stderr.decode()}")
            return

        mdlops_mdl = mdlops_mdl_path.read_bytes()
        mdlops_mdx = mdlops_mdx_path.read_bytes() if mdlops_mdx_path.exists() else b""

        print(f"PyKotor: MDL={len(pykotor_mdl)}, MDX={len(pykotor_mdx)}")
        print(f"MDLOps:  MDL={len(mdlops_mdl)}, MDX={len(mdlops_mdx)}")

        # Compare file headers
        print("\n=== File Header (0x00-0x0B) ===")
        print(f"{'Field':<20} {'PyKotor':<15} {'MDLOps':<15} {'Match'}")
        for name, offset in [("Magic", 0), ("MDL Size", 4), ("MDX Size", 8)]:
            pk_val = struct.unpack_from("<I", pykotor_mdl, offset)[0]
            mo_val = struct.unpack_from("<I", mdlops_mdl, offset)[0]
            match = "YES" if pk_val == mo_val else "NO"
            print(f"{name:<20} {pk_val:<15} {mo_val:<15} {match}")

        # Compare geometry headers
        print("\n=== Geometry Header ===")
        pk_root = find_root_node_offset(pykotor_mdl)
        mo_root = find_root_node_offset(mdlops_mdl)
        pk_nodes = get_node_count(pykotor_mdl)
        mo_nodes = get_node_count(mdlops_mdl)
        print(f"{'Field':<20} {'PyKotor':<15} {'MDLOps':<15} {'Match'}")
        print(f"{'Root Node Offset':<20} {pk_root:<15} {mo_root:<15} {'YES' if pk_root == mo_root else 'NO'}")
        print(f"{'Node Count':<20} {pk_nodes:<15} {mo_nodes:<15} {'YES' if pk_nodes == mo_nodes else 'NO'}")

        # Get model name
        pk_name = pykotor_mdl[20:52].split(b"\x00")[0].decode("ascii", errors="replace")
        mo_name = mdlops_mdl[20:52].split(b"\x00")[0].decode("ascii", errors="replace")
        print(f"{'Model Name':<20} {pk_name:<15} {mo_name:<15} {'YES' if pk_name == mo_name else 'NO'}")

        # Analyze first mesh node (root node + 12 for file header offset)
        print("\n=== Root Node Analysis ===")
        pk_root_file = pk_root + 12
        mo_root_file = mo_root + 12

        pk_node = analyze_node_at_offset(pykotor_mdl, pk_root_file, "PyKotor")
        mo_node = analyze_node_at_offset(mdlops_mdl, mo_root_file, "MDLOps")

        print(f"{'Field':<25} {'PyKotor':<15} {'MDLOps':<15} {'Match'}")
        for key in ["type_id", "node_id", "offset_to_children", "children_count", "offset_to_controllers", "controller_count"]:
            pk_val = pk_node[key]
            mo_val = mo_node[key]
            match = "YES" if pk_val == mo_val else "NO"
            print(f"{key:<25} {pk_val:<15} {mo_val:<15} {match}")

        # If it's a mesh node (type & 32), analyze trimesh header
        if pk_node["type_id"] & 32:
            print("\n=== Root Trimesh Header ===")
            pk_tm = analyze_trimesh_at_offset(pykotor_mdl, pk_root_file + 80, "PyKotor")
            mo_tm = analyze_trimesh_at_offset(mdlops_mdl, mo_root_file + 80, "MDLOps")

            print(f"{'Field':<25} {'PyKotor':<15} {'MDLOps':<15} {'Match'}")
            for key in ["vertex_count", "face_count", "vertices_offset", "offset_to_faces", "mdx_data_size", "mdx_data_bitmap", "mdx_data_offset", "texture1"]:
                pk_val = pk_tm[key]
                mo_val = mo_tm[key]
                match = "YES" if pk_val == mo_val else "NO"
                if isinstance(pk_val, int):
                    print(f"{key:<25} {pk_val:<15} {mo_val:<15} {match}")
                else:
                    print(f"{key:<25} {str(pk_val):<15} {str(mo_val):<15} {match}")

            # Show hex representation of bitmap
            print(f"\n  PyKotor bitmap: 0x{pk_tm['mdx_data_bitmap']:08X}")
            print(f"  MDLOps bitmap:  0x{mo_tm['mdx_data_bitmap']:08X}")

        # Find first difference in MDL
        print("\n=== First MDL Byte Difference ===")
        min_len = min(len(pykotor_mdl), len(mdlops_mdl))
        for i in range(min_len):
            if pykotor_mdl[i] != mdlops_mdl[i]:
                print(f"First diff at offset 0x{i:X}")
                print(f"  PyKotor: {hex_line(pykotor_mdl, max(0, i - 8), 32)}")
                print(f"  MDLOps:  {hex_line(mdlops_mdl, max(0, i - 8), 32)}")
                break

        # Calculate total vertex bytes
        total_vertices = 0
        for node in mdl_obj.all_nodes():
            if node.mesh and node.mesh.vertex_positions:
                total_vertices += len(node.mesh.vertex_positions)
        print("\n=== Vertex Summary ===")
        print(f"Total vertices in model: {total_vertices}")
        print(f"Total vertex bytes (12 per vertex): {total_vertices * 12}")
        print(f"MDL size difference: {len(mdlops_mdl) - len(pykotor_mdl)}")
        print(f"MDX size difference: {len(mdlops_mdx) - len(pykotor_mdx)}")


if __name__ == "__main__":
    main()
