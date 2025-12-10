# cls_atk_*.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Base attack bonus progression tables for each class. [files](GFF-File-Format) [ARE](GFF-File-Format#are-area) named `cls_atk_<classname>.2da` (e.g., `cls_atk_jedi_guardian.2da`). The engine uses these [files](GFF-File-Format) to calculate attack bonuses for each class at each level.

**Row [index](2DA-File-Format#row-labels)**: Level (integer, typically 1-20)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `level` | Integer | Character level |
| `attackbonus` | Integer | Base attack bonus at this level |

---
