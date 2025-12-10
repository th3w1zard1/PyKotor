# areaeffects.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines area effect configurations. The engine uses this [file](GFF-File-Format) to determine area effect scripts for enter, heartbeat, and exit events.

**Row [index](2DA-File-Format#row-labels)**: Area Effect ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Area effect label |
| `onenter` | [ResRef](GFF-File-Format#gff-data-types) | Script [ResRef](GFF-File-Format#gff-data-types) for on-enter event |
| `heartbeat` | [ResRef](GFF-File-Format#gff-data-types) | Script [ResRef](GFF-File-Format#gff-data-types) for heartbeat event |
| `onexit` | [ResRef](GFF-File-Format#gff-data-types) | Script [ResRef](GFF-File-Format#gff-data-types) for on-exit event |
| Additional columns | Various | Area effect properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:237`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L237) - Script [ResRef](GFF-File-Format#gff-data-types) column definitions for areaeffects.2da

---

## Additional Item Property [files](GFF-File-Format)

The following additional [2DA files](2DA-File-Format) [ARE](GFF-File-Format#are-area) used in KotOR games:

## Audio & Music

- `ambientmusic.2da`: Ambient music track definitions for areas
- `ambientsound.2da`: Ambient sound effect definitions for areas

## Item Property Cost Tables

The game uses numerous item property cost calculation tables. Common patterns include:

- `iprp_costtable.2da`: Base cost calculation tables for item properties
- `iprp_ammocost.2da`: Ammunition cost per shot (documented above)
- `iprp_damagecost.2da`: Damage bonus cost calculations (documented above)
- `iprp_onhit*.2da`: On-hit item property definitions and cost tables
- `iprp_onslash*.2da`: On-slash item property definitions and cost tables
- `iprp_onstab*.2da`: On-stab item property definitions and cost tables
- `iprp_oncrush*.2da`: On-crush item property definitions and cost tables
- `iprp_onunarmed*.2da`: On-unarmed item property definitions and cost tables
- `iprp_onranged*.2da`: On-ranged item property definitions and cost tables
- `iprp_onmonster*.2da`: On-monster-hit item property definitions and cost tables (for monster weapons)

Each attack [type](GFF-File-Format#gff-data-types) typically has multiple related [files](GFF-File-Format) for damage, properties, costs, durations, saving throws, and [value](GFF-File-Format#gff-data-types) calculations. Many of these [files](GFF-File-Format) have numbered variants (e.g., `iprp_onhitpropsvalue2.2da` through `iprp_onhitpropsvalue50.2da`) for different property [value](GFF-File-Format#gff-data-types) ranges.

**Note**: Some [2DA files](2DA-File-Format) may have variations between KotOR and KotOR 2. Always verify [file](GFF-File-Format) [structure](GFF-File-Format#file-structure-overview) against the specific game version. The reone dataminer tool can extract all [2DA files](2DA-File-Format) from game archives to analyze their [structure](GFF-File-Format#file-structure-overview).

**References**:

- [`vendor/reone/src/apps/dataminer/2daparsers.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/apps/dataminer/2daparsers.cpp) - Tool for extracting and analyzing all [2DA files](2DA-File-Format) from game archives

---

[2DA files](2DA-File-Format) [ARE](GFF-File-Format#are-area) the primary configuration mechanism for KotOR's game rules and content. Nearly every game system references at least one [2DA file](2DA-File-Format) for its behavior.

---
