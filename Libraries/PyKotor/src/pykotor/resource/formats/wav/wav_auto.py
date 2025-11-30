"""Auto-detect and handle KotOR WAV files.

This module provides the public API for reading and writing WAV files.
It automatically handles KotOR's various audio obfuscation formats.

Usage:
------
    # Reading (automatic deobfuscation):
    wav = read_wav("path/to/file.wav")
    
    # Writing (with obfuscation for game compatibility):
    write_wav(wav, "output.wav", ResourceType.WAV)
    
    # Writing (clean for media players):
    write_wav(wav, "output.wav", ResourceType.WAV_DEOB)
    
    # Get playable bytes (for Qt media player, etc.):
    playable_bytes = get_playable_bytes(wav)
    
References:
----------
    vendor/KotOR.js/src/audio/AudioFile.ts:164-205 - getPlayableByteStream()
    vendor/reone/src/libs/audio/format/wavreader.cpp - Format detection
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.wav.io_wav import WAVBinaryReader, WAVBinaryWriter
from pykotor.resource.formats.wav.io_wav_standard import WAVStandardWriter
from pykotor.resource.formats.wav.wav_data import AudioFormat
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.wav.wav_data import WAV
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


def read_wav(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> WAV:
    """Returns a WAV instance from the source with automatic deobfuscation.

    The function automatically detects and removes obfuscation headers if present.
    The returned WAV object contains clean, deobfuscated data.

    Supported formats:
        - Standard RIFF/WAVE (streamvoice, dialog audio)
        - SFX with 470-byte header (streammusic, sound effects)
        - MP3-in-WAV (some music files with RIFF size == 50)

    Args:
        source: The source of the data (file path, bytes, or file-like object)
        offset: The byte offset of the file inside the data
        size: Number of bytes to read. If not specified, uses the whole stream.

    Raises:
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory.
        PermissionError: If the file could not be accessed.
        ValueError: If the file was corrupted or format unrecognized.

    Returns:
        A WAV instance (automatically deobfuscated).
    """
    return WAVBinaryReader(source, offset, size or 0).load()


def write_wav(
    wav: WAV,
    target: TARGET_TYPES,
    file_format: ResourceType = ResourceType.WAV,
):
    """Writes the WAV data to the target location.

    If file_format is ResourceType.WAV, the data will be obfuscated based on
    the WAV's type (SFX adds header, VO is unchanged) for game compatibility.
    
    If file_format is ResourceType.WAV_DEOB, writes clean RIFF/WAVE format
    playable by standard media players.

    Args:
        wav: The WAV file being written.
        target: The location to write the data to.
        file_format: WAV for game format, WAV_DEOB for clean playable format.

    Raises:
        IsADirectoryError: If the specified path is a directory.
        PermissionError: If the file could not be written.
    """
    if file_format is ResourceType.WAV:
        WAVBinaryWriter(wav, target).write()
    else:
        WAVStandardWriter(wav, target).write()


def bytes_wav(
    wav: WAV,
    file_format: ResourceType = ResourceType.WAV,
) -> bytes:
    """Returns the WAV data as a bytes object.

    If file_format is ResourceType.WAV, returns obfuscated format for game use.
    If file_format is ResourceType.WAV_DEOB, returns clean playable format.

    Args:
        wav: The target WAV object.
        file_format: WAV for game format, WAV_DEOB for clean playable format.

    Returns:
        The WAV data as bytes.
    """
    data = bytearray()
    write_wav(wav, data, file_format)
    return bytes(data)


def get_playable_bytes(wav: WAV) -> bytes:
    """Returns playable audio bytes for media player use.
    
    This is the preferred method for getting audio data that can be played
    by Qt's QMediaPlayer or other standard audio players.
    
    For MP3 format: Returns raw MP3 bytes
    For WAVE format: Returns clean RIFF/WAVE structure
    
    Args:
        wav: The WAV object to convert
        
    Returns:
        Audio bytes playable by standard media players
        
    References:
        vendor/KotOR.js/src/audio/AudioFile.ts:164-205 - getPlayableByteStream()
    """
    return bytes_wav(wav, ResourceType.WAV_DEOB)


def detect_audio_type(wav: WAV) -> str:
    """Returns the file extension appropriate for this audio's actual format.
    
    Useful for saving to temp files with correct extension.
    
    Args:
        wav: The WAV object to check
        
    Returns:
        "mp3" for MP3 format, "wav" for WAVE format
        
    References:
        vendor/KotOR.js/src/audio/AudioFile.ts:348-354 - getExportExtension()
    """
    if wav.audio_format == AudioFormat.MP3:
        return "mp3"
    return "wav"
