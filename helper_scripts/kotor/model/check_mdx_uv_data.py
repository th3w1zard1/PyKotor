import struct
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path

sys.path.insert(0, 'vendor/PyKotor/Libraries/PyKotor/src')
from pykotor.resource.formats.mdl.mdl_auto import read_mdl, write_mdl
from pykotor.resource.type import ResourceType

mdl_p = Path('vendor/PyKotor/Libraries/PyKotor/tests/test_files/mdl/dor_lhr02.mdl')
mdx_p = Path('vendor/PyKotor/Libraries/PyKotor/tests/test_files/mdl/dor_lhr02.mdx')
mdlops_p = Path('vendor/MDLOps/mdlops.exe')

td = Path(tempfile.mkdtemp())
shutil.copy(mdl_p, td / mdl_p.name)
shutil.copy(mdx_p, td / mdx_p.name)

# Decompile with MDLOps
subprocess.run([str(mdlops_p), str(td / mdl_p.name)], cwd=str(td), 
               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
ascii_p = td / f'{mdl_p.stem}-ascii.mdl'

# Read and write with PyKotor
obj = read_mdl(ascii_p.read_bytes(), file_format=ResourceType.MDL_ASCII)
out_dir = td / 'out'
out_dir.mkdir()
write_mdl(obj, out_dir / mdl_p.name, ResourceType.MDL, target_ext=out_dir / mdx_p.name)

# Check MDX file
mdx_data = (out_dir / mdx_p.name).read_bytes()
print(f'MDX file size: {len(mdx_data)} bytes')

# Also check the MDL file header to see MDX size
with open(out_dir / mdl_p.name, 'rb') as f:
    f.seek(4)  # Skip first uint32
    mdl_size = struct.unpack('<I', f.read(4))[0]
    mdx_size_from_header = struct.unpack('<I', f.read(4))[0]
print(f'MDL header says MDX size: {mdx_size_from_header} bytes (actual: {len(mdx_data)})')

# Find node with texture LHR_dor02 by searching for headers with tex1_off=12
mdl_data = (out_dir / mdl_p.name).read_bytes()
tex_name = b'LHR_dor02\x00' + b'\x00' * (32 - len('LHR_dor02'))
# Search for texture1_offset = 12 (0x0000000C)
tex1_off_pattern = struct.pack('<I', 12)
tex1_off_positions = []
start = 0
while True:
    pos = mdl_data.find(tex1_off_pattern, start)
    if pos == -1:
        break
    tex1_off_positions.append(pos)
    start = pos + 1

print(f'Found texture1_offset=12 at {len(tex1_off_positions)} positions')

# For each tex1_off position, check if it's at offset 68 from a trimesh header with matching texture
th_start = None
matching_headers = []
for tex1_off_pos in tex1_off_positions:
    # texture1_offset is at offset 68 from start of trimesh header
    th_start_candidate = tex1_off_pos - 68
    if th_start_candidate >= 0 and th_start_candidate + 84 + 32 <= len(mdl_data):
        # Check if texture name matches at offset 84
        tex_at_offset = mdl_data[th_start_candidate + 84:th_start_candidate + 84 + 32]
        if tex_name in tex_at_offset:
            # Verify the bitmap value is correct (should be 0x00000003 or 0x00000007)
            bitmap_at_pos = struct.unpack('<I', mdl_data[th_start_candidate + 52:th_start_candidate + 56])[0]
            if bitmap_at_pos & 0x2:  # TEXTURE1 flag set
                matching_headers.append((th_start_candidate, bitmap_at_pos, tex1_off_pos))
                if th_start is None:  # Use first match
                    th_start = th_start_candidate
                    print(f'\nFound matching trimesh header at offset {th_start} (tex1_off at {tex1_off_pos}, bitmap=0x{bitmap_at_pos:08X})')

if len(matching_headers) > 1:
    print(f'  (Found {len(matching_headers)} total headers with texture LHR_dor02 and tex1_off=12)')

if th_start is None:
    # Fallback to texture name search
    tex_pos = mdl_data.find(tex_name)
    if tex_pos != -1:
        th_start = tex_pos - 84
        print(f'\nUsing texture name search, found at offset {th_start}')
    else:
        print('ERROR: Could not find trimesh header')
        th_start = None

if th_start is not None and th_start >= 0:
    with open(out_dir / mdl_p.name, 'rb') as f:
        f.seek(th_start + 48)
        mdx_off = struct.unpack('<I', f.read(4))[0]
        f.seek(th_start + 52)
        bitmap = struct.unpack('<I', f.read(4))[0]
        f.seek(th_start + 68)
        tex1_off = struct.unpack('<I', f.read(4))[0]
    
    print(f'mdx_data_offset: {mdx_off} (0x{mdx_off:08X})')
    print(f'bitmap: 0x{bitmap:08X} (TEXTURE1: {bool(bitmap & 0x2)})')
    print(f'texture1_offset: {tex1_off} (0x{tex1_off:08X})')
    
    if mdx_off < len(mdx_data) and tex1_off != 0xFFFFFFFF and tex1_off < 100:
        # For interleaved data, first UV is at mdx_off + tex1_off
        uv_offset = mdx_off + tex1_off
        print(f'\nUV data should be at MDX offset {uv_offset}')
        if uv_offset + 8 <= len(mdx_data):
            u, v = struct.unpack('<ff', mdx_data[uv_offset:uv_offset+8])
            print(f'First UV: ({u:.6f}, {v:.6f})')
            # Check a few more UVs to verify pattern
            block_size = 20  # vertex (12) + texture1 (8) if no normals
            for i in range(min(3, (len(mdx_data) - uv_offset) // block_size)):
                uv_off = mdx_off + i * block_size + tex1_off
                if uv_off + 8 <= len(mdx_data):
                    u, v = struct.unpack('<ff', mdx_data[uv_off:uv_off+8])
                    print(f'  UV[{i}]: ({u:.6f}, {v:.6f})')
        else:
            print(f'ERROR: UV offset {uv_offset} + 8 = {uv_offset+8} exceeds MDX size {len(mdx_data)}')
    else:
        print(f'ERROR: Invalid offsets - mdx_off={mdx_off}, tex1_off={tex1_off}')

