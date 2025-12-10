# grenadesnd.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines grenade sound configurations. The engine uses this file to determine grenade sound effects.

**Row index**: Grenade Sound ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Grenade sound label |
| `sound` | [ResRef](GFF-File-Format#gff-data-types) | Sound [ResRef](GFF-File-Format#gff-data-types) for grenade |
| Additional columns | Various | Grenade sound properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:199`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L199) - Sound [ResRef](GFF-File-Format#gff-data-types) column definition for grenadesnd.2da

---
