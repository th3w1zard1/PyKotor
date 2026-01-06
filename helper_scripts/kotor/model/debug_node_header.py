#!/usr/bin/env python3
"""Debug script to decode node headers from MDL files."""
from __future__ import annotations

import struct
from typing import Any
from pathlib import Path

base = Path(r"C:\Users\boden\AppData\Local\Temp\mdl_aio_aratech3")
orig_mdl = base / "aratech_sign-original.mdl"
pk_mdl = base / "aratech_sign-pykotor.mdl"
mo_mdl = base / "aratech_sign-mdlops.mdl"
orig_data = orig_mdl.read_bytes()
pk_data = pk_mdl.read_bytes()
mo_data = mo_mdl.read_bytes()

root_node_offset = struct.unpack("<I", orig_data[0x34:0x38])[0]
print(f"root_node_offset (internal): 0x{root_node_offset:X} ({root_node_offset})")
root_abs = root_node_offset + 12
print(f"root_node_offset (absolute): 0x{root_abs:X} ({root_abs})")


def decode_node_header(data: bytes, offset: int, name: str = "") -> dict[str, int | float | list[float] | tuple[Any, ...]]:
    hdr: dict[str, int | float | list[float] | tuple[Any, ...]] = {}
    hdr["type_id"] = struct.unpack("<H", data[offset : offset + 2])[0]
    hdr["padding0"] = struct.unpack("<H", data[offset + 2 : offset + 4])[0]
    hdr["node_id"] = struct.unpack("<H", data[offset + 4 : offset + 6])[0]
    hdr["name_id"] = struct.unpack("<H", data[offset + 6 : offset + 8])[0]
    hdr["offset_to_root"] = struct.unpack("<I", data[offset + 8 : offset + 12])[0]
    hdr["offset_to_parent"] = struct.unpack("<I", data[offset + 12 : offset + 16])[0]
    hdr["position"] = struct.unpack("<3f", data[offset + 16 : offset + 28])
    hdr["orientation"] = struct.unpack("<4f", data[offset + 28 : offset + 44])
    hdr["offset_to_children"] = struct.unpack("<I", data[offset + 44 : offset + 48])[0]
    hdr["children_count"] = struct.unpack("<I", data[offset + 48 : offset + 52])[0]
    hdr["children_count2"] = struct.unpack("<I", data[offset + 52 : offset + 56])[0]
    hdr["offset_to_controllers"] = struct.unpack("<I", data[offset + 56 : offset + 60])[0]
    hdr["controller_count"] = struct.unpack("<I", data[offset + 60 : offset + 64])[0]
    hdr["controller_count2"] = struct.unpack("<I", data[offset + 64 : offset + 68])[0]
    hdr["offset_to_controller_data"] = struct.unpack("<I", data[offset + 68 : offset + 72])[0]
    hdr["controller_data_length"] = struct.unpack("<I", data[offset + 72 : offset + 76])[0]
    hdr["controller_data_length2"] = struct.unpack("<I", data[offset + 76 : offset + 80])[0]

    type_id = hdr["type_id"]
    node_id = hdr["node_id"]
    name_id = hdr["name_id"]
    print(f"{name} at 0x{offset:X}:")
    print(f"  type_id={type_id}, node_id={node_id}, name_id={name_id}")
    print(f"  offset_to_root=0x{hdr['offset_to_root']:X}")
    print(f"  offset_to_parent=0x{hdr['offset_to_parent']:X}")
    print(f"  offset_to_children=0x{hdr['offset_to_children']:X} (at file offset 0x{offset + 44:X})")
    print(f"  children_count={hdr['children_count']}, children_count2={hdr['children_count2']}")
    print(f"  offset_to_controllers=0x{hdr['offset_to_controllers']:X} (at file offset 0x{offset + 56:X})")
    print(f"  controller_count={hdr['controller_count']}, controller_count2={hdr['controller_count2']}")
    print(f"  offset_to_controller_data=0x{hdr['offset_to_controller_data']:X} (at file offset 0x{offset + 68:X})")
    print(f"  controller_data_length={hdr['controller_data_length']}, controller_data_length2={hdr['controller_data_length2']}")
    return hdr


print("\n=== ROOT NODE (ORIGINAL) ===")
orig_root = decode_node_header(orig_data, root_abs, "ORIGINAL")

print("\n=== ROOT NODE (PYKOTOR) ===")
pk_root = decode_node_header(pk_data, root_abs, "PYKOTOR")

print("\n=== ROOT NODE (MDLOPS) ===")
mo_root = decode_node_header(mo_data, root_abs, "MDLOPS")

print("\n=== PROBLEMATIC OFFSETS ===")
print(f"Offset 0x13C = {0x13C} is at relative offset {0x13C - root_abs} from root node (root at {root_abs})")
print(f"Offset 0x148 = {0x148} is at relative offset {0x148 - root_abs} from root node")
print(f"Offset 0x163 = {0x163} is at relative offset {0x163 - root_abs} from root node")

# Node header is 80 bytes
# 0x13C is probably in the second node or later
# Let's find where node 2 would start
node1_end = root_abs + 80
print(f"\nFirst node ends at: 0x{node1_end:X} ({node1_end})")

# Find child offsets from root node if it has children
children_count = orig_root["children_count"]
assert isinstance(children_count, int)
offset_to_children = orig_root["offset_to_children"]
assert isinstance(offset_to_children, int)
if children_count > 0:
    children_offset = offset_to_children + 12  # Add 12 for absolute
    assert isinstance(children_offset, int)
    print(f"Children array at: 0x{children_offset:X}")
    # Read child pointers
    for i in range(children_count):
        child_ptr = struct.unpack("<I", orig_data[children_offset + i * 4 : children_offset + i * 4 + 4])[0]
        child_abs = child_ptr + 12
        print(f"  Child {i}: ptr=0x{child_ptr:X}, abs=0x{child_abs:X}")
        if child_abs < len(orig_data):
            print(f"\n=== CHILD {i} NODE (ORIGINAL) ===")
            decode_node_header(orig_data, child_abs, f"CHILD {i} ORIGINAL")
            print(f"\n=== CHILD {i} NODE (PYKOTOR) ===")
            decode_node_header(pk_data, child_abs, f"CHILD {i} PYKOTOR")
            print(f"\n=== CHILD {i} NODE (MDLOPS) ===")
            decode_node_header(mo_data, child_abs, f"CHILD {i} MDLOPS")
