# KotOR [WAV](WAV-File-Format) [file](GFF-File-Format) [format](GFF-File-Format) Documentation

KotOR stores both standard [WAV](WAV-File-Format) voice-over lines and Bioware-obfuscated sound-effect [files](GFF-File-Format). Voice-over assets [ARE](GFF-File-Format#are-area) regular RIFF containers with PCM [headers](GFF-File-Format#file-header), while SFX assets prepend a 470-[byte](GFF-File-Format#byte) custom block before the RIFF [data](GFF-File-Format#file-structure). PyKotor handles both variants transparently.

## Table of Contents

- [KotOR WAV File Format Documentation](#kotor-wav-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Types](#file-types)
  - [Standard RIFF/WAVE Structure](#standard-riffwave-structure)
    - [Format Chunk](#format-chunk)
    - [Data Chunk](#data-chunk)
  - [KotOR SFX Header](#kotor-sfx-header)
  - [Encoding Details](#encoding-details)
  - [Implementation Details](#implementation-details)

---

## [file](GFF-File-Format) [types](GFF-File-Format#data-types)

| [type](GFF-File-Format#data-types) | Usage | Description |
| ---- | ----- | ----------- |
| **VO (Voice-over)** | Dialogue lines (`*.wav` referenced by [TLK](TLK-File-Format) [StrRefs](TLK-File-Format#string-references-strref)). | Plain RIFF/WAVE PCM [files](GFF-File-Format) readable by any media player. |
| **SFX (Sound effects)** | Combat, UI, ambience, `.wav` [files](GFF-File-Format) under `StreamSounds`/`SFX`. | Contains a Bioware 470-[byte](GFF-File-Format#byte) obfuscation [header](GFF-File-Format#file-header) followed by the same RIFF [data](GFF-File-Format#file-structure). |

PyKotor exposes these via the `WAVType` enum (`VO` vs. `SFX`) so tools know whether to insert/remove the proprietary header (`io_wav.py:52-121`).

---

## Standard RIFF/WAVE [structure](GFF-File-Format#file-structure)

KotOR sticks to the canonical RIFF chunk order:

| [offset](GFF-File-Format#file-structure) | [field](GFF-File-Format#file-structure) | Description |
| ------ | ----- | ----------- |
| 0 (0x00) | `"RIFF"` | Chunk ID |
| 4 (0x04) | `<uint32>` | [file](GFF-File-Format) [size](GFF-File-Format#file-structure) minus 8 |
| 8 (0x08) | `"WAVE"` | [format](GFF-File-Format) tag |
| 12 (0x0C) | `"fmt "` | [format](GFF-File-Format) chunk ID |
| 16 (0x10) | `<uint32>` | [format](GFF-File-Format) chunk size (usually 0x10) |
| … | See below | |

### [format](GFF-File-Format) Chunk

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
| ----- | ---- | ----------- |
| `audio_format` | uint16 | `0x0001` for PCM, `0x0011` for IMA ADPCM. |
| `channels` | uint16 | 1 (mono) or 2 (stereo). |
| `sample_rate` | uint32 | Typically 22050 Hz (SFX) or 44100 Hz (VO). |
| `bytes_per_sec` | uint32 | `sample_rate × block_align`. |
| `block_align` | uint16 | Bytes per sample frame. |
| `bits_per_sample` | uint16 | 8 or 16 for PCM. |
| `extra_bytes` | … | Present only when `fmt_size > 0x10` (e.g., ADPCM coefficients). |

### [data](GFF-File-Format#file-structure) Chunk

After the `fmt` chunk (and any optional `fact` chunk), the `"data"` chunk begins:

| [field](GFF-File-Format#file-structure) | Description |
| ----- | ----------- |
| `"data"` | Chunk ID. |
| `<uint32>` | Number of bytes of raw audio. |
| `<byte[]>` | PCM/ADPCM sample [data](GFF-File-Format#file-structure). |

KotOR voice-over WAVs add a `"fact"` chunk with a 32-[bit](GFF-File-Format#data-types) sample [count](GFF-File-Format#file-structure), which PyKotor writes for compatibility (`io_wav.py:182-186`).

---

## KotOR SFX [header](GFF-File-Format#file-header)

- SFX assets start with 470 bytes of obfuscated metadata (magic numbers plus filler `0x55`).  
- After this [header](GFF-File-Format#file-header), the [file](GFF-File-Format) resumes at the `"RIFF"` signature described above.  
- When exporting SFX, PyKotor recreates the [header](GFF-File-Format#file-header) verbatim so the game recognizes the asset (`io_wav.py:150-163`).  

**Reference:** [`vendor/reone/src/libs/audio/format/wavreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/audio/format/wavreader.cpp)  

---

## Encoding Details

- **PCM (`audio_format = 0x0001`)**: Most dialogue is 16-[bit](GFF-File-Format#data-types) mono PCM, which streams directly through the engine mixer.  
- **IMA ADPCM (`audio_format = 0x0011`)**: Some ambient SFX use compressed ADPCM frames; when present, the `fmt` chunk includes the extra coefficient block defined by the [WAV](WAV-File-Format) spec.  
- KotOR requires `block_align` and `bytes_per_sec` to match the [values](GFF-File-Format#data-types) implied by the codec; mismatched [headers](GFF-File-Format#file-header) can crash the in-engine decoder.  

External tooling such as SithCodec and `SWKotOR-Audio-Encoder` implement the same [formats](GFF-File-Format); PyKotor simply exposes the metadata so conversions stay lossless.

---

## Implementation Details

- **Binary Reader/Writer:** [`Libraries/PyKotor/src/pykotor/resource/formats/wav/io_wav.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/wav/io_wav.py)  
- **[data](GFF-File-Format#file-structure) [model](MDL-MDX-File-Format):** [`Libraries/PyKotor/src/pykotor/resource/formats/wav/wav_data.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/wav/wav_data.py)  
- **Reference Implementations:**  
  - [`vendor/reone/src/libs/audio/format/wavreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/audio/format/wavreader.cpp)  
  - [`vendor/SithCodec`](https://github.com/th3w1zard1/SithCodec) (encoding/decoding utility)  
  - [`vendor/SWKotOR-Audio-Encoder`](https://github.com/th3w1zard1/SWKotOR-Audio-Encoder)  

With this [structure](GFF-File-Format#file-structure), [WAV](WAV-File-Format) assets authored in PyKotor will play identically in the base game and in the other vendor tools.

---
