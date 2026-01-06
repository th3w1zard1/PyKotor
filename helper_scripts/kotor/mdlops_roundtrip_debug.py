from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from pykotor.common.misc import Game
from pykotor.common.stream import BinaryReader
from pykotor.extract.installation import Installation
from pykotor.resource.formats.mdl import read_mdl, write_mdl
from pykotor.resource.formats.mdl.io_mdl import _ModelHeader, _Node
from pykotor.resource.type import ResourceType
from pykotor.tools.path import find_kotor_paths_from_default


def _parse_game(value: str) -> Game:
    v = value.strip().lower()
    if v in {"k1", "kotOR1", "kotor1"}:
        return Game.K1
    if v in {"k2", "tsl", "kotOR2", "kotor2"}:
        return Game.K2
    raise argparse.ArgumentTypeError(f"Invalid --game: {value!r} (expected k1 or k2)")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Roundtrip a single MDL/MDX through PyKotor and MDLOps, keeping outputs for inspection.",
    )
    parser.add_argument("resname", help="Resource name without extension (e.g. m10ac_28d)")
    parser.add_argument("--game", type=_parse_game, default=Game.K1, help="Game: k1 or k2 (default: k1)")
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("_tmp_mdl_debug"),
        help="Output directory (default: _tmp_mdl_debug)",
    )
    parser.add_argument(
        "--mdlops",
        type=Path,
        default=Path("vendor/MDLOps/mdlops.exe"),
        help="Path to mdlops.exe (default: vendor/MDLOps/mdlops.exe)",
    )
    args = parser.parse_args()

    paths = find_kotor_paths_from_default().get(args.game, [])
    if not paths:
        raise SystemExit(f"No install paths found for {args.game.name}")

    inst = Installation(paths[0])
    mdl_res = inst.resource(args.resname, ResourceType.MDL)
    mdx_res = inst.resource(args.resname, ResourceType.MDX)
    if mdl_res is None or mdx_res is None:
        raise SystemExit(f"Missing MDL/MDX for {args.resname!r} in {paths[0]!s}")

    args.outdir.mkdir(parents=True, exist_ok=True)
    orig_mdl = args.outdir / f"{args.resname}.mdl"
    orig_mdx = args.outdir / f"{args.resname}.mdx"
    def _res_bytes(res) -> bytes:
        data_attr = getattr(res, "data", None)
        if callable(data_attr):
            return data_attr()
        if isinstance(data_attr, (bytes, bytearray, memoryview)):
            return bytes(data_attr)
        raise TypeError(f"Unsupported resource data for {res!r}")

    orig_mdl.write_bytes(_res_bytes(mdl_res))
    orig_mdx.write_bytes(_res_bytes(mdx_res))

    mdl_obj = read_mdl(orig_mdl, source_ext=orig_mdx, file_format=ResourceType.MDL)
    if mdl_obj is None:
        raise SystemExit("PyKotor read_mdl returned None")

    py_mdl = args.outdir / f"{args.resname}-pykotor.mdl"
    py_mdx = args.outdir / f"{args.resname}-pykotor.mdx"
    write_mdl(mdl_obj, py_mdl, ResourceType.MDL, target_ext=py_mdx)

    # Dump key node offsets for quick sanity checks.
    r = BinaryReader.from_auto(py_mdl)
    r.set_offset(r.offset() + 12)
    h = _ModelHeader().read(r)
    root = h.geometry.root_node_offset
    print(f"root={root} node_count={h.geometry.node_count}")

    seen: set[int] = set()
    stack: list[int] = [root]
    while stack:
        off = stack.pop()
        if off in seen:
            continue
        seen.add(off)
        r.seek(off)
        bn = _Node().read(r, args.game)
        hdr = bn.header
        if hdr is None:
            continue
        if bn.trimesh is not None:
            t = bn.trimesh
            need = int(t.vertex_count) * 12
            ok = t.vertices_offset not in (0, 0xFFFFFFFF) and (t.vertices_offset + need) <= r.size()
            print(
                "mesh",
                f"node_off={off}",
                f"type=0x{hdr.type_id:04X}",
                f"node_id={hdr.node_id}",
                f"faces={t.faces_count}",
                f"vcount={t.vertex_count}",
                f"faces_ptr=0x{t.offset_to_faces:08X}",
                f"vert_ptr=0x{t.vertices_offset:08X}",
                f"vert_bytes_ok={ok}",
            )
        stack.extend(bn.children_offsets)
    print(f"visited={len(seen)}")

    if args.mdlops.exists():
        subprocess.run([str(args.mdlops), orig_mdl.name], cwd=str(args.outdir), check=False)
        subprocess.run([str(args.mdlops), py_mdl.name], cwd=str(args.outdir), check=False)
        print("MDLOps done.")
    else:
        print(f"MDLOps not found at {args.mdlops!s} (skipping decompile)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


