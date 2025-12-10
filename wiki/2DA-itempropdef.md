# [itempropdef.2da](2DA-itempropdef)

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines item property definitions and their base properties. This is the master table for all item properties in the game. The engine uses this [file](GFF-File-Format) to determine item property [types](GFF-File-Format#data-types), costs, and effects.

**Row [index](2DA-File-Format#row-labels)**: Item Property ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Property label |
| Additional columns | Various | Property definitions, costs, and parameters |

**Note**: This [file](GFF-File-Format) may be the same as or related to `itemprops.2da` documented earlier. The exact relationship between these [files](GFF-File-Format) may vary between KotOR 1 and 2.

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:475`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L475) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:74`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L74) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:107-111`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L107-L111) - Item property loading in item editor

---
