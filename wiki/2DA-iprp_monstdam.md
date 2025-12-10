# iprp_monstdam.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Maps item property [values](GFF-File-Format#data-types) to monster damage bonuses. The engine uses this [file](GFF-File-Format) to determine damage bonus calculations for monster weapons.

**Row [index](2DA-File-Format#row-labels)**: Item Property Value (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Property [value](GFF-File-Format#data-types) label |
| Additional columns | Various | Monster damage mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:580`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L580) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure) mapping: "MonsterDamage" -> iprp_monstdam.2da

---
