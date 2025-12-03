#!/usr/bin/env python3
with open('swkotor_unpacked_test.exe', 'rb') as f:
    f.seek(0x1000)
    orig = f.read(16)
    
with open('swkotor_packed_test.exe', 'rb') as f:
    f.seek(0x1000)
    packed = f.read(16)
    
print('Original .text start:', orig.hex())
print('Packed .text start:  ', packed.hex())
print('XOR check (packed ^ 0x5a):', bytes(b ^ 0x5a for b in packed[:16]).hex())
print('First byte orig:', hex(orig[0]))
print('First byte packed:', hex(packed[0]))
print('First byte packed^0x5a:', hex(packed[0] ^ 0x5a))


