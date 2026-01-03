"""KotorDiff-driven comparison command for KotorCLI."""

from __future__ import annotations

from argparse import Namespace

from loggerplus import RobustLogger as Logger  # type: ignore[import-untyped]

from kotorcli.diff_tool.cli import execute_cli, has_cli_paths


def cmd_diff_installation(args: Namespace, logger: Logger) -> int:
    """Run the integrated KotorDiff tool.

    - When CLI paths are provided (or explicit options), run headless.
    - Otherwise, launch the GUI for interactive comparisons.
    """
    try:
        if has_cli_paths(args) and not args.gui:
            return execute_cli(args, exit_on_completion=False)

        from kotorcli.diff_tool.gui import KotorDiffApp  # noqa: PLC0415

        app = KotorDiffApp()
        app.root.mainloop()
    except Exception:
        logger.exception("KotorDiff execution failed")
        return 1
    else:
        return 0
