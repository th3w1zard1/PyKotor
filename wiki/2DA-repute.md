# repute.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines reputation values between different factions. The engine uses this file to determine whether creatures [ARE](GFF-File-Format#are-area) enemies, friends, or neutral to each other based on their faction relationships.

**Row index**: Faction ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Faction label |
| Additional columns | Integer | Reputation values for each faction (column names match faction labels) |

**Note**: The `repute.2da` file is a square [matrix](BWM-File-Format#walkable-adjacencies) where each row represents a faction, and each column (after `label`) represents the reputation value toward another faction. Reputation values typically range from 0-100, where values below 50 [ARE](GFF-File-Format#are-area) enemies, above 50 [ARE](GFF-File-Format#are-area) friends, and 50 is neutral.

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:460`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L460) - TwoDARegistry.FACTIONS constant definition (maps to "repute")
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:526-527`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L526-L527) - [GFF](GFF-File-Format) field mapping: "FactionID" and "Faction" -> repute.2da
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:92`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L92) - REPUTE.fac documentation comment
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:1593`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L1593) - REPUTE.fac file check comment
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:1627`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L1627) - REPUTE.fac documentation
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:1667`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L1667) - REPUTE_IDENTIFIER constant definition
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:1683-1684`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L1683-L1684) - repute [GFF](GFF-File-Format) field initialization
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:1759-1761`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L1759-L1761) - REPUTE.fac parsing
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:1795-1796`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L1795-L1796) - REPUTE.fac writing

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:59`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L59) - HTInstallation.TwoDA_FACTIONS constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utc.py:239`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utc.py#L239) - repute.2da included in batch cache for [UTC](GFF-File-Format#utc-creature) editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/utc.py:253-280`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utc.py#L253-L280) - repute.2da usage in faction selection combobox
- [`Tools/HolocronToolset/src/toolset/gui/editors/utp.py:121-128`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utp.py#L121-L128) - repute.2da usage in [UTP](GFF-File-Format#utp-placeable) editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/utd.py:117-124`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utd.py#L117-L124) - repute.2da usage in [UTD](GFF-File-Format#utd-door) editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/ute.py:106-109`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/ute.py#L106-L109) - repute.2da usage in [UTE](GFF-File-Format#ute-encounter) editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/utt.py:72-78`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utt.py#L72-L78) - repute.2da usage in [UTT](GFF-File-Format#utt-trigger) editor

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/reputes.cpp:36-62`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/reputes.cpp#L36-L62) - Repute [matrix](BWM-File-Format#walkable-adjacencies) loading from [2DA](2DA-File-Format)

---
