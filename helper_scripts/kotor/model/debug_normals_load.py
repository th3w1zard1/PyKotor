#!/usr/bin/env python
"""Debug normals loading from MDL/MDX."""

from __future__ import annotations

import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "Libraries" / "PyKotor" / "src"))

from pykotor.common.misc import Game
from pykotor.extract.file import ResourceResult
from pykotor.extract.installation import Installation
from pykotor.resource.formats.mdl import read_mdl
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath, find_kotor_paths_from_default


def main():
    model_name = "comm_b_f2"
    game = Game.K1

    paths: dict[Game, list[CaseAwarePath]] = find_kotor_paths_from_default()
    game_paths = paths.get(game, [])
    if not game_paths:
        print(f"No {game.name} installation found")
        return

    installation: Installation = Installation(game_paths[0])

    mdl_res: ResourceResult | None = installation.resource(model_name, ResourceType.MDL)
    mdx_res: ResourceResult | None = installation.resource(model_name, ResourceType.MDX)

    assert mdl_res is not None, "MDL not found"
    assert mdx_res is not None, "MDX not found"

    print(f"Reading {model_name}...")
    mdl = read_mdl(mdl_res.data, source_ext=mdx_res.data, file_format=ResourceType.MDL)

    print(f"\nModel: {mdl.root.name}")
    print(f"Total nodes: {len(mdl.all_nodes())}")

    # Check each mesh node
    mesh_nodes = [n for n in mdl.all_nodes() if n.mesh]
    print(f"Mesh nodes: {len(mesh_nodes)}")

    total_verts = 0
    total_normals = 0
    total_uvs = 0

    for node in mesh_nodes:
        if not node.mesh:
            continue
        vcount = len(node.mesh.vertex_positions) if node.mesh.vertex_positions else 0
        ncount = len(node.mesh.vertex_normals) if node.mesh.vertex_normals else 0
        uvcount = len(node.mesh.vertex_uv1) if node.mesh.vertex_uv1 else 0

        total_verts += vcount
        total_normals += ncount
        total_uvs += uvcount

        if ncount != vcount or uvcount != vcount:
            print(f"\n  Node {node.name}: verts={vcount}, normals={ncount}, uv1={uvcount}")
            if ncount == 0 and vcount > 0:
                print("    *** MISSING NORMALS ***")
            if uvcount == 0 and vcount > 0:
                print("    *** MISSING UVs ***")

    print("\n=== Totals ===")
    print(f"Total vertices: {total_verts}")
    print(f"Total normals: {total_normals} {'(MATCHES)' if total_normals == total_verts else '(MISMATCH!)'}")
    print(f"Total UVs: {total_uvs} {'(MATCHES)' if total_uvs == total_verts else '(MISMATCH!)'}")

    # Sample some normal values to verify they're not all zeros
    print("\n=== Sample Normal Values ===")
    for node in mesh_nodes[:3]:
        if node.mesh and node.mesh.vertex_normals:
            print(f"\nNode {node.name}:")
            for i, n in enumerate(node.mesh.vertex_normals[:5]):
                print(f"  Normal {i}: ({n.x:.6f}, {n.y:.6f}, {n.z:.6f})")


if __name__ == "__main__":
    main()
