#!/usr/bin/env python3
"""KotorDiff entry point - handles GUI vs CLI mode selection."""
from __future__ import annotations

import atexit
import pathlib
import sys
import tempfile

from contextlib import suppress
from types import TracebackType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kotordiff.gui import KotorDiffApp


def is_frozen() -> bool:
    """Check if running as a frozen executable."""
    return (
        getattr(sys, "frozen", False)
        or getattr(sys, "_MEIPASS", False)
        or tempfile.gettempdir() in sys.executable
    )


if not is_frozen():

    def update_sys_path(path):
        working_dir = str(path)
        if working_dir not in sys.path:
            sys.path.append(working_dir)

    with suppress(Exception):
        pykotor_path = pathlib.Path(__file__).parents[4] / "Libraries" / "PyKotor" / "src" / "pykotor"
        if pykotor_path.exists():
            update_sys_path(pykotor_path.parent)
    with suppress(Exception):
        utility_path = pathlib.Path(__file__).parents[4] / "Libraries" / "Utility" / "src" / "utility"
        if utility_path.exists():
            update_sys_path(utility_path.parent)
    with suppress(Exception):
        update_sys_path(pathlib.Path(__file__).parents[1])


from loggerplus import RobustLogger  # noqa: E402  # type: ignore[import-untyped]

from kotordiff.cli import execute_cli, has_cli_paths, parse_args  # noqa: E402
from utility.error_handling import universal_simplify_exception  # noqa: E402
from utility.system.app_process.shutdown import terminate_main_process  # noqa: E402

CURRENT_VERSION = "1.0.0"


def on_app_crash(
    etype: type[BaseException],
    exc: BaseException,
    tback: TracebackType | None,
):
    """Handle uncaught exceptions."""
    title, short_msg = universal_simplify_exception(exc)
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
    force_cli = has_cli_paths(cmdline_args) and not cmdline_args.gui

    if force_cli:
        # CLI mode - paths were provided
        execute_cli(cmdline_args)
    else:
        # GUI mode
        try:
            from kotordiff.gui import KotorDiffApp
            app = KotorDiffApp()
            atexit.register(lambda: kotordiff_cleanup_func(app))
            app.root.mainloop()
        except Exception as e:  # noqa: BLE001
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
