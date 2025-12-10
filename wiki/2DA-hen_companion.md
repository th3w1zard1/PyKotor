# hen_companion.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines companion configurations (HEN - Henchman system). The engine uses this [file](GFF-File-Format) to determine companion names and base [resource references](GFF-File-Format#resref).

**Row [index](2DA-File-Format#row-labels)**: Companion ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Companion label |
| `strref` | [StrRef](TLK-File-Format#string-references-strref) | [string](GFF-File-Format#cexostring) reference for companion name |
| `baseresref` | [ResRef](GFF-File-Format#resref) | Base [resource reference](GFF-File-Format#resref) for companion (not used in game engine) |
| Additional columns | Various | Companion properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:87`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L87) - [StrRef](TLK-File-Format#string-references-strref) column definition for hen_companion.2da
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:157`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L157) - [ResRef](GFF-File-Format#resref) column definition for hen_companion.2da (baseresref, not used in engine)

---
