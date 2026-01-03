# iprp_combatdam.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Maps item property values to combat damage bonuses. The engine uses this file to determine damage bonus calculations for item properties.

**Row index**: Item Property Value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| Additional columns | Various | Combat damage mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:480`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L480) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:79`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L79) - HTInstallation constant

---
