from __future__ import annotations

import tempfile
import time
import traceback
import uuid

from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import qtpy

from loggerplus import RobustLogger  # type: ignore[import-untyped] # pyright: ignore[reportMissingTypeStubs]
from qtpy import QtCore
from qtpy.QtCore import QBuffer, QIODevice, QTimer
from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtMultimedia import QMediaPlayer
from qtpy.QtWidgets import (
    QAction,
    QFileDialog,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QShortcut,
)

from pykotor.extract.file import ResourceIdentifier  # type: ignore[import-not-found] # pyright: ignore[reportMissingImports]
from pykotor.resource.type import ResourceType  # type: ignore[import-not-found] # pyright: ignore[reportMissingImports]
from pykotor.tools.misc import is_any_erf_type_file, is_bif_file, is_capsule_file, is_rim_file  # type: ignore[import-not-found] # pyright: ignore[reportMissingImports]
from toolset.gui.dialogs.save.to_module import SaveToModuleDialog  # type: ignore[import-not-found] # pyright: ignore[reportMissingImports]
from utility.error_handling import universal_simplify_exception  # type: ignore[import-not-found] # pyright: ignore[reportMissingImports]
from utility.system.os_helper import remove_any  # type: ignore[import-not-found] # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    import os

    from PyQt6.QtMultimedia import QMediaPlayer as PyQt6MediaPlayer  # pyright: ignore[reportMissingImports, reportAttributeAccessIssue]
    from PySide6.QtMultimedia import QMediaPlayer as PySide6MediaPlayer  # type: ignore[import-not-found]  # pyright: ignore[reportMissingImports, reportAttributeAccessIssue]
    from qtpy.QtGui import QCloseEvent
    from qtpy.QtWidgets import QWidget

    from toolset.data.installation import HTInstallation  # type: ignore[import-not-found] # pyright: ignore[reportMissingImports]


