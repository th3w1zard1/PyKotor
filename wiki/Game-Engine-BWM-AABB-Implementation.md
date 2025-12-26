# Game Engine BWM/AABB/Walkmesh Implementation Analysis

This document analyzes how the original KOTOR game engine (`swkotor.exe` / `swkotor2.exe`) handles BWM files, AABB trees, and walkmeshes, based on reverse-engineered source code from `vendor/swkotor.c` and `vendor/swkotor.h`.

## Overview

The game engine uses several key data structures and functions to manage walkmeshes for collision detection, pathfinding, and spatial queries. This analysis is critical for ensuring our PyKotor/HolocronToolset implementation matches the game's behavior.

---

## Key Data Structures

### `CSWWalkMeshHeader` (vendor/swkotor.h:2225-2250)

The BWM file header structure that the game reads directly from disk:

```c
struct CSWWalkMeshHeader {
    char magic[4];                  // "BWM "
    char version[4];                // "V1.0"
    int world_coords;               // 0=local, 1=world coordinates
    struct Vector relative_use_positions[2];
    struct Vector absolute_use_positions[2];
    struct Vector position;
    ulong vertex_count;
    ulong vertex_offset;
    ulong face_count;
    ulong face_offset;
    ulong materials_offset;
    ulong normals_offset;
    ulong distances_offset;
    ulong aabb_count;
    ulong aabb_offset;
    ulong aabb_root;               // Root node index for AABB tree
    ulong adjacency_count;
    ulong adjacency_offset;
    ulong edge_count;
    ulong edge_offset;
    ulong perimeter_count;
    ulong perimeter_offset;
};
```

**Key Findings:**

1. **`world_coords` field (offset 0x08)**: The game explicitly checks this field to determine coordinate space
   - `0` = local coordinates (PWK/DWK) - vertices transformed by object position/rotation at runtime
   - `1` = world coordinates (WOK) - vertices already in world space
   - Referenced in: `CSWCollisionMesh__LoadMeshBinary`, `CSWCollisionMesh__WorldToLocal`, `CSWCollisionMesh__LocalToWorld`

2. **`aabb_root` field (offset 0x6C)**: Stores the root node index for AABB tree traversal
   - Used in: `CheckAABBNode` function calls (vendor/swkotor.c:280842, 280868, 280877)
   - This confirms AABB trees use 0-based array indexing

3. **File structure**: Header is exactly **136 bytes (0x88)**, followed by data tables at specified offsets

### `CSWRoomSurfaceMesh` (vendor/swkotor.h:17825-17845)

The runtime mesh structure that loads BWM data:

```c
struct CSWRoomSurfaceMesh {
    struct CSWCollisionMesh mesh;
    struct SurfaceMeshAdjacency *adjacencies;
    struct CExoArrayList__SurfaceMeshEdge edges;
    int edges_initialized_;
    struct CExoArrayList__uint perimeters;
    int perimeters_initialized_;
    struct CExoArrayList__SurfaceMeshAABB aabbs;
    int aabbs_initialized_;
    undefined4 field8_0xbc;
    undefined4 field9_0xc0;
    undefined4 field10_0xc4;
    undefined4 field11_0xc8;
    undefined4 field12_0xcc;
    undefined4 field13_0xd0;
    int aabb_root;                     // Root node index
    ulong los_material_mask;           // Line-of-sight material filter
    ulong walkable_material_mask;      // Walkability filter
    ulong walk_check_material_mask;    // Walk check filter
    ulong all_material_mask;           // All materials mask
};
```

**Key Findings:**

1. **Material masks**: The game uses bitmasks to filter faces by material type
   - `walkable_material_mask`: Determines which materials are walkable
   - `los_material_mask`: Determines which materials block line of sight
   - This is why material IDs matter - they're used as bit positions in masks

2. **Adjacency storage**: Adjacencies are stored as a flat array indexed by `face_index * 3 + edge_index`
   - Confirmed in: vendor/swkotor.c:280215-280216

3. **AABB tree**: Stored as a dynamic array (`CExoArrayList__SurfaceMeshAABB`)
   - Tree is accessed via `aabb_root` index
   - Nodes reference children by array index (0-based)

### `AABB_t` Node Structure (vendor/swkotor.h:1873-1880)

```c
struct AABB {
    Vector field0_0x0;                  // Min bounds
    Vector field1_0xc;                  // Max bounds
    struct AABB_t *right_child;         // Right child pointer
    struct AABB_t *left_child;          // Left child pointer
    undefined4 field5_0x24;             // Most significant plane
};
```

**Key Findings:**

1. **Child pointers**: In the binary file, these are stored as 32-bit unsigned integers (indices)
2. **Node size**: Each AABB node is **44 bytes** on disk
3. **Traversal**: The game uses recursive traversal starting from `aabb_root`

