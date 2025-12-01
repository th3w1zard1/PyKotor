"""Standard WAV binary reader/writer (non-obfuscated output).

This module provides IO for standard RIFF/WAVE format output without KotOR obfuscation.
Use this for saving WAV files that can be played by standard media players.

Note: For reading, always use WAVBinaryReader which handles deobfuscation.
This module's writer produces clean RIFF/WAVE output regardless of input format.

References:
----------
    vendor/reone/src/libs/audio/format/wavreader.cpp - WAV reading
    vendor/xoreos/src/sound/decoders/wave.cpp - WAV structure
    Standard RIFF/WAVE format specification
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.wav.wav_data import (
    WAV,
    AudioFormat,
)
from pykotor.resource.type import ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.type import TARGET_TYPES


class WAVStandardWriter(ResourceWriter):
    """Handles writing standard (non-obfuscated) WAV binary data.
    
    This writer produces clean RIFF/WAVE format without KotOR obfuscation headers.
    For MP3 audio data, writes the raw MP3 bytes directly (not wrapped in WAV).
    
    Use this writer when you need playable audio for:
    - Media players
    - Qt audio playback
    - Audio editing software
    """

    def __init__(
        self,
        wav: WAV,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self.wav: WAV = wav

    @autoclose
    def write(self, *, auto_close: bool = True) -> None:  # noqa: FBT001, FBT002, ARG002  # pyright: ignore[reportUnusedParameters]
        """Write standard WAV data to target (no obfuscation).

        Processing Logic:
            - For MP3 audio format: Write raw MP3 bytes directly
            - For WAVE audio format: Write proper RIFF/WAVE structure
        """
        # For MP3 format, write raw MP3 bytes
        # Media players can handle raw MP3 without WAV wrapper
        if self.wav.audio_format == AudioFormat.MP3:
            self._writer.write_bytes(self.wav.data)
            return
        
        # Calculate sizes for RIFF header
        data_size = len(self.wav.data)
        fmt_chunk_size = 16
        # RIFF size = 4 (WAVE) + 8 (fmt header) + fmt_chunk_size + 8 (data header) + data_size
        file_size = 4 + 8 + fmt_chunk_size + 8 + data_size

        # Write RIFF header
        self._writer.write_bytes(b"RIFF")
        self._writer.write_uint32(file_size)
        self._writer.write_bytes(b"WAVE")

        # Write format chunk
        self._writer.write_bytes(b"fmt ")
        self._writer.write_uint32(fmt_chunk_size)
        self._writer.write_uint16(self.wav.encoding if isinstance(self.wav.encoding, int) else self.wav.encoding)
        self._writer.write_uint16(self.wav.channels)
        self._writer.write_uint32(self.wav.sample_rate)
        bytes_per_sec = self.wav.bytes_per_sec or (self.wav.sample_rate * self.wav.block_align)
        self._writer.write_uint32(bytes_per_sec)
        self._writer.write_uint16(self.wav.block_align)
        self._writer.write_uint16(self.wav.bits_per_sample)

        # Write data chunk
        self._writer.write_bytes(b"data")
        self._writer.write_uint32(data_size)
        self._writer.write_bytes(self.wav.data)
