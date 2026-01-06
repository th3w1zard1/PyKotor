"""PyKotor CLI package.

This package provides command-line interface functionality for PyKotor.
The CLI can be invoked via:
- `python -m pykotor` (module entrypoint)
- `pykotor` (console script)
- `pykotorcli` (console script, alias)
"""

from __future__ import annotations

from pykotor.cli.version import VERSION

__version__ = VERSION
__all__: list[str] = []
