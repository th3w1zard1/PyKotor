#!/usr/bin/env python
"""Analyze all nodes in a model comparing PyKotor vs MDLOps output."""

from __future__ import annotations

import struct
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


def get_uint32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def get_uint16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def get_string(data: bytes, offset: int, length: int = 32) -> str:
    return data[offset : offset + length].split(b"\x00")[0].decode("ascii", errors="replace")


def analyze_node(data: bytes, offset: int) -> dict:
    """Analyze a node at given file offset."""
    result = {}
    result["type_id"] = get_uint16(data, offset)
    result["node_id"] = get_uint16(data, offset + 4)
    result["name_id"] = get_uint16(data, offset + 6)
    result["offset_to_children"] = get_uint32(data, offset + 44)
    result["children_count"] = get_uint32(data, offset + 48)
    
    # If mesh node (type & 32)
    if result["type_id"] & 32:
        tm_offset = offset + 80  # After 80-byte node header
        result["face_count"] = get_uint32(data, tm_offset + 232)
        result["vertex_count"] = get_uint32(data, tm_offset + 252)
        result["vertices_offset"] = get_uint32(data, tm_offset + 248)
        result["offset_to_faces"] = get_uint32(data, tm_offset + 228)
        result["mdx_data_size"] = get_uint32(data, tm_offset + 308)
        result["mdx_data_bitmap"] = get_uint32(data, tm_offset + 312)
        result["mdx_data_offset"] = get_uint32(data, tm_offset + 316)
        result["texture1"] = get_string(data, tm_offset + 52)
    
    return result


def traverse_nodes_linear(data: bytes, start_offset: int, node_count: int) -> list[tuple[int, dict]]:
    """Traverse nodes linearly through the file, collecting all nodes."""
    nodes = []
    # Find all mesh nodes by scanning the MDL linearly
    # Nodes are typically laid out contiguously after the header
    offset = start_offset + 12  # Add 12 for file header offset
    
    for i in range(node_count):
        if offset >= len(data):
            break
        try:
            node_info = analyze_node(data, offset)
            nodes.append((offset, node_info))
            
            # Calculate next node offset based on current node type
            next_offset = offset + 80  # Base node header
            if node_info["type_id"] & 32:  # Mesh
                # Trimesh header size varies by game/node type
                # K1 trimesh: 332 bytes, K2: 340 bytes
                # Add variable-length arrays too
                next_offset += 332
            if node_info["type_id"] & 64:  # Light
                next_offset += 92
            if node_info["type_id"] & 128:  # Emitter
                next_offset += 224
            if node_info["type_id"] & 256:  # Reference
                next_offset += 68
            if node_info["type_id"] & 512:  # Skin
                next_offset += 116  # Plus variable-length arrays
            
            # This is a simplified calculation - actual node traversal should use the children pointers
            # For now, we'll just skip ahead to scan more nodes
            offset = next_offset
        except Exception as e:
            print(f"Error at offset {offset}: {e}")
            offset += 80  # Try to skip ahead
    
    return nodes


def scan_all_mesh_nodes(data: bytes, max_scan: int = 200000) -> list[tuple[int, dict]]:
    """Scan binary for mesh nodes by looking for trimesh patterns."""
    nodes = []
    # Mesh nodes have type_id with bit 5 set (0x20 = 32)
    # Try to find mesh node headers by scanning for valid type patterns
    offset = 620  # Start after typical header (file header + geometry header + name offsets)
    
    while offset < min(len(data) - 400, max_scan):
        try:
            type_id = get_uint16(data, offset)
            # Check if this looks like a valid mesh node (type has MESH flag)
            if type_id & 32 and type_id < 0x1000:  # Reasonable type ID
                node_info = analyze_node(data, offset)
                # Validate by checking vertex count is reasonable
                if node_info.get("vertex_count", 0) < 100000:
                    nodes.append((offset, node_info))
        except:
            pass
        offset += 4  # Scan in 4-byte increments
    
    return nodes


def main():
    model_name = "comm_b_f2"
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
    assert mdl_res is not None and mdx_res is not None

    orig_mdl = mdl_res.data
    orig_mdx = mdx_res.data

    with tempfile.TemporaryDirectory(prefix="mdl_nodes_") as td:
        td_path = Path(td)

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

        # MDLOps roundtrip
        subprocess.run([str(mdlops_exe), str(orig_mdl_path)], cwd=str(td_path), capture_output=True, timeout=60)
        subprocess.run([str(mdlops_exe), str(td_path / f"{model_name}-ascii.mdl"), "-k1"], cwd=str(td_path), capture_output=True, timeout=60)
        mdlops_mdl = (td_path / f"{model_name}-ascii-k1-bin.mdl").read_bytes()

        # Get root offset and node count
        pk_root = get_uint32(pykotor_mdl, 52)
        pk_nodes = get_uint32(pykotor_mdl, 56)
        mo_root = get_uint32(mdlops_mdl, 52)
        mo_nodes = get_uint32(mdlops_mdl, 56)

        print(f"Model: {model_name}")
        print(f"PyKotor: MDL={len(pykotor_mdl)}, root_offset={pk_root}, nodes={pk_nodes}")
        print(f"MDLOps:  MDL={len(mdlops_mdl)}, root_offset={mo_root}, nodes={mo_nodes}")

        # Compare mesh nodes
        print("\n=== Mesh Nodes Comparison ===")
        print(f"{'NodeID':<8} {'Type':<6} {'Verts(PK)':<12} {'Verts(MO)':<12} {'VOffset(PK)':<12} {'VOffset(MO)':<12} {'FaceOff(PK)':<12} {'FaceOff(MO)':<12}")
        
        pk_nodes_list = traverse_nodes(pykotor_mdl, pk_root, pk_nodes)
        mo_nodes_list = traverse_nodes(mdlops_mdl, mo_root, mo_nodes)
        
        total_pk_verts = 0
        total_mo_verts = 0
        total_pk_vbytes = 0
        total_mo_vbytes = 0
        
        for i, (pk_off, pk_info) in enumerate(pk_nodes_list):
            if pk_info["type_id"] & 32:  # Mesh node
                mo_info = mo_nodes_list[i][1] if i < len(mo_nodes_list) else {}
                
                pk_vcount = pk_info.get("vertex_count", 0)
                mo_vcount = mo_info.get("vertex_count", 0)
                pk_voff = pk_info.get("vertices_offset", 0)
                mo_voff = mo_info.get("vertices_offset", 0)
                pk_foff = pk_info.get("offset_to_faces", 0)
                mo_foff = mo_info.get("offset_to_faces", 0)
                
                total_pk_verts += pk_vcount
                total_mo_verts += mo_vcount
                
                # Only count vertex bytes if vertices_offset is set (means vertices in MDL)
                if pk_voff > 0:
                    total_pk_vbytes += pk_vcount * 12
                if mo_voff > 0:
                    total_mo_vbytes += mo_vcount * 12
                
                marker = "" if pk_voff == mo_voff else " <-- DIFF"
                print(f"{pk_info['node_id']:<8} 0x{pk_info['type_id']:04X} {pk_vcount:<12} {mo_vcount:<12} {pk_voff:<12} {mo_voff:<12} {pk_foff:<12} {mo_foff:<12}{marker}")
        
        print(f"\nTotal vertices: PyKotor={total_pk_verts}, MDLOps={total_mo_verts}")
        print(f"Total vertex bytes in MDL: PyKotor={total_pk_vbytes}, MDLOps={total_mo_vbytes}")
        print(f"Difference in MDL vertex bytes: {total_mo_vbytes - total_pk_vbytes}")


if __name__ == "__main__":
    main()

