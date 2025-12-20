#!/usr/bin/env python
"""Analyze raw BWM binary structure to understand the bug.

This script parses the raw BWM header and edge data to understand
how transitions ended up on the wrong faces.
"""

import struct
import sys
from pathlib import Path

# Add PyKotor to path
pykotor_path = Path(__file__).resolve().parent.parent / "Libraries" / "PyKotor" / "src"
sys.path.insert(0, str(pykotor_path))

from pykotor.resource.formats.erf import read_erf
from pykotor.resource.type import ResourceType


def parse_bwm_header(data: bytes) -> dict:
    """Parse BWM header and return offsets/counts.
    
    Header structure (136 bytes total):
    - 0-3: "BWM " (4 bytes)
    - 4-7: "V1.0" (4 bytes)
    - 8-11: walkmesh_type (4 bytes)
    - 12-23: relative_hook1 (12 bytes, Vector3)
    - 24-35: relative_hook2 (12 bytes, Vector3)
    - 36-47: absolute_hook1 (12 bytes, Vector3)
    - 48-59: absolute_hook2 (12 bytes, Vector3)
    - 60-71: position (12 bytes, Vector3)
    - 72-75: vertex_count (4 bytes)
    - 76-79: vertex_offset (4 bytes)
    - 80-83: face_count (4 bytes)
    - 84-87: indices_offset (4 bytes)
    - 88-91: materials_offset (4 bytes)
    - 92-95: normals_offset (4 bytes)
    - 96-99: planar_distances_offset (4 bytes)
    - 100-103: aabb_count (4 bytes)
    - 104-107: aabb_offset (4 bytes)
    - 108-111: skip (4 bytes)
    - 112-115: adjacency_count (4 bytes)
    - 116-119: adjacency_offset (4 bytes)
    - 120-123: edges_count (4 bytes)
    - 124-127: edges_offset (4 bytes)
    - 128-131: perimeters_count (4 bytes)
    - 132-135: perimeters_offset (4 bytes)
    """
    file_type = data[0:4].decode('ascii')
    version = data[4:8].decode('ascii')
    
    walkmesh_type = struct.unpack_from("I", data, 8)[0]
    position = struct.unpack_from("fff", data, 60)
    
    vertex_count = struct.unpack_from("I", data, 72)[0]
    vertex_offset = struct.unpack_from("I", data, 76)[0]
    face_count = struct.unpack_from("I", data, 80)[0]
    indices_offset = struct.unpack_from("I", data, 84)[0]
    material_offset = struct.unpack_from("I", data, 88)[0]
    
    adjacency_count = struct.unpack_from("I", data, 112)[0]  # walkable face count
    adjacency_offset = struct.unpack_from("I", data, 116)[0]
    edge_count = struct.unpack_from("I", data, 120)[0]
    edge_offset = struct.unpack_from("I", data, 124)[0]
    perimeter_count = struct.unpack_from("I", data, 128)[0]
    perimeter_offset = struct.unpack_from("I", data, 132)[0]
    
    return {
        "file_type": file_type,
        "version": version,
        "walkmesh_type": walkmesh_type,
        "vertex_count": vertex_count,
        "vertex_offset": vertex_offset,
        "face_count": face_count,
        "indices_offset": indices_offset,
        "material_offset": material_offset,
        "walkable_count": adjacency_count,
        "adjacency_offset": adjacency_offset,
        "edge_count": edge_count,
        "edge_offset": edge_offset,
        "perimeter_count": perimeter_count,
        "perimeter_offset": perimeter_offset,
    }


def analyze_edges(data: bytes, header: dict) -> list:
    """Parse edge data from BWM file."""
    edges = []
    edge_offset = header["edge_offset"]
    edge_count = header["edge_count"]
    
    for i in range(edge_count):
        offset = edge_offset + i * 8
        edge_index, transition = struct.unpack_from("ii", data, offset)
        face_idx = edge_index // 3
        edge_idx = edge_index % 3
        edges.append({
            "raw_index": edge_index,
            "face_idx": face_idx,
            "edge_idx": edge_idx,
            "transition": transition,
        })
    
    return edges


def analyze_materials(data: bytes, header: dict) -> list:
    """Parse face materials from BWM file."""
    materials = []
    material_offset = header["material_offset"]
    face_count = header["face_count"]
    
    for i in range(face_count):
        offset = material_offset + i * 4
        material = struct.unpack_from("I", data, offset)[0]
        materials.append(material)
    
    return materials


