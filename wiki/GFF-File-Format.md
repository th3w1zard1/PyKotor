# KotOR GFF File Format Documentation

This document provides a detailed description of the GFF (Generic File Format) used in Knights of the Old Republic (KotOR) games. GFF is a container format used for many different game resource types, including character templates, areas, dialogs, placeables, creatures, items, and more.

**Official Bioware Documentation:** For the authoritative Bioware Aurora Engine GFF format specification, see [Bioware Aurora GFF Format](Bioware-Aurora-GFF) and [Bioware Aurora Common GFF Structs](Bioware-Aurora-CommonGFFStructs).

**For mod developers:** To modify GFF files in your mods, see the [TSLPatcher GFFList Syntax Guide](TSLPatcher-GFFList-Syntax). For general modding information, see [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.).

**Related formats:** GFF files often reference other formats such as [2DA files](2DA-File-Format) for configuration data, [TLK files](TLK-File-Format) for text strings, [MDL/MDX files](MDL-MDX-File-Format) for 3D models, and [NCS files](NCS-File-Format) for scripts.

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
    - [Field Indices](#field-indices)
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
    - [GUI](#gui)
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
  - [Implementation Details](#implementation-details)

---

## File Structure Overview

GFF files use a [hierarchical](https://en.wikipedia.org/wiki/Hierarchical_data_model) structure with [structs](https://en.wikipedia.org/wiki/Struct_(C_programming_language)) containing fields, which can be simple values or nested structs and lists. The format supports version V3.2 (KotOR) and later versions (V3.3, V4.0, V4.1) used in other BioWare games.

### GFF as a Universal Container

GFF is BioWare's universal container format for structured game data. Think of it as a binary [JSON](https://en.wikipedia.org/wiki/JSON) or [XML](https://en.wikipedia.org/wiki/XML) with strong typing:

**Advantages:**

- **[Type Safety](https://en.wikipedia.org/wiki/Type_safety)**: Each field has an explicit data type (unlike text formats)
- **Compact**: [Binary encoding](https://en.wikipedia.org/wiki/Binary_code) is much smaller than equivalent XML/JSON
- **Fast**: Direct [memory mapping](https://en.wikipedia.org/wiki/Memory-mapped_file) without parsing overhead
- **[Hierarchical](https://en.wikipedia.org/wiki/Hierarchical_data_model)**: Natural representation of nested game data
- **Extensible**: New fields can be added without breaking compatibility

**Common Uses:**

- Character/Creature templates (UTC, UTP, UTD, UTE, etc.)
- Area definitions (ARE, GIT, IFO)
- Dialogue trees (DLG)
- Quest journals (JRL)
- Module information (IFO)
- Save game state (SAV files contain GFF resources)
- User interface layouts (GUI)

Every `.utc`, `.uti`, `.dlg`, `.are`, and dozens of other KotOR file types are GFF files with different file type signatures and field schemas.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/gff/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/)

**Vendor References:**
- [`vendor/reone/src/libs/resource/gff.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/gff.cpp) - Complete C++ GFF reader/writer implementation
- [`vendor/reone/include/reone/resource/gff.h`](https://github.com/th3w1zard1/reone/blob/master/include/reone/resource/gff.h) - GFF type definitions and API
- [`vendor/xoreos/src/aurora/gff3file.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/gff3file.cpp) - Generic Aurora GFF3 implementation (shared format)
- [`vendor/KotOR.js/src/resource/GFFObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/GFFObject.ts) - TypeScript GFF parser with schema validation
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/GFFObject.cs`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/GFFObject.cs) - C# Unity GFF loader
- [`vendor/Kotor.NET/Kotor.NET/Formats/KotorGFF/GFF.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorGFF/GFF.cs) - .NET GFF reader/writer
- [`vendor/xoreos-tools/src/aurora/gff3file.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/aurora/gff3file.cpp) - Command-line GFF tools implementation

**See Also:**
- [TSLPatcher GFFList Syntax](TSLPatcher-GFFList-Syntax) - Modding GFF files with TSLPatcher
- [2DA File Format](2DA-File-Format) - Configuration data referenced by GFF files
- [TLK File Format](TLK-File-Format) - Text strings used by GFF LocalizedString fields
- [Bioware Aurora GFF Format](Bioware-Aurora-GFF) - Official BioWare specification

---

## Binary Format

### File Header

The file header is 56 bytes in size:

| Name                | Type    | Offset | Size | Description                                    |
| ------------------- | ------- | ------ | ---- | ---------------------------------------------- |
| File Type           | char[4] | 0      | 4    | Content type (e.g., `"GFF "`, `"ARE "`, `"UTC "`) |
| File Version        | char[4] | 4      | 4    | Format version (`"V3.2"` for KotOR)           |
| Struct Array Offset | uint32  | 8      | 4    | Offset to struct array                        |
| Struct Count        | uint32  | 12     | 4    | Number of structs                              |
| Field Array Offset  | uint32  | 16     | 4    | Offset to field array                         |
| Field Count         | uint32  | 20     | 4    | Number of fields                               |
| Label Array Offset   | uint32  | 24     | 4    | Offset to label array                         |
| Label Count          | uint32  | 28     | 4    | Number of labels                               |
| Field Data Offset    | uint32  | 32     | 4    | Offset to field data section                  |
| Field Data Count     | uint32  | 36     | 4    | Size of field data section in bytes           |
| Field Indices Offset | uint32  | 40     | 4    | Offset to field indices array                 |
| Field Indices Count  | uint32  | 44     | 4    | Number of field indices                       |
| List Indices Offset  | uint32  | 48     | 4    | Offset to list indices array                  |
| List Indices Count   | uint32  | 52     | 4    | Number of list indices                        |

**Reference**: [`vendor/reone/src/libs/resource/format/gffreader.cpp:30-44`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/gffreader.cpp#L30-L44)

### Label Array

Labels are 16-byte null-terminated strings used as field names:

| Name   | Type     | Size | Description                                                      |
| ------ | -------- | ---- | ---------------------------------------------------------------- |
| Labels | char[16] | 16×N | [Array](https://en.wikipedia.org/wiki/Array_data_structure) of field name labels ([null-padded](https://en.wikipedia.org/wiki/Null-terminated_string) to 16 bytes)            |

**Reference**: [`vendor/reone/src/libs/resource/format/gffreader.cpp:151-154`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/gffreader.cpp#L151-L154)

### Struct Array

Each struct entry is 12 bytes:

| Name       | Type   | Offset | Size | Description                                                      |
| ---------- | ------ | ------ | ---- | ---------------------------------------------------------------- |
| Struct ID  | int32  | 0      | 4    | Structure type identifier                                        |
| Data/Offset| uint32 | 4      | 4    | Field index (if 1 field) or offset to field indices (if multiple) |
| Field Count| uint32 | 8      | 4    | Number of fields in this struct (0, 1, or >1)                   |

**Reference**: [`vendor/reone/src/libs/resource/format/gffreader.cpp:40-62`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/gffreader.cpp#L40-L62)

### Field Array

Each field entry is 12 bytes:

| Name        | Type   | Offset | Size | Description                                                      |
| ----------- | ------ | ------ | ---- | ---------------------------------------------------------------- |
| Field Type  | uint32 | 0      | 4    | Data type (see [GFF Data Types](#gff-data-types))              |
| Label Index | uint32 | 4      | 4    | Index into label array for field name                           |
| Data/Offset | uint32 | 8      | 4    | Inline data (simple types) or offset to field data (complex types) |

**Reference**: [`vendor/reone/src/libs/resource/format/gffreader.cpp:67-76`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/gffreader.cpp#L67-L76)

### Field Data

Complex field types store their data in the field data section:

| Field Type        | Storage Format                                                      |
| ----------------- | ------------------------------------------------------------------- |
| UInt64            | 8 bytes (uint64)                                                    |
| Int64             | 8 bytes (int64)                                                     |
| Double            | 8 bytes (double)                                                    |
| String            | 4 bytes length + N bytes string data                                |
| ResRef            | 1 byte length + N bytes resref data (max 16 chars)                  |
| LocalizedString   | 4 bytes count + N×8 bytes (Language ID + StrRef pairs)              |
| Binary            | 4 bytes length + N bytes binary data                                 |
| Vector3           | 12 bytes (3×float)                                                   |
| Vector4           | 16 bytes (4×float)                                                   |

**Reference**: [`vendor/reone/src/libs/resource/format/gffreader.cpp:78-146`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/gffreader.cpp#L78-L146)

### Field Indices

When a struct has multiple fields, the struct's data field contains an offset into the field indices array, which lists the field indices for that struct.

### List Indices

Lists are stored as arrays of struct indices. The list field contains an offset into the list indices array, which contains the struct indices that make up the list.

---

## GFF Data Types

GFF supports the following field types:

| Type ID | Name              | Size (inline) | Description                                                      |
| ------- | ----------------- | ------------- | ---------------------------------------------------------------- |
| 0       | Byte              | 1             | 8-bit unsigned integer                                           |
| 1       | Char              | 1             | 8-bit signed integer                                              |
| 2       | Word              | 2             | 16-bit unsigned integer                                          |
| 3       | Short             | 2             | 16-bit signed integer                                             |
| 4       | DWord             | 4             | 32-bit unsigned integer                                          |
| 5       | Int               | 4             | 32-bit signed integer                                             |
| 6       | DWord64           | 8             | 64-bit unsigned integer (stored in field data)                  |
| 7       | Int64              | 8             | 64-bit signed integer (stored in field data)                      |
| 8       | Float             | 4             | 32-bit floating point                                             |
| 9       | Double            | 8             | 64-bit floating point (stored in field data)                     |
| 10      | CExoString        | varies        | Null-terminated string (stored in field data)                    |
| 11      | ResRef            | varies        | Resource reference (stored in field data, max 16 chars)          |
| 12      | CExoLocString     | varies        | Localized string (stored in field data)                           |
| 13      | Void              | varies        | Binary data blob (stored in field data)                          |
| 14      | Struct            | 4             | Nested struct (struct index stored inline)                       |
| 15      | List              | 4             | List of structs (offset to list indices stored inline)            |
| 16      | Orientation       | 16            | Quaternion (4×float, stored in field data as Vector4)            |
| 17      | Vector            | 12            | 3D vector (3×float, stored in field data)                       |
| 18      | StrRef            | 4             | String reference (TLK StrRef, stored inline as int32)             |

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py:73-108`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py#L73-L108)

**Type Selection Guidelines:**

- Use **Byte/Char** for small integers (-128 to 255) and boolean flags
- Use **Word/Short** for medium integers like IDs and counts
- Use **DWord/Int** for large values and most numeric fields
- Use **Float** for decimals that don't need high precision (positions, angles)
- Use **Double** for high-precision calculations (rare in KotOR)
- Use **CExoString** for text that doesn't need localization
- Use **CExoLocString** for player-visible text that should be translated
- Use **ResRef** for filenames without extensions (models, textures, scripts)
- Use **Void** for binary blobs like encrypted data or custom structures
- Use **Struct** for nested objects with multiple fields
- Use **List** for arrays of structs (inventory items, dialogue replies)
- Use **Vector** for 3D positions and directions
- Use **Orientation** for quaternion rotations
- Use **StrRef** for references to dialog.tlk entries

**Storage Optimization:**

Inline types (0-5, 8, 14, 15, 18) store their value directly in the field entry, saving space and improving access speed. Complex types (6-7, 9-13, 16-17) require an offset to field data, adding overhead. When designing custom GFF schemas, prefer inline types where possible.

---

## GFF Structure

### GFFStruct

A GFF struct is a collection of named fields. Each struct has:

- **Struct ID**: Type identifier (often 0xFFFFFFFF for generic structs)
- **Fields**: Dictionary mapping field names (labels) to field values

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py:400-800`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py#L400-L800)

### GFFField

Fields can be accessed using type-specific getter/setter methods:

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

A GFF list is an ordered collection of structs. Lists are accessed via:

- `get_list(label)`: Returns a `GFFList` object
- `GFFList.get(i)`: Gets struct at index `i`
- `GFFList.append(struct)`: Adds a struct to the list

**Common List Usage:**

Lists are used extensively for variable-length arrays:

- **ItemList** in UTC files: Character inventory items
- **Equip_ItemList** in UTC files: Equipped items
- **EntryList** in DLG files: Dialogue entry nodes
- **ReplyList** in DLG files: Dialogue reply options
- **SkillList** in UTC files: Character skills
- **FeatList** in UTC files: Character feats
- **EffectList** in various files: Applied effects
- **Creature_List** in GIT files: Spawned creatures in area

When modifying lists, always maintain struct IDs and parent references to avoid breaking internal links.

---

## GFF Generic Types

GFF files are used as containers for various game resource types. Each generic type has its own structure and field definitions.

### ARE (Area)

See [ARE (Area)](GFF-ARE) for detailed documentation.

### DLG (Dialogue)

See [DLG (Dialogue)](GFF-DLG) for detailed documentation.

### GIT (Game Instance Template)

See [GIT (Game Instance Template)](GFF-GIT) for detailed documentation.

### GUI

See [GUI](GFF-GUI) for detailed documentation.

### IFO (Module Info)

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

## Implementation Details

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/gff/io_gff.py:26-419`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/io_gff.py#L26-L419)

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/gff/io_gff.py:421-800`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/io_gff.py#L421-L800)

**GFF Class**: [`Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py:200-400`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py#L200-L400)

**GFFStruct Class**: [`Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py:400-800`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py#L400-L800)

---

This documentation aims to provide a comprehensive overview of the KotOR GFF file format, focusing on the detailed file structure and data formats used within the games.