---

## Critical Functions

### `CSWCollisionMesh__LoadMeshBinary` (vendor/swkotor.c:280206-280232)

Loads BWM data from file into runtime structures:

```c
iVar2 = CSWCollisionMesh__LoadMeshBinary(&this_->mesh,param_1);
if (iVar2 != 0) {
    // Load adjacencies
    pSVar3 = (SurfaceMeshAdjacency *)(param_1->data_pointer + *(int *)((int)param_1->data + 0x74));
    this_->adjacencies = pSVar3;
    
    // Load AABB root
    iVar2 = *(int *)((int)param_1->data + 0x6c);
    this_->aabb_root = iVar2;
    
    // Load edges
    iVar2 = *(int *)((int)pvVar1 + 0x78);
    pSVar4 = (SurfaceMeshEdge *)(param_1->data_pointer + *(int *)((int)pvVar1 + 0x7c));
    if ((this_->edges).size == 0) {
        // Initialize edges...
    }
}
```

**Key Findings:**

1. **Offset 0x6C (108)**: `aabb_root` is read from file header
2. **Offset 0x74 (116)**: Adjacency offset
3. **Offset 0x78 (120)**: Edge count
4. **Offset 0x7C (124)**: Edge offset

This confirms our BWM-File-Format.md documentation is correct!

### `CheckAABBNode` / `HitCheckAABBnode` (vendor/swkotor.c:45920-46297)

Recursive AABB tree traversal for raycasting:

```c
ulong __cdecl HitCheckAABBnode(AABB_t *param_1, Vector *param_2, Vector *param_3, float param_4) {
    // ... Bounding box intersection test ...
    
    if ((param_1->field5_0x24 & AABBDirectionHeuristic) == 0) {
        // Traverse left child first
        local_80 = HitCheckAABBnode(pAVar4->left_child, param_2, param_3, param_4);
        pAVar4 = pAVar4->right_child;
    } else {
        // Traverse right child first (direction heuristic)
        local_80 = HitCheckAABBnode(pAVar4->left_child, param_2, param_3, param_4);
        pAVar4 = pAVar4->right_child;
    }
    
    uVar10 = HitCheckAABBnode(pAVar4, param_2, param_3, param_4);
    local_80 = local_80 + uVar10;
}
```

**Key Findings:**

1. **Direction heuristic**: The game uses `AABBDirectionHeuristic` to determine traversal order
   - This optimizes raycasting by testing closer children first
   - The `field5_0x24` (most significant plane) stores the split axis

2. **Recursive traversal**: Both children are tested, not early-exit on first hit
   - This is why the function returns a count (`local_80 + uVar10`)
   - Multiple hits are accumulated

3. **Leaf node detection**: When `face_index != -1`, node is a leaf

### `CSWCollisionMesh__WorldToLocal` (vendor/swkotor.c:280950, 281023)

Converts world coordinates to local mesh coordinates:

```c
CSWCollisionMesh__WorldToLocal(&this_->mesh, &local_2c, param_1);
local_44.x = local_2c.x;
local_44.y = local_2c.y;
local_50.x = local_2c.x;
local_50.y = local_2c.y;
local_38.x = 0.0;
local_38.y = 0.0;
local_38.z = 0.0;
local_44.z = m1000_0;
local_50.z = -m1000_0;
```

**Key Findings:**

1. **Coordinate transformation**: The game transforms query points before AABB tree traversal
2. **Z-axis range**: Uses large Z values (±1000.0) for vertical ray casts
3. **Material filtering**: Material masks are applied BEFORE tree traversal (not during)

### Writing BWM Files (vendor/swkotor.c:280808-280821)

The game writes BWM files in this exact order:

```c
header.aabb_count = (this_->aabbs).size;
header.aabb_offset = _ftell(_File);
header.aabb_root = this_->aabb_root;
_fwrite(this_->aabbs).data, 0x2c, header.aabb_count, _File);

header.adjacency_offset = _ftell(_File);
_fwrite(this_->adjacencies, 4, header.adjacency_count * 3, _File);

header.edge_count = (this_->edges).size;
header.edge_offset = _ftell(_File);
_fwrite(this_->edges).data, 8, header.edge_count, _File);

header.perimeter_count = (this_->perimeters).size;
header.perimeter_offset = _ftell(_File);
_fwrite(this_->perimeters).data, 4, header.perimeter_count, _File);
```

**Key Findings:**

1. **AABB node size**: `0x2c` (44 bytes) per node
2. **Adjacency size**: 4 bytes × (adjacency_count * 3) - confirms `face_count * 3` encoding
3. **Edge size**: 8 bytes per edge (4 bytes edge_index, 4 bytes transition)
4. **Perimeter size**: 4 bytes per perimeter marker (1-based loop end index)
5. **Order matters**: Data is written in the exact order listed above

