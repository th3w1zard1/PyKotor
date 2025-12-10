# skills.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: Defines all skills available in the game, including which classes can use them, their [KEY](KEY-File-Format) ability scores, and skill descriptions. The engine uses this file to determine skill availability, skill point costs, and skill checks.

**Row index**: Skill ID (integer)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | string | Skill label |
| `name` | [StrRef](TLK-File-Format#string-references-strref) | string reference for skill name |
| `description` | [StrRef](TLK-File-Format#string-references-strref) | string reference for skill description |
| `keyability` | Integer | [KEY](KEY-File-Format) ability score (STR, DEX, INT, etc.) |
| `armorcheckpenalty` | Boolean | Whether armor check penalty applies |
| `allclassescanuse` | Boolean | Whether all classes can use this skill |
| `category` | Integer | Skill category identifier |
| `maxrank` | Integer | Maximum skill rank |
| `untrained` | Boolean | Whether skill can be used untrained |
| `constant` | Integer (optional) | Constant modifier |
| `hostileskill` | Boolean | Whether skill is hostile |
| `icon` | ResRef (optional) | Skill icon [ResRef](GFF-File-Format#gff-data-types) |

**Column Details** (from reone implementation):

The following columns [ARE](GFF-File-Format#are-area) accessed by the reone engine:

- `name`: string reference for skill name
- `description`: string reference for skill description
- `icon`: Icon [ResRef](GFF-File-Format#gff-data-types)
- Dynamic class skill columns: For each class, there is a column named `{classname}_class` (e.g., `jedi_guardian_class`) that contains `1` if the skill is a class skill for that class
- `droidcanuse`: Boolean - whether droids can use this skill
- `npccanuse`: Boolean - whether NPCs can use this skill

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:148`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L148) - [StrRef](TLK-File-Format#string-references-strref) column definitions for skills.2da (K1: name, description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:326`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L326) - [StrRef](TLK-File-Format#string-references-strref) column definitions for skills.2da (K2: name, description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:472`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L472) - TwoDARegistry.SKILLS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:563`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L563) - [GFF](GFF-File-Format) field mapping: "SkillID" -> skills.2da

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:71`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L71) - HTInstallation.TwoDA_SKILLS constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/savegame.py:129`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/savegame.py#L129) - Skills table widget in save game editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/savegame.py:511-519`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/savegame.py#L511-L519) - Skills table population in save game editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/savegame.py:542-543`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/savegame.py#L542-L543) - Skills table update logic

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/d20/skills.cpp:32-48`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/d20/skills.cpp#L32-L48) - Skill loading from [2DA](2DA-File-Format)
- [`vendor/reone/src/libs/game/d20/class.cpp:58-65`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/d20/class.cpp#L58-L65) - Class skill checking using dynamic column names
- [`vendor/KotOR.js/src/talents/TalentSkill.ts:38-49`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/talents/TalentSkill.ts#L38-L49) - Skill loading from [2DA](2DA-File-Format) with droidcanuse and npccanuse columns

---
