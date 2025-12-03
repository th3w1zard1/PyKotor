#!/usr/bin/env python3
"""
Test script to verify KOTOR DRM packer/unpacker idempotency.

This script tests that:
- pack -> unpack -> pack produces the same file as pack
- unpack -> pack -> unpack produces the same file as unpack
- Multiple round trips produce identical SHA256 hashes
"""

import hashlib
import sys
from pathlib import Path

from kotor_drm_unpacker import KotorPacker


def sha256_file(filepath: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def test_idempotency(exe_path: Path, temp_dir: Path):
    """Test packer/unpacker idempotency."""
    print("=" * 70)
    print("KOTOR DRM Packer/Unpacker Idempotency Test")
    print("=" * 70)
    print()
    
    if not exe_path.exists():
        print(f"ERROR: File not found: {exe_path}")
        return False
        
    original_hash = sha256_file(exe_path)
    print(f"Original file: {exe_path}")
    print(f"SHA256: {original_hash}")
    print()
    
    # Test 1: Pack -> Unpack -> Pack (should match Pack)
    print("Test 1: Pack -> Unpack -> Pack")
    print("-" * 70)
    
    packed1 = temp_dir / "test_packed1.exe"
    unpacked1 = temp_dir / "test_unpacked1.exe"
    packed2 = temp_dir / "test_packed2.exe"
    
    packer1 = KotorPacker(exe_path)
    if not packer1.pack(packed1):
        print("ERROR: Initial pack failed")
        return False
    hash_packed1 = sha256_file(packed1)
    print(f"  Packed 1 SHA256: {hash_packed1}")
    
    packer2 = KotorPacker(packed1)
    if not packer2.unpack(unpacked1):
        print("ERROR: Unpack failed")
        return False
    hash_unpacked1 = sha256_file(unpacked1)
    print(f"  Unpacked SHA256: {hash_unpacked1}")
    
    packer3 = KotorPacker(unpacked1)
    if not packer3.pack(packed2):
        print("ERROR: Second pack failed")
        return False
    hash_packed2 = sha256_file(packed2)
    print(f"  Packed 2 SHA256: {hash_packed2}")
    
    if hash_packed1 == hash_packed2:
        print("  ✓ PASS: Pack -> Unpack -> Pack is idempotent")
    else:
        print("  ✗ FAIL: Pack -> Unpack -> Pack produced different hashes")
        return False
    print()
    
    # Test 2: Unpack -> Pack -> Unpack (should match Unpack)
    print("Test 2: Unpack -> Pack -> Unpack")
    print("-" * 70)
    
    # First check if original is packed
    packer_check = KotorPacker(exe_path)
    is_original_packed = packer_check._is_packed()
    
    if is_original_packed:
        unpacked_orig = temp_dir / "test_unpacked_orig.exe"
        packer_orig = KotorPacker(exe_path)
        if not packer_orig.unpack(unpacked_orig):
            print("ERROR: Initial unpack failed")
            return False
        hash_unpacked_orig = sha256_file(unpacked_orig)
        print(f"  Unpacked original SHA256: {hash_unpacked_orig}")
        
        packed_orig = temp_dir / "test_packed_orig.exe"
        packer_pack = KotorPacker(unpacked_orig)
        if not packer_pack.pack(packed_orig):
            print("ERROR: Pack failed")
            return False
        hash_packed_orig = sha256_file(packed_orig)
        print(f"  Packed SHA256: {hash_packed_orig}")
        
        unpacked_final = temp_dir / "test_unpacked_final.exe"
        packer_final = KotorPacker(packed_orig)
        if not packer_final.unpack(unpacked_final):
            print("ERROR: Final unpack failed")
            return False
        hash_unpacked_final = sha256_file(unpacked_final)
        print(f"  Unpacked final SHA256: {hash_unpacked_final}")
        
        if hash_unpacked_orig == hash_unpacked_final:
            print("  ✓ PASS: Unpack -> Pack -> Unpack is idempotent")
        else:
            print("  ✗ FAIL: Unpack -> Pack -> Unpack produced different hashes")
            return False
    else:
        print("  Skipped: Original file is not packed")
    print()
    
    # Test 3: Multiple round trips
    print("Test 3: Multiple Round Trips")
    print("-" * 70)
    
    current_file = exe_path
    hashes = []
    
    for i in range(5):
        if i % 2 == 0:
            # Pack
            output = temp_dir / f"roundtrip_{i}.exe"
            packer = KotorPacker(current_file)
            if not packer.pack(output):
                print(f"ERROR: Pack failed at iteration {i}")
                return False
            current_file = output
        else:
            # Unpack
            output = temp_dir / f"roundtrip_{i}.exe"
            packer = KotorPacker(current_file)
            if not packer.unpack(output):
                print(f"ERROR: Unpack failed at iteration {i}")
                return False
            current_file = output
            
        hash_val = sha256_file(current_file)
        hashes.append(hash_val)
        print(f"  Iteration {i+1}: {hash_val[:16]}...")
        
    # Check that all hashes match (for same operation type)
    if len(set(hashes[::2])) == 1 and len(set(hashes[1::2])) == 1:
        print("  ✓ PASS: Multiple round trips are idempotent")
    else:
        print("  ✗ FAIL: Multiple round trips produced different hashes")
        return False
    print()
    
    print("=" * 70)
    print("All tests PASSED! Packer/Unpacker is fully idempotent.")
    print("=" * 70)
    return True


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test KOTOR DRM packer idempotency')
    parser.add_argument('exe', type=Path, help='Path to executable to test')
    parser.add_argument('--temp-dir', type=Path, default=Path('temp_test'), help='Temporary directory for test files')
    
    args = parser.parse_args()
    
    args.temp_dir.mkdir(exist_ok=True)
    
    success = test_idempotency(args.exe, args.temp_dir)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())

