# iprp_bonusfeat.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Maps item property values to bonus feat grants. The engine uses this file to determine which feats [ARE](GFF-File-Format#are-area) granted by item properties.

**Row index**: Item Property Value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| Additional columns | Various | Bonus feat mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:577`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L577) - [GFF](GFF-File-Format) field mapping: "BonusFeatID" -> iprp_bonusfeat.2da

---
