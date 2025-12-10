# UTP (Placeable)

Part of the [GFF File Format Documentation](GFF-File-Format).

[UTP files](GFF-File-Format#utp-placeable) define [placeable object templates](GFF-File-Format#utp-placeable) including containers, furniture, switches, workbenches, and interactive environmental objects. [Placeables](GFF-File-Format#utp-placeable) can have inventories, be destroyed, locked, trapped, and trigger [scripts](NCS-File-Format).

**Official Bioware Documentation:** For the authoritative Bioware Aurora Engine Door/Placeable [format](GFF-File-Format) specification, see [Bioware Aurora Door/Placeable GFF Format](Bioware-Aurora-DoorPlaceableGFF).

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utp.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utp.py)

## Core Identity [fields](GFF-File-Format#file-structure-overview)

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | [ResRef](GFF-File-Format#gff-data-types) | Template identifier for this placeable |
| `Tag` | [CExoString](GFF-File-Format#gff-data-types) | Unique tag for script references |
| `LocName` | [CExoLocString](GFF-File-Format#gff-data-types) | Placeable name (localized) |
| `Description` | [CExoLocString](GFF-File-Format#gff-data-types) | Placeable description |
| `Comment` | [CExoString](GFF-File-Format#gff-data-types) | Developer comment/notes |

## Appearance & [type](GFF-File-Format#gff-data-types)

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `Appearance` | DWord | [index](2DA-File-Format#row-labels) into [`placeables.2da`](2DA-placeables) |
| `Type` | Byte | Placeable [type](GFF-File-Format#gff-data-types) category |
| `AnimationState` | Byte | Current [animation](MDL-MDX-File-Format#animation-header) state |

**Appearance System:**

- [`placeables.2da`](2DA-placeables) defines [models](MDL-MDX-File-Format), lighting, and sounds
- Appearance determines visual [model](MDL-MDX-File-Format) and interaction [animation](MDL-MDX-File-Format#animation-header)
- [type](GFF-File-Format#gff-data-types) influences behavior (container, switch, generic)

## Inventory System

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `HasInventory` | Byte | Placeable contains items |
| `ItemList` | List | Items in inventory |
| `BodyBag` | Byte | Container for corpse loot |

**ItemList Struct [fields](GFF-File-Format#file-structure-overview):**

- `InventoryRes` ([ResRef](GFF-File-Format#gff-data-types)): [UTI](GFF-File-Format#uti-item) template [ResRef](GFF-File-Format#gff-data-types)
- `Repos_PosX` (Word): Grid X position (optional)
- `Repos_Posy` (Word): Grid Y position (optional)
- `Dropable` (Byte): Can drop item

**Container Behavior:**

- **HasInventory=1**: Can be looted
- **BodyBag=1**: Corpse container (special loot rules)
- ItemList populated on placeable instantiation
- Empty containers can still be interacted with

## Locking & Security

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `Locked` | Byte | Placeable is currently locked |
| `Lockable` | Byte | Can be locked/unlocked |
| `KeyRequired` | Byte | Requires specific [KEY](KEY-File-Format) item |
| `KeyName` | [CExoString](GFF-File-Format#gff-data-types) | Tag of required [KEY](KEY-File-Format) [item](GFF-File-Format#uti-item) |
| `AutoRemoveKey` | Byte | [KEY](KEY-File-Format) consumed on use |
| `OpenLockDC` | Byte | Security skill DC to pick lock |
| `CloseLockDC` (KotOR2) | [byte](GFF-File-Format#gff-data-types) | Security DC to lock |
| `OpenLockDiff` (KotOR2) | Int | Additional difficulty modifier |
| `OpenLockDiffMod` (KotOR2) | Int | Modifier to difficulty |

**Lock Mechanics:**

- Identical to [UTD](GFF-File-Format#utd-door) door locking system
- Prevents access to inventory
- Can be picked or opened with [KEY](KEY-File-Format)

## Hit Points & Durability

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `HP` | Short | Maximum hit points |
| `CurrentHP` | Short | Current hit points |
| `Hardness` | Byte | Damage reduction |
| `Min1HP` (KotOR2) | [byte](GFF-File-Format#gff-data-types) | Cannot drop below 1 HP |
| `Fort` | Byte | Fortitude save (usually 0) |
| `Ref` | Byte | Reflex save (usually 0) |
| `Will` | Byte | Will save (usually 0) |

**Destructible Placeables:**

- Containers, crates, and terminals can have HP
- Some placeables reveal items when destroyed
- Hardness reduces incoming damage

## Interaction & Behavior

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `Plot` | Byte | Plot-critical (cannot be destroyed) |
| `Static` | Byte | Static geometry (no interaction) |
| `Useable` | Byte | Can be clicked/used |
| `Conversation` | [ResRef](GFF-File-Format#gff-data-types) | [Dialog](GFF-DLG) [file](GFF-File-Format) when used |
| `Faction` | Word | Faction identifier |
| `PartyInteract` | Byte | Requires party member selection |
| `NotBlastable` (KotOR2) | [byte](GFF-File-Format#gff-data-types) | Immune to area damage |

**Usage Patterns:**

- **Useable=0**: Cannot be directly interacted with
- **Conversation**: Triggers dialog on use (terminals, panels)
- **PartyInteract**: Shows party selection [GUI](GFF-File-Format#gui-graphical-user-interface)
- **Static**: Pure visual element, no gameplay

## Script Hooks

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `OnClosed` | [ResRef](GFF-File-Format#gff-data-types) | Fires when container closes |
| `OnDamaged` | [ResRef](GFF-File-Format#gff-data-types) | Fires when placeable takes damage |
| `OnDeath` | [ResRef](GFF-File-Format#gff-data-types) | Fires when placeable is destroyed |
| `OnDisarm` | [ResRef](GFF-File-Format#gff-data-types) | Fires when trap is disarmed |
| `OnEndDialogue` | [ResRef](GFF-File-Format#gff-data-types) | Fires when conversation ends |
| `OnHeartbeat` | [ResRef](GFF-File-Format#gff-data-types) | Fires periodically |
| `OnInvDisturbed` | [ResRef](GFF-File-Format#gff-data-types) | Fires when inventory changed |
| `OnLock` | [ResRef](GFF-File-Format#gff-data-types) | Fires when locked |
| `OnMeleeAttacked` | [ResRef](GFF-File-Format#gff-data-types) | Fires when attacked in melee |
| `OnOpen` | [ResRef](GFF-File-Format#gff-data-types) | Fires when opened |
| `OnSpellCastAt` | [ResRef](GFF-File-Format#gff-data-types) | Fires when spell cast at placeable |
| `OnUnlock` | [ResRef](GFF-File-Format#gff-data-types) | Fires when unlocked |
| `OnUsed` | [ResRef](GFF-File-Format#gff-data-types) | Fires when used/clicked |
| `OnUserDefined` | [ResRef](GFF-File-Format#gff-data-types) | Fires on user-defined events |
| `OnFailToOpen` (KotOR2) | [ResRef](GFF-File-Format#gff-data-types) | Fires when opening fails |

## Trap System

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `TrapDetectable` | Byte | Trap can be detected |
| `TrapDetectDC` | Byte | Awareness DC to detect trap |
| `TrapDisarmable` | Byte | Trap can be disarmed |
| `DisarmDC` | Byte | Security DC to disarm trap |
| `TrapFlag` | Byte | Trap is active |
| `TrapOneShot` | Byte | Trap triggers only once |
| `TrapType` | Byte | [index](2DA-File-Format#row-labels) into [`traps.2da`](2DA-traps) ([trap definitions](2DA-traps)) |

**Trap Behavior:**

- Identical to door trap system
- Triggers on placeable use
- Common on containers and terminals

## Visual Customization

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `PortraitId` | Word | Portrait icon identifier |
| `PaletteID` | Byte | Toolset palette category |

**[model](MDL-MDX-File-Format) & Lighting:**

- Appearance determines [model](MDL-MDX-File-Format) and light [color](GFF-File-Format#color)
- Some placeables have animated components
- Light properties defined in [`placeables.2da`](2DA-placeables)

## Implementation Notes

**Placeable Categories:**

**Containers:**

- Footlockers, crates, corpses
- Have inventory (ItemList populated)
- Can be locked, trapped, destroyed
- `HasInventory=1`, `BodyBag` [flag](GFF-File-Format#gff-data-types) for corpses

**Switches & Terminals:**

- Trigger scripts or conversations
- No inventory typically
- `Useable=1`, `Conversation` or scripts set
- Common for puzzle activation

**Workbenches:**

- Special placeable [type](GFF-File-Format#gff-data-types) for crafting
- Opens crafting interface on use
- Defined by [type](GFF-File-Format#gff-data-types) or Appearance

**Furniture:**

- Non-interactive decoration
- `Static=1` or `Useable=0`
- Pure visual elements

**Environmental Objects:**

- Explosive containers, power generators
- Can be destroyed with effects
- Often have HP and OnDeath scripts

**Instantiation Flow:**

1. **Template Load**: [GFF](GFF-File-Format) parsed from [UTP](GFF-File-Format#utp-placeable)
2. **Appearance Setup**: [model](MDL-MDX-File-Format) loaded from [`placeables.2da`](2DA-placeables)
3. **Inventory Population**: ItemList instantiated
4. **Lock State**: Locked status applied
5. **Trap Activation**: Trap armed if configured
6. **Script Registration**: Event handlers registered

**Container Loot:**

- ItemList defines initial inventory
- Random loot can be added via script
- OnInvDisturbed fires when items taken
- BodyBag containers have special loot rules

**Conversation Placeables:**

- Terminals, control panels, puzzle interfaces
- Conversation property set to [DLG](GFF-DLG) [file](GFF-File-Format)
- Use triggers dialog instead of direct interaction
- Dialog can have conditional responses

**Common Placeable [types](GFF-File-Format#gff-data-types):**

**Storage Containers:**

- Footlockers, crates, bins
- Standard inventory interface
- Often locked or trapped

**Corpses:**

- BodyBag [flag](GFF-File-Format#gff-data-types) set
- Contain enemy loot
- Disappear when looted (usually)

**Terminals:**

- Computer interfaces
- Trigger conversations or scripts
- May require Computer Use skill checks

**Switches:**

- Activate doors, puzzles, machinery
- Fire OnUsed script
- Visual feedback [animation](MDL-MDX-File-Format#animation-header)

**Workbenches:**

- Crafting interface activation
- Lab stations, upgrade benches
- Special [type](GFF-File-Format#gff-data-types) [value](GFF-File-Format#gff-data-types)

**Decorative Objects:**

- No gameplay interaction
- Static or non-useable
- Environmental detail

**Mines (Special Case):**

- Placed as placeable or creature
- Trap properties define behavior
- Can be detected and disarmed
- Trigger on proximity or interaction
