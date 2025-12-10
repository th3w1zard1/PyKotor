# fractionalcr.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines fractional challenge rating configurations. The engine uses this file to determine fractional CR display strings.

**Row index**: Fractional CR ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Fractional CR label |
| `displaystrref` | [StrRef](TLK-File-Format#string-references-strref) | string reference for fractional CR display text |
| Additional columns | Various | Fractional CR properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:84`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L84) - [StrRef](TLK-File-Format#string-references-strref) column definition for fractionalcr.2da

---
