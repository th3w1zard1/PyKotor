# bodyvariation.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines body variation [types](GFF-File-Format#data-types) for items and creatures. The engine uses this [file](GFF-File-Format) to determine body variation assignments, which affect [model](MDL-MDX-File-Format) and [texture](TPC-File-Format) selection for equipped items.

**Row [index](2DA-File-Format#row-labels)**: Body Variation ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Body variation label |
| Additional columns | Various | Body variation properties |

**References**:

- [`vendor/reone/src/libs/resource/parser/gff/uti.cpp:45`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/uti.cpp#L45) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure) parsing: "BodyVariation" from UTI (item) templates
- [`vendor/reone/src/libs/resource/parser/gff/utc.cpp:87`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/utc.cpp#L87) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure) parsing: "BodyVariation" from UTC (creature) templates
- [`vendor/reone/src/libs/game/object/item.cpp:124,140,155`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/item.cpp#L124) - Body variation usage in item object
- [`vendor/KotOR.js/src/module/ModuleItem.ts:136`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleItem.ts#L136) - Body variation method in item module
- [`vendor/KotOR.js/src/module/ModuleCreature.ts:82,3908,4798`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L82) - Body variation [field](GFF-File-Format#file-structure) handling in creature module
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:539`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L539) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure) mapping: "BodyVariation" -> bodyvariation.2da

---
