# dialoganimations.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Maps dialog [animation](MDL-MDX-File-Format#animation-header) ordinals to [animation](MDL-MDX-File-Format#animation-header) names for use in conversations. The engine uses this [file](GFF-File-Format) to determine which [animation](MDL-MDX-File-Format#animation-header) to play when a dialog line specifies an [animation](MDL-MDX-File-Format#animation-header) ordinal.

**Row [index](2DA-File-Format#row-labels)**: [animation](MDL-MDX-File-Format#animation-header) Index (integer, ordinal - 10000)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | [animation](MDL-MDX-File-Format#animation-header) label |
| `name` | [string](GFF-File-Format#cexostring) | [animation](MDL-MDX-File-Format#animation-header) name (used to look up [animation](MDL-MDX-File-Format#animation-header) in [model](MDL-MDX-File-Format)) |

**References**:

- [`vendor/reone/src/libs/game/gui/dialog.cpp:302-315`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/gui/dialog.cpp#L302-L315) - Dialog [animation](MDL-MDX-File-Format#animation-header) lookup from [2DA](2DA-File-Format)

---
