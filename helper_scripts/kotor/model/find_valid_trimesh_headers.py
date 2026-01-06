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

# Search for valid trimesh headers by looking for K1 function pointers
found_headers = []
for i in range(0, len(mdl_content) - 361, 4):  # Step by 4 to align with uint32
    fp0 = struct.unpack("<I", mdl_content[i : i + 4])[0]
    fp1 = struct.unpack("<I", mdl_content[i + 4 : i + 8])[0]

    # K1 function pointers are around 4216656
    if 4216000 <= fp0 <= 4217000 and 4216000 <= fp1 <= 4217000:
        # This looks like a trimesh header - read texture1
        if i + 84 + 32 <= len(mdl_content):
            tex1 = (
                mdl_content[i + 84 : i + 84 + 32]
                .rstrip(b"\x00")
                .decode("ascii", errors="ignore")
            )
            if tex1 and ("LHR" in tex1 or "dor02" in tex1.lower()):
                # Read MDX fields
                mdx_data_bitmap = struct.unpack("<I", mdl_content[i + 52 : i + 56])[0]
                mdx_texture1_offset = struct.unpack("<I", mdl_content[i + 68 : i + 72])[
                    0
                ]

                found_headers.append(
                    {
                        "offset": i,
                        "texture1": tex1,
                        "mdx_data_bitmap": mdx_data_bitmap,
                        "mdx_texture1_offset": mdx_texture1_offset,
                    }
                )

print(f"Found {len(found_headers)} trimesh headers with LHR/dor02 texture:")
for i, hdr in enumerate(found_headers):
    print(f"\n  Header {i + 1}:")
    print(f"    offset: {hdr['offset']} (absolute: {hdr['offset'] + 12})")
    print(f"    texture1: {repr(hdr['texture1'])}")
    print(
        f"    mdx_data_bitmap: 0x{hdr['mdx_data_bitmap']:08X} (TEXTURE1={bool(hdr['mdx_data_bitmap'] & 0x2)})"
    )
    print(
        f"    mdx_texture1_offset: {hdr['mdx_texture1_offset']} (0x{hdr['mdx_texture1_offset']:08X})"
    )
    if hdr["mdx_data_bitmap"] & 0x2 and hdr["mdx_texture1_offset"] == 12:
        print("    STATUS: CORRECT")
    elif hdr["mdx_data_bitmap"] & 0x2 and hdr["mdx_texture1_offset"] != 12:
        print(
            f"    STATUS: TEXTURE1 flag set but offset is {hdr['mdx_texture1_offset']}, expected 12"
        )
    elif not (hdr["mdx_data_bitmap"] & 0x2):
        print("    STATUS: TEXTURE1 flag not set")
