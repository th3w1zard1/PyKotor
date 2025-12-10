# acbonus.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines armor class bonus calculations. The engine uses this [file](GFF-File-Format) to determine AC bonus [values](GFF-File-Format#gff-data-types) for different scenarios and calculations.

**Row [index](2DA-File-Format#row-labels)**: AC Bonus Entry ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | AC bonus entry label |
| Additional columns | Various | AC bonus calculation parameters |

**References**:

- [`vendor/KotOR.js/src/combat/CreatureClass.ts:302-304`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/combat/CreatureClass.ts#L302-L304) - AC bonus loading from [2DA](2DA-File-Format)

---
