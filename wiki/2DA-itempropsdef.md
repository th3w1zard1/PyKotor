# itempropsdef.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines item property definitions and their base properties. This is the master table for all item properties in the game. The engine uses this [file](GFF-File-Format) to determine item property [types](GFF-File-Format#gff-data-types), costs, and effects.

**Row [index](2DA-File-Format#row-labels)**: Item Property ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Property label |
| Additional columns | Various | Property definitions, costs, and parameters |

**Note**: This [file](GFF-File-Format) may be the same as or related to `itempropdef.2da` and `itemprops.2da` documented earlier. The exact relationship between these [files](GFF-File-Format) may vary between KotOR 1 and 2.

**References**:

- [`vendor/KotOR.js/src/engine/rules/SWRuleSet.ts:167-173`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/engine/rules/SWRuleSet.ts#L167-L173) - Item properties initialization from [2DA](2DA-File-Format)

---
