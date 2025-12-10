# [doortypes.2da](2DA-doortypes)

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines door type configurations and their properties. The engine uses this file to determine door type names, [models](MDL-MDX-File-Format), and behaviors.

**Row index**: Door type ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Door type label |
| `stringrefgame` | [StrRef](TLK-File-Format#string-references-strref) | string reference for door type name |
| `model` | [ResRef](GFF-File-Format#gff-data-types) | [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) for the door type |
| Additional columns | Various | Door type properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:78`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L78) - [StrRef](TLK-File-Format#string-references-strref) column definition for [doortypes.2da](2DA-doortypes)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:177`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L177) - [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definition for [doortypes.2da](2DA-doortypes)

---
