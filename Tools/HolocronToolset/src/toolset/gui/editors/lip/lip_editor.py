from __future__ import annotations

import wave

from typing import TYPE_CHECKING, Any, Optional, cast

import qtpy

from qtpy.QtCore import QTimer, QUrl, Qt
from qtpy.QtGui import QKeySequence
from qtpy.QtMultimedia import QAudioOutput, QMediaPlayer
from qtpy.QtWidgets import (
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMenu,
    QMessageBox,
    QPushButton,
    QShortcut,  # pyright: ignore[reportPrivateImportUsage]
    QVBoxLayout,
    QWidget,
)

from pykotor.resource.formats.lip import LIP, LIPKeyFrame, LIPShape, bytes_lip, read_lip
from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from qtpy.QtCore import QPoint
    from qtpy.QtGui import _QAction

    from toolset.data.installation import HTInstallation


# Command pattern for undo/redo functionality
class Command:
    """Base class for undoable commands."""

    def execute(self) -> None:
        """Execute the command."""
        raise NotImplementedError

    def undo(self) -> None:
        """Undo the command."""
        raise NotImplementedError

    def redo(self) -> None:
        """Redo the command (same as execute for most commands)."""
        self.execute()

    def description(self) -> str:
        """Return a human-readable description of the command."""
        return "Command"


class AddKeyframeCommand(Command):
    """Command for adding a keyframe."""

    def __init__(
        self,
        lip: LIP,
        time: float,
        shape: LIPShape,
    ) -> None:
        self.lip: LIP = lip
        self.time: float = time
        self.shape: LIPShape = shape
        self.removed_frame: LIPKeyFrame | None = None

    def execute(self) -> None:
        # Store any existing frame at this time for undo
        existing_frames = [f for f in self.lip.frames if abs(f.time - self.time) <= 0.0001]
        if existing_frames:
            self.removed_frame = existing_frames[0]

        # Add the new frame
        self.lip.add(self.time, self.shape)

    def undo(self) -> None:
        # Remove the added frame
        self.lip.frames = [f for f in self.lip.frames if abs(f.time - self.time) > 0.0001]

        # Restore any previously removed frame
        if self.removed_frame:
            self.lip.frames.append(self.removed_frame)
            self.lip.frames.sort()

    def description(self) -> str:
        return f"Add keyframe at {self.time:.3f}s ({self.shape.name})"


class UpdateKeyframeCommand(Command):
    """Command for updating a keyframe."""

    def __init__(self, lip: LIP, old_time: float, new_time: float, new_shape: LIPShape):
        self.lip = lip
        self.old_time = old_time
        self.new_time = new_time
        self.new_shape = new_shape
        self.old_shape: Optional[LIPShape] = None
        self.was_replaced = False

    def execute(self) -> None:
        # Find the frame to update
        for frame in self.lip.frames:
            if abs(frame.time - self.old_time) <= 0.0001:
                self.old_shape = frame.shape
                break

        # Check if we're replacing an existing frame at new_time
        existing_frames = [f for f in self.lip.frames if abs(f.time - self.new_time) <= 0.0001]
        if existing_frames and abs(self.old_time - self.new_time) > 0.0001:
            self.was_replaced = True
            # Store the frame that will be replaced
            self.replaced_frame = existing_frames[0]

        # Update the frame
        self.lip.frames = [f for f in self.lip.frames if abs(f.time - self.old_time) > 0.0001]
        self.lip.add(self.new_time, self.new_shape)

    def undo(self) -> None:
        # Remove the updated frame
        self.lip.frames = [f for f in self.lip.frames if abs(f.time - self.new_time) > 0.0001]

        # Restore the old frame
        if self.old_shape is not None:
            self.lip.add(self.old_time, self.old_shape)

        # Restore any replaced frame
        if self.was_replaced:
            self.lip.frames.append(self.replaced_frame)
            self.lip.frames.sort()

    def description(self) -> str:
        return f"Update keyframe from {self.old_time:.3f}s to {self.new_time:.3f}s"


