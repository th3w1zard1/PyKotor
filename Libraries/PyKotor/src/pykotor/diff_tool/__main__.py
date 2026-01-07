#!/usr/bin/env python3
"""KotorDiff entry point - handles GUI vs CLI mode selection."""

from __future__ import annotations

import atexit
import sys
import tempfile

from contextlib import suppress
from types import TracebackType
from typing import TYPE_CHECKING

# sys.path modifications removed - pykotor is now a proper package
from loggerplus import RobustLogger  # type: ignore[import-untyped]
from pykotor.diff_tool.cli import execute_cli, has_cli_paths, parse_args
from utility.system.app_process.shutdown import terminate_main_process

if TYPE_CHECKING:
    from pykotor.diff_tool.gui import KotorDiffApp


def is_frozen() -> bool:
    """Check if running as a frozen executable."""
    return getattr(sys, "frozen", False) or getattr(sys, "_MEIPASS", False) or tempfile.gettempdir() in sys.executable


CURRENT_VERSION = "1.0.0"


def on_app_crash(
    etype: type[BaseException],
    exc: BaseException,
    tback: TracebackType | None,
):
    """Handle uncaught exceptions."""
    title, short_msg = (exc.__class__.__name__, str(exc))
    if tback is None:
        with suppress(Exception):
            import inspect

            current_stack = inspect.stack()
            if current_stack:
                current_stack = current_stack[1:][::-1]
                fake_traceback = None
                for frame_info in current_stack:
                    frame = frame_info.frame
                    fake_traceback = TracebackType(fake_traceback, frame, frame.f_lasti, frame.f_lineno)
                exc = exc.with_traceback(fake_traceback)
                tback = exc.__traceback__
    RobustLogger().error("Unhandled exception caught.", exc_info=(etype, exc, tback))

    with suppress(Exception):
        from tkinter import Tk, messagebox

        root = Tk()
        root.withdraw()
        messagebox.showerror(title, short_msg)
        root.destroy()

    print(f"[CRASH] {title}: {short_msg}", file=sys.stderr)
    sys.exit(1)


sys.excepthook = on_app_crash


def kotordiff_cleanup_func(app: KotorDiffApp):
    """Prevents the app from running in the background after sys.exit is called."""
    print("Fully shutting down KotorDiff...")
    terminate_main_process()
    app.root.destroy()


def main():
    """Main entry point."""
    cmdline_args = parse_args()

    # Determine if we should run in CLI mode
    force_cli = has_cli_paths(cmdline_args) and not getattr(cmdline_args, "gui", False)

    if force_cli:
        # CLI mode - paths were provided
        execute_cli(cmdline_args)
    else:
        # GUI mode - check if we can run GUI
        try:
            import os

            # Check if display is available
            display = os.environ.get("DISPLAY", "")
            if not display and os.name != "nt":  # Not Windows and no DISPLAY
                raise RuntimeError("No display available")
            from pykotor.diff_tool.gui import KotorDiffApp

            app = KotorDiffApp()
            atexit.register(lambda: kotordiff_cleanup_func(app))
            app.root.mainloop()
        except Exception as e:  # noqa: BLE001
            if has_cli_paths(cmdline_args):
                # If we have paths but GUI failed, fall back to CLI
                execute_cli(cmdline_args)
            else:
                RobustLogger().warning(f"GUI not available: {e}")
                print("[Warning] Display driver not available, cannot run in GUI mode without command-line arguments.")
                print("[Info] Use --help to see CLI options")
                sys.exit(0)


def is_running_from_temp():
    """Check if running from a temporary directory."""
    from pathlib import Path

    app_path = Path(sys.executable)
    temp_dir = tempfile.gettempdir()
    return str(app_path).startswith(temp_dir)


if __name__ == "__main__":
    if is_running_from_temp():
        error_msg = "This application cannot be run from within a zip or temporary directory. Please extract it to a permanent location before running."
        with suppress(Exception):
            from tkinter import Tk, messagebox

            root = Tk()
            root.withdraw()
            messagebox.showerror("Error", error_msg)
            root.destroy()
        print(f"[Error] {error_msg}", file=sys.stderr)
        sys.exit("Exiting: Application was run from a temporary or zip directory.")
    main()
