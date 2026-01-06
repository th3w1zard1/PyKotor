#!/usr/bin/env python
"""Compare binary structure of original vs PyKotor MDL."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from io import BytesIO
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "Libraries" / "PyKotor" / "src"))

from pykotor.common.misc import Game
from pykotor.common.stream import BinaryReader
from pykotor.extract.installation import Installation
from pykotor.resource.formats.mdl import read_mdl, write_mdl
from pykotor.resource.formats.mdl.io_mdl import _ModelHeader, _NodeHeader, _TrimeshHeader
from pykotor.resource.formats.mdl.mdl_types import MDLNodeFlags
from pykotor.resource.type import ResourceType


def walk_nodes(mdl_bytes: bytes, game: Game, verbose: bool = False) -> list[dict]:
    """Walk all nodes in MDL and return their metadata."""
    reader = BinaryReader.from_auto(mdl_bytes, 0)
    reader.set_offset(reader.offset() + 12)
    
    try:
        header = _ModelHeader().read(reader)
    except Exception as e:
        print(f"ERROR reading header: {e}")
        return []
    
    if verbose:
        print(f"  Root node offset: {header.geometry.root_node_offset}")
    
    file_size = len(mdl_bytes)
    nodes: list[dict] = []
    seen: set[int] = set()

    def walk(offset: int, depth: int = 0) -> None:
        if offset in seen:
            return
        if offset == 0 or offset >= file_size:
            if verbose and offset != 0:
                print(f"  Skipping invalid offset {offset}")
            return
        seen.add(offset)

        try:
            reader.seek(offset)
            hdr = _NodeHeader().read(reader)
        except Exception as e:
            if verbose:
                print(f"  ERROR reading node at {offset}: {e}")
            return

        if hdr.node_id > 1000:
            if verbose:
                print(f"  Skipping node with invalid id {hdr.node_id} at {offset}")
            return

        is_mesh = bool(hdr.type_id & MDLNodeFlags.MESH)
        is_skin = bool(hdr.type_id & 0x40)
        
        if verbose:
            print(f"  {'  '*depth}Node {hdr.node_id} @ {offset}: type=0x{hdr.type_id:04X}, children={hdr.children_count}")
        
        node_info = {
            "offset": offset,
            "node_id": hdr.node_id,
            "type_id": hdr.type_id,
            "is_mesh": is_mesh,
            "is_skin": is_skin,
            "children_count": hdr.children_count,
            "offset_to_children": hdr.offset_to_children,
        }
        
        if is_mesh:
            try:
                tri = _TrimeshHeader().read(reader, game)
                node_info["vertex_count"] = tri.vertex_count
                node_info["mdx_data_offset"] = tri.mdx_data_offset
                node_info["mdx_data_size"] = tri.mdx_data_size
                node_info["mdx_data_bitmap"] = tri.mdx_data_bitmap
                if verbose:
                    print(f"  {'  '*depth}  -> mesh: verts={tri.vertex_count}, row_size={tri.mdx_data_size}")
            except Exception as e:
                node_info["error"] = str(e)
                if verbose:
                    print(f"  {'  '*depth}  -> ERROR reading trimesh: {e}")
        
        nodes.append(node_info)

        if hdr.children_count > 0 and hdr.children_count < 100:
            if 0 < hdr.offset_to_children < file_size:
                try:
                    reader.seek(hdr.offset_to_children)
                    child_offsets = []
                    for _ in range(hdr.children_count):
                        child_off = reader.read_uint32()
                        child_offsets.append(child_off)
                    
                    valid_children = [c for c in child_offsets if 0 < c < file_size]
                    invalid_children = [c for c in child_offsets if c <= 0 or c >= file_size]
                    
                    if verbose and invalid_children:
                        print(f"  {'  '*depth}  -> Invalid children: {invalid_children[:5]}{'...' if len(invalid_children) > 5 else ''}")
                    
                    for child_off in valid_children:
                        walk(child_off, depth + 1)
                except Exception as e:
                    if verbose:
                        print(f"  {'  '*depth}  -> ERROR reading children: {e}")
            elif verbose:
                print(f"  {'  '*depth}  -> Invalid children offset: {hdr.offset_to_children}")

    walk(header.geometry.root_node_offset)
    return nodes


def main() -> None:
    resref = "comm_b_f2"
    k1_path = Path(r"C:/Program Files (x86)/Steam/steamapps/common/swkotor")
    inst = Installation(k1_path)

    mdl_res = inst.resource(resref, ResourceType.MDL)
    mdx_res = inst.resource(resref, ResourceType.MDX)
    assert mdl_res is not None and mdx_res is not None

    orig_mdl = mdl_res.data
    orig_mdx = mdx_res.data

    print("=" * 80)
    print("ORIGINAL MDL")
    print("=" * 80)
    orig_nodes = walk_nodes(orig_mdl, Game.K1, verbose=True)
    print(f"Total nodes: {len(orig_nodes)}")
    mesh_nodes = [n for n in orig_nodes if n["is_mesh"]]
    print(f"Mesh nodes: {len(mesh_nodes)}")
    print()
    for n in sorted(mesh_nodes, key=lambda x: x["node_id"]):
        bitmap = n.get("mdx_data_bitmap", 0)
        size = n.get("mdx_data_size", 0)
        verts = n.get("vertex_count", 0)
        print(f"  Node {n['node_id']:>3}: verts={verts:>4}, row_size={size:>3}, bitmap=0x{bitmap:08X}")
    print()

    # Generate PyKotor roundtrip
    mdl = read_mdl(orig_mdl, source_ext=orig_mdx)
    pk_mdl_out = BytesIO()
    pk_mdx_out = BytesIO()
    write_mdl(mdl, pk_mdl_out, ResourceType.MDL, target_ext=pk_mdx_out)
    pk_mdl = pk_mdl_out.getvalue()
    pk_mdx = pk_mdx_out.getvalue()

    print("=" * 80)
    print("PYKOTOR ROUNDTRIP MDL")
    print("=" * 80)
    pk_nodes = walk_nodes(pk_mdl, Game.K1, verbose=True)
    print(f"Total nodes: {len(pk_nodes)}")
    mesh_nodes = [n for n in pk_nodes if n["is_mesh"]]
    print(f"Mesh nodes: {len(mesh_nodes)}")
    print()
    for n in sorted(mesh_nodes, key=lambda x: x["node_id"]):
        bitmap = n.get("mdx_data_bitmap", 0)
        size = n.get("mdx_data_size", 0)
        verts = n.get("vertex_count", 0)
        print(f"  Node {n['node_id']:>3}: verts={verts:>4}, row_size={size:>3}, bitmap=0x{bitmap:08X}")
    print()

    # Generate MDLOps roundtrip
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        (td_path / f"{resref}.mdl").write_bytes(orig_mdl)
        (td_path / f"{resref}.mdx").write_bytes(orig_mdx)

        mdlops_exe = REPO_ROOT / "vendor" / "MDLOps" / "mdlops.exe"
        subprocess.run([str(mdlops_exe), str(td_path / f"{resref}.mdl")], cwd=str(td_path), capture_output=True)
        # MDLOps requires flags before file path: mdlops.exe [options] [-k1|-k2] filepath
        subprocess.run([str(mdlops_exe), "-k1", str(td_path / f"{resref}-ascii.mdl")], cwd=str(td_path), capture_output=True)

        mo_mdl = (td_path / f"{resref}-ascii-k1-bin.mdl").read_bytes()
        mo_mdx = (td_path / f"{resref}-ascii-k1-bin.mdx").read_bytes()

    print("=" * 80)
    print("MDLOPS ROUNDTRIP MDL")
    print("=" * 80)
    mo_nodes = walk_nodes(mo_mdl, Game.K1)
    print(f"Total nodes: {len(mo_nodes)}")
    mesh_nodes = [n for n in mo_nodes if n["is_mesh"]]
    print(f"Mesh nodes: {len(mesh_nodes)}")
    print()
    for n in sorted(mesh_nodes, key=lambda x: x["node_id"]):
        bitmap = n.get("mdx_data_bitmap", 0)
        size = n.get("mdx_data_size", 0)
        verts = n.get("vertex_count", 0)
        print(f"  Node {n['node_id']:>3}: verts={verts:>4}, row_size={size:>3}, bitmap=0x{bitmap:08X}")
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"MDL sizes: Original={len(orig_mdl)}, PyKotor={len(pk_mdl)}, MDLOps={len(mo_mdl)}")
    print(f"MDX sizes: Original={len(orig_mdx)}, PyKotor={len(pk_mdx)}, MDLOps={len(mo_mdx)}")


if __name__ == "__main__":
    main()

