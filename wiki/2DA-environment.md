# environment.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines environment configurations for areas. The engine uses this [file](GFF-File-Format) to determine environment names and properties.

**Row [index](2DA-File-Format#row-labels)**: Environment ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Environment label |
| `strref` | [StrRef](TLK-File-Format#string-references-strref) | [string](GFF-File-Format#cexostring) reference for environment name |
| Additional columns | Various | Environment properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:81`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L81) - [StrRef](TLK-File-Format#string-references-strref) column definition for environment.2da

---