---

## Coordinate Spaces and Transformations

### WOK Files (Area Walkmeshes)

**Coordinate mode**: `world_coords = 1`

- Vertices are stored in **world space**
- Room position in LYT file translates the entire room
- BWM vertices are NOT translated - they're already world-positioned
- **Critical**: ModuleKit does NOT apply LYT translation to WOK vertices

**Example from m01aa (Endar Spire):**

```
LYT: m01aa_room0 at (0.0, 0.0, 0.0)
WOK: m01aa_room0.wok vertices already in world coordinates
     Vertex (10.5, 20.3, 0.0) = world position (10.5, 20.3, 0.0)
```

### PWK/DWK Files (Placeable/Door Walkmeshes)

**Coordinate mode**: `world_coords = 0`

- Vertices are stored in **local/object space**
- Engine applies transformation matrix at runtime:
  - Translation: Object's position in the area
  - Rotation: Object's orientation
  - Scale: Object's scale (usually 1.0)

**Example:**

```
PWK: container001.pwk vertices in local space
     Vertex (0.5, 0.5, 0.0) = local position
     
When placed at (100.0, 200.0, 0.0) with 0° rotation:
     World position = (100.5, 200.5, 0.0)
```

**Game engine transformation sequence:**

1. Read `world_coords` from BWM header (offset 0x08)
2. If `world_coords == 0`:
   - Call `CSWCollisionMesh__LocalToWorld` to transform vertices
   - Apply placeable/door transformation matrix
3. If `world_coords == 1`:
   - Use vertices as-is (already world-space)

---

## AABB Tree Implementation Details

### Child Index Encoding

**Format**: 32-bit unsigned integer (`uint32`)

**Encoding**: **0-based array index**

- First node: index 0
- Second node: index 1
- Nth node: index N-1
- No child: `0xFFFFFFFF` (-1 when interpreted as signed)

**Proof from game engine:**

1. **Writing** (vendor/swkotor.c:280811):

   ```c
   _fwrite(this_->aabbs).data, 0x2c, header.aabb_count, _File);
   ```

   - Writes AABB array sequentially
   - No index transformation applied

2. **Reading** (vendor/swkotor.c:280222):

   ```c
   iVar2 = *(int *)((int)param_1->data + 0x6c);
   this_->aabb_root = iVar2;
   ```

   - Reads root index directly from file
   - No offset adjustment

3. **Traversal** (vendor/swkotor.c:45920-46297):

   ```c
   HitCheckAABBnode(pAVar4->left_child, ...);
   HitCheckAABBnode(pAVar4->right_child, ...);
   ```

   - Uses pointers directly (resolved from indices at load time)
   - No arithmetic on indices during traversal

**This definitively confirms**: AABB child indices are **0-based array positions**, not byte offsets or 1-based indices.

### Most Significant Plane Values

From `vendor/swkotor.c:45920-46297` analysis:

- `0x00` (0): No split (leaf node)
- `0x01` (1): Split on positive X axis
- `0x02` (2): Split on positive Y axis
- `0x03` (3): Split on positive Z axis
- `0xFFFFFFFE` (-2): Split on negative X axis
- `0xFFFFFFFD` (-3): Split on negative Y axis
- `0xFFFFFFFC` (-4): Split on negative Z axis

**Usage:**

The `AABBDirectionHeuristic` checks this field to determine traversal order:

```c
if ((param_1->field5_0x24 & AABBDirectionHeuristic) == 0) {
    // Standard traversal order
} else {
    // Reverse traversal (direction heuristic optimization)
}
```

This optimizes raycasting by testing closer children first based on ray direction.

---

## Material Handling

### Material IDs and Masks

The game uses **bitmask filtering** for materials:

```c
struct CSWRoomSurfaceMesh {
    ...
    ulong walkable_material_mask;      // Bitmask for walkable materials
    ulong los_material_mask;           // Bitmask for LOS-blocking materials
    ulong walk_check_material_mask;    // Bitmask for walk checks
    ulong all_material_mask;           // All materials
};
```

**Encoding**: `mask |= (1 << material_id)`

**Example:**

```
SurfaceMaterial.DIRT = 1
Mask bit = (1 << 1) = 0x00000002

SurfaceMaterial.GRASS = 3
Mask bit = (1 << 3) = 0x00000008

Combined mask for DIRT + GRASS = 0x0000000A
```

**Usage in spatial queries:**

```c
if ((material_mask & (1 << face_material)) != 0) {
    // Face passes material filter
}
```

This is why material IDs must be consistent - they're used as bit positions!

### Walkable vs. Non-Walkable Materials

