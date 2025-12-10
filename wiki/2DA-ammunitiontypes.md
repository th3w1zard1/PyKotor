# ammunitiontypes.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines ammunition [types](GFF-File-Format#data-types) for ranged weapons, including their [models](MDL-MDX-File-Format) and sound effects. The engine uses this [file](GFF-File-Format) when loading items to determine ammunition properties for ranged weapons.

**Row [index](2DA-File-Format#row-labels)**: Ammunition [type](GFF-File-Format#data-types) ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Ammunition [type](GFF-File-Format#data-types) label |
| `model` | [ResRef](GFF-File-Format#resref) | Ammunition [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#resref) |
| `shotsound0` | ResRef (optional) | Shot sound effect ResRef (variant 1) |
| `shotsound1` | ResRef (optional) | Shot sound effect ResRef (variant 2) |
| `impactsound0` | ResRef (optional) | Impact sound effect ResRef (variant 1) |
| `impactsound1` | ResRef (optional) | Impact sound effect ResRef (variant 2) |

**References**:

- [`vendor/reone/src/libs/game/object/item.cpp:164-171`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/item.cpp#L164-L171) - Ammunition [type](GFF-File-Format#data-types) loading from [2DA](2DA-File-Format)

---
