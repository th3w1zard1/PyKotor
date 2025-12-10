# loadscreens.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines loading screen configurations for area transitions. The engine uses this [file](GFF-File-Format) to determine which loading screen image, music, and hints to display when transitioning between areas.

**Row [index](2DA-File-Format#row-labels)**: Loading Screen ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Loading screen label |
| `bmpresref` | [ResRef](GFF-File-Format#resref) | Loading screen background image [ResRef](GFF-File-Format#resref) |
| `musicresref` | [ResRef](GFF-File-Format#resref) | Music track [ResRef](GFF-File-Format#resref) to play during loading |
| Additional columns | Various | Other loading screen properties |

**References**:

- [`vendor/KotOR.js/src/module/ModuleArea.ts:210`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleArea.ts#L210) - Comment referencing loadscreens.2da for area loading screen [index](2DA-File-Format#row-labels)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:549`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L549) - [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure) mapping: "LoadScreenID" -> loadscreens.2da

---
