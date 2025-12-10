# placeableobjsnds.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines sound effects for placeable objects based on sound appearance [type](GFF-File-Format#data-types). The engine uses this [file](GFF-File-Format) to play appropriate sounds when interacting with placeables.

**Row [index](2DA-File-Format#row-labels)**: Sound Appearance [type](GFF-File-Format#data-types) ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Sound appearance [type](GFF-File-Format#data-types) label |
| Additional columns | [ResRef](GFF-File-Format#resref) | Sound effect ResRefs for different interaction [types](GFF-File-Format#data-types) |

**References**:

- [`vendor/KotOR.js/src/module/ModulePlaceable.ts:387-389`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModulePlaceable.ts#L387-L389) - Placeable sound lookup from [2DA](2DA-File-Format)
- [`vendor/KotOR.js/src/module/ModuleDoor.ts:239-241`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleDoor.ts#L239-L241) - Door sound lookup from [2DA](2DA-File-Format)

---
