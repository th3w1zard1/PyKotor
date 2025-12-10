# weaponsounds.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines sound effects for weapon attacks based on base item [type](GFF-File-Format#gff-data-types). The engine uses this [file](GFF-File-Format) to play appropriate weapon sounds during combat.

**Row [index](2DA-File-Format#row-labels)**: Base Item ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Base item label |
| Additional columns | [ResRef](GFF-File-Format#gff-data-types) | Sound effect ResRefs for different attack [types](GFF-File-Format#gff-data-types) |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:1819-1822`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L1819-L1822) - Weapon sound lookup from [2DA](2DA-File-Format)

---
