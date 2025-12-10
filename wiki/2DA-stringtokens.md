# stringtokens.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines [string](GFF-File-Format#cexostring) token configurations. The engine uses this [file](GFF-File-Format) to determine [string](GFF-File-Format#cexostring) token [values](GFF-File-Format#data-types) for various game systems.

**Row [index](2DA-File-Format#row-labels)**: [string](GFF-File-Format#cexostring) Token ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | [string](GFF-File-Format#cexostring) token label |
| `strref1` through `strref4` | [StrRef](TLK-File-Format#string-references-strref) | [string](GFF-File-Format#cexostring) references for token [values](GFF-File-Format#data-types) |
| Additional columns | Various | [string](GFF-File-Format#cexostring) token properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:144`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L144) - [StrRef](TLK-File-Format#string-references-strref) column definitions for stringtokens.2da

---
