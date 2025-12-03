"""Test script to verify FNV64 UTF-16LE hash calculation."""
k_string = "Foobar"
utf16le = k_string.encode('utf-16le')
print(f'UTF-16LE bytes: {utf16le.hex()}')

# FNV64 hash with bytes
hash_value = 0xCBF29CE484222325
prime = 1099511628211
for b in utf16le:
    hash_value = ((hash_value * prime) ^ b) & 0xFFFFFFFFFFFFFFFF
print(f'Hash with bytes: 0x{hash_value:016X}')

# Expected
expected = 0xA73456F669A95770
print(f'Expected: 0x{expected:016X}')
print(f'Match: {hash_value == expected}')

