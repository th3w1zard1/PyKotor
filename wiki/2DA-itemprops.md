# itemprops.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Master table defining all item property [types](GFF-File-Format#gff-data-types) available in the game. Each row represents a property type (damage bonuses, ability score bonuses, skill bonuses, etc.) with their cost calculations and effect parameters. The engine uses this [file](GFF-File-Format) to determine item property costs, effects, and availability.

**Row [index](2DA-File-Format#row-labels)**: Item property ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Property label |
| `name` | [StrRef](TLK-File-Format#string-references-strref) | [string](GFF-File-Format#gff-data-types) reference for property name |
| `costtable` | [string](GFF-File-Format#gff-data-types) | Cost calculation table reference |
| `param1` | [string](GFF-File-Format#gff-data-types) | Parameter 1 label |
| `param2` | [string](GFF-File-Format#gff-data-types) | Parameter 2 label |
| `subtype` | Integer | Property subtype identifier |
| `costvalue` | Integer | Base cost [value](GFF-File-Format#gff-data-types) |
| `param1value` | Integer | Parameter 1 default [value](GFF-File-Format#gff-data-types) |
| `param2value` | Integer | Parameter 2 default [value](GFF-File-Format#gff-data-types) |
| `description` | [StrRef](TLK-File-Format#string-references-strref) | Property description [string](GFF-File-Format#gff-data-types) reference |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:135`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L135) - [StrRef](TLK-File-Format#string-references-strref) column definition for itemprops.2da (K1: stringref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:313`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L313) - [StrRef](TLK-File-Format#string-references-strref) column definition for itemprops.2da (K2: stringref)

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:74`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L74) - HTInstallation.TwoDA_ITEM_PROPERTIES constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:107-111`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L107-L111) - itemprops.2da loading in [UTI](GFF-File-Format#uti-item) editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:278-287`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L278-L287) - itemprops.2da usage for property cost table and parameter lookups
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:449-465`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L449-L465) - itemprops.2da usage in property selection and loading

---
