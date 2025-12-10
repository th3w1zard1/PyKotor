# subrace.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines subrace [types](GFF-File-Format#data-types) for character creation and [creature templates](GFF-File-Format#utc-creature). The engine uses this [file](GFF-File-Format) to determine subrace properties and restrictions.

**Row [index](2DA-File-Format#row-labels)**: Subrace ID (integer)

**Column [structure](GFF-File-Format#file-structure)**:

| Column Name | [type](GFF-File-Format#data-types) | Description |
|------------|------|-------------|
| `label` | [string](GFF-File-Format#cexostring) | Subrace label |
| Additional columns | Various | Subrace properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:457`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L457) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:56`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L56) - HTInstallation constant

---
