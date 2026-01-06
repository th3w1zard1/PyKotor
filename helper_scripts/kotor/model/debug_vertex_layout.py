#!/usr/bin/env python
"""Debug script to analyze vertex data layout in MDL vs MDX."""

from __future__ import annotations

import sys

sys.path.insert(0, "Libraries/PyKotor/src")

from io import BytesIO

from pykotor.common.misc import Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.mdl import write_mdl
from pykotor.resource.formats.mdl.io_mdl import MDLBinaryReader, MDLBinaryWriter, _ModelHeader, _Node, _NodeHeader, _TrimeshHeader
from pykotor.resource.type import ResourceType
from pykotor.tools.path import find_kotor_paths_from_default

k1_path = find_kotor_paths_from_default()[Game.K1][0]
inst = Installation(k1_path)

mdl_res = inst.resource("comm_b_f2", ResourceType.MDL)
mdx_res = inst.resource("comm_b_f2", ResourceType.MDX)

assert mdl_res is not None, "MDL resource not found"
assert mdx_res is not None, "MDX resource not found"
assert mdl_res.data is not None, "MDL data not found"
assert mdx_res.data is not None, "MDX data not found"

print(f"Original MDL: {len(mdl_res.data)}, MDX: {len(mdx_res.data)}")

# Read the original binary to check vertices_offset values
print("\n=== Original Binary Vertices Offsets ===")
reader = MDLBinaryReader(mdl_res.data, source_ext=mdx_res.data)
original_load_node = reader._load_node
orig_vertex_data = []


def capture_orig_load_node(offset, parent):
    reader._reader.seek(offset)
    bin_header = _NodeHeader().read(reader._reader)

    if bin_header.type_id & 0x20:  # MESH flag
        trimesh = _TrimeshHeader()
        trimesh.read(reader._reader, Game.K1)
        orig_vertex_data.append(
            {
                "node_id": bin_header.node_id,
                "mdx_data_offset": trimesh.mdx_data_offset,
                "vertices_offset": trimesh.vertices_offset,
                "vertex_count": trimesh.vertex_count,
            }
        )

    return original_load_node(offset, parent)


reader._load_node = capture_orig_load_node
mdl = reader.load()

print(f"{'NodeID':<8} {'VCount':<8} {'MDX_off':<12} {'MDL_verts_off':<15}")
print("-" * 50)
for d in orig_vertex_data[:10]:
    print(f"{d['node_id']:<8} {d['vertex_count']:<8} {d['mdx_data_offset']:<12} {d['vertices_offset']:<15}")

# Calculate how much vertex data is in original MDL vertex blocks
total_orig_mdl_verts_bytes = sum(d["vertex_count"] * 12 for d in orig_vertex_data if d["vertices_offset"] not in (0, 0xFFFFFFFF))
print(f"\nTotal original MDL vertex bytes: {total_orig_mdl_verts_bytes}")
print(f"Total vertices: {sum(d['vertex_count'] for d in orig_vertex_data)}")

# Write with PyKotor
print("\n=== Write Test ===")
mdl_out = BytesIO()
mdx_out = BytesIO()
write_mdl(mdl, mdl_out, file_format=ResourceType.MDL, target_ext=mdx_out)
pykotor_mdl = mdl_out.getvalue()
pykotor_mdx = mdx_out.getvalue()

print(f"Original MDL: {len(mdl_res.data)}")
print(f"PyKotor MDL: {len(pykotor_mdl)}")
print(f"MDL diff: {len(pykotor_mdl) - len(mdl_res.data)}")
print(f"\nOriginal MDX: {len(mdx_res.data)}")
print(f"PyKotor MDX: {len(pykotor_mdx)}")
print(f"MDX diff: {len(pykotor_mdx) - len(mdx_res.data)}")

# Now simulate writer to check what vertices PyKotor thinks it's writing
print("\n=== PyKotor Writer Analysis ===")
writer = MDLBinaryWriter(mdl, BytesIO(), target_ext=BytesIO())
writer._mdl_nodes[:] = mdl.all_nodes()
writer._bin_nodes[:] = [_Node() for _ in writer._mdl_nodes]
writer._bin_anims[:] = []
writer._names = [n.name for n in writer._mdl_nodes]
writer._anim_offsets = []
writer._node_offsets = [0 for _ in writer._bin_nodes]
writer.game = Game.K1
writer._update_all_data()

# Check what vertices bin_nodes have
total_pykotor_verts_bytes = sum(bn.trimesh.vertices_size() if bn.trimesh else 0 for bn in writer._bin_nodes)
print(f"PyKotor would write vertex bytes: {total_pykotor_verts_bytes}")

