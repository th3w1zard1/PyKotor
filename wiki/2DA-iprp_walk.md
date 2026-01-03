# iprp_walk.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Maps item property values to movement/walk speed modifiers. The engine uses this file to determine movement speed calculations for item properties.

**Row index**: Item Property Value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| Additional columns | Various | Movement speed mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:490`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L490) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:89`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L89) - HTInstallation constant

---
