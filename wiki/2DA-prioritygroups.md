# prioritygroups.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines priority groups for sound effects, determining which sounds take precedence when multiple sounds [ARE](GFF-File-Format#are-area) playing. The engine uses this [file](GFF-File-Format) to calculate sound priority [values](GFF-File-Format#data-types).

**Row [index](2DA-File-Format#row-labels)**: Priority Group ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Priority group label |
| `priority` | Integer | Priority value (higher = more important) |

**References**:

- [`vendor/reone/src/libs/game/object/sound.cpp:92-96`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/sound.cpp#L92-L96) - Priority group loading from [2DA](2DA-File-Format)

---
