# minglobalrim.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines minimum global RIM configurations. The engine uses this [file](GFF-File-Format) to determine module [resource references](GFF-File-Format#resref).

**Row [index](2DA-File-Format#row-labels)**: Global RIM ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Global RIM label |
| `moduleresref` | [ResRef](GFF-File-Format#resref) | Module [resource reference](GFF-File-Format#resref) |
| Additional columns | Various | Global RIM properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:161`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L161) - [ResRef](GFF-File-Format#resref) column definition for minglobalrim.2da

---
