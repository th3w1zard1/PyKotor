# KotOR LYT files format Documentation

LYT (Layout) files define how area [room models](LYT-File-Format#room-definitions) are positioned inside a module. They are plain-text descriptors that list room placements, swoop-track props, obstacles, and door hook transforms. The engine combines this data with [MDL](MDL-MDX-File-Format)/[MDX](MDL-MDX-File-Format) [geometry](MDL-MDX-File-Format#geometry-header) to assemble the final area.

## Table of Contents

- KotOR LYT files format Documentation
  - Table of Contents
  - [format Overview](#format-overview)
  - [Syntax](#syntax)
    - [Room Definitions](#room-definitions)
    - [Track Definitions](#track-definitions)
    - [Obstacle Definitions](#obstacle-definitions)
    - [Door Hooks](#door-hooks)
  - [coordinate System](#coordinate-system)
  - [Implementation Details](#implementation-details)

---

## format Overview

- LYT files are [ASCII](https://en.wikipedia.org/wiki/ASCII) text with a deterministic order: `beginlayout`, optional sections, then `donelayout`.  
- Every section declares a count and then lists entries on subsequent lines.  
- All implementations (`vendor/reone`, `vendor/xoreos`, `vendor/KotOR.js`, `vendor/Kotor.NET`) parse identical tokens; KotOR-Unity mirrors the same structure.  

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/lyt/`](https://github.com/OldRepublicDevs/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/lyt)

**Vendor References:**

- [`vendor/reone/src/libs/resource/format/lytreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/lytreader.cpp) - Complete C++ LYT parser with room positioning
- [`vendor/xoreos/src/aurora/lytfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/lytfile.cpp) - Generic Aurora LYT implementation (shared format)
- [`vendor/KotOR.js/src/resource/LYTObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/LYTObject.ts) - TypeScript LYT parser with scene graph integration
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/LYTObject.cs`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/LYTObject.cs) - C# Unity LYT loader
- [`vendor/Kotor.NET/Kotor.NET/Formats/KotorLYT/LYT.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorLYT/LYT.cs) - .NET LYT reader/writer

**See Also:**

- [MDL/MDX File Format](MDL-MDX-File-Format) - [room models](LYT-File-Format#room-definitions) referenced by LYT entries
- [BWM File Format](BWM-File-Format) - Walkmeshes ([WOK](BWM-File-Format) files) loaded alongside LYT rooms
- [VIS File Format](VIS-File-Format) - Visibility graph for areas with LYT rooms
- [GFF-ARE](GFF-ARE) - [area files](GFF-File-Format#are-area) that load LYT layouts
- [Indoor Map Builder Implementation Guide](Indoor-Map-Builder-Implementation-Guide) - Uses LYT format for generated modules

---

## Syntax

```plaintext
beginlayout
roomcount <N>
  <room_model> <x> <y> <z>
trackcount <N>
  <track_model> <x> <y> <z>
obstaclecount <N>
  <obstacle_model> <x> <y> <z>
doorhookcount <N>
  <room_name> <door_name> <x> <y> <z> <qx> <qy> <qz> <qw> [optional floats]
donelayout
```

### Room Definitions

| Token | Description |
| ----- | ----------- |
| `roomcount` | Declares how many rooms follow. |
| `<room_model>` | [ResRef](GFF-File-Format#gff-data-types) of the [MDL/MDX](MDL-MDX-File-Format)/[WOK](BWM-File-Format) triple (max 16 chars, no spaces). |
| `<x y z>` | World-space position for the room’s origin. |

Rooms are case-insensitive; PyKotor lowercases entries for caching and resource lookup.

**Reference:** [`vendor/reone/src/libs/resource/format/lytreader.cpp:37-77`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/lytreader.cpp#L37-L77)

### Track Definitions

Tracks (`LYTTrack`) are booster elements used exclusively in swoop racing mini-games, primarily in KotOR II. Each track entry defines a booster element that can be placed along a racing track to provide speed boosts or other gameplay effects.

**format:**

```plaintext
trackcount <N>
  <track_model> <x> <y> <z>
```

| Token | Description |
| ----- | ----------- |
| `trackcount` | Declares how many track elements follow |
| `<track_model>` | [ResRef](GFF-File-Format#gff-data-types) of the track booster model ([MDL](MDL-MDX-File-Format) file, max 16 chars) |
| `<x y z>` | World-space position for the track element |

**Usage:**

- Tracks are optional - most modules omit this section entirely
- Primarily used in KotOR II swoop racing modules (e.g., Telos surface racing)
- Each track element represents a booster that can be placed along the racing track
- The engine uses these positions to spawn track boosters during racing mini-games

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py:286-329`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py#L286-L329)

**Reference:** [`vendor/KotOR.js/src/resource/LYTObject.ts:73-83`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/LYTObject.ts#L73-L83), [`vendor/xoreos/src/aurora/lytfile.cpp:98-107`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/lytfile.cpp#L98-L107)

### Obstacle Definitions

Obstacles (`LYTObstacle`) are hazard elements used exclusively in swoop racing mini-games, primarily in KotOR II. Each obstacle entry defines a hazard element that can be placed along a racing track to create challenges or obstacles for the player.

**format:**

```plaintext
obstaclecount <N>
  <obstacle_model> <x> <y> <z>
```

| Token | Description |
| ----- | ----------- |
| `obstaclecount` | Declares how many obstacle elements follow |
| `<obstacle_model>` | [ResRef](GFF-File-Format#gff-data-types) of the obstacle model ([MDL](MDL-MDX-File-Format) file, max 16 chars) |
| `<x y z>` | World-space position for the obstacle element |

**Usage:**

- Obstacles are optional - most modules omit this section entirely
- Typically only present in KotOR II racing modules (e.g., Telos surface racing)
- Each obstacle element represents a hazard that can be placed along the racing track
- The engine uses these positions to spawn obstacles during racing mini-games
- Mirrors the track format but represents hazards instead of boosters

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py:332-375`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py#L332-L375)

**Reference:** [`vendor/KotOR.js/src/resource/LYTObject.ts:79-83`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/LYTObject.ts#L79-L83), [`vendor/xoreos/src/aurora/lytfile.cpp:109-118`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/lytfile.cpp#L109-L118)

### Door Hooks

Door hooks (`LYTDoorHook`) bind door models (DYN or placeable) to rooms. Each entry defines a position and orientation where a door can be placed, enabling area transitions and room connections.

**format:**

```plaintext
doorhookcount <N>
  <room_name> <door_name> <x> <y> <z> <qx> <qy> <qz> <qw> [optional floats]
```

| Token | Description |
| ----- | ----------- |
| `doorhookcount` | Declares how many door hooks follow |
| `<room_name>` | Target room (must match a `roomcount` entry, case-insensitive) |
| `<door_name>` | Hook identifier (used in module files to reference this door, case-insensitive) |
| `<x y z>` | position of door origin in world space |
| `<qx qy qz qw>` | [Quaternion](https://en.wikipedia.org/wiki/Quaternion) orientation for door rotation |
| `[optional floats]` | Some builds (notably xoreos/KotOR-Unity) record five extra floats; PyKotor ignores them while preserving compatibility |

**Usage:**

- Door hooks define where doors are placed in rooms to create area transitions
- Each door hook specifies which room it belongs to and a unique door name
- The engine uses door hooks to position door [models](MDL-MDX-File-Format) and enable transitions between areas
- Door hooks are separate from [BWM](BWM-File-Format) hooks (see [BWM File Format](BWM-File-Format.md#walkmesh-properties)) - [BWM](BWM-File-Format) hooks define interaction points, while LYT doorhooks define door placement

**Relationship to [BWM](BWM-File-Format):**

- Door hooks in LYT files define where doors are placed in the layout
- [BWM](BWM-File-Format) [walkmeshes](BWM-File-Format) may have [edge](BWM-File-Format#edges) transitions that reference these door hooks
- The engine combines LYT doorhook positions with [BWM](BWM-File-Format) transition data to create functional doorways

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py:378-456`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py#L378-L456)

**Reference:** [`vendor/xoreos/src/aurora/lytfile.cpp:161-200`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/lytfile.cpp#L161-L200), [`vendor/KotOR.js/src/resource/LYTObject.ts:85-91`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/LYTObject.ts#L85-L91)

---

## coordinate System

- Units are meters in the same left-handed coordinate system as [MDL](MDL-MDX-File-Format) [models](MDL-MDX-File-Format).  
- PyKotor validates that room ResRefs and hook targets are lowercase and conform to resource naming restrictions.  
- The engine expects rooms to be pre-aligned so that adjoining doors share positions/rotations; [VIS files](VIS-File-Format) then control visibility between those rooms.  

**Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py:150-267`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py#L150-L267)

---

## Implementation Details

- **Parser:** [`Libraries/PyKotor/src/pykotor/resource/formats/lyt/io_lyt.py`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lyt/io_lyt.py)  
- **data [model](MDL-MDX-File-Format):** [`Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py)  
- **Reference Implementations:**  
  - [`vendor/reone/src/libs/resource/format/lytreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/lytreader.cpp)  
  - [`vendor/xoreos/src/aurora/lytfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/lytfile.cpp)  
  - [`vendor/KotOR.js/src/resource/LYTObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/LYTObject.ts)  
  - [`vendor/Kotor.NET/Kotor.NET/Formats/KotorLYT/LYT.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorLYT/LYT.cs)  

All of the projects listed above agree on the plain-text token sequence; KotOR-Unity and NorthernLights consume the same format without introducing additional metadata.
