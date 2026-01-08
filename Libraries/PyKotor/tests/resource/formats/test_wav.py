"""Comprehensive tests for WAV file handling.

Tests cover:
- Reading standard and obfuscated WAV files
- Writing in both formats (WAV and WAV_DEOB)
- Different audio characteristics (sample rates, channels, bit depths)
- Error handling for corrupted files
- Round-trip conversion (read-write-read)
- Obfuscation/deobfuscation
"""

from __future__ import annotations

import math
import os
import pathlib
import struct
import sys
import tempfile
import unittest
from io import BytesIO

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[4].joinpath("src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[6].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.resource.formats.wav.wav_auto import bytes_wav, read_wav, write_wav
from pykotor.resource.formats.wav.wav_data import WAV, WAVType, WaveEncoding
from pykotor.resource.formats.wav.wav_obfuscation import deobfuscate_audio, obfuscate_audio
from pykotor.resource.type import ResourceType

TEST_FILES_DIR = THIS_SCRIPT_PATH.parents[3] / "test_files"
DOES_NOT_EXIST_FILE = "./thisfiledoesnotexist"


def create_test_wav_file(
    filepath: pathlib.Path,
    sample_rate: int = 44100,
    channels: int = 1,
    bits_per_sample: int = 16,
    duration_seconds: float = 0.5,
) -> None:
    """Create a simple WAV file with sine wave audio.
    
    Args:
    ----
        filepath: Path to save the WAV file
        sample_rate: Sample rate in Hz
        channels: Number of audio channels (1=mono, 2=stereo)
        bits_per_sample: Bits per sample (8 or 16)
        duration_seconds: Duration of audio in seconds
    """
    num_samples = int(sample_rate * duration_seconds)
    
    # Generate sine wave audio data
    frequency = 440.0  # A4 note
    audio_data = bytearray()
    
    for i in range(num_samples):
        # Generate sine wave sample
        t = i / sample_rate
        sample_value = math.sin(2 * math.pi * frequency * t)
        
        if bits_per_sample == 16:
            # 16-bit PCM: range -32768 to 32767
            int_sample = int(sample_value * 32767)
            for _ in range(channels):
                audio_data.extend(struct.pack('<h', int_sample))
        else:  # 8-bit
            # 8-bit PCM: range 0 to 255 (unsigned)
            int_sample = int((sample_value + 1) * 127.5)
            for _ in range(channels):
                audio_data.extend(struct.pack('B', int_sample))
    
    data_size = len(audio_data)
    block_align = channels * (bits_per_sample // 8)
    byte_rate = sample_rate * block_align
    
    # Calculate file size (RIFF header + format chunk + data chunk)
    file_size = 36 + data_size
    
    # Write WAV file
    with filepath.open('wb') as f:
        # RIFF header
        f.write(b'RIFF')
        f.write(struct.pack('<I', file_size))
        f.write(b'WAVE')
        
        # Format chunk
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))  # Format chunk size
        f.write(struct.pack('<H', 1))   # Audio format (1 = PCM)
        f.write(struct.pack('<H', channels))
        f.write(struct.pack('<I', sample_rate))
        f.write(struct.pack('<I', byte_rate))
        f.write(struct.pack('<H', block_align))
        f.write(struct.pack('<H', bits_per_sample))
        
        # Data chunk
        f.write(b'data')
        f.write(struct.pack('<I', data_size))
        f.write(audio_data)


def ensure_test_wav_files() -> dict[str, pathlib.Path]:
    """Ensure test WAV files exist, creating them if necessary.
    
    Returns:
    -------
        Dictionary mapping descriptive names to file paths
    """
    TEST_FILES_DIR.mkdir(parents=True, exist_ok=True)
    
    test_wavs = {
        "mono_44k_16bit": (44100, 1, 16, 0.5),
        "stereo_44k_16bit": (44100, 2, 16, 0.5),
        "mono_22k_16bit": (22050, 1, 16, 1.0),
        "mono_48k_8bit": (48000, 1, 8, 0.3),
        "stereo_48k_16bit": (48000, 2, 16, 0.75),
    }
    
    files = {}
    for name, (sample_rate, channels, bits_per_sample, duration) in test_wavs.items():
        filepath = TEST_FILES_DIR / f"test_wav_{name}.wav"
        if not filepath.exists():
            create_test_wav_file(filepath, sample_rate, channels, bits_per_sample, duration)
        files[name] = filepath
    
    return files


