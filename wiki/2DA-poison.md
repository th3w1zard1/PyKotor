# poison.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines poison effect [types](GFF-File-Format#gff-data-types) and their properties. The engine uses this [file](GFF-File-Format) to determine poison effects, durations, and damage calculations.

**Row [index](2DA-File-Format#row-labels)**: Poison [type](GFF-File-Format#gff-data-types) ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Poison [type](GFF-File-Format#gff-data-types) label |
| Additional columns | Various | Poison effect properties, damage, and duration |

**References**:

- [`vendor/NorthernLights/nwscript.nss:949`](https://github.com/th3w1zard1/NorthernLights/blob/master/nwscript.nss#L949) - Comment referencing poison.2da constants
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts:3194-3199`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts#L3194-L3199) - EffectPoison function

---
