# soundset.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Maps sound set IDs to voice set assignments for characters. The engine uses this file to determine which voice lines to play for characters based on their sound set.

**Row index**: Sound set ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Sound set label |
| `resref` | [ResRef](GFF-File-Format#gff-data-types) | [sound set files](SSF-File-Format) ResRef (e.g., `c_human_m_01`) |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:143`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L143) - [StrRef](TLK-File-Format#string-references-strref) column definition for soundset.2da (K1: [StrRef](TLK-File-Format#string-references-strref))
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:321`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L321) - [StrRef](TLK-File-Format#string-references-strref) column definition for soundset.2da (K2: [StrRef](TLK-File-Format#string-references-strref))
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:459`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L459) - TwoDARegistry.SOUNDSETS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:522`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L522) - [GFF](GFF-File-Format) field mapping: "SoundSetFile" -> soundset.2da
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:90-92`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L90-L92) - [UTC](GFF-File-Format#utc-creature) soundset_id field documentation
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:359`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L359) - [UTC](GFF-File-Format#utc-creature) soundset_id field initialization
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:549-550`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L549-L550) - SoundSetFile field parsing from [UTC](GFF-File-Format#utc-creature) [GFF](GFF-File-Format)
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:821`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L821) - SoundSetFile field writing to [UTC](GFF-File-Format#utc-creature) [GFF](GFF-File-Format)

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:58`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L58) - HTInstallation.TwoDA_SOUNDSETS constant
- [`Tools/HolocronToolset/src/ui/editors/utc.ui:260-267`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/ui/editors/utc.ui#L260-L267) - Soundset selection combobox in [UTC](GFF-File-Format#utc-creature) editor UI

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/object/creature.cpp:1347-1354`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L1347-L1354) - Sound set loading from [2DA](2DA-File-Format)

---
