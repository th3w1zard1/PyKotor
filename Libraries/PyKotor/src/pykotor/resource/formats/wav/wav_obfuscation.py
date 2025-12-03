"""WAV obfuscation utilities for KotOR audio files.

KotOR audio files have various obfuscation formats that need to be handled:

1. **SFX Format** (streammusic, some sounds):
   - Header: 0xFF 0xF3 0x60 0xC4 (little-endian: 0xC460F3FF = 3294888959)
   - Skip 470 bytes (0x1DA), then standard RIFF/WAVE follows
   
2. **MP3-in-WAV Format** (some music):
   - Header: RIFF with riffSize == 50
   - Skip 58 bytes, then raw MP3 data follows
   
3. **Standard WAV** (streamvoice, most dialog):
   - Standard RIFF/WAVE format, no obfuscation

**Internal Module**: The functions in this module are internal implementation details
and should only be called from within the wav folder (e.g., `io_wav.py`).
External code should use the public API in `wav_auto.py`.

References:
----------
    vendor/reone/src/libs/audio/format/wavreader.cpp:30-38
        - Shows magic "\xff\xf3\x60\xc4" detection and seek to 0x1DA
    vendor/KotOR.js/src/audio/AudioFile.ts:9-162
        - fakeHeaderTest = [0xFF, 0xF3, 0x60, 0xC4] → skip 470 bytes
        - riffSize == 50 → skip 58 bytes → MP3
    vendor/SithCodec/src/codec.cpp (Audio codec implementation)
    vendor/SWKotOR-Audio-Encoder/ (Full audio encoder/decoder)
"""

from __future__ import annotations

import struct

from enum import IntEnum


class DeobfuscationResult(IntEnum):
    """Result type from deobfuscation indicating what format was detected."""
    STANDARD = 0       # Standard RIFF/WAVE, no header removed
    SFX_HEADER = 1     # SFX 470-byte header removed, data is WAVE
    MP3_IN_WAV = 2     # MP3-in-WAV 58-byte header removed, data is MP3


# Magic numbers for detection
# vendor/reone/src/libs/audio/format/wavreader.cpp:34
# "\xff\xf3\x60\xc4" as bytes (0xFFF360C4 big-endian, 0xC460F3FF little-endian)
SFX_MAGIC_BYTES = b"\xff\xf3\x60\xc4"
SFX_MAGIC_LE = 0xC460F3FF  # Little-endian interpretation: 3294888959

# RIFF header magic
RIFF_MAGIC = b"RIFF"
RIFF_MAGIC_LE = 0x46464952  # "RIFF" as little-endian uint32: 1179011410

# MP3-in-WAV format has riffSize == 50
MP3_IN_WAV_RIFF_SIZE = 50
MP3_IN_WAV_HEADER_SIZE = 58  # Skip 58 bytes for MP3 data

# SFX header size
SFX_HEADER_SIZE = 470  # 0x1DA bytes


def detect_audio_format(data: bytes) -> tuple[DeobfuscationResult, int]:
    """Detect the audio format and return the header size to skip.
    
    Args:
        data: Raw audio file bytes
        
    Returns:
        Tuple of (format_type, header_size_to_skip)
        
    References:
        vendor/reone/src/libs/audio/format/wavreader.cpp:30-38
        vendor/KotOR.js/src/audio/AudioFile.ts:111-146
    """
    if len(data) < 12:
        return DeobfuscationResult.STANDARD, 0
    
    # Check first 4 bytes
    first_four = data[:4]
    
    # Check for SFX header: 0xFF 0xF3 0x60 0xC4
    # Reference: vendor/reone/src/libs/audio/format/wavreader.cpp:34
    if first_four == SFX_MAGIC_BYTES:
        return DeobfuscationResult.SFX_HEADER, SFX_HEADER_SIZE
    
    # Check for RIFF header
    if first_four == RIFF_MAGIC:
        # Read the riffSize (bytes 4-8)
        riff_size = struct.unpack("<I", data[4:8])[0]
        
        # Reference: vendor/KotOR.js/src/audio/AudioFile.ts:134
        # if(riffSize == 50) → MP3 wrapped in WAV
        if riff_size == MP3_IN_WAV_RIFF_SIZE:
            return DeobfuscationResult.MP3_IN_WAV, MP3_IN_WAV_HEADER_SIZE
        
        # Standard RIFF/WAVE
        return DeobfuscationResult.STANDARD, 0
    
    # Unknown format, assume standard
    return DeobfuscationResult.STANDARD, 0


def deobfuscate_audio(data: bytes) -> bytes:
    """Removes obfuscation headers from KotOR audio files.
    
    This function detects and removes KotOR-specific audio headers to produce
    data playable by standard media players.

    Args:
        data: Raw audio data bytes from KotOR installation

    Returns:
        Cleaned audio data bytes (RIFF/WAVE or raw MP3)

    Processing Logic:
        1. Check for SFX header (0xFF 0xF3 0x60 0xC4) → skip 470 bytes
        2. Check for MP3-in-WAV (RIFF with size 50) → skip 58 bytes (returns MP3!)
        3. Otherwise return unchanged (standard WAV)
        
    References:
        vendor/reone/src/libs/audio/format/wavreader.cpp:30-38
        vendor/KotOR.js/src/audio/AudioFile.ts:111-162
    """
    format_type, skip_size = detect_audio_format(data)
    
    if skip_size > 0 and len(data) > skip_size:
        return data[skip_size:]
    
    return data


def get_deobfuscation_result(data: bytes) -> tuple[bytes, DeobfuscationResult]:
    """Deobfuscate audio and return both the data and the format detected.
    
    This is useful when you need to know whether the result is WAVE or MP3.
    
    Args:
        data: Raw audio data bytes
        
    Returns:
        Tuple of (deobfuscated_data, format_type)
    """
    format_type, skip_size = detect_audio_format(data)
    
    if skip_size > 0 and len(data) > skip_size:
        return data[skip_size:], format_type
    
    return data, format_type


def obfuscate_audio(
    data: bytes,
    wav_type: str = "SFX",
) -> bytes:
    """Adds obfuscation header to audio data for KotOR compatibility.

    Args:
        data: Clean audio data bytes (RIFF/WAVE format)
        wav_type: Type of WAV ("SFX" or "VO"). Defaults to "SFX".

    Returns:
        Obfuscated audio data bytes

    Processing Logic:
        - For SFX files, prepend 470-byte header with SFX magic number
        - For VO files, return data unchanged (standard WAV)
        
    Note:
        VO files in KotOR are standard WAV format and don't need obfuscation.
        Only SFX files (streammusic) use the 470-byte header format.
    """
    if wav_type == "SFX":
        # Create 470-byte SFX header
        # Reference: vendor/reone/src/libs/audio/format/wavreader.cpp:34
        # Header starts with 0xFF 0xF3 0x60 0xC4
        header = bytearray(SFX_HEADER_SIZE)
        header[0:4] = SFX_MAGIC_BYTES
        # Fill remaining bytes with pattern (the exact pattern doesn't matter
        # as long as the magic is correct - game just skips to offset 0x1DA)
        # Using 0x00 for the rest is safe
        return bytes(header) + data
    
    # VO files don't need obfuscation
    return data
