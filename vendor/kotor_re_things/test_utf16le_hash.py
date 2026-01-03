"""Test script to verify UTF-16LE hash calculation."""

import struct

k_string = "Foobar"
utf16le = k_string.encode("utf-16le")
print(f"UTF-16LE bytes: {utf16le.hex()}")

# Method 1: Hash individual bytes
hash_value_bytes = 0x811C9DC5
prime = 16777619
for b in utf16le:
    hash_value_bytes = ((hash_value_bytes * prime) ^ b) & 0xFFFFFFFF
print(f"Hash with bytes: 0x{hash_value_bytes:08X}")

# Method 2: Hash 16-bit characters
chars = [struct.unpack("<H", utf16le[i : i + 2])[0] for i in range(0, len(utf16le), 2)]
print(f"16-bit chars: {[hex(c) for c in chars]}")
hash_value_chars = 0x811C9DC5
for c in chars:
    hash_value_chars = ((hash_value_chars * prime) ^ c) & 0xFFFFFFFF
print(f"Hash with 16-bit chars: 0x{hash_value_chars:08X}")

# Expected
expected = 0xCE5005F0
print(f"Expected: 0x{expected:08X}")
print(f"Bytes match: {hash_value_bytes == expected}")
print(f"Chars match: {hash_value_chars == expected}")
