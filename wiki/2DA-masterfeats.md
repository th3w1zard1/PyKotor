# masterfeats.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines master feat configurations. The engine uses this [file](GFF-File-Format) to determine master feat names and properties.

**Row [index](2DA-File-Format#row-labels)**: Master Feat ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Master feat label |
| `strref` | [StrRef](TLK-File-Format#string-references-strref) | [string](GFF-File-Format#cexostring) reference for master feat name |
| Additional columns | Various | Master feat properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:138`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L138) - [StrRef](TLK-File-Format#string-references-strref) column definition for masterfeats.2da

---
