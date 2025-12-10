# aliensound.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines alien sound configurations. The engine uses this file to determine alien sound effect filenames.

**Row index**: Alien Sound ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Alien sound label |
| `filename` | [ResRef](GFF-File-Format#gff-data-types) | Sound filename [ResRef](GFF-File-Format#gff-data-types) |
| Additional columns | Various | Alien sound properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:183`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L183) - Sound [ResRef](GFF-File-Format#gff-data-types) column definition for aliensound.2da

---
