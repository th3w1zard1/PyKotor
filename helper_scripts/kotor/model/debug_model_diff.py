#!/usr/bin/env python
"""Debug script to analyze model differences between PyKotor and MDLOps."""
from __future__ import annotations

import sys

sys.path.insert(0, "Libraries/PyKotor/src")

from pathlib import Path

from pykotor.extract.installation import Installation
from pykotor.resource.formats.mdl.io_mdl import MDLBinaryReader, _MDXDataFlags, _NodeHeader, _TrimeshHeader
from pykotor.resource.type import ResourceType

# Find the model
k1_path = Path(r"C:/Program Files (x86)/Steam/steamapps/common/swkotor")
inst = Installation(k1_path)

# Get the specific model
mdl_resource = inst.resource("i_drdsrcscp_001", ResourceType.MDL)
assert mdl_resource is not None, "MDL resource not found"
mdx_resource = inst.resource("i_drdsrcscp_001", ResourceType.MDX)
assert mdx_resource is not None, "MDX resource not found"
mdl_data = mdl_resource.data
mdx_data = mdx_resource.data

print(f"Original MDL size: {len(mdl_data)}")
print(f"Original MDX size: {len(mdx_data)}")

# Create reader with debug
reader = MDLBinaryReader(mdl_data, source_ext=mdx_data)

# Add instrumentation by patching the reader's _load_node method
original_load_node = reader._load_node


def debug_load_node(offset, parent):
    """Wrapper to print debug info during node loading."""

    # First read the raw node header to get info before full parsing
    reader._reader.seek(offset)
    bin_node_header = _NodeHeader().read(reader._reader)

    print(f"\n=== Loading node at offset {offset} ===")
    print(f"  type_id=0x{bin_node_header.type_id:04X}")
    print(f"  node_id={bin_node_header.node_id}")
    print(f"  name_id={bin_node_header.name_id}")

    # Check if it's a trimesh
    if bin_node_header.type_id & 0x20:  # MESH flag
        # Read trimesh header
        trimesh = _TrimeshHeader()
        trimesh.read(reader._reader, reader.game)

        print("  === Trimesh header ===")
        print(f"    vertex_count={trimesh.vertex_count}")
        print(f"    texture1='{trimesh.texture1}'")
        print(f"    texture2='{trimesh.texture2}'")
        print(f"    mdx_data_size={trimesh.mdx_data_size}")
        print(f"    mdx_data_bitmap=0x{trimesh.mdx_data_bitmap:08X}")
        print(f"    mdx_data_offset={trimesh.mdx_data_offset}")
        print(f"    mdx_vertex_offset={trimesh.mdx_vertex_offset}")
        print(f"    mdx_normal_offset={trimesh.mdx_normal_offset}")
        print(f"    mdx_texture1_offset={trimesh.mdx_texture1_offset}")
        print(f"    mdx_texture2_offset={trimesh.mdx_texture2_offset}")
        print(f"    vertices_offset={trimesh.vertices_offset}")
        print(f"    VERTEX flag: {bool(trimesh.mdx_data_bitmap & _MDXDataFlags.VERTEX)}")
        print(f"    NORMAL flag: {bool(trimesh.mdx_data_bitmap & _MDXDataFlags.NORMAL)}")
        print(f"    TEX0 flag: {bool(trimesh.mdx_data_bitmap & _MDXDataFlags.TEX0)}")
        print(f"    TEX1 flag: {bool(trimesh.mdx_data_bitmap & _MDXDataFlags.TEX1)}")

    # Call original
    return original_load_node(offset, parent)


# Patch
reader._load_node = debug_load_node

# Read with instrumented reader
print("\n===== Reading model =====")
mdl = reader.load()

print("\n===== Results =====")
print(f"Model name: {mdl.root.name}")
print(f"Node count: {len(mdl.all_nodes())}")

# Show mesh node details
for node in mdl.all_nodes():
    if node.mesh:
        vcount = len(node.mesh.vertex_positions) if node.mesh.vertex_positions else 0
        fcount = len(node.mesh.faces) if node.mesh.faces else 0
        ncount = len(node.mesh.vertex_normals) if node.mesh.vertex_normals else 0
        uv1count = len(node.mesh.vertex_uv1) if node.mesh.vertex_uv1 else 0
        print(f"\nNode {node.name}:")
        print(f"  verts={vcount}, faces={fcount}, normals={ncount}, uv1={uv1count}")
        print(f'  texture1="{node.mesh.texture_1}"')

# Now test write functionality
from io import BytesIO
from pykotor.resource.formats.mdl import write_mdl

print("\n===== Testing write_mdl =====")
mdl_out = BytesIO()
mdx_out = BytesIO()
write_mdl(mdl, mdl_out, file_format=ResourceType.MDL, target_ext=mdx_out)
pykotor_mdl = mdl_out.getvalue()
pykotor_mdx = mdx_out.getvalue()

print(f"Original MDL size: {len(mdl_data)}")
print(f"Original MDX size: {len(mdx_data)}")
print(f"PyKotor MDL size: {len(pykotor_mdl)}")
print(f"PyKotor MDX size: {len(pykotor_mdx)}")
print(f"MDL diff vs original: {len(pykotor_mdl) - len(mdl_data)}")
print(f"MDX diff vs original: {len(pykotor_mdx) - len(mdx_data)}")
