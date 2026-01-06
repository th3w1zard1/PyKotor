#!/usr/bin/env python
"""Analyze node offsets and sizes in MDL files."""

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


def analyze_model_header(data: bytes) -> dict:
    """Extract model header fields."""
    result = {}
    result["magic"] = get_uint32(data, 0)
    result["mdl_size"] = get_uint32(data, 4)
    result["mdx_size"] = get_uint32(data, 8)
    result["func_ptr0"] = get_uint32(data, 12)
    result["func_ptr1"] = get_uint32(data, 16)
    result["model_name"] = get_string(data, 20)
    result["root_node_offset"] = get_uint32(data, 52)
    result["node_count"] = get_uint32(data, 56)
    result["offset_to_animations"] = get_uint32(data, 80)
    result["animation_count"] = get_uint32(data, 84)
    result["offset_to_name_offsets"] = get_uint32(data, 180)
    result["name_offsets_count"] = get_uint32(data, 184)
    return result


def calc_mesh_node_data_size(type_id: int, vertex_count: int, face_count: int, 
                              indices_counts_count: int, indices_offsets_count: int, 
                              counters_count: int, game: Game = Game.K1) -> int:
    """Calculate the data size for a mesh node (arrays written after header)."""
    # indices_counts array
    size = indices_counts_count * 4
    # indices_offsets array  
    size += indices_offsets_count * 4
    # inverted_counters array
    size += counters_count * 4
    # faces array (32 bytes each)
    size += face_count * 32
    # vertices array (12 bytes each)
    size += vertex_count * 12
    
    return size


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

    with tempfile.TemporaryDirectory(prefix="mdl_offsets_") as td:
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

        print(f"Model: {model_name}")
        print(f"Original: MDL={len(orig_mdl)}")
        print(f"PyKotor:  MDL={len(pykotor_mdl)}")
        print(f"MDLOps:   MDL={len(mdlops_mdl)}")
        
        # Compare headers
        print("\n=== Model Headers ===")
        orig_hdr = analyze_model_header(orig_mdl)
        pk_hdr = analyze_model_header(pykotor_mdl)
        mo_hdr = analyze_model_header(mdlops_mdl)
        
        print(f"{'Field':<25} {'Original':<15} {'PyKotor':<15} {'MDLOps':<15}")
        for key in ["root_node_offset", "node_count", "offset_to_animations", "animation_count", 
                    "offset_to_name_offsets", "name_offsets_count"]:
            print(f"{key:<25} {orig_hdr[key]:<15} {pk_hdr[key]:<15} {mo_hdr[key]:<15}")
        
        # Analyze where data is placed
        print("\n=== Data Layout ===")
        
        # Name offsets come first after header
        pk_names_start = pk_hdr["offset_to_name_offsets"] + 12
        mo_names_start = mo_hdr["offset_to_name_offsets"] + 12
        pk_names_size = pk_hdr["name_offsets_count"] * 4
        mo_names_size = mo_hdr["name_offsets_count"] * 4
        
        print(f"Name offsets: PyKotor starts at 0x{pk_names_start:X}, MDLOps starts at 0x{mo_names_start:X}")
        
        # Check animations offset
        pk_anims_start = pk_hdr["offset_to_animations"] + 12
        mo_anims_start = mo_hdr["offset_to_animations"] + 12
        
        print(f"Animations: PyKotor starts at 0x{pk_anims_start:X}, MDLOps starts at 0x{mo_anims_start:X}")
        
        # Calculate space between name offsets and animations (this is where names strings are)
        pk_names_str_space = pk_hdr["offset_to_animations"] - (pk_hdr["offset_to_name_offsets"] + pk_names_size)
        mo_names_str_space = mo_hdr["offset_to_animations"] - (mo_hdr["offset_to_name_offsets"] + mo_names_size)
        print(f"Names strings space: PyKotor={pk_names_str_space}, MDLOps={mo_names_str_space}")
        
        # Check root node
        pk_root = pk_hdr["root_node_offset"] + 12
        mo_root = mo_hdr["root_node_offset"] + 12
        print(f"Root node: PyKotor at 0x{pk_root:X}, MDLOps at 0x{mo_root:X}")
        
        # Estimate node data size from file
        # For PyKotor: from root node to name offsets
        pk_node_data_size = pk_hdr["offset_to_name_offsets"] - pk_hdr["root_node_offset"]
        mo_node_data_size = mo_hdr["offset_to_name_offsets"] - mo_hdr["root_node_offset"]
        
        print(f"\nNode data block size: PyKotor={pk_node_data_size}, MDLOps={mo_node_data_size}")
        print(f"Difference: {mo_node_data_size - pk_node_data_size} bytes (MDLOps larger)")
        
        # This difference should account for the vertex data difference
        # Expected: 14484 bytes for 1207 vertices
        print(f"\nExpected vertex data size for 1207 vertices: {1207 * 12} bytes")


if __name__ == "__main__":
    main()

