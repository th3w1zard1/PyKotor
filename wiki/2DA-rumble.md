# rumble.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines rumble/vibration patterns for [controller](MDL-MDX-File-Format#controllers) feedback. The engine uses this [file](GFF-File-Format) to determine rumble patterns for camera shake and [controller](MDL-MDX-File-Format#controllers) vibration effects.

**Row [index](2DA-File-Format#row-labels)**: Rumble Pattern ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Rumble pattern label |
| `lsamples` | Integer | Left channel sample [count](GFF-File-Format#file-structure-overview) |
| `rsamples` | Integer | Right channel sample [count](GFF-File-Format#file-structure-overview) |
| Additional columns | Various | Rumble pattern [data](GFF-File-Format#file-structure-overview) |

**References**:

- [`vendor/KotOR.js/src/managers/CameraShakeManager.ts:46`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/managers/CameraShakeManager.ts#L46) - Rumble pattern loading from [2DA](2DA-File-Format)
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts:4500-4515`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts#L4500-L4515) - PlayRumblePattern and StopRumblePattern functions

---
