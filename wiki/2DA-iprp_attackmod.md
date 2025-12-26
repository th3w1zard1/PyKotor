# iprp_attackmod.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Maps item property values to attack modifier bonuses. The engine uses this file to determine attack bonus calculations for item properties.

**Row index**: Item Property Value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| Additional columns | Various | Attack modifier mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:575`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L575) - [GFF](GFF-File-Format) field mapping: "AttackModifier" -> iprp_attackmod.2da

---
