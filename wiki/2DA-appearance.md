# appearance.2da

Part of the [2DA File Format Documentation](2DA-File-Format).

**Engine Usage**: The `appearance.2da` file is one of the most critical [2DA files](2DA-File-Format) in KotOR. It maps appearance IDs (used in [creature templates](GFF-File-Format#utc-creature) and character creation) to 3D [model](MDL-MDX-File-Format) ResRefs, [texture](TPC-File-Format) assignments, race associations, and physical properties. The engine uses this file when loading creatures, determining which [model](MDL-MDX-File-Format) and [textures](TPC-File-Format) to display, calculating hit detection, and managing character [animations](MDL-MDX-File-Format#animation-header).

**Row index**: Appearance ID (integer, typically 0-based)

**Column structure**:

| Column Name | type | Description |
|------------|------|-------------|
| `label` | String (optional) | Human-readable label for the appearance |
| `modeltype` | string | [model](MDL-MDX-File-Format) type identifier (e.g., "F", "B", "P") |
| `modela` through `modeln` | ResRef (optional) | [model](MDL-MDX-File-Format) ResRefs for different body parts or variations ([models](MDL-MDX-File-Format) a-n) |
| `texa` through `texn` | ResRef (optional) | [texture](TPC-File-Format) ResRefs for different body parts ([textures](TPC-File-Format) a-n) |
| `texaevil`, `texbevil`, `texievil`, `texlevil`, `texnevil` | ResRef (optional) | Dark side variant [textures](TPC-File-Format) |
| `race` | ResRef (optional) | Race identifier [ResRef](GFF-File-Format#gff-data-types) |
| `racetex` | ResRef (optional) | Race-specific [texture](TPC-File-Format) [ResRef](GFF-File-Format#gff-data-types) |
| `racialtype` | Integer | Numeric racial type identifier |
| `normalhead` | Integer (optional) | Default head appearance ID |
| `backuphead` | Integer (optional) | Fallback head appearance ID |
| `portrait` | ResRef (optional) | Portrait image [ResRef](GFF-File-Format#gff-data-types) |
| `skin` | ResRef (optional) | Skin [texture](TPC-File-Format) [ResRef](GFF-File-Format#gff-data-types) |
| `headtexe`, `headtexg`, `headtexve`, `headtexvg` | ResRef (optional) | Head [texture](TPC-File-Format) variations |
| `headbone` | String (optional) | Bone name for head attachment |
| `height` | [Float](https://en.wikipedia.org/wiki/Single-precision_floating-point_format) | Character height multiplier |
| `hitdist` | [Float](https://en.wikipedia.org/wiki/Single-precision_floating-point_format) | Hit detection distance |
| `hitradius` | [Float](https://en.wikipedia.org/wiki/Single-precision_floating-point_format) | Hit detection radius |
| `sizecategory` | Integer | size category (affects combat calculations) |
| `moverate` | string | Movement rate identifier |
| `walkdist` | Float | Walking distance threshold |
| `rundist` | Float | Running distance threshold |
| `prefatckdist` | Float | Preferred attack distance |
| `creperspace` | Float | Creature personal space radius |
| `perspace` | Float | Personal space radius |
| `cameraspace` | Float (optional) | Camera space offset |
| `cameraheightoffset` | String (optional) | Camera height offset |
| `targetheight` | string | Target height for combat |
| `perceptiondist` | Integer | Perception distance |
| `headArcH` | Integer | Head horizontal arc angle |
| `headArcV` | Integer | Head vertical arc angle |
| `headtrack` | Boolean | Whether head tracking is enabled |
| `hasarms` | Boolean | Whether creature has arms |
| `haslegs` | Boolean | Whether creature has legs |
| `groundtilt` | Boolean | Whether ground tilt is enabled |
| `footsteptype` | Integer (optional) | Footstep sound type |
| `footstepsound` | ResRef (optional) | Footstep sound [ResRef](GFF-File-Format#gff-data-types) |
| `footstepvolume` | Boolean | Whether footstep volume is enabled |
| `armorSound` | ResRef (optional) | Armor sound effect [ResRef](GFF-File-Format#gff-data-types) |
| `combatSound` | ResRef (optional) | Combat sound effect [ResRef](GFF-File-Format#gff-data-types) |
| `soundapptype` | Integer (optional) | Sound appearance type |
| `bloodcolr` | string | Blood color identifier |
| `deathvfx` | Integer (optional) | Death visual effect ID |
| `deathvfxnode` | String (optional) | Death VFX attachment [node](MDL-MDX-File-Format#node-structures) |
| `fadedelayondeath` | Boolean (optional) | Whether to fade on death |
| `destroyobjectdelay` | Boolean (optional) | Whether to delay object destruction |
| `disableinjuredanim` | Boolean (optional) | Whether to disable injured [animations](MDL-MDX-File-Format#animation-header) |
| `abortonparry` | Boolean | Whether to abort on parry |
| `freelookeffect` | Integer (optional) | Free look effect ID |
| `equipslotslocked` | Integer (optional) | Locked equipment slot [flags](GFF-File-Format#gff-data-types) |
| `weaponscale` | String (optional) | Weapon scale multiplier |
| `wingTailScale` | Boolean | Whether wing/tail scaling is enabled |
| `helmetScaleF` | String (optional) | Female helmet scale |
| `helmetScaleM` | String (optional) | Male helmet scale |
| `envmap` | ResRef (optional) | Environment map [texture](TPC-File-Format) [ResRef](GFF-File-Format#gff-data-types) |
| `bodyBag` | Integer (optional) | Body bag appearance ID |
| `stringRef` | Integer (optional) | string reference for appearance name |
| `driveaccl` | Integer | Vehicle drive acceleration |
| `drivemaxspeed` | Float | Vehicle maximum speed |
| `driveanimwalk` | Float | Vehicle walk [animation](MDL-MDX-File-Format#animation-header) speed |
| `driveanimrunPc` | Float | PC vehicle run [animation](MDL-MDX-File-Format#animation-header) speed |
| `driveanimrunXbox` | Float | Xbox vehicle run [animation](MDL-MDX-File-Format#animation-header) speed |

**Column Details**:

The `appearance.2da` file contains a comprehensive set of columns for character appearance configuration. The complete column list is parsed by reone's appearance parser:

- [model](MDL-MDX-File-Format) columns: `modela` through `modeln` (14 [model](MDL-MDX-File-Format) variations)
- [texture](TPC-File-Format) columns: `texa` through `texn` (14 [texture](TPC-File-Format) variations)
- Evil [texture](TPC-File-Format) columns: `texaevil`, `texbevil`, `texievil`, `texlevil`, `texnevil`
- Head [texture](TPC-File-Format) columns: `headtexe`, `headtexg`, `headtexve`, `headtexvg`
- Movement: `walkdist`, `rundist`, `prefatckdist`, `moverate`
- Physical properties: `height`, `hitdist`, `hitradius`, `sizecategory`, `perceptiondist`
- Personal space: `perspace`, `creperspace`
- Camera: `cameraspace`, `cameraheightoffset`, `targetheight`
- Head tracking: `headArcH`, `headArcV`, `headtrack`
- Body parts: `hasarms`, `haslegs`, `groundtilt`, `wingTailScale`
- Footsteps: `footsteptype`, `footstepsound`, `footstepvolume`
- Sounds: `armorSound`, `combatSound`, `soundapptype`
- Visual effects: `deathvfx`, `deathvfxnode`, `fadedelayondeath`, `freelookeffect`
- Equipment: `equipslotslocked`, `weaponscale`, `helmetScaleF`, `helmetScaleM`
- [textures](TPC-File-Format): `envmap`, `skin`, `portrait`, `race`, `racetex`, `racialtype`
- Heads: `normalhead`, `backuphead`, `headbone`
- Vehicle: `driveaccl`, `drivemaxspeed`, `driveanimwalk`, `driveanimrunPc`, `driveanimrunXbox`
- Other: `bloodcolr`, `bodyBag`, `stringRef`, `abortonparry`, `destroyobjectdelay`, `disableinjuredanim`

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:73`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L73) - [StrRef](TLK-File-Format#string-references-strref) column definition for appearance.2da (K1: string_ref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:248`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L248) - [StrRef](TLK-File-Format#string-references-strref) column definition for appearance.2da (K2: string_ref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:155`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L155) - [ResRef](GFF-File-Format#gff-data-types) column definition for appearance.2da (race)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:168`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L168) - [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definitions for appearance.2da (modela through modelj)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:213-214`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L213-L214) - [texture](TPC-File-Format) [ResRef](GFF-File-Format#gff-data-types) column definitions for appearance.2da (racetex, texa through texj, headtexve, headtexe, headtexvg, headtexg)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:456`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L456) - TwoDARegistry.APPEARANCES constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:524`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L524) - [GFF](GFF-File-Format) field mapping: "Appearance_Type" -> appearance.2da

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:55`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L55) - HTInstallation.TwoDA_APPEARANCES constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utc.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utc.py) - Appearance selection combobox in [UTC](GFF-File-Format#utc-creature) editor (UI reference)
- [`Tools/HolocronToolset/src/toolset/gui/editors/utp.py:124-131`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utp.py#L124-L131) - Appearance selection in UTP (placeable) editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/utd.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utd.py) - Appearance selection in UTD (door) editor (UI reference)
- [`Tools/HolocronToolset/src/toolset/gui/editors/ute.py:181`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/ute.py#L181) - Appearance ID usage in encounter editor

**Vendor Implementations:**

- [`vendor/reone/src/libs/resource/parser/2da/appearance.cpp:28-125`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/2da/appearance.cpp#L28-L125) - Complete column parsing implementation with all column names
- [`vendor/reone/src/libs/game/object/creature.cpp:98-107`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L98-L107) - Appearance loading and column usage
- [`vendor/reone/src/libs/game/object/creature.cpp:1156-1228`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L1156-L1228) - [model](MDL-MDX-File-Format) and [texture](TPC-File-Format) column access

---