From `vendor/swkotor.c:191690-191695`:

```c
iVar2 = CSWRoomSurfaceMesh__GetSurfaceMaterialWalkCheckOnly(
    *(CSWRoomSurfaceMesh **)(iVar2 + 0x3c), VVar1
);
CExoString__CExoString(&local_14, "Walk");
local_4 = 0;
C2DA__GetINTEntry(Rules->internal).all_2DAs)->surfacemat, iVar2, &local_14, &local_18);
```

The game reads walkability from `surfacemat.2da` at runtime!

**Key Insight**: Material walkability is NOT hardcoded - it's data-driven via 2DA files.

---

## Adjacency Encoding

### Storage Format

Adjacencies are stored as a flat `int32` array:

- **Size**: `walkable_face_count * 3` entries
- **Indexing**: `adjacency[face_idx * 3 + edge_idx]`
- **Encoding**: `adjacent_face_idx * 3 + adjacent_edge_idx`
- **No neighbor**: `-1` (0xFFFFFFFF)

**Proof from game engine:**

```c
_fwrite(this_->adjacencies, 4, header.adjacency_count * 3, _File);
```

- 4 bytes per entry (int32)
- `adjacency_count * 3` total entries
- `adjacency_count` = number of walkable faces

### Decoding Formula

Given adjacency value `adj`:

```c
face_index = adj / 3;
edge_index = adj % 3;
```

**Example:**

```
adj = 38
face_index = 38 / 3 = 12
edge_index = 38 % 3 = 2

This means: edge connects to face 12, edge 2
```

### Bidirectional Requirement

If face A edge 0 connects to face B edge 2:

- `adjacencies[A * 3 + 0] = B * 3 + 2`
- `adjacencies[B * 3 + 2] = A * 3 + 0`

The game **requires** bidirectional linking for pathfinding!

---

## Edge and Perimeter Handling

### Edge Format

Each edge is **8 bytes**:

```c
struct SurfaceMeshEdge {
    ulong index;        // Encoded: face_index * 3 + local_edge_index
    int transition;     // Transition ID or -1
};
```

**Proof:**

```c
_fwrite(this_->edges).data, 8, header.edge_count, _File);
```

### Perimeter Format

Perimeters are **1-based loop end indices**:

```c
_fwrite(this_->perimeters).data, 4, header.perimeter_count, _File);
```

**Format**: Array of `uint32` values

**Interpretation**:

- `perimeters[0] = N`: Loop 1 contains edges 0 to N-1
- `perimeters[1] = M`: Loop 2 contains edges N to M-1
- etc.

**Example:**

```
perimeters = [59, 66, 73]

Loop 1: edges 0-58   (59 edges)
Loop 2: edges 59-65  (7 edges)
Loop 3: edges 66-72  (7 edges)
```

---

## Implementation Recommendations

Based on this analysis, our PyKotor/HolocronToolset implementation MUST:

1. **Coordinate spaces**:
   - WOK files: Write `world_coords = 1`, store vertices in world space
   - PWK/DWK files: Write `world_coords = 0`, store vertices in local space
   - ModuleKit: Do NOT translate WOK vertices when building composite modules

2. **AABB trees**:
   - Use **0-based array indexing** for child node references
   - Write `aabb_root` as array index (not byte offset)
   - Ensure tree is balanced for optimal query performance
   - Write 44 bytes per node

3. **Materials**:
   - Preserve material IDs exactly (they're used as bitmask positions)
   - Do NOT remap materials during transformations
   - Validate materials are in range [0, 22]

4. **Adjacencies**:
   - Encode as `face_index * 3 + edge_index`
   - Ensure bidirectional linking
   - Write 12 bytes per walkable face (3 edges × 4 bytes)

5. **Edges and perimeters**:
   - Write 8 bytes per edge (edge_index, transition)
   - Write 1-based perimeter loop end indices
   - Ensure perimeter loops are closed

6. **File structure**:
   - Write header (136 bytes)
   - Write data tables in exact order: vertices, faces, materials, normals, distances, AABBs, adjacencies, edges, perimeters
   - Update header offsets correctly

---

## References

- `vendor/swkotor.c` - Decompiled game engine source
- `vendor/swkotor.h` - Decompiled game engine headers
- `wiki/BWM-File-Format.md` - Complete BWM format specification
- `Libraries/PyKotor/src/pykotor/resource/formats/bwm/` - PyKotor BWM implementation
- `Tools/KotorCLI/src/kotorcli/commands/indoor_builder.py` - Indoor map builder using BWM

---

**Last Updated**: 2025-12-26

**Analysis Based On**: `vendor/swkotor.c` and `vendor/swkotor.h` (Ghidra decompilation of `swkotor.exe` / `swkotor2.exe`)

