#!/usr/bin/env python
"""Debug what PyKotor writes to MDX vs what MDLOps writes."""

from __future__ import annotations

import struct
import subprocess
import sys
import tempfile

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "Libraries" / "PyKotor" / "src"))

from pykotor.common.misc import Game
from pykotor.extract.file import ResourceResult
from pykotor.extract.installation import Installation
from pykotor.resource.formats.mdl import read_mdl, write_mdl
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath, find_kotor_paths_from_default


def hex_floats(
    data: bytes,
    offset: int,
    count: int,
) -> list[float]:
    """Read count floats from data at offset."""
    floats = []
    for i in range(count):
        f = struct.unpack_from("<f", data, offset + i * 4)[0]
        floats.append(f)
    return floats


def main():
    model_name = "comm_b_f2"
    game = Game.K1

    paths: dict[Game, list[CaseAwarePath]] = find_kotor_paths_from_default()
    game_paths: list[CaseAwarePath] = paths.get(game, [])
    if not game_paths:
        print(f"No {game.name} installation found")
        return

    installation = Installation(game_paths[0])
    mdlops_exe = Path(__file__).parents[3] / "vendor" / "MDLOps" / "mdlops.exe"

    mdl_res: ResourceResult | None = installation.resource(model_name, ResourceType.MDL)
    mdx_res: ResourceResult | None = installation.resource(model_name, ResourceType.MDX)

    assert mdl_res is not None, "MDL resource not found"
    assert mdx_res is not None, "MDX resource not found"

    orig_mdx = mdx_res.data

    with tempfile.TemporaryDirectory(prefix="mdl_debug_") as td:
        td_path = Path(td)

        # Write original
        orig_mdl_path = td_path / f"{model_name}.mdl"
        orig_mdx_path = td_path / f"{model_name}.mdx"
        orig_mdl_path.write_bytes(mdl_res.data)
        orig_mdx_path.write_bytes(mdx_res.data)

        # PyKotor roundtrip
        mdl_obj = read_mdl(mdl_res.data, source_ext=mdx_res.data, file_format=ResourceType.MDL)
        pykotor_mdl_path = td_path / f"{model_name}-pykotor.mdl"
        pykotor_mdx_path = td_path / f"{model_name}-pykotor.mdx"
        write_mdl(mdl_obj, pykotor_mdl_path, ResourceType.MDL, target_ext=pykotor_mdx_path)
        pykotor_mdx = pykotor_mdx_path.read_bytes()

        # MDLOps roundtrip
        subprocess.run([str(mdlops_exe), str(orig_mdl_path)], cwd=str(td_path), capture_output=True, timeout=60)
        ascii_path = td_path / f"{model_name}-ascii.mdl"
        subprocess.run([str(mdlops_exe), str(ascii_path), "-k1"], cwd=str(td_path), capture_output=True, timeout=60)
        mdlops_mdx_path = td_path / f"{model_name}-ascii-k1-bin.mdx"
        mdlops_mdx = mdlops_mdx_path.read_bytes()

        print(f"Original MDX: {len(orig_mdx)} bytes")
        print(f"PyKotor MDX: {len(pykotor_mdx)} bytes")
        print(f"MDLOps MDX: {len(mdlops_mdx)} bytes")

        # Sample some floats from different locations
        print("\n=== MDX Float Comparison ===")
        # First node vertex data starts around offset 0
        sample_offsets = [0, 12, 24, 0x258, 0x260, 0x26C, 0x500, 0x1000]

        for off in sample_offsets:
            if off + 12 <= min(len(orig_mdx), len(pykotor_mdx), len(mdlops_mdx)):
                orig_f = hex_floats(orig_mdx, off, 3)
                pyk_f = hex_floats(pykotor_mdx, off, 3)
                mdl_f = hex_floats(mdlops_mdx, off, 3)

                print(f"\nOffset 0x{off:04X}:")
                print(f"  Original: {orig_f[0]:12.6f} {orig_f[1]:12.6f} {orig_f[2]:12.6f}")
                print(f"  PyKotor:  {pyk_f[0]:12.6f} {pyk_f[1]:12.6f} {pyk_f[2]:12.6f}")
                print(f"  MDLOps:   {mdl_f[0]:12.6f} {mdl_f[1]:12.6f} {mdl_f[2]:12.6f}")

                # Check if they match
                orig_match_pyk = all(abs(orig_f[i] - pyk_f[i]) < 0.001 for i in range(3))
                orig_match_mdl = all(abs(orig_f[i] - mdl_f[i]) < 0.001 for i in range(3))
                print(f"  Original matches PyKotor: {orig_match_pyk}")
                print(f"  Original matches MDLOps: {orig_match_mdl}")

        # Check the first mesh node's data
        print("\n=== First Mesh Node Data ===")
        # The first mesh node (tongue/head) should have vertex/normal/UV data
        # Let's look at the internal model structure
        print("\nFirst few mesh nodes vertex data:")
        for node in mdl_obj.all_nodes()[:5]:
            if node.mesh and node.mesh.vertex_positions:
                print(f"\nNode: {node.name}")
                print(f"  Positions: {len(node.mesh.vertex_positions)}")
                print(f"  Normals: {len(node.mesh.vertex_normals) if node.mesh.vertex_normals else 0}")
                print(f"  UV1: {len(node.mesh.vertex_uv1) if node.mesh.vertex_uv1 else 0}")

                if node.mesh.vertex_normals:
                    n0 = node.mesh.vertex_normals[0]
                    print(f"  First normal: ({n0.x:.6f}, {n0.y:.6f}, {n0.z:.6f})")


if __name__ == "__main__":
    main()
