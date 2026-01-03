#!/usr/bin/env python3
"""Debug script for decompilation issues."""
import traceback
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "Libraries" / "PyKotor" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "Utility" / "src"))

from pykotor.resource.formats.ncs.ncs_auto import compile_nss, decompile_ncs
from pykotor.common.misc import Game

root = Path("vendor/Vanilla_KOTOR_Script_Source")
script_path = root / "K1" / "Modules" / "M01AA_Endar_Spire_Command_Module_end_m01aa" / "k_end_cut2_fght.nss"

if not script_path.exists():
    print(f"Script not found: {script_path}")
    sys.exit(1)

source = script_path.read_text(encoding="windows-1252", errors="ignore")
print(f"Compiling {script_path.name}...")
original_ncs = compile_nss(source, Game.K1)
print(f"Compiled successfully: {len(original_ncs.instructions)} instructions")

try:
    print("Decompiling...")
    decompiled = decompile_ncs(original_ncs, Game.K1)
    print("SUCCESS: Decompilation completed")
    print(f"Decompiled length: {len(decompiled)} characters")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    traceback.print_exc()
    sys.exit(1)

