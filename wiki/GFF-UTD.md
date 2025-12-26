# UTD (Door)

Part of the [GFF File Format Documentation](GFF-File-Format).

UTD files define [door templates](GFF-File-Format#utd-door) for all interactive doors in the game world. Doors can be locked, require keys, have hit points, conversations, and various gameplay interactions.

**Official Bioware Documentation:** For the authoritative Bioware Aurora Engine Door/Placeable format specification, see [Bioware Aurora Door/Placeable GFF Format](Bioware-Aurora-DoorPlaceableGFF).

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utd.py`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utd.py)

## Core Identity fields

| field | type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | [ResRef](GFF-File-Format#gff-data-types) | Template identifier for this door |
| `Tag` | [CExoString](GFF-File-Format#gff-data-types) | Unique tag for script references |
| `LocName` | [CExoLocString](GFF-File-Format#gff-data-types) | Door name (localized) |
| `Description` | [CExoLocString](GFF-File-Format#gff-data-types) | Door description |
| `Comment` | [CExoString](GFF-File-Format#gff-data-types) | Developer comment/notes |

## Door Appearance & type

| field | type | Description |
| ----- | ---- | ----------- |
| `Appearance` | DWord | index into `genericdoors.2da` |
| `GenericType` | DWord | Generic door type category |
| `AnimationState` | Byte | Current [animation](MDL-MDX-File-Format#animation-header) state (always 0 in templates) |

**Appearance System:**

- `genericdoors.2da` defines door [models](MDL-MDX-File-Format) and [animations](MDL-MDX-File-Format#animation-header)
- Different appearance types support different behaviors
- Opening [animation](MDL-MDX-File-Format#animation-header) determined by appearance entry

## Locking & Security

| field | type | Description |
| ----- | ---- | ----------- |
| `Locked` | Byte | Door is currently locked |
| `Lockable` | Byte | Door can be locked/unlocked |
| `KeyRequired` | Byte | Requires specific [KEY](KEY-File-Format) item |
| `KeyName` | [CExoString](GFF-File-Format#gff-data-types) | Tag of required [KEY](KEY-File-Format) item |
| `AutoRemoveKey` | Byte | [KEY](KEY-File-Format) consumed on use |
| `OpenLockDC` | Byte | Security skill DC to pick lock |
| `CloseLockDC` (KotOR2) | [byte](GFF-File-Format#gff-data-types) | Security skill DC to lock door |

**Lock Mechanics:**

- **Locked**: Door cannot be opened normally
- **KeyRequired**: Must have [KEY](KEY-File-Format) in inventory
- **OpenLockDC**: Player rolls Security skill vs. DC
- **AutoRemoveKey**: [KEY](KEY-File-Format) destroyed after successful use

## Hit Points & Durability

| field | type | Description |
| ----- | ---- | ----------- |
| `HP` | Short | Maximum hit points |
| `CurrentHP` | Short | Current hit points |
| `Hardness` | Byte | Damage reduction |
| `Min1HP` (KotOR2) | [byte](GFF-File-Format#gff-data-types) | Cannot drop below 1 HP |
| `Fort` | Byte | Fortitude save (always 0) |
| `Ref` | Byte | Reflex save (always 0) |
| `Will` | Byte | Will save (always 0) |

**Destructible Doors:**

- Doors with HP can be attacked and destroyed
- **Hardness** reduces each hit's damage
- **Min1HP** prevents destruction (plot doors)
- Save values unused in KotOR

## Interaction & Behavior

| field | type | Description |
| ----- | ---- | ----------- |
| `Plot` | Byte | Plot-critical (cannot be destroyed) |
| `Static` | Byte | Door is static geometry (no interaction) |
| `Interruptable` | Byte | Opening can be interrupted |
| `Conversation` | [ResRef](GFF-File-Format#gff-data-types) | Dialog file when used |
| `Faction` | Word | Faction identifier |
| `AnimationState` | Byte | Starting animation (0=closed, other values unused) |

**Conversation Doors:**

- When clicked, triggers dialogue instead of opening
- Useful for password entry, NPC interactions
- Dialog can conditionally open door via script

## Script Hooks

| field | type | Description |
| ----- | ---- | ----------- |
| `OnOpen` | [ResRef](GFF-File-Format#gff-data-types) | Fires when door opens |
| `OnClose` | [ResRef](GFF-File-Format#gff-data-types) | Fires when door closes |
| `OnClosed` | [ResRef](GFF-File-Format#gff-data-types) | Fires after door finishes closing |
| `OnDamaged` | [ResRef](GFF-File-Format#gff-data-types) | Fires when door takes damage |
| `OnDeath` | [ResRef](GFF-File-Format#gff-data-types) | Fires when door is destroyed |
| `OnDisarm` | [ResRef](GFF-File-Format#gff-data-types) | Fires when trap is disarmed |
| `OnHeartbeat` | [ResRef](GFF-File-Format#gff-data-types) | Fires periodically |
| `OnLock` | [ResRef](GFF-File-Format#gff-data-types) | Fires when door is locked |
| `OnMeleeAttacked` | [ResRef](GFF-File-Format#gff-data-types) | Fires when attacked in melee |
| `OnSpellCastAt` | [ResRef](GFF-File-Format#gff-data-types) | Fires when spell cast at door |
| `OnUnlock` | [ResRef](GFF-File-Format#gff-data-types) | Fires when door is unlocked |
| `OnUserDefined` | [ResRef](GFF-File-Format#gff-data-types) | Fires on user-defined events |
| `OnClick` | [ResRef](GFF-File-Format#gff-data-types) | Fires when clicked |
| `OnFailToOpen` (KotOR2) | [ResRef](GFF-File-Format#gff-data-types) | Fires when opening fails |

## Trap System

| field | type | Description |
| ----- | ---- | ----------- |
| `TrapDetectable` | Byte | Trap can be detected |
| `TrapDetectDC` | Byte | Awareness DC to detect trap |
| `TrapDisarmable` | Byte | Trap can be disarmed |
| `DisarmDC` | Byte | Security DC to disarm trap |
| `TrapFlag` | Byte | Trap is active |
| `TrapOneShot` | Byte | Trap triggers only once |
| `TrapType` | Byte | index into `traps.2da` |

**Trap Mechanics:**

1. **Detection**: Player rolls Awareness vs. `TrapDetectDC`
2. **Disarm**: Player rolls Security vs. `DisarmDC`
3. **Trigger**: If not detected/disarmed, trap fires on door use
4. **One-Shot**: Trap disabled after first trigger

## Load-Bearing Doors (KotOR2)

| field | type | Description |
| ----- | ---- | ----------- |
| `LoadScreenID` (KotOR2) | Word | Loading screen to show |
| `LinkedTo` (KotOR2) | [CExoString](GFF-File-Format#gff-data-types) | Destination module tag |
| `LinkedToFlags` (KotOR2) | [byte](GFF-File-Format#gff-data-types) | Transition behavior [flags](GFF-File-Format#gff-data-types) |
| `LinkedToModule` (KotOR2) | [ResRef](GFF-File-Format#gff-data-types) | Destination module [ResRef](GFF-File-Format#gff-data-types) |
| `TransitionDestin` (KotOR2) | [CExoLocString](GFF-File-Format#gff-data-types) | Destination label |

**Transition System:**

- Doors can load new modules/areas
- Loading screen displayed during transition
- Linked destination defines spawn point

## Appearance Customization

| field | type | Description |
| ----- | ---- | ----------- |
| `PortraitId` | Word | Portrait icon identifier |
| `PaletteID` | Byte | Toolset palette category |

**Visual Representation:**

- `Appearance` determines 3D [model](MDL-MDX-File-Format)
- Some doors have customizable [textures](TPC-File-Format)
- Portrait used in UI elements

## Implementation Notes

**Door State Machine:**

Doors maintain runtime state:

1. **Closed**: Default state, blocking
2. **Opening**: [animation](MDL-MDX-File-Format#animation-header) playing, becoming non-blocking
3. **Open**: Fully open, non-blocking
4. **Closing**: [animation](MDL-MDX-File-Format#animation-header) playing, becoming blocking
5. **Locked**: Closed and cannot open
6. **Destroyed**: Hit points depleted, permanently open

**Opening Sequence:**

1. Player clicks door
2. If conversation set, start dialog
3. If locked, check for [KEY](KEY-File-Format) or Security skill
4. If trapped, check for detection/disarm
5. Fire `OnOpen` script
6. Play opening [animation](MDL-MDX-File-Format#animation-header)
7. Transition to "open" state

**Locking System:**

- **Lockable=0**: Door cannot be locked (always opens)
- **Locked=1, KeyRequired=1**: Must have specific [KEY](KEY-File-Format)
- **Locked=1, OpenLockDC>0**: Can pick lock with Security skill
- **Locked=1, KeyRequired=0, OpenLockDC=0**: Locked via script only

**Common Door types:**

**Standard Doors:**

- Simple open/close
- No lock, HP, or trap
- Used for interior navigation

**Locked Doors:**

- Requires [KEY](KEY-File-Format) or Security skill
- Quest progression gates
- May have conversation for passwords

**Destructible Doors:**

- Have HP and Hardness
- Can be bashed down
- Alternative to lockpicking

**Trapped Doors:**

- Trigger trap on opening
- Require detection and disarming
- Often in hostile areas

**Transition Doors:**

- Load new modules/areas
- Show loading screens
- Used for major location changes

**Conversation Doors:**

- Trigger dialog on click
- May open after conversation
- Used for password entry, riddles
