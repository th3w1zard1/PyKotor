"""WAV/Audio Editor for the Holocron Toolset.

This editor provides comprehensive audio file handling including:
- WAV, MP3, OGG, FLAC format support
- Playback controls (play, pause, stop, seek)
- File management (new, open, save, save as, revert)
- Format detection based on magic bytes
- Qt5/Qt6 compatibility

The editor inherits from the base Editor class and uses its built-in
MediaPlayerWidget for audio playback, while providing its own UI controls.
"""
from __future__ import annotations

import tempfile
import time

from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import qtpy

from loggerplus import RobustLogger
from qtpy.QtCore import QBuffer, QIODevice
from qtpy.QtMultimedia import QMediaPlayer

from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor
from utility.system.os_helper import remove_any

if TYPE_CHECKING:
    import os

    from PyQt6.QtMultimedia import QMediaPlayer as PyQt6MediaPlayer  # pyright: ignore[reportMissingImports]
    from PySide6.QtMultimedia import QMediaPlayer as PySide6MediaPlayer  # pyright: ignore[reportMissingImports]
    from qtpy.QtGui import QCloseEvent
    from qtpy.QtWidgets import QWidget

    from toolset.data.installation import HTInstallation


class WAVEditor(Editor):
    """Audio editor for WAV and other audio formats.

    Supports WAV, MP3, OGG, FLAC audio files with full playback
    controls and file management capabilities.

    The editor uses the base Editor class's MediaPlayerWidget internally
    but provides its own UI controls for a dedicated audio editing experience.
    """

    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation | None = None,
    ):
        """Initialize the audio editor.

        Args:
            parent: Parent widget
            installation: HTInstallation object for game context
        """
        # Support WAV and MP3 formats
        supported: list[ResourceType] = [ResourceType.WAV, ResourceType.MP3]
        super().__init__(parent, "Audio Editor", "audio", supported, supported, installation)

        # Ensure mediaPlayer exists - create it if base class didn't
        # The base Editor class should create this, but if it doesn't, we create it
        if not hasattr(self, 'mediaPlayer'):
            from toolset.gui.widgets.media_player_widget import MediaPlayerWidget
            self.mediaPlayer = MediaPlayerWidget(self)

        # Audio-specific state
        self._audio_data: bytes = b""
        self._temp_file: str | None = None
        self._detected_format: str = "Unknown"

        # Import and setup UI
        from toolset.uic.qtpy.editors.wav import Ui_MainWindow  # pyright: ignore[reportMissingImports]

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Hide the base MediaPlayerWidget - we use our own UI controls
        self.mediaPlayer.hide()  # pyright: ignore[reportAttributeAccessIssue]

        self._setup_menus()
        self._setup_signals()
        self._setup_player_signals()

        self.new()
        self.setMinimumSize(350, 150)

    def _setup_signals(self) -> None:
        """Set up UI control signals."""
        self.ui.playButton.clicked.connect(self._on_play)
        self.ui.pauseButton.clicked.connect(self._on_pause)
        self.ui.stopButton.clicked.connect(self._on_stop)
        self.ui.timeSlider.sliderReleased.connect(self._on_seek)
        self.ui.timeSlider.sliderPressed.connect(self._on_slider_pressed)

    def _setup_player_signals(self) -> None:
        """Set up media player signals."""
        player = self.mediaPlayer.player  # pyright: ignore[reportAttributeAccessIssue]
        
        # Disconnect any existing connections to avoid duplicates
        try:
            player.durationChanged.disconnect()
        except TypeError:
            pass  # No connections to disconnect
        try:
            player.positionChanged.disconnect()
        except TypeError:
            pass
        try:
            player.mediaStatusChanged.disconnect()
        except TypeError:
            pass
        if qtpy.QT5:
            try:
                player.error.disconnect()  # type: ignore[attr-defined]
            except TypeError:
                pass  # No connections to disconnect
        else:
            try:
                player.errorOccurred.disconnect()  # type: ignore[attr-defined]
            except TypeError:
                pass  # No connections to disconnect
        
        # Connect signals
        player.durationChanged.connect(self._on_duration_changed)
        player.positionChanged.connect(self._on_position_changed)
        player.mediaStatusChanged.connect(self._on_media_status_changed)

        # Error handling differs between Qt5 and Qt6
        if qtpy.QT5:
            player.error.connect(self._on_player_error)  # type: ignore[attr-defined]
        else:
            player.errorOccurred.connect(self._on_player_error)  # type: ignore[attr-defined]

    # =========================================================================
    # Format Detection
    # =========================================================================

    @staticmethod
    def detect_audio_format(data: bytes | bytearray) -> str:
        """Detect audio format from file magic bytes.

        Returns appropriate file extension for media player compatibility.

        Args:
            data: Raw audio file bytes

        Returns:
            File extension including dot (e.g., ".wav", ".mp3")

        References:
            vendor/KotOR.js/src/audio/AudioFile.ts:9-16 - Magic byte constants
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

    @staticmethod
    def get_format_name(extension: str) -> str:
        """Get human-readable format name from extension.

        Args:
            extension: File extension including dot

        Returns:
            Human-readable format name
        """
        format_names = {
            ".wav": "WAV (RIFF)",
            ".mp3": "MP3",
            ".ogg": "OGG Vorbis",
            ".flac": "FLAC",
        }
        return format_names.get(extension.lower(), "Unknown")

    # =========================================================================
    # Editor Interface Implementation
    # =========================================================================

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes | bytearray,
    ) -> None:
        """Load an audio file for editing and playback.

        Args:
            filepath: Path to the audio file
            resref: Resource reference name
            restype: Resource type
            data: Raw audio data bytes
        """
        super().load(filepath, resref, restype, data)

        data_bytes = bytes(data) if isinstance(data, bytearray) else data
        self._audio_data = data_bytes
        self._detected_format = self.get_format_name(self.detect_audio_format(data_bytes))

        # Update format label
        self.ui.formatLabel.setText(f"Format: {self._detected_format}")

        # Set up media for playback
        self._set_media(data_bytes)

    def build(self) -> tuple[bytes, bytes]:
        """Build/serialize the current audio data.

        Returns:
            Tuple of (audio_data, empty_bytes) for consistency with Editor interface
        """
        return self._audio_data, b""

    def new(self) -> None:
        """Create a new empty audio file."""
        super().new()

        self._audio_data = b""
        self._detected_format = "Unknown"
        self._cleanup_temp_file()

        # Reset UI
        self.ui.currentTimeLabel.setText("00:00:00")
        self.ui.totalTimeLabel.setText("00:00:00")
        self.ui.timeSlider.setValue(0)
        self.ui.timeSlider.setMaximum(0)
        self.ui.formatLabel.setText("Format: -")

        # Stop any playback
        self.mediaPlayer.player.stop()  # pyright: ignore[reportAttributeAccessIssue]

    # =========================================================================
    # Media Playback
    # =========================================================================

    def _set_media(self, data: bytes) -> None:
        """Set up media data for playback.

        Handles multiple audio formats and Qt5/Qt6 compatibility.

        Args:
            data: Raw audio data bytes
        """
        player = self.mediaPlayer.player  # pyright: ignore[reportAttributeAccessIssue]
        
        # Stop player and clear media to prevent signal firing during cleanup
        player.stop()
        
        # Clear media to release any existing resources
        try:
            if qtpy.QT5:
                from qtpy.QtMultimedia import QMediaContent  # pyright: ignore[reportAttributeAccessIssue]
                player.setMedia(QMediaContent())  # pyright: ignore[reportAttributeAccessIssue]
            else:
                player.setSource(None)  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            pass  # Ignore errors when clearing media
        
        # Cleanup temp files synchronously
        self._cleanup_temp_file()

        if not data:
            return

        # Detect format from actual data
        suffix = self.detect_audio_format(data)
        original_data = data

        # Check for specific formats by magic bytes
        is_mp3 = len(data) >= 3 and data[:3] == b"ID3"
        is_ogg = len(data) >= 4 and data[:4] == b"OggS"
        is_flac = len(data) >= 4 and data[:4] == b"fLaC"
        is_riff_wav = len(data) >= 4 and data[:4] == b"RIFF"

        # Only attempt WAV parsing if it's actually a RIFF WAV file
        is_wav = is_riff_wav and suffix == ".wav" and not (is_mp3 or is_ogg or is_flac)

        # For WAV files, try PyKotor's WAV parser for validation/compatibility
        if is_wav:
            try:
                from io import BytesIO

                from pykotor.resource.formats.wav.wav_auto import bytes_wav, read_wav as read_wav_auto

                wav = read_wav_auto(BytesIO(data))
                data = bytes_wav(wav, ResourceType.INVALID)
                if not data:
                    RobustLogger().warning("Failed to parse WAV file, falling back to direct playback")
                    is_wav = False
                    data = original_data
            except Exception as e:  # noqa: BLE001
                RobustLogger().warning(f"Error parsing WAV file, using direct playback: {e}")
                is_wav = False
                data = original_data

        # Set up playback based on Qt version
        if qtpy.QT5:
            self._setup_qt5_playback(data, original_data, suffix, is_wav)
        elif qtpy.QT6:
            self._setup_qt6_playback(data, original_data, suffix, is_wav)

    def _get_media_player_buffer(self) -> QBuffer:
        """Get the media player's buffer, creating if necessary."""
        return self.mediaPlayer.buffer  # pyright: ignore[reportAttributeAccessIssue]

    def _set_media_player_buffer(self, buffer: QBuffer) -> None:
        """Set the media player's buffer."""
        self.mediaPlayer.buffer = buffer  # pyright: ignore[reportAttributeAccessIssue]

    def _setup_qt5_playback(
        self,
        data: bytes,
        original_data: bytes,
        suffix: str,
        is_wav: bool,
    ) -> None:
        """Set up playback for Qt5.

        Args:
            data: Processed audio data
            original_data: Original unprocessed data
            suffix: File extension
            is_wav: Whether the file is WAV format
        """
        player = self.mediaPlayer.player  # pyright: ignore[reportAttributeAccessIssue]

        if is_wav:
            # Qt5 can use buffer for WAV files
            buffer = QBuffer(self)
            self._set_media_player_buffer(buffer)
            buffer.setData(data)
            if not buffer.open(QIODevice.OpenModeFlag.ReadOnly):
                RobustLogger().error("Audio player buffer not ready")
                return
            from qtpy.QtMultimedia import QMediaContent  # pyright: ignore[reportAttributeAccessIssue]

            player.setMedia(QMediaContent(), buffer)  # pyright: ignore[reportAttributeAccessIssue]
        else:
            # For non-WAV formats in Qt5, use temporary file
            from qtpy.QtCore import QUrl
            from qtpy.QtMultimedia import QMediaContent  # pyright: ignore[reportAttributeAccessIssue]

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)  # noqa: SIM115
            temp_file.write(original_data)
            temp_file.flush()
            temp_file.close()
            self._temp_file = temp_file.name

            url = QUrl.fromLocalFile(self._temp_file)
            player.setMedia(QMediaContent(url))  # pyright: ignore[reportAttributeAccessIssue]

    def _setup_qt6_playback(
        self,
        data: bytes,
        original_data: bytes,
        suffix: str,
        is_wav: bool,
    ) -> None:
        """Set up playback for Qt6.

        Args:
            data: Processed audio data
            original_data: Original unprocessed data
            suffix: File extension
            is_wav: Whether the file is WAV format
        """
        from qtpy.QtCore import QUrl
        from qtpy.QtMultimedia import QAudioOutput

        player: PyQt6MediaPlayer | PySide6MediaPlayer = cast("Any", self.mediaPlayer.player)  # pyright: ignore[reportAttributeAccessIssue]

        # Qt6 requires a file for most formats
        file_data = data if is_wav else original_data
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)  # noqa: SIM115
        temp_file.write(file_data)
        temp_file.flush()
        temp_file.close()
        self._temp_file = temp_file.name

        # Set up audio output
        audio_output = QAudioOutput(self)  # type: ignore[call-overload]
        audio_output.setVolume(1.0)
        player.setAudioOutput(audio_output)

        # Set source
        url = QUrl.fromLocalFile(self._temp_file)
        player.setSource(url)  # type: ignore[arg-type]

    def _cleanup_temp_file(self) -> None:
        """Clean up any temporary audio file."""
        if self._temp_file and Path(self._temp_file).is_file():
            try:
                remove_any(self._temp_file)
            except OSError:
                RobustLogger().exception(f"Error removing temporary file {self._temp_file}")
        self._temp_file = None

    # =========================================================================
    # Playback Controls
    # =========================================================================

    def _on_play(self) -> None:
        """Handle play button click."""
        self.mediaPlayer.player.play()  # pyright: ignore[reportAttributeAccessIssue]

    def _on_pause(self) -> None:
        """Handle pause button click."""
        self.mediaPlayer.player.pause()  # pyright: ignore[reportAttributeAccessIssue]

    def _on_stop(self) -> None:
        """Handle stop button click."""
        self.mediaPlayer.player.stop()  # pyright: ignore[reportAttributeAccessIssue]

    def _on_seek(self) -> None:
        """Handle seek bar release."""
        position = self.ui.timeSlider.value()
        self.mediaPlayer.player.setPosition(position)  # pyright: ignore[reportAttributeAccessIssue]

    def _on_slider_pressed(self) -> None:
        """Handle slider press (pause during drag)."""
        # Optional: pause during drag for smoother seeking
        pass

    def _on_duration_changed(self, duration: int) -> None:
        """Handle duration change from media player.

        Args:
            duration: Duration in milliseconds
        """
        # Clamp duration to valid range for QSlider (int32 max) and ensure non-negative
        max_slider_value = 2147483647
        duration = max(0, min(duration, max_slider_value))
        
        # Format time only if duration is valid
        if duration > 0:
            try:
                total_time = time.strftime("%H:%M:%S", time.gmtime(duration // 1000))
            except (OSError, ValueError, OverflowError):
                total_time = "00:00:00"
        else:
            total_time = "00:00:00"
            
        self.ui.totalTimeLabel.setText(total_time)
        # Set minimum to 0 to ensure valid range even for zero duration
        self.ui.timeSlider.setMinimum(0)
        self.ui.timeSlider.setMaximum(duration)

    def _on_position_changed(self, position: int) -> None:
        """Handle position change from media player.

        Args:
            position: Current position in milliseconds
        """
        # Clamp position to valid range and ensure non-negative
        position = max(0, min(position, 2147483647))
        
        # Only format time if position is valid
        if position > 0:
            try:
                current_time = time.strftime("%H:%M:%S", time.gmtime(position // 1000))
            except (OSError, ValueError, OverflowError):
                # Invalid time value, use default
                current_time = "00:00:00"
        else:
            current_time = "00:00:00"
        
        self.ui.currentTimeLabel.setText(current_time)

        # Fix for inaccurate duration calculation (but clamp to avoid overflow)
        if position > self.ui.timeSlider.maximum():
            clamped_position = max(0, min(position, 2147483647))
            self._on_duration_changed(clamped_position)

        # Update slider if not being dragged
        if not self.ui.timeSlider.isSliderDown():
            self.ui.timeSlider.setValue(position)

    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        """Handle media status changes.

        Args:
            status: New media status
        """
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            # Reset to beginning when playback ends
            self.ui.timeSlider.setValue(0)
            self.ui.currentTimeLabel.setText("00:00:00")

    def _on_player_error(self, *args: Any, **kwargs: Any) -> None:
        """Handle media player errors."""
        RobustLogger().warning(f"Media player error: {args}, {kwargs}")

    # =========================================================================
    # Cleanup
    # =========================================================================

    def closeEvent(self, a0: QCloseEvent | None) -> None:  # noqa: N802
        """Handle window close event.

        Args:
            a0: Close event
        """
        self.mediaPlayer.player.stop()  # pyright: ignore[reportAttributeAccessIssue]
        self._cleanup_temp_file()
        if a0 is not None:
            super().closeEvent(a0)

