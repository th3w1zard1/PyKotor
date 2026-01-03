# Verify trimesh header structure to match MDLOps expectations
# MDLOps reads from indices: 51 (mdxdatasize), 52 (mdxdatabitmap), 53 (mdxvertcoordsloc), 54 (mdxvertnormalsloc), 55 (mdxvertcolorsloc), 56 (mdxtex0vertsloc)

# Our trimesh header write order (from io_mdl.py _TrimeshHeader.write):
write_order = [
    "function_pointer0",      # 0: uint32
    "function_pointer1",      # 1: uint32
    "offset_to_faces",        # 2: uint32
    "faces_count",            # 3: uint32
    "faces_count2",           # 4: uint32
    "bounding_box_min",       # 5-7: Vector3 (3 floats)
    "bounding_box_max",       # 8-10: Vector3 (3 floats)
    "radius",                 # 11: float
    "average",                 # 12-14: Vector3 (3 floats)
    "diffuse",                # 15-17: Vector3 (3 floats)
    "ambient",                # 18-20: Vector3 (3 floats)
    "transparency_hint",      # 21: uint32
    "texture1",               # 22-29: 32-byte string (8 uint32s when unpacked as uint32s, but 1 element as string)
    "texture2",               # 30-37: 32-byte string
    "unknown0",               # 38-43: 24 bytes (6 uint32s)
    "offset_to_indices_counts", # 44: uint32
    "indices_counts_count",   # 45: uint32
    "indices_counts_count2",  # 46: uint32
    "offset_to_indices_offset", # 47: uint32
    "indices_offsets_count",  # 48: uint32
    "indices_offsets_count2", # 49: uint32
    "offset_to_counters",     # 50: uint32
    "counters_count",         # 51: uint32
    "counters_count2",        # 52: uint32
    "unknown1",               # 53-55: 12 bytes (3 uint32s)
    "saber_unknowns",         # 56-57: 8 bytes (2 uint32s)
    "unknown2",               # 58: uint32
    "uv_direction",           # 59-60: Vector2 (2 floats)
    "uv_jitter",              # 61: float
    "uv_speed",               # 62: float
    "mdx_data_size",          # 63: uint32
    "mdx_data_bitmap",        # 64: uint32
    "mdx_vertex_offset",      # 65: uint32
    "mdx_normal_offset",      # 66: uint32
    "mdx_color_offset",       # 67: uint32
    "mdx_texture1_offset",    # 68: uint32
    "mdx_texture2_offset",    # 69: uint32
    # ... more fields
]

# But MDLOps template unpacks differently - strings are 1 element, not 8
# Let's count what MDLOps actually sees:
# Template: "L[5]f[16]LZ[32]Z[32]Z[12]Z[12]L[9]l[3]C[8]lf[4]l[13]SSC[6]SfL[3]"
# L[5] = 5 elements (indices 0-4)
# f[16] = 16 elements (indices 5-20)
# L = 1 element (index 21)
# Z[32] = 1 element (index 22) - texture1
# Z[32] = 1 element (index 23) - texture2
# Z[12] = 1 element (index 24)
# Z[12] = 1 element (index 25)
# L[9] = 9 elements (indices 26-34)
# l[3] = 3 elements (indices 35-37)
# C[8] = 8 elements (indices 38-45)
# l = 1 element (index 46)
# f[4] = 4 elements (indices 47-50)
# l[13] = 13 elements (indices 51-63)
# SS = 2 elements (indices 64-65)
# C[6] = 6 elements (indices 66-71)
# S = 1 element (index 72)
# f = 1 element (index 73)
# L[3] = 3 elements (indices 74-76)

# So:
# Index 51 = first element of l[13] = mdx_data_size (byte offset 48 + 13*4 = 100, but l[13] starts at byte offset...)
# Actually, let me recalculate from the template more carefully

print("MDLOps template indices:")
print("  Index 51: mdxdatasize (should be mdx_data_size)")
print("  Index 52: mdxdatabitmap (should be mdx_data_bitmap)")
print("  Index 53: mdxvertcoordsloc (should be mdx_vertex_offset)")
print("  Index 54: mdxvertnormalsloc (should be mdx_normal_offset)")
print("  Index 55: mdxvertcolorsloc (should be mdx_color_offset)")
print("  Index 56: mdxtex0vertsloc (should be mdx_texture1_offset)")

# Let's manually count the template:
# L[5] = indices 0-4 (20 bytes)
# f[16] = indices 5-20 (64 bytes, total 84)
# L = index 21 (4 bytes, total 88)
# Z[32] = index 22 (32 bytes, total 120) - texture1
# Z[32] = index 23 (32 bytes, total 152) - texture2
# Z[12] = index 24 (12 bytes, total 164)
# Z[12] = index 25 (12 bytes, total 176)
# L[9] = indices 26-34 (36 bytes, total 212)
# l[3] = indices 35-37 (12 bytes, total 224)
# C[8] = indices 38-45 (8 bytes, total 232)
# l = index 46 (4 bytes, total 236)
# f[4] = indices 47-50 (16 bytes, total 252)
# l[13] = indices 51-63 (52 bytes, total 304) - this includes mdx_data_size, mdx_data_bitmap, and MDX offsets!
# SS = indices 64-65 (4 bytes, total 308)
# C[6] = indices 66-71 (6 bytes, total 314)
# S = index 72 (2 bytes, total 316)
# f = index 73 (4 bytes, total 320)
# L[3] = indices 74-76 (12 bytes, total 332)

# So l[13] (indices 51-63) contains:
# Index 51 = mdx_data_size (byte offset 252)
# Index 52 = mdx_data_bitmap (byte offset 256)
# Index 53 = mdx_vertex_offset (byte offset 260)
# Index 54 = mdx_normal_offset (byte offset 264)
# Index 55 = mdx_color_offset (byte offset 268)
# Index 56 = mdx_texture1_offset (byte offset 272) - but we write it at byte offset 68!

print("\nOur write order byte offsets:")
print("  mdx_data_size at byte offset 48 (but MDLOps expects it at 252)")
print("  mdx_data_bitmap at byte offset 52 (but MDLOps expects it at 256)")
print("  mdx_texture1_offset at byte offset 68 (but MDLOps expects it at 272)")

print("\nThis suggests our trimesh header structure doesn't match MDLOps' template!")

