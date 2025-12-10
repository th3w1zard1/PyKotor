# iprp_savingthrow.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Maps item property [values](GFF-File-Format#data-types) to saving throw [types](GFF-File-Format#data-types). The engine uses this [file](GFF-File-Format) to determine saving throw calculations for item properties.

**Row [index](2DA-File-Format#row-labels)**: Item Property Value (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Property [value](GFF-File-Format#data-types) label |
| Additional columns | Various | Saving throw [type](GFF-File-Format#data-types) mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:486`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L486) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:85`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L85) - HTInstallation constant

---
