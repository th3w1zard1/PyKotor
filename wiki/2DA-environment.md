# environment.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines environment configurations for areas. The engine uses this file to determine environment names and properties.

**Row index**: Environment ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Environment label |
| `strref` | [StrRef](TLK-File-Format#string-references-strref) | string reference for environment name |
| Additional columns | Various | Environment properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:81`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L81) - [StrRef](TLK-File-Format#string-references-strref) column definition for environment.2da

---
