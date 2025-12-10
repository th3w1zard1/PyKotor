# [textures](TPC-File-Format).2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines [texture](TPC-File-Format) variation configurations. The engine uses this [file](GFF-File-Format) to determine [texture](TPC-File-Format) variation assignments for objects that support [texture](TPC-File-Format) variations.

**Row [index](2DA-File-Format#row-labels)**: [texture](TPC-File-Format) Variation ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | [texture](TPC-File-Format) variation label |
| Additional columns | Various | [texture](TPC-File-Format) variation properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:540`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L540) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure) mapping: "TextureVar" -> [textures](TPC-File-Format).2da

---
