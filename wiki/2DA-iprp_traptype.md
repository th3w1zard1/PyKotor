# iprp_traptype.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Maps item property [values](GFF-File-Format#gff-data-types) to trap [type](GFF-File-Format#gff-data-types) configurations. The engine uses this [file](GFF-File-Format) to determine trap [type](GFF-File-Format#gff-data-types) settings for item properties.

**Row [index](2DA-File-Format#row-labels)**: Item Property Value (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Property [value](GFF-File-Format#gff-data-types) label |
| Additional columns | Various | Trap [type](GFF-File-Format#gff-data-types) mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:587`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L587) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure-overview) mapping: "Trap" -> iprp_traptype.2da

---
