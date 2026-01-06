#!/usr/bin/env python
"""Debug script to trace node walking in binary MDL."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "Libraries" / "PyKotor" / "src"))

from pykotor.common.misc import Game
from pykotor.common.stream import BinaryReader
from pykotor.extract.installation import Installation
from pykotor.resource.formats.mdl.io_mdl import _ModelHeader, _NodeHeader, _TrimeshHeader
from pykotor.resource.formats.mdl.mdl_types import MDLNodeFlags
from pykotor.resource.type import ResourceType


def main() -> None:
    resref = "comm_b_f2"
    k1_path = Path(r"C:/Program Files (x86)/Steam/steamapps/common/swkotor")
    inst = Installation(k1_path)

    mdl_res = inst.resource(resref, ResourceType.MDL)
    assert mdl_res is not None
    mdl_data = mdl_res.data

    reader = BinaryReader.from_auto(mdl_data, 0)
    reader.set_offset(reader.offset() + 12)

    header = _ModelHeader().read(reader)
    print(f"Root node offset: {header.geometry.root_node_offset}")
    print(f"Node count from header: {header.geometry.node_count}")
    print()

    seen: set[int] = set()
    all_nodes: list[dict] = []

    def walk(offset: int, depth: int = 0) -> None:
        if offset in seen or offset == 0:
            return
        seen.add(offset)

        try:
            reader.seek(offset)
            hdr = _NodeHeader().read(reader)
        except OSError as e:
            indent = "  " * depth
            print(f"{indent}ERROR: Cannot read node at offset {offset}: {e}")
            return

        is_mesh = bool(hdr.type_id & MDLNodeFlags.MESH)
        is_skin = bool(hdr.type_id & 0x40)

        node_type = "MESH" if is_mesh else "dummy"
        if is_skin:
            node_type = "SKIN"

        all_nodes.append({
            "offset": offset,
            "node_id": hdr.node_id,
            "type_id": hdr.type_id,
            "is_mesh": is_mesh,
            "children_count": hdr.children_count,
            "offset_to_children": hdr.offset_to_children,
        })

        indent = "  " * depth
        print(f"{indent}Node id={hdr.node_id} type=0x{hdr.type_id:04X} ({node_type}) children={hdr.children_count} @{offset} (children_offset={hdr.offset_to_children})")

        if hdr.children_count > 0 and hdr.offset_to_children not in (0, 0xFFFFFFFF) and hdr.children_count < 100:
            try:
                reader.seek(hdr.offset_to_children)
                child_offsets = []
                for i in range(hdr.children_count):
                    child_off = reader.read_uint32()
                    child_offsets.append(child_off)
                
                # Show child offsets for debugging
                if depth < 10:
                    valid = [o for o in child_offsets if 0 < o < 100000]
                    invalid = [o for o in child_offsets if o <= 0 or o >= 100000]
                    print(f"{indent}  -> Valid children: {valid[:5]}{'...' if len(valid) > 5 else ''}")
                    if invalid:
                        print(f"{indent}  -> INVALID children: {invalid[:5]}{'...' if len(invalid) > 5 else ''}")
                
                for child_off in child_offsets:
                    if 0 < child_off < 100000:  # Sanity check
                        walk(child_off, depth + 1)
            except OSError as e:
                print(f"{indent}  ERROR: Cannot read children at offset {hdr.offset_to_children}: {e}")

    walk(header.geometry.root_node_offset)

    print()
    print(f"Total nodes walked: {len(all_nodes)}")
    mesh_nodes = [n for n in all_nodes if n["is_mesh"]]
    print(f"Mesh nodes found: {len(mesh_nodes)}")
    for m in mesh_nodes:
        print(f"  id={m['node_id']} type=0x{m['type_id']:04X} @{m['offset']}")


if __name__ == "__main__":
    main()

