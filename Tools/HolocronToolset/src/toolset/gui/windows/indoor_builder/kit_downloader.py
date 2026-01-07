from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog, QFormLayout, QMessageBox, QPushButton, QWidget

from toolset.config import get_remote_toolset_update_info, is_remote_version_newer
from toolset.gui.common.filters import NoScrollEventFilter
from toolset.gui.dialogs.asyncloader import AsyncLoader
from toolset.gui.widgets.settings.installations import GlobalSettings
from utility.error_handling import format_exception_with_variables, universal_simplify_exception
from utility.misc import is_debug_mode
from utility.system.os_helper import is_frozen
from utility.updater.github import download_github_release_asset


class KitDownloader(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint & ~Qt.WindowType.WindowContextHelpButtonHint & ~Qt.WindowType.WindowMinMaxButtonsHint,
        )

        from toolset.uic.qtpy.dialogs.indoor_downloader import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self._no_scroll_filter: NoScrollEventFilter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        self.ui.downloadAllButton.clicked.connect(self._download_all_button_pressed)
        self._setup_downloads()

    def _setup_downloads(self):
        update_info_data: Exception | dict[str, Any] = get_remote_toolset_update_info(use_beta_channel=GlobalSettings().useBetaChannel)
        try:
            if not isinstance(update_info_data, dict):
                raise update_info_data  # type: ignore[reportUnnecessaryIsInstance]

            for kit_name, kit_dict in update_info_data["kits"].items():
                kit_id = kit_dict["id"]
                kit_path = Path(f"kits/{kit_id}.json")
                if kit_path.is_file():
                    button = QPushButton("Already Downloaded")
                    button.setEnabled(True)
                    local_kit_dict = None
                    try:
                        local_kit_dict = json.loads(kit_path.read_text())
                    except Exception as e:  # noqa: BLE001
                        print((e.__class__.__name__, str(e)), "\n in _setup_downloads for kit update check")
                        button.setText("Missing JSON - click to redownload.")
                        button.setEnabled(True)
                    else:
                        local_kit_version = str(local_kit_dict["version"])
                        retrieved_kit_version = str(kit_dict["version"])
                        if is_remote_version_newer(local_kit_version, retrieved_kit_version) is not False:
                            button.setText("Update Available")
                            button.setEnabled(True)
                else:
                    button = QPushButton("Download")
                button.clicked.connect(
                    lambda _=None, kit_dict=kit_dict, button=button: self._download_button_pressed(button, kit_dict),
                )

                layout: QFormLayout | None = self.ui.groupBox.layout()  # type: ignore[union-attr, assignment]  # pyright: ignore[reportAssignmentType]
                if layout is None:
                    msg = "Kit downloader group box layout is None"
                    raise RuntimeError(msg)  # noqa: TRY301
                layout.addRow(kit_name, button)
        except Exception as e:  # noqa: BLE001
            error_msg = str((e.__class__.__name__, str(e))).replace("\n", "<br>")
            err_msg_box = QMessageBox(
                QMessageBox.Icon.Information,
                "An unexpected error occurred while setting up the kit downloader.",
                error_msg,
                QMessageBox.StandardButton.Ok,
                parent=None,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            )
            err_msg_box.setWindowIcon(self.windowIcon())
            err_msg_box.exec()

    def _download_button_pressed(
        self,
        button: QPushButton,
        info_dict: dict[str, Any],
    ):
        button.setText("Downloading")
        button.setEnabled(False)

        def task() -> bool:
            try:
                return self._download_kit(info_dict["id"])
            except Exception as e:
                print(format_exception_with_variables(e))
                raise

        if is_debug_mode() and not is_frozen():
            try:
                task()
                button.setText("Download Complete")
            except Exception as e:  # noqa: BLE001
                print(format_exception_with_variables(e, message="Error downloading kit"))
                button.setText("Download Failed")
                button.setEnabled(True)
        else:
            loader = AsyncLoader(self, "Downloading Kit...", task, "Failed to download.")
            if loader.exec():
                button.setText("Download Complete")
            else:
                button.setText("Download Failed")
                button.setEnabled(True)

    def _download_all_kits(self) -> bool:
        kits_path = Path("kits").resolve()
        kits_path.mkdir(parents=True, exist_ok=True)
        kits_zip_path = Path("kits.zip")

        update_info_data: Exception | dict[str, Any] = get_remote_toolset_update_info(use_beta_channel=GlobalSettings().useBetaChannel)

        if isinstance(update_info_data, Exception):
            print(f"Failed to get update info: {update_info_data}")
            return False

        kits_config = update_info_data.get("kits", {})
        repository: str = kits_config.get("repository", "th3w1zard1/ToolsetData")
        release_tag: str = kits_config.get("release_tag", "latest")

        try:
            owner, repo = repository.split("/")
            print(f"Downloading kits.zip from {repository} release {release_tag}...")
            download_github_release_asset(
                owner=owner,
                repo=repo,
                tag_name=release_tag,
                asset_name="kits.zip",
                local_path=kits_zip_path,
            )
        except Exception as e:
            print(format_exception_with_variables(e, message="Failed to download kits.zip"))
            return False

        try:
            with zipfile.ZipFile(kits_zip_path) as zip_file:
                print(f"Extracting all kits to {kits_path}")
                with TemporaryDirectory() as tmp_dir:
                    tempdir_path = Path(tmp_dir)
                    zip_file.extractall(tmp_dir)

                    for item in tempdir_path.iterdir():
                        if item.is_dir():
                            dst_path = kits_path / item.name
                            if dst_path.is_dir():
                                print(f"Removing old {item.name} kit...")
                                shutil.rmtree(dst_path)
                            print(f"Copying {item.name} kit...")
                            shutil.copytree(item, dst_path)
                        elif item.suffix.lower() == ".json" and item.stem != "available_kits":
                            dst_file = kits_path / item.name
                            print(f"Copying {item.name}...")
                            shutil.copy(item, dst_file)
        except Exception as e:
            print(format_exception_with_variables(e, message="Failed to extract kits"))
            return False
        finally:
            if kits_zip_path.exists() and kits_zip_path.is_file():
                kits_zip_path.unlink()

        return True

    def _download_all_button_pressed(self):
        self.ui.downloadAllButton.setText("Downloading All...")
        self.ui.downloadAllButton.setEnabled(False)

        def task() -> bool:
            try:
                return self._download_all_kits()
            except Exception as e:
                print(format_exception_with_variables(e))
                raise

        if is_debug_mode() and not is_frozen():
            try:
                task()
                self.ui.downloadAllButton.setText("Download All Complete")
                self._refresh_kit_buttons()
            except Exception as e:  # noqa: BLE001
                print(format_exception_with_variables(e, message="Error downloading all kits"))
                self.ui.downloadAllButton.setText("Download All Failed")
                self.ui.downloadAllButton.setEnabled(True)
        else:
            loader = AsyncLoader(self, "Downloading All Kits...", task, "Failed to download all kits.")
            if loader.exec():
                self.ui.downloadAllButton.setText("Download All Complete")
                self._refresh_kit_buttons()
            else:
                self.ui.downloadAllButton.setText("Download All Failed")
                self.ui.downloadAllButton.setEnabled(True)

    def _refresh_kit_buttons(self):
        layout: QFormLayout | None = self.ui.groupBox.layout()  # type: ignore[assignment]  # pyright: ignore[reportAssignmentType]
        if layout is None:
            return

        for i in range(layout.rowCount()):
            item = layout.itemAt(i, QFormLayout.ItemRole.FieldRole)
            if item and isinstance(item.widget(), QPushButton):
                button: QPushButton = cast(QPushButton, item.widget())
                button.setText("Already Downloaded")
                button.setEnabled(False)

    def _download_kit(self, kit_id: str) -> bool:
        kits_path: Path = Path("kits").resolve()
        kits_path.mkdir(parents=True, exist_ok=True)
        kits_zip_path: Path = Path("kits.zip")

        update_info_data: Exception | dict[str, Any] = get_remote_toolset_update_info(use_beta_channel=GlobalSettings().useBetaChannel)

        if isinstance(update_info_data, Exception):
            print(f"Failed to get update info: {update_info_data}")
            return False

        kits_config: dict[str, Any] = update_info_data.get("kits", {})
        repository: str = kits_config.get("repository", "th3w1zard1/ToolsetData")
        release_tag: str = kits_config.get("release_tag", "latest")

        try:
            owner, repo = repository.split("/")
            print(f"Downloading kits.zip from {repository} release {release_tag}...")
            download_github_release_asset(
                owner=owner,
                repo=repo,
                tag_name=release_tag,
                asset_name="kits.zip",
                local_path=kits_zip_path,
            )
        except Exception as e:
            print(format_exception_with_variables(e, message="Failed to download kits.zip"))
            return False

        try:
            with zipfile.ZipFile(kits_zip_path) as zip_file:
                print(f"Extracting {kit_id} kit to {kits_path}")
                with TemporaryDirectory() as tmp_dir:
                    tempdir_path = Path(tmp_dir)
                    zip_file.extractall(tmp_dir)
                    src_path = tempdir_path / kit_id
                    this_kit_dst_path = kits_path / kit_id

                    if not src_path.exists():
                        msg = f"Kit '{kit_id}' not found in kits.zip"
                        print(msg)
                        return False

                    print(f"Copying '{src_path}' to '{this_kit_dst_path}'...")
                    if this_kit_dst_path.is_dir():
                        print(f"Deleting old {kit_id} kit folder/files...")
                        shutil.rmtree(this_kit_dst_path)
                    shutil.copytree(src_path, str(this_kit_dst_path))

                    this_kit_json_filename = f"{kit_id}.json"
                    src_kit_json_path = tempdir_path / this_kit_json_filename
                    if not src_kit_json_path.is_file():
                        msg = f"Kit '{kit_id}' is missing the '{this_kit_json_filename}' file, cannot complete download"
                        print(msg)
                        return False
                    shutil.copy(src_kit_json_path, kits_path / this_kit_json_filename)
        except Exception as e:
            print(format_exception_with_variables(e, message=f"Failed to extract kit {kit_id}"))
            return False
        finally:
            if kits_zip_path.exists() and kits_zip_path.is_file():
                kits_zip_path.unlink()

        return True

