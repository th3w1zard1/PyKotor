# KotOR WAV file format Documentation

KotOR stores both standard WAV voice-over lines and Bioware-obfuscated sound-effect files. Voice-over assets are regular RIFF containers with PCM headers, while SFX assets prepend a 470-[byte](GFF-File-Format#gff-data-types) custom block before the RIFF data. PyKotor handles both variants transparently.

## Table of Contents

- KotOR WAV File Format Documentation
  - Table of Contents
  - File Types
  - [Standard RIFF/WAVE Structure](#standard-riffwave-structure)
    - [Format Chunk](#format-chunk)
    - [Data Chunk](#data-chunk)
  - [KotOR SFX Header](#kotor-sfx-header)
  - [Encoding Details](#encoding-details)
  - [Implementation Details](#implementation-details)

---

## file types

| type | Usage | Description |
| ---- | ----- | ----------- |
| **VO (Voice-over)** | Dialogue lines (`*.wav` referenced by [TLK](TLK-File-Format) [StrRefs](TLK-File-Format#string-references-strref)). | Plain RIFF/WAVE PCM files readable by any media player. |
| **SFX (Sound effects)** | Combat, UI, ambience, `.wav` files under `StreamSounds`/`SFX`. | Contains a Bioware 470-[byte](GFF-File-Format#gff-data-types) obfuscation header followed by the same RIFF data. |

PyKotor exposes these via the `WAVType` enum (`VO` vs. `SFX`) so tools know whether to insert/remove the proprietary header (`io_wav.py:52-121`).

---

## Standard RIFF/WAVE structure

KotOR sticks to the canonical RIFF chunk order:

| offset | field | Description |
| ------ | ----- | ----------- |
| 0 (0x00) | `"RIFF"` | Chunk ID |
| 4 (0x04) | `<uint32>` | file size minus 8 |
| 8 (0x08) | `"WAVE"` | format tag |
| 12 (0x0C) | `"fmt "` | format chunk ID |
| 16 (0x10) | `<uint32>` | format chunk size (usually 0x10) |
| … | See below | |

### format Chunk

| field | type | Description |
| ----- | ---- | ----------- |
| `audio_format` | uint16 | `0x0001` for PCM, `0x0011` for IMA ADPCM. |
| `channels` | uint16 | 1 (mono) or 2 (stereo). |
| `sample_rate` | uint32 | Typically 22050 Hz (SFX) or 44100 Hz (VO). |
| `bytes_per_sec` | uint32 | `sample_rate × block_align`. |
| `block_align` | uint16 | Bytes per sample frame. |
| `bits_per_sample` | uint16 | 8 or 16 for PCM. |
| `extra_bytes` | … | Present only when `fmt_size > 0x10` (e.g., ADPCM coefficients). |

### data Chunk

After the `fmt` chunk (and any optional `fact` chunk), the `"data"` chunk begins:

| field | Description |
| ----- | ----------- |
| `"data"` | Chunk ID. |
| `<uint32>` | Number of bytes of raw audio. |
| `<byte[]>` | PCM/ADPCM sample data. |

KotOR voice-over WAVs add a `"fact"` chunk with a 32-bit sample count, which PyKotor writes for compatibility (`io_wav.py:182-186`).

---

## KotOR SFX header

- SFX assets start with 470 bytes of obfuscated metadata (magic numbers plus filler `0x55`).  
- After this header, the file resumes at the `"RIFF"` signature described above.  
- When exporting SFX, PyKotor recreates the header verbatim so the game recognizes the asset (`io_wav.py:150-163`).  

**Reference:** [`vendor/reone/src/libs/audio/format/wavreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/audio/format/wavreader.cpp)  

---

## Encoding Details

- **PCM (`audio_format = 0x0001`)**: Most dialogue is 16-bit mono PCM, which streams directly through the engine mixer.  
- **IMA ADPCM (`audio_format = 0x0011`)**: Some ambient SFX use compressed ADPCM frames; when present, the `fmt` chunk includes the extra coefficient block defined by the WAV spec.  
- KotOR requires `block_align` and `bytes_per_sec` to match the values implied by the codec; mismatched headers can crash the in-engine decoder.  

External tooling such as SithCodec and `SWKotOR-Audio-Encoder` implement the same formats; PyKotor simply exposes the metadata so conversions stay lossless.

---

## Implementation Details

- **Binary Reader/Writer:** [`Libraries/PyKotor/src/pykotor/resource/formats/wav/io_wav.py`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/wav/io_wav.py)  
- **data [model](MDL-MDX-File-Format):** [`Libraries/PyKotor/src/pykotor/resource/formats/wav/wav_data.py`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/wav/wav_data.py)  
- **Reference Implementations:**  
  - [`vendor/reone/src/libs/audio/format/wavreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/audio/format/wavreader.cpp)  
  - [`vendor/SithCodec`](https://github.com/th3w1zard1/SithCodec) (encoding/decoding utility)  
  - [`vendor/SWKotOR-Audio-Encoder`](https://github.com/th3w1zard1/SWKotOR-Audio-Encoder)  

With this structure, WAV assets authored in PyKotor will play identically in the base game and in the other vendor tools.

---
