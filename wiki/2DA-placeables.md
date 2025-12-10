# [placeables.2da](2DA-placeables)

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines placeable objects (containers, usable objects, interactive elements) with their [models](MDL-MDX-File-Format), properties, and behaviors. The engine uses this [file](GFF-File-Format) when loading placeable objects in areas, determining their [models](MDL-MDX-File-Format), hit detection, and interaction properties.

**Row [index](2DA-File-Format#row-labels)**: Placeable [type](GFF-File-Format#gff-data-types) ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | String (optional) | Placeable [type](GFF-File-Format#gff-data-types) label |
| `modelname` | ResRef (optional) | 3D [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) |
| `strref` | Integer | [string](GFF-File-Format#gff-data-types) reference for placeable name |
| `bodybag` | Boolean | Whether placeable can contain bodies |
| `canseeheight` | Float | Can-see height for line of sight |
| `hitcheck` | Boolean | Whether hit detection is enabled |
| `hostile` | Boolean | Whether placeable is hostile |
| `ignorestatichitcheck` | Boolean | Whether to ignore static hit checks |
| `lightcolor` | String (optional) | Light [color](GFF-File-Format#color) RGB [values](GFF-File-Format#gff-data-types) |
| `lightoffsetx` | String (optional) | Light X [offset](GFF-File-Format#file-structure-overview) |
| `lightoffsety` | String (optional) | Light Y [offset](GFF-File-Format#file-structure-overview) |
| `lightoffsetz` | String (optional) | Light Z [offset](GFF-File-Format#file-structure-overview) |
| `lowgore` | String (optional) | Low gore [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) |
| `noncull` | Boolean | Whether to disable culling |
| `preciseuse` | Boolean | Whether precise use is enabled |
| `shadowsize` | Boolean | Whether shadow [size](GFF-File-Format#file-structure-overview) is enabled |
| `soundapptype` | Integer (optional) | Sound appearance type |
| `usesearch` | Boolean | Whether placeable can be searched |

**Column Details**:

The complete column [structure](GFF-File-Format#file-structure-overview) is defined in reone's placeables parser:

- `label`: Optional label [string](GFF-File-Format#gff-data-types)
- `modelname`: 3D [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types)
- `strref`: [string](GFF-File-Format#gff-data-types) reference for placeable name
- `bodybag`: Boolean - whether placeable can contain bodies
- `canseeheight`: Float - can-see height for line of sight
- `hitcheck`: Boolean - whether hit detection is enabled
- `hostile`: Boolean - whether placeable is hostile
- `ignorestatichitcheck`: Boolean - whether to ignore static hit checks
- `lightcolor`: Optional [string](GFF-File-Format#gff-data-types) - light [color](GFF-File-Format#color) RGB [values](GFF-File-Format#gff-data-types)
- `lightoffsetx`: Optional [string](GFF-File-Format#gff-data-types) - light X [offset](GFF-File-Format#file-structure-overview)
- `lightoffsety`: Optional [string](GFF-File-Format#gff-data-types) - light Y [offset](GFF-File-Format#file-structure-overview)
- `lightoffsetz`: Optional [string](GFF-File-Format#gff-data-types) - light Z [offset](GFF-File-Format#file-structure-overview)
- `lowgore`: Optional [string](GFF-File-Format#gff-data-types) - low gore [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types)
- `noncull`: Boolean - whether to disable culling
- `preciseuse`: Boolean - whether precise use is enabled
- `shadowsize`: Boolean - whether shadow [size](GFF-File-Format#file-structure-overview) is enabled
- `soundapptype`: Optional integer - sound appearance type
- `usesearch`: Boolean - whether placeable can be searched

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:141`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L141) - [StrRef](TLK-File-Format#string-references-strref) column definition for [placeables.2da](2DA-placeables) (K1: [StrRef](TLK-File-Format#string-references-strref))
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:170`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L170) - [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definition for [placeables.2da](2DA-placeables) (K1: modelname)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:319`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L319) - [StrRef](TLK-File-Format#string-references-strref) column definition for [placeables.2da](2DA-placeables) (K2: [StrRef](TLK-File-Format#string-references-strref))
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:349`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L349) - [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definition for [placeables.2da](2DA-placeables) (K2: modelname)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:467`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L467) - TwoDARegistry.PLACEABLES constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:542`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L542) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure-overview) mapping: "Appearance" -> [placeables.2da](2DA-placeables)

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:66`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L66) - HTInstallation.TwoDA_PLACEABLES constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utp.py:52`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utp.py#L52) - [placeables.2da](2DA-placeables) cache initialization comment
- [`Tools/HolocronToolset/src/toolset/gui/editors/utp.py:62`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utp.py#L62) - [placeables.2da](2DA-placeables) cache loading
- [`Tools/HolocronToolset/src/toolset/gui/editors/utp.py:121-131`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utp.py#L121-L131) - [placeables.2da](2DA-placeables) usage in appearance selection combobox
- [`Tools/HolocronToolset/src/toolset/gui/editors/utp.py:471`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utp.py#L471) - [placeables.2da](2DA-placeables) usage for [model](MDL-MDX-File-Format) name lookup

**Vendor Implementations:**

- [`vendor/reone/src/libs/resource/parser/2da/placeables.cpp:29-49`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/2da/placeables.cpp#L29-L49) - Complete column parsing implementation with all column names
- [`vendor/reone/src/libs/game/object/placeable.cpp:59-60`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/placeable.cpp#L59-L60) - Placeable loading from [2DA](2DA-File-Format)

---
