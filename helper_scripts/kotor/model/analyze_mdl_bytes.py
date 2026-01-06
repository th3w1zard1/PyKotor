#!/usr/bin/env python
"""Analyze raw MDL bytes to understand layout."""

from __future__ import annotations

import struct
import subprocess
import sys
import tempfile

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "Libraries" / "PyKotor" / "src"))

from pykotor.common.misc import Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.mdl import read_mdl, write_mdl
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath, find_kotor_paths_from_default
from pykotor.extract.file import ResourceResult


def hex_dump(data: bytes, start: int, end: int, label: str):
    """Print hex dump with field annotations."""
    print(f"\n=== {label} (0x{start:04X}-0x{end:04X}) ===")
    for i in range(start, end, 16):
        chunk = data[i:min(i+16, end)]
        hex_str = " ".join(f"{b:02X}" for b in chunk)
        ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"  {i:04X}: {hex_str:<48} {ascii_str}")


def get_uint32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def main():
    model_name = "comm_b_f2"
    game = Game.K1

    paths: dict[Game, list[CaseAwarePath]] = find_kotor_paths_from_default()
    game_paths = paths.get(game, [])
    if not game_paths:
        print(f"No {game.name} installation found")
        return

    installation: Installation = Installation(game_paths[0])
    mdlops_exe = Path(__file__).parents[3] / "vendor" / "MDLOps" / "mdlops.exe"

    mdl_res: ResourceResult | None = installation.resource(model_name, ResourceType.MDL)
    mdx_res = installation.resource(model_name, ResourceType.MDX)
    assert mdl_res is not None and mdx_res is not None

    orig_mdl = mdl_res.data
    orig_mdx = mdx_res.data

    with tempfile.TemporaryDirectory(prefix="mdl_bytes_") as td:
        td_path = Path(td)

        orig_mdl_path = td_path / f"{model_name}.mdl"
        orig_mdx_path = td_path / f"{model_name}.mdx"
        orig_mdl_path.write_bytes(orig_mdl)
        orig_mdx_path.write_bytes(orig_mdx)

        # PyKotor roundtrip
        mdl_obj = read_mdl(orig_mdl, source_ext=orig_mdx, file_format=ResourceType.MDL)
        pykotor_mdl_path = td_path / f"{model_name}-pykotor.mdl"
        pykotor_mdx_path = td_path / f"{model_name}-pykotor.mdx"
        write_mdl(mdl_obj, pykotor_mdl_path, ResourceType.MDL, target_ext=pykotor_mdx_path)
        pykotor_mdl = pykotor_mdl_path.read_bytes()

        # MDLOps roundtrip
        subprocess.run([str(mdlops_exe), str(orig_mdl_path)], cwd=str(td_path), capture_output=True, timeout=60)
        subprocess.run([str(mdlops_exe), str(td_path / f"{model_name}-ascii.mdl"), "-k1"], cwd=str(td_path), capture_output=True, timeout=60)
        mdlops_mdl = (td_path / f"{model_name}-ascii-k1-bin.mdl").read_bytes()

        print(f"Model: {model_name}")
        print(f"Original: MDL={len(orig_mdl)}")
        print(f"PyKotor:  MDL={len(pykotor_mdl)}")
        print(f"MDLOps:   MDL={len(mdlops_mdl)}")

        # Show first 256 bytes of each
        hex_dump(orig_mdl, 0, 256, "Original MDL Header")
        hex_dump(pykotor_mdl, 0, 256, "PyKotor MDL Header")
        hex_dump(mdlops_mdl, 0, 256, "MDLOps MDL Header")

        # Decode specific fields (all offsets are file-relative after 12-byte file header)
        # File header: 0x00-0x0B (12 bytes)
        # Geometry header starts at 0x0C
        
        print("\n=== Key Fields ===")
        print(f"{'Field':<40} {'Orig':<15} {'PyKotor':<15} {'MDLOps':<15}")
        
        # File header
        for name, off in [("MDL Size", 4), ("MDX Size", 8)]:
            print(f"{name:<40} {get_uint32(orig_mdl, off):<15} {get_uint32(pykotor_mdl, off):<15} {get_uint32(mdlops_mdl, off):<15}")
        
        # Geometry header (starts at 0x0C = 12)
        base = 12
        for name, rel_off in [
            ("func_ptr0", 0),
            ("func_ptr1", 4),
            ("root_node_offset", 40),  # After 32-byte name
            ("node_count", 44),
        ]:
            off = base + rel_off
            print(f"{name:<40} {get_uint32(orig_mdl, off):<15} {get_uint32(pykotor_mdl, off):<15} {get_uint32(mdlops_mdl, off):<15}")
        
        # Model header fields (after geometry header which is 48 bytes)
        model_header_base = 12 + 48  # = 60
        for name, rel_off in [
            ("unknown1", 6),  # 2 bytes padding + 2 bytes fog + 2 bytes unknown1?
            ("offset_to_animations", 8),
            ("animation_count", 12),
            ("offset_to_super_root", 28),
            ("mdx_size", 36),
            ("mdx_offset", 40),
            ("offset_to_name_offsets", 44),  # Should be at offset 60+44=104 in file
            ("name_offsets_count", 48),
        ]:
            off = model_header_base + rel_off
            print(f"{name} (file offset {off})"[:40].ljust(40) + f" {get_uint32(orig_mdl, off):<15} {get_uint32(pykotor_mdl, off):<15} {get_uint32(mdlops_mdl, off):<15}")
        
        # Show bytes around the name header area (around 0xB0-0xC0)
        print("\n--- Bytes 0xA0-0xC4 (name header area) ---")
        for label, data in [("Original", orig_mdl), ("PyKotor", pykotor_mdl), ("MDLOps", mdlops_mdl)]:
            print(f"\n{label}:")
            for i in range(0xA0, 0xC4, 4):
                val = get_uint32(data, i)
                print(f"  0x{i:02X}: {val:10} (0x{val:08X})")


if __name__ == "__main__":
    main()

