# credits.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines credits/acknowledgments configurations (KotOR 2 only). The engine uses this file to determine credits entries.

**Row index**: Credit ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Credit label |
| `name` | [StrRef](TLK-File-Format#string-references-strref) | string reference for credit name |
| Additional columns | Various | Credit properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:251`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L251) - [StrRef](TLK-File-Format#string-references-strref) column definition for credits.2da (KotOR 2 only)

---
