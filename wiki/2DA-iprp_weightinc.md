# iprp_weightinc.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Maps item property [values](GFF-File-Format#data-types) to weight increase calculations. The engine uses this [file](GFF-File-Format) to determine weight increase calculations for item properties.

**Row [index](2DA-File-Format#row-labels)**: Item Property Value (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Property [value](GFF-File-Format#data-types) label |
| `name` | [StrRef](TLK-File-Format#string-references-strref) | [string](GFF-File-Format#cexostring) reference for property name |
| Additional columns | Various | Weight increase mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:133,311`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L133) - [StrRef](TLK-File-Format#string-references-strref) column definition for iprp_weightinc.2da
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:586`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L586) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure) mapping: "WeightIncrease" -> iprp_weightinc.2da

---
