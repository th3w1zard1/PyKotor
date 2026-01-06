#!/usr/bin/env python
"""Debug vertex counts in PyKotor vs MDLOps output.

This script traces the vertex data to understand why PyKotor's MDL is smaller.
"""

from __future__ import annotations

import sys
import tempfile

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "Libraries" / "PyKotor" / "src"))

from pykotor.common.misc import Game
from pykotor.extract.file import ResourceResult
from pykotor.extract.installation import Installation
from pykotor.resource.formats.mdl import read_mdl
from pykotor.resource.formats.mdl.io_mdl import MDLBinaryWriter
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
    mdx_res = installation.resource(model_name, ResourceType.MDX)
    if mdl_res is None:
        print(f"Model {model_name} not found")
        return

    orig_mdl = mdl_res.data
    orig_mdx = mdx_res.data if mdx_res else b""

    print(f"Model: {model_name}")
    print(f"Original: MDL={len(orig_mdl)}, MDX={len(orig_mdx)}")

    # Read the model
    mdl_obj = read_mdl(orig_mdl, source_ext=orig_mdx or None, file_format=ResourceType.MDL)

    print("\n=== Node Vertex Analysis ===")
    print(f"{'Node':<25} {'Type':<10} {'VertPos':<10} {'VertNorm':<10} {'UV1':<10}")
    print("-" * 65)

    total_vertex_positions = 0
    total_vertex_normals = 0
    total_uvs = 0
    mesh_nodes = 0

    for node in mdl_obj.all_nodes():
        if node.mesh:
            mesh_nodes += 1
            vpos = len(node.mesh.vertex_positions) if node.mesh.vertex_positions else 0
            vnorm = len(node.mesh.vertex_normals) if node.mesh.vertex_normals else 0
            uv1 = len(node.mesh.vertex_uv1) if node.mesh.vertex_uv1 else 0

            total_vertex_positions += vpos
            total_vertex_normals += vnorm
            total_uvs += uv1

            node_type = type(node.mesh).__name__
            print(f"{node.name:<25} {node_type:<10} {vpos:<10} {vnorm:<10} {uv1:<10}")

    print("-" * 65)
    print(f"{'TOTAL':<25} {mesh_nodes:<10} {total_vertex_positions:<10} {total_vertex_normals:<10} {total_uvs:<10}")

    # Calculate expected MDL vertex bytes
    expected_vertex_bytes = total_vertex_positions * 12  # Vector3 = 3 floats = 12 bytes
    print("\n=== Expected Vertex Bytes in MDL ===")
    print(f"Total vertices: {total_vertex_positions}")
    print(f"Expected bytes: {expected_vertex_bytes}")

    # Now trace through the writer to see what it actually writes
    print("\n=== Writer Trace ===")
    with tempfile.TemporaryDirectory(prefix="mdl_verts_") as td:
        td_path = Path(td)
        pykotor_mdl_path = td_path / f"{model_name}-pykotor.mdl"
        pykotor_mdx_path = td_path / f"{model_name}-pykotor.mdx"

        # Create writer manually to inspect state
        writer = MDLBinaryWriter(mdl_obj, pykotor_mdl_path, pykotor_mdx_path)
        writer.write(auto_close=False)

        # Check the bin_nodes
        print("\n=== Writer Bin Nodes ===")
        print(f"{'Node':<25} {'Vertices':<10} {'VertCount':<10} {'VertSize':<10}")
        print("-" * 55)

        total_bin_vertices = 0
        total_bin_vertex_bytes = 0
        total_indices_counts = 0
        total_indices_offsets = 0
        total_inverted = 0
        for i, bin_node in enumerate(writer._bin_nodes):
            if bin_node.trimesh:
                vcount = len(bin_node.trimesh.vertices)
                vsize = bin_node.trimesh.vertices_size()
                total_bin_vertices += vcount
                total_bin_vertex_bytes += vsize
                total_indices_counts += len(bin_node.trimesh.indices_counts)
                total_indices_offsets += len(bin_node.trimesh.indices_offsets)
                total_inverted += len(bin_node.trimesh.inverted_counters)
                name = writer._names[i] if i < len(writer._names) else f"node_{i}"
                print(f"{name:<25} {vcount:<10} {bin_node.trimesh.vertex_count:<10} {vsize:<10}")

        print("-" * 55)
        print(f"{'TOTAL':<25} {total_bin_vertices:<10} {'':<10} {total_bin_vertex_bytes:<10}")

        print("\n=== Extra Arrays ===")
        print(f"Total indices_counts entries: {total_indices_counts} ({total_indices_counts * 4} bytes)")
        print(f"Total indices_offsets entries: {total_indices_offsets} ({total_indices_offsets * 4} bytes)")
        print(f"Total inverted_counters entries: {total_inverted} ({total_inverted * 4} bytes)")

        # Check actual file size
        pykotor_mdl = pykotor_mdl_path.read_bytes()
        print(f"\nActual MDL size: {len(pykotor_mdl)}")
        print(f"Expected vertex bytes: {total_bin_vertex_bytes}")

        # Calculate MDL size breakdown
        header_size = 196  # _ModelHeader.SIZE
        name_offsets_size = len(writer._names) * 4
        names_size = sum(len(n) + 1 for n in writer._names)
        anim_offsets_size = len(writer._bin_anims) * 4

        # Sum all node sizes
        node_sizes = 0
        for bin_node in writer._bin_nodes:
            node_sizes += bin_node.calc_size(writer.game)

        print("\n=== MDL Size Breakdown ===")
        print(f"Header:       {header_size}")
        print(f"Name offsets: {name_offsets_size}")
        print(f"Names:        {names_size}")
        print(f"Anim offsets: {anim_offsets_size}")
        print(f"Node total:   {node_sizes}")
        print(f"Calculated:   {header_size + name_offsets_size + names_size + anim_offsets_size + node_sizes}")
        print(f"Actual:       {len(pykotor_mdl) - 12}")  # -12 for file header


if __name__ == "__main__":
    main()
