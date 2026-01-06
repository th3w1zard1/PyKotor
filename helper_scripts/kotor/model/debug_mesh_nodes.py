#!/usr/bin/env python
"""Debug script to compare mesh node MDX metadata between PyKotor and MDLOps."""

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


def parse_mesh_nodes(mdl_bytes: bytes, game: Game) -> list[dict]:
    """Parse mesh nodes from binary MDL and extract MDX metadata."""
    reader = BinaryReader.from_auto(mdl_bytes, 0)
    reader.set_offset(reader.offset() + 12)
    header = _ModelHeader().read(reader)

    nodes: list[dict] = []
    seen: set[int] = set()
    file_size = len(mdl_bytes)

    def walk(offset: int) -> None:
        # Sanity checks
        if offset in seen:
            return
        if offset == 0 or offset >= file_size:
            return
        seen.add(offset)

        try:
            reader.seek(offset)
            node_hdr = _NodeHeader().read(reader)
        except OSError:
            return  # Invalid offset

        # Validate node_id - should be reasonable
        if node_hdr.node_id > 1000:
            return  # Garbage data

        is_mesh = bool(node_hdr.type_id & MDLNodeFlags.MESH)
        is_skin = bool(node_hdr.type_id & 0x40)  # SKIN flag

        if is_mesh:
            # Read trimesh header
            try:
                trimesh = _TrimeshHeader().read(reader, game)
                # Validate trimesh data
                if trimesh.vertex_count < 10000 and trimesh.mdx_data_size < 1000:
                    nodes.append({
                        "node_id": node_hdr.node_id,
                        "type": "skin" if is_skin else "mesh",
                        "vertex_count": trimesh.vertex_count,
                        "mdx_data_offset": trimesh.mdx_data_offset,
                        "mdx_data_size": trimesh.mdx_data_size,
                        "mdx_data_bitmap": trimesh.mdx_data_bitmap,
                        "texture1": trimesh.texture1 or "NULL",
                    })
            except OSError:
                pass  # Ignore OOB reads

        # Walk children (with sanity checks to avoid reading garbage)
        if node_hdr.children_count > 0 and node_hdr.children_count < 100:
            if 0 < node_hdr.offset_to_children < file_size:
                try:
                    reader.seek(node_hdr.offset_to_children)
                    for _ in range(node_hdr.children_count):
                        child_off = reader.read_uint32()
                        # Sanity check: offset must be within reasonable bounds
                        if 0 < child_off < file_size:
                            walk(child_off)
                except OSError:
                    pass  # Ignore OOB offsets

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

    # Parse ORIGINAL mesh nodes first
    print("=" * 80)
    print("ORIGINAL MDL mesh nodes:")
    print("=" * 80)
    orig_nodes = parse_mesh_nodes(orig_mdl, Game.K1)
    
    print(f"Found {len(orig_nodes)} mesh nodes")
    print()
    print(f"{'ID':>3} {'Tex':<12} {'Type':<5} {'Verts':>6} {'Row':>5} {'Bitmap':>12} {'MDX Off':>10} {'MDX Bytes':>10}")
    print("-" * 80)
    
    total_mdx_orig = 0
    for n in sorted(orig_nodes, key=lambda x: x["node_id"]):
        mdx_bytes = n["vertex_count"] * n["mdx_data_size"]
        total_mdx_orig += mdx_bytes
        print(
            f"{n['node_id']:>3} {n['texture1'][:12]:<12} {n['type']:<5} "
            f"{n['vertex_count']:>6} {n['mdx_data_size']:>5} "
            f"0x{n['mdx_data_bitmap']:08X} {n['mdx_data_offset']:>10} {mdx_bytes:>10}"
        )
    print("-" * 80)
    print(f"Total MDX from headers: {total_mdx_orig} bytes")
    print(f"Actual MDX file size: {len(orig_mdx)} bytes")
    print()

    # Generate PyKotor roundtrip
    mdl = read_mdl(orig_mdl, source_ext=orig_mdx)
    pk_mdl_out = BytesIO()
    pk_mdx_out = BytesIO()
    write_mdl(mdl, pk_mdl_out, ResourceType.MDL, target_ext=pk_mdx_out)
    pk_mdl = pk_mdl_out.getvalue()
    pk_mdx = pk_mdx_out.getvalue()

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
    print("COMPARISON: PyKotor vs MDLOps roundtrip")
    print("=" * 80)
    print("MDL/MDX sizes:")
    print(f"  Original: MDL={len(orig_mdl)}, MDX={len(orig_mdx)}")
    print(f"  PyKotor:  MDL={len(pk_mdl)}, MDX={len(pk_mdx)}")
    print(f"  MDLOps:   MDL={len(mo_mdl)}, MDX={len(mo_mdx)}")
    print()

    # Parse mesh nodes
    pk_nodes = parse_mesh_nodes(pk_mdl, Game.K1)
    mo_nodes = parse_mesh_nodes(mo_mdl, Game.K1)

    print(f"Mesh nodes parsed: PyKotor={len(pk_nodes)}, MDLOps={len(mo_nodes)}")
    print()

    pk_by_id = {n["node_id"]: n for n in pk_nodes}
    mo_by_id = {n["node_id"]: n for n in mo_nodes}

    # Calculate total MDX data per source
    pk_total = sum(n["vertex_count"] * n["mdx_data_size"] for n in pk_nodes)
    mo_total = sum(n["vertex_count"] * n["mdx_data_size"] for n in mo_nodes)
    print(f"Total MDX data from mesh headers:")
    print(f"  PyKotor: {pk_total} bytes")
    print(f"  MDLOps:  {mo_total} bytes")
    print(f"  Difference: {pk_total - mo_total:+d} bytes")
    print()

    print("Node-by-node comparison (only mismatches):")
    print(f"{'ID':>3} {'Tex':<12} {'PK row':>7} {'MO row':>7} {'PK bitmap':>12} {'MO bitmap':>12} {'Issue':>20}")
    print("-" * 90)

    mismatch_count = 0
    for node_id in sorted(set(pk_by_id.keys()) | set(mo_by_id.keys())):
        pk = pk_by_id.get(node_id)
        mo = mo_by_id.get(node_id)

        if pk and mo:
            issues = []
            if pk["mdx_data_size"] != mo["mdx_data_size"]:
                issues.append(f"row {pk['mdx_data_size']}!={mo['mdx_data_size']}")
            if pk["mdx_data_bitmap"] != mo["mdx_data_bitmap"]:
                issues.append("bitmap")
            if pk["vertex_count"] != mo["vertex_count"]:
                issues.append(f"verts {pk['vertex_count']}!={mo['vertex_count']}")
            
            if issues:
                mismatch_count += 1
                print(
                    f"{node_id:>3} {pk['texture1'][:12]:<12} "
                    f"{pk['mdx_data_size']:>7} {mo['mdx_data_size']:>7} "
                    f"0x{pk['mdx_data_bitmap']:08X} 0x{mo['mdx_data_bitmap']:08X} "
                    f"{', '.join(issues):>20}"
                )
        elif pk:
            mismatch_count += 1
            print(f"{node_id:>3} {pk['texture1'][:12]:<12}  ONLY in PyKotor")
        elif mo:
            mismatch_count += 1
            print(f"{node_id:>3} {mo['texture1'][:12]:<12}  ONLY in MDLOps")
    
    if mismatch_count == 0:
        print("  (No mismatches - all nodes match)")
    print()
    print(f"Total mismatches: {mismatch_count}")


if __name__ == "__main__":
    main()

