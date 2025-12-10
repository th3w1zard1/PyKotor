# keymap.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines keyboard and [controller](MDL-MDX-File-Format#controllers) [KEY](KEY-File-Format) mappings for different game contexts (in-game, [GUI](GFF-File-Format#gui-graphical-user-interface), dialog, minigame, etc.). The engine uses this file to determine which keys trigger which actions in different contexts.

**Row index**: Keymap Entry ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Keymap entry label |
| Additional columns | Various | [KEY](KEY-File-Format) mappings for different contexts (ingame, [GUI](GFF-File-Format#gui-graphical-user-interface), dialog, minigame, freelook, movie) |

**References**:

- [`vendor/KotOR.js/src/controls/KeyMapper.ts:293-299`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/controls/KeyMapper.ts#L293-L299) - Keymap initialization from [2DA](2DA-File-Format)

---
