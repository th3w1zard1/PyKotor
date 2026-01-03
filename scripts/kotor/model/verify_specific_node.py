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

# Skip MDL header
mdl_content = mdl_data[12:] if len(mdl_data) > 12 else mdl_data

# Check the texture name at position 734 (from previous output)
tex_pos = 734 - 12  # Adjust for MDL header
th_start = tex_pos - 84  # texture1 is at offset 84 in trimesh header

if th_start >= 0 and th_start + 361 <= len(mdl_content):
    print(f"Trimesh header at offset {th_start} (absolute: {th_start + 12}):")

    # Check function pointers
    fp0 = struct.unpack("<I", mdl_content[th_start : th_start + 4])[0]
    fp1 = struct.unpack("<I", mdl_content[th_start + 4 : th_start + 8])[0]
    print(f"  function_pointer0: {fp0} (0x{fp0:08X})")
    print(f"  function_pointer1: {fp1} (0x{fp1:08X})")

    # Read texture1
    tex1 = (
        mdl_content[th_start + 84 : th_start + 84 + 32]
        .rstrip(b"\x00")
        .decode("ascii", errors="ignore")
    )
    print(f"  texture1: {repr(tex1)}")

    # Read MDX fields
    mdx_data_size = struct.unpack("<I", mdl_content[th_start + 48 : th_start + 52])[0]
    mdx_data_bitmap = struct.unpack("<I", mdl_content[th_start + 52 : th_start + 56])[0]
    mdx_vertex_offset = struct.unpack("<I", mdl_content[th_start + 56 : th_start + 60])[
        0
    ]
    mdx_normal_offset = struct.unpack("<I", mdl_content[th_start + 60 : th_start + 64])[
        0
    ]
    mdx_color_offset = struct.unpack("<I", mdl_content[th_start + 64 : th_start + 68])[
        0
    ]
    mdx_texture1_offset = struct.unpack(
        "<I", mdl_content[th_start + 68 : th_start + 72]
    )[0]
    mdx_texture2_offset = struct.unpack(
        "<I", mdl_content[th_start + 72 : th_start + 76]
    )[0]

    print(f"  mdx_data_size: {mdx_data_size}")
    print(
        f"  mdx_data_bitmap: 0x{mdx_data_bitmap:08X} (VERTEX={bool(mdx_data_bitmap & 0x1)}, TEXTURE1={bool(mdx_data_bitmap & 0x2)})"
    )
    print(f"  mdx_vertex_offset: {mdx_vertex_offset} (0x{mdx_vertex_offset:08X})")
    print(f"  mdx_normal_offset: {mdx_normal_offset} (0x{mdx_normal_offset:08X})")
    print(f"  mdx_texture1_offset: {mdx_texture1_offset} (0x{mdx_texture1_offset:08X})")
    print(f"  mdx_texture2_offset: {mdx_texture2_offset} (0x{mdx_texture2_offset:08X})")

    # Read mdx_data_offset (at offset 362 in trimesh header)
    mdx_data_offset = struct.unpack("<I", mdl_content[th_start + 362 : th_start + 366])[
        0
    ]
    vertices_offset = struct.unpack("<I", mdl_content[th_start + 366 : th_start + 370])[
        0
    ]
    print(f"  mdx_data_offset: {mdx_data_offset} (0x{mdx_data_offset:08X})")
    print(f"  vertices_offset: {vertices_offset} (0x{vertices_offset:08X})")

    # Check if MDX data is accessible
    if mdx_data_offset < len(mdx_data) and mdx_texture1_offset == 12:
        # Read first vertex position
        if mdx_data_offset + 12 <= len(mdx_data):
            x, y, z = struct.unpack(
                "<fff", mdx_data[mdx_data_offset : mdx_data_offset + 12]
            )
            print(f"  MDX vertex[0]: ({x:.6f}, {y:.6f}, {z:.6f})")

        # Read first texture1 UV
        uv_offset = mdx_data_offset + mdx_texture1_offset
        if uv_offset + 8 <= len(mdx_data):
            u, v = struct.unpack("<ff", mdx_data[uv_offset : uv_offset + 8])
            print(f"  MDX texture1[0] UV: ({u:.6f}, {v:.6f})")
            print("  ✓ MDX data structure looks correct")
    elif mdx_texture1_offset != 12:
        print(f"  ERROR: mdx_texture1_offset is {mdx_texture1_offset}, expected 12")
    else:
        print(
            f"  ✗ mdx_data_offset {mdx_data_offset} is out of bounds (MDX size: {len(mdx_data)})"
        )
