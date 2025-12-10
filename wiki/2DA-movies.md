# movies.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines movie/cutscene configurations. The engine uses this [file](GFF-File-Format) to determine movie names and descriptions.

**Row [index](2DA-File-Format#row-labels)**: Movie ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Movie label |
| `strrefname` | [StrRef](TLK-File-Format#string-references-strref) | [string](GFF-File-Format#cexostring) reference for movie name |
| `strrefdesc` | [StrRef](TLK-File-Format#string-references-strref) | [string](GFF-File-Format#cexostring) reference for movie description |
| Additional columns | Various | Movie properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:140`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L140) - [StrRef](TLK-File-Format#string-references-strref) column definitions for movies.2da

---
