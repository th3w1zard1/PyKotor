# iprp_damagecost.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines cost calculations for damage bonus item properties. Used to determine item property costs based on damage bonus [values](GFF-File-Format#data-types).

**Row [index](2DA-File-Format#row-labels)**: Damage bonus value (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Damage bonus label |
| `cost` | Integer | Cost for this damage bonus [value](GFF-File-Format#data-types) |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:99`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L99) - [StrRef](TLK-File-Format#string-references-strref) column definition for iprp_damagecost.2da (K1: name)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:277`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L277) - [StrRef](TLK-File-Format#string-references-strref) column definition for iprp_damagecost.2da (K2: name)

---
