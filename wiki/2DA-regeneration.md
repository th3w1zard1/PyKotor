# regeneration.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines regeneration rates for creatures in combat and non-combat states. The engine uses this [file](GFF-File-Format) to determine how quickly creatures regenerate hit points and Force points.

**Row [index](2DA-File-Format#row-labels)**: Regeneration State ID (integer, 0=combat, 1=non-combat)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Regeneration state label |
| Additional columns | [float](GFF-File-Format#float) | Regeneration rates for different resource [types](GFF-File-Format#data-types) |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:759`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L759) - Regeneration rate loading from [2DA](2DA-File-Format)

---
