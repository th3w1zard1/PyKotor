from __future__ import annotations

# Try to import defusedxml, fallback to ElementTree if not available
from xml.etree import ElementTree as ElemTree

try:  # sourcery skip: remove-redundant-exception, simplify-single-exception-tuple
    from defusedxml.ElementTree import fromstring as _fromstring

    ElemTree.fromstring = _fromstring
except (ImportError, ModuleNotFoundError):
    print("warning: defusedxml is not available but recommended for security")

import zipfile

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

import markdown

from loggerplus import RobustLogger
from qtpy import QtCore
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QMainWindow, QMessageBox, QTreeWidgetItem

from pykotor.tools.encoding import decode_bytes_with_fallbacks
from toolset.config import get_remote_toolset_update_info, is_remote_version_newer
from toolset.gui.dialogs.asyncloader import AsyncLoader
from toolset.gui.widgets.settings.installations import GlobalSettings
from utility.error_handling import universal_simplify_exception
from utility.system.os_helper import is_frozen
from utility.updater.github import download_github_file

if TYPE_CHECKING:
    import os

    from qtpy.QtGui import QShowEvent
    from qtpy.QtWidgets import QWidget


class HelpWindow(QMainWindow):
    ENABLE_UPDATES = True

    def __init__(self, parent: QWidget | None, startingPage: str | None = None):
        super().__init__(parent)

        self.version: str | None = None

        from toolset.uic.qtpy.windows import help as toolset_help

        self.ui = toolset_help.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_signals()
        self._setup_contents()
        self.starting_page: str | None = startingPage

        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter

        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

    def showEvent(self, a0: QShowEvent):
        super().showEvent(a0)
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
            tree = ElemTree.parse("./help/contents.xml")  # noqa: S314 incorrect warning.
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
        addItem: Callable[[QTreeWidgetItem], None] = (  # type: ignore[arg-type]
            self.ui.contentsTree.addTopLevelItem if parent is None else parent.addChild
        )

        structure = data.get("structure", {})
        for title in structure:
            item = QTreeWidgetItem([title])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, structure[title]["filename"])
            addItem(item)
            self._setup_contents_rec_json(item, structure[title])

    def _setup_contents_rec_xml(self, parent: QTreeWidgetItem | None, element: ElemTree.Element):
        addItem: Callable[[QTreeWidgetItem], None] = (  # type: ignore[arg-type]
            self.ui.contentsTree.addTopLevelItem if parent is None else parent.addChild
        )

        for child in element:
            item = QTreeWidgetItem([child.get("name", "")])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, child.get("file"))
            addItem(item)
            self._setup_contents_rec_xml(item, child)

    def check_for_updates(self):
        remoteInfo = get_remote_toolset_update_info(use_beta_channel=GlobalSettings().useBetaChannel)
        try:
            if not isinstance(remoteInfo, dict):
                raise remoteInfo  # noqa: TRY301

            new_version = str(remoteInfo["help"]["version"])
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
            error_msg = str(universal_simplify_exception(e)).replace("\n", "<br>")
            from toolset.gui.common.localization import translate as tr

            errMsgBox = QMessageBox(
                QMessageBox.Icon.Information,
                tr("An unexpected error occurred while parsing the help booklet."),
                error_msg,
                QMessageBox.StandardButton.Ok,
                parent=None,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            )
            errMsgBox.setWindowIcon(self.windowIcon())
            errMsgBox.exec()
        else:
            newHelpMsgBox = QMessageBox(
                QMessageBox.Icon.Information,
                title,
                text,
                parent=None,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            )
            newHelpMsgBox.setWindowIcon(self.windowIcon())
            newHelpMsgBox.addButton(QMessageBox.StandardButton.Yes)
            newHelpMsgBox.addButton(QMessageBox.StandardButton.No)
            user_response = newHelpMsgBox.exec()
            if user_response == QMessageBox.StandardButton.Yes:

                def task():
                    return self._download_update()

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
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 100%;
            margin: 0;
            padding: 24px;
            background-color: #ffffff;
        }}
        
        h1 {{
            font-size: 2em;
            font-weight: 600;
            margin-top: 0;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid #e1e4e8;
            color: #24292e;
        }}
        
        h2 {{
            font-size: 1.5em;
            font-weight: 600;
            margin-top: 32px;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid #e1e4e8;
            color: #24292e;
        }}
        
        h3 {{
            font-size: 1.25em;
            font-weight: 600;
            margin-top: 24px;
            margin-bottom: 12px;
            color: #24292e;
        }}
        
        h4, h5, h6 {{
            font-size: 1.1em;
            font-weight: 600;
            margin-top: 20px;
            margin-bottom: 10px;
            color: #24292e;
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
            background-color: #f6f8fa;
        }}
        
        table th {{
            font-weight: 600;
            text-align: left;
            padding: 12px 16px;
            border: 1px solid #d1d5da;
            background-color: #f6f8fa;
            color: #24292e;
        }}
        
        table td {{
            padding: 12px 16px;
            border: 1px solid #d1d5da;
            vertical-align: top;
        }}
        
        table tbody tr:nth-child(even) {{
            background-color: #f9fafb;
        }}
        
        table tbody tr:hover {{
            background-color: #f1f3f5;
        }}
        
        code {{
            font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', 'Menlo', 'Courier', monospace;
            font-size: 0.9em;
            padding: 2px 6px;
            background-color: #f6f8fa;
            border-radius: 3px;
            color: #e83e8c;
        }}
        
        pre {{
            font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', 'Menlo', 'Courier', monospace;
            font-size: 0.9em;
            padding: 16px;
            background-color: #f6f8fa;
            border-radius: 6px;
            overflow-x: auto;
            margin: 16px 0;
            border: 1px solid #e1e4e8;
        }}
        
        pre code {{
            padding: 0;
            background-color: transparent;
            color: #24292e;
            border-radius: 0;
        }}
        
        a {{
            color: #0366d6;
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
            border-top: 1px solid #e1e4e8;
        }}
        
        blockquote {{
            margin: 16px 0;
            padding: 0 16px;
            color: #6a737d;
            border-left: 4px solid #dfe2e5;
        }}
        
        strong {{
            font-weight: 600;
            color: #24292e;
        }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""

    def display_file(self, filepath: os.PathLike | str):
        filepath = Path(filepath)
        try:
            text: str = decode_bytes_with_fallbacks(filepath.read_bytes())
            if filepath.suffix.lower() == ".md":
                html_body: str = markdown.markdown(text, extensions=["tables", "fenced_code", "codehilite"])
                html: str = self._wrap_html_with_styles(html_body)
            else:
                html: str = text
            self.ui.textDisplay.setHtml(html)
        except OSError as e:
            from toolset.gui.common.localization import translate as tr, trf

            QMessageBox(
                QMessageBox.Icon.Critical,
                tr("Failed to open help file"),
                trf("Could not access '{filepath}'.\n{error}", filepath=str(filepath), error=str(universal_simplify_exception(e))),
            ).exec()

    def on_contents_clicked(self):
        if not self.ui.contentsTree.selectedItems():
            return
        item: QTreeWidgetItem = self.ui.contentsTree.selectedItems()[0]  # type: ignore[arg-type]
        filename = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if filename:
            help_path = Path("./help").resolve()
            file_path = Path(help_path, filename)
            self.ui.textDisplay.setSearchPaths([str(help_path), str(file_path.parent)])
            self.display_file(file_path)