class TestWAVData(unittest.TestCase):
    """Test WAV data structures and basic operations."""
    
    def test_wav_creation_defaults(self):
        """Test creating WAV with default parameters."""
        wav = WAV()
        self.assertEqual(wav.wav_type, WAVType.VO)
        self.assertEqual(wav.encoding, WaveEncoding.PCM)
        self.assertEqual(wav.channels, 1)
        self.assertEqual(wav.sample_rate, 44100)
        self.assertEqual(wav.bits_per_sample, 16)
        self.assertEqual(wav.block_align, 2)  # 1 channel * 2 bytes (16-bit)
        self.assertEqual(wav.data, b"")
    
    def test_wav_creation_custom(self):
        """Test creating WAV with custom parameters."""
        wav = WAV(
            wav_type=WAVType.SFX,
            encoding=WaveEncoding.IMA_ADPCM,
            channels=2,
            sample_rate=48000,
            bits_per_sample=16,
            bytes_per_sec=192000,
            block_align=4,
            data=b"\x00\x01\x02\x03"
        )
        self.assertEqual(wav.wav_type, WAVType.SFX)
        self.assertEqual(wav.encoding, WaveEncoding.IMA_ADPCM)
        self.assertEqual(wav.channels, 2)
        self.assertEqual(wav.sample_rate, 48000)
        self.assertEqual(wav.bits_per_sample, 16)
        self.assertEqual(wav.block_align, 4)
        self.assertEqual(wav.data, b"\x00\x01\x02\x03")
    
    def test_wav_equality(self):
        """Test WAV equality comparison."""
        wav1 = WAV(
            wav_type=WAVType.VO,
            channels=1,
            sample_rate=44100,
            data=b"test"
        )
        wav2 = WAV(
            wav_type=WAVType.VO,
            channels=1,
            sample_rate=44100,
            data=b"test"
        )
        wav3 = WAV(
            wav_type=WAVType.SFX,
            channels=1,
            sample_rate=44100,
            data=b"test"
        )
        
        self.assertEqual(wav1, wav2)
        self.assertNotEqual(wav1, wav3)
        self.assertNotEqual(wav1, "not a wav")
    
    def test_wav_hash(self):
        """Test WAV hashing."""
        wav1 = WAV(data=b"test")
        wav2 = WAV(data=b"test")
        wav3 = WAV(data=b"different")
        
        self.assertEqual(hash(wav1), hash(wav2))
        self.assertNotEqual(hash(wav1), hash(wav3))
    
    def test_wav_type_enum(self):
        """Test WAVType enum values."""
        self.assertIsNotNone(WAVType.VO)
        self.assertIsNotNone(WAVType.SFX)
        self.assertNotEqual(WAVType.VO, WAVType.SFX)
    
    def test_wave_encoding_enum(self):
        """Test WaveEncoding enum values."""
        self.assertEqual(WaveEncoding.PCM.value, 0x01)
        self.assertEqual(WaveEncoding.IMA_ADPCM.value, 0x11)
        self.assertNotEqual(WaveEncoding.PCM, WaveEncoding.IMA_ADPCM)


