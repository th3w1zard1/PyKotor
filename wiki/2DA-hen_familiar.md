# hen_familiar.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines familiar configurations (HEN - Henchman system). The engine uses this [file](GFF-File-Format) to determine familiar base resource references (not used in game engine).

**Row [index](2DA-File-Format#row-labels)**: Familiar ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Familiar label |
| `baseresref` | [ResRef](GFF-File-Format#resref) | Base [resource reference](GFF-File-Format#resref) for familiar (not used in game engine) |
| Additional columns | Various | Familiar properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:158`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L158) - [ResRef](GFF-File-Format#resref) column definition for hen_familiar.2da (baseresref, not used in engine)

---
