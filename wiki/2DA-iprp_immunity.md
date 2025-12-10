# iprp_immunity.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Maps item property [values](GFF-File-Format#data-types) to immunity [types](GFF-File-Format#data-types). The engine uses this [file](GFF-File-Format) to determine immunity calculations for item properties.

**Row [index](2DA-File-Format#row-labels)**: Item Property Value (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Property [value](GFF-File-Format#data-types) label |
| Additional columns | Various | Immunity [type](GFF-File-Format#data-types) mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:484`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L484) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:83`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L83) - HTInstallation constant

---
