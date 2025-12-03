#!/usr/bin/env python
"""Test script for KotOR WAV file loading.

Tests the WAV loading implementation against various KotOR audio file formats.
This script verifies that the deobfuscation and parsing work correctly.

Usage:
    python scripts/test_wav_loading.py [--path PATH_TO_WAV] [--kotor2 PATH]

Examples:
    # Test a specific file
    python scripts/test_wav_loading.py --path "path/to/file.wav"

    # Test all audio in KotOR 2 installation
    python scripts/test_wav_loading.py --kotor2 "C:/Program Files (x86)/Steam/steamapps/common/Knights of the Old Republic II"
"""

from __future__ import annotations

import argparse
import sys

from pathlib import Path

# Add library paths
SCRIPTS_PATH = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_PATH.parent
PYKOTOR_LIB = PROJECT_ROOT / "Libraries" / "PyKotor" / "src"
UTILITY_LIB = PROJECT_ROOT / "Libraries" / "Utility" / "src"

for lib_path in (PYKOTOR_LIB, UTILITY_LIB):
    if lib_path.exists() and str(lib_path) not in sys.path:
        sys.path.insert(0, str(lib_path))


def test_single_file(wav_path: Path) -> bool:
    """Test loading a single WAV file."""
    from io import BytesIO

    from pykotor.resource.formats.wav.wav_auto import get_playable_bytes, read_wav
    from pykotor.resource.formats.wav.wav_data import AudioFormat, WAVType, WaveEncoding
    from pykotor.resource.formats.wav.wav_obfuscation import DeobfuscationResult, detect_audio_format

    print(f"\n{'=' * 60}")
    print(f"Testing: {wav_path}")
    print(f"{'=' * 60}")

    if not wav_path.exists():
        print("  ERROR: File does not exist")
        return False

    # Read raw bytes
    raw_data = wav_path.read_bytes()
    print(f"  File size: {len(raw_data)} bytes")

    # Check first bytes
    print(f"  First 16 bytes (hex): {raw_data[:16].hex()}")
    print(f"  First 16 bytes (raw): {raw_data[:16]!r}")

    # Detect audio format
    format_type, skip_size = detect_audio_format(raw_data)
    format_names = {
        DeobfuscationResult.STANDARD: "Standard RIFF/WAVE",
        DeobfuscationResult.SFX_HEADER: "SFX (470-byte header)",
        DeobfuscationResult.MP3_IN_WAV: "MP3-in-WAV (58-byte header)",
    }
    print(f"  Detected format: {format_names.get(format_type, 'Unknown')}")
    print(f"  Header bytes to skip: {skip_size}")

    # Try to load
    try:
        wav = read_wav(BytesIO(raw_data))
        print("  ✓ Successfully loaded WAV")

        wav_type_names = {WAVType.VO: "Voice Over", WAVType.SFX: "Sound Effect"}
        audio_format_names = {AudioFormat.WAVE: "RIFF/WAVE", AudioFormat.MP3: "MP3", AudioFormat.UNKNOWN: "Unknown"}

        print(f"    WAV Type: {wav_type_names.get(wav.wav_type, wav.wav_type)}")
        print(f"    Audio Format: {audio_format_names.get(wav.audio_format, wav.audio_format)}")

        try:
            encoding = WaveEncoding(wav.encoding)
            print(f"    Encoding: {encoding.name} (0x{wav.encoding:04X})")
        except ValueError:
            print(f"    Encoding: Unknown (0x{wav.encoding:04X})")

        print(f"    Channels: {wav.channels}")
        print(f"    Sample Rate: {wav.sample_rate} Hz")
        print(f"    Bits/Sample: {wav.bits_per_sample}")
        print(f"    Block Align: {wav.block_align}")
        print(f"    Data Size: {len(wav.data)} bytes")

        # Get playable bytes
        playable = get_playable_bytes(wav)
        print(f"    Playable Size: {len(playable)} bytes")
        print(f"    Playable Start: {playable[:16].hex()}")

        # Verify playable format
        if playable[:4] == b"RIFF":
            print("    Playable Format: Valid RIFF/WAVE")
        elif playable[:3] == b"ID3" or (len(playable) >= 2 and playable[0] == 0xFF and (playable[1] & 0xE0) == 0xE0):
            print("    Playable Format: Valid MP3")
        else:
            print("    Playable Format: Unknown (might not play correctly)")

        return True

    except Exception as e:
        print(f"  ✗ FAILED to load: {e.__class__.__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_kotor_installation(kotor_path: Path) -> dict[str, int]:
    """Test all WAV files in a KotOR installation."""
    results = {"success": 0, "failed": 0, "total": 0}

    # Find all WAV files
    wav_dirs = [
        kotor_path / "streamvoice",
        kotor_path / "streamsounds",
        kotor_path / "streammusic",
        kotor_path / "streamwaves",
    ]

    wav_files: list[Path] = []
    for wav_dir in wav_dirs:
        if wav_dir.exists():
            wav_files.extend(wav_dir.rglob("*.wav"))

    if not wav_files:
        print(f"No WAV files found in {kotor_path}")
        return results

    print(f"\nFound {len(wav_files)} WAV files in {kotor_path}")

    # Test sample of files (first 10 from each directory type)
    tested_dirs: dict[str, int] = {}
    for wav_file in wav_files:
        parent_name = wav_file.parent.parent.name  # e.g., "streamvoice"
        if tested_dirs.get(parent_name, 0) >= 10:
            continue
        tested_dirs[parent_name] = tested_dirs.get(parent_name, 0) + 1

        results["total"] += 1
        if test_single_file(wav_file):
            results["success"] += 1
        else:
            results["failed"] += 1

    return results


def main():
    parser = argparse.ArgumentParser(description="Test KotOR WAV file loading")
    parser.add_argument("--path", type=Path, help="Path to a specific WAV file to test")
    parser.add_argument("--kotor1", type=Path, help="Path to KotOR 1 installation")
    parser.add_argument("--kotor2", type=Path, help="Path to KotOR 2 installation")
    parser.add_argument("--all", action="store_true", help="Test ALL files (not just sample)")

    args = parser.parse_args()

    if args.path:
        success = test_single_file(args.path)
        sys.exit(0 if success else 1)

    if args.kotor1:
        results = test_kotor_installation(args.kotor1)
        print(f"\n\nKotOR 1 Results: {results['success']}/{results['total']} passed ({results['failed']} failed)")

    if args.kotor2:
        results = test_kotor_installation(args.kotor2)
        print(f"\n\nKotOR 2 Results: {results['success']}/{results['total']} passed ({results['failed']} failed)")

    if not any([args.path, args.kotor1, args.kotor2]):
        print("No test path specified. Use --path, --kotor1, or --kotor2")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
