# footstepsounds.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines footstep sound effects for different surface [types](GFF-File-Format#data-types) and footstep [types](GFF-File-Format#data-types). The engine uses this [file](GFF-File-Format) to play appropriate footstep sounds based on the surface [material](MDL-MDX-File-Format#trimesh-header) and creature footstep [type](GFF-File-Format#data-types).

**Row [index](2DA-File-Format#row-labels)**: Footstep [type](GFF-File-Format#data-types) ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Footstep [type](GFF-File-Format#data-types) label |
| `dirt0`, `dirt1`, `dirt2` | ResRef (optional) | Dirt surface footstep sounds |
| `grass0`, `grass1`, `grass2` | ResRef (optional) | Grass surface footstep sounds |
| `stone0`, `stone1`, `stone2` | ResRef (optional) | Stone surface footstep sounds |
| `wood0`, `wood1`, `wood2` | ResRef (optional) | Wood surface footstep sounds |
| `water0`, `water1`, `water2` | ResRef (optional) | Water surface footstep sounds |
| `carpet0`, `carpet1`, `carpet2` | ResRef (optional) | Carpet surface footstep sounds |
| `metal0`, `metal1`, `metal2` | ResRef (optional) | Metal surface footstep sounds |
| `leaves0`, `leaves1`, `leaves2` | ResRef (optional) | Leaves surface footstep sounds |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:188-198`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L188-L198) - Sound [ResRef](GFF-File-Format#resref) column definitions for footstepsounds.2da (K1: rolling, dirt0-2, grass0-2, stone0-2, wood0-2, water0-2, carpet0-2, metal0-2, puddles0-2, leaves0-2, force1-3)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:380-390`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L380-L390) - Sound [ResRef](GFF-File-Format#resref) column definitions for footstepsounds.2da (K2: rolling, dirt0-2, grass0-2, stone0-2, wood0-2, water0-2, carpet0-2, metal0-2, puddles0-2, leaves0-2, force1-3)

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/footstepsounds.cpp:31-57`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/footstepsounds.cpp#L31-L57) - Footstep sounds loading from [2DA](2DA-File-Format)
- [`vendor/reone/src/libs/game/object/creature.cpp:106`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L106) - Footstep [type](GFF-File-Format#data-types) usage from [appearance.2da](2DA-appearance)

---
