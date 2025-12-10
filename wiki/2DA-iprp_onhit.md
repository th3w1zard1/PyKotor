# iprp_onhit.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Maps item property [values](GFF-File-Format#gff-data-types) to on-hit effect [types](GFF-File-Format#gff-data-types). The engine uses this [file](GFF-File-Format) to determine on-hit effect calculations for item properties.

**Row [index](2DA-File-Format#row-labels)**: Item Property Value (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Property [value](GFF-File-Format#gff-data-types) label |
| Additional columns | Various | On-hit effect mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:487`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L487) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:86`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L86) - HTInstallation constant

---
