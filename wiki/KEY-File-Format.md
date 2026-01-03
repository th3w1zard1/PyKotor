# KotOR KEY file format Documentation

This document provides a detailed description of the KEY (KEY Table) file format used in Knights of the Old Republic (KotOR) games. KEY files serve as the master index for all [BIF files](BIF-File-Format) in the game.

## Table of Contents

- KotOR KEY file format Documentation
  - Table of Contents
  - [file structure Overview](#file-structure-overview)
    - [KEY file Purpose](#key-file-purpose)
  - [Binary Format](#binary-format)
    - [file header](#file-header)
    - [file Table](#file-table)
    - [Filename Table](#filename-table)
    - [KEY Table](#key-table)
  - [Resource ID Encoding](#resource-id-encoding)
  - [Implementation Details](#implementation-details)

---

## file structure Overview

KEY files map resource names ([ResRefs](GFF-File-Format#gff-data-types)) and types to specific locations within [BIF archives](BIF-File-Format). KotOR uses `chitin.key` as the main KEY file which references all game [BIF files](BIF-File-Format).

### KEY file Purpose

The KEY file serves as the master index for the game's resource system:

1. **Resource Lookup**: Maps [ResRef](GFF-File-Format#gff-data-types) + ResourceType → [BIF](BIF-File-Format) location
2. **[BIF](BIF-File-Format) Registration**: Tracks all [BIF files](BIF-File-Format) and their install paths
3. **Resource Naming**: Provides the filename ([ResRef](GFF-File-Format#gff-data-types)) missing from [BIF files](BIF-File-Format)
4. **Drive Mapping**: Historical feature indicating which media (CD/HD) contained each [BIF](BIF-File-Format)

**Resource Resolution Order:**

When the game needs a resource, it searches in this order:

1. Override folder (`override/`)
2. Currently loaded MOD/[ERF files](ERF-File-Format)
3. Currently loaded SAV file (if in-game)
4. [BIF files](BIF-File-Format) via KEY lookup
5. Hardcoded defaults (if no resource found)

The KEY file only manages [BIF](BIF-File-Format) resources (step 4). Higher-priority locations can override KEY-indexed resources without modifying the KEY file.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/key/`](https://github.com/OldRepublicDevs/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/key/)

**Vendor References:**

- [`vendor/reone/src/libs/resource/format/keyreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/keyreader.cpp) - Complete C++ KEY reader implementation
- [`vendor/xoreos/src/aurora/keyfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/keyfile.cpp) - Generic Aurora KEY implementation (shared format across KotOR, NWN, and other Aurora games)
- [`vendor/KotOR.js/src/resource/KEYObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/KEYObject.ts) - TypeScript KEY parser
- [`vendor/Kotor.NET/Kotor.NET/Formats/KotorKEY/`](https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Formats/KotorKEY) - .NET KEY reader/writer
- [`vendor/xoreos-tools/src/aurora/keyfile.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/aurora/keyfile.cpp) - Command-line KEY tools

**See Also:**

- [BIF File Format](BIF-File-Format) - Archive format indexed by KEY files
- [ERF File Format](ERF-File-Format) - Self-contained alternative to KEY+[BIF](BIF-File-Format)
- [Bioware Aurora KeyBIF Format](Bioware-Aurora-KeyBIF) - Official BioWare specification

---

## [Binary Format](https://en.wikipedia.org/wiki/Binary_file)

### file header

The file header is 64 bytes in size:

| Name                | type    | offset | size | Description                                    |
| ------------------- | ------- | ------ | ---- | ---------------------------------------------- |
| file type           | [char](GFF-File-Format#gff-data-types) | 0 (0x00) | 4    | Always `"KEY "` (space-padded)                 |
| file Version        | [char](GFF-File-Format#gff-data-types) | 4 (0x04) | 4    | `"V1  "` or `"V1.1"`                           |
| [BIF](BIF-File-Format) count           | [uint32](GFF-File-Format#gff-data-types)  | 8 (0x08) | 4    | Number of [BIF files](BIF-File-Format) referenced                 |
| KEY count           | [uint32](GFF-File-Format#gff-data-types)  | 12 (0x0C) | 4    | Number of resource entries                     |
| offset to file Table | [uint32](GFF-File-Format#gff-data-types) | 16 (0x10) | 4    | offset to [BIF file](BIF-File-Format) entries array               |
| offset to KEY Table | [uint32](GFF-File-Format#gff-data-types) | 20 (0x14) | 4    | offset to resource entries array               |
| Build Year          | [uint32](GFF-File-Format#gff-data-types)  | 24 (0x18) | 4    | Build year (years since 1900)                  |
| Build Day           | [uint32](GFF-File-Format#gff-data-types)  | 28 (0x1C) | 4    | Build day (days since Jan 1)                   |
| Reserved            | [byte](GFF-File-Format#gff-data-types) | 32 (0x20) | 32   | Padding (usually zeros)                        |

**Note on header Variations**: [`vendor/xoreos-docs/specs/torlack/key.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/key.html) (Tim Smith/Torlack's reverse-engineered documentation) shows the header ending at offset 0x0040 with unknown values at offset 0x0018. The structure shown here (with Build Year/Day and Reserved fields) matches the actual KotOR KEY file format.

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorKEY/KEYBinaryStructure.cs:13-114`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorKEY/KEYBinaryStructure.cs#L13-L114)  
**Reference**: [`vendor/xoreos-docs/specs/torlack/key.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/key.html) - Tim Smith (Torlack)'s reverse-engineered KEY format documentation (may show variant header structure)

### file Table

Each file entry is 12 bytes:

| Name            | type   | offset | size | Description                                                      |
| --------------- | ------ | ------ | ---- | ---------------------------------------------------------------- |
| file size       | [uint32](GFF-File-Format#gff-data-types) | 0 (0x00) | 4    | size of [BIF file](BIF-File-Format) on disk                                         |
| Filename offset | [uint32](GFF-File-Format#gff-data-types) | 4 (0x04) | 4    | offset into filename table                                       |
| Filename Length | [uint16](GFF-File-Format#gff-data-types) | 8 (0x08) | 2    | Length of filename in bytes                                      |
| Drives          | [uint16](GFF-File-Format#gff-data-types) | 10 (0x0A) | 2    | Drive flags (0x0001=HD0, 0x0002=CD1, etc.)                      |

**Drive [flags](GFF-File-Format#gff-data-types) Explained:**

Drive [flags](GFF-File-Format#gff-data-types) [ARE](GFF-File-Format#are-area) a legacy feature from the multi-CD distribution era:

| [flag](GFF-File-Format#gff-data-types) value | Meaning | Description |
| ---------- | ------- | ----------- |
| `0x0001` | HD (Hard Drive) | [BIF](BIF-File-Format) is installed on the hard drive |
| `0x0002` | CD1 | [BIF](BIF-File-Format) is on the first game disc |
| `0x0004` | CD2 | [BIF](BIF-File-Format) is on the second game disc |
| `0x0008` | CD3 | [BIF](BIF-File-Format) is on the third game disc |
| `0x0010` | CD4 | [BIF](BIF-File-Format) is on the fourth game disc |

**Modern Usage:**

In contemporary distributions (Steam, GOG, digital):

- All [BIF files](BIF-File-Format) use `0x0001` (HD [flag](GFF-File-Format#gff-data-types)) since everything is installed locally
- The engine doesn't prompt for disc swapping
- Multiple [flags](GFF-File-Format#gff-data-types) can be combined (bitwise OR) if a [BIF](BIF-File-Format) could be on multiple sources
- Mod tools typically set this to `0x0001` for all files

The drive system was originally designed so the engine could:

- Prompt users to insert specific CDs when needed resources weren't on the hard drive
- Optimize installation by allowing users to choose what to install vs. run from CD
- Support partial installs to save disk space (common in the early 2000s)

**Reference**: [`vendor/reone/src/libs/resource/format/keyreader.cpp:55-70`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/keyreader.cpp#L55-L70)

### Filename Table

The filename table contains [null-terminated](https://en.cppreference.com/w/c/string/byte) strings:

| Name      | type   | Description                                                      |
| --------- | ------ | ---------------------------------------------------------------- |
| Filenames | [char](GFF-File-Format#gff-data-types)[] | [null-terminated](https://en.cppreference.com/w/c/string/byte) [BIF](BIF-File-Format) filenames (e.g., "data/[models](MDL-MDX-File-Format).bif")         |

### KEY Table

Each KEY entry is 22 bytes:

| Name        | type     | offset | size | Description                                                      |
| ----------- | -------- | ------ | ---- | ---------------------------------------------------------------- |
| [ResRef](GFF-File-Format#gff-data-types)      | [char](GFF-File-Format#gff-data-types) | 0 (0x00) | 16   | Resource filename (null-padded, max 16 chars)                   |
| Resource type | [uint16](GFF-File-Format#gff-data-types) | 16 (0x10) | 2    | Resource type identifier                                         |
| Resource ID | [uint32](GFF-File-Format#gff-data-types)   | 18 (0x12) | 4    | Encoded resource location (see [Resource ID Encoding](#resource-id-encoding)) |

**Critical structure Packing Note:**

The KEY entry structure must use **[byte](GFF-File-Format#gff-data-types) or word alignment** (1-[byte](GFF-File-Format#gff-data-types) or 2-[byte](GFF-File-Format#gff-data-types) packing). If the structure is packed with 4-[byte](GFF-File-Format#gff-data-types) or 8-[byte](GFF-File-Format#gff-data-types) alignment, the `uint32` at offset 0x0012 (18) will be incorrectly placed at offset 0x0014 (20), causing incorrect resource ID decoding.

On non-Intel platforms, this alignment requirement may cause alignment faults unless the compiler provides an "unaligned" type or special care is taken when accessing the `uint32` field. The structure should be explicitly packed to ensure the `uint32` starts at offset 18 rather than being aligned to a 4-[byte](GFF-File-Format#gff-data-types) boundary.

**Reference**: [`vendor/reone/src/libs/resource/format/keyreader.cpp:72-100`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/keyreader.cpp#L72-L100)

---

## Resource ID Encoding

The Resource ID field encodes both the [BIF](BIF-File-Format) index and resource index within that [BIF](BIF-File-Format):

- **bits 31-20**: [BIF](BIF-File-Format) Index (top 12 bits) - index into file table
- **bits 19-0**: Resource Index (bottom 20 bits) - index within the [BIF file](BIF-File-Format)

**Decoding:**

```python
bif_index = (resource_id >> 20) & 0xFFF  # Extract top 12 bits
resource_index = resource_id & 0xFFFFF   # Extract bottom 20 bits
```

**Encoding:**

```python
resource_id = (bif_index << 20) | resource_index
```

**Practical Limits:**

- Maximum [BIF files](BIF-File-Format): 4,096 (12-bit [BIF](BIF-File-Format) index)
- Maximum resources per [BIF](BIF-File-Format): 1,048,576 (20-bit resource index)

These limits [ARE](GFF-File-Format#are-area) more than sufficient for KotOR, which typically has:

- ~50-100 [BIF files](BIF-File-Format) in a full installation
- ~100-10,000 resources per BIF (largest BIFs [ARE](GFF-File-Format#are-area) [texture](TPC-File-Format) packs)

**Example:**

Given Resource ID `0x00123456`:

```plaintext
Binary: 0000 0000 0001 0010 0011 0100 0101 0110
        |---- 12 bits -----|------ 20 bits ------|
BIF Index:     0x001 (BIF #1)
Resource Index: 0x23456 (Resource #144,470 within that BIF)
```

The encoding allows a single 32-bit integer to precisely locate any resource in the entire [BIF](BIF-File-Format) system.

**Reference**: [`vendor/reone/src/libs/resource/format/keyreader.cpp:95-100`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/keyreader.cpp#L95-L100)  
**Reference**: [`vendor/xoreos-docs/specs/torlack/key.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/key.html) - [BIF](BIF-File-Format) ID encoding explanation with example (0x00400029 → [BIF](BIF-File-Format) #4, Resource #41)

---

## Implementation Details

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/key/io_key.py`](https://github.com/OldRepublicDevs/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/key/io_key.py)

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/key/io_key.py`](https://github.com/OldRepublicDevs/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/key/io_key.py)

**KEY Class**: [`Libraries/PyKotor/src/pykotor/resource/formats/key/key_data.py:100-462`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/key/key_data.py#L100-L462)

---

This documentation aims to provide a comprehensive overview of the KotOR KEY file format, focusing on the detailed file structure and data formats used within the games.
