# aiscripts.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines AI script templates and their properties. The engine uses this file to determine AI script names and descriptions (KotOR 1 only; KotOR 2 uses `name_strref` only).

**Row index**: AI Script ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | AI script label |
| `name_strref` | [StrRef](TLK-File-Format#string-references-strref) | string reference for AI script name |
| `description_strref` | [StrRef](TLK-File-Format#string-references-strref) | string reference for AI script description (KotOR 1 only) |
| Additional columns | Various | AI script properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:71`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L71) - [StrRef](TLK-File-Format#string-references-strref) column definitions for aiscripts.2da (K1: name_strref, description_strref; K2: name_strref only)

---
