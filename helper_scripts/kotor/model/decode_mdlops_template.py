# Decode MDLOps unpack template to find index mapping
# Template: "L[5]f[16]LZ[32]Z[32]Z[12]Z[12]L[9]l[3]C[8]lf[4]l[13]SSC[6]SfL[3]"

template = "L[5]f[16]LZ[32]Z[32]Z[12]Z[12]L[9]l[3]C[8]lf[4]l[13]SSC[6]SfL[3]"

# Map template characters to their sizes
# L = unsigned long (uint32) = 4 bytes, but unpacked as 1 element
# l = signed long (int32) = 4 bytes, but unpacked as 1 element  
# f = float = 4 bytes, but unpacked as 1 element
# Z[n] = null-terminated string of n bytes, unpacked as 1 element (the string)
# C[n] = unsigned char array of n bytes, unpacked as n elements
# S = unsigned short (uint16) = 2 bytes, but unpacked as 1 element

index = 0
byte_offset = 0
elements = []

import re  # noqa: E402

# Parse template
pattern = r'([LlZCfS])(?:\[(\d+)\])?'
matches = re.findall(pattern, template)

for char, count_str in matches:
    count = int(count_str) if count_str else 1
    
    if char == 'L':  # unsigned long (uint32)
        for i in range(count):
            elements.append((index, byte_offset, f'L[{index}]'))
            index += 1
            byte_offset += 4
    elif char == 'l':  # signed long (int32)
        for i in range(count):
            elements.append((index, byte_offset, f'l[{index}]'))
            index += 1
            byte_offset += 4
    elif char == 'f':  # float
        for i in range(count):
            elements.append((index, byte_offset, f'f[{index}]'))
            index += 1
            byte_offset += 4
    elif char == 'Z':  # null-terminated string
        elements.append((index, byte_offset, f'Z[{count}][{index}]'))
        index += 1
        byte_offset += count
    elif char == 'C':  # unsigned char array
        for i in range(count):
            elements.append((index, byte_offset, f'C[{index}]'))
            index += 1
            byte_offset += 1
    elif char == 'S':  # unsigned short (uint16)
        for i in range(count):
            elements.append((index, byte_offset, f'S[{index}]'))
            index += 1
            byte_offset += 2

print(f"Total elements: {index}, Total bytes: {byte_offset}")
print(f"\nKey indices:")
print(f"  Index 56: {elements[56] if 56 < len(elements) else 'N/A'}")
print(f"  Index 57: {elements[57] if 57 < len(elements) else 'N/A'}")
print(f"  Index 54: {elements[54] if 54 < len(elements) else 'N/A'}")
print(f"  Index 55: {elements[55] if 55 < len(elements) else 'N/A'}")

# Find mdx_texture1_offset (should be at byte offset 68)
for i, (idx, byte_off, desc) in enumerate(elements):
    if byte_off == 68:
        print(f"\n  mdx_texture1_offset at byte offset 68: index {idx} ({desc})")
    if byte_off == 52:
        print(f"  mdx_data_bitmap at byte offset 52: index {idx} ({desc})")
    if byte_off == 48:
        print(f"  mdx_data_size at byte offset 48: index {idx} ({desc})")

