# KotOR [BIF](BIF-File-Format) [file](GFF-File-Format) [format](GFF-File-Format) Documentation

This document provides a detailed description of the BIF (BioWare Index File) file format used in Knights of the Old Republic (KotOR) games. [BIF files](BIF-File-Format) [ARE](GFF-File-Format#are-area) archive containers that store the bulk of game resources.

## Table of Contents

- [KotOR BIF File Format Documentation](#kotor-bif-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
    - [BIF Usage in KotOR](#bif-usage-in-kotor)
  - [Binary Format](#binary-format)
    - [File Header](#file-header)
    - [Variable Resource Table](#variable-resource-table)
    - [Resource Data](#resource-data)
  - [BZF Compression](#bzf-compression)
    - [BZF Format Details](#bzf-format-details)
  - [KEY File Relationship](#key-file-relationship)
  - [Implementation Details](#implementation-details)

---

## [file](GFF-File-Format) [structure](GFF-File-Format#file-structure) Overview

[BIF files](BIF-File-Format) work in tandem with [KEY files](KEY-File-Format) which provide the filename-to-resource mappings. [BIF files](BIF-File-Format) contain only resource IDs, [types](GFF-File-Format#data-types), and [data](GFF-File-Format#file-structure) - the actual filenames ([ResRefs](GFF-File-Format#resref)) [ARE](GFF-File-Format#are-area) stored in the [KEY file](KEY-File-Format). BIF [files](GFF-File-Format) [ARE](GFF-File-Format#are-area) [archive containers](https://en.wikipedia.org/wiki/Archive_file) that store the bulk of game resources.

### [BIF](BIF-File-Format) Usage in KotOR

[BIF archives](BIF-File-Format) [ARE](GFF-File-Format#are-area) the primary storage mechanism for game assets. The game organizes resources into multiple [BIF files](BIF-File-Format) by category:

- `data/models.bif`: 3D [model](MDL-MDX-File-Format) files ([MDL/MDX](MDL-MDX-File-Format))
- `data/textures_*.bif`: [texture](TPC-File-Format) data ([TPC](TPC-File-Format)/[TXI](TXI-File-Format) [files](GFF-File-Format)) - split across multiple archives
- `data/sounds.bif`: Audio files ([WAV](WAV-File-Format))
- `data/2da.bif`: Game [data](GFF-File-Format#file-structure) tables ([2DA files](2DA-File-Format))
- `data/scripts.bif`: Compiled scripts ([NCS](NCS-File-Format))
- `data/dialogs.bif`: Conversation files ([DLG](GFF-DLG))
- `data/lips.bif`: [LIP](LIP-File-Format)-sync [animation](MDL-MDX-File-Format#animation-header) data ([LIP](LIP-File-Format))
- Additional platform-specific BIFs (e.g., `dataxbox/`, `data_mac/`)

The [modular structure](https://en.wikipedia.org/wiki/Modular_programming) allows for efficient loading and potential platform-specific optimizations. Resources in [BIF files](BIF-File-Format) [ARE](GFF-File-Format#are-area) read-only at runtime; mods override them via the `override/` directory or custom [ERF](ERF-File-Format)/MOD [files](GFF-File-Format).

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/bif/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/bif/)

**Vendor References:**

- [`vendor/reone/src/libs/resource/format/bifreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/bifreader.cpp) - Complete C++ [BIF](BIF-File-Format) reader implementation
- [`vendor/xoreos/src/aurora/biffile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/biffile.cpp) - Generic Aurora [BIF](BIF-File-Format) implementation (shared [format](GFF-File-Format))
- [`vendor/KotOR.js/src/resource/BIFObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/BIFObject.ts) - TypeScript [BIF](BIF-File-Format) parser with decompression
- [`vendor/Kotor.NET/Kotor.NET/Formats/KotorBIF/`](https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Formats/KotorBIF) - .NET BIF reader/writer
- [`vendor/xoreos-tools/src/aurora/biffile.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/aurora/biffile.cpp) - Command-line [BIF](BIF-File-Format) extraction tools

**See Also:**

- [KEY File Format](KEY-File-Format) - [index](2DA-File-Format#row-labels) [file](GFF-File-Format) that references [BIF archives](BIF-File-Format)
- [ERF File Format](ERF-File-Format) - Alternative self-contained archive [format](GFF-File-Format)
- [Bioware Aurora KeyBIF Format](Bioware-Aurora-KeyBIF) - Official BioWare specification

---

## [Binary Format](https://en.wikipedia.org/wiki/Binary_file)

### File Header

The file header is 20 bytes in size:

| Name                      | [type](GFF-File-Format#data-types)    | [offset](GFF-File-Format#file-structure) | [size](GFF-File-Format#file-structure) | Description                                    |
| ------------------------- | ------- | ------ | ---- | ---------------------------------------------- |
| [file](GFF-File-Format) [type](GFF-File-Format#data-types)                 | [char][GFF-File-Format#char](4) | 0 (0x00) | 4    | `"BIFF"` for [BIF](BIF-File-Format), `"BZF "` for compressed [BIF](BIF-File-Format)  |
| [file](GFF-File-Format) Version              | [char][GFF-File-Format#char](4) | 4 (0x04) | 4    | `"V1  "` for [BIF](BIF-File-Format), `"V1.0"` for BZF             |
| Variable Resource [count](GFF-File-Format#file-structure)   | [uint32](GFF-File-Format#dword)  | 8 (0x08) | 4    | Number of variable-[size](GFF-File-Format#file-structure) resources              |
| Fixed Resource [count](GFF-File-Format#file-structure)      | [uint32](GFF-File-Format#dword)  | 12 (0x0C) | 4    | Number of fixed-[size](GFF-File-Format#file-structure) resources (unused, always 0) |
| [offset](GFF-File-Format#file-structure) to Variable Resource Table | [uint32](GFF-File-Format#dword) | 16 (0x10) | 4 | [offset](GFF-File-Format#file-structure) to variable resource entries            |

**Note on Fixed Resources:** The "Fixed Resource [count](GFF-File-Format#file-structure)" [field](GFF-File-Format#file-structure) is a legacy holdover from Neverwinter Nights where some resource [types](GFF-File-Format#data-types) had predetermined sizes. In KotOR, this [field](GFF-File-Format#file-structure) is always `0` and fixed resource tables [ARE](GFF-File-Format#are-area) never used. All resources [ARE](GFF-File-Format#are-area) stored in the variable resource table regardless of their [size](GFF-File-Format#file-structure).

**Note on [header](GFF-File-Format#file-header) Variations**: Some older documentation (e.g., xoreos-docs) shows the [field](GFF-File-Format#file-structure) at [offset](GFF-File-Format#file-structure) 0x000C as "Unknown [value](GFF-File-Format#data-types)" rather than "Fixed Resource [count](GFF-File-Format#file-structure)". This reflects the [field](GFF-File-Format#file-structure)'s historical ambiguity, but in practice it serves as the fixed resource count (always 0 in KotOR).

**Reference**: [`vendor/xoreos/src/aurora/biffile.cpp:64-67`](https://github.com/xoreos/xoreos/blob/master/src/aurora/biffile.cpp#L64-L67) explicitly checks that fixed resource [count](GFF-File-Format#file-structure) is 0 and throws an exception if it's not. [`vendor/reone/src/libs/resource/format/bifreader.cpp:34`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/bifreader.cpp#L34) reads the fixed resource [count](GFF-File-Format#file-structure) but does not use it.  
**Reference**: [`vendor/Kotor.NET/Kotor.NET/Formats/KotorBIF/BIFBinaryStructure.cs:13-67`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorBIF/BIFBinaryStructure.cs#L13-L67)  
**Reference**: [`vendor/xoreos-docs/specs/torlack/bif.html`](vendor/xoreos-docs/specs/torlack/bif.html) - Tim Smith (Torlack)'s reverse-engineered [BIF](BIF-File-Format) [format](GFF-File-Format) documentation

### Variable Resource Table

Each variable resource entry is 16 bytes:

| Name        | [type](GFF-File-Format#data-types)   | [offset](GFF-File-Format#file-structure) | [size](GFF-File-Format#file-structure) | Description                                                      |
| ----------- | ------ | ------ | ---- | ---------------------------------------------------------------- |
| Resource ID | [uint32](GFF-File-Format#dword) | 0 (0x00) | 4    | Resource ID (matches [KEY file](KEY-File-Format) entry, encodes [BIF](BIF-File-Format) [index](2DA-File-Format#row-labels) and resource [index](2DA-File-Format#row-labels)) |
| [offset](GFF-File-Format#file-structure)      | [uint32](GFF-File-Format#dword) | 4 (0x04) | 4    | [offset](GFF-File-Format#file-structure) to resource [data](GFF-File-Format#file-structure) in file (absolute [file](GFF-File-Format) [offset](GFF-File-Format#file-structure))                    |
| [file](GFF-File-Format) [size](GFF-File-Format#file-structure)   | [uint32](GFF-File-Format#dword) | 8 (0x08) | 4    | Uncompressed [size](GFF-File-Format#file-structure) of resource data (bytes)                                 |
| Resource [type](GFF-File-Format#data-types) | [uint32](GFF-File-Format#dword) | 12 (0x0C) | 4    | Resource [type](GFF-File-Format#data-types) identifier (see ResourceType enum)                          |

**Entry Reading Order:**

Entries [ARE](GFF-File-Format#are-area) read sequentially from the variable resource table. The table is located at the [offset](GFF-File-Format#file-structure) specified in the [file](GFF-File-Format) [header](GFF-File-Format#file-header). Each entry is exactly 16 bytes, allowing efficient sequential reading.

**Reference**: [`vendor/reone/src/libs/resource/format/bifreader.cpp:50-63`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/bifreader.cpp#L50-L63) shows the exact reading order: Resource ID, [offset](GFF-File-Format#file-structure), [file](GFF-File-Format) [size](GFF-File-Format#file-structure), Resource [type](GFF-File-Format#data-types). [`vendor/Kotor.NET/Kotor.NET/Formats/KotorBIF/BIFBinaryStructure.cs:51-65`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorBIF/BIFBinaryStructure.cs#L51-L65) confirms the same [structure](GFF-File-Format#file-structure). [`vendor/xoreos/src/aurora/biffile.cpp:84-96`](https://github.com/xoreos/xoreos/blob/master/src/aurora/biffile.cpp#L84-L96) shows reading with version-specific handling (V1.1 includes an additional [flags](GFF-File-Format#data-types) [field](GFF-File-Format#file-structure) that KotOR does not use).

### Resource [data](GFF-File-Format#file-structure)

Resource [data](GFF-File-Format#file-structure) is stored at the [offsets](GFF-File-Format#file-structure) specified in the resource table:

| Name         | [type](GFF-File-Format#data-types)   | Description                                                      |
| ------------ | ------ | ---------------------------------------------------------------- |
| Resource [data](GFF-File-Format#file-structure) | [byte](GFF-File-Format#byte)[] | Raw binary [data](GFF-File-Format#file-structure) for each resource                               |

**Resource Storage Details:**

- Resources [ARE](GFF-File-Format#are-area) stored sequentially but not necessarily contiguously (gaps may exist between resources)
- Each resource's [size](GFF-File-Format#file-structure) is specified in the variable resource table entry
- Resource [data](GFF-File-Format#file-structure) is stored in its native format (no additional [BIF](BIF-File-Format)-specific wrapping or metadata)
- [offsets](GFF-File-Format#file-structure) in the variable resource table [ARE](GFF-File-Format#are-area) absolute [file](GFF-File-Format) offsets (relative to start of [file](GFF-File-Format))
- Resource [data](GFF-File-Format#file-structure) begins immediately at the specified [offset](GFF-File-Format#file-structure)

**Resource Access Flow:**

The engine reads resources through the following process:

1. **KEY Lookup**: Look up the ResRef (and optionally ResourceType) in the [KEY file](KEY-File-Format) to get the Resource ID
2. **ID Decoding**: Extract the [BIF](BIF-File-Format) index (upper 12 [bits](GFF-File-Format#data-types)) and resource index (lower 20 [bits](GFF-File-Format#data-types)) from the Resource ID
3. **BIF Selection**: Use the [BIF](BIF-File-Format) [index](2DA-File-Format#row-labels) to identify which [BIF file](BIF-File-Format) contains the resource
4. **Table Access**: Read the [BIF file](BIF-File-Format) [header](GFF-File-Format#file-header) to find the [offset](GFF-File-Format#file-structure) to the variable resource table
5. **Entry Lookup**: Find the resource entry at the specified [index](2DA-File-Format#row-labels) in the variable resource table
6. **[data](GFF-File-Format#file-structure) Reading**: Seek to the [offset](GFF-File-Format#file-structure) specified in the entry and read the number of bytes specified by the [file](GFF-File-Format) [size](GFF-File-Format#file-structure)

**Reference**: [`vendor/xoreos/src/aurora/biffile.cpp:84-96`](https://github.com/xoreos/xoreos/blob/master/src/aurora/biffile.cpp#L84-L96) shows how variable resource entries [ARE](GFF-File-Format#are-area) read. [`vendor/reone/src/libs/resource/format/bifreader.cpp:41-48`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/bifreader.cpp#L41-L48) demonstrates resource table loading. [`vendor/xoreos/src/aurora/biffile.cpp:99-123`](https://github.com/xoreos/xoreos/blob/master/src/aurora/biffile.cpp#L99-L123) shows the mergeKEY process that combines [KEY](KEY-File-Format) and [BIF](BIF-File-Format) information.  
**Reference**: [`vendor/xoreos-docs/specs/torlack/bif.html`](vendor/xoreos-docs/specs/torlack/bif.html) - Resource [structure](GFF-File-Format#file-structure) details (Resource ID, [offset](GFF-File-Format#file-structure), Length, [type](GFF-File-Format#data-types))

**Resource IDs:**

The Resource ID in the [BIF file](BIF-File-Format)'s variable resource table must match the Resource ID stored in the [KEY file](KEY-File-Format). The Resource ID is a 32-[bit](GFF-File-Format#data-types) [value](GFF-File-Format#data-types) that encodes two pieces of information:

- **Lower 20 bits ([bits](GFF-File-Format#data-types) 0-19)**: Resource [index](2DA-File-Format#row-labels) within the [BIF](BIF-File-Format) file (0-based [index](2DA-File-Format#row-labels) into the variable resource table)
- **Upper 12 bits ([bits](GFF-File-Format#data-types) 20-31)**: [BIF](BIF-File-Format) [index](2DA-File-Format#row-labels) in the [KEY file](KEY-File-Format)'s [BIF](BIF-File-Format) table (identifies which [BIF file](BIF-File-Format) contains this resource)

**Example:** A Resource ID of `0x00400029` decodes as:

- Resource [index](2DA-File-Format#row-labels): `0x29` (41st resource in the [BIF](BIF-File-Format))
- [BIF](BIF-File-Format) [index](2DA-File-Format#row-labels): `0x004` (4th [BIF file](BIF-File-Format) in the [KEY](KEY-File-Format)'s [BIF](BIF-File-Format) table)

**Reference**: [`vendor/xoreos-docs/specs/torlack/key.html:154-168`](https://github.com/xoreos/xoreos-docs/blob/master/specs/torlack/key.html#L154-L168) provides detailed explanation of Resource ID encoding. [`vendor/reone/src/libs/resource/format/bifreader.cpp:50-54`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/bifreader.cpp#L50-L54) shows how Resource IDs [ARE](GFF-File-Format#are-area) read from [BIF](BIF-File-Format) entries.

---

## BZF [Compression](https://en.wikipedia.org/wiki/Data_compression)

BZF [files](GFF-File-Format) [ARE](GFF-File-Format#are-area) LZMA-compressed [BIF files](BIF-File-Format) used primarily in iOS (and maybe Android) ports of KotOR. The BZF [header](GFF-File-Format#file-header) contains `"BZF "` + `"V1.0"`, followed by LZMA-compressed [BIF](BIF-File-Format) [data](GFF-File-Format#file-structure). Decompression reveals a standard [BIF](BIF-File-Format) [structure](GFF-File-Format#file-structure).

### BZF [format](GFF-File-Format) Details

The BZF [format](GFF-File-Format) wraps a complete [BIF file](BIF-File-Format) in LZMA compression:

1. **BZF [header](GFF-File-Format#file-header)** (8 bytes): `"BZF "` + `"V1.0"` signature
2. **LZMA Stream**: Compressed [BIF file](BIF-File-Format) [data](GFF-File-Format#file-structure) using LZMA algorithm
3. **Decompressed Result**: Standard [BIF file](BIF-File-Format) structure (as described above)

**Compression Details:**

- The entire [BIF](BIF-File-Format) file (after the 8-[byte](GFF-File-Format#byte) [header](GFF-File-Format#file-header)) is compressed using LZMA (Lempel-Ziv-Markov chain Algorithm)
- LZMA provides high compression ratios with good decompression speed
- The compressed stream follows immediately after the BZF [header](GFF-File-Format#file-header)
- Decompression yields a standard [BIF file](BIF-File-Format) that can be read normally

**Benefits of BZF:**

- Significantly reduced [file](GFF-File-Format) sizes (typically 40-60% compression ratio)
- Faster download times for mobile platforms
- Reduced storage requirements
- Identical resource access after decompression
- No performance penalty during gameplay (decompressed once at load time)

**Platform Usage:**

- PC releases use uncompressed [BIF files](BIF-File-Format) for faster access
- Mobile releases (iOS/Android) use BZF for storage efficiency
- Modding tools can (and should) convert between [BIF](BIF-File-Format) and BZF [formats](GFF-File-Format) freely

**Implementation Notes:**

The BZF wrapper is completely transparent to the game engine - once decompressed in memory, the resource access patterns [ARE](GFF-File-Format#are-area) identical to standard [BIF files](BIF-File-Format). Tools should decompress BZF [files](GFF-File-Format) before reading resource entries, as the variable resource table [offsets](GFF-File-Format#file-structure) [ARE](GFF-File-Format#are-area) relative to the decompressed [BIF](BIF-File-Format) [structure](GFF-File-Format#file-structure).

**Reference**: [`vendor/xoreos/src/aurora/biffile.h:56-60`](https://github.com/xoreos/xoreos/blob/master/src/aurora/biffile.h#L56-L60) documents BZF as compressed [BIF files](BIF-File-Format) found exclusively in Android and iOS versions. [`vendor/reone/src/libs/resource/format/bifreader.cpp:27-30`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/bifreader.cpp#L27-L30) shows [BIF](BIF-File-Format) signature detection. [`Libraries/PyKotor/src/pykotor/resource/formats/bif/bif_data.py:45-52`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bif/bif_data.py#L45-L52) documents BZF compression details.

---

## [KEY](KEY-File-Format) [file](GFF-File-Format) Relationship

[BIF](BIF-File-Format) [files](GFF-File-Format) require a [KEY file](KEY-File-Format) to map resource IDs to filenames (ResRefs). The [KEY file](KEY-File-Format) contains:

- [BIF](BIF-File-Format) [file](GFF-File-Format) entries (filename, [size](GFF-File-Format#file-structure), location)
- [KEY](KEY-File-Format) entries mapping [ResRef](GFF-File-Format#resref) + ResourceType to Resource ID

The Resource ID in the [BIF file](BIF-File-Format) matches the Resource ID in the [KEY file](KEY-File-Format)'s [KEY](KEY-File-Format) entries.

**Reference**: See [KEY File Format](KEY-File-Format) documentation.

---

## Implementation Details

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/bif/io_bif.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/bif/io_bif.py)

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/bif/io_bif.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/bif/io_bif.py)

**[BIF](BIF-File-Format) Class**: [`Libraries/PyKotor/src/pykotor/resource/formats/bif/bif_data.py:100-575`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bif/bif_data.py#L100-L575)

---

This documentation aims to provide a comprehensive overview of the KotOR [BIF file](BIF-File-Format) [format](GFF-File-Format), focusing on the detailed [file](GFF-File-Format) [structure](GFF-File-Format#file-structure) and [data](GFF-File-Format#file-structure) [formats](GFF-File-Format) used within the games.
