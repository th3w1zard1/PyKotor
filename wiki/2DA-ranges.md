# ranges.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines perception ranges for creatures, including sight and hearing ranges. The engine uses this [file](GFF-File-Format) to determine how far creatures can see and hear.

**Row [index](2DA-File-Format#row-labels)**: Range ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Range label |
| `primaryrange` | Float | Primary perception range (sight range) |
| `secondaryrange` | Float | Secondary perception range (hearing range) |

**References**:

- [`vendor/reone/src/libs/game/object/creature.cpp:1398-1406`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L1398-L1406) - Perception range loading from [2DA](2DA-File-Format)
- [`vendor/KotOR.js/src/module/ModuleCreature.ts:3178-3187`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L3178-L3187) - Perception range access from [2DA](2DA-File-Format)

---
