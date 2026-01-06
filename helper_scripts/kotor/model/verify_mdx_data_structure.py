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

# Find first node with texture LHR_dor02 and valid texture1_offset=12
tex_name = b"LHR_dor02"
tex1_off_12 = struct.pack("<I", 12)
bitmap_03 = struct.pack("<I", 0x00000003)

# Search for texture1_offset=12
found = False
for i in range(len(mdl_data) - 100):
    if mdl_data[i : i + 4] == tex1_off_12:
        # Check if this is at offset 68 from a trimesh header
        th_start = i - 68
        if th_start >= 0 and th_start + 84 + 32 <= len(mdl_data):
            # Check texture name
            tex_at_offset = mdl_data[th_start + 84 : th_start + 84 + 32]
            if tex_name in tex_at_offset:
                # Check bitmap
                bitmap_at = struct.unpack(
                    "<I", mdl_data[th_start + 52 : th_start + 56]
                )[0]
                if bitmap_at & 0x2:  # TEXTURE1 flag
                    print(f"Found correct trimesh header at offset {th_start}")
                    mdx_off = struct.unpack(
                        "<I", mdl_data[th_start + 48 : th_start + 52]
                    )[0]
                    tex1_off = struct.unpack(
                        "<I", mdl_data[th_start + 68 : th_start + 72]
                    )[0]
                    print(f"  mdx_data_offset: {mdx_off} (0x{mdx_off:08X})")
                    print(f"  mdx_texture1_offset: {tex1_off} (0x{tex1_off:08X})")
                    print(f"  MDX file size: {len(mdx_data)} bytes")

                    if mdx_off < len(mdx_data) and tex1_off == 12:
                        # Check MDX data structure
                        # For interleaved data: vertex (12) + texture1 (8) = 20 bytes per vertex
                        block_size = 20
                        print(
                            f"\n  MDX data structure (block_size={block_size} bytes per vertex):"
                        )

                        # First vertex position at mdx_off + 0
                        if mdx_off + 12 <= len(mdx_data):
                            x, y, z = struct.unpack(
                                "<fff", mdx_data[mdx_off : mdx_off + 12]
                            )
                            print(
                                f"    Vertex[0] position: ({x:.6f}, {y:.6f}, {z:.6f})"
                            )

                        # First texture1 UV at mdx_off + 12
                        if mdx_off + tex1_off + 8 <= len(mdx_data):
                            u, v = struct.unpack(
                                "<ff",
                                mdx_data[mdx_off + tex1_off : mdx_off + tex1_off + 8],
                            )
                            print(f"    Texture1[0] UV: ({u:.6f}, {v:.6f})")

                            # Check a few more to verify pattern
                            for vi in range(
                                min(3, (len(mdx_data) - mdx_off) // block_size)
                            ):
                                uv_off = mdx_off + vi * block_size + tex1_off
                                if uv_off + 8 <= len(mdx_data):
                                    u, v = struct.unpack(
                                        "<ff", mdx_data[uv_off : uv_off + 8]
                                    )
                                    print(f"    Texture1[{vi}] UV: ({u:.6f}, {v:.6f})")

                    found = True
                    break

if not found:
    print("Could not find trimesh header with texture LHR_dor02 and tex1_off=12")
