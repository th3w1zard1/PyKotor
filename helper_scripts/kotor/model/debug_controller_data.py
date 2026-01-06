"""Debug controller data writing to find MDLOps timeout issue."""

from __future__ import annotations

import tempfile

from pathlib import Path

from pykotor.common.misc import Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.mdl import read_mdl, write_mdl
from pykotor.resource.type import ResourceType
from pykotor.tools.path import find_kotor_paths_from_default


def debug_controller_data(model_name: str, game: Game):
    """Debug controller data for a specific model."""
    paths = find_kotor_paths_from_default()
    game_paths = paths.get(game, [])
    if not game_paths:
        print(f"No {game} installation found")
        return

    installation = Installation(game_paths[0])
    mdl_res = None
    mdx_res = None

    for res in installation:
        if res.resname() == model_name and res.restype() == ResourceType.MDL:
            mdl_res = res
        elif res.resname() == model_name and res.restype() == ResourceType.MDX:
            mdx_res = res

    if not mdl_res or not mdx_res:
        print(f"Model {model_name} not found")
        return

    with tempfile.TemporaryDirectory(prefix="mdl_debug_") as td:
        td_path = Path(td)
        test_mdl = td_path / f"{model_name}.mdl"
        test_mdx = td_path / f"{model_name}.mdx"

        test_mdl.write_bytes(mdl_res.data())
        test_mdx.write_bytes(mdx_res.data())

        print(f"Reading {model_name}...")
        mdl_obj = read_mdl(test_mdl, source_ext=test_mdx, file_format=ResourceType.MDL)
        if mdl_obj is None:
            print("Failed to read MDL")
            return

        # Check controller data
        print(f"\nModel has {len(mdl_obj.all_nodes())} nodes")
        for node in mdl_obj.all_nodes():
            if node.controllers:
                print(f"  Node {node.name}: {len(node.controllers)} controllers")
                for i, ctrl in enumerate(node.controllers):
                    print(f"    Controller {i}: type={ctrl.controller_type}, rows={len(ctrl.rows)}, compress_quaternions={mdl_obj.compress_quaternions}")
                    if ctrl.controller_type.value == 20:  # ORIENTATION
                        print(f"      First row data length: {len(ctrl.rows[0].data) if ctrl.rows else 0}")

        print("\nWriting PyKotor output...")
        pykotor_mdl = td_path / f"{model_name}-pykotor.mdl"
        pykotor_mdx = td_path / f"{model_name}-pykotor.mdx"

        try:
            write_mdl(mdl_obj, pykotor_mdl, ResourceType.MDL, target_ext=pykotor_mdx)

            # Read the binary header to check controller_data_length
            with open(pykotor_mdl, "rb") as f:
                data = f.read()
                # Skip MDL header (first 12 bytes: 3 uint32s)
                offset = 12  # noqa: F841
                # Read model header
                # Find first node header (after names, animations, etc.)
                # For now, just check file size
                print(f"PyKotor MDL size: {len(data)} bytes")
                print(f"PyKotor MDX size: {pykotor_mdx.stat().st_size} bytes")

        except Exception as e:
            print(f"Error: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    print("Debugging n_darkjedim.mdl (K1)...")
    debug_controller_data("n_darkjedim", Game.K1)
