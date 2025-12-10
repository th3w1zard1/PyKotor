# modulesave.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines which modules should be included in save games. The engine uses this [file](GFF-File-Format) to determine whether a module's state should be persisted when saving the game.

**Row [index](2DA-File-Format#row-labels)**: Module Index (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Module label |
| `modulename` | [string](GFF-File-Format#cexostring) | Module filename (e.g., "001ebo") |
| `includeInSave` | Boolean | Whether module state should be saved (0 = false, 1 = true) |

**References**:

- [`vendor/KotOR.js/src/module/Module.ts:663-669`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/Module.ts#L663-L669) - Module save inclusion check from [2DA](2DA-File-Format)

---