# Summary
print("\n=== Summary ===")
print(f"Original has {total_orig_mdl_verts_bytes} bytes of MDL vertex data")
print(f"PyKotor writes {total_pykotor_verts_bytes} bytes of MDL vertex data")
print(f"Both write same vertex data to MDL: {total_orig_mdl_verts_bytes == total_pykotor_verts_bytes}")
print()
print(f"But MDL size difference is: {len(pykotor_mdl) - len(mdl_res.data)} bytes")
print(f"This suggests original has {len(mdl_res.data) - len(pykotor_mdl)} extra bytes not from vertices")

# Investigate where the extra bytes come from
print("\n=== Investigating Extra Data ===")

# Calculate expected sizes for various components
header_size = _ModelHeader.SIZE
print(f"Header size: {header_size}")

# Name data
orig_names = [n.name for n in mdl.all_nodes()]
name_offsets_size = 4 * len(orig_names)
names_size = sum(len(name) + 1 for name in orig_names)
print(f"Name offsets: {name_offsets_size}, Names: {names_size}")

# Animation data
anim_count = len(mdl.anims)
print(f"Animation count: {anim_count}")

# Calculate total controller data
total_controllers = 0
total_controller_data = 0
for node in mdl.all_nodes():
    total_controllers += len(node.controllers)
    for ctrl in node.controllers:
        # Each row has 1 timekey + len(data) values
        for row in ctrl.rows:
            total_controller_data += 1 + len(row.data)  # timekey + values

print(f"Total controllers: {total_controllers}")
print(f"Total controller floats: {total_controller_data}")
print(f"Controller data bytes: {total_controller_data * 4}")

# Check faces
total_faces = sum(len(node.mesh.faces) if node.mesh else 0 for node in mdl.all_nodes())
face_struct_size = 32  # Size of _Face struct
total_face_bytes = total_faces * face_struct_size
print(f"Total faces: {total_faces}, bytes: {total_face_bytes}")

# Check skin data
total_skin_bones = 0
total_bonemap = 0
total_qbones = 0
total_tbones = 0
for node in mdl.all_nodes():
    if node.skin:
        # Each bone vertex has 4 indices + 4 weights = 8 values
        total_skin_bones += len(node.skin.vertex_bones) if node.skin.vertex_bones else 0
        total_bonemap += len(node.skin.bonemap) if node.skin.bonemap else 0
        total_qbones += len(node.skin.qbones) if node.skin.qbones else 0
        total_tbones += len(node.skin.tbones) if node.skin.tbones else 0
print(f"Total skin bone vertices: {total_skin_bones}")
print(f"Total bonemap entries: {total_bonemap} ({total_bonemap * 4} bytes)")
print(f"Total qbones: {total_qbones} ({total_qbones * 16} bytes)")
print(f"Total tbones: {total_tbones} ({total_tbones * 12} bytes)")
total_skin_extra = total_bonemap * 4 + total_qbones * 16 + total_tbones * 12
print(f"Total skin extra bytes: {total_skin_extra}")

# Check indices arrays
total_indices_counts = 0
total_indices_offsets = 0
total_inverted_counters = 0
for node in mdl.all_nodes():
    if node.mesh:
        total_indices_counts += len(node.mesh.indices_counts) if node.mesh.indices_counts else 0
        total_indices_offsets += len(node.mesh.indices_offsets) if node.mesh.indices_offsets else 0
        total_inverted_counters += len(node.mesh.inverted_counters) if node.mesh.inverted_counters else 0
print(f"Total indices_counts: {total_indices_counts}")
print(f"Total indices_offsets: {total_indices_offsets}")
print(f"Total inverted_counters: {total_inverted_counters}")

# Now compare calc_size per node between original reader and writer
print("\n=== Per-Node Size Comparison ===")

import struct

mdl_bytes = mdl_res.data

# Model header has root_node_offset at a known location
geom_root_offset = struct.unpack_from("<I", mdl_bytes, 12 + 8 + 32)[0]
print(f"Root node offset (in file): {geom_root_offset + 12}")

# Compare with PyKotor's calculation
total_calc_size = sum(bn.calc_size(Game.K1) for bn in writer._bin_nodes)
print(f"PyKotor total calc_size for all nodes: {total_calc_size}")

# Calculate complete expected size breakdown
print("\n=== Complete Size Breakdown ===")
node_header_size = 80  # _NodeHeader.SIZE
trimesh_header_k1 = 332  # _TrimeshHeader.SIZE_K1
skin_header = 64  # _SkinmeshHeader.SIZE
controller_struct = 16  # _Controller.SIZE

# Count different node types
dummy_nodes = 0
mesh_only_nodes = 0
skin_nodes = 0
for node in mdl.all_nodes():
    if node.skin:
        skin_nodes += 1
    elif node.mesh:
        mesh_only_nodes += 1
    else:
        dummy_nodes += 1

