from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5 import QtCore
from PyQt5.QtWidgets import QDialog, QFileDialog, QListWidgetItem

from pykotor.common.module import Module
from utility.system.path import Path

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget

    from toolset.data.installation import HTInstallation


class SelectModuleDialog(QDialog):
    def __init__(self, parent: QWidget, installation: HTInstallation):
        """Initializes the dialog to select a module.

        Args:
            parent (QWidget): Parent widget
            installation (HTInstallation): HT installation object

        Processing Logic:
        ----------------
            - Initializes the UI from the dialog design
            - Connects button click signals to methods
            - Builds the initial module list
            - Sets up filtering of module list.
        """
        super().__init__(parent)

        self._installation: HTInstallation = installation

        self.module_root: str = ""
        self.module_filename: str = ""
        self.module_filepath: str = ""

        from toolset.uic.dialogs.select_module import Ui_Dialog  # pylint: disable=C0415  # noqa: PLC0415

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.openButton.clicked.connect(self.confirm)
        self.ui.cancelButton.clicked.connect(self.reject)
        self.ui.browseButton.clicked.connect(self.browse)
        self.ui.moduleList.currentRowChanged.connect(self.onRowChanged)
        self.ui.filterEdit.textEdited.connect(self.onFilterEdited)

        self._buildModuleList()

    def _buildModuleList(self):
        """Builds a list of installed modules.

        Args:
        ----
            self: The class instance
        """
        moduleNames = self._installation.module_names()
        listedModules: set[str] = set()

        for module in self._installation.modules_list():
            root = Module.get_root(module)

            if root in listedModules:
                continue
            listedModules.add(root)

            item = QListWidgetItem(f"{moduleNames[module]}  [{root}]")
            item.setData(QtCore.Qt.UserRole, root)
            item.setData(QtCore.Qt.UserRole + 1, module)
            item.setData(QtCore.Qt.UserRole + 2, str(self._installation.module_path() / module))
            self.ui.moduleList.addItem(item)

    def browse(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select module to open",
            str(self._installation.module_path()),
            "Module File (*.mod *.rim *.erf)",
        )

        if filepath:
            self.module_root = Module.get_root(filepath)
            self.module_filename = Path(filepath).name
            self.module_filepath = filepath
            self.accept()

    def confirm(self):
        """Confirms the selected module.

        Args:
        ----
            self: The object instance
        """
        self.module_root = self.ui.moduleList.currentItem().data(QtCore.Qt.UserRole)
        self.module_filename = self.ui.moduleList.currentItem().data(QtCore.Qt.UserRole + 1)
        self.module_filepath = self.ui.moduleList.currentItem().data(QtCore.Qt.UserRole + 2)
        self.accept()

    def onRowChanged(self):
        self.ui.openButton.setEnabled(self.ui.moduleList.currentItem() is not None)

    def onFilterEdited(self):
        """Filter modules based on filter text.

        Args:
        ----
            self: The class instance
        """
        text = self.ui.filterEdit.text()
        for row in range(self.ui.moduleList.count()):
            item = self.ui.moduleList.item(row)
            item.setHidden(text.lower() not in item.text().lower())
