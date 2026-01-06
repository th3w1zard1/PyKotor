from __future__ import annotations

import atexit
import importlib
import multiprocessing
import os
import pathlib
import subprocess
import sys
import tempfile
import threading
import traceback

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import TracebackType


def is_frozen() -> bool:
    """Check if the toolset is frozen in an executable file e.g. with PyInstaller.

    Returns:
        bool: True if the toolset is frozen, False otherwise.
    """
    return (
        getattr(sys, "frozen", False)
        or getattr(sys, "_MEIPASS", False)
    )


def on_app_crash(
    etype: type[BaseException],
    exc: BaseException,
    tback: TracebackType | None,
):  # sourcery skip: extract-method
    """Handle uncaught exceptions.

    This function should be called when an uncaught exception occurs, set to sys.excepthook.
    """
    if issubclass(etype, KeyboardInterrupt):
        sys.__excepthook__(etype, exc, tback)
        return
    from loggerplus import RobustLogger  # noqa: PLC0415
    import time  # noqa: PLC0415
    logger = RobustLogger()
    logger.critical("Uncaught exception", exc_info=(etype, exc, tback))

    # If the Qt app is running, also surface a non-blocking dialog so users aren't left with a silent crash.
    # This must be best-effort and must never raise.
    try:
        from qtpy.QtCore import QTimer, Qt  # type: ignore[import-not-found]
        from qtpy.QtWidgets import QApplication, QMessageBox  # type: ignore[import-not-found]

        app = QApplication.instance()
        if app is None:
            return

        # Create a fingerprint of this exception to prevent duplicate dialogs
        # Use exception type, message, and the first frame of the traceback
        exc_fingerprint: str
        if tback is not None:
            # Get the first frame's filename and line number
            tb_frame = tback.tb_frame
            exc_fingerprint = f"{etype.__name__}:{str(exc)[:100]}:{tb_frame.f_code.co_filename}:{tb_frame.f_lineno}"
        else:
            exc_fingerprint = f"{etype.__name__}:{str(exc)[:100]}"

        # Initialize tracking structures if they don't exist
        if not hasattr(on_app_crash, "_toolset_seen_exceptions"):
            setattr(on_app_crash, "_toolset_seen_exceptions", set())
        if not hasattr(on_app_crash, "_toolset_exception_timestamps"):
            setattr(on_app_crash, "_toolset_exception_timestamps", {})
        if not hasattr(on_app_crash, "_toolset_dialog_count"):
            setattr(on_app_crash, "_toolset_dialog_count", 0)
        if not hasattr(on_app_crash, "_toolset_crash_boxes"):
            setattr(on_app_crash, "_toolset_crash_boxes", [])

        seen_exceptions: set[str] = getattr(on_app_crash, "_toolset_seen_exceptions")
        exception_timestamps: dict[str, float] = getattr(on_app_crash, "_toolset_exception_timestamps")
        dialog_count: int = getattr(on_app_crash, "_toolset_dialog_count")
        crash_boxes: list[QMessageBox] = getattr(on_app_crash, "_toolset_crash_boxes")

        # Check if we've seen this exact exception recently (within 5 seconds)
        current_time = time.time()
        last_seen = exception_timestamps.get(exc_fingerprint, 0)
        cooldown_period = 5.0  # seconds

        # Maximum number of dialogs to show (prevent memory exhaustion)
        max_dialogs = 3

        # Skip if:
        # 1. We've already shown a dialog for this exact exception within the cooldown period
        # 2. We've already shown too many dialogs total
        if (current_time - last_seen) < cooldown_period:
            # Still log it, but don't show another dialog
            logger.debug(f"Suppressing duplicate exception dialog: {exc_fingerprint}")
            return

        if dialog_count >= max_dialogs:
            # Still log it, but don't show another dialog
            logger.warning(f"Maximum dialog limit reached ({max_dialogs}), suppressing exception dialog: {exc_fingerprint}")
            return

        # Mark this exception as seen and update timestamp
        seen_exceptions.add(exc_fingerprint)
        exception_timestamps[exc_fingerprint] = current_time
        setattr(on_app_crash, "_toolset_dialog_count", dialog_count + 1)

        # Clean up old timestamps (older than 60 seconds) to prevent memory leak
        cutoff_time = current_time - 60.0
        exception_timestamps = {k: v for k, v in exception_timestamps.items() if v > cutoff_time}
        setattr(on_app_crash, "_toolset_exception_timestamps", exception_timestamps)

        details = "".join(traceback.format_exception(etype, exc, tback))

        def _show_dialog():  # noqa: ANN001
            try:
                box = QMessageBox()
                box.setIcon(QMessageBox.Icon.Critical)
                box.setWindowTitle("Unexpected error")
                box.setText("An unexpected error occurred. The application will continue running, but may be unstable.")
                box.setDetailedText(details)
                box.setWindowFlags(box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
                box.show()

                # Keep a reference to avoid GC closing the dialog immediately.
                # Limit the list size to prevent memory issues
                crash_boxes.append(box)
                if len(crash_boxes) > max_dialogs:
                    # Remove the oldest dialog
                    old_box = crash_boxes.pop(0)
                    try:
                        old_box.close()
                    except Exception:  # noqa: BLE001
                        pass
            except Exception:  # noqa: BLE001
                logger.exception("Failed to show crash dialog")

        QTimer.singleShot(0, _show_dialog)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to schedule crash dialog")


def fix_sys_and_cwd_path():
    """Fixes sys.path and current working directory for PyKotor.

    It makes no sense to call this function in frozen code.
    This function ensures a user can run toolset/__main__.py directly.
    """

    def update_sys_path(path: pathlib.Path):
        working_dir = str(path)
        if working_dir not in sys.path:
            sys.path.append(working_dir)

    file_absolute_path = pathlib.Path(__file__).resolve()

    pykotor_path = file_absolute_path.parents[4] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        update_sys_path(pykotor_path.parent)
    pykotor_gl_path = file_absolute_path.parents[4] / "Libraries" / "PyKotorGL" / "src" / "pykotor"
    if pykotor_gl_path.exists():
        update_sys_path(pykotor_gl_path.parent)
    utility_path = file_absolute_path.parents[4] / "Libraries" / "Utility" / "src"
    if utility_path.exists():
        update_sys_path(utility_path)
    toolset_path = file_absolute_path.parents[1] / "toolset"
    if toolset_path.exists():
        update_sys_path(toolset_path.parent)
        os.chdir(toolset_path)


def fix_frozen_paths():
    """Fixes sys.path for frozen builds.

    When frozen with PyInstaller, modules are bundled but paths may need adjustment.
    This ensures utility and other local modules are accessible.
    """
    if not is_frozen():
        return

    def update_sys_path(path: pathlib.Path):
        working_dir = str(path)
        if working_dir not in sys.path:
            sys.path.insert(0, working_dir)  # Insert at beginning for priority

    # For frozen builds, try to find utility relative to the executable
    # PyInstaller sets sys._MEIPASS to the temp directory where bundled files are extracted
    _meipass: str | None = getattr(sys, "_MEIPASS", None)
    if _meipass is not None:
        meipass: pathlib.Path = pathlib.Path(_meipass)
        # Utility should be bundled by PyInstaller, check if it exists
        utility_path = meipass / "utility"
        if utility_path.exists():
            update_sys_path(utility_path.parent)
        # Also check for utility in the same directory structure
        utility_src_path = meipass / "Libraries" / "Utility" / "src"
        if utility_src_path.exists():
            update_sys_path(utility_src_path)


def fix_qt_env_var():
    """Fix the QT_API environment variable.

    This function should be called when the toolset is not frozen.
    """
    qtpy_case_map: dict[str, str] = {
        "pyqt5": "PyQt5",
        "pyqt6": "PyQt6",
        "pyside2": "PySide2",
        "pyside6": "PySide6",
    }
    case_api_name = qtpy_case_map.get(os.environ.get("QT_API", "").lower().strip())
    if case_api_name in ("PyQt5", "PyQt6", "PySide2", "PySide6"):
        print(f"QT_API manually set by user to '{case_api_name}'.")
        os.environ["QT_API"] = case_api_name
    else:
        set_qt_api()


def set_qt_api():
    """Set the QT_API environment variable to the first available API.

    This function should only be called when the toolset is not frozen.
    """
    available_apis: list[str] = ["PyQt5", "PyQt6", "PySide2", "PySide6"]
    for api in available_apis:
        try:
            if api == "PyQt5":
                importlib.import_module("PyQt5.QtCore")
            elif api == "PyQt6":
                importlib.import_module("PyQt6.QtCore")
            elif api == "PySide2":
                importlib.import_module("PySide2.QtCore")
            elif api == "PySide6":
                importlib.import_module("PySide6.QtCore")
        except ImportError:  # noqa: S112, PERF203
            continue
        else:
            os.environ["QT_API"] = api
            print(f"QT_API auto-resolved as '{api}'.")
            break


def is_running_from_temp() -> bool:
    return str(pathlib.Path(sys.executable)).startswith(tempfile.gettempdir())


def main_init():
    """Initialize the Holocron Toolset.

    This function should be called before the QApplication is created.
    """
    # Set up paths BEFORE importing loggerplus (which depends on utility)
    if is_frozen():
        fix_frozen_paths()
    else:
        fix_sys_and_cwd_path()
        fix_qt_env_var()

    # Now safe to import loggerplus
    from loggerplus import RobustLogger  # noqa: PLC0415

    sys.excepthook = on_app_crash
    # Ensure thread exceptions (Python 3.8+) are routed to the same handler.
    def _thread_excepthook(args: threading.ExceptHookArgs):  # noqa: ANN001
        if args.exc_value is not None:
            on_app_crash(args.exc_type, args.exc_value, args.exc_traceback)

    threading.excepthook = _thread_excepthook
    is_main_process: bool = multiprocessing.current_process() == "MainProcess"
    if is_main_process:
        multiprocessing.set_start_method("spawn")  # 'spawn' is default on windows, linux/mac defaults to most likely 'fork' which breaks the built-in updater.
        
        # Fix for PyInstaller: Hide console windows for multiprocessing child processes on Windows
        #if sys.platform == "win32" and is_frozen():
        #    _patch_multiprocessing_for_windows()
        
        atexit.register(last_resort_cleanup)  # last_resort_cleanup already handles child processes.

    if is_frozen():
        RobustLogger().debug("App is frozen - calling multiprocessing.freeze_support()")
        multiprocessing.freeze_support()
        if is_main_process:
            set_qt_api()
    # Do not use `faulthandler.enable()` in the toolset!
    # https://bugreports.qt.io/browse/PYSIDE-2359
    #faulthandler.enable()


def _patch_multiprocessing_for_windows():
    """Patch multiprocessing to hide console windows on Windows when frozen.
    
    This prevents command prompt windows from appearing when multiprocessing
    spawns child processes in a PyInstaller-compiled application.
    
    The patch intercepts subprocess.Popen calls made by multiprocessing and
    adds the CREATE_NO_WINDOW flag to hide console windows.
    """
    try:
        import multiprocessing.popen_spawn_win32
        
        # Store original _launch method
        original_launch = multiprocessing.popen_spawn_win32.Popen._launch
        
        def patched_launch(self, process_obj):
            """Patched _launch that adds CREATE_NO_WINDOW flag to subprocess calls."""
            # Store original subprocess.Popen
            original_subprocess_popen = subprocess.Popen
            
            # Create a wrapper that adds CREATE_NO_WINDOW flag
            def no_window_popen(*args, **kwargs):
                if sys.platform == "win32":
                    # Add CREATE_NO_WINDOW flag to hide console window
                    kwargs.setdefault("creationflags", 0)
                    kwargs["creationflags"] |= subprocess.CREATE_NO_WINDOW
                return original_subprocess_popen(*args, **kwargs)
            
            # Temporarily replace subprocess.Popen during process launch
            subprocess.Popen = no_window_popen
            try:
                return original_launch(self, process_obj)
            finally:
                # Restore original subprocess.Popen
                subprocess.Popen = original_subprocess_popen
        
        # Replace the _launch method
        multiprocessing.popen_spawn_win32.Popen._launch = patched_launch
        
    except (ImportError, AttributeError) as e:
        # If patching fails, log but don't crash
        from loggerplus import RobustLogger  # noqa: PLC0415
        RobustLogger().debug(f"Could not patch multiprocessing for Windows (non-critical): {e}")


def last_resort_cleanup():
    """Prevents the toolset from running in the background after sys.exit is called.

    This function should be registered with atexit as early as possible.
    """
    from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]

    from utility.system.app_process.shutdown import gracefully_shutdown_threads, start_shutdown_process

    RobustLogger().info("Fully shutting down Holocron Toolset...")
    gracefully_shutdown_threads()
    RobustLogger().debug("Starting new shutdown process...")
    start_shutdown_process()
    RobustLogger().debug("Shutdown process started...")
    # The shutdown process will take care of the rest.
    # This is just a last resort to ensure the toolset doesn't run in the background.
    # This should be the last thing to run before the process exits.
    RobustLogger().debug("Last resort cleanup done.")
    # The process will exit when the shutdown process is done.
