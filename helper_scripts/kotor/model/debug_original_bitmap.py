#!/usr/bin/env python
"""Debug original binary's MDX data bitmap to understand UV handling."""

from __future__ import annotations

import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "Libraries" / "PyKotor" / "src"))

from pykotor.common.misc import Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.mdl.io_mdl import MDLBinaryReader, _MDXDataFlags, _NodeHeader, _TrimeshHeader
from pykotor.resource.type import ResourceType
from pykotor.tools.path import find_kotor_paths_from_default


def main():
    model_name = "comm_b_f2"
    game = Game.K1

    paths = find_kotor_paths_from_default()
    game_paths = paths.get(game, [])
    if not game_paths:
        print(f"No {game.name} installation found")
        return

    installation = Installation(game_paths[0])

    mdl_res = installation.resource(model_name, ResourceType.MDL)
    mdx_res = installation.resource(model_name, ResourceType.MDX)

    assert mdl_res is not None, "MDL not found"
    assert mdx_res is not None, "MDX not found"

    print(f"Reading {model_name} original binary...")
    print(f"MDL size: {len(mdl_res.data)}, MDX size: {len(mdx_res.data)}")

    # Instrument the reader to capture bitmap flags
    reader = MDLBinaryReader(mdl_res.data, source_ext=mdx_res.data)
    orig_load = reader._load_node

    node_data = []

    def capture_load_node(offset, parent):
        reader._reader.seek(offset)
        hdr = _NodeHeader().read(reader._reader)

        info = {
            "name_id": hdr.name_id,
            "node_id": hdr.node_id,
            "type_id": hdr.type_id,
            "is_mesh": bool(hdr.type_id & 0x20),  # MESH flag
        }

        if hdr.type_id & 0x20:  # MESH flag
            trimesh = _TrimeshHeader()
            trimesh.read(reader._reader, game)
            info["vcount"] = trimesh.vertex_count
            info["bitmap"] = trimesh.mdx_data_bitmap
            info["has_vertex"] = bool(trimesh.mdx_data_bitmap & _MDXDataFlags.VERTEX)
            info["has_normal"] = bool(trimesh.mdx_data_bitmap & _MDXDataFlags.NORMAL)
            info["has_tex0"] = bool(trimesh.mdx_data_bitmap & _MDXDataFlags.TEX0)
            info["has_tex1"] = bool(trimesh.mdx_data_bitmap & _MDXDataFlags.TEX1)
            info["mdx_offset"] = trimesh.mdx_data_offset
            info["texture1"] = trimesh.texture1
            info["texture2"] = trimesh.texture2

        node_data.append(info)
        return orig_load(offset, parent)

    reader._load_node = capture_load_node
    mdl = reader.load()

    # Get names from loaded model
    all_nodes = mdl.all_nodes()
    name_map = {i: n.name for i, n in enumerate(all_nodes)}

    print(f"\nLoaded {len(all_nodes)} nodes")
    print(f"\n{'Name':<20} {'VCount':>6} {'Bitmap':>10} {'VERT':>5} {'NORM':>5} {'TEX0':>5} {'Texture1':<20}")
    print("-" * 90)

    mesh_nodes = [d for d in node_data if d["is_mesh"]]
    for i, d in enumerate(mesh_nodes):
        name = name_map.get(d["node_id"], f"node_{d['node_id']}")
        vcount = d.get("vcount", 0)
        bitmap = d.get("bitmap", 0)
        has_vert = "Y" if d.get("has_vertex") else "N"
        has_norm = "Y" if d.get("has_normal") else "N"
        has_tex0 = "Y" if d.get("has_tex0") else "N"
        texture1 = d.get("texture1", "")

        print(f"{name:<20} {vcount:>6} 0x{bitmap:>08X} {has_vert:>5} {has_norm:>5} {has_tex0:>5} {texture1:<20}")

    # Summary
    print("\n=== Summary ===")
    total_with_tex0 = sum(1 for d in mesh_nodes if d.get("has_tex0"))
    total_mesh = len(mesh_nodes)
    print(f"Mesh nodes with TEX0 flag: {total_with_tex0} / {total_mesh}")

    # Show nodes missing TEX0
    missing_tex0 = [d for d in mesh_nodes if not d.get("has_tex0")]
    if missing_tex0:
        print(f"\nNodes WITHOUT TEX0 flag ({len(missing_tex0)}):")
        for d in missing_tex0:
            name = name_map.get(d["node_id"], f"node_{d['node_id']}")
            print(f"  {name}: texture1='{d.get('texture1', '')}'")


if __name__ == "__main__":
    main()
