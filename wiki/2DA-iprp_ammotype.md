# iprp_ammotype.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Maps item property values to ammunition type restrictions. The engine uses this file to determine ammunition type calculations for item properties.

**Row index**: Item Property Value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| Additional columns | Various | Ammunition type mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:488`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L488) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:87`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L87) - HTInstallation constant

---
