from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from qtpy.QtCore import QPoint
from qtpy.QtGui import QCloseEvent
from qtpy.QtWidgets import QFileDialog, QMenu, QMessageBox, QShortcut, QStyle

from pykotor.extract.talktable import TalkTable
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.ssf import SSF, SSFSound, read_ssf, write_ssf
from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QLineEdit, QSpinBox, QToolButton, QWidget

    from pykotor.extract.talktable import StringResult
    from toolset.data.installation import HTInstallation


try:  # QUndoStack location differs between Qt5/Qt6 bindings
    from qtpy.QtWidgets import QUndoCommand, QUndoStack  # type: ignore[assignment]
except Exception:  # noqa: BLE001
    from qtpy.QtGui import QUndoCommand, QUndoStack  # type: ignore[assignment]


@dataclass(frozen=True)
class _SSFRow:
    label: str
    spin: QSpinBox
    sound_edit: QLineEdit
    text_edit: QLineEdit
    play_button: QToolButton
    more_button: QToolButton


class _SpinValueCommand(QUndoCommand):
    def __init__(
        self,
        editor: "SSFEditor",
        *,
        row_label: str,
        spin: QSpinBox,
        old_value: int,
        new_value: int,
    ):
        super().__init__(f"Set {row_label} StringRef")
        self._editor = editor
        self._spin = spin
        self._old_value = old_value
        self._new_value = new_value

    def undo(self):  # noqa: D401
        self._editor._apply_spin_value(self._spin, self._old_value)  # noqa: SLF001

    def redo(self):  # noqa: D401
        self._editor._apply_spin_value(self._spin, self._new_value)  # noqa: SLF001


class SSFEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation | None = None,
    ):
        """Initialize Soundset Editor window.

        Args:
        ----
            parent: {Parent widget}
            installation: {Installation object}.

        Processing Logic:
        ----------------
            - Call super().__init__ to initialize base editor
            - Get talktable from installation if provided
            - Import and setup UI
            - Setup menus and signals
            - Call new() to start with empty soundset
        """
        supported: list[ResourceType] = [ResourceType.SSF]
        super().__init__(parent, "Soundset Editor", "soundset", supported, supported, installation)

        self._talktable: TalkTable | None = installation.talktable() if installation else None
        self._undo_stack: QUndoStack = QUndoStack(self)
        self._clean_undo_index: int = self._undo_stack.index()
        self._suppress_undo_push: bool = False
        self._last_spin_values: dict[QSpinBox, int] = {}
        self._rows: list[_SSFRow] = []
        
        # Setup event filter to prevent scroll wheel interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        from toolset.uic.qtpy.editors.ssf import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()
        self._add_help_action()
        self._setup_signals()
        self._setup_sound_rows()

        self.new()
        self.setMinimumSize(577, 437)

    def _setup_signals(self):
        """Connects signals to update text boxes.

        Args:
        ----
            self: The class instance.

        Processing Logic:
        ----------------
            - Connects valueChanged signals from spin boxes to updateTextBoxes method
            - Connects triggered signal from actionSetTLK to selectTalkTable method
        """
        self.ui.actionSetTLK.triggered.connect(self.select_talk_table)
        self._undo_stack.indexChanged.connect(self._on_undo_index_changed)
        QShortcut("Ctrl+Z", self).activated.connect(self._undo_stack.undo)
        QShortcut("Ctrl+Y", self).activated.connect(self._undo_stack.redo)
        QShortcut("Ctrl+Shift+Z", self).activated.connect(self._undo_stack.redo)

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        """Loads sound data from an SSF file.

        Args:
        ----
            filepath: {PathLike or string}: Path to SSF file
            resref: {string}: Resource reference
            restype: {ResourceType}: Resource type
            data: {bytes}: SSF data

        Loads sound data from an SSF file and sets values of UI spin boxes:
            - Reads SSF data from file
            - Sets values of spin boxes for different sound events like battlecries, attacks, abilities etc
            - Populates UI with sound data from file.
        """
        super().load(filepath, resref, restype, data)
        ssf: SSF = read_ssf(data)

        self._suppress_undo_push = True
        self.ui.battlecry1StrrefSpin.setValue(ssf.get(SSFSound.BATTLE_CRY_1) or 0)
        self.ui.battlecry2StrrefSpin.setValue(ssf.get(SSFSound.BATTLE_CRY_2) or 0)
        self.ui.battlecry3StrrefSpin.setValue(ssf.get(SSFSound.BATTLE_CRY_3) or 0)
        self.ui.battlecry4StrrefSpin.setValue(ssf.get(SSFSound.BATTLE_CRY_4) or 0)
        self.ui.battlecry5StrrefSpin.setValue(ssf.get(SSFSound.BATTLE_CRY_5) or 0)
        self.ui.battlecry6StrrefSpin.setValue(ssf.get(SSFSound.BATTLE_CRY_6) or 0)
        self.ui.select1StrrefSpin.setValue(ssf.get(SSFSound.SELECT_1) or 0)
        self.ui.select2StrrefSpin.setValue(ssf.get(SSFSound.SELECT_2) or 0)
        self.ui.select3StrrefSpin.setValue(ssf.get(SSFSound.SELECT_3) or 0)
        self.ui.attack1StrrefSpin.setValue(ssf.get(SSFSound.ATTACK_GRUNT_1) or 0)
        self.ui.attack2StrrefSpin.setValue(ssf.get(SSFSound.ATTACK_GRUNT_2) or 0)
        self.ui.attack3StrrefSpin.setValue(ssf.get(SSFSound.ATTACK_GRUNT_3) or 0)
        self.ui.pain1StrrefSpin.setValue(ssf.get(SSFSound.PAIN_GRUNT_1) or 0)
        self.ui.pain2StrrefSpin.setValue(ssf.get(SSFSound.PAIN_GRUNT_2) or 0)
        self.ui.lowHpStrrefSpin.setValue(ssf.get(SSFSound.LOW_HEALTH) or 0)
        self.ui.deadStrrefSpin.setValue(ssf.get(SSFSound.DEAD) or 0)
        self.ui.criticalStrrefSpin.setValue(ssf.get(SSFSound.CRITICAL_HIT) or 0)
        self.ui.immuneStrrefSpin.setValue(ssf.get(SSFSound.TARGET_IMMUNE) or 0)
        self.ui.layMineStrrefSpin.setValue(ssf.get(SSFSound.LAY_MINE) or 0)
        self.ui.disarmMineStrrefSpin.setValue(ssf.get(SSFSound.DISARM_MINE) or 0)
        self.ui.beginSearchStrrefSpin.setValue(ssf.get(SSFSound.BEGIN_SEARCH) or 0)
        self.ui.beginUnlockStrrefSpin.setValue(ssf.get(SSFSound.BEGIN_UNLOCK) or 0)
        self.ui.beginStealthStrrefSpin.setValue(ssf.get(SSFSound.BEGIN_STEALTH) or 0)
        self.ui.unlockSuccessStrrefSpin.setValue(ssf.get(SSFSound.UNLOCK_SUCCESS) or 0)
        self.ui.unlockFailedStrrefSpin.setValue(ssf.get(SSFSound.UNLOCK_FAILED) or 0)
        self.ui.partySeparatedStrrefSpin.setValue(ssf.get(SSFSound.SEPARATED_FROM_PARTY) or 0)
        self.ui.rejoinPartyStrrefSpin.setValue(ssf.get(SSFSound.REJOINED_PARTY) or 0)
        self.ui.poisonedStrrefSpin.setValue(ssf.get(SSFSound.POISONED) or 0)
        self._suppress_undo_push = False

        self._sync_last_spin_values()
        self._undo_stack.clear()
        self._clean_undo_index = self._undo_stack.index()
        self.setWindowModified(False)
        self.update_text_boxes()

    def build(self) -> tuple[bytes, bytes]:
        """Builds sound data from UI values.

        Args:
        ----
            self: {The class instance}: Provides UI element values

        Returns:
        -------
            tuple[bytes, bytes]: {The built sound data and empty string}

        Processing Logic:
        ----------------
            - Initialize SSF object
            - Set data for each sound type from corresponding UI element value
            - Serialize SSF to bytearray
            - Return bytearray and empty string.
        """
        ssf = SSF()

        ssf.set_data(SSFSound.BATTLE_CRY_1, self.ui.battlecry1StrrefSpin.value())
        ssf.set_data(SSFSound.BATTLE_CRY_2, self.ui.battlecry2StrrefSpin.value())
        ssf.set_data(SSFSound.BATTLE_CRY_3, self.ui.battlecry3StrrefSpin.value())
        ssf.set_data(SSFSound.BATTLE_CRY_4, self.ui.battlecry4StrrefSpin.value())
        ssf.set_data(SSFSound.BATTLE_CRY_5, self.ui.battlecry5StrrefSpin.value())
        ssf.set_data(SSFSound.BATTLE_CRY_6, self.ui.battlecry6StrrefSpin.value())
        ssf.set_data(SSFSound.SELECT_1, self.ui.select1StrrefSpin.value())
        ssf.set_data(SSFSound.SELECT_2, self.ui.select2StrrefSpin.value())
        ssf.set_data(SSFSound.SELECT_3, self.ui.select3StrrefSpin.value())
        ssf.set_data(SSFSound.ATTACK_GRUNT_1, self.ui.attack1StrrefSpin.value())
        ssf.set_data(SSFSound.ATTACK_GRUNT_2, self.ui.attack2StrrefSpin.value())
        ssf.set_data(SSFSound.ATTACK_GRUNT_3, self.ui.attack3StrrefSpin.value())
        ssf.set_data(SSFSound.PAIN_GRUNT_1, self.ui.pain1StrrefSpin.value())
        ssf.set_data(SSFSound.PAIN_GRUNT_2, self.ui.pain2StrrefSpin.value())
        ssf.set_data(SSFSound.LOW_HEALTH, self.ui.lowHpStrrefSpin.value())
        ssf.set_data(SSFSound.DEAD, self.ui.deadStrrefSpin.value())
        ssf.set_data(SSFSound.CRITICAL_HIT, self.ui.criticalStrrefSpin.value())
        ssf.set_data(SSFSound.TARGET_IMMUNE, self.ui.immuneStrrefSpin.value())
        ssf.set_data(SSFSound.LAY_MINE, self.ui.layMineStrrefSpin.value())
        ssf.set_data(SSFSound.DISARM_MINE, self.ui.disarmMineStrrefSpin.value())
        ssf.set_data(SSFSound.BEGIN_STEALTH, self.ui.beginStealthStrrefSpin.value())
        ssf.set_data(SSFSound.BEGIN_SEARCH, self.ui.beginSearchStrrefSpin.value())
        ssf.set_data(SSFSound.BEGIN_UNLOCK, self.ui.beginUnlockStrrefSpin.value())
        ssf.set_data(SSFSound.UNLOCK_FAILED, self.ui.unlockFailedStrrefSpin.value())
        ssf.set_data(SSFSound.UNLOCK_SUCCESS, self.ui.unlockSuccessStrrefSpin.value())
        ssf.set_data(SSFSound.SEPARATED_FROM_PARTY, self.ui.partySeparatedStrrefSpin.value())
        ssf.set_data(SSFSound.REJOINED_PARTY, self.ui.rejoinPartyStrrefSpin.value())
        ssf.set_data(SSFSound.POISONED, self.ui.poisonedStrrefSpin.value())

        data = bytearray()
        write_ssf(ssf, data)
        return data, b""

    def new(self):
        if not self._maybe_save_changes():
            return
        super().new()

        self._suppress_undo_push = True
        self.ui.battlecry1StrrefSpin.setValue(0)
        self.ui.battlecry2StrrefSpin.setValue(0)
        self.ui.battlecry3StrrefSpin.setValue(0)
        self.ui.battlecry4StrrefSpin.setValue(0)
        self.ui.battlecry5StrrefSpin.setValue(0)
        self.ui.battlecry6StrrefSpin.setValue(0)
        self.ui.select1StrrefSpin.setValue(0)
        self.ui.select2StrrefSpin.setValue(0)
        self.ui.select3StrrefSpin.setValue(0)
        self.ui.attack1StrrefSpin.setValue(0)
        self.ui.attack2StrrefSpin.setValue(0)
        self.ui.attack3StrrefSpin.setValue(0)
        self.ui.pain1StrrefSpin.setValue(0)
        self.ui.pain2StrrefSpin.setValue(0)
        self.ui.lowHpStrrefSpin.setValue(0)
        self.ui.deadStrrefSpin.setValue(0)
        self.ui.criticalStrrefSpin.setValue(0)
        self.ui.immuneStrrefSpin.setValue(0)
        self.ui.layMineStrrefSpin.setValue(0)
        self.ui.disarmMineStrrefSpin.setValue(0)
        self.ui.beginSearchStrrefSpin.setValue(0)
        self.ui.beginUnlockStrrefSpin.setValue(0)
        self.ui.beginStealthStrrefSpin.setValue(0)
        self.ui.unlockSuccessStrrefSpin.setValue(0)
        self.ui.unlockFailedStrrefSpin.setValue(0)
        self.ui.partySeparatedStrrefSpin.setValue(0)
        self.ui.rejoinPartyStrrefSpin.setValue(0)
        self.ui.poisonedStrrefSpin.setValue(0)
        self._suppress_undo_push = False

        self._undo_stack.clear()
        self._clean_undo_index = self._undo_stack.index()
        self.setWindowModified(False)
        self._sync_last_spin_values()
        self.update_text_boxes()

    def update_text_boxes(self):
        """Updates text boxes with sound and text from talktable.

        Args:
        ----
            self: The class instance

        Processing Logic:
        ----------------
            - Gets stringref values from UI elements
            - Batches stringref lookups to talktable
            - Loops through pairs of UI elements and assigns text/sound from talktable.
        """
        # Always update enable/disable state for the row controls, even if TLK isn't set.
        if self._talktable is None:
            for row in self._rows:
                row.sound_edit.setText("")
                row.text_edit.setText("")
                row.play_button.setEnabled(False)
                row.more_button.setEnabled(False)
            return

        pairs: dict[tuple[QLineEdit, QLineEdit], int] = {(r.sound_edit, r.text_edit): r.spin.value() for r in self._rows}
        batch: dict[int, StringResult] = self._talktable.batch(list(pairs.values()))

        for pair, stringref in pairs.items():
            entry: StringResult | None = batch.get(stringref)
            if entry is None:
                text, sound = "Bad StrRef", ""
            else:
                text, sound = entry
            sound_str = "" if sound is None else str(sound)
            pair[0].setText("" if sound_str.strip().lower() == "none" else sound_str)
            pair[1].setText(text)

        # Update per-row button enablement based on resolved sound resref
        for row in self._rows:
            sound_resref = row.sound_edit.text().strip()
            enabled = bool(sound_resref) and self._installation is not None
            row.play_button.setEnabled(enabled)
            row.more_button.setEnabled(enabled)

    def select_talk_table(self):
        filepath, filter = QFileDialog.getOpenFileName(self, "Select a TLK file", "", "TalkTable (*.tlk)")
        if filepath:
            self._talktable = TalkTable(filepath)
        self.update_text_boxes()

    def open(self):  # noqa: D401
        if not self._maybe_save_changes():
            return
        super().open()

    def save(self):  # noqa: D401
        super().save()
        # If save succeeded, Editor will have set WindowModified to False.
        if not self.isWindowModified():
            self._clean_undo_index = self._undo_stack.index()

    def closeEvent(self, event: QCloseEvent | None):  # noqa: N802
        if event is None:
            return
        if not self._maybe_save_changes():
            event.ignore()
            return
        event.accept()

    # ---------------------------------------------------------------------
    # Sound row setup + handlers
    # ---------------------------------------------------------------------

    def _setup_sound_rows(self):
        style: QStyle | None = self.style()
        play_icon = style.standardIcon(QStyle.StandardPixmap.SP_MediaPlay) if style is not None else None  # pyright: ignore[reportOptionalMemberAccess]

        self._rows = [
            _SSFRow("Battlecry 1", self.ui.battlecry1StrrefSpin, self.ui.battlecry1SoundEdit, self.ui.battlecry1TextEdit, self.ui.battlecry1PlayButton, self.ui.battlecry1MoreButton),
            _SSFRow("Battlecry 2", self.ui.battlecry2StrrefSpin, self.ui.battlecry2SoundEdit, self.ui.battlecry2TextEdit, self.ui.battlecry2PlayButton, self.ui.battlecry2MoreButton),
            _SSFRow("Battlecry 3", self.ui.battlecry3StrrefSpin, self.ui.battlecry3SoundEdit, self.ui.battlecry3TextEdit, self.ui.battlecry3PlayButton, self.ui.battlecry3MoreButton),
            _SSFRow("Battlecry 4", self.ui.battlecry4StrrefSpin, self.ui.battlecry4SoundEdit, self.ui.battlecry4TextEdit, self.ui.battlecry4PlayButton, self.ui.battlecry4MoreButton),
            _SSFRow("Battlecry 5", self.ui.battlecry5StrrefSpin, self.ui.battlecry5SoundEdit, self.ui.battlecry5TextEdit, self.ui.battlecry5PlayButton, self.ui.battlecry5MoreButton),
            _SSFRow("Battlecry 6", self.ui.battlecry6StrrefSpin, self.ui.battlecry6SoundEdit, self.ui.battlecry6TextEdit, self.ui.battlecry6PlayButton, self.ui.battlecry6MoreButton),
            _SSFRow("Select 1", self.ui.select1StrrefSpin, self.ui.select1SoundEdit, self.ui.select1TextEdit, self.ui.select1PlayButton, self.ui.select1MoreButton),
            _SSFRow("Select 2", self.ui.select2StrrefSpin, self.ui.select2SoundEdit, self.ui.select2TextEdit, self.ui.select2PlayButton, self.ui.select2MoreButton),
            _SSFRow("Select 3", self.ui.select3StrrefSpin, self.ui.select3SoundEdit, self.ui.select3TextEdit, self.ui.select3PlayButton, self.ui.select3MoreButton),
            _SSFRow("Attack Grunt 1", self.ui.attack1StrrefSpin, self.ui.attack1SoundEdit, self.ui.attack1TextEdit, self.ui.attack1PlayButton, self.ui.attack1MoreButton),
            _SSFRow("Attack Grunt 2", self.ui.attack2StrrefSpin, self.ui.attack2SoundEdit, self.ui.attack2TextEdit, self.ui.attack2PlayButton, self.ui.attack2MoreButton),
            _SSFRow("Attack Grunt 3", self.ui.attack3StrrefSpin, self.ui.attack3SoundEdit, self.ui.attack3TextEdit, self.ui.attack3PlayButton, self.ui.attack3MoreButton),
            _SSFRow("Pain Grunt 1", self.ui.pain1StrrefSpin, self.ui.pain1SoundEdit, self.ui.pain1TextEdit, self.ui.pain1PlayButton, self.ui.pain1MoreButton),
            _SSFRow("Pain Grunt 2", self.ui.pain2StrrefSpin, self.ui.pain2SoundEdit, self.ui.pain2TextEdit, self.ui.pain2PlayButton, self.ui.pain2MoreButton),
            _SSFRow("Low Health", self.ui.lowHpStrrefSpin, self.ui.lowHpSoundEdit, self.ui.lowHpTextEdit, self.ui.lowHpPlayButton, self.ui.lowHpMoreButton),
            _SSFRow("Dead", self.ui.deadStrrefSpin, self.ui.deadSoundEdit, self.ui.deadTextEdit, self.ui.deadPlayButton, self.ui.deadMoreButton),
            _SSFRow("Critical Hit", self.ui.criticalStrrefSpin, self.ui.criticalSoundEdit, self.ui.criticalTextEdit, self.ui.criticalPlayButton, self.ui.criticalMoreButton),
            _SSFRow("Target Immune", self.ui.immuneStrrefSpin, self.ui.immuneSoundEdit, self.ui.immuneTextEdit, self.ui.immunePlayButton, self.ui.immuneMoreButton),
            _SSFRow("Lay Mine", self.ui.layMineStrrefSpin, self.ui.layMineSoundEdit, self.ui.layMineTextEdit, self.ui.layMinePlayButton, self.ui.layMineMoreButton),
            _SSFRow("Disarm Mine", self.ui.disarmMineStrrefSpin, self.ui.disarmMineSoundEdit, self.ui.disarmMineTextEdit, self.ui.disarmMinePlayButton, self.ui.disarmMineMoreButton),
            _SSFRow("Begin Stealth", self.ui.beginStealthStrrefSpin, self.ui.beginStealthSoundEdit, self.ui.beginStealthTextEdit, self.ui.beginStealthPlayButton, self.ui.beginStealthMoreButton),
            _SSFRow("Begin Search", self.ui.beginSearchStrrefSpin, self.ui.beginSearchSoundEdit, self.ui.beginSearchTextEdit, self.ui.beginSearchPlayButton, self.ui.beginSearchMoreButton),
            _SSFRow("Begin Unlock", self.ui.beginUnlockStrrefSpin, self.ui.beginUnlockSoundEdit, self.ui.beginUnlockTextEdit, self.ui.beginUnlockPlayButton, self.ui.beginUnlockMoreButton),
            _SSFRow("Unlock Failed", self.ui.unlockFailedStrrefSpin, self.ui.unlockFailedSoundEdit, self.ui.unlockFailedTextEdit, self.ui.unlockFailedPlayButton, self.ui.unlockFailedMoreButton),
            _SSFRow("Unlock Success", self.ui.unlockSuccessStrrefSpin, self.ui.unlockSuccessSoundEdit, self.ui.unlockSuccessTextEdit, self.ui.unlockSuccessPlayButton, self.ui.unlockSuccessMoreButton),
            _SSFRow("Party Separated", self.ui.partySeparatedStrrefSpin, self.ui.partySeparatedSoundEdit, self.ui.partySeparatedTextEdit, self.ui.partySeparatedPlayButton, self.ui.partySeparatedMoreButton),
            _SSFRow("Rejoin Party", self.ui.rejoinPartyStrrefSpin, self.ui.rejoinPartySoundEdit, self.ui.rejoinPartyTextEdit, self.ui.rejoinPartyPlayButton, self.ui.rejoinPartyMoreButton),
            _SSFRow("Poisoned", self.ui.poisonedStrrefSpin, self.ui.poisonedSoundEdit, self.ui.poisonedTextEdit, self.ui.poisonedPlayButton, self.ui.poisonedMoreButton),
        ]

        for row in self._rows:
            # Icon-only Play button
            if play_icon is not None:
                row.play_button.setIcon(play_icon)
            row.play_button.setToolTip("Play")
            row.play_button.setEnabled(False)
            row.more_button.setToolTip("Locate sound…")
            row.more_button.setEnabled(False)

            row.spin.valueChanged.connect(lambda value, r=row: self._on_spin_value_changed(r, int(value)))
            row.play_button.clicked.connect(lambda *args, r=row: self._play_row_sound(r))  # type: ignore[misc]
            row.more_button.clicked.connect(lambda *args, r=row: self._open_row_menu(r))  # type: ignore[misc]

        self._sync_last_spin_values()
        self.update_text_boxes()

    def _sync_last_spin_values(self):
        self._last_spin_values = {row.spin: int(row.spin.value()) for row in self._rows}

    def _on_spin_value_changed(self, row: _SSFRow, new_value: int):
        if self._suppress_undo_push:
            self._last_spin_values[row.spin] = new_value
            return
        old_value = self._last_spin_values.get(row.spin, new_value)
        if new_value == old_value:
            return
        self._last_spin_values[row.spin] = new_value
        self._undo_stack.push(_SpinValueCommand(self, row_label=row.label, spin=row.spin, old_value=old_value, new_value=new_value))

    def _apply_spin_value(self, spin: QSpinBox, value: int):
        self._suppress_undo_push = True
        try:
            spin.setValue(int(value))
        finally:
            self._suppress_undo_push = False
        self._last_spin_values[spin] = int(value)
        self.update_text_boxes()
        # WindowModified is driven by undo stack index vs clean index.
        self.setWindowModified(self._undo_stack.index() != self._clean_undo_index)

    def _on_undo_index_changed(self, index: int):
        self.setWindowModified(index != self._clean_undo_index)

    def _play_row_sound(self, row: _SSFRow):
        sound_resref = row.sound_edit.text().strip()
        if not sound_resref or self._installation is None:
            self.blink_window(sound=False)
            return
        self.play_sound(sound_resref)

    def _open_row_menu(self, row: _SSFRow):
        if self._installation is None:
            self.blink_window(sound=False)
            return
        sound_resref = row.sound_edit.text().strip()
        if not sound_resref:
            self.blink_window(sound=False)
            return
        menu = QMenu(self)
        self._installation.build_file_context_menu(
            menu,
            parent_widget=row.more_button,
            widget_text=sound_resref,
            resref_type=[ResourceType.WAV],
            order=[
                SearchLocation.MUSIC,
                SearchLocation.VOICE,
                SearchLocation.SOUND,
                SearchLocation.OVERRIDE,
                SearchLocation.MODULES,
                SearchLocation.RIMS,
                SearchLocation.CHITIN,
            ],
        )
        menu.exec(row.more_button.mapToGlobal(QPoint(0, row.more_button.height())))

    def _maybe_save_changes(self) -> bool:
        """Return True if it is OK to proceed, False if the user cancelled."""
        # Avoid modal prompts during automated tests
        import sys

        if "pytest" in sys.modules:
            return True

        if not self.isWindowModified():
            return True

        result = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes. Do you want to save?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
        )
        if result == QMessageBox.StandardButton.Save:
            self.save()
            return not self.isWindowModified()
        if result == QMessageBox.StandardButton.Discard:
            return True
        return False
