# GIT ([game instance template](GFF-File-Format#git-game-instance-template))

Part of the [GFF File Format Documentation](GFF-File-Format).

[GIT files](GFF-File-Format#git-game-instance-template) store dynamic instance [data](GFF-File-Format#file-structure-overview) for areas, defining where creatures, doors, placeables, triggers, waypoints, stores, encounters, sounds, and cameras [ARE](GFF-File-Format#are-area) positioned in the game world. While [ARE](GFF-File-Format#are-area) [files](GFF-File-Format) define static environmental properties, [GIT files](GFF-File-Format#git-game-instance-template) contain all runtime object placement and instance-specific properties.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/git.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/git.py)

## [area properties](GFF-File-Format#are-area)

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `AmbientSndDay` | Int | Day ambient sound ID |
| `AmbientSndDayVol` | Int | Day ambient volume (0-127) |
| `AmbientSndNight` | Int | Night ambient sound ID |
| `AmbientSndNightVol` | Int | Night ambient volume |
| `EnvAudio` | Int | Environment audio type |
| `MusicBattle` | Int | Battle music track ID |
| `MusicDay` | Int | Standard/exploration music ID |
| `MusicNight` | Int | Night music track ID |
| `MusicDelay` | Int | Delay before music starts (seconds) |

**Audio Configuration:**

- **Ambient Sounds**: Looping background ambience
- **Music Tracks**: From `ambientmusic.2da` and `musicbattle.2da`
- **EnvAudio**: Reverb/echo [type](GFF-File-Format#gff-data-types) for area
- **MusicDelay**: Prevents instant music start

**Music System:**

- MusicDay plays during exploration
- MusicBattle triggers during combat
- MusicNight unused in KotOR (no day/night cycle)
- Smooth transitions between tracks

## Instance Lists

[GIT](GFF-File-Format#git-game-instance-template) [files](GFF-File-Format) contain multiple lists defining object instances:

| List [field](GFF-File-Format#file-structure-overview) | Contains | Description |
| ---------- | -------- | ----------- |
| `Creature List` | GITCreature | Spawned NPCs and enemies |
| `Door List` | GITDoor | Placed doors |
| `Placeable List` | GITPlaceable | Containers, furniture, objects |
| `Encounter List` | GITEncounter | Encounter spawn zones |
| `TriggerList` | GITTrigger | Trigger volumes |
| `WaypointList` | GITWaypoint | Waypoint markers |
| `StoreList` | GITStore | Merchant vendors |
| `SoundList` | GITSound | Positional audio emitters |
| `CameraList` | GITCamera | Camera definitions |

**Instance [structure](GFF-File-Format#file-structure-overview):**

Each instance [type](GFF-File-Format#gff-data-types) has common [fields](GFF-File-Format#file-structure-overview) plus [type](GFF-File-Format#gff-data-types)-specific [data](GFF-File-Format#file-structure-overview):

**Common Instance [fields](GFF-File-Format#file-structure-overview):**

- Position (X, Y, Z [coordinates](GFF-File-Format#are-area))
- Orientation ([quaternion](MDL-MDX-File-Format#node-header) or Euler angles)
- Template ResRef ([UTC](GFF-File-Format#utc-creature), [UTD](GFF-File-Format#utd-door), [UTP](GFF-File-Format#utp-placeable), etc.)
- Tag override (optional)

## GITCreature Instances

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | [ResRef](GFF-File-Format#gff-data-types) | [UTC](GFF-File-Format#utc-creature) template to spawn |
| `XPosition` | Float | World X [coordinate](GFF-File-Format#are-area) |
| `YPosition` | Float | World Y [coordinate](GFF-File-Format#are-area) |
| `ZPosition` | Float | World Z [coordinate](GFF-File-Format#are-area) |
| `XOrientation` | Float | [orientation](MDL-MDX-File-Format#node-header) X component |
| `YOrientation` | Float | [orientation](MDL-MDX-File-Format#node-header) Y component |

**Creature Spawning:**

- Engine loads [UTC](GFF-File-Format#utc-creature) template
- Applies [position](MDL-MDX-File-Format#node-header)/[orientation](MDL-MDX-File-Format#node-header) from [GIT](GFF-File-Format#git-game-instance-template)
- Creature initialized with template stats
- Scripts fire after spawn

## GITDoor Instances

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | [ResRef](GFF-File-Format#gff-data-types) | [UTD](GFF-File-Format#utd-door) template |
| `Tag` | [CExoString](GFF-File-Format#gff-data-types) | Instance tag override |
| `LinkedToModule` | [ResRef](GFF-File-Format#gff-data-types) | Destination module |
| `LinkedTo` | [CExoString](GFF-File-Format#gff-data-types) | Destination waypoint tag |
| `LinkedToFlags` | Byte | Transition [flags](GFF-File-Format#gff-data-types) |
| `TransitionDestin` | [CExoLocString](GFF-File-Format#gff-data-types) | Destination label (UI) |
| `X`, `Y`, `Z` | Float | [position](MDL-MDX-File-Format#node-header) [coordinates](GFF-File-Format#are-area) |
| `Bearing` | Float | Door [orientation](MDL-MDX-File-Format#node-header) |
| `TweakColor` | DWord | Door [color](GFF-File-Format#color) tint |
| `Hitpoints` | Short | Current HP override |

**Door Linking:**

- **LinkedToModule**: Target module [ResRef](GFF-File-Format#gff-data-types)
- **LinkedTo**: Waypoint tag in target module
- **TransitionDestin**: Loading screen text
- Doors can teleport between modules

**Door Instances:**

- Inherit properties from [UTD](GFF-File-Format#utd-door) template
- [GIT](GFF-File-Format#git-game-instance-template) can override HP, tag, linked destination
- [position](MDL-MDX-File-Format#node-header)/[orientation](MDL-MDX-File-Format#node-header) instance-specific

## GITPlaceable Instances

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | [ResRef](GFF-File-Format#gff-data-types) | [UTP](GFF-File-Format#utp-placeable) template |
| `Tag` | [CExoString](GFF-File-Format#gff-data-types) | Instance tag override |
| `X`, `Y`, `Z` | Float | [position](MDL-MDX-File-Format#node-header) [coordinates](GFF-File-Format#are-area) |
| `Bearing` | Float | [rotation](MDL-MDX-File-Format#node-header) angle |
| `TweakColor` | DWord | [color](GFF-File-Format#color) tint |
| `Hitpoints` | Short | Current HP override |
| `Useable` | Byte | Can be used override |

**Placeable Spawning:**

- Template defines behavior, appearance
- [GIT](GFF-File-Format#git-game-instance-template) defines placement and [orientation](MDL-MDX-File-Format#node-header)
- Can override usability and HP at instance level

## GITTrigger Instances

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | [ResRef](GFF-File-Format#gff-data-types) | [UTT](GFF-File-Format#utt-trigger) template |
| `Tag` | [CExoString](GFF-File-Format#gff-data-types) | Instance tag |
| `TransitionDestin` | [CExoLocString](GFF-File-Format#gff-data-types) | Transition label |
| `LinkedToModule` | [ResRef](GFF-File-Format#gff-data-types) | Destination module |
| `LinkedTo` | [CExoString](GFF-File-Format#gff-data-types) | Destination waypoint |
| `LinkedToFlags` | Byte | Transition [flags](GFF-File-Format#gff-data-types) |
| `X`, `Y`, `Z` | Float | Trigger [position](MDL-MDX-File-Format#node-header) |
| `XPosition`, `YPosition`, `ZPosition` | Float | Position (alternate) |
| `XOrientation`, `YOrientation`, `ZOrientation` | Float | [orientation](MDL-MDX-File-Format#node-header) |
| `Geometry` | List | Trigger volume [vertices](MDL-MDX-File-Format#vertex-structure) |

**[geometry](MDL-MDX-File-Format#geometry-header) Struct:**

- List of Vector3 points
- Defines trigger boundary polygon
- Planar geometry (Z-axis extrusion)

**Trigger [types](GFF-File-Format#gff-data-types):**

- **Area Transition**: LinkedToModule set
- **Script Trigger**: Fires scripts from [UTT](GFF-File-Format#utt-trigger)
- **Generic Trigger**: Custom behavior

## GITWaypoint Instances

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | [ResRef](GFF-File-Format#gff-data-types) | [UTW](GFF-File-Format#utw-waypoint) template |
| `Tag` | [CExoString](GFF-File-Format#gff-data-types) | Waypoint identifier |
| `Appearance` | DWord | Waypoint appearance type |
| `LinkedTo` | [CExoString](GFF-File-Format#gff-data-types) | Linked waypoint tag |
| `X`, `Y`, `Z` | Float | [position](MDL-MDX-File-Format#node-header) [coordinates](GFF-File-Format#are-area) |
| `XOrientation`, `YOrientation` | Float | [orientation](MDL-MDX-File-Format#node-header) |
| `HasMapNote` | Byte | Has map note |
| `MapNote` | [CExoLocString](GFF-File-Format#gff-data-types) | Map note text |
| `MapNoteEnabled` | Byte | Map note visible |

**Waypoint Usage:**

- **Spawn Points**: Character entry locations
- **Pathfinding**: AI navigation targets
- **Script Targets**: "Go to waypoint X"
- **Map Notes**: Player-visible markers

## GITEncounter Instances

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | [ResRef](GFF-File-Format#gff-data-types) | [UTE](GFF-File-Format#ute-encounter) template |
| `Tag` | [CExoString](GFF-File-Format#gff-data-types) | Encounter identifier |
| `X`, `Y`, `Z` | Float | Spawn [position](MDL-MDX-File-Format#node-header) |
| `Geometry` | List | Spawn zone boundary |

**Encounter System:**

- [geometry](MDL-MDX-File-Format#geometry-header) defines trigger zone
- Engine spawns creatures from [UTE](GFF-File-Format#ute-encounter) when entered
- Respawn behavior from [UTE](GFF-File-Format#ute-encounter) template

## GITStore Instances

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | [ResRef](GFF-File-Format#gff-data-types) | [UTM](GFF-File-Format#utm-merchant) template |
| `Tag` | [CExoString](GFF-File-Format#gff-data-types) | Store identifier |
| `X`, `Y`, `Z` | Float | Position (for UI, not physical) |
| `XOrientation`, `YOrientation` | Float | [orientation](MDL-MDX-File-Format#node-header) |

**Store System:**

- Stores don't have physical presence
- [position](MDL-MDX-File-Format#node-header) used for toolset only
- Accessed via conversations or scripts

## GITSound Instances

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | [ResRef](GFF-File-Format#gff-data-types) | [UTS](GFF-File-Format#uts-sound) template |
| `Tag` | [CExoString](GFF-File-Format#gff-data-types) | Sound identifier |
| `X`, `Y`, `Z` | Float | Emitter [position](MDL-MDX-File-Format#node-header) |
| `MaxDistance` | Float | Audio falloff distance |
| `MinDistance` | Float | Full volume radius |
| `RandomRangeX`, `RandomRangeY` | Float | [position](MDL-MDX-File-Format#node-header) randomization |
| `Volume` | Byte | Volume level (0-127) |

**Positional Audio:**

- 3D sound emitter at [position](MDL-MDX-File-Format#node-header)
- Volume falloff over distance
- Random [offset](GFF-File-Format#file-structure-overview) for variation

## GITCamera Instances

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `CameraID` | Int | Camera identifier |
| `FOV` | Float | [field](GFF-File-Format#file-structure-overview) of view (degrees) |
| `Height` | Float | Camera height |
| `MicRange` | Float | Audio capture range |
| `Orientation` | Vector4 | Camera rotation ([quaternion](MDL-MDX-File-Format#node-header)) |
| `Pitch` | Float | Camera pitch angle |
| `Position` | Vector3 | Camera [position](MDL-MDX-File-Format#node-header) |

**Camera System:**

- Defines fixed camera angles
- Used for cutscenes and dialogue
- FOV controls zoom level

## Implementation Notes

**[GIT](GFF-File-Format#git-game-instance-template) Loading Process:**

1. **Parse [GIT](GFF-File-Format#git-game-instance-template)**: Read [GFF](GFF-File-Format) [structure](GFF-File-Format#file-structure-overview)
2. **Load Templates**: Read [UTC](GFF-File-Format#utc-creature), [UTD](GFF-File-Format#utd-door), [UTP](GFF-File-Format#utp-placeable), etc. [files](GFF-File-Format)
3. **Instantiate Objects**: Create runtime objects from templates
4. **Apply Overrides**: [GIT](GFF-File-Format#git-game-instance-template) [position](MDL-MDX-File-Format#node-header), HP, tag overrides applied
5. **Link Objects**: Resolve LinkedTo references
6. **Execute Spawn Scripts**: Fire OnSpawn events
7. **Activate Triggers**: Register trigger [geometry](MDL-MDX-File-Format#geometry-header)

**Instance vs. Template:**

- **Template ([UTC](GFF-File-Format#utc-creature)/[UTD](GFF-File-Format#utd-door)/[UTP](GFF-File-Format#utp-placeable)/etc.)**: Defines what the object is
- **Instance ([GIT](GFF-File-Format#git-game-instance-template) entry)**: Defines where the object is
- [GIT](GFF-File-Format#git-game-instance-template) can override specific template properties
- Multiple instances can share one template

**Performance Considerations:**

- Large instance counts impact load time
- Complex trigger [geometry](MDL-MDX-File-Format#geometry-header) affects collision checks
- Many sounds can overwhelm audio system
- Creature AI scales with creature [count](GFF-File-Format#file-structure-overview)

**Dynamic vs. Static:**

- **[GIT](GFF-File-Format#git-game-instance-template)**: Dynamic, saved with game progress
- **[ARE](GFF-File-Format#are-area)**: Static, never changes
- [GIT](GFF-File-Format#git-game-instance-template) instances can be destroyed, moved, modified
- [ARE](GFF-File-Format#are-area) properties remain constant

**Save Game Integration:**

- [GIT](GFF-File-Format#git-game-instance-template) state saved in save [files](GFF-File-Format)
- Instance [positions](MDL-MDX-File-Format#node-header), HP, inventory preserved
- Destroyed objects marked as deleted
- New dynamic objects added to save

**Common [GIT](GFF-File-Format#git-game-instance-template) Patterns:**

**Ambush Spawns:**

- Creatures placed outside player view
- Positioned for tactical advantage
- Often linked to trigger activation

**Progression Gates:**

- Locked doors requiring keys/skills
- Triggers that load new modules
- Waypoints marking objectives

**Interactive Areas:**

- Clusters of placeables (containers)
- NPCs for dialogue
- Stores for shopping
- Workbenches for crafting

**Navigation Networks:**

- Waypoints for AI pathfinding
- Logical connections via LinkedTo
- Map notes for player guidance

**Audio Atmosphere:**

- Ambient sound emitters positioned strategically
- Varied volumes and ranges
- Random [offsets](GFF-File-Format#file-structure-overview) for natural feel