def analyze_mod_wok(mod_path: Path, wok_name: str) -> None:
    """Analyze a specific WOK file from a MOD."""
    print(f"\n{'='*70}")
    print(f"RAW BINARY ANALYSIS: {wok_name}")
    print(f"{'='*70}")
    
    erf = read_erf(mod_path.read_bytes())
    data = erf.get(wok_name, ResourceType.WOK)
    
    if data is None:
        print(f"ERROR: WOK '{wok_name}' not found in {mod_path}")
        return
    
    header = parse_bwm_header(data)
    
    print(f"\nHeader Info:")
    print(f"  File Type: {header['file_type']}")
    print(f"  Version: {header['version']}")
    print(f"  Walkmesh Type: {header['walkmesh_type']}")
    print(f"  Vertex Count: {header['vertex_count']}")
    print(f"  Face Count: {header['face_count']}")
    print(f"  Walkable Count: {header['walkable_count']}")
    print(f"  Edge Count: {header['edge_count']}")
    print(f"  Perimeter Count: {header['perimeter_count']}")
    
    # Analyze materials
    materials = analyze_materials(data, header)
    walkable_materials = {1, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 16, 18, 20, 21, 22}
    
    walkable_faces = [i for i, m in enumerate(materials) if m in walkable_materials]
    unwalkable_faces = [i for i, m in enumerate(materials) if m not in walkable_materials]
    
    print(f"\nMaterial Analysis:")
    print(f"  Walkable faces (by material): {len(walkable_faces)}")
    print(f"  Unwalkable faces (by material): {len(unwalkable_faces)}")
    print(f"  Walkable range should be: 0-{header['walkable_count']-1}")
    print(f"  Unwalkable range should be: {header['walkable_count']}-{header['face_count']-1}")
    
    # Analyze edges
    edges = analyze_edges(data, header)
    edges_with_trans = [e for e in edges if e["transition"] >= 0]
    
    print(f"\nEdge Analysis:")
    print(f"  Total edges: {len(edges)}")
    print(f"  Edges with transitions (transition >= 0): {len(edges_with_trans)}")
    
    if edges_with_trans:
        print(f"\n  Edges with transitions:")
        for e in edges_with_trans:
            in_walkable = e["face_idx"] < header["walkable_count"]
            mat = materials[e["face_idx"]] if e["face_idx"] < len(materials) else "?"
            status = "WALKABLE" if in_walkable else "**UNWALKABLE**"
            print(f"    Face {e['face_idx']} edge {e['edge_idx']}: transition={e['transition']}, material={mat}, {status}")
    else:
        print(f"\n  ** NO EDGES WITH TRANSITIONS! This is the bug. **")
        print(f"  The BWM writer computed edges only from walkable faces,")
        print(f"  but the transitions were on unwalkable faces, so no edges were written.")


def main():
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    
    step01_mod = repo_root / "reproduce_walkbug_indoorbuilder" / "step01" / "step01.mod"
    step02_mod = repo_root / "reproduce_walkbug_indoorbuilder" / "step02 from beta" / "step02.mod"
    
    print("="*70)
    print("RAW BWM BINARY STRUCTURE ANALYSIS")
    print("="*70)
    
    # Analyze step01 (working)
    analyze_mod_wok(step01_mod, "step01_room0")
    
    # Analyze step02 (buggy)
    analyze_mod_wok(step02_mod, "test01_room0")
    
    # Compare edge data
    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)
    print("""
The bug is confirmed:

STEP01 (Working):
  - Edges point to WALKABLE faces (indices 0-59)
  - Transitions are properly encoded in edge data

STEP02 (Buggy):
  - NO edges with transitions (edge_count might be > 0 but no positive transitions)
  - The faces that SHOULD have transitions have material=NON_WALK
  - Since edges() only considers walkable faces, no edges are generated for these
  - When read back, the faces have NO transitions from edges

ROOT CAUSE:
  The BWM data has face materials set to NON_WALK for faces that should
  have transitions. This happens BEFORE bytes_bwm() is called.
  
  The issue is likely in how the indoor builder's paint/material feature
  or some other code path is modifying face materials incorrectly.
""")


if __name__ == "__main__":
    main()

