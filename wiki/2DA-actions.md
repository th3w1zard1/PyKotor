# actions.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines action [types](GFF-File-Format#data-types) and their properties. The engine uses this [file](GFF-File-Format) to determine action icons, descriptions, and behaviors for various in-game actions.

**Row [index](2DA-File-Format#row-labels)**: Action ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Action label |
| `string_ref` | [StrRef](TLK-File-Format#string-references-strref) | [string](GFF-File-Format#cexostring) reference for action description |
| `iconresref` | [ResRef](GFF-File-Format#resref) | Icon [ResRef](GFF-File-Format#resref) for the action |
| Additional columns | Various | Action properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:70`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L70) - [StrRef](TLK-File-Format#string-references-strref) column definition for actions.2da
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:212`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L212) - [texture](TPC-File-Format) [ResRef](GFF-File-Format#resref) column definition for actions.2da

---
