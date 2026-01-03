
from __future__ import annotations

import platform
import sys

from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Process, Queue
from typing import TYPE_CHECKING, Any

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication, QMessageBox

from toolset.config import CURRENT_VERSION, get_remote_toolset_update_info, is_remote_version_newer
from toolset.gui.dialogs.select_update import ProgressDialog, UpdateDialog, run_progress_dialog
from toolset.gui.widgets.settings.installations import GlobalSettings
from utility.error_handling import universal_simplify_exception
from utility.misc import ProcessorArchitecture
from utility.updater.update import AppUpdate

if TYPE_CHECKING:
    from concurrent.futures import Future

    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]


def fetch_update_info(
    useBetaChannel: bool = False,  # noqa: FBT001, FBT002
    silent: bool = False,  # noqa: FBT001, FBT002
) -> dict[str, Any] | Exception:
    return get_remote_toolset_update_info(use_beta_channel=useBetaChannel, silent=silent)


class UpdateManager:
    def __init__(self, *, silent: bool = False):
        self.settings: GlobalSettings = GlobalSettings()
        self.silent: bool = silent
        self.master_info: dict[str, Any] | Exception | None = None
        self.edge_info: dict[str, Any] | Exception | None = None

    def check_for_updates(
        self,
        *,
        silent: bool = False,
    ):
        RobustLogger().debug("TRACE: check_for_updates called")
        print("Checking for updates")
        RobustLogger().debug("TRACE: About to enter ProcessPoolExecutor context")
        with ProcessPoolExecutor() as executor:
            RobustLogger().debug("TRACE: Inside ProcessPoolExecutor context")
            if self.settings.useBetaChannel:
                print("Using beta channel")
                RobustLogger().debug("TRACE: Beta channel enabled, submitting edge_future")
                edge_future: Future[dict[str, Any] | Exception] = executor.submit(fetch_update_info, True, silent)
                print("Edge future submitted")
                RobustLogger().debug("TRACE: edge_future submitted")
            else:
                RobustLogger().debug("TRACE: Beta channel disabled, edge_future will be None")
                edge_future = None
            print("Using release channel")
            RobustLogger().debug("TRACE: Submitting master_future")
            master_future: Future[dict[str, Any] | Exception] = executor.submit(fetch_update_info, False, silent)
            print("Master future submitted")
            RobustLogger().debug("TRACE: master_future submitted")
            RobustLogger().debug("TRACE: About to exit ProcessPoolExecutor context (will wait for tasks)")

        RobustLogger().debug("TRACE: Exited ProcessPoolExecutor context")
        RobustLogger().debug("TRACE: Adding done callbacks to futures")
        master_future.add_done_callback(self.on_master_future_fetched)
        RobustLogger().debug("TRACE: master_future callback added")
        if edge_future is not None:
            edge_future.add_done_callback(self.on_edge_future_fetched)
            RobustLogger().debug("TRACE: edge_future callback added")
        else:
            RobustLogger().debug("TRACE: edge_future is None, skipping callback")
        RobustLogger().debug("TRACE: check_for_updates returning")

    def on_master_future_fetched(
        self,
        master_future: Future[dict[str, Any] | Exception],
    ):
        RobustLogger().debug("TRACE: on_master_future_fetched called")
        print("Master future fetched")
        RobustLogger().debug("TRACE: Getting master_future.result()")
        self.master_info = master_future.result()
        RobustLogger().debug("TRACE: master_future.result() completed, master_info set")
        if self.edge_info:
            RobustLogger().debug("TRACE: edge_info exists, calling _on_update_info_fetched")
            self._on_update_info_fetched()
        else:
            RobustLogger().debug("TRACE: edge_info not set yet, waiting for edge callback")
        RobustLogger().debug("TRACE: on_master_future_fetched returning")

    def on_edge_future_fetched(
        self,
        edge_future: Future[dict[str, Any] | Exception],
    ):
        RobustLogger().debug("TRACE: on_edge_future_fetched called")
        print("Edge future fetched")
        RobustLogger().debug("TRACE: Getting edge_future.result()")
        self.edge_info = edge_future.result()
        RobustLogger().debug("TRACE: edge_future.result() completed, edge_info set")
        if self.master_info:
            RobustLogger().debug("TRACE: master_info exists, calling _on_update_info_fetched")
            self._on_update_info_fetched()
        else:
            RobustLogger().debug("TRACE: master_info not set yet, waiting for master callback")
        RobustLogger().debug("TRACE: on_edge_future_fetched returning")

    def _on_update_info_fetched(self):
        print("Updating info fetched")
        if self.edge_info is None or self.master_info is None:
            RobustLogger().error("Edge and master info are None")
            return
        print("Master info is not None")
        if isinstance(self.master_info, Exception):
            RobustLogger().exception("Failed to fetch master update info")
            if not self.silent:
                etype, msg = universal_simplify_exception(self.master_info)
                QMessageBox(
                    QMessageBox.Icon.Information,
                    f"Unable to fetch latest version ({etype})",
                    f"Check if you are connected to the internet.\nError: {msg}",
                    QMessageBox.StandardButton.Ok,
                ).exec()
            return
        print("Edge info is not None")
        if isinstance(self.edge_info, Exception):
            print("Edge info is an exception")
            RobustLogger().exception("Failed to fetch edge update info")
            if not self.silent:
                etype, msg = universal_simplify_exception(self.edge_info)
                QMessageBox(
                    QMessageBox.Icon.Information,
                    f"Unable to fetch latest version ({etype})",
                    f"Check if you are connected to the internet.\nError: {msg}",
                    QMessageBox.StandardButton.Ok,
                ).exec()
            return
        remote_info, release_version_checked = self._determine_version_info(self.edge_info, self.master_info)
        print("Remote info: ", remote_info)
        greatest_available_version = remote_info["toolsetLatestVersion"] if release_version_checked else remote_info["toolsetLatestBetaVersion"]
        toolset_latest_notes = remote_info.get("toolsetLatestNotes", "") if release_version_checked else remote_info.get("toolsetBetaLatestNotes", "")
        toolset_download_link = remote_info["toolsetDownloadLink"] if release_version_checked else remote_info["toolsetBetaDownloadLink"]
        version_check = is_remote_version_newer(CURRENT_VERSION, greatest_available_version)
        print("Version check: ", version_check)
        cur_version_beta_release_str = ""
        if remote_info["toolsetLatestVersion"] == CURRENT_VERSION:
            cur_version_beta_release_str = "release "
        elif remote_info["toolsetLatestBetaVersion"] == CURRENT_VERSION:
            cur_version_beta_release_str = "beta "
        print("Current version beta release string: ", cur_version_beta_release_str)
        self._display_version_message(
            cur_version_beta_release_str,
            greatest_available_version,
            toolset_latest_notes,
            toolset_download_link,
            remote_info,
            is_up_to_date=version_check is False,
            release_version_checked=release_version_checked,
        )
        RobustLogger().debug("TRACE: Version message displayed - _on_update_info_fetched about to return")
        RobustLogger().debug("TRACE: _on_update_info_fetched returning")

    def _determine_version_info(
        self,
        edge_remote_info: dict[str, Any],
        master_remote_info: dict[str, Any],
    ) -> tuple[dict[str, Any], bool]:
        version_list: list[tuple[Literal["toolsetLatestVersion", "toolsetLatestBetaVersion"], Literal["master", "edge"], str]] = []
        print("Version list: ", version_list)
        if self.settings.useBetaChannel:
            version_list.append(("toolsetLatestVersion", "master", master_remote_info.get("toolsetLatestVersion", "")))
            version_list.append(("toolsetLatestVersion", "edge", edge_remote_info.get("toolsetLatestVersion", "")))
            version_list.append(("toolsetLatestBetaVersion", "master", master_remote_info.get("toolsetLatestBetaVersion", "")))
            version_list.append(("toolsetLatestBetaVersion", "edge", edge_remote_info.get("toolsetLatestBetaVersion", "")))
        else:
            version_list.append(("toolsetLatestVersion", "master", master_remote_info.get("toolsetLatestVersion", "")))

        version_list.sort(key=lambda x: bool(is_remote_version_newer("0.0.0", x[2])))

        release_version = version_list[0][0] == "toolsetLatestVersion"
        remote_info: dict[str, Any] = edge_remote_info if version_list[0][1] == "edge" else master_remote_info
        return remote_info, release_version

    def _display_version_message(  # noqa: PLR0913
        self,
        cur_version_str: str,
        greatest_version: str,
        notes: str,
        download_link: str,
        remote_info: dict[str, Any],
        *,
        is_up_to_date: bool,
        release_version_checked: bool,
    ):
        if is_up_to_date:
            if self.silent:
                return
            from toolset.gui.common.localization import translate as tr, trf
            up_to_date_msg_box = QMessageBox(
                QMessageBox.Icon.Information,
                tr("Version is up to date"),
                trf("You are running the latest {version_str}version ({version}).", version_str=cur_version_str, version=CURRENT_VERSION),
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Close,
                parent=None,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            )

            from toolset.gui.common.localization import translate as tr
            up_to_date_msg_box.button(QMessageBox.StandardButton.Ok).setText(tr("Auto-Update"))  # pyright: ignore[reportOptionalMemberAccess]
            up_to_date_msg_box.button(QMessageBox.StandardButton.Yes).setText(tr("Choose Update"))  # pyright: ignore[reportOptionalMemberAccess]
            result = up_to_date_msg_box.exec()

            if result == QMessageBox.StandardButton.Ok:
                self.autoupdate_toolset(greatest_version, remote_info, is_release=release_version_checked)
            elif result == QMessageBox.StandardButton.Yes:
                toolset_updater = UpdateDialog()
                toolset_updater.exec()
            return

        beta_string: Literal["release ", "beta "] = "release " if release_version_checked else "beta "
        from toolset.gui.common.localization import translate as tr, trf
        new_version_msg_box = QMessageBox(
            QMessageBox.Icon.Information,
            trf("Your toolset version {version} is outdated.", version=CURRENT_VERSION),
            trf("A new toolset {beta_str}version ({new_version}) is available for <a href='{link}'>download</a>.<br><br>{notes}", beta_str=beta_string, new_version=greatest_version, link=download_link, notes=notes),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Abort,
            parent=None,
            flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
        )

        new_version_msg_box.setDefaultButton(QMessageBox.StandardButton.Abort)
        from toolset.gui.common.localization import translate as tr
        new_version_msg_box.button(QMessageBox.StandardButton.Ok).setText(tr("Auto-Update"))  # pyright: ignore[reportOptionalMemberAccess]
        new_version_msg_box.button(QMessageBox.StandardButton.Yes).setText(tr("Details"))  # pyright: ignore[reportOptionalMemberAccess]
        new_version_msg_box.button(QMessageBox.StandardButton.Abort).setText(tr("Ignore"))  # pyright: ignore[reportOptionalMemberAccess]
        response = new_version_msg_box.exec()

        if response == QMessageBox.StandardButton.Ok:
            self.autoupdate_toolset(greatest_version, remote_info, is_release=release_version_checked)
        elif response == QMessageBox.StandardButton.Yes:
            toolset_updater = UpdateDialog()
            toolset_updater.exec()

    def autoupdate_toolset(
        self,
        latest_version: str,
        remote_info: dict[str, Any],
        *,
        is_release: bool,
    ):
        proc_arch = ProcessorArchitecture.from_os()
        assert proc_arch == ProcessorArchitecture.from_python()
        os_name = platform.system()

        links: list[str] = []

        is_release = False  # TODO(th3w1zard1): remove this line when the release version direct links are ready.
        if is_release:
            links = remote_info["toolsetDirectLinks"][os_name][proc_arch.value]
        else:
            links = remote_info["toolsetBetaDirectLinks"][os_name][proc_arch.value]

        progress_queue = Queue()
        progress_process = Process(target=run_progress_dialog, args=(progress_queue, "Holocron Toolset is updating and will restart shortly..."))
        progress_process.start()

        def download_progress_hook(
            data: dict[str, Any],
            progress_queue: Queue = progress_queue,
        ):
            progress_queue.put(data)

        progress_hooks = [download_progress_hook]

        def exitapp(kill_self_here: bool = True):  # noqa: FBT002, FBT001
            packaged_data = {"action": "shutdown", "data": {}}
            progress_queue.put(packaged_data)
            ProgressDialog.monitor_and_terminate(progress_process)
            if kill_self_here:
                sys.exit(0)

        updater = AppUpdate(links, "HolocronToolset", CURRENT_VERSION, latest_version, downloader=None, progress_hooks=progress_hooks, exithook=exitapp)

        try:
            progress_queue.put({"action": "update_status", "text": "Downloading update..."})
            updater.download(background=False)
            progress_queue.put({"action": "update_status", "text": "Restarting and Applying update..."})
            updater.extract_restart()
            progress_queue.put({"action": "update_status", "text": "Cleaning up..."})
            updater.cleanup()
        except Exception:  # noqa: BLE001
            RobustLogger().exception("Failed to complete the updater")
        finally:
            exitapp(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    update_manager = UpdateManager(silent=False)
    update_manager.check_for_updates()
    sys.exit(app.exec())
