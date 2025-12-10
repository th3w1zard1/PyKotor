# inventorysnds.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines inventory sound configurations. The engine uses this [file](GFF-File-Format) to determine inventory sound effects for item interactions.

**Row [index](2DA-File-Format#row-labels)**: Inventory Sound ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Inventory sound label |
| `inventorysound` | [ResRef](GFF-File-Format#gff-data-types) | Inventory sound [ResRef](GFF-File-Format#gff-data-types) |
| Additional columns | Various | Inventory sound properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:201`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L201) - Sound [ResRef](GFF-File-Format#gff-data-types) column definition for inventorysnds.2da

---
