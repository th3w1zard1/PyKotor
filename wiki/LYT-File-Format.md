# KotOR [LYT files](LYT-File-Format) [format](GFF-File-Format) Documentation

LYT (Layout) [files](GFF-File-Format) define how area [room models](LYT-File-Format#room-definitions) [ARE](GFF-File-Format#are-area) positioned inside a module. They [ARE](GFF-File-Format#are-area) plain-text descriptors that list room placements, swoop-track props, obstacles, and door hook transforms. The engine combines this [data](GFF-File-Format#file-structure) with [MDL](MDL-MDX-File-Format)/[MDX](MDL-MDX-File-Format) [geometry](MDL-MDX-File-Format#geometry-header) to assemble the final area.

## Table of Contents

- [KotOR LYT files Format Documentation](#kotor-lyt-files-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [Format Overview](#format-overview)
  - [Syntax](#syntax)
    - [Room Definitions](#room-definitions)
    - [Track Definitions](#track-definitions)
    - [Obstacle Definitions](#obstacle-definitions)
    - [Door Hooks](#door-hooks)
  - [Coordinate System](#coordinate-system)
  - [Implementation Details](#implementation-details)

---

## [format](GFF-File-Format) Overview

- [LYT files](LYT-File-Format) [ARE](GFF-File-Format#are-area) [ASCII](https://en.wikipedia.org/wiki/ASCII) text with a deterministic order: `beginlayout`, optional sections, then `donelayout`.  
- Every section declares a [count](GFF-File-Format#file-structure) and then lists entries on subsequent lines.  
- All implementations (`vendor/reone`, `vendor/xoreos`, `vendor/KotOR.js`, `vendor/Kotor.NET`) parse identical tokens; KotOR-Unity mirrors the same [structure](GFF-File-Format#file-structure).  

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/lyt/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/lyt)

**Vendor References:**

- [`vendor/reone/src/libs/resource/format/lytreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/lytreader.cpp) - Complete C++ [LYT](LYT-File-Format) parser with room positioning
- [`vendor/xoreos/src/aurora/lytfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/lytfile.cpp) - Generic Aurora [LYT](LYT-File-Format) implementation (shared [format](GFF-File-Format))
- [`vendor/KotOR.js/src/resource/LYTObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/LYTObject.ts) - TypeScript [LYT](LYT-File-Format) parser with scene graph integration
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/LYTObject.cs`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/LYTObject.cs) - C# Unity [LYT](LYT-File-Format) loader
- [`vendor/Kotor.NET/Kotor.NET/Formats/KotorLYT/LYT.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorLYT/LYT.cs) - .NET [LYT](LYT-File-Format) reader/writer

**See Also:**

- [MDL/MDX File Format](MDL-MDX-File-Format) - [room models](LYT-File-Format#room-definitions) referenced by [LYT](LYT-File-Format) entries
- [BWM File Format](BWM-File-Format) - Walkmeshes ([WOK](BWM-File-Format) [files](GFF-File-Format)) loaded alongside [LYT](LYT-File-Format) rooms
- [VIS File Format](VIS-File-Format) - Visibility graph for areas with [LYT](LYT-File-Format) rooms
- [GFF-ARE](GFF-ARE) - [area files](GFF-File-Format#are-area) that load [LYT](LYT-File-Format) layouts
- [Indoor Map Builder Implementation Guide](Indoor-Map-Builder-Implementation-Guide) - Uses [LYT](LYT-File-Format) [format](GFF-File-Format) for generated modules

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
| `<room_model>` | [ResRef](GFF-File-Format#resref) of the [MDL/MDX](MDL-MDX-File-Format)/[WOK](BWM-File-Format) triple (max 16 chars, no spaces). |
| `<x y z>` | World-space [position](MDL-MDX-File-Format#node-header) for the room’s origin. |

Rooms [ARE](GFF-File-Format#are-area) case-insensitive; PyKotor lowercases entries for caching and resource lookup.

**Reference:** [`vendor/reone/src/libs/resource/format/lytreader.cpp:37-77`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/lytreader.cpp#L37-L77)

### Track Definitions

Tracks (`LYTTrack`) [ARE](GFF-File-Format#are-area) booster elements used exclusively in swoop racing mini-games, primarily in KotOR II. Each track entry defines a booster element that can be placed along a racing track to provide speed boosts or other gameplay effects.

**[format](GFF-File-Format):**

```plaintext
trackcount <N>
  <track_model> <x> <y> <z>
```

| Token | Description |
| ----- | ----------- |
| `trackcount` | Declares how many track elements follow |
| `<track_model>` | [ResRef](GFF-File-Format#resref) of the track booster model ([MDL](MDL-MDX-File-Format) [file](GFF-File-Format), max 16 chars) |
| `<x y z>` | World-space [position](MDL-MDX-File-Format#node-header) for the track element |

**Usage:**

- Tracks [ARE](GFF-File-Format#are-area) optional - most modules omit this section entirely
- Primarily used in [KotOR II](KotOR-II) swoop racing modules (e.g., Telos surface racing)
- Each track element represents a booster that can be placed along the racing track
- The engine uses these [positions](MDL-MDX-File-Format#node-header) to spawn track boosters during racing mini-games

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py:286-329`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py#L286-L329)

**Reference:** [`vendor/KotOR.js/src/resource/LYTObject.ts:73-83`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/LYTObject.ts#L73-L83), [`vendor/xoreos/src/aurora/lytfile.cpp:98-107`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/lytfile.cpp#L98-L107)

### Obstacle Definitions

Obstacles (`LYTObstacle`) [ARE](GFF-File-Format#are-area) hazard elements used exclusively in swoop racing mini-games, primarily in [KotOR II](KotOR-II). Each obstacle entry defines a hazard element that can be placed along a racing track to create challenges or obstacles for the player.

**[format](GFF-File-Format):**

```plaintext
obstaclecount <N>
  <obstacle_model> <x> <y> <z>
```

| Token | Description |
| ----- | ----------- |
| `obstaclecount` | Declares how many obstacle elements follow |
| `<obstacle_model>` | [ResRef](GFF-File-Format#resref) of the obstacle model ([MDL](MDL-MDX-File-Format) [file](GFF-File-Format), max 16 chars) |
| `<x y z>` | World-space [position](MDL-MDX-File-Format#node-header) for the obstacle element |

**Usage:**

- Obstacles [ARE](GFF-File-Format#are-area) optional - most modules omit this section entirely
- Typically only present in [KotOR II](KotOR-II) racing modules (e.g., Telos surface racing)
- Each obstacle element represents a hazard that can be placed along the racing track
- The engine uses these [positions](MDL-MDX-File-Format#node-header) to spawn obstacles during racing mini-games
- Mirrors the track [format](GFF-File-Format) but represents hazards instead of boosters

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py:332-375`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py#L332-L375)

**Reference:** [`vendor/KotOR.js/src/resource/LYTObject.ts:79-83`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/LYTObject.ts#L79-L83), [`vendor/xoreos/src/aurora/lytfile.cpp:109-118`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/lytfile.cpp#L109-L118)

### Door Hooks

Door hooks (`LYTDoorHook`) bind [door models](MDL-MDX-File-Format#door-models) (DYN or placeable) to rooms. Each entry defines a [position](MDL-MDX-File-Format#node-header) and [orientation](MDL-MDX-File-Format#node-header) where a door can be placed, enabling area transitions and room connections.

**[format](GFF-File-Format):**

```plaintext
doorhookcount <N>
  <room_name> <door_name> <x> <y> <z> <qx> <qy> <qz> <qw> [optional floats]
```

| Token | Description |
| ----- | ----------- |
| `doorhookcount` | Declares how many door hooks follow |
| `<room_name>` | Target room (must match a `roomcount` entry, case-insensitive) |
| `<door_name>` | Hook identifier (used in module [files](GFF-File-Format) to reference this door, case-insensitive) |
| `<x y z>` | [position](MDL-MDX-File-Format#node-header) of door origin in world space |
| `<qx qy qz qw>` | [Quaternion](https://en.wikipedia.org/wiki/Quaternion) [orientation](MDL-MDX-File-Format#node-header) for door [rotation](MDL-MDX-File-Format#node-header) |
| `[optional floats]` | Some builds (notably xoreos/KotOR-Unity) record five extra floats; PyKotor ignores them while preserving compatibility |

**Usage:**

- Door hooks define where doors [ARE](GFF-File-Format#are-area) placed in rooms to create area transitions
- Each door hook specifies which room it belongs to and a unique door name
- The engine uses door hooks to [position](MDL-MDX-File-Format#node-header) door [models](MDL-MDX-File-Format) and enable transitions between areas
- Door hooks [ARE](GFF-File-Format#are-area) separate from [BWM](BWM-File-Format) hooks (see [BWM File Format](BWM-File-Format.md#walkmesh-properties)) - [BWM](BWM-File-Format) hooks define interaction points, while [LYT](LYT-File-Format) doorhooks define door placement

**Relationship to [BWM](BWM-File-Format):**

- Door hooks in [LYT files](LYT-File-Format) define where doors [ARE](GFF-File-Format#are-area) placed in the layout
- [BWM](BWM-File-Format) [walkmeshes](BWM-File-Format) may have [edge](BWM-File-Format#edges) transitions that reference these door hooks
- The engine combines [LYT](LYT-File-Format) doorhook [positions](MDL-MDX-File-Format#node-header) with [BWM](BWM-File-Format) transition [data](GFF-File-Format#file-structure) to create functional doorways

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py:378-456`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py#L378-L456)

**Reference:** [`vendor/xoreos/src/aurora/lytfile.cpp:161-200`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/lytfile.cpp#L161-L200), [`vendor/KotOR.js/src/resource/LYTObject.ts:85-91`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/LYTObject.ts#L85-L91)

---

## [coordinate](GFF-File-Format#are-area) System

- Units [ARE](GFF-File-Format#are-area) meters in the same left-handed [coordinate](GFF-File-Format#are-area) system as [MDL](MDL-MDX-File-Format) [models](MDL-MDX-File-Format).  
- PyKotor validates that room ResRefs and hook targets [ARE](GFF-File-Format#are-area) lowercase and conform to resource naming restrictions.  
- The engine expects rooms to be pre-aligned so that adjoining doors share [positions](MDL-MDX-File-Format#node-header)/[rotations](MDL-MDX-File-Format#node-header); [VIS files](VIS-File-Format) then control visibility between those rooms.  

**Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py:150-267`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py#L150-L267)

---

## Implementation Details

- **Parser:** [`Libraries/PyKotor/src/pykotor/resource/formats/lyt/io_lyt.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lyt/io_lyt.py)  
- **[data](GFF-File-Format#file-structure) [model](MDL-MDX-File-Format):** [`Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/lyt/lyt_data.py)  
- **Reference Implementations:**  
  - [`vendor/reone/src/libs/resource/format/lytreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/lytreader.cpp)  
  - [`vendor/xoreos/src/aurora/lytfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/lytfile.cpp)  
  - [`vendor/KotOR.js/src/resource/LYTObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/LYTObject.ts)  
  - [`vendor/Kotor.NET/Kotor.NET/Formats/KotorLYT/LYT.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorLYT/LYT.cs)  

All of the projects listed above agree on the plain-text token sequence; KotOR-Unity and NorthernLights consume the same [format](GFF-File-Format) without introducing additional metadata.
