# hen_companion.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines companion configurations (HEN - Henchman system). The engine uses this file to determine companion names and base [resource references](GFF-File-Format#gff-data-types).

**Row index**: Companion ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Companion label |
| `strref` | [StrRef](TLK-File-Format#string-references-strref) | string reference for companion name |
| `baseresref` | [ResRef](GFF-File-Format#gff-data-types) | Base [resource reference](GFF-File-Format#gff-data-types) for companion (not used in game engine) |
| Additional columns | Various | Companion properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:87`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L87) - [StrRef](TLK-File-Format#string-references-strref) column definition for hen_companion.2da
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:157`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L157) - [ResRef](GFF-File-Format#gff-data-types) column definition for hen_companion.2da (baseresref, not used in engine)

---
