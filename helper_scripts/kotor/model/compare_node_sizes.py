#!/usr/bin/env python
"""Compare node-level sizes between PyKotor and MDLOps output."""

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


def read_mdl_header(data: bytes):
    """Read basic MDL header info."""
    # Skip 12-byte file header
    offset = 12
    # Geometry header: func_ptr0, func_ptr1 (8 bytes), name (32 bytes), root offset
    root_offset = struct.unpack_from("<I", data, offset + 8 + 32)[0]
    node_count = struct.unpack_from("<I", data, offset + 8 + 32 + 4 + 4 + 4 + 4)[0]
    return root_offset, node_count


def main():
    model_name = "comm_b_f2"
    game = Game.K1

    paths: dict[Game, list[CaseAwarePath]] = find_kotor_paths_from_default()
    game_paths: list[CaseAwarePath] = paths.get(game, [])
    if not game_paths:
        print(f"No {game.name} installation found")
        return

    installation: Installation = Installation(game_paths[0])
    mdlops_exe = Path(__file__).parents[3] / "vendor" / "MDLOps" / "mdlops.exe"

    mdl_res: ResourceResult | None = installation.resource(model_name, ResourceType.MDL)
    mdx_res: ResourceResult | None = installation.resource(model_name, ResourceType.MDX)

    assert mdl_res is not None, "MDL resource not found"
    assert mdx_res is not None, "MDX resource not found"

    with tempfile.TemporaryDirectory(prefix="mdl_compare_") as td:
        td_path = Path(td)

        # Write original
        orig_mdl_path = td_path / f"{model_name}.mdl"
        orig_mdx_path = td_path / f"{model_name}.mdx"
        orig_mdl_path.write_bytes(mdl_res.data if mdl_res.data else b"")
        orig_mdx_path.write_bytes(mdx_res.data if mdx_res.data else b"")

        # PyKotor roundtrip
        mdl_obj = read_mdl(mdl_res.data, source_ext=mdx_res.data, file_format=ResourceType.MDL)
        pykotor_mdl_path = td_path / f"{model_name}-pykotor.mdl"
        pykotor_mdx_path = td_path / f"{model_name}-pykotor.mdx"
        write_mdl(mdl_obj, pykotor_mdl_path, ResourceType.MDL, target_ext=pykotor_mdx_path)
        pykotor_mdl = pykotor_mdl_path.read_bytes()
        pykotor_mdx = pykotor_mdx_path.read_bytes()

        # MDLOps roundtrip
        subprocess.run([str(mdlops_exe), str(orig_mdl_path)], cwd=str(td_path), capture_output=True, timeout=60)
        ascii_path = td_path / f"{model_name}-ascii.mdl"
        subprocess.run([str(mdlops_exe), str(ascii_path), "-k1"], cwd=str(td_path), capture_output=True, timeout=60)
        mdlops_mdl_path = td_path / f"{model_name}-ascii-k1-bin.mdl"
        mdlops_mdx_path = td_path / f"{model_name}-ascii-k1-bin.mdx"
        mdlops_mdl = mdlops_mdl_path.read_bytes()
        mdlops_mdx = mdlops_mdx_path.read_bytes()

        print("=== File Sizes ===")
        print(f"Original: MDL={len(mdl_res.data)}, MDX={len(mdx_res.data)}, Total={len(mdl_res.data) + len(mdx_res.data)}")
        print(f"PyKotor:  MDL={len(pykotor_mdl)}, MDX={len(pykotor_mdx)}, Total={len(pykotor_mdl) + len(pykotor_mdx)}")
        print(f"MDLOps:   MDL={len(mdlops_mdl)}, MDX={len(mdlops_mdx)}, Total={len(mdlops_mdl) + len(mdlops_mdx)}")

        # Compare headers
        print("\n=== Header Comparison ===")
        pyk_root, pyk_nodes = read_mdl_header(pykotor_mdl)
        mdl_root, mdl_nodes = read_mdl_header(mdlops_mdl)
        print(f"PyKotor: root_offset={pyk_root}, node_count={pyk_nodes}")
        print(f"MDLOps:  root_offset={mdl_root}, node_count={mdl_nodes}")

        # Find where data sections start by looking at specific offsets
        print("\n=== Section Breakdown ===")

        # In the model header, look for animation count and offsets
        # Model header is at offset 12, animation info starts at offset 12+80
        pyk_name_offsets_offset = struct.unpack_from("<I", pykotor_mdl, 12 + 164)[0]  # offset to name offsets
        pyk_name_count = struct.unpack_from("<I", pykotor_mdl, 12 + 168)[0]  # name offsets count
        pyk_anim_offset = struct.unpack_from("<I", pykotor_mdl, 12 + 172)[0]  # offset to animations

        mdl_name_offsets_offset = struct.unpack_from("<I", mdlops_mdl, 12 + 164)[0]
        mdl_name_count = struct.unpack_from("<I", mdlops_mdl, 12 + 168)[0]
        mdl_anim_offset = struct.unpack_from("<I", mdlops_mdl, 12 + 172)[0]

        print(f"PyKotor: name_offsets=@{pyk_name_offsets_offset}, name_count={pyk_name_count}, anim_offset=@{pyk_anim_offset}")
        print(f"MDLOps:  name_offsets=@{mdl_name_offsets_offset}, name_count={mdl_name_count}, anim_offset=@{mdl_anim_offset}")

        # Calculate data sections
        header_end = 12 + 196  # file header + model header
        pyk_names_end = pyk_name_offsets_offset + pyk_name_count * 4 + 12  # rough estimate
        mdl_names_end = mdl_name_offsets_offset + mdl_name_count * 4 + 12

        # Difference breakdown
        diff_mdl = len(mdlops_mdl) - len(pykotor_mdl)
        diff_mdx = len(mdlops_mdx) - len(pykotor_mdx)

        print("\n=== Size Differences ===")
        print(f"MDL diff (MDLOps - PyKotor): {diff_mdl} bytes")
        print(f"MDX diff (MDLOps - PyKotor): {diff_mdx} bytes")
        print(f"Net total diff: {diff_mdl + diff_mdx} bytes")

        # Check node count matches
        print("\n=== Node Count Verification ===")
        all_nodes = mdl_obj.all_nodes()
        print(f"PyKotor parsed {len(all_nodes)} nodes")

        # Count vertex data
        total_verts = sum(len(n.mesh.vertex_positions) if n.mesh and n.mesh.vertex_positions else 0 for n in all_nodes)
        total_faces = sum(len(n.mesh.faces) if n.mesh else 0 for n in all_nodes)
        total_normals = sum(len(n.mesh.vertex_normals) if n.mesh and n.mesh.vertex_normals else 0 for n in all_nodes)
        total_uvs = sum(len(n.mesh.vertex_uv1) if n.mesh and n.mesh.vertex_uv1 else 0 for n in all_nodes)

        print(f"Total vertices: {total_verts}")
        print(f"Total faces: {total_faces}")
        print(f"Total normals: {total_normals}")
        print(f"Total UVs: {total_uvs}")

        print(f"\nExpected vertex bytes in MDL: {total_verts * 12}")
        print(f"Expected normal bytes in MDX: {total_normals * 12}")
        print(f"Expected UV bytes in MDX: {total_uvs * 8}")


if __name__ == "__main__":
    main()
