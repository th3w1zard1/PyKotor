# KotOR [TLK](TLK-File-Format) [file](GFF-File-Format) [format](GFF-File-Format) Documentation

This document provides a detailed description of the TLK ([Talk Table](TLK-File-Format)) [file](GFF-File-Format) [format](GFF-File-Format) used in Knights of the Old Republic (KotOR) games. [TLK files](TLK-File-Format) contain all text [strings](GFF-File-Format#cexostring) used in the game, both written and spoken, enabling easy localization by providing a lookup table from [string](GFF-File-Format#cexostring) reference numbers ([StrRef](TLK-File-Format#string-references-strref)) to localized text and associated voice-over audio [files](GFF-File-Format).

**For mod developers:** To modify [TLK files](TLK-File-Format) in your mods, see the [TSLPatcher TLKList Syntax Guide](TSLPatcher-TLKList-Syntax). For general modding information, see [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.).

**Related [formats](GFF-File-Format):** [TLK files](TLK-File-Format) [ARE](GFF-File-Format#are-area) referenced by [GFF files](GFF-File-Format) (especially [DLG](GFF-File-Format#dlg-dialogue) [dialogue files](GFF-File-Format#dlg-dialogue)), [2DA files](2DA-File-Format) for item names and descriptions, and [SSF files](SSF-File-Format) for character sound sets.

## Table of Contents

- [KotOR TLK File Format Documentation](#kotor-tlk-file-format-documentation)
  - [Table of Contents](#table-of-contents)
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

## [file](GFF-File-Format) [structure](GFF-File-Format#file-structure) Overview

[TLK files](TLK-File-Format) store localized [strings](GFF-File-Format#cexostring) in a binary [format](GFF-File-Format). The game loads [`dialog.tlk`](TLK-File-Format) at startup and references [strings](GFF-File-Format#cexostring) throughout the game using [StrRef](TLK-File-Format#string-references-strref) numbers ([array](2DA-File-Format) [indices](2DA-File-Format#row-labels)).

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/tlk/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/tlk/)

**Vendor References:**

- [`vendor/TSLPatcher/lib/site/Bioware/TLK.pm`](https://github.com/th3w1zard1/TSLPatcher/blob/master/lib/site/Bioware/TLK.pm) - Original Perl [TLK](TLK-File-Format) implementation from TSLPatcher
- [`vendor/reone/src/libs/resource/format/tlkreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/tlkreader.cpp) - Complete C++ [TLK](TLK-File-Format) reader implementation
- [`vendor/xoreos/src/aurora/talktable.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/talktable.cpp) - Generic Aurora [Talk Table](TLK-File-Format) implementation (shared [format](GFF-File-Format))
- [`vendor/KotOR.js/src/resource/TLKObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/TLKObject.ts) - TypeScript [TLK](TLK-File-Format) parser with localization support
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/TLKObject.cs`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/TLKObject.cs) - C# Unity [TLK](TLK-File-Format) loader
- [`vendor/Kotor.NET/Kotor.NET/Formats/KotorTLK/`](https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Formats/KotorTLK) - .NET TLK reader/writer with builder API
- [`vendor/xoreos-tools/src/aurora/talktable.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/aurora/talktable.cpp) - Command-line [TLK](TLK-File-Format) extraction and editing tools

**See Also:**

- [TSLPatcher TLKList Syntax](TSLPatcher-TLKList-Syntax) - Modding [TLK files](TLK-File-Format) with TSLPatcher
- [GFF File Format](GFF-File-Format) - Dialogue and templates that reference [TLK](TLK-File-Format) strings
- [SSF File Format](SSF-File-Format) - Sound sets that reference [TLK](TLK-File-Format) entries
- [2DA File Format](2DA-File-Format) - Game tables with name/description StrRefs

---

## Binary Format

### File Header

The file header is 20 bytes in size:

| Name                | [type](GFF-File-Format#data-types)    | [offset](GFF-File-Format#file-structure) | [size](GFF-File-Format#file-structure) | Description                                    |
| ------------------- | ------- | ------ | ---- | ---------------------------------------------- |
| [file](GFF-File-Format) [type](GFF-File-Format#data-types)           | [char][GFF-File-Format#char](4) | 0 (0x00) | 4    | Always `"TLK "` (space-padded)                  |
| [file](GFF-File-Format) Version        | [char][GFF-File-Format#char](4) | 4 (0x04) | 4    | `"V3.0"` for KotOR, `"V4.0"` for Jade Empire  |
| Language ID         | [int32](GFF-File-Format#int)   | 8 (0x08) | 4    | Language identifier (see [Localization](#localization)) |
| [string](GFF-File-Format#cexostring) [count](GFF-File-Format#file-structure)        | [int32](GFF-File-Format#int)   | 12 (0x0C) | 4    | Number of [string](GFF-File-Format#cexostring) entries in the [file](GFF-File-Format)           |
| [string](GFF-File-Format#cexostring) Entries [offset](GFF-File-Format#file-structure) | [int32](GFF-File-Format#int) | 16 (0x10) | 4    | [offset](GFF-File-Format#file-structure) to [string](GFF-File-Format#cexostring) entries array (typically 20)  |

**Reference**: [`vendor/reone/src/libs/resource/format/tlkreader.cpp:31-84`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/tlkreader.cpp#L31-L84)

### String Data Table

The string data table contains metadata for each [string](GFF-File-Format#cexostring) entry. Each entry is 40 bytes:

| Name              | [type](GFF-File-Format#data-types)      | [offset](GFF-File-Format#file-structure) | [size](GFF-File-Format#file-structure) | Description                                                      |
| ----------------- | --------- | ------ | ---- | ---------------------------------------------------------------- |
| [flags](GFF-File-Format#data-types)             | [uint32](GFF-File-Format#dword)    | 0 (0x00) | 4    | [bit](GFF-File-Format#data-types) [flags](GFF-File-Format#data-types): [bit](GFF-File-Format#data-types) 0=text present, [bit](GFF-File-Format#data-types) 1=sound present, [bit](GFF-File-Format#data-types) 2=sound length present |
| Sound [ResRef](GFF-File-Format#resref)      | [char][GFF-File-Format#char](16)  | 4 (0x04) | 16   | Voice-over audio filename ([null-terminated](https://en.cppreference.com/w/c/string/byte), max 16 chars)        |
| Volume Variance   | [uint32](GFF-File-Format#dword)    | 20 (0x14) | 4    | Unused in KotOR (always 0)                                      |
| Pitch Variance    | [uint32](GFF-File-Format#dword)    | 24 (0x18) | 4    | Unused in KotOR (always 0)                                      |
| [offset](GFF-File-Format#file-structure) to [string](GFF-File-Format#cexostring)  | [uint32](GFF-File-Format#dword)    | 28 (0x1C) | 4    | [offset](GFF-File-Format#file-structure) to [string](GFF-File-Format#cexostring) text (relative to [string](GFF-File-Format#cexostring) Entries [offset](GFF-File-Format#file-structure))       |
| [string](GFF-File-Format#cexostring) [size](GFF-File-Format#file-structure)       | [uint32](GFF-File-Format#dword)    | 32 (0x20) | 4    | Length of [string](GFF-File-Format#cexostring) text in bytes                                  |
| Sound Length      | [float](GFF-File-Format#float)     | 36 (0x24) | 4    | Duration of voice-over audio in seconds                         |

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorTLK/TLKBinaryStructure.cs:57-90`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorTLK/TLKBinaryStructure.cs#L57-L90)

**[flag](GFF-File-Format#data-types) [bits](GFF-File-Format#data-types):**

- **[bit](GFF-File-Format#data-types) 0 (0x0001)**: Text present - [string](GFF-File-Format#cexostring) has text content
- **[bit](GFF-File-Format#data-types) 1 (0x0002)**: Sound present - [string](GFF-File-Format#cexostring) has associated voice-over audio
- **[bit](GFF-File-Format#data-types) 2 (0x0004)**: Sound length present - sound length [field](GFF-File-Format#file-structure) is valid

**[flag](GFF-File-Format#data-types) Combinations:**

Common [flag](GFF-File-Format#data-types) patterns in KotOR [TLK files](TLK-File-Format):

| [flags](GFF-File-Format#data-types) | Hex | Description | Usage |
| ----- | --- | ----------- | ----- |
| `0x0001` | `0x01` | Text only | Menu options, item descriptions, non-voiced dialog |
| `0x0003` | `0x03` | Text + Sound | Voiced dialog lines (most common for party/NPC speech) |
| `0x0007` | `0x07` | Text + Sound + Length | Fully voiced with duration data (cutscenes, important dialog) |
| `0x0000` | `0x00` | Empty entry | Unused [StrRef](TLK-File-Format#string-references-strref) slots |

The engine uses these [flags](GFF-File-Format#data-types) to decide:

- Whether to display subtitles (Text present [flag](GFF-File-Format#data-types))
- Whether to play voice-over audio (Sound present [flag](GFF-File-Format#data-types))
- How long to wait before auto-advancing dialog (Sound length present [flag](GFF-File-Format#data-types))

Missing [flags](GFF-File-Format#data-types) [ARE](GFF-File-Format#are-area) treated as `false` - if Text present is not set, the [string](GFF-File-Format#cexostring) is treated as empty even if text [data](GFF-File-Format#file-structure) exists.

### [string](GFF-File-Format#cexostring) Entries

[string](GFF-File-Format#cexostring) entries follow the [string](GFF-File-Format#cexostring) [data](GFF-File-Format#file-structure) table:

| Name         | [type](GFF-File-Format#data-types)   | Description                                                      |
| ------------ | ------ | ---------------------------------------------------------------- |
| [string](GFF-File-Format#cexostring) Text  | [char](GFF-File-Format#char)[] | [null-terminated string](https://en.cppreference.com/w/c/string/byte) data (UTF-8 or Windows-1252 encoded)     |

[string](GFF-File-Format#cexostring) text is stored at the [offset](GFF-File-Format#file-structure) specified in the [string](GFF-File-Format#cexostring) [data](GFF-File-Format#file-structure) table entry. The encoding depends on the language ID (see [Localization](#localization)).

---

## TLKEntry [structure](GFF-File-Format#file-structure)

Each [TLK](TLK-File-Format) entry contains:

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/tlk/tlk_data.py:293-424`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tlk/tlk_data.py#L293-L424)

| Attribute        | [type](GFF-File-Format#data-types)   | Description                                                      |
| ---------------- | ------ | ---------------------------------------------------------------- |
| `text`           | str    | Localized text [string](GFF-File-Format#cexostring)                                            |
| `voiceover`      | [ResRef](GFF-File-Format#resref) | Voice-over audio filename ([WAV file](WAV-File-Format))                            |
| `text_present`   | bool   | Whether text content exists                                      |
| `sound_present`  | bool   | Whether voice-over audio exists                                  |
| `soundlength_present` | bool | Whether sound length is valid                                    |
| `sound_length`   | float  | Duration of voice-over audio in seconds                         |

---

## [string](GFF-File-Format#cexostring) References ([StrRef](TLK-File-Format#string-references-strref))

[string](GFF-File-Format#cexostring) references ([StrRef](TLK-File-Format#string-references-strref)) [ARE](GFF-File-Format#are-area) integer [indices](2DA-File-Format#row-labels) into the [TLK file](TLK-File-Format)'s entry [array](2DA-File-Format):

- **[StrRef](TLK-File-Format#string-references-strref) 0**: First entry in the [TLK file](TLK-File-Format)
- **[StrRef](TLK-File-Format#string-references-strref) -1**: No [string](GFF-File-Format#cexostring) reference (used to indicate missing/empty [strings](GFF-File-Format#cexostring))
- **[StrRef](TLK-File-Format#string-references-strref) N**: Nth entry (0-based indexing)

The game uses [StrRef](TLK-File-Format#string-references-strref) [values](GFF-File-Format#data-types) throughout [GFF files](GFF-File-Format), scripts, and other resources to reference localized text. When displaying text, the game looks up the [StrRef](TLK-File-Format#string-references-strref) in [`dialog.tlk`](TLK-File-Format) and displays the corresponding text.

### Custom [TLK](TLK-File-Format) [files](GFF-File-Format)

Mods can add custom [TLK files](TLK-File-Format) to extend available [strings](GFF-File-Format#cexostring):

**[dialog.tlk](TLK-File-Format) [structure](GFF-File-Format#file-structure):**

- Base game: [`dialog.tlk`](TLK-File-Format) (read-only, ~50,000-100,000 entries)
- Custom content: `dialogf.tlk` or custom [TLK files](TLK-File-Format) placed in override

**[StrRef](TLK-File-Format#string-references-strref) Ranges:**

- `0` to `~50,000`: Base game strings (varies by language)
- `16,777,216` (`0x01000000`) and above: Custom [TLK](TLK-File-Format) range (TSLPatcher convention)
- Negative [values](GFF-File-Format#data-types): Invalid/missing references

**Mod Tools Approach:**

TSLPatcher and similar tools use high [StrRef](TLK-File-Format#string-references-strref) ranges for custom [strings](GFF-File-Format#cexostring):

```plaintext
Base [StrRef](TLK-File-Format#string-references-strref):   0 - 50,000 ([dialog.tlk](TLK-File-Format))
Custom Range:  16777216+ (custom [TLK files](TLK-File-Format))
```

This avoids conflicts with base game [strings](GFF-File-Format#cexostring) and allows mods to add thousands of custom text entries without overwriting existing content.

**Multiple [TLK](TLK-File-Format) [files](GFF-File-Format):**

The game can load multiple [TLK](TLK-File-Format) [files](GFF-File-Format):

1. [`dialog.tlk`](TLK-File-Format) - Primary game text
2. `dialogf.tlk` - Female-specific variants (polish K1 only)

Priority: Custom TLKs → dialogf.tlk → [`dialog.tlk`](TLK-File-Format)

**Reference**: [`vendor/TSLPatcher/lib/site/Bioware/TLK.pm:31-123`](https://github.com/th3w1zard1/TSLPatcher/blob/master/lib/site/Bioware/TLK.pm#L31-L123)

---

## Localization

[TLK files](TLK-File-Format) support multiple languages through the Language ID [field](GFF-File-Format#file-structure):

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

**Note**: KotOR games typically ignore the Language ID [field](GFF-File-Format#file-structure) and always use [`dialog.tlk`](TLK-File-Format). The [field](GFF-File-Format#file-structure) is primarily used by modding tools to identify language.

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorTLK/TLKBinaryStructure.cs:63`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorTLK/TLKBinaryStructure.cs#L63)

---

## Implementation Details

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/tlk/io_tlk.py:19-115`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tlk/io_tlk.py#L19-L115)

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/tlk/io_tlk.py:117-178`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tlk/io_tlk.py#L117-L178)

**[TLK](TLK-File-Format) Class**: [`Libraries/PyKotor/src/pykotor/resource/formats/tlk/tlk_data.py:56-291`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tlk/tlk_data.py#L56-L291)

---

This documentation aims to provide a comprehensive overview of the KotOR [TLK file](TLK-File-Format) [format](GFF-File-Format), focusing on the detailed [file](GFF-File-Format) [structure](GFF-File-Format#file-structure) and [data](GFF-File-Format#file-structure) [formats](GFF-File-Format) used within the games.
