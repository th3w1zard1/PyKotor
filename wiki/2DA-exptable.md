# exptable.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines experience point requirements for each character level. The engine uses this [file](GFF-File-Format) to determine when a character levels up based on accumulated experience.

**Row [index](2DA-File-Format#row-labels)**: Level (integer, typically 1-20)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Level label |
| Additional columns | Integer | Experience point requirements for leveling up |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:2926-2941`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L2926-L2941) - Experience table lookup from [2DA](2DA-File-Format)

---
