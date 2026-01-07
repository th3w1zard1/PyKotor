from __future__ import annotations

# Try to import defusedxml, fallback to ElementTree if not available
from xml.etree import ElementTree as ET

try:  # sourcery skip: remove-redundant-exception, simplify-single-exception-tuple
    from defusedxml.ElementTree import fromstring as _fromstring

    ET.fromstring = _fromstring
except (ImportError, ModuleNotFoundError):
    print("warning: defusedxml is not available but recommended for security")

import zipfile

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, ClassVar

import markdown

from qtpy import QtCore
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QMainWindow, QMessageBox, QTreeWidgetItem

from loggerplus import RobustLogger
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from toolset.config import get_remote_toolset_update_info, is_remote_version_newer
from toolset.gui.dialogs.asyncloader import AsyncLoader
from toolset.gui.widgets.settings.installations import GlobalSettings
from utility.system.os_helper import is_frozen
from utility.updater.github import download_github_file

if TYPE_CHECKING:
    import os

    from qtpy.QtGui import QShowEvent
    from qtpy.QtWidgets import QWidget


class HelpWindow(QMainWindow):
    ENABLE_UPDATES: ClassVar[bool] = True

    def __init__(
        self,
        parent: QWidget | None,
        startingPage: str | None = None,
    ):
        super().__init__(parent)

        from toolset.uic.qtpy.windows import help as toolset_help

        self.version: str | None = None
        self.ui: toolset_help.Ui_MainWindow = toolset_help.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_signals()
        self._setup_contents()
        self.starting_page: str | None = startingPage

        # Setup event filter to prevent scroll wheel interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter

        self._no_scroll_filter: NoScrollEventFilter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

    def showEvent(self, event: QShowEvent):  # pyright: ignore[reportIncompatibleMethodOverride]  # type: ignore[override]
        super().showEvent(event)
        self.ui.textDisplay.setSearchPaths(["./help"])

        if self.ENABLE_UPDATES:
            self.check_for_updates()

        if self.starting_page is None:
            return
        self.display_file(self.starting_page)

    def _setup_signals(self):
        self.ui.contentsTree.clicked.connect(self.on_contents_clicked)

    def _setup_contents(self):
        self.ui.contentsTree.clear()

        try:
            tree = ET.parse("./help/contents.xml")  # noqa: S314 incorrect warning.
            root = tree.getroot()

            self.version = str(root.get("version", "0.0"))
            self._setup_contents_rec_xml(None, root)

            # Old JSON code:
            # text = Path("./help/contents.xml").read_text()
            # data = json.loads(text)
            # self.version = data["version"]
            # self._setupContentsRecJSON(None, data)
        except Exception:  # noqa: BLE001
            RobustLogger().debug("Suppressed error in HelpWindow._setupContents", exc_info=True)

    def _setup_contents_rec_json(self, parent: QTreeWidgetItem | None, data: dict[str, Any]):
        add_item: Callable[[QTreeWidgetItem], None] = (  # type: ignore[arg-type]
            self.ui.contentsTree.addTopLevelItem if parent is None else parent.addChild
        )

        structure: dict[str, Any] = data.get("structure", {})
        for title in structure:
            item = QTreeWidgetItem([title])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, structure[title]["filename"])
            add_item(item)
            self._setup_contents_rec_json(item, structure[title])

    def _setup_contents_rec_xml(
        self,
        parent: QTreeWidgetItem | None,
        element: ET.Element,
    ):
        add_item: Callable[[QTreeWidgetItem], None] = (  # type: ignore[arg-type]
            self.ui.contentsTree.addTopLevelItem if parent is None else parent.addChild
        )

        for child in element:
            item = QTreeWidgetItem([child.get("name", "")])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, child.get("file"))
            add_item(item)
            self._setup_contents_rec_xml(item, child)

    def check_for_updates(self):
        remote_info: dict[str, Any] | Exception = get_remote_toolset_update_info(use_beta_channel=GlobalSettings().useBetaChannel)
        try:
            if not isinstance(remote_info, dict):
                raise remote_info

            new_version = str(remote_info["help"]["version"])
            if self.version is None:
                title = "Help book missing"
                text = "You do not seem to have a valid help booklet downloaded, would you like to download it?"
            elif is_remote_version_newer(self.version, new_version):
                title = "Update available"
                text = "A newer version of the help book is available for download, would you like to download it?"
            else:
                RobustLogger().debug("No help booklet updates available, using version %s (latest version: %s)", self.version, new_version)
                return
        except Exception as e:  # noqa: BLE001
            error_msg = str((e.__class__.__name__, str(e))).replace("\n", "<br>")
            from toolset.gui.common.localization import translate as tr

            err_msg_box = QMessageBox(
                QMessageBox.Icon.Information,
                tr("An unexpected error occurred while parsing the help booklet."),
                error_msg,
                QMessageBox.StandardButton.Ok,
                parent=None,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            )
            err_msg_box.setWindowIcon(self.windowIcon())
            err_msg_box.exec()
        else:
            new_help_msg_box = QMessageBox(
                QMessageBox.Icon.Information,
                title,
                text,
                parent=None,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            )
            new_help_msg_box.setWindowIcon(self.windowIcon())
            new_help_msg_box.addButton(QMessageBox.StandardButton.Yes)
            new_help_msg_box.addButton(QMessageBox.StandardButton.No)
            user_response = new_help_msg_box.exec()
            if user_response == QMessageBox.StandardButton.Yes:

                def task():
                    self._download_update()

                loader = AsyncLoader(self, "Download newer help files...", task, "Failed to update.")
                if loader.exec():
                    self._setup_contents()

    def _download_update(self):
        help_path = Path("./help").resolve()
        help_path.mkdir(parents=True, exist_ok=True)
        help_zip_path = Path("./help.zip").resolve()
        download_github_file("th3w1zard1/PyKotor", help_zip_path, "/Tools/HolocronToolset/downloads/help.zip")

        # Extract the ZIP file
        with zipfile.ZipFile(help_zip_path) as zip_file:
            RobustLogger().info("Extracting downloaded content to %s", help_path)
            zip_file.extractall(help_path)

        if is_frozen():
            help_zip_path.unlink()

    def _wrap_html_with_styles(self, html_body: str) -> str:
        """Wrap HTML body with modern CSS styling for better readability."""
        from qtpy.QtGui import QColor, QPalette

        pal = self.palette()
        fg = pal.color(QPalette.ColorRole.WindowText)
        bg = pal.color(QPalette.ColorRole.Window)
        base = pal.color(QPalette.ColorRole.Base)
        alt_base = pal.color(QPalette.ColorRole.AlternateBase)
        border = pal.color(QPalette.ColorRole.Mid)
        highlight = pal.color(QPalette.ColorRole.Highlight)
        link = pal.color(QPalette.ColorRole.Link)

        muted_fg = QColor(fg)
        muted_fg.setAlpha(190)
        muted_css = f"rgba({muted_fg.red()}, {muted_fg.green()}, {muted_fg.blue()}, {muted_fg.alpha() / 255.0:.3f})"

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
            line-height: 1.6;
            color: {fg.name()};
            max-width: 100%;
            margin: 0;
            padding: 24px;
            background-color: {bg.name()};
        }}
        
        h1 {{
            font-size: 2em;
            font-weight: 600;
            margin-top: 0;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid {border.name()};
            color: {fg.name()};
        }}
        
        h2 {{
            font-size: 1.5em;
            font-weight: 600;
            margin-top: 32px;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid {border.name()};
            color: {fg.name()};
        }}
        
        h3 {{
            font-size: 1.25em;
            font-weight: 600;
            margin-top: 24px;
            margin-bottom: 12px;
            color: {fg.name()};
        }}
        
        h4, h5, h6 {{
            font-size: 1.1em;
            font-weight: 600;
            margin-top: 20px;
            margin-bottom: 10px;
            color: {fg.name()};
        }}
        
        p {{
            margin-top: 0;
            margin-bottom: 16px;
        }}
        
        ul, ol {{
            margin-top: 0;
            margin-bottom: 16px;
            padding-left: 32px;
        }}
        
        li {{
            margin-bottom: 8px;
        }}
        
        li > p {{
            margin-bottom: 8px;
        }}
        
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 24px 0;
            display: block;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }}
        
        table thead {{
            background-color: {alt_base.name()};
        }}
        
        table th {{
            font-weight: 600;
            text-align: left;
            padding: 12px 16px;
            border: 1px solid {border.name()};
            background-color: {alt_base.name()};
            color: {fg.name()};
        }}
        
        table td {{
            padding: 12px 16px;
            border: 1px solid {border.name()};
            vertical-align: top;
        }}
        
        table tbody tr:nth-child(even) {{
            background-color: {alt_base.name()};
        }}
        
        table tbody tr:hover {{
            background-color: {base.name()};
        }}
        
        code {{
            font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', 'Menlo', 'Courier', monospace;
            font-size: 0.9em;
            padding: 2px 6px;
            background-color: {alt_base.name()};
            border-radius: 3px;
            color: {highlight.name()};
        }}
        
        pre {{
            font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', 'Menlo', 'Courier', monospace;
            font-size: 0.9em;
            padding: 16px;
            background-color: {alt_base.name()};
            border-radius: 6px;
            overflow-x: auto;
            margin: 16px 0;
            border: 1px solid {border.name()};
        }}
        
        pre code {{
            padding: 0;
            background-color: transparent;
            color: {fg.name()};
            border-radius: 0;
        }}
        
        a {{
            color: {link.name()};
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        hr {{
            height: 0;
            margin: 24px 0;
            background: transparent;
            border: 0;
            border-top: 1px solid {border.name()};
        }}
        
        blockquote {{
            margin: 16px 0;
            padding: 0 16px;
            color: {muted_css};
            border-left: 4px solid {border.name()};
        }}
        
        strong {{
            font-weight: 600;
            color: {fg.name()};
        }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""

    def display_file(
        self,
        filepath: os.PathLike | str,
    ):
        filepath = Path(filepath)
        try:
            text: str = decode_bytes_with_fallbacks(filepath.read_bytes())
            if filepath.suffix.lower() == ".md":
                html_body: str = markdown.markdown(text, extensions=["tables", "fenced_code", "codehilite"])
                html: str = self._wrap_html_with_styles(html_body)
            else:
                html = text
            self.ui.textDisplay.setHtml(html)
        except OSError as e:
            from toolset.gui.common.localization import translate as tr, trf

            msg_box = QMessageBox(
                QMessageBox.Icon.Critical,
                tr("Failed to open help file"),
                trf("Could not access '{filepath}'.\n{error}", filepath=str(filepath), error=str((e.__class__.__name__, str(e)))),
            )
            msg_box.setWindowIcon(self.windowIcon())
            msg_box.exec()

    def on_contents_clicked(self):
        selected_items = self.ui.contentsTree.selectedItems()
        if not selected_items:
            return
        item: QTreeWidgetItem = selected_items[0]  # type: ignore[arg-type]
        filename: str = str(item.data(0, QtCore.Qt.ItemDataRole.UserRole) or "").strip()
        if filename:
            help_path = Path("./help").resolve()
            file_path = Path(help_path, str(filename))
            self.ui.textDisplay.setSearchPaths([str(help_path), str(file_path.parent)])
            self.display_file(str(file_path))
