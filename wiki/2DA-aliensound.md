# aliensound.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines alien sound configurations. The engine uses this [file](GFF-File-Format) to determine alien sound effect filenames.

**Row [index](2DA-File-Format#row-labels)**: Alien Sound ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Alien sound label |
| `filename` | [ResRef](GFF-File-Format#gff-data-types) | Sound filename [ResRef](GFF-File-Format#gff-data-types) |
| Additional columns | Various | Alien sound properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:183`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L183) - Sound [ResRef](GFF-File-Format#gff-data-types) column definition for aliensound.2da

---
