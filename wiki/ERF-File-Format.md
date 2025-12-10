# KotOR [ERF](ERF-File-Format) [file](GFF-File-Format) [format](GFF-File-Format) Documentation

This document provides a detailed description of the ERF (Encapsulated Resource [file](GFF-File-Format)) [file](GFF-File-Format) [format](GFF-File-Format) used in Knights of the Old Republic (KotOR) games. [ERF files](ERF-File-Format) [ARE](GFF-File-Format#are-area) [self-contained archives](ERF-File-Format) used for modules, save games, [texture](TPC-File-Format) packs, and hak paks.

## Table of Contents

- [KotOR ERF file format Documentation](#kotor-erf-file-format-documentation)
  - [Table of Contents](#table-of-contents)
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

## [file](GFF-File-Format) [structure](GFF-File-Format#file-structure-overview) Overview

[ERF files](ERF-File-Format) [ARE](GFF-File-Format#are-area) [self-contained archives](ERF-File-Format) that store both resource names ([ResRefs](GFF-File-Format#gff-data-types)) and [data](GFF-File-Format#file-structure-overview) in the same [file](GFF-File-Format). Unlike [BIF files](BIF-File-Format) which require a [KEY file](KEY-File-Format) for filename lookups, [ERF](ERF-File-Format) [files](GFF-File-Format) include [ResRef](GFF-File-Format#gff-data-types) information directly in the [archive](ERF-File-Format).

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/erf/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/erf/)

**Vendor References:**

- [`vendor/reone/src/libs/resource/format/erfreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/erfreader.cpp) - Complete C++ [ERF](ERF-File-Format) reader implementation with MOD/SAV/HAK support
- [`vendor/reone/include/reone/resource/format/erfreader.h`](https://github.com/th3w1zard1/reone/blob/master/include/reone/resource/format/erfreader.h) - [ERF](ERF-File-Format) reader [type](GFF-File-Format#gff-data-types) definitions
- [`vendor/xoreos/src/aurora/erffile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/erffile.cpp) - Generic Aurora [ERF](ERF-File-Format) implementation (shared [format](GFF-File-Format))
- [`vendor/KotOR.js/src/resource/ERFObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/ERFObject.ts) - TypeScript [ERF](ERF-File-Format) parser with streaming support
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/ERFObject.cs`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/ERFObject.cs) - C# Unity [ERF](ERF-File-Format) loader
- [`vendor/Kotor.NET/Kotor.NET/Formats/KotorERF/`](https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Formats/KotorERF) - .NET ERF reader/writer with builder API
- [`vendor/xoreos-tools/src/aurora/erffile.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/aurora/erffile.cpp) - Command-line [ERF](ERF-File-Format) extraction tools

**See Also:**

- [BIF File Format](BIF-File-Format) - Alternative archive [format](GFF-File-Format) used with [KEY](KEY-File-Format) [files](GFF-File-Format)
- [KEY File Format](KEY-File-Format) - [index](2DA-File-Format#row-labels) [file](GFF-File-Format) for [BIF archives](BIF-File-Format)
- [GFF File Format](GFF-File-Format) - Common content [type](GFF-File-Format#gff-data-types) stored in [ERF](ERF-File-Format) archives
- [RIM File Format](RIM-File-Format) - Similar archive [format](GFF-File-Format) for area resources

---

## [Binary Format](https://en.wikipedia.org/wiki/Binary_file)

### [file](GFF-File-Format) [header](GFF-File-Format#file-header)

The [file](GFF-File-Format) [header](GFF-File-Format#file-header) is 160 bytes in [size](GFF-File-Format#file-structure-overview):

| Name                      | [type](GFF-File-Format#gff-data-types)    | [offset](GFF-File-Format#file-structure-overview) | [size](GFF-File-Format#file-structure-overview) | Description                                    |
| ------------------------- | ------- | ------ | ---- | ---------------------------------------------- |
| [file](GFF-File-Format) [type](GFF-File-Format#gff-data-types)                 | [[char](GFF-File-Format#gff-data-types)][GFF-File-Format#char](4) | 0 (0x00) | 4    | `"ERF "`, `"MOD "`, `"SAV "`, or `"HAK "`     |
| [file](GFF-File-Format) Version              | [[char](GFF-File-Format#gff-data-types)][GFF-File-Format#char](4) | 4 (0x04) | 4    | Always `"V1.0"`                                 |
| Language [count](GFF-File-Format#file-structure-overview)            | [uint32](GFF-File-Format#gff-data-types)  | 8 (0x08) | 4    | Number of localized [string](GFF-File-Format#gff-data-types) entries             |
| Localized [string](GFF-File-Format#gff-data-types) [size](GFF-File-Format#file-structure-overview)     | [uint32](GFF-File-Format#gff-data-types)  | 12 (0x0C) | 4    | Total [size](GFF-File-Format#file-structure-overview) of localized [string](GFF-File-Format#gff-data-types) [data](GFF-File-Format#file-structure-overview) in bytes   |
| Entry [count](GFF-File-Format#file-structure-overview)               | [uint32](GFF-File-Format#gff-data-types)  | 16 (0x10) | 4    | Number of resources in the archive              |
| [offset](GFF-File-Format#file-structure-overview) to Localized [string](GFF-File-Format#gff-data-types) List | [uint32](GFF-File-Format#gff-data-types) | 20 (0x14) | 4 | [offset](GFF-File-Format#file-structure-overview) to localized [string](GFF-File-Format#gff-data-types) entries             |
| [offset](GFF-File-Format#file-structure-overview) to [KEY](KEY-File-Format) List        | [uint32](GFF-File-Format#gff-data-types)  | 24 (0x18) | 4    | [offset](GFF-File-Format#file-structure-overview) to [KEY](KEY-File-Format) entries [array](2DA-File-Format)                    |
| [offset](GFF-File-Format#file-structure-overview) to Resource List   | [uint32](GFF-File-Format#gff-data-types)  | 28 (0x1C) | 4    | [offset](GFF-File-Format#file-structure-overview) to resource entries [array](2DA-File-Format)                |
| Build Year                | [uint32](GFF-File-Format#gff-data-types)  | 32 (0x20) | 4    | Build year (years since 1900)                   |
| Build Day                 | [uint32](GFF-File-Format#gff-data-types)  | 36 (0x24) | 4    | Build day (days since Jan 1)                   |
| Description [StrRef](TLK-File-Format#string-references-strref)        | [uint32](GFF-File-Format#gff-data-types)  | 40 (0x28) | 4    | [TLK](TLK-File-Format) [string](GFF-File-Format#gff-data-types) reference for description           |
| Reserved                  | [[byte](GFF-File-Format#gff-data-types)][GFF-File-Format#byte](116) | 44 (0x2C)  | 116  | Padding (usually zeros)                         |

**Build Date [fields](GFF-File-Format#file-structure-overview):**

The Build Year and Build Day [fields](GFF-File-Format#file-structure-overview) timestamp when the [ERF file](ERF-File-Format) was created:

- **Build Year**: Years since 1900 (e.g., `103` = year 2003)
- **Build Day**: Day of year (1-365/366, with January 1 = day 1)

These timestamps [ARE](GFF-File-Format#are-area) primarily informational and used by development tools to track module versions. The game engine doesn't rely on them for functionality.

**Example Calculation:**

```plaintext
Build Year: 103 → 1900 + 103 = 2003
Build Day: 247 → September 4th (the 247th day of 2003)
```

Most mod tools either zero out these [fields](GFF-File-Format#file-structure-overview) or set them to the current date when creating/modifying [ERF files](ERF-File-Format).

**Description [StrRef](TLK-File-Format#string-references-strref) [values](GFF-File-Format#gff-data-types) by [file](GFF-File-Format) [type](GFF-File-Format#gff-data-types):**

The Description [StrRef](TLK-File-Format#string-references-strref) field ([offset](GFF-File-Format#file-structure-overview) 0x0028 / 0x28) varies depending on the [ERF](ERF-File-Format) variant:

- **MOD [files](GFF-File-Format)**: `-1` (no [TLK](TLK-File-Format) reference, uses localized [strings](GFF-File-Format#gff-data-types) instead)
- **SAV [files](GFF-File-Format)**: `0` (typically no description)
- **NWM [files](GFF-File-Format)**: `-1` (Neverwinter Nights module [format](GFF-File-Format), not used in KotOR)
- **[ERF](ERF-File-Format)/HAK [files](GFF-File-Format)**: Unpredictable (may contain valid [StrRef](TLK-File-Format#string-references-strref) or `-1`)

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs:11-46`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs#L11-L46)  
**Reference**: [`vendor/xoreos-docs/specs/torlack/mod.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/mod.html) - Tim Smith (Torlack)'s reverse-engineered [ERF](ERF-File-Format) [format](GFF-File-Format) documentation

### Localized [string](GFF-File-Format#gff-data-types) List

Localized [strings](GFF-File-Format#gff-data-types) provide descriptions in multiple languages:

| Name         | [type](GFF-File-Format#gff-data-types)    | [size](GFF-File-Format#file-structure-overview) | Description                                                      |
| ------------ | ------- | ---- | ---------------------------------------------------------------- |
| Language ID  | [uint32](GFF-File-Format#gff-data-types)  | 4    | Language identifier (see Language enum)                          |
| [string](GFF-File-Format#gff-data-types) [size](GFF-File-Format#file-structure-overview)  | [uint32](GFF-File-Format#gff-data-types)  | 4    | Length of [string](GFF-File-Format#gff-data-types) in bytes                                       |
| [string](GFF-File-Format#gff-data-types) [data](GFF-File-Format#file-structure-overview)  | [char](GFF-File-Format#gff-data-types)[]  | N    | UTF-8 encoded text                                               |

**Localized [string](GFF-File-Format#gff-data-types) Usage:**

[ERF](ERF-File-Format) localized [strings](GFF-File-Format#gff-data-types) provide multi-language descriptions for the archive itself. These [ARE](GFF-File-Format#are-area) primarily used in MOD [files](GFF-File-Format) to display module names and descriptions in the game's module selection screen.

**Language IDs:**

- `0` = English
- `1` = French  
- `2` = German
- `3` = Italian
- `4` = Spanish
- `5` = Polish
- Additional languages for Asian releases

**Important Notes:**

- Most [ERF files](ERF-File-Format) have zero localized strings (Language [count](GFF-File-Format#file-structure-overview) = 0)
- MOD [files](GFF-File-Format) may include localized module names for the load screen
- Localized [strings](GFF-File-Format#gff-data-types) [ARE](GFF-File-Format#are-area) optional metadata and don't affect resource access
- The Description [StrRef](TLK-File-Format#string-references-strref) field (in [header](GFF-File-Format#file-header)) provides an alternative via [TLK](TLK-File-Format) reference

**Reference**: [`vendor/reone/src/libs/resource/format/erfreader.cpp:47-65`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/erfreader.cpp#L47-L65)

### [KEY](KEY-File-Format) List

Each [KEY](KEY-File-Format) entry is 24 bytes and maps ResRefs to resource [indices](2DA-File-Format#row-labels):

| Name        | [type](GFF-File-Format#gff-data-types)     | [offset](GFF-File-Format#file-structure-overview) | [size](GFF-File-Format#file-structure-overview) | Description                                                      |
| ----------- | -------- | ------ | ---- | ---------------------------------------------------------------- |
| [ResRef](GFF-File-Format#gff-data-types)      | [[char](GFF-File-Format#gff-data-types)][GFF-File-Format#char](16) | 0 (0x00) | 16   | Resource filename (null-padded, max 16 chars)                    |
| Resource ID | [uint32](GFF-File-Format#gff-data-types)   | 16 (0x10) | 4    | [index](2DA-File-Format#row-labels) into resource list                                         |
| Resource [type](GFF-File-Format#gff-data-types) | [uint16](GFF-File-Format#gff-data-types) | 20 (0x14) | 2    | Resource [type](GFF-File-Format#gff-data-types) identifier                                         |
| Unused      | [uint16](GFF-File-Format#gff-data-types)   | 22 (0x16) | 2    | Padding                                                           |

**[ResRef](GFF-File-Format#gff-data-types) Padding Notes:**

Resource names [ARE](GFF-File-Format#are-area) padded with NULL bytes to 16 characters, but [ARE](GFF-File-Format#are-area) not necessarily [null-terminated](https://en.cppreference.com/w/c/string/byte). If a resource name is exactly 16 characters long, no [null terminator](https://en.cppreference.com/w/c/string/byte) exists. Resource names can be mixed case, though most [ARE](GFF-File-Format#are-area) lowercase in practice.

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs:115-168`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs#L115-L168)  
**Reference**: [`vendor/xoreos-docs/specs/torlack/mod.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/mod.html) - Resource [structure](GFF-File-Format#file-structure-overview) details and [ResRef](GFF-File-Format#gff-data-types) padding notes

### Resource List

Each resource entry is 8 bytes:

| Name          | [type](GFF-File-Format#gff-data-types)   | [offset](GFF-File-Format#file-structure-overview) | [size](GFF-File-Format#file-structure-overview) | Description                                                      |
| ------------- | ------ | ------ | ---- | ---------------------------------------------------------------- |
| [offset](GFF-File-Format#file-structure-overview) to [data](GFF-File-Format#file-structure-overview) | [uint32](GFF-File-Format#gff-data-types) | 0 (0x00) | 4    | [offset](GFF-File-Format#file-structure-overview) to resource [data](GFF-File-Format#file-structure-overview) in [file](GFF-File-Format)                                  |
| Resource [size](GFF-File-Format#file-structure-overview) | [uint32](GFF-File-Format#gff-data-types) | 4 (0x04) | 4    | [size](GFF-File-Format#file-structure-overview) of resource [data](GFF-File-Format#file-structure-overview) in bytes                                   |

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs:119-120`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs#L119-L120)

### Resource [data](GFF-File-Format#file-structure-overview)

Resource [data](GFF-File-Format#file-structure-overview) is stored at the [offsets](GFF-File-Format#file-structure-overview) specified in the resource list:

| Name         | [type](GFF-File-Format#gff-data-types)   | Description                                                      |
| ------------ | ------ | ---------------------------------------------------------------- |
| Resource [data](GFF-File-Format#file-structure-overview) | [byte](GFF-File-Format#gff-data-types)[] | Raw binary [data](GFF-File-Format#file-structure-overview) for each resource                               |

### MOD/NWM [file](GFF-File-Format) [format](GFF-File-Format) Quirk: Blank [data](GFF-File-Format#file-structure-overview) Block

**Note**: For MOD and NWM [files](GFF-File-Format) only, there exists an unusual block of [data](GFF-File-Format#file-structure-overview) between the resource structures ([KEY](KEY-File-Format) List) and the [position](MDL-MDX-File-Format#node-header) structures (Resource List). This block is 8 bytes per resource and appears to be all NULL bytes in practice. This [data](GFF-File-Format#file-structure-overview) block is not referenced by any [offset](GFF-File-Format#file-structure-overview) in the [ERF file](ERF-File-Format) [header](GFF-File-Format#file-header), which is uncharacteristic of BioWare's [file](GFF-File-Format) [format](GFF-File-Format) design.

**Reference**: [`vendor/xoreos-docs/specs/torlack/mod.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/mod.html) - "Strange Blank [data](GFF-File-Format#file-structure-overview)" section documenting this MOD/NWM-specific quirk

---

## [ERF](ERF-File-Format) Variants

[ERF files](ERF-File-Format) come in several variants based on [file](GFF-File-Format) [type](GFF-File-Format#gff-data-types):

| [file](GFF-File-Format) [type](GFF-File-Format#gff-data-types) | Extension | Description                                                      |
| --------- | --------- | ---------------------------------------------------------------- |
| [ERF](ERF-File-Format)       | `.erf`    | Generic encapsulated resource [file](GFF-File-Format)                               |
| MOD       | `.mod`    | Module file (contains area resources)                            |
| SAV       | `.sav`    | Save game file (contains saved game state)                       |
| HAK       | `.hak`    | Hak pak file (contains override resources)                      |

All variants use the same binary [format](GFF-File-Format) [structure](GFF-File-Format#file-structure-overview), differing only in the [file](GFF-File-Format) [type](GFF-File-Format#gff-data-types) signature.

### MOD Files ([module archives](ERF-File-Format))

MOD [files](GFF-File-Format) package all resources needed for a game module (level/area):

**Typical Contents:**

- Area layouts (`.are`, `.git`)
- Module information (`.ifo`)
- Dialogs and scripts (`.dlg`, `.ncs`)
- Module-specific [2DA](2DA-File-Format) overrides
- Character templates (`.utc`, `.utp`, `.utd`)
- Waypoints and triggers (`.utw`, `.utt`)

The game loads MOD [files](GFF-File-Format) from the `modules/` directory. When entering a module, the engine mounts the MOD archive and prioritizes its resources over [BIF files](BIF-File-Format) but below the `override/` folder.

### SAV Files ([save game archives](ERF-File-Format))

SAV [files](GFF-File-Format) store complete game state:

**Contents:**

- Party member data (inventory, stats, equipped items)
- Module state (spawned creatures, opened containers)
- Global variables and plot [flags](GFF-File-Format#gff-data-types)
- Area layouts with modifications
- Quick bar configurations
- Portrait images

Save [files](GFF-File-Format) preserve the state of all modified resources. When a placeable is looted or a door opened, the updated `.git` resource is stored in the SAV [file](GFF-File-Format).

### HAK Files (Override Paks)

HAK [files](GFF-File-Format) provide mod content that overrides base game resources:

**Usage:**

- High-priority resource overrides (above base game, below saves)
- Total conversion mods
- Large content packs
- Shareable mod packages

Unlike the `override/` directory, HAK [files](GFF-File-Format):

- [ARE](GFF-File-Format#are-area) self-contained and portable
- Can be enabled/disabled per-module
- Support multiple HAKs with defined load order
- [ARE](GFF-File-Format#are-area) referenced by module `.ifo` [files](GFF-File-Format)

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

This documentation aims to provide a comprehensive overview of the KotOR [ERF file](ERF-File-Format) [format](GFF-File-Format), focusing on the detailed [file](GFF-File-Format) [structure](GFF-File-Format#file-structure-overview) and [data](GFF-File-Format#file-structure-overview) [formats](GFF-File-Format) used within the games.
