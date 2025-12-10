# chargenclothes.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines character generation clothing configurations. The engine uses this [file](GFF-File-Format) to determine starting clothing items for character creation.

**Row [index](2DA-File-Format#row-labels)**: Character Generation Clothes ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Character generation clothes label |
| `itemresref` | [ResRef](GFF-File-Format#gff-data-types) | Item [resource reference](GFF-File-Format#gff-data-types) for clothing |
| Additional columns | Various | Character generation clothes properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:226,419`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L226) - Item [ResRef](GFF-File-Format#gff-data-types) column definition for chargenclothes.2da

---
