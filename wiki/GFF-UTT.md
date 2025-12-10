# UTT (Trigger)

Part of the [GFF File Format Documentation](GFF-File-Format).

UTT [files](GFF-File-Format) define [trigger templates](GFF-File-Format#utt-trigger) for invisible volumes that fire scripts when entered, exited, or used. Triggers [ARE](GFF-File-Format#are-area) essential for area transitions, cutscenes, traps, and game logic.

**Official Bioware Documentation:** For the authoritative Bioware Aurora Engine Trigger [format](GFF-File-Format) specification, see [Bioware Aurora Trigger Format](Bioware-Aurora-Trigger).

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utt.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utt.py)

## Core Identity [fields](GFF-File-Format#file-structure-overview)

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | [ResRef](GFF-File-Format#gff-data-types) | Template identifier for this trigger |
| `Tag` | [CExoString](GFF-File-Format#gff-data-types) | Unique tag for script references |
| `LocName` | [CExoLocString](GFF-File-Format#gff-data-types) | Trigger name (localized) |
| `Comment` | [CExoString](GFF-File-Format#gff-data-types) | Developer comment/notes |

## Trigger Configuration

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `Type` | Int | Trigger type (0=Generic, 1=Transition, 2=Trap) |
| `Faction` | Word | Faction identifier |
| `Cursor` | Int | Cursor icon when hovered (0=None, 1=Door, etc) |
| `HighlightHeight` | Float | Height of selection highlight |

**Trigger [types](GFF-File-Format#gff-data-types):**

- **Generic**: Script execution volume
- **Transition**: Loads new module or moves to waypoint
- **Trap**: Damages/effects entering object

## Transition Settings

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `LinkedTo` | [CExoString](GFF-File-Format#gff-data-types) | Destination waypoint tag |
| `LinkedToModule` | [ResRef](GFF-File-Format#gff-data-types) | Destination module [ResRef](GFF-File-Format#gff-data-types) |
| `LinkedToFlags` | Byte | Transition behavior [flags](GFF-File-Format#gff-data-types) |
| `LoadScreenID` | Word | Loading screen ID |
| `PortraitId` | Word | Portrait ID (unused) |

**Area Transitions:**

- **LinkedToModule**: Target module to load
- **LinkedTo**: Waypoint where player spawns
- **LoadScreenID**: Image displayed during load

## Trap System

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `TrapFlag` | Byte | Trigger is a trap |
| `TrapType` | Byte | [index](2DA-File-Format#row-labels) into `traps.2da` |
| `TrapDetectable` | Byte | Can be detected |
| `TrapDetectDC` | Byte | Awareness DC to detect |
| `TrapDisarmable` | Byte | Can be disarmed |
| `DisarmDC` | Byte | Security DC to disarm |
| `TrapOneShot` | Byte | Fires once then disables |
| `AutoRemoveKey` | Byte | [KEY](KEY-File-Format) removed on use |
| `KeyName` | [CExoString](GFF-File-Format#gff-data-types) | [KEY](KEY-File-Format) tag required to disarm/bypass |

**Trap Mechanics:**

- Floor traps (mines, pressure plates) [ARE](GFF-File-Format#are-area) triggers
- Detection makes trap visible and clickable
- Entering without disarm triggers trap effect

## Script Hooks

| [field](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#gff-data-types) | Description |
| ----- | ---- | ----------- |
| `OnClick` | [ResRef](GFF-File-Format#gff-data-types) | Fires when clicked |
| `OnDisarm` | [ResRef](GFF-File-Format#gff-data-types) | Fires when disarmed |
| `OnHeartbeat` | [ResRef](GFF-File-Format#gff-data-types) | Fires periodically |
| `OnScriptEnter` | [ResRef](GFF-File-Format#gff-data-types) | Fires when object enters |
| `OnScriptExit` | [ResRef](GFF-File-Format#gff-data-types) | Fires when object exits |
| `OnTrapTriggered` | [ResRef](GFF-File-Format#gff-data-types) | Fires when trap activates |
| `OnUserDefined` | [ResRef](GFF-File-Format#gff-data-types) | Fires on user event |

**Scripting:**

- **OnScriptEnter**: Most common hook (cutscenes, spawns)
- **OnHeartbeat**: Area-of-effect damage/buffs
- **OnClick**: Used for interactive transitions
