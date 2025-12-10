# KotOR [SSF](SSF-File-Format) [file](GFF-File-Format) [format](GFF-File-Format) Documentation

This document provides a detailed description of the SSF ([sound set files](SSF-File-Format)) [file](GFF-File-Format) [format](GFF-File-Format) used in Knights of the Old Republic (KotOR) games. [SSF files](SSF-File-Format) contain mappings from sound event [types](GFF-File-Format#gff-data-types) to [string](GFF-File-Format#gff-data-types) references ([StrRefs](TLK-File-Format#string-references-strref)) in the [TLK file](TLK-File-Format).

**For mod developers:** To modify [SSF files](SSF-File-Format) in your mods, see the [TSLPatcher SSFList Syntax Guide](TSLPatcher-SSFList-Syntax). For general modding information, see [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.).

**Related [formats](GFF-File-Format):** [SSF](SSF-File-Format) [files](GFF-File-Format) reference [TLK files](TLK-File-Format) for [string](GFF-File-Format#gff-data-types) references ([StrRefs](TLK-File-Format#string-references-strref)) that point to the actual sound text [strings](GFF-File-Format#gff-data-types).

## Table of Contents

- [KotOR SSF File Format Documentation](#kotor-ssf-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
  - [Binary Format](#binary-format)
    - [File Header](#file-header)
    - [Sound Table](#sound-table)
  - [Sound Event Types](#sound-event-types)
  - [Implementation Details](#implementation-details)

---

## [file](GFF-File-Format) [structure](GFF-File-Format#file-structure-overview) Overview

[SSF files](SSF-File-Format) define a set of 28 sound effects that creatures can play during various game events (battle cries, pain grunts, selection sounds, etc.). The [StrRefs](TLK-File-Format#string-references-strref) point to entries in [`dialog.tlk`](TLK-File-Format) which contain the actual [WAV file](WAV-File-Format) references.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/ssf/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/ssf/)

**Vendor References:**

- [`vendor/reone/src/libs/resource/format/ssfreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/ssfreader.cpp) - Complete C++ [SSF](SSF-File-Format) reader implementation
- [`vendor/xoreos/src/aurora/ssffile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/ssffile.cpp) - Generic Aurora [SSF](SSF-File-Format) implementation (shared [format](GFF-File-Format))
- [`vendor/KotOR.js/src/resource/SSFObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/SSFObject.ts) - TypeScript [SSF](SSF-File-Format) parser
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/SSFObject.cs`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/SSFObject.cs) - C# Unity [SSF](SSF-File-Format) loader
- [`vendor/Kotor.NET/Kotor.NET/Formats/KotorSSF/`](https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Formats/KotorSSF) - .NET SSF reader/writer

**See Also:**

- [TSLPatcher SSFList Syntax](TSLPatcher-SSFList-Syntax) - Modding [SSF files](SSF-File-Format) with TSLPatcher
- [TLK File Format](TLK-File-Format) - [Talk Table](TLK-File-Format) containing actual sound references
- [Bioware Aurora SSF Format](Bioware-Aurora-SSF) - Official BioWare specification
- [GFF-UTC](GFF-UTC) - [creature templates](GFF-File-Format#utc-creature) that reference [SSF](SSF-File-Format) [files](GFF-File-Format)
- [2DA-soundset](2DA-soundset) - Sound set definitions table

---

## Binary [format](GFF-File-Format)

### [file](GFF-File-Format) [header](GFF-File-Format#file-header)

The [file](GFF-File-Format) [header](GFF-File-Format#file-header) is 12 bytes in [size](GFF-File-Format#file-structure-overview):

| Name                | [type](GFF-File-Format#data-types)    | [offset](GFF-File-Format#file-structure-overview) | [size](GFF-File-Format#file-structure-overview) | Description                                    |
| ------------------- | ------- | ------ | ---- | ---------------------------------------------- |
| [file](GFF-File-Format) [type](GFF-File-Format#data-types)           | [[char](GFF-File-Format#gff-data-types)][GFF-File-Format#char](4) | 0 (0x00) | 4    | Always `"SSF "` (space-padded)                 |
| [file](GFF-File-Format) Version        | [[char](GFF-File-Format#gff-data-types)][GFF-File-Format#char](4) | 4 (0x04) | 4    | Always `"V1.1"`                                 |
| [offset](GFF-File-Format#file-structure-overview) to Sound Table | [uint32](GFF-File-Format#gff-data-types) | 8 (0x08) | 4    | [offset](GFF-File-Format#file-structure-overview) to sound table (typically 12)          |

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorSSF/SSFBinaryStructure.cs:10-91`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorSSF/SSFBinaryStructure.cs#L10-L91)

### Sound Table

The sound table contains 28 [StrRef](TLK-File-Format#string-references-strref) entries (112 bytes total):

| Name              | [type](GFF-File-Format#data-types)   | [offset](GFF-File-Format#file-structure-overview) | [size](GFF-File-Format#file-structure-overview) | Description                                                      |
| ----------------- | ------ | ------ | ---- | ---------------------------------------------------------------- |
| [StrRef](TLK-File-Format#string-references-strref) [array](2DA-File-Format)      | [int32](GFF-File-Format#gff-data-types)[] | 0 (0x00) | 4×28 | [array](2DA-File-Format) of 28 [StrRef](TLK-File-Format#string-references-strref) values (one per sound event [type](GFF-File-Format#data-types))            |

Each entry is a [StrRef](TLK-File-Format#string-references-strref) ([string](GFF-File-Format#gff-data-types) reference) into [`dialog.tlk`](TLK-File-Format). [value](GFF-File-Format#gff-data-types) `-1` indicates no sound for that event [type](GFF-File-Format#data-types).

**Reference**: [`vendor/reone/src/libs/resource/format/ssfreader.cpp:31`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/ssfreader.cpp#L31)

---

## Sound Event [types](GFF-File-Format#gff-data-types)

The 28 sound event [types](GFF-File-Format#gff-data-types) correspond to [array](2DA-File-Format) [indices](2DA-File-Format#row-labels):

| [index](2DA-File-Format#row-labels) | Event [type](GFF-File-Format#data-types)          | Description                                                      |
| ----- | ------------------- | ---------------------------------------------------------------- |
| 0     | BATTLE_CRY_1        | First battle cry                                                 |
| 1     | BATTLE_CRY_2        | Second battle cry                                                |
| 2     | BATTLE_CRY_3        | Third battle cry                                                 |
| 3     | SELECT_1            | First selection sound                                             |
| 4     | SELECT_2             | Second selection sound                                            |
| 5     | SELECT_3             | Third selection sound                                             |
| 6     | ATTACK_1             | First attack sound                                                |
| 7     | ATTACK_2             | Second attack sound                                               |
| 8     | ATTACK_3             | Third attack sound                                               |
| 9     | PAIN_1               | First pain grunt                                                  |
| 10    | PAIN_2               | Second pain grunt                                                 |
| 11    | PAIN_3               | Third pain grunt                                                  |
| 12    | LOW_HEALTH           | Low health warning                                                |
| 13    | DEAD                 | Death sound                                                       |
| 14    | CRITICAL_HIT         | Critical hit sound                                                |
| 15    | IMMUNE               | Immune to attack sound                                            |
| 16    | LAYING_MINE          | Laying mine sound                                                 |
| 17    | DISARM_MINE          | Disarming mine sound                                              |
| 18    | STUN                 | Stunned sound                                                     |
| 19    | UNLOCK_DOOR          | Unlocking door sound                                              |
| 20    | LOCK_DOOR            | Locking door sound                                                |
| 21    | UNLOCK_CONTAINER     | Unlocking container sound                                         |
| 22    | LOCK_CONTAINER       | Locking container sound                                          |
| 23    | UNLOCKABLE           | Unlockable object sound                                           |
| 24    | LOCKED               | Locked object sound                                               |
| 25    | ELEVATOR_MOVING       | Elevator moving sound                                             |
| 26    | WHIRL_WIND            | Whirlwind sound                                                   |
| 27    | POISONED              | Poisoned sound                                                    |

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/ssf/ssf_data.py:50-258`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ssf/ssf_data.py#L50-L258)

---

## Implementation Details

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/ssf/io_ssf.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/ssf/io_ssf.py)

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/ssf/io_ssf.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/ssf/io_ssf.py)

**[SSF](SSF-File-Format) Class**: [`Libraries/PyKotor/src/pykotor/resource/formats/ssf/ssf_data.py:50-258`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ssf/ssf_data.py#L50-L258)

---

This documentation aims to provide a comprehensive overview of the KotOR [SSF file](SSF-File-Format) [format](GFF-File-Format), focusing on the detailed [file](GFF-File-Format) [structure](GFF-File-Format#file-structure-overview) and [data](GFF-File-Format#file-structure-overview) [formats](GFF-File-Format) used within the games.
