# subrace.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines subrace types for character creation and [creature templates](GFF-File-Format#utc-creature). The engine uses this file to determine subrace properties and restrictions.

**Row index**: Subrace ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Subrace label |
| Additional columns | Various | Subrace properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:457`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L457) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:56`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L56) - HTInstallation constant

---
