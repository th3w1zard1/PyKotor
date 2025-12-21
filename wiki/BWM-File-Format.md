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
- [Runtime Model](#runtime-model)
  - [BWM Class](#bwm-class)
  - [BWMFace Class](#bwmface-class)
  - [BWMEdge Class](#bwmedge-class)
  - [BWMNodeAABB Class](#bwmnodeaabb-class)
  - [BWMAdjacency Class](#bwmadjacency-class)
- [Implementation Approaches and Differences](#implementation-approaches-and-differences)
  - [AABB Tree Child Index Encoding](#aabb-tree-child-index-encoding)
  - [AABB Tree Reading Strategies](#aabb-tree-reading-strategies)
  - [Room Link Methodologies](#room-link-methodologies)

---

## File Structure Overview

The binary format uses a header-based structure where offsets point to various data tables, allowing efficient random access to vertices, faces, materials, and acceleration structures. This design enables the engine to load only necessary portions of large walkmeshes or stream data as needed.

**Total header size**: 136 bytes (0x88)

The file structure is:

1. **Header** (8 bytes): Magic "BWM " and version "V1.0"
2. **Walkmesh Properties** (52 bytes): Type, hook vectors, position
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
| type                    | uint32    | 8 (0x08)   | 4    | Walkmesh type (0=PWK/DWK, 1=WOK/Area)                            |
| Relative Use position 1 | float32| 12 (0x0C)   | 12   | Relative use hook position 1 (x, y, z)                           |
| Relative Use position 2 | float32| 24 (0x18)   | 12   | Relative use hook position 2 (x, y, z)                           |
| Absolute Use position 1 | float32| 36 (0x24)   | 12   | Absolute use hook position 1 (x, y, z)                           |
| Absolute Use position 2 | float32| 48 (0x30)   | 12   | Absolute use hook position 2 (x, y, z)                           |
| position                | float32| 60 (0x3C)   | 12   | Walkmesh position offset (x, y, z)                               |

**Walkmesh Types:**

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

## Implementation Approaches and Differences

This section describes how different implementations handle various aspects of the BWM file format, particularly focusing on AABB tree encoding and reading/writing strategies. Understanding these differences can help when working with files generated by different tools or when implementing BWM support in new projects.

### AABB Tree Child Index Encoding

One of the critical aspects of BWM file format compatibility is how AABB tree child indices are encoded. The BWM format stores AABB nodes sequentially in an array, and parent nodes reference their children using indices into this array.

#### Specification

The game engine (`swkotor.exe` / `swkotor2.exe`) expects **0-based array indices** for AABB child nodes. This means:

- The first node in the array is at index 0
- The second node is at index 1
- The Nth node is at index N-1
- When a parent node references its left child, it stores the 0-based position of that child in the array

**Binary Format**: Child indices are stored as 32-bit unsigned integers (`uint32`) at offsets 0x24 (left child) and 0x28 (right child) within each AABB node. The value `0xFFFFFFFF` indicates no child (leaf node or missing child).

#### Why This Matters

Child indices must be encoded correctly for the game engine to properly traverse the AABB tree. Incorrect encoding (e.g., using 1-based indexing instead of 0-based) will cause the engine to:

1. Read an incorrect index from the file
2. Access the wrong node in the array when traversing the tree
3. Follow incorrect paths through the tree structure
4. Fail to find walkable triangles for spatial queries
5. Result in characters being unable to move or interact with the walkmesh

#### Implementation Approaches

Different projects have taken different approaches to handling AABB trees:

##### Game Engine (swkotor.exe / swkotor2.exe)

**Strategy**: Reads AABB data directly from file, uses indices as 0-based array offsets.

**Evidence**: Reverse engineering via Ghidra analysis shows the game engine writes child indices as raw 32-bit integers without offset calculation, confirming 0-based encoding. The BWM writing function writes AABB nodes sequentially with child indices stored directly as array positions.

**Reference**: This is the canonical implementation that defines the correct format specification.

##### reone (C++ Engine Rewrite)

**Strategy**: Reads AABB data from file, interprets child indices as 0-based array indices.

**Implementation Approach**: Two-pass reading - first reads all nodes into memory, then links children using the stored indices as direct array references. This matches the game engine's behavior and is based on reverse engineering of the original executables.

**Key Code Pattern**:

```cpp
// Reads child indices directly from file
uint32_t childIdx1 = _bwm.readUint32();
uint32_t childIdx2 = _bwm.readUint32();

// Uses indices directly as array indices (0-based)
aabbs[i]->left = aabbs[childIdx1];   // Direct array access
aabbs[i]->right = aabbs[childIdx2];  // Direct array access
```

##### xoreos (C++ Engine Rewrite)

**Strategy**: Reads AABB data from file, interprets child indices as byte offset multipliers.

**Implementation Approach**: Multiplies indices by the node size (44 bytes) to compute byte offsets. While this is a different interpretation (byte offset multiplier vs. array index), it still requires indices to be 0-based for correct calculation. If indices were 1-based, the multiplication would produce incorrect offsets.

**Key Code Pattern**:

```cpp
const uint32_t leftOffset = stream.readUint32LE();
const uint32_t rightOffset = stream.readUint32LE();

// Multiplies indices by node size (44 bytes) to get byte offsets
const uint32_t AABBNodeSize = 44;
Common::AABBNode *leftNode = getAABB(stream, leftOffset * AABBNodeSize + AABBsOffset, ...);
Common::AABBNode *rightNode = getAABB(stream, rightOffset * AABBNodeSize + AABBsOffset, ...);
```

##### kotorblender (Blender Add-on)

**Strategy**: Generates AABB tree during export, writes 0-based indices.

**Implementation Approach**: Builds AABB tree recursively during export, using Python list length (`len(aabb_tree)`) to compute child indices. Since Python lists use 0-based indexing and `len()` returns the current count (which equals the next index), this naturally produces 0-based indices.

**Key Code Pattern**:

```python
# Generation uses array length (0-based indexing)
node[6] = len(aabb_tree)  # Set left child to current tree length
generate_tree(aabb_tree, left_faces, depth + 1)

# Writing writes indices directly without modification
self.bwm.write_int32(aabb.child_idx1)  # 0-based index
self.bwm.write_int32(aabb.child_idx2)  # 0-based index
```

##### KOTORMax / KAurora (3DS Max Plugins)

**Strategy**: Export ASCII WOK format, which is compiled to binary by external tools.

**Implementation Details**:

- KOTORMax and KAurora are 3DS Max plugins based on BioWare's original export scripts
- They export ASCII WOK files (`.wok.ascii`) containing walkmesh data in text format
- ASCII files are compiled to binary BWM format by the game engine's compiler or separate compilation tools
- The `BuildAABBTreeNode` function in KAurora builds trees recursively by appending nodes to an array in order
- Since nodes are appended sequentially, their array positions are naturally 0-based
- Compiled output works correctly in-game, confirming proper 0-based encoding

**ASCII Format Structure**:

The ASCII WOK format exported by these tools includes:

- Vertex coordinates (in world space, converted from Max units)
- Face definitions with vertex indices and material IDs
- Room links/transitions (via vertex color encoding in KOTORMax's `do_aabb` function)
- AABB tree data (in KAurora, via `BuildAABBTreeNode` and `ExportAABBTree` functions)

**KAurora AABB Tree Generation**:

KAurora's `BuildAABBTreeNode` function recursively builds AABB trees by:

1. Calculating bounding box for current face list
2. If single face remains, creating a leaf node with face index
3. If multiple faces, creating an internal node with "-1" marker
4. Splitting faces along longest axis (X, Y, or Z)
5. Recursively building left and right subtrees
6. Appending nodes to array in order (naturally 0-based)

The ASCII format stores AABB nodes as text lines containing bounding box coordinates (6 floats: minX, minY, minZ, maxX, maxY, maxZ) followed by either a face index (leaf nodes) or "-1" (internal nodes).

**Note**: These tools don't directly write binary child index encoding - the compilation process handles the binary conversion. The working in-game behavior confirms compiled output uses 0-based indices.

##### PyKotor / Andastra.Parsing

**Strategy**: Generates AABB trees on-the-fly when reading, writes 0-based indices when writing. Currently supports binary BWM format only.

**Key Design Choice**: PyKotor (and its C# port Andastra.Parsing) takes a different approach compared to most implementations:

- **Reader**: Does NOT read AABB data from files - always generates trees on-the-fly when `bwm.Aabbs()` is called
- **Writer**: Generates AABB tree and writes it to file using 0-based indices
- **Format Support**: Currently supports binary BWM format only (no ASCII WOK export/import)

**Reading Implementation**:

```python
# Reads AABB count and offset from header but does not read actual AABB data
_reader.ReadUInt32(); // aabb_count
_reader.ReadUInt32(); // aabb_offset
_reader.Skip(4);

# AABB tree is generated on-demand
bwm.Aabbs()  # Generates tree using BWM._AabbsRec()
```

**Writing Implementation**:

```python
# Finds child indices in array
left_idx = next(i for i, a in enumerate(aabbs) if a is aabb.left)  # 0-based
right_idx = next(i for i, a in enumerate(aabbs) if a is aabb.right)  # 0-based

# Writes indices directly
writer.write_uint32(left_idx)   # 0-based index
writer.write_uint32(right_idx)  # 0-based index
```

**Rationale**: Generating trees on-the-fly ensures structural correctness and simplifies the reader code (no need to parse binary AABB structure and link child nodes). The trade-off is that the original tree structure from files is not preserved, and trees must be regenerated each time (O(n log n) complexity, which is acceptable for typical walkmesh sizes).

**Important**: Even though the reader generates trees, the writer must still produce files compatible with the game engine and other tools. Therefore, PyKotor/Andastra.Parsing writes 0-based indices to match the game engine's expectations.

**Future ASCII Support**: PyKotor could be extended to support ASCII WOK format (similar to KOTORMax/KAurora) by implementing `BWMBinaryWriter.write_ascii()` and `BWMBinaryReader.read_ascii()` methods. The ASCII format would export:

- Vertex coordinates as text
- Face definitions with vertex indices and material IDs
- Room links/transitions (if supported)
- AABB tree data as text lines (bounding box coordinates + face index or "-1" marker)

Such an implementation would follow the same patterns as PyKotor's existing `MDLAsciiWriter` and `MDLAsciiReader` classes, matching the ASCII format structure used by KOTORMax and KAurora.

#### Comparison Summary

| Implementation | Reads AABB from File? | Generates AABB? | Child Index Encoding | Notes |
|---------------|----------------------|-----------------|---------------------|--------|
| **swkotor.exe / swkotor2.exe** | ✅ Yes | ❌ No | 0-based array indices | Reference implementation |
| **reone** | ✅ Yes | ❌ No | 0-based array indices | Matches game engine behavior |
| **xoreos** | ✅ Yes | ❌ No | 0-based (as byte offset multiplier) | Different interpretation, same result |
| **kotorblender** | ✅ Yes | ✅ Yes (on export) | 0-based array indices | Generates during export, reads from files |
| **KOTORMax** | ⚠️ N/A (exports ASCII) | ✅ Yes (ASCII export) | 0-based (compiled output) | Compilation handles binary conversion |
| **KAurora** | ✅ Yes (can process binary) | ✅ Yes (generates ASCII) | 0-based (compiled output) | Can process/regenerate BWM files |
| **PyKotor/Andastra.Parsing Reader** | ❌ No | ✅ Yes (on demand) | N/A (generates, doesn't read) | Non-standard approach, generates on-the-fly; binary format only |
| **PyKotor/Andastra.Parsing Writer** | ❌ No | ✅ Yes | 0-based array indices | Must match game engine format; binary format only |

### AABB Tree Reading Strategies

When implementing BWM file support, there are two main approaches for handling AABB trees:

#### Reading from Files (Standard Approach)

**Advantages**:

- Preserves original tree structure from source files
- Faster loading for large walkmeshes (no tree construction overhead)
- Matches how the game engine and most tools work
- Enables format verification and round-trip testing

**Disadvantages**:

- Must correctly parse binary AABB structure
- Must handle child index linking correctly
- More complex reader code

**Used by**: reone, xoreos, kotorblender, game engine

#### Generating On-the-Fly (Alternative Approach)

**Advantages**:

- Always structurally correct trees (no dependency on file format encoding)
- Simpler reader code (no AABB parsing needed)
- Immune to file format bugs in AABB encoding

**Disadvantages**:

- Original tree structure is lost (cannot preserve exact tree from files)
- Must regenerate every time (O(n log n) complexity)
- Slightly slower loading for large walkmeshes
- Non-standard approach (fewer implementations use this)

**Used by**: PyKotor, Andastra.Parsing

**Note**: Even when using generation for reading, the writer must still produce files with correct encoding (0-based indices) because files may be consumed by other tools or the game engine.

#### Recommendations for Implementers

1. **For Writers**: Always use 0-based array indices for AABB child nodes. This matches the game engine's expectations and ensures compatibility with all tools.

2. **For Readers**: You have two choices:
   - **Standard Approach**: Read AABB data from files (like reone, xoreos, kotorblender). This preserves the original tree structure and is faster for large walkmeshes.
   - **Generation Approach**: Generate trees on-the-fly (like PyKotor). This ensures structural correctness and simplifies code, but loses the original tree structure and requires regeneration each time.

3. **Index Interpretation**: When reading child indices, treat them as 0-based array positions. While xoreos multiplies by node size to compute byte offsets, this still requires 0-based indices for correct calculation.

4. **Testing**: Test your implementation with files generated by different tools (game engine, kotorblender, etc.) to ensure compatibility. Verify that spatial queries (raycasting, point-in-triangle tests) work correctly.

### Room Link Methodologies

Different tools use different approaches for defining room links (transitions between rooms):

#### KOTORMax: Edge Selection

- **Method**: Users select edges directly in 3DS Max edge selection mode
- **Tool**: "Room Link Editor" (`kx_roomlinker.ms`)
- **Storage**: Edge selection converted to vertex color data in map channel (`kx_roomlinkChannel`)
- **Encoding**: Green channel stores room number (value = 100 + room_number)
- **Advantages**: Visual edge selection is intuitive and user-friendly
- **Workflow**: Select edges → Pick room number → Apply → Tool handles encoding

#### KotorBlender: Vertex Painting

- **Method**: Users manually paint vertex colors using Blender's vertex paint mode
- **Storage**: Vertex colors with green channel encoding room numbers
- **Encoding**: Red=0, Blue=0, Green=(100 + room_number)
- **Workflow**: Switch to vertex paint → Select color based on room number → Paint vertices of connecting edges
- **Considerations**: Requires understanding encoding scheme, more manual work, error-prone if vertices are painted incorrectly

#### Indoor Map Builder (HolocronToolset)

- **Method**: Programmatic module building without manual vertex painting
- **Approach**: Uses proximity-based hook matching to automatically connect rooms
- **Workflow**: Automated - no manual room link definition required
- **Advantages**: No manual work, consistent results, suitable for procedural generation

**Note**: These different methodologies all ultimately store the same data (room transition indices in the BWM file), but use different user interfaces and workflows. Understanding these differences helps when working with files from different tools or when choosing a workflow for module creation.

---

This documentation provides a comprehensive overview of the KotOR BWM file format, focusing on clear explanations of what each component does and how it works, based on the canonical implementation in the Andastra codebase.
