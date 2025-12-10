# ai_styles.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines AI behavior styles for creatures. The engine uses this [file](GFF-File-Format) to determine AI behavior patterns and combat strategies.

**Row [index](2DA-File-Format#row-labels)**: AI Style ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | AI style label |
| Additional columns | Various | AI behavior parameters |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:572`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L572) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure) mapping: "AIStyle" -> ai_styles.2da

---
