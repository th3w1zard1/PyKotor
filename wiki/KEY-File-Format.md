# KotOR [KEY](KEY-File-Format) [file](GFF-File-Format) [format](GFF-File-Format) Documentation

This document provides a detailed description of the KEY ([KEY](KEY-File-Format) Table) [file](GFF-File-Format) [format](GFF-File-Format) used in Knights of the Old Republic (KotOR) games. [KEY files](KEY-File-Format) serve as the master [index](2DA-File-Format#row-labels) for all [BIF files](BIF-File-Format) in the game.

## Table of Contents

- [KotOR KEY File Format Documentation](#kotor-key-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
    - [KEY File Purpose](#key-file-purpose)
  - [Binary Format](#binary-format)
    - [File Header](#file-header)
    - [File Table](#file-table)
    - [Filename Table](#filename-table)
    - [Key Table](#key-table)
  - [Resource ID Encoding](#resource-id-encoding)
  - [Implementation Details](#implementation-details)

---

## [file](GFF-File-Format) [structure](GFF-File-Format#file-structure) Overview

[KEY files](KEY-File-Format) map resource names ([ResRefs](GFF-File-Format#resref)) and [types](GFF-File-Format#data-types) to specific locations within [BIF archives](BIF-File-Format). KotOR uses `chitin.key` as the main [KEY file](KEY-File-Format) which references all game [BIF files](BIF-File-Format).

### [KEY](KEY-File-Format) [file](GFF-File-Format) Purpose

The [KEY file](KEY-File-Format) serves as the master [index](2DA-File-Format#row-labels) for the game's resource system:

1. **Resource Lookup**: Maps [ResRef](GFF-File-Format#resref) + ResourceType → [BIF](BIF-File-Format) location
2. **[BIF](BIF-File-Format) Registration**: Tracks all [BIF files](BIF-File-Format) and their install paths
3. **Resource Naming**: Provides the filename ([ResRef](GFF-File-Format#resref)) missing from [BIF files](BIF-File-Format)
4. **Drive Mapping**: Historical feature indicating which media (CD/HD) contained each [BIF](BIF-File-Format)

**Resource Resolution Order:**

When the game needs a resource, it searches in this order:

1. Override folder (`override/`)
2. Currently loaded MOD/[ERF files](ERF-File-Format)
3. Currently loaded SAV file (if in-game)
4. [BIF files](BIF-File-Format) via [KEY](KEY-File-Format) lookup
5. Hardcoded defaults (if no resource found)

The [KEY](KEY-File-Format) [file](GFF-File-Format) only manages [BIF](BIF-File-Format) resources (step 4). Higher-priority locations can override [KEY](KEY-File-Format)-indexed resources without modifying the [KEY file](KEY-File-Format).

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/key/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/key/)

**Vendor References:**

- [`vendor/reone/src/libs/resource/format/keyreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/keyreader.cpp) - Complete C++ [KEY](KEY-File-Format) reader implementation
- [`vendor/xoreos/src/aurora/keyfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/keyfile.cpp) - Generic Aurora [KEY](KEY-File-Format) implementation (shared [format](GFF-File-Format))
- [`vendor/KotOR.js/src/resource/KEYObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/KEYObject.ts) - TypeScript [KEY](KEY-File-Format) parser
- [`vendor/Kotor.NET/Kotor.NET/Formats/KotorKEY/`](https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Formats/KotorKEY) - .NET KEY reader/writer
- [`vendor/xoreos-tools/src/aurora/keyfile.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/aurora/keyfile.cpp) - Command-line [KEY](KEY-File-Format) tools

**See Also:**

- [BIF File Format](BIF-File-Format) - Archive [format](GFF-File-Format) indexed by [KEY](KEY-File-Format) files
- [ERF File Format](ERF-File-Format) - Self-contained alternative to [KEY](KEY-File-Format)+[BIF](BIF-File-Format)
- [Bioware Aurora KeyBIF Format](Bioware-Aurora-KeyBIF) - Official BioWare specification

---

## [Binary Format](https://en.wikipedia.org/wiki/Binary_file)

### File Header

The file header is 64 bytes in size:

| Name                | [type](GFF-File-Format#data-types)    | [offset](GFF-File-Format#file-structure) | [size](GFF-File-Format#file-structure) | Description                                    |
| ------------------- | ------- | ------ | ---- | ---------------------------------------------- |
| [file](GFF-File-Format) [type](GFF-File-Format#data-types)           | [char][GFF-File-Format#char](4) | 0 (0x00) | 4    | Always `"KEY "` (space-padded)                 |
| [file](GFF-File-Format) Version        | [char][GFF-File-Format#char](4) | 4 (0x04) | 4    | `"V1  "` or `"V1.1"`                           |
| [BIF](BIF-File-Format) [count](GFF-File-Format#file-structure)           | [uint32](GFF-File-Format#dword)  | 8 (0x08) | 4    | Number of [BIF files](BIF-File-Format) referenced                 |
| [KEY](KEY-File-Format) [count](GFF-File-Format#file-structure)           | [uint32](GFF-File-Format#dword)  | 12 (0x0C) | 4    | Number of resource entries                     |
| [offset](GFF-File-Format#file-structure) to [file](GFF-File-Format) Table | [uint32](GFF-File-Format#dword) | 16 (0x10) | 4    | [offset](GFF-File-Format#file-structure) to [BIF file](BIF-File-Format) entries [array](2DA-File-Format)               |
| [offset](GFF-File-Format#file-structure) to [KEY](KEY-File-Format) Table | [uint32](GFF-File-Format#dword) | 20 (0x14) | 4    | [offset](GFF-File-Format#file-structure) to resource entries [array](2DA-File-Format)               |
| Build Year          | [uint32](GFF-File-Format#dword)  | 24 (0x18) | 4    | Build year (years since 1900)                  |
| Build Day           | [uint32](GFF-File-Format#dword)  | 28 (0x1C) | 4    | Build day (days since Jan 1)                   |
| Reserved            | [byte][GFF-File-Format#byte](32) | 32 (0x20) | 32   | Padding (usually zeros)                        |

**Note on [header](GFF-File-Format#file-header) Variations**: Some older documentation (e.g., xoreos-docs) shows the [header](GFF-File-Format#file-header) ending at [offset](GFF-File-Format#file-structure) 0x0040 with unknown [values](GFF-File-Format#data-types) at [offset](GFF-File-Format#file-structure) 0x0018. The [structure](GFF-File-Format#file-structure) shown here (with Build Year/Day and Reserved [fields](GFF-File-Format#file-structure)) matches the actual KotOR [KEY file](KEY-File-Format) [format](GFF-File-Format).

**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorKEY/KEYBinaryStructure.cs:13-114`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorKEY/KEYBinaryStructure.cs#L13-L114)  
**Reference**: [`vendor/xoreos-docs/specs/torlack/key.html`](vendor/xoreos-docs/specs/torlack/key.html) - Tim Smith (Torlack)'s reverse-engineered [KEY](KEY-File-Format) [format](GFF-File-Format) documentation (may show variant [header](GFF-File-Format#file-header) [structure](GFF-File-Format#file-structure))

### [file](GFF-File-Format) Table

Each [file](GFF-File-Format) entry is 12 bytes:

| Name            | [type](GFF-File-Format#data-types)   | [offset](GFF-File-Format#file-structure) | [size](GFF-File-Format#file-structure) | Description                                                      |
| --------------- | ------ | ------ | ---- | ---------------------------------------------------------------- |
| [file](GFF-File-Format) [size](GFF-File-Format#file-structure)       | [uint32](GFF-File-Format#dword) | 0 (0x00) | 4    | [size](GFF-File-Format#file-structure) of [BIF file](BIF-File-Format) on disk                                         |
| Filename [offset](GFF-File-Format#file-structure) | [uint32](GFF-File-Format#dword) | 4 (0x04) | 4    | [offset](GFF-File-Format#file-structure) into filename table                                       |
| Filename Length | [uint16](GFF-File-Format#word) | 8 (0x08) | 2    | Length of filename in bytes                                      |
| Drives          | [uint16](GFF-File-Format#word) | 10 (0x0A) | 2    | Drive flags (0x0001=HD0, 0x0002=CD1, etc.)                      |

**Drive [flags](GFF-File-Format#data-types) Explained:**

Drive [flags](GFF-File-Format#data-types) [ARE](GFF-File-Format#are-area) a legacy feature from the multi-CD distribution era:

| [flag](GFF-File-Format#data-types) [value](GFF-File-Format#data-types) | Meaning | Description |
| ---------- | ------- | ----------- |
| `0x0001` | HD (Hard Drive) | [BIF](BIF-File-Format) is installed on the hard drive |
| `0x0002` | CD1 | [BIF](BIF-File-Format) is on the first game disc |
| `0x0004` | CD2 | [BIF](BIF-File-Format) is on the second game disc |
| `0x0008` | CD3 | [BIF](BIF-File-Format) is on the third game disc |
| `0x0010` | CD4 | [BIF](BIF-File-Format) is on the fourth game disc |

**Modern Usage:**

In contemporary distributions (Steam, GOG, digital):

- All [BIF files](BIF-File-Format) use `0x0001` (HD [flag](GFF-File-Format#data-types)) since everything is installed locally
- The engine doesn't prompt for disc swapping
- Multiple [flags](GFF-File-Format#data-types) can be combined (bitwise OR) if a [BIF](BIF-File-Format) could be on multiple sources
- Mod tools typically set this to `0x0001` for all [files](GFF-File-Format)

The drive system was originally designed so the engine could:

- Prompt users to insert specific CDs when needed resources weren't on the hard drive
- Optimize installation by allowing users to choose what to install vs. run from CD
- Support partial installs to save disk space (common in the early 2000s)

**Reference**: [`vendor/reone/src/libs/resource/format/keyreader.cpp:55-70`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/keyreader.cpp#L55-L70)

### Filename Table

The filename table contains [null-terminated](https://en.cppreference.com/w/c/string/byte) [strings](GFF-File-Format#cexostring):

| Name      | [type](GFF-File-Format#data-types)   | Description                                                      |
| --------- | ------ | ---------------------------------------------------------------- |
| Filenames | [char](GFF-File-Format#char)[] | [null-terminated](https://en.cppreference.com/w/c/string/byte) [BIF](BIF-File-Format) filenames (e.g., "[data](GFF-File-Format#file-structure)/[models](MDL-MDX-File-Format).bif")         |

### [KEY](KEY-File-Format) Table

Each [KEY](KEY-File-Format) entry is 22 bytes:

| Name        | [type](GFF-File-Format#data-types)     | [offset](GFF-File-Format#file-structure) | [size](GFF-File-Format#file-structure) | Description                                                      |
| ----------- | -------- | ------ | ---- | ---------------------------------------------------------------- |
| [ResRef](GFF-File-Format#resref)      | [char][GFF-File-Format#char](16) | 0 (0x00) | 16   | Resource filename (null-padded, max 16 chars)                   |
| Resource [type](GFF-File-Format#data-types) | [uint16](GFF-File-Format#word) | 16 (0x10) | 2    | Resource [type](GFF-File-Format#data-types) identifier                                         |
| Resource ID | [uint32](GFF-File-Format#dword)   | 18 (0x12) | 4    | Encoded resource location (see [Resource ID Encoding](#resource-id-encoding)) |

**Critical [structure](GFF-File-Format#file-structure) Packing Note:**

The [KEY](KEY-File-Format) entry [structure](GFF-File-Format#file-structure) must use **[byte](GFF-File-Format#byte) or word alignment** (1-[byte](GFF-File-Format#byte) or 2-[byte](GFF-File-Format#byte) packing). If the [structure](GFF-File-Format#file-structure) is packed with 4-[byte](GFF-File-Format#byte) or 8-[byte](GFF-File-Format#byte) alignment, the `uint32` at [offset](GFF-File-Format#file-structure) 0x0012 (18) will be incorrectly placed at [offset](GFF-File-Format#file-structure) 0x0014 (20), causing incorrect resource ID decoding.

On non-Intel platforms, this alignment requirement may cause alignment faults unless the compiler provides an "unaligned" [type](GFF-File-Format#data-types) or special care is taken when accessing the `uint32` [field](GFF-File-Format#file-structure). The [structure](GFF-File-Format#file-structure) should be explicitly packed to ensure the `uint32` starts at [offset](GFF-File-Format#file-structure) 18 rather than being aligned to a 4-[byte](GFF-File-Format#byte) boundary.

**Reference**: [`vendor/reone/src/libs/resource/format/keyreader.cpp:72-100`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/keyreader.cpp#L72-L100)

---

## Resource ID Encoding

The Resource ID [field](GFF-File-Format#file-structure) encodes both the [BIF](BIF-File-Format) [index](2DA-File-Format#row-labels) and resource [index](2DA-File-Format#row-labels) within that [BIF](BIF-File-Format):

- **[bits](GFF-File-Format#data-types) 31-20**: [BIF](BIF-File-Format) Index (top 12 [bits](GFF-File-Format#data-types)) - [index](2DA-File-Format#row-labels) into [file](GFF-File-Format) table
- **[bits](GFF-File-Format#data-types) 19-0**: Resource Index (bottom 20 [bits](GFF-File-Format#data-types)) - [index](2DA-File-Format#row-labels) within the [BIF file](BIF-File-Format)

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

- Maximum [BIF files](BIF-File-Format): 4,096 (12-[bit](GFF-File-Format#data-types) [BIF](BIF-File-Format) [index](2DA-File-Format#row-labels))
- Maximum resources per [BIF](BIF-File-Format): 1,048,576 (20-[bit](GFF-File-Format#data-types) resource [index](2DA-File-Format#row-labels))

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

The encoding allows a single 32-[bit](GFF-File-Format#data-types) integer to precisely locate any resource in the entire [BIF](BIF-File-Format) system.

**Reference**: [`vendor/reone/src/libs/resource/format/keyreader.cpp:95-100`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/keyreader.cpp#L95-L100)  
**Reference**: [`vendor/xoreos-docs/specs/torlack/key.html`](vendor/xoreos-docs/specs/torlack/key.html) - [BIF](BIF-File-Format) ID encoding explanation with example (0x00400029 → [BIF](BIF-File-Format) #4, Resource #41)

---

## Implementation Details

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/key/io_key.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/key/io_key.py)

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/key/io_key.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/key/io_key.py)

**[KEY](KEY-File-Format) Class**: [`Libraries/PyKotor/src/pykotor/resource/formats/key/key_data.py:100-462`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/key/key_data.py#L100-L462)

---

This documentation aims to provide a comprehensive overview of the KotOR [KEY file](KEY-File-Format) [format](GFF-File-Format), focusing on the detailed [file](GFF-File-Format) [structure](GFF-File-Format#file-structure) and [data](GFF-File-Format#file-structure) [formats](GFF-File-Format) used within the games.
