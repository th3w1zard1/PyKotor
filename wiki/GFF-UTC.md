# UTC (Creature)

Part of the [GFF File Format Documentation](GFF-File-Format).

UTC files define [creature templates](GFF-File-Format#utc-creature) including NPCs, party members, enemies, and the player character. They [ARE](GFF-File-Format#are-area) comprehensive [GFF files](GFF-File-Format) containing all data needed to spawn and control a creature in the game world.

**Official Bioware Documentation:** For the authoritative Bioware Aurora Engine Creature format specification, see [Bioware Aurora Creature Format](Bioware-Aurora-Creature).

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py)

## Core Identity fields

| field | type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | [ResRef](GFF-File-Format#gff-data-types) | Template identifier for this creature |
| `Tag` | [CExoString](GFF-File-Format#gff-data-types) | Unique tag for script/conversation references |
| `FirstName` | [CExoLocString](GFF-File-Format#gff-data-types) | Creature's first name (localized) |
| `LastName` | [CExoLocString](GFF-File-Format#gff-data-types) | Creature's last name (localized) |
| `Comment` | [CExoString](GFF-File-Format#gff-data-types) | Developer comment/notes |

## Appearance & Visuals

| field | type | Description |
| ----- | ---- | ----------- |
| `Appearance_Type` | DWord | index into [`appearance.2da`](2DA-appearance) |
| `PortraitId` | Word | index into [`portraits.2da`](2DA-portraits) |
| `Gender` | Byte | 0=Male, 1=Female, 2=Both, 3=Other, 4=None |
| `Race` | Word | index into [`racialtypes.2da`](2DA-racialtypes) |
| `SubraceIndex` | Byte | Subrace identifier |
| `BodyVariation` | Byte | Body [model](MDL-MDX-File-Format) variation (0-9) |
| `TextureVar` | Byte | [texture](TPC-File-Format) variation (1-9) |
| `SoundSetFile` | Word | index into [sound set table](SSF-File-Format) |

## Core Stats & Attributes

| field | type | Description |
| ----- | ---- | ----------- |
| `Str` | Byte | Strength score (3-255) |
| `Dex` | Byte | Dexterity score (3-255) |
| `Con` | Byte | Constitution score (3-255) |
| `Int` | Byte | Intelligence score (3-255) |
| `Wis` | Byte | Wisdom score (3-255) |
| `Cha` | Byte | Charisma score (3-255) |
| `HitPoints` | Short | Current hit points |
| `CurrentHitPoints` | Short | Alias for hit points |
| `MaxHitPoints` | Short | Maximum hit points |
| `ForcePoints` | Short | Current Force points (KotOR specific) |
| `CurrentForce` | Short | Alias for Force points |
| `MaxForcePoints` | Short | Maximum Force points |

## Character Progression

| field | type | Description |
| ----- | ---- | ----------- |
| `ClassList` | List | List of character classes with levels |
| `Experience` | DWord | Total experience points |
| `LevelUpStack` | List | Pending level-up choices |
| `SkillList` | List | Skill ranks (index + rank) |
| `FeatList` | List | Acquired feats |
| `SpecialAbilityList` | List | Special abilities/powers |

**ClassList Struct fields:**

- `Class` (Int): index into [`classes.2da`](2DA-classes) ([class definitions](2DA-classes))
- `ClassLevel` (Short): Levels in this class

**SkillList Struct fields:**

- `Rank` (Byte): Skill rank value

**FeatList Struct fields:**

- `Feat` (Word): index into [`feat.2da`](2DA-feat) ([feat definitions](2DA-feat))

## Combat & Behavior

| field | type | Description |
| ----- | ---- | ----------- |
| `FactionID` | Word | Faction identifier (determines hostility) |
| `NaturalAC` | Byte | Natural armor class bonus |
| `ChallengeRating` | Float | CR for encounter calculations |
| `PerceptionRange` | Byte | Perception distance category |
| `WalkRate` | Int | Movement speed identifier |
| `Interruptable` | Byte | Can be interrupted during actions |
| `NoPermDeath` | Byte | Cannot permanently die |
| `IsPC` | Byte | Is player character |
| `Plot` | Byte | Plot-critical (cannot die) |
| `MinOneHP` | Byte | Cannot drop below 1 HP |
| `PartyInteract` | Byte | Shows party selection interface |
| `Hologram` | Byte | Rendered as hologram |

## Equipment & Inventory

| field | type | Description |
| ----- | ---- | ----------- |
| `ItemList` | List | Inventory items |
| `Equip_ItemList` | List | Equipped items with slots |
| `EquippedRes` | [ResRef](GFF-File-Format#gff-data-types) | Deprecated equipment field |

**ItemList Struct fields:**

- `InventoryRes` ([ResRef](GFF-File-Format#gff-data-types)): [UTI](GFF-File-Format#uti-item) template [ResRef](GFF-File-Format#gff-data-types)
- `Repos_PosX` (Word): Inventory grid X position
- `Repos_Posy` (Word): Inventory grid Y position
- `Dropable` (Byte): Can be dropped/removed

**Equip_ItemList Struct fields:**

- `EquippedRes` ([ResRef](GFF-File-Format#gff-data-types)): [UTI](GFF-File-Format#uti-item) template [ResRef](GFF-File-Format#gff-data-types)
- Equipment slots reference `equipmentslots.2da`

## Script Hooks

| field | type | Description |
| ----- | ---- | ----------- |
| `ScriptAttacked` | [ResRef](GFF-File-Format#gff-data-types) | Fires when attacked |
| `ScriptDamaged` | [ResRef](GFF-File-Format#gff-data-types) | Fires when damaged |
| `ScriptDeath` | [ResRef](GFF-File-Format#gff-data-types) | Fires on death |
| `ScriptDialogue` | [ResRef](GFF-File-Format#gff-data-types) | Fires when conversation starts |
| `ScriptDisturbed` | [ResRef](GFF-File-Format#gff-data-types) | Fires when inventory disturbed |
| `ScriptEndRound` | [ResRef](GFF-File-Format#gff-data-types) | Fires at combat round end |
| `ScriptEndDialogue` | [ResRef](GFF-File-Format#gff-data-types) | Fires when conversation ends |
| `ScriptHeartbeat` | [ResRef](GFF-File-Format#gff-data-types) | Fires periodically |
| `ScriptOnBlocked` | [ResRef](GFF-File-Format#gff-data-types) | Fires when movement blocked |
| `ScriptOnNotice` | [ResRef](GFF-File-Format#gff-data-types) | Fires when notices something |
| `ScriptRested` | [ResRef](GFF-File-Format#gff-data-types) | Fires after rest |
| `ScriptSpawn` | [ResRef](GFF-File-Format#gff-data-types) | Fires on spawn |
| `ScriptSpellAt` | [ResRef](GFF-File-Format#gff-data-types) | Fires when spell cast at creature |
| `ScriptUserDefine` | [ResRef](GFF-File-Format#gff-data-types) | Fires on user-defined events |

## KotOR-Specific Features

**Alignment:**

- `GoodEvil` (Byte): 0-100 scale (0=Dark, 100=Light)
- `LawfulChaotic` (Byte): Unused in KotOR

**Multiplayer (Unused in KotOR):**

- `Deity` ([CExoString](GFF-File-Format#gff-data-types))
- `Subrace` ([CExoString](GFF-File-Format#gff-data-types))
- `Morale` (Byte)
- `MorealBreak` (Byte)

**Special Abilities:**

- Stored in `SpecialAbilityList` referencing `spells.2da` or feat-based abilities

## Implementation Notes

[UTC](GFF-File-Format#utc-creature) files [ARE](GFF-File-Format#are-area) loaded during module initialization or creature spawning. The engine:

1. **Reads template data** from the [UTC](GFF-File-Format#utc-creature) [GFF](GFF-File-Format) structure
2. **Applies appearance** based on [`appearance.2da`](2DA-appearance) ([appearance definitions](2DA-appearance)) lookup
3. **Calculates derived stats** (AC, saves, attack bonuses) from attributes and equipment
4. **Loads inventory** by instantiating [UTI](GFF-File-Format#uti-item) ([item templates](GFF-File-Format#uti-item)) templates
5. **Applies effects** from equipped items and active powers
6. **Registers scripts** ([NCS files](NCS-File-Format)) for the creature's event handlers

**Performance Considerations:**

- Complex creatures with many items/feats increase load time
- Script hooks fire frequently - keep handlers optimized
- Large SkillList/FeatList structures add memory overhead

**Common Use Cases:**

- **Party Members**: Full [UTC](GFF-File-Format#utc-creature) with all progression data, complex equipment
- **Plot NPCs**: Basic stats, specific appearance, dialogue scripts
- **Generic Enemies**: Minimal data, shared appearance, basic AI scripts
- **Vendors**: Specialized with store inventory, merchant scripts
- **Placeables As Creatures**: Invisible creatures for complex scripting
