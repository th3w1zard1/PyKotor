# iprp_feats.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Maps item property [values](GFF-File-Format#data-types) to feat bonuses. When an item grants a feat bonus, this table determines which feat is granted based on the property [value](GFF-File-Format#data-types).

**Row [index](2DA-File-Format#row-labels)**: Item property value (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Property [value](GFF-File-Format#data-types) label |
| `feat` | Integer | Feat ID granted by this property [value](GFF-File-Format#data-types) |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:102`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L102) - [StrRef](TLK-File-Format#string-references-strref) column definition for iprp_feats.2da (K1: name)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:280`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L280) - [StrRef](TLK-File-Format#string-references-strref) column definition for iprp_feats.2da (K2: name)

---
