# KotOR 2DA file format Documentation

This document provides a detailed description of the 2DA (Two-Dimensional array) file format used in **Knights of the Old Republic (KotOR)** and **Knights of the Old Republic II: The Sith Lords (KotOR 2)**. 2DA files store tabular game data in a spreadsheet-like format, containing configuration data for nearly all game systems: items, Force powers, creatures, skills, feats, and many other game mechanics.

**Official Bioware Documentation:** For the authoritative Bioware Aurora Engine 2DA format specification, see [Bioware Aurora 2DA Format](Bioware-Aurora-2DA).

**For mod developers:** To modify 2DA files in your mods, see the [TSLPatcher 2DAList Syntax Guide](TSLPatcher-2DAList-Syntax). For general modding information, see [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.).

**Related formats:** 2DA files [ARE](GFF-File-Format#are-area) often referenced by [GFF files](GFF-File-Format) (such as [UTC (Creature)](GFF-File-Format#utc-creature), [UTI (Item)](GFF-File-Format#uti-item), [UTP (Placeable)](GFF-File-Format#utp-placeable) templates) and may contain references to [TLK files](TLK-File-Format) for text strings.

**Important**: While the 2DA file format structure is shared across BioWare's Aurora engine games (including Neverwinter Nights, Dragon Age, and Jade Empire), this documentation focuses exclusively on KotOR and KotOR 2. All 2DA file examples, column structures, and engine usage descriptions [ARE](GFF-File-Format#are-area) specific to these games. References to vendor implementations [ARE](GFF-File-Format#are-area) marked as either KotOR-specific or generic Aurora engine code (shared format).

## Table of Contents

- [KotOR 2DA file format Documentation](#kotor-2da-file-format-documentation)
  - Table of Contents
  - [file structure Overview](#file-structure-overview)
  - [Format](#format)
    - [File Header](#file-header)
    - [Column headers](#column-headers)
    - [Row count](#row-count)
    - [Row Labels](#row-labels)
    - [Cell data offsets](#cell-data-offsets)
    - [Cell data string Table](#cell-data-string-table)
  - [data structure](#data-structure)
    - [TwoDA Class](#twoda-class)
    - [TwoDARow Class](#twodarow-class)
  - [Cell value types](#cell-value-types)
  - [Confirmed Engine Usage](#confirmed-engine-usage)
  - [Known 2DA files](#known-2da-files)
  - [Character \& Combat 2DA files](#character--combat-2da-files)
    - [appearance.2da](#appearance2da)
    - [baseitems.2da](#baseitems2da)
    - [classes.2da](#classes2da)
    - [feat.2da](#feat2da)
    - [skills.2da](#skills2da)
    - [spells.2da](#spells2da)
  - [Items \& Properties 2DA files](#items--properties-2da-files)
    - [itemprops.2da](#itemprops2da)
    - [iprp\_feats.2da](#iprp_feats2da)
    - [iprp\_spells.2da](#iprp_spells2da)
    - [iprp\_ammocost.2da](#iprp_ammocost2da)
    - [iprp\_damagecost.2da](#iprp_damagecost2da)
  - [Objects \& Area 2DA files](#objects--area-2da-files)
    - [placeables.2da](#placeables2da)
    - [genericdoors.2da](#genericdoors2da)
    - [doortypes.2da](#doortypes2da)
    - [soundset.2da](#soundset2da)
  - [Visual Effects \& animations 2DA files](#visual-effects--animations-2da-files)
    - [visualeffects.2da](#visualeffects2da)
    - [portraits.2da](#portraits2da)
    - [heads.2da](#heads2da)
  - [Progression Tables 2DA files](#progression-tables-2da-files)
    - [classpowergain.2da](#classpowergain2da)
    - [cls\_atk\_\*.2da](#cls_atk_2da)
    - [cls\_savthr\_\*.2da](#cls_savthr_2da)
  - [Name Generation 2DA files](#name-generation-2da-files)
    - [humanfirst.2da](#humanfirst2da)
    - [humanlast.2da](#humanlast2da)
    - [Other Name Generation files](#other-name-generation-files)
  - [Additional 2DA files](#additional-2da-files)
    - [ambientmusic.2da](#ambientmusic2da)
    - [ambientsound.2da](#ambientsound2da)
    - [ammunitiontypes.2da](#ammunitiontypes2da)
    - [camerastyle.2da](#camerastyle2da)
    - [footstepsounds.2da](#footstepsounds2da)
    - [prioritygroups.2da](#prioritygroups2da)
    - [repute.2da](#repute2da)
    - [surfacemat.2da](#surfacemat2da)
    - [loadscreenhints.2da](#loadscreenhints2da)
    - [bodybag.2da](#bodybag2da)
    - [ranges.2da](#ranges2da)
    - [regeneration.2da](#regeneration2da)
    - [animations.2da](#animations2da)
    - [combatanimations.2da](#combatanimations2da)
    - [weaponsounds.2da](#weaponsounds2da)
    - [placeableobjsnds.2da](#placeableobjsnds2da)
    - [creaturespeed.2da](#creaturespeed2da)
    - [exptable.2da](#exptable2da)
    - [guisounds.2da](#guisounds2da)
    - [dialoganimations.2da](#dialoganimations2da)
    - [tilecolor.2da](#tilecolor2da)
    - [forceshields.2da](#forceshields2da)
    - [plot.2da](#plot2da)
    - [traps.2da](#traps2da)
    - [modulesave.2da](#modulesave2da)
    - [tutorial.2da](#tutorial2da)
    - [globalcat.2da](#globalcat2da)
    - [subrace.2da](#subrace2da)
    - [gender.2da](#gender2da)
    - [racialtypes.2da](#racialtypes2da)
    - [upgrade.2da](#upgrade2da)
    - [encdifficulty.2da](#encdifficulty2da)
    - [itempropdef.2da](#itempropdef2da)
    - [emotion.2da](#emotion2da)
    - [facialanim.2da](#facialanim2da)
    - [videoeffects.2da](#videoeffects2da)
    - [planetary.2da](#planetary2da)
    - [cursors.2da](#cursors2da)
  - [Item Property Parameter \& Cost Tables 2DA files](#item-property-parameter--cost-tables-2da-files)
    - [iprp\_paramtable.2da](#iprp_paramtable2da)
    - [iprp\_costtable.2da](#iprp_costtable2da)
    - [iprp\_abilities.2da](#iprp_abilities2da)
    - [iprp\_aligngrp.2da](#iprp_aligngrp2da)
    - [iprp\_combatdam.2da](#iprp_combatdam2da)
    - [iprp\_damagetype.2da](#iprp_damagetype2da)
    - [iprp\_protection.2da](#iprp_protection2da)
    - [iprp\_acmodtype.2da](#iprp_acmodtype2da)
    - [iprp\_immunity.2da](#iprp_immunity2da)
    - [iprp\_saveelement.2da](#iprp_saveelement2da)
    - [iprp\_savingthrow.2da](#iprp_savingthrow2da)
    - [iprp\_onhit.2da](#iprp_onhit2da)
    - [iprp\_ammotype.2da](#iprp_ammotype2da)
    - [iprp\_mosterhit.2da](#iprp_mosterhit2da)
    - [iprp\_walk.2da](#iprp_walk2da)
    - [ai\_styles.2da](#ai_styles2da)
    - [iprp\_damagevs.2da](#iprp_damagevs2da)
    - [iprp\_attackmod.2da](#iprp_attackmod2da)
    - [iprp\_bonusfeat.2da](#iprp_bonusfeat2da)
    - [iprp\_lightcol.2da](#iprp_lightcol2da)
    - [iprp\_monstdam.2da](#iprp_monstdam2da)
    - [iprp\_skillcost.2da](#iprp_skillcost2da)
    - [iprp\_weightinc.2da](#iprp_weightinc2da)
    - [iprp\_traptype.2da](#iprp_traptype2da)
    - [iprp\_damagered.2da](#iprp_damagered2da)
    - [iprp\_spellres.2da](#iprp_spellres2da)
    - [rumble.2da](#rumble2da)
    - [musictable.2da](#musictable2da)
    - [difficultyopt.2da](#difficultyopt2da)
    - [xptable.2da](#xptable2da)
    - [featgain.2da](#featgain2da)
    - [effecticon.2da](#effecticon2da)
    - [itempropsdef.2da](#itempropsdef2da)
    - [pazaakdecks.2da](#pazaakdecks2da)
    - [acbonus.2da](#acbonus2da)
    - [keymap.2da](#keymap2da)
    - [soundeax.2da](#soundeax2da)
    - [poison.2da](#poison2da)
    - [feedbacktext.2da](#feedbacktext2da)
    - [creaturesize.2da](#creaturesize2da)
    - [appearancesndset.2da](#appearancesndset2da)
    - [texpacks.2da](#texpacks2da)
    - [videoquality.2da](#videoquality2da)
    - [loadscreens.2da](#loadscreens2da)
    - [phenotype.2da](#phenotype2da)
    - [palette.2da](#palette2da)
    - [bodyvariation.2da](#bodyvariation2da)
    - [textures.2da](#textures2da)
    - [merchants.2da](#merchants2da)
    - [actions.2da](#actions2da)
    - [aiscripts.2da](#aiscripts2da)
    - [bindablekeys.2da](#bindablekeys2da)
    - [crtemplates.2da](#crtemplates2da)
    - [environment.2da](#environment2da)
    - [fractionalcr.2da](#fractionalcr2da)
    - [gamespyrooms.2da](#gamespyrooms2da)
    - [hen\_companion.2da](#hen_companion2da)
    - [hen\_familiar.2da](#hen_familiar2da)
    - [masterfeats.2da](#masterfeats2da)
    - [movies.2da](#movies2da)
    - [stringtokens.2da](#stringtokens2da)
    - [tutorial\_old.2da](#tutorial_old2da)
    - [credits.2da](#credits2da)
    - [disease.2da](#disease2da)
    - [droiddischarge.2da](#droiddischarge2da)
    - [minglobalrim.2da](#minglobalrim2da)
    - [upcrystals.2da](#upcrystals2da)
    - [chargenclothes.2da](#chargenclothes2da)
    - [aliensound.2da](#aliensound2da)
    - [alienvo.2da](#alienvo2da)
    - [grenadesnd.2da](#grenadesnd2da)
    - [inventorysnds.2da](#inventorysnds2da)
    - [areaeffects.2da](#areaeffects2da)
  - [Implementation Details](#implementation-details)
    - [PyKotor Implementation](#pykotor-implementation)
    - [Vendor Implementations](#vendor-implementations)

---

## file structure Overview

2DA files store tabular game data in a compact format used by the KotOR game engine. files use version "V2.b" and have the `.2da` extension.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/twoda/`](https://github.com/OldRepublicDevs/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/twoda/)

**Vendor References:**

- [`vendor/kotor/docs/2da.md`](https://github.com/th3w1zard1/kotor/blob/master/docs/2da.md) - Basic format structure and parsing overview
- [`vendor/reone/src/libs/resource/format/2dareader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/2dareader.cpp) - Complete C++ 2DA parser implementation
- [`vendor/xoreos/src/aurora/2dafile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/2dafile.cpp) - Generic Aurora engine 2DA implementation (shared format)
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/2DAObject.cs`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/2DAObject.cs) - C# Unity 2DA loader
- [`vendor/KotOR.js/src/resource/TwoDAObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/TwoDAObject.ts) - TypeScript 2DA parser with memory-efficient caching
- [`vendor/Kotor.NET/Kotor.NET/Formats/Kotor2DA/Kotor2DA.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/Kotor2DA/Kotor2DA.cs) - .NET 2DA reader/writer

**See Also:**

- [TSLPatcher 2DAList Syntax](TSLPatcher-2DAList-Syntax) - Modding 2DA files with TSLPatcher
- [GFF File Format](GFF-File-Format) - Related format that often references 2DA data
- [TLK File Format](TLK-File-Format) - Text strings referenced by 2DA entries

---

## format

The 2DA file format (version "V2.b") is the representation used by the game engine.

### File header

The file header is 9 bytes in size:

| Name         | type    | offset | size | Description                                    |
| ------------ | ------- | ------ | ---- | ---------------------------------------------- |
| file type    | [char](GFF-File-Format#gff-data-types) | 0 (0x00) | 4    | Always `"2DA "` (space-padded) or `"2DA\t"` (tab-padded) |
| file Version | [char](GFF-File-Format#gff-data-types) | 4 (0x04) | 4    | Always `"V2.b"`              |
| Line Break   | [uint8](GFF-File-Format#gff-data-types)   | 8 (0x08) | 1    | Newline character (`\n`, value `0x0A`)        |

The file type can be either `"2DA "` (space-padded) or `"2DA\t"` (tab-padded). Both [ARE](GFF-File-Format#are-area) valid and accepted by the game engine.

**References**:

- [`vendor/reone/src/libs/resource/format/2dareader.cpp:29-32`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/2dareader.cpp#L29-L32) - KotOR-specific header validation
- [`vendor/xoreos/src/aurora/2dafile.cpp:48-51`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/2dafile.cpp#L48-L51) - Generic Aurora engine header constants (format shared across KotOR and other Aurora games)
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/2DAObject.cs:25-32`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/2DAObject.cs#L25-L32) - KotOR-specific header reading

### Column headers

Column headers immediately follow the header, terminated by a [null byte](https://en.cppreference.com/w/c/string/byte):

| Name            | type    | Description                                                      |
| --------------- | ------- | ---------------------------------------------------------------- |
| Column headers  | [char](GFF-File-Format#gff-data-types)[]  | [Tab-separated](https://en.wikipedia.org/wiki/Tab-separated_values) column names (e.g., `"label\tname\tdescription"`) |
| [null terminator](https://en.cppreference.com/w/c/string/byte) | [uint8](GFF-File-Format#gff-data-types)   | Single [null byte](https://en.cppreference.com/w/c/string/byte) (`\0`) marking end of headers                   |

Each column name is terminated by a tab character (`0x09`). The entire header list is terminated by a [null byte](https://en.cppreference.com/w/c/string/byte) (`0x00`). Column names [ARE](GFF-File-Format#are-area) case-sensitive and typically lowercase in KotOR files.

**References**:

- [`vendor/reone/src/libs/resource/format/2dareader.cpp:72-89`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/2dareader.cpp#L72-L89) - KotOR-specific token reading with tab separator
- [`vendor/xoreos/src/aurora/2dafile.cpp:260-275`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/2dafile.cpp#L260-L275) - Generic Aurora engine header reading (format shared across KotOR and other Aurora games)
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/2DAObject.cs:36-48`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/2DAObject.cs#L36-L48) - KotOR-specific column header parsing
- [`vendor/kotor/docs/2da.md:32-37`](https://github.com/th3w1zard1/kotor/blob/master/docs/2da.md#L32-L37) - KotOR-specific column structure

### Row count

| Name      | type    | offset | size | Description                    |
| --------- | ------- | ------ | ---- | ------------------------------ |
| Row count | [uint32](GFF-File-Format#gff-data-types)  | varies | 4    | Number of data rows in the file ([little-endian](https://en.wikipedia.org/wiki/Endianness)) |

The row count is stored as a 32-bit unsigned integer in [little-endian](https://en.wikipedia.org/wiki/Endianness) [byte](GFF-File-Format#gff-data-types) order. This value determines how many row labels and data rows follow.

**References**:

- [`vendor/reone/src/libs/resource/format/2dareader.cpp:34`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/2dareader.cpp#L34) - KotOR-specific row count reading
- [`vendor/xoreos/src/aurora/2dafile.cpp:284`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/2dafile.cpp#L284) - Generic Aurora engine row count reading (format shared across KotOR and other Aurora games)
- [`vendor/kotor/docs/2da.md:39-44`](https://github.com/th3w1zard1/kotor/blob/master/docs/2da.md#L39-L44) - KotOR-specific row indices structure

### Row Labels

Row labels immediately follow the row count:

| Name       | type    | Description                                                      |
| ---------- | ------- | ---------------------------------------------------------------- |
| Row Labels | [char](GFF-File-Format#gff-data-types)[]  | [Tab-separated](https://en.wikipedia.org/wiki/Tab-separated_values) row labels (one per row, typically numeric)       |

Each row label is read as a [tab-terminated](2DA-File-Format#column-headers) string (tab character `0x09`). Row labels [ARE](GFF-File-Format#are-area) usually numeric ("0", "1", "2"...) but can be arbitrary strings.

**Important**: The row label list is **not** terminated by a [null byte](https://en.cppreference.com/w/c/string/byte) (`0x00`). The reader must consume exactly `row_count` labels based on the count field. This differs from the column headers which do have a [null terminator](https://en.cppreference.com/w/c/string/byte). The row labels [ARE](GFF-File-Format#are-area) primarily for human readability and editing tools - the actual row indexing in the game engine is based on position, not label value.

**References**:

- [`vendor/reone/src/libs/resource/format/2dareader.cpp:35`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/2dareader.cpp#L35) - KotOR-specific row label reading (skipped in reone)
- [`vendor/xoreos/src/aurora/2dafile.cpp:277-294`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/2dafile.cpp#L277-L294) - Generic Aurora engine row label skipping implementation (format shared across KotOR and other Aurora games)
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/2DAObject.cs:56-70`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/2DAObject.cs#L56-L70) - KotOR-specific row label parsing
- [`vendor/kotor/docs/2da.md:39-46`](https://github.com/th3w1zard1/kotor/blob/master/docs/2da.md#L39-L46) - KotOR-specific row indices structure and termination note

### Cell data offsets

After row labels, cell data offsets [ARE](GFF-File-Format#are-area) stored:

| Name            | type     | size | Description                                                      |
| --------------- | -------- | ---- | ---------------------------------------------------------------- |
| Cell offsets    | [uint16](GFF-File-Format#gff-data-types)[] | 2×N  | [Array](https://en.wikipedia.org/wiki/Array_data_structure) of offsets into cell data string table (N = [row_count](2DA-File-Format#row-labels) × [column_count](2DA-File-Format#column-headers), [little-endian](https://en.wikipedia.org/wiki/Endianness)) |
| Cell data size  | [uint16](GFF-File-Format#gff-data-types)   | 2    | Total size of cell data string table in bytes ([little-endian](https://en.wikipedia.org/wiki/Endianness))   |

Each cell has a 16-bit unsigned integer offset ([little-endian](https://en.wikipedia.org/wiki/Endianness)) pointing to its string value in the cell data string table. Offsets [ARE](GFF-File-Format#are-area) stored in [row-major order](https://en.wikipedia.org/wiki/Row-_and_column-major_order) (all cells of row 0, then all cells of row 1, etc.). The cell data size field immediately follows the offset array and precedes the actual cell data.

**Important**: The offsets [ARE](GFF-File-Format#are-area) relative to the start of the cell data string table (which begins immediately after the `cell_data_size` field). Multiple cells can share the same offset value if they contain identical strings, enabling data [deduplication](https://en.wikipedia.org/wiki/Data_deduplication).

**References**:

- [`vendor/reone/src/libs/resource/format/2dareader.cpp:47-52`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/2dareader.cpp#L47-L52) - KotOR-specific offset array reading
- [`vendor/xoreos/src/aurora/2dafile.cpp:314-317`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/2dafile.cpp#L314-L317) - Generic Aurora engine offset reading (format shared across KotOR and other Aurora games)
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/2DAObject.cs:72-83`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/2DAObject.cs#L72-L83) - KotOR-specific offset array parsing
- [`vendor/reone/src/libs/resource/format/2dawriter.cpp:63-89`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/2dawriter.cpp#L63-L89) - KotOR-specific offset [deduplication](https://en.wikipedia.org/wiki/Data_deduplication) during writing
- [`vendor/kotor/docs/2da.md:48-54`](https://github.com/th3w1zard1/kotor/blob/master/docs/2da.md#L48-L54) - KotOR-specific cell offsets structure

### Cell data string Table

The cell data string table contains all cell values as [null-terminated](https://en.cppreference.com/w/c/string/byte) strings:

| Name         | type   | Description                                                      |
| ------------ | ------ | ---------------------------------------------------------------- |
| Cell strings | [char](GFF-File-Format#gff-data-types)[] | [Null-terminated](https://en.cppreference.com/w/c/string/byte) strings, [deduplicated](https://en.wikipedia.org/wiki/Data_deduplication) (same value shares offset) |

The cell data string table begins immediately after the `cell_data_size` field. Each string is [null-terminated](https://en.cppreference.com/w/c/string/byte) (`0x00`). Blank or empty cells [ARE](GFF-File-Format#are-area) typically stored as empty strings (immediately [null-terminated](https://en.cppreference.com/w/c/string/byte)) or the string `"****"`. The string table is [deduplicated](https://en.wikipedia.org/wiki/Data_deduplication) - multiple cells with the same value share the same offset, reducing file size.

**Reading Process**: For each cell, the reader:

1. Retrieves the 16-bit offset from the offset array (indexed by `row_index × column_count + column_index`)
2. Seeks to `cell_data_start_position + offset`
3. Reads a [null-terminated](https://en.cppreference.com/w/c/string/byte) string from that position

**References**:

- [`vendor/reone/src/libs/resource/format/2dareader.cpp:54-65`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/2dareader.cpp#L54-L65) - KotOR-specific cell data reading with offset calculation
- [`vendor/xoreos/src/aurora/2dafile.cpp:319-335`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/2dafile.cpp#L319-L335) - Generic Aurora engine cell data reading (format shared across KotOR and other Aurora games, with KotOR-specific comment at line 545)
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/2DAObject.cs:85-100`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/2DAObject.cs#L85-L100) - KotOR-specific cell data reading loop
- [`vendor/xoreos/src/aurora/2dafile.cpp:63-64`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/2dafile.cpp#L63-L64) - Generic Aurora engine empty cell representation (`"****"`, shared across KotOR and other Aurora games)
- [`vendor/kotor/docs/2da.md:57-64`](https://github.com/th3w1zard1/kotor/blob/master/docs/2da.md#L57-L64) - KotOR-specific cell data structure

---

## data structure

### TwoDA Class

The `TwoDA` class represents a complete 2DA file in memory:

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/twoda/twoda_data.py:77-119`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/twoda/twoda_data.py#L77-L119)

**Attributes:**

- `_rows`: List of dictionaries, each mapping column headers to cell values
- `_headers`: List of column header names (case-sensitive, typically lowercase)
- `_labels`: List of row labels (usually numeric strings like "0", "1", "2"...)

**Methods:**

- `get_cell(row_index, column_header)`: Get cell value by row index and column header
- `set_cell(row_index, column_header, value)`: Set cell value
- `get_column(header)`: Get all values for a column
- `add_row(label)`: Add a new row
- `add_column(header)`: Add a new column

### TwoDARow Class

The `TwoDARow` class provides a convenient interface for accessing row data:

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/twoda/twoda_data.py:850-950`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/twoda/twoda_data.py#L850-L950)

**Attributes:**

- `label`: Row label string
- `cells`: Dictionary mapping column headers to cell values

---

## Cell value types

All cell values [ARE](GFF-File-Format#are-area) stored as strings in the 2DA file, but [ARE](GFF-File-Format#are-area) interpreted as different types by the game engine:

- **Integers**: Numeric strings parsed as [`int32`](https://en.wikipedia.org/wiki/Integer_(computer_science)) - used for numeric identifiers, counts, and enumerated values
- **Floats**: Decimal strings parsed as [`float`](https://en.wikipedia.org/wiki/Single-precision_floating-point_format) - used for calculations like damage multipliers, timers, and percentages
- **ResRefs**: [Resource references](GFF-File-Format#gff-data-types) (max 16 characters, no extension) - point to other game resources like [models](MDL-MDX-File-Format), [textures](TPC-File-Format), or scripts
- **StrRefs**: [String references](TLK-File-Format#string-references-strref) into [`dialog.tlk`](TLK-File-Format) (typically negative values like `-1` indicate no reference) - used for localized text display
- **Boolean**: `"0"` or `"1"` (sometimes `"TRUE"`/`"FALSE"`) - control feature [flags](GFF-File-Format#gff-data-types) and settings
- **Empty Cells**: Represented as `"****"` - treated as null/undefined by the engine

The game engine parses cell values based on context and expected data type for each column. For example, the `appearance.2da` file uses integers for [model](MDL-MDX-File-Format) indices, [ResRefs](GFF-File-Format#gff-data-types) for [texture](TPC-File-Format) names, and [StrRefs](TLK-File-Format#string-references-strref) for race names.

---

## Confirmed Engine Usage

The following 2DA files have been confirmed to be actively loaded and used by the KotOR game engine through comprehensive reverse engineering analysis of `swkotor.exe` and `swkotor2.exe` using Ghidra (via Reva MCP server). This analysis examined the actual game executables to identify all 2DA files loaded via `Load2DArrays()`, `CResRef__CResRef()` calls, and related loading functions.

### Analysis Methodology

The game engine analysis was performed by:

1. Decompiling `swkotor.exe` (KotOR 1) and `swkotor2.exe` (KotOR 2/TSL) using Ghidra
2. Identifying all `Load2DArrays_*()` functions and their `CResRef()` calls
3. Tracing `C2DA::Load2DArray()` calls throughout the codebase
4. Verifying string references to 2DA file names in the executable binaries
5. Cross-referencing findings with vendor source code (`vendor/swkotor.c`, `vendor/swkotor.h`)

### KotOR 1 (swkotor.exe) - Confirmed 2DA Files

**Core Game Systems:**

- `classes.2da` - LoadClassInfo() → CResRef("Classes")
- `feat.2da` - LoadFeatInfo() → CResRef("Feat")
- `featgain.2da` - CSWClass::LoadFeatGain() → CResRef("featgain")
- `skills.2da` - LoadSkillInfo() → CResRef("Skills")
- `spells.2da` - Load2DArrays_Spells() → CResRef("Spells")
- `exptable.2da` - CSWRules::CSWRules() → CResRef("EXPTABLE")
- `xptable.2da` - Load2DArrays_XpBase() → CResRef("XPTable")

**Character & Appearance:**

- `appearance.2da` - Load2DArrays_Appearance() → CResRef("Appearance")
- `racialtypes.2da` - LoadRaceInfo() → CResRef("RacialTypes")
- `gender.2da` - Load2DArrays_Gender() → CResRef("GENDER")
- `portraits.2da` - Load2DArrays_Portrait() → CResRef("Portraits")
- `heads.2da` - Load2DArrays_Heads() → CResRef("Heads")
- `creaturespeed.2da` - Load2DArrays_CreatureSpeed() → CResRef("CreatureSpeed")
- `ranges.2da` - CSWRules::CSWRules() → CResRef("Ranges")

**Items & Equipment:**

- `baseitems.2da` - CSWBaseItemArray::Load() → CResRef("BASEITEMS")
- `itempropdef.2da` - Load2DArrays_ItemPropDef() → CResRef("ItemPropDef")
- `itemprops.2da` - HandleServerToPlayerDebugInfo_Item() → CResRef("ITEMPROPS")
- `upgrade.2da` - CSWGuiUpgrade() → CResRef("upgrade")

**Objects & Areas:**

- `placeables.2da` - Load2DArrays_Placeables() → CResRef("Placeables")
- `genericdoors.2da` - Load2DArrays_GenericDoors() → CResRef("GenericDoors")
- `doortypes.2da` - Load2DArrays_DoorTypes() → CResRef("DoorTypes")
- `traps.2da` - Load2DArrays_Traps() → CResRef("Traps")
- `encdifficulty.2da` - Load2DArrays_EncDifficulty() → CResRef("EncDifficulty")
- `loadscreens.2da` - Load2DArrays_AreaTransition() → CResRef("Loadscreens")
- `modulesave.2da` - StartNewModule() → CResRef("modulesave")

**Audio & Visual:**

- `ambientmusic.2da` - Load2DArrays_AmbientMusic() → CResRef("AmbientMusic")
- `ambientsound.2da` - Load2DArrays_AmbientSound() → CResRef("AmbientSound")
- `footstepsounds.2da` - Load2DArrays_FootstepSounds() → CResRef("FootstepSounds")
- `appearancesndset.2da` - Load2DArrays_AppearanceSounds() → CResRef("AppearanceSounds")
- `weaponsounds.2da` - Load2DArrays_WeaponSounds() → CResRef("WeaponSounds")
- `placeablesounds.2da` - Load2DArrays_PlaceableSounds() → CResRef("PlaceableSounds")
- `camerastyle.2da` - Load2DArrays_CameraStyle() → CResRef("CameraStyle")
- `surfacemat.2da` - Load2DArrays_SurfaceMaterial() → CResRef("SurfaceMaterial")
- `visualeffects.2da` - Load2DArrays_VisualEffect() → CResRef("VisualEffect")
- `videoeffects.2da` - Load2DArrays_VideoEffects() → CResRef("VideoEffects")
- `dialoganimations.2da` - Load2DArrays_DialogAnimations() → CResRef("DialogAnimations")
- `cursors.2da` - Load2DArrays_Cursor() → CResRef("cursors")

**Item Properties (IPRP):**

- `iprp_abilities.2da` - Load2DArrays_IPRPAbilities() → CResRef("IPRP_ABILITIES")
- `iprp_acmodtype.2da` - LoadIPRPCostTables() → CResRef("IPRP_ACMODTYPE")
- `iprp_aligngrp.2da` - LoadIPRPCostTables() → CResRef("IPRP_ALIGNGRP")
- `iprp_ammotype.2da` - LoadIPRPCostTables() → CResRef("IPRP_AMMOTYPE")
- `iprp_combatdam.2da` - LoadIPRPCostTables() → CResRef("IPRP_COMBATDAM")
- `iprp_costtable.2da` - LoadIPRPCostTables() → CResRef("IPRP_COSTTABLE")
- `iprp_damagecost.2da` - Load2DArrays_IPRPDamage() → CResRef("IPRP_DAMAGECOST")
- `iprp_damagetype.2da` - LoadIPRPCostTables() → CResRef("IPRP_DAMAGETYPE")
- `iprp_immunity.2da` - LoadIPRPCostTables() → CResRef("IPRP_IMMUNITY")
- `iprp_lightcol.2da` - Load2DArrays_LightColor() → CResRef("LightColor")
- `iprp_meleecost.2da` - Load2DArrays_IPRPMelee() → CResRef("IPRP_MeleeCost")
- `iprp_mosterhit.2da` - LoadIPRPCostTables() → CResRef("IPRP_MONSTERHIT")
- `iprp_onhit.2da` - Load2DArrays_OnHit() → CResRef("IPRP_ONHIT")
- `iprp_paramtable.2da` - LoadIPRPParamTables() → CResRef("IPRP_PARAMTABLE")
- `iprp_protection.2da` - LoadIPRPCostTables() → CResRef("IPRP_PROTECTION")
- `iprp_saveelement.2da` - LoadIPRPCostTables() → CResRef("IPRP_SAVEELEMENT")
- `iprp_savingthrow.2da` - LoadIPRPCostTables() → CResRef("IPRP_SAVINGTHROW")
- `iprp_walk.2da` - LoadIPRPCostTables() → CResRef("IPRP_WALK")

**Factions & Reputation:**

- `repute.2da` - Load2DArrays_Repute() → CResRef("Repute")

**Game Systems:**

- `plot.2da` - Load2DArrays_PlotXP() → CResRef("Plot")
- `planetary.2da` - Load2DArrays_Planetary() → CResRef("Planetary")
- `loadscreenhints.2da` - CClientExoAppInternal::GetNextLoadScreenHintSTRREF() → CResRef("loadscreenhints")
- `movies.2da` - Load2DArrays_Movies() → CResRef("Movies")
- `globalcat.2da` - CSWGlobalVariableTable::ReadCatalogue() → CResRef("globalcat")
- `tutorial.2da` - Load2DArrays_Tutorial() → CResRef("Tutorial")
- `difficultyopt.2da` - Load2DArrays_DifficultyOptions() → CResRef("DifficultyOptions")
- `gamma.2da` - Load2DArrays_Gamma() → CResRef("Gamma")
- `statescripts.2da` - Load2DArrays_StateScripts() → CResRef("StateScripts")
- `poison.2da` - Load2DArrays_Poison() → CResRef("Poison")
- `disease.2da` - Load2DArrays_Disease() → CResRef("Disease")
- `repaadjustments.2da` - Load2DArrays_RepAdjustments() → CResRef("RepAdjustments")
- `fractionalcr.2da` - Load2DArrays_FractionalCR() → CResRef("FractionalCR")
- `regeneration.2da` - Load2DArrays_Regeneration() → CResRef("Regeneration")
- `ammunitiontypes.2da` - Load2DArrays_AmmunitionTypes() → CResRef("AmmunitionTypes")
- `keymap.2da` - Load2DArrays_Keymap() → CResRef("Keymap")
- `bindablekeys.2da` - Load2DArrays_BindableKey() → CResRef("BindableKey")

### KotOR 2/TSL (swkotor2.exe) - Additional 2DA Files

The following 2DA files are loaded in KotOR 2 but not in KotOR 1:

- `emotion.2da` - FUN_00612fb0() → CResRef("Emotion")
- `facialanim.2da` - FUN_005e6ac0() → CResRef("FacialAnim")
- `subrace.2da` - FUN_00612ab0() → CResRef("Subrace")
- `soundset.2da` - FUN_006ce0c0() → CResRef("SoundSet")
- `pazaakdecks.2da` - FUN_00754f60() → CResRef("PazaakDecks")
- `upcrystals.2da` - FUN_00730970() → CResRef("upcrystals")
- `iprp_monstcost.2da` - FUN_00611120() → CResRef("IPRP_MONSTCOST")
- `iprp_bonuscost.2da` - FUN_006111c0() → CResRef("IPRP_BONUSCOST")
- `iprp_srcost.2da` - FUN_00611260() → CResRef("IPRP_SRCOST")
- `iprp_neg5cost.2da` - FUN_00611300() → CResRef("IPRP_NEG5COST")
- `iprp_onhitdur.2da` - FUN_006114e0() → CResRef("IPRP_ONHITDUR")
- `iprp_pc.2da` - FUN_00612b50() → CResRef("IPRP_PC")

**Note:** All files listed above have been verified through decompilation analysis of the game executables. Function names in `swkotor2.exe` are obfuscated (shown as `FUN_*` addresses), but the 2DA file loading calls have been confirmed. Files documented below that are not listed here may be remnants from Neverwinter Nights (NWN), unused by the game engine, or used in ways not yet identified.

## Known 2DA files

This section documents all known 2DA files used in KotOR and KotOR 2, organized by category. Each entry includes engine usage, column definitions, and data structure details.

---

## Character & Combat 2DA files

### appearance.2da

**Engine Usage**: The `appearance.2da` file is one of the most critical [2DA files](2DA-File-Format) in KotOR. It maps appearance IDs (used in [creature templates](GFF-File-Format#utc-creature) and character creation) to 3D [model](MDL-MDX-File-Format) ResRefs, [texture](TPC-File-Format) assignments, race associations, and physical properties. The engine uses this file when loading creatures, determining which [model](MDL-MDX-File-Format) and [textures](TPC-File-Format) to display, calculating hit detection, and managing character [animations](MDL-MDX-File-Format#animation-header).

**Row index**: Appearance ID (integer, typically 0-based)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | String (optional) | Human-readable label for the appearance |
| `modeltype` | string | [model](MDL-MDX-File-Format) type identifier (e.g., "F", "B", "P") |
| `modela` through `modeln` | ResRef (optional) | [model](MDL-MDX-File-Format) ResRefs for different body parts or variations ([models](MDL-MDX-File-Format) a-n) |
| `texa` through `texn` | ResRef (optional) | [texture](TPC-File-Format) ResRefs for different body parts ([textures](TPC-File-Format) a-n) |
| `texaevil`, `texbevil`, `texievil`, `texlevil`, `texnevil` | ResRef (optional) | Dark side variant [textures](TPC-File-Format) |
| `race` | ResRef (optional) | Race identifier [ResRef](GFF-File-Format#gff-data-types) |
| `racetex` | ResRef (optional) | Race-specific [texture](TPC-File-Format) [ResRef](GFF-File-Format#gff-data-types) |
| `racialtype` | Integer | Numeric racial type identifier |
| `normalhead` | Integer (optional) | Default head appearance ID |
| `backuphead` | Integer (optional) | Fallback head appearance ID |
| `portrait` | ResRef (optional) | Portrait image [ResRef](GFF-File-Format#gff-data-types) |
| `skin` | ResRef (optional) | Skin [texture](TPC-File-Format) [ResRef](GFF-File-Format#gff-data-types) |
| `headtexe`, `headtexg`, `headtexve`, `headtexvg` | ResRef (optional) | Head [texture](TPC-File-Format) variations |
| `headbone` | String (optional) | Bone name for head attachment |
| `height` | [Float](https://en.wikipedia.org/wiki/Single-precision_floating-point_format) | Character height multiplier |
| `hitdist` | [Float](https://en.wikipedia.org/wiki/Single-precision_floating-point_format) | Hit detection distance |
| `hitradius` | [Float](https://en.wikipedia.org/wiki/Single-precision_floating-point_format) | Hit detection radius |
| `sizecategory` | Integer | size category (affects combat calculations) |
| `moverate` | string | Movement rate identifier |
| `walkdist` | Float | Walking distance threshold |
| `rundist` | Float | Running distance threshold |
| `prefatckdist` | Float | Preferred attack distance |
| `creperspace` | Float | Creature personal space radius |
| `perspace` | Float | Personal space radius |
| `cameraspace` | Float (optional) | Camera space offset |
| `cameraheightoffset` | String (optional) | Camera height offset |
| `targetheight` | string | Target height for combat |
| `perceptiondist` | Integer | Perception distance |
| `headArcH` | Integer | Head horizontal arc angle |
| `headArcV` | Integer | Head vertical arc angle |
| `headtrack` | Boolean | Whether head tracking is enabled |
| `hasarms` | Boolean | Whether creature has arms |
| `haslegs` | Boolean | Whether creature has legs |
| `groundtilt` | Boolean | Whether ground tilt is enabled |
| `footsteptype` | Integer (optional) | Footstep sound type |
| `footstepsound` | ResRef (optional) | Footstep sound [ResRef](GFF-File-Format#gff-data-types) |
| `footstepvolume` | Boolean | Whether footstep volume is enabled |
| `armorSound` | ResRef (optional) | Armor sound effect [ResRef](GFF-File-Format#gff-data-types) |
| `combatSound` | ResRef (optional) | Combat sound effect [ResRef](GFF-File-Format#gff-data-types) |
| `soundapptype` | Integer (optional) | Sound appearance type |
| `bloodcolr` | string | Blood color identifier |
| `deathvfx` | Integer (optional) | Death visual effect ID |
| `deathvfxnode` | String (optional) | Death VFX attachment [node](MDL-MDX-File-Format#node-structures) |
| `fadedelayondeath` | Boolean (optional) | Whether to fade on death |
| `destroyobjectdelay` | Boolean (optional) | Whether to delay object destruction |
| `disableinjuredanim` | Boolean (optional) | Whether to disable injured [animations](MDL-MDX-File-Format#animation-header) |
| `abortonparry` | Boolean | Whether to abort on parry |
| `freelookeffect` | Integer (optional) | Free look effect ID |
| `equipslotslocked` | Integer (optional) | Locked equipment slot [flags](GFF-File-Format#gff-data-types) |
| `weaponscale` | String (optional) | Weapon scale multiplier |
| `wingTailScale` | Boolean | Whether wing/tail scaling is enabled |
| `helmetScaleF` | String (optional) | Female helmet scale |
| `helmetScaleM` | String (optional) | Male helmet scale |
| `envmap` | ResRef (optional) | Environment map [texture](TPC-File-Format) [ResRef](GFF-File-Format#gff-data-types) |
| `bodyBag` | Integer (optional) | Body bag appearance ID |
| `stringRef` | Integer (optional) | string reference for appearance name |
| `driveaccl` | Integer | Vehicle drive acceleration |
| `drivemaxspeed` | Float | Vehicle maximum speed |
| `driveanimwalk` | Float | Vehicle walk [animation](MDL-MDX-File-Format#animation-header) speed |
| `driveanimrunPc` | Float | PC vehicle run [animation](MDL-MDX-File-Format#animation-header) speed |
| `driveanimrunXbox` | Float | Xbox vehicle run [animation](MDL-MDX-File-Format#animation-header) speed |

**Column Details**:

The `appearance.2da` file contains a comprehensive set of columns for character appearance configuration. The complete column list is parsed by reone's appearance parser:

- [model](MDL-MDX-File-Format) columns: `modela` through `modeln` (14 [model](MDL-MDX-File-Format) variations)
- [texture](TPC-File-Format) columns: `texa` through `texn` (14 [texture](TPC-File-Format) variations)
- Evil [texture](TPC-File-Format) columns: `texaevil`, `texbevil`, `texievil`, `texlevil`, `texnevil`
- Head [texture](TPC-File-Format) columns: `headtexe`, `headtexg`, `headtexve`, `headtexvg`
- Movement: `walkdist`, `rundist`, `prefatckdist`, `moverate`
- Physical properties: `height`, `hitdist`, `hitradius`, `sizecategory`, `perceptiondist`
- Personal space: `perspace`, `creperspace`
- Camera: `cameraspace`, `cameraheightoffset`, `targetheight`
- Head tracking: `headArcH`, `headArcV`, `headtrack`
- Body parts: `hasarms`, `haslegs`, `groundtilt`, `wingTailScale`
- Footsteps: `footsteptype`, `footstepsound`, `footstepvolume`
- Sounds: `armorSound`, `combatSound`, `soundapptype`
- Visual effects: `deathvfx`, `deathvfxnode`, `fadedelayondeath`, `freelookeffect`
- Equipment: `equipslotslocked`, `weaponscale`, `helmetScaleF`, `helmetScaleM`
- [textures](TPC-File-Format): `envmap`, `skin`, `portrait`, `race`, `racetex`, `racialtype`
- Heads: `normalhead`, `backuphead`, `headbone`
- Vehicle: `driveaccl`, `drivemaxspeed`, `driveanimwalk`, `driveanimrunPc`, `driveanimrunXbox`
- Other: `bloodcolr`, `bodyBag`, `stringRef`, `abortonparry`, `destroyobjectdelay`, `disableinjuredanim`

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:73`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L73) - [StrRef](TLK-File-Format#string-references-strref) column definition for appearance.2da (K1: string_ref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:248`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L248) - [StrRef](TLK-File-Format#string-references-strref) column definition for appearance.2da (K2: string_ref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:155`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L155) - [ResRef](GFF-File-Format#gff-data-types) column definition for appearance.2da (race)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:168`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L168) - [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definitions for appearance.2da (modela through modelj)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:213-214`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L213-L214) - [texture](TPC-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definitions for appearance.2da (racetex, texa through texj, headtexve, headtexe, headtexvg, headtexg)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:456`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L456) - TwoDARegistry.APPEARANCES constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:524`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L524) - [GFF](GFF-File-Format) field mapping: "Appearance_Type" -> appearance.2da

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:55`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L55) - HTInstallation.TwoDA_APPEARANCES constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utc.py`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utc.py) - Appearance selection combobox in [UTC](GFF-File-Format#utc-creature) editor (UI reference)
- [`Tools/HolocronToolset/src/toolset/gui/editors/utp.py:124-131`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utp.py#L124-L131) - Appearance selection in UTP (placeable) editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/utd.py`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utd.py) - Appearance selection in UTD (door) editor (UI reference)
- [`Tools/HolocronToolset/src/toolset/gui/editors/ute.py:181`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/ute.py#L181) - Appearance ID usage in encounter editor

**Vendor Implementations:**

- [`vendor/reone/src/libs/resource/parser/2da/appearance.cpp:28-125`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/2da/appearance.cpp#L28-L125) - Complete column parsing implementation with all column names
- [`vendor/reone/src/libs/game/object/creature.cpp:98-107`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L98-L107) - Appearance loading and column usage
- [`vendor/reone/src/libs/game/object/creature.cpp:1156-1228`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L1156-L1228) - [model](MDL-MDX-File-Format) and [texture](TPC-File-Format) column access

### [baseitems.2da](2DA-baseitems)

**Engine Usage**: Defines base item types that form the foundation for all items in the game. Each row represents a base item type (weapon, armor, shield, etc.) with properties like damage dice, weapon categories, equipment slots, and item [flags](GFF-File-Format#gff-data-types). The engine uses this file to determine item behavior, combat statistics, and equipment compatibility.

**Row index**: Base item ID (integer)

**Column structure** (columns accessed by reone):

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Item type label |
| `name` | [StrRef](TLK-File-Format#string-references-strref) | string reference for item type name |
| `basecost` | Integer | Base gold cost |
| `stacking` | Integer | Stack size limit |
| `invslotwidth` | Integer | Inventory slot width |
| `invslotheight` | Integer | Inventory slot height |
| `canrotateicon` | Boolean | Whether icon can be rotated in inventory |
| `itemclass` | Integer | Item class identifier |
| `weapontype` | Integer | Weapon type (if weapon) |
| `weaponsize` | Integer | Weapon size category |
| `weaponwield` | Integer | Wield type (one-handed, two-handed, etc.) |
| `damagedice` | Integer | Damage dice count |
| `damagedie` | Integer | Damage die size |
| `damagebonus` | Integer | Base damage bonus |
| `damagetype` | Integer | Damage type [flags](GFF-File-Format#gff-data-types) |
| `weaponmattype` | Integer | Weapon [material](MDL-MDX-File-Format#trimesh-header) type |
| `weaponsound` | Integer | Weapon sound type |
| `ammunitiontype` | Integer | Ammunition type required |
| `rangedweapon` | Boolean | Whether item is a ranged weapon |
| `maxattackrange` | Integer | Maximum attack range |
| `preferredattackrange` | Integer | Preferred attack range |
| `attackmod` | Integer | Attack modifier |
| `damagebonusfeat` | Integer | Feat ID for damage bonus |
| `weaponfocustype` | Integer | Weapon focus type |
| `weaponfocusfeat` | Integer | Weapon focus feat ID |
| `description` | [StrRef](TLK-File-Format#string-references-strref) | string reference for item description |
| `icon` | [ResRef](GFF-File-Format#gff-data-types) | Icon image [ResRef](GFF-File-Format#gff-data-types) |
| `equipableslots` | Integer | Equipment slot [flags](GFF-File-Format#gff-data-types) |
| `model1` through `model6` | ResRef (optional) | 3D [model](MDL-MDX-File-Format) ResRefs for different variations |
| `partenvmap` | ResRef (optional) | Partial environment map [texture](TPC-File-Format) |
| `defaultmodel` | ResRef (optional) | Default [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) |
| `defaulticon` | ResRef (optional) | Default icon [ResRef](GFF-File-Format#gff-data-types) |
| `container` | Boolean | Whether item is a container |
| `weapon` | Boolean | Whether item is a weapon |
| `armor` | Boolean | Whether item is armor |
| `chargesstarting` | Integer | Starting charges (for usable items) |
| `costpercharge` | Integer | Cost per charge to recharge |
| `addcost` | Integer | Additional cost modifier |
| `stolen` | Boolean | Whether item is marked as stolen |
| `minlevel` | Integer | Minimum level requirement |
| `stacking` | Integer | Maximum stack size |
| `reqfeat0` through `reqfeat3` | Integer (optional) | Required feat IDs |
| `reqfeatcount0` through `reqfeatcount3` | Integer (optional) | Required feat counts |
| `reqclass` | Integer (optional) | Required class ID |
| `reqrace` | Integer (optional) | Required race ID |
| `reqalign` | Integer (optional) | Required alignment |
| `reqdeity` | Integer (optional) | Required deity ID |
| `reqstr` | Integer (optional) | Required strength |
| `reqdex` | Integer (optional) | Required dexterity |
| `reqint` | Integer (optional) | Required intelligence |
| `reqwis` | Integer (optional) | Required wisdom |
| `reqcon` | Integer (optional) | Required constitution |
| `reqcha` | Integer (optional) | Required charisma |

**Column Details** (from reone implementation):

The following columns [ARE](GFF-File-Format#are-area) accessed by the reone engine:

- `maxattackrange`: Maximum attack range for ranged weapons
- `crithitmult`: Critical hit multiplier
- `critthreat`: Critical threat range
- `damageflags`: Damage type [flags](GFF-File-Format#gff-data-types)
- `dietoroll`: Damage die size
- `equipableslots`: Equipment slot flags (hex integer)
- `itemclass`: Item class identifier (string)
- `numdice`: Number of damage dice
- `weapontype`: Weapon type identifier
- `weaponwield`: Weapon wield type (one-handed, two-handed, etc.)
- `bodyvar`: Body variation for armor
- `ammunitiontype`: Ammunition type ID (used to look up `ammunitiontypes.2da`)

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:169`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L169) - [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definition for baseitems.2da (defaultmodel)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:187`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L187) - Sound [ResRef](GFF-File-Format#gff-data-types) column definitions for baseitems.2da (powerupsnd, powerdownsnd, poweredsnd)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:215`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L215) - [texture](TPC-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definition for baseitems.2da (defaulticon)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:225`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L225) - Item [ResRef](GFF-File-Format#gff-data-types) column definitions for baseitems.2da (itemclass, baseitemstatref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:466`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L466) - TwoDARegistry.BASEITEMS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:537`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L537) - [GFF](GFF-File-Format) field mapping: "BaseItem" and "ModelVariation" -> baseitems.2da

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:65`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L65) - HTInstallation.TwoDA_BASEITEMS constant
- [`Tools/HolocronToolset/src/toolset/data/installation.py:594-607`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L594-L607) - get_item_icon_from_uti method using baseitems.2da for item class lookup
- [`Tools/HolocronToolset/src/toolset/data/installation.py:609-620`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L609-L620) - get_item_base_name method using baseitems.2da
- [`Tools/HolocronToolset/src/toolset/data/installation.py:630-643`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L630-L643) - get_item_icon_path method using baseitems.2da for item class and icon path
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:107-117`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L107-L117) - baseitems.2da loading and usage in UTI (item) editor for base item selection
- [`Tools/HolocronToolset/src/toolset/gui/dialogs/inventory.py:668-704`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/dialogs/inventory.py#L668-L704) - baseitems.2da usage for equipment slot and droid/human [flag](GFF-File-Format#gff-data-types) lookup

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/object/item.cpp:126-136`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/item.cpp#L126-L136) - Base item column access
- [`vendor/reone/src/libs/game/object/item.cpp:160-171`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/item.cpp#L160-L171) - Ammunition type lookup from baseitems.2da

---

### [classes.2da](2DA-classes)

**Engine Usage**: Defines character classes with their progression tables, skill point calculations, hit dice, saving throw progressions, and feat access. The engine uses this file to determine class abilities, skill point allocation, and level progression mechanics.

**Row index**: Class ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Class label |
| `name` | [StrRef](TLK-File-Format#string-references-strref) | string reference for class name |
| `description` | [StrRef](TLK-File-Format#string-references-strref) | string reference for class description |
| `hitdie` | Integer | Hit dice size (d6, d8, d10, etc.) |
| `skillpointbase` | Integer | Base skill points per level |
| `skillpointbonus` | Integer | Intelligence bonus skill points |
| `attackbonus` | string | Attack bonus progression table reference |
| `savingthrow` | string | Saving throw progression table reference |
| `savingthrowtable` | string | Saving throw table filename |
| `spellgaintable` | string | Spell/Force power gain table reference |
| `spellknowntable` | string | Spell/Force power known table reference |
| `primaryability` | Integer | Primary ability score for class |
| `preferredalignment` | Integer | Preferred alignment |
| `alignrestrict` | Integer | Alignment restrictions |
| `classfeat` | Integer | Class-specific feat ID |
| `classskill` | Integer | Class skill [flags](GFF-File-Format#gff-data-types) |
| `skillpointmaxlevel` | Integer | Maximum level for skill point calculation |
| `spellcaster` | Integer | Spellcasting level (0 = non-caster) |
| `spellcastingtype` | Integer | Spellcasting type identifier |
| `spelllevel` | Integer | Maximum spell level |
| `spellbook` | ResRef (optional) | Spellbook [ResRef](GFF-File-Format#gff-data-types) |
| `icon` | [ResRef](GFF-File-Format#gff-data-types) | Class icon [ResRef](GFF-File-Format#gff-data-types) |
| `portrait` | ResRef (optional) | Class portrait [ResRef](GFF-File-Format#gff-data-types) |
| `startingfeat0` through `startingfeat9` | Integer (optional) | Starting feat IDs |
| `startingpack` | Integer (optional) | Starting equipment pack ID |
| `description` | [StrRef](TLK-File-Format#string-references-strref) | Class description string reference |

**Column Details** (from reone implementation):

The following columns [ARE](GFF-File-Format#are-area) accessed by the reone engine:

- `name`: string reference for class name
- `description`: string reference for class description
- `hitdie`: Hit dice size
- `skillpointbase`: Base skill points per level
- `str`, `dex`, `con`, `int`, `wis`, `cha`: Default ability scores
- `skillstable`: Skills table reference (used to check class skills in `skills.2da`)
- `savingthrowtable`: Saving throw table reference (e.g., `cls_savthr_jedi_guardian`)
- `attackbonustable`: Attack bonus table reference (e.g., `cls_atk_jedi_guardian`)

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:75`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L75) - [StrRef](TLK-File-Format#string-references-strref) column definitions for classes.2da (K1: name, description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:250`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L250) - [StrRef](TLK-File-Format#string-references-strref) column definitions for classes.2da (K2: name, description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:463`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L463) - TwoDARegistry.CLASSES constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:531`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L531) - [GFF](GFF-File-Format) field mapping: "Class" -> classes.2da

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:62`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L62) - HTInstallation.TwoDA_CLASSES constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utc.py:242`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utc.py#L242) - classes.2da included in batch cache for [UTC](GFF-File-Format#utc-creature) editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/utc.py:256`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utc.py#L256) - classes.2da loading from cache
- [`Tools/HolocronToolset/src/toolset/gui/editors/utc.py:291-298`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utc.py#L291-L298) - classes.2da usage in class selection comboboxes and label population

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/d20/class.cpp:34-56`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/d20/class.cpp#L34-L56) - Class loading from [2DA](2DA-File-Format) with column access
- [`vendor/reone/src/libs/game/d20/class.cpp:58-86`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/d20/class.cpp#L58-L86) - Class skills, saving throws, and attack bonuses loading

---

### [feat.2da](2DA-feat)

**Engine Usage**: Defines all feats available in the game, including combat feats, skill feats, Force feats, and class-specific abilities. The engine uses this file to determine feat prerequisites, effects, and availability during character creation and level-up.

**Row index**: Feat ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Feat label |
| `name` | [StrRef](TLK-File-Format#string-references-strref) | string reference for feat name |
| `description` | [StrRef](TLK-File-Format#string-references-strref) | string reference for feat description |
| `icon` | [ResRef](GFF-File-Format#gff-data-types) | Feat icon [ResRef](GFF-File-Format#gff-data-types) |
| `takentext` | [StrRef](TLK-File-Format#string-references-strref) | string reference for "feat taken" message |
| `prerequisite` | Integer (optional) | Prerequisite feat ID |
| `minattackbonus` | Integer (optional) | Minimum attack bonus requirement |
| `minstr` | Integer (optional) | Minimum strength requirement |
| `mindex` | Integer (optional) | Minimum dexterity requirement |
| `minint` | Integer (optional) | Minimum intelligence requirement |
| `minwis` | Integer (optional) | Minimum wisdom requirement |
| `mincon` | Integer (optional) | Minimum constitution requirement |
| `mincha` | Integer (optional) | Minimum charisma requirement |
| `minlevel` | Integer (optional) | Minimum character level |
| `minclasslevel` | Integer (optional) | Minimum class level |
| `minspelllevel` | Integer (optional) | Minimum spell level |
| `spellid` | Integer (optional) | Required spell ID |
| `successor` | Integer (optional) | Successor feat ID (for feat chains) |
| `maxrank` | Integer (optional) | Maximum rank for stackable feats |
| `minrank` | Integer (optional) | Minimum rank requirement |
| `masterfeat` | Integer (optional) | Master feat ID |
| `targetself` | Boolean | Whether feat targets self |
| `orreqfeat0` through `orreqfeat4` | Integer (optional) | Alternative prerequisite feat IDs |
| `reqskill` | Integer (optional) | Required skill ID |
| `reqskillrank` | Integer (optional) | Required skill rank |
| `constant` | Integer (optional) | Constant value for feat calculations |
| `toolscategories` | Integer (optional) | Tool categories [flags](GFF-File-Format#gff-data-types) |
| `effecticon` | ResRef (optional) | Effect icon [ResRef](GFF-File-Format#gff-data-types) |
| `effectdesc` | StrRef (optional) | Effect description string reference |
| `effectcategory` | Integer (optional) | Effect category identifier |
| `allclassescanuse` | Boolean | Whether all classes can use this feat |
| `category` | Integer | Feat category identifier |
| `maxcr` | Integer (optional) | Maximum challenge rating |
| `spellid` | Integer (optional) | Associated spell ID |
| `usesperday` | Integer (optional) | Uses per day limit |
| `masterfeat` | Integer (optional) | Master feat ID for feat trees |

**Column Details** (from reone implementation):

The following columns [ARE](GFF-File-Format#are-area) accessed by the reone engine:

- `name`: string reference for feat name
- `description`: string reference for feat description
- `icon`: Icon [ResRef](GFF-File-Format#gff-data-types)
- `mincharlevel`: Minimum character level (hex integer)
- `prereqfeat1`: Prerequisite feat ID 1 (hex integer)
- `prereqfeat2`: Prerequisite feat ID 2 (hex integer)
- `successor`: Successor feat ID (hex integer)
- `pips`: Feat pips/ranks (hex integer)
- `allclassescanuse`: Boolean - whether all classes can use this feat
- `masterfeat`: Master feat ID
- `orreqfeat0` through `orreqfeat4`: Alternative prerequisite feat IDs
- `hostilefeat`: Boolean - whether feat is hostile
- `category`: Feat category identifier

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:82`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L82) - [StrRef](TLK-File-Format#string-references-strref) column definitions for feat.2da (K1: name, description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:260`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L260) - [StrRef](TLK-File-Format#string-references-strref) column definitions for feat.2da (K2: name, description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:227`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L227) - [ResRef](GFF-File-Format#gff-data-types) column definition for feat.2da (icon)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:464`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L464) - TwoDARegistry.FEATS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:561-562`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L561-L562) - [GFF](GFF-File-Format) field mapping: "FeatID" and "Feat" -> feat.2da
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:321-323`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L321-L323) - [UTC](GFF-File-Format#utc-creature) feat list field documentation
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:432`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L432) - [UTC](GFF-File-Format#utc-creature) feats list initialization
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:762-768`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L762-L768) - Feat list parsing from [UTC](GFF-File-Format#utc-creature) [GFF](GFF-File-Format)
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:907-909`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L907-L909) - Feat list writing to [UTC](GFF-File-Format#utc-creature) [GFF](GFF-File-Format)

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:63`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L63) - HTInstallation.TwoDA_FEATS constant

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/d20/feats.cpp:32-58`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/d20/feats.cpp#L32-L58) - Feat loading from [2DA](2DA-File-Format) with column access
- [`vendor/KotOR.js/src/talents/TalentFeat.ts:36-53`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/talents/TalentFeat.ts#L36-L53) - Feat structure with additional columns
- [`vendor/KotOR.js/src/talents/TalentFeat.ts:122-132`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/talents/TalentFeat.ts#L122-L132) - Feat loading from [2DA](2DA-File-Format)

---

### [skills.2da](2DA-skills)

**Engine Usage**: Defines all skills available in the game, including which classes can use them, their [KEY](KEY-File-Format) ability scores, and skill descriptions. The engine uses this file to determine skill availability, skill point costs, and skill checks.

**Row index**: Skill ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Skill label |
| `name` | [StrRef](TLK-File-Format#string-references-strref) | string reference for skill name |
| `description` | [StrRef](TLK-File-Format#string-references-strref) | string reference for skill description |
| `keyability` | Integer | [KEY](KEY-File-Format) ability score (STR, DEX, INT, etc.) |
| `armorcheckpenalty` | Boolean | Whether armor check penalty applies |
| `allclassescanuse` | Boolean | Whether all classes can use this skill |
| `category` | Integer | Skill category identifier |
| `maxrank` | Integer | Maximum skill rank |
| `untrained` | Boolean | Whether skill can be used untrained |
| `constant` | Integer (optional) | Constant modifier |
| `hostileskill` | Boolean | Whether skill is hostile |
| `icon` | ResRef (optional) | Skill icon [ResRef](GFF-File-Format#gff-data-types) |

**Column Details** (from reone implementation):

The following columns [ARE](GFF-File-Format#are-area) accessed by the reone engine:

- `name`: string reference for skill name
- `description`: string reference for skill description
- `icon`: Icon [ResRef](GFF-File-Format#gff-data-types)
- Dynamic class skill columns: For each class, there is a column named `{classname}_class` (e.g., `jedi_guardian_class`) that contains `1` if the skill is a class skill for that class
- `droidcanuse`: Boolean - whether droids can use this skill
- `npccanuse`: Boolean - whether NPCs can use this skill

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:148`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L148) - [StrRef](TLK-File-Format#string-references-strref) column definitions for skills.2da (K1: name, description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:326`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L326) - [StrRef](TLK-File-Format#string-references-strref) column definitions for skills.2da (K2: name, description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:472`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L472) - TwoDARegistry.SKILLS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:563`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L563) - [GFF](GFF-File-Format) field mapping: "SkillID" -> skills.2da

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:71`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L71) - HTInstallation.TwoDA_SKILLS constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/savegame.py:129`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/savegame.py#L129) - Skills table widget in save game editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/savegame.py:511-519`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/savegame.py#L511-L519) - Skills table population in save game editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/savegame.py:542-543`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/savegame.py#L542-L543) - Skills table update logic

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/d20/skills.cpp:32-48`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/d20/skills.cpp#L32-L48) - Skill loading from [2DA](2DA-File-Format)
- [`vendor/reone/src/libs/game/d20/class.cpp:58-65`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/d20/class.cpp#L58-L65) - Class skill checking using dynamic column names
- [`vendor/KotOR.js/src/talents/TalentSkill.ts:38-49`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/talents/TalentSkill.ts#L38-L49) - Skill loading from [2DA](2DA-File-Format) with droidcanuse and npccanuse columns

---

### [spells.2da](2DA-spells)

**Engine Usage**: Defines all Force powers (and legacy spell entries) in KotOR, including their costs, targeting modes, visual effects, and descriptions. The engine uses this file to determine Force power availability, casting requirements, and effects. Note: KotOR uses Force powers rather than traditional D&D spells, though the file structure is inherited from the Aurora engine (originally designed for Neverwinter Nights).

**Row index**: Spell ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Spell label |
| `name` | [StrRef](TLK-File-Format#string-references-strref) | string reference for spell name |
| `school` | Integer | Spell school identifier |
| `range` | Integer | Spell range type |
| `vs` | Integer | Versus type (self, touch, etc.) |
| `metamagic` | Integer | Metamagic [flags](GFF-File-Format#gff-data-types) |
| `targettype` | Integer | Target type [flags](GFF-File-Format#gff-data-types) |
| `impactscript` | ResRef (optional) | Impact script [ResRef](GFF-File-Format#gff-data-types) |
| `innate` | Integer | Innate Force power level (0 = not available) |
| `conjtime` | Float | Casting/conjuration time |
| `conjtimevfx` | Integer (optional) | Casting time visual effect |
| `conjheadvfx` | Integer (optional) | Casting head visual effect |
| `conjhandvfx` | Integer (optional) | Casting hand visual effect |
| `conjgrndvfx` | Integer (optional) | Casting ground visual effect |
| `conjcastvfx` | Integer (optional) | Casting visual effect |
| `conjimpactscript` | ResRef (optional) | Conjuration impact script |
| `conjduration` | Float | Conjuration duration |
| `conjrange` | Integer | Conjuration range |
| `conjca` | Integer | Conjuration casting [animation](MDL-MDX-File-Format#animation-header) |
| `conjca2` through `conjca50` | Integer (optional) | Additional casting animations (numbered 2-50) |
| `hostilesetting` | Integer | Hostile setting [flags](GFF-File-Format#gff-data-types) |
| `featid` | Integer (optional) | Associated feat ID |
| `counter1` | Integer (optional) | Counter spell ID 1 |
| `counter2` | Integer (optional) | Counter spell ID 2 |
| `counter3` | Integer (optional) | Counter spell ID 3 |
| `projectile` | ResRef (optional) | Projectile [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) |
| `projectilesound` | ResRef (optional) | Projectile sound [ResRef](GFF-File-Format#gff-data-types) |
| `projectiletype` | Integer | Projectile type identifier |
| `projectileorient` | Integer | Projectile orientation |
| `projectilepath` | Integer | Projectile path type |
| `projectilehoming` | Boolean | Whether projectile homes on target |
| `projectilemodel` | ResRef (optional) | Projectile 3D [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) |
| `projectilemodel2` through `projectilemodel50` | ResRef (optional) | Additional projectile models (numbered 2-50) |
| `icon` | [ResRef](GFF-File-Format#gff-data-types) | Spell icon [ResRef](GFF-File-Format#gff-data-types) |
| `icon2` through `icon50` | ResRef (optional) | Additional icons (numbered 2-50) |
| `description` | [StrRef](TLK-File-Format#string-references-strref) | Spell description string reference |
| `altmessage` | StrRef (optional) | Alternative message string reference |
| `usewhencast` | Integer | Use when cast [flags](GFF-File-Format#gff-data-types) |
| `blood` | Boolean | Whether spell causes blood effects |
| `concentration` | Integer | Concentration check DC |
| `immunitytype` | Integer | Immunity type identifier |
| `immunitytype2` through `immunitytype50` | Integer (optional) | Additional immunity types (numbered 2-50) |
| `immunityitem` | Integer | Immunity item type |
| `immunityitem2` through `immunityitem50` | Integer (optional) | Additional immunity items (numbered 2-50) |

**Column Details** (from reone implementation):

The following columns [ARE](GFF-File-Format#are-area) accessed by the reone engine:

- `name`: string reference for spell name
- `spelldesc`: string reference for spell description (note: column name is `spelldesc`, not `description`)
- `iconresref`: Icon ResRef (note: column name is `iconresref`, not `icon`)
- `pips`: Spell pips/ranks (hex integer)
- `conjtime`: Conjuration/casting time
- `casttime`: Cast time
- `catchtime`: Catch time
- `conjanim`: Conjuration [animation](MDL-MDX-File-Format#animation-header) type (e.g., "throw", "up")
- `hostilesetting`: Hostile setting [flags](GFF-File-Format#gff-data-types)
- `projectile`: Projectile [ResRef](GFF-File-Format#gff-data-types)
- `projectileHook`: Projectile hook point
- `projectileOrigin`: Projectile origin point
- `projectileTarget`: Projectile target point
- `projectileCurve`: Projectile curve type
- `projmodel`: Projectile [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types)
- `range`: Spell range
- `impactscript`: Impact script [ResRef](GFF-File-Format#gff-data-types)
- `casthandvisual`: Cast hand visual effect

**Note**: The `spells.2da` file contains many optional columns for projectile [models](MDL-MDX-File-Format), icons, and immunity types (numbered 1-50). These [ARE](GFF-File-Format#are-area) used for spell variations and visual effects.

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:149`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L149) - [StrRef](TLK-File-Format#string-references-strref) column definitions for spells.2da (K1: name, spelldesc)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:327`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L327) - [StrRef](TLK-File-Format#string-references-strref) column definitions for spells.2da (K2: name, spelldesc)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:239`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L239) - Script [ResRef](GFF-File-Format#gff-data-types) column definition for spells.2da (impactscript)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:432`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L432) - Script [ResRef](GFF-File-Format#gff-data-types) column definition for spells.2da (K2: impactscript)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:465`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L465) - TwoDARegistry.POWERS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:558-560`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L558-L560) - [GFF](GFF-File-Format) field mapping: "Subtype", "SpellId", and "Spell" -> spells.2da
- [`Libraries/PyKotor/src/pykotor/common/scriptdefs.py:9380-9381`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptdefs.py#L9380-L9381) - GetLastForcePowerUsed function comment referencing spells.2da
- [`Libraries/PyKotor/src/pykotor/common/scriptlib.py:5676`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptlib.py#L5676) - Debug print referencing spells.2da ID

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:64`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L64) - HTInstallation.TwoDA_POWERS constant

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/d20/spells.cpp:32-48`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/d20/spells.cpp#L32-L48) - Spell loading from [2DA](2DA-File-Format) with column access
- [`vendor/KotOR.js/src/talents/TalentSpell.ts:16-44`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/talents/TalentSpell.ts#L16-L44) - Spell structure with additional columns
- [`vendor/KotOR.js/src/talents/TalentSpell.ts:42-53`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/talents/TalentSpell.ts#L42-L53) - Spell loading from [2DA](2DA-File-Format)

---

## Items & Properties 2DA files

### itemprops.2da

**Engine Usage**: Master table defining all item property types available in the game. Each row represents a property type (damage bonuses, ability score bonuses, skill bonuses, etc.) with their cost calculations and effect parameters. The engine uses this file to determine item property costs, effects, and availability.

**Row index**: Item property ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property label |
| `name` | [StrRef](TLK-File-Format#string-references-strref) | string reference for property name |
| `costtable` | string | Cost calculation table reference |
| `param1` | string | Parameter 1 label |
| `param2` | string | Parameter 2 label |
| `subtype` | Integer | Property subtype identifier |
| `costvalue` | Integer | Base cost value |
| `param1value` | Integer | Parameter 1 default value |
| `param2value` | Integer | Parameter 2 default value |
| `description` | [StrRef](TLK-File-Format#string-references-strref) | Property description string reference |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:135`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L135) - [StrRef](TLK-File-Format#string-references-strref) column definition for itemprops.2da (K1: stringref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:313`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L313) - [StrRef](TLK-File-Format#string-references-strref) column definition for itemprops.2da (K2: stringref)

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:74`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L74) - HTInstallation.TwoDA_ITEM_PROPERTIES constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:107-111`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L107-L111) - itemprops.2da loading in [UTI](GFF-File-Format#uti-item) editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:278-287`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L278-L287) - itemprops.2da usage for property cost table and parameter lookups
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:449-465`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L449-L465) - itemprops.2da usage in property selection and loading

---


### iprp_damagecost.2da

**Engine Usage**: Defines cost calculations for damage bonus item properties. Used to determine item property costs based on damage bonus values.

**Row index**: Damage bonus value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Damage bonus label |
| `cost` | Integer | Cost for this damage bonus value |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:99`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L99) - [StrRef](TLK-File-Format#string-references-strref) column definition for iprp_damagecost.2da (K1: name)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:277`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L277) - [StrRef](TLK-File-Format#string-references-strref) column definition for iprp_damagecost.2da (K2: name)

---

## Objects & Area 2DA files

### [placeables.2da](2DA-placeables)

**Engine Usage**: Defines placeable objects (containers, usable objects, interactive elements) with their [models](MDL-MDX-File-Format), properties, and behaviors. The engine uses this file when loading placeable objects in areas, determining their [models](MDL-MDX-File-Format), hit detection, and interaction properties.

**Row index**: Placeable type ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | String (optional) | Placeable type label |
| `modelname` | ResRef (optional) | 3D [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) |
| `strref` | Integer | string reference for placeable name |
| `bodybag` | Boolean | Whether placeable can contain bodies |
| `canseeheight` | Float | Can-see height for line of sight |
| `hitcheck` | Boolean | Whether hit detection is enabled |
| `hostile` | Boolean | Whether placeable is hostile |
| `ignorestatichitcheck` | Boolean | Whether to ignore static hit checks |
| `lightcolor` | String (optional) | Light color RGB values |
| `lightoffsetx` | String (optional) | Light X offset |
| `lightoffsety` | String (optional) | Light Y offset |
| `lightoffsetz` | String (optional) | Light Z offset |
| `lowgore` | String (optional) | Low gore [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) |
| `noncull` | Boolean | Whether to disable culling |
| `preciseuse` | Boolean | Whether precise use is enabled |
| `shadowsize` | Boolean | Whether shadow size is enabled |
| `soundapptype` | Integer (optional) | Sound appearance type |
| `usesearch` | Boolean | Whether placeable can be searched |

**Column Details**:

The complete column structure is defined in reone's placeables parser:

- `label`: Optional label string
- `modelname`: 3D [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types)
- `strref`: string reference for placeable name
- `bodybag`: Boolean - whether placeable can contain bodies
- `canseeheight`: Float - can-see height for line of sight
- `hitcheck`: Boolean - whether hit detection is enabled
- `hostile`: Boolean - whether placeable is hostile
- `ignorestatichitcheck`: Boolean - whether to ignore static hit checks
- `lightcolor`: Optional string - light color RGB values
- `lightoffsetx`: Optional string - light X offset
- `lightoffsety`: Optional string - light Y offset
- `lightoffsetz`: Optional string - light Z offset
- `lowgore`: Optional string - low gore [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types)
- `noncull`: Boolean - whether to disable culling
- `preciseuse`: Boolean - whether precise use is enabled
- `shadowsize`: Boolean - whether shadow size is enabled
- `soundapptype`: Optional integer - sound appearance type
- `usesearch`: Boolean - whether placeable can be searched

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:141`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L141) - [StrRef](TLK-File-Format#string-references-strref) column definition for placeables.2da (K1: [StrRef](TLK-File-Format#string-references-strref))
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:170`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L170) - [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definition for placeables.2da (K1: modelname)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:319`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L319) - [StrRef](TLK-File-Format#string-references-strref) column definition for placeables.2da (K2: [StrRef](TLK-File-Format#string-references-strref))
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:349`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L349) - [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definition for placeables.2da (K2: modelname)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:467`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L467) - TwoDARegistry.PLACEABLES constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:542`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L542) - [GFF](GFF-File-Format) field mapping: "Appearance" -> placeables.2da

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:66`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L66) - HTInstallation.TwoDA_PLACEABLES constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utp.py:52`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utp.py#L52) - placeables.2da cache initialization comment
- [`Tools/HolocronToolset/src/toolset/gui/editors/utp.py:62`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utp.py#L62) - placeables.2da cache loading
- [`Tools/HolocronToolset/src/toolset/gui/editors/utp.py:121-131`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utp.py#L121-L131) - placeables.2da usage in appearance selection combobox
- [`Tools/HolocronToolset/src/toolset/gui/editors/utp.py:471`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utp.py#L471) - placeables.2da usage for [model](MDL-MDX-File-Format) name lookup

**Vendor Implementations:**

- [`vendor/reone/src/libs/resource/parser/2da/placeables.cpp:29-49`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/2da/placeables.cpp#L29-L49) - Complete column parsing implementation with all column names
- [`vendor/reone/src/libs/game/object/placeable.cpp:59-60`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/placeable.cpp#L59-L60) - Placeable loading from [2DA](2DA-File-Format)

---

### [genericdoors.2da](2DA-genericdoors)

**Engine Usage**: Defines door types with their [models](MDL-MDX-File-Format), [animations](MDL-MDX-File-Format#animation-header), and properties. The engine uses this file when loading doors in areas, determining which [model](MDL-MDX-File-Format) to display and how the door behaves.

**Row index**: Door type ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Door type label |
| `modelname` | [ResRef](GFF-File-Format#gff-data-types) | 3D [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) |
| `name` | String (optional) | Door type name |
| `strref` | Integer (optional) | string reference for door name |
| `blocksight` | Boolean | Whether door blocks line of sight |
| `nobin` | Boolean | Whether door has no bin (container) |
| `preciseuse` | Boolean | Whether precise use is enabled |
| `soundapptype` | Integer (optional) | Sound appearance type |
| `staticanim` | String (optional) | Static [animation](MDL-MDX-File-Format#animation-header) [ResRef](GFF-File-Format#gff-data-types) |
| `visiblemodel` | Boolean | Whether [model](MDL-MDX-File-Format) is visible |

**Column Details**:

The complete column structure is defined in reone's genericdoors parser:

- `label`: Door type label
- `modelname`: 3D [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types)
- `name`: Optional door type name string
- `strref`: Optional integer - string reference for door name
- `blocksight`: Boolean - whether door blocks line of sight
- `nobin`: Boolean - whether door has no bin (container)
- `preciseuse`: Boolean - whether precise use is enabled
- `soundapptype`: Optional integer - sound appearance type
- `staticanim`: Optional string - static [animation](MDL-MDX-File-Format#animation-header) [ResRef](GFF-File-Format#gff-data-types)
- `visiblemodel`: Boolean - whether [model](MDL-MDX-File-Format) is visible

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:78`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L78) - [StrRef](TLK-File-Format#string-references-strref) column definition for [doortypes.2da](2DA-doortypes) (K1: stringrefgame)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:86`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L86) - [StrRef](TLK-File-Format#string-references-strref) column definition for genericdoors.2da (K1: [StrRef](TLK-File-Format#string-references-strref))
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:177`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L177) - [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definition for [doortypes.2da](2DA-doortypes) (K1: [model](MDL-MDX-File-Format))
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:178`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L178) - [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definition for genericdoors.2da (K1: modelname)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:256`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L256) - [StrRef](TLK-File-Format#string-references-strref) column definition for [doortypes.2da](2DA-doortypes) (K2: stringrefgame)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:264`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L264) - [StrRef](TLK-File-Format#string-references-strref) column definition for genericdoors.2da (K2: [StrRef](TLK-File-Format#string-references-strref))
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:356`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L356) - [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definition for [doortypes.2da](2DA-doortypes) (K2: [model](MDL-MDX-File-Format))
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:357`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L357) - [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definition for genericdoors.2da (K2: modelname)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:468`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L468) - TwoDARegistry.DOORS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:543`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L543) - [GFF](GFF-File-Format) field mapping: "GenericType" -> genericdoors.2da

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:67`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L67) - HTInstallation.TwoDA_DOORS constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utd.py:60`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utd.py#L60) - genericdoors.2da cache loading
- [`Tools/HolocronToolset/src/toolset/gui/editors/utd.py:117-123`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utd.py#L117-L123) - genericdoors.2da usage in appearance selection combobox
- [`Tools/HolocronToolset/src/toolset/gui/editors/utd.py:409`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utd.py#L409) - genericdoors.2da usage for [model](MDL-MDX-File-Format) name lookup

**Vendor Implementations:**

- [`vendor/reone/src/libs/resource/parser/2da/genericdoors.cpp:29-41`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/2da/genericdoors.cpp#L29-L41) - Complete column parsing implementation with all column names
- [`vendor/reone/src/libs/game/object/door.cpp:66-67`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/door.cpp#L66-L67) - Door loading from [2DA](2DA-File-Format)

---

### [doortypes.2da](2DA-doortypes)

**Engine Usage**: Defines door type configurations and their properties. The engine uses this file to determine door type names, [models](MDL-MDX-File-Format), and behaviors.

**Row index**: Door type ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Door type label |
| `stringrefgame` | [StrRef](TLK-File-Format#string-references-strref) | string reference for door type name |
| `model` | [ResRef](GFF-File-Format#gff-data-types) | [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) for the door type |
| Additional columns | Various | Door type properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:78`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L78) - [StrRef](TLK-File-Format#string-references-strref) column definition for doortypes.2da
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:177`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L177) - [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definition for doortypes.2da

---

### [soundset.2da](2DA-soundset)

**Engine Usage**: Maps sound set IDs to voice set assignments for characters. The engine uses this file to determine which voice lines to play for characters based on their sound set.

**Row index**: Sound set ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Sound set label |
| `resref` | [ResRef](GFF-File-Format#gff-data-types) | [sound set files](SSF-File-Format) ResRef (e.g., `c_human_m_01`) |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:143`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L143) - [StrRef](TLK-File-Format#string-references-strref) column definition for soundset.2da (K1: [StrRef](TLK-File-Format#string-references-strref))
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:321`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L321) - [StrRef](TLK-File-Format#string-references-strref) column definition for soundset.2da (K2: [StrRef](TLK-File-Format#string-references-strref))
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:459`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L459) - TwoDARegistry.SOUNDSETS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:522`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L522) - [GFF](GFF-File-Format) field mapping: "SoundSetFile" -> soundset.2da
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:90-92`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L90-L92) - [UTC](GFF-File-Format#utc-creature) soundset_id field documentation
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:359`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L359) - [UTC](GFF-File-Format#utc-creature) soundset_id field initialization
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:549-550`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L549-L550) - SoundSetFile field parsing from [UTC](GFF-File-Format#utc-creature) [GFF](GFF-File-Format)
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:821`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L821) - SoundSetFile field writing to [UTC](GFF-File-Format#utc-creature) [GFF](GFF-File-Format)

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:58`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L58) - HTInstallation.TwoDA_SOUNDSETS constant
- [`Tools/HolocronToolset/src/ui/editors/utc.ui:260-267`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/ui/editors/utc.ui#L260-L267) - Soundset selection combobox in [UTC](GFF-File-Format#utc-creature) editor UI

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/object/creature.cpp:1347-1354`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L1347-L1354) - Sound set loading from [2DA](2DA-File-Format)

---

## Visual Effects & [animations](MDL-MDX-File-Format#animation-header) 2DA files

### [visualeffects.2da](2DA-visualeffects)

**Engine Usage**: Defines visual effects (particle effects, impact effects, environmental effects) with their durations, [models](MDL-MDX-File-Format), and properties. The engine uses this file when playing visual effects for spells, combat, and environmental events.

**Row index**: Visual effect ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Visual effect label |
| `name` | [StrRef](TLK-File-Format#string-references-strref) | string reference for effect name |
| `model` | ResRef (optional) | Effect [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) |
| `impactmodel` | ResRef (optional) | Impact [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) |
| `impactorient` | Integer | Impact orientation |
| `impacttype` | Integer | Impact type identifier |
| `duration` | Float | Effect duration in seconds |
| `durationvariance` | Float | Duration variance |
| `loop` | Boolean | Whether effect loops |
| `render` | Boolean | Whether effect is rendered |
| `renderhint` | Integer | Render hint [flags](GFF-File-Format#gff-data-types) |
| `sound` | ResRef (optional) | Sound effect [ResRef](GFF-File-Format#gff-data-types) |
| `sounddelay` | Float | Sound delay in seconds |
| `soundvariance` | Float | Sound variance |
| `soundloop` | Boolean | Whether sound loops |
| `soundvolume` | Float | Sound volume (0.0-1.0) |
| `light` | Boolean | Whether effect emits light |
| `lightcolor` | string | Light color RGB values |
| `lightintensity` | Float | Light intensity |
| `lightradius` | Float | Light radius |
| `lightpulse` | Boolean | Whether light pulses |
| `lightpulselength` | Float | Light pulse length |
| `lightfade` | Boolean | Whether light fades |
| `lightfadelength` | Float | Light fade length |
| `lightfadestart` | Float | Light fade start time |
| `lightfadeend` | Float | Light fade end time |
| `lightshadow` | Boolean | Whether light casts shadows |
| `lightshadowradius` | Float | Light shadow radius |
| `lightshadowintensity` | Float | Light shadow intensity |
| `lightshadowcolor` | string | Light shadow color RGB values |
| `lightshadowfade` | Boolean | Whether light shadow fades |
| `lightshadowfadelength` | Float | Light shadow fade length |
| `lightshadowfadestart` | Float | Light shadow fade start time |
| `lightshadowfadeend` | Float | Light shadow fade end time |
| `lightshadowpulse` | Boolean | Whether light shadow pulses |
| `lightshadowpulselength` | Float | Light shadow pulse length |
| `lightshadowpulseintensity` | Float | Light shadow pulse intensity |
| `lightshadowpulsecolor` | string | Light shadow pulse color RGB values |
| `lightshadowpulsefade` | Boolean | Whether light shadow pulse fades |
| `lightshadowpulsefadelength` | Float | Light shadow pulse fade length |
| `lightshadowpulsefadestart` | Float | Light shadow pulse fade start time |
| `lightshadowpulsefadeend` | Float | Light shadow pulse fade end time |
| `lightshadowpulsefadeintensity` | Float | Light shadow pulse fade intensity |
| `lightshadowpulsefadecolor` | string | Light shadow pulse fade color RGB values |
| `lightshadowpulsefadepulse` | Boolean | Whether light shadow pulse fade pulses |
| `lightshadowpulsefadepulselength` | Float | Light shadow pulse fade pulse length |
| `lightshadowpulsefadepulseintensity` | Float | Light shadow pulse fade pulse intensity |
| `lightshadowpulsefadepulsecolor` | string | Light shadow pulse fade pulse color RGB values |
| `lightshadowpulsefadepulsefade` | Boolean | Whether light shadow pulse fade pulse fades |
| `lightshadowpulsefadepulsefadelength` | Float | Light shadow pulse fade pulse fade length |
| `lightshadowpulsefadepulsefadestart` | Float | Light shadow pulse fade pulse fade start time |
| `lightshadowpulsefadepulsefadeend` | Float | Light shadow pulse fade pulse fade end time |
| `lightshadowpulsefadepulsefadeintensity` | Float | Light shadow pulse fade pulse fade intensity |
| `lightshadowpulsefadepulsefadecolor` | string | Light shadow pulse fade pulse fade color RGB values |

**Note**: The `visualeffects.2da` file may contain many optional columns for advanced lighting and shadow effects.

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:593`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L593) - [GFF](GFF-File-Format) field mapping: "VisualType" -> visualeffects.2da

---

### [portraits.2da](2DA-portraits)

**Engine Usage**: Maps portrait IDs to portrait image ResRefs for character selection screens and character sheets. The engine uses this file to display character portraits in the UI.

**Row index**: Portrait ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Portrait label |
| `baseresref` | [ResRef](GFF-File-Format#gff-data-types) | Base portrait image [ResRef](GFF-File-Format#gff-data-types) |
| `appearancenumber` | Integer | Associated appearance ID |
| `appearance_s` | Integer | Small appearance ID |
| `appearance_l` | Integer | Large appearance ID |
| `forpc` | Boolean | Whether portrait is for player character |
| `sex` | Integer | Gender (0=male, 1=female) |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:455`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L455) - TwoDARegistry.PORTRAITS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:523`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L523) - [GFF](GFF-File-Format) field mapping: "PortraitId" -> portraits.2da
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:66`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L66) - Party portraits documentation comment
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:226-228`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L226-L228) - Portrait rotation logic documentation
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:241`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L241) - Party portraits field documentation
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:391`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L391) - Portraits parsing comment
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:456`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L456) - Portraits writing comment
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:2157`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L2157) - SAVENFO.res portraits documentation
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:2309`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L2309) - Party portraits documentation
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:2370`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L2370) - Portrait debug print

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:54`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L54) - HTInstallation.TwoDA_PORTRAITS constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utc.py:140-152`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utc.py#L140-L152) - portraits.2da usage for portrait selection with alignment-based variant selection (baseresref, baseresrefe, baseresrefve, baseresrefvve, baseresrefvvve)
- [`Tools/HolocronToolset/src/ui/editors/utc.ui:407`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/ui/editors/utc.ui#L407) - Portrait selection combobox in [UTC](GFF-File-Format#utc-creature) editor UI
- [`Tools/HolocronToolset/src/toolset/gui/editors/savegame.py:51`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/savegame.py#L51) - Portraits documentation in save game editor
- [`Tools/HolocronToolset/src/ui/editors/savegame.ui:94-98`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/ui/editors/savegame.ui#L94-L98) - Portraits group box in save game editor UI

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/portraits.cpp:33-51`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/portraits.cpp#L33-L51) - Portrait loading from [2DA](2DA-File-Format) with all column access

---

### heads.2da

**Engine Usage**: Defines head [models](MDL-MDX-File-Format) and [textures](TPC-File-Format) for player characters and NPCs. The engine uses this file when loading character heads, determining which 3D [model](MDL-MDX-File-Format) and [textures](TPC-File-Format) to apply.

**Row index**: Head ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `head` | ResRef (optional) | Head [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) |
| `headtexe` | ResRef (optional) | Head [texture](TPC-File-Format) E [ResRef](GFF-File-Format#gff-data-types) |
| `headtexg` | ResRef (optional) | Head [texture](TPC-File-Format) G [ResRef](GFF-File-Format#gff-data-types) |
| `headtexve` | ResRef (optional) | Head [texture](TPC-File-Format) VE [ResRef](GFF-File-Format#gff-data-types) |
| `headtexvg` | ResRef (optional) | Head [texture](TPC-File-Format) VG [ResRef](GFF-File-Format#gff-data-types) |
| `headtexvve` | ResRef (optional) | Head [texture](TPC-File-Format) VVE [ResRef](GFF-File-Format#gff-data-types) |
| `headtexvvve` | ResRef (optional) | Head [texture](TPC-File-Format) VVVE [ResRef](GFF-File-Format#gff-data-types) |
| `alttexture` | ResRef (optional) | Alternative [texture](TPC-File-Format) [ResRef](GFF-File-Format#gff-data-types) |

**Column Details**:

The complete column structure is defined in reone's heads parser:

- `head`: Optional [ResRef](GFF-File-Format#gff-data-types) - head [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types)
- `alttexture`: Optional [ResRef](GFF-File-Format#gff-data-types) - alternative [texture](TPC-File-Format) [ResRef](GFF-File-Format#gff-data-types)
- `headtexe`: Optional [ResRef](GFF-File-Format#gff-data-types) - head [texture](TPC-File-Format) for evil alignment
- `headtexg`: Optional [ResRef](GFF-File-Format#gff-data-types) - head [texture](TPC-File-Format) for good alignment
- `headtexve`: Optional [ResRef](GFF-File-Format#gff-data-types) - head [texture](TPC-File-Format) for very evil alignment
- `headtexvg`: Optional [ResRef](GFF-File-Format#gff-data-types) - head [texture](TPC-File-Format) for very good alignment
- `headtexvve`: Optional [ResRef](GFF-File-Format#gff-data-types) - head [texture](TPC-File-Format) for very very evil alignment
- `headtexvvve`: Optional [ResRef](GFF-File-Format#gff-data-types) - head [texture](TPC-File-Format) for very very very evil alignment

**References**:

- [`vendor/reone/src/libs/resource/parser/2da/heads.cpp:29-39`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/2da/heads.cpp#L29-L39) - Complete column parsing implementation with all column names
- [`vendor/reone/src/libs/game/object/creature.cpp:1223-1228`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L1223-L1228) - Head loading from [2DA](2DA-File-Format)

---

## Progression Tables 2DA files

### classpowergain.2da

**Engine Usage**: Defines Force power progression by class and level. The engine uses this file to determine which Force powers [ARE](GFF-File-Format#are-area) available to each class at each level.

**Row index**: Level (integer, typically 1-20)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `level` | Integer | Character level |
| `jedi_guardian` | Integer | Jedi Guardian power gain |
| `jedi_consular` | Integer | Jedi Consular power gain |
| `jedi_sentinel` | Integer | Jedi Sentinel power gain |
| `soldier` | Integer | Soldier power gain |
| `scout` | Integer | Scout power gain |
| `scoundrel` | Integer | Scoundrel power gain |
| `jedi_guardian_prestige` | Integer (optional) | Jedi Guardian prestige power gain |
| `jedi_consular_prestige` | Integer (optional) | Jedi Consular prestige power gain |
| `jedi_sentinel_prestige` | Integer (optional) | Jedi Sentinel prestige power gain |

---

## Name Generation 2DA files

### Other Name Generation files

Similar name generation files exist for other species:

- `catharfirst.2da` / `catharlast.2da`: Cathar names (KotOR 2)
- `droidfirst.2da` / `droidlast.2da`: Droid names
- `miracianfirst.2da` / `miracianlast.2da`: Miraluka names (KotOR 2, alternate spelling)
- `miralukafirst.2da` / `miralukalast.2da`: Miraluka names (KotOR 2)
- `rodianfirst.2da` / `rodianlast.2da`: Rodian names
- `twilekfirst.2da` / `twileklast.2da`: Twi'lek names
- `wookieefirst.2da` / `wookieelast.2da`: Wookiee names
- `zabrakfirst.2da` / `zabraklast.2da`: Zabrak names

---

## Additional 2DA files

### ambientmusic.2da

**Engine Usage**: Defines ambient music tracks for areas. The engine uses this file to determine which music to play in different areas based on [area properties](GFF-File-Format#are-area).

**Row index**: Music ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Music label |
| `music` | [ResRef](GFF-File-Format#gff-data-types) | Music file [ResRef](GFF-File-Format#gff-data-types) |
| `resource` | [ResRef](GFF-File-Format#gff-data-types) | Music resource [ResRef](GFF-File-Format#gff-data-types) |
| `stinger1`, `stinger2`, `stinger3` | ResRef (optional) | Stinger music ResRefs |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:206`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L206) - Music [ResRef](GFF-File-Format#gff-data-types) column definitions for ambientmusic.2da (K1: resource, stinger1, stinger2, stinger3)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:398`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L398) - Music [ResRef](GFF-File-Format#gff-data-types) column definitions for ambientmusic.2da (K2: resource, stinger1, stinger2, stinger3)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:545-548`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L545-L548) - [GFF](GFF-File-Format) field mapping: "MusicDay", "MusicNight", "MusicBattle", "MusicDelay" -> ambientmusic.2da

---

### ambientsound.2da

**Engine Usage**: Defines ambient sound effects for areas. The engine uses this file to play ambient sounds in areas.

**Row index**: Sound ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Sound label |
| `sound` | [ResRef](GFF-File-Format#gff-data-types) | Sound file [ResRef](GFF-File-Format#gff-data-types) |
| `resource` | [ResRef](GFF-File-Format#gff-data-types) | Sound resource [ResRef](GFF-File-Format#gff-data-types) |
| `description` | [StrRef](TLK-File-Format#string-references-strref) | Sound description string reference |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:72`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L72) - [StrRef](TLK-File-Format#string-references-strref) column definition for ambientsound.2da (K1: description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:184`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L184) - Sound [ResRef](GFF-File-Format#gff-data-types) column definition for ambientsound.2da (K1: resource)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:247`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L247) - [StrRef](TLK-File-Format#string-references-strref) column definition for ambientsound.2da (K2: description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:376`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L376) - Sound [ResRef](GFF-File-Format#gff-data-types) column definition for ambientsound.2da (K2: resource)
- [`Libraries/PyKotor/src/pykotor/common/scriptdefs.py:6986-6988`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptdefs.py#L6986-L6988) - AmbientSoundPlay function comment

---

### ammunitiontypes.2da

**Engine Usage**: Defines ammunition types for ranged weapons, including their [models](MDL-MDX-File-Format) and sound effects. The engine uses this file when loading items to determine ammunition properties for ranged weapons.

**Row index**: Ammunition type ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Ammunition type label |
| `model` | [ResRef](GFF-File-Format#gff-data-types) | Ammunition [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) |
| `shotsound0` | ResRef (optional) | Shot sound effect ResRef (variant 1) |
| `shotsound1` | ResRef (optional) | Shot sound effect ResRef (variant 2) |
| `impactsound0` | ResRef (optional) | Impact sound effect ResRef (variant 1) |
| `impactsound1` | ResRef (optional) | Impact sound effect ResRef (variant 2) |

**References**:

- [`vendor/reone/src/libs/game/object/item.cpp:164-171`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/item.cpp#L164-L171) - Ammunition type loading from [2DA](2DA-File-Format)

---

### camerastyle.2da

**Engine Usage**: Defines camera styles for areas, including distance, pitch, view angle, and height settings. The engine uses this file to configure camera behavior in different areas.

**Row index**: Camera Style ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Camera style label |
| `name` | string | Camera style name |
| `distance` | Float | Camera distance from target |
| `pitch` | Float | Camera pitch angle |
| `viewangle` | Float | Camera view angle |
| `height` | Float | Camera height offset |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:497`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L497) - TwoDARegistry.CAMERAS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:550`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L550) - [GFF](GFF-File-Format) field mapping: "CameraStyle" -> camerastyle.2da
- [`Libraries/PyKotor/src/pykotor/resource/generics/are.py:37`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/are.py#L37) - [ARE](GFF-File-Format#are-area) camera_style field documentation
- [`Libraries/PyKotor/src/pykotor/resource/generics/are.py:123`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/are.py#L123) - Camera style index comment
- [`Libraries/PyKotor/src/pykotor/resource/generics/are.py:442`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/are.py#L442) - CameraStyle field parsing from [ARE](GFF-File-Format#are-area) [GFF](GFF-File-Format)
- [`Libraries/PyKotor/src/pykotor/resource/generics/are.py:579`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/are.py#L579) - CameraStyle field writing to [ARE](GFF-File-Format#are-area) [GFF](GFF-File-Format)

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:96`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L96) - HTInstallation.TwoDA_CAMERAS constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/are.py:102`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/are.py#L102) - camerastyle.2da loading in [ARE](GFF-File-Format#are-area) editor

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/camerastyles.cpp:29-42`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/camerastyles.cpp#L29-L42) - Camera style loading from [2DA](2DA-File-Format)
- [`vendor/reone/src/libs/game/object/area.cpp:140-148`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/area.cpp#L140-L148) - Camera style usage in areas

---

### footstepsounds.2da

**Engine Usage**: Defines footstep sound effects for different surface types and footstep types. The engine uses this file to play appropriate footstep sounds based on the surface [material](MDL-MDX-File-Format#trimesh-header) and creature footstep type.

**Row index**: Footstep type ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Footstep type label |
| `dirt0`, `dirt1`, `dirt2` | ResRef (optional) | Dirt surface footstep sounds |
| `grass0`, `grass1`, `grass2` | ResRef (optional) | Grass surface footstep sounds |
| `stone0`, `stone1`, `stone2` | ResRef (optional) | Stone surface footstep sounds |
| `wood0`, `wood1`, `wood2` | ResRef (optional) | Wood surface footstep sounds |
| `water0`, `water1`, `water2` | ResRef (optional) | Water surface footstep sounds |
| `carpet0`, `carpet1`, `carpet2` | ResRef (optional) | Carpet surface footstep sounds |
| `metal0`, `metal1`, `metal2` | ResRef (optional) | Metal surface footstep sounds |
| `leaves0`, `leaves1`, `leaves2` | ResRef (optional) | Leaves surface footstep sounds |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:188-198`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L188-L198) - Sound [ResRef](GFF-File-Format#gff-data-types) column definitions for footstepsounds.2da (K1: rolling, dirt0-2, grass0-2, stone0-2, wood0-2, water0-2, carpet0-2, metal0-2, puddles0-2, leaves0-2, force1-3)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:380-390`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L380-L390) - Sound [ResRef](GFF-File-Format#gff-data-types) column definitions for footstepsounds.2da (K2: rolling, dirt0-2, grass0-2, stone0-2, wood0-2, water0-2, carpet0-2, metal0-2, puddles0-2, leaves0-2, force1-3)

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/footstepsounds.cpp:31-57`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/footstepsounds.cpp#L31-L57) - Footstep sounds loading from [2DA](2DA-File-Format)
- [`vendor/reone/src/libs/game/object/creature.cpp:106`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L106) - Footstep type usage from [appearance.2da](2DA-appearance)

---

### prioritygroups.2da

**Engine Usage**: Defines priority groups for sound effects, determining which sounds take precedence when multiple sounds [ARE](GFF-File-Format#are-area) playing. The engine uses this file to calculate sound priority values.

**Row index**: Priority Group ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Priority group label |
| `priority` | Integer | Priority value (higher = more important) |

**References**:

- [`vendor/reone/src/libs/game/object/sound.cpp:92-96`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/sound.cpp#L92-L96) - Priority group loading from [2DA](2DA-File-Format)

---

### repute.2da

**Engine Usage**: Defines reputation values between different factions. The engine uses this file to determine whether creatures [ARE](GFF-File-Format#are-area) enemies, friends, or neutral to each other based on their faction relationships.

**Row index**: Faction ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Faction label |
| Additional columns | Integer | Reputation values for each faction (column names match faction labels) |

**Note**: The `repute.2da` file is a square [matrix](BWM-File-Format#walkable-adjacencies) where each row represents a faction, and each column (after `label`) represents the reputation value toward another faction. Reputation values typically range from 0-100, where values below 50 [ARE](GFF-File-Format#are-area) enemies, above 50 [ARE](GFF-File-Format#are-area) friends, and 50 is neutral.

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:460`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L460) - TwoDARegistry.FACTIONS constant definition (maps to "repute")
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:526-527`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L526-L527) - [GFF](GFF-File-Format) field mapping: "FactionID" and "Faction" -> repute.2da
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:92`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L92) - REPUTE.fac documentation comment
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:1593`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L1593) - REPUTE.fac file check comment
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:1627`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L1627) - REPUTE.fac documentation
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:1667`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L1667) - REPUTE_IDENTIFIER constant definition
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:1683-1684`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L1683-L1684) - repute [GFF](GFF-File-Format) field initialization
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:1759-1761`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L1759-L1761) - REPUTE.fac parsing
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:1795-1796`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L1795-L1796) - REPUTE.fac writing

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:59`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L59) - HTInstallation.TwoDA_FACTIONS constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utc.py:239`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utc.py#L239) - repute.2da included in batch cache for [UTC](GFF-File-Format#utc-creature) editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/utc.py:253-280`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utc.py#L253-L280) - repute.2da usage in faction selection combobox
- [`Tools/HolocronToolset/src/toolset/gui/editors/utp.py:121-128`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utp.py#L121-L128) - repute.2da usage in [UTP](GFF-File-Format#utp-placeable) editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/utd.py:117-124`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utd.py#L117-L124) - repute.2da usage in [UTD](GFF-File-Format#utd-door) editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/ute.py:106-109`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/ute.py#L106-L109) - repute.2da usage in [UTE](GFF-File-Format#ute-encounter) editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/utt.py:72-78`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utt.py#L72-L78) - repute.2da usage in [UTT](GFF-File-Format#utt-trigger) editor

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/reputes.cpp:36-62`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/reputes.cpp#L36-L62) - Repute [matrix](BWM-File-Format#walkable-adjacencies) loading from [2DA](2DA-File-Format)

---

### surfacemat.2da

**Engine Usage**: Defines surface [material](MDL-MDX-File-Format#trimesh-header) properties for [walkmesh](BWM-File-Format) surfaces, including walkability, line of sight blocking, and grass rendering. The engine uses this file to determine surface behavior during pathfinding and rendering.

**Row index**: Surface [material](MDL-MDX-File-Format#trimesh-header) ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Surface [material](MDL-MDX-File-Format#trimesh-header) label |
| `walk` | Boolean | Whether surface is walkable |
| `walkcheck` | Boolean | Whether walk check applies |
| `lineofsight` | Boolean | Whether surface blocks line of sight |
| `grass` | Boolean | Whether surface has grass rendering |
| `sound` | string | Sound type identifier for footstep sounds |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/resource/formats/mdl/io_mdl.py:21`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/mdl/io_mdl.py#L21) - SurfaceMaterial import
- [`Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_types.py:9`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_types.py#L9) - SurfaceMaterial import
- [`Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_types.py:412`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_types.py#L412) - SurfaceMaterial.GRASS default value
- [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:47`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L47) - SurfaceMaterial ID per [face](MDL-MDX-File-Format#face-structure) documentation
- [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:784`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L784) - SurfaceMaterial ID field documentation
- [`Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py:1578`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py#L1578) - Comment referencing surfacemat.2da for [walkmesh](BWM-File-Format) surface [material](MDL-MDX-File-Format#trimesh-header)
- [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py:160`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py#L160) - SurfaceMaterial parsing from [BWM](BWM-File-Format)

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/surfaces.cpp:29-44`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/surfaces.cpp#L29-L44) - Surface [material](MDL-MDX-File-Format#trimesh-header) loading from [2DA](2DA-File-Format)

---

### loadscreenhints.2da

**Engine Usage**: Defines loading screen hints displayed during area transitions. The engine uses this file to show helpful tips and hints to players while loading.

**Row index**: Loading Screen Hint ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Hint label |
| `strref` | [StrRef](TLK-File-Format#string-references-strref) | string reference for hint text |

**References**:

- [`vendor/xoreos/src/engines/kotor/gui/loadscreen/loadscreen.cpp:45`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotor/gui/loadscreen/loadscreen.cpp#L45) - Loading screen hints TODO comment (KotOR-specific)

---

### bodybag.2da

**Engine Usage**: Defines body bag appearances for creatures when they die. The engine uses this file to determine which appearance to use for the body bag container that appears when a creature is killed.

**Row index**: Body Bag ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Body bag label |
| `name` | [StrRef](TLK-File-Format#string-references-strref) | string reference for body bag name |
| `appearance` | Integer | Appearance ID for the body bag [model](MDL-MDX-File-Format) |
| `corpse` | Boolean | Whether the body bag represents a corpse |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:536`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L536) - [GFF](GFF-File-Format) field mapping: "BodyBag" -> bodybag.2da
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:296-298`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L296-L298) - [UTC](GFF-File-Format#utc-creature) bodybag_id field documentation (not used by game engine)
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:438`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L438) - [UTC](GFF-File-Format#utc-creature) bodybag_id field initialization
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:555-556`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L555-L556) - BodyBag field parsing from [UTC](GFF-File-Format#utc-creature) GFF (deprecated)
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:944`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L944) - BodyBag field writing to [UTC](GFF-File-Format#utc-creature) [GFF](GFF-File-Format)
- [`Libraries/PyKotor/src/pykotor/resource/generics/utp.py:105`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utp.py#L105) - [UTP](GFF-File-Format#utp-placeable) bodybag_id field documentation
- [`Libraries/PyKotor/src/pykotor/resource/generics/utp.py:179`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utp.py#L179) - [UTP](GFF-File-Format#utp-placeable) bodybag_id field initialization
- [`Libraries/PyKotor/src/pykotor/resource/generics/utp.py:254`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utp.py#L254) - BodyBag field parsing from [UTP](GFF-File-Format#utp-placeable) [GFF](GFF-File-Format)
- [`Libraries/PyKotor/src/pykotor/resource/generics/utp.py:341`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utp.py#L341) - BodyBag field writing to [UTP](GFF-File-Format#utp-placeable) [GFF](GFF-File-Format)

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/object/creature.cpp:1357-1366`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L1357-L1366) - Body bag loading from [2DA](2DA-File-Format)

---

### ranges.2da

**Engine Usage**: Defines perception ranges for creatures, including sight and hearing ranges. The engine uses this file to determine how far creatures can see and hear.

**Row index**: Range ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Range label |
| `primaryrange` | Float | Primary perception range (sight range) |
| `secondaryrange` | Float | Secondary perception range (hearing range) |

**References**:

- [`vendor/reone/src/libs/game/object/creature.cpp:1398-1406`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L1398-L1406) - Perception range loading from [2DA](2DA-File-Format)
- [`vendor/KotOR.js/src/module/ModuleCreature.ts:3178-3187`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L3178-L3187) - Perception range access from [2DA](2DA-File-Format)

---

### regeneration.2da

**Engine Usage**: Defines regeneration rates for creatures in combat and non-combat states. The engine uses this file to determine how quickly creatures regenerate hit points and Force points.

**Row index**: Regeneration State ID (integer, 0=combat, 1=non-combat)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Regeneration state label |
| Additional columns | [float](GFF-File-Format#gff-data-types) | Regeneration rates for different resource types |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:759`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L759) - Regeneration rate loading from [2DA](2DA-File-Format)

---

### animations.2da

**Engine Usage**: Defines [animation](MDL-MDX-File-Format#animation-header) names and properties for creatures and objects. The engine uses this file to map [animation](MDL-MDX-File-Format#animation-header) IDs to [animation](MDL-MDX-File-Format#animation-header) names for playback.

**Row index**: [animation](MDL-MDX-File-Format#animation-header) ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | [animation](MDL-MDX-File-Format#animation-header) label |
| `name` | string | [animation](MDL-MDX-File-Format#animation-header) name (used to look up [animation](MDL-MDX-File-Format#animation-header) in [model](MDL-MDX-File-Format)) |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:1474-1482`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L1474-L1482) - [animation](MDL-MDX-File-Format#animation-header) lookup from [2DA](2DA-File-Format)
- [`vendor/KotOR.js/src/module/ModulePlaceable.ts:1063-1103`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModulePlaceable.ts#L1063-L1103) - Placeable [animation](MDL-MDX-File-Format#animation-header) lookup from [2DA](2DA-File-Format)
- [`vendor/KotOR.js/src/module/ModuleDoor.ts:1343-1365`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleDoor.ts#L1343-L1365) - Door [animation](MDL-MDX-File-Format#animation-header) lookup from [2DA](2DA-File-Format)

### combatanimations.2da

**Engine Usage**: Defines combat-specific [animation](MDL-MDX-File-Format#animation-header) properties and mappings. The engine uses this file to determine which [animations](MDL-MDX-File-Format#animation-header) to play during combat actions.

**Row index**: Combat [animation](MDL-MDX-File-Format#animation-header) ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Combat [animation](MDL-MDX-File-Format#animation-header) label |
| Additional columns | Various | Combat [animation](MDL-MDX-File-Format#animation-header) properties |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:1482`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L1482) - Combat [animation](MDL-MDX-File-Format#animation-header) lookup from [2DA](2DA-File-Format)

---

### weaponsounds.2da

**Engine Usage**: Defines sound effects for weapon attacks based on base item type. The engine uses this file to play appropriate weapon sounds during combat.

**Row index**: Base Item ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Base item label |
| Additional columns | [ResRef](GFF-File-Format#gff-data-types) | Sound effect ResRefs for different attack types |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:1819-1822`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L1819-L1822) - Weapon sound lookup from [2DA](2DA-File-Format)

---

### placeableobjsnds.2da

**Engine Usage**: Defines sound effects for placeable objects based on sound appearance type. The engine uses this file to play appropriate sounds when interacting with placeables.

**Row index**: Sound Appearance type ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Sound appearance type label |
| Additional columns | [ResRef](GFF-File-Format#gff-data-types) | Sound effect ResRefs for different interaction types |

**References**:

- [`vendor/KotOR.js/src/module/ModulePlaceable.ts:387-389`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModulePlaceable.ts#L387-L389) - Placeable sound lookup from [2DA](2DA-File-Format)
- [`vendor/KotOR.js/src/module/ModuleDoor.ts:239-241`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleDoor.ts#L239-L241) - Door sound lookup from [2DA](2DA-File-Format)

---

### creaturespeed.2da

**Engine Usage**: Defines movement speed rates for creatures based on walk rate ID. The engine uses this file to determine walking and running speeds.

**Row index**: Walk Rate ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Walk rate label |
| `walkrate` | Float | Walking speed rate |
| `runrate` | Float | Running speed rate |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:2875-2887`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L2875-L2887) - Creature speed lookup from [2DA](2DA-File-Format)

---

### exptable.2da

**Engine Usage**: Defines experience point requirements for each character level. The engine uses this file to determine when a character levels up based on accumulated experience.

**Row index**: Level (integer, typically 1-20)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Level label |
| Additional columns | Integer | Experience point requirements for leveling up |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:2926-2941`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L2926-L2941) - Experience table lookup from [2DA](2DA-File-Format)

---

### guisounds.2da

**Engine Usage**: Defines sound effects for [GUI](GFF-File-Format#gui-graphical-user-interface) interactions (button clicks, mouse enter events, etc.). The engine uses this file to play appropriate sounds when the player interacts with UI elements.

**Row index**: Sound ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Sound label (e.g., "Clicked_Default", "Entered_Default") |
| `soundresref` | [ResRef](GFF-File-Format#gff-data-types) | Sound effect [ResRef](GFF-File-Format#gff-data-types) |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:200`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L200) - Sound [ResRef](GFF-File-Format#gff-data-types) column definition for guisounds.2da (K1: soundresref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:392`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L392) - Sound [ResRef](GFF-File-Format#gff-data-types) column definition for guisounds.2da (K2: soundresref)

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/gui/sounds.cpp:31-45`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/gui/sounds.cpp#L31-L45) - [GUI](GFF-File-Format#gui-graphical-user-interface) sound loading from [2DA](2DA-File-Format)

---

### dialoganimations.2da

**Engine Usage**: Maps dialog [animation](MDL-MDX-File-Format#animation-header) ordinals to [animation](MDL-MDX-File-Format#animation-header) names for use in conversations. The engine uses this file to determine which [animation](MDL-MDX-File-Format#animation-header) to play when a dialog line specifies an [animation](MDL-MDX-File-Format#animation-header) ordinal.

**Row index**: [animation](MDL-MDX-File-Format#animation-header) Index (integer, ordinal - 10000)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | [animation](MDL-MDX-File-Format#animation-header) label |
| `name` | string | [animation](MDL-MDX-File-Format#animation-header) name (used to look up [animation](MDL-MDX-File-Format#animation-header) in [model](MDL-MDX-File-Format)) |

**References**:

- [`vendor/reone/src/libs/game/gui/dialog.cpp:302-315`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/gui/dialog.cpp#L302-L315) - Dialog [animation](MDL-MDX-File-Format#animation-header) lookup from [2DA](2DA-File-Format)

---


### forceshields.2da

**Engine Usage**: Defines Force shield visual effects and properties. The engine uses this file to determine which visual effect to display when a Force shield is active.

**Row index**: Force Shield ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Force shield label |
| Additional columns | Various | Force shield visual effect properties |

**References**:

- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts:5552`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts#L5552) - Force shield lookup from [2DA](2DA-File-Format)

---

### plot.2da

**Engine Usage**: Defines journal/quest entries with their experience point rewards and labels. The engine uses this file to manage quest tracking, [journal entries](GFF-File-Format#jrl-journal), and experience point calculations for quest completion.

**Row index**: Plot ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Plot/quest label (used as quest identifier) |
| `xp` | Integer | Experience points awarded for quest completion |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:123-125`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L123-L125) - [UTC](GFF-File-Format#utc-creature) plot field documentation
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:375`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L375) - [UTC](GFF-File-Format#utc-creature) plot field initialization
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:579-580`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L579-L580) - Plot field parsing from [UTC](GFF-File-Format#utc-creature) [GFF](GFF-File-Format)
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:839`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L839) - Plot field writing to [UTC](GFF-File-Format#utc-creature) [GFF](GFF-File-Format)
- [`Libraries/PyKotor/src/pykotor/resource/generics/uti.py:71-73`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/uti.py#L71-L73) - [UTI](GFF-File-Format#uti-item) plot field documentation
- [`Libraries/PyKotor/src/pykotor/resource/generics/uti.py:129`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/uti.py#L129) - [UTI](GFF-File-Format#uti-item) plot field initialization
- [`Libraries/PyKotor/src/pykotor/resource/generics/uti.py:256-258`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/uti.py#L256-L258) - Plot field parsing from [UTI](GFF-File-Format#uti-item) [GFF](GFF-File-Format)
- [`Libraries/PyKotor/src/pykotor/resource/generics/uti.py:339`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/uti.py#L339) - Plot field writing to [UTI](GFF-File-Format#uti-item) [GFF](GFF-File-Format)
- [`Libraries/PyKotor/src/pykotor/resource/generics/dlg/io/gff.py:89-92`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/dlg/io/gff.py#L89-L92) - Dialog [node](MDL-MDX-File-Format#node-structures) PlotIndex and PlotXPPercentage field parsing

**Vendor Implementations:**

- [`vendor/KotOR.js/src/managers/JournalManager.ts:58-64`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/managers/JournalManager.ts#L58-L64) - Plot/quest experience lookup from [2DA](2DA-File-Format)
- [`vendor/KotOR.js/src/managers/JournalManager.ts:101-104`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/managers/JournalManager.ts#L101-L104) - Plot existence check from [2DA](2DA-File-Format)
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts:7845-7848`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts#L7845-L7848) - Plot table access for quest experience

---

### [traps.2da](2DA-traps)

**Engine Usage**: Defines trap properties including [models](MDL-MDX-File-Format), sounds, and scripts. The engine uses this file when loading triggers with trap types to determine trap appearance and behavior.

**Row index**: Trap type ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Trap type label |
| `name` | [StrRef](TLK-File-Format#string-references-strref) | string reference for trap name |
| `model` | [ResRef](GFF-File-Format#gff-data-types) | Trap [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) |
| `explosionsound` | [ResRef](GFF-File-Format#gff-data-types) | Explosion sound effect [ResRef](GFF-File-Format#gff-data-types) |
| `resref` | [ResRef](GFF-File-Format#gff-data-types) | Trap script [ResRef](GFF-File-Format#gff-data-types) |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:150`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L150) - [StrRef](TLK-File-Format#string-references-strref) column definitions for traps.2da (K1: trapname, name)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:328`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L328) - [StrRef](TLK-File-Format#string-references-strref) column definitions for traps.2da (K2: trapname, name)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:470`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L470) - TwoDARegistry.TRAPS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:568`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L568) - [GFF](GFF-File-Format) field mapping: "TrapType" -> traps.2da
- [`Libraries/PyKotor/src/pykotor/common/scriptdefs.py:6347-6348`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptdefs.py#L6347-L6348) - VersusTrapEffect function comments
- [`Libraries/PyKotor/src/pykotor/common/scriptdefs.py:7975-7976`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptdefs.py#L7975-L7976) - GetLastHostileActor function comment mentioning traps
- [`Libraries/PyKotor/src/pykotor/common/scriptlib.py:21692`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptlib.py#L21692) - Trap targeting comment

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:69`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L69) - HTInstallation.TwoDA_TRAPS constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utt.py:73-87`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utt.py#L73-L87) - traps.2da loading and usage in trap type selection combobox
- [`Tools/HolocronToolset/src/toolset/gui/editors/utt.py:167`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utt.py#L167) - traps.2da usage for setting trap type index
- [`Tools/HolocronToolset/src/toolset/gui/editors/utt.py:216`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utt.py#L216) - traps.2da usage for getting trap type index
- [`Tools/HolocronToolset/src/ui/editors/utt.ui:252`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/ui/editors/utt.ui#L252) - Trap selection combobox in [UTT](GFF-File-Format#utt-trigger) editor UI

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/object/trigger.cpp:75-78`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/trigger.cpp#L75-L78) - Trap type loading from [2DA](2DA-File-Format)
- [`vendor/KotOR.js/src/module/ModuleTrigger.ts:605-611`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleTrigger.ts#L605-L611) - Trap loading from [2DA](2DA-File-Format)
- [`vendor/KotOR.js/src/module/ModuleObject.ts:1822`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleObject.ts#L1822) - Trap lookup from [2DA](2DA-File-Format)

---

### modulesave.2da

**Engine Usage**: Defines which modules should be included in save games. The engine uses this file to determine whether a module's state should be persisted when saving the game.

**Row index**: Module Index (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Module label |
| `modulename` | string | Module filename (e.g., "001ebo") |
| `includeInSave` | Boolean | Whether module state should be saved (0 = false, 1 = true) |

**References**:

- [`vendor/KotOR.js/src/module/Module.ts:663-669`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/Module.ts#L663-L669) - Module save inclusion check from [2DA](2DA-File-Format)

---

### tutorial.2da

**Engine Usage**: Defines tutorial window tracking entries. The engine uses this file to track which tutorial windows have been shown to the player.

**Row index**: Tutorial ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Tutorial label |
| Additional columns | Various | Tutorial window properties |

**References**:

- [`vendor/KotOR.js/src/managers/PartyManager.ts:180-187`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/managers/PartyManager.ts#L180-L187) - Tutorial window tracker initialization from [2DA](2DA-File-Format)
- [`vendor/KotOR.js/src/managers/PartyManager.ts:438`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/managers/PartyManager.ts#L438) - Tutorial table access

---

### globalcat.2da

**Engine Usage**: Defines global variables and their types for the game engine. The engine uses this file to initialize global variables at game start, determining which variables [ARE](GFF-File-Format#are-area) integers, floats, or strings.

**Row index**: Global Variable Index (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Global variable label |
| `name` | string | Global variable name |
| `type` | string | Variable type ("Number", "Boolean", "string", etc.) |

**References**:

- [`vendor/NorthernLights/Assets/Scripts/Systems/StateSystem.cs:282-294`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/Systems/StateSystem.cs#L282-L294) - Global variable initialization from [2DA](2DA-File-Format)

---

### subrace.2da

**Engine Usage**: Defines subrace types for character creation and [creature templates](GFF-File-Format#utc-creature). The engine uses this file to determine subrace properties and restrictions.

**Row index**: Subrace ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Subrace label |
| Additional columns | Various | Subrace properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:457`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L457) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:56`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L56) - HTInstallation constant

---

### gender.2da

**Engine Usage**: Defines gender types for character creation and [creature templates](GFF-File-Format#utc-creature). The engine uses this file to determine gender-specific properties and restrictions.

**Row index**: Gender ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Gender label |
| Additional columns | Various | Gender properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:461`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L461) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:60`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L60) - HTInstallation constant

---

### [racialtypes.2da](2DA-racialtypes)

**Engine Usage**: Defines racial types for character creation and [creature templates](GFF-File-Format#utc-creature). The engine uses this file to determine race-specific properties, restrictions, and bonuses.

**Row index**: Race ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Race label |
| Additional columns | Various | Race properties and bonuses |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:471`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L471) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:70`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L70) - HTInstallation constant

---

### upgrade.2da

**Engine Usage**: Defines item upgrade types and properties. The engine uses this file to determine which upgrades can be applied to items and their effects.

**Row index**: Upgrade type ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Upgrade type label |
| Additional columns | Various | Upgrade properties and effects |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:473`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L473) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:72`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L72) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:632-639`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L632-L639) - Upgrade selection in item editor

---

### encdifficulty.2da

**Engine Usage**: Defines encounter difficulty levels for area encounters. The engine uses this file to determine encounter scaling and difficulty modifiers.

**Row index**: Difficulty ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Difficulty label |
| Additional columns | Various | Difficulty modifiers and properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:474`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L474) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:73`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L73) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/ute.py:101-104`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/ute.py#L101-L104) - Encounter difficulty selection

---

### [itempropdef.2da](2DA-itempropdef)

**Engine Usage**: Defines item property definitions and their base properties. This is the master table for all item properties in the game. The engine uses this file to determine item property types, costs, and effects.

**Row index**: Item Property ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property label |
| Additional columns | Various | Property definitions, costs, and parameters |

**Note**: This file may be the same as or related to `itemprops.2da` documented earlier. The exact relationship between these files may vary between KotOR 1 and 2.

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:475`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L475) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:74`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L74) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:107-111`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L107-L111) - Item property loading in item editor

---

### emotion.2da

**Engine Usage**: Defines emotion [animations](MDL-MDX-File-Format#animation-header) for dialog conversations (KotOR 2 only). The engine uses this file to determine which emotion [animation](MDL-MDX-File-Format#animation-header) to play during dialog lines.

**Row index**: Emotion ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Emotion label |
| Additional columns | Various | Emotion [animation](MDL-MDX-File-Format#animation-header) properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:491`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L491) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:90`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L90) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/dlg/editor.py:1267-1319`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/dlg/editor.py#L1267-L1319) - Emotion loading in dialog editor (KotOR 2 only)

---

### facialanim.2da

**Engine Usage**: Defines facial [animation](MDL-MDX-File-Format#animation-header) expressions for dialog conversations (KotOR 2 only). The engine uses this file to determine which facial expression [animation](MDL-MDX-File-Format#animation-header) to play during dialog lines.

**Row index**: Expression ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Expression label |
| Additional columns | Various | Facial [animation](MDL-MDX-File-Format#animation-header) properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:492`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L492) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:91`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L91) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/dlg/editor.py:1267-1325`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/dlg/editor.py#L1267-L1325) - Expression loading in dialog editor (KotOR 2 only)

---

### videoeffects.2da

**Engine Usage**: Defines video/camera effects for dialog conversations. The engine uses this file to determine which visual effect to apply during dialog camera shots.

**Row index**: Video Effect ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Video effect label |
| Additional columns | Various | Video effect properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:493`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L493) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:92`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L92) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/dlg/editor.py:1263-1298`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/dlg/editor.py#L1263-L1298) - Video effect loading in dialog editor

---

### planetary.2da

**Engine Usage**: Defines planetary information for the galaxy map and travel system. The engine uses this file to determine planet names, descriptions, and travel properties.

**Row index**: Planet ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Planet label |
| Additional columns | Various | Planet properties and travel information |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:495`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L495) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:94`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L94) - HTInstallation constant

---

### cursors.2da

**Engine Usage**: Defines cursor types for different object interactions. The engine uses this file to determine which cursor to display when hovering over different object types.

**Row index**: Cursor ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Cursor label |
| Additional columns | Various | Cursor properties and ResRefs |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:469`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L469) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:68`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L68) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utt.py:71-76`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utt.py#L71-L76) - Cursor selection in trigger editor

---

## Item Property Parameter & Cost Tables 2DA files

The following 2DA files [ARE](GFF-File-Format#are-area) used for item property parameter and cost calculations:

### iprp_paramtable.2da

**Engine Usage**: Master table listing all item property parameter tables. The engine uses this file to look up which parameter table to use for a specific item property type.

**Row index**: Parameter Table ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Parameter table label |
| Additional columns | Various | Parameter table ResRefs and properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:476`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L476) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:75`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L75) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:517-558`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L517-L558) - Parameter table lookup in item editor

---

### iprp_costtable.2da

**Engine Usage**: Master table listing all item property cost calculation tables. The engine uses this file to look up which cost table to use for calculating item property costs.

**Row index**: Cost Table ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Cost table label |
| Additional columns | Various | Cost table ResRefs and properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:477`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L477) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:76`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L76) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:486-496`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L486-L496) - Cost table lookup in item editor

---

### iprp_abilities.2da

**Engine Usage**: Maps item property values to ability score bonuses. The engine uses this file to determine which ability score is affected by an item property.

**Row index**: Item Property Value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| Additional columns | Various | Ability score mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:478`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L478) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:77`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L77) - HTInstallation constant

---

### iprp_aligngrp.2da

**Engine Usage**: Maps item property values to alignment group restrictions. The engine uses this file to determine alignment restrictions for item properties.

**Row index**: Item Property Value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| Additional columns | Various | Alignment group mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:479`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L479) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:78`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L78) - HTInstallation constant

---

### iprp_combatdam.2da

**Engine Usage**: Maps item property values to combat damage bonuses. The engine uses this file to determine damage bonus calculations for item properties.

**Row index**: Item Property Value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| Additional columns | Various | Combat damage mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:480`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L480) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:79`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L79) - HTInstallation constant

---

### iprp_damagetype.2da

**Engine Usage**: Maps item property values to damage type [flags](GFF-File-Format#gff-data-types). The engine uses this file to determine damage type calculations for item properties.

**Row index**: Item Property Value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| Additional columns | Various | Damage type mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:481`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L481) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:80`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L80) - HTInstallation constant

---

### iprp_protection.2da

**Engine Usage**: Maps item property values to protection/immunity types. The engine uses this file to determine protection calculations for item properties.

**Row index**: Item Property Value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| Additional columns | Various | Protection type mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:482`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L482) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:81`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L81) - HTInstallation constant

---

### iprp_acmodtype.2da

**Engine Usage**: Maps item property values to armor class modifier types. The engine uses this file to determine AC modifier calculations for item properties.

**Row index**: Item Property Value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| Additional columns | Various | AC modifier type mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:483`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L483) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:82`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L82) - HTInstallation constant

---

### iprp_immunity.2da

**Engine Usage**: Maps item property values to immunity types. The engine uses this file to determine immunity calculations for item properties.

**Row index**: Item Property Value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| Additional columns | Various | Immunity type mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:484`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L484) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:83`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L83) - HTInstallation constant

---

### iprp_saveelement.2da

**Engine Usage**: Maps item property values to saving throw element types. The engine uses this file to determine saving throw element calculations for item properties.

**Row index**: Item Property Value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| Additional columns | Various | Saving throw element mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:485`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L485) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:84`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L84) - HTInstallation constant

---

### iprp_savingthrow.2da

**Engine Usage**: Maps item property values to saving throw types. The engine uses this file to determine saving throw calculations for item properties.

**Row index**: Item Property Value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| Additional columns | Various | Saving throw type mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:486`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L486) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:85`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L85) - HTInstallation constant

---

### iprp_onhit.2da

**Engine Usage**: Maps item property values to on-hit effect types. The engine uses this file to determine on-hit effect calculations for item properties.

**Row index**: Item Property Value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| Additional columns | Various | On-hit effect mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:487`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L487) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:86`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L86) - HTInstallation constant

---

### iprp_ammotype.2da

**Engine Usage**: Maps item property values to ammunition type restrictions. The engine uses this file to determine ammunition type calculations for item properties.

**Row index**: Item Property Value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| Additional columns | Various | Ammunition type mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:488`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L488) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:87`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L87) - HTInstallation constant

---

### iprp_mosterhit.2da

**Engine Usage**: Maps item property values to monster hit effect types. The engine uses this file to determine monster hit effect calculations for item properties.

**Row index**: Item Property Value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| Additional columns | Various | Monster hit effect mappings |

**Note**: The filename contains a typo ("mosterhit" instead of "monsterhit") which is preserved in the game files.

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:489`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L489) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:88`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L88) - HTInstallation constant

---

### iprp_walk.2da

**Engine Usage**: Maps item property values to movement/walk speed modifiers. The engine uses this file to determine movement speed calculations for item properties.

**Row index**: Item Property Value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| Additional columns | Various | Movement speed mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:490`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L490) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:89`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L89) - HTInstallation constant

---

### iprp_lightcol.2da

**Engine Usage**: Maps item property values to light color configurations. The engine uses this file to determine light color settings for item properties.

**Row index**: Item Property Value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| Additional columns | Various | Light color mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:579`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L579) - [GFF](GFF-File-Format) field mapping: "LightColor" -> iprp_lightcol.2da

---

### iprp_monstdam.2da

**Engine Usage**: Maps item property values to monster damage bonuses. The engine uses this file to determine damage bonus calculations for monster weapons.

**Row index**: Item Property Value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| Additional columns | Various | Monster damage mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:580`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L580) - [GFF](GFF-File-Format) field mapping: "MonsterDamage" -> iprp_monstdam.2da

---

### difficultyopt.2da

**Engine Usage**: Defines difficulty options and their properties. The engine uses this file to determine difficulty settings, modifiers, and descriptions.

**Row index**: Difficulty Option ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Difficulty option label |
| `desc` | string | Difficulty description (e.g., "Default") |
| Additional columns | Various | Difficulty modifiers and properties |

**References**:

- [`vendor/KotOR.js/src/engine/rules/SWRuleSet.ts:66-74`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/engine/rules/SWRuleSet.ts#L66-L74) - Difficulty options initialization from [2DA](2DA-File-Format)

---

### xptable.2da

**Engine Usage**: Defines experience point reward calculations for defeating enemies. The engine uses this file to calculate how much XP to grant when a creature is defeated, based on the defeated creature's level and properties.

**Row index**: XP Table Entry ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | XP table entry label |
| Additional columns | Various | XP calculation parameters |

**Note**: This is different from `exptable.2da` which defines XP requirements for leveling up. `xptable.2da` defines XP rewards for defeating enemies.

**References**:

- [`vendor/KotOR.js/src/engine/rules/SWRuleSet.ts:89-95`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/engine/rules/SWRuleSet.ts#L89-L95) - XP table initialization from [2DA](2DA-File-Format)

---

### featgain.2da

**Engine Usage**: Defines feat gain progression by class and level. The engine uses this file to determine which feats [ARE](GFF-File-Format#are-area) available to each class at each level.

**Row index**: Feat Gain Entry ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Feat gain entry label |
| Additional columns | Various | Feat gain progression by class and level |

**References**:

- [`vendor/KotOR.js/src/engine/rules/SWRuleSet.ts:101-105`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/engine/rules/SWRuleSet.ts#L101-L105) - Feat gain initialization from [2DA](2DA-File-Format)

---

### effecticon.2da

**Engine Usage**: Defines effect icons displayed on character portraits and character sheets. The engine uses this file to determine which icon to display for status effects, buffs, and debuffs.

**Row index**: Effect Icon ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Effect icon label |
| Additional columns | Various | Effect icon properties and ResRefs |

**References**:

- [`vendor/KotOR.js/src/engine/rules/SWRuleSet.ts:143-150`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/engine/rules/SWRuleSet.ts#L143-L150) - Effect icon initialization from [2DA](2DA-File-Format)
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts:6441-6446`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts#L6441-L6446) - SetEffectIcon function
- [`vendor/NorthernLights/nwscript.nss:4678`](https://github.com/th3w1zard1/NorthernLights/blob/master/nwscript.nss#L4678) - Comment referencing effecticon.2da

---

### pazaakdecks.2da

**Engine Usage**: Defines Pazaak card decks for the Pazaak mini-game. The engine uses this file to determine which cards [ARE](GFF-File-Format#are-area) available in opponent decks and player decks.

**Row index**: Pazaak Deck ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Deck label |
| Additional columns | Various | Deck card definitions and properties |

**References**:

- [`vendor/KotOR.js/src/engine/rules/SWRuleSet.ts:178-185`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/engine/rules/SWRuleSet.ts#L178-L185) - Pazaak decks initialization from [2DA](2DA-File-Format)
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts:4438`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts#L4438) - StartPazaakGame function comment
- [`vendor/NorthernLights/nwscript.nss:3847`](https://github.com/th3w1zard1/NorthernLights/blob/master/nwscript.nss#L3847) - Comment referencing PazaakDecks.2da

---

### acbonus.2da

**Engine Usage**: Defines armor class bonus calculations. The engine uses this file to determine AC bonus values for different scenarios and calculations.

**Row index**: AC Bonus Entry ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | AC bonus entry label |
| Additional columns | Various | AC bonus calculation parameters |

**References**:

- [`vendor/KotOR.js/src/combat/CreatureClass.ts:302-304`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/combat/CreatureClass.ts#L302-L304) - AC bonus loading from [2DA](2DA-File-Format)
- [`Tools/HolocronToolset/src/toolset/data/installation.py:63`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L63) - HTInstallation.ACBONUS constant

---

### keymap.2da

**Engine Usage**: Defines keyboard and [controller](MDL-MDX-File-Format#controllers) [KEY](KEY-File-Format) mappings for different game contexts (in-game, [GUI](GFF-File-Format#gui-graphical-user-interface), dialog, minigame, etc.). The engine uses this file to determine which keys trigger which actions in different contexts.

**Row index**: Keymap Entry ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Keymap entry label |
| Additional columns | Various | [KEY](KEY-File-Format) mappings for different contexts (ingame, [GUI](GFF-File-Format#gui-graphical-user-interface), dialog, minigame, freelook, movie) |

**References**:

- [`vendor/KotOR.js/src/controls/KeyMapper.ts:293-299`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/controls/KeyMapper.ts#L293-L299) - Keymap initialization from [2DA](2DA-File-Format)

---

### poison.2da

**Engine Usage**: Defines poison effect types and their properties. The engine uses this file to determine poison effects, durations, and damage calculations.

**Row index**: Poison type ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Poison type label |
| Additional columns | Various | Poison effect properties, damage, and duration |

**References**:

- [`vendor/NorthernLights/nwscript.nss:949`](https://github.com/th3w1zard1/NorthernLights/blob/master/nwscript.nss#L949) - Comment referencing poison.2da constants
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts:3194-3199`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts#L3194-L3199) - EffectPoison function

---

### feedbacktext.2da

**Engine Usage**: Defines feedback text strings displayed to the player for various game events and actions. The engine uses this file to provide contextual feedback messages.

**Row index**: Feedback Text ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Feedback text label |
| Additional columns | Various | Feedback text strings and properties |

**References**:

- [`vendor/NorthernLights/nwscript.nss:3858`](https://github.com/th3w1zard1/NorthernLights/blob/master/nwscript.nss#L3858) - Comment referencing FeedBackText.2da
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts:4464-4465`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts#L4464-L4465) - DisplayFeedBackText function

---

### appearancesndset.2da

**Engine Usage**: Defines sound appearance types for creature appearances. The engine uses this file to determine which sound appearance type to use based on the creature's appearance.

**Row index**: Sound Appearance type ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Sound appearance type label |
| Additional columns | Various | Sound appearance type properties |

**References**:

- [`vendor/Kotor.NET/Kotor.NET/Tables/Appearance.cs:58-60`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Tables/Appearance.cs#L58-L60) - Comment referencing appearancesndset.2da for SoundAppTypeID

---

### texpacks.2da

**Engine Usage**: Defines [texture](TPC-File-Format) pack configurations for graphics settings (KotOR 2 only). The engine uses this file to determine available [texture](TPC-File-Format) pack options in the graphics menu.

**Row index**: [texture](TPC-File-Format) Pack ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | [texture](TPC-File-Format) pack label |
| `strrefname` | [StrRef](TLK-File-Format#string-references-strref) | string reference for [texture](TPC-File-Format) pack name |
| Additional columns | Various | [texture](TPC-File-Format) pack properties and settings |

**References**:

- [`vendor/KotOR.js/src/game/tsl/menu/MenuGraphicsAdvanced.ts:51-122`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/game/tsl/menu/MenuGraphicsAdvanced.ts#L51-L122) - [texture](TPC-File-Format) pack loading from [2DA](2DA-File-Format) for graphics menu (KotOR 2 only)
- [`vendor/KotOR.js/src/game/kotor/menu/MenuGraphicsAdvanced.ts:63-121`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/game/kotor/menu/MenuGraphicsAdvanced.ts#L63-L121) - [texture](TPC-File-Format) pack usage in KotOR 1 graphics menu

---

### loadscreens.2da

**Engine Usage**: Defines loading screen configurations for area transitions. The engine uses this file to determine which loading screen image, music, and hints to display when transitioning between areas.

**Row index**: Loading Screen ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Loading screen label |
| `bmpresref` | [ResRef](GFF-File-Format#gff-data-types) | Loading screen background image [ResRef](GFF-File-Format#gff-data-types) |
| `musicresref` | [ResRef](GFF-File-Format#gff-data-types) | Music track [ResRef](GFF-File-Format#gff-data-types) to play during loading |
| Additional columns | Various | Other loading screen properties |

**References**:

- [`vendor/KotOR.js/src/module/ModuleArea.ts:210`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleArea.ts#L210) - Comment referencing loadscreens.2da for area loading screen index
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:549`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L549) - [GFF](GFF-File-Format) field mapping: "LoadScreenID" -> loadscreens.2da

---

### fractionalcr.2da

**Engine Usage**: Defines fractional challenge rating configurations. The engine uses this file to determine fractional CR display strings.

**Row index**: Fractional CR ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Fractional CR label |
| `displaystrref` | [StrRef](TLK-File-Format#string-references-strref) | string reference for fractional CR display text |
| Additional columns | Various | Fractional CR properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:84`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L84) - [StrRef](TLK-File-Format#string-references-strref) column definition for fractionalcr.2da

---

### bindablekeys.2da

**Engine Usage**: Defines bindable [KEY](KEY-File-Format) actions and their string references. The engine uses this file to determine [KEY](KEY-File-Format) action names for the [KEY](KEY-File-Format) binding interface.

**Row index**: Bindable [KEY](KEY-File-Format) ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Bindable [KEY](KEY-File-Format) label |
| `keynamestrref` | [StrRef](TLK-File-Format#string-references-strref) | string reference for [KEY](KEY-File-Format) name |
| Additional columns | Various | [KEY](KEY-File-Format) binding properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:74`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L74) - [StrRef](TLK-File-Format#string-references-strref) column definition for bindablekeys.2da

---

### masterfeats.2da

**Engine Usage**: Defines master feat configurations. The engine uses this file to determine master feat names and properties.

**Row index**: Master Feat ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Master feat label |
| `strref` | [StrRef](TLK-File-Format#string-references-strref) | string reference for master feat name |
| Additional columns | Various | Master feat properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:138`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L138) - [StrRef](TLK-File-Format#string-references-strref) column definition for masterfeats.2da

---

### movies.2da

**Engine Usage**: Defines movie/cutscene configurations. The engine uses this file to determine movie names and descriptions.

**Row index**: Movie ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Movie label |
| `strrefname` | [StrRef](TLK-File-Format#string-references-strref) | string reference for movie name |
| `strrefdesc` | [StrRef](TLK-File-Format#string-references-strref) | string reference for movie description |
| Additional columns | Various | Movie properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:140`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L140) - [StrRef](TLK-File-Format#string-references-strref) column definitions for movies.2da

---

### stringtokens.2da

**Engine Usage**: Defines string token configurations. The engine uses this file to determine string token values for various game systems.

**Row index**: string Token ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | string token label |
| `strref1` through `strref4` | [StrRef](TLK-File-Format#string-references-strref) | string references for token values |
| Additional columns | Various | string token properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:144`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L144) - [StrRef](TLK-File-Format#string-references-strref) column definitions for stringtokens.2da

---

### disease.2da

**Engine Usage**: Defines disease effect configurations. The engine uses this file to determine disease names, scripts, and properties.

**Row index**: Disease ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Disease label |
| `name` | [StrRef](TLK-File-Format#string-references-strref) | string reference for disease name (KotOR 2) |
| `end_incu_script` | [ResRef](GFF-File-Format#gff-data-types) | Script [ResRef](GFF-File-Format#gff-data-types) for end incubation period |
| `24_hour_script` | [ResRef](GFF-File-Format#gff-data-types) | Script [ResRef](GFF-File-Format#gff-data-types) for 24-hour disease effect |
| Additional columns | Various | Disease properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:255`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L255) - [StrRef](TLK-File-Format#string-references-strref) column definition for disease.2da (KotOR 2)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:238,431`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L238) - Script [ResRef](GFF-File-Format#gff-data-types) column definitions for disease.2da

---

### droiddischarge.2da

**Engine Usage**: Defines droid discharge effect configurations. The engine uses this file to determine droid discharge properties.

**Row index**: Droid Discharge ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Droid discharge label |
| `>>##HEADER##<<` | [ResRef](GFF-File-Format#gff-data-types) | header [resource reference](GFF-File-Format#gff-data-types) |
| Additional columns | Various | Droid discharge properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:156`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L156) - [ResRef](GFF-File-Format#gff-data-types) column definition for droiddischarge.2da

---

### upcrystals.2da

**Engine Usage**: Defines upgrade crystal configurations. The engine uses this file to determine crystal [model](MDL-MDX-File-Format) variations for lightsaber upgrades.

**Row index**: Upgrade Crystal ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Upgrade crystal label |
| `shortmdlvar` | [ResRef](GFF-File-Format#gff-data-types) | Short [model](MDL-MDX-File-Format) variation [ResRef](GFF-File-Format#gff-data-types) |
| `longmdlvar` | [ResRef](GFF-File-Format#gff-data-types) | Long [model](MDL-MDX-File-Format) variation [ResRef](GFF-File-Format#gff-data-types) |
| `doublemdlvar` | [ResRef](GFF-File-Format#gff-data-types) | [double](GFF-File-Format#gff-data-types)-bladed [model](MDL-MDX-File-Format) variation [ResRef](GFF-File-Format#gff-data-types) |
| Additional columns | Various | Crystal properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:172`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L172) - [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definitions for upcrystals.2da

---

### grenadesnd.2da

**Engine Usage**: Defines grenade sound configurations. The engine uses this file to determine grenade sound effects.

**Row index**: Grenade Sound ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Grenade sound label |
| `sound` | [ResRef](GFF-File-Format#gff-data-types) | Sound [ResRef](GFF-File-Format#gff-data-types) for grenade |
| Additional columns | Various | Grenade sound properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:199`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L199) - Sound [ResRef](GFF-File-Format#gff-data-types) column definition for grenadesnd.2da

---

### inventorysnds.2da

**Engine Usage**: Defines inventory sound configurations. The engine uses this file to determine inventory sound effects for item interactions.

**Row index**: Inventory Sound ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Inventory sound label |
| `inventorysound` | [ResRef](GFF-File-Format#gff-data-types) | Inventory sound [ResRef](GFF-File-Format#gff-data-types) |
| Additional columns | Various | Inventory sound properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:201`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L201) - Sound [ResRef](GFF-File-Format#gff-data-types) column definition for inventorysnds.2da

---

## Implementation Details

### PyKotor Implementation

**Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/twoda/io_twoda.py:12-106`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/twoda/io_twoda.py#L12-L106)

**Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/twoda/io_twoda.py:109-174`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/twoda/io_twoda.py#L109-L174)

### Vendor Implementations

**reone** (C++):

- Reading: [`vendor/reone/src/libs/resource/format/2dareader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/2dareader.cpp)
- Writing: [`vendor/reone/src/libs/resource/format/2dawriter.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/2dawriter.cpp)
- data structure: [`vendor/reone/src/libs/resource/2da.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/2da.cpp)

**xoreos** (C++):

- Reading: [`vendor/xoreos/src/aurora/2dafile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/2dafile.cpp) - Generic Aurora engine 2DA format parser (shared across KotOR, Neverwinter Nights, and other Aurora engine games). The format structure is the same, but specific 2DA files and their columns [ARE](GFF-File-Format#are-area) KotOR-specific.

**KotOR-Unity** (C#):

- Reading: [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/2DAObject.cs:23-105`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/2DAObject.cs#L23-L105) - Complete 2DA reading implementation with column parsing, row indices, and cell data reading

**KotOR.js** (TypeScript):

- Reading: [`vendor/KotOR.js/src/resource/TwoDAObject.ts:69-145`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/TwoDAObject.ts#L69-L145) - Complete 2DA reading implementation
- Manager: [`vendor/KotOR.js/src/managers/TwoDAManager.ts:21-37`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/managers/TwoDAManager.ts#L21-L37) - 2DA table loading from game archives
- Usage: [`vendor/KotOR.js/src/talents/TalentFeat.ts:122-132`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/talents/TalentFeat.ts#L122-L132) - Feat loading from `feat.2da`

**Kotor.NET** (C#):

- structure: [`vendor/Kotor.NET/Kotor.NET/Formats/Kotor2DA/TwoDABinaryStructure.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/Kotor2DA/TwoDABinaryStructure.cs)

---

This documentation aims to provide a comprehensive overview of the KotOR 2DA file format, focusing on the detailed file structure and data formats used within the games.
