# hen_familiar.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines familiar configurations (HEN - Henchman system). The engine uses this file to determine familiar base resource references (not used in game engine).

**Row index**: Familiar ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Familiar label |
| `baseresref` | [ResRef](GFF-File-Format#gff-data-types) | Base [resource reference](GFF-File-Format#gff-data-types) for familiar (not used in game engine) |
| Additional columns | Various | Familiar properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:158`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L158) - [ResRef](GFF-File-Format#gff-data-types) column definition for hen_familiar.2da (baseresref, not used in engine)

---
