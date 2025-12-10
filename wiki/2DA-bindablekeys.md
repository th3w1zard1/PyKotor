# bindablekeys.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines bindable [KEY](KEY-File-Format) actions and their [string](GFF-File-Format#gff-data-types) references. The engine uses this [file](GFF-File-Format) to determine [KEY](KEY-File-Format) action names for the [KEY](KEY-File-Format) binding interface.

**Row [index](2DA-File-Format#row-labels)**: Bindable [KEY](KEY-File-Format) ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Bindable [KEY](KEY-File-Format) label |
| `keynamestrref` | [StrRef](TLK-File-Format#string-references-strref) | [string](GFF-File-Format#gff-data-types) reference for [KEY](KEY-File-Format) name |
| Additional columns | Various | [KEY](KEY-File-Format) binding properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:74`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L74) - [StrRef](TLK-File-Format#string-references-strref) column definition for bindablekeys.2da

---
