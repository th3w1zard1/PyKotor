# KotOR [BWM](BWM-File-Format) [file](GFF-File-Format) [format](GFF-File-Format) Documentation

This document provides a detailed description of the [BWM (Binary WalkMesh)](BWM-File-Format) [file](GFF-File-Format) [format](GFF-File-Format) used in Knights of the Old Republic (KotOR) games. [BWM files](BWM-File-Format), stored on disk as [WOK files](BWM-File-Format), define [walkable surfaces](BWM-File-Format) for pathfinding and collision detection in game areas.

**Related [formats](GFF-File-Format):** [BWM files](BWM-File-Format) [ARE](GFF-File-Format#are-area) used in conjunction with [GFF ARE files](GFF-File-Format#are-area) which define [area properties](GFF-File-Format#are-area) and contain references to [walkmesh](BWM-File-Format) [files](GFF-File-Format).

## Table of Contents

- [KotOR BWM file format Documentation](#kotor-bwm-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [file structure Overview](#file-structure-overview)
  - [Binary format](#binary-format)
    - [file header](#file-header)
    - [walkmesh Properties](#walkmesh-properties)
    - [data Table offsets](#data-table-offsets)
    - [vertices](#vertices)
    - [faces](#faces)
    - [materials](#materials)
    - [Derived data](#derived-data)
    - [AABB Tree](#aabb-tree)
    - [Walkable adjacencies](#walkable-adjacencies)
    - [edges](#edges)
    - [perimeters](#perimeters)
  - [Runtime model](#runtime-model)
    - [BWM Class](#bwm-class)
    - [BWMFace Class](#bwmface-class)
    - [BWMEdge Class](#bwmedge-class)
    - [BWMNodeAABB Class](#bwmnodeaabb-class)
  - [Implementation Comparison](#implementation-comparison)
    - [Summary of KEY Differences](#summary-of-key-differences)
    - [Recommendations for PyKotor](#recommendations-for-pykotor)
    - [Test Coverage Analysis](#test-coverage-analysis)
  - [Implementation Details](#implementation-details)

---

## [file](GFF-File-Format) [structure](GFF-File-Format#file-structure-overview) Overview

[BWM (Binary WalkMesh)](BWM-File-Format) [files](GFF-File-Format) define [walkable surfaces](BWM-File-Format) using triangular [faces](MDL-MDX-File-Format#face-structure). Each [face](MDL-MDX-File-Format#face-structure) has [material](MDL-MDX-File-Format#trimesh-header) properties that determine whether it's walkable, [adjacency](BWM-File-Format#walkable-adjacencies) information for pathfinding, and optional [edge](BWM-File-Format#edges) transitions for area connections. The [format](GFF-File-Format) supports two distinct [walkmesh](BWM-File-Format) [types](GFF-File-Format#gff-data-types): area walkmeshes ([WOK](BWM-File-Format)) for level [geometry](MDL-MDX-File-Format#geometry-header) and placeable/door walkmeshes ([PWK](BWM-File-Format)/[DWK](BWM-File-Format)) for interactive objects.

[walkmeshes](BWM-File-Format) serve multiple critical functions in KotOR:

- **Pathfinding**: NPCs and the player use [walkmeshes](BWM-File-Format) to navigate areas, with [adjacency](BWM-File-Format#walkable-adjacencies) [data](GFF-File-Format#file-structure-overview) enabling pathfinding algorithms to find routes between [walkable faces](BWM-File-Format#faces)
- **Collision Detection**: The engine uses [walkmeshes](BWM-File-Format) to prevent characters from walking through walls, objects, and impassable terrain
- **Spatial Queries**: [AABB](BWM-File-Format#aabb-tree) trees enable efficient ray casting (mouse clicks, projectiles) and point-in-triangle tests (determining which [face](MDL-MDX-File-Format#face-structure) a character stands on)
- **Area Transitions**: [edge](BWM-File-Format#edges) transitions link [walkmeshes](BWM-File-Format) to door connections and area boundaries, enabling seamless movement between rooms

The binary [format](GFF-File-Format) uses a [header](GFF-File-Format#file-header)-based [structure](GFF-File-Format#file-structure-overview) where [offsets](GFF-File-Format#file-structure-overview) point to various [data](GFF-File-Format#file-structure-overview) tables, allowing efficient random access to [vertices](MDL-MDX-File-Format#vertex-structure), [faces](MDL-MDX-File-Format#face-structure), [materials](MDL-MDX-File-Format#trimesh-header), and acceleration [structures](GFF-File-Format#file-structure-overview). This design enables the engine to load only necessary portions of large [walkmeshes](BWM-File-Format) or stream [data](GFF-File-Format#file-structure-overview) as needed.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/)

**Reference Implementations:**

- [`vendor/reone/src/libs/graphics/format/bwmreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp) - C++ [BWM](BWM-File-Format) reader with complete parsing logic
- [`vendor/reone/include/reone/graphics/format/bwmreader.h`](https://github.com/th3w1zard1/reone/blob/master/include/reone/graphics/format/bwmreader.h) - [BWM](BWM-File-Format) reader [header](GFF-File-Format#file-header) with [type](GFF-File-Format#gff-data-types) definitions
- [`vendor/reone/include/reone/graphics/walkmesh.h`](https://github.com/th3w1zard1/reone/blob/master/include/reone/graphics/walkmesh.h) - Runtime [walkmesh](BWM-File-Format) class definition
- [`vendor/reone/src/libs/graphics/walkmesh.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/walkmesh.cpp) - Runtime raycasting implementation
- [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py) - Python [BWM](BWM-File-Format) reader for Blender import
- [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py) - Python [BWM](BWM-File-Format) writer for Blender export with [adjacency](BWM-File-Format#walkable-adjacencies) calculation
- [`vendor/kotorblender/io_scene_kotor/aabb.py`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/aabb.py) - [AABB](BWM-File-Format#aabb-tree) tree generation algorithm
- [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp) - xoreos [walkmesh](BWM-File-Format) loader with pathfinding integration
- [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts) - Complete TypeScript [walkmesh](BWM-File-Format) implementation with raycasting and spatial queries
- [`vendor/KotOR.js/src/odyssey/WalkmeshEdge.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/WalkmeshEdge.ts) - WalkmeshEdge class for [perimeter](BWM-File-Format#perimeters) [edge](BWM-File-Format#edges) handling
- [`vendor/KotOR.js/src/odyssey/WalkmeshPerimeter.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/WalkmeshPerimeter.ts) - WalkmeshPerimeter class for boundary loop management

---

## Binary [format](GFF-File-Format)

### [file](GFF-File-Format) [header](GFF-File-Format#file-header)

| Name         | [type](GFF-File-Format#gff-data-types)    | [offset](GFF-File-Format#file-structure-overview) | [size](GFF-File-Format#file-structure-overview) | Description                                    |
| ------------ | ------- | ------ | ---- | ---------------------------------------------- |
| Magic        | [[char](GFF-File-Format#gff-data-types)][GFF-File-Format#char](4) | 0 (0x00)   | 4    | Always `"BWM "` (space-padded)                 |
| Version      | [[char](GFF-File-Format#gff-data-types)][GFF-File-Format#char](4) | 4 (0x04)   | 4    | Always `"V1.0"`                                 |

The [file](GFF-File-Format) [header](GFF-File-Format#file-header) begins with an 8-[byte](GFF-File-Format#gff-data-types) signature that must exactly match `"BWM V1.0"` (the space after "[BWM](BWM-File-Format)" is significant). This signature serves as both a [file](GFF-File-Format) [type](GFF-File-Format#gff-data-types) identifier and version marker. The version [string](GFF-File-Format#gff-data-types) "V1.0" indicates this is the first and only version of the [BWM](BWM-File-Format) [format](GFF-File-Format) used in KotOR games. Implementations should validate this [header](GFF-File-Format#file-header) before proceeding with [file](GFF-File-Format) parsing to ensure they're reading a valid [BWM file](BWM-File-Format).

**Vendor Consensus:** All implementations (reone, xoreos, KotOR.js, kotorblender, PyKotor) agree on this [header](GFF-File-Format#file-header) [format](GFF-File-Format) and validation.

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:28`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L28), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:52-59`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L52-L59), [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:73-75`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L73-L75), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:452-454`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L452-L454)

### [walkmesh](BWM-File-Format) Properties

The [walkmesh](BWM-File-Format) properties section immediately follows the [header](GFF-File-Format#file-header) and contains [type](GFF-File-Format#gff-data-types) information, hook [vectors](GFF-File-Format#gff-data-types), and [position](MDL-MDX-File-Format#node-header) [data](GFF-File-Format#file-structure-overview). This section is 52 bytes total (from [offset](GFF-File-Format#file-structure-overview) 0x08 to 0x3C), providing essential metadata about the [walkmesh](BWM-File-Format)'s purpose and positioning.

| Name                    | [type](GFF-File-Format#gff-data-types)      | [offset](GFF-File-Format#file-structure-overview) | [size](GFF-File-Format#file-structure-overview) | Description                                                      |
| ----------------------- | --------- | ------ | ---- | ---------------------------------------------------------------- |
| [type](GFF-File-Format#gff-data-types)                    | [uint32](GFF-File-Format#gff-data-types)    | 8 (0x08)   | 4    | [walkmesh](BWM-File-Format) type (0=[PWK](BWM-File-Format)/[DWK](BWM-File-Format), 1=[WOK](BWM-File-Format)/Area)                            |
| Relative Use [position](MDL-MDX-File-Format#node-header) 1 | [[float32](GFF-File-Format#gff-data-types)][GFF-File-Format#float](3)| 12 (0x0C)   | 12   | Relative use hook [position](MDL-MDX-File-Format#node-header) 1 (x, y, z)                           |
| Relative Use [position](MDL-MDX-File-Format#node-header) 2 | [[float32](GFF-File-Format#gff-data-types)][GFF-File-Format#float](3)| 24 (0x18)   | 12   | Relative use hook [position](MDL-MDX-File-Format#node-header) 2 (x, y, z)                           |
| Absolute Use [position](MDL-MDX-File-Format#node-header) 1 | [[float32](GFF-File-Format#gff-data-types)][GFF-File-Format#float](3)| 36 (0x24)   | 12   | Absolute use hook [position](MDL-MDX-File-Format#node-header) 1 (x, y, z)                           |
| Absolute Use [position](MDL-MDX-File-Format#node-header) 2 | [[float32](GFF-File-Format#gff-data-types)][GFF-File-Format#float](3)| 48 (0x30)   | 12   | Absolute use hook [position](MDL-MDX-File-Format#node-header) 2 (x, y, z)                           |
| [position](MDL-MDX-File-Format#node-header)                | [[float32](GFF-File-Format#gff-data-types)][GFF-File-Format#float](3)| 60 (0x3C)   | 12   | [walkmesh](BWM-File-Format) [position](MDL-MDX-File-Format#node-header) offset (x, y, z)                               |

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:30-38`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L30-L38), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:60-67`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L60-L67), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:455-457`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L455-L457)

**[walkmesh](BWM-File-Format) [types](GFF-File-Format#gff-data-types):**

KotOR uses different [walkmesh](BWM-File-Format) [types](GFF-File-Format#gff-data-types) for different purposes, each optimized for its specific use case:

- **WOK ([type](GFF-File-Format#gff-data-types) 1)**: Area [walkmesh](BWM-File-Format) - defines walkable regions in game areas
  - Stored as `<area_name>.wok` files (e.g., `m12aa.wok` for Dantooine area)
  - Large planar surfaces covering entire rooms or outdoor areas for player movement and NPC pathfinding
  - Often split across multiple rooms in complex areas, with each room having its own [walkmesh](BWM-File-Format)
  - Includes complete spatial acceleration ([AABB](BWM-File-Format#aabb-tree) tree), [adjacencies](BWM-File-Format#walkable-adjacencies) for pathfinding, [edges](BWM-File-Format#edges) for transitions, and [perimeters](BWM-File-Format#perimeters) for boundary detection
  - Used by the pathfinding system to compute routes between [walkable faces](BWM-File-Format#faces)
  - **Reference**: [`vendor/reone/include/reone/graphics/format/bwmreader.h:40-43`](https://github.com/th3w1zard1/reone/blob/master/include/reone/graphics/format/bwmreader.h#L40-L43), [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:52-64`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L52-L64), [`vendor/KotOR.js/src/enums/odyssey/OdysseyWalkMeshType.ts:11-14`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/enums/odyssey/OdysseyWalkMeshType.ts#L11-L14)
  
- **[PWK](BWM-File-Format)/DWK ([type](GFF-File-Format#gff-data-types) 0)**: Placeable/Door [walkmesh](BWM-File-Format) - collision for placeable objects and doors
  - **[PWK](BWM-File-Format)**: Stored as `<model_name>.pwk` [files](GFF-File-Format) - collision [geometry](MDL-MDX-File-Format#geometry-header) for containers, furniture, and other interactive placeable objects
    - Prevents the player from walking through solid objects like crates, tables, and containers
    - Typically much simpler than area [walkmeshes](BWM-File-Format), containing only the essential collision [geometry](MDL-MDX-File-Format#geometry-header)
  - **[DWK](BWM-File-Format)**: Stored as `<door_model>.dwk` [files](GFF-File-Format), often with multiple states:
    - `<name>0.dwk` - Closed door state
    - `<name>1.dwk` - Partially open state (if applicable)
    - `<name>2.dwk` - Fully open state
    - Door [walkmeshes](BWM-File-Format) update dynamically as doors open and close, switching between states
    - The engine loads the appropriate [DWK](BWM-File-Format) [file](GFF-File-Format) based on the door's current [animation](MDL-MDX-File-Format#animation-header) state
  - Compact collision [geometry](MDL-MDX-File-Format#geometry-header) optimized for small objects rather than large areas
  - Does not include [AABB](BWM-File-Format#aabb-tree) tree or [adjacency](BWM-File-Format#walkable-adjacencies) data (simpler [structure](GFF-File-Format#file-structure-overview), faster loading)
  - Hook vectors (USE1, USE2) define interaction points where the player can activate doors or placeables
  - **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:179-231`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L179-L231)

**Hook [vectors](GFF-File-Format#gff-data-types)** [ARE](GFF-File-Format#are-area) reference points used by the engine for positioning and interaction. These [ARE](GFF-File-Format#are-area) **NOT** related to [walkmesh](BWM-File-Format) [geometry](MDL-MDX-File-Format#geometry-header) itself ([faces](MDL-MDX-File-Format#face-structure), [edges](BWM-File-Format#edges), [vertices](MDL-MDX-File-Format#vertex-structure)), but rather define interaction points for doors and placeables.

**Important Distinction**: [BWM](BWM-File-Format) hooks [ARE](GFF-File-Format#are-area) different from [LYT](LYT-File-Format) doorhooks:

- **[BWM](BWM-File-Format) Hooks**: Interaction points stored in the [walkmesh](BWM-File-Format) [file](GFF-File-Format) itself (relative/absolute [positions](MDL-MDX-File-Format#node-header))
- **[LYT](LYT-File-Format) Doorhooks**: Door placement points defined in layout files (see [LYT File Format](LYT-File-Format.md#door-hooks))

- **Relative Hook [positions](MDL-MDX-File-Format#node-header)** (Relative Use [position](MDL-MDX-File-Format#node-header) 1/2): [positions](MDL-MDX-File-Format#node-header) relative to the [walkmesh](BWM-File-Format) origin, used when the [walkmesh](BWM-File-Format) itself may be transformed or positioned
  - For doors: Define where the player must stand to interact with the door (relative to door [model](MDL-MDX-File-Format))
  - For placeables: Define interaction points relative to the object's local [coordinate](GFF-File-Format#are-area) system
  - Stored as `relative_hook1` and `relative_hook2` in the [BWM](BWM-File-Format) class
  - **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:61-64`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L61-L64), [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:309-310`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L309-L310), [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:165-175`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L165-L175)

- **Absolute Hook [positions](MDL-MDX-File-Format#node-header)** (Absolute Use [position](MDL-MDX-File-Format#node-header) 1/2): [positions](MDL-MDX-File-Format#node-header) in world space, used when the [walkmesh](BWM-File-Format) [position](MDL-MDX-File-Format#node-header) is known
  - For doors: Precomputed world-space interaction points ([position](MDL-MDX-File-Format#node-header) + relative hook)
  - For placeables: World-space interaction points accounting for object placement
  - Stored as `absolute_hook1` and `absolute_hook2` in the [BWM](BWM-File-Format) class
  - **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:313-318`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L313-L318), [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:177-187`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L177-L187)

- **[position](MDL-MDX-File-Format#node-header)**: The [walkmesh](BWM-File-Format)'s origin [offset](GFF-File-Format#file-structure-overview) in world space
  - For area walkmeshes ([WOK](BWM-File-Format)): Typically `(0, 0, 0)` as areas define their own [coordinate](GFF-File-Format#are-area) system
  - For placeable/door [walkmeshes](BWM-File-Format): The [position](MDL-MDX-File-Format#node-header) where the object is placed in the area
  - Used to transform [vertices](MDL-MDX-File-Format#vertex-structure) from local to world [coordinates](GFF-File-Format#are-area)
  - **Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:37-38`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L37-L38), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:65`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L65), [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:103`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L103), [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:158-163`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L158-L163)

Hook [vectors](GFF-File-Format#gff-data-types) enable the engine to:

- Spawn creatures at designated locations relative to [walkable surfaces](BWM-File-Format)
- [position](MDL-MDX-File-Format#node-header) triggers and encounters at specific points
- Align objects to the walkable surface (e.g., placing items on tables)
- Define door interaction points (USE1, USE2) where the player can activate doors or placeables
- **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:214-222`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L214-L222)

### [data](GFF-File-Format#file-structure-overview) Table [offsets](GFF-File-Format#file-structure-overview)

After the [walkmesh](BWM-File-Format) properties, the [header](GFF-File-Format#file-header) contains [offset](GFF-File-Format#file-structure-overview) and [count](GFF-File-Format#file-structure-overview) information for all [data](GFF-File-Format#file-structure-overview) tables:

| Name                | [type](GFF-File-Format#gff-data-types)   | [offset](GFF-File-Format#file-structure-overview) | [size](GFF-File-Format#file-structure-overview) | Description                                                      |
| ------------------- | ------ | ------ | ---- | ---------------------------------------------------------------- |
| [vertex](MDL-MDX-File-Format#vertex-structure) [count](GFF-File-Format#file-structure-overview)        | [uint32](GFF-File-Format#gff-data-types) | 72 (0x48)   | 4    | Number of [vertices](MDL-MDX-File-Format#vertex-structure)                                               |
| [vertex](MDL-MDX-File-Format#vertex-structure) [offset](GFF-File-Format#file-structure-overview)       | [uint32](GFF-File-Format#gff-data-types) | 76 (0x4C)   | 4    | [offset](GFF-File-Format#file-structure-overview) to [vertex](MDL-MDX-File-Format#vertex-structure) [array](2DA-File-Format)                                           |
| [face](MDL-MDX-File-Format#face-structure) [count](GFF-File-Format#file-structure-overview)          | [uint32](GFF-File-Format#gff-data-types) | 80 (0x50)   | 4    | Number of [faces](MDL-MDX-File-Format#face-structure)                                                  |
| [face](MDL-MDX-File-Format#face-structure) [indices](2DA-File-Format#row-labels) [offset](GFF-File-Format#file-structure-overview) | [uint32](GFF-File-Format#gff-data-types) | 84 (0x54)   | 4    | [offset](GFF-File-Format#file-structure-overview) to [face](MDL-MDX-File-Format#face-structure) [indices](2DA-File-Format#row-labels) [array](2DA-File-Format)                                     |
| [materials](MDL-MDX-File-Format#trimesh-header) [offset](GFF-File-Format#file-structure-overview)    | [uint32](GFF-File-Format#gff-data-types) | 88 (0x58)   | 4    | [offset](GFF-File-Format#file-structure-overview) to [materials](MDL-MDX-File-Format#trimesh-header) [array](2DA-File-Format)                                       |
| Normals [offset](GFF-File-Format#file-structure-overview)      | [uint32](GFF-File-Format#gff-data-types) | 92 (0x5C)   | 4    | [offset](GFF-File-Format#file-structure-overview) to [face](MDL-MDX-File-Format#face-structure) normals [array](2DA-File-Format)                                     |
| Distances [offset](GFF-File-Format#file-structure-overview)    | [uint32](GFF-File-Format#gff-data-types) | 96 (0x60)   | 4    | [offset](GFF-File-Format#file-structure-overview) to planar distances [array](2DA-File-Format)                                 |
| [AABB](BWM-File-Format#aabb-tree) [count](GFF-File-Format#file-structure-overview)          | [uint32](GFF-File-Format#gff-data-types) | 100 (0x64)   | 4    | Number of [AABB](BWM-File-Format#aabb-tree) nodes ([WOK](BWM-File-Format) only, 0 for [PWK](BWM-File-Format)/[DWK](BWM-File-Format))                  |
| [AABB](BWM-File-Format#aabb-tree) [offset](GFF-File-Format#file-structure-overview)         | [uint32](GFF-File-Format#gff-data-types) | 104 (0x68)   | 4    | [offset](GFF-File-Format#file-structure-overview) to [AABB](BWM-File-Format#aabb-tree) [nodes](MDL-MDX-File-Format#node-structures) array ([WOK](BWM-File-Format) only)                            |
| Unknown             | [uint32](GFF-File-Format#gff-data-types) | 108 (0x6C)   | 4    | Unknown field (typically 0 or 4)                                 |
| [adjacency](BWM-File-Format#walkable-adjacencies) [count](GFF-File-Format#file-structure-overview)     | [uint32](GFF-File-Format#gff-data-types) | 112 (0x70)   | 4    | Number of [walkable faces](BWM-File-Format#faces) for adjacency ([WOK](BWM-File-Format) only)                |
| [adjacency](BWM-File-Format#walkable-adjacencies) [offset](GFF-File-Format#file-structure-overview)    | [uint32](GFF-File-Format#gff-data-types) | 116 (0x74)   | 4    | [offset](GFF-File-Format#file-structure-overview) to [adjacency](BWM-File-Format#walkable-adjacencies) array ([WOK](BWM-File-Format) only)                            |
| [edge](BWM-File-Format#edges) [count](GFF-File-Format#file-structure-overview)          | [uint32](GFF-File-Format#gff-data-types) | 120 (0x78)   | 4    | Number of [perimeter](BWM-File-Format#perimeters) edges ([WOK](BWM-File-Format) only)                            |
| [edge](BWM-File-Format#edges) [offset](GFF-File-Format#file-structure-overview)         | [uint32](GFF-File-Format#gff-data-types) | 124 (0x7C)   | 4    | [offset](GFF-File-Format#file-structure-overview) to [edge](BWM-File-Format#edges) array ([WOK](BWM-File-Format) only)                                  |
| [perimeter](BWM-File-Format#perimeters) [count](GFF-File-Format#file-structure-overview)     | [uint32](GFF-File-Format#gff-data-types) | 128 (0x80)   | 4    | Number of [perimeter](BWM-File-Format#perimeters) markers ([WOK](BWM-File-Format) only)                           |
| [perimeter](BWM-File-Format#perimeters) [offset](GFF-File-Format#file-structure-overview)    | [uint32](GFF-File-Format#gff-data-types) | 132 (0x84)   | 4    | [offset](GFF-File-Format#file-structure-overview) to [perimeter](BWM-File-Format#perimeters) array ([WOK](BWM-File-Format) only)                            |

**Total [header](GFF-File-Format#file-header) [size](GFF-File-Format#file-structure-overview)**: 136 bytes (0x88)

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:40-64`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L40-L64), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:66-81`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L66-L81), [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:79-94`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L79-L94), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:458-473`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L458-L473)

### [vertices](MDL-MDX-File-Format#vertex-structure)

| Name     | [type](GFF-File-Format#gff-data-types)      | [size](GFF-File-Format#file-structure-overview) | Description                                                      |
| -------- | --------- | ---- | ---------------------------------------------------------------- |
| [vertices](MDL-MDX-File-Format#vertex-structure) | [[float32](GFF-File-Format#gff-data-types)][GFF-File-Format#float](3)| 12×N | [array](2DA-File-Format) of [vertex](MDL-MDX-File-Format#vertex-structure) positions (X, Y, Z triplets)                    |

[vertices](MDL-MDX-File-Format#vertex-structure) [ARE](GFF-File-Format#are-area) stored as absolute world [coordinates](GFF-File-Format#are-area) in 32-[bit](GFF-File-Format#gff-data-types) IEEE floating-point [format](GFF-File-Format). Each [vertex](MDL-MDX-File-Format#vertex-structure) is 12 bytes (three [float32](GFF-File-Format#gff-data-types) [values](GFF-File-Format#gff-data-types)), and [vertices](MDL-MDX-File-Format#vertex-structure) [ARE](GFF-File-Format#are-area) typically shared between multiple [faces](MDL-MDX-File-Format#face-structure) to reduce memory usage and ensure geometric consistency.

**[vertex](MDL-MDX-File-Format#vertex-structure) [coordinate](GFF-File-Format#are-area) Systems:**

The [coordinate](GFF-File-Format#are-area) system used for [vertices](MDL-MDX-File-Format#vertex-structure) depends on the [walkmesh](BWM-File-Format) [type](GFF-File-Format#gff-data-types) and how implementations choose to process them:

- **For area walkmeshes ([WOK](BWM-File-Format))**: [vertices](MDL-MDX-File-Format#vertex-structure) [ARE](GFF-File-Format#are-area) stored in [world space](https://en.wikipedia.org/wiki/World_coordinates) [coordinates](GFF-File-Format#are-area). However, some implementations (e.g., [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:84-87`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L84-L87)) subtract the [walkmesh](BWM-File-Format) [position](MDL-MDX-File-Format#node-header) during reading to work in [local coordinates](https://en.wikipedia.org/wiki/Local_coordinates), which simplifies geometric operations. The [walkmesh](BWM-File-Format) [position](MDL-MDX-File-Format#node-header) is then added back when transforming to [world space](https://en.wikipedia.org/wiki/World_coordinates). This approach allows the [walkmesh](BWM-File-Format) to be positioned anywhere in the world while keeping local calculations simple.
  - **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:84-87`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L84-L87) - Subtracts [position](MDL-MDX-File-Format#node-header) during reading
  - **Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:94-103`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L94-L103) - Reads [vertices](MDL-MDX-File-Format#vertex-structure) directly without [offset](GFF-File-Format#file-structure-overview)

- **For placeable/door walkmeshes ([PWK](BWM-File-Format)/[DWK](BWM-File-Format))**: [vertices](MDL-MDX-File-Format#vertex-structure) [ARE](GFF-File-Format#are-area) stored relative to the object's local origin. When the object is placed in an area, the engine applies a [transformation matrix](https://en.wikipedia.org/wiki/Transformation_matrix) (including translation, [rotation](MDL-MDX-File-Format#node-header), and [scale](MDL-MDX-File-Format#node-header)) to convert these [local coordinates](https://en.wikipedia.org/wiki/Local_coordinates) to [world space](https://en.wikipedia.org/wiki/World_coordinates). This allows the same [walkmesh](BWM-File-Format) to be reused for multiple instances of the same object at different [positions](MDL-MDX-File-Format#node-header) and [orientations](MDL-MDX-File-Format#node-header).
  - **Reference**: [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:182-206`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L182-L206) - Applies [transformation](BWM-File-Format#vertex-data-processing) [matrix](BWM-File-Format#vertex-data-processing) to [vertices](MDL-MDX-File-Format#vertex-structure)

**Vendor Discrepancy ([vertex](MDL-MDX-File-Format#vertex-structure) [position](MDL-MDX-File-Format#node-header) Handling):**

| Implementation | Behavior | Reference |
|---------------|----------|-----------|
| kotorblender | Subtracts [position](MDL-MDX-File-Format#node-header) from [vertices](MDL-MDX-File-Format#vertex-structure) during read, adds back during write | `reader.py:86` |
| reone | Reads [vertices](MDL-MDX-File-Format#vertex-structure) directly without [position](MDL-MDX-File-Format#node-header) [offset](GFF-File-Format#file-structure-overview) | `bwmreader.cpp:98-102` |
| xoreos | Applies full [transformation](BWM-File-Format#vertex-data-processing) [matrix](BWM-File-Format#vertex-data-processing) to [vertices](MDL-MDX-File-Format#vertex-structure) | `walkmeshloader.cpp:182-206` |
| KotOR.js | Reads [vertices](MDL-MDX-File-Format#vertex-structure) directly, applies [matrix](BWM-File-Format#vertex-data-processing) transform later via `updateMatrix()` | `OdysseyWalkMesh.ts:243-258` |
| PyKotor | Reads [vertices](MDL-MDX-File-Format#vertex-structure) directly without [position](MDL-MDX-File-Format#node-header) [offset](GFF-File-Format#file-structure-overview) | `io_bwm.py:143` |

**Consensus**: Most implementations read [vertices](MDL-MDX-File-Format#vertex-structure) as stored and apply [transformations](BWM-File-Format#vertex-data-processing) at runtime. kotorblender's approach of subtracting [position](MDL-MDX-File-Format#node-header) during read is a Blender-specific optimization.

**[vertex](MDL-MDX-File-Format#vertex-structure) Sharing and Indexing:**

[vertices](MDL-MDX-File-Format#vertex-structure) [ARE](GFF-File-Format#are-area) shared by reference through the [index](2DA-File-Format#row-labels) system: multiple [faces](MDL-MDX-File-Format#face-structure) can reference the same [vertex](MDL-MDX-File-Format#vertex-structure) [index](2DA-File-Format#row-labels), ensuring that adjacent [faces](MDL-MDX-File-Format#face-structure) share exact [vertex](MDL-MDX-File-Format#vertex-structure) [positions](MDL-MDX-File-Format#node-header). This is critical for [adjacency](BWM-File-Format#walkable-adjacencies) calculations, as two [faces](MDL-MDX-File-Format#face-structure) [ARE](GFF-File-Format#are-area) considered adjacent only if they share exactly two vertices (forming a shared [edge](BWM-File-Format#edges)). The [vertex](MDL-MDX-File-Format#vertex-structure) [array](2DA-File-Format) is typically deduplicated during [walkmesh](BWM-File-Format) generation, with similar vertices (within a small tolerance) merged to reduce memory usage and ensure geometric consistency.

- **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:155-166`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L155-L166) - [vertex](MDL-MDX-File-Format#vertex-structure) deduplication using SimilarVertex class
- **Reference**: [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:264-269`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L264-L269) - [vertex](MDL-MDX-File-Format#vertex-structure) [array](2DA-File-Format) reading

### [faces](MDL-MDX-File-Format#face-structure)

| Name  | [type](GFF-File-Format#gff-data-types)     | [size](GFF-File-Format#file-structure-overview) | Description                                                      |
| ----- | -------- | ---- | ---------------------------------------------------------------- |
| [faces](MDL-MDX-File-Format#face-structure) | [[uint32](GFF-File-Format#gff-data-types)][GFF-File-Format#dword](3)| 12×N | [array](2DA-File-Format) of [face](MDL-MDX-File-Format#face-structure) [vertex](MDL-MDX-File-Format#vertex-structure) indices (triplets referencing [vertex](MDL-MDX-File-Format#vertex-structure) [array](2DA-File-Format)) |

Each [face](MDL-MDX-File-Format#face-structure) is a triangle defined by three [vertex](MDL-MDX-File-Format#vertex-structure) indices (0-based) into the [vertex](MDL-MDX-File-Format#vertex-structure) [array](2DA-File-Format). Each [face](MDL-MDX-File-Format#face-structure) entry is 12 bytes (three [uint32](GFF-File-Format#gff-data-types) [values](GFF-File-Format#gff-data-types)). The [vertex](MDL-MDX-File-Format#vertex-structure) [indices](2DA-File-Format#row-labels) define the triangle's [vertices](MDL-MDX-File-Format#vertex-structure) in counter-clockwise order when viewed from the front (the side the normal points toward).

**[face](MDL-MDX-File-Format#face-structure) Ordering:**
[faces](MDL-MDX-File-Format#face-structure) [ARE](GFF-File-Format#are-area) typically ordered with [walkable faces](BWM-File-Format#faces) first, followed by non-[walkable faces](BWM-File-Format#faces). This ordering is important because:

- [adjacency](BWM-File-Format#walkable-adjacencies) [data](GFF-File-Format#file-structure-overview) is stored only for [walkable faces](BWM-File-Format#faces), and the [adjacency](BWM-File-Format#walkable-adjacencies) [array](2DA-File-Format) [index](2DA-File-Format#row-labels) corresponds to the [walkable face](BWM-File-Format#faces)'s [position](MDL-MDX-File-Format#node-header) in the [walkable face](BWM-File-Format#faces) list (not the overall [face](MDL-MDX-File-Format#face-structure) list)
- The engine can quickly iterate through [walkable faces](BWM-File-Format#faces) for pathfinding without checking [material](MDL-MDX-File-Format#trimesh-header) [types](GFF-File-Format#gff-data-types)
- Non-[walkable faces](BWM-File-Format#faces) [ARE](GFF-File-Format#are-area) still needed for collision detection (preventing characters from walking through walls)

**Vendor Implementation Analysis:**

| Implementation | [face](MDL-MDX-File-Format#face-structure) Ordering | [adjacency](BWM-File-Format#walkable-adjacencies) Mapping | Reference |
|---------------|--------------|-------------------|-----------|
| **kotorblender** (writer) | Explicitly orders walkable first, then non-walkable | [adjacency](BWM-File-Format#walkable-adjacencies) [index](2DA-File-Format#row-labels) `i` maps to [face](MDL-MDX-File-Format#face-structure) [index](2DA-File-Format#row-labels) `i` in reordered list | [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:175-194`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L175-L194), [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:241-273`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L241-L273) |
| **PyKotor** (writer) | Explicitly orders walkable first, then non-walkable | [adjacency](BWM-File-Format#walkable-adjacencies) [index](2DA-File-Format#row-labels) maps to [position](MDL-MDX-File-Format#node-header) in reordered `faces` [array](2DA-File-Format) | [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py:213-215`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py#L213-L215), [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py:266-276`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py#L266-L276) |
| **KotOR.js** | Sorts walkable first in `rebuild()` method | [adjacency](BWM-File-Format#walkable-adjacencies) [matrix](BWM-File-Format#vertex-data-processing) [count](GFF-File-Format#file-structure-overview) equals [walkable faces](BWM-File-Format#faces) | [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:692`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L692), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:305-337`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L305-L337) |
| **xoreos** | Reads as stored; maintains separate `_walkableFaces` [array](2DA-File-Format) | Maps via `_walkableFaces[a]` to actual [face](MDL-MDX-File-Format#face-structure) index (works with any ordering) | [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:119-135`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L119-L135), [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:155-169`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L155-L169) |
| **reone** | Reads as stored | Does not load [adjacency](BWM-File-Format#walkable-adjacencies) [data](GFF-File-Format#file-structure-overview) | [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:74-87`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L74-L87) |

**Consensus**: [adjacency](BWM-File-Format#walkable-adjacencies) [array](2DA-File-Format) contains `num_walkable_faces` entries (not `num_faces`). When [faces](MDL-MDX-File-Format#face-structure) [ARE](GFF-File-Format#are-area) ordered walkable-first, [adjacency](BWM-File-Format#walkable-adjacencies) [index](2DA-File-Format#row-labels) `i` maps directly to [face](MDL-MDX-File-Format#face-structure) [index](2DA-File-Format#row-labels) `i` in the overall [array](2DA-File-Format). xoreos demonstrates an alternative mapping approach that works regardless of [file](GFF-File-Format) ordering.

**[face](MDL-MDX-File-Format#face-structure) Winding:**
The [vertex](MDL-MDX-File-Format#vertex-structure) order determines the [face](MDL-MDX-File-Format#face-structure)'s normal direction (via the right-hand rule). The engine uses this to determine which side of the [face](MDL-MDX-File-Format#face-structure) is "up" (walkable) versus "down" (non-walkable). [faces](MDL-MDX-File-Format#face-structure) should be oriented such that their normals point upward for [walkable surfaces](BWM-File-Format).

**Vendor Implementation Analysis:**

| Implementation | Normal Calculation | [vertex](MDL-MDX-File-Format#vertex-structure) Winding | Reference |
|---------------|-------------------|----------------|-----------|
| **KotOR.js** | `normal = (v3 - v2) × (v1 - v2)` (dynamic) | Counter-clockwise when viewed from front | [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:700-710`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L700-L710) |
| **kotorblender** | Reads precomputed normals from [file](GFF-File-Format) | Assumes counter-clockwise | [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:98-105`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L98-L105) |
| **reone** | Reads precomputed normals from [file](GFF-File-Format) | Reads as stored | [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:125-134`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L125-L134) |
| **xoreos** | Reads precomputed normals from [file](GFF-File-Format) | Reads as stored | Not explicitly shown in walkmeshloader.cpp |
| **PyKotor** | Uses `Face.normal()` from [geometry](MDL-MDX-File-Format#geometry-header) module | Counter-clockwise expected | [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py) |

**Consensus**: Normals follow right-hand rule: counter-clockwise [vertex](MDL-MDX-File-Format#vertex-structure) order (v1 → v2 → v3) when viewed from front yields upward-pointing normal for [walkable surfaces](BWM-File-Format). Cross product formulas `(v2 - v1) × (v3 - v1)` and `(v3 - v2) × (v1 - v2)` [ARE](GFF-File-Format#are-area) mathematically equivalent. Most implementations read precomputed normals from [file](GFF-File-Format) to avoid runtime overhead.

### [materials](MDL-MDX-File-Format#trimesh-header)

| Name      | [type](GFF-File-Format#gff-data-types)   | [size](GFF-File-Format#file-structure-overview) | Description                                                      |
| --------- | ------ | ---- | ---------------------------------------------------------------- |
| [materials](MDL-MDX-File-Format#trimesh-header) | [uint32](GFF-File-Format#gff-data-types)  | 4×N  | Surface [material](MDL-MDX-File-Format#trimesh-header) [index](2DA-File-Format#row-labels) per face (determines walkability)         |

**Surface [materials](MDL-MDX-File-Format#trimesh-header):**

Each [face](MDL-MDX-File-Format#face-structure) is assigned a [material](MDL-MDX-File-Format#trimesh-header) [type](GFF-File-Format#gff-data-types) that determines its physical properties and interaction behavior. The [material](MDL-MDX-File-Format#trimesh-header) ID is stored as a `uint32` per [face](MDL-MDX-File-Format#face-structure).

**Complete [material](MDL-MDX-File-Format#trimesh-header) List (from surfacemat.2da and vendor implementations):**

| ID | Name              | Walkable | Description                                                      | Source |
|----|-------------------|----------|------------------------------------------------------------------|--------|
| 0  | NotDefined/UNDEFINED | No    | Undefined material (default)                                     | All |
| 1  | Dirt              | Yes      | Standard walkable dirt surface                                   | All |
| 2  | Obscuring         | No       | Blocks line of sight but may be walkable                        | All |
| 3  | Grass             | Yes      | Walkable with grass sound effects                                | All |
| 4  | Stone             | Yes      | Walkable with stone sound effects                                | All |
| 5  | Wood              | Yes      | Walkable with wood sound effects                                 | All |
| 6  | Water             | Yes      | Shallow water - walkable with water sounds                       | All |
| 7  | Nonwalk/NON_WALK  | No       | Impassable surface - blocks character movement                  | All |
| 8  | Transparent       | No       | Transparent non-[walkable surfaces](BWM-File-Format)                                 | All |
| 9  | Carpet            | Yes      | Walkable with muffled footstep sounds                           | All |
| 10 | Metal             | Yes      | Walkable with metallic sound effects                            | All |
| 11 | Puddles           | Yes      | Walkable water puddles                                          | All |
| 12 | Swamp             | Yes      | Walkable swamp terrain                                          | All |
| 13 | Mud               | Yes      | Walkable mud surface                                             | All |
| 14 | Leaves            | Yes      | Walkable with leaf sound effects                                 | All |
| 15 | Lava              | No       | Damage-dealing surface (non-walkable)                            | All |
| 16 | BottomlessPit     | **Yes*** | Walkable but dangerous (fall damage)                            | kotorblender |
| 17 | DeepWater         | No       | Deep water - typically non-walkable or swim areas                | All |
| 18 | Door              | Yes      | Door surface (special handling)                                 | All |
| 19 | Snow/NON_WALK_GRASS | No     | Snow surface (non-walkable)                                      | kotorblender: Snow, PyKotor: NON_WALK_GRASS |
| 20 | Sand              | Yes      | Walkable sand surface                                            | kotorblender |
| 21 | BareBones         | Yes      | Walkable bare surface                                            | kotorblender |
| 22 | StoneBridge       | Yes      | Walkable stone bridge surface                                    | kotorblender |
| 30 | Trigger           | Yes      | Trigger surface (PyKotor extended)                               | PyKotor only |

**Note**: [material](MDL-MDX-File-Format#trimesh-header) 16 (BottomlessPit) walkability varies between implementations. kotorblender marks it as walkable (allowing the player to fall), while some game logic may treat it differently.

**Vendor Discrepancy ([material](MDL-MDX-File-Format#trimesh-header) Walkability):**

| [material](MDL-MDX-File-Format#trimesh-header) ID | kotorblender | PyKotor | Notes |
|-------------|--------------|---------|-------|
| 16 (BottomlessPit) | Walkable | Not in walkable set | May be intentionally walkable for fall damage |
| 19 (Snow) | Non-walkable | Non-walkable (NON_WALK_GRASS) | Name differs but behavior matches |
| 20+ | Named (Sand, BareBones, etc.) | Generic (SURFACE_MATERIAL_20, etc.) | kotorblender has more specific names |
| 30 (Trigger) | Not defined | Walkable | PyKotor extension |

**Consensus**: Use kotorblender's [material](MDL-MDX-File-Format#trimesh-header) names and walkability [flags](GFF-File-Format#gff-data-types) for IDs 0-22 as they're derived from `surfacemat.2da`.

[materials](MDL-MDX-File-Format#trimesh-header) control not just walkability but also:

- Footstep sound effects during movement
- Visual effects (ripples on water, dust on dirt)
- Damage-over-time mechanics (lava, acid)
- AI pathfinding cost (creatures prefer some surfaces over others)
- Line-of-sight blocking (obscuring [materials](MDL-MDX-File-Format#trimesh-header))

**Reference**: [`vendor/kotorblender/io_scene_kotor/constants.py:27-51`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/constants.py#L27-L51), [`Libraries/PyKotor/src/utility/common/geometry.py:1118-1172`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/utility/common/geometry.py#L1118-L1172)

### Derived [data](GFF-File-Format#file-structure-overview)

| Name           | [type](GFF-File-Format#gff-data-types)    | [size](GFF-File-Format#file-structure-overview) | Description                                                      |
| -------------- | ------- | ---- | ---------------------------------------------------------------- |
| [face](MDL-MDX-File-Format#face-structure) Normals   | [[float32](GFF-File-Format#gff-data-types)][GFF-File-Format#float](3) | 12×N | Normal [vectors](GFF-File-Format#gff-data-types) for each face (normalized)                        |
| Planar Distances | [float32](GFF-File-Format#gff-data-types) | 4×N | D component of plane equation (ax + by + cz + d = 0) for each [face](MDL-MDX-File-Format#face-structure) |

[face](MDL-MDX-File-Format#face-structure) normals [ARE](GFF-File-Format#are-area) precomputed unit [vectors](GFF-File-Format#gff-data-types) perpendicular to each [face](MDL-MDX-File-Format#face-structure). They [ARE](GFF-File-Format#are-area) calculated using the cross product of two [edge](BWM-File-Format#edges) [vectors](GFF-File-Format#gff-data-types): `normal = normalize((v2 - v1) × (v3 - v1))`. The normal direction follows the right-hand rule based on [vertex](MDL-MDX-File-Format#vertex-structure) winding order, with normals typically pointing upward for [walkable surfaces](BWM-File-Format).

**Normal Calculation (from KotOR.js):**

```typescript
// KotOR.js/src/odyssey/OdysseyWalkMesh.ts:700-710
const cb = vertex_3.clone().sub(vertex_2);
const ab = vertex_1.clone().sub(vertex_2);
cb.cross(ab);
face.normal.copy(cb);
```

**Planar Distance Calculation (from kotorblender):**

```python
# kotorblender/io_scene_kotor/format/bwm/writer.py:392-396
vert1 = Vector(self.verts[face[0]])
normal = Vector(self.facelist.normals[face_idx])
distance = -1.0 * (normal @ vert1)  # Dot product: -normal · v1
```

Planar distances [ARE](GFF-File-Format#are-area) the D component of the plane equation `ax + by + cz + d = 0`, where (a, b, c) is the [face](MDL-MDX-File-Format#face-structure) normal. The D component is calculated as `d = -normal · vertex1` for each [face](MDL-MDX-File-Format#face-structure), where vertex1 is typically the first [vertex](MDL-MDX-File-Format#vertex-structure) of the triangle. This precomputed [value](GFF-File-Format#gff-data-types) allows the engine to quickly test point-plane relationships without recalculating the plane equation each time.

These derived [values](GFF-File-Format#gff-data-types) [ARE](GFF-File-Format#are-area) stored in the [file](GFF-File-Format) to avoid recomputation during runtime, which is especially important for large [walkmeshes](BWM-File-Format) where thousands of [faces](MDL-MDX-File-Format#face-structure) need to be tested for intersection or containment queries.

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:125-134`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L125-L134), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:98-105`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L98-L105), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:700-710`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L700-L710)

### [AABB](BWM-File-Format#aabb-tree) Tree

| Name          | [type](GFF-File-Format#gff-data-types)    | [size](GFF-File-Format#file-structure-overview) | Description                                                      |
| ------------- | ------- | ---- | ---------------------------------------------------------------- |
| [AABB](BWM-File-Format#aabb-tree) [nodes](MDL-MDX-File-Format#node-structures)    | varies  | varies | [bounding box](MDL-MDX-File-Format#model-header) tree [nodes](MDL-MDX-File-Format#node-structures) for spatial acceleration ([WOK](BWM-File-Format) only)      |

Each [AABB](BWM-File-Format#aabb-tree) [node](MDL-MDX-File-Format#node-structures) is **44 bytes** and contains:

| Name                  | [type](GFF-File-Format#gff-data-types)    | [offset](GFF-File-Format#file-structure-overview) | [size](GFF-File-Format#file-structure-overview) | Description                                                      |
| --------------------- | ------- | ------ | ---- | ---------------------------------------------------------------- |
| Bounds Min            | [[float32](GFF-File-Format#gff-data-types)][GFF-File-Format#float](3) | 0 (0x00) | 12  | Minimum [bounding box](MDL-MDX-File-Format#model-header) coordinates (x, y, z)                      |
| Bounds Max            | [[float32](GFF-File-Format#gff-data-types)][GFF-File-Format#float](3) | 12 (0x0C) | 12  | Maximum [bounding box](MDL-MDX-File-Format#model-header) coordinates (x, y, z)                       |
| [face](MDL-MDX-File-Format#face-structure) [index](2DA-File-Format#row-labels)            | [int32](GFF-File-Format#gff-data-types)   | 24 (0x18) | 4    | [face](MDL-MDX-File-Format#face-structure) [index](2DA-File-Format#row-labels) for leaf [nodes](MDL-MDX-File-Format#node-structures), -1 (0xFFFFFFFF) for internal [nodes](MDL-MDX-File-Format#node-structures)   |
| Unknown               | [uint32](GFF-File-Format#gff-data-types)  | 28 (0x1C) | 4    | Unknown field (typically 4)                                       |
| Most Significant Plane| [uint32](GFF-File-Format#gff-data-types)  | 32 (0x20) | 4    | Split axis/plane identifier (see below)                          |
| Left Child [index](2DA-File-Format#row-labels)      | [uint32](GFF-File-Format#gff-data-types)  | 36 (0x24) | 4    | [index](2DA-File-Format#row-labels) to left child node (see encoding below)                   |
| Right Child [index](2DA-File-Format#row-labels)     | [uint32](GFF-File-Format#gff-data-types)  | 40 (0x28) | 4    | [index](2DA-File-Format#row-labels) to right child node (see encoding below)                 |

**Most Significant Plane [values](GFF-File-Format#gff-data-types):**

| [value](GFF-File-Format#gff-data-types) | Meaning |
|-------|---------|
| 0x00 | No children (leaf [node](MDL-MDX-File-Format#node-structures)) |
| 0x01 | Positive X axis split |
| 0x02 | Positive Y axis split |
| 0x03 | Positive Z axis split |
| 0xFFFFFFFE (-2) | Negative X axis split |
| 0xFFFFFFFD (-3) | Negative Y axis split |
| 0xFFFFFFFC (-4) | Negative Z axis split |

**Vendor Discrepancy ([AABB](BWM-File-Format#aabb-tree) Child [index](2DA-File-Format#row-labels) Encoding):**

| Implementation | Child [index](2DA-File-Format#row-labels) Encoding | Reference |
|---------------|---------------------|-----------|
| reone | 0-based index (reads directly into [array](2DA-File-Format)) | `bwmreader.cpp:164-167` |
| xoreos | Multiplies by 44 ([node](MDL-MDX-File-Format#node-structures) [size](GFF-File-Format#file-structure-overview)) to get [byte](GFF-File-Format#gff-data-types) [offset](GFF-File-Format#file-structure-overview) | `walkmeshloader.cpp:241-243` |
| KotOR.js | Reads as 0-based [index](2DA-File-Format#row-labels) | `OdysseyWalkMesh.ts:443-444` |
| kotorblender (write) | Uses 0-based [index](2DA-File-Format#row-labels) during generation | `aabb.py:61-64` |
| PyKotor (write) | Uses 1-based [indices](2DA-File-Format#row-labels) in output (0 = no child becomes 0xFFFFFFFF) | `io_bwm.py:259-262` |

**Critical Note**: The xoreos implementation multiplies child [indices](2DA-File-Format#row-labels) by 44 (the [node](MDL-MDX-File-Format#node-structures) [size](GFF-File-Format#file-structure-overview)) to compute [byte](GFF-File-Format#gff-data-types) [offsets](GFF-File-Format#file-structure-overview), while reone and KotOR.js use 0-based [array](2DA-File-Format) [indices](2DA-File-Format#row-labels). This suggests **two interpretations [ARE](GFF-File-Format#are-area) possible**:

1. **[array](2DA-File-Format) [index](2DA-File-Format#row-labels)**: Child [values](GFF-File-Format#gff-data-types) [ARE](GFF-File-Format#are-area) 0-based [indices](2DA-File-Format#row-labels) into the [AABB](BWM-File-Format#aabb-tree) [array](2DA-File-Format)
2. **Byte [offset](GFF-File-Format#file-structure-overview) divisor**: Child [values](GFF-File-Format#gff-data-types) [ARE](GFF-File-Format#are-area) [indices](2DA-File-Format#row-labels) that, when multiplied by 44, give the [byte](GFF-File-Format#gff-data-types) [offset](GFF-File-Format#file-structure-overview) from [AABB](BWM-File-Format#aabb-tree) start

Both interpretations yield the same result when reading, but differ in semantics. The **consensus** based on majority usage is that child [indices](2DA-File-Format#row-labels) [ARE](GFF-File-Format#are-area) **0-based [array](2DA-File-Format) [indices](2DA-File-Format#row-labels)**, with 0xFFFFFFFF indicating no child.

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:136-171`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L136-L171), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:112-130`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L112-L130), [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:218-248`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L218-L248), [`vendor/kotorblender/io_scene_kotor/aabb.py:40-64`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/aabb.py#L40-L64)

**[AABB](BWM-File-Format#aabb-tree) Tree Purpose:**

The Axis-Aligned Bounding Box ([AABB](BWM-File-Format#aabb-tree)) tree is a spatial acceleration [structure](GFF-File-Format#file-structure-overview) that dramatically improves performance for common operations. Without it, the engine would need to test every [face](MDL-MDX-File-Format#face-structure) individually (O(N) complexity), which becomes prohibitively slow for large [walkmeshes](BWM-File-Format) with thousands of [faces](MDL-MDX-File-Format#face-structure). The tree reduces this to O(log N) average case complexity.

**Key Operations Enabled:**

- **Ray Casting**: Finding where a ray intersects the [walkmesh](BWM-File-Format)
  - Mouse clicks: Determining which [walkable face](BWM-File-Format#faces) the player clicked on for movement commands
  - Projectiles: Testing if projectiles hit [walkable surfaces](BWM-File-Format) or obstacles
  - Line of sight: Checking if a line between two points intersects the [walkmesh](BWM-File-Format)
  - **Reference**: [`vendor/reone/src/libs/graphics/walkmesh.cpp:24-100`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/walkmesh.cpp#L24-L100)

- **Point Queries**: Determining which [face](MDL-MDX-File-Format#face-structure) a character is standing on
  - Character positioning: Finding the [walkable face](BWM-File-Format#faces) beneath a character's [position](MDL-MDX-File-Format#node-header)
  - Elevation calculation: Computing the Z [coordinate](GFF-File-Format#are-area) for a character at a given (X, Y) [position](MDL-MDX-File-Format#node-header)
  - Collision response: Determining surface normals and [materials](MDL-MDX-File-Format#trimesh-header) for physics calculations
  - **Reference**: [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:497-504`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L497-L504)

**Tree Construction (from kotorblender [AABB](BWM-File-Format#aabb-tree).py):**

[AABB](BWM-File-Format#aabb-tree) trees [ARE](GFF-File-Format#are-area) constructed recursively:

1. Compute bounding box for all [faces](MDL-MDX-File-Format#face-structure)
2. If only one [face](MDL-MDX-File-Format#face-structure) remains, create a leaf [node](MDL-MDX-File-Format#node-structures)
3. Find the longest axis of the [bounding box](MDL-MDX-File-Format#model-header)
4. Split [faces](MDL-MDX-File-Format#face-structure) into left/right groups based on centroid [position](MDL-MDX-File-Format#node-header) relative to [bounding box](MDL-MDX-File-Format#model-header) center
5. Recursively build left and right subtrees
6. Handle degenerate cases (all [faces](MDL-MDX-File-Format#face-structure) on one side) by trying alternative axes or splitting evenly

**Reference**: [`vendor/kotorblender/io_scene_kotor/aabb.py:40-126`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/aabb.py#L40-L126)

### Walkable [adjacencies](BWM-File-Format#walkable-adjacencies)

| Name            | [type](GFF-File-Format#gff-data-types)    | [size](GFF-File-Format#file-structure-overview) | Description                                                      |
| --------------- | ------- | ---- | ---------------------------------------------------------------- |
| [adjacencies](BWM-File-Format#walkable-adjacencies)     | [[int32](GFF-File-Format#gff-data-types)][GFF-File-Format#int](3)| 12×N | Three [adjacency](BWM-File-Format#walkable-adjacencies) [indices](2DA-File-Format#row-labels) per walkable face (-1 = no neighbor)     |

[adjacencies](BWM-File-Format#walkable-adjacencies) [ARE](GFF-File-Format#are-area) stored only for walkable faces ([faces](MDL-MDX-File-Format#face-structure) with walkable [materials](MDL-MDX-File-Format#trimesh-header)). Each [walkable face](BWM-File-Format#faces) has exactly three [adjacency](BWM-File-Format#walkable-adjacencies) entries, one for each edge ([edges](BWM-File-Format#edges) 0, 1, and 2). The [adjacency](BWM-File-Format#walkable-adjacencies) [count](GFF-File-Format#file-structure-overview) in the [header](GFF-File-Format#file-header) equals the number of [walkable faces](BWM-File-Format#faces), not the total [face](MDL-MDX-File-Format#face-structure) [count](GFF-File-Format#file-structure-overview).

**[adjacency](BWM-File-Format#walkable-adjacencies) Encoding:**

The [adjacency](BWM-File-Format#walkable-adjacencies) [index](2DA-File-Format#row-labels) is a clever encoding that stores both the adjacent [face](MDL-MDX-File-Format#face-structure) [index](2DA-File-Format#row-labels) and the specific [edge](BWM-File-Format#edges) within that [face](MDL-MDX-File-Format#face-structure) in a single integer:

- **Encoding Formula**: `adjacency_index = face_index * 3 + edge_index`
  - `face_index`: The [index](2DA-File-Format#row-labels) of the adjacent [walkable face](BWM-File-Format#faces) in the overall [face](MDL-MDX-File-Format#face-structure) [array](2DA-File-Format)
  - `edge_index`: The local [edge](BWM-File-Format#edges) index (0, 1, or 2) within that adjacent [face](MDL-MDX-File-Format#face-structure)
  - This encoding allows the engine to know not just which [face](MDL-MDX-File-Format#face-structure) is adjacent, but which [edge](BWM-File-Format#edges) of that [face](MDL-MDX-File-Format#face-structure) connects to the current [edge](BWM-File-Format#edges)
- **No Neighbor**: `-1` (0xFFFFFFFF signed) indicates no adjacent [walkable face](BWM-File-Format#faces) on that [edge](BWM-File-Format#edges)
  - This occurs when the [edge](BWM-File-Format#edges) is a boundary edge ([perimeter](BWM-File-Format#perimeters) [edge](BWM-File-Format#edges))
  - Boundary [edges](BWM-File-Format#edges) may have corresponding entries in the [edges](BWM-File-Format#edges) [array](2DA-File-Format) with transition information

**Decoding:**

```python
face_index = adjacency_index // 3
edge_index = adjacency_index % 3
```

**[adjacency](BWM-File-Format#walkable-adjacencies) Calculation (from kotorblender):**

```python
# kotorblender/io_scene_kotor/format/bwm/writer.py:241-273
for face_idx in range(self.num_walkable_faces):
    face = self.facelist.vertices[face_idx]
    edges = [
        tuple(sorted(edge))
        for edge in [(face[0], face[1]), (face[1], face[2]), (face[2], face[0])]
    ]
    for other_face_idx in range(face_idx + 1, self.num_walkable_faces):
        other_face = self.facelist.vertices[other_face_idx]
        other_edges = [
            tuple(sorted(edge))
            for edge in [
                (other_face[0], other_face[1]),
                (other_face[1], other_face[2]),
                (other_face[2], other_face[0]),
            ]
        ]
        for n in range(3):
            if self.adjacent_edges[face_idx][n] != -1:
                continue
            for j in range(3):
                if edges[n] == other_edges[j]:
                    self.adjacent_edges[face_idx][n] = 3 * other_face_idx + j
                    self.adjacent_edges[other_face_idx][j] = 3 * face_idx + n
                    break
```

**Vendor Discrepancy ([adjacency](BWM-File-Format#walkable-adjacencies) Decoding in xoreos):**

xoreos has a unique [adjacency](BWM-File-Format#walkable-adjacencies) decoding that differs from other implementations:

```cpp
// xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:164-168
const uint32_t edge = stream.readSint32LE();
if (edge < UINT32_MAX)
    adjFaces[_walkableFaces[a] * 3 + n] = (edge + (2 - edge % 3)) / 3 + prevFaceCount;
```

This formula `(edge + (2 - edge % 3)) / 3` appears to map [adjacency](BWM-File-Format#walkable-adjacencies) [indices](2DA-File-Format#row-labels) differently, possibly to recover the adjacent [face](MDL-MDX-File-Format#face-structure)'s [index](2DA-File-Format#row-labels) when decoding. The standard formula `edge // 3` is used by other implementations.

**Consensus**: Use `face_index = adjacency_index // 3` and `edge_index = adjacency_index % 3` for decoding.

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:58-59`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L58-L59), [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:155-169`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L155-L169), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:305-337`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L305-L337), [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:241-273`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L241-L273)

### [edges](BWM-File-Format#edges)

| Name  | [type](GFF-File-Format#gff-data-types)     | [size](GFF-File-Format#file-structure-overview) | Description                                                      |
| ----- | -------- | ---- | ---------------------------------------------------------------- |
| [edges](BWM-File-Format#edges) | varies   | varies | [perimeter](BWM-File-Format#perimeters) [edge](BWM-File-Format#edges) data (edge_index, transition pairs) ([WOK](BWM-File-Format) only)  |

The [edges](BWM-File-Format#edges) [array](2DA-File-Format) contains [perimeter](BWM-File-Format#perimeters) edges (boundary [edges](BWM-File-Format#edges) with no walkable neighbor). Each [edge](BWM-File-Format#edges) entry is **8 bytes**:

| Name        | [type](GFF-File-Format#gff-data-types)   | [size](GFF-File-Format#file-structure-overview) | Description                                                      |
| ----------- | ------ | ---- | ---------------------------------------------------------------- |
| [edge](BWM-File-Format#edges) [index](2DA-File-Format#row-labels)  | [uint32](GFF-File-Format#gff-data-types) | 4    | Encoded [edge](BWM-File-Format#edges) [index](2DA-File-Format#row-labels): `face_index * 3 + local_edge_index`        |
| Transition  | [int32](GFF-File-Format#gff-data-types)  | 4    | Transition ID for room/area connections, -1 if no transition     |

**[edge](BWM-File-Format#edges) [index](2DA-File-Format#row-labels) Encoding:**

The [edge](BWM-File-Format#edges) [index](2DA-File-Format#row-labels) uses the same encoding as [adjacency](BWM-File-Format#walkable-adjacencies) [indices](2DA-File-Format#row-labels): `edge_index = face_index * 3 + local_edge_index`. This identifies:

- Which [face](MDL-MDX-File-Format#face-structure) the [edge](BWM-File-Format#edges) belongs to (`face_index = edge_index // 3`)
- Which [edge](BWM-File-Format#edges) of that face (0, 1, or 2) (`local_edge_index = edge_index % 3`)

**[edge](BWM-File-Format#edges) Definitions:**

| Local [edge](BWM-File-Format#edges) | [vertices](MDL-MDX-File-Format#vertex-structure) | Description |
|------------|----------|-------------|
| 0 | v1 → v2 | First edge (between [vertex](MDL-MDX-File-Format#vertex-structure) 1 and [vertex](MDL-MDX-File-Format#vertex-structure) 2) |
| 1 | v2 → v3 | Second edge (between [vertex](MDL-MDX-File-Format#vertex-structure) 2 and [vertex](MDL-MDX-File-Format#vertex-structure) 3) |
| 2 | v3 → v1 | Third edge (between [vertex](MDL-MDX-File-Format#vertex-structure) 3 and [vertex](MDL-MDX-File-Format#vertex-structure) 1) |

**Reference**: [`vendor/KotOR.js/src/odyssey/WalkmeshEdge.ts:67-79`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/WalkmeshEdge.ts#L67-L79)

**[perimeter](BWM-File-Format#perimeters) [edges](BWM-File-Format#edges):**

[perimeter](BWM-File-Format#perimeters) [edges](BWM-File-Format#edges) [ARE](GFF-File-Format#are-area) [edges](BWM-File-Format#edges) of [walkable faces](BWM-File-Format#faces) that have no adjacent walkable neighbor. These [edges](BWM-File-Format#edges) form the boundaries of walkable regions and [ARE](GFF-File-Format#are-area) critical for:

- **Area Transitions**: [edges](BWM-File-Format#edges) with non-negative transition IDs link to door connections or area boundaries
- **Boundary Detection**: [perimeter](BWM-File-Format#perimeters) [edges](BWM-File-Format#edges) define the limits of walkable space
- **Visual Debugging**: [perimeter](BWM-File-Format#perimeters) [edges](BWM-File-Format#edges) can be visualized to show [walkmesh](BWM-File-Format) boundaries in level editors

**Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:138-143`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L138-L143), [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:275-307`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L275-L307), [`vendor/KotOR.js/src/odyssey/WalkmeshEdge.ts:15-110`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/WalkmeshEdge.ts#L15-L110), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:339-345`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L339-L345)

### [perimeters](BWM-File-Format#perimeters)

| Name      | [type](GFF-File-Format#gff-data-types)   | [size](GFF-File-Format#file-structure-overview) | Description                                                      |
| --------- | ------ | ---- | ---------------------------------------------------------------- |
| [perimeters](BWM-File-Format#perimeters) | [uint32](GFF-File-Format#gff-data-types) | 4×N  | [indices](2DA-File-Format#row-labels) into [edge](BWM-File-Format#edges) [array](2DA-File-Format) marking end of [perimeter](BWM-File-Format#perimeters) loops ([WOK](BWM-File-Format) only) |

[perimeters](BWM-File-Format#perimeters) mark the end of closed loops of [perimeter](BWM-File-Format#perimeters) [edges](BWM-File-Format#edges). Each [perimeter](BWM-File-Format#perimeters) [value](GFF-File-Format#gff-data-types) is an [index](2DA-File-Format#row-labels) into the [edge](BWM-File-Format#edges) [array](2DA-File-Format), indicating where a [perimeter](BWM-File-Format#perimeters) loop ends. This allows the engine to traverse complete boundary loops for pathfinding and area transitions.

**Vendor Discrepancy ([perimeter](BWM-File-Format#perimeters) [index](2DA-File-Format#row-labels) Base):**

| Implementation | [index](2DA-File-Format#row-labels) Base | Reference |
|---------------|------------|-----------|
| kotorblender (write) | 1-based (adds 1 when writing) | `writer.py:303` |
| KotOR.js (read) | Reads as-is (doesn't subtract 1) | `OdysseyWalkMesh.ts:349` |
| PyKotor (write) | 1-based (adds 1 when writing) | `io_bwm.py:315` |

**Critical Note**: The [perimeter](BWM-File-Format#perimeters) [indices](2DA-File-Format#row-labels) may be either 0-based or 1-based depending on interpretation. kotorblender and PyKotor write 1-based [indices](2DA-File-Format#row-labels), while KotOR.js reads them without adjustment. This suggests:

- **Stored [format](GFF-File-Format)**: [perimeter](BWM-File-Format#perimeters) [values](GFF-File-Format#gff-data-types) [ARE](GFF-File-Format#are-area) 1-based [indices](2DA-File-Format#row-labels) marking the end of each loop
- **Loop 1**: [edges](BWM-File-Format#edges) from [index](2DA-File-Format#row-labels) 0 to `perimeters[0] - 1` (when 1-based)
- **Loop N**: [edges](BWM-File-Format#edges) from `perimeters[N-2]` to `perimeters[N-1] - 1`

**[perimeter](BWM-File-Format#perimeters) Loop Construction (from KotOR.js):**

```typescript
// KotOR.js/src/odyssey/OdysseyWalkMesh.ts:716-782
while(edges.length){
  if(!current_perimeter){
    let edge: WalkmeshEdge = edges.shift();
    current_perimeter = {
      closed: false,
      start: edge.vertex_1,
      next: edge.vertex_2,
      edges: [edge]
    }
  }
  if(current_perimeter.next == current_perimeter.start){
    current_perimeter.closed = true;
    current_perimeter = undefined;
    continue;
  }
  let next_idx = edges.findIndex((n_edge) => n_edge.vertex_1 == current_perimeter.next);
  if(next_idx >= 0){
    let n_edge = edges.splice(next_idx, 1)[0];
    current_perimeter.edges.push(n_edge);
    current_perimeter.next = n_edge.vertex_2;
  }
}
```

**Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:145-147`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L145-L147), [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:302-303`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L302-L303), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:347-352`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L347-L352), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:716-782`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L716-L782)

---

## Runtime [model](MDL-MDX-File-Format)

The runtime [model](MDL-MDX-File-Format) provides high-level, in-memory representations of [walkmesh](BWM-File-Format) [data](GFF-File-Format#file-structure-overview) that [ARE](GFF-File-Format#are-area) easier to work with than raw binary [structures](GFF-File-Format#file-structure-overview). These classes abstract away the binary [format](GFF-File-Format) details and provide convenient methods for common operations.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:25-496`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L25-L496)

### [BWM](BWM-File-Format) Class

The `BWM` class represents a complete [walkmesh](BWM-File-Format) in memory, providing a high-level interface for working with [walkmesh](BWM-File-Format) [data](GFF-File-Format#file-structure-overview).

**Key Attributes:**

- **`faces`**: Ordered list of `BWMFace` objects representing all triangular [faces](MDL-MDX-File-Format#face-structure) in the [walkmesh](BWM-File-Format)
  - [faces](MDL-MDX-File-Format#face-structure) [ARE](GFF-File-Format#are-area) typically ordered with [walkable faces](BWM-File-Format#faces) first, followed by non-[walkable faces](BWM-File-Format#faces)
  - The [face](MDL-MDX-File-Format#face-structure) list is the primary [data](GFF-File-Format#file-structure-overview) [structure](GFF-File-Format#file-structure-overview) for accessing [walkmesh](BWM-File-Format) [geometry](MDL-MDX-File-Format#geometry-header)
- **`walkmesh_type`**: type of walkmesh (`BWMType.AreaModel` for [WOK](BWM-File-Format), `BWMType.PlaceableOrDoor` for [PWK](BWM-File-Format)/[DWK](BWM-File-Format))
- **`position`**: 3D [position](MDL-MDX-File-Format#node-header) [offset](GFF-File-Format#file-structure-overview) for the [walkmesh](BWM-File-Format) in world space
- **Positional hooks**: `relative_hook1`, `relative_hook2`, `absolute_hook1`, `absolute_hook2` - Used by the engine for positioning and interaction points

**Helper Methods:**

- `walkable_faces()`: Returns a filtered list of only walkable faces (for pathfinding)
- `unwalkable_faces()`: Returns a filtered list of only non-walkable faces (for collision detection)
- `vertices()`: Returns unique [vertex](MDL-MDX-File-Format#vertex-structure) objects referenced by faces (identity-based uniqueness)
- `adjacencies(face)`: Computes [adjacencies](BWM-File-Format#walkable-adjacencies) for a specific [face](MDL-MDX-File-Format#face-structure)
- `edges()`: Returns [perimeter](BWM-File-Format#perimeters) edges ([edges](BWM-File-Format#edges) with no walkable neighbor)
- `aabbs()`: Generates [AABB](BWM-File-Format#aabb-tree) tree for spatial acceleration

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:126-289`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L126-L289), [`vendor/reone/include/reone/graphics/walkmesh.h:27-89`](https://github.com/th3w1zard1/reone/blob/master/include/reone/graphics/walkmesh.h#L27-L89), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:24-205`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L24-L205)

### BWMFace Class

Each `BWMFace` represents a single triangular [face](MDL-MDX-File-Format#face-structure) in the [walkmesh](BWM-File-Format), containing all information needed for collision detection, pathfinding, and rendering.

**Key Attributes:**

- **`v1`, `v2`, `v3`**: [vertex](MDL-MDX-File-Format#vertex-structure) objects (`Vector3` instances) defining the triangle's three corners
  - [vertices](MDL-MDX-File-Format#vertex-structure) [ARE](GFF-File-Format#are-area) shared by reference: multiple [faces](MDL-MDX-File-Format#face-structure) can reference the same [vertex](MDL-MDX-File-Format#vertex-structure) object
  - This ensures geometric consistency and enables efficient [adjacency](BWM-File-Format#walkable-adjacencies) calculations
- **`material`**: `SurfaceMaterial` enum determining walkability and physical properties
  - Controls whether the [face](MDL-MDX-File-Format#face-structure) is walkable, blocks line of sight, produces sound effects, etc.
- **`trans1`, `trans2`, `trans3`**: Optional per-[edge](BWM-File-Format#edges) transition [indices](2DA-File-Format#row-labels)
  - These [ARE](GFF-File-Format#are-area) **NOT** unique identifiers and do **NOT** encode geometric [adjacency](BWM-File-Format#walkable-adjacencies)
  - They reference area/room transition data (e.g., door connections, area boundaries)
  - Only present on [edges](BWM-File-Format#edges) that have corresponding entries in the [edges](BWM-File-Format#edges) [array](2DA-File-Format)

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:934-1040`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L934-L1040), [`vendor/KotOR.js/src/three/odyssey/OdysseyFace3.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/three/odyssey/OdysseyFace3.ts)

### BWMEdge Class

The `BWMEdge` class represents a boundary edge (an [edge](BWM-File-Format#edges) with no walkable neighbor) computed from [adjacency](BWM-File-Format#walkable-adjacencies) [data](GFF-File-Format#file-structure-overview).

**Key Attributes:**

- **`face`**: The `BWMFace` object this [edge](BWM-File-Format#edges) belongs to
- **`index`**: The local [edge](BWM-File-Format#edges) index (0, 1, or 2) within the [face](MDL-MDX-File-Format#face-structure)
  - [edge](BWM-File-Format#edges) 0: between `v1` and `v2`
  - [edge](BWM-File-Format#edges) 1: between `v2` and `v3`
  - [edge](BWM-File-Format#edges) 2: between `v3` and `v1`
- **`transition`**: Optional transition ID linking to area/room transition [data](GFF-File-Format#file-structure-overview)
  - `-1` indicates no transition (just a boundary [edge](BWM-File-Format#edges))
  - Non-negative [values](GFF-File-Format#gff-data-types) reference door connections or area boundaries
- **`final`**: Boolean [flag](GFF-File-Format#gff-data-types) marking the end of a [perimeter](BWM-File-Format#perimeters) loop

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:1273-1352`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L1273-L1352), [`vendor/KotOR.js/src/odyssey/WalkmeshEdge.ts:15-110`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/WalkmeshEdge.ts#L15-L110)

### BWMNodeAABB Class

The `BWMNodeAABB` class represents a [node](MDL-MDX-File-Format#node-structures) in the [AABB](BWM-File-Format#aabb-tree) tree, providing spatial acceleration for intersection queries.

**Key Attributes:**

- **`bb_min`, `bb_max`**: Minimum and maximum [bounding box](MDL-MDX-File-Format#model-header) coordinates (x, y, z) defining the [node](MDL-MDX-File-Format#node-structures)'s spatial extent
- **`face`**: For leaf [nodes](MDL-MDX-File-Format#node-structures), the associated [face](MDL-MDX-File-Format#face-structure); `None` for internal [nodes](MDL-MDX-File-Format#node-structures)
- **`sigplane`**: The axis (X, Y, or Z) along which this [node](MDL-MDX-File-Format#node-structures) splits space
- **`left`, `right`**: References to child nodes (for internal [nodes](MDL-MDX-File-Format#node-structures)) or `None` (for leaf [nodes](MDL-MDX-File-Format#node-structures))

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:1052-1216`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L1052-L1216)

---

## Implementation Comparison

This section documents discrepancies between vendor implementations and provides consensus recommendations.

### Summary of [KEY](KEY-File-Format) Differences

| Feature | reone | xoreos | KotOR.js | kotorblender | PyKotor | Consensus |
|---------|-------|--------|----------|--------------|---------|-----------|
| [vertex](MDL-MDX-File-Format#vertex-structure) [position](MDL-MDX-File-Format#node-header) handling | Direct read | Transform [matrix](BWM-File-Format#vertex-data-processing) | Direct + [matrix](BWM-File-Format#vertex-data-processing) | Subtracts [position](MDL-MDX-File-Format#node-header) | Direct read | Direct read (most common) |
| [AABB](BWM-File-Format#aabb-tree) child [indices](2DA-File-Format#row-labels) | 0-based | Multiplied by 44 | 0-based | 0-based | 1-based on write | 0-based [array](2DA-File-Format) [indices](2DA-File-Format#row-labels) |
| [perimeter](BWM-File-Format#perimeters) [indices](2DA-File-Format#row-labels) | - | - | As-is | 1-based write | 1-based write | 1-based (marking end of loop) |
| [material](MDL-MDX-File-Format#trimesh-header) 16 (BottomlessPit) | - | - | - | Walkable | Not walkable | Walkable (kotorblender source) |
| [adjacency](BWM-File-Format#walkable-adjacencies) decoding | [edge](BWM-File-Format#edges) // 3 | Special formula | [edge](BWM-File-Format#edges) // 3 | [edge](BWM-File-Format#edges) // 3 | [edge](BWM-File-Format#edges) // 3 | [edge](BWM-File-Format#edges) // 3 |

### Recommendations for PyKotor

Based on vendor analysis:

1. **[material](MDL-MDX-File-Format#trimesh-header) Names**: Update `SurfaceMaterial` enum to use kotorblender's names for IDs 20-22 (Sand, BareBones, StoneBridge)
2. **[material](MDL-MDX-File-Format#trimesh-header) 16 Walkability**: Consider making BottomlessPit walkable to match kotorblender
3. **[perimeter](BWM-File-Format#perimeters) [indices](2DA-File-Format#row-labels)**: Current 1-based implementation matches kotorblender
4. **[AABB](BWM-File-Format#aabb-tree) Child [indices](2DA-File-Format#row-labels)**: Current implementation should write 0-based indices (or 0xFFFFFFFF for no child)
5. **Vertex Handling**: Current direct-read approach is correct

### Test Coverage Analysis

PyKotor's `test_bwm.py` provides comprehensive coverage including:

- ✅ [header](GFF-File-Format#file-header) validation (magic, version)
- ✅ [walkmesh](BWM-File-Format) type ([WOK](BWM-File-Format) vs [PWK](BWM-File-Format)/[DWK](BWM-File-Format))
- ✅ [vertex](MDL-MDX-File-Format#vertex-structure) roundtrip and deduplication
- ✅ [face](MDL-MDX-File-Format#face-structure) ordering (walkable first)
- ✅ [material](MDL-MDX-File-Format#trimesh-header) preservation
- ✅ [adjacency](BWM-File-Format#walkable-adjacencies) calculation
- ✅ [edge](BWM-File-Format#edges)/[perimeter](BWM-File-Format#perimeters) identification
- ✅ [AABB](BWM-File-Format#aabb-tree) tree generation ([WOK](BWM-File-Format) only)
- ✅ Hook [vector](GFF-File-Format#gff-data-types) preservation
- ✅ Complete roundtrip testing

**Missing Test Coverage:**

- ⚠️ [AABB](BWM-File-Format#aabb-tree) tree raycasting functionality
- ⚠️ Point-in-[face](MDL-MDX-File-Format#face-structure) queries
- ⚠️ Comparison against actual game [files](GFF-File-Format)
- ⚠️ Multi-room [walkmesh](BWM-File-Format) loading
- ⚠️ [transformation](BWM-File-Format#vertex-data-processing) [matrix](BWM-File-Format#vertex-data-processing) application

---

## Implementation Details

This section covers important implementation considerations and best practices when working with [BWM files](BWM-File-Format).

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py:42-182`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py#L42-L182)

The binary reader follows a standard pattern that efficiently loads [walkmesh](BWM-File-Format) [data](GFF-File-Format#file-structure-overview) using the [offset](GFF-File-Format#file-structure-overview)-based [structure](GFF-File-Format#file-structure-overview):

1. **Validate [header](GFF-File-Format#file-header)**: Check magic "[BWM](BWM-File-Format) " and version "V1.0" to ensure [file](GFF-File-Format) [format](GFF-File-Format) compatibility
2. **Read [walkmesh](BWM-File-Format) properties**: Load [type](GFF-File-Format#gff-data-types), hook [vectors](GFF-File-Format#gff-data-types), and [position](MDL-MDX-File-Format#node-header)
3. **Read [data](GFF-File-Format#file-structure-overview) table [offsets](GFF-File-Format#file-structure-overview)**: Load all [offset](GFF-File-Format#file-structure-overview) and [count](GFF-File-Format#file-structure-overview) [values](GFF-File-Format#gff-data-types) from the [header](GFF-File-Format#file-header)
4. **Seek and read [data](GFF-File-Format#file-structure-overview) tables**: For each [data](GFF-File-Format#file-structure-overview) table, seek to the specified [offset](GFF-File-Format#file-structure-overview) and read the appropriate number of elements
5. **Process [WOK](BWM-File-Format)-specific [data](GFF-File-Format#file-structure-overview)** (if [type](GFF-File-Format#gff-data-types) is [WOK](BWM-File-Format)): Load [AABB](BWM-File-Format#aabb-tree) tree [nodes](MDL-MDX-File-Format#node-structures), [adjacency](BWM-File-Format#walkable-adjacencies) [data](GFF-File-Format#file-structure-overview), [edges](BWM-File-Format#edges), and [perimeters](BWM-File-Format#perimeters)
6. **Process [edges](BWM-File-Format#edges) and transitions**: Extract transition information from the [edges](BWM-File-Format#edges) [array](2DA-File-Format) and apply it to the corresponding [faces](MDL-MDX-File-Format#face-structure)
7. **Construct runtime `BWM` object**: Create the high-level [walkmesh](BWM-File-Format) representation with all loaded [data](GFF-File-Format#file-structure-overview)

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py:185-355`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py#L185-L355)

The binary writer must perform several complex operations:

1. **Calculate all [data](GFF-File-Format#file-structure-overview) table [offsets](GFF-File-Format#file-structure-overview)**: This requires computing the [size](GFF-File-Format#file-structure-overview) of each [data](GFF-File-Format#file-structure-overview) table before writing
2. **Write [header](GFF-File-Format#file-header) with [offsets](GFF-File-Format#file-structure-overview)**: Write the magic, version, [walkmesh](BWM-File-Format) properties, and all [offset](GFF-File-Format#file-structure-overview)/[count](GFF-File-Format#file-structure-overview) [values](GFF-File-Format#gff-data-types)
3. **Write [data](GFF-File-Format#file-structure-overview) tables in order**: Write [vertices](MDL-MDX-File-Format#vertex-structure), [face](MDL-MDX-File-Format#face-structure) [indices](2DA-File-Format#row-labels), [materials](MDL-MDX-File-Format#trimesh-header), normals, planar distances, [AABB](BWM-File-Format#aabb-tree) [nodes](MDL-MDX-File-Format#node-structures), [adjacencies](BWM-File-Format#walkable-adjacencies), [edges](BWM-File-Format#edges), and [perimeters](BWM-File-Format#perimeters)
4. **Compute [adjacencies](BWM-File-Format#walkable-adjacencies) from [geometry](MDL-MDX-File-Format#geometry-header)**: The runtime [model](MDL-MDX-File-Format) doesn't store [adjacency](BWM-File-Format#walkable-adjacencies) [data](GFF-File-Format#file-structure-overview) directly, so it must be computed
5. **Generate [AABB](BWM-File-Format#aabb-tree) tree if writing [WOK file](BWM-File-Format)**: [AABB](BWM-File-Format#aabb-tree) tree generation is a complex recursive operation
6. **Compute [edges](BWM-File-Format#edges) and [perimeters](BWM-File-Format#perimeters) from [adjacency](BWM-File-Format#walkable-adjacencies) [data](GFF-File-Format#file-structure-overview)**: Identify [perimeter](BWM-File-Format#perimeters) [edges](BWM-File-Format#edges) and group them into loops

**Critical Implementation Notes:**

**Identity vs. [value](GFF-File-Format#gff-data-types) Equality:**

- Use identity-based searches (`is` operator) when mapping [faces](MDL-MDX-File-Format#face-structure) back to [indices](2DA-File-Format#row-labels)
- [value](GFF-File-Format#gff-data-types)-based equality can collide: two different [face](MDL-MDX-File-Format#face-structure) objects with the same [vertices](MDL-MDX-File-Format#vertex-structure) [ARE](GFF-File-Format#are-area) equal by [value](GFF-File-Format#gff-data-types) but distinct by identity
- When computing [edge](BWM-File-Format#edges) indices (`face_index * 3 + edge_index`), you must use the actual [face](MDL-MDX-File-Format#face-structure) object's [index](2DA-File-Format#row-labels) in the [array](2DA-File-Format), not search by [value](GFF-File-Format#gff-data-types)
- **Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:564-587`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L564-L587)

**Transitions vs. [adjacency](BWM-File-Format#walkable-adjacencies):**

- `trans1`/`trans2`/`trans3` [ARE](GFF-File-Format#are-area) optional metadata only, **NOT** [adjacency](BWM-File-Format#walkable-adjacencies) definitions
- [adjacency](BWM-File-Format#walkable-adjacencies) is computed purely from geometry (shared [vertices](MDL-MDX-File-Format#vertex-structure) between [walkable faces](BWM-File-Format#faces))
- Transitions reference area/room [data](GFF-File-Format#file-structure-overview) structures (doors, area boundaries) and [ARE](GFF-File-Format#are-area) only present on [perimeter](BWM-File-Format#perimeters) [edges](BWM-File-Format#edges)

**[vertex](MDL-MDX-File-Format#vertex-structure) Sharing:**

- [vertices](MDL-MDX-File-Format#vertex-structure) [ARE](GFF-File-Format#are-area) shared by object identity: multiple [faces](MDL-MDX-File-Format#face-structure) reference the same `Vector3` object
- This ensures geometric consistency: adjacent [faces](MDL-MDX-File-Format#face-structure) share exact [vertex](MDL-MDX-File-Format#vertex-structure) [positions](MDL-MDX-File-Format#node-header)
- When modifying [vertices](MDL-MDX-File-Format#vertex-structure), changes affect all [faces](MDL-MDX-File-Format#face-structure) that reference that [vertex](MDL-MDX-File-Format#vertex-structure)

**[face](MDL-MDX-File-Format#face-structure) Ordering:**

- [walkable faces](BWM-File-Format#faces) [ARE](GFF-File-Format#are-area) typically ordered before non-[walkable faces](BWM-File-Format#faces) in the [face](MDL-MDX-File-Format#face-structure) [array](2DA-File-Format)
- This ordering is important because [adjacency](BWM-File-Format#walkable-adjacencies) [data](GFF-File-Format#file-structure-overview) [indices](2DA-File-Format#row-labels) correspond to [walkable face](BWM-File-Format#faces) [positions](MDL-MDX-File-Format#node-header)
- When writing, maintain this ordering to ensure [adjacency](BWM-File-Format#walkable-adjacencies) [indices](2DA-File-Format#row-labels) remain valid

---

This documentation aims to provide a comprehensive overview of the KotOR [BWM file](BWM-File-Format) [format](GFF-File-Format), focusing on the detailed [file](GFF-File-Format) [structure](GFF-File-Format#file-structure-overview) and [data](GFF-File-Format#file-structure-overview) [formats](GFF-File-Format) used within the games, with particular attention to vendor implementation discrepancies and consensus recommendations.
