# bindablekeys.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines bindable [KEY](KEY-File-Format) actions and their string references. The engine uses this file to determine [KEY](KEY-File-Format) action names for the [KEY](KEY-File-Format) binding interface.

**Row index**: Bindable [KEY](KEY-File-Format) ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Bindable [KEY](KEY-File-Format) label |
| `keynamestrref` | [StrRef](TLK-File-Format#string-references-strref) | string reference for [KEY](KEY-File-Format) name |
| Additional columns | Various | [KEY](KEY-File-Format) binding properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:74`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L74) - [StrRef](TLK-File-Format#string-references-strref) column definition for bindablekeys.2da

---
