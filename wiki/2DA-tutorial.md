# tutorial.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines tutorial window tracking entries. The engine uses this [file](GFF-File-Format) to track which tutorial windows have been shown to the player.

**Row [index](2DA-File-Format#row-labels)**: Tutorial ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Tutorial label |
| Additional columns | Various | Tutorial window properties |

**References**:

- [`vendor/KotOR.js/src/managers/PartyManager.ts:180-187`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/managers/PartyManager.ts#L180-L187) - Tutorial window tracker initialization from [2DA](2DA-File-Format)
- [`vendor/KotOR.js/src/managers/PartyManager.ts:438`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/managers/PartyManager.ts#L438) - Tutorial table access

---
