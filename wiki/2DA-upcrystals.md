# upcrystals.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines upgrade crystal configurations. The engine uses this file to determine crystal [model](MDL-MDX-File-Format) variations for lightsaber upgrades.

**Row index**: Upgrade Crystal ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Upgrade crystal label |
| `shortmdlvar` | [ResRef](GFF-File-Format#gff-data-types) | Short [model](MDL-MDX-File-Format) variation [ResRef](GFF-File-Format#gff-data-types) |
| `longmdlvar` | [ResRef](GFF-File-Format#gff-data-types) | Long [model](MDL-MDX-File-Format) variation [ResRef](GFF-File-Format#gff-data-types) |
| `doublemdlvar` | [ResRef](GFF-File-Format#gff-data-types) | [double](GFF-File-Format#gff-data-types)-bladed [model](MDL-MDX-File-Format) variation [ResRef](GFF-File-Format#gff-data-types) |
| Additional columns | Various | Crystal properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:172`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L172) - [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definitions for upcrystals.2da

---
