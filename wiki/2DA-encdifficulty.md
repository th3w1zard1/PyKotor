# encdifficulty.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines encounter difficulty levels for area encounters. The engine uses this [file](GFF-File-Format) to determine encounter scaling and difficulty modifiers.

**Row [index](2DA-File-Format#row-labels)**: Difficulty ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Difficulty label |
| Additional columns | Various | Difficulty modifiers and properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:474`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L474) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:73`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L73) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/ute.py:101-104`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/ute.py#L101-L104) - Encounter difficulty selection

---
