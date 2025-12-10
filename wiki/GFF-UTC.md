# UTC (Creature)

Part of the [GFF File Format Documentation](GFF-File-Format).

UTC [files](GFF-File-Format) define [creature templates](GFF-File-Format#utc-creature) including NPCs, party members, enemies, and the player character. They [ARE](GFF-File-Format#are-area) comprehensive [GFF files](GFF-File-Format) containing all [data](GFF-File-Format#file-structure) needed to spawn and control a creature in the game world.

**Official Bioware Documentation:** For the authoritative Bioware Aurora Engine Creature [format](GFF-File-Format) specification, see [Bioware Aurora Creature Format](Bioware-Aurora-Creature).

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py)

## Core Identity [fields](GFF-File-Format#file-structure)

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | [ResRef](GFF-File-Format#resref) | Template identifier for this creature |
| `Tag` | [CExoString](GFF-File-Format#cexostring) | Unique tag for script/conversation references |
| `FirstName` | [CExoLocString](GFF-File-Format#localizedstring) | Creature's first name (localized) |
| `LastName` | [CExoLocString](GFF-File-Format#localizedstring) | Creature's last name (localized) |
| `Comment` | [CExoString](GFF-File-Format#cexostring) | Developer comment/notes |

## Appearance & Visuals

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
| ----- | ---- | ----------- |
| `Appearance_Type` | DWord | [index](2DA-File-Format#row-labels) into [`appearance.2da`](2DA-appearance) |
| `PortraitId` | Word | [index](2DA-File-Format#row-labels) into [`portraits.2da`](2DA-portraits) |
| `Gender` | Byte | 0=Male, 1=Female, 2=Both, 3=Other, 4=None |
| `Race` | Word | [index](2DA-File-Format#row-labels) into [`racialtypes.2da`](2DA-racialtypes) |
| `SubraceIndex` | Byte | Subrace identifier |
| `BodyVariation` | Byte | Body [model](MDL-MDX-File-Format) variation (0-9) |
| `TextureVar` | Byte | [texture](TPC-File-Format) variation (1-9) |
| `SoundSetFile` | Word | [index](2DA-File-Format#row-labels) into [sound set table](SSF-File-Format) |

## Core Stats & Attributes

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
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

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
| ----- | ---- | ----------- |
| `ClassList` | List | List of character classes with levels |
| `Experience` | DWord | Total experience points |
| `LevelUpStack` | List | Pending level-up choices |
| `SkillList` | List | Skill ranks ([index](2DA-File-Format#row-labels) + rank) |
| `FeatList` | List | Acquired feats |
| `SpecialAbilityList` | List | Special abilities/powers |

**ClassList Struct [fields](GFF-File-Format#file-structure):**

- `Class` (Int): [index](2DA-File-Format#row-labels) into [`classes.2da`](2DA-classes) ([class definitions](2DA-classes))
- `ClassLevel` (Short): Levels in this class

**SkillList Struct [fields](GFF-File-Format#file-structure):**

- `Rank` (Byte): Skill rank [value](GFF-File-Format#data-types)

**FeatList Struct [fields](GFF-File-Format#file-structure):**

- `Feat` (Word): [index](2DA-File-Format#row-labels) into [`feat.2da`](2DA-feat) ([feat definitions](2DA-feat))

## Combat & Behavior

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
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

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
| ----- | ---- | ----------- |
| `ItemList` | List | Inventory items |
| `Equip_ItemList` | List | Equipped items with slots |
| `EquippedRes` | [ResRef](GFF-File-Format#resref) | Deprecated equipment [field](GFF-File-Format#file-structure) |

**ItemList Struct [fields](GFF-File-Format#file-structure):**

- `InventoryRes` ([ResRef](GFF-File-Format#resref)): [UTI](GFF-File-Format#uti-item) template [ResRef](GFF-File-Format#resref)
- `Repos_PosX` (Word): Inventory grid X [position](MDL-MDX-File-Format#node-header)
- `Repos_Posy` (Word): Inventory grid Y [position](MDL-MDX-File-Format#node-header)
- `Dropable` (Byte): Can be dropped/removed

**Equip_ItemList Struct [fields](GFF-File-Format#file-structure):**

- `EquippedRes` ([ResRef](GFF-File-Format#resref)): [UTI](GFF-File-Format#uti-item) template [ResRef](GFF-File-Format#resref)
- Equipment slots reference `equipmentslots.2da`

## Script Hooks

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
| ----- | ---- | ----------- |
| `ScriptAttacked` | [ResRef](GFF-File-Format#resref) | Fires when attacked |
| `ScriptDamaged` | [ResRef](GFF-File-Format#resref) | Fires when damaged |
| `ScriptDeath` | [ResRef](GFF-File-Format#resref) | Fires on death |
| `ScriptDialogue` | [ResRef](GFF-File-Format#resref) | Fires when conversation starts |
| `ScriptDisturbed` | [ResRef](GFF-File-Format#resref) | Fires when inventory disturbed |
| `ScriptEndRound` | [ResRef](GFF-File-Format#resref) | Fires at combat round end |
| `ScriptEndDialogue` | [ResRef](GFF-File-Format#resref) | Fires when conversation ends |
| `ScriptHeartbeat` | [ResRef](GFF-File-Format#resref) | Fires periodically |
| `ScriptOnBlocked` | [ResRef](GFF-File-Format#resref) | Fires when movement blocked |
| `ScriptOnNotice` | [ResRef](GFF-File-Format#resref) | Fires when notices something |
| `ScriptRested` | [ResRef](GFF-File-Format#resref) | Fires after rest |
| `ScriptSpawn` | [ResRef](GFF-File-Format#resref) | Fires on spawn |
| `ScriptSpellAt` | [ResRef](GFF-File-Format#resref) | Fires when spell cast at creature |
| `ScriptUserDefine` | [ResRef](GFF-File-Format#resref) | Fires on user-defined events |

## KotOR-Specific Features

**Alignment:**

- `GoodEvil` (Byte): 0-100 scale (0=Dark, 100=Light)
- `LawfulChaotic` (Byte): Unused in KotOR

**Multiplayer (Unused in KotOR):**

- `Deity` ([CExoString](GFF-File-Format#cexostring))
- `Subrace` ([CExoString](GFF-File-Format#cexostring))
- `Morale` (Byte)
- `MorealBreak` (Byte)

**Special Abilities:**

- Stored in `SpecialAbilityList` referencing `spells.2da` or feat-based abilities

## Implementation Notes

[UTC](GFF-File-Format#utc-creature) [files](GFF-File-Format) [ARE](GFF-File-Format#are-area) loaded during module initialization or creature spawning. The engine:

1. **Reads template [data](GFF-File-Format#file-structure)** from the [UTC](GFF-File-Format#utc-creature) [GFF](GFF-File-Format) [structure](GFF-File-Format#file-structure)
2. **Applies appearance** based on [`appearance.2da`](2DA-appearance) ([appearance definitions](2DA-appearance)) lookup
3. **Calculates derived stats** (AC, saves, attack bonuses) from attributes and equipment
4. **Loads inventory** by instantiating [UTI](GFF-File-Format#uti-item) ([item templates](GFF-File-Format#uti-item)) templates
5. **Applies effects** from equipped items and active powers
6. **Registers scripts** ([NCS files](NCS-File-Format)) for the creature's event handlers

**Performance Considerations:**

- Complex creatures with many items/feats increase load time
- Script hooks fire frequently - keep handlers optimized
- Large SkillList/FeatList [structures](GFF-File-Format#file-structure) add memory overhead

**Common Use Cases:**

- **Party Members**: Full [UTC](GFF-File-Format#utc-creature) with all progression [data](GFF-File-Format#file-structure), complex equipment
- **Plot NPCs**: Basic stats, specific appearance, dialogue scripts
- **Generic Enemies**: Minimal [data](GFF-File-Format#file-structure), shared appearance, basic AI scripts
- **Vendors**: Specialized with store inventory, merchant scripts
- **Placeables As Creatures**: Invisible creatures for complex scripting
