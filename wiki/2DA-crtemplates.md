# crtemplates.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines [creature templates](GFF-File-Format#utc-creature) configurations. The engine uses this file to determine [creature templates](GFF-File-Format#utc-creature) names and properties.

**Row index**: [creature templates](GFF-File-Format#utc-creature) ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | [creature templates](GFF-File-Format#utc-creature) label |
| `strref` | [StrRef](TLK-File-Format#string-references-strref) | string reference for [creature templates](GFF-File-Format#utc-creature) name |
| Additional columns | Various | [creature templates](GFF-File-Format#utc-creature) properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:76`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L76) - [StrRef](TLK-File-Format#string-references-strref) column definition for crtemplates.2da

---
