from __future__ import annotations

import asyncio
import cProfile
import logging
import os
import pstats
import sys

from contextlib import suppress
from datetime import datetime
from pathlib import Path

from loggerplus import RobustLogger
from qtpy.QtCore import QEvent, QObject, QThread
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QApplication, QMessageBox, QWidget

import resources_rc  # noqa: PLC0415, F401  # pylint: disable=ungrouped-imports,unused-import

from toolset.config import CURRENT_VERSION
from toolset.gui.windows.main import ToolWindow
from toolset.main_init import is_running_from_temp
from toolset.main_settings import setup_post_init_settings, setup_pre_init_settings, setup_toolset_default_env
from toolset.utils.qt_exceptions import install_asyncio_exception_handler, install_qt_signal_slot_safety_net, install_sys_unraisablehook
from toolset.utils.window import TOOLSET_WINDOWS
from utility.system.app_process.shutdown import terminate_child_processes


class ToolsetApplication(QApplication):
    """QApplication wrapper to route Qt callback exceptions to sys.excepthook.

    Qt callbacks (signals/events) can swallow exceptions and/or terminate the app
    without invoking `sys.excepthook`. Wrapping `notify()` ensures we capture and
    log unexpected errors via the existing `toolset.main_init.on_app_crash` hook.
    """

    def notify(self, receiver: QObject, event: QEvent) -> bool:  # type: ignore[override]
        try:
            return super().notify(receiver, event)
        except Exception:  # noqa: BLE001
            etype, exc, tback = sys.exc_info()
            if etype is not None and exc is not None:
                sys.excepthook(etype, exc, tback)
            return False


class VerboseEventTracer(QObject):
    """Ultimate debug event tracer – logs detailed Qt event diagnostics."""

    def __init__(self, logger: logging.Logger | None = None, budget: int = 10_000):
        super().__init__()
        self.logger = logger or logging.getLogger("EventTracer")
        self.logger.setLevel(logging.DEBUG)
        self.budget = budget  # Safety valve – set to -1 for unlimited

    @staticmethod
    def event_type_name(event_type: QEvent.Type) -> str:
        """Resolve a QEvent.Type to its enum name."""
        for name in dir(QEvent):
            value = getattr(QEvent, name)
            if isinstance(value, QEvent.Type) and value == event_type:
                return name
        return f"Unknown({int(event_type)})"

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: ARG002  # pyright: ignore[reportIncompatibleMethodOverride]
        if self.budget == 0:
            return False
        if self.budget > 0:
            self.budget -= 1

        obj_name = obj.objectName() or "(no name)"
        meta_object = obj.metaObject()
        qt_class = meta_object.className() if meta_object else "Unknown"
        py_class = type(obj).__name__
        ptr = f"0x{id(obj):x}"

        event_type = event.type()
        event_type_name = self.event_type_name(event_type)
        try:
            spontaneous = event.spontaneous()
        except AttributeError:
            spontaneous = "N/A"
        accepted = event.isAccepted()
        details = repr(event)

        self.logger.debug(
            "EVENT >>> obj='%s' qt_class=%s py_class=%s ptr=%s",
            obj_name,
            qt_class,
            py_class,
            ptr,
        )
        self.logger.debug(
            "          type=%-4s (%-20s) class=%-20s spontaneous=%s accepted=%s",
            int(event_type),
            event_type_name,
            type(event).__name__,
            spontaneous,
            accepted,
        )
        self.logger.debug("          details → %s", details)

        if isinstance(obj, QWidget):
            window_handle = obj.windowHandle()
            self.logger.debug(
                "          widget visible=%s hidden=%s enabled=%s geometry=%s pos=%s size=%s windowState=%s",
                obj.isVisible(),
                obj.isHidden(),
                obj.isEnabled(),
                obj.geometry(),
                obj.pos(),
                obj.size(),
                obj.windowState(),
            )
            if window_handle is not None:
                screen = window_handle.screen()
                screen_name = screen.name() if screen is not None else None
                self.logger.debug(
                    "          window exposed=%s screen=%s",
                    window_handle.isExposed(),
                    screen_name,
                )

        important_types = {
            QEvent.Type.Show,
            QEvent.Type.Hide,
            QEvent.Type.ShowToParent,
            QEvent.Type.Expose,
            QEvent.Type.Paint,
            QEvent.Type.Resize,
            QEvent.Type.Move,
            QEvent.Type.WindowStateChange,
            QEvent.Type.ActivationChange,
            QEvent.Type.Polish,
            QEvent.Type.PolishRequest,
        }
        if event_type in important_types:
            self.logger.warning("!!! IMPORTANT VISIBILITY EVENT: %s on %s", event_type_name, obj_name)
        return False


