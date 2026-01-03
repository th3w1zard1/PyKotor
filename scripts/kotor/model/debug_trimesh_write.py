from __future__ import annotations

import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "vendor/PyKotor/Libraries/PyKotor/src")
from pykotor.resource.formats.mdl.mdl_auto import read_mdl, write_mdl
from pykotor.resource.type import ResourceType

mdl_p = Path("vendor/PyKotor/Libraries/PyKotor/tests/test_files/mdl/dor_lhr02.mdl")
mdx_p = Path("vendor/PyKotor/Libraries/PyKotor/tests/test_files/mdl/dor_lhr02.mdx")
mdlops_p = Path("vendor/MDLOps/mdlops.exe")

td = Path(tempfile.mkdtemp())
shutil.copy(mdl_p, td / mdl_p.name)
shutil.copy(mdx_p, td / mdx_p.name)

# Decompile with MDLOps
subprocess.run(
    [str(mdlops_p), str(td / mdl_p.name)],
    cwd=str(td),
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    check=True,
)
ascii_p = td / f"{mdl_p.stem}-ascii.mdl"

# Read and write with PyKotor
obj = read_mdl(ascii_p.read_bytes(), file_format=ResourceType.MDL_ASCII)
out_dir = td / "out"
out_dir.mkdir()
write_mdl(obj, out_dir / mdl_p.name, ResourceType.MDL, target_ext=out_dir / mdx_p.name)

# Read generated files
mdl_data = (out_dir / mdl_p.name).read_bytes()
mdx_data = (out_dir / mdx_p.name).read_bytes()

# Find node with texture LHR_dor02 by searching for texture name in trimesh headers
tex_name = b"LHR_dor02"
tex_name_padded = tex_name + b"\x00" * (32 - len(tex_name))

# Skip MDL header (12 bytes: 0, mdl_size, mdx_size)
mdl_content = mdl_data[12:] if len(mdl_data) > 12 else mdl_data

# Search for texture name in MDL (should be at offset 84 in trimesh header)
found_nodes = []
for i in range(len(mdl_content) - 200):
    # Check if this could be a texture1 field (32 bytes, null-terminated)
    tex_candidate = mdl_content[i : i + 32]
    if tex_name in tex_candidate and tex_candidate.startswith(tex_name):
        # This might be a texture1 field - check if it's at offset 84 from a trimesh header
        th_start = i - 84
        if th_start >= 0 and th_start + 361 <= len(mdl_content):
            # Verify this looks like a trimesh header by checking function pointers
            fp0 = struct.unpack("<I", mdl_content[th_start : th_start + 4])[0]
            fp1 = struct.unpack("<I", mdl_content[th_start + 4 : th_start + 8])[0]
            # K1 function pointers are around 4216656
            if 4216000 <= fp0 <= 4217000 and 4216000 <= fp1 <= 4217000:
                # Read the MDX-related fields
                mdx_data_size = struct.unpack(
                    "<I", mdl_content[th_start + 48 : th_start + 52]
                )[0]
                mdx_data_bitmap = struct.unpack(
                    "<I", mdl_content[th_start + 52 : th_start + 56]
                )[0]
                mdx_vertex_offset = struct.unpack(
                    "<I", mdl_content[th_start + 56 : th_start + 60]
                )[0]
                mdx_normal_offset = struct.unpack(
                    "<I", mdl_content[th_start + 60 : th_start + 64]
                )[0]
                mdx_color_offset = struct.unpack(
                    "<I", mdl_content[th_start + 64 : th_start + 68]
                )[0]
                mdx_texture1_offset = struct.unpack(
                    "<I", mdl_content[th_start + 68 : th_start + 72]
                )[0]
                mdx_texture2_offset = struct.unpack(
                    "<I", mdl_content[th_start + 72 : th_start + 76]
                )[0]

                found_nodes.append(
                    {
                        "th_start": th_start + 12,  # Add 12 to account for MDL header
                        "texture1": mdl_content[th_start + 84 : th_start + 84 + 32]
                        .rstrip(b"\x00")
                        .decode("ascii", errors="ignore"),
                        "mdx_data_size": mdx_data_size,
                        "mdx_data_bitmap": mdx_data_bitmap,
                        "mdx_vertex_offset": mdx_vertex_offset,
                        "mdx_normal_offset": mdx_normal_offset,
                        "mdx_texture1_offset": mdx_texture1_offset,
                        "mdx_texture2_offset": mdx_texture2_offset,
                    }
                )

print(f"Found {len(found_nodes)} nodes with texture LHR_dor02:")
for i, node in enumerate(found_nodes):
    print(f"\n  Node {i + 1}:")
    print(f"    th_start: {node['th_start']}")
    print(f"    texture1: {node['texture1']}")
    print(
        f"    mdx_data_bitmap: 0x{node['mdx_data_bitmap']:08X} (TEXTURE1={bool(node['mdx_data_bitmap'] & 0x2)})"
    )
    print(
        f"    mdx_texture1_offset: {node['mdx_texture1_offset']} (0x{node['mdx_texture1_offset']:08X})"
    )
    print(f"    mdx_data_size: {node['mdx_data_size']}")
    print(
        f"    mdx_vertex_offset: {node['mdx_vertex_offset']} (0x{node['mdx_vertex_offset']:08X})"
    )

    # Check if mdx_data_offset is valid (at offset 362 in trimesh header, but th_start includes MDL header)
    th_start_in_content = node["th_start"] - 12  # Remove MDL header offset
    mdx_data_offset = (
        struct.unpack(
            "<I", mdl_content[th_start_in_content + 362 : th_start_in_content + 366]
        )[0]
        if th_start_in_content + 366 <= len(mdl_content)
        else 0
    )
    print(f"    mdx_data_offset: {mdx_data_offset} (0x{mdx_data_offset:08X})")

    if node["mdx_data_bitmap"] & 0x2 and node["mdx_texture1_offset"] == 12:
        print("    ✓ Correct TEXTURE1 flag and offset")
    elif node["mdx_data_bitmap"] & 0x2 and node["mdx_texture1_offset"] != 12:
        print(
            f"    ✗ TEXTURE1 flag set but offset is {node['mdx_texture1_offset']}, expected 12"
        )
    elif not (node["mdx_data_bitmap"] & 0x2):
        print("    ✗ TEXTURE1 flag not set")
