# iprp_ammocost.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines ammunition cost per shot for ranged weapons. Used to calculate ammunition consumption rates.

**Row [index](2DA-File-Format#row-labels)**: Ammunition [type](GFF-File-Format#data-types) ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Ammunition [type](GFF-File-Format#data-types) label |
| `cost` | Integer | Ammunition cost per shot |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:92`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L92) - [StrRef](TLK-File-Format#string-references-strref) column definition for iprp_ammocost.2da (K1: name)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:270`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L270) - [StrRef](TLK-File-Format#string-references-strref) column definition for iprp_ammocost.2da (K2: name)

---
