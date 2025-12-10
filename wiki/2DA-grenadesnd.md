# grenadesnd.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines grenade sound configurations. The engine uses this [file](GFF-File-Format) to determine grenade sound effects.

**Row [index](2DA-File-Format#row-labels)**: Grenade Sound ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Grenade sound label |
| `sound` | [ResRef](GFF-File-Format#gff-data-types) | Sound [ResRef](GFF-File-Format#gff-data-types) for grenade |
| Additional columns | Various | Grenade sound properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:199`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L199) - Sound [ResRef](GFF-File-Format#gff-data-types) column definition for grenadesnd.2da

---
