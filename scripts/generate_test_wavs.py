"""Generate test WAV files for testing.

Creates various WAV files with different characteristics:
- Different sample rates (22050, 44100, 48000)
- Different channels (mono, stereo)
- Different bit depths (8, 16)
- Different data sizes
"""

from __future__ import annotations

import struct
from pathlib import Path


def create_wav_file(
    filepath: Path,
    sample_rate: int = 44100,
    channels: int = 1,
    bits_per_sample: int = 16,
    duration_seconds: float = 0.5,
):
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
    import math
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


def main():
    """Generate all test WAV files."""
    test_files_dir = Path(__file__).parents[1] / "tests" / "test_pykotor" / "test_files"
    test_files_dir.mkdir(parents=True, exist_ok=True)
    
    # Create 5 different test WAV files
    wav_files = [
        ("test_wav_mono_44k_16bit.wav", 44100, 1, 16, 0.5),
        ("test_wav_stereo_44k_16bit.wav", 44100, 2, 16, 0.5),
        ("test_wav_mono_22k_16bit.wav", 22050, 1, 16, 1.0),
        ("test_wav_mono_48k_8bit.wav", 48000, 1, 8, 0.3),
        ("test_wav_stereo_48k_16bit.wav", 48000, 2, 16, 0.75),
    ]
    
    for filename, sample_rate, channels, bits_per_sample, duration in wav_files:
        filepath = test_files_dir / filename
        print(f"Generating {filename}...")
        create_wav_file(filepath, sample_rate, channels, bits_per_sample, duration)
        print(f"  Created: {filepath} ({filepath.stat().st_size} bytes)")
    
    print(f"\nGenerated {len(wav_files)} test WAV files in {test_files_dir}")


if __name__ == "__main__":
    main()

