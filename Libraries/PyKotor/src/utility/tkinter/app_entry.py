"""Base entry point utilities for PyKotor GUI tools.

This module provides reusable functions and patterns for creating
consistent entry points across all PyKotor GUI applications.

Usage in __main__.py:
    from utility.tkinter.app_entry import (
        is_frozen,
        is_running_from_temp,
        setup_sys_path,
        create_exception_hook,
        create_cleanup_func,
        main_wrapper,
    )

    # Setup paths (call early, before other imports)
    setup_sys_path(__file__)

    # After imports
    from myapp.cli import parse_args, execute_cli
    from myapp.app import App

    sys.excepthook = create_exception_hook("MyApp")

    def main():
        main_wrapper(
            app_class=App,
            parse_args_func=parse_args,
            execute_cli_func=execute_cli,
            cli_condition=lambda args: bool(args.some_required_arg),
            cleanup_func=create_cleanup_func("MyApp"),
        )

    if __name__ == "__main__":
        main()
"""
from __future__ import annotations

import atexit
import pathlib
import sys
import tempfile

from contextlib import suppress
from types import TracebackType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Callable

    from utility.tkinter.base_app import BaseApp


def is_frozen() -> bool:
    """Check if running as a frozen executable (e.g., PyInstaller).

    Returns:
        True if running from a frozen executable
    """
    return (
        getattr(sys, "frozen", False)
        or getattr(sys, "_MEIPASS", False)
        or tempfile.gettempdir() in sys.executable
    )


def is_running_from_temp() -> bool:
    """Check if running from a temporary directory (e.g., inside a zip).

    Returns:
        True if executable is in a temp directory
    """
    from pathlib import Path
    app_path = Path(sys.executable)
    temp_dir = tempfile.gettempdir()
    return str(app_path).startswith(temp_dir)


def setup_sys_path(
    module_file: str,
    *,
    include_pykotor: bool = True,
    include_utility: bool = True,
    include_module_parent: bool = True,
):
    """Set up sys.path for development mode.

    This function adds the necessary paths for imports to work when
    running from source (not frozen). Should be called early in __main__.py
    before other imports.

    Args:
        module_file: The __file__ of the calling module
        include_pykotor: Whether to add PyKotor library path
        include_utility: Whether to add Utility library path
        include_module_parent: Whether to add the module's parent (src) directory
    """
    if is_frozen():
        return

    def update_sys_path(path: pathlib.Path):
        working_dir = str(path)
        if working_dir not in sys.path:
            sys.path.append(working_dir)

    module_path = pathlib.Path(module_file)

    # Standard layout: Tools/<ToolName>/src/<module>/__main__.py
    # -> parents[4] = repo root containing Libraries/
    # Alternatively: may need parents[3] or parents[4] depending on structure

    # Try to find Libraries directory by walking up
    for i in range(2, 6):  # Try 2-5 levels up
        with suppress(IndexError, Exception):
            potential_root = module_path.parents[i]
            libraries_path = potential_root / "Libraries"
            if libraries_path.exists():
                if include_pykotor:
                    pykotor_path = libraries_path / "PyKotor" / "src" / "pykotor"
                    if pykotor_path.exists():
                        update_sys_path(pykotor_path.parent)

                if include_utility:
                    # utility is inside PyKotor/src
                    utility_path = libraries_path / "PyKotor" / "src" / "utility"
                    if utility_path.exists():
                        update_sys_path(utility_path.parent)
                break

    # Add module parent (src directory)
    if include_module_parent:
        with suppress(Exception):
            update_sys_path(module_path.parents[1])


