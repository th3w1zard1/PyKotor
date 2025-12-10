# iprp_bonusfeat.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Maps item property [values](GFF-File-Format#gff-data-types) to bonus feat grants. The engine uses this [file](GFF-File-Format) to determine which feats [ARE](GFF-File-Format#are-area) granted by item properties.

**Row [index](2DA-File-Format#row-labels)**: Item Property Value (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Property [value](GFF-File-Format#gff-data-types) label |
| Additional columns | Various | Bonus feat mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:577`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L577) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure-overview) mapping: "BonusFeatID" -> iprp_bonusfeat.2da

---
