# merchants.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines merchant markup and markdown configurations for shop transactions. The engine uses this file to determine buy/sell price multipliers for different merchant types.

**Row index**: Merchant type ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Merchant type label |
| Additional columns | Various | Markup and markdown price multipliers |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:564-565`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L564-L565) - [GFF](GFF-File-Format) field mapping: "MarkUp" and "MarkDown" -> merchants.2da
- [`Libraries/PyKotor/src/pykotor/resource/generics/utm.py:54,60`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utm.py#L54) - Comments referencing merchants.2da for markup/markdown values

---
