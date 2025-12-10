# fractionalcr.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines fractional challenge rating configurations. The engine uses this [file](GFF-File-Format) to determine fractional CR display [strings](GFF-File-Format#gff-data-types).

**Row [index](2DA-File-Format#row-labels)**: Fractional CR ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Fractional CR label |
| `displaystrref` | [StrRef](TLK-File-Format#string-references-strref) | [string](GFF-File-Format#gff-data-types) reference for fractional CR display text |
| Additional columns | Various | Fractional CR properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:84`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L84) - [StrRef](TLK-File-Format#string-references-strref) column definition for fractionalcr.2da

---