class TestWAVIO(unittest.TestCase):
    """Test WAV file I/O operations."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class - ensure test files exist."""
        cls.test_wav_files = ensure_test_wav_files()
    
    def test_read_standard_wav_mono(self):
        """Test reading a standard mono WAV file."""
        filepath = self.test_wav_files["mono_44k_16bit"]
        wav = read_wav(filepath)
        
        self.assertIsInstance(wav, WAV)
        self.assertEqual(wav.wav_type, WAVType.VO)
        self.assertEqual(wav.channels, 1)
        self.assertEqual(wav.sample_rate, 44100)
        self.assertEqual(wav.bits_per_sample, 16)
        self.assertGreater(len(wav.data), 0)
    
    def test_read_standard_wav_stereo(self):
        """Test reading a standard stereo WAV file."""
        filepath = self.test_wav_files["stereo_44k_16bit"]
        wav = read_wav(filepath)
        
        self.assertIsInstance(wav, WAV)
        self.assertEqual(wav.channels, 2)
        self.assertEqual(wav.sample_rate, 44100)
        self.assertEqual(wav.bits_per_sample, 16)
        self.assertGreater(len(wav.data), 0)
    
    def test_read_different_sample_rates(self):
        """Test reading WAV files with different sample rates."""
        test_cases = [
            ("mono_22k_16bit", 22050),
            ("mono_44k_16bit", 44100),
            ("mono_48k_8bit", 48000),
        ]
        
        for name, expected_rate in test_cases:
            with self.subTest(name=name, rate=expected_rate):
                filepath = self.test_wav_files[name]
                wav = read_wav(filepath)
                self.assertEqual(wav.sample_rate, expected_rate)
    
    def test_read_different_bit_depths(self):
        """Test reading WAV files with different bit depths."""
        test_cases = [
            ("mono_48k_8bit", 8),
            ("mono_44k_16bit", 16),
        ]
        
        for name, expected_bits in test_cases:
            with self.subTest(name=name, bits=expected_bits):
                filepath = self.test_wav_files[name]
                wav = read_wav(filepath)
                self.assertEqual(wav.bits_per_sample, expected_bits)
    
    def test_read_from_bytes(self):
        """Test reading WAV from bytes object."""
        filepath = self.test_wav_files["mono_44k_16bit"]
        wav_data = filepath.read_bytes()
        
        wav = read_wav(wav_data)
        self.assertIsInstance(wav, WAV)
        self.assertEqual(wav.sample_rate, 44100)
    
    def test_read_from_bytesio(self):
        """Test reading WAV from BytesIO."""
        filepath = self.test_wav_files["mono_44k_16bit"]
        wav_data = filepath.read_bytes()
        
        wav = read_wav(BytesIO(wav_data))
        self.assertIsInstance(wav, WAV)
        self.assertEqual(wav.sample_rate, 44100)
    
    def test_read_from_path_string(self):
        """Test reading WAV from path string."""
        filepath = str(self.test_wav_files["mono_44k_16bit"])
        wav = read_wav(filepath)
        self.assertIsInstance(wav, WAV)
    
    def test_read_from_pathlib_path(self):
        """Test reading WAV from pathlib.Path."""
        filepath = self.test_wav_files["mono_44k_16bit"]
        wav = read_wav(filepath)
        self.assertIsInstance(wav, WAV)
    
    def test_read_raises_file_not_found(self):
        """Test that reading non-existent file raises FileNotFoundError."""
        self.assertRaises(FileNotFoundError, read_wav, DOES_NOT_EXIST_FILE)
    
    # sourcery skip: no-conditionals-in-tests
    def test_read_raises_directory_error(self):
        """Test that reading a directory raises appropriate error."""
        if os.name == "nt":
            self.assertRaises(PermissionError, read_wav, ".")
        else:
            self.assertRaises(IsADirectoryError, read_wav, ".")
    
    def test_read_raises_invalid_format(self):
        """Test that reading invalid format raises ValueError."""
        invalid_data = b"This is not a valid WAV file"
        self.assertRaises(ValueError, read_wav, invalid_data)
    
    def test_read_raises_missing_riff(self):
        """Test that reading file without RIFF header raises ValueError."""
        invalid_data = b"XXXX" + b"\x00" * 100
        self.assertRaises(ValueError, read_wav, invalid_data)
    
    def test_read_raises_missing_wave(self):
        """Test that reading file without WAVE tag raises ValueError."""
        invalid_data = b"RIFF" + struct.pack("<I", 100) + b"XXXX" + b"\x00" * 92
        self.assertRaises(ValueError, read_wav, invalid_data)
    
    def test_read_raises_missing_format_chunk(self):
        """Test that reading file without format chunk raises ValueError."""
        invalid_data = (
            b"RIFF" + struct.pack("<I", 36) + b"WAVE" +
            b"XXXX" + b"\x00" * 28
        )
        self.assertRaises(ValueError, read_wav, invalid_data)
    
    def test_read_raises_missing_data_chunk(self):
        """Test that reading file without data chunk raises ValueError."""
        invalid_data = (
            b"RIFF" + struct.pack("<I", 36) + b"WAVE" +
            b"fmt " + struct.pack("<I", 16) +
            struct.pack("<HHIIHH", 1, 1, 44100, 88200, 2, 16) +
            b"XXXX" + struct.pack("<I", 0)
        )
        self.assertRaises(ValueError, read_wav, invalid_data)


