# iprp_immunity.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Maps item property values to immunity types. The engine uses this file to determine immunity calculations for item properties.

**Row index**: Item Property Value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| Additional columns | Various | Immunity type mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:484`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L484) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:83`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L83) - HTInstallation constant

---
