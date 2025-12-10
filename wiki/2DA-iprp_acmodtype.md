# iprp_acmodtype.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Maps item property [values](GFF-File-Format#gff-data-types) to armor class modifier [types](GFF-File-Format#gff-data-types). The engine uses this [file](GFF-File-Format) to determine AC modifier calculations for item properties.

**Row [index](2DA-File-Format#row-labels)**: Item Property Value (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Property [value](GFF-File-Format#gff-data-types) label |
| Additional columns | Various | AC modifier [type](GFF-File-Format#gff-data-types) mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:483`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L483) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:82`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L82) - HTInstallation constant

---