class TestWAVWrite(unittest.TestCase):
    """Test WAV file writing operations."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class - ensure test files exist."""
        cls.test_wav_files = ensure_test_wav_files()
    
    def test_write_wav_obfuscated(self):
        """Test writing WAV in obfuscated format (ResourceType.WAV)."""
        # Read a test file
        filepath = self.test_wav_files["mono_44k_16bit"]
        wav = read_wav(filepath)
        
        # Write to bytes in obfuscated format
        output = bytearray()
        write_wav(wav, output, ResourceType.WAV)
        
        # Should have written obfuscated data
        self.assertGreater(len(output), len(wav.data))
        
        # Should be able to read it back
        wav_readback = read_wav(BytesIO(output))
        self.assertEqual(wav.sample_rate, wav_readback.sample_rate)
        self.assertEqual(wav.channels, wav_readback.channels)
    
    def test_write_wav_deobfuscated(self):
        """Test writing WAV in deobfuscated format (ResourceType.WAV_DEOB)."""
        # Read a test file
        filepath = self.test_wav_files["mono_44k_16bit"]
        wav = read_wav(filepath)
        
        # Write to bytes in deobfuscated format
        output = bytearray()
        write_wav(wav, output, ResourceType.WAV_DEOB)
        
        # Should start with RIFF header (standard WAV format)
        self.assertEqual(output[:4], b"RIFF")
        self.assertEqual(output[8:12], b"WAVE")
        
        # Should be able to read it back
        wav_readback = read_wav(BytesIO(output))
        self.assertEqual(wav.sample_rate, wav_readback.sample_rate)
        self.assertEqual(wav.channels, wav_readback.channels)
    
    def test_write_wav_to_file(self):
        """Test writing WAV to a file."""
        filepath = self.test_wav_files["mono_44k_16bit"]
        wav = read_wav(filepath)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
            tmp_path = pathlib.Path(tmp.name)
        
        try:
            write_wav(wav, tmp_path, ResourceType.WAV_DEOB)
            self.assertTrue(tmp_path.exists())
            self.assertGreater(tmp_path.stat().st_size, 0)
            
            # Should be readable
            wav_readback = read_wav(tmp_path)
            self.assertEqual(wav.sample_rate, wav_readback.sample_rate)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
    
    def test_write_wav_to_string_path(self):
        """Test writing WAV to a string path."""
        filepath = self.test_wav_files["mono_44k_16bit"]
        wav = read_wav(filepath)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
            tmp_path_str = tmp.name
        
        try:
            write_wav(wav, tmp_path_str, ResourceType.WAV_DEOB)
            tmp_path = pathlib.Path(tmp_path_str)
            self.assertTrue(tmp_path.exists())
        finally:
            if pathlib.Path(tmp_path_str).exists():
                pathlib.Path(tmp_path_str).unlink()
    
    def test_bytes_wav_obfuscated(self):
        """Test bytes_wav function with obfuscated format."""
        filepath = self.test_wav_files["mono_44k_16bit"]
        wav = read_wav(filepath)
        
        data = bytes_wav(wav, ResourceType.WAV)
        self.assertIsInstance(data, bytes)
        self.assertGreater(len(data), 0)
        
        # Should be readable (will auto-deobfuscate)
        wav_readback = read_wav(BytesIO(data))
        self.assertEqual(wav.sample_rate, wav_readback.sample_rate)
    
    def test_bytes_wav_deobfuscated(self):
        """Test bytes_wav function with deobfuscated format."""
        filepath = self.test_wav_files["mono_44k_16bit"]
        wav = read_wav(filepath)
        
        data = bytes_wav(wav, ResourceType.WAV_DEOB)
        self.assertIsInstance(data, bytes)
        self.assertGreater(len(data), 0)
        
        # Should start with RIFF header
        self.assertEqual(data[:4], b"RIFF")
        
        # Should be readable
        wav_readback = read_wav(BytesIO(data))
        self.assertEqual(wav.sample_rate, wav_readback.sample_rate)
    
    def test_bytes_wav_default(self):
        """Test bytes_wav function with default format (obfuscated)."""
        filepath = self.test_wav_files["mono_44k_16bit"]
        wav = read_wav(filepath)
        
        data = bytes_wav(wav)  # Default should be ResourceType.WAV (obfuscated)
        self.assertIsInstance(data, bytes)
        self.assertGreater(len(data), 0)
        
        # Should be readable (will auto-deobfuscate)
        wav_readback = read_wav(BytesIO(data))
        self.assertEqual(wav.sample_rate, wav_readback.sample_rate)
    
    # sourcery skip: no-conditionals-in-tests
    def test_write_raises_directory_error(self):
        """Test that writing to a directory raises appropriate error."""
        wav = WAV()
        if os.name == "nt":
            self.assertRaises(PermissionError, write_wav, wav, ".", ResourceType.WAV_DEOB)
        else:
            self.assertRaises(IsADirectoryError, write_wav, wav, ".", ResourceType.WAV_DEOB)


