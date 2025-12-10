# gamespyrooms.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines GameSpy room configurations for multiplayer (if supported). The engine uses this [file](GFF-File-Format) to determine GameSpy room names and properties.

**Row [index](2DA-File-Format#row-labels)**: GameSpy Room ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | GameSpy room label |
| `str_ref` | [StrRef](TLK-File-Format#string-references-strref) | [string](GFF-File-Format#cexostring) reference for GameSpy room name |
| Additional columns | Various | GameSpy room properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:85`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L85) - [StrRef](TLK-File-Format#string-references-strref) column definition for gamespyrooms.2da

---