class DeleteKeyframeCommand(Command):
    """Command for deleting a keyframe."""

    def __init__(self, lip: LIP, time: float):
        self.lip = lip
        self.time = time
        self.deleted_frame: Optional[LIPKeyFrame] = None

    def execute(self) -> None:
        # Find and store the frame to delete
        for frame in self.lip.frames:
            if abs(frame.time - self.time) <= 0.0001:
                self.deleted_frame = LIPKeyFrame(frame.time, frame.shape)
                break

        # Remove the frame
        self.lip.frames = [f for f in self.lip.frames if abs(f.time - self.time) > 0.0001]

    def undo(self) -> None:
        # Restore the deleted frame
        if self.deleted_frame:
            self.lip.frames.append(self.deleted_frame)
            self.lip.frames.sort()

    def description(self) -> str:
        return f"Delete keyframe at {self.time:.3f}s"


class LoadLIPCommand(Command):
    """Command for loading a LIP file."""

    def __init__(self, editor: LIPEditor, old_lip: Optional[LIP], new_lip: LIP):
        self.editor = editor
        self.old_lip = old_lip
        self.new_lip = new_lip

    def execute(self) -> None:
        self.editor.lip = self.new_lip
        self.editor.duration = self.new_lip.length
        self.editor.duration_label.setText(f"{self.editor.duration:.3f}s")
        self.editor.time_input.setMaximum(self.editor.duration)
        self.editor.update_preview()

    def undo(self) -> None:
        self.editor.lip = self.old_lip
        if self.old_lip:
            self.editor.duration = self.old_lip.length
            self.editor.duration_label.setText(f"{self.editor.duration:.3f}s")
            self.editor.time_input.setMaximum(self.editor.duration)
        else:
            self.editor.duration = 0.0
            self.editor.duration_label.setText("0.000s")
            self.editor.time_input.setMaximum(999.999)
        self.editor.update_preview()

    def description(self) -> str:
        return "Load LIP file"


class NewLIPCommand(Command):
    """Command for creating a new LIP file."""

    def __init__(self, editor: LIPEditor, old_lip: Optional[LIP]):
        self.editor = editor
        self.old_lip = old_lip
        self.new_lip = LIP()

    def execute(self) -> None:
        self.editor.lip = self.new_lip
        self.editor.duration = 0.0
        self.editor.duration_label.setText("0.000s")
        self.editor.time_input.setMaximum(999.999)
        self.editor.update_preview()

    def undo(self) -> None:
        self.editor.lip = self.old_lip
        if self.old_lip:
            self.editor.duration = self.old_lip.length
            self.editor.duration_label.setText(f"{self.editor.duration:.3f}s")
            self.editor.time_input.setMaximum(self.editor.duration)
        self.editor.update_preview()

    def description(self) -> str:
        return "New LIP file"


class UndoRedoManager:
    """Manages undo/redo functionality with command stacks."""

    def __init__(self):
        self.undo_stack: list[Command] = []
        self.redo_stack: list[Command] = []
        self.max_stack_size = 50

    def execute(self, command: Command) -> None:
        """Execute a command and add it to the undo stack."""
        command.execute()
        self.undo_stack.append(command)
        self.redo_stack.clear()  # Clear redo stack when new command is executed

        # Limit stack size
        if len(self.undo_stack) > self.max_stack_size:
            self.undo_stack.pop(0)

    def undo(self) -> Optional[Command]:
        """Undo the last command."""
        if not self.undo_stack:
            return None

        command = self.undo_stack.pop()
        command.undo()
        self.redo_stack.append(command)
        return command

    def redo(self) -> Optional[Command]:
        """Redo the last undone command."""
        if not self.redo_stack:
            return None

        command = self.redo_stack.pop()
        command.redo()
        self.undo_stack.append(command)
        return command

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self.redo_stack) > 0

    def undo_description(self) -> str:
        """Get description of the command that can be undone."""
        if self.undo_stack:
            return self.undo_stack[-1].description()
        return ""

    def redo_description(self) -> str:
        """Get description of the command that can be redone."""
        if self.redo_stack:
            return self.redo_stack[-1].description()
        return ""

    def clear(self) -> None:
        """Clear all undo/redo history."""
        self.undo_stack.clear()
        self.redo_stack.clear()


