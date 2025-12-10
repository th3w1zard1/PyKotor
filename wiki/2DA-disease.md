# disease.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines disease effect configurations. The engine uses this [file](GFF-File-Format) to determine disease names, scripts, and properties.

**Row [index](2DA-File-Format#row-labels)**: Disease ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Disease label |
| `name` | [StrRef](TLK-File-Format#string-references-strref) | [string](GFF-File-Format#cexostring) reference for disease name (KotOR 2) |
| `end_incu_script` | [ResRef](GFF-File-Format#resref) | Script [ResRef](GFF-File-Format#resref) for end incubation period |
| `24_hour_script` | [ResRef](GFF-File-Format#resref) | Script [ResRef](GFF-File-Format#resref) for 24-hour disease effect |
| Additional columns | Various | Disease properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:255`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L255) - [StrRef](TLK-File-Format#string-references-strref) column definition for disease.2da (KotOR 2)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:238,431`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L238) - Script [ResRef](GFF-File-Format#resref) column definitions for disease.2da

---
