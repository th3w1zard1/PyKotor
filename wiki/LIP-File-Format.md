# KotOR [LIP](LIP-File-Format) [file](GFF-File-Format) [format](GFF-File-Format) Documentation

LIP ([LIP](LIP-File-Format) Synchronization) [files](GFF-File-Format) drive mouth [animation](MDL-MDX-File-Format#animation-header) for voiced dialogue. Each [file](GFF-File-Format) contains a compact series of [keyframes](MDL-MDX-File-Format#controller-structure) that map timestamps to discrete viseme (mouth shape) [indices](2DA-File-Format#row-labels) so that the engine can interpolate character [LIP](LIP-File-Format) movement while playing the companion [WAV](WAV-File-Format) line.

## Table of Contents

- [KotOR LIP File Format Documentation](#kotor-lip-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
  - [Binary Format](#binary-format)
    - [Header](#header)
    - [Keyframe Table](#keyframe-table)
  - [Mouth Shapes (Viseme Table)](#mouth-shapes-viseme-table)
  - [Animation Rules](#animation-rules)
  - [Implementation Details](#implementation-details)

---

## [file](GFF-File-Format) [structure](GFF-File-Format#file-structure) Overview

- [LIP files](LIP-File-Format) [ARE](GFF-File-Format#are-area) always binary (`"LIP V1.0"` signature) and contain only [animation](MDL-MDX-File-Format#animation-header) [data](GFF-File-Format#file-structure).  
- They [ARE](GFF-File-Format#are-area) paired with [WAV](WAV-File-Format) voice-over resources of identical duration; the [LIP](LIP-File-Format) `length` [field](GFF-File-Format#file-structure) must match the [WAV](WAV-File-Format) `data` playback time for glitch-free [animation](MDL-MDX-File-Format#animation-header).  
- [keyframes](MDL-MDX-File-Format#controller-structure) [ARE](GFF-File-Format#are-area) sorted chronologically and store a timestamp ([float](GFF-File-Format#float) seconds) plus a 1-[byte](GFF-File-Format#byte) viseme index (0–15).  
- The layout is identical across `vendor/reone`, `vendor/xoreos`, `vendor/Kotor.NET`, `vendor/KotOR.js`, and `vendor/mdlops`, so the [header](GFF-File-Format#file-header)/[keyframe](MDL-MDX-File-Format#controller-structure) [offsets](GFF-File-Format#file-structure) below [ARE](GFF-File-Format#are-area) cross-confirmed against those implementations.  

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/lip/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/lip)

**Vendor References:**

- [`vendor/reone/src/libs/graphics/format/lipreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/lipreader.cpp) - Complete C++ [LIP](LIP-File-Format) parser implementation
- [`vendor/xoreos/src/graphics/aurora/lipfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/graphics/aurora/lipfile.cpp) - Generic Aurora [LIP](LIP-File-Format) implementation (shared [format](GFF-File-Format))
- [`vendor/KotOR.js/src/resource/LIPObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/LIPObject.ts) - TypeScript [LIP](LIP-File-Format) parser with [animation](MDL-MDX-File-Format#animation-header) playback
- [`vendor/Kotor.NET/Kotor.NET/Formats/KotorLIP/LIP.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorLIP/LIP.cs) - .NET LIP reader/writer
- [`vendor/mdlops/mdlops/`](https://github.com/th3w1zard1/mdlops/tree/master/mdlops) - Legacy Python [LIP](LIP-File-Format) generation tools

**See Also:**

- [TLK File Format](TLK-File-Format) - [Talk Table](TLK-File-Format) containing voice-over references
- [WAV File Format](WAV-File-Format) - Audio [format](GFF-File-Format) paired with [LIP](LIP-File-Format) [files](GFF-File-Format)
- [GFF-DLG](GFF-DLG) - [dialogue files](GFF-File-Format#dlg-dialogue) that trigger [LIP](LIP-File-Format) [animations](MDL-MDX-File-Format#animation-header)

---

## Binary [format](GFF-File-Format)

### [header](GFF-File-Format#file-header)

| Name          | [type](GFF-File-Format#data-types)    | [offset](GFF-File-Format#file-structure) | [size](GFF-File-Format#file-structure) | Description |
| ------------- | ------- | ------ | ---- | ----------- |
| [file](GFF-File-Format) [type](GFF-File-Format#data-types)     | [char][GFF-File-Format#char](4) | 0 (0x00)   | 4    | Always `"LIP "` |
| [file](GFF-File-Format) Version  | [char][GFF-File-Format#char](4) | 4 (0x04)   | 4    | Always `"V1.0"` |
| Sound Length  | [float32](GFF-File-Format#float) | 8 (0x08)   | 4    | Duration in seconds (must equal [WAV](WAV-File-Format) length) |
| Entry [count](GFF-File-Format#file-structure)   | [uint32](GFF-File-Format#dword)  | 12 (0x0C)   | 4    | Number of [keyframes](MDL-MDX-File-Format#controller-structure) immediately following |

**Reference:** [`vendor/reone/src/libs/graphics/format/lipreader.cpp:27-42`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/lipreader.cpp#L27-L42)

### [keyframe](MDL-MDX-File-Format#controller-structure) Table

[keyframes](MDL-MDX-File-Format#controller-structure) follow immediately after the [header](GFF-File-Format#file-header); there is no padding.

| Name       | [type](GFF-File-Format#data-types)    | Offset (per entry) | [size](GFF-File-Format#file-structure) | Description |
| ---------- | ------- | ------------------ | ---- | ----------- |
| Timestamp  | [float32](GFF-File-Format#float) | 0 (0x00)               | 4    | Seconds from [animation](MDL-MDX-File-Format#animation-header) start |
| Shape      | [uint8](GFF-File-Format#byte)   | 4 (0x04)               | 1    | Viseme index (`0–15`) |

- Entries [ARE](GFF-File-Format#are-area) stored sequentially and **must** be sorted ascending by timestamp.  
- Libraries average multiple implementations to validate this layout (`vendor/reone`, `vendor/xoreos`, `vendor/KotOR.js`, `vendor/Kotor.NET`).  

**Reference:** [`vendor/KotOR.js/src/resource/LIPObject.ts:93-146`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/LIPObject.ts#L93-L146)

---

## Mouth Shapes (Viseme Table)

KotOR reuses the 16-shape Preston Blair [phoneme](https://en.wikipedia.org/wiki/Phoneme) set. Every implementation agrees on the [byte](GFF-File-Format#byte) [value](GFF-File-Format#data-types) assignments; KotOR.js only renames a few labels but the [indices](2DA-File-Format#row-labels) match.

| [value](GFF-File-Format#data-types) | Shape | Description |
| ----- | ----- | ----------- |
| 0 | NEUTRAL | Rest/closed mouth |
| 1 | EE | Teeth apart, wide smile (long “ee”) |
| 2 | EH | Relaxed mouth (“eh”) |
| 3 | AH | Mouth open (“ah/aa”) |
| 4 | OH | Rounded lips (“oh”) |
| 5 | OOH | Pursed lips (“oo”, “w”) |
| 6 | Y | Slight smile (“y”) |
| 7 | STS | Teeth touching (“s”, “z”, “ts”) |
| 8 | FV | Lower [LIP](LIP-File-Format) touches teeth (“f”, “v”) |
| 9 | NG | Tongue raised (“n”, “ng”) |
| 10 | TH | Tongue between teeth (“th”) |
| 11 | MPB | Lips closed (“m”, “p”, “b”) |
| 12 | TD | Tongue up (“t”, “d”) |
| 13 | SH | Rounded relaxed (“sh”, “ch”, “j”) |
| 14 | L | Tongue forward (“l”, “r”) |
| 15 | KG | Back of tongue raised (“k”, “g”, “h”) |

**Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/lip/lip_data.py:50-169`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lip/lip_data.py#L50-L169)

---

## [animation](MDL-MDX-File-Format#animation-header) Rules

- **[Interpolation](https://en.wikipedia.org/wiki/Interpolation):** The engine interpolates between consecutive [keyframes](https://en.wikipedia.org/wiki/Key_frame); PyKotor exposes `LIP.get_shapes()` to compute the left/right [visemes](https://en.wikipedia.org/wiki/Viseme) plus blend factor.  
  **Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/lip/lip_data.py:342-385`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lip/lip_data.py#L342-L385)
- **Sorting:** When adding frames, PyKotor removes existing entries at the same timestamp and keeps the list sorted.  
  **Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/lip/lip_data.py:305-323`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lip/lip_data.py#L305-L323)
- **Duration Alignment:** [LIP](LIP-File-Format) `length` is updated to the max timestamp so exported [animations](MDL-MDX-File-Format#animation-header) stay aligned with their [WAV](WAV-File-Format) line.  
  **Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/lip/lip_data.py:267-323`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lip/lip_data.py#L267-L323)
- **Generation:** Automated pipelines (MDLOps, KotORBlender) map phonemes to visemes via `LIPShape.from_phoneme()`, and the same mapping table appears in the vendor projects referenced above to keep authoring tools consistent.  

---

## Implementation Details

- **Binary Reader:** [`Libraries/PyKotor/src/pykotor/resource/formats/lip/io_lip.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lip/io_lip.py)  
- **[data](GFF-File-Format#file-structure) [model](MDL-MDX-File-Format):** [`Libraries/PyKotor/src/pykotor/resource/formats/lip/lip_data.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lip/lip_data.py)  
- **Reference Implementations:**  
  - [`vendor/reone/src/libs/graphics/format/lipreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/lipreader.cpp)  
  - [`vendor/xoreos/src/aurora/lipfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/lipfile.cpp)  
  - [`vendor/KotOR.js/src/resource/LIPObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/LIPObject.ts)  
  - [`vendor/Kotor.NET/Kotor.NET/Formats/KotorLIP/LIP.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorLIP/LIP.cs)  

The references above implement the same [header](GFF-File-Format#file-header) layout and [keyframe](MDL-MDX-File-Format#controller-structure) encoding, ensuring PyKotor stays compatible with the other toolchains.
