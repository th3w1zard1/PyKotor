# masterfeats.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines master feat configurations. The engine uses this file to determine master feat names and properties.

**Row index**: Master Feat ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Master feat label |
| `strref` | [StrRef](TLK-File-Format#string-references-strref) | string reference for master feat name |
| Additional columns | Various | Master feat properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:138`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L138) - [StrRef](TLK-File-Format#string-references-strref) column definition for masterfeats.2da

---
