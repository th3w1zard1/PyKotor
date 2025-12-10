# classpowergain.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines Force power progression by class and level. The engine uses this [file](GFF-File-Format) to determine which Force powers [ARE](GFF-File-Format#are-area) available to each class at each level.

**Row [index](2DA-File-Format#row-labels)**: Level (integer, typically 1-20)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `level` | Integer | Character level |
| `jedi_guardian` | Integer | Jedi Guardian power gain |
| `jedi_consular` | Integer | Jedi Consular power gain |
| `jedi_sentinel` | Integer | Jedi Sentinel power gain |
| `soldier` | Integer | Soldier power gain |
| `scout` | Integer | Scout power gain |
| `scoundrel` | Integer | Scoundrel power gain |
| `jedi_guardian_prestige` | Integer (optional) | Jedi Guardian prestige power gain |
| `jedi_consular_prestige` | Integer (optional) | Jedi Consular prestige power gain |
| `jedi_sentinel_prestige` | Integer (optional) | Jedi Sentinel prestige power gain |

---
