#!/usr/bin/env python
"""Debug AABB data loading."""
from __future__ import annotations

import struct
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PYKOTOR_SRC = REPO_ROOT / "Libraries" / "PyKotor" / "src"
if str(PYKOTOR_SRC) not in sys.path:
    sys.path.insert(0, str(PYKOTOR_SRC))

from pykotor.common.misc import Game
from pykotor.common.stream import BinaryReader
from pykotor.extract.installation import Installation
from pykotor.resource.formats.mdl import read_mdl
from pykotor.resource.type import ResourceType
from pykotor.tools.path import find_kotor_paths_from_default


def main():
    # Find K1 installation
    k1_paths = find_kotor_paths_from_default().get(Game.K1)
    if not k1_paths:
        print("No K1 installation found")
        return 1
    k1 = k1_paths[0]
    
    install = Installation(k1)
    resref = "m16aa_09a"
    mdl_res = install.resource(resref, ResourceType.MDL)
    mdx_res = install.resource(resref, ResourceType.MDX)
    
    if not mdl_res:
        print(f"Model {resref} not found")
        return 1
    
    mdl_data = mdl_res.data
    mdx_data = mdx_res.data if mdx_res else b""
    
    print(f"MDL size: {len(mdl_data)} bytes")
    print(f"MDX size: {len(mdx_data)} bytes")
    
    # Parse with read_mdl
    pk_mdl = read_mdl(mdl_data, source_ext=mdx_data, file_format=ResourceType.MDL)
    
    print(f"\nTotal nodes: {len(list(pk_mdl.all_nodes()))}")
    
    # Find nodes with AABB
    for node in pk_mdl.all_nodes():
        if node.aabb is not None:
            print(f"\n=== AABB Node: {node.name} ===")
            aabb_count = len(node.aabb.aabbs) if node.aabb.aabbs else 0
            print(f"AABB entries: {aabb_count}")
            
            if aabb_count > 0:
                for i, aabb in enumerate(node.aabb.aabbs[:5]):  # First 5
                    print(f"  [{i}] bbox_min={aabb.bbox_min}, bbox_max={aabb.bbox_max}, face={aabb.face_index}")
                if aabb_count > 5:
                    print(f"  ... and {aabb_count - 5} more")
    
    # Now let's manually find the AABB offset and read raw data
    print("\n=== Manual AABB data inspection ===")
    reader = BinaryReader.from_bytes(mdl_data)
    
    # File header: 12 bytes
    # Model header includes _GeometryHeader at offset 0xC (after file header)
    # _GeometryHeader is 80 bytes
    # _ModelHeader adds more fields after
    
    # Let me just find offset_to_name_offsets to get model header end
    # Looking at MDLOps structure:
    # File: 0x00-0x0B = 12-byte file header
    # Geom: 0x0C-0x5B = 80-byte geometry header (ends at 0x5C)
    # Model: 0x5C-... = rest of model header
    
    # Model header fields after geometry (from MDLOps):
    # 0x5C: model_classification (1 byte)
    # 0x5D: subclassification (1 byte)
    # 0x5E: unknown_flag (1 byte)
    # 0x5F: affect_fog (1 byte)
    # 0x60-0x63: child_model_count (4 bytes)
    # 0x64-0x8B: animations_array (40 bytes) - offset and count
    # 0x8C-0x8F: supermodel_ref (4 bytes)
    # 0x90-0xAF: bounding_box (32 bytes)
    # 0xB0-0xB3: radius (4 bytes)
    # 0xB4-0xB7: anim_scale (4 bytes)
    # 0xB8-0xEB: supermodel_name (52 bytes)
    # 0xEC-0x113: partnames_array (40 bytes) - offset and count
    
    # Read partnames (node name) array offset and count
    reader.seek(0xEC + 12)  # offset 0xEC + file header
    name_offsets_offset = reader.read_uint32()
    reader.seek(0xF0 + 12)
    name_offsets_count = reader.read_uint32()
    
    # Actually, the array struct in MDL is: offset (4), used_count (4), alloc_count (4)
    # So offset is at 0xEC, count at 0xF0, alloc at 0xF4
    reader.seek(0xEC)  # Without file header offset since BinaryReader doesn't auto-adjust
    name_off_raw = reader.read_bytes(12)
    name_off_vals = struct.unpack("<III", name_off_raw)
    print(f"Name offsets array at 0xEC: offset={name_off_vals[0]}, count={name_off_vals[1]}, alloc={name_off_vals[2]}")
    
    # Geometry header root_node_offset is at 0xC (file header) + 0x28 = 0x34
    reader.seek(0x34)
    root_node_offset_raw = reader.read_uint32()
    print(f"Root node offset (at 0x34): {root_node_offset_raw} (0x{root_node_offset_raw:X})")
    
    # The offset stored in file is (actual_offset - 12), so actual = raw + 12
    root_node_actual = root_node_offset_raw + 12
    print(f"Root node actual offset: {root_node_actual} (0x{root_node_actual:X})")
    
    # Now let me use MDLOps-style decompilation output to check what it sees
    # For now, let me just verify we can read the root node header
    reader.seek(root_node_actual)
    node_header_raw = reader.read_bytes(80)  # Node header is ~80 bytes
    node_type, = struct.unpack("<H", node_header_raw[0:2])
    print(f"Root node type at 0x{root_node_actual:X}: 0x{node_type:04X}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

