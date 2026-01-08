# KotOR BWM File Format Documentation

This document provides a detailed description of the BWM (Binary WalkMesh) file format used in Knights of the Old Republic (KotOR) games.

## What is a BWM File?

A BWM file is a file format used by BioWare games to store walkmesh data. A walkmesh is a simplified 3D model made of triangles that defines where characters can walk, where they cannot walk, and how high the ground is at different locations.

**BWM files come in three types:**

- **WOK (Area Walkmesh)**: Used for entire areas/modules. Contains vertices in world coordinates, includes an AABB tree for fast spatial queries, has walkable adjacency information, and perimeter edges for transitions between areas.
- **PWK (Placeable Walkmesh)**: Used for placeable objects (chests, tables, etc.). Contains vertices in local coordinates (relative to the placeable's position), collision-only (no pathfinding), typically no AABB tree.
- **DWK (Door Walkmesh)**: Used for doors. Similar to PWK, contains vertices in local coordinates, collision-only, typically no AABB tree.

**What walkmeshes do:**

Walkmeshes serve multiple critical functions in KotOR:

- **Pathfinding**: NPCs and the player use walkmeshes to navigate areas, with adjacency data enabling pathfinding algorithms to find routes between walkable faces
- **Collision Detection**: The engine uses walkmeshes to prevent characters from walking through walls, objects, and impassable terrain
- **Spatial Queries**: AABB trees enable efficient ray casting (mouse clicks, projectiles) and point-in-triangle tests (determining which face a character stands on)
- **Area Transitions**: Edge transitions link walkmeshes to door connections and area boundaries, enabling seamless movement between rooms

**Related formats:** BWM files are used in conjunction with [GFF ARE files](GFF-File-Format#are-area) which define area properties and contain references to walkmesh files.

**Game Engine Implementation**: See [Game Engine BWM/AABB Implementation](Game-Engine-BWM-AABB-Implementation) for detailed analysis of how the original KOTOR engine handles BWM files, based on reverse-engineered source code.

---

## Table of Contents

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
- [ASCII Format](#ascii-format)
  - [Format Structure](#format-structure)
  - [Parsing Process](#parsing-process)
  - [Field Specifications](#field-specifications)
  - [Implementation Notes](#implementation-notes)
- [Runtime Model](#runtime-model)
  - [BWM Class](#bwm-class)
  - [BWMFace Class](#bwmface-class)
  - [BWMEdge Class](#bwmedge-class)
  - [BWMNodeAABB Class](#bwmnodeaabb-class)
  - [BWMAdjacency Class](#bwmadjacency-class)

---

## File Structure Overview

The binary format uses a header-based structure where offsets point to various data tables, allowing efficient random access to vertices, faces, materials, and acceleration structures. This design enables the engine to load only necessary portions of large walkmeshes or stream data as needed.

**Total header size**: 136 bytes (0x88)

The file structure is:

1. **Header** (8 bytes): Magic "BWM " and version "V1.0"
2. **Walkmesh Properties** (52 bytes): Coordinate mode, hook vectors, position
3. **Data Table Offsets** (76 bytes): Counts and offsets for all data sections
4. **Data Tables**: Vertices, faces, materials, normals, planar distances, AABB tree, adjacencies, edges, perimeters

---

## Binary Format

### File Header

| Name         | Type    | Offset | Size | Description                                    |
| ------------ | ------- | ------ | ---- | ---------------------------------------------- |
| Magic        | char    | 0 (0x00)   | 4    | Always `"BWM "` (space-padded)                 |
| Version      | char    | 4 (0x04)   | 4    | Always `"V1.0"`                                 |

The file header begins with an 8-byte signature that must exactly match `"BWM V1.0"` (the space after "BWM" is significant). This signature serves as both a file type identifier and version marker. The version string "V1.0" indicates this is the first and only version of the BWM format used in KotOR games. Implementations should validate this header before proceeding with file parsing to ensure they're reading a valid BWM file.

### Walkmesh Properties

The walkmesh properties section immediately follows the header and contains type information, hook vectors, and position data. This section is 52 bytes total (from offset 0x08 to 0x3C).

| Name                    | Type      | Offset | Size | Description                                                      |
| ----------------------- | --------- | ------ | ---- | ---------------------------------------------------------------- |
| world_coords            | uint32    | 8 (0x08)   | 4    | Coordinate mode flag (0=local, 1=world)                          |
| Relative Use position 1 | float32| 12 (0x0C)   | 12   | Relative use hook position 1 (x, y, z)                           |
| Relative Use position 2 | float32| 24 (0x18)   | 12   | Relative use hook position 2 (x, y, z)                           |
| Absolute Use position 1 | float32| 36 (0x24)   | 12   | Absolute use hook position 1 (x, y, z)                           |
| Absolute Use position 2 | float32| 48 (0x30)   | 12   | Absolute use hook position 2 (x, y, z)                           |
| position                | float32| 60 (0x3C)   | 12   | Walkmesh position offset (x, y, z)                               |

**Coordinate mode (`world_coords`):**

- **0 (local)**: vertices are stored in local space and transformed by the engine at runtime (using the owning object's position/rotation).
- **1 (world)**: vertices are stored in world space; the engine treats them as already-transformed.

This is not just a documentation preference: the decompiled engine explicitly treats the field at offset `0x08` as a `world_coords` flag.

References (engine source-of-truth):

- `vendor/swkotor.h`: `CSWWalkMeshHeader.world_coords`
- `vendor/swkotor.c`: `CSWCollisionMesh__LoadMeshBinary` reads `world_coords` from `(data + 0x08)`
- `vendor/swkotor.c`: `CSWCollisionMesh__WorldToLocal` and `CSWCollisionMesh__LocalToWorld` short-circuit when `world_coords != 0`
- `vendor/swkotor.c`: `CSWCollisionMesh__TransformToWorld` sets `world_coords = 1` after baking translation into vertex data
- See [Game Engine BWM/AABB Implementation](Game-Engine-BWM-AABB-Implementation#coordinate-spaces-and-transformations) for detailed coordinate space handling

**Walkmesh Types (by file extension):**

- **WOK (type 1)**: Area walkmesh - defines walkable regions in game areas
  - Stored as `<area_name>.wok` files (e.g., `m12aa.wok` for Dantooine area)
  - Large planar surfaces covering entire rooms or outdoor areas for player movement and NPC pathfinding
  - Often split across multiple rooms in complex areas, with each room having its own walkmesh
  - Includes complete spatial acceleration (AABB tree), adjacencies for pathfinding, edges for transitions, and perimeters for boundary detection
  - Used by the pathfinding system to compute routes between walkable faces

- **PWK/DWK (type 0)**: Placeable/Door walkmesh - collision for placeable objects and doors
  - **PWK**: Stored as `<model_name>.pwk` files - collision geometry for containers, furniture, and other interactive placeable objects
    - Prevents the player from walking through solid objects like crates, tables, and containers
    - Typically much simpler than area walkmeshes, containing only the essential collision geometry
  - **DWK**: Stored as `<door_model>.dwk` files, often with multiple states:
    - `<name>0.dwk` - Closed door state
    - `<name>1.dwk` - Partially open state (if applicable)
    - `<name>2.dwk` - Fully open state
    - Door walkmeshes update dynamically as doors open and close, switching between states
  - Compact collision geometry optimized for small objects rather than large areas
  - Does not include AABB tree or adjacency data (simpler structure, faster loading)
  - Hook vectors (USE1, USE2) define interaction points where the player can activate doors or placeables

**Hook Vectors:**

Hook vectors are reference points used by the engine for positioning and interaction. These are **NOT** related to walkmesh geometry itself (faces, edges, vertices), but rather define interaction points for doors and placeables.

**Important Distinction**: BWM hooks are different from LYT doorhooks:

- **BWM Hooks**: Interaction points stored in the walkmesh file itself (relative/absolute positions)
- **LYT Doorhooks**: Door placement points defined in layout files

- **Relative Hook positions** (Relative Use position 1/2): Positions relative to the walkmesh origin, used when the walkmesh itself may be transformed or positioned
  - For doors: Define where the player must stand to interact with the door (relative to door model)
  - For placeables: Define interaction points relative to the object's local coordinate system

- **Absolute Hook positions** (Absolute Use position 1/2): Positions in world space, used when the walkmesh position is known
  - For doors: Precomputed world-space interaction points (position + relative hook)
  - For placeables: World-space interaction points accounting for object placement

- **Position**: The walkmesh's origin offset in world space
  - For area walkmeshes (WOK): Typically `(0, 0, 0)` as areas define their own coordinate system
  - For placeable/door walkmeshes: The position where the object is placed in the area
  - Used to transform vertices from local to world coordinates

Hook vectors enable the engine to:

- Spawn creatures at designated locations relative to walkable surfaces
- Position triggers and encounters at specific points
- Align objects to the walkable surface (e.g., placing items on tables)
- Define door interaction points (USE1, USE2) where the player can activate doors or placeables

### Data Table Offsets

After the walkmesh properties, the header contains offset and count information for all data tables:

| Name                | Type   | Offset | Size | Description                                                      |
| ------------------- | ------ | ------ | ---- | ---------------------------------------------------------------- |
| Vertex count        | uint32 | 72 (0x48)   | 4    | Number of vertices                                               |
| Vertex offset       | uint32 | 76 (0x4C)   | 4    | Offset to vertex array                                           |
| Face count          | uint32 | 80 (0x50)   | 4    | Number of faces                                                  |
| Face indices offset | uint32 | 84 (0x54)   | 4    | Offset to face indices array                                     |
| Materials offset    | uint32 | 88 (0x58)   | 4    | Offset to materials array                                       |
| Normals offset      | uint32 | 92 (0x5C)   | 4    | Offset to face normals array                                     |
| Distances offset    | uint32 | 96 (0x60)   | 4    | Offset to planar distances array                                 |
| AABB count          | uint32 | 100 (0x64)   | 4    | Number of AABB nodes (WOK only, 0 for PWK/DWK)                  |
| AABB offset         | uint32 | 104 (0x68)   | 4    | Offset to AABB nodes array (WOK only)                            |
| Unknown             | uint32 | 108 (0x6C)   | 4    | Unknown field (typically 0 or 4)                                 |
| Adjacency count     | uint32 | 112 (0x70)   | 4    | Number of walkable faces for adjacency (WOK only)                |
| Adjacency offset    | uint32 | 116 (0x74)   | 4    | Offset to adjacency array (WOK only)                            |
| Edge count          | uint32 | 120 (0x78)   | 4    | Number of perimeter edges (WOK only)                            |
| Edge offset         | uint32 | 124 (0x7C)   | 4    | Offset to edge array (WOK only)                                  |
| Perimeter count     | uint32 | 128 (0x80)   | 4    | Number of perimeter markers (WOK only)                           |
| Perimeter offset    | uint32 | 132 (0x84)   | 4    | Offset to perimeter array (WOK only)                            |

### Vertices

| Name     | Type      | Size | Description                                                      |
| -------- | --------- | ---- | ---------------------------------------------------------------- |
| Vertices | float32| 12×N | Array of vertex positions (X, Y, Z triplets)                    |

Vertices are stored as absolute world coordinates in 32-bit IEEE floating-point format. Each vertex is 12 bytes (three float32 values), and vertices are typically shared between multiple faces to reduce memory usage and ensure geometric consistency.

**Vertex Coordinate Systems:**

- **For area walkmeshes (WOK)**: Vertices are stored in world space coordinates. The walkmesh position is usually (0,0,0) for area walkmeshes, so vertices are already in world space.

- **For placeable/door walkmeshes (PWK/DWK)**: Vertices are stored relative to the object's local origin. When the object is placed in an area, the engine applies a transformation matrix (including translation, rotation, and scale) to convert these local coordinates to world space. This allows the same walkmesh to be reused for multiple instances of the same object at different positions and orientations.

**Vertex Sharing and Indexing:**

Vertices are shared by reference through the index system: multiple faces can reference the same vertex index, ensuring that adjacent faces share exact vertex positions. This is critical for adjacency calculations, as two faces are considered adjacent only if they share exactly two vertices (forming a shared edge). The vertex array is typically deduplicated during walkmesh generation, with similar vertices (within a small tolerance) merged to reduce memory usage and ensure geometric consistency.

### Faces

| Name  | Type     | Size | Description                                                      |
| ----- | -------- | ---- | ---------------------------------------------------------------- |
| Faces | uint32| 12×N | Array of face vertex indices (triplets referencing vertex array) |

Each face is a triangle defined by three vertex indices (0-based) into the vertex array. Each face entry is 12 bytes (three uint32 values). The vertex indices define the triangle's vertices in counter-clockwise order when viewed from the front (the side the normal points toward).

**Face Ordering:**

Faces are typically ordered with walkable faces first, followed by non-walkable faces. This ordering is important because:

- Adjacency data is stored only for walkable faces, and the adjacency array index corresponds to the walkable face's position in the walkable face list (not the overall face list)
- The engine can quickly iterate through walkable faces for pathfinding without checking material types
- Non-walkable faces are still needed for collision detection (preventing characters from walking through walls)

**Face Winding:**

The vertex order determines the face's normal direction (via the right-hand rule). The engine uses this to determine which side of the face is "up" (walkable) versus "down" (non-walkable). Faces should be oriented such that their normals point upward for walkable surfaces.

Normals follow right-hand rule: counter-clockwise vertex order (v1 → v2 → v3) when viewed from front yields upward-pointing normal for walkable surfaces. Cross product formulas `(v2 - v1) × (v3 - v1)` and `(v3 - v2) × (v1 - v2)` are mathematically equivalent.

**Edge Numbering:**

Each triangle has 3 edges, numbered 0, 1, and 2:

- Edge 0: From vertex V1 to vertex V2 (V1 → V2)
- Edge 1: From vertex V2 to vertex V3 (V2 → V3)
- Edge 2: From vertex V3 to vertex V1 (V3 → V1)

### Materials

| Name      | Type   | Size | Description                                                      |
| --------- | ------ | ---- | ---------------------------------------------------------------- |
| Materials | uint32  | 4×N  | Surface material index per face (determines walkability)         |

Each face is assigned a material type that determines its physical properties and interaction behavior. The material ID is stored as a `uint32` per face.

**Complete Material List:**

| ID | Name              | Walkable | Description                                                      |
|----|-------------------|----------|------------------------------------------------------------------|
| 0  | NotDefined/UNDEFINED | No    | Undefined material (default)                                     |
| 1  | Dirt              | Yes      | Standard walkable dirt surface                                   |
| 2  | Obscuring         | No       | Blocks line of sight but may be walkable                        |
| 3  | Grass             | Yes      | Walkable with grass sound effects                                |
| 4  | Stone             | Yes      | Walkable with stone sound effects                                |
| 5  | Wood              | Yes      | Walkable with wood sound effects                                 |
| 6  | Water             | Yes      | Shallow water - walkable with water sounds                       |
| 7  | Nonwalk/NON_WALK  | No       | Impassable surface - blocks character movement                  |
| 8  | Transparent       | No       | Transparent non-walkable surfaces                                 |
| 9  | Carpet            | Yes      | Walkable with muffled footstep sounds                           |
| 10 | Metal             | Yes      | Walkable with metallic sound effects                            |
| 11 | Puddles           | Yes      | Walkable water puddles                                          |
| 12 | Swamp             | Yes      | Walkable swamp terrain                                          |
| 13 | Mud               | Yes      | Walkable mud surface                                             |
| 14 | Leaves            | Yes      | Walkable with leaf sound effects                                 |
| 15 | Lava              | No       | Damage-dealing surface (non-walkable)                            |
| 16 | BottomlessPit     | Yes*     | Walkable but dangerous (fall damage)                            |
| 17 | DeepWater         | No       | Deep water - typically non-walkable or swim areas                |
| 18 | Door              | Yes      | Door surface (special handling)                                 |
| 19 | Snow/NON_WALK_GRASS | No     | Snow surface (non-walkable)                                      |
| 20 | Sand              | Yes      | Walkable sand surface                                            |
| 21 | BareBones         | Yes      | Walkable bare surface                                            |
| 22 | StoneBridge       | Yes      | Walkable stone bridge surface                                    |
| 30 | Trigger           | Yes      | Trigger surface (PyKotor extended)                               |

**Note**: Material 16 (BottomlessPit) walkability may vary between implementations. Some mark it as walkable (allowing the player to fall), while some game logic may treat it differently.

Materials control not just walkability but also:

- Footstep sound effects during movement
- Visual effects (ripples on water, dust on dirt)
- Damage-over-time mechanics (lava, acid)
- AI pathfinding cost (creatures prefer some surfaces over others)
- Line-of-sight blocking (obscuring materials)

### Derived Data

| Name           | Type    | Size | Description                                                      |
| -------------- | ------- | ---- | ---------------------------------------------------------------- |
| Face Normals   | float32 | 12×N | Normal vectors for each face (normalized)                        |
| Planar Distances | float32 | 4×N | D component of plane equation (ax + by + cz + d = 0) for each face |

**Face Normals:**

Face normals are precomputed unit vectors perpendicular to each face. They are calculated using the cross product of two edge vectors: `normal = normalize((v2 - v1) × (v3 - v1))`. The normal direction follows the right-hand rule based on vertex winding order, with normals typically pointing upward for walkable surfaces.

**Planar Distances:**

Planar distances are the D component of the plane equation `ax + by + cz + d = 0`, where (a, b, c) is the face normal. The D component is calculated as `d = -normal · vertex1` for each face, where vertex1 is typically the first vertex of the triangle. This precomputed value allows the engine to quickly test point-plane relationships without recalculating the plane equation each time.

These derived values are stored in the file to avoid recomputation during runtime, which is especially important for large walkmeshes where thousands of faces need to be tested for intersection or containment queries.

### AABB Tree

| Name          | Type    | Size | Description                                                      |
| ------------- | ------- | ---- | ---------------------------------------------------------------- |
| AABB Nodes    | varies  | varies | Bounding box tree nodes for spatial acceleration (WOK only)      |

**What is an AABB Tree?**

An AABB tree is a way of organizing triangles into boxes so we can find them quickly. Without it, we would have to check every single triangle to find which one contains a point, which is very slow when there are thousands of triangles. With an AABB tree, we can find triangles much faster (in O(log n) time instead of O(n) time).

**How it Works:**

The tree is built using a recursive top-down approach:

1. Start with all triangles in one big box (the root)
2. Split the box in half along the longest axis (X, Y, or Z)
3. Put triangles on the left side of the split into one box, triangles on the right side into another
4. Recursively split each box until each box contains only one triangle (a leaf node)

**The Tree Structure:**

- **Internal nodes**: Boxes that contain other boxes. They have Left and Right child pointers.
- **Leaf nodes**: Boxes that contain exactly one triangle. They have a Face pointer instead of children.

Each node stores:

- **BbMin**: The minimum corner of the bounding box (smallest X, Y, Z values)
- **BbMax**: The maximum corner of the bounding box (largest X, Y, Z values)
- **Face**: The triangle (only for leaf nodes, null for internal nodes)
- **Sigplane**: Which axis was used to split this node (X=1, Y=2, Z=3, or 0 for leaf nodes)
- **Left**: Pointer to the left child node (null for leaf nodes)
- **Right**: Pointer to the right child node (null for leaf nodes)

**Why Only Area Walkmeshes Get AABB Trees:**

- Area walkmeshes (WOK files) can have thousands of triangles, so an AABB tree is essential for fast spatial queries (finding which triangle contains a point, raycasting, etc.)
- Placeable/door walkmeshes (PWK/DWK files) are small (usually only a few triangles), so brute force is fast enough and building a tree would be unnecessary overhead

**Performance:**

- Building the tree: O(n log n) time where n is the number of triangles
- Finding a triangle: O(log n) average case, O(n) worst case (degenerate tree)
- Without tree: O(n) always (must check every triangle)
- Speedup: 100x-1000x faster for large meshes (1000+ triangles)

**Key Operations Enabled:**

- **Ray Casting**: Finding where a ray intersects the walkmesh
  - Mouse clicks: Determining which walkable face the player clicked on for movement commands
  - Projectiles: Testing if projectiles hit walkable surfaces or obstacles
  - Line of sight: Checking if a line between two points intersects the walkmesh

- **Point Queries**: Determining which face a character is standing on
  - Character positioning: Finding the walkable face beneath a character's position
  - Elevation calculation: Computing the Z coordinate for a character at a given (X, Y) position
  - Collision response: Determining surface normals and materials for physics calculations

**AABB Node Structure:**

Each AABB node is **44 bytes** and contains:

| Name                  | Type    | Offset | Size | Description                                                      |
| --------------------- | ------- | ------ | ---- | ---------------------------------------------------------------- |
| Bounds Min            | float32 | 0 (0x00) | 12  | Minimum bounding box coordinates (x, y, z)                      |
| Bounds Max            | float32 | 12 (0x0C) | 12  | Maximum bounding box coordinates (x, y, z)                       |
| Face index            | int32   | 24 (0x18) | 4    | Face index for leaf nodes, -1 (0xFFFFFFFF) for internal nodes   |
| Unknown               | uint32  | 28 (0x1C) | 4    | Unknown field (typically 4)                                       |
| Most Significant Plane| uint32  | 32 (0x20) | 4    | Split axis/plane identifier (see below)                          |
| Left Child index      | uint32  | 36 (0x24) | 4    | Index to left child node (0-based array index, 0xFFFFFFFF = no child) |
| Right Child index     | uint32  | 40 (0x28) | 4    | Index to right child node (0-based array index, 0xFFFFFFFF = no child) |

**Important**: Child indices use **0-based array indexing**. The first node in the AABB array is at index 0, the second at index 1, and so on. The value `0xFFFFFFFF` indicates no child (leaf node or missing child). This matches standard array indexing in most programming languages. For implementation details and how different tools handle this, see the [Implementation Approaches and Differences](#implementation-approaches-and-differences) section.

**Most Significant Plane values:**

| Value | Meaning |
|-------|---------|
| 0x00 | No children (leaf node) |
| 0x01 | Positive X axis split |
| 0x02 | Positive Y axis split |
| 0x03 | Positive Z axis split |
| 0xFFFFFFFE (-2) | Negative X axis split |
| 0xFFFFFFFD (-3) | Negative Y axis split |
| 0xFFFFFFFC (-4) | Negative Z axis split |

**Tree Construction Algorithm:**

1. Compute bounding box for all faces
2. If only one face remains, create a leaf node
3. Find the longest axis of the bounding box
4. Split faces into left/right groups based on centroid position relative to bounding box center
5. Recursively build left and right subtrees
6. Handle degenerate cases (all faces on one side) by trying alternative axes or splitting evenly

### Walkable Adjacencies

| Name            | Type    | Size | Description                                                      |
| --------------- | ------- | ---- | ---------------------------------------------------------------- |
| Adjacencies     | int32| 12×N | Three adjacency indices per walkable face (-1 = no neighbor)     |

**What is Adjacency?**

Adjacency tells which triangles share edges with each other. Two triangles are adjacent (neighbors) if they share exactly two vertices, which forms a shared edge. This information is critical for pathfinding because the pathfinding algorithm needs to know which triangles can be reached from the current triangle.

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

```python
face_index = adjacency_index // 3
edge_index = adjacency_index % 3
```

**Bidirectional Linking:**

Adjacency is always bidirectional. If face A's edge connects to face B's edge, then:

- Face A's adjacency points to face B
- Face B's adjacency points to face A

This ensures pathfinding can traverse in both directions along shared edges.

**Adjacency Calculation:**

The algorithm computes adjacency by:

1. Looking at each edge of each walkable triangle
2. Finding if any other walkable triangle shares that same edge (same two vertices)
3. If found, creates an adjacency linking them using the encoding: `face_index * 3 + edge_index`
4. Stores this in the adjacency array

### Edges

| Name  | Type     | Size | Description                                                      |
| ----- | -------- | ---- | ---------------------------------------------------------------- |
| Edges | varies   | varies | Perimeter edge data (edge_index, transition pairs) (WOK only)  |

**What is a BWMEdge?**

A BWMEdge represents an edge of a walkmesh triangle that is on the perimeter (boundary) of the walkable area. Perimeter edges are edges that don't have a neighboring triangle on one side - they form the outer boundary of the walkmesh.

The edges array contains perimeter edges (boundary edges with no walkable neighbor). Each edge entry is **8 bytes**:

| Name        | Type   | Size | Description                                                      |
| ----------- | ------ | ---- | ---------------------------------------------------------------- |
| Edge index  | uint32 | 4    | Encoded edge index: `face_index * 3 + local_edge_index`        |
| Transition  | int32  | 4    | Transition ID for room/area connections, -1 if no transition     |

**Edge Index Encoding:**

The edge index uses the same encoding as adjacency indices: `edge_index = face_index * 3 + local_edge_index`. This identifies:

- Which face the edge belongs to (`face_index = edge_index // 3`)
- Which edge of that face (0, 1, or 2) (`local_edge_index = edge_index % 3`)

**Perimeter Edges:**

Perimeter edges are edges of walkable faces that have no adjacent walkable neighbor. These edges form the boundaries of walkable regions and are critical for:

- **Area Transitions**: Edges with non-negative transition IDs link to door connections or area boundaries
- **Boundary Detection**: Perimeter edges define the limits of walkable space
- **Visual Debugging**: Perimeter edges can be visualized to show walkmesh boundaries in level editors

**How are Edges Identified as Perimeter?**

An edge is a perimeter edge if:

1. It belongs to a walkable face (non-walkable faces don't have perimeter edges)
2. It doesn't have an adjacent neighbor face (no other triangle shares that edge)

The BWM.Edges() method finds all perimeter edges by:

1. Getting all walkable faces
2. Computing adjacency for each walkable face
3. Finding edges that have no adjacency (null adjacency = perimeter edge)
4. Following the perimeter loop by walking along connected perimeter edges

**Transitions and Door Placement:**

Transitions tell the game which rooms or areas are connected at this edge. When you place a door in the indoor map builder, it uses transitions to know where doors should go.

The transition value comes from the face's Trans1, Trans2, or Trans3 property, depending on which edge this is:

- Edge 0 (V1->V2): Uses face.Trans1
- Edge 1 (V2->V3): Uses face.Trans2
- Edge 2 (V3->V1): Uses face.Trans3

When the indoor map builder processes a room's walkmesh, it remaps transitions from dummy indices (from the kit component) to actual room indices (in the built module).

### Perimeters

| Name      | Type   | Size | Description                                                      |
| --------- | ------ | ---- | ---------------------------------------------------------------- |
| Perimeters | uint32 | 4×N  | Indices into edge array marking end of perimeter loops (WOK only) |

**What are Perimeters?**

Perimeters mark the end of closed loops of perimeter edges. Each perimeter value is an index into the edge array, indicating where a perimeter loop ends. This allows the engine to traverse complete boundary loops for pathfinding and area transitions.

**Perimeter Loop Construction:**

Perimeter edges form closed loops around walkable areas. The algorithm:

1. Starts at a perimeter edge
2. Follows connected perimeter edges in a loop
3. Marks the last edge in each loop with Final = true
4. Continues until all perimeter edges are processed

These loops define the boundaries of walkable areas and are used for:

- Door placement (doors go on perimeter edges with transitions)
- Area visualization (drawing boundaries)
- Collision detection (knowing where walkable area ends)

**Perimeter Index Encoding:**

Perimeter indices are 1-based indices marking the end of each loop:

- **Loop 1**: Edges from index 0 to `perimeters[0] - 1`
- **Loop N**: Edges from `perimeters[N-2]` to `perimeters[N-1] - 1`

---

## ASCII Format

The game engine also supports an ASCII text-based walkmesh format, typically used for development and toolset export/import. The ASCII format uses a hierarchical block structure similar to ASCII model files.

The format is parsed by the game engine's `CSWRoomSurfaceMesh::LoadMeshText` function (K1: `0x00582d70` in `swkotor.exe`, TSL: `0x00577860` in `swkotor2.exe`).

**Note**: The ASCII format is primarily a development/toolset format, not typically used in-game. The binary format (BWM) is the runtime format used by the game. The engine supports both formats, detecting automatically in `LoadMesh`.

### Format Structure

#### Grammar

```
walkmesh ::= "node aabb" NEWLINE
             position_block
             orientation_block?
             verts_block
             faces_block
             aabb_block?
             "endnode" NEWLINE

position_block ::= "    position" SPACE float SPACE float SPACE float NEWLINE

orientation_block ::= "    orientation" SPACE float SPACE float SPACE float SPACE float NEWLINE

verts_block ::= "    verts" SPACE integer NEWLINE
                (vertex_line NEWLINE)+

vertex_line ::= SPACE* float SPACE float SPACE float

faces_block ::= "    faces" SPACE integer NEWLINE
                (face_line NEWLINE)+

face_line ::= SPACE* integer SPACE integer SPACE integer SPACE integer SPACE integer SPACE integer SPACE integer SPACE integer
              // 8 integers: v1 v2 v3 adj1 adj2 adj3 adj4 material

aabb_block ::= "    aabb" NEWLINE
               (aabb_line NEWLINE)*

aabb_line ::= SPACE* float SPACE float SPACE float SPACE float SPACE float SPACE float SPACE integer
              // 7 values: min_x min_y min_z max_x max_y max_z face_index

endnode ::= "endnode" NEWLINE
```

#### Example File

```
node aabb
    position 0.0 0.0 0.0
    orientation 0.0 0.0 0.0 1.0
    verts 4
        0.0 0.0 0.0
        10.0 0.0 0.0
        10.0 10.0 0.0
        0.0 10.0 0.0
    faces 2
        0 1 2 -1 -1 -1 -1 0
        0 2 3 -1 -1 -1 -1 0
    aabb
        0.0 0.0 0.0 10.0 10.0 0.0 0
        0.0 0.0 0.0 10.0 10.0 0.0 1
endnode
```

### Parsing Process

The engine parses ASCII walkmesh files line-by-line using a helper function `CSWCollisionMesh::LoadMeshString` (K1: `0x005968a0` in `swkotor.exe`, TSL: `0x005573e0` in `swkotor2.exe`). Both implementations read up to 256 bytes per line, stopping at newline characters (0x0A) and null-terminating the result.

#### Line Reading

```c
int LoadMeshString(byte** input_ptr, size_t* remaining, byte* buffer, size_t buffer_size) {
    size_t bytes_read = 0;
    while (bytes_read < (buffer_size - 1) && *remaining > 0) {
        buffer[bytes_read] = **input_ptr;
        (*input_ptr)++;
        (*remaining)--;
        if (buffer[bytes_read] == 0x0A) break;  // Newline
        bytes_read++;
    }
    if (bytes_read >= buffer_size) return 0;  // Buffer overflow
    buffer[bytes_read] = 0;  // Null-terminate
    return 1;
}
```

#### Whitespace Handling

Leading whitespace (spaces and tabs) is stripped before keyword detection:

```c
char* src = line_buffer;
while (*src == 0x20) {  // Space character
    src++;
}
// Process keyword from 'src' position
```

### Field Specifications

#### 1. Node Block

The walkmesh must start with `"node aabb"` and end with `"endnode"`.

**Detection Logic**:
```c
if (strncmp(src, "node", 4) == 0) {
    src += 4;
    if (strncmp(src, " aabb", 5) == 0) {
        in_node_block = 1;
    }
}

// End detection
if (strncmp(src, "endnode", 7) == 0) {
    in_node_block = 0;
}
```

#### 2. Position Field

**Format**: `"position" SPACE float SPACE float SPACE float`

**Parsing**:
```c
float x, y, z;
sscanf(src, "position %f %f %f", &x, &y, &z);
mesh->position.x = x;
mesh->position.y = y;
mesh->position.z = z;
```

**Storage**: Stored as a Vector3 in the mesh structure (offset 0x2C).

#### 3. Orientation Field

**Format**: `"orientation" SPACE float SPACE float SPACE float SPACE float`

**Parsing**:
```c
float x, y, z, w;
sscanf(src, "orientation %f %f %f %f", &x, &y, &z, &w);

if (abs(x) < 0.0001 && abs(y) < 0.0001 && abs(z) < 0.0001) {
    // Identity quaternion (0, 0, 0, 1)
    mesh->orientation.x = 0.0;
    mesh->orientation.y = 0.0;
    mesh->orientation.z = 0.0;
    mesh->orientation.w = 1.0;
} else {
    // Convert axis-angle to quaternion
    Vector3 axis(x, y, z);
    Quaternion q(axis, w);  // Axis-angle constructor
    mesh->orientation = q;
}
```

**Note**: The orientation field uses axis-angle representation (axis vector + angle), not direct xyzw quaternion. The engine converts this internally.

**Storage**: Stored as a Quaternion in the mesh structure (offset 0x38).

#### 4. Vertices Block

**Format**:
```
"verts" SPACE integer NEWLINE
(float SPACE float SPACE float NEWLINE)+
```

**Parsing**:
```c
int vertex_count;
sscanf(src, "verts %d", &vertex_count);
mesh->SetVertexCount(vertex_count);

for (int i = 0; i < vertex_count; i++) {
    float x, y, z;
    LoadMeshString(&input_ptr, &remaining, line_buffer, 256);
    sscanf(line_buffer, "%f %f %f", &x, &y, &z);
    mesh->vertices[i].x = x;
    mesh->vertices[i].y = y;
    mesh->vertices[i].z = z;
}
```

**Storage**: Vertices stored as an array of Vector3 structures (12 bytes each: 3 floats).

**Coordinate Quantization**: The engine performs a quantization check on vertex coordinates, but this appears to be for binary format optimization. For ASCII parsing, coordinates are read directly as floats.

#### 5. Faces Block

**Format**:
```
"faces" SPACE integer NEWLINE
(integer SPACE integer SPACE integer SPACE integer SPACE integer SPACE integer SPACE integer SPACE integer NEWLINE)+
```

**Face Line Format**: Each face line contains **8 integers**:
1. `v1` - First vertex index
2. `v2` - Second vertex index
3. `v3` - Third vertex index
4. `adj1` - Adjacency data (read but not stored)
5. `adj2` - Adjacency data (read but not stored)
6. `adj3` - Adjacency data (read but not stored)
7. `adj4` - Adjacency data (read but not stored)
8. `material` - Material ID

**Parsing**:
```c
int face_count;
sscanf(src, "faces %d", &face_count);

// Allocate temporary buffers
uint32_t* vertex_indices = malloc(face_count * 12);  // 3 indices per face
uint32_t* material_ids = malloc(face_count * 4);     // 1 material per face

// Read all faces
for (int i = 0; i < face_count; i++) {
    int v1, v2, v3, adj1, adj2, adj3, adj4, material;
    LoadMeshString(&input_ptr, &remaining, line_buffer, 256);
    sscanf(line_buffer, "%d %d %d %d %d %d %d %d", 
           &v1, &v2, &v3, &adj1, &adj2, &adj3, &adj4, &material);
    
    // Store only vertex indices and material ID
    vertex_indices[i * 3 + 0] = v1;
    vertex_indices[i * 3 + 1] = v2;
    vertex_indices[i * 3 + 2] = v3;
    material_ids[i] = material;
    // Adjacency data (adj1-adj4) is read but not stored
}
```

**Material Lookup and Walkability**:

The engine determines walkability by looking up the material in the `surfacemat.2DA` table:

```c
int walkable_count = 0;
int unwalkable_count = 0;
uint32_t* walkable_indices = malloc(face_count * 4);
uint32_t* unwalkable_indices = malloc(face_count * 4);

for (int i = 0; i < face_count; i++) {
    int walk_value;
    C2DA::GetINTEntry(surfacemat_2da, material_ids[i], "Walk", &walk_value);
    
    if (walk_value == 0) {
        // Material is NOT walkable
        unwalkable_indices[unwalkable_count++] = i;
    } else {
        // Material IS walkable
        walkable_indices[walkable_count++] = i;
    }
}
```

**Face Reordering**:

Walkable faces are stored first, followed by unwalkable faces:

```c
// Copy walkable faces first
for (int i = 0; i < walkable_count; i++) {
    int src_idx = walkable_indices[i];
    mesh->face_indices[i].vertex_1 = vertex_indices[src_idx * 3 + 0];
    mesh->face_indices[i].vertex_2 = vertex_indices[src_idx * 3 + 1];
    mesh->face_indices[i].vertex_3 = vertex_indices[src_idx * 3 + 2];
    mesh->materials[i] = material_ids[src_idx];
}

// Copy unwalkable faces after walkable faces
for (int i = 0; i < unwalkable_count; i++) {
    int src_idx = unwalkable_indices[i];
    int dst_idx = walkable_count + i;
    mesh->face_indices[dst_idx].vertex_1 = vertex_indices[src_idx * 3 + 0];
    mesh->face_indices[dst_idx].vertex_2 = vertex_indices[src_idx * 3 + 1];
    mesh->face_indices[dst_idx].vertex_3 = vertex_indices[src_idx * 3 + 2];
    mesh->materials[dst_idx] = material_ids[src_idx];
}

mesh->adjacency_count = walkable_count;  // Number of walkable faces
```

**Final Structure**:
- **Walkable faces** (indices 0 to `adjacency_count - 1`): Stored first
- **Unwalkable faces** (indices `adjacency_count` to `face_count - 1`): Stored after walkable faces
- `adjacency_count`: Set to number of walkable faces (used for adjacency table size in binary format)

#### 6. AABB Block

**Format**:
```
"aabb" NEWLINE
(float SPACE float SPACE float SPACE float SPACE float SPACE float SPACE integer NEWLINE)*
```

**AABB Line Format**: Each line contains **7 values**:
1. `min_x` (float) - Minimum X bound
2. `min_y` (float) - Minimum Y bound
3. `min_z` (float) - Minimum Z bound
4. `max_x` (float) - Maximum X bound
5. `max_y` (float) - Maximum Y bound
6. `max_z` (float) - Maximum Z bound
7. `face_index` (int) - Face index for leaf nodes (-1 for internal nodes)

**Parsing**:
```c
while (/* more lines available */) {
    float min_x, min_y, min_z, max_x, max_y, max_z;
    int face_index;
    LoadMeshString(&input_ptr, &remaining, line_buffer, 256);
    
    // Check if line is "aabb" keyword or data line
    if (strncmp(line_buffer, "aabb", 4) == 0) {
        continue;  // Skip keyword line
    }
    
    sscanf(line_buffer, "%f %f %f %f %f %f %d",
           &min_x, &min_y, &min_z, &max_x, &max_y, &max_z, &face_index);
    
    // Min/Max Swapping
    if (max_x < min_x) { float tmp = min_x; min_x = max_x; max_x = tmp; }
    if (max_y < min_y) { float tmp = min_y; min_y = max_y; max_y = tmp; }
    if (max_z < min_z) { float tmp = min_z; min_z = max_z; max_z = tmp; }
    
    // Epsilon Expansion
    const float EPSILON = 0.01f;  // 0x3C23D70A
    min_x -= EPSILON;
    min_y -= EPSILON;
    min_z -= EPSILON;
    max_x += EPSILON;
    max_y += EPSILON;
    max_z += EPSILON;
    
    // Face Index Mapping
    // Maps face indices to reordered array (walkable first, unwalkable second)
    if (face_index != -1) {
        // Map to correct position in reordered face array
    }
    
    // Store AABB node (44 bytes = 0x2c)
    AABBNode* node = malloc(44);
    node->bbox_min = Vector3(min_x, min_y, min_z);
    node->bbox_max = Vector3(max_x, max_y, max_z);
    node->face_index = face_index;
    // ... other fields ...
}
```

**AABB Node Structure** (44 bytes):
- Offset 0x00-0x17 (24 bytes): Bounding box (6 floats: min_x, min_y, min_z, max_x, max_y, max_z)
- Offset 0x18 (4 bytes): Face index (int32, -1 for internal nodes)
- Offset 0x1C (4 bytes): Unknown field
- Offset 0x20 (4 bytes): Split plane axis (int32, used for tree traversal)
- Offset 0x24 (4 bytes): Left child pointer/index
- Offset 0x28 (4 bytes): Right child pointer/index

**Tree Construction**: The engine builds a hierarchical AABB tree structure from the parsed nodes, linking parent-child relationships and calculating split planes based on bounding box dimensions. The complete tree building algorithm is complex and involves maintaining stacks of nodes with unresolved children.

**Epsilon Constant**: `0.01` (0x3C23D70A) - Applied to all bounding box coordinates to prevent floating-point precision issues.

### Implementation Notes

#### Critical Requirements

1. **8-Integer Face Format**: The format reads 8 integers per face, but only stores vertex indices (3 ints) and material ID (1 int). The adjacency integers (4 ints) are parsed but not stored in the face structure.

2. **Walkable/Unwalkable Separation**: Faces **MUST** be separated into walkable and unwalkable groups, with walkable faces stored first. This ordering is critical for adjacency table indexing in binary format.

3. **Material Lookup**: Walkability is determined by looking up the material ID in the `surfacemat.2DA` table using the "Walk" column. A value of 0 means unwalkable, non-zero means walkable.

4. **AABB Tree Construction**: The AABB tree construction is complex. For initial implementation, parsing AABB nodes and storing them is sufficient. Full tree reconstruction can be deferred to the writer, which regenerates AABB trees from geometry.

5. **Epsilon Expansion**: Apply 0.01 epsilon to all AABB bounding box coordinates to match engine behavior.

6. **Face Index Mapping**: When parsing AABB nodes, map face indices to the reordered face array (walkable first, unwalkable second).

#### Error Handling

The engine handles errors by:
- Calling `LoadDefaultMesh` vtable function on parse errors
- Returning `1` on error (not `0`)
- Freeing all allocated memory on error

#### Line Buffer

- **Buffer Size**: 256 bytes (0x100)
- **Behavior**: Stops reading at newline (0x0A) or buffer limit
- **Null Termination**: Adds null terminator after reading line

#### Whitespace

- **Leading Whitespace**: Stripped before keyword detection
- **Inter-Token Whitespace**: Required between values (handled by `sscanf`)
- **Newlines**: Required after each line (0x0A, consumed by `LoadMeshString`)

#### Engine References

- `CSWRoomSurfaceMesh::LoadMeshText` - K1: `0x00582d70` in `swkotor.exe`, TSL: `0x00577860` in `swkotor2.exe` (3882 bytes)
- `CSWCollisionMesh::LoadMeshString` - K1: `0x005968a0` in `swkotor.exe`, TSL: `0x005573e0` in `swkotor2.exe` (95 bytes)
- `CSWCollisionMesh::LoadMesh` - K1: `0x00596670` in `swkotor.exe` (entry point, detects ASCII vs binary)
- `C2DA::GetINTEntry` - `0x0041d630` in both games (material lookup)

---

## Runtime Model

The runtime model provides high-level, in-memory representations of walkmesh data that are easier to work with than raw binary structures. These classes abstract away the binary format details and provide convenient methods for common operations.

### BWM Class

The `BWM` class represents a complete walkmesh in memory, providing a high-level interface for working with walkmesh data.

**Key Attributes:**

- **`Faces`**: Ordered list of `BWMFace` objects representing all triangular faces in the walkmesh
  - Faces are typically ordered with walkable faces first, followed by non-walkable faces
  - The face list is the primary data structure for accessing walkmesh geometry
- **`WalkmeshType`**: Type of walkmesh (`BWMType.AreaModel` for WOK, `BWMType.PlaceableOrDoor` for PWK/DWK)
- **`Position`**: 3D position offset for the walkmesh in world space
- **Positional hooks**: `RelativeHook1`, `RelativeHook2`, `AbsoluteHook1`, `AbsoluteHook2` - Used by the engine for positioning and interaction points

**Helper Methods:**

- `WalkableFaces()`: Returns a filtered list of only walkable faces (for pathfinding)
- `UnwalkableFaces()`: Returns a filtered list of only non-walkable faces (for collision detection)
- `Vertices()`: Returns unique vertex objects referenced by faces (identity-based uniqueness)
- `Adjacencies(face)`: Computes adjacencies for a specific face
- `Edges()`: Returns perimeter edges (edges with no walkable neighbor)
- `Aabbs()`: Generates AABB tree for spatial acceleration
- `Raycast(origin, direction, maxDistance, materials)`: Performs a raycast against the walkmesh
- `FindFaceAt(x, y, materials)`: Finds which triangle contains a given (x, y) point
- `GetHeightAt(x, y, materials)`: Gets the height (Z coordinate) of the walkmesh surface at a given (x, y) position

### BWMFace Class

Each `BWMFace` represents a single triangular face in the walkmesh, containing all information needed for collision detection, pathfinding, and rendering.

**What is a BWMFace?**

A BWMFace is a single triangle in a walkmesh. It represents one small piece of the walkable surface. The walkmesh is made up of many BWMFace objects, each one a triangle that covers part of the ground.

**Key Attributes:**

- **`V1`, `V2`, `V3`**: Vertex objects (`Vector3` instances) defining the triangle's three corners
  - Vertices are shared by reference: multiple faces can reference the same vertex object
  - This ensures geometric consistency and enables efficient adjacency calculations
- **`Material`**: `SurfaceMaterial` enum determining walkability and physical properties
  - Controls whether the face is walkable, blocks line of sight, produces sound effects, etc.
- **`Trans1`, `Trans2`, `Trans3`**: Optional per-edge transition indices
  - These are **NOT** unique identifiers and do **NOT** encode geometric adjacency
  - They reference area/room transition data (e.g., door connections, area boundaries)
  - Only present on edges that have corresponding entries in the edges array

**How are Transitions Used?**

Transitions tell the game which rooms or areas are connected at each edge of the triangle. When you place a door in the indoor map builder, it uses transitions to know where doors should go. The transition value is an index into the list of rooms in the module.

For example:

- If Trans1 = 5, it means edge 0 connects to room index 5
- If Trans1 = null, it means edge 0 has no connection (is a boundary or wall)

When the indoor map builder processes a room's walkmesh, it remaps transitions from dummy indices (from the kit component) to actual room indices (in the built module).

**Material Inheritance:**

BWMFace inherits from Face, which provides:

- V1, V2, V3: The three vertices
- Material: The surface material
- Normal(): Calculates the triangle's normal vector
- Area(): Calculates the triangle's area
- Centre(): Gets the center point of the triangle
- DetermineZ(x, y): Calculates height at a given (x, y) point

The Material property is critical for walkability. When checking if a face is walkable, the code calls Material.Walkable() which checks if the material ID is in the walkable set.

**Critical: Material Preservation During Transformations:**

When a BWM is transformed (flipped, rotated, or translated), the Material property MUST be preserved. The BWM.Flip(), BWM.Rotate(), and BWM.Translate() methods only modify vertices, not materials, so materials are automatically preserved.

However, when creating deep copies of BWMs (like in IndoorMap.ProcessBwm), you MUST ensure that Material is copied: `newFace.Material = face.Material`

If materials are not preserved, faces that should be walkable will become non-walkable, causing bugs where levels/modules are NOT walkable despite having the right surface material.

### BWMEdge Class

The `BWMEdge` class represents a boundary edge (an edge with no walkable neighbor) computed from adjacency data.

**What is a BWMEdge?**

A BWMEdge represents an edge of a walkmesh triangle that is on the perimeter (boundary) of the walkable area. Perimeter edges are edges that don't have a neighboring triangle on one side - they form the outer boundary of the walkmesh.

**Key Attributes:**

- **`Face`**: The `BWMFace` object this edge belongs to
- **`Index`**: The local edge index (0, 1, or 2) within the face
  - Edge 0: between `v1` and `v2`
  - Edge 1: between `v2` and `v3`
  - Edge 2: between `v3` and `v1`
- **`Transition`**: Optional transition ID linking to area/room transition data
  - `-1` indicates no transition (just a boundary edge)
  - Non-negative values reference door connections or area boundaries
- **`Final`**: Boolean flag marking the end of a perimeter loop

### BWMNodeAABB Class

The `BWMNodeAABB` class represents a node in the AABB (Axis-Aligned Bounding Box) tree stored in a BWM file.

**What is a BWMNodeAABB?**

A BWMNodeAABB is a single node in a tree structure that helps the game quickly find which triangles are near a given point. It's like a filing cabinet where files (triangles) are organized into drawers (boxes) that are organized into bigger drawers (bigger boxes).

The AABB tree is stored directly in the BWM file for WOK (area) walkmeshes. When the game loads a walkmesh, it can use this pre-built tree instead of building a new one from scratch. This saves time during loading.

**Key Attributes:**

- **`BbMin`, `BbMax`**: Minimum and maximum bounding box coordinates (x, y, z) defining the node's spatial extent
- **`Face`**: For leaf nodes, the associated face; `null` for internal nodes
- **`Sigplane`**: The "most significant plane" used to split this node
  - This tells us which axis (X, Y, or Z) was used to divide triangles into left and right
  - Used when building the tree to decide how to organize triangles
- **`Left`, `Right`**: References to child nodes (for internal nodes) or `null` (for leaf nodes)

**Leaf Nodes vs Internal Nodes:**

- **Leaf Node** (contains a triangle):
  - Face != null (points to a BWMFace)
  - Left = null (no children)
  - Right = null (no children)
  - BbMin and BbMax form a box around the triangle

- **Internal Node** (contains child nodes):
  - Face = null (no triangle here)
  - Left != null (has a left child)
  - Right != null (has a right child)
  - BbMin and BbMax form a box that contains both children's boxes

### BWMAdjacency Class

The `BWMAdjacency` class represents adjacency information between two walkmesh faces.

**What is Adjacency?**

Adjacency tells which triangles share edges with each other. Two triangles are adjacent (neighbors) if they share exactly two vertices, which forms a shared edge. This information is critical for pathfinding because the pathfinding algorithm needs to know which triangles can be reached from the current triangle.

**What Data Does it Store?**

A BWMAdjacency stores:

1. **Face**: The adjacent (neighbor) triangle that shares an edge
2. **Edge**: Which edge of the neighbor triangle connects to the current face
   - Edge 0: V1 -> V2
   - Edge 1: V2 -> V3
   - Edge 2: V3 -> V1

**How is it Used?**

When computing adjacency for a walkmesh, the algorithm:

1. Looks at each edge of each triangle
2. Finds if any other triangle shares that same edge
3. If found, creates a BWMAdjacency object linking them
4. Stores this in the adjacency array using encoding: `faceIndex * 3 + edgeIndex`

For example, if face 5's edge 1 is adjacent to face 12's edge 2:

- The adjacency for face 5, edge 1 would be: BWMAdjacency(face12, edge2)
- This is stored at index 5*3+1 = 16 in the adjacency array
- The value stored is: 12*3+2 = 38 (encoding of face 12, edge 2)

**Bidirectional Linking:**

Adjacency is always bidirectional. If face A's edge connects to face B's edge, then:

- Face A's adjacency points to face B
- Face B's adjacency points to face A

This ensures pathfinding can traverse in both directions along shared edges.

---

This documentation provides a comprehensive overview of the KotOR BWM file format, focusing on clear explanations of what each component does and how it works, based on the canonical implementation in the Andastra codebase.
