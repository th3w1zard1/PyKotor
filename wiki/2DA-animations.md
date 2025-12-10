# [animations](MDL-MDX-File-Format#animation-header).2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines [animation](MDL-MDX-File-Format#animation-header) names and properties for creatures and objects. The engine uses this [file](GFF-File-Format) to map [animation](MDL-MDX-File-Format#animation-header) IDs to [animation](MDL-MDX-File-Format#animation-header) names for playback.

**Row [index](2DA-File-Format#row-labels)**: [animation](MDL-MDX-File-Format#animation-header) ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | [animation](MDL-MDX-File-Format#animation-header) label |
| `name` | [string](GFF-File-Format#cexostring) | [animation](MDL-MDX-File-Format#animation-header) name (used to look up [animation](MDL-MDX-File-Format#animation-header) in [model](MDL-MDX-File-Format)) |

**References**:

- [`vendor/KotOR.js/src/module/ModuleCreature.ts:1474-1482`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L1474-L1482) - [animation](MDL-MDX-File-Format#animation-header) lookup from [2DA](2DA-File-Format)
- [`vendor/KotOR.js/src/module/ModulePlaceable.ts:1063-1103`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModulePlaceable.ts#L1063-L1103) - Placeable [animation](MDL-MDX-File-Format#animation-header) lookup from [2DA](2DA-File-Format)
- [`vendor/KotOR.js/src/module/ModuleDoor.ts:1343-1365`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleDoor.ts#L1343-L1365) - Door [animation](MDL-MDX-File-Format#animation-header) lookup from [2DA](2DA-File-Format)

---
