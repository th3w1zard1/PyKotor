# iprp_mosterhit.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Maps item property [values](GFF-File-Format#data-types) to monster hit effect [types](GFF-File-Format#data-types). The engine uses this [file](GFF-File-Format) to determine monster hit effect calculations for item properties.

**Row [index](2DA-File-Format#row-labels)**: Item Property Value (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Property [value](GFF-File-Format#data-types) label |
| Additional columns | Various | Monster hit effect mappings |

**Note**: The filename contains a typo ("mosterhit" instead of "monsterhit") which is preserved in the game [files](GFF-File-Format).

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:489`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L489) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:88`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L88) - HTInstallation constant

---
