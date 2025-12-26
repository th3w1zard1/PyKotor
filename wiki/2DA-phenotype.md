# phenotype.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines phenotype types for creatures. The engine uses this file to determine creature phenotype classifications, which affect [model](MDL-MDX-File-Format) and [texture](TPC-File-Format) selection.

**Row index**: Phenotype ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Phenotype label |
| Additional columns | Various | Phenotype properties |

**References**:

- [`vendor/reone/src/libs/resource/parser/gff/utc.cpp:133`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/gff/utc.cpp#L133) - [GFF](GFF-File-Format) field parsing: "Phenotype" from UTC (creature) templates
- [`vendor/KotOR.js/src/module/ModuleCreature.ts:118,4033,4689,4832`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleCreature.ts#L118) - Phenotype field handling in creature module
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:525`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L525) - [GFF](GFF-File-Format) field mapping: "Phenotype" -> phenotype.2da

---