def qt_cleanup():
    """Cleanup so we can exit."""
    RobustLogger().debug("Closing/destroy all windows from TOOLSET_WINDOWS list, (%s to handle)...", len(TOOLSET_WINDOWS))
    for window in TOOLSET_WINDOWS:
        window.close()
        window.destroy()

    TOOLSET_WINDOWS.clear()
    terminate_child_processes()


def _should_enable_profiling() -> bool:
    """Check if profiling should be enabled.
    
    Profiling is controlled *exclusively* by an explicit toggle (env or CLI).
    It is not tied to debug/frozen state.
    
    Enable when:
      - Environment variable TOOLSET_PROFILE is one of: 1, true, yes, on
      - OR command-line argument --profile is present
    
    Disable when:
      - Environment variable TOOLSET_DISABLE_PROFILE is one of: 1, true, yes, on
      - OR command-line argument --no-profile is present
    
    Returns:
        bool: True if profiling should be enabled, False otherwise
    """
    env_enable = os.environ.get("TOOLSET_PROFILE", "").lower().strip() in ("1", "true", "yes", "on")
    cli_enable = "--profile" in sys.argv
    env_disable = os.environ.get("TOOLSET_DISABLE_PROFILE", "").lower().strip() in ("1", "true", "yes", "on")
    cli_disable = "--no-profile" in sys.argv
    return (env_enable or cli_enable) and not (env_disable or cli_disable)


