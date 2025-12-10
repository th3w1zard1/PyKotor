# [classes.2da](2DA-classes)

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines character classes with their progression tables, skill point calculations, hit dice, saving throw progressions, and feat access. The engine uses this [file](GFF-File-Format) to determine class abilities, skill point allocation, and level progression mechanics.

**Row [index](2DA-File-Format#row-labels)**: Class ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Class label |
| `name` | [StrRef](TLK-File-Format#string-references-strref) | [string](GFF-File-Format#gff-data-types) reference for class name |
| `description` | [StrRef](TLK-File-Format#string-references-strref) | [string](GFF-File-Format#gff-data-types) reference for class description |
| `hitdie` | Integer | Hit dice size (d6, d8, d10, etc.) |
| `skillpointbase` | Integer | Base skill points per level |
| `skillpointbonus` | Integer | Intelligence bonus skill points |
| `attackbonus` | [string](GFF-File-Format#gff-data-types) | Attack bonus progression table reference |
| `savingthrow` | [string](GFF-File-Format#gff-data-types) | Saving throw progression table reference |
| `savingthrowtable` | [string](GFF-File-Format#gff-data-types) | Saving throw table filename |
| `spellgaintable` | [string](GFF-File-Format#gff-data-types) | Spell/Force power gain table reference |
| `spellknowntable` | [string](GFF-File-Format#gff-data-types) | Spell/Force power known table reference |
| `primaryability` | Integer | Primary ability score for class |
| `preferredalignment` | Integer | Preferred alignment |
| `alignrestrict` | Integer | Alignment restrictions |
| `classfeat` | Integer | Class-specific feat ID |
| `classskill` | Integer | Class skill [flags](GFF-File-Format#gff-data-types) |
| `skillpointmaxlevel` | Integer | Maximum level for skill point calculation |
| `spellcaster` | Integer | Spellcasting level (0 = non-caster) |
| `spellcastingtype` | Integer | Spellcasting [type](GFF-File-Format#gff-data-types) identifier |
| `spelllevel` | Integer | Maximum spell level |
| `spellbook` | ResRef (optional) | Spellbook [ResRef](GFF-File-Format#gff-data-types) |
| `icon` | [ResRef](GFF-File-Format#gff-data-types) | Class icon [ResRef](GFF-File-Format#gff-data-types) |
| `portrait` | ResRef (optional) | Class portrait [ResRef](GFF-File-Format#gff-data-types) |
| `startingfeat0` through `startingfeat9` | Integer (optional) | Starting feat IDs |
| `startingpack` | Integer (optional) | Starting equipment pack ID |
| `description` | [StrRef](TLK-File-Format#string-references-strref) | Class description [string](GFF-File-Format#gff-data-types) reference |

**Column Details** (from reone implementation):

The following columns [ARE](GFF-File-Format#are-area) accessed by the reone engine:

- `name`: [string](GFF-File-Format#gff-data-types) reference for class name
- `description`: [string](GFF-File-Format#gff-data-types) reference for class description
- `hitdie`: Hit dice [size](GFF-File-Format#file-structure-overview)
- `skillpointbase`: Base skill points per level
- `str`, `dex`, `con`, `int`, `wis`, `cha`: Default ability scores
- `skillstable`: Skills table reference (used to check class skills in `skills.2da`)
- `savingthrowtable`: Saving throw table reference (e.g., `cls_savthr_jedi_guardian`)
- `attackbonustable`: Attack bonus table reference (e.g., `cls_atk_jedi_guardian`)

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:75`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L75) - [StrRef](TLK-File-Format#string-references-strref) column definitions for [classes.2da](2DA-classes) (K1: name, description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:250`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L250) - [StrRef](TLK-File-Format#string-references-strref) column definitions for [classes.2da](2DA-classes) (K2: name, description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:463`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L463) - TwoDARegistry.CLASSES constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:531`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L531) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure-overview) mapping: "Class" -> [classes.2da](2DA-classes)

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:62`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L62) - HTInstallation.TwoDA_CLASSES constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utc.py:242`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utc.py#L242) - [classes.2da](2DA-classes) included in batch cache for [UTC](GFF-File-Format#utc-creature) editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/utc.py:256`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utc.py#L256) - [classes.2da](2DA-classes) loading from cache
- [`Tools/HolocronToolset/src/toolset/gui/editors/utc.py:291-298`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utc.py#L291-L298) - [classes.2da](2DA-classes) usage in class selection comboboxes and label population

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/d20/class.cpp:34-56`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/d20/class.cpp#L34-L56) - Class loading from [2DA](2DA-File-Format) with column access
- [`vendor/reone/src/libs/game/d20/class.cpp:58-86`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/d20/class.cpp#L58-L86) - Class skills, saving throws, and attack bonuses loading

---
