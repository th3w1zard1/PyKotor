# cls_savthr_*.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Saving throw progression tables for each class. files are named `cls_savthr_<classname>.2da` (e.g., `cls_savthr_jedi_guardian.2da`). The engine uses these files to calculate saving throw bonuses for each class at each level.

**Row index**: Level (integer, typically 1-20)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `level` | Integer | Character level |
| `fortitude` | Integer | Fortitude save bonus |
| `reflex` | Integer | Reflex save bonus |
| `will` | Integer | Will save bonus |

---
