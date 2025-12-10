# musictable.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines music tracks available in the main menu music selection. The engine uses this [file](GFF-File-Format) to populate the music list in the options menu.

**Row [index](2DA-File-Format#row-labels)**: Music Track ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Music track label |
| Additional columns | Various | Music track properties and ResRefs |

**References**:

- [`vendor/KotOR.js/src/game/tsl/menu/MainMusic.ts:63-68`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/game/tsl/menu/MainMusic.ts#L63-L68) - Music table loading for main menu

---
