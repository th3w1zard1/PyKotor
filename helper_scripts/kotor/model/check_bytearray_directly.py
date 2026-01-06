from __future__ import annotations

import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "vendor/PyKotor/Libraries/PyKotor/src")
from pykotor.common.stream import BinaryWriter
from pykotor.resource.formats.mdl import MDLBinaryWriter, read_mdl
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

# Create a bytearray writer to inspect the data
mdl_target = BinaryWriter.to_bytearray()
mdx_target = BinaryWriter.to_bytearray()

writer = MDLBinaryWriter(obj, mdl_target, mdx_target)
writer.write(auto_close=False)

# Get the bytearray data
writer_data = mdl_target.data()

# Search for texture name "LHR_dor02" in the bytearray
tex_name = b"LHR_dor02"
found_positions = []
i = 0
while True:
    pos = writer_data.find(tex_name, i)
    if pos == -1:
        break
    found_positions.append(pos)
    i = pos + 1

print(f"Found 'LHR_dor02' at {len(found_positions)} positions in bytearray:")
for pos in found_positions:
    # Check if this is at offset 84 from a trimesh header
    th_start = pos - 84
    if th_start >= 0 and th_start + 361 <= len(writer_data):
        # Check function pointers
        fp0 = struct.unpack("<I", writer_data[th_start : th_start + 4])[0]
        fp1 = struct.unpack("<I", writer_data[th_start + 4 : th_start + 8])[0]
        if 4216000 <= fp0 <= 4217000 and 4216000 <= fp1 <= 4217000:
            print(f"\n  Valid trimesh header at bytearray offset {th_start}:")
            print(f"    texture1 position: {pos}")
            print(f"    function_pointer0: {fp0}")
            print(f"    function_pointer1: {fp1}")

            # Read MDX fields
            mdx_data_bitmap = struct.unpack(
                "<I",
                writer_data[th_start + 52 : th_start + 56],
            )[0]
            mdx_texture1_offset = struct.unpack(
                "<I",
                writer_data[th_start + 68 : th_start + 72],
            )[0]
            print(f"    mdx_data_bitmap: 0x{mdx_data_bitmap:08X} (TEXTURE1={bool(mdx_data_bitmap & 0x2)})")
            print(f"    mdx_texture1_offset: {mdx_texture1_offset} (0x{mdx_texture1_offset:08X})")

            if mdx_data_bitmap & 0x2 and mdx_texture1_offset == 12:
                print("    STATUS: CORRECT")
            elif mdx_data_bitmap & 0x2 and mdx_texture1_offset != 12:
                print(f"    STATUS: ERROR - TEXTURE1 flag set but offset is {mdx_texture1_offset}, expected 12")
            elif not (mdx_data_bitmap & 0x2):
                print("    STATUS: ERROR - TEXTURE1 flag not set")
