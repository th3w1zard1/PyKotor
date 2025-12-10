# actions.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines action types and their properties. The engine uses this file to determine action icons, descriptions, and behaviors for various in-game actions.

**Row index**: Action ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Action label |
| `string_ref` | [StrRef](TLK-File-Format#string-references-strref) | string reference for action description |
| `iconresref` | [ResRef](GFF-File-Format#gff-data-types) | Icon [ResRef](GFF-File-Format#gff-data-types) for the action |
| Additional columns | Various | Action properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:70`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L70) - [StrRef](TLK-File-Format#string-references-strref) column definition for actions.2da
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:212`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L212) - [texture](TPC-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definition for actions.2da

---
