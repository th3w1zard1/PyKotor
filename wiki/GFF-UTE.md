# UTE (Encounter)

Part of the [GFF File Format Documentation](GFF-File-Format).

UTE files define [encounter templates](GFF-File-Format#ute-encounter) which spawn creatures when triggered by the player. Encounters handle spawning logic, difficulty scaling, respawning, and faction settings for groups of enemies or neutral creatures.

**Official Bioware Documentation:** For the authoritative Bioware Aurora Engine Encounter format specification, see [Bioware Aurora Encounter Format](Bioware-Aurora-Encounter).

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/ute.py`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/ute.py)

## Core Identity fields

| field | type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | [ResRef](GFF-File-Format#gff-data-types) | Template identifier for this encounter |
| `Tag` | [CExoString](GFF-File-Format#gff-data-types) | Unique tag for script references |
| `LocalizedName` | [CExoLocString](GFF-File-Format#gff-data-types) | Encounter name (unused in game) |
| `Comment` | [CExoString](GFF-File-Format#gff-data-types) | Developer comment/notes |

## Spawn Configuration

| field | type | Description |
| ----- | ---- | ----------- |
| `Active` | Byte | Encounter is currently active |
| `Difficulty` | Int | Difficulty setting (unused) |
| `DifficultyIndex` | Int | Difficulty scaling index |
| `Faction` | Word | Faction of spawned creatures |
| `MaxCreatures` | Int | Maximum concurrent creatures |
| `RecCreatures` | Int | Recommended number of creatures |
| `SpawnOption` | Int | Spawn behavior (0=Continuous, 1=Single Shot) |

**Spawn Behavior:**

- **Active**: If 0, encounter won't trigger until activated by script
- **MaxCreatures**: Hard limit on spawned entities to prevent overcrowding
- **RecCreatures**: Target number to maintain
- **SpawnOption**: Single Shot encounters fire once and disable

## Respawn Logic

| field | type | Description |
| ----- | ---- | ----------- |
| `Reset` | Byte | Encounter resets after being cleared |
| `ResetTime` | Int | Time in seconds before reset |
| `Respawns` | Int | Number of times it can respawn (-1 = infinite) |

**Respawn System:**

- Allows for renewable enemy sources
- **ResetTime**: Cooldown period after players leave area
- **Respawns**: Limits farming/grinding

## Creature List

| field | type | Description |
| ----- | ---- | ----------- |
| `CreatureList` | List | List of creatures to spawn |

**CreatureList Struct fields:**

- `[ResRef](GFF-File-Format#gff-data-types)` ([ResRef](GFF-File-Format#gff-data-types)): [UTC](GFF-File-Format#utc-creature) template to spawn
- `Appearance` (Int): Appearance type (optional override)
- `CR` (Float): Challenge Rating
- `SingleSpawn` (Byte): Unique spawn [flag](GFF-File-Format#gff-data-types)

**Spawn Selection:**

- Engine selects from CreatureList based on CR and difficulty
- Random selection weighted by difficulty settings

## Trigger Logic

| field | type | Description |
| ----- | ---- | ----------- |
| `PlayerOnly` | Byte | Only triggers for player (not NPCs) |
| `OnEntered` | [ResRef](GFF-File-Format#gff-data-types) | Script fires when trigger entered |
| `OnExit` | [ResRef](GFF-File-Format#gff-data-types) | Script fires when trigger exited |
| `OnExhausted` | [ResRef](GFF-File-Format#gff-data-types) | Script fires when spawns depleted |
| `OnHeartbeat` | [ResRef](GFF-File-Format#gff-data-types) | Script fires periodically |
| `OnUserDefined` | [ResRef](GFF-File-Format#gff-data-types) | Script fires on user events |

**Implementation Notes:**

- Encounters are volumes ([geometry](MDL-MDX-File-Format#geometry-header) defined in [GIT](GFF-File-Format#git-game-instance-template))
- Spawning happens when volume is entered
- Creatures spawn at specific spawn points ([UTW](GFF-File-Format#utw-waypoint)) or random locations
