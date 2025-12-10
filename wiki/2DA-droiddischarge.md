# droiddischarge.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines droid discharge effect configurations. The engine uses this [file](GFF-File-Format) to determine droid discharge properties.

**Row [index](2DA-File-Format#row-labels)**: Droid Discharge ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Droid discharge label |
| `>>##HEADER##<<` | [ResRef](GFF-File-Format#resref) | [header](GFF-File-Format#file-header) [resource reference](GFF-File-Format#resref) |
| Additional columns | Various | Droid discharge properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:156`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L156) - [ResRef](GFF-File-Format#resref) column definition for droiddischarge.2da

---
