# KotOR BWM File Format Documentation

This document provides a detailed description of the BWM (Binary WalkMesh) file format used in Knights of the Old Republic (KotOR) games. BWM files, stored on disk as WOK files, define walkable surfaces for [pathfinding](https://en.wikipedia.org/wiki/Pathfinding) and [collision detection](https://en.wikipedia.org/wiki/Collision_detection) in game areas.

**Related formats:** BWM files are used in conjunction with [GFF ARE files](GFF-File-Format#are-area) which define area properties and contain references to walkmesh files.

## Table of Contents

- [KotOR BWM File Format Documentation](#kotor-bwm-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
  - [Binary Format](#binary-format)
    - [File Header](#file-header)
    - [Walkmesh Properties](#walkmesh-properties)
    - [Data Table Offsets](#data-table-offsets)
    - [Vertices](#vertices)
    - [Faces](#faces)
    - [Materials](#materials)
    - [Derived Data](#derived-data)
    - [AABB Tree](#aabb-tree)
    - [Walkable Adjacencies](#walkable-adjacencies)
    - [Edges](#edges)
    - [Perimeters](#perimeters)
  - [Runtime Model](#runtime-model)
    - [BWM Class](#bwm-class)
    - [BWMFace Class](#bwmface-class)
    - [BWMEdge Class](#bwmedge-class)
    - [BWMNodeAABB Class](#bwmnodeaabb-class)
  - [Implementation Comparison](#implementation-comparison)
    - [Summary of Key Differences](#summary-of-key-differences)
    - [Recommendations for PyKotor](#recommendations-for-pykotor)
    - [Test Coverage Analysis](#test-coverage-analysis)
  - [Implementation Details](#implementation-details)

---

## File Structure Overview

BWM (Binary WalkMesh) files define walkable surfaces using triangular faces. Each face has material properties that determine whether it's walkable, adjacency information for pathfinding, and optional edge transitions for area connections. The format supports two distinct walkmesh types: area walkmeshes (WOK) for level geometry and placeable/door walkmeshes (PWK/DWK) for interactive objects.

Walkmeshes serve multiple critical functions in KotOR:

- **[Pathfinding](https://en.wikipedia.org/wiki/Pathfinding)**: NPCs and the player use walkmeshes to navigate areas, with adjacency data enabling [pathfinding algorithms](https://en.wikipedia.org/wiki/Pathfinding) to find routes between walkable faces
- **[Collision Detection](https://en.wikipedia.org/wiki/Collision_detection)**: The engine uses walkmeshes to prevent characters from walking through walls, objects, and impassable terrain
- **Spatial Queries**: [AABB trees](https://en.wikipedia.org/wiki/Bounding_volume_hierarchy) enable efficient [ray casting](https://en.wikipedia.org/wiki/Ray_casting) (mouse clicks, projectiles) and [point-in-triangle](https://en.wikipedia.org/wiki/Point_in_polygon) tests (determining which face a character stands on)
- **Area Transitions**: Edge transitions link walkmeshes to door connections and area boundaries, enabling seamless movement between rooms

The binary format uses a header-based structure where offsets point to various data tables, allowing efficient random access to vertices, faces, materials, and acceleration structures. This design enables the engine to load only necessary portions of large walkmeshes or stream data as needed.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/)

**Reference Implementations:**

- [`vendor/reone/src/libs/graphics/format/bwmreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp) - C++ BWM reader with complete parsing logic
- [`vendor/reone/include/reone/graphics/format/bwmreader.h`](https://github.com/th3w1zard1/reone/blob/master/include/reone/graphics/format/bwmreader.h) - BWM reader header with type definitions
- [`vendor/reone/include/reone/graphics/walkmesh.h`](https://github.com/th3w1zard1/reone/blob/master/include/reone/graphics/walkmesh.h) - Runtime walkmesh class definition
- [`vendor/reone/src/libs/graphics/walkmesh.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/walkmesh.cpp) - Runtime raycasting implementation
- [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py) - Python BWM reader for Blender import
- [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py) - Python BWM writer for Blender export with adjacency calculation
- [`vendor/kotorblender/io_scene_kotor/aabb.py`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/aabb.py) - AABB tree generation algorithm
- [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp) - xoreos walkmesh loader with [pathfinding](https://en.wikipedia.org/wiki/Pathfinding) integration
- [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts) - Complete TypeScript walkmesh implementation with [raycasting](https://en.wikipedia.org/wiki/Ray_casting) and spatial queries
- [`vendor/KotOR.js/src/odyssey/WalkmeshEdge.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/WalkmeshEdge.ts) - WalkmeshEdge class for perimeter edge handling
- [`vendor/KotOR.js/src/odyssey/WalkmeshPerimeter.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/WalkmeshPerimeter.ts) - WalkmeshPerimeter class for boundary loop management

---

## Binary Format

### File Header

| Name         | Type    | Offset | Size | Description                                    |
| ------------ | ------- | ------ | ---- | ---------------------------------------------- |
| Magic        | char[4] | 0x00   | 4    | Always `"BWM "` (space-padded)                 |
| Version      | char[4] | 0x04   | 4    | Always `"V1.0"`                                 |

The file header begins with an 8-byte signature that must exactly match `"BWM V1.0"` (the space after "BWM" is significant). This signature serves as both a file type identifier and version marker. The version string "V1.0" indicates this is the first and only version of the BWM format used in KotOR games. Implementations should validate this header before proceeding with file parsing to ensure they're reading a valid BWM file.

**Vendor Consensus:** All implementations (reone, xoreos, KotOR.js, kotorblender, PyKotor) agree on this header format and validation.

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:28`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L28), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:52-59`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L52-L59), [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:73-75`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L73-L75), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:452-454`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L452-L454)

### Walkmesh Properties

The walkmesh properties section immediately follows the header and contains type information, hook vectors, and position data. This section is 52 bytes total (from offset 0x08 to 0x3C), providing essential metadata about the walkmesh's purpose and positioning.

| Name                    | Type      | Offset | Size | Description                                                      |
| ----------------------- | --------- | ------ | ---- | ---------------------------------------------------------------- |
| Type                    | uint32    | 0x08   | 4    | Walkmesh type (0=PWK/DWK, 1=WOK/Area)                            |
| Relative Use Position 1 | float32[3]| 0x0C   | 12   | Relative use hook position 1 (x, y, z)                           |
| Relative Use Position 2 | float32[3]| 0x18   | 12   | Relative use hook position 2 (x, y, z)                           |
| Absolute Use Position 1 | float32[3]| 0x24   | 12   | Absolute use hook position 1 (x, y, z)                           |
| Absolute Use Position 2 | float32[3]| 0x30   | 12   | Absolute use hook position 2 (x, y, z)                           |
| Position                | float32[3]| 0x3C   | 12   | Walkmesh position offset (x, y, z)                               |

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:30-38`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L30-L38), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:60-67`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L60-L67), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:455-457`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L455-L457)

**Walkmesh Types:**

KotOR uses different walkmesh types for different purposes, each optimized for its specific use case:

- **WOK (Type 1)**: Area walkmesh - defines walkable regions in game areas
  - Stored as `<area_name>.wok` files (e.g., `m12aa.wok` for Dantooine area)
  - Large planar surfaces covering entire rooms or outdoor areas for player movement and NPC pathfinding
  - Often split across multiple rooms in complex areas, with each room having its own walkmesh
  - Includes complete spatial acceleration ([AABB tree](https://en.wikipedia.org/wiki/Bounding_volume_hierarchy)), adjacencies for [pathfinding](https://en.wikipedia.org/wiki/Pathfinding), edges for transitions, and perimeters for boundary detection
  - Used by the [pathfinding](https://en.wikipedia.org/wiki/Pathfinding) system to compute routes between walkable faces
  - **Reference**: [`vendor/reone/include/reone/graphics/format/bwmreader.h:40-43`](https://github.com/th3w1zard1/reone/blob/master/include/reone/graphics/format/bwmreader.h#L40-L43), [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:52-64`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L52-L64), [`vendor/KotOR.js/src/enums/odyssey/OdysseyWalkMeshType.ts:11-14`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/enums/odyssey/OdysseyWalkMeshType.ts#L11-L14)
  
- **PWK/DWK (Type 0)**: Placeable/Door walkmesh - collision for placeable objects and doors
  - **PWK**: Stored as `<model_name>.pwk` files - collision geometry for containers, furniture, and other interactive placeable objects
    - Prevents the player from walking through solid objects like crates, tables, and containers
    - Typically much simpler than area walkmeshes, containing only the essential collision geometry
  - **DWK**: Stored as `<door_model>.dwk` files, often with multiple states:
    - `<name>0.dwk` - Closed door state
    - `<name>1.dwk` - Partially open state (if applicable)
    - `<name>2.dwk` - Fully open state
    - Door walkmeshes update dynamically as doors open and close, switching between states
    - The engine loads the appropriate DWK file based on the door's current animation state
  - Compact collision geometry optimized for small objects rather than large areas
  - Does not include AABB tree or adjacency data (simpler structure, faster loading)
  - Hook vectors (USE1, USE2) define interaction points where the player can activate doors or placeables
  - **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:179-231`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L179-L231)

**Hook Vectors** are reference points used by the engine for positioning and interaction. These are **NOT** related to walkmesh geometry itself (faces, edges, vertices), but rather define interaction points for doors and placeables.

**Important Distinction**: BWM hooks are different from LYT doorhooks:

- **BWM Hooks**: Interaction points stored in the walkmesh file itself (relative/absolute positions)
- **LYT Doorhooks**: Door placement points defined in layout files (see [LYT File Format](LYT-File-Format.md#door-hooks))

- **Relative Hook Positions** (Relative Use Position 1/2): Positions relative to the walkmesh origin, used when the walkmesh itself may be transformed or positioned
  - For doors: Define where the player must stand to interact with the door (relative to door model)
  - For placeables: Define interaction points relative to the object's local coordinate system
  - Stored as `relative_hook1` and `relative_hook2` in the BWM class
  - **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:61-64`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L61-L64), [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:309-310`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L309-L310), [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:165-175`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L165-L175)

- **Absolute Hook Positions** (Absolute Use Position 1/2): Positions in world space, used when the walkmesh position is known
  - For doors: Precomputed world-space interaction points (position + relative hook)
  - For placeables: World-space interaction points accounting for object placement
  - Stored as `absolute_hook1` and `absolute_hook2` in the BWM class
  - **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:313-318`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L313-L318), [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:177-187`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L177-L187)

- **Position**: The walkmesh's origin offset in world space
  - For area walkmeshes (WOK): Typically `(0, 0, 0)` as areas define their own coordinate system
  - For placeable/door walkmeshes: The position where the object is placed in the area
  - Used to transform vertices from local to world coordinates
  - **Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:37-38`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L37-L38), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:65`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L65), [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:103`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L103), [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:158-163`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L158-L163)

Hook vectors enable the engine to:

- Spawn creatures at designated locations relative to walkable surfaces
- Position triggers and encounters at specific points
- Align objects to the walkable surface (e.g., placing items on tables)
- Define door interaction points (USE1, USE2) where the player can activate doors or placeables
- **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:214-222`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L214-L222)

### Data Table Offsets

After the walkmesh properties, the header contains offset and count information for all data tables:

| Name                | Type   | Offset | Size | Description                                                      |
| ------------------- | ------ | ------ | ---- | ---------------------------------------------------------------- |
| Vertex Count        | uint32 | 0x48   | 4    | Number of vertices                                               |
| Vertex Offset       | uint32 | 0x4C   | 4    | Offset to vertex array                                           |
| Face Count          | uint32 | 0x50   | 4    | Number of faces                                                  |
| Face Indices Offset | uint32 | 0x54   | 4    | Offset to face indices array                                     |
| Materials Offset    | uint32 | 0x58   | 4    | Offset to materials array                                       |
| Normals Offset      | uint32 | 0x5C   | 4    | Offset to face normals array                                     |
| Distances Offset    | uint32 | 0x60   | 4    | Offset to planar distances array                                 |
| AABB Count          | uint32 | 0x64   | 4    | Number of AABB nodes (WOK only, 0 for PWK/DWK)                  |
| AABB Offset         | uint32 | 0x68   | 4    | Offset to AABB nodes array (WOK only)                            |
| Unknown             | uint32 | 0x6C   | 4    | Unknown field (typically 0 or 4)                                 |
| Adjacency Count     | uint32 | 0x70   | 4    | Number of walkable faces for adjacency (WOK only)                |
| Adjacency Offset    | uint32 | 0x74   | 4    | Offset to adjacency array (WOK only)                            |
| Edge Count          | uint32 | 0x78   | 4    | Number of perimeter edges (WOK only)                            |
| Edge Offset         | uint32 | 0x7C   | 4    | Offset to edge array (WOK only)                                  |
| Perimeter Count     | uint32 | 0x80   | 4    | Number of perimeter markers (WOK only)                           |
| Perimeter Offset    | uint32 | 0x84   | 4    | Offset to perimeter array (WOK only)                            |

**Total Header Size**: 136 bytes (0x88)

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:40-64`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L40-L64), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:66-81`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L66-L81), [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:79-94`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L79-L94), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:458-473`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L458-L473)

### Vertices

| Name     | Type      | Size | Description                                                      |
| -------- | --------- | ---- | ---------------------------------------------------------------- |
| Vertices | float32[3]| 12×N | Array of vertex positions (X, Y, Z triplets)                    |

Vertices are stored as absolute world coordinates in 32-bit [IEEE floating-point](https://en.wikipedia.org/wiki/IEEE_754) format. Each vertex is 12 bytes (three float32 values), and vertices are typically shared between multiple faces to reduce memory usage and ensure geometric consistency.

**Vertex Coordinate Systems:**

The coordinate system used for vertices depends on the walkmesh type and how implementations choose to process them:

- **For area walkmeshes (WOK)**: Vertices are stored in [world space](https://en.wikipedia.org/wiki/World_coordinates) coordinates. However, some implementations (like kotorblender) subtract the walkmesh position during reading to work in [local coordinates](https://en.wikipedia.org/wiki/Local_coordinates), which simplifies geometric operations. The walkmesh position is then added back when transforming to [world space](https://en.wikipedia.org/wiki/World_coordinates). This approach allows the walkmesh to be positioned anywhere in the world while keeping local calculations simple.
  - **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:84-87`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L84-L87) - Subtracts position during reading
  - **Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:94-103`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L94-L103) - Reads vertices directly without offset

- **For placeable/door walkmeshes (PWK/DWK)**: Vertices are stored relative to the object's local origin. When the object is placed in an area, the engine applies a [transformation matrix](https://en.wikipedia.org/wiki/Transformation_matrix) (including translation, rotation, and scale) to convert these [local coordinates](https://en.wikipedia.org/wiki/Local_coordinates) to [world space](https://en.wikipedia.org/wiki/World_coordinates). This allows the same walkmesh to be reused for multiple instances of the same object at different positions and orientations.
  - **Reference**: [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:182-206`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L182-L206) - Applies transformation matrix to vertices

**Vendor Discrepancy (Vertex Position Handling):**

| Implementation | Behavior | Reference |
|---------------|----------|-----------|
| kotorblender | Subtracts position from vertices during read, adds back during write | `reader.py:86` |
| reone | Reads vertices directly without position offset | `bwmreader.cpp:98-102` |
| xoreos | Applies full transformation matrix to vertices | `walkmeshloader.cpp:182-206` |
| KotOR.js | Reads vertices directly, applies matrix transform later via `updateMatrix()` | `OdysseyWalkMesh.ts:243-258` |
| PyKotor | Reads vertices directly without position offset | `io_bwm.py:143` |

**Consensus**: Most implementations read vertices as stored and apply transformations at runtime. kotorblender's approach of subtracting position during read is a Blender-specific optimization.

**Vertex Sharing and Indexing:**

Vertices are shared by reference through the index system: multiple faces can reference the same vertex index, ensuring that adjacent faces share exact vertex positions. This is critical for adjacency calculations, as two faces are considered adjacent only if they share exactly two vertices (forming a shared edge). The vertex array is typically deduplicated during walkmesh generation, with similar vertices (within a small tolerance) merged to reduce memory usage and ensure geometric consistency.

- **Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:155-166`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L155-L166) - Vertex deduplication using SimilarVertex class
- **Reference**: [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:264-269`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L264-L269) - Vertex array reading

### Faces

| Name  | Type     | Size | Description                                                      |
| ----- | -------- | ---- | ---------------------------------------------------------------- |
| Faces | uint32[3]| 12×N | Array of face vertex indices (triplets referencing vertex array) |

Each face is a triangle defined by three vertex indices (0-based) into the vertex array. Each face entry is 12 bytes (three uint32 values). The vertex indices define the triangle's vertices in counter-clockwise order when viewed from the front (the side the [normal](https://en.wikipedia.org/wiki/Normal_(geometry)) points toward).

**Face Ordering:**
Faces are typically ordered with walkable faces first, followed by non-walkable faces. This ordering is important because:

- Adjacency data is stored only for walkable faces, and the adjacency array index corresponds to the walkable face's position in the walkable face list (not the overall face list)
- The engine can quickly iterate through walkable faces for pathfinding without checking material types
- Non-walkable faces are still needed for collision detection (preventing characters from walking through walls)

**Face Winding:**
The vertex order determines the face's normal direction (via the right-hand rule). The engine uses this to determine which side of the face is "up" (walkable) versus "down" (non-walkable). Faces should be oriented such that their normals point upward for walkable surfaces.

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:105-114`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L105-L114), [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:74-87`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L74-L87), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:89-93`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L89-L93), [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:175-194`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L175-L194), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:271-281`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L271-L281)

### Materials

| Name      | Type   | Size | Description                                                      |
| --------- | ------ | ---- | ---------------------------------------------------------------- |
| Materials | uint32  | 4×N  | Surface material index per face (determines walkability)         |

**Surface Materials:**

Each face is assigned a material type that determines its physical properties and interaction behavior. The material ID is stored as a `uint32` per face.

**Complete Material List (from surfacemat.2da and vendor implementations):**

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
| 8  | Transparent       | No       | Transparent non-walkable surface                                 | All |
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

**Note**: Material 16 (BottomlessPit) walkability varies between implementations. kotorblender marks it as walkable (allowing the player to fall), while some game logic may treat it differently.

**Vendor Discrepancy (Material Walkability):**

| Material ID | kotorblender | PyKotor | Notes |
|-------------|--------------|---------|-------|
| 16 (BottomlessPit) | Walkable | Not in walkable set | May be intentionally walkable for fall damage |
| 19 (Snow) | Non-walkable | Non-walkable (NON_WALK_GRASS) | Name differs but behavior matches |
| 20+ | Named (Sand, BareBones, etc.) | Generic (SURFACE_MATERIAL_20, etc.) | kotorblender has more specific names |
| 30 (Trigger) | Not defined | Walkable | PyKotor extension |

**Consensus**: Use kotorblender's material names and walkability flags for IDs 0-22 as they're derived from `surfacemat.2da`.

Materials control not just walkability but also:

- Footstep sound effects during movement
- Visual effects (ripples on water, dust on dirt)
- Damage-over-time mechanics (lava, acid)
- AI pathfinding cost (creatures prefer some surfaces over others)
- Line-of-sight blocking (obscuring materials)

**Reference**: [`vendor/kotorblender/io_scene_kotor/constants.py:27-51`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/constants.py#L27-L51), [`Libraries/PyKotor/src/utility/common/geometry.py:1118-1172`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/utility/common/geometry.py#L1118-L1172)

### Derived Data

| Name           | Type    | Size | Description                                                      |
| -------------- | ------- | ---- | ---------------------------------------------------------------- |
| Face Normals   | float32[3] | 12×N | Normal vectors for each face (normalized)                        |
| Planar Distances | float32 | 4×N | D component of plane equation (ax + by + cz + d = 0) for each face |

Face normals are precomputed unit vectors perpendicular to each face. They are calculated using the cross product of two edge vectors: `normal = normalize((v2 - v1) × (v3 - v1))`. The normal direction follows the right-hand rule based on vertex winding order, with normals typically pointing upward for walkable surfaces.

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

Planar distances are the D component of the plane equation `ax + by + cz + d = 0`, where (a, b, c) is the face normal. The D component is calculated as `d = -normal · vertex1` for each face, where vertex1 is typically the first vertex of the triangle. This precomputed value allows the engine to quickly test point-plane relationships without recalculating the plane equation each time.

These derived values are stored in the file to avoid recomputation during runtime, which is especially important for large walkmeshes where thousands of faces need to be tested for intersection or containment queries.

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:125-134`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L125-L134), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:98-105`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L98-L105), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:700-710`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L700-L710)

### AABB Tree

| Name          | Type    | Size | Description                                                      |
| ------------- | ------- | ---- | ---------------------------------------------------------------- |
| AABB Nodes    | varies  | varies | Bounding box tree nodes for spatial acceleration (WOK only)      |

Each AABB node is **44 bytes** and contains:

| Name                  | Type    | Offset | Size | Description                                                      |
| --------------------- | ------- | ------ | ---- | ---------------------------------------------------------------- |
| Bounds Min            | float32[3] | 0x00 | 12  | Minimum bounding box coordinates (x, y, z)                      |
| Bounds Max            | float32[3] | 0x0C | 12  | Maximum bounding box coordinates (x, y, z)                       |
| Face Index            | int32   | 0x18 | 4    | Face index for leaf nodes, -1 (0xFFFFFFFF) for internal nodes   |
| Unknown               | uint32  | 0x1C | 4    | Unknown field (typically 4)                                       |
| Most Significant Plane| uint32  | 0x20 | 4    | Split axis/plane identifier (see below)                          |
| Left Child Index      | uint32  | 0x24 | 4    | Index to left child node (see encoding below)                   |
| Right Child Index     | uint32  | 0x28 | 4    | Index to right child node (see encoding below)                 |

**Most Significant Plane Values:**

| Value | Meaning |
|-------|---------|
| 0x00 | No children (leaf node) |
| 0x01 | Positive X axis split |
| 0x02 | Positive Y axis split |
| 0x03 | Positive Z axis split |
| 0xFFFFFFFE (-2) | Negative X axis split |
| 0xFFFFFFFD (-3) | Negative Y axis split |
| 0xFFFFFFFC (-4) | Negative Z axis split |

**Vendor Discrepancy (AABB Child Index Encoding):**

| Implementation | Child Index Encoding | Reference |
|---------------|---------------------|-----------|
| reone | 0-based index (reads directly into array) | `bwmreader.cpp:164-167` |
| xoreos | Multiplies by 44 (node size) to get byte offset | `walkmeshloader.cpp:241-243` |
| KotOR.js | Reads as 0-based index | `OdysseyWalkMesh.ts:443-444` |
| kotorblender (write) | Uses 0-based index during generation | `aabb.py:61-64` |
| PyKotor (write) | Uses 1-based indices in output (0 = no child becomes 0xFFFFFFFF) | `io_bwm.py:259-262` |

**Critical Note**: The xoreos implementation multiplies child indices by 44 (the node size) to compute byte offsets, while reone and KotOR.js use 0-based array indices. This suggests **two interpretations are possible**:

1. **Array index**: Child values are 0-based indices into the AABB array
2. **Byte offset divisor**: Child values are indices that, when multiplied by 44, give the byte offset from AABB start

Both interpretations yield the same result when reading, but differ in semantics. The **consensus** based on majority usage is that child indices are **0-based array indices**, with 0xFFFFFFFF indicating no child.

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:136-171`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L136-L171), [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:112-130`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L112-L130), [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:218-248`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L218-L248), [`vendor/kotorblender/io_scene_kotor/aabb.py:40-64`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/aabb.py#L40-L64)

**AABB Tree Purpose:**

The Axis-Aligned Bounding Box (AABB) tree is a spatial acceleration structure that dramatically improves performance for common operations. Without it, the engine would need to test every face individually (O(N) complexity), which becomes prohibitively slow for large walkmeshes with thousands of faces. The tree reduces this to O(log N) average case complexity.

**Key Operations Enabled:**

- **Ray Casting**: Finding where a ray intersects the walkmesh
  - Mouse clicks: Determining which walkable face the player clicked on for movement commands
  - Projectiles: Testing if projectiles hit walkable surfaces or obstacles
  - Line of sight: Checking if a line between two points intersects the walkmesh
  - **Reference**: [`vendor/reone/src/libs/graphics/walkmesh.cpp:24-100`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/walkmesh.cpp#L24-L100)

- **Point Queries**: Determining which face a character is standing on
  - Character positioning: Finding the walkable face beneath a character's position
  - Elevation calculation: Computing the Z coordinate for a character at a given (X, Y) position
  - Collision response: Determining surface normals and materials for physics calculations
  - **Reference**: [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:497-504`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L497-L504)

**Tree Construction (from kotorblender aabb.py):**

AABB trees are constructed recursively:

1. Compute bounding box for all faces
2. If only one face remains, create a leaf node
3. Find the longest axis of the bounding box
4. Split faces into left/right groups based on centroid position relative to bounding box center
5. Recursively build left and right subtrees
6. Handle degenerate cases (all faces on one side) by trying alternative axes or splitting evenly

**Reference**: [`vendor/kotorblender/io_scene_kotor/aabb.py:40-126`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/aabb.py#L40-L126)

### Walkable Adjacencies

| Name            | Type    | Size | Description                                                      |
| --------------- | ------- | ---- | ---------------------------------------------------------------- |
| Adjacencies     | int32[3]| 12×N | Three adjacency indices per walkable face (-1 = no neighbor)     |

Adjacencies are stored only for walkable faces (faces with walkable materials). Each walkable face has exactly three adjacency entries, one for each edge (edges 0, 1, and 2). The adjacency count in the header equals the number of walkable faces, not the total face count.

**Adjacency Encoding:**

The adjacency index is a clever encoding that stores both the adjacent face index and the specific edge within that face in a single integer:

- **Encoding Formula**: `adjacency_index = face_index * 3 + edge_index`
  - `face_index`: The index of the adjacent walkable face in the overall face array
  - `edge_index`: The local edge index (0, 1, or 2) within that adjacent face
  - This encoding allows the engine to know not just which face is adjacent, but which edge of that face connects to the current edge
- **No Neighbor**: `-1` (0xFFFFFFFF signed) indicates no adjacent walkable face on that edge
  - This occurs when the edge is a boundary edge (perimeter edge)
  - Boundary edges may have corresponding entries in the edges array with transition information

**Decoding:**

```
face_index = adjacency_index // 3
edge_index = adjacency_index % 3
```

**Adjacency Calculation (from kotorblender):**

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
        for i in range(3):
            if self.adjacent_edges[face_idx][i] != -1:
                continue
            for j in range(3):
                if edges[i] == other_edges[j]:
                    self.adjacent_edges[face_idx][i] = 3 * other_face_idx + j
                    self.adjacent_edges[other_face_idx][j] = 3 * face_idx + i
                    break
```

**Vendor Discrepancy (Adjacency Decoding in xoreos):**

xoreos has a unique adjacency decoding that differs from other implementations:

```cpp
// xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:164-168
const uint32_t edge = stream.readSint32LE();
if (edge < UINT32_MAX)
    adjFaces[_walkableFaces[a] * 3 + i] = (edge + (2 - edge % 3)) / 3 + prevFaceCount;
```

This formula `(edge + (2 - edge % 3)) / 3` appears to map adjacency indices differently, possibly to recover the adjacent face's index when decoding. The standard formula `edge // 3` is used by other implementations.

**Consensus**: Use `face_index = adjacency_index // 3` and `edge_index = adjacency_index % 3` for decoding.

**Reference**: [`vendor/reone/src/libs/graphics/format/bwmreader.cpp:58-59`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/bwmreader.cpp#L58-L59), [`vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:155-169`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/path/walkmeshloader.cpp#L155-L169), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:305-337`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L305-L337), [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:241-273`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L241-L273)

### Edges

| Name  | Type     | Size | Description                                                      |
| ----- | -------- | ---- | ---------------------------------------------------------------- |
| Edges | varies   | varies | Perimeter edge data (edge_index, transition pairs) (WOK only)  |

The edges array contains perimeter edges (boundary edges with no walkable neighbor). Each edge entry is **8 bytes**:

| Name        | Type   | Size | Description                                                      |
| ----------- | ------ | ---- | ---------------------------------------------------------------- |
| Edge Index  | uint32 | 4    | Encoded edge index: `face_index * 3 + local_edge_index`        |
| Transition  | int32  | 4    | Transition ID for room/area connections, -1 if no transition     |

**Edge Index Encoding:**

The edge index uses the same encoding as adjacency indices: `edge_index = face_index * 3 + local_edge_index`. This identifies:

- Which face the edge belongs to (`face_index = edge_index // 3`)
- Which edge of that face (0, 1, or 2) (`local_edge_index = edge_index % 3`)

**Edge Definitions:**

| Local Edge | Vertices | Description |
|------------|----------|-------------|
| 0 | v1 → v2 | First edge (between vertex 1 and vertex 2) |
| 1 | v2 → v3 | Second edge (between vertex 2 and vertex 3) |
| 2 | v3 → v1 | Third edge (between vertex 3 and vertex 1) |

**Reference**: [`vendor/KotOR.js/src/odyssey/WalkmeshEdge.ts:67-79`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/WalkmeshEdge.ts#L67-L79)

**Perimeter Edges:**

Perimeter edges are edges of walkable faces that have no adjacent walkable neighbor. These edges form the boundaries of walkable regions and are critical for:

- **Area Transitions**: Edges with non-negative transition IDs link to door connections or area boundaries
- **Boundary Detection**: Perimeter edges define the limits of walkable space
- **Visual Debugging**: Perimeter edges can be visualized to show walkmesh boundaries in level editors

**Reference**: [`vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:138-143`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/reader.py#L138-L143), [`vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:275-307`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/bwm/writer.py#L275-L307), [`vendor/KotOR.js/src/odyssey/WalkmeshEdge.ts:15-110`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/WalkmeshEdge.ts#L15-L110), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:339-345`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L339-L345)

### Perimeters

| Name      | Type   | Size | Description                                                      |
| --------- | ------ | ---- | ---------------------------------------------------------------- |
| Perimeters | uint32 | 4×N  | Indices into edge array marking end of perimeter loops (WOK only) |

Perimeters mark the end of closed loops of perimeter edges. Each perimeter value is an index into the edge array, indicating where a perimeter loop ends. This allows the engine to traverse complete boundary loops for pathfinding and area transitions.

**Vendor Discrepancy (Perimeter Index Base):**

| Implementation | Index Base | Reference |
|---------------|------------|-----------|
| kotorblender (write) | 1-based (adds 1 when writing) | `writer.py:303` |
| KotOR.js (read) | Reads as-is (doesn't subtract 1) | `OdysseyWalkMesh.ts:349` |
| PyKotor (write) | 1-based (adds 1 when writing) | `io_bwm.py:315` |

**Critical Note**: The perimeter indices may be either 0-based or 1-based depending on interpretation. kotorblender and PyKotor write 1-based indices, while KotOR.js reads them without adjustment. This suggests:

- **Stored format**: Perimeter values are 1-based indices marking the end of each loop
- **Loop 1**: Edges from index 0 to `perimeters[0] - 1` (when 1-based)
- **Loop N**: Edges from `perimeters[N-2]` to `perimeters[N-1] - 1`

**Perimeter Loop Construction (from KotOR.js):**

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

## Runtime Model

The runtime model provides high-level, in-memory representations of walkmesh data that are easier to work with than raw binary structures. These classes abstract away the binary format details and provide convenient methods for common operations.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:25-496`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L25-L496)

### BWM Class

The `BWM` class represents a complete walkmesh in memory, providing a high-level interface for working with walkmesh data.

**Key Attributes:**

- **`faces`**: Ordered list of `BWMFace` objects representing all triangular faces in the walkmesh
  - Faces are typically ordered with walkable faces first, followed by non-walkable faces
  - The face list is the primary data structure for accessing walkmesh geometry
- **`walkmesh_type`**: Type of walkmesh (`BWMType.AreaModel` for WOK, `BWMType.PlaceableOrDoor` for PWK/DWK)
- **`position`**: 3D position offset for the walkmesh in world space
- **Positional hooks**: `relative_hook1`, `relative_hook2`, `absolute_hook1`, `absolute_hook2` - Used by the engine for positioning and interaction points

**Helper Methods:**

- `walkable_faces()`: Returns a filtered list of only walkable faces (for pathfinding)
- `unwalkable_faces()`: Returns a filtered list of only non-walkable faces (for collision detection)
- `vertices()`: Returns unique vertex objects referenced by faces (identity-based uniqueness)
- `adjacencies(face)`: Computes adjacencies for a specific face
- `edges()`: Returns perimeter edges (edges with no walkable neighbor)
- `aabbs()`: Generates AABB tree for spatial acceleration

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:126-289`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L126-L289), [`vendor/reone/include/reone/graphics/walkmesh.h:27-89`](https://github.com/th3w1zard1/reone/blob/master/include/reone/graphics/walkmesh.h#L27-L89), [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:24-205`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L24-L205)

### BWMFace Class

Each `BWMFace` represents a single triangular face in the walkmesh, containing all information needed for collision detection, pathfinding, and rendering.

**Key Attributes:**

- **`v1`, `v2`, `v3`**: Vertex objects (`Vector3` instances) defining the triangle's three corners
  - Vertices are shared by reference: multiple faces can reference the same vertex object
  - This ensures geometric consistency and enables efficient adjacency calculations
- **`material`**: `SurfaceMaterial` enum determining walkability and physical properties
  - Controls whether the face is walkable, blocks line of sight, produces sound effects, etc.
- **`trans1`, `trans2`, `trans3`**: Optional per-edge transition indices
  - These are **NOT** unique identifiers and do **NOT** encode geometric adjacency
  - They reference area/room transition data (e.g., door connections, area boundaries)
  - Only present on edges that have corresponding entries in the edges array

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:934-1040`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L934-L1040), [`vendor/KotOR.js/src/three/odyssey/OdysseyFace3.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/three/odyssey/OdysseyFace3.ts)

### BWMEdge Class

The `BWMEdge` class represents a boundary edge (an edge with no walkable neighbor) computed from adjacency data.

**Key Attributes:**

- **`face`**: The `BWMFace` object this edge belongs to
- **`index`**: The local edge index (0, 1, or 2) within the face
  - Edge 0: between `v1` and `v2`
  - Edge 1: between `v2` and `v3`
  - Edge 2: between `v3` and `v1`
- **`transition`**: Optional transition ID linking to area/room transition data
  - `-1` indicates no transition (just a boundary edge)
  - Non-negative values reference door connections or area boundaries
- **`final`**: Boolean flag marking the end of a perimeter loop

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:1273-1352`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L1273-L1352), [`vendor/KotOR.js/src/odyssey/WalkmeshEdge.ts:15-110`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/WalkmeshEdge.ts#L15-L110)

### BWMNodeAABB Class

The `BWMNodeAABB` class represents a node in the AABB tree, providing spatial acceleration for intersection queries.

**Key Attributes:**

- **`bb_min`, `bb_max`**: Minimum and maximum bounding box coordinates (x, y, z) defining the node's spatial extent
- **`face`**: For leaf nodes, the associated face; `None` for internal nodes
- **`sigplane`**: The axis (X, Y, or Z) along which this node splits space
- **`left`, `right`**: References to child nodes (for internal nodes) or `None` (for leaf nodes)

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:1052-1216`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L1052-L1216)

---

## Implementation Comparison

This section documents discrepancies between vendor implementations and provides consensus recommendations.

### Summary of Key Differences

| Feature | reone | xoreos | KotOR.js | kotorblender | PyKotor | Consensus |
|---------|-------|--------|----------|--------------|---------|-----------|
| Vertex position handling | Direct read | Transform matrix | Direct + matrix | Subtracts position | Direct read | Direct read (most common) |
| AABB child indices | 0-based | Multiplied by 44 | 0-based | 0-based | 1-based on write | 0-based array indices |
| Perimeter indices | - | - | As-is | 1-based write | 1-based write | 1-based (marking end of loop) |
| Material 16 (BottomlessPit) | - | - | - | Walkable | Not walkable | Walkable (kotorblender source) |
| Adjacency decoding | edge // 3 | Special formula | edge // 3 | edge // 3 | edge // 3 | edge // 3 |

### Recommendations for PyKotor

Based on vendor analysis:

1. **Material Names**: Update `SurfaceMaterial` enum to use kotorblender's names for IDs 20-22 (Sand, BareBones, StoneBridge)
2. **Material 16 Walkability**: Consider making BottomlessPit walkable to match kotorblender
3. **Perimeter Indices**: Current 1-based implementation matches kotorblender
4. **AABB Child Indices**: Current implementation should write 0-based indices (or 0xFFFFFFFF for no child)
5. **Vertex Handling**: Current direct-read approach is correct

### Test Coverage Analysis

PyKotor's `test_bwm.py` provides comprehensive coverage including:

- ✅ Header validation (magic, version)
- ✅ Walkmesh type (WOK vs PWK/DWK)
- ✅ Vertex roundtrip and deduplication
- ✅ Face ordering (walkable first)
- ✅ Material preservation
- ✅ Adjacency calculation
- ✅ Edge/perimeter identification
- ✅ AABB tree generation (WOK only)
- ✅ Hook vector preservation
- ✅ Complete roundtrip testing

**Missing Test Coverage:**

- ⚠️ AABB tree raycasting functionality
- ⚠️ Point-in-face queries
- ⚠️ Comparison against actual game files
- ⚠️ Multi-room walkmesh loading
- ⚠️ Transformation matrix application

---

## Implementation Details

This section covers important implementation considerations and best practices when working with BWM files.

**Binary Reading**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py:42-182`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py#L42-L182)

The binary reader follows a standard pattern that efficiently loads walkmesh data using the offset-based structure:

1. **Validate header**: Check magic "BWM " and version "V1.0" to ensure file format compatibility
2. **Read walkmesh properties**: Load type, hook vectors, and position
3. **Read data table offsets**: Load all offset and count values from the header
4. **Seek and read data tables**: For each data table, seek to the specified offset and read the appropriate number of elements
5. **Process WOK-specific data** (if type is WOK): Load AABB tree nodes, adjacency data, edges, and perimeters
6. **Process edges and transitions**: Extract transition information from the edges array and apply it to the corresponding faces
7. **Construct runtime `BWM` object**: Create the high-level walkmesh representation with all loaded data

**Binary Writing**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py:185-355`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/io_bwm.py#L185-L355)

The binary writer must perform several complex operations:

1. **Calculate all data table offsets**: This requires computing the size of each data table before writing
2. **Write header with offsets**: Write the magic, version, walkmesh properties, and all offset/count values
3. **Write data tables in order**: Write vertices, face indices, materials, normals, planar distances, AABB nodes, adjacencies, edges, and perimeters
4. **Compute adjacencies from geometry**: The runtime model doesn't store adjacency data directly, so it must be computed
5. **Generate AABB tree if writing WOK file**: AABB tree generation is a complex recursive operation
6. **Compute edges and perimeters from adjacency data**: Identify perimeter edges and group them into loops

**Critical Implementation Notes:**

**Identity vs. Value Equality:**

- Use identity-based searches (`is` operator) when mapping faces back to indices
- Value-based equality can collide: two different face objects with the same vertices are equal by value but distinct by identity
- When computing edge indices (`face_index * 3 + edge_index`), you must use the actual face object's index in the array, not search by value
- **Reference**: [`Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py:564-587`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/bwm/bwm_data.py#L564-L587)

**Transitions vs. Adjacency:**

- `trans1`/`trans2`/`trans3` are optional metadata only, **NOT** adjacency definitions
- Adjacency is computed purely from geometry (shared vertices between walkable faces)
- Transitions reference area/room data structures (doors, area boundaries) and are only present on perimeter edges

**Vertex Sharing:**

- Vertices are shared by object identity: multiple faces reference the same `Vector3` object
- This ensures geometric consistency: adjacent faces share exact vertex positions
- When modifying vertices, changes affect all faces that reference that vertex

**Face Ordering:**

- Walkable faces are typically ordered before non-walkable faces in the face array
- This ordering is important because adjacency data indices correspond to walkable face positions
- When writing, maintain this ordering to ensure adjacency indices remain valid

---

This documentation aims to provide a comprehensive overview of the KotOR BWM file format, focusing on the detailed file structure and data formats used within the games, with particular attention to vendor implementation discrepancies and consensus recommendations.
