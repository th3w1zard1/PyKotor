# KotOR [ERF](ERF-File-Format) file format Documentation

This document provides a detailed description of the ERF (Encapsulated Resource file) file format used in Knights of the Old Republic (KotOR) games. [ERF files](ERF-File-Format) [ARE](GFF-File-Format#are-area) [self-contained archives](ERF-File-Format) used for modules, save games, [texture](TPC-File-Format) packs, and hak paks.

## Table of Contents

- KotOR ERF file format Documentation
  - Table of Contents
  - [file structure Overview](#file-structure-overview)
  - [Binary Format](#binary-format)
    - [file header](#file-header)
    - [Localized string List](#localized-string-list)
    - [KEY List](#key-list)
    - [Resource List](#resource-list)
    - [Resource data](#resource-data)
    - [MOD/NWM file format Quirk: Blank data Block](#modnwm-file-format-quirk-blank-data-block)
  - [ERF Variants](#erf-variants)
    - [MOD Files (module archives)](#mod-files-module-archives)
    - [SAV Files (save game archives)](#sav-files-save-game-archives)
    - [HAK Files (Override Paks)](#hak-files-override-paks)
    - [ERF Files (Generic Archives)](#erf-files-generic-archives)
  - [Implementation Details](#implementation-details)

---

## file structure Overview

[ERF files](ERF-File-Format) [ARE](GFF-File-Format#are-area) [self-contained archives](ERF-File-Format) that store both resource names ([ResRefs](GFF-File-Format#gff-data-types)) and data in the same file. Unlike [BIF files](BIF-File-Format) which require a [KEY file](KEY-File-Format) for filename lookups, [ERF](ERF-File-Format) files include [ResRef](GFF-File-Format#gff-data-types) information directly in the [archive](ERF-File-Format).

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/erf/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/erf/)

**Vendor References:**

- [`vendor/reone/src/libs/resource/format/erfreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/erfreader.cpp) - Complete C++ [ERF](ERF-File-Format) reader implementation with MOD/SAV/HAK support
- [`vendor/reone/include/reone/resource/format/erfreader.h`](https://github.com/th3w1zard1/reone/blob/master/include/reone/resource/format/erfreader.h) - [ERF](ERF-File-Format) reader type definitions
- [`vendor/xoreos/src/aurora/erffile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/erffile.cpp) - Generic Aurora [ERF](ERF-File-Format) implementation (shared format across KotOR, NWN, and other Aurora games)
- [`vendor/KotOR.js/src/resource/ERFObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/ERFObject.ts) - TypeScript [ERF](ERF-File-Format) parser with streaming support
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/ERFObject.cs`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/ERFObject.cs) - C# Unity [ERF](ERF-File-Format) loader
- [`vendor/Kotor.NET/Kotor.NET/Formats/KotorERF/`](https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Formats/KotorERF) - .NET ERF reader/writer with builder API
- [`vendor/xoreos-tools/src/aurora/erffile.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/aurora/erffile.cpp) - Command-line [ERF](ERF-File-Format) extraction tools

**See Also:**

- [BIF File Format](BIF-File-Format) - Alternative archive format used with [KEY](KEY-File-Format) files
- [KEY File Format](KEY-File-Format) - index file for [BIF archives](BIF-File-Format)
- [GFF File Format](GFF-File-Format) - Common content type stored in [ERF](ERF-File-Format) archives
- [RIM File Format](ERF-File-Format) - Similar archive format for area resources

---

## [Binary Format](https://en.wikipedia.org/wiki/Binary_file)

### file header

The file header is 160 bytes in size:

| Name                      | type    | offset | size | Description                                    |
| ------------------------- | ------- | ------ | ---- | ---------------------------------------------- |
| file type                 | [char](GFF-File-Format#gff-data-types) | 0 (0x00) | 4    | `"ERF "`, `"MOD "`, `"SAV "`, or `"HAK "`     |
| file Version              | [char](GFF-File-Format#gff-data-types) | 4 (0x04) | 4    | Always `"V1.0"`                                 |
| Language count            | [uint32](GFF-File-Format#gff-data-types)  | 8 (0x08) | 4    | Number of localized string entries             |
| Localized string size     | [uint32](GFF-File-Format#gff-data-types)  | 12 (0x0C) | 4    | Total size of localized string data in bytes   |
| Entry count               | [uint32](GFF-File-Format#gff-data-types)  | 16 (0x10) | 4    | Number of resources in the archive              |
| offset to Localized string List | [uint32](GFF-File-Format#gff-data-types) | 20 (0x14) | 4 | offset to localized string entries             |
| offset to [KEY](KEY-File-Format) List        | [uint32](GFF-File-Format#gff-data-types)  | 24 (0x18) | 4    | offset to [KEY](KEY-File-Format) entries array                    |
| offset to Resource List   | [uint32](GFF-File-Format#gff-data-types)  | 28 (0x1C) | 4    | offset to resource entries array                |
| Build Year                | [uint32](GFF-File-Format#gff-data-types)  | 32 (0x20) | 4    | Build year (years since 1900)                   |
| Build Day                 | [uint32](GFF-File-Format#gff-data-types)  | 36 (0x24) | 4    | Build day (days since Jan 1)                   |
| Description [StrRef](TLK-File-Format#string-references-strref)        | [uint32](GFF-File-Format#gff-data-types)  | 40 (0x28) | 4    | [TLK](TLK-File-Format) string reference for description           |
| Reserved                  | [byte](GFF-File-Format#gff-data-types) | 44 (0x2C)  | 116  | Padding (usually zeros)                         |

**Build Date fields:**

The Build Year and Build Day fields timestamp when the [ERF file](ERF-File-Format) was created:

- **Build Year**: Years since 1900 (e.g., `103` = year 2003)
- **Build Day**: Day of year (1-365/366, with January 1 = day 1)

These timestamps [ARE](GFF-File-Format#are-area) primarily informational and used by development tools to track module versions. The game engine doesn't rely on them for functionality.

**Example Calculation:**

```plaintext
Build Year: 103 → 1900 + 103 = 2003
Build Day: 247 → September 4th (the 247th day of 2003)
```

Most mod tools either zero out these fields or set them to the current date when creating/modifying [ERF files](ERF-File-Format).

**Description [StrRef](TLK-File-Format#string-references-strref) values by file type:**

The Description [StrRef](TLK-File-Format#string-references-strref) field (offset 0x0028 / 0x28) varies depending on the [ERF](ERF-File-Format) variant:

- **MOD files**: `-1` (no [TLK](TLK-File-Format) reference, uses localized strings instead)
- **SAV files**: `0` (typically no description)
- **NWM files**: `-1` (**Neverwinter Nights module format, NOT used in KotOR**)
- **[ERF](ERF-File-Format)/HAK files**: Unpredictable (may contain valid [StrRef](TLK-File-Format#string-references-strref) or `-1`)

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs:11-46`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs#L11-L46)  
**Reference**: [`vendor/xoreos-docs/specs/torlack/mod.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/mod.html) - Tim Smith (Torlack)'s reverse-engineered [ERF](ERF-File-Format) format documentation

### Localized string List

Localized strings provide descriptions in multiple languages:

| Name         | type    | size | Description                                                      |
| ------------ | ------- | ---- | ---------------------------------------------------------------- |
| Language ID  | [uint32](GFF-File-Format#gff-data-types)  | 4    | Language identifier (see Language enum)                          |
| string size  | [uint32](GFF-File-Format#gff-data-types)  | 4    | Length of string in bytes                                       |
| string data  | [char](GFF-File-Format#gff-data-types)[]  | N    | UTF-8 encoded text                                               |

**Localized string Usage:**

[ERF](ERF-File-Format) localized strings provide multi-language descriptions for the archive itself. These [ARE](GFF-File-Format#are-area) primarily used in MOD files to display module names and descriptions in the game's module selection screen.

**Language IDs:**

- `0` = English
- `1` = French  
- `2` = German
- `3` = Italian
- `4` = Spanish
- `5` = Polish
- Additional languages for Asian releases

**Important Notes:**

- Most [ERF files](ERF-File-Format) have zero localized strings (Language count = 0)
- MOD files may include localized module names for the load screen
- Localized strings [ARE](GFF-File-Format#are-area) optional metadata and don't affect resource access
- The Description [StrRef](TLK-File-Format#string-references-strref) field (in header) provides an alternative via [TLK](TLK-File-Format) reference

**Reference**: [`vendor/reone/src/libs/resource/format/erfreader.cpp:47-65`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/erfreader.cpp#L47-L65)

### [KEY](KEY-File-Format) List

Each [KEY](KEY-File-Format) entry is 24 bytes and maps ResRefs to resource indices:

| Name        | type     | offset | size | Description                                                      |
| ----------- | -------- | ------ | ---- | ---------------------------------------------------------------- |
| [ResRef](GFF-File-Format#gff-data-types)      | [char](GFF-File-Format#gff-data-types) | 0 (0x00) | 16   | Resource filename (null-padded, max 16 chars)                    |
| Resource ID | [uint32](GFF-File-Format#gff-data-types)   | 16 (0x10) | 4    | index into resource list                                         |
| Resource type | [uint16](GFF-File-Format#gff-data-types) | 20 (0x14) | 2    | Resource type identifier                                         |
| Unused      | [uint16](GFF-File-Format#gff-data-types)   | 22 (0x16) | 2    | Padding                                                           |

**[ResRef](GFF-File-Format#gff-data-types) Padding Notes:**

Resource names [ARE](GFF-File-Format#are-area) padded with NULL bytes to 16 characters, but [ARE](GFF-File-Format#are-area) not necessarily [null-terminated](https://en.cppreference.com/w/c/string/byte). If a resource name is exactly 16 characters long, no [null terminator](https://en.cppreference.com/w/c/string/byte) exists. Resource names can be mixed case, though most [ARE](GFF-File-Format#are-area) lowercase in practice.

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs:115-168`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs#L115-L168)  
**Reference**: [`vendor/xoreos-docs/specs/torlack/mod.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/mod.html) - Resource structure details and [ResRef](GFF-File-Format#gff-data-types) padding notes

### Resource List

Each resource entry is 8 bytes:

| Name          | type   | offset | size | Description                                                      |
| ------------- | ------ | ------ | ---- | ---------------------------------------------------------------- |
| offset to data | [uint32](GFF-File-Format#gff-data-types) | 0 (0x00) | 4    | offset to resource data in file                                  |
| Resource size | [uint32](GFF-File-Format#gff-data-types) | 4 (0x04) | 4    | size of resource data in bytes                                   |

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs:119-120`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs#L119-L120)

### Resource data

Resource data is stored at the offsets specified in the resource list:

| Name         | type   | Description                                                      |
| ------------ | ------ | ---------------------------------------------------------------- |
| Resource data | [byte](GFF-File-Format#gff-data-types)[] | Raw binary data for each resource                               |

### MOD/NWM file format Quirk: Blank data Block

**Note**: For MOD and NWM files only, there exists an unusual block of data between the resource structures ([KEY](KEY-File-Format) List) and the position structures (Resource List). This block is 8 bytes per resource and appears to be all NULL bytes in practice. This data block is not referenced by any offset in the [ERF file](ERF-File-Format) header, which is uncharacteristic of BioWare's file format design.

**Reference**: [`vendor/xoreos-docs/specs/torlack/mod.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/mod.html) - "Strange Blank data" section documenting this MOD/NWM-specific quirk

---

## [ERF](ERF-File-Format) Variants

[ERF files](ERF-File-Format) come in several variants based on file type:

| file type | Extension | Description                                                      |
| --------- | --------- | ---------------------------------------------------------------- |
| [ERF](ERF-File-Format)       | `.erf`    | Generic encapsulated resource file                               |
| MOD       | `.mod`    | Module file (contains area resources)                            |
| SAV       | `.sav`    | Save game file (contains saved game state)                       |
| HAK       | `.hak`    | Hak pak file (contains override resources)                      |

All variants use the same binary format structure, differing only in the file type signature.

### MOD Files ([module archives](ERF-File-Format))

MOD files package all resources needed for a game module (level/area):

**Typical Contents:**

- Area layouts (`.are`, `.git`)
- Module information (`.ifo`)
- Dialogs and scripts (`.dlg`, `.ncs`)
- Module-specific [2DA](2DA-File-Format) overrides
- Character templates (`.utc`, `.utp`, `.utd`)
- Waypoints and triggers (`.utw`, `.utt`)

The game loads MOD files from the `modules/` directory. When entering a module, the engine mounts the MOD archive and prioritizes its resources over [BIF files](BIF-File-Format) but below the `override/` folder.

### SAV Files ([save game archives](ERF-File-Format))

SAV files store complete game state:

**Contents:**

- Party member data (inventory, stats, equipped items)
- Module state (spawned creatures, opened containers)
- Global variables and plot [flags](GFF-File-Format#gff-data-types)
- Area layouts with modifications
- Quick bar configurations
- Portrait images

Save files preserve the state of all modified resources. When a placeable is looted or a door opened, the updated `.git` resource is stored in the SAV file.

### HAK Files (Override Paks)

HAK files provide mod content that overrides base game resources:

**Usage:**

- High-priority resource overrides (above base game, below saves)
- Total conversion mods
- Large content packs
- Shareable mod packages

Unlike the `override/` directory, HAK files:

- [ARE](GFF-File-Format#are-area) self-contained and portable
- Can be enabled/disabled per-module
- Support multiple HAKs with defined load order
- [ARE](GFF-File-Format#are-area) referenced by module `.ifo` files

### [ERF](ERF-File-Format) Files (Generic Archives)

Generic [ERF files](ERF-File-Format) serve miscellaneous purposes:

- [texture](TPC-File-Format) packs
- Audio replacement packs
- Campaign-specific resources
- Developer test archives

**Reference**: [`vendor/reone/src/libs/resource/format/erfreader.cpp:27-34`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/erfreader.cpp#L27-L34)

---

## Implementation Details

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/erf/io_erf.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/erf/io_erf.py)

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/erf/io_erf.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/erf/io_erf.py)

**[ERF](ERF-File-Format) Class**: [`Libraries/PyKotor/src/pykotor/resource/formats/erf/erf_data.py:100-229`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/erf/erf_data.py#L100-L229)

---

This documentation aims to provide a comprehensive overview of the KotOR [ERF file](ERF-File-Format) format, focusing on the detailed file structure and data formats used within the games.
