from __future__ import annotations

import multiprocessing
import os
import sys

from multiprocessing import Queue
from typing import TYPE_CHECKING, Any, NoReturn

from loggerplus import RobustLogger
from qtpy.QtCore import QCoreApplication, QThread
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QApplication, QStyle

from toolset.config import LOCAL_PROGRAM_INFO, toolset_tag_to_version, version_to_toolset_tag
from toolset.gui.dialogs.asyncloader import ProgressDialog
from utility.system.app_process.shutdown import terminate_child_processes
from utility.updater.update import AppUpdate

if TYPE_CHECKING:
    from utility.updater.github import GithubRelease


def run_progress_dialog(
    progress_queue: Queue,
    title: str = "Operation Progress",
) -> NoReturn:
    """Call this with multiprocessing.Process."""
    app: QApplication = QApplication(sys.argv)
    dialog: ProgressDialog = ProgressDialog(progress_queue, title)
    app_style: QStyle | None = app.style()
    if app_style is None:
        raise RuntimeError("Failed to get QStyle for application")
    icon: QIcon | None = app_style.standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
    if icon is not None:
        dialog.setWindowIcon(QIcon(icon))
    dialog.show()
    sys.exit(app.exec())


def start_update_process(
    release: GithubRelease,
    download_url: str,
) -> None:
    """Start the update process with progress dialog.
    
    This function:
    1. Creates a separate process for the progress dialog
    2. Downloads the update
    3. Extracts and applies the update (which launches the updater script)
    4. Cleans up and exits the application
    """
    progress_queue: Queue = Queue()
    progress_process: multiprocessing.Process = multiprocessing.Process(
        target=run_progress_dialog,
        args=(
            progress_queue,
            "Holocron Toolset is updating and will restart shortly...",
        ),
    )
    progress_process.start()

    def download_progress_hook(
        data: dict[str, Any],
        progress_queue: Queue = progress_queue,
    ):
        progress_queue.put(data)

    def exitapp(kill_self_here: bool):  # noqa: FBT001
        """Clean exit hook for the update process.
        
        This function ensures proper cleanup of:
        1. The progress dialog process
        2. Child processes (texture loader, etc.)
        3. Qt threads
        4. The Qt application itself
        
        Args:
            kill_self_here: If True, forcefully exit after cleanup
        """
        log = RobustLogger()
        log.info("Update exit hook called (kill_self_here=%s)", kill_self_here)
        
        # 1. Signal the progress dialog to close
        try:
            packaged_data: dict[str, Any] = {"action": "shutdown", "data": {}}
            progress_queue.put(packaged_data)
        except Exception:
            log.debug("Could not send shutdown signal to progress dialog", exc_info=True)
        
        # 2. Wait for progress dialog process to terminate
        try:
            ProgressDialog.monitor_and_terminate(progress_process, timeout=3)
        except Exception:
            log.debug("Error terminating progress dialog process", exc_info=True)
        
        # 3. Terminate child processes (texture loaders, etc.)
        try:
            terminate_child_processes(timeout=2)
        except Exception:
            log.debug("Error terminating child processes", exc_info=True)
        
        # 4. Stop all running QThreads in the application
        _terminate_qt_threads(log)
        
        # 5. Quit the Qt application properly
        _quit_qt_application(log)
        
        if kill_self_here:
            log.info("Forcefully exiting application...")
            # Use os._exit to ensure we actually exit, bypassing any
            # cleanup handlers that might block
            os._exit(0)

    def expected_archive_filenames() -> list[str]:
        return [asset.name for asset in release.assets]

    updater = AppUpdate(
        [download_url],
        "HolocronToolset",
        LOCAL_PROGRAM_INFO["currentVersion"],
        toolset_tag_to_version(release.tag_name),
        downloader=None,
        progress_hooks=[download_progress_hook],
        exithook=exitapp,
        version_to_tag_parser=version_to_toolset_tag,
    )
    updater.get_archive_names = expected_archive_filenames

    try:
        progress_queue.put({"action": "update_status", "text": "Downloading update..."})
        updater.download(background=False)
        progress_queue.put({"action": "update_status", "text": "Restarting and Applying update..."})
        updater.extract_restart()
        progress_queue.put({"action": "update_status", "text": "Cleaning up..."})
        updater.cleanup()
    except Exception:  # noqa: BLE001
        RobustLogger().exception("Error occurred while downloading/installing the toolset.")
    finally:
        exitapp(kill_self_here=True)


def _terminate_qt_threads(log: RobustLogger):
    """Terminate all running QThreads in the current application.
    
    Uses QCoreApplication.instance() to get threads rather than gc.get_objects()
    for better reliability.
    """
    app = QCoreApplication.instance()
    if app is None:
        log.debug("No QApplication instance found")
        return
    
    # Find and terminate all QThread instances that are children of the app
    # or any top-level widget
    threads_terminated = 0
    
    try:
        # Get all QThread children of the application
        for child in app.findChildren(QThread):
            if child.isRunning():
                log.debug("Terminating QThread: %s", child.objectName() or type(child).__name__)
                try:
                    child.quit()
                    # Wait briefly for graceful termination
                    if not child.wait(1000):  # 1 second timeout
                        log.debug("QThread did not quit gracefully, terminating...")
                        child.terminate()
                        child.wait(500)
                    threads_terminated += 1
                except Exception:
                    log.debug("Error terminating QThread", exc_info=True)
    except Exception:
        log.debug("Error finding QThreads", exc_info=True)
    
    if threads_terminated > 0:
        log.debug("Terminated %d QThread(s)", threads_terminated)


def _quit_qt_application(log: RobustLogger):
    """Quit the Qt application and process any remaining events."""
    app = QCoreApplication.instance()
    if app is None:
        log.debug("No QApplication instance to quit")
        return
    
    try:
        # Process any pending events
        app.processEvents()
        
        # Close all top-level windows
        if isinstance(app, QApplication):
            for window in app.topLevelWidgets():
                try:
                    window.close()
                except Exception:
                    log.debug("Error closing window %s", window, exc_info=True)
        
        # Quit the application
        app.quit()
        
        # Process remaining events
        app.processEvents()
        
        log.debug("Qt application quit successfully")
    except Exception:
        log.debug("Error quitting Qt application", exc_info=True)
