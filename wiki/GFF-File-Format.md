# KotOR [GFF](GFF-File-Format) [file](GFF-File-Format) [format](GFF-File-Format) Documentation

This document provides a detailed description of the GFF (Generic [file](GFF-File-Format) [format](GFF-File-Format)) used in Knights of the Old Republic (KotOR) games. GFF is a container [format](GFF-File-Format) used for many different game resource [types](GFF-File-Format#data-types), including character templates, areas, dialogs, placeables, creatures, items, and more.

**Official Bioware Documentation:** For the authoritative Bioware Aurora Engine [GFF](GFF-File-Format) [format](GFF-File-Format) specification, see [Bioware Aurora GFF Format](Bioware-Aurora-GFF) and [Bioware Aurora Common GFF Structs](Bioware-Aurora-CommonGFFStructs).

**For mod developers:** To modify [GFF files](GFF-File-Format) in your mods, see the [TSLPatcher GFFList Syntax Guide](TSLPatcher-GFFList-Syntax). For general modding information, see [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.).

**Related [formats](GFF-File-Format):** [GFF files](GFF-File-Format) often reference other [formats](GFF-File-Format) such as [2DA files](2DA-File-Format) for configuration [data](GFF-File-Format#file-structure), [TLK files](TLK-File-Format) for text [strings](GFF-File-Format#cexostring), [MDL/MDX files](MDL-MDX-File-Format) for 3D [models](MDL-MDX-File-Format), and [NCS files](NCS-File-Format) for scripts.

## Table of Contents

- [KotOR GFF File Format Documentation](#kotor-gff-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
    - [GFF as a Universal Container](#gff-as-a-universal-container)
  - [Binary Format](#binary-format)
    - [File Header](#file-header)
    - [Label Array](#label-array)
    - [Struct Array](#struct-array)
    - [Field Array](#field-array)
    - [Field Data](#field-data)
    - [Field Indices (Multiple Element Map / MultiMap)](#field-indices-multiple-element-map--multimap)
    - [List Indices](#list-indices)
  - [GFF Data Types](#gff-data-types)
  - [GFF Structure](#gff-structure)
    - [GFFStruct](#gffstruct)
    - [GFFField](#gfffield)
    - [GFFList](#gfflist)
  - [GFF Generic Types](#gff-generic-types)
    - [ARE (Area)](#are-area)
    - [DLG (Dialogue)](#dlg-dialogue)
    - [GIT (Game Instance Template)](#git-game-instance-template)
    - [GUI (Graphical User Interface)](#gui-graphical-user-interface)
    - [IFO (Module Info)](#ifo-module-info)
    - [JRL (Journal)](#jrl-journal)
    - [PTH (Path)](#pth-path)
    - [UTC (Creature)](#utc-creature)
    - [UTD (Door)](#utd-door)
    - [UTE (Encounter)](#ute-encounter)
    - [UTI (Item)](#uti-item)
    - [UTM (Merchant)](#utm-merchant)
    - [UTP (Placeable)](#utp-placeable)
    - [UTS (Sound)](#uts-sound)
    - [UTT (Trigger)](#utt-trigger)
    - [UTW (Waypoint)](#utw-waypoint)
  - [Alternative Terminology (Historical)](#alternative-terminology-historical)
  - [Field Data Access Patterns](#field-data-access-patterns)
    - [Direct Access Types](#direct-access-types)
    - [Indirect Access Types](#indirect-access-types)
    - [Complex Access Types](#complex-access-types)
  - [Implementation Details](#implementation-details)

---

## [file](GFF-File-Format) [structure](GFF-File-Format#file-structure) Overview

[GFF files](GFF-File-Format) use a hierarchical [structure](GFF-File-Format#file-structure) with structs containing [fields](GFF-File-Format#file-structure), which can be simple [values](GFF-File-Format#data-types) or nested structs and lists. The [format](GFF-File-Format) supports version V3.2 (KotOR) and later versions (V3.3, V4.0, V4.1) used in other BioWare games.

### [GFF](GFF-File-Format) as a Universal Container

[GFF](GFF-File-Format) is BioWare's universal container [format](GFF-File-Format) for structured game [data](GFF-File-Format#file-structure). Think of it as a binary JSON or XML with strong typing:

**Advantages:**

- **[type](GFF-File-Format#data-types) Safety**: Each [field](GFF-File-Format#file-structure) has an explicit [data](GFF-File-Format#file-structure) type (unlike text [formats](GFF-File-Format))
- **Compact**: Binary encoding is much smaller than equivalent XML/JSON
- **Fast**: Direct memory mapping without parsing overhead
- **Hierarchical**: Natural representation of nested game [data](GFF-File-Format#file-structure)
- **Extensible**: New [fields](GFF-File-Format#file-structure) can be added without breaking compatibility

**Common Uses:**

- Character/Creature templates ([UTC](GFF-File-Format#utc-creature), [UTP](GFF-File-Format#utp-placeable), [UTD](GFF-File-Format#utd-door), [UTE](GFF-File-Format#ute-encounter), etc.)
- Area definitions ([ARE](GFF-File-Format#are-area), [GIT](GFF-File-Format#git-game-instance-template), [IFO](GFF-File-Format#ifo-module-info))
- Dialogue trees ([DLG](GFF-File-Format#dlg-dialogue))
- Quest journals ([JRL](GFF-File-Format#jrl-journal))
- Module information ([IFO](GFF-File-Format#ifo-module-info))
- Save game state (SAV [files](GFF-File-Format) contain [GFF](GFF-File-Format) resources)
- User interface layouts ([GUI](GFF-File-Format#gui-graphical-user-interface))

Every `.utc` ([UTC](GFF-File-Format#utc-creature)), `.uti` ([UTI](GFF-File-Format#uti-item)), `.dlg` ([DLG](GFF-File-Format#dlg-dialogue)), `.are` ([ARE](GFF-File-Format#are-area)), and dozens of other KotOR [file](GFF-File-Format) [types](GFF-File-Format#data-types) [ARE](GFF-File-Format#are-area) [GFF files](GFF-File-Format) with different [file](GFF-File-Format) [type](GFF-File-Format#data-types) signatures and [field](GFF-File-Format#file-structure) schemas.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/gff/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/)

**Vendor References:**

- [`vendor/reone/src/libs/resource/gff.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/gff.cpp) - Complete C++ [GFF](GFF-File-Format) reader/writer implementation
- [`vendor/reone/include/reone/resource/gff.h`](https://github.com/th3w1zard1/reone/blob/master/include/reone/resource/gff.h) - [GFF](GFF-File-Format) [type](GFF-File-Format#data-types) definitions and API
- [`vendor/xoreos/src/aurora/gff3file.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/gff3file.cpp) - Generic Aurora GFF3 implementation (shared [format](GFF-File-Format))
- [`vendor/KotOR.js/src/resource/GFFObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/GFFObject.ts) - TypeScript [GFF](GFF-File-Format) parser with schema validation
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/GFFObject.cs`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/GFFObject.cs) - C# Unity [GFF](GFF-File-Format) loader
- [`vendor/Kotor.NET/Kotor.NET/Formats/KotorGFF/GFF.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorGFF/GFF.cs) - .NET GFF reader/writer
- [`vendor/xoreos-tools/src/aurora/gff3file.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/aurora/gff3file.cpp) - Command-line [GFF](GFF-File-Format) tools implementation

**See Also:**

- [TSLPatcher GFFList Syntax](TSLPatcher-GFFList-Syntax) - Modding [GFF files](GFF-File-Format) with TSLPatcher
- [2DA File Format](2DA-File-Format) - Configuration [data](GFF-File-Format#file-structure) referenced by [GFF](GFF-File-Format) files
- [TLK File Format](TLK-File-Format) - Text [strings](GFF-File-Format#cexostring) used by [GFF](GFF-File-Format) LocalizedString [fields](GFF-File-Format#file-structure)
- [Bioware Aurora GFF Format](Bioware-Aurora-GFF) - Official BioWare specification

---

## Binary Format

### File Header

The file header is 56 bytes in size:

| Name                | [type](GFF-File-Format#data-types)    | [offset](GFF-File-Format#file-structure) | [size](GFF-File-Format#file-structure) | Description                                    |
| ------------------- | ------- | ------ | ---- | ---------------------------------------------- |
| [file](GFF-File-Format) [type](GFF-File-Format#data-types)           | [char][GFF-File-Format#char](4) | 0 (0x00) | 4    | Content type (e.g., `"GFF "`, `"ARE "`, `"UTC "`) |
| [file](GFF-File-Format) Version        | [char][GFF-File-Format#char](4) | 4 (0x04) | 4    | [format](GFF-File-Format) version (`"V3.2"` for KotOR)           |
| Struct [array](2DA-File-Format) [offset](GFF-File-Format#file-structure) | [uint32](GFF-File-Format#dword)  | 8 (0x08) | 4    | [offset](GFF-File-Format#file-structure) to struct [array](2DA-File-Format)                        |
| Struct [count](GFF-File-Format#file-structure)        | [uint32](GFF-File-Format#dword)  | 12 (0x0C) | 4    | Number of structs                              |
| Field Array Offset  | [uint32](GFF-File-Format#dword)  | 16 (0x10) | 4    | [offset](GFF-File-Format#file-structure) to [field](GFF-File-Format#file-structure) [array](2DA-File-Format)                         |
| [field](GFF-File-Format#file-structure) [count](GFF-File-Format#file-structure)         | [uint32](GFF-File-Format#dword)  | 20 (0x14) | 4    | Number of [fields](GFF-File-Format#file-structure)                               |
| Label [array](2DA-File-Format) [offset](GFF-File-Format#file-structure)   | [uint32](GFF-File-Format#dword)  | 24 (0x18) | 4    | [offset](GFF-File-Format#file-structure) to label [array](2DA-File-Format)                         |
| Label [count](GFF-File-Format#file-structure)          | [uint32](GFF-File-Format#dword)  | 28 (0x1C) | 4    | Number of labels                               |
| Field Data Offset    | [uint32](GFF-File-Format#dword)  | 32 (0x20) | 4    | [offset](GFF-File-Format#file-structure) to [field](GFF-File-Format#file-structure) [data](GFF-File-Format#file-structure) section                  |
| Field Data Count     | [uint32](GFF-File-Format#dword)  | 36 (0x24) | 4    | [size](GFF-File-Format#file-structure) of [field](GFF-File-Format#file-structure) [data](GFF-File-Format#file-structure) section in bytes           |
| [field](GFF-File-Format#file-structure) [indices](2DA-File-Format#row-labels) [offset](GFF-File-Format#file-structure) | [uint32](GFF-File-Format#dword)  | 40 (0x28) | 4    | [offset](GFF-File-Format#file-structure) to [field](GFF-File-Format#file-structure) [indices](2DA-File-Format#row-labels) [array](2DA-File-Format)                 |
| [field](GFF-File-Format#file-structure) [indices](2DA-File-Format#row-labels) [count](GFF-File-Format#file-structure)  | [uint32](GFF-File-Format#dword)  | 44 (0x2C) | 4    | Number of [field](GFF-File-Format#file-structure) [indices](2DA-File-Format#row-labels)                       |
| List [indices](2DA-File-Format#row-labels) [offset](GFF-File-Format#file-structure)  | [uint32](GFF-File-Format#dword)  | 48 (0x30) | 4    | [offset](GFF-File-Format#file-structure) to list [indices](2DA-File-Format#row-labels) [array](2DA-File-Format)                  |
| List [indices](2DA-File-Format#row-labels) [count](GFF-File-Format#file-structure)   | [uint32](GFF-File-Format#dword)  | 52 (0x34) | 4    | Number of list [indices](2DA-File-Format#row-labels)                        |

**Reference**: [`vendor/reone/src/libs/resource/format/gffreader.cpp:30-44`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/gffreader.cpp#L30-L44)

### Label [array](2DA-File-Format)

Labels [ARE](GFF-File-Format#are-area) 16-[byte](GFF-File-Format#byte) [null-terminated](https://en.cppreference.com/w/c/string/byte) [strings](GFF-File-Format#cexostring) used as [field](GFF-File-Format#file-structure) names:

| Name   | [type](GFF-File-Format#data-types)     | [size](GFF-File-Format#file-structure) | Description                                                      |
| ------ | -------- | ---- | ---------------------------------------------------------------- |
| Labels | [char][GFF-File-Format#char](16) | 16×N | [array](2DA-File-Format) of [field](GFF-File-Format#file-structure) name labels (null-padded to 16 bytes)            |

**Reference**: [`vendor/reone/src/libs/resource/format/gffreader.cpp:151-154`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/gffreader.cpp#L151-L154)

### Struct [array](2DA-File-Format)

Each struct entry is 12 bytes:

| Name       | [type](GFF-File-Format#data-types)   | [offset](GFF-File-Format#file-structure) | [size](GFF-File-Format#file-structure) | Description                                                      |
| ---------- | ------ | ------ | ---- | ---------------------------------------------------------------- |
| Struct ID  | [int32](GFF-File-Format#int)  | 0 (0x00) | 4    | [structure](GFF-File-Format#file-structure) [type](GFF-File-Format#data-types) identifier                                        |
| [data](GFF-File-Format#file-structure)/[offset](GFF-File-Format#file-structure)| [uint32](GFF-File-Format#dword) | 4 (0x04) | 4    | [field](GFF-File-Format#file-structure) index (if 1 [field](GFF-File-Format#file-structure)) or [offset](GFF-File-Format#file-structure) to [field](GFF-File-Format#file-structure) indices (if multiple) |
| [field](GFF-File-Format#file-structure) [count](GFF-File-Format#file-structure)| [uint32](GFF-File-Format#dword) | 8 (0x08) | 4    | Number of [fields](GFF-File-Format#file-structure) in this struct (0, 1, or >1)                   |

**Reference**: [`vendor/reone/src/libs/resource/format/gffreader.cpp:40-62`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/gffreader.cpp#L40-L62)

### [field](GFF-File-Format#file-structure) [array](2DA-File-Format)

Each [field](GFF-File-Format#file-structure) entry is 12 bytes:

| Name        | [type](GFF-File-Format#data-types)   | [offset](GFF-File-Format#file-structure) | [size](GFF-File-Format#file-structure) | Description                                                      |
| ----------- | ------ | ------ | ---- | ---------------------------------------------------------------- |
| [field](GFF-File-Format#file-structure) [type](GFF-File-Format#data-types)  | [uint32](GFF-File-Format#dword) | 0 (0x00) | 4    | [data](GFF-File-Format#file-structure) type (see [GFF Data Types](#gff-data-types))              |
| Label [index](2DA-File-Format#row-labels) | [uint32](GFF-File-Format#dword) | 4 (0x04) | 4    | [index](2DA-File-Format#row-labels) into label [array](2DA-File-Format) for [field](GFF-File-Format#file-structure) name                           |
| [data](GFF-File-Format#file-structure)/[offset](GFF-File-Format#file-structure) | [uint32](GFF-File-Format#dword) | 8 (0x08) | 4    | Inline data (simple [types](GFF-File-Format#data-types)) or [offset](GFF-File-Format#file-structure) to [field](GFF-File-Format#file-structure) data (complex [types](GFF-File-Format#data-types)) |

**Reference**: [`vendor/reone/src/libs/resource/format/gffreader.cpp:67-76`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/gffreader.cpp#L67-L76)

### [field](GFF-File-Format#file-structure) [data](GFF-File-Format#file-structure)

Complex [field](GFF-File-Format#file-structure) [types](GFF-File-Format#data-types) store their data in the field data section:

| Field Type        | Storage Format                                                      |
| ----------------- | ------------------------------------------------------------------- |
| UInt64            | 8 bytes (uint64)                                                    |
| Int64             | 8 bytes (int64)                                                     |
| [double](GFF-File-Format#double)            | 8 bytes ([double](GFF-File-Format#double))                                                    |
| [string](GFF-File-Format#cexostring)            | 4 bytes length + N bytes [string](GFF-File-Format#cexostring) [data](GFF-File-Format#file-structure)                                |
| [ResRef](GFF-File-Format#resref)            | 1 [byte](GFF-File-Format#byte) length + N bytes [ResRef](GFF-File-Format#resref) data (max 16 chars)                  |
| LocalizedString   | 4 bytes [count](GFF-File-Format#file-structure) + N×8 bytes (Language ID + [StrRef](TLK-File-Format#string-references-strref) pairs)              |
| Binary            | 4 bytes length + N bytes binary [data](GFF-File-Format#file-structure)                                 |
| Vector3           | 12 bytes (3×[float](GFF-File-Format#float))                                                   |
| Vector4           | 16 bytes (4×[float](GFF-File-Format#float))                                                   |

**Reference**: [`vendor/reone/src/libs/resource/format/gffreader.cpp:78-146`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/gffreader.cpp#L78-L146)

### [field](GFF-File-Format#file-structure) Indices (Multiple Element Map / MultiMap)

When a struct has multiple [fields](GFF-File-Format#file-structure), the struct's [data](GFF-File-Format#file-structure) [field](GFF-File-Format#file-structure) contains an [offset](GFF-File-Format#file-structure) into the [field](GFF-File-Format#file-structure) [indices](2DA-File-Format#row-labels) array (also called the "Multiple Element Map" or "MultiMap" in older documentation), which lists the [field](GFF-File-Format#file-structure) [indices](2DA-File-Format#row-labels) for that struct.

**Access Pattern**: When a struct has exactly one [field](GFF-File-Format#file-structure), the struct's [data](GFF-File-Format#file-structure) [field](GFF-File-Format#file-structure) directly contains the [field](GFF-File-Format#file-structure) [index](2DA-File-Format#row-labels). When a struct has more than one [field](GFF-File-Format#file-structure), the [data](GFF-File-Format#file-structure) [field](GFF-File-Format#file-structure) contains a [byte](GFF-File-Format#byte) [offset](GFF-File-Format#file-structure) into the [field](GFF-File-Format#file-structure) [indices](2DA-File-Format#row-labels) [array](2DA-File-Format), which is an [array](2DA-File-Format) of [uint32](GFF-File-Format#dword) [values](GFF-File-Format#data-types) listing the [field](GFF-File-Format#file-structure) [indices](2DA-File-Format#row-labels).

**Reference**: [`vendor/xoreos-docs/specs/torlack/itp.html`](vendor/xoreos-docs/specs/torlack/itp.html) - Entry/Entity table access patterns and MultiMap explanation

### List [indices](2DA-File-Format#row-labels)

Lists [ARE](GFF-File-Format#are-area) stored as [arrays](2DA-File-Format) of struct [indices](2DA-File-Format#row-labels). The list [field](GFF-File-Format#file-structure) contains an [offset](GFF-File-Format#file-structure) into the list [indices](2DA-File-Format#row-labels) [array](2DA-File-Format), which contains the struct [indices](2DA-File-Format#row-labels) that make up the list.

**Access Pattern**: For a LIST [type](GFF-File-Format#data-types) [field](GFF-File-Format#file-structure), the [field](GFF-File-Format#file-structure)'s [data](GFF-File-Format#file-structure)/[offset](GFF-File-Format#file-structure) [value](GFF-File-Format#data-types) specifies a [byte](GFF-File-Format#byte) [offset](GFF-File-Format#file-structure) into the list [indices](2DA-File-Format#row-labels) table. At that [offset](GFF-File-Format#file-structure), the first [uint32](GFF-File-Format#dword) is the [count](GFF-File-Format#file-structure) of entries, followed by that many [uint32](GFF-File-Format#dword) [values](GFF-File-Format#data-types) representing the struct [indices](2DA-File-Format#row-labels).

**Reference**: [`vendor/xoreos-docs/specs/torlack/itp.html`](vendor/xoreos-docs/specs/torlack/itp.html) - LIST [type](GFF-File-Format#data-types) access pattern

---

## [GFF](GFF-File-Format) [data](GFF-File-Format#file-structure) [types](GFF-File-Format#data-types)

[GFF](GFF-File-Format) supports the following [field](GFF-File-Format#file-structure) [types](GFF-File-Format#data-types):

| [type](GFF-File-Format#data-types) ID | Name              | Size (inline) | Description                                                      |
| ------- | ----------------- | ------------- | ---------------------------------------------------------------- |
| 0       | [byte](GFF-File-Format#byte)              | 1             | 8-[bit](GFF-File-Format#data-types) unsigned integer                                           |
| 1       | [char](GFF-File-Format#char)              | 1             | 8-[bit](GFF-File-Format#data-types) signed integer                                              |
| 2       | Word              | 2             | 16-[bit](GFF-File-Format#data-types) unsigned integer                                          |
| 3       | Short             | 2             | 16-[bit](GFF-File-Format#data-types) signed integer                                             |
| 4       | DWord             | 4             | 32-[bit](GFF-File-Format#data-types) unsigned integer                                          |
| 5       | Int               | 4             | 32-[bit](GFF-File-Format#data-types) signed integer                                             |
| 6       | DWord64           | 8             | 64-[bit](GFF-File-Format#data-types) unsigned integer (stored in [field](GFF-File-Format#file-structure) [data](GFF-File-Format#file-structure))                  |
| 7       | Int64              | 8             | 64-[bit](GFF-File-Format#data-types) signed integer (stored in [field](GFF-File-Format#file-structure) [data](GFF-File-Format#file-structure))                      |
| 8       | [float](GFF-File-Format#float)             | 4             | 32-[bit](GFF-File-Format#data-types) floating point                                             |
| 9       | [double](GFF-File-Format#double)            | 8             | 64-[bit](GFF-File-Format#data-types) floating point (stored in [field](GFF-File-Format#file-structure) [data](GFF-File-Format#file-structure))                     |
| 10      | [CExoString](GFF-File-Format#cexostring)        | varies        | [null-terminated](https://en.cppreference.com/w/c/string/byte) string (stored in [field](GFF-File-Format#file-structure) [data](GFF-File-Format#file-structure))                    |
| 11      | [ResRef](GFF-File-Format#resref)            | varies        | Resource reference (stored in [field](GFF-File-Format#file-structure) [data](GFF-File-Format#file-structure), max 16 chars)          |
| 12      | [CExoLocString](GFF-File-Format#localizedstring)     | varies        | Localized string (stored in [field](GFF-File-Format#file-structure) [data](GFF-File-Format#file-structure))                           |
| 13      | Void              | varies        | Binary [data](GFF-File-Format#file-structure) blob (stored in [field](GFF-File-Format#file-structure) [data](GFF-File-Format#file-structure))                          |
| 14      | Struct            | 4             | Nested struct (struct [index](2DA-File-Format#row-labels) stored inline)                       |
| 15      | List              | 4             | List of structs ([offset](GFF-File-Format#file-structure) to list [indices](2DA-File-Format#row-labels) stored inline)            |
| 16      | [orientation](MDL-MDX-File-Format#node-header)       | 16            | Quaternion (4×[float](GFF-File-Format#float), stored in [field](GFF-File-Format#file-structure) [data](GFF-File-Format#file-structure) as Vector4)            |
| 17      | [vector](GFF-File-Format#vector)            | 12            | 3D vector (3×[float](GFF-File-Format#float), stored in [field](GFF-File-Format#file-structure) [data](GFF-File-Format#file-structure))                       |
| 18      | [StrRef](TLK-File-Format#string-references-strref)            | 4             | [string](GFF-File-Format#cexostring) reference ([TLK](TLK-File-Format) [StrRef](TLK-File-Format#string-references-strref), stored inline as [int32](GFF-File-Format#int))             |

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py:73-108`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py#L73-L108)

**[type](GFF-File-Format#data-types) Selection Guidelines:**

- Use **[byte](GFF-File-Format#byte)/[char](GFF-File-Format#char)** for small integers (-128 to 255) and boolean [flags](GFF-File-Format#data-types)
- Use **Word/Short** for medium integers like IDs and counts
- Use **DWord/Int** for large [values](GFF-File-Format#data-types) and most numeric [fields](GFF-File-Format#file-structure)
- Use **[float](GFF-File-Format#float)** for decimals that don't need high precision ([positions](MDL-MDX-File-Format#node-header), angles)
- Use **[double](GFF-File-Format#double)** for high-precision calculations (rare in KotOR)
- Use **[CExoString](GFF-File-Format#cexostring)** for text that doesn't need localization
- Use **[CExoLocString](GFF-File-Format#localizedstring)** for player-visible text that should be translated
- Use **[ResRef](GFF-File-Format#resref)** for filenames without extensions ([models](MDL-MDX-File-Format), [textures](TPC-File-Format), scripts)
- Use **Void** for binary blobs like encrypted [data](GFF-File-Format#file-structure) or custom [structures](GFF-File-Format#file-structure)
- Use **Struct** for nested objects with multiple [fields](GFF-File-Format#file-structure)
- Use **List** for [arrays](2DA-File-Format) of structs (inventory items, dialogue replies)
- Use **[vector](GFF-File-Format#vector)** for 3D [positions](MDL-MDX-File-Format#node-header) and directions
- Use **[orientation](MDL-MDX-File-Format#node-header)** for [quaternion](MDL-MDX-File-Format#node-header) [rotations](MDL-MDX-File-Format#node-header)
- Use **[StrRef](TLK-File-Format#string-references-strref)** for references to [dialog.tlk](TLK-File-Format) entries

**Storage Optimization:**

Inline types (0-5, 8, 14, 15, 18) store their [value](GFF-File-Format#data-types) directly in the [field](GFF-File-Format#file-structure) entry, saving space and improving access speed. Complex types (6-7, 9-13, 16-17) require an [offset](GFF-File-Format#file-structure) to [field](GFF-File-Format#file-structure) [data](GFF-File-Format#file-structure), adding overhead. When designing custom [GFF](GFF-File-Format) schemas, prefer inline [types](GFF-File-Format#data-types) where possible.

---

## [GFF](GFF-File-Format) [structure](GFF-File-Format#file-structure)

### GFFStruct

A [GFF](GFF-File-Format) struct is a collection of named [fields](GFF-File-Format#file-structure). Each struct has:

- **Struct ID**: [type](GFF-File-Format#data-types) identifier (often 0xFFFFFFFF for generic structs)
- **[fields](GFF-File-Format#file-structure)**: Dictionary mapping [field](GFF-File-Format#file-structure) names (labels) to [field](GFF-File-Format#file-structure) [values](GFF-File-Format#data-types)

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py:400-800`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py#L400-L800)

### GFFField

[fields](GFF-File-Format#file-structure) can be accessed using [type](GFF-File-Format#data-types)-specific getter/setter methods:

- `get_uint8(label)`, `set_uint8(label, value)`
- `get_int32(label)`, `set_int32(label, value)`
- `get_float(label)`, `set_float(label, value)`
- `get_string(label)`, `set_string(label, value)`
- `get_resref(label)`, `set_resref(label, value)`
- `get_locstring(label)`, `set_locstring(label, value)`
- `get_vector3(label)`, `set_vector3(label, value)`
- `get_struct(label)`, `set_struct(label, struct)`
- `get_list(label)`, `set_list(label, list)`

### GFFList

A [GFF](GFF-File-Format) list is an ordered collection of structs. Lists [ARE](GFF-File-Format#are-area) accessed via:

- `get_list(label)`: Returns a `GFFList` object
- `GFFList.get(i)`: Gets struct at [index](2DA-File-Format#row-labels) `i`
- `GFFList.append(struct)`: Adds a struct to the list

**Common List Usage:**

Lists [ARE](GFF-File-Format#are-area) used extensively for variable-length [arrays](2DA-File-Format):

- **ItemList** in [UTC](GFF-File-Format#utc-creature) [files](GFF-File-Format): Character inventory items
- **Equip_ItemList** in [UTC](GFF-File-Format#utc-creature) [files](GFF-File-Format): Equipped items
- **EntryList** in [DLG](GFF-File-Format#dlg-dialogue) [files](GFF-File-Format): Dialogue entry [nodes](MDL-MDX-File-Format#node-structures)
- **ReplyList** in [DLG](GFF-File-Format#dlg-dialogue) [files](GFF-File-Format): Dialogue reply options
- **SkillList** in [UTC](GFF-File-Format#utc-creature) [files](GFF-File-Format): Character skills
- **FeatList** in [UTC](GFF-File-Format#utc-creature) [files](GFF-File-Format): Character feats
- **EffectList** in various [files](GFF-File-Format): Applied effects
- **Creature_List** in [GIT](GFF-File-Format#git-game-instance-template) [files](GFF-File-Format): Spawned creatures in area

When modifying lists, always maintain struct IDs and parent references to avoid breaking internal links.

---

## [GFF](GFF-File-Format) Generic [types](GFF-File-Format#data-types)

[GFF files](GFF-File-Format) [ARE](GFF-File-Format#are-area) used as containers for various game resource [types](GFF-File-Format#data-types). Each generic [type](GFF-File-Format#data-types) has its own [structure](GFF-File-Format#file-structure) and [field](GFF-File-Format#file-structure) definitions.

### ARE (Area)

See [ARE (Area)](GFF-ARE) for detailed documentation.

### DLG (Dialogue)

See [DLG (Dialogue)](GFF-DLG) for detailed documentation.

### GIT ([game instance template](GFF-File-Format#git-game-instance-template))

See [GIT (Game Instance Template)](GFF-GIT) for detailed documentation.

### GUI (Graphical User Interface)

See [GUI (Graphical User Interface)](GFF-GUI) for detailed documentation.

### IFO ([module info](GFF-File-Format#ifo-module-info))

See [IFO (Module Info)](GFF-IFO) for detailed documentation.

### JRL (Journal)

See [JRL (Journal)](GFF-JRL) for detailed documentation.

### PTH (Path)

See [PTH (Path)](GFF-PTH) for detailed documentation.

### UTC (Creature)

See [UTC (Creature)](GFF-UTC) for detailed documentation.

### UTD (Door)

See [UTD (Door)](GFF-UTD) for detailed documentation.

### UTE (Encounter)

See [UTE (Encounter)](GFF-UTE) for detailed documentation.

### UTI (Item)

See [UTI (Item)](GFF-UTI) for detailed documentation.

### UTM (Merchant)

See [UTM (Merchant)](GFF-UTM) for detailed documentation.

### UTP (Placeable)

See [UTP (Placeable)](GFF-UTP) for detailed documentation.

### UTS (Sound)

See [UTS (Sound)](GFF-UTS) for detailed documentation.

### UTT (Trigger)

See [UTT (Trigger)](GFF-UTT) for detailed documentation.

### UTW (Waypoint)

See [UTW (Waypoint)](GFF-UTW) for detailed documentation.

## Alternative Terminology (Historical)

The [GFF](GFF-File-Format) [format](GFF-File-Format) is also known as "ITP" in older documentation (from Neverwinter Nights era). The following terminology mapping may be helpful when reading older specifications:

| Modern Term ([GFF](GFF-File-Format)) | Historical Term (ITP) | Description |
| ----------------- | --------------------- | ----------- |
| Struct [array](2DA-File-Format) | Entry Table / Entity Table | [array](2DA-File-Format) of struct entries |
| [field](GFF-File-Format#file-structure) [array](2DA-File-Format) | Element Table | [array](2DA-File-Format) of [field](GFF-File-Format#file-structure)/element entries |
| Label [array](2DA-File-Format) | Variable Names Table | [array](2DA-File-Format) of 16-[byte](GFF-File-Format#byte) [field](GFF-File-Format#file-structure) name [strings](GFF-File-Format#cexostring) |
| [field](GFF-File-Format#file-structure) [data](GFF-File-Format#file-structure) | Variable [data](GFF-File-Format#file-structure) Section | Storage for complex [field](GFF-File-Format#file-structure) [types](GFF-File-Format#data-types) |
| [field](GFF-File-Format#file-structure) [indices](2DA-File-Format#row-labels) | Multiple Element Map (MultiMap) | [array](2DA-File-Format) mapping structs to their [fields](GFF-File-Format#file-structure) |
| List [indices](2DA-File-Format#row-labels) | List Section | [array](2DA-File-Format) mapping list [fields](GFF-File-Format#file-structure) to struct [indices](2DA-File-Format#row-labels) |

**Note**: The first entry in the struct [array](2DA-File-Format) is always the root of the entire hierarchy. All other structs and [fields](GFF-File-Format#file-structure) can be accessed from this root entry.

**Reference**: [`vendor/xoreos-docs/specs/torlack/itp.html`](vendor/xoreos-docs/specs/torlack/itp.html) - Tim Smith (Torlack)'s reverse-engineered [GFF](GFF-File-Format)/ITP [format](GFF-File-Format) documentation

## [field](GFF-File-Format#file-structure) [data](GFF-File-Format#file-structure) Access Patterns

### Direct Access [types](GFF-File-Format#data-types)

Simple types ([uint8](GFF-File-Format#byte), Int8, [uint16](GFF-File-Format#word), [int16](GFF-File-Format#short), [uint32](GFF-File-Format#dword), [int32](GFF-File-Format#int), [float](GFF-File-Format#float)) store their [values](GFF-File-Format#data-types) directly in the [field](GFF-File-Format#file-structure) entry's [data](GFF-File-Format#file-structure)/[offset](GFF-File-Format#file-structure) field ([offset](GFF-File-Format#file-structure) 0x0008 in the element [structure](GFF-File-Format#file-structure)). These [values](GFF-File-Format#data-types) [ARE](GFF-File-Format#are-area) stored in [little-endian](https://en.wikipedia.org/wiki/Endianness) [format](GFF-File-Format).

### Indirect Access [types](GFF-File-Format#data-types)

Complex [types](GFF-File-Format#data-types) require accessing [data](GFF-File-Format#file-structure) from the [field](GFF-File-Format#file-structure) [data](GFF-File-Format#file-structure) section:

- **UInt64, Int64, [double](GFF-File-Format#double)**: The [field](GFF-File-Format#file-structure)'s [data](GFF-File-Format#file-structure)/[offset](GFF-File-Format#file-structure) contains a [byte](GFF-File-Format#byte) [offset](GFF-File-Format#file-structure) into the [field](GFF-File-Format#file-structure) [data](GFF-File-Format#file-structure) section where the 8-[byte](GFF-File-Format#byte) [value](GFF-File-Format#data-types) is stored.
- **String ([CExoString](GFF-File-Format#cexostring))**: The [offset](GFF-File-Format#file-structure) points to a [uint32](GFF-File-Format#dword) length followed by the [string](GFF-File-Format#cexostring) bytes (not [null-terminated](https://en.cppreference.com/w/c/string/byte)).
- **[ResRef](GFF-File-Format#resref)**: The [offset](GFF-File-Format#file-structure) points to a [uint8](GFF-File-Format#byte) length (max 16) followed by the resource name bytes (not [null-terminated](https://en.cppreference.com/w/c/string/byte)).
- **LocalizedString ([CExoLocString](GFF-File-Format#localizedstring))**: The [offset](GFF-File-Format#file-structure) points to a [structure](GFF-File-Format#file-structure) containing:
  - [uint32](GFF-File-Format#dword): Total size (not including this [count](GFF-File-Format#file-structure))
  - [int32](GFF-File-Format#int): [StrRef](TLK-File-Format#string-references-strref) ID ([dialog.tlk](TLK-File-Format) reference, -1 if none)
  - [uint32](GFF-File-Format#dword): Number of language-specific [strings](GFF-File-Format#cexostring)
  - For each language string (if [count](GFF-File-Format#file-structure) > 0):
    - [uint32](GFF-File-Format#dword): Language ID
    - [uint32](GFF-File-Format#dword): [string](GFF-File-Format#cexostring) length in bytes
    - [char](GFF-File-Format#char)[]: [string](GFF-File-Format#cexostring) [data](GFF-File-Format#file-structure)
- **Void (Binary)**: The [offset](GFF-File-Format#file-structure) points to a [uint32](GFF-File-Format#dword) length followed by the binary [data](GFF-File-Format#file-structure) bytes.
- **Vector3**: The [offset](GFF-File-Format#file-structure) points to 12 bytes (3×[float](GFF-File-Format#float)) in the [field](GFF-File-Format#file-structure) [data](GFF-File-Format#file-structure) section.
- **Vector4 / [orientation](MDL-MDX-File-Format#node-header)**: The [offset](GFF-File-Format#file-structure) points to 16 bytes (4×[float](GFF-File-Format#float)) in the [field](GFF-File-Format#file-structure) [data](GFF-File-Format#file-structure) section.

### Complex Access [types](GFF-File-Format#data-types)

- **Struct (CAPREF)**: The [field](GFF-File-Format#file-structure)'s [data](GFF-File-Format#file-structure)/[offset](GFF-File-Format#file-structure) contains a struct index (not an [offset](GFF-File-Format#file-structure)). This references a struct in the struct [array](2DA-File-Format).
- **List**: The [field](GFF-File-Format#file-structure)'s [data](GFF-File-Format#file-structure)/[offset](GFF-File-Format#file-structure) contains a [byte](GFF-File-Format#byte) [offset](GFF-File-Format#file-structure) into the list [indices](2DA-File-Format#row-labels) [array](2DA-File-Format). At that [offset](GFF-File-Format#file-structure), the first [uint32](GFF-File-Format#dword) is the entry [count](GFF-File-Format#file-structure), followed by that many [uint32](GFF-File-Format#dword) struct [indices](2DA-File-Format#row-labels).

**Reference**: [`vendor/xoreos-docs/specs/torlack/itp.html`](vendor/xoreos-docs/specs/torlack/itp.html) - Detailed [field](GFF-File-Format#file-structure) [data](GFF-File-Format#file-structure) access patterns and code examples

## Implementation Details

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/gff/io_gff.py:26-419`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/io_gff.py#L26-L419)

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/gff/io_gff.py:421-800`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/io_gff.py#L421-L800)

**[GFF](GFF-File-Format) Class**: [`Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py:200-400`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py#L200-L400)

**GFFStruct Class**: [`Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py:400-800`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py#L400-L800)

---

This documentation aims to provide a comprehensive overview of the KotOR [GFF file](GFF-File-Format) [format](GFF-File-Format), focusing on the detailed [file](GFF-File-Format) [structure](GFF-File-Format#file-structure) and [data](GFF-File-Format#file-structure) [formats](GFF-File-Format) used within the games.
