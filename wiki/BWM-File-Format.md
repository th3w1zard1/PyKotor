# KotOR BWM file format Documentation

This document provides a detailed description of the BWM (Binary WalkMesh) file format used in Knights of the Old Republic (KotOR) games. BWM files, stored on disk as WOK files, define walkable surfaces for pathfinding and collision detection in game areas.

**Related formats:** BWM files [ARE](GFF-File-Format#are-area) used in conjunction with [GFF ARE files](GFF-File-Format#are-area) which define [area properties](GFF-File-Format#are-area) and contain references to walkmesh files.

## Table of Contents

- KotOR BWM file format Documentation
  - Table of Contents
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

## file structure Overview

BWM (Binary WalkMesh) files define walkable surfaces using triangular [faces](MDL-MDX-File-Format#face-structure). Each [face](MDL-MDX-File-Format#face-structure) has [material](MDL-MDX-File-Format#trimesh-header) properties that determine whether it's walkable, [adjacency](BWM-File-Format#walkable-adjacencies) information for pathfinding, and optional [edge](BWM-File-Format#edges) transitions for area connections. The format supports two distinct walkmesh types: area walkmeshes (WOK) for level [geometry](MDL-MDX-File-Format#geometry-header) and placeable/door walkmeshes (PWK/DWK) for interactive objects.

walkmeshes serve multiple critical functions in KotOR:

- **Pathfinding**: NPCs and the player use walkmeshes to navigate areas, with [adjacency](BWM-File-Format#walkable-adjacencies) data enabling pathfinding algorithms to find routes between [walkable faces](BWM-File-Format#faces)
- **Collision Detection**: The engine uses walkmeshes to prevent characters from walking through walls, objects, and impassable terrain
- **Spatial Queries**: [AABB](BWM-File-Format#aabb-tree) trees enable efficient ray casting (mouse clicks, projectiles) and point-in-triangle tests (determining which [face](MDL-MDX-File-Format#face-structure) a character stands on)
- **Area Transitions**: [edge](BWM-File-Format#edges) transitions link walkmeshes to door connections and area boundaries, enabling seamless movement between rooms

The binary format uses a header-based structure where offsets point to various data tables, allowing efficient random access to [vertices](MDL-MDX-File-Format#vertex-structure), [faces](MDL-MDX-File-Format#face-structure), [materials](MDL-MDX-File-Format#trimesh-header), and acceleration structures. This design enables the engine to load only necessary portions of large walkmeshes or stream data as needed.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/)

**Reference Implementations:**

- [`vendor/reone/src/libs/graphics/format/bwmreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp) - C++ BWM reader with complete parsing logic
- [`vendor/reone/include/reone/graphics/format/bwmreader.h`](https://github.com/th3w1zard1/reone/blob/master/include/reone/graphics/format/bwmreader.h) - BWM reader header with type definitions
- [`vendor/reone/include/reone/graphics/walkmesh.h`](https://github.com/th3w1zard1/reone/blob/master/include/reone/graphics/walkmesh.h) - Runtime walkmesh class definition
- [`vendor/reone/src/libs/graphics/walkmesh.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/walkmesh.cpp) - Runtime raycasting implementation
- [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py) - Python BWM reader for Blender import
- [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py) - Python BWM writer for Blender export with [adjacency](BWM-File-Format#walkable-adjacencies) calculation
- [`vendor/kotorblender/io_scene_kotor/aabb.py`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/aabb.py) - [AABB](BWM-File-Format#aabb-tree) tree generation algorithm
- [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp) - xoreos walkmesh loader with pathfinding integration
- [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts) - Complete TypeScript walkmesh implementation with raycasting and spatial queries
- [`vendor/KotOR.js/src/odyssey/WalkmeshEdge.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/WalkmeshEdge.ts) - WalkmeshEdge class for [perimeter](BWM-File-Format#perimeters) [edge](BWM-File-Format#edges) handling
- [`vendor/KotOR.js/src/odyssey/WalkmeshPerimeter.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/WalkmeshPerimeter.ts) - WalkmeshPerimeter class for boundary loop management

---

## Binary format

### file header

| Name         | type    | offset | size | Description                                    |
| ------------ | ------- | ------ | ---- | ---------------------------------------------- |
| Magic        | [char](GFF-File-Format#gff-data-types) | 0 (0x00)   | 4    | Always `"BWM "` (space-padded)                 |
| Version      | [char](GFF-File-Format#gff-data-types) | 4 (0x04)   | 4    | Always `"V1.0"`                                 |

The file header begins with an 8-[byte](GFF-File-Format#gff-data-types) signature that must exactly match `"BWM V1.0"` (the space after "BWM" is significant). This signature serves as both a file type identifier and version marker. The version string "V1.0" indicates this is the first and only version of the BWM format used in KotOR games. Implementations should validate this header before proceeding with file parsing to ensure they're reading a valid BWM file.

**Vendor Consensus:** All implementations (reone, xoreos, KotOR.js, kotorblender, PyKotor) agree on this header format and validation.

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:28`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L28), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:52-59`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L52-L59), [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:73-75`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L73-L75), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:452-454`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L452-L454)

### walkmesh Properties

The walkmesh properties section immediately follows the header and contains type information, hook vectors, and position data. This section is 52 bytes total (from offset 0x08 to 0x3C), providing essential metadata about the walkmesh's purpose and positioning.

| Name                    | type      | offset | size | Description                                                      |
| ----------------------- | --------- | ------ | ---- | ---------------------------------------------------------------- |
| type                    | [uint32](GFF-File-Format#gff-data-types)    | 8 (0x08)   | 4    | walkmesh type (0=PWK/DWK, 1=WOK/Area)                            |
| Relative Use position 1 | [float32](GFF-File-Format#gff-data-types)| 12 (0x0C)   | 12   | Relative use hook position 1 (x, y, z)                           |
| Relative Use position 2 | [float32](GFF-File-Format#gff-data-types)| 24 (0x18)   | 12   | Relative use hook position 2 (x, y, z)                           |
| Absolute Use position 1 | [float32](GFF-File-Format#gff-data-types)| 36 (0x24)   | 12   | Absolute use hook position 1 (x, y, z)                           |
| Absolute Use position 2 | [float32](GFF-File-Format#gff-data-types)| 48 (0x30)   | 12   | Absolute use hook position 2 (x, y, z)                           |
| position                | [float32](GFF-File-Format#gff-data-types)| 60 (0x3C)   | 12   | walkmesh position offset (x, y, z)                               |

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:30-38`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L30-L38), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:60-67`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L60-L67), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:455-457`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L455-L457)

**walkmesh types:**

KotOR uses different walkmesh types for different purposes, each optimized for its specific use case:

- **WOK (type 1)**: Area walkmesh - defines walkable regions in game areas
  - Stored as `<area_name>.wok` files (e.g., `m12aa.wok` for Dantooine area)
  - Large planar surfaces covering entire rooms or outdoor areas for player movement and NPC pathfinding
  - Often split across multiple rooms in complex areas, with each room having its own walkmesh
  - Includes complete spatial acceleration ([AABB](BWM-File-Format#aabb-tree) tree), [adjacencies](BWM-File-Format#walkable-adjacencies) for pathfinding, [edges](BWM-File-Format#edges) for transitions, and [perimeters](BWM-File-Format#perimeters) for boundary detection
  - Used by the pathfinding system to compute routes between [walkable faces](BWM-File-Format#faces)
  - **Reference**: [`vendor/reone/include/reone/graphics/format/bwmreader.h:40-43`](https://github.com/th3w1zard1/reone/blob/master/include/reone/graphics/format/bwmreader.h#L40-L43), [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:52-64`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L52-L64), [`vendor/KotOR.js/src/enums/odyssey/OdysseyWalkMeshType.ts:11-14`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/enums/odyssey/OdysseyWalkMeshType.ts#L11-L14)
  
- **PWK/DWK (type 0)**: Placeable/Door walkmesh - collision for placeable objects and doors
  - **PWK**: Stored as `<model_name>.pwk` files - collision [geometry](MDL-MDX-File-Format#geometry-header) for containers, furniture, and other interactive placeable objects
    - Prevents the player from walking through solid objects like crates, tables, and containers
    - Typically much simpler than area walkmeshes, containing only the essential collision [geometry](MDL-MDX-File-Format#geometry-header)
  - **DWK**: Stored as `<door_model>.dwk` files, often with multiple states:
    - `<name>0.dwk` - Closed door state
    - `<name>1.dwk` - Partially open state (if applicable)
    - `<name>2.dwk` - Fully open state
    - Door walkmeshes update dynamically as doors open and close, switching between states
    - The engine loads the appropriate DWK file based on the door's current [animation](MDL-MDX-File-Format#animation-header) state
  - Compact collision [geometry](MDL-MDX-File-Format#geometry-header) optimized for small objects rather than large areas
  - Does not include [AABB](BWM-File-Format#aabb-tree) tree or [adjacency](BWM-File-Format#walkable-adjacencies) data (simpler structure, faster loading)
  - Hook vectors (USE1, USE2) define interaction points where the player can activate doors or placeables
  - **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:179-231`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L179-L231)

**Hook vectors** [ARE](GFF-File-Format#are-area) reference points used by the engine for positioning and interaction. These [ARE](GFF-File-Format#are-area) **NOT** related to walkmesh [geometry](MDL-MDX-File-Format#geometry-header) itself ([faces](MDL-MDX-File-Format#face-structure), [edges](BWM-File-Format#edges), [vertices](MDL-MDX-File-Format#vertex-structure)), but rather define interaction points for doors and placeables.

**Important Distinction**: BWM hooks [ARE](GFF-File-Format#are-area) different from [LYT](LYT-File-Format) doorhooks:

- **BWM Hooks**: Interaction points stored in the walkmesh file itself (relative/absolute positions)
- **[LYT](LYT-File-Format) Doorhooks**: Door placement points defined in layout files (see [LYT File Format](LYT-File-Format.md#door-hooks))

- **Relative Hook positions** (Relative Use position 1/2): positions relative to the walkmesh origin, used when the walkmesh itself may be transformed or positioned
  - For doors: Define where the player must stand to interact with the door (relative to door [model](MDL-MDX-File-Format))
  - For placeables: Define interaction points relative to the object's local coordinate system
  - Stored as `relative_hook1` and `relative_hook2` in the BWM class
  - **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:61-64`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L61-L64), [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:309-310`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L309-L310), [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:165-175`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L165-L175)

- **Absolute Hook positions** (Absolute Use position 1/2): positions in world space, used when the walkmesh position is known
  - For doors: Precomputed world-space interaction points (position + relative hook)
  - For placeables: World-space interaction points accounting for object placement
  - Stored as `absolute_hook1` and `absolute_hook2` in the BWM class
  - **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:313-318`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L313-L318), [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:177-187`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L177-L187)

- **position**: The walkmesh's origin offset in world space
  - For area walkmeshes (WOK): Typically `(0, 0, 0)` as areas define their own coordinate system
  - For placeable/door walkmeshes: The position where the object is placed in the area
  - Used to transform [vertices](MDL-MDX-File-Format#vertex-structure) from local to world coordinates
  - **Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:37-38`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L37-L38), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:65`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L65), [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:103`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L103), [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:158-163`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L158-L163)

Hook vectors enable the engine to:

- Spawn creatures at designated locations relative to walkable surfaces
- position triggers and encounters at specific points
- Align objects to the walkable surface (e.g., placing items on tables)
- Define door interaction points (USE1, USE2) where the player can activate doors or placeables
- **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:214-222`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L214-L222)

### data Table offsets

After the walkmesh properties, the header contains offset and count information for all data tables:

| Name                | type   | offset | size | Description                                                      |
| ------------------- | ------ | ------ | ---- | ---------------------------------------------------------------- |
| [vertex](MDL-MDX-File-Format#vertex-structure) count        | [uint32](GFF-File-Format#gff-data-types) | 72 (0x48)   | 4    | Number of [vertices](MDL-MDX-File-Format#vertex-structure)                                               |
| [vertex](MDL-MDX-File-Format#vertex-structure) offset       | [uint32](GFF-File-Format#gff-data-types) | 76 (0x4C)   | 4    | offset to [vertex](MDL-MDX-File-Format#vertex-structure) array                                           |
| [face](MDL-MDX-File-Format#face-structure) count          | [uint32](GFF-File-Format#gff-data-types) | 80 (0x50)   | 4    | Number of [faces](MDL-MDX-File-Format#face-structure)                                                  |
| [face](MDL-MDX-File-Format#face-structure) indices offset | [uint32](GFF-File-Format#gff-data-types) | 84 (0x54)   | 4    | offset to [face](MDL-MDX-File-Format#face-structure) indices array                                     |
| [materials](MDL-MDX-File-Format#trimesh-header) offset    | [uint32](GFF-File-Format#gff-data-types) | 88 (0x58)   | 4    | offset to [materials](MDL-MDX-File-Format#trimesh-header) array                                       |
| Normals offset      | [uint32](GFF-File-Format#gff-data-types) | 92 (0x5C)   | 4    | offset to [face](MDL-MDX-File-Format#face-structure) normals array                                     |
| Distances offset    | [uint32](GFF-File-Format#gff-data-types) | 96 (0x60)   | 4    | offset to planar distances array                                 |
| [AABB](BWM-File-Format#aabb-tree) count          | [uint32](GFF-File-Format#gff-data-types) | 100 (0x64)   | 4    | Number of [AABB](BWM-File-Format#aabb-tree) nodes (WOK only, 0 for PWK/DWK)                  |
| [AABB](BWM-File-Format#aabb-tree) offset         | [uint32](GFF-File-Format#gff-data-types) | 104 (0x68)   | 4    | offset to [AABB](BWM-File-Format#aabb-tree) [nodes](MDL-MDX-File-Format#node-structures) array (WOK only)                            |
| Unknown             | [uint32](GFF-File-Format#gff-data-types) | 108 (0x6C)   | 4    | Unknown field (typically 0 or 4)                                 |
| [adjacency](BWM-File-Format#walkable-adjacencies) count     | [uint32](GFF-File-Format#gff-data-types) | 112 (0x70)   | 4    | Number of [walkable faces](BWM-File-Format#faces) for adjacency (WOK only)                |
| [adjacency](BWM-File-Format#walkable-adjacencies) offset    | [uint32](GFF-File-Format#gff-data-types) | 116 (0x74)   | 4    | offset to [adjacency](BWM-File-Format#walkable-adjacencies) array (WOK only)                            |
| [edge](BWM-File-Format#edges) count          | [uint32](GFF-File-Format#gff-data-types) | 120 (0x78)   | 4    | Number of [perimeter](BWM-File-Format#perimeters) edges (WOK only)                            |
| [edge](BWM-File-Format#edges) offset         | [uint32](GFF-File-Format#gff-data-types) | 124 (0x7C)   | 4    | offset to [edge](BWM-File-Format#edges) array (WOK only)                                  |
| [perimeter](BWM-File-Format#perimeters) count     | [uint32](GFF-File-Format#gff-data-types) | 128 (0x80)   | 4    | Number of [perimeter](BWM-File-Format#perimeters) markers (WOK only)                           |
| [perimeter](BWM-File-Format#perimeters) offset    | [uint32](GFF-File-Format#gff-data-types) | 132 (0x84)   | 4    | offset to [perimeter](BWM-File-Format#perimeters) array (WOK only)                            |

**Total header size**: 136 bytes (0x88)

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:40-64`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L40-L64), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:66-81`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L66-L81), [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:79-94`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L79-L94), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:458-473`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L458-L473)

### [vertices](MDL-MDX-File-Format#vertex-structure)

| Name     | type      | size | Description                                                      |
| -------- | --------- | ---- | ---------------------------------------------------------------- |
| [vertices](MDL-MDX-File-Format#vertex-structure) | [float32](GFF-File-Format#gff-data-types)| 12×N | array of [vertex](MDL-MDX-File-Format#vertex-structure) positions (X, Y, Z triplets)                    |

[vertices](MDL-MDX-File-Format#vertex-structure) [ARE](GFF-File-Format#are-area) stored as absolute world coordinates in 32-bit IEEE floating-point format. Each [vertex](MDL-MDX-File-Format#vertex-structure) is 12 bytes (three [float32](GFF-File-Format#gff-data-types) values), and [vertices](MDL-MDX-File-Format#vertex-structure) [ARE](GFF-File-Format#are-area) typically shared between multiple [faces](MDL-MDX-File-Format#face-structure) to reduce memory usage and ensure geometric consistency.

**[vertex](MDL-MDX-File-Format#vertex-structure) coordinate Systems:**

The coordinate system used for [vertices](MDL-MDX-File-Format#vertex-structure) depends on the walkmesh type and how implementations choose to process them:

- **For area walkmeshes (WOK)**: [vertices](MDL-MDX-File-Format#vertex-structure) [ARE](GFF-File-Format#are-area) stored in [world space](https://en.wikipedia.org/wiki/World_coordinates) coordinates. However, some implementations (e.g., [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:84-87`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L84-L87)) subtract the walkmesh position during reading to work in [local coordinates](https://en.wikipedia.org/wiki/Local_coordinates), which simplifies geometric operations. The walkmesh position is then added back when transforming to [world space](https://en.wikipedia.org/wiki/World_coordinates). This approach allows the walkmesh to be positioned anywhere in the world while keeping local calculations simple.
  - **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:84-87`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L84-L87) - Subtracts position during reading
  - **Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:94-103`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L94-L103) - Reads [vertices](MDL-MDX-File-Format#vertex-structure) directly without offset

- **For placeable/door walkmeshes (PWK/DWK)**: [vertices](MDL-MDX-File-Format#vertex-structure) [ARE](GFF-File-Format#are-area) stored relative to the object's local origin. When the object is placed in an area, the engine applies a [transformation matrix](https://en.wikipedia.org/wiki/Transformation_matrix) (including translation, rotation, and scale) to convert these [local coordinates](https://en.wikipedia.org/wiki/Local_coordinates) to [world space](https://en.wikipedia.org/wiki/World_coordinates). This allows the same walkmesh to be reused for multiple instances of the same object at different positions and orientations.
  - **Reference**: [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:182-206`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L182-L206) - Applies [transformation](BWM-File-Format#walkable-adjacencies) [matrix](BWM-File-Format#walkable-adjacencies) to [vertices](MDL-MDX-File-Format#vertex-structure)

**Vendor Discrepancy ([vertex](MDL-MDX-File-Format#vertex-structure) position Handling):**

| Implementation | Behavior | Reference |
|---------------|----------|-----------|
| kotorblender | Subtracts position from [vertices](MDL-MDX-File-Format#vertex-structure) during read, adds back during write | `reader.py:86` |
| reone | Reads [vertices](MDL-MDX-File-Format#vertex-structure) directly without position offset | `bwmreader.cpp:98-102` |
| xoreos | Applies full [transformation](BWM-File-Format#walkable-adjacencies) [matrix](BWM-File-Format#walkable-adjacencies) to [vertices](MDL-MDX-File-Format#vertex-structure) | `walkmeshloader.cpp:182-206` |
| KotOR.js | Reads [vertices](MDL-MDX-File-Format#vertex-structure) directly, applies [matrix](BWM-File-Format#walkable-adjacencies) transform later via `updateMatrix()` | `OdysseyWalkMesh.ts:243-258` |
| PyKotor | Reads [vertices](MDL-MDX-File-Format#vertex-structure) directly without position offset | `io_bwm.py:143` |

**Consensus**: Most implementations read [vertices](MDL-MDX-File-Format#vertex-structure) as stored and apply [transformations](BWM-File-Format#walkable-adjacencies) at runtime. kotorblender's approach of subtracting position during read is a Blender-specific optimization.

**[vertex](MDL-MDX-File-Format#vertex-structure) Sharing and Indexing:**

[vertices](MDL-MDX-File-Format#vertex-structure) [ARE](GFF-File-Format#are-area) shared by reference through the index system: multiple [faces](MDL-MDX-File-Format#face-structure) can reference the same [vertex](MDL-MDX-File-Format#vertex-structure) index, ensuring that adjacent [faces](MDL-MDX-File-Format#face-structure) share exact [vertex](MDL-MDX-File-Format#vertex-structure) positions. This is critical for [adjacency](BWM-File-Format#walkable-adjacencies) calculations, as two [faces](MDL-MDX-File-Format#face-structure) [ARE](GFF-File-Format#are-area) considered adjacent only if they share exactly two vertices (forming a shared [edge](BWM-File-Format#edges)). The [vertex](MDL-MDX-File-Format#vertex-structure) array is typically deduplicated during walkmesh generation, with similar vertices (within a small tolerance) merged to reduce memory usage and ensure geometric consistency.

- **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:155-166`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L155-L166) - [vertex](MDL-MDX-File-Format#vertex-structure) deduplication using SimilarVertex class
- **Reference**: [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:264-269`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L264-L269) - [vertex](MDL-MDX-File-Format#vertex-structure) array reading

### [faces](MDL-MDX-File-Format#face-structure)

| Name  | type     | size | Description                                                      |
| ----- | -------- | ---- | ---------------------------------------------------------------- |
| [faces](MDL-MDX-File-Format#face-structure) | [uint32](GFF-File-Format#gff-data-types)| 12×N | array of [face](MDL-MDX-File-Format#face-structure) [vertex](MDL-MDX-File-Format#vertex-structure) indices (triplets referencing [vertex](MDL-MDX-File-Format#vertex-structure) array) |

Each [face](MDL-MDX-File-Format#face-structure) is a triangle defined by three [vertex](MDL-MDX-File-Format#vertex-structure) indices (0-based) into the [vertex](MDL-MDX-File-Format#vertex-structure) array. Each [face](MDL-MDX-File-Format#face-structure) entry is 12 bytes (three [uint32](GFF-File-Format#gff-data-types) values). The [vertex](MDL-MDX-File-Format#vertex-structure) indices define the triangle's [vertices](MDL-MDX-File-Format#vertex-structure) in counter-clockwise order when viewed from the front (the side the normal points toward).

**[face](MDL-MDX-File-Format#face-structure) Ordering:**
[faces](MDL-MDX-File-Format#face-structure) [ARE](GFF-File-Format#are-area) typically ordered with walkable faces first, followed by non-walkable faces. This ordering is important because:

- [adjacency](BWM-File-Format#walkable-adjacencies) data is stored only for [walkable faces](BWM-File-Format#faces), and the [adjacency](BWM-File-Format#walkable-adjacencies) array index corresponds to the [walkable face](BWM-File-Format#faces)'s position in the [walkable face](BWM-File-Format#faces) list (not the overall [face](MDL-MDX-File-Format#face-structure) list)
- The engine can quickly iterate through [walkable faces](BWM-File-Format#faces) for pathfinding without checking [material](MDL-MDX-File-Format#trimesh-header) types
- Non-[walkable faces](BWM-File-Format#faces) [ARE](GFF-File-Format#are-area) still needed for collision detection (preventing characters from walking through walls)

**Vendor Implementation Analysis:**

| Implementation | [face](MDL-MDX-File-Format#face-structure) Ordering | [adjacency](BWM-File-Format#walkable-adjacencies) Mapping | Reference |
|---------------|--------------|-------------------|-----------|
| **kotorblender** (writer) | Explicitly orders walkable first, then non-walkable | [adjacency](BWM-File-Format#walkable-adjacencies) index `i` maps to [face](MDL-MDX-File-Format#face-structure) index `i` in reordered list | [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:175-194`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L175-L194), [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:241-273`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L241-L273) |
| **PyKotor** (writer) | Explicitly orders walkable first, then non-walkable | [adjacency](BWM-File-Format#walkable-adjacencies) index maps to position in reordered `faces` array | [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py:213-215`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py#L213-L215), [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py:266-276`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py#L266-L276) |
| **KotOR.js** | Sorts walkable first in `rebuild()` method | [adjacency](BWM-File-Format#walkable-adjacencies) [matrix](BWM-File-Format#walkable-adjacencies) count equals [walkable faces](BWM-File-Format#faces) | [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:692`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L692), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:305-337`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L305-L337) |
| **xoreos** | Reads as stored; maintains separate `_walkableFaces` array | Maps via `_walkableFaces[a]` to actual [face](MDL-MDX-File-Format#face-structure) index (works with any ordering) | [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:119-135`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L119-L135), [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:155-169`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L155-L169) |
| **reone** | Reads as stored | Does not load [adjacency](BWM-File-Format#walkable-adjacencies) data | [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:74-87`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L74-L87) |

**Consensus**: [adjacency](BWM-File-Format#walkable-adjacencies) array contains `num_walkable_faces` entries (not `num_faces`). When [faces](MDL-MDX-File-Format#face-structure) [ARE](GFF-File-Format#are-area) ordered walkable-first, [adjacency](BWM-File-Format#walkable-adjacencies) index `i` maps directly to [face](MDL-MDX-File-Format#face-structure) index `i` in the overall array. xoreos demonstrates an alternative mapping approach that works regardless of file ordering.

**[face](MDL-MDX-File-Format#face-structure) Winding:**
The [vertex](MDL-MDX-File-Format#vertex-structure) order determines the [face](MDL-MDX-File-Format#face-structure)'s normal direction (via the right-hand rule). The engine uses this to determine which side of the [face](MDL-MDX-File-Format#face-structure) is "up" (walkable) versus "down" (non-walkable). [faces](MDL-MDX-File-Format#face-structure) should be oriented such that their normals point upward for walkable surfaces.

**Vendor Implementation Analysis:**

| Implementation | Normal Calculation | [vertex](MDL-MDX-File-Format#vertex-structure) Winding | Reference |
|---------------|-------------------|----------------|-----------|
| **KotOR.js** | `normal = (v3 - v2) × (v1 - v2)` (dynamic) | Counter-clockwise when viewed from front | [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:700-710`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L700-L710) |
| **kotorblender** | Reads precomputed normals from file | Assumes counter-clockwise | [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:98-105`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L98-L105) |
| **reone** | Reads precomputed normals from file | Reads as stored | [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:125-134`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L125-L134) |
| **xoreos** | Reads precomputed normals from file | Reads as stored | Not explicitly shown in walkmeshloader.cpp |
| **PyKotor** | Uses `Face.normal()` from [geometry](MDL-MDX-File-Format#geometry-header) module | Counter-clockwise expected | [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py) |

**Consensus**: Normals follow right-hand rule: counter-clockwise [vertex](MDL-MDX-File-Format#vertex-structure) order (v1 → v2 → v3) when viewed from front yields upward-pointing normal for walkable surfaces. Cross product formulas `(v2 - v1) × (v3 - v1)` and `(v3 - v2) × (v1 - v2)` [ARE](GFF-File-Format#are-area) mathematically equivalent. Most implementations read precomputed normals from file to avoid runtime overhead.

### [materials](MDL-MDX-File-Format#trimesh-header)

| Name      | type   | size | Description                                                      |
| --------- | ------ | ---- | ---------------------------------------------------------------- |
| [materials](MDL-MDX-File-Format#trimesh-header) | [uint32](GFF-File-Format#gff-data-types)  | 4×N  | Surface [material](MDL-MDX-File-Format#trimesh-header) index per face (determines walkability)         |

**Surface [materials](MDL-MDX-File-Format#trimesh-header):**

Each [face](MDL-MDX-File-Format#face-structure) is assigned a [material](MDL-MDX-File-Format#trimesh-header) type that determines its physical properties and interaction behavior. The [material](MDL-MDX-File-Format#trimesh-header) ID is stored as a `uint32` per [face](MDL-MDX-File-Format#face-structure).

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
| 8  | Transparent       | No       | Transparent non-walkable surfaces                                 | All |
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

### Derived data

| Name           | type    | size | Description                                                      |
| -------------- | ------- | ---- | ---------------------------------------------------------------- |
| [face](MDL-MDX-File-Format#face-structure) Normals   | [float32](GFF-File-Format#gff-data-types) | 12×N | Normal vectors for each face (normalized)                        |
| Planar Distances | [float32](GFF-File-Format#gff-data-types) | 4×N | D component of plane equation (ax + by + cz + d = 0) for each [face](MDL-MDX-File-Format#face-structure) |

[face](MDL-MDX-File-Format#face-structure) normals [ARE](GFF-File-Format#are-area) precomputed unit vectors perpendicular to each [face](MDL-MDX-File-Format#face-structure). They [ARE](GFF-File-Format#are-area) calculated using the cross product of two [edge](BWM-File-Format#edges) vectors: `normal = normalize((v2 - v1) × (v3 - v1))`. The normal direction follows the right-hand rule based on [vertex](MDL-MDX-File-Format#vertex-structure) winding order, with normals typically pointing upward for walkable surfaces.

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

Planar distances [ARE](GFF-File-Format#are-area) the D component of the plane equation `ax + by + cz + d = 0`, where (a, b, c) is the [face](MDL-MDX-File-Format#face-structure) normal. The D component is calculated as `d = -normal · vertex1` for each [face](MDL-MDX-File-Format#face-structure), where vertex1 is typically the first [vertex](MDL-MDX-File-Format#vertex-structure) of the triangle. This precomputed value allows the engine to quickly test point-plane relationships without recalculating the plane equation each time.

These derived values [ARE](GFF-File-Format#are-area) stored in the file to avoid recomputation during runtime, which is especially important for large walkmeshes where thousands of [faces](MDL-MDX-File-Format#face-structure) need to be tested for intersection or containment queries.

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:125-134`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L125-L134), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:98-105`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L98-L105), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:700-710`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L700-L710)

### AABB Tree

| Name          | type    | size | Description                                                      |
| ------------- | ------- | ---- | ---------------------------------------------------------------- |
| AABB [nodes](MDL-MDX-File-Format#node-structures)    | varies  | varies | [bounding box](MDL-MDX-File-Format#model-header) tree [nodes](MDL-MDX-File-Format#node-structures) for spatial acceleration (WOK only)      |

Each AABB [node](MDL-MDX-File-Format#node-structures) is **44 bytes** and contains:

| Name                  | type    | offset | size | Description                                                      |
| --------------------- | ------- | ------ | ---- | ---------------------------------------------------------------- |
| Bounds Min            | [float32](GFF-File-Format#gff-data-types) | 0 (0x00) | 12  | Minimum [bounding box](MDL-MDX-File-Format#model-header) coordinates (x, y, z)                      |
| Bounds Max            | [float32](GFF-File-Format#gff-data-types) | 12 (0x0C) | 12  | Maximum [bounding box](MDL-MDX-File-Format#model-header) coordinates (x, y, z)                       |
| [face](MDL-MDX-File-Format#face-structure) index            | [int32](GFF-File-Format#gff-data-types)   | 24 (0x18) | 4    | [face](MDL-MDX-File-Format#face-structure) index for leaf [nodes](MDL-MDX-File-Format#node-structures), -1 (0xFFFFFFFF) for internal [nodes](MDL-MDX-File-Format#node-structures)   |
| Unknown               | [uint32](GFF-File-Format#gff-data-types)  | 28 (0x1C) | 4    | Unknown field (typically 4)                                       |
| Most Significant Plane| [uint32](GFF-File-Format#gff-data-types)  | 32 (0x20) | 4    | Split axis/plane identifier (see below)                          |
| Left Child index      | [uint32](GFF-File-Format#gff-data-types)  | 36 (0x24) | 4    | index to left child node (see encoding below)                   |
| Right Child index     | [uint32](GFF-File-Format#gff-data-types)  | 40 (0x28) | 4    | index to right child node (see encoding below)                 |

**Most Significant Plane values:**

| value | Meaning |
|-------|---------|
| 0x00 | No children (leaf [node](MDL-MDX-File-Format#node-structures)) |
| 0x01 | Positive X axis split |
| 0x02 | Positive Y axis split |
| 0x03 | Positive Z axis split |
| 0xFFFFFFFE (-2) | Negative X axis split |
| 0xFFFFFFFD (-3) | Negative Y axis split |
| 0xFFFFFFFC (-4) | Negative Z axis split |

**Vendor Discrepancy ([AABB](BWM-File-Format#aabb-tree) Child index Encoding):**

| Implementation | Child index Encoding | Reference |
|---------------|---------------------|-----------|
| reone | 0-based index (reads directly into array) | `bwmreader.cpp:164-167` |
| xoreos | Multiplies by 44 ([node](MDL-MDX-File-Format#node-structures) size) to get [byte](GFF-File-Format#gff-data-types) offset | `walkmeshloader.cpp:241-243` |
| KotOR.js | Reads as 0-based index | `OdysseyWalkMesh.ts:443-444` |
| kotorblender (write) | Uses 0-based index during generation | `aabb.py:61-64` |
| PyKotor (write) | Uses 1-based indices in output (0 = no child becomes 0xFFFFFFFF) | `io_bwm.py:259-262` |

**Critical Note**: The xoreos implementation multiplies child indices by 44 (the [node](MDL-MDX-File-Format#node-structures) size) to compute [byte](GFF-File-Format#gff-data-types) offsets, while reone and KotOR.js use 0-based array indices. This suggests **two interpretations [ARE](GFF-File-Format#are-area) possible**:

1. **array index**: Child values [ARE](GFF-File-Format#are-area) 0-based indices into the [AABB](BWM-File-Format#aabb-tree) array
2. **Byte offset divisor**: Child values [ARE](GFF-File-Format#are-area) indices that, when multiplied by 44, give the [byte](GFF-File-Format#gff-data-types) offset from [AABB](BWM-File-Format#aabb-tree) start

Both interpretations yield the same result when reading, but differ in semantics. The **consensus** based on majority usage is that child indices [ARE](GFF-File-Format#are-area) **0-based array indices**, with 0xFFFFFFFF indicating no child.

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:136-171`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L136-L171), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:112-130`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L112-L130), [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:218-248`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L218-L248), [`vendor/kotorblender/io_scene_kotor/aabb.py:40-64`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/aabb.py#L40-L64)

**[AABB](BWM-File-Format#aabb-tree) Tree Purpose:**

The Axis-Aligned Bounding Box ([AABB](BWM-File-Format#aabb-tree)) tree is a spatial acceleration structure that dramatically improves performance for common operations. Without it, the engine would need to test every [face](MDL-MDX-File-Format#face-structure) individually (O(N) complexity), which becomes prohibitively slow for large walkmeshes with thousands of [faces](MDL-MDX-File-Format#face-structure). The tree reduces this to O(log N) average case complexity.

**Key Operations Enabled:**

- **Ray Casting**: Finding where a ray intersects the walkmesh
  - Mouse clicks: Determining which [walkable face](BWM-File-Format#faces) the player clicked on for movement commands
  - Projectiles: Testing if projectiles hit walkable surfaces or obstacles
  - Line of sight: Checking if a line between two points intersects the walkmesh
  - **Reference**: [`vendor/reone/src/libs/graphics/walkmesh.cpp:24-100`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/walkmesh.cpp#L24-L100)

- **Point Queries**: Determining which [face](MDL-MDX-File-Format#face-structure) a character is standing on
  - Character positioning: Finding the [walkable face](BWM-File-Format#faces) beneath a character's position
  - Elevation calculation: Computing the Z coordinate for a character at a given (X, Y) position
  - Collision response: Determining surface normals and [materials](MDL-MDX-File-Format#trimesh-header) for physics calculations
  - **Reference**: [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:497-504`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L497-L504)

**Tree Construction (from kotorblender [AABB](BWM-File-Format#aabb-tree).py):**

[AABB](BWM-File-Format#aabb-tree) trees [ARE](GFF-File-Format#are-area) constructed recursively:

1. Compute bounding box for all [faces](MDL-MDX-File-Format#face-structure)
2. If only one [face](MDL-MDX-File-Format#face-structure) remains, create a leaf [node](MDL-MDX-File-Format#node-structures)
3. Find the longest axis of the [bounding box](MDL-MDX-File-Format#model-header)
4. Split [faces](MDL-MDX-File-Format#face-structure) into left/right groups based on centroid position relative to [bounding box](MDL-MDX-File-Format#model-header) center
5. Recursively build left and right subtrees
6. Handle degenerate cases (all [faces](MDL-MDX-File-Format#face-structure) on one side) by trying alternative axes or splitting evenly

**Reference**: [`vendor/kotorblender/io_scene_kotor/aabb.py:40-126`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/aabb.py#L40-L126)

### Walkable adjacencies

| Name            | type    | size | Description                                                      |
| --------------- | ------- | ---- | ---------------------------------------------------------------- |
| adjacencies     | [int32](GFF-File-Format#gff-data-types)| 12×N | Three adjacency indices per walkable face (-1 = no neighbor)     |

adjacencies [ARE](GFF-File-Format#are-area) stored only for walkable faces ([faces](MDL-MDX-File-Format#face-structure) with walkable [materials](MDL-MDX-File-Format#trimesh-header)). Each [walkable face](BWM-File-Format#faces) has exactly three adjacency entries, one for each edge ([edges](BWM-File-Format#edges) 0, 1, and 2). The adjacency count in the header equals the number of [walkable faces](BWM-File-Format#faces), not the total [face](MDL-MDX-File-Format#face-structure) count.

**adjacency Encoding:**

The adjacency index is a clever encoding that stores both the adjacent [face](MDL-MDX-File-Format#face-structure) index and the specific [edge](BWM-File-Format#edges) within that [face](MDL-MDX-File-Format#face-structure) in a single integer:

- **Encoding Formula**: `adjacency_index = face_index * 3 + edge_index`
  - `face_index`: The index of the adjacent [walkable face](BWM-File-Format#faces) in the overall [face](MDL-MDX-File-Format#face-structure) array
  - `edge_index`: The local [edge](BWM-File-Format#edges) index (0, 1, or 2) within that adjacent [face](MDL-MDX-File-Format#face-structure)
  - This encoding allows the engine to know not just which [face](MDL-MDX-File-Format#face-structure) is adjacent, but which [edge](BWM-File-Format#edges) of that [face](MDL-MDX-File-Format#face-structure) connects to the current [edge](BWM-File-Format#edges)
- **No Neighbor**: `-1` (0xFFFFFFFF signed) indicates no adjacent [walkable face](BWM-File-Format#faces) on that [edge](BWM-File-Format#edges)
  - This occurs when the [edge](BWM-File-Format#edges) is a boundary edge ([perimeter](BWM-File-Format#perimeters) [edge](BWM-File-Format#edges))
  - Boundary [edges](BWM-File-Format#edges) may have corresponding entries in the [edges](BWM-File-Format#edges) array with transition information

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

This formula `(edge + (2 - edge % 3)) / 3` appears to map [adjacency](BWM-File-Format#walkable-adjacencies) indices differently, possibly to recover the adjacent [face](MDL-MDX-File-Format#face-structure)'s index when decoding. The standard formula `edge // 3` is used by other implementations.

**Consensus**: Use `face_index = adjacency_index // 3` and `edge_index = adjacency_index % 3` for decoding.

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:58-59`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L58-L59), [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:155-169`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L155-L169), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:305-337`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L305-L337), [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:241-273`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L241-L273)

### edges

| Name  | type     | size | Description                                                      |
| ----- | -------- | ---- | ---------------------------------------------------------------- |
| edges | varies   | varies | [perimeter](BWM-File-Format#perimeters) edge data (edge_index, transition pairs) (WOK only)  |

The edges array contains [perimeter](BWM-File-Format#perimeters) edges (boundary edges with no walkable neighbor). Each edge entry is **8 bytes**:

| Name        | type   | size | Description                                                      |
| ----------- | ------ | ---- | ---------------------------------------------------------------- |
| edge index  | [uint32](GFF-File-Format#gff-data-types) | 4    | Encoded edge index: `face_index * 3 + local_edge_index`        |
| Transition  | [int32](GFF-File-Format#gff-data-types)  | 4    | Transition ID for room/area connections, -1 if no transition     |

**[edge](BWM-File-Format#edges) index Encoding:**

The [edge](BWM-File-Format#edges) index uses the same encoding as [adjacency](BWM-File-Format#walkable-adjacencies) indices: `edge_index = face_index * 3 + local_edge_index`. This identifies:

- Which [face](MDL-MDX-File-Format#face-structure) the [edge](BWM-File-Format#edges) belongs to (`face_index = edge_index // 3`)
- Which [edge](BWM-File-Format#edges) of that face (0, 1, or 2) (`local_edge_index = edge_index % 3`)

**[edge](BWM-File-Format#edges) Definitions:**

| Local [edge](BWM-File-Format#edges) | [vertices](MDL-MDX-File-Format#vertex-structure) | Description |
|------------|----------|-------------|
| 0 | v1 → v2 | First edge (between [vertex](MDL-MDX-File-Format#vertex-structure) 1 and [vertex](MDL-MDX-File-Format#vertex-structure) 2) |
| 1 | v2 → v3 | Second edge (between [vertex](MDL-MDX-File-Format#vertex-structure) 2 and [vertex](MDL-MDX-File-Format#vertex-structure) 3) |
| 2 | v3 → v1 | Third edge (between [vertex](MDL-MDX-File-Format#vertex-structure) 3 and [vertex](MDL-MDX-File-Format#vertex-structure) 1) |

**Reference**: [`vendor/KotOR.js/src/odyssey/WalkmeshEdge.ts:67-79`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/WalkmeshEdge.ts#L67-L79)

**perimeter [edges](BWM-File-Format#edges):**

perimeter [edges](BWM-File-Format#edges) [ARE](GFF-File-Format#are-area) [edges](BWM-File-Format#edges) of [walkable faces](BWM-File-Format#faces) that have no adjacent walkable neighbor. These [edges](BWM-File-Format#edges) form the boundaries of walkable regions and [ARE](GFF-File-Format#are-area) critical for:

- **Area Transitions**: [edges](BWM-File-Format#edges) with non-negative transition IDs link to door connections or area boundaries
- **Boundary Detection**: perimeter [edges](BWM-File-Format#edges) define the limits of walkable space
- **Visual Debugging**: perimeter [edges](BWM-File-Format#edges) can be visualized to show walkmesh boundaries in level editors

**Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:138-143`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L138-L143), [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:275-307`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L275-L307), [`vendor/KotOR.js/src/odyssey/WalkmeshEdge.ts:15-110`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/WalkmeshEdge.ts#L15-L110), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:339-345`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L339-L345)

### perimeters

| Name      | type   | size | Description                                                      |
| --------- | ------ | ---- | ---------------------------------------------------------------- |
| perimeters | [uint32](GFF-File-Format#gff-data-types) | 4×N  | indices into [edge](BWM-File-Format#edges) array marking end of perimeter loops (WOK only) |

perimeters mark the end of closed loops of perimeter [edges](BWM-File-Format#edges). Each perimeter value is an index into the [edge](BWM-File-Format#edges) array, indicating where a perimeter loop ends. This allows the engine to traverse complete boundary loops for pathfinding and area transitions.

**Vendor Discrepancy (perimeter index Base):**

| Implementation | index Base | Reference |
|---------------|------------|-----------|
| kotorblender (write) | 1-based (adds 1 when writing) | `writer.py:303` |
| KotOR.js (read) | Reads as-is (doesn't subtract 1) | `OdysseyWalkMesh.ts:349` |
| PyKotor (write) | 1-based (adds 1 when writing) | `io_bwm.py:315` |

**Critical Note**: The [perimeter](BWM-File-Format#perimeters) indices may be either 0-based or 1-based depending on interpretation. kotorblender and PyKotor write 1-based indices, while KotOR.js reads them without adjustment. This suggests:

- **Stored format**: [perimeter](BWM-File-Format#perimeters) values [ARE](GFF-File-Format#are-area) 1-based indices marking the end of each loop
- **Loop 1**: [edges](BWM-File-Format#edges) from index 0 to `perimeters[0] - 1` (when 1-based)
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

The runtime [model](MDL-MDX-File-Format) provides high-level, in-memory representations of walkmesh data that [ARE](GFF-File-Format#are-area) easier to work with than raw binary structures. These classes abstract away the binary format details and provide convenient methods for common operations.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:25-496`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L25-L496)

### BWM Class

The `BWM` class represents a complete walkmesh in memory, providing a high-level interface for working with walkmesh data.

**Key Attributes:**

- **`faces`**: Ordered list of `BWMFace` objects representing all triangular [faces](MDL-MDX-File-Format#face-structure) in the walkmesh
  - [faces](MDL-MDX-File-Format#face-structure) [ARE](GFF-File-Format#are-area) typically ordered with [walkable faces](BWM-File-Format#faces) first, followed by non-[walkable faces](BWM-File-Format#faces)
  - The [face](MDL-MDX-File-Format#face-structure) list is the primary data structure for accessing walkmesh [geometry](MDL-MDX-File-Format#geometry-header)
- **`walkmesh_type`**: type of walkmesh (`BWMType.AreaModel` for WOK, `BWMType.PlaceableOrDoor` for PWK/DWK)
- **`position`**: 3D position offset for the walkmesh in world space
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

Each `BWMFace` represents a single triangular [face](MDL-MDX-File-Format#face-structure) in the walkmesh, containing all information needed for collision detection, pathfinding, and rendering.

**Key Attributes:**

- **`v1`, `v2`, `v3`**: [vertex](MDL-MDX-File-Format#vertex-structure) objects (`Vector3` instances) defining the triangle's three corners
  - [vertices](MDL-MDX-File-Format#vertex-structure) [ARE](GFF-File-Format#are-area) shared by reference: multiple [faces](MDL-MDX-File-Format#face-structure) can reference the same [vertex](MDL-MDX-File-Format#vertex-structure) object
  - This ensures geometric consistency and enables efficient [adjacency](BWM-File-Format#walkable-adjacencies) calculations
- **`material`**: `SurfaceMaterial` enum determining walkability and physical properties
  - Controls whether the [face](MDL-MDX-File-Format#face-structure) is walkable, blocks line of sight, produces sound effects, etc.
- **`trans1`, `trans2`, `trans3`**: Optional per-[edge](BWM-File-Format#edges) transition indices
  - These [ARE](GFF-File-Format#are-area) **NOT** unique identifiers and do **NOT** encode geometric [adjacency](BWM-File-Format#walkable-adjacencies)
  - They reference area/room transition data (e.g., door connections, area boundaries)
  - Only present on [edges](BWM-File-Format#edges) that have corresponding entries in the [edges](BWM-File-Format#edges) array

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:934-1040`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L934-L1040), [`vendor/KotOR.js/src/three/odyssey/OdysseyFace3.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/three/odyssey/OdysseyFace3.ts)

### BWMEdge Class

The `BWMEdge` class represents a boundary edge (an [edge](BWM-File-Format#edges) with no walkable neighbor) computed from [adjacency](BWM-File-Format#walkable-adjacencies) data.

**Key Attributes:**

- **`face`**: The `BWMFace` object this [edge](BWM-File-Format#edges) belongs to
- **`index`**: The local [edge](BWM-File-Format#edges) index (0, 1, or 2) within the [face](MDL-MDX-File-Format#face-structure)
  - [edge](BWM-File-Format#edges) 0: between `v1` and `v2`
  - [edge](BWM-File-Format#edges) 1: between `v2` and `v3`
  - [edge](BWM-File-Format#edges) 2: between `v3` and `v1`
- **`transition`**: Optional transition ID linking to area/room transition data
  - `-1` indicates no transition (just a boundary [edge](BWM-File-Format#edges))
  - Non-negative values reference door connections or area boundaries
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
| [vertex](MDL-MDX-File-Format#vertex-structure) position handling | Direct read | Transform [matrix](BWM-File-Format#walkable-adjacencies) | Direct + [matrix](BWM-File-Format#walkable-adjacencies) | Subtracts position | Direct read | Direct read (most common) |
| [AABB](BWM-File-Format#aabb-tree) child indices | 0-based | Multiplied by 44 | 0-based | 0-based | 1-based on write | 0-based array indices |
| [perimeter](BWM-File-Format#perimeters) indices | - | - | As-is | 1-based write | 1-based write | 1-based (marking end of loop) |
| [material](MDL-MDX-File-Format#trimesh-header) 16 (BottomlessPit) | - | - | - | Walkable | Not walkable | Walkable (kotorblender source) |
| [adjacency](BWM-File-Format#walkable-adjacencies) decoding | [edge](BWM-File-Format#edges) // 3 | Special formula | [edge](BWM-File-Format#edges) // 3 | [edge](BWM-File-Format#edges) // 3 | [edge](BWM-File-Format#edges) // 3 | [edge](BWM-File-Format#edges) // 3 |

### Recommendations for PyKotor

Based on vendor analysis:

1. **[material](MDL-MDX-File-Format#trimesh-header) Names**: Update `SurfaceMaterial` enum to use kotorblender's names for IDs 20-22 (Sand, BareBones, StoneBridge)
2. **[material](MDL-MDX-File-Format#trimesh-header) 16 Walkability**: Consider making BottomlessPit walkable to match kotorblender
3. **[perimeter](BWM-File-Format#perimeters) indices**: Current 1-based implementation matches kotorblender
4. **[AABB](BWM-File-Format#aabb-tree) Child indices**: Current implementation should write 0-based indices (or 0xFFFFFFFF for no child)
5. **Vertex Handling**: Current direct-read approach is correct

### Test Coverage Analysis

PyKotor's `test_bwm.py` provides comprehensive coverage including:

- ✅ header validation (magic, version)
- ✅ walkmesh type (WOK vs PWK/DWK)
- ✅ [vertex](MDL-MDX-File-Format#vertex-structure) roundtrip and deduplication
- ✅ [face](MDL-MDX-File-Format#face-structure) ordering (walkable first)
- ✅ [material](MDL-MDX-File-Format#trimesh-header) preservation
- ✅ [adjacency](BWM-File-Format#walkable-adjacencies) calculation
- ✅ [edge](BWM-File-Format#edges)/[perimeter](BWM-File-Format#perimeters) identification
- ✅ [AABB](BWM-File-Format#aabb-tree) tree generation (WOK only)
- ✅ Hook vector preservation
- ✅ Complete roundtrip testing

**Missing Test Coverage:**

- ⚠️ [AABB](BWM-File-Format#aabb-tree) tree raycasting functionality
- ⚠️ Point-in-[face](MDL-MDX-File-Format#face-structure) queries
- ⚠️ Comparison against actual game files
- ⚠️ Multi-room walkmesh loading
- ⚠️ [transformation](BWM-File-Format#walkable-adjacencies) [matrix](BWM-File-Format#walkable-adjacencies) application

---

## Implementation Details

This section covers important implementation considerations and best practices when working with BWM files.

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py:42-182`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py#L42-L182)

The binary reader follows a standard pattern that efficiently loads walkmesh data using the offset-based structure:

1. **Validate header**: Check magic "BWM " and version "V1.0" to ensure file format compatibility
2. **Read walkmesh properties**: Load type, hook vectors, and position
3. **Read data table offsets**: Load all offset and count values from the header
4. **Seek and read data tables**: For each data table, seek to the specified offset and read the appropriate number of elements
5. **Process WOK-specific data** (if type is WOK): Load [AABB](BWM-File-Format#aabb-tree) tree [nodes](MDL-MDX-File-Format#node-structures), [adjacency](BWM-File-Format#walkable-adjacencies) data, [edges](BWM-File-Format#edges), and [perimeters](BWM-File-Format#perimeters)
6. **Process [edges](BWM-File-Format#edges) and transitions**: Extract transition information from the [edges](BWM-File-Format#edges) array and apply it to the corresponding [faces](MDL-MDX-File-Format#face-structure)
7. **Construct runtime `BWM` object**: Create the high-level walkmesh representation with all loaded data

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py:185-355`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py#L185-L355)

The binary writer must perform several complex operations:

1. **Calculate all data table offsets**: This requires computing the size of each data table before writing
2. **Write header with offsets**: Write the magic, version, walkmesh properties, and all offset/count values
3. **Write data tables in order**: Write [vertices](MDL-MDX-File-Format#vertex-structure), [face](MDL-MDX-File-Format#face-structure) indices, [materials](MDL-MDX-File-Format#trimesh-header), normals, planar distances, [AABB](BWM-File-Format#aabb-tree) [nodes](MDL-MDX-File-Format#node-structures), [adjacencies](BWM-File-Format#walkable-adjacencies), [edges](BWM-File-Format#edges), and [perimeters](BWM-File-Format#perimeters)
4. **Compute [adjacencies](BWM-File-Format#walkable-adjacencies) from [geometry](MDL-MDX-File-Format#geometry-header)**: The runtime [model](MDL-MDX-File-Format) doesn't store [adjacency](BWM-File-Format#walkable-adjacencies) data directly, so it must be computed
5. **Generate [AABB](BWM-File-Format#aabb-tree) tree if writing WOK file**: [AABB](BWM-File-Format#aabb-tree) tree generation is a complex recursive operation
6. **Compute [edges](BWM-File-Format#edges) and [perimeters](BWM-File-Format#perimeters) from [adjacency](BWM-File-Format#walkable-adjacencies) data**: Identify [perimeter](BWM-File-Format#perimeters) [edges](BWM-File-Format#edges) and group them into loops

**Critical Implementation Notes:**

**Identity vs. value Equality:**

- Use identity-based searches (`is` operator) when mapping [faces](MDL-MDX-File-Format#face-structure) back to indices
- value-based equality can collide: two different [face](MDL-MDX-File-Format#face-structure) objects with the same [vertices](MDL-MDX-File-Format#vertex-structure) [ARE](GFF-File-Format#are-area) equal by value but distinct by identity
- When computing [edge](BWM-File-Format#edges) indices (`face_index * 3 + edge_index`), you must use the actual [face](MDL-MDX-File-Format#face-structure) object's index in the array, not search by value
- **Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:564-587`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L564-L587)

**Transitions vs. [adjacency](BWM-File-Format#walkable-adjacencies):**

- `trans1`/`trans2`/`trans3` [ARE](GFF-File-Format#are-area) optional metadata only, **NOT** [adjacency](BWM-File-Format#walkable-adjacencies) definitions
- [adjacency](BWM-File-Format#walkable-adjacencies) is computed purely from geometry (shared [vertices](MDL-MDX-File-Format#vertex-structure) between [walkable faces](BWM-File-Format#faces))
- Transitions reference area/room data structures (doors, area boundaries) and [ARE](GFF-File-Format#are-area) only present on [perimeter](BWM-File-Format#perimeters) [edges](BWM-File-Format#edges)

**[vertex](MDL-MDX-File-Format#vertex-structure) Sharing:**

- [vertices](MDL-MDX-File-Format#vertex-structure) [ARE](GFF-File-Format#are-area) shared by object identity: multiple [faces](MDL-MDX-File-Format#face-structure) reference the same `Vector3` object
- This ensures geometric consistency: adjacent [faces](MDL-MDX-File-Format#face-structure) share exact [vertex](MDL-MDX-File-Format#vertex-structure) positions
- When modifying [vertices](MDL-MDX-File-Format#vertex-structure), changes affect all [faces](MDL-MDX-File-Format#face-structure) that reference that [vertex](MDL-MDX-File-Format#vertex-structure)

**[face](MDL-MDX-File-Format#face-structure) Ordering:**

- [walkable faces](BWM-File-Format#faces) [ARE](GFF-File-Format#are-area) typically ordered before non-[walkable faces](BWM-File-Format#faces) in the [face](MDL-MDX-File-Format#face-structure) array
- This ordering is important because [adjacency](BWM-File-Format#walkable-adjacencies) data indices correspond to [walkable face](BWM-File-Format#faces) positions
- When writing, maintain this ordering to ensure [adjacency](BWM-File-Format#walkable-adjacencies) indices remain valid

---

This documentation aims to provide a comprehensive overview of the KotOR BWM file format, focusing on the detailed file structure and data formats used within the games, with particular attention to vendor implementation discrepancies and consensus recommendations.