class TestWAVRoundTrip(unittest.TestCase):
    """Test round-trip conversion (read-write-read)."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class - ensure test files exist."""
        cls.test_wav_files = ensure_test_wav_files()
    
    def test_roundtrip_obfuscated(self):
        """Test round-trip conversion with obfuscated format."""
        filepath = self.test_wav_files["mono_44k_16bit"]
        original_wav = read_wav(filepath)
        
        # Write in obfuscated format
        data = bytes_wav(original_wav, ResourceType.WAV)
        
        # Read back
        roundtrip_wav = read_wav(BytesIO(data))
        
        # Compare key properties
        self.assertEqual(original_wav.sample_rate, roundtrip_wav.sample_rate)
        self.assertEqual(original_wav.channels, roundtrip_wav.channels)
        self.assertEqual(original_wav.bits_per_sample, roundtrip_wav.bits_per_sample)
        self.assertEqual(original_wav.encoding, roundtrip_wav.encoding)
        self.assertEqual(len(original_wav.data), len(roundtrip_wav.data))
    
    def test_roundtrip_deobfuscated(self):
        """Test round-trip conversion with deobfuscated format."""
        filepath = self.test_wav_files["stereo_44k_16bit"]
        original_wav = read_wav(filepath)
        
        # Write in deobfuscated format
        data = bytes_wav(original_wav, ResourceType.WAV_DEOB)
        
        # Read back
        roundtrip_wav = read_wav(BytesIO(data))
        
        # Compare key properties
        self.assertEqual(original_wav.sample_rate, roundtrip_wav.sample_rate)
        self.assertEqual(original_wav.channels, roundtrip_wav.channels)
        self.assertEqual(original_wav.bits_per_sample, roundtrip_wav.bits_per_sample)
        self.assertEqual(original_wav.encoding, roundtrip_wav.encoding)
        self.assertEqual(len(original_wav.data), len(roundtrip_wav.data))
    
    def test_roundtrip_all_test_files(self):
        """Test round-trip conversion for all test WAV files."""
        for name, filepath in self.test_wav_files.items():
            with self.subTest(name=name):
                original_wav = read_wav(filepath)
                
                # Test both formats
                for format_type in [ResourceType.WAV, ResourceType.WAV_DEOB]:
                    data = bytes_wav(original_wav, format_type)
                    roundtrip_wav = read_wav(BytesIO(data))
                    
                    self.assertEqual(original_wav.sample_rate, roundtrip_wav.sample_rate)
                    self.assertEqual(original_wav.channels, roundtrip_wav.channels)
                    self.assertEqual(original_wav.bits_per_sample, roundtrip_wav.bits_per_sample)


