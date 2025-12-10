# KotOR TLK file format Documentation

This document provides a detailed description of the TLK (Talk Table) file format used in Knights of the Old Republic (KotOR) games. TLK files contain all text strings used in the game, both written and spoken, enabling easy localization by providing a lookup table from string reference numbers ([StrRef](TLK-File-Format#string-references-strref)) to localized text and associated voice-over audio files.

**For mod developers:** To modify TLK files in your mods, see the [TSLPatcher TLKList Syntax Guide](TSLPatcher-TLKList-Syntax). For general modding information, see [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.).

**Related formats:** TLK files [ARE](GFF-File-Format#are-area) referenced by [GFF files](GFF-File-Format) (especially [DLG](GFF-File-Format#dlg-dialogue) [dialogue files](GFF-File-Format#dlg-dialogue)), [2DA files](2DA-File-Format) for item names and descriptions, and [SSF files](SSF-File-Format) for character sound sets.

## Table of Contents

- KotOR TLK File Format Documentation
  - Table of Contents
  - [File Structure Overview](#file-structure-overview)
  - [Binary Format](#binary-format)
    - [File Header](#file-header)
    - [String Data Table](#string-data-table)
    - [String Entries](#string-entries)
  - [TLKEntry Structure](#tlkentry-structure)
  - [String References (StrRef)](#string-references-strref)
    - [Custom TLK Files](#custom-tlk-files)
  - [Localization](#localization)
  - [Implementation Details](#implementation-details)

---

## file structure Overview

TLK files store localized strings in a binary format. The game loads `dialog.tlk` at startup and references strings throughout the game using [StrRef](TLK-File-Format#string-references-strref) numbers (array indices).

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/tlk/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/tlk/)

**Vendor References:**

- [`vendor/TSLPatcher/lib/site/Bioware/TLK.pm`](https://github.com/th3w1zard1/TSLPatcher/blob/master/lib/site/Bioware/TLK.pm) - Original Perl TLK implementation from TSLPatcher
- [`vendor/reone/src/libs/resource/format/tlkreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/tlkreader.cpp) - Complete C++ TLK reader implementation
- [`vendor/xoreos/src/aurora/talktable.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/talktable.cpp) - Generic Aurora Talk Table implementation (shared format)
- [`vendor/KotOR.js/src/resource/TLKObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/TLKObject.ts) - TypeScript TLK parser with localization support
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/TLKObject.cs`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/TLKObject.cs) - C# Unity TLK loader
- [`vendor/Kotor.NET/Kotor.NET/Formats/KotorTLK/`](https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Formats/KotorTLK) - .NET TLK reader/writer with builder API
- [`vendor/xoreos-tools/src/aurora/talktable.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/aurora/talktable.cpp) - Command-line TLK extraction and editing tools

**See Also:**

- [TSLPatcher TLKList Syntax](TSLPatcher-TLKList-Syntax) - Modding TLK files with TSLPatcher
- [GFF File Format](GFF-File-Format) - Dialogue and templates that reference TLK strings
- [SSF File Format](SSF-File-Format) - Sound sets that reference TLK entries
- [2DA File Format](2DA-File-Format) - Game tables with name/description StrRefs

---

## Binary format

### file header

The file header is 20 bytes in size:

| Name                | type    | offset | size | Description                                    |
| ------------------- | ------- | ------ | ---- | ---------------------------------------------- |
| file type           | [char](GFF-File-Format#gff-data-types) | 0 (0x00) | 4    | Always `"TLK "` (space-padded)                  |
| file Version        | [char](GFF-File-Format#gff-data-types) | 4 (0x04) | 4    | `"V3.0"` for KotOR, `"V4.0"` for Jade Empire  |
| Language ID         | [int32](GFF-File-Format#gff-data-types)   | 8 (0x08) | 4    | Language identifier (see [Localization](#localization)) |
| string count        | [int32](GFF-File-Format#gff-data-types)   | 12 (0x0C) | 4    | Number of string entries in the file           |
| string Entries offset | [int32](GFF-File-Format#gff-data-types) | 16 (0x10) | 4    | offset to string entries array (typically 20)  |

**Reference**: [`vendor/reone/src/libs/resource/format/tlkreader.cpp:31-84`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/tlkreader.cpp#L31-L84)

### string data Table

The string data table contains metadata for each string entry. Each entry is 40 bytes:

| Name              | type      | offset | size | Description                                                      |
| ----------------- | --------- | ------ | ---- | ---------------------------------------------------------------- |
| [flags](GFF-File-Format#gff-data-types)             | [uint32](GFF-File-Format#gff-data-types)    | 0 (0x00) | 4    | bit [flags](GFF-File-Format#gff-data-types): bit 0=text present, bit 1=sound present, bit 2=sound length present |
| Sound [ResRef](GFF-File-Format#gff-data-types)      | [char](GFF-File-Format#gff-data-types)  | 4 (0x04) | 16   | Voice-over audio filename ([null-terminated](https://en.cppreference.com/w/c/string/byte), max 16 chars)        |
| Volume Variance   | [uint32](GFF-File-Format#gff-data-types)    | 20 (0x14) | 4    | Unused in KotOR (always 0)                                      |
| Pitch Variance    | [uint32](GFF-File-Format#gff-data-types)    | 24 (0x18) | 4    | Unused in KotOR (always 0)                                      |
| offset to string  | [uint32](GFF-File-Format#gff-data-types)    | 28 (0x1C) | 4    | offset to string text (relative to string Entries offset)       |
| string size       | [uint32](GFF-File-Format#gff-data-types)    | 32 (0x20) | 4    | Length of string text in bytes                                  |
| Sound Length      | [float](GFF-File-Format#gff-data-types)     | 36 (0x24) | 4    | Duration of voice-over audio in seconds                         |

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorTLK/TLKBinaryStructure.cs:57-90`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorTLK/TLKBinaryStructure.cs#L57-L90)

**[flag](GFF-File-Format#gff-data-types) bits:**

- **bit 0 (0x0001)**: Text present - string has text content
- **bit 1 (0x0002)**: Sound present - string has associated voice-over audio
- **bit 2 (0x0004)**: Sound length present - sound length field is valid

**[flag](GFF-File-Format#gff-data-types) Combinations:**

Common [flag](GFF-File-Format#gff-data-types) patterns in KotOR TLK files:

| [flags](GFF-File-Format#gff-data-types) | Hex | Description | Usage |
| ----- | --- | ----------- | ----- |
| `0x0001` | `0x01` | Text only | Menu options, item descriptions, non-voiced dialog |
| `0x0003` | `0x03` | Text + Sound | Voiced dialog lines (most common for party/NPC speech) |
| `0x0007` | `0x07` | Text + Sound + Length | Fully voiced with duration data (cutscenes, important dialog) |
| `0x0000` | `0x00` | Empty entry | Unused [StrRef](TLK-File-Format#string-references-strref) slots |

The engine uses these [flags](GFF-File-Format#gff-data-types) to decide:

- Whether to display subtitles (Text present [flag](GFF-File-Format#gff-data-types))
- Whether to play voice-over audio (Sound present [flag](GFF-File-Format#gff-data-types))
- How long to wait before auto-advancing dialog (Sound length present [flag](GFF-File-Format#gff-data-types))

Missing [flags](GFF-File-Format#gff-data-types) [ARE](GFF-File-Format#are-area) treated as `false` - if Text present is not set, the string is treated as empty even if text data exists.

### string Entries

string entries follow the string data table:

| Name         | type   | Description                                                      |
| ------------ | ------ | ---------------------------------------------------------------- |
| string Text  | [char](GFF-File-Format#gff-data-types)[] | [null-terminated string](https://en.cppreference.com/w/c/string/byte) data (UTF-8 or Windows-1252 encoded)     |

string text is stored at the offset specified in the string data table entry. The encoding depends on the language ID (see [Localization](#localization)).

---

## TLKEntry structure

Each TLK entry contains:

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/tlk/tlk_data.py:293-424`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tlk/tlk_data.py#L293-L424)

| Attribute        | type   | Description                                                      |
| ---------------- | ------ | ---------------------------------------------------------------- |
| `text`           | str    | Localized text string                                            |
| `voiceover`      | [ResRef](GFF-File-Format#gff-data-types) | Voice-over audio filename ([WAV file](WAV-File-Format))                            |
| `text_present`   | bool   | Whether text content exists                                      |
| `sound_present`  | bool   | Whether voice-over audio exists                                  |
| `soundlength_present` | bool | Whether sound length is valid                                    |
| `sound_length`   | float  | Duration of voice-over audio in seconds                         |

---

## string References (StrRef)

string references (StrRef) [ARE](GFF-File-Format#are-area) integer indices into the TLK file's entry array:

- **StrRef 0**: First entry in the TLK file
- **StrRef -1**: No string reference (used to indicate missing/empty strings)
- **StrRef N**: Nth entry (0-based indexing)

The game uses StrRef values throughout [GFF files](GFF-File-Format), scripts, and other resources to reference localized text. When displaying text, the game looks up the StrRef in `dialog.tlk` and displays the corresponding text.

### Custom TLK files

Mods can add custom TLK files to extend available strings:

**dialog.tlk structure:**

- Base game: `dialog.tlk` (read-only, ~50,000-100,000 entries)
- Custom content: `dialogf.tlk` or custom TLK files placed in override

**[StrRef](TLK-File-Format#string-references-strref) Ranges:**

- `0` to `~50,000`: Base game strings (varies by language)
- `16,777,216` (`0x01000000`) and above: Custom TLK range (TSLPatcher convention)
- Negative values: Invalid/missing references

**Mod Tools Approach:**

TSLPatcher and similar tools use high [StrRef](TLK-File-Format#string-references-strref) ranges for custom strings:

```plaintext
Base [StrRef](TLK-File-Format#string-references-strref):   0 - 50,000 (dialog.tlk)
Custom Range:  16777216+ (custom TLK files)
```

This avoids conflicts with base game strings and allows mods to add thousands of custom text entries without overwriting existing content.

**Multiple TLK files:**

The game can load multiple TLK files:

1. `dialog.tlk` - Primary game text
2. `dialogf.tlk` - Female-specific variants (polish K1 only)

Priority: Custom TLKs → dialogf.tlk → `dialog.tlk`

**Reference**: [`vendor/TSLPatcher/lib/site/Bioware/TLK.pm:31-123`](https://github.com/th3w1zard1/TSLPatcher/blob/master/lib/site/Bioware/TLK.pm#L31-L123)

---

## Localization

TLK files support multiple languages through the Language ID field:

| Language ID | Language | Encoding      |
| ----------- | -------- | ------------- |
| 0           | English  | Windows-1252  |
| 1           | French   | Windows-1252  |
| 2           | German   | Windows-1252  |
| 3           | Italian  | Windows-1252  |
| 4           | Spanish  | Windows-1252  |
| 5           | Polish   | Windows-1250  |
| 6           | Korean   | UTF-8         |
| 7           | Chinese  | UTF-8         |
| 8           | Japanese | UTF-8         |

**Note**: KotOR games typically ignore the Language ID field and always use `dialog.tlk`. The field is primarily used by modding tools to identify language.

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorTLK/TLKBinaryStructure.cs:63`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorTLK/TLKBinaryStructure.cs#L63)

---

## Implementation Details

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/tlk/io_tlk.py:19-115`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tlk/io_tlk.py#L19-L115)

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/tlk/io_tlk.py:117-178`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tlk/io_tlk.py#L117-L178)

**TLK Class**: [`Libraries/PyKotor/src/pykotor/resource/formats/tlk/tlk_data.py:56-291`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tlk/tlk_data.py#L56-L291)

---

This documentation aims to provide a comprehensive overview of the KotOR TLK file format, focusing on the detailed file structure and data formats used within the games.
