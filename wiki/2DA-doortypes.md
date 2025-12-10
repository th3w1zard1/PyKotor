# [doortypes.2da](2DA-doortypes)

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines door [type](GFF-File-Format#gff-data-types) configurations and their properties. The engine uses this [file](GFF-File-Format) to determine door [type](GFF-File-Format#gff-data-types) names, [models](MDL-MDX-File-Format), and behaviors.

**Row [index](2DA-File-Format#row-labels)**: Door [type](GFF-File-Format#gff-data-types) ID (integer)

**Column [structure](GFF-File-Format#file-structure-overview)**:

| Column Name | [type](GFF-File-Format#gff-data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#gff-data-types) | Door [type](GFF-File-Format#gff-data-types) label |
| `stringrefgame` | [StrRef](TLK-File-Format#string-references-strref) | [string](GFF-File-Format#gff-data-types) reference for door [type](GFF-File-Format#gff-data-types) name |
| `model` | [ResRef](GFF-File-Format#gff-data-types) | [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) for the door [type](GFF-File-Format#gff-data-types) |
| Additional columns | Various | Door [type](GFF-File-Format#gff-data-types) properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:78`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L78) - [StrRef](TLK-File-Format#string-references-strref) column definition for [doortypes.2da](2DA-doortypes)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:177`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L177) - [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definition for [doortypes.2da](2DA-doortypes)

---
