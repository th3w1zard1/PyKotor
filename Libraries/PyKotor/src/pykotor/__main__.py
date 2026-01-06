"""Module entry point for PyKotor CLI.

This allows PyKotor to be run as:
    python -m pykotor
"""

from __future__ import annotations

from pykotor.cli.__main__ import main

if __name__ == "__main__":
    import sys

    sys.exit(main())