class AudioPlayer(QMainWindow):
    """Audio player window with comprehensive file management capabilities.

    Features:
    - Play audio files (WAV, MP3, OGG, FLAC)
    - Full File menu with New, Open, Save, Save As, Revert, Exit
    - Support for saving to files and modules (MOD/ERF/RIM)
    - Keyboard shortcuts for all operations
    """

    def __init__(self, parent: QWidget | None, installation: HTInstallation | None = None):
        super().__init__(parent)

        from toolset.uic.qtpy.windows.audio_player import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._installation: HTInstallation | None = installation
        self._filepath: Path | None = None
        self._resname: str = f"untitled_{uuid.uuid4().hex[:8]}"
        self._restype: ResourceType = ResourceType.WAV
        self._revert: bytes = b""
        self._current_data: bytes = b""

        self.player: QMediaPlayer = QMediaPlayer(self)
        self.buffer: QBuffer = QBuffer(self)
        self.temp_file: str | None = None  # Path to temporary file

        # Supported audio resource types
        self._read_supported: list[ResourceType] = [ResourceType.WAV, ResourceType.MP3, ResourceType.BMU]
        self._write_supported: list[ResourceType] = [ResourceType.WAV, ResourceType.MP3]

        # Set up filters
        self._setup_file_filters()

        # Set up menus
        self._setup_menus()

        # Connect player signals
        self._setup_player_signals()

        # Set window icon
        self._setup_icon()

    def _setup_file_filters(self) -> None:
        """Set up file filters for open/save dialogs."""
        self._save_filter: str = "Audio Files ("
        for resource in self._write_supported:
            self._save_filter += f'*.{resource.extension}{"" if self._write_supported[-1] == resource else " "}'
        self._save_filter += ");;"
        for resource in self._write_supported:
            self._save_filter += f"{resource.category} File (*.{resource.extension});;"
        self._save_filter += "All Files (*.*)"

        self._open_filter: str = "Audio Files ("
        for resource in self._read_supported:
            self._open_filter += f'*.{resource.extension}{"" if self._read_supported[-1] == resource else " "}'
        self._open_filter += ");;"
        for resource in self._read_supported:
            self._open_filter += f"{resource.category} File (*.{resource.extension});;"
        self._open_filter += "All Files (*.*)"

    def _setup_menus(self) -> None:
        """Set up menu bar with all file operations."""
        menubar: QMenuBar | None = self.menuBar()
        assert menubar is not None, "menubar is somehow None"

        # Get or create File menu
        file_menu: QMenu | None = None
        for action in menubar.actions():
            if action.text() == "File":
                file_menu = action.menu()
                break

        if file_menu is None:
            file_menu = QMenu("File", self)
            menubar.addMenu(file_menu)

        # Connect existing actions or create new ones
        actions_map = {
            "New": ("actionNew", "Ctrl+N", self.new),
            "Open": ("actionOpen", "Ctrl+O", self.open),
            "Save": ("actionSave", "Ctrl+S", self.save),
            "Save As": ("actionSaveAs", "Ctrl+Shift+S", self.save_as),
            "Revert": ("actionRevert", "Ctrl+R", self.revert),
            "Exit": ("actionExit", "Ctrl+Q", self.close),
        }

        # Find and connect actions
        for menu_text, (action_name, shortcut, handler) in actions_map.items():
            action = self.findChild(QAction, action_name)
            if action:
                if not action.actions() if hasattr(action, "actions") else True:  # Check if already connected
                    action.triggered.connect(handler)  # type: ignore[attr-defined]
                action.setShortcut(shortcut)  # type: ignore[attr-defined]
                if menu_text == "Revert":
                    action.setEnabled(False)  # type: ignore[attr-defined]

        # Set up keyboard shortcuts
        QShortcut("Ctrl+N", self).activated.connect(self.new)
        QShortcut("Ctrl+O", self).activated.connect(self.open)
        QShortcut("Ctrl+S", self).activated.connect(self.save)
        QShortcut("Ctrl+Shift+S", self).activated.connect(self.save_as)
        QShortcut("Ctrl+R", self).activated.connect(self.revert)
        QShortcut("Ctrl+Q", self).activated.connect(self.close)

        # Connect player controls
        self.ui.stopButton.clicked.connect(self.player.stop)
        self.ui.playButton.clicked.connect(self.player.play)
        self.ui.pauseButton.clicked.connect(self.player.pause)
        self.ui.timeSlider.sliderReleased.connect(self.changePosition)

    def _setup_player_signals(self) -> None:
        """Set up media player signals."""
        self.player.durationChanged.connect(self.duration_changed)
        self.player.positionChanged.connect(self.positionChanged)
        self.destroyed.connect(self.closeEvent)
        if qtpy.QT5:
            self.player.error.connect(lambda _=None: self.handle_error())  # type: ignore[attr-defined]
        else:
            self.player.errorOccurred.connect(lambda *args, **kwargs: self.handle_error(*args, **kwargs))  # type: ignore[attr-defined] # noqa: FBT001  # pyright: ignore[reportAttributeAccessIssue]

    def _setup_icon(self) -> None:
        """Set up window icon."""
        icon_version: str = "x" if self._installation is None else ("2" if self._installation.tsl else "1")
        icon_path_str: str = f":/images/icons/k{icon_version}/audio_player.png"
        try:
            self.setWindowIcon(QIcon(QPixmap(icon_path_str)))
        except Exception:  # noqa: BLE001
            # Icon not found, use default
            pass

    def _detect_audio_extension(self, data: bytes) -> str:
        """Detect audio format from file magic bytes.
        
        Returns appropriate file extension for media player compatibility.
        
        References:
            vendor/KotOR.js/src/audio/AudioFile.ts:9-16 - Magic byte constants
            toolset/gui/editor/media.py:25-52 - Similar detection logic
        """
        if len(data) < 4:
            return ".wav"
        
        # Check for MP3 signatures
        # ID3 header (ID3v2 tags at start of MP3)
        if data[:3] == b"ID3":
            return ".mp3"
        # MP3 frame sync (0xFF 0xFB, 0xFF 0xFA, 0xFF 0xF3, 0xFF 0xF2)
        if len(data) >= 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0:
            return ".mp3"
        # LAME header
        if data[:4] == b"LAME":
            return ".mp3"
        
        # Check for RIFF/WAVE
        if data[:4] == b"RIFF":
            return ".wav"
        
        # Check for OGG
        if data[:4] == b"OggS":
            return ".ogg"
        
        # Check for FLAC
        if data[:4] == b"fLaC":
            return ".flac"
        
        # Default to wav
        return ".wav"

    def refresh_window_title(self) -> None:
        """Refresh the window title based on current state."""
        installation_name: str = self._installation.name if self._installation else "No Installation"
        title: str = f"Audio Player ({installation_name})[*]"
        if self._filepath and self._resname and self._restype:
            relpath: Path = self._filepath.relative_to(self._filepath.parent.parent) if self._filepath.parent.parent.name else self._filepath.parent
            title = f"{relpath} - {title}"
        self.setWindowTitle(title)
        self.setWindowModified(len(self._current_data) > 0 and self._current_data != self._revert)

    # File menu operations

    def new(self) -> None:
        """Create a new audio file."""
        self._revert = b""
        self._current_data = b""
        self._filepath = Path(tempfile.gettempdir()) / f"{self._resname}.{self._restype.extension}"
        self._resname = f"untitled_{uuid.uuid4().hex[:8]}"
        self._restype = ResourceType.WAV
        self._update_revert_action(False)
        self.refresh_window_title()
        self.player.stop()

    def open(self) -> None:
        """Open an audio file."""
        filepath_str, _filter = QFileDialog.getOpenFileName(self, "Open Audio File", "", self._open_filter, "")
        if not filepath_str or not str(filepath_str).strip():
            return

        r_filepath = Path(filepath_str)

        if is_capsule_file(r_filepath):
            # Load from module - would need module dialog here
            QMessageBox.information(
                self,
                "Load from Module",
                "Loading from modules is not yet supported in the Audio Player.\nPlease extract the file first.",
            )
            return

        try:
            data: bytes = r_filepath.read_bytes()
            res_ident: ResourceIdentifier = ResourceIdentifier.from_path(r_filepath).validate()
            self.load(r_filepath, res_ident.resname, res_ident.restype, data)
        except Exception as e:  # noqa: BLE001
            RobustLogger().exception(f"Error opening file '{filepath_str}'")
            QMessageBox.critical(
                self,
                "Error Opening File",
                f"Failed to open file:\n{universal_simplify_exception(e)}",
            )

    def save(self) -> None:
        """Save the current audio file."""
        if self._filepath is None or not self._current_data:
            self.save_as()
            return

        try:
            # Save to file
            if is_bif_file(self._filepath) or is_rim_file(self._filepath.name) or is_any_erf_type_file(self._filepath):
                # Save to module - would need module save dialog
                QMessageBox.information(
                    self,
                    "Save to Module",
                    "Saving to modules is not yet supported in the Audio Player.\nPlease use Save As to save to a file.",
                )
                return

            self._filepath.write_bytes(self._current_data)
            self._revert = self._current_data
            self._update_revert_action(True)
            self.refresh_window_title()
            self.setWindowModified(False)

            QMessageBox.information(self, "File Saved", f"Audio file saved to:\n{self._filepath}")
        except Exception as e:  # noqa: BLE001
            RobustLogger().exception(f"Error saving file '{self._filepath}'")
            QMessageBox.critical(
                self,
                "Error Saving File",
                f"Failed to save file:\n{universal_simplify_exception(e)}",
            )

    def save_as(self) -> None:  # noqa: C901
        """Save the audio file with a new name."""
        if not self._current_data:
            QMessageBox.warning(self, "No Data", "No audio data to save.")
            return

        def show_invalid(exc: Exception | None, msg: str) -> None:
            msg_box = QMessageBox(
                QMessageBox.Icon.Critical,
                "Invalid filename/extension",
                f"Check the filename and try again. Could not save!{f'<br><br>{msg}' if msg else ''}",
                parent=self,
            )
            if exc is not None:
                msg_box.setDetailedText(traceback.format_exc())
            msg_box.exec()

        default_path = str(self._filepath) if self._filepath else ""
        filepath_str, _filter = QFileDialog.getSaveFileName(self, "Save Audio File As", default_path, self._save_filter, "")
        if not filepath_str:
            return

        error_msg, exc = "", None
        try:
            identifier = ResourceIdentifier.from_path(filepath_str)
            if identifier.restype.is_invalid:
                show_invalid(None, str(identifier))
                return
        except ValueError as e:
            exc = e
            RobustLogger().exception(f"ValueError raised, assuming invalid filename/extension '{filepath_str}'")
            error_msg = str(universal_simplify_exception(e)).replace("\n", "<br>")
            show_invalid(exc, error_msg)
            return

        if is_capsule_file(filepath_str):
            # Save to module
            if self._resname is None or self._restype is None:
                self._resname = "new"
                self._restype = self._write_supported[0]

            dialog = SaveToModuleDialog(self._resname, self._restype, self._write_supported)
            if dialog.exec():
                self._resname = dialog.resname()
                self._restype = dialog.restype()
                self._filepath = Path(filepath_str)
                # TODO: Implement saving to module
                QMessageBox.information(
                    self,
                    "Save to Module",
                    "Saving to modules is not yet fully implemented in the Audio Player.",
                )
            return

        # Save to regular file
        self._filepath = Path(filepath_str)
        self._resname, self._restype = identifier.unpack()
        self.save()

    def revert(self) -> None:
        """Revert to the last saved version."""
        if not self._revert:
            QMessageBox.warning(self, "No Revert Data", "No saved data to revert to.")
            return

        self._current_data = self._revert
        self.set_media(self._current_data, self._restype)
        self.refresh_window_title()

    def _update_revert_action(self, enabled: bool) -> None:
        """Update the enabled state of the Revert action."""
        menubar: QMenuBar | None = self.menuBar()
        if menubar:
            for action in menubar.actions():
                menu = action.menu()
                if menu:
                    for menu_action in menu.actions():
                        if menu_action.text() == "Revert":
                            menu_action.setEnabled(enabled)  # type: ignore[attr-defined]
                            return

    # Media operations

    def load(
        self,
        filepath: os.PathLike | str,
        resname: str,
        restype: ResourceType,
        data: bytes,
    ) -> None:
        """Load an audio file for playback."""
        from toolset.gui.common.localization import trf  # type: ignore[import-not-found] # pyright: ignore[reportMissingImports]

        self._filepath = Path(filepath)
        self._resname = resname
        self._restype = restype
        self._current_data = data
        self._revert = data

        self.setWindowTitle(trf("{name}.{ext} - Audio Player", name=resname, ext=restype.extension))
        self.set_media(data, restype)
        self._update_revert_action(True)
        self.refresh_window_title()

    def set_media(self, data: bytes, restype: ResourceType) -> None:
        """Set media data for playback, handling multiple audio formats."""
        self.player.stop()
        
        # Clear any existing temporary file
        if self.temp_file and Path(self.temp_file).is_file():
            remove_any(self.temp_file)
        self.temp_file = None

        if not data:
            return

        # Detect audio format from actual data (not just restype, as it might be wrong)
        # This is critical: a file might have ResourceType.WAV but actually contain MP3 data
        suffix = self._detect_audio_extension(data)
        original_data = data  # Preserve original data for all formats
        
        # CRITICAL: Only attempt WAV parsing if the file actually starts with RIFF header
        # This prevents trying to parse MP3/OGG/etc files as WAV, which causes errors
        # Explicitly check for non-WAV formats first
        is_mp3 = len(data) >= 3 and data[:3] == b"ID3"
        is_ogg = len(data) >= 4 and data[:4] == b"OggS"
        is_flac = len(data) >= 4 and data[:4] == b"fLaC"
        is_riff_wav = len(data) >= 4 and data[:4] == b"RIFF"
        
        # Only consider it WAV if it's actually a RIFF file and detection says WAV
        is_wav = is_riff_wav and suffix == ".wav" and not (is_mp3 or is_ogg or is_flac)

        # For WAV files only, try to use PyKotor's WAV parser (for compatibility/validation)
        # For all other formats (MP3, OGG, FLAC, etc.), use Qt's native media player directly
        # This skips WAV parsing entirely for non-WAV files, preventing errors
        if is_wav:
            try:
                from io import BytesIO

                from pykotor.resource.formats.wav.wav_auto import bytes_wav, read_wav  # type: ignore[import-not-found] # pyright: ignore[reportMissingImports]
                wav = read_wav(BytesIO(data))
                data = bytes_wav(wav, ResourceType.INVALID)
                if not data:
                    RobustLogger().warning("Failed to parse WAV file, falling back to direct playback")
                    is_wav = False  # Fall through to direct playback
                    data = original_data  # Restore original data
            except Exception as e:  # noqa: BLE001
                # If WAV parsing fails, fall back to direct playback
                RobustLogger().warning(f"Error parsing WAV file, using direct playback: {e}")
                is_wav = False
                data = original_data  # Restore original data

        if qtpy.QT5:
            if is_wav:
                # Qt5 can use buffer for WAV files
                self.buffer = QBuffer(self)
                self.buffer.setData(data)
                if not self.buffer.open(QIODevice.OpenModeFlag.ReadOnly):
                    RobustLogger().error("Audio player Buffer not ready")
                    return
                from qtpy.QtMultimedia import QMediaContent  # pyright: ignore[reportAttributeAccessIssue]
                self.player.setMedia(QMediaContent(), self.buffer)  # pyright: ignore[reportAttributeAccessIssue]
            else:
                # For non-WAV formats in Qt5, use temporary file
                from qtpy.QtCore import QUrl  # pyright: ignore[reportAttributeAccessIssue]
                from qtpy.QtMultimedia import QMediaContent  # pyright: ignore[reportAttributeAccessIssue]
                
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)  # noqa: SIM115
                temp_file.write(original_data)  # Use original data, not potentially modified data
                temp_file.flush()
                temp_file.close()
                self.temp_file = temp_file.name
                
                temp_file_path = self.temp_file
                url = QUrl.fromLocalFile(temp_file_path)  # pyright: ignore[reportAttributeAccessIssue]
                self.player.setMedia(QMediaContent(url))  # pyright: ignore[reportAttributeAccessIssue]
                self.player.mediaStatusChanged.connect(lambda status, file_name=temp_file_path: self.remove_temp_audio_file(status, file_name))
            
            QtCore.QTimer.singleShot(0, self.player.play)
        elif qtpy.QT6:
            from qtpy.QtMultimedia import QAudioOutput, QUrl  # pyright: ignore[reportAttributeAccessIssue]

            # Qt6 requires a file for most formats, especially MP3
            # Use original_data for non-WAV, processed data for WAV
            file_data = data if is_wav else original_data
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)  # noqa: SIM115
            temp_file.write(file_data)  # pyright: ignore[reportArgumentType, reportCallIssue]
            temp_file.flush()
            temp_file.close()
            self.temp_file = temp_file.name

            # Set up player
            player: PyQt6MediaPlayer | PySide6MediaPlayer = cast("Any", self.player)
            audio_output = QAudioOutput(self)  # type: ignore[call-overload]
            audio_output.setVolume(1)
            player.setAudioOutput(audio_output)
            
            # Use file source (more reliable than buffer for all formats)
            temp_file_path = self.temp_file
            url = QUrl.fromLocalFile(temp_file_path)  # pyright: ignore[reportAttributeAccessIssue]
            player.setSource(url)  # type: ignore[arg-type]
            player.mediaStatusChanged.connect(lambda status, file_name=temp_file_path: self.remove_temp_audio_file(status, file_name))
            player.play()

    def remove_temp_audio_file(
        self,
        status: QMediaPlayer.MediaStatus,
        filePathStr: str,
    ) -> None:
        """Remove temporary audio file when playback ends."""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            try:
                self.player.stop()
                QTimer.singleShot(33, lambda: remove_any(filePathStr))
            except OSError:
                RobustLogger().exception(f"Error removing temporary file {filePathStr}")

    # Player controls

    def handle_error(self, *args, **kwargs) -> None:
        """Handle media player errors."""
        RobustLogger().warning(f"Media player error: {args}, {kwargs}")
        # Don't close on error, just log it

    def duration_changed(self, duration: int) -> None:
        """Handle duration changes."""
        total_time: str = time.strftime("%H:%M:%S", time.gmtime(duration // 1000))
        self.ui.totalTimeLabel.setText(total_time)
        self.ui.timeSlider.setMaximum(duration)

    def positionChanged(self, position: int) -> None:
        """Handle position changes."""
        current_time: str = time.strftime("%H:%M:%S", time.gmtime(position // 1000))
        self.ui.currentTimeLabel.setText(current_time)

        # sometimes QMediaPlayer does not accurately calculate the duration of the audio
        if position > self.ui.timeSlider.maximum():
            self.duration_changed(position)

        self.ui.timeSlider.setValue(position)

    def changePosition(self) -> None:
        """Change playback position."""
        position: int = self.ui.timeSlider.value()
        self.player.setPosition(position)

    def closeEvent(self, event: QCloseEvent | None = None) -> None:
        """Handle window close event."""
        self.player.stop()
        
        # Clean up temp file
        if self.temp_file and Path(self.temp_file).is_file():
            remove_any(self.temp_file)

        if event is not None:
            event.accept()
            super().closeEvent(event)
