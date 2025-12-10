# KotOR [VIS files](VIS-File-Format) [format](GFF-File-Format) Documentation

VIS (Visibility) [files](GFF-File-Format) describe which module rooms can be seen from other rooms. They drive the engine’s [occlusion culling](https://en.wikipedia.org/wiki/Hidden-surface_determination) so that only [geometry](MDL-MDX-File-Format#geometry-header) visible from the player’s current room is rendered, reducing draw calls and overdraw.

## Table of Contents

- [KotOR VIS File Format Documentation](#kotor-vis-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [Format Overview](#format-overview)
  - [File Layout](#file-layout)
    - [Parent Lines](#parent-lines)
    - [Child Lines](#child-lines)
  - [Runtime Behavior](#runtime-behavior)
  - [Implementation Details](#implementation-details)

---

## [format](GFF-File-Format) Overview

- [VIS files](VIS-File-Format) [ARE](GFF-File-Format#are-area) plain [ASCII](https://en.wikipedia.org/wiki/ASCII) text; each parent room line lists how many child rooms follow.  
- Child room lines [ARE](GFF-File-Format#are-area) indented by two spaces. Empty lines [ARE](GFF-File-Format#are-area) ignored and names [ARE](GFF-File-Format#are-area) case-insensitive.  
- [files](GFF-File-Format) usually ship as `moduleXXX.vis` pairs; the `moduleXXXs.vis` (or `.vis` appended inside [ERF](ERF-File-Format)) uses the same syntax.  

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/vis/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/vis)

**Vendor References:**

- [`vendor/reone/src/libs/resource/format/visreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/visreader.cpp) - Complete C++ [VIS](VIS-File-Format) parser implementation
- [`vendor/xoreos/src/aurora/visfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/visfile.cpp) - Generic Aurora [VIS](VIS-File-Format) implementation (shared [format](GFF-File-Format))
- [`vendor/KotOR.js/src/resource/VISObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/VISObject.ts) - TypeScript [VIS](VIS-File-Format) parser with rendering integration
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/VISObject.cs`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/VISObject.cs) - C# Unity [VIS](VIS-File-Format) loader with occlusion culling

**See Also:**

- [LYT File Format](LYT-File-Format) - [layout files](LYT-File-Format) defining room positions
- [MDL/MDX File Format](MDL-MDX-File-Format) - [room models](LYT-File-Format#room-definitions) controlled by [VIS](VIS-File-Format)
- [BWM File Format](BWM-File-Format) - [walkmeshes](BWM-File-Format) for room collision/pathfinding
- [GFF-ARE](GFF-ARE) - [area files](GFF-File-Format#are-area) that load [VIS](VIS-File-Format) visibility graphs
- [Indoor Map Builder Implementation Guide](Indoor-Map-Builder-Implementation-Guide) - Generates [VIS files](VIS-File-Format) for created areas  

---

## [file](GFF-File-Format) Layout

### Parent Lines

```vis
ROOM_NAME CHILD_COUNT
```

| Token | Description |
| ----- | ----------- |
| `ROOM_NAME` | Room label (typically the [MDL](MDL-MDX-File-Format) [ResRef](GFF-File-Format#resref) of the room). |
| `CHILD_COUNT` | Number of child lines that follow immediately. |

Example:

```vis
room012 3
  room013
  room014
  room015
```

### Child Lines

- Each child line begins with two spaces followed by the visible room name.  
- There is no explicit delimiter; the parser trims whitespace.  
- A parent can list itself to force always-rendered rooms (rare but valid).  

**Reference:** [`vendor/KotOR.js/src/resource/VISObject.ts:71-126`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/VISObject.ts#L71-L126)  

---

## Runtime Behavior

- When the player stands in room `A`, the engine renders any room listed under `A` and recursively any linked lights or effects.  
- [VIS files](VIS-File-Format) only control visibility; collision and pathfinding still rely on [walkmeshes](BWM-File-Format) and module [GFF](GFF-File-Format) [data](GFF-File-Format#file-structure).  
- Editing [VIS](VIS-File-Format) entries is a common optimization: removing unnecessary pairs prevents the renderer from drawing walls behind closed doors, while adding entries can fix disappearing [geometry](MDL-MDX-File-Format#geometry-header) when doorways [ARE](GFF-File-Format#are-area) wide open.

**NOTE**: [VIS](VIS-File-Format) [ARE](GFF-File-Format#are-area) NOT required by the game. Most modern hardware can run kotor significantly well even without these defined. The game however does not implement frustrum culling, so you may want to regardless.

**Performance Impact:**

[VIS files](VIS-File-Format) [ARE](GFF-File-Format#are-area) crucial for performance in large areas:

- **Without [VIS](VIS-File-Format)**: Engine renders all rooms, even those behind walls/doors (thousands of unnecessary polygons)
- **With [VIS](VIS-File-Format)**: Only visible rooms [ARE](GFF-File-Format#are-area) submitted to the renderer (10-50x fewer draw calls)
- **Overly Restrictive [VIS](VIS-File-Format)**: Causes pop-in where rooms suddenly appear when entering adjacent areas
- **Too Permissive [VIS](VIS-File-Format)**: Wastes GPU resources rendering unseen [geometry](MDL-MDX-File-Format#geometry-header)

**Common Issues:**

- **Missing Room**: Room not in any [VIS](VIS-File-Format) list → never renders → appears invisible
- **One-way Visibility**: Room A lists B, but B doesn't list A → asymmetric rendering
- **Performance Problems**: All rooms list each other → defeats purpose of [VIS](VIS-File-Format) optimization
- **Doorway Artifacts**: Door rooms not mutually visible → walls clip during door [animations](MDL-MDX-File-Format#animation-header)

Module designers balance between performance (fewer visible rooms) and visual quality (no pop-in/clipping). Testing [VIS](VIS-File-Format) changes in-game is essential.  

PyKotor’s `VIS` class stores the [data](GFF-File-Format#file-structure) as a `dict[str, set[str]]`, exposing helpers like `set_visible()` and `set_all_visible()` for tooling (see [`vis_data.py:52-294`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/vis/vis_data.py#L52-L294)).

---

## Implementation Details

- **Parser:** [`Libraries/PyKotor/src/pykotor/resource/formats/vis/io_vis.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/vis/io_vis.py)  
- **[data](GFF-File-Format#file-structure) [model](MDL-MDX-File-Format):** [`Libraries/PyKotor/src/pykotor/resource/formats/vis/vis_data.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/vis/vis_data.py)  
- **Reference Implementations:**  
  - [`vendor/reone/src/libs/resource/format/visreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/format/visreader.cpp)  
  - [`vendor/xoreos/src/aurora/visfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/visfile.cpp)  
  - [`vendor/KotOR.js/src/resource/VISObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/VISObject.ts)  

These sources agree on the ASCII layout above, so [VIS files](VIS-File-Format) authored with PyKotor behave identically across the other toolchains.

---
