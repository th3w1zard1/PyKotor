import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "vendor/PyKotor/Libraries/PyKotor/src")
from pykotor.resource.formats.mdl.mdl_auto import read_mdl, write_mdl
from pykotor.resource.type import ResourceType

sys.path.pop(0)

mdl = Path("vendor/PyKotor/Libraries/PyKotor/tests/test_files/mdl/dor_lhr02.mdl")
mdx = Path("vendor/PyKotor/Libraries/PyKotor/tests/test_files/mdl/dor_lhr02.mdx")
mdlops = Path("vendor/MDLOps/mdlops.exe")

td = Path(tempfile.mkdtemp())
shutil.copy(mdl, td / mdl.name)
shutil.copy(mdx, td / mdx.name)

subprocess.run(
    [str(mdlops), str(td / mdl.name)],
    cwd=str(td),
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    check=True,
)
ascii_p = td / f"{mdl.stem}-ascii.mdl"
obj = read_mdl(ascii_p.read_bytes(), file_format=ResourceType.MDL_ASCII)

out_dir = td / "out"
out_dir.mkdir()
write_mdl(obj, out_dir / mdl.name, ResourceType.MDL, target_ext=out_dir / mdx.name)

# Find ALL occurrences of texture name in binary
with open(out_dir / mdl.name, "rb") as f:
    data = f.read()

tex_name = b"LHR_dor02\x00" + b"\x00" * (32 - len("LHR_dor02"))
positions = []
start = 0
while True:
    pos = data.find(tex_name, start)
    if pos == -1:
        break
    positions.append(pos)
    start = pos + 1

print(f"Found texture name at {len(positions)} positions: {positions}")

# Search for the bitmap value 0x00000003 (which includes TEXTURE1 flag) to find actual trimesh headers
bitmap_pattern = struct.pack("<I", 0x00000003)
bitmap_positions = []
start = 0
while True:
    pos = data.find(bitmap_pattern, start)
    if pos == -1:
        break
    bitmap_positions.append(pos)
    start = pos + 1

print(
    f"Found bitmap 0x00000003 at {len(bitmap_positions)} positions: {bitmap_positions[:10]}"
)  # Show first 10

# Check each occurrence
# Instead of calculating from texture name, search for the bitmap value we expect (0x00000003 or similar)
# Then read the texture1_offset from the correct relative position
# Try both approaches: from texture name position and from bitmap position
for i, pos in enumerate(positions[:3]):  # Check first 3 only
    # Approach 1: Calculate from texture name position
    th_start_from_tex = pos - 84  # Texture name is at offset 84 in trimesh header
    with open(out_dir / mdl.name, "rb") as f:
        f.seek(th_start_from_tex + 52)
        bitmap_from_tex = struct.unpack("<I", f.read(4))[0]
        f.seek(th_start_from_tex + 68)
        tex1_off_from_tex = struct.unpack("<I", f.read(4))[0]

    # Approach 2: Find nearest bitmap position and work backwards
    # Bitmap is at offset 52 from trimesh header start, so trimesh header starts at bitmap_pos - 52
    nearest_bitmap_pos = min(
        bitmap_positions, key=lambda x: abs(x - (pos - 32)), default=None
    )
    if nearest_bitmap_pos:
        th_start_from_bitmap = nearest_bitmap_pos - 52
        with open(out_dir / mdl.name, "rb") as f:
            f.seek(nearest_bitmap_pos)
            bitmap_from_bitmap = struct.unpack("<I", f.read(4))[0]
            f.seek(th_start_from_bitmap + 68)
            tex1_off_from_bitmap = struct.unpack("<I", f.read(4))[0]
            # Also read texture name to verify
            f.seek(th_start_from_bitmap + 84)
            tex_name_from_bitmap = (
                f.read(32).rstrip(b"\x00").decode("ascii", errors="ignore")
            )
    else:
        bitmap_from_bitmap = None
        tex1_off_from_bitmap = None
        tex_name_from_bitmap = None

    bitmap = bitmap_from_tex
    tex1_off = tex1_off_from_tex
    normal_off = 0
    color_off = 0
    with open(out_dir / mdl.name, "rb") as f:
        f.seek(th_start_from_tex + 60)
        normal_off = struct.unpack("<I", f.read(4))[0]
        f.seek(th_start_from_tex + 64)
        color_off = struct.unpack("<I", f.read(4))[0]

        print(f"\nTrimesh header #{i + 1} (texture at {pos}):")
        print(f"  From texture pos (th_start={th_start_from_tex}):")
        print(
            f"    mdx_data_bitmap: 0x{bitmap_from_tex:08X} (TEXTURE1: {bool(bitmap_from_tex & 0x2)})"
        )
        print(
            f"    mdx_texture1_offset: {tex1_off_from_tex} (0x{tex1_off_from_tex:08X})"
        )
        if nearest_bitmap_pos:
            print(
                f"  From bitmap pos (th_start={th_start_from_bitmap}, bitmap_at={nearest_bitmap_pos}):"
            )
            print(
                f"    mdx_data_bitmap: 0x{bitmap_from_bitmap:08X} (TEXTURE1: {bool(bitmap_from_bitmap & 0x2) if bitmap_from_bitmap else False})"
            )
            print(
                f"    mdx_texture1_offset: {tex1_off_from_bitmap} (0x{tex1_off_from_bitmap:08X})"
                if tex1_off_from_bitmap is not None
                else "    mdx_texture1_offset: N/A"
            )
            print(f"    texture_name: {tex_name_from_bitmap}")

        if (bitmap & 0x2) and tex1_off == 0xFFFFFFFF:
            print("  *** ERROR: TEXTURE1 flag set but offset is invalid! ***")
        elif (bitmap & 0x2) and tex1_off != 0xFFFFFFFF:
            print(
                "  Offset looks valid. Expected: 12 (if no normals) or 24 (if normals)"
            )
            if tex1_off == 12:
                print("  ✓ Offset is 12 (no normals) - correct!")
            elif tex1_off == 24:
                print("  ✓ Offset is 24 (with normals) - correct!")
            else:
                print(f"  ✗ Offset is {tex1_off} - unexpected!")
        elif not (bitmap & 0x2):
            print("  *** ERROR: TEXTURE1 flag NOT set! ***")
