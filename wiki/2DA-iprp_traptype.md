# iprp_traptype.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Maps item property values to trap type configurations. The engine uses this file to determine trap type settings for item properties.

**Row index**: Item Property Value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| Additional columns | Various | Trap type mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:587`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L587) - [GFF](GFF-File-Format) field mapping: "Trap" -> iprp_traptype.2da

---
