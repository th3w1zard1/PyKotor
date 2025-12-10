# upcrystals.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines upgrade crystal configurations. The engine uses this [file](GFF-File-Format) to determine crystal [model](MDL-MDX-File-Format) variations for lightsaber upgrades.

**Row [index](2DA-File-Format#row-labels)**: Upgrade Crystal ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Upgrade crystal label |
| `shortmdlvar` | [ResRef](GFF-File-Format#gff-data-types) | Short [model](MDL-MDX-File-Format) variation [ResRef](GFF-File-Format#gff-data-types) |
| `longmdlvar` | [ResRef](GFF-File-Format#gff-data-types) | Long [model](MDL-MDX-File-Format) variation [ResRef](GFF-File-Format#gff-data-types) |
| `doublemdlvar` | [ResRef](GFF-File-Format#gff-data-types) | [double](GFF-File-Format#gff-data-types)-bladed [model](MDL-MDX-File-Format) variation [ResRef](GFF-File-Format#gff-data-types) |
| Additional columns | Various | Crystal properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:172`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L172) - [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definitions for upcrystals.2da

---
