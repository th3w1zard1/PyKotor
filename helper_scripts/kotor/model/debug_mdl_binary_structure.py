from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, "vendor/PyKotor/Libraries/PyKotor/src")
import shutil
import subprocess
import tempfile

from pykotor.resource.formats.mdl.mdl_auto import read_mdl, write_mdl
from pykotor.resource.type import ResourceType

mdl_path = Path("vendor/PyKotor/Libraries/PyKotor/tests/test_files/mdl/dor_lhr02.mdl")
mdx_path = Path("vendor/PyKotor/Libraries/PyKotor/tests/test_files/mdl/dor_lhr02.mdx")
mdlops_path = Path("vendor/MDLOps/mdlops.exe")

# Read original binary
with open(mdl_path, "rb") as f:
    orig_mdl_data = f.read()
with open(mdx_path, "rb") as f:
    orig_mdx_data = f.read()

# Find texture name in original
tex_name = b"LHR_dor02\x00" + b"\x00" * (32 - len("LHR_dor02"))
tex_pos = orig_mdl_data.find(tex_name)
if tex_pos != -1:
    # Texture1 is at offset 84 from start of _TrimeshHeader
    th_start_orig = tex_pos - 84
    print(f"Original binary - Trimesh header at offset {th_start_orig}:")
    with open(mdl_path, "rb") as f:
        f.seek(th_start_orig + 52)  # mdx_data_bitmap
        bitmap_orig = struct.unpack("<I", f.read(4))[0]
        f.seek(th_start_orig + 68)  # mdx_texture1_offset
        tex1_off_orig = struct.unpack("<I", f.read(4))[0]
        f.seek(th_start_orig + 48)  # mdx_data_offset
        mdx_data_off_orig = struct.unpack("<I", f.read(4))[0]
        f.seek(th_start_orig + 56)  # mdx_vertex_offset
        mdx_vertex_off_orig = struct.unpack("<I", f.read(4))[0]
    print(
        f"  mdx_data_bitmap: 0x{bitmap_orig:08X} (TEXTURE1: {bool(bitmap_orig & 0x2)})"
    )
    print(f"  mdx_data_offset: {mdx_data_off_orig} (0x{mdx_data_off_orig:08X})")
    print(f"  mdx_vertex_offset: {mdx_vertex_off_orig} (0x{mdx_vertex_off_orig:08X})")
    print(f"  mdx_texture1_offset: {tex1_off_orig} (0x{tex1_off_orig:08X})")

    # Read actual MDX data
    if mdx_data_off_orig < len(orig_mdx_data):
        print(f"\n  MDX data at offset {mdx_data_off_orig}:")
        if mdx_vertex_off_orig < len(orig_mdx_data) - mdx_data_off_orig:
            vpos_offset = mdx_data_off_orig + mdx_vertex_off_orig
            print(f"    First vertex position at MDX offset {vpos_offset}: ", end="")
            if vpos_offset + 12 <= len(orig_mdx_data):
                x, y, z = struct.unpack(
                    "<fff", orig_mdx_data[vpos_offset : vpos_offset + 12]
                )
                print(f"({x:.3f}, {y:.3f}, {z:.3f})")
        if (
            tex1_off_orig != 0xFFFFFFFF
            and tex1_off_orig < len(orig_mdx_data) - mdx_data_off_orig
        ):
            tuv_offset = mdx_data_off_orig + tex1_off_orig
            print(f"    First texture1 UV at MDX offset {tuv_offset}: ", end="")
            if tuv_offset + 8 <= len(orig_mdx_data):
                u, v = struct.unpack("<ff", orig_mdx_data[tuv_offset : tuv_offset + 8])
                print(f"({u:.3f}, {v:.3f})")