print(f"Dummy nodes: {dummy_nodes}")
print(f"Mesh-only nodes: {mesh_only_nodes}")
print(f"Skin nodes: {skin_nodes}")

# Expected header bytes
expected_node_headers = len(mdl.all_nodes()) * node_header_size
expected_trimesh_headers = (mesh_only_nodes + skin_nodes) * trimesh_header_k1
expected_skin_headers = skin_nodes * skin_header
expected_controller_structs = total_controllers * controller_struct

print(f"\nExpected node headers: {expected_node_headers}")
print(f"Expected trimesh headers: {expected_trimesh_headers}")
print(f"Expected skin headers: {expected_skin_headers}")
print(f"Expected controller structs: {expected_controller_structs}")
print(f"Expected controller data: {total_controller_data * 4}")
print(f"Expected faces: {total_face_bytes}")
print(f"Expected vertices: {total_pykotor_verts_bytes}")
print(f"Expected skin extra: {total_skin_extra}")
print(f"Expected indices arrays: {(total_indices_counts + total_indices_offsets + total_inverted_counters) * 4}")

# Children offsets (4 bytes per child reference)
total_children = sum(len(node.children) for node in mdl.all_nodes())
expected_children_offsets = total_children * 4
print(f"Expected children offsets: {expected_children_offsets}")

# Sum up expected data section
expected_data = (
    header_size  # Model header
    + name_offsets_size  # Name offsets array
    + names_size  # Name strings
    + expected_node_headers
    + expected_trimesh_headers
    + expected_skin_headers
    + expected_controller_structs
    + (total_controller_data * 4)
    + total_face_bytes
    + total_pykotor_verts_bytes
    + total_skin_extra
    + ((total_indices_counts + total_indices_offsets + total_inverted_counters) * 4)
    + expected_children_offsets
)

print("\n=== Size Comparison ===")
print(f"Expected (calculated): {expected_data}")
print(f"PyKotor actual output: {len(pykotor_mdl)}")
print(f"Original MDL file: {len(mdl_res.data)}")
print(f"PyKotor vs expected: {len(pykotor_mdl) - expected_data}")
print(f"Original vs expected: {len(mdl_res.data) - expected_data}")
print(f"Original vs PyKotor: {len(mdl_res.data) - len(pykotor_mdl)}")

# Check for special node types
print("\n=== Special Node Types ===")
aabb_nodes = dangly_nodes = emitter_nodes = light_nodes = reference_nodes = saber_nodes = 0
for node in mdl.all_nodes():
    if node.aabb:
        aabb_nodes += 1
    if node.dangly:
        dangly_nodes += 1
    if node.emitter:
        emitter_nodes += 1
    if node.light:
        light_nodes += 1
    if node.reference:
        reference_nodes += 1
    if node.saber:
        saber_nodes += 1

print(f"AABB nodes: {aabb_nodes}")
print(f"Dangly nodes: {dangly_nodes}")
print(f"Emitter nodes: {emitter_nodes}")
print(f"Light nodes: {light_nodes}")
print(f"Reference nodes: {reference_nodes}")
print(f"Saber nodes: {saber_nodes}")

# Check original binary node type flags
from pykotor.resource.formats.mdl.mdl_types import MDLNodeFlags

print("\n=== Original Binary Node Flags ===")
reader2 = MDLBinaryReader(mdl_res.data, source_ext=mdx_res.data)
orig_load = reader2._load_node
node_flags = []


def capture_flags(offset, parent):
    reader2._reader.seek(offset)
    hdr = _NodeHeader().read(reader2._reader)
    flags = []
    if hdr.type_id & MDLNodeFlags.MESH:
        flags.append("MESH")
    if hdr.type_id & MDLNodeFlags.SKIN:
        flags.append("SKIN")
    if hdr.type_id & MDLNodeFlags.DANGLY:
        flags.append("DANGLY")
    if hdr.type_id & MDLNodeFlags.AABB:
        flags.append("AABB")
    if hdr.type_id & MDLNodeFlags.SABER:
        flags.append("SABER")
    if hdr.type_id & MDLNodeFlags.EMITTER:
        flags.append("EMITTER")
    if hdr.type_id & MDLNodeFlags.LIGHT:
        flags.append("LIGHT")
    if hdr.type_id & MDLNodeFlags.REFERENCE:
        flags.append("REFERENCE")
    node_flags.append({"node_id": hdr.node_id, "type_id": hdr.type_id, "flags": flags})
    return orig_load(offset, parent)


reader2._load_node = capture_flags
_ = reader2.load()

for nf in node_flags:
    if nf["flags"] and set(nf["flags"]) != {"MESH"}:
        print(f"Node {nf['node_id']}: type_id=0x{nf['type_id']:04X}, flags={nf['flags']}")