def create_exception_hook(
    app_name: str,
    exit_code: int = 1,
) -> Callable[[type[BaseException], BaseException, TracebackType | None], None]:
    """Create a sys.excepthook handler for uncaught exceptions.

    The handler:
    - Logs the exception using RobustLogger
    - Shows a tkinter messagebox (if available)
    - Prints to stderr
    - Exits with the specified exit code

    Args:
        app_name: Application name for log messages
        exit_code: Exit code to use on crash

    Returns:
        Exception hook function suitable for sys.excepthook
    """
    def on_app_crash(
        etype: type[BaseException],
        exc: BaseException,
        tback: TracebackType | None,
    ):
        from loggerplus import RobustLogger

        from utility.error_handling import universal_simplify_exception

        title, short_msg = universal_simplify_exception(exc)

        # Attempt to create traceback if missing
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

        RobustLogger().error(f"Unhandled exception in {app_name}.", exc_info=(etype, exc, tback))

        # Try GUI messagebox
        with suppress(Exception):
            from tkinter import Tk, messagebox
            root = Tk()
            root.withdraw()
            messagebox.showerror(title, short_msg)
            root.destroy()

        # Print to stderr
        print(f"[CRASH] {title}: {short_msg}", file=sys.stderr)
        sys.exit(exit_code)

    return on_app_crash


def create_cleanup_func(
    app_name: str,
) -> Callable[[BaseApp], None]:
    """Create a cleanup function for atexit registration.

    Args:
        app_name: Application name for log messages

    Returns:
        Cleanup function that takes an App instance
    """
    def cleanup(app: BaseApp):
        """Prevent the app from running in background after sys.exit."""
        from utility.system.app_process.shutdown import terminate_main_process

        print(f"Fully shutting down {app_name}...")
        terminate_main_process()
        app.root.destroy()

    return cleanup


def check_temp_directory(
    app_name: str = "This application",
) -> bool:
    """Check if running from temp directory and show error if so.

    Should be called at the start of __main__.py's if __name__ == "__main__" block.

    Args:
        app_name: Name to use in error message

    Returns:
        True if running from temp (error was shown), False if OK to proceed
    """
    if not is_running_from_temp():
        return False

    error_msg = (
        f"{app_name} cannot be run from within a zip or temporary directory. "
        "Please extract it to a permanent location before running."
    )

    # Try GUI message
    with suppress(Exception):
        from tkinter import Tk, messagebox
        root = Tk()
        root.withdraw()
        messagebox.showerror("Error", error_msg)
        root.destroy()

    # Print to stderr
    print(f"[Error] {error_msg}", file=sys.stderr)
    sys.exit("Exiting: Application was run from a temporary or zip directory.")
    return True


def main_wrapper(
    app_class: type[BaseApp],
    parse_args_func: Callable[[], Namespace],
    execute_cli_func: Callable[[Namespace], Any] | None = None,
    cli_condition: Callable[[Namespace], bool] | None = None,
    cleanup_func: Callable[[BaseApp], None] | None = None,
    *,
    gui_fallback_message: str = "[Warning] Display driver not available, cannot run in GUI mode without command-line arguments.",
):
    """Main wrapper that handles CLI vs GUI mode selection.

    This provides a standard pattern for PyKotor tool entry points:
    1. Parse command line arguments
    2. If CLI condition is met, run in CLI mode
    3. Otherwise, try to launch GUI
    4. If GUI fails, show fallback message

    Args:
        app_class: The App class to instantiate for GUI mode
        parse_args_func: Function to parse command line arguments
        execute_cli_func: Function to execute CLI operations (optional)
        cli_condition: Function that returns True if CLI mode should be used
        cleanup_func: Cleanup function for atexit registration
        gui_fallback_message: Message to show if GUI is unavailable
    """
    from loggerplus import RobustLogger

    cmdline_args = parse_args_func()

    # Determine if we should run in CLI mode
    force_cli = cli_condition(cmdline_args) if cli_condition else False

    if force_cli and execute_cli_func is not None:
        # CLI mode explicitly requested
        execute_cli_func(cmdline_args)
    else:
        # Try GUI mode, fall back to CLI if unavailable
        try:
            app = app_class()
            if cleanup_func is not None:
                atexit.register(lambda: cleanup_func(app))
            app.root.mainloop()
        except Exception as e:  # noqa: BLE001
            RobustLogger().warning(f"GUI not available: {e}")
            print(gui_fallback_message)
            print("[Info] Use --help to see CLI options")
            sys.exit(0)

