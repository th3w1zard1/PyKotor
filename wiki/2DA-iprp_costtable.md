# iprp_costtable.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Master table listing all item property cost calculation tables. The engine uses this [file](GFF-File-Format) to look up which cost table to use for calculating item property costs.

**Row [index](2DA-File-Format#row-labels)**: Cost Table ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Cost table label |
| Additional columns | Various | Cost table ResRefs and properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:477`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L477) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:76`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L76) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:486-496`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L486-L496) - Cost table lookup in item editor

---
