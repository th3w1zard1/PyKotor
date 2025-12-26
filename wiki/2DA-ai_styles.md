# ai_styles.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines AI behavior styles for creatures. The engine uses this file to determine AI behavior patterns and combat strategies.

**Row index**: AI Style ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | AI style label |
| Additional columns | Various | AI behavior parameters |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:572`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L572) - [GFF](GFF-File-Format) field mapping: "AIStyle" -> ai_styles.2da

---
