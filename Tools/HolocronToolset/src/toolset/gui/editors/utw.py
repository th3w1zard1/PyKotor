from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

import qtpy

from pykotor.common.language import LocalizedString
from pykotor.common.misc import ResRef
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.utw import UTW, dismantle_utw, read_utw
from pykotor.resource.type import ResourceType
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QWidget

    from toolset.data.installation import HTInstallation


class UTWEditor(Editor):
    def __init__(self, parent: QWidget | None, installation: HTInstallation | None = None):
        """Initialize Waypoint Editor window.

        Args:
        ----
            parent: {Parent widget}
            installation: {Installation object}.

        Processing Logic:
        ----------------
            - Initialize UI elements from designer file
            - Set up menu bar and signal connections
            - Load installation data if provided
            - Initialize UTW object
            - Create new empty waypoint by default.
        """
        supported: list[ResourceType] = [ResourceType.UTW]
        super().__init__(parent, "Waypoint Editor", "waypoint", supported, supported, installation)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.editors.utw import (
                Ui_MainWindow,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.editors.utw import (
                Ui_MainWindow,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.editors.utw import (
                Ui_MainWindow,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.editors.utw import (
                Ui_MainWindow,  # noqa: PLC0415  # pylint: disable=C0415
            )
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        if installation is not None:  # will only be none in the unittests
            self._setupInstallation(installation)

        self._utw = UTW()

        self.new()

    def _setupSignals(self):
        self.ui.tagGenerateButton.clicked.connect(self.generateTag)
        self.ui.resrefGenerateButton.clicked.connect(self.generateResref)
        self.ui.noteChangeButton.clicked.connect(self.changeNote)

    def _setupInstallation(self, installation: HTInstallation):
        self._installation = installation
        self.ui.nameEdit.setInstallation(installation)

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes):
        super().load(filepath, resref, restype, data)

        utw = read_utw(data)
        self._loadUTW(utw)

    def _loadUTW(self, utw: UTW):
        """Load UTW data into UI elements.

        Args:
        ----
            utw (UTW): UTW object to load data from

        Processing Logic:
        ----------------
            - Load basic UTW data like name, tag and resref into line edits
            - Load advanced data like map note flags and text into checkboxes and line edit
            - Load comment text into plain text edit
            - No return, simply loads UI elements from UTW object.
        """
        self._utw = utw

        # Basic
        self.ui.nameEdit.setLocstring(utw.name)
        self.ui.tagEdit.setText(utw.tag)
        self.ui.resrefEdit.setText(str(utw.resref))

        # Advanced
        self.ui.isNoteCheckbox.setChecked(utw.has_map_note)
        self.ui.noteEnabledCheckbox.setChecked(utw.map_note_enabled)
        self._loadLocstring(self.ui.noteEdit, utw.map_note)  # pyright: ignore[reportArgumentType]

        # Comments
        self.ui.commentsEdit.setPlainText(utw.comment)

    def build(self) -> tuple[bytes, bytes]:
        """Builds a UTW object from UI controls.

        Args:
        ----
            self: The UI object containing controls.

        Returns:
        -------
            data: The serialized UTWSave object as bytes.
            b"": An empty bytes object.

        Processing Logic:
        ----------------
            - Populate UTW object from UI control values
            - Serialize UTW to bytes using GFF format
            - Return bytes and empty bytes
        """
        utw: UTW = deepcopy(self._utw)

        utw.name = self.ui.nameEdit.locstring()
        utw.tag = self.ui.tagEdit.text()
        utw.resref = ResRef(self.ui.resrefEdit.text())
        utw.has_map_note = self.ui.isNoteCheckbox.isChecked()
        utw.map_note_enabled = self.ui.noteEnabledCheckbox.isChecked()
        try:
            utw.map_note = self.ui.noteEdit.locstring  # FIXME:
        except AttributeError:
            utw.map_note = LocalizedString(self.ui.noteEdit.text())  # ALSO FIXME:
        utw.comment = self.ui.commentsEdit.toPlainText()

        data = bytearray()
        gff = dismantle_utw(utw)
        write_gff(gff, data)

        return data, b""

    def new(self):
        super().new()
        self._loadUTW(UTW())

    def changeName(self):
        assert self._installation is not None
        dialog = LocalizedStringDialog(self, self._installation, self.ui.nameEdit.locstring())
        if dialog.exec_():
            self._loadLocstring(self.ui.nameEdit.ui.locstringText, dialog.locstring)  # pyright: ignore[reportArgumentType]

    def changeNote(self):
        assert self._installation is not None
        try:
            dialog = LocalizedStringDialog(self, self._installation, self.ui.noteEdit.locstring)  # pyright: ignore[reportArgumentType]
        except AttributeError:
            dialog = LocalizedStringDialog(self, self._installation, self.ui.noteEdit.text())  # pyright: ignore[reportArgumentType]
        if dialog.exec_():
            self._loadLocstring(self.ui.noteEdit, dialog.locstring)  # pyright: ignore[reportArgumentType]

    def generateTag(self):
        if not self.ui.resrefEdit.text():
            self.generateResref()
        self.ui.tagEdit.setText(self.ui.resrefEdit.text())

    def generateResref(self):
        if self._resname:
            self.ui.resrefEdit.setText(self._resname)
        else:
            self.ui.resrefEdit.setText("m00xx_way_000")
