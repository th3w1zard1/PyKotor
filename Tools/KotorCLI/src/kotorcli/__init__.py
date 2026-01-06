"""KotorCLI compatibility shim package.

This package forwards to PyKotor CLI for backwards compatibility.
"""

from __future__ import annotations

# Re-export main entry point
from pykotor.cli.__main__ import main  # noqa: F401

# Re-export version
from pykotor.cli.version import VERSION as __version__  # noqa: F401
