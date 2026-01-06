import struct
from pathlib import Path

mdl = Path('vendor/PyKotor/Libraries/PyKotor/tests/test_files/mdl/dor_lhr02.mdl')
mdx = Path('vendor/PyKotor/Libraries/PyKotor/tests/test_files/mdl/dor_lhr02.mdx')

mdl_data = mdl.read_bytes()
mdx_data = mdx.read_bytes()

# Search for bitmap values that have TEXTURE1 flag set
tex_name = b'LHR_dor02'
# Search for reasonable bitmap values (has TEXTURE1 flag)
found_headers = []
for i in range(0, len(mdl_data) - 100, 4):
    try:
        bitmap = struct.unpack('<I', mdl_data[i:i+4])[0]
        if bitmap & 0x2:  # TEXTURE1 flag set
            # Check if texture name is at offset 84 from this position (bitmap is at offset 52)
            th_start_candidate = i - 52
            if th_start_candidate >= 0 and th_start_candidate + 84 + 32 <= len(mdl_data):
                tex_at_offset = mdl_data[th_start_candidate + 84:th_start_candidate + 84 + 32]
                if tex_name in tex_at_offset:
                    found_headers.append((th_start_candidate, bitmap, i))
    except Exception as e:
        pass

print(f'Found {len(found_headers)} trimesh headers with texture LHR_dor02')
for th_start, bitmap, bitmap_pos in found_headers[:3]:  # Show first 3
    with open(mdl, 'rb') as f:
        f.seek(th_start + 48)
        mdx_off = struct.unpack('<I', f.read(4))[0]
        f.seek(th_start + 68)
        tex1_off = struct.unpack('<I', f.read(4))[0]
    
    print(f'\nTrimesh header at offset {th_start} (bitmap at {bitmap_pos}):')
    print(f'  mdx_data_offset: {mdx_off} (0x{mdx_off:08X})')
    print(f'  mdx_data_bitmap: 0x{bitmap:08X}')
    print(f'  mdx_texture1_offset: {tex1_off} (0x{tex1_off:08X})')
    print(f'  MDX file size: {len(mdx_data)} bytes')
    if mdx_off < len(mdx_data) and tex1_off != 0xFFFFFFFF and tex1_off < 100:
        uv_offset = mdx_off + tex1_off
        if uv_offset + 8 <= len(mdx_data):
            u, v = struct.unpack('<ff', mdx_data[uv_offset:uv_offset+8])
            print(f'  First UV at MDX offset {uv_offset}: ({u:.6f}, {v:.6f})')
