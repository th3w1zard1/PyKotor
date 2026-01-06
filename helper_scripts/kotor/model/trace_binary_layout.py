#!/usr/bin/env python
"""Trace the binary layout of MDL files to understand where data is placed."""

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


def find_node_type_locations(data: bytes) -> list[tuple[int, int, int]]:
    """Scan for node headers by looking for valid node type patterns."""
    locations = []
    # Node headers have type_id at offset 0 (uint16)
    # Valid types: 1, 33, 97, 161, 289, 545, etc.
    valid_base_types = {1, 33, 97, 161, 289, 545, 2081}
    
    for offset in range(200, len(data) - 80, 4):  # Start after header, align to 4 bytes
        type_id = get_uint16(data, offset)
        # Check if this looks like a valid node header
        if type_id in valid_base_types or (type_id & 0x20 and type_id < 0x1000):
            # Check if node_id and name_id are reasonable
            node_id = get_uint16(data, offset + 4)
            name_id = get_uint16(data, offset + 6)
            if node_id < 1000 and name_id < 1000:
                # Check if children count is reasonable
                children_count = get_uint32(data, offset + 48)
                if children_count < 100:
                    locations.append((offset, type_id, node_id))
    
    return locations


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

    with tempfile.TemporaryDirectory(prefix="mdl_layout_") as td:
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
        
        # Extract key layout values
        print("\n=== Key Layout Offsets ===")
        
        # From model header (file position 12+)
        # Geometry header: root_node_offset at pos 12+40=52, node_count at 12+44=56
        pk_root = get_uint32(pykotor_mdl, 52)
        mo_root = get_uint32(mdlops_mdl, 52)
        print(f"root_node_offset: PyKotor={pk_root}, MDLOps={mo_root}")
        
        # offset_to_super_root at file pos 180 (0xB4)
        pk_super = get_uint32(pykotor_mdl, 180)
        mo_super = get_uint32(mdlops_mdl, 180)
        print(f"offset_to_super_root (0xB4): PyKotor={pk_super}, MDLOps={mo_super}")
        
        # offset_to_name_offsets at file pos 184 (0xB8)
        pk_names = get_uint32(pykotor_mdl, 184)
        mo_names = get_uint32(mdlops_mdl, 184)
        print(f"offset_to_name_offsets (0xB8): PyKotor={pk_names}, MDLOps={mo_names}")
        
        # name_offsets_count at file pos 188
        pk_names_count = get_uint32(pykotor_mdl, 188)
        mo_names_count = get_uint32(mdlops_mdl, 188)
        print(f"name_offsets_count: PyKotor={pk_names_count}, MDLOps={mo_names_count}")

        # Calculate layout regions
        print("\n=== Layout Regions ===")
        print(f"{'Region':<30} {'PyKotor':<20} {'MDLOps':<20}")
        
        # Header ends at 196 (model header size)
        print(f"{'Header':30} 0-195              0-195")
        
        # Names region
        pk_names_end = pk_names + pk_names_count * 4  # name offsets array
        mo_names_end = mo_names + mo_names_count * 4
        print(f"{'Name offsets':30} {pk_names}-{pk_names_end:<11} {mo_names}-{mo_names_end}")
        
        # Root node region (node headers + data)
        print(f"{'Root node (from header)':30} {pk_root+12:<19} {mo_root+12}")
        
        # Super root region
        print(f"{'Super root (from 0xB4)':30} {pk_super+12:<19} {mo_super+12}")
        
        # Look for first mesh node by finding type 33 (trimesh)
        print("\n=== Node Type Scan (first 10) ===")
        for label, data in [("PyKotor", pykotor_mdl), ("MDLOps", mdlops_mdl)]:
            locations = find_node_type_locations(data)[:10]
            print(f"\n{label}:")
            for offset, type_id, node_id in locations:
                print(f"  offset={offset}, type=0x{type_id:04X}, node_id={node_id}")


if __name__ == "__main__":
    main()

