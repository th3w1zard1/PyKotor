"""KotOR WAV file reader/writer with automatic obfuscation handling.

This module handles reading and writing WAV files from KotOR, including:
- Standard RIFF/WAVE files (streamvoice, dialog audio)
- SFX files with 470-byte obfuscation header (streammusic, sound effects)
- MP3 wrapped in WAV container (some music files)

References:
----------
    vendor/reone/src/libs/audio/format/wavreader.cpp - WAV reading & format detection
    vendor/KotOR.js/src/audio/AudioFile.ts - Audio format handling
    vendor/xoreos/src/sound/decoders/wave.cpp - Standard WAV parsing
    vendor/SithCodec/src/codec.cpp - Audio codec implementation
"""
from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.wav.wav_data import (
    WAV,
    AudioFormat,
    WAVType,
    WaveEncoding,
)
from pykotor.resource.formats.wav.wav_obfuscation import (
    DeobfuscationResult,
    get_deobfuscation_result,
    obfuscate_audio,
)
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class WAVBinaryReader(ResourceReader):
    """Handles reading WAV binary data with automatic deobfuscation.
    
    WAV files in KotOR come in several formats:
    
    1. **Standard RIFF/WAVE** - Most voice-over files (streamvoice/)
       - Standard PCM or IMA ADPCM encoding
       - No obfuscation header
       
    2. **SFX Format** - Sound effects and some music (streammusic/)
       - 470-byte header starting with 0xFF 0xF3 0x60 0xC4
       - After header removal, standard RIFF/WAVE follows
       
    3. **MP3-in-WAV** - Some music files
       - RIFF header with size == 50
       - After 58-byte header removal, raw MP3 data follows
    
    References:
    ----------
        vendor/reone/src/libs/audio/format/wavreader.cpp:30-56
        vendor/KotOR.js/src/audio/AudioFile.ts:111-162
        vendor/xoreos/src/sound/decoders/wave.cpp:38-106
    """
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0x0,
        size: int = 0x0,
    ):
        super().__init__(source, offset, size)
        self._wav: WAV | None = None

    @autoclose
    def load(self, *, auto_close: bool = True) -> WAV:  # noqa: FBT001, FBT002, ARG002
        """Load WAV file with automatic deobfuscation.

        Returns:
            WAV: The loaded WAV object (deobfuscated)

        Processing Logic:
            1. Read all raw data
            2. Detect and remove obfuscation header
            3. If MP3 format, return WAV object with MP3 data
            4. Otherwise parse RIFF/WAVE structure
        """
        # Read all data
        self._reader.seek(0)
        raw_data = self._reader.read_all()
        
        # Deobfuscate and get format info
        deobfuscated_data, format_type = get_deobfuscation_result(raw_data)
        
        # Determine WAV type based on deobfuscation result
        if format_type == DeobfuscationResult.SFX_HEADER:
            wav_type = WAVType.SFX
        else:
            wav_type = WAVType.VO
        
        # If MP3-in-WAV format detected, return MP3 data directly
        # Reference: vendor/KotOR.js/src/audio/AudioFile.ts:134-140
        if format_type == DeobfuscationResult.MP3_IN_WAV:
            return WAV(
                wav_type=wav_type,
                audio_format=AudioFormat.MP3,
                encoding=WaveEncoding.MP3,
                channels=2,  # Default stereo for MP3
                sample_rate=44100,  # Default sample rate
                bits_per_sample=16,
                data=deobfuscated_data
            )
        
        # Parse as RIFF/WAVE
        return self._parse_riff_wave(deobfuscated_data, wav_type)
    
    def _parse_riff_wave(self, data: bytes, wav_type: WAVType) -> WAV:
        """Parse RIFF/WAVE format data.
        
        Args:
            data: Deobfuscated audio data (should start with RIFF)
            wav_type: The determined WAV type (VO/SFX)
            
        Returns:
            Parsed WAV object
            
        References:
            vendor/xoreos/src/sound/decoders/wave.cpp:38-106
            vendor/KotOR.js/src/audio/AudioFile.ts:250-262
        """
        reader = BinaryReader(BytesIO(data))
        
        # Read RIFF header
        # Reference: vendor/xoreos/src/sound/decoders/wave.cpp:39-41
        riff_tag = reader.read_bytes(4)
        if riff_tag != b"RIFF":
            msg = f"Not a valid RIFF file, got: {riff_tag!r}"
            raise ValueError(msg)

        file_size = reader.read_uint32()
        wave_tag = reader.read_bytes(4)
        
        # Reference: vendor/xoreos/src/sound/decoders/wave.cpp:45-47
        if wave_tag != b"WAVE":
            msg = f"Not a valid WAVE file, got: {wave_tag!r}"
            raise ValueError(msg)

        # Initialize format values with defaults
        encoding = WaveEncoding.PCM
        channels = 1
        sample_rate = 44100
        bytes_per_sec = 88200
        block_align = 2
        bits_per_sample = 16
        audio_data = b""
        
        # Parse chunks until we find 'data'
        # Reference: vendor/xoreos/src/sound/decoders/wave.cpp:49-77
        while reader.remaining() >= 8:
            chunk_id = reader.read_bytes(4)
            chunk_size = reader.read_uint32()

            if chunk_id == b"fmt ":
                # Parse format chunk
                # Reference: vendor/xoreos/src/sound/decoders/wave.cpp:57-66
                # Reference: vendor/KotOR.js/src/audio/AudioFile.ts:214-228
                encoding_value = reader.read_uint16()
                try:
                    encoding = WaveEncoding(encoding_value)
                except ValueError:
                    # Store as raw int value for unsupported encodings
                    encoding = encoding_value  # type: ignore[assignment]
                    
                channels = reader.read_uint16()
                sample_rate = reader.read_uint32()
                bytes_per_sec = reader.read_uint32()
                block_align = reader.read_uint16()
                bits_per_sample = reader.read_uint16()

                # Skip any extra format bytes
                # Reference: vendor/xoreos/src/sound/decoders/wave.cpp:66
                if chunk_size > 16:
                    reader.skip(chunk_size - 16)

            elif chunk_id == b"data":
                # Read audio data
                # Reference: vendor/xoreos/src/sound/decoders/wave.cpp:79-80
                actual_size = min(chunk_size, reader.remaining())
                audio_data = reader.read_bytes(actual_size)
                break  # Found data, stop parsing

            elif chunk_id == b"fact":
                # Skip fact chunk (contains sample count for compressed formats)
                # Reference: vendor/KotOR.js/src/audio/AudioFile.ts:230-234
                reader.skip(chunk_size)
                
            else:
                # Skip unknown chunks
                if chunk_size > reader.remaining():
                    break  # Malformed chunk, stop
                reader.skip(chunk_size)
                # RIFF chunks are word-aligned
                if chunk_size % 2 == 1 and reader.remaining() > 0:
                    reader.skip(1)

        if not audio_data:
            msg = "No audio data chunk found in WAV file"
            raise ValueError(msg)

        # Create WAV object
        self._wav = WAV(
            wav_type=wav_type,
            audio_format=AudioFormat.WAVE,
            encoding=encoding,
            channels=channels,
            sample_rate=sample_rate,
            bits_per_sample=bits_per_sample,
            bytes_per_sec=bytes_per_sec,
            block_align=block_align,
            data=audio_data
        )

        return self._wav


