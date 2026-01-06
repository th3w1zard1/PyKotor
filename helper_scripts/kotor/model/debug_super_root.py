#!/usr/bin/env python
"""Debug the offset_to_super_root calculation by comparing PyKotor vs MDLOps."""

from __future__ import annotations

import struct
import subprocess
import sys
import tempfile

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "Libraries" / "PyKotor" / "src"))

from pykotor.common.misc import Game
from pykotor.extract.file import ResourceResult
from pykotor.extract.installation import Installation
from pykotor.resource.formats.mdl import read_mdl, write_mdl
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath, find_kotor_paths_from_default


def get_uint32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def main():
    # Use a model with animations to see offset_to_super_root differences
    model_name = "comm_b_f2"  # Has animations
    game = Game.K1

    paths: dict[Game, list[CaseAwarePath]] = find_kotor_paths_from_default()
    game_paths = paths.get(game, [])
    if not game_paths:
        print(f"No {game.name} installation found")
        return

    installation: Installation = Installation(game_paths[0])
    mdlops_exe = Path(__file__).parents[3] / "vendor" / "MDLOps" / "mdlops.exe"

    # Also check Override for test model
    override = game_paths[0] / "Override"
    orig_mdl_file = override / f"{model_name}.mdl"
    orig_mdx_file = override / f"{model_name}.mdx"

    if orig_mdl_file.exists():
        orig_mdl = orig_mdl_file.read_bytes()
        orig_mdx = orig_mdx_file.read_bytes() if orig_mdx_file.exists() else b""
        print(f"Loaded {model_name} from Override")
    else:
        mdl_res: ResourceResult | None = installation.resource(model_name, ResourceType.MDL)
        mdx_res = installation.resource(model_name, ResourceType.MDX)
        if mdl_res is None:
            print(f"Model {model_name} not found")
            return
        orig_mdl = mdl_res.data
        orig_mdx = mdx_res.data if mdx_res else b""
        print(f"Loaded {model_name} from installation")

    print(f"Original MDL size: {len(orig_mdl)} bytes")
    print(f"Original MDX size: {len(orig_mdx)} bytes")

    with tempfile.TemporaryDirectory(prefix="mdl_superroot_") as td:
        td_path = Path(td)

        orig_mdl_path = td_path / f"{model_name}.mdl"
        orig_mdx_path = td_path / f"{model_name}.mdx"
        orig_mdl_path.write_bytes(orig_mdl)
        if orig_mdx:
            orig_mdx_path.write_bytes(orig_mdx)

        # PyKotor roundtrip
        mdl_obj = read_mdl(orig_mdl, source_ext=orig_mdx or None, file_format=ResourceType.MDL)
        pykotor_mdl_path = td_path / f"{model_name}-pykotor.mdl"
        pykotor_mdx_path = td_path / f"{model_name}-pykotor.mdx"
        write_mdl(mdl_obj, pykotor_mdl_path, ResourceType.MDL, target_ext=pykotor_mdx_path)
        pykotor_mdl = pykotor_mdl_path.read_bytes()

        # MDLOps roundtrip (decompile + recompile)
        result = subprocess.run([str(mdlops_exe), str(orig_mdl_path)], cwd=str(td_path), capture_output=True, timeout=60)
        if result.returncode != 0:
            print(f"MDLOps decompile failed: {result.stderr.decode()}")
            return

        ascii_path = td_path / f"{model_name}-ascii.mdl"
        if not ascii_path.exists():
            print(f"MDLOps ASCII not found: {ascii_path}")
            return

        result = subprocess.run([str(mdlops_exe), str(ascii_path), "-k1"], cwd=str(td_path), capture_output=True, timeout=60)
        if result.returncode != 0:
            print(f"MDLOps compile failed: {result.stderr.decode()}")
            return

        mdlops_mdl_path = td_path / f"{model_name}-ascii-k1-bin.mdl"
        if not mdlops_mdl_path.exists():
            print(f"MDLOps binary not found: {mdlops_mdl_path}")
            return
        mdlops_mdl = mdlops_mdl_path.read_bytes()

        print("\n=== File Sizes ===")
        print(f"Original: {len(orig_mdl)}")
        print(f"PyKotor:  {len(pykotor_mdl)}")
        print(f"MDLOps:   {len(mdlops_mdl)}")

        print("\n=== Header Fields (file positions in decimal) ===")
        # File header: 12 bytes at position 0
        # Position 0: magic (should be 0)
        # Position 4: MDL size (excluding file header)
        # Position 8: MDX size
        print(f"{'Field':<30} {'Pos':<6} {'Orig':<12} {'PyKotor':<12} {'MDLOps':<12}")
        print("-" * 72)

        fields = [
            ("magic", 0x00),                  # 0
            ("mdl_data_size", 0x04),          # 4
            ("mdx_size", 0x08),               # 8
            # Geometry header (offset from file header = 0x0C)
            ("func_ptr0", 0x0C),              # 12
            ("func_ptr1", 0x10),              # 16
            # name is at 0x14, 32 bytes
            ("root_node_offset", 0x34),       # 52
            ("node_count", 0x38),             # 56
            # ... unknowns from 0x3C-0x57
            ("geometry_type", 0x58),          # 88
            # Model header at 0x5C
            ("model_type_byte", 0x5C),        # 92
            ("offset_to_animations", 0x64),   # 100
            ("animation_count", 0x68),        # 104
            ("animation_count2", 0x6C),       # 108
            # bounding box at 0x74-0x8B  (116-139)
            # radius at 0x8C  (140)
            # anim_scale at 0x90  (144)
            # supermodel at 0x94, 32 bytes  (148-179)
            # Names header at 0xB4  (180)
            ("offset_to_super_root", 0xB4),   # 180
            ("unknown3", 0xB8),               # 184
            ("mdx_size_in_header", 0xBC),     # 188
            ("mdx_offset", 0xC0),             # 192
            ("offset_to_name_offsets", 0xC4), # 196
            ("name_offsets_count", 0xC8),     # 200
            ("name_offsets_count2", 0xCC),    # 204
        ]

        for name, pos in fields:
            orig_val = get_uint32(orig_mdl, pos) if len(orig_mdl) > pos + 4 else "N/A"
            pk_val = get_uint32(pykotor_mdl, pos) if len(pykotor_mdl) > pos + 4 else "N/A"
            mo_val = get_uint32(mdlops_mdl, pos) if len(mdlops_mdl) > pos + 4 else "N/A"

            # Check if values match
            match = ""
            if isinstance(orig_val, int) and isinstance(pk_val, int) and isinstance(mo_val, int):
                if pk_val == mo_val:
                    match = " (PK=MO)"
                elif pk_val != mo_val:
                    match = " *** DIFF ***"

            print(f"{name:<30} {pos:<6} {str(orig_val):<12} {str(pk_val):<12} {str(mo_val):<12}{match}")

        print("\n=== Key Analysis ===")
        or_root = get_uint32(orig_mdl, 52)
        pk_root = get_uint32(pykotor_mdl, 52)
        mo_root = get_uint32(mdlops_mdl, 52)
        or_super = get_uint32(orig_mdl, 180)
        pk_super = get_uint32(pykotor_mdl, 180)
        mo_super = get_uint32(mdlops_mdl, 180)
        or_names = get_uint32(orig_mdl, 196)
        pk_names = get_uint32(pykotor_mdl, 196)
        mo_names = get_uint32(mdlops_mdl, 196)

        print(f"Original: root_node_offset={or_root}, offset_to_super_root={or_super}, offset_to_name_offsets={or_names}")
        print(f"PyKotor:  root_node_offset={pk_root}, offset_to_super_root={pk_super}, offset_to_name_offsets={pk_names}")
        print(f"MDLOps:   root_node_offset={mo_root}, offset_to_super_root={mo_super}, offset_to_name_offsets={mo_names}")

        # Check if original super_root differs from root_node_offset
        if or_super != or_root:
            print(f"\nORIGINAL: offset_to_super_root ({or_super}) != root_node_offset ({or_root})")
            print("  This is UNUSUAL - examining what's at these offsets...")

            # What's at root_node_offset + 12 (file pos) in original?
            file_pos_root = or_root + 12
            file_pos_super = or_super + 12
            print(f"  File pos of root_node_offset: {file_pos_root}")
            print(f"  File pos of offset_to_super_root: {file_pos_super}")

            # Read node type at root_node_offset
            if file_pos_root + 2 <= len(orig_mdl):
                node_type = struct.unpack_from("<H", orig_mdl, file_pos_root)[0]
                print(f"  Node type at root_node_offset: 0x{node_type:04X}")

            # Check if offset_to_super_root points to valid data
            if file_pos_super + 4 <= len(orig_mdl):
                data_at_super = struct.unpack_from("<I", orig_mdl, file_pos_super)[0]
                print(f"  Data at offset_to_super_root: {data_at_super} (0x{data_at_super:08X})")

        print("\n=== Layout Calculation ===")
        # Calculate what offset_to_super_root SHOULD be based on node writing position
        # For PyKotor:
        pk_name_count = get_uint32(pykotor_mdl, 200)
        pk_anim_offset = get_uint32(pykotor_mdl, 100)
        pk_anim_count = get_uint32(pykotor_mdl, 104)
        print(f"PyKotor: name_offsets_count={pk_name_count}, offset_to_animations={pk_anim_offset}, animation_count={pk_anim_count}")

        # The node start should be: after header + names + anims
        # But if no anims, it's after names
        # Let's see what PyKotor's root_node_offset actually is
        print(f"PyKotor actual root_node_offset: {pk_root}")
        print("This should equal the position after anims (or after names if no anims)")


if __name__ == "__main__":
    main()
