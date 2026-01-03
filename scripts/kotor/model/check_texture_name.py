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

# Skip MDL header
mdl_content = mdl_data[12:] if len(mdl_data) > 12 else mdl_data

# Search for "LHR" anywhere in the file
lhr_positions = []
search_term = b"LHR"
i = 0
while True:
    pos = mdl_content.find(search_term, i)
    if pos == -1:
        break
    lhr_positions.append(pos)
    i = pos + 1

print(f"Found 'LHR' at {len(lhr_positions)} positions:")
for pos in lhr_positions[:10]:  # Show first 10
    context_start = max(0, pos - 20)
    context_end = min(len(mdl_content), pos + 50)
    context = mdl_content[context_start:context_end]
    print(f"  Position {pos}: {context.hex()}")
    # Try to decode as ASCII
    try:
        decoded = context.decode("ascii", errors="replace")
        print(f"    Decoded: {repr(decoded)}")
    except:
        pass

    # Check if this could be a texture name at offset 84
    th_start = pos - 84
    if th_start >= 0 and th_start + 361 <= len(mdl_content):
        # Check function pointers
        fp0 = struct.unpack("<I", mdl_content[th_start : th_start + 4])[0]
        fp1 = struct.unpack("<I", mdl_content[th_start + 4 : th_start + 8])[0]
        if 4216000 <= fp0 <= 4217000 and 4216000 <= fp1 <= 4217000:
            print(f"    ✓ Looks like trimesh header at offset {th_start}")
            # Read texture1 field
            tex1 = (
                mdl_content[th_start + 84 : th_start + 84 + 32]
                .rstrip(b"\x00")
                .decode("ascii", errors="ignore")
            )
            print(f"    texture1: {repr(tex1)}")
            # Read MDX fields
            mdx_data_bitmap = struct.unpack(
                "<I", mdl_content[th_start + 52 : th_start + 56]
            )[0]
            mdx_texture1_offset = struct.unpack(
                "<I", mdl_content[th_start + 68 : th_start + 72]
            )[0]
            print(f"    mdx_data_bitmap: 0x{mdx_data_bitmap:08X}")
            print(f"    mdx_texture1_offset: {mdx_texture1_offset}")
