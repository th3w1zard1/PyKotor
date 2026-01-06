#!/usr/bin/env python
"""Check MDLOps ASCII output to understand vertex placement."""

from __future__ import annotations

import subprocess
import sys
import tempfile

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "Libraries" / "PyKotor" / "src"))

from pykotor.common.misc import Game
from pykotor.extract.file import ResourceResult
from pykotor.extract.installation import Installation
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath, find_kotor_paths_from_default


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

    with tempfile.TemporaryDirectory(prefix="mdlops_") as td:
        td_path = Path(td)

        # Write original
        orig_mdl_path = td_path / f"{model_name}.mdl"
        orig_mdx_path = td_path / f"{model_name}.mdx"
        orig_mdl_path.write_bytes(mdl_res.data if mdl_res.data else b"")
        orig_mdx_path.write_bytes(mdx_res.data if mdx_res.data else b"")

        # Decompile with MDLOps
        result = subprocess.run(
            [str(mdlops_exe), str(orig_mdl_path)],
            cwd=str(td_path),
            capture_output=True,
            timeout=60,
        )

        ascii_path = td_path / f"{model_name}-ascii.mdl"
        if not ascii_path.exists():
            print(f"MDLOps failed: {result.stderr.decode()}")
            return

        ascii_content = ascii_path.read_text()

        # Find mesh nodes and check their vertex info
        print("=== MDLOps ASCII vertex info ===")
        lines = ascii_content.split("\n")
        current_node = None
        in_node = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            if stripped.startswith("node trimesh") or stripped.startswith("node skin") or stripped.startswith("node danglymesh"):
                current_node = stripped.split()[-1]
                in_node = True
                print(f"\n{stripped}")
                continue

            if in_node and stripped == "endnode":
                in_node = False
                current_node = None
                continue

            if in_node and (any(stripped.startswith(kw) for kw in ["verts ", "tverts ", "bitmap ", "texture0 ", "render "])):
                print(f"  {stripped}")
                continue


if __name__ == "__main__":
    main()