class WAVBinaryWriter(ResourceWriter):
    """Handles writing WAV binary data with optional obfuscation.
    
    For VO files: Writes standard RIFF/WAVE format
    For SFX files: Adds 470-byte obfuscation header before RIFF/WAVE
    For MP3 data: Wraps in appropriate container based on wav_type
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
        """Write WAV data to target with automatic obfuscation.

        Processing Logic:
            1. Build clean RIFF/WAVE data (or use MP3 directly)
            2. Obfuscate based on WAV type (SFX adds header, VO is unchanged)
            3. Write obfuscated data to target
        """
        from pykotor.common.stream import BinaryWriter
        
        # For MP3 format, just obfuscate and write
        if self.wav.audio_format == AudioFormat.MP3:
            wav_type_str = "SFX" if self.wav.wav_type == WAVType.SFX else "VO"
            obfuscated_data = obfuscate_audio(self.wav.data, wav_type_str)
            self._writer.write_bytes(obfuscated_data)
            return
        
        # Build clean WAV data
        clean_buffer = BytesIO()
        clean_writer = BinaryWriter.to_stream(clean_buffer)
        
        # Calculate sizes
        data_size = len(self.wav.data)
        fmt_chunk_size = 16
        # RIFF size = 4 (WAVE) + 8 (fmt header) + fmt_chunk_size + 8 (data header) + data_size
        file_size = 4 + 8 + fmt_chunk_size + 8 + data_size

        # Write RIFF header
        clean_writer.write_bytes(b"RIFF")
        clean_writer.write_uint32(file_size)
        clean_writer.write_bytes(b"WAVE")

        # Write format chunk
        clean_writer.write_bytes(b"fmt ")
        clean_writer.write_uint32(fmt_chunk_size)
        clean_writer.write_uint16(self.wav.encoding if isinstance(self.wav.encoding, int) else self.wav.encoding.value)
        clean_writer.write_uint16(self.wav.channels)
        clean_writer.write_uint32(self.wav.sample_rate)
        bytes_per_sec = self.wav.bytes_per_sec or (self.wav.sample_rate * self.wav.block_align)
        clean_writer.write_uint32(bytes_per_sec)
        clean_writer.write_uint16(self.wav.block_align)
        clean_writer.write_uint16(self.wav.bits_per_sample)

        # Write data chunk
        clean_writer.write_bytes(b"data")
        clean_writer.write_uint32(data_size)
        clean_writer.write_bytes(self.wav.data)
        
        # Get clean data and obfuscate it
        clean_data = clean_buffer.getvalue()
        wav_type_str = "SFX" if self.wav.wav_type == WAVType.SFX else "VO"
        obfuscated_data = obfuscate_audio(clean_data, wav_type_str)
        
        # Write obfuscated data
        self._writer.write_bytes(obfuscated_data)
