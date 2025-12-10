# credits.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines credits/acknowledgments configurations (KotOR 2 only). The engine uses this [file](GFF-File-Format) to determine credits entries.

**Row [index](2DA-File-Format#row-labels)**: Credit ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Credit label |
| `name` | [StrRef](TLK-File-Format#string-references-strref) | [string](GFF-File-Format#gff-data-types) reference for credit name |
| Additional columns | Various | Credit properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:251`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L251) - [StrRef](TLK-File-Format#string-references-strref) column definition for credits.2da (KotOR 2 only)

---