class LIPEditor(Editor):
    """Editor for KotOR LIP files."""

    def __init__(
        self,
        parent: QWidget | None = None,
        installation: HTInstallation | None = None,
    ):
        """Initialize the LIP editor."""
        supported = [ResourceType.LIP, ResourceType.LIP_XML, ResourceType.LIP_JSON]
        super().__init__(parent, "LIP Editor", "lip", supported, supported, installation)

        # Phoneme to viseme mapping from KLE
        self.phoneme_map: dict[str, LIPShape] = {
            "AA": LIPShape.AH,  # father
            "AE": LIPShape.AH,  # cat
            "AH": LIPShape.AH,  # cut
            "AO": LIPShape.OH,  # dog
            "AW": LIPShape.OH,  # cow
            "AY": LIPShape.AH,  # hide
            "B": LIPShape.MPB,  # be
            "CH": LIPShape.SH,  # cheese
            "D": LIPShape.TD,  # dee
            "DH": LIPShape.TD,  # thee
            "EH": LIPShape.EH,  # pet
            "ER": LIPShape.EE,  # fur
            "EY": LIPShape.AH,  # ate
            "F": LIPShape.FV,  # fee
            "G": LIPShape.TD,  # green
            "HH": LIPShape.EE,  # he
            "IH": LIPShape.EE,  # it
            "IY": LIPShape.EE,  # eat
            "JH": LIPShape.SH,  # gee
            "K": LIPShape.KG,  # key
            "L": LIPShape.L,  # lee
            "M": LIPShape.MPB,  # me
            "N": LIPShape.NG,  # knee
            "NG": LIPShape.NG,  # ping
            "OW": LIPShape.OH,  # oat
            "OY": LIPShape.OH,  # toy
            "P": LIPShape.MPB,  # pee
            "R": LIPShape.L,  # read
            "S": LIPShape.STS,  # sea
            "SH": LIPShape.SH,  # she
            "T": LIPShape.TD,  # tea
            "TH": LIPShape.FV,  # theta
            "UH": LIPShape.EE,  # hood
            "UW": LIPShape.OOH,  # two
            "V": LIPShape.FV,  # vee
            "W": LIPShape.MPB,  # we
            "Y": LIPShape.Y,  # yield
            "Z": LIPShape.STS,  # zee
            "ZH": LIPShape.STS,  # seizure
        }

        self.central_widget: QWidget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        # Preview playback
        self.player = QMediaPlayer()
        self.audio_output: QAudioOutput | None = None
        
        # Qt6 requires explicit audio output setup
        if qtpy.QT6:
            self.audio_output = QAudioOutput()
            self.audio_output.setVolume(1)
            player: Any = cast("Any", self.player)
            player.setAudioOutput(self.audio_output)  # type: ignore[attr-defined]
        
        self.player.positionChanged.connect(self.on_playback_position_changed)
        state_changed = self.player.stateChanged if qtpy.QT5 else self.player.playbackStateChanged  # type: ignore[attr-defined]
        state_changed.connect(self.on_playback_state_changed)

        self.preview_timer = QTimer()
        self.preview_timer.setInterval(16)  # ~60fps
        self.preview_timer.timeout.connect(self.update_preview_display)

        # Initialize undo/redo actions
        self.undo_action: Optional[QAction] = None
        self.redo_action: Optional[QAction] = None

        # Current preview state
        self.current_shape: Optional[LIPShape] = None
        self.preview_label: Optional[QLabel] = None

        self.setup_ui()
        self._setup_menus()
        self._add_help_action()
        self.setup_shortcuts()

        # Initialize undo/redo system
        self.undo_redo_manager = UndoRedoManager()

        self.lip: Optional[LIP] = None
        self.duration: float = 0.0

    def setup_ui(self):
        """Set up the UI elements."""
        layout = QVBoxLayout(self.central_widget)

        # Audio file selection
        audio_layout = QHBoxLayout()
        self.audio_path: QLineEdit = QLineEdit()
        self.audio_path.setReadOnly(True)
        self.audio_path.setToolTip("Path to the WAV audio file")
        audio_layout.addWidget(QLabel("Audio File:"))
        audio_layout.addWidget(self.audio_path)
        load_audio_btn = QPushButton("Load Audio")
        load_audio_btn.setToolTip("Load a WAV audio file (Ctrl+O)")
        load_audio_btn.clicked.connect(self.load_audio)
        audio_layout.addWidget(load_audio_btn)
        layout.addLayout(audio_layout)

        # Duration display
        duration_layout = QHBoxLayout()
        from toolset.gui.common.localization import translate as tr
        duration_layout.addWidget(QLabel(tr("Duration:")))
        self.duration_label: QLabel = QLabel("0.000s")
        self.duration_label.setToolTip(tr("Duration of the loaded audio file"))
        duration_layout.addWidget(self.duration_label)
        layout.addLayout(duration_layout)

        # Preview list
        self.preview_list: QListWidget = QListWidget()
        self.preview_list.setToolTip(tr("List of keyframes (right-click for options)"))
        self.preview_list.itemSelectionChanged.connect(self.on_keyframe_selected)
        self.preview_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.preview_list.customContextMenuRequested.connect(self.show_preview_context_menu)
        layout.addWidget(self.preview_list)

        # Keyframe editing
        keyframe_layout = QHBoxLayout()

        # Time input
        keyframe_layout.addWidget(QLabel("Time:"))
        self.time_input: QDoubleSpinBox = QDoubleSpinBox()
        self.time_input.setToolTip("Time in seconds for the keyframe")
        self.time_input.setDecimals(3)
        self.time_input.setRange(0.0, 999.999)
        self.time_input.setSingleStep(0.1)
        keyframe_layout.addWidget(self.time_input)

        # Shape selection
        keyframe_layout.addWidget(QLabel("Shape:"))
        self.shape_select: QComboBox = QComboBox()
        self.shape_select.setToolTip("Lip shape/viseme for the keyframe")
        for shape in LIPShape:
            self.shape_select.addItem(shape.name)
        keyframe_layout.addWidget(self.shape_select)

        layout.addLayout(keyframe_layout)

        # Keyframe buttons
        button_layout = QHBoxLayout()

        add_keyframe_btn = QPushButton("Add Keyframe")
        add_keyframe_btn.setToolTip("Add a new keyframe (Insert)")
        add_keyframe_btn.clicked.connect(self.add_keyframe)
        button_layout.addWidget(add_keyframe_btn)

        update_keyframe_btn = QPushButton("Update Keyframe")
        update_keyframe_btn.setToolTip("Update selected keyframe (Enter)")
        update_keyframe_btn.clicked.connect(self.update_keyframe)
        button_layout.addWidget(update_keyframe_btn)

        delete_keyframe_btn = QPushButton("Delete Keyframe")
        delete_keyframe_btn.setToolTip("Delete selected keyframe (Delete)")
        delete_keyframe_btn.clicked.connect(self.delete_keyframe)
        button_layout.addWidget(delete_keyframe_btn)

        layout.addLayout(button_layout)

        # Preview display
        preview_layout = QHBoxLayout()
        preview_layout.addWidget(QLabel("Current Shape:"))
        self.preview_label = QLabel("None")
        self.preview_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #f0f0f0;
            }
        """)
        preview_layout.addWidget(self.preview_label)
        layout.addLayout(preview_layout)

        # Playback controls
        playback_layout = QHBoxLayout()

        play_btn = QPushButton("Play")
        play_btn.setToolTip("Play preview (Space)")
        play_btn.clicked.connect(self.play_preview)
        playback_layout.addWidget(play_btn)

        stop_btn = QPushButton("Stop")
        stop_btn.setToolTip("Stop preview (Esc)")
        stop_btn.clicked.connect(self.stop_preview)
        playback_layout.addWidget(stop_btn)

        layout.addLayout(playback_layout)

    def setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        # File operations
        QShortcut(QKeySequence.StandardKey.Open, self, self.load_audio)
        QShortcut(QKeySequence.StandardKey.Save, self, self.save)
        QShortcut(QKeySequence.StandardKey.SaveAs, self, self.save_as)

        # Keyframe operations
        QShortcut(Qt.Key.Key_Insert, self, self.add_keyframe)
        QShortcut(Qt.Key.Key_Return, self, self.update_keyframe)
        QShortcut(Qt.Key.Key_Delete, self, self.delete_keyframe)

        # Playback controls
        QShortcut(Qt.Key.Key_Space, self, self.play_preview)
        QShortcut(Qt.Key.Key_Escape, self, self.stop_preview)

        # Undo/Redo
        QShortcut(QKeySequence.StandardKey.Undo, self, self.undo)
        QShortcut(QKeySequence.StandardKey.Redo, self, self.redo)

    def _setup_menus(self):
        """Set up the edit menu with undo/redo actions."""
        from qtpy.QtWidgets import QMenuBar

        # Get the menu bar
        menubar = self.menuBar()
        if not menubar:
            return

        # Find or create Edit menu
        edit_menu = menubar.findChild(QMenu, "edit_menu")
        if not edit_menu:
            edit_menu = menubar.addMenu("&Edit")

        # Add undo/redo actions
        self.undo_action = edit_menu.addAction("&Undo")
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.triggered.connect(self.undo)
        self.undo_action.setEnabled(False)

        self.redo_action = edit_menu.addAction("&Redo")
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_action.triggered.connect(self.redo)
        self.redo_action.setEnabled(False)

        # Update initial state
        self._update_undo_redo_state()

    def _update_undo_redo_state(self):
        """Update the enabled state and text of undo/redo actions."""
        if self.undo_action:
            can_undo = self.undo_redo_manager.can_undo()
            self.undo_action.setEnabled(can_undo)
            if can_undo:
                description = self.undo_redo_manager.undo_description()
                self.undo_action.setText(f"&Undo {description}")
            else:
                self.undo_action.setText("&Undo")

        if self.redo_action:
            can_redo = self.undo_redo_manager.can_redo()
            self.redo_action.setEnabled(can_redo)
            if can_redo:
                description = self.undo_redo_manager.redo_description()
                self.redo_action.setText(f"&Redo {description}")
            else:
                self.redo_action.setText("&Redo")

    def show_preview_context_menu(self, pos: QPoint):
        """Show context menu for preview list."""
        menu = QMenu(self)

        # Add actions
        add_action: _QAction = menu.addAction("Add Keyframe")
        add_action.triggered.connect(self.add_keyframe)

        # Only enable these if an item is selected
        selected_items = self.preview_list.selectedItems()
        if selected_items:
            update_action: _QAction = menu.addAction("Update Keyframe")
            update_action.triggered.connect(self.update_keyframe)

            delete_action: _QAction = menu.addAction("Delete Keyframe")
            delete_action.triggered.connect(self.delete_keyframe)

        menu.exec(self.preview_list.mapToGlobal(pos))

    def undo(self):
        """Undo last action."""
        command = self.undo_redo_manager.undo()
        if command:
            self.update_preview()
            # Update UI state after undo
            self._update_undo_redo_state()
        else:
            QMessageBox.information(self, "Undo", "Nothing to undo")

    def redo(self):
        """Redo last undone action."""
        command = self.undo_redo_manager.redo()
        if command:
            self.update_preview()
            # Update UI state after redo
            self._update_undo_redo_state()
        else:
            QMessageBox.information(self, "Redo", "Nothing to redo")

    def load_audio(self):
        """Load an audio file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Audio File", "", "Audio Files (*.wav)")
        if file_path:
            self.audio_path.setText(file_path)
            # Get audio duration
            with wave.open(file_path, "rb") as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                self.duration = frames / float(rate)
                self.duration_label.setText(f"{self.duration:.3f}s")
                self.time_input.setMaximum(self.duration)

            # Clear undo/redo history when loading new audio
            self.undo_redo_manager.clear()
            self._update_undo_redo_state()

            # Set up media player
            if qtpy.QT5:
                from qtpy.QtMultimedia import QMediaContent  # pyright: ignore[reportAttributeAccessIssue]
                self.player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))  # pyright: ignore[reportAttributeAccessIssue]
            elif qtpy.QT6:
                player: Any = cast("Any", self.player)
                player.setSource(QUrl.fromLocalFile(file_path))  # type: ignore[attr-defined]

    def add_keyframe(self):
        """Add a keyframe to the LIP file."""
        try:
            time = self.time_input.value()
            shape = LIPShape[self.shape_select.currentText()]

            if not self.lip:
                self.lip = LIP()
                self.lip.length = self.duration

            command = AddKeyframeCommand(self.lip, time, shape)
            self.undo_redo_manager.execute(command)
            self.update_preview()
            self._update_undo_redo_state()

        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))

    def update_keyframe(self):
        """Update the selected keyframe."""
        if not self.lip:
            QMessageBox.warning(self, "Error", "No LIP file loaded")
            return

        selected_items = self.preview_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a keyframe to update")
            return

        try:
            # Get current values
            new_time = self.time_input.value()
            new_shape = LIPShape[self.shape_select.currentText()]

            # Get old keyframe info
            selected_idx = self.preview_list.row(selected_items[0])
            old_frame = self.lip.frames[selected_idx]
            old_time = old_frame.time

            command = UpdateKeyframeCommand(self.lip, old_time, new_time, new_shape)
            self.undo_redo_manager.execute(command)
            self.update_preview()
            self._update_undo_redo_state()

        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))

    def delete_keyframe(self):
        """Delete the selected keyframe."""
        if not self.lip:
            QMessageBox.warning(self, "Error", "No LIP file loaded")
            return

        selected_items = self.preview_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a keyframe to delete")
            return

        selected_idx = self.preview_list.row(selected_items[0])
        frame_to_delete = self.lip.frames[selected_idx]

        command = DeleteKeyframeCommand(self.lip, frame_to_delete.time)
        self.undo_redo_manager.execute(command)
        self.update_preview()
        self._update_undo_redo_state()

    def on_keyframe_selected(self):
        """Update inputs when a keyframe is selected."""
        if not self.lip:
            return

        selected_items = self.preview_list.selectedItems()
        if not selected_items:
            return

        selected_idx = self.preview_list.row(selected_items[0])
        frame = self.lip.frames[selected_idx]

        self.time_input.setValue(frame.time)
        self.shape_select.setCurrentText(frame.shape.name)

    def update_preview(self):
        """Update the preview list."""
        self.preview_list.clear()
        if not self.lip:
            return

        for frame in sorted(self.lip.frames, key=lambda f: f.time):
            self.preview_list.addItem(f"{frame.time:.3f}s: {frame.shape.name}")

    def play_preview(self):
        """Start preview playback."""
        if not self.lip or not self.audio_path.text():
            QMessageBox.warning(self, "Error", "Please load both a LIP file and audio file")
            return

        self.player.play()
        self.preview_timer.start()

    def stop_preview(self):
        """Stop preview playback."""
        self.player.stop()
        self.preview_timer.stop()
        if self.preview_label:
            self.preview_label.setText("None")
        self.current_shape = None

    def on_playback_position_changed(self, position: int):
        """Update current time during playback."""
        current_time = position / 1000.0  # Convert ms to seconds

        # Find the current shape based on time
        if not self.lip:
            return

        # Sort frames by time
        sorted_frames = sorted(self.lip.frames, key=lambda f: f.time)

        # Find the last frame before current_time
        current_shape = None
        for frame in sorted_frames:
            if frame.time <= current_time:
                current_shape = frame.shape
            else:
                break

        self.current_shape = current_shape

    def update_preview_display(self):
        """Update the preview display with current shape."""
        if not self.preview_label:
            return

        if self.current_shape:
            self.preview_label.setText(self.current_shape.name)
        else:
            self.preview_label.setText("None")

    def on_playback_state_changed(self, state: int):
        """Handle playback state changes."""
        state_enum = QMediaPlayer.State if qtpy.QT5 else QMediaPlayer.PlaybackState  # type: ignore[attr-defined]
        if state == state_enum.StoppedState:
            if self.preview_label:
                self.preview_label.setText("None")
            self.preview_timer.stop()
            self.current_shape = None

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes | bytearray,
    ) -> None:
        """Load a LIP file."""
        super().load(filepath, resref, restype, data)

        old_lip = self.lip
        new_lip = read_lip(data)

        command = LoadLIPCommand(self, old_lip, new_lip)
        self.undo_redo_manager.execute(command)
        self._update_undo_redo_state()

    def build(self) -> tuple[bytes, bytes]:
        """Build LIP file data."""
        if not self.lip:
            return b"", b""

        return bytes_lip(self.lip), b""

    def new(self):
        """Create new LIP file."""
        super().new()

        old_lip = self.lip
        command = NewLIPCommand(self, old_lip)
        self.undo_redo_manager.execute(command)
        self._update_undo_redo_state()

