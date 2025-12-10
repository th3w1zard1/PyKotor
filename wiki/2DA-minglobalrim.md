# minglobalrim.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines minimum global RIM configurations. The engine uses this file to determine module [resource references](GFF-File-Format#gff-data-types).

**Row index**: Global RIM ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Global RIM label |
| `moduleresref` | [ResRef](GFF-File-Format#gff-data-types) | Module [resource reference](GFF-File-Format#gff-data-types) |
| Additional columns | Various | Global RIM properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:161`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L161) - [ResRef](GFF-File-Format#gff-data-types) column definition for minglobalrim.2da

---
