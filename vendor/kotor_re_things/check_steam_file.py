#!/usr/bin/env python3
import pefile
import sys

steam_path = r"C:/Program Files (x86)/Steam/steamapps/common/swkotor/swkotor.exe"

try:
    pe = pefile.PE(steam_path)
    print(f"Entry point: 0x{pe.OPTIONAL_HEADER.AddressOfEntryPoint:08x}")
    print("\nSections:")
    for s in pe.sections:
        print(f"  {s.Name.rstrip(b'\x00').decode():10s} RVA=0x{s.VirtualAddress:08x} Size=0x{s.SizeOfRawData:08x}")

    entry_rva = pe.OPTIONAL_HEADER.AddressOfEntryPoint
    entry_section = None
    for s in pe.sections:
        if s.VirtualAddress <= entry_rva < s.VirtualAddress + s.Misc_VirtualSize:
            entry_section = s
            break

    print(f"\nEntry section: {entry_section.Name.rstrip(b'\x00').decode() if entry_section else 'unknown'}")

    # Check for .bind section
    has_bind = any(s.Name.rstrip(b"\x00") == b".bind" for s in pe.sections)
    print(f"Has .bind section: {has_bind}")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
