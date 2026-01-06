#!/usr/bin/env python
"""Debug script to trace vertex writing in PyKotor."""

from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "Libraries" / "PyKotor" / "src"))

from pykotor.common.misc import Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.mdl import read_mdl
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath, find_kotor_paths_from_default
from pykotor.extract.file import ResourceResult

# Import internal writer classes
from pykotor.resource.formats.mdl.io_mdl import MDLBinaryWriter, _Node


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
    assert mdl_res is not None and mdx_res is not None

    orig_mdl = mdl_res.data
    orig_mdx = mdx_res.data

    print(f"Model: {model_name}")
    print(f"Original: MDL={len(orig_mdl)}, MDX={len(orig_mdx)}")

    # Read with PyKotor
    mdl_obj = read_mdl(orig_mdl, source_ext=orig_mdx, file_format=ResourceType.MDL)
    
    # Create writer manually to inspect state
    mdl_stream = BytesIO()
    mdx_stream = BytesIO()
    
    # Note: MDLBinaryWriter populates nodes in write(), not __init__
    # So we need to call write() first, then inspect
    
    # Create a custom writer class to inspect state during write
    class DebugWriter(MDLBinaryWriter):
        def write(self, auto_close: bool = True):
            self._mdl_nodes[:] = self._mdl.all_nodes()
            self._bin_nodes[:] = [_Node() for _ in self._mdl_nodes]
            self._names = [n.name for n in self._mdl_nodes]
            
            # After populating nodes, update the data
            self._update_all_data()
            
            # Now print info
            print(f"\n=== Node Data After _update_all_data ===")
            print(f"MDL nodes: {len(self._mdl_nodes)}")
            print(f"Bin nodes: {len(self._bin_nodes)}")
            
            total_vertices_from_mesh = 0
            total_vertices_from_trimesh = 0
            
            for i, (mdl_node, bin_node) in enumerate(zip(self._mdl_nodes, self._bin_nodes)):
                if bin_node.trimesh:
                    mdl_vcount = len(mdl_node.mesh.vertex_positions) if mdl_node.mesh and mdl_node.mesh.vertex_positions else 0
                    bin_vcount = len(bin_node.trimesh.vertices) if bin_node.trimesh.vertices else 0
                    vcount_header = bin_node.trimesh.vertex_count
                    voffset = bin_node.trimesh.vertices_offset
                    
                    total_vertices_from_mesh += mdl_vcount
                    total_vertices_from_trimesh += bin_vcount
                    
                    vertices_size = bin_node.trimesh.vertices_size()
                    
                    if mdl_vcount != bin_vcount:
                        print(f"Node {i} {mdl_node.name}: MDL mesh={mdl_vcount}, trimesh.vertices={bin_vcount}, header={vcount_header}, vsize={vertices_size} <-- MISMATCH")
                    else:
                        print(f"Node {i} {mdl_node.name}: {mdl_vcount} vertices, header={vcount_header}, vsize={vertices_size}")
            
            print(f"\nTotal vertices from mesh: {total_vertices_from_mesh}")
            print(f"Total vertices from trimesh: {total_vertices_from_trimesh}")
            print(f"Expected MDL vertex bytes: {total_vertices_from_trimesh * 12}")
            
            # Continue with normal write
            return super().write(auto_close)
    
    writer = DebugWriter(mdl_obj, mdl_stream, target_ext=mdx_stream)
    writer.write()
    
    pykotor_mdl = mdl_stream.getvalue()
    pykotor_mdx = mdx_stream.getvalue()
    
    print(f"\n=== After Write ===")
    print(f"PyKotor: MDL={len(pykotor_mdl)}, MDX={len(pykotor_mdx)}")


if __name__ == "__main__":
    main()

