# keymap.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines keyboard and [controller](MDL-MDX-File-Format#controllers) [KEY](KEY-File-Format) mappings for different game contexts (in-game, [GUI](GFF-File-Format#gui-graphical-user-interface), dialog, minigame, etc.). The engine uses this [file](GFF-File-Format) to determine which keys trigger which actions in different contexts.

**Row [index](2DA-File-Format#row-labels)**: Keymap Entry ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Keymap entry label |
| Additional columns | Various | [KEY](KEY-File-Format) mappings for different contexts (ingame, [GUI](GFF-File-Format#gui-graphical-user-interface), dialog, minigame, freelook, movie) |

**References**:

- [`vendor/KotOR.js/src/controls/KeyMapper.ts:293-299`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/controls/KeyMapper.ts#L293-L299) - Keymap initialization from [2DA](2DA-File-Format)

---
