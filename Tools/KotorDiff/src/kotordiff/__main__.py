"""KotorDiff shim entry point - forwards to pykotor.diff_tool."""

from __future__ import annotations

import sys

# Forward to pykotor.diff_tool
from pykotor.diff_tool.__main__ import main  # noqa: F401

if __name__ == "__main__":
    sys.exit(main())
