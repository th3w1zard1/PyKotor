from __future__ import annotations

import struct
from pathlib import Path

mdl_dir = Path("vendor/PyKotor/Libraries/PyKotor/tests/test_files/mdl")

print("Checking game versions for test models:\n")

for mdl_path in sorted(mdl_dir.glob("*.mdl")):
    mdx_path = mdl_path.with_suffix(".mdx")
    if not mdx_path.exists():
        continue

    # Read MDL header to determine game version
    with open(mdl_path, "rb") as f:
        # Skip first 12 bytes (MDL header: 0, mdl_size, mdx_size)
        f.seek(12)
        # Read geometry header function pointers
        fp0 = struct.unpack("<I", f.read(4))[0]
        fp1 = struct.unpack("<I", f.read(4))[0]

    # K1 function pointers are around 4216656, K2 around 4216880
    if 4216000 <= fp0 <= 4217000:
        if 4216600 <= fp0 <= 4216700:
            game = "K1"
        elif 4216800 <= fp0 <= 4216900:
            game = "K2 (TSL)"
        else:
            game = f"Unknown (fp0=0x{fp0:08X})"
    else:
        game = f"Unknown (fp0=0x{fp0:08X})"

    print(f"{mdl_path.name:30} -> {game} (fp0=0x{fp0:08X}, fp1=0x{fp1:08X})")