def _save_profile_stats(profiler: cProfile.Profile, output_path: Path):
    """Save profiling statistics to files.
    
    Saves both:
    - Binary .prof file (for tools like snakeviz, py-spy, etc.)
    - Text .txt file (human-readable stats)
    
    Args:
        profiler: The cProfile.Profile instance
        output_path: Base path where to save the profile stats (will add .prof and .txt extensions)
    """
    try:
        # Save binary profile data (.prof) - compatible with snakeviz, py-spy, etc.
        profiler.dump_stats(str(output_path))
        
        # Also save human-readable text stats
        txt_path = output_path.with_suffix(".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            stats = pstats.Stats(profiler, stream=f)
            stats.sort_stats("cumulative")
            stats.print_stats()
        
        RobustLogger().info("Profile statistics saved:")
        RobustLogger().info(f"  - Binary: {output_path} (use with snakeviz: snakeviz {output_path})")
        RobustLogger().info(f"  - Text: {txt_path} (human-readable)")
    except Exception as e:
        RobustLogger().error(f"Failed to save profile statistics: {e}")


def _prune_old_profiles(profile_dir: Path, max_profiles: int = 10):
    """Keep only the newest `max_profiles` profile files (prof+txt)."""
    try:
        profs = sorted(profile_dir.glob("toolset_profile_*.prof"), key=lambda p: p.stat().st_mtime, reverse=True)
        if len(profs) <= max_profiles:
            return
        for stale_prof in profs[max_profiles:]:
            txt = stale_prof.with_suffix(".txt")
            with suppress(Exception):
                stale_prof.unlink()
            with suppress(Exception):
                if txt.exists():
                    txt.unlink()
        RobustLogger().info(
            "Pruned old profile files, kept newest %s (dir=%s)", max_profiles, profile_dir
        )
    except Exception as e:  # noqa: BLE001
        RobustLogger().warning(f"Failed to prune old profile files: {e}")


def main():
    """Main entry point for the Holocron Toolset.

    This block is ran when users run __main__.py directly.
    
    When not frozen, cProfile is enabled by default to profile the application execution.
    Profile statistics will be saved to a timestamped file in the current directory.
    Profiling can be disabled by setting TOOLSET_DISABLE_PROFILE=1 or using --no-profile flag.
    """
    setup_pre_init_settings()
    
    # Enable profiling if requested and not frozen
    enable_profiling = _should_enable_profiling()
    profiler: cProfile.Profile | None = None
    profile_output_path: Path | None = None
    
    profile_dir = Path(__file__).resolve().parent
    if enable_profiling:
        profiler = cProfile.Profile()
        profiler.enable()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        profile_output_path = profile_dir / f"toolset_profile_{timestamp}.prof"
        RobustLogger().info(f"Profiling enabled. Statistics will be saved to: {profile_output_path}")
        RobustLogger().info("To disable profiling, set TOOLSET_DISABLE_PROFILE=1 or use --no-profile flag")
        RobustLogger().info("Profiling will capture all function calls and execution times")

    app = ToolsetApplication(sys.argv)
    app.setApplicationName("HolocronToolset")
    app.setOrganizationName("PyKotor")
    app.setOrganizationDomain("github.com/OldRepublicDevs/PyKotor")
    app.setApplicationVersion(CURRENT_VERSION)
    app.setDesktopFileName("com.pykotor.toolset")
    app.setApplicationDisplayName("Holocron Toolset")
    icon_path = ":/images/icons/sith.png"
    icon = QIcon(icon_path)
    if icon.isNull():
        RobustLogger().warning(f"Warning: Main application icon not found at '{icon_path}'")
    else:
        app.setWindowIcon(icon)
    main_gui_thread: QThread | None = app.thread()
    assert main_gui_thread is not None, "Main GUI thread should not be None"
    main_gui_thread.setPriority(QThread.Priority.HighestPriority)

    # Global crash resistance:
    # - Route unraisable exceptions to sys.excepthook
    # - Wrap Qt signal/slot connections so Python exceptions in slots are forwarded to sys.excepthook
    install_sys_unraisablehook()
    install_qt_signal_slot_safety_net()
    
    def cleanup_with_profiling():
        """Cleanup function that also saves profiling stats if enabled."""
        # Disable profiler before cleanup to avoid profiling cleanup code
        if profiler is not None:
            profiler.disable()
        
        qt_cleanup()
        
        # Save profile stats after cleanup
        if profiler is not None and profile_output_path is not None:
            _save_profile_stats(profiler, profile_output_path)
            _prune_old_profiles(profile_dir, max_profiles=10)
    
    app.aboutToQuit.connect(cleanup_with_profiling)

    setup_post_init_settings()
    setup_toolset_default_env()

    if is_running_from_temp():
        QMessageBox.critical(
            None,
            "Error",
            "This application cannot be run from within a zip or temporary directory. Please extract it to a permanent location before running."
        )
        sys.exit("Exiting: Application was run from a temporary or zip directory.")

    RobustLogger().debug("TRACE: About to create ToolWindow")
    tool_window = ToolWindow()
    RobustLogger().debug("TRACE: ToolWindow created")
    RobustLogger().debug("TRACE: About to call tool_window.show()")
    tool_window.show()
    RobustLogger().debug("TRACE: tool_window.show() called")
    RobustLogger().debug("TRACE: About to call check_for_updates")
    tool_window.update_manager.check_for_updates(silent=True)
    RobustLogger().debug("TRACE: check_for_updates returned")
    RobustLogger().debug("TRACE: About to setup qasync")
    qasync_installed = False
    with suppress(ImportError):
        RobustLogger().debug("TRACE: Importing qasync")
        from qasync import QEventLoop  # type: ignore[import-not-found, import-untyped, note]  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]
        RobustLogger().debug("TRACE: qasync imported, creating QEventLoop")
        asyncio.set_event_loop(QEventLoop(app))
        RobustLogger().debug("TRACE: QEventLoop created and set")
        qasync_installed = True
    if qasync_installed:
        RobustLogger().debug("TRACE: qasync installed; asyncio event loop integrated with Qt")
    else:
        RobustLogger().debug("TRACE: qasync not installed, falling back to default event loop")

    # Best-effort: capture asyncio task exceptions too (especially when qasync is in use).
    install_asyncio_exception_handler()
    
    # Install event filter only when explicitly requested to avoid log spam/perf issues
    trace_events_env = os.environ.get("TOOLSET_TRACE_EVENTS", "").lower().strip()
    trace_events_enabled = trace_events_env in ("1", "true", "yes", "on")
    if trace_events_enabled:
        trace_events_budget_env = os.environ.get("TOOLSET_TRACE_EVENTS_BUDGET", "").strip()
        trace_events_budget = 10_000
        if trace_events_budget_env:
            try:
                trace_events_budget = int(trace_events_budget_env)
            except ValueError:
                RobustLogger().warning(
                    "Invalid TOOLSET_TRACE_EVENTS_BUDGET=%s; using default budget %s",
                    trace_events_budget_env,
                    trace_events_budget,
                )

        event_filter = VerboseEventTracer(logger=RobustLogger(), budget=trace_events_budget)
        app.installEventFilter(event_filter)
        RobustLogger().debug(
            "TRACE: Verbose event filter installed (TOOLSET_TRACE_EVENTS=1, budget=%s)",
            trace_events_budget,
        )
    else:
        RobustLogger().debug("TRACE: Event filter disabled (set TOOLSET_TRACE_EVENTS=1 to sample events)")
    
    RobustLogger().debug("TRACE: About to call app.exec()")
    exit_code = app.exec()
    RobustLogger().debug(f"TRACE: app.exec() returned with exit code: {exit_code}")
    sys.exit(exit_code)
