# upgrade.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines item upgrade [types](GFF-File-Format#data-types) and properties. The engine uses this [file](GFF-File-Format) to determine which upgrades can be applied to items and their effects.

**Row [index](2DA-File-Format#row-labels)**: Upgrade [type](GFF-File-Format#data-types) ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Upgrade [type](GFF-File-Format#data-types) label |
| Additional columns | Various | Upgrade properties and effects |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:473`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L473) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:72`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L72) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:632-639`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L632-L639) - Upgrade selection in item editor

---
