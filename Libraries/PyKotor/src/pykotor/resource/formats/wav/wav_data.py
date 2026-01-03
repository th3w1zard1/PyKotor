"""This module handles classes relating to editing WAV files.

WAV files in KotOR can be voice-over (VO) or sound effects (SFX) with various encodings.

KotOR Audio Format Reference:
----------------------------
    - SFX files (streammusic): Have 0xFFF360C4 header, skip 470 bytes, then RIFF/WAVE
    - VO files (streamvoice): Usually standard RIFF/WAVE with PCM or IMA ADPCM
    - Music with MP3: RIFF header with size=50, skip 58 bytes, then MP3 data
    
References:
----------
    vendor/reone/src/libs/audio/format/wavreader.cpp:30-56 - WAV header detection
    vendor/KotOR.js/src/audio/AudioFile.ts:9-162 - Audio format detection & deobfuscation
    vendor/xoreos/src/sound/decoders/wave.cpp - Standard WAV parsing
    vendor/SithCodec - Audio codec for KotOR WAV handling
    vendor/SWKotOR-Audio-Encoder - Audio encoding tools
"""

from __future__ import annotations

from enum import IntEnum

from pykotor.resource.type import ResourceType


class WaveEncoding(IntEnum):
    """Wave encoding types used by Bioware.
    
    References:
    ----------
        vendor/KotOR.js/src/enums/audio/AudioFileWaveEncoding.ts
        vendor/xoreos/src/sound/decoders/wave_types.h
    """
    PCM = 0x01           # Linear PCM (uncompressed)
    MS_ADPCM = 0x02      # Microsoft ADPCM
    ALAW = 0x06          # A-Law companded
    MULAW = 0x07         # μ-Law companded
    IMA_ADPCM = 0x11     # IMA ADPCM (also known as DVI ADPCM)
    MP3 = 0x55           # MPEG Layer 3


class AudioFormat(IntEnum):
    """Audio format types for the WAV wrapper."""
    WAVE = 1       # Standard RIFF/WAVE format
    MP3 = 2        # MP3 data (possibly wrapped in WAV)
    UNKNOWN = 0    # Unknown format


class WAVType(IntEnum):
    """The type of WAV file for KotOR obfuscation purposes."""
    VO = 1      # Voice over WAV (streamvoice, streamwaves)
    SFX = 2     # Sound effects WAV (streammusic/sounds with 470-byte header)


class WAV:
    """Represents a WAV file.

    Attributes:
    ----------
        wav_type: The WAV type (VO or SFX)
        audio_format: The actual audio format (WAVE or MP3)
        encoding: The wave encoding type (for WAVE format)
        channels: Number of audio channels
        sample_rate: Audio sample rate
        bits_per_sample: Bits per audio sample
        block_align: Block alignment
        bytes_per_sec: Bytes per second
        data: The raw audio data (PCM samples for WAVE, raw bytes for MP3)
        
    Note:
    ----
        When audio_format is MP3, the data contains raw MP3 bytes that should be
        played directly without WAV parsing.
    """

    BINARY_TYPE = ResourceType.WAV

    def __init__(
        self,
        wav_type: WAVType = WAVType.VO,
        audio_format: AudioFormat = AudioFormat.WAVE,
        encoding: WaveEncoding | int = WaveEncoding.PCM,
        channels: int = 1,
        sample_rate: int = 44100,
        bits_per_sample: int = 16,
        bytes_per_sec: int = 0,
        block_align: int = 0,
        data: bytes | None = None,
    ):
        self.wav_type: WAVType = wav_type
        self.audio_format: AudioFormat = audio_format
        # Store encoding as int to allow unsupported values
        self.encoding: int = int(encoding) if isinstance(encoding, WaveEncoding) else encoding
        self.channels: int = channels
        self.sample_rate: int = sample_rate
        self.bits_per_sample: int = bits_per_sample
        self.bytes_per_sec: int = bytes_per_sec
        self.block_align: int = block_align or (channels * bits_per_sample // 8)
        self.data: bytes = data if data is not None else b""

    def get_encoding_enum(self) -> WaveEncoding | None:
        """Get the encoding as WaveEncoding enum, or None if unsupported."""
        try:
            return WaveEncoding(self.encoding)
        except ValueError:
            return None

    def is_pcm(self) -> bool:
        """Check if the audio is PCM encoded."""
        return self.encoding == WaveEncoding.PCM

    def is_adpcm(self) -> bool:
        """Check if the audio is IMA ADPCM encoded."""
        return self.encoding == WaveEncoding.IMA_ADPCM

    def is_mp3(self) -> bool:
        """Check if the audio is MP3 format."""
        return self.audio_format == AudioFormat.MP3 or self.encoding == WaveEncoding.MP3

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, WAV):
            return NotImplemented
        return (
            self.wav_type == other.wav_type
            and self.audio_format == other.audio_format
            and self.encoding == other.encoding
            and self.channels == other.channels
            and self.sample_rate == other.sample_rate
            and self.bits_per_sample == other.bits_per_sample
            and self.block_align == other.block_align
            and self.data == other.data
        )

    def __hash__(self):
        return hash((self.wav_type, self.audio_format, self.encoding, self.channels, 
                     self.sample_rate, self.bits_per_sample, self.block_align, self.data))