# Now generate PyKotor binary and compare
with tempfile.TemporaryDirectory() as tmpdir:
    td = Path(tmpdir)
    shutil.copy(mdl_path, td / mdl_path.name)
    shutil.copy(mdx_path, td / mdx_path.name)

    # Decompile with MDLOps
    subprocess.run(
        [str(mdlops_path), str(td / mdl_path.name)],
        cwd=str(td),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    ascii_p = td / f"{mdl_path.stem}-ascii.mdl"

    # Read and write with PyKotor
    obj = read_mdl(ascii_p.read_bytes(), file_format=ResourceType.MDL_ASCII)
    out_dir = td / "out"
    out_dir.mkdir()
    write_mdl(
        obj,
        out_dir / mdl_path.name,
        ResourceType.MDL,
        target_ext=out_dir / mdx_path.name,
    )

    # Read generated binary
    with open(out_dir / mdl_path.name, "rb") as f:
        gen_mdl_data = f.read()
    with open(out_dir / mdx_path.name, "rb") as f:
        gen_mdx_data = f.read()

    # Find texture name in generated
    tex_pos_gen = gen_mdl_data.find(tex_name)
    if tex_pos_gen != -1:
        th_start_gen = tex_pos_gen - 84
        print(f"\nGenerated binary - Trimesh header at offset {th_start_gen}:")
        with open(out_dir / mdl_path.name, "rb") as f:
            f.seek(th_start_gen + 52)
            bitmap_gen = struct.unpack("<I", f.read(4))[0]
            f.seek(th_start_gen + 68)
            tex1_off_gen = struct.unpack("<I", f.read(4))[0]
            f.seek(th_start_gen + 48)
            mdx_data_off_gen = struct.unpack("<I", f.read(4))[0]
            f.seek(th_start_gen + 56)
            mdx_vertex_off_gen = struct.unpack("<I", f.read(4))[0]
        print(
            f"  mdx_data_bitmap: 0x{bitmap_gen:08X} (TEXTURE1: {bool(bitmap_gen & 0x2)})"
        )
        print(f"  mdx_data_offset: {mdx_data_off_gen} (0x{mdx_data_off_gen:08X})")
        print(f"  mdx_vertex_offset: {mdx_vertex_off_gen} (0x{mdx_vertex_off_gen:08X})")
        print(f"  mdx_texture1_offset: {tex1_off_gen} (0x{tex1_off_gen:08X})")

        # Read actual MDX data
        if mdx_data_off_gen < len(gen_mdx_data):
            print(f"\n  MDX data at offset {mdx_data_off_gen}:")
            # Calculate block size: vertex (12) + texture1 (8) = 20 bytes per vertex if no normals
            # Or vertex (12) + normal (12) + texture1 (8) = 32 bytes per vertex if normals
            mdx_block_size = (
                20 if (bitmap_gen & 0x20) == 0 else 32
            )  # 0x20 is NORMAL flag
            print(f"    Estimated block size: {mdx_block_size} bytes per vertex")
            if mdx_vertex_off_gen != 0xFFFFFFFF and mdx_vertex_off_gen < mdx_block_size:
                vpos_offset = (
                    mdx_data_off_gen + mdx_vertex_off_gen
                )  # First vertex, position at offset 0
                print(
                    f"    First vertex position at MDX offset {vpos_offset}: ", end=""
                )
                if vpos_offset + 12 <= len(gen_mdx_data):
                    x, y, z = struct.unpack(
                        "<fff", gen_mdx_data[vpos_offset : vpos_offset + 12]
                    )
                    print(f"({x:.3f}, {y:.3f}, {z:.3f})")
            if tex1_off_gen != 0xFFFFFFFF and tex1_off_gen < mdx_block_size:
                # For interleaved data, first texture1 UV is at mdx_data_offset + tex1_off_gen (within first vertex block)
                tuv_offset = mdx_data_off_gen + tex1_off_gen
                print(
                    f"    First texture1 UV at MDX offset {tuv_offset} (within first vertex block): ",
                    end="",
                )
                if tuv_offset + 8 <= len(gen_mdx_data):
                    u, v = struct.unpack(
                        "<ff", gen_mdx_data[tuv_offset : tuv_offset + 8]
                    )
                    print(f"({u:.3f}, {v:.3f})")
                else:
                    print(
                        f"ERROR: Offset {tuv_offset} + 8 = {tuv_offset + 8} exceeds MDX size {len(gen_mdx_data)}"
                    )
            else:
                print(
                    f"    ERROR: texture1_offset is invalid (0x{tex1_off_gen:08X}) or exceeds block size"
                )
