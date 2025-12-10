# iprp_damagevs.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Maps item property [values](GFF-File-Format#data-types) to damage vs. specific creature [type](GFF-File-Format#data-types) bonuses. The engine uses this [file](GFF-File-Format) to determine damage bonuses against specific creature [types](GFF-File-Format#data-types).

**Row [index](2DA-File-Format#row-labels)**: Item Property Value (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Property [value](GFF-File-Format#data-types) label |
| Additional columns | Various | Damage vs. creature [type](GFF-File-Format#data-types) mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:574`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L574) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure) mapping: "DamageVsType" -> iprp_damagevs.2da

---
