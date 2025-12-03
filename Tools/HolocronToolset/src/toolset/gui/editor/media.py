from __future__ import annotations

import tempfile

from typing import TYPE_CHECKING, Any, cast

import qtpy

from loggerplus import RobustLogger
from qtpy.QtCore import QBuffer, QIODevice, QTimer, QUrl
from qtpy.QtMultimedia import QMediaPlayer

from pykotor.extract.installation import SearchLocation
from utility.system.os_helper import remove_any

if TYPE_CHECKING:
    import os

    from PyQt6.QtMultimedia import QMediaPlayer as PyQt6MediaPlayer  # pyright: ignore[reportMissingImports, reportAttributeAccessIssue]
    from PySide6.QtMultimedia import QMediaPlayer as PySide6MediaPlayer  # pyright: ignore[reportMissingImports, reportAttributeAccessIssue]

    from toolset.gui.editor.base import Editor


def _detect_audio_extension(data: bytes) -> str:
    """Detect audio format from file magic bytes.
    
    Returns appropriate file extension for media player compatibility.
    
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
    
    # Default to wav
    return ".wav"


class EditorMedia:
    def __init__(
        self,
        editor: Editor,
    ):
        self.editor: Editor = editor

    def play_byte_source_media(
        self,
        data: bytes | None,
    ) -> bool:
        if not data:
            self.editor.blink_window()
            return False
        if qtpy.QT5:
            from qtpy.QtMultimedia import QMediaContent  # pyright: ignore[reportAttributeAccessIssue]

            self.editor.media_player.buffer = buffer = QBuffer(self.editor)
            buffer.setData(data)
            buffer.open(QIODevice.OpenModeFlag.ReadOnly)
            self.editor.media_player.player.setMedia(QMediaContent(), buffer)  # pyright: ignore[reportAttributeAccessIssue]
            QTimer.singleShot(0, self.editor.media_player.player.play)

        elif qtpy.QT6:
            from qtpy.QtMultimedia import QAudioOutput

            # Detect audio format for proper file extension
            # Reference: vendor/KotOR.js/src/audio/AudioFile.ts:348-354
            suffix = _detect_audio_extension(data)
            
            temp_file: tempfile._TemporaryFileWrapper[bytes] = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)  # noqa: SIM115
            temp_file.write(data)  # pyright: ignore[reportArgumentType, reportCallIssue]
            temp_file.flush()
            temp_file.seek(0)
            temp_file.close()

            player: PyQt6MediaPlayer | PySide6MediaPlayer = cast("Any", self.editor.media_player.player)
            audio_output = QAudioOutput(self.editor)  # pyright: ignore[reportCallIssue, reportArgumentType]
            audio_output.setVolume(1)
            player.setAudioOutput(audio_output)  # pyright: ignore[reportArgumentType]
            player.setSource(QUrl.fromLocalFile(temp_file.name))  # pyright: ignore[reportArgumentType]
            player.mediaStatusChanged.connect(lambda status, file_name=temp_file.name: self.remove_temp_audio_file(status, file_name))
            player.play()
        return True

    def play_sound(
        self,
        resname: str,
        order: list[SearchLocation] | None = None,
    ) -> bool:
        """Plays a sound resource."""
        if not resname or not resname.strip() or self.editor._installation is None:  # noqa: SLF001
            self.editor.blink_window(sound=False)
            return False

        self.editor.media_player.player.stop()

        data: bytes | None = self.editor._installation.sound(  # noqa: SLF001
            resname,
            order
            if order is not None
            else [
                SearchLocation.MUSIC,
                SearchLocation.VOICE,
                SearchLocation.SOUND,
                SearchLocation.OVERRIDE,
                SearchLocation.CHITIN,
            ],
        )
        if not data:
            self.editor.blink_window(sound=False)
        return self.play_byte_source_media(data)

    def remove_temp_audio_file(
        self,
        status: QMediaPlayer.MediaStatus,
        file_path: os.PathLike | str,
    ):
        if status != QMediaPlayer.MediaStatus.EndOfMedia:
            return
        try:
            self.editor.media_player.player.stop()
            QTimer.singleShot(33, lambda: remove_any(file_path))
        except OSError:
            RobustLogger().exception(f"Error removing temporary file '{file_path}'")
