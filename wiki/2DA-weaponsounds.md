# weaponsounds.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines sound effects for weapon attacks based on base item type. The engine uses this file to play appropriate weapon sounds during combat.

**Row index**: Base Item ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Base item label |
| Additional columns | [ResRef](GFF-File-Format#gff-data-types) | Sound effect ResRefs for different attack types |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:1819-1822`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L1819-L1822) - Weapon sound lookup from [2DA](2DA-File-Format)

---
