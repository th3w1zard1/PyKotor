"""KotorCLI compatibility shim.

This module forwards all CLI functionality to the new PyKotor CLI implementation.
The kotorcli package is maintained for backwards compatibility.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence

# Forward to pykotor.cli
from pykotor.cli.__main__ import main  # type: ignore[import-untyped]


def kitgenerator_entry(argv: Sequence[str] | None = None) -> int:
    """Entry point for kitgenerator console script (compatibility shim)."""
    # Map to kit-generate command
    arg_list = list(sys.argv[1:] if argv is None else argv)
    if not arg_list:
        # No args -> launch GUI (same behavior as main)
        return main([])
    # Map to kit-generate command
    kit_args = ["kit-generate"] + arg_list
    return main(kit_args)


def gui_converter_entry(argv: Sequence[str] | None = None) -> int:
    """Entry point for gui-converter console script (compatibility shim)."""
    arg_list = list(sys.argv[1:] if argv is None else argv)
    if not arg_list:
        # No args -> launch GUI
        return main([])
    # Map to gui-convert command
    gui_args = ["gui-convert"] + arg_list
    return main(gui_args)


def kotordiff_entry(argv: Sequence[str] | None = None) -> int:
    """Entry point for kotordiff console script (compatibility shim)."""
    arg_list = list(sys.argv[1:] if argv is None else argv)
    # Map to diff-installation command
    diff_args = ["diff-installation"] + arg_list
    return main(diff_args)


if __name__ == "__main__":
    sys.exit(main())
