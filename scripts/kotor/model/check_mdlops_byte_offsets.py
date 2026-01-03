from __future__ import annotations

import struct
from pathlib import Path

# Read original binary and find where MDLOps actually reads the values
mdl = Path("vendor/PyKotor/Libraries/PyKotor/tests/test_files/mdl/dor_lhr02.mdl")
mdl_data = mdl.read_bytes()

# Find texture name
tex_name = b"LHR_dor02"
tex_pos = mdl_data.find(tex_name)
if tex_pos != -1:
    # Try different offsets to find trimesh header
    for offset in [84, 88, 80, 76]:
        th_start = tex_pos - offset
        if th_start >= 0 and th_start + 300 < len(mdl_data):
            # Check if this looks like a trimesh header
            bitmap = struct.unpack("<I", mdl_data[th_start + 52 : th_start + 56])[0]
            if 0 < bitmap < 0xFFFFFFFF and (bitmap & 0x2):  # TEXTURE1 flag set
                print(f"Found trimesh header at offset {th_start} (texture at offset {offset})")

                # Read all MDX-related fields
                mdx_data_size = struct.unpack(
                    "<I",
                    mdl_data[th_start + 48 : th_start + 52],
                )[0]
                mdx_data_bitmap = struct.unpack(
                    "<I",
                    mdl_data[th_start + 52 : th_start + 56],
                )[0]
                mdx_vertex_offset = struct.unpack(
                    "<I",
                    mdl_data[th_start + 56 : th_start + 60],
                )[0]
                mdx_normal_offset = struct.unpack(
                    "<I",
                    mdl_data[th_start + 60 : th_start + 64],
                )[0]
                mdx_color_offset = struct.unpack(
                    "<I",
                    mdl_data[th_start + 64 : th_start + 68],
                )[0]
                mdx_texture1_offset = struct.unpack(
                    "<I",
                    mdl_data[th_start + 68 : th_start + 72],
                )[0]

                print("  Byte offsets from trimesh header start:")
                print(f"    +48: mdx_data_size = {mdx_data_size} (0x{mdx_data_size:08X})")
                print(f"    +52: mdx_data_bitmap = 0x{mdx_data_bitmap:08X}")
                print(f"    +56: mdx_vertex_offset = {mdx_vertex_offset} (0x{mdx_vertex_offset:08X})")
                print(f"    +60: mdx_normal_offset = {mdx_normal_offset} (0x{mdx_normal_offset:08X})")
                print(f"    +64: mdx_color_offset = {mdx_color_offset} (0x{mdx_color_offset:08X})")
                print(f"    +68: mdx_texture1_offset = {mdx_texture1_offset} (0x{mdx_texture1_offset:08X})")

                # Now check what MDLOps template would see at indices 51-56
                # We need to unpack the header using MDLOps' template to see what's at those indices
                print("\n  MDLOps reads from unpacked array indices:")
                print("    Index 51: mdxdatasize")
                print("    Index 52: mdxdatabitmap")
                print("    Index 53: mdxvertcoordsloc")
                print("    Index 54: mdxvertnormalsloc")
                print("    Index 55: mdxvertcolorsloc")
                print("    Index 56: mdxtex0vertsloc")

                # Try to unpack using MDLOps template to see what's actually at those indices
                # Template: "L[5]f[16]LZ[32]Z[32]Z[12]Z[12]L[9]l[3]C[8]lf[4]l[13]SSC[6]SfL[3]"
                # This is complex, so let's just verify our byte offsets match what we write
                break
