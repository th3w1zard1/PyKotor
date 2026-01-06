#!/usr/bin/env python
"""Quick test for decompilation."""
import sys
import traceback

from pykotor.common.misc import Game
from pykotor.resource.formats.ncs.ncs_auto import compile_nss, decompile_ncs

source = """void main() { int a = 1; }"""

print("=== Compiling ===", file=sys.stderr)
ncs = compile_nss(source, Game.K1)
print(f"Compiled {len(ncs.instructions)} instructions", file=sys.stderr)

print("=== Decompiling ===", file=sys.stderr)
try:
    result = decompile_ncs(ncs, Game.K1)
    print("=== RESULT ===", file=sys.stderr)
    print(result, file=sys.stderr)
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)

