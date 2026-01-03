# iprp_onhit.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Maps item property values to on-hit effect types. The engine uses this file to determine on-hit effect calculations for item properties.

**Row index**: Item Property Value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| Additional columns | Various | On-hit effect mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:487`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L487) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:86`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L86) - HTInstallation constant

---
