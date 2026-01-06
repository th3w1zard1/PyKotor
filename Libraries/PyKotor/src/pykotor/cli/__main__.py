"""Main entry point for PyKotor CLI."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from pykotor.cli.dispatch import cli_main


def launch_gui() -> int:
    """Launch the Tkinter GUI when no CLI args are provided."""
    try:
        from pykotor.cli.gui.kitgenerator_app import App
    except Exception as exc:
        from loggerplus import RobustLogger  # type: ignore[import-untyped]

        RobustLogger().warning("GUI not available: %s", exc)
        print("[Warning] Display driver not available, cannot run in GUI mode without command-line arguments.")  # noqa: T201
        print("[Info] Use --help to see CLI options")  # noqa: T201
        return 0

    app = App()
    app.root.mainloop()
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Main entry point that selects CLI vs GUI based on arguments.

    - No arguments -> launch the Tkinter GUI.
    - Any arguments -> run headless CLI.
    """
    arg_list = list(sys.argv[1:] if argv is None else argv)
    if not arg_list:
        return launch_gui()
    return cli_main(arg_list)


if __name__ == "__main__":
    sys.exit(main())
