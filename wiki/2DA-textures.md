# [textures](TPC-File-Format).2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines [texture](TPC-File-Format) variation configurations. The engine uses this file to determine [texture](TPC-File-Format) variation assignments for objects that support [texture](TPC-File-Format) variations.

**Row index**: [texture](TPC-File-Format) Variation ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | [texture](TPC-File-Format) variation label |
| Additional columns | Various | [texture](TPC-File-Format) variation properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:540`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L540) - [GFF](GFF-File-Format) field mapping: "TextureVar" -> [textures](TPC-File-Format).2da

---
