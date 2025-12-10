# [feat.2da](2DA-feat)

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines all feats available in the game, including combat feats, skill feats, Force feats, and class-specific abilities. The engine uses this file to determine feat prerequisites, effects, and availability during character creation and level-up.

**Row index**: Feat ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Feat label |
| `name` | [StrRef](TLK-File-Format#string-references-strref) | string reference for feat name |
| `description` | [StrRef](TLK-File-Format#string-references-strref) | string reference for feat description |
| `icon` | [ResRef](GFF-File-Format#gff-data-types) | Feat icon [ResRef](GFF-File-Format#gff-data-types) |
| `takentext` | [StrRef](TLK-File-Format#string-references-strref) | string reference for "feat taken" message |
| `prerequisite` | Integer (optional) | Prerequisite feat ID |
| `minattackbonus` | Integer (optional) | Minimum attack bonus requirement |
| `minstr` | Integer (optional) | Minimum strength requirement |
| `mindex` | Integer (optional) | Minimum dexterity requirement |
| `minint` | Integer (optional) | Minimum intelligence requirement |
| `minwis` | Integer (optional) | Minimum wisdom requirement |
| `mincon` | Integer (optional) | Minimum constitution requirement |
| `mincha` | Integer (optional) | Minimum charisma requirement |
| `minlevel` | Integer (optional) | Minimum character level |
| `minclasslevel` | Integer (optional) | Minimum class level |
| `minspelllevel` | Integer (optional) | Minimum spell level |
| `spellid` | Integer (optional) | Required spell ID |
| `successor` | Integer (optional) | Successor feat ID (for feat chains) |
| `maxrank` | Integer (optional) | Maximum rank for stackable feats |
| `minrank` | Integer (optional) | Minimum rank requirement |
| `masterfeat` | Integer (optional) | Master feat ID |
| `targetself` | Boolean | Whether feat targets self |
| `orreqfeat0` through `orreqfeat4` | Integer (optional) | Alternative prerequisite feat IDs |
| `reqskill` | Integer (optional) | Required skill ID |
| `reqskillrank` | Integer (optional) | Required skill rank |
| `constant` | Integer (optional) | Constant value for feat calculations |
| `toolscategories` | Integer (optional) | Tool categories [flags](GFF-File-Format#gff-data-types) |
| `effecticon` | ResRef (optional) | Effect icon [ResRef](GFF-File-Format#gff-data-types) |
| `effectdesc` | StrRef (optional) | Effect description string reference |
| `effectcategory` | Integer (optional) | Effect category identifier |
| `allclassescanuse` | Boolean | Whether all classes can use this feat |
| `category` | Integer | Feat category identifier |
| `maxcr` | Integer (optional) | Maximum challenge rating |
| `spellid` | Integer (optional) | Associated spell ID |
| `usesperday` | Integer (optional) | Uses per day limit |
| `masterfeat` | Integer (optional) | Master feat ID for feat trees |

**Column Details** (from reone implementation):

The following columns [ARE](GFF-File-Format#are-area) accessed by the reone engine:

- `name`: string reference for feat name
- `description`: string reference for feat description
- `icon`: Icon [ResRef](GFF-File-Format#gff-data-types)
- `mincharlevel`: Minimum character level (hex integer)
- `prereqfeat1`: Prerequisite feat ID 1 (hex integer)
- `prereqfeat2`: Prerequisite feat ID 2 (hex integer)
- `successor`: Successor feat ID (hex integer)
- `pips`: Feat pips/ranks (hex integer)
- `allclassescanuse`: Boolean - whether all classes can use this feat
- `masterfeat`: Master feat ID
- `orreqfeat0` through `orreqfeat4`: Alternative prerequisite feat IDs
- `hostilefeat`: Boolean - whether feat is hostile
- `category`: Feat category identifier

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:82`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L82) - [StrRef](TLK-File-Format#string-references-strref) column definitions for [feat.2da](2DA-feat) (K1: name, description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:260`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L260) - [StrRef](TLK-File-Format#string-references-strref) column definitions for [feat.2da](2DA-feat) (K2: name, description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:227`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L227) - [ResRef](GFF-File-Format#gff-data-types) column definition for [feat.2da](2DA-feat) (icon)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:464`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L464) - TwoDARegistry.FEATS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:561-562`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L561-L562) - [GFF](GFF-File-Format) field mapping: "FeatID" and "Feat" -> [feat.2da](2DA-feat)
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:321-323`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L321-L323) - [UTC](GFF-File-Format#utc-creature) feat list field documentation
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:432`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L432) - [UTC](GFF-File-Format#utc-creature) feats list initialization
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:762-768`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L762-L768) - Feat list parsing from [UTC](GFF-File-Format#utc-creature) [GFF](GFF-File-Format)
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:907-909`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L907-L909) - Feat list writing to [UTC](GFF-File-Format#utc-creature) [GFF](GFF-File-Format)

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:63`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L63) - HTInstallation.TwoDA_FEATS constant

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/d20/feats.cpp:32-58`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/d20/feats.cpp#L32-L58) - Feat loading from [2DA](2DA-File-Format) with column access
- [`vendor/KotOR.js/src/talents/TalentFeat.ts:36-53`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/talents/TalentFeat.ts#L36-L53) - Feat structure with additional columns
- [`vendor/KotOR.js/src/talents/TalentFeat.ts:122-132`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/talents/TalentFeat.ts#L122-L132) - Feat loading from [2DA](2DA-File-Format)

---
