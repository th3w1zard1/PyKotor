# genericdoors.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

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

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:78`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L78) - [StrRef](TLK-File-Format#string-references-strref) column definition for [doortypes.2da](2DA-doortypes) (K1: stringrefgame)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:86`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L86) - [StrRef](TLK-File-Format#string-references-strref) column definition for genericdoors.2da (K1: [StrRef](TLK-File-Format#string-references-strref))
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:177`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L177) - [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definition for [doortypes.2da](2DA-doortypes) (K1: [model](MDL-MDX-File-Format))
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:178`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L178) - [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definition for genericdoors.2da (K1: modelname)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:256`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L256) - [StrRef](TLK-File-Format#string-references-strref) column definition for [doortypes.2da](2DA-doortypes) (K2: stringrefgame)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:264`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L264) - [StrRef](TLK-File-Format#string-references-strref) column definition for genericdoors.2da (K2: [StrRef](TLK-File-Format#string-references-strref))
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:356`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L356) - [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definition for [doortypes.2da](2DA-doortypes) (K2: [model](MDL-MDX-File-Format))
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:357`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L357) - [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definition for genericdoors.2da (K2: modelname)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:468`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L468) - TwoDARegistry.DOORS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:543`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L543) - [GFF](GFF-File-Format) field mapping: "GenericType" -> genericdoors.2da

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:67`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L67) - HTInstallation.TwoDA_DOORS constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utd.py:60`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utd.py#L60) - genericdoors.2da cache loading
- [`Tools/HolocronToolset/src/toolset/gui/editors/utd.py:117-123`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utd.py#L117-L123) - genericdoors.2da usage in appearance selection combobox
- [`Tools/HolocronToolset/src/toolset/gui/editors/utd.py:409`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utd.py#L409) - genericdoors.2da usage for [model](MDL-MDX-File-Format) name lookup

**Vendor Implementations:**

- [`vendor/reone/src/libs/resource/parser/2da/genericdoors.cpp:29-41`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/2da/genericdoors.cpp#L29-L41) - Complete column parsing implementation with all column names
- [`vendor/reone/src/libs/game/object/door.cpp:66-67`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/door.cpp#L66-L67) - Door loading from [2DA](2DA-File-Format)

---
