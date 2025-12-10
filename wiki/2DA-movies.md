# movies.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines movie/cutscene configurations. The engine uses this file to determine movie names and descriptions.

**Row index**: Movie ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Movie label |
| `strrefname` | [StrRef](TLK-File-Format#string-references-strref) | string reference for movie name |
| `strrefdesc` | [StrRef](TLK-File-Format#string-references-strref) | string reference for movie description |
| Additional columns | Various | Movie properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:140`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L140) - [StrRef](TLK-File-Format#string-references-strref) column definitions for movies.2da

---
