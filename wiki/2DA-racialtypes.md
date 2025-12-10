# [racialtypes.2da](2DA-racialtypes)

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines racial [types](GFF-File-Format#data-types) for character creation and [creature templates](GFF-File-Format#utc-creature). The engine uses this [file](GFF-File-Format) to determine race-specific properties, restrictions, and bonuses.

**Row [index](2DA-File-Format#row-labels)**: Race ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Race label |
| Additional columns | Various | Race properties and bonuses |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:471`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L471) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:70`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L70) - HTInstallation constant

---
