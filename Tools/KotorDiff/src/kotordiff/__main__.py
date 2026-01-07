"""KotorDiff shim entry point - forwards to pykotor.diff_tool."""

from __future__ import annotations

import sys
from pathlib import Path

# Add the PyKotor source directory to the Python path
script_dir = Path(__file__).resolve().parent  # kotordiff
src_dir = script_dir.parent  # src
kotordiff_dir = src_dir.parent  # KotorDiff
tools_dir = kotordiff_dir.parent  # Tools
pykotor_dir = tools_dir.parent  # PyKotor root
pykotor_src = pykotor_dir / "Libraries" / "PyKotor" / "src"
if str(pykotor_src) not in sys.path:
    sys.path.insert(0, str(pykotor_src))

# Forward to pykotor.diff_tool
from pykotor.diff_tool.__main__ import main  # noqa: F401

if __name__ == "__main__":
    sys.exit(main())
