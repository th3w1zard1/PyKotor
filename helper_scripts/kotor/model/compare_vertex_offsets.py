#!/usr/bin/env python
"""Compare vertex offsets between PyKotor and MDLOps binary output."""

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

    with tempfile.TemporaryDirectory(prefix="mdl_verts_") as td:
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
        pykotor_mdx = pykotor_mdx_path.read_bytes()

        # MDLOps roundtrip
        subprocess.run([str(mdlops_exe), str(orig_mdl_path)], cwd=str(td_path), capture_output=True, timeout=60)
        subprocess.run([str(mdlops_exe), str(td_path / f"{model_name}-ascii.mdl"), "-k1"], cwd=str(td_path), capture_output=True, timeout=60)
        mdlops_mdl = (td_path / f"{model_name}-ascii-k1-bin.mdl").read_bytes()
        mdlops_mdx = (td_path / f"{model_name}-ascii-k1-bin.mdx").read_bytes()

        print(f"Model: {model_name}")
        print(f"PyKotor: MDL={len(pykotor_mdl)}, MDX={len(pykotor_mdx)}")
        print(f"MDLOps:  MDL={len(mdlops_mdl)}, MDX={len(mdlops_mdx)}")
        
        # Print node info from PyKotor's model object
        print(f"\n=== PyKotor Model Structure ===")
        all_nodes = mdl_obj.all_nodes()
        print(f"Total nodes: {len(all_nodes)}")
        
        mesh_nodes = [n for n in all_nodes if n.mesh]
        print(f"Mesh nodes: {len(mesh_nodes)}")
        
        total_vertices = 0
        total_faces = 0
        for node in mesh_nodes:
            vcount = len(node.mesh.vertex_positions) if node.mesh.vertex_positions else 0
            fcount = len(node.mesh.faces) if node.mesh.faces else 0
            total_vertices += vcount
            total_faces += fcount
            print(f"  {node.name}: {vcount} vertices, {fcount} faces")
        
        print(f"\nTotal: {total_vertices} vertices, {total_faces} faces")
        print(f"Vertex bytes: {total_vertices * 12}")
        
        # Compare sizes
        print(f"\n=== Size Analysis ===")
        print(f"MDL difference: {len(mdlops_mdl) - len(pykotor_mdl)} bytes")
        print(f"MDX difference: {len(mdlops_mdx) - len(pykotor_mdx)} bytes")
        
        # If MDLOps MDL is larger, it's likely because it writes vertcoords to MDL
        # but PyKotor doesn't (or writes them differently)
        expected_mdl_diff_from_vertices = total_vertices * 12
        actual_mdl_diff = len(mdlops_mdl) - len(pykotor_mdl)
        
        print(f"\nExpected MDL diff if vertices missing: {expected_mdl_diff_from_vertices}")
        print(f"Actual MDL diff: {actual_mdl_diff}")
        
        # Check what data PyKotor is missing
        # By looking at the MDLOps-vs-PyKotor difference
        if actual_mdl_diff > 0:
            print(f"\nPyKotor MDL is {actual_mdl_diff} bytes smaller than MDLOps")
            # This suggests PyKotor is NOT writing vertcoords to MDL for some nodes
            # Let's calculate how many vertices worth of data is missing
            missing_verts = actual_mdl_diff // 12
            print(f"This equals approximately {missing_verts} missing vertices ({actual_mdl_diff} / 12)")
        
        # Check if PyKotor is writing more to MDX
        mdx_diff = len(pykotor_mdx) - len(mdlops_mdx)
        if mdx_diff > 0:
            print(f"\nPyKotor MDX is {mdx_diff} bytes larger than MDLOps")
            # This is expected because MDLOps recalculates normals
            # Let's see if the difference could be explained by normal recalculation
            # If MDLOps strips some data, the difference would be visible here


if __name__ == "__main__":
    main()

