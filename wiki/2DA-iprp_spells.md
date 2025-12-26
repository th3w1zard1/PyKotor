# iprp_spells.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Maps item property values to spell/Force power grants. Defines on-use and on-hit spell effects for items based on property values. The engine uses this file to determine which spells or Force powers [ARE](GFF-File-Format#are-area) granted by item properties.

**Row index**: Item property value (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Property value label |
| `spell` | Integer | Spell ID associated with this property value |
| `name` | [StrRef](TLK-File-Format#string-references-strref) | string reference for spell name (K1/K2) |
| `icon` | [ResRef](GFF-File-Format#gff-data-types) | Icon [ResRef](GFF-File-Format#gff-data-types) for the spell (K1/K2) |
| Additional columns | Various | Spell mappings |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:126`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L126) - [StrRef](TLK-File-Format#string-references-strref) column definition for iprp_spells.2da (K1: name)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:218`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L218) - [ResRef](GFF-File-Format#gff-data-types) column definition for iprp_spells.2da (K1: icon)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:304`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L304) - [StrRef](TLK-File-Format#string-references-strref) column definition for iprp_spells.2da (K2: name)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:411`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L411) - [ResRef](GFF-File-Format#gff-data-types) column definition for iprp_spells.2da (K2: icon)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:578`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L578) - [GFF](GFF-File-Format) field mapping: "CastSpell" -> iprp_spells.2da

---
