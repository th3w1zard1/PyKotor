"""Console/terminal helpers for PyKotor CLI.

These helpers exist primarily to keep CLI output robust on Windows terminals that
may default to non-UTF-8 encodings (e.g. cp1252). Avoid emitting unicode glyphs
unless the active stdout encoding can represent them.
"""

from __future__ import annotations

import sys
from functools import lru_cache


def _stream_can_encode(text: str) -> bool:
    stream = sys.stdout
    encoding = getattr(stream, "encoding", None) or sys.getdefaultencoding()
    try:
        text.encode(encoding)
    except Exception:
        return False
    return True


@lru_cache(maxsize=1)
def ok_fail_symbols() -> tuple[str, str]:
    """Return `(ok, fail)` symbols that are safe for the current stdout encoding."""
    if _stream_can_encode("✓✗"):
        return "✓", "✗"
    return "OK", "X"
