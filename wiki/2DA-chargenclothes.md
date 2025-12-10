# chargenclothes.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines character generation clothing configurations. The engine uses this [file](GFF-File-Format) to determine starting clothing items for character creation.

**Row [index](2DA-File-Format#row-labels)**: Character Generation Clothes ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Character generation clothes label |
| `itemresref` | [ResRef](GFF-File-Format#resref) | Item [resource reference](GFF-File-Format#resref) for clothing |
| Additional columns | Various | Character generation clothes properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:226,419`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L226) - Item [ResRef](GFF-File-Format#resref) column definition for chargenclothes.2da

---
