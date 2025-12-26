# racialtypes.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines racial types for character creation and [creature templates](GFF-File-Format#utc-creature). The engine uses this file to determine race-specific properties, restrictions, and bonuses.

**Row index**: Race ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Race label |
| Additional columns | Various | Race properties and bonuses |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:471`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L471) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:70`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L70) - HTInstallation constant

---
