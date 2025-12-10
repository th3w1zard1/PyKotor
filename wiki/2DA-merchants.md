# merchants.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines merchant markup and markdown configurations for shop transactions. The engine uses this [file](GFF-File-Format) to determine buy/sell price multipliers for different merchant [types](GFF-File-Format#data-types).

**Row [index](2DA-File-Format#row-labels)**: Merchant [type](GFF-File-Format#data-types) ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Merchant [type](GFF-File-Format#data-types) label |
| Additional columns | Various | Markup and markdown price multipliers |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:564-565`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L564-L565) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure) mapping: "MarkUp" and "MarkDown" -> merchants.2da
- [`Libraries/PyKotor/src/pykotor/resource/generics/utm.py:54,60`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utm.py#L54) - Comments referencing merchants.2da for markup/markdown [values](GFF-File-Format#data-types)

---
