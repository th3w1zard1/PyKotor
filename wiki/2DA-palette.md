# palette.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines palette configurations for placeable objects, items, and other game objects. The engine uses this [file](GFF-File-Format) to determine [color](GFF-File-Format#color) palette assignments for objects that support palette variations.

**Row [index](2DA-File-Format#row-labels)**: Palette ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Palette label |
| Additional columns | Various | Palette [color](GFF-File-Format#color) definitions and properties |

**References**:

- [`vendor/reone/src/libs/resource/parser/gff/utw.cpp:38`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/utw.cpp#L38) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure) parsing: "PaletteID" from UTW (waypoint) templates
- [`vendor/reone/src/libs/resource/parser/gff/utt.cpp:44`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/utt.cpp#L44) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure) parsing: "PaletteID" from UTT (trigger) templates
- [`vendor/reone/src/libs/resource/parser/gff/uts.cpp:47`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/uts.cpp#L47) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure) parsing: "PaletteID" from UTS (sound) templates
- [`vendor/reone/src/libs/resource/parser/gff/utp.cpp:84`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/utp.cpp#L84) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure) parsing: "PaletteID" from UTP (placeable) templates
- [`vendor/reone/src/libs/resource/parser/gff/uti.cpp:54`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/uti.cpp#L54) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure) parsing: "PaletteID" from UTI (item) templates
- [`vendor/reone/src/libs/resource/parser/gff/ute.cpp:55`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/ute.cpp#L55) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure) parsing: "PaletteID" from UTE (encounter) templates
- [`vendor/reone/src/libs/resource/parser/gff/utd.cpp:73`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/utd.cpp#L73) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure) parsing: "PaletteID" from UTD (door) templates
- [`vendor/reone/src/libs/resource/parser/gff/utc.cpp:130`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/utc.cpp#L130) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure) parsing: "PaletteID" from UTC (creature) templates
- [`vendor/KotOR.js/src/module/ModulePlaceable.ts:71,813,1152`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModulePlaceable.ts#L71) - PaletteID [field](GFF-File-Format#file-structure) handling in placeable module
- [`vendor/KotOR.js/src/module/ModuleItem.ts:745`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleItem.ts#L745) - PaletteID [field](GFF-File-Format#file-structure) handling in item module
- [`vendor/KotOR.js/src/module/ModuleDoor.ts:76,1088,1413`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleDoor.ts#L76) - PaletteID [field](GFF-File-Format#file-structure) handling in door module
- [`vendor/KotOR.js/src/module/ModuleEncounter.ts:52,383`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleEncounter.ts#L52) - PaletteID [field](GFF-File-Format#file-structure) handling in encounter module
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:535`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L535) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure) mapping: "PaletteID" -> palette.2da

---
