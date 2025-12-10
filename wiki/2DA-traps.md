# traps.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines trap properties including [models](MDL-MDX-File-Format), sounds, and scripts. The engine uses this file when loading triggers with trap types to determine trap appearance and behavior.

**Row index**: Trap type ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Trap type label |
| `name` | [StrRef](TLK-File-Format#string-references-strref) | string reference for trap name |
| `model` | [ResRef](GFF-File-Format#gff-data-types) | Trap [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) |
| `explosionsound` | [ResRef](GFF-File-Format#gff-data-types) | Explosion sound effect [ResRef](GFF-File-Format#gff-data-types) |
| `resref` | [ResRef](GFF-File-Format#gff-data-types) | Trap script [ResRef](GFF-File-Format#gff-data-types) |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:150`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L150) - [StrRef](TLK-File-Format#string-references-strref) column definitions for traps.2da (K1: trapname, name)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:328`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L328) - [StrRef](TLK-File-Format#string-references-strref) column definitions for traps.2da (K2: trapname, name)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:470`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L470) - TwoDARegistry.TRAPS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:568`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L568) - [GFF](GFF-File-Format) field mapping: "TrapType" -> traps.2da
- [`Libraries/PyKotor/src/pykotor/common/scriptdefs.py:6347-6348`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptdefs.py#L6347-L6348) - VersusTrapEffect function comments
- [`Libraries/PyKotor/src/pykotor/common/scriptdefs.py:7975-7976`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptdefs.py#L7975-L7976) - GetLastHostileActor function comment mentioning traps
- [`Libraries/PyKotor/src/pykotor/common/scriptlib.py:21692`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptlib.py#L21692) - Trap targeting comment

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:69`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L69) - HTInstallation.TwoDA_TRAPS constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utt.py:73-87`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utt.py#L73-L87) - traps.2da loading and usage in trap type selection combobox
- [`Tools/HolocronToolset/src/toolset/gui/editors/utt.py:167`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utt.py#L167) - traps.2da usage for setting trap type index
- [`Tools/HolocronToolset/src/toolset/gui/editors/utt.py:216`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utt.py#L216) - traps.2da usage for getting trap type index
- [`Tools/HolocronToolset/src/ui/editors/utt.ui:252`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/ui/editors/utt.ui#L252) - Trap selection combobox in [UTT](GFF-File-Format#utt-trigger) editor UI

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/object/trigger.cpp:75-78`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/trigger.cpp#L75-L78) - Trap type loading from [2DA](2DA-File-Format)
- [`vendor/KotOR.js/src/module/ModuleTrigger.ts:605-611`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleTrigger.ts#L605-L611) - Trap loading from [2DA](2DA-File-Format)
- [`vendor/KotOR.js/src/module/ModuleObject.ts:1822`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleObject.ts#L1822) - Trap lookup from [2DA](2DA-File-Format)

---
