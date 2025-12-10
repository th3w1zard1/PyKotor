# KotOR ERF File Format Documentation

This document provides a detailed description of the ERF (Encapsulated Resource File) file format used in Knights of the Old Republic (KotOR) games. ERF files are self-contained archives used for modules, save games, texture packs, and hak paks.

## Table of Contents

- [KotOR ERF File Format Documentation](#kotor-erf-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
  - [Binary Format](#binary-format)
    - [File Header](#file-header)
    - [Localized String List](#localized-string-list)
    - [Key List](#key-list)
    - [Resource List](#resource-list)
    - [Resource Data](#resource-data)
    - [MOD/NWM File Format Quirk: Blank Data Block](#modnwm-file-format-quirk-blank-data-block)
  - [ERF Variants](#erf-variants)
    - [MOD Files (Module Archives)](#mod-files-module-archives)
    - [SAV Files (Save Game Archives)](#sav-files-save-game-archives)
    - [HAK Files (Override Paks)](#hak-files-override-paks)
    - [ERF Files (Generic Archives)](#erf-files-generic-archives)
  - [Implementation Details](#implementation-details)

---

## File Structure Overview

ERF files are self-contained [archives](https://en.wikipedia.org/wiki/Archive_file) that store both resource names (ResRefs) and data in the same file. Unlike BIF files which require a KEY file for filename lookups, ERF files include ResRef information directly in the archive.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/erf/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/erf/)

**Vendor References:**

- [`vendor/reone/src/libs/resource/format/erfreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/erfreader.cpp) - Complete C++ ERF reader implementation with MOD/SAV/HAK support
- [`vendor/reone/include/reone/resource/format/erfreader.h`](https://github.com/th3w1zard1/reone/blob/master/include/reone/resource/format/erfreader.h) - ERF reader type definitions
- [`vendor/xoreos/src/aurora/erffile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/erffile.cpp) - Generic Aurora ERF implementation (shared format)
- [`vendor/KotOR.js/src/resource/ERFObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/ERFObject.ts) - TypeScript ERF parser with streaming support
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/ERFObject.cs`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/ERFObject.cs) - C# Unity ERF loader
- [`vendor/Kotor.NET/Kotor.NET/Formats/KotorERF/`](https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Formats/KotorERF) - .NET ERF reader/writer with builder API
- [`vendor/xoreos-tools/src/aurora/erffile.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/aurora/erffile.cpp) - Command-line ERF extraction tools

**See Also:**

- [BIF File Format](BIF-File-Format) - Alternative archive format used with KEY files
- [KEY File Format](KEY-File-Format) - Index file for BIF archives
- [GFF File Format](GFF-File-Format) - Common content type stored in ERF archives
- [RIM File Format](RIM-File-Format) - Similar archive format for area resources

---

## [Binary Format](https://en.wikipedia.org/wiki/Binary_file)

### File Header

The file header is 160 bytes in size:

| Name                      | Type    | Offset | Size | Description                                    |
| ------------------------- | ------- | ------ | ---- | ---------------------------------------------- |
| File Type                 | char[4] | 0      | 4    | `"ERF "`, `"MOD "`, `"SAV "`, or `"HAK "`     |
| File Version              | char[4] | 4      | 4    | Always `"V1.0"`                                 |
| Language Count            | uint32  | 8      | 4    | Number of localized string entries             |
| Localized String Size     | uint32  | 12     | 4    | Total size of localized string data in bytes   |
| Entry Count               | uint32  | 16     | 4    | Number of resources in the archive              |
| Offset to Localized String List | uint32 | 20 | 4 | Offset to localized string entries             |
| Offset to Key List        | uint32  | 24     | 4    | Offset to key entries array                    |
| Offset to Resource List   | uint32  | 28     | 4    | Offset to resource entries array                |
| Build Year                | uint32  | 32     | 4    | Build year (years since 1900)                   |
| Build Day                 | uint32  | 36     | 4    | Build day (days since Jan 1)                   |
| Description StrRef        | uint32  | 40     | 4    | TLK string reference for description           |
| Reserved                  | byte[116] | 44  | 116  | Padding (usually zeros)                         |

**Build Date Fields:**

The Build Year and Build Day fields timestamp when the ERF file was created:

- **Build Year**: Years since 1900 (e.g., `103` = year 2003)
- **Build Day**: Day of year (1-365/366, with January 1 = day 1)

These timestamps are primarily informational and used by development tools to track module versions. The game engine doesn't rely on them for functionality.

**Example Calculation:**

```plaintext
Build Year: 103 → 1900 + 103 = 2003
Build Day: 247 → September 4th (the 247th day of 2003)
```

Most mod tools either zero out these fields or set them to the current date when creating/modifying ERF files.

**Description StrRef Values by File Type:**

The Description StrRef field (offset 0x0028 / 0x28) varies depending on the ERF variant:

- **MOD files**: `-1` (no TLK reference, uses localized strings instead)
- **SAV files**: `0` (typically no description)
- **NWM files**: `-1` (Neverwinter Nights module format, not used in KotOR)
- **ERF/HAK files**: Unpredictable (may contain valid StrRef or `-1`)

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs:11-46`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs#L11-L46)  
**Reference**: [`vendor/xoreos-docs/specs/torlack/mod.html`](vendor/xoreos-docs/specs/torlack/mod.html) - Tim Smith (Torlack)'s reverse-engineered ERF format documentation

### Localized String List

Localized strings provide descriptions in multiple languages:

| Name         | Type    | Size | Description                                                      |
| ------------ | ------- | ---- | ---------------------------------------------------------------- |
| Language ID  | uint32  | 4    | Language identifier (see Language enum)                          |
| String Size  | uint32  | 4    | Length of string in bytes                                       |
| String Data  | char[]  | N    | UTF-8 encoded text                                               |

**Localized String Usage:**

ERF localized strings provide multi-language descriptions for the archive itself. These are primarily used in MOD files to display module names and descriptions in the game's module selection screen.

**Language IDs:**

- `0` = English
- `1` = French  
- `2` = German
- `3` = Italian
- `4` = Spanish
- `5` = Polish
- Additional languages for Asian releases

**Important Notes:**

- Most ERF files have zero localized strings (Language Count = 0)
- MOD files may include localized module names for the load screen
- Localized strings are optional metadata and don't affect resource access
- The Description StrRef field (in header) provides an alternative via TLK reference

**Reference**: [`vendor/reone/src/libs/resource/format/erfreader.cpp:47-65`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/erfreader.cpp#L47-L65)

### Key List

Each key entry is 24 bytes and maps ResRefs to resource indices:

| Name        | Type     | Offset | Size | Description                                                      |
| ----------- | -------- | ------ | ---- | ---------------------------------------------------------------- |
| ResRef      | char[16] | 0      | 16   | Resource filename (null-padded, max 16 chars)                    |
| Resource ID | uint32   | 16     | 4    | Index into resource list                                         |
| Resource Type | uint16 | 20   | 2    | Resource type identifier                                         |
| Unused      | uint16   | 22     | 2    | Padding                                                           |

**ResRef Padding Notes:**

Resource names are padded with NULL bytes to 16 characters, but are not necessarily NULL-terminated. If a resource name is exactly 16 characters long, no NULL terminator exists. Resource names can be mixed case, though most are lowercase in practice.

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs:115-168`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs#L115-L168)  
**Reference**: [`vendor/xoreos-docs/specs/torlack/mod.html`](vendor/xoreos-docs/specs/torlack/mod.html) - Resource structure details and ResRef padding notes

### Resource List

Each resource entry is 8 bytes:

| Name          | Type   | Offset | Size | Description                                                      |
| ------------- | ------ | ------ | ---- | ---------------------------------------------------------------- |
| Offset to Data | uint32 | 0    | 4    | Offset to resource data in file                                  |
| Resource Size | uint32 | 4      | 4    | Size of resource data in bytes                                   |

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs:119-120`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs#L119-L120)

### Resource Data

Resource data is stored at the offsets specified in the resource list:

| Name         | Type   | Description                                                      |
| ------------ | ------ | ---------------------------------------------------------------- |
| Resource Data | byte[] | Raw binary data for each resource                               |

### MOD/NWM File Format Quirk: Blank Data Block

**Note**: For MOD and NWM files only, there exists an unusual block of data between the resource structures (Key List) and the position structures (Resource List). This block is 8 bytes per resource and appears to be all NULL bytes in practice. This data block is not referenced by any offset in the ERF file header, which is uncharacteristic of BioWare's file format design.

**Reference**: [`vendor/xoreos-docs/specs/torlack/mod.html`](vendor/xoreos-docs/specs/torlack/mod.html) - "Strange Blank Data" section documenting this MOD/NWM-specific quirk

---

## ERF Variants

ERF files come in several variants based on file type:

| File Type | Extension | Description                                                      |
| --------- | --------- | ---------------------------------------------------------------- |
| ERF       | `.erf`    | Generic encapsulated resource file                               |
| MOD       | `.mod`    | Module file (contains area resources)                            |
| SAV       | `.sav`    | Save game file (contains saved game state)                       |
| HAK       | `.hak`    | Hak pak file (contains override resources)                      |

All variants use the same binary format structure, differing only in the file type signature.

### MOD Files (Module Archives)

MOD files package all resources needed for a game module (level/area):

**Typical Contents:**

- Area layouts (`.are`, `.git`)
- Module information (`.ifo`)
- Dialogs and scripts (`.dlg`, `.ncs`)
- Module-specific 2DA overrides
- Character templates (`.utc`, `.utp`, `.utd`)
- Waypoints and triggers (`.utw`, `.utt`)

The game loads MOD files from the `modules/` directory. When entering a module, the engine mounts the MOD archive and prioritizes its resources over BIF files but below the `override/` folder.

### SAV Files (Save Game Archives)

SAV files store complete game state:

**Contents:**

- Party member data (inventory, stats, equipped items)
- Module state (spawned creatures, opened containers)
- Global variables and plot flags
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

- Are self-contained and portable
- Can be enabled/disabled per-module
- Support multiple HAKs with defined load order
- Are referenced by module `.ifo` files

### ERF Files (Generic Archives)

Generic ERF files serve miscellaneous purposes:

- Texture packs
- Audio replacement packs
- Campaign-specific resources
- Developer test archives

**Reference**: [`vendor/reone/src/libs/resource/format/erfreader.cpp:27-34`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/erfreader.cpp#L27-L34)

---

## Implementation Details

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/erf/io_erf.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/erf/io_erf.py)

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/erf/io_erf.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/erf/io_erf.py)

**ERF Class**: [`Libraries/PyKotor/src/pykotor/resource/formats/erf/erf_data.py:100-229`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/erf/erf_data.py#L100-L229)

---

This documentation aims to provide a comprehensive overview of the KotOR ERF file format, focusing on the detailed file structure and data formats used within the games.
