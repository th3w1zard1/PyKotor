# phenotype.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines phenotype [types](GFF-File-Format#gff-data-types) for creatures. The engine uses this [file](GFF-File-Format) to determine creature phenotype classifications, which affect [model](MDL-MDX-File-Format) and [texture](TPC-File-Format) selection.

**Row [index](2DA-File-Format#row-labels)**: Phenotype ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Phenotype label |
| Additional columns | Various | Phenotype properties |

**References**:

- [`vendor/reone/src/libs/resource/parser/gff/utc.cpp:133`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/utc.cpp#L133) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure-overview) parsing: "Phenotype" from UTC (creature) templates
- [`vendor/KotOR.js/src/module/ModuleCreature.ts:118,4033,4689,4832`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L118) - Phenotype [field](GFF-File-Format#file-structure-overview) handling in creature module
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:525`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L525) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure-overview) mapping: "Phenotype" -> phenotype.2da

---