class TestWAVObfuscation(unittest.TestCase):
    """Test WAV obfuscation/deobfuscation functionality."""
    
    def test_deobfuscate_clean_data(self):
        """Test that deobfuscating clean data returns it unchanged."""
        clean_data = b"RIFF" + b"\x00" * 100
        result = deobfuscate_audio(clean_data)
        self.assertEqual(result, clean_data)
    
    def test_deobfuscate_short_data(self):
        """Test that deobfuscating short data returns it unchanged."""
        short_data = b"test"
        result = deobfuscate_audio(short_data)
        self.assertEqual(result, short_data)
    
    def test_obfuscate_sfx(self):
        """Test obfuscating data as SFX."""
        clean_data = b"RIFF" + b"\x00" * 100
        obfuscated = obfuscate_audio(clean_data, "SFX")
        
        # Should add 470-byte header
        self.assertEqual(len(obfuscated), len(clean_data) + 470)
        self.assertNotEqual(obfuscated[:4], b"RIFF")  # Should not start with RIFF
    
    def test_obfuscate_vo(self):
        """Test obfuscating data as VO."""
        clean_data = b"RIFF" + b"\x00" * 100
        obfuscated = obfuscate_audio(clean_data, "VO")
        
        # Should add 20-byte header (to satisfy deobfuscation check at offset 16)
        # NOTE: VO header magic number (1179011410) is "RIFF" in ASCII, so obfuscated data starts with "RIFF"
        self.assertEqual(len(obfuscated), len(clean_data) + 20)
        # Header starts with "RIFF" (magic number 1179011410)
        self.assertEqual(obfuscated[:4], b"RIFF")
        # Original data should start at offset 20 (also "RIFF")
        self.assertEqual(obfuscated[20:24], b"RIFF")
        # But they should be different instances (different positions)
        self.assertIsNot(obfuscated[:4], obfuscated[20:24])
    
    def test_obfuscate_deobfuscate_roundtrip_sfx(self):
        """Test obfuscation-deobfuscation round-trip for SFX."""
        clean_data = b"RIFF" + b"\x00" * 1000
        obfuscated = obfuscate_audio(clean_data, "SFX")
        deobfuscated = deobfuscate_audio(obfuscated)
        
        self.assertEqual(deobfuscated, clean_data)
    
    def test_obfuscate_deobfuscate_roundtrip_vo(self):
        """Test obfuscation-deobfuscate round-trip for VO."""
        clean_data = b"RIFF" + b"\x00" * 1000
        obfuscated = obfuscate_audio(clean_data, "VO")
        deobfuscated = deobfuscate_audio(obfuscated)
        
        self.assertEqual(deobfuscated, clean_data)


class TestWAVEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class - ensure test files exist."""
        cls.test_wav_files = ensure_test_wav_files()
    
    def test_empty_wav_data(self):
        """Test creating and writing WAV with empty data."""
        wav = WAV(data=b"")
        data = bytes_wav(wav, ResourceType.WAV_DEOB)
        
        # Should still be valid WAV format
        self.assertEqual(data[:4], b"RIFF")
        
        # Should be readable
        wav_readback = read_wav(BytesIO(data))
        self.assertEqual(len(wav_readback.data), 0)
    
    def test_wav_with_large_data(self):
        """Test handling WAV with large data."""
        # Create a large audio data chunk
        large_data = b"\x00\x01" * 100000  # 200KB of audio data
        
        wav = WAV(
            channels=1,
            sample_rate=44100,
            bits_per_sample=16,
            data=large_data
        )
        
        # Should be able to write and read
        output = bytearray()
        write_wav(wav, output, ResourceType.WAV_DEOB)
        self.assertGreater(len(output), len(large_data))
        
        wav_readback = read_wav(BytesIO(output))
        self.assertEqual(len(wav_readback.data), len(large_data))
    
    def test_wav_with_various_channels(self):
        """Test WAV files with different channel configurations."""
        for channels in [1, 2]:
            with self.subTest(channels=channels):
                data_size = 1000 * channels * 2  # 1000 samples * channels * 2 bytes
                audio_data = b"\x00" * data_size
                
                wav = WAV(
                    channels=channels,
                    sample_rate=44100,
                    bits_per_sample=16,
                    data=audio_data
                )
                
                output = bytes_wav(wav, ResourceType.WAV_DEOB)
                wav_readback = read_wav(BytesIO(output))
                self.assertEqual(wav_readback.channels, channels)
    
    def test_wav_with_various_sample_rates(self):
        """Test WAV files with different sample rates."""
        sample_rates = [8000, 11025, 16000, 22050, 44100, 48000, 96000]
        
        for rate in sample_rates:
            with self.subTest(sample_rate=rate):
                wav = WAV(
                    sample_rate=rate,
                    data=b"\x00\x01" * 1000
                )
                
                output = bytes_wav(wav, ResourceType.WAV_DEOB)
                wav_readback = read_wav(BytesIO(output))
                self.assertEqual(wav_readback.sample_rate, rate)


if __name__ == "__main__":
    unittest.main()

