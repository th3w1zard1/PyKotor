# ASCII Walkmesh Format Specification

This document describes the ASCII walkmesh format used by both KotOR I and KotOR II: The Sith Lords. The format is a text-based representation of collision meshes that can be exported from and imported into the Aurora toolset.

## Overview

ASCII walkmesh files (typically with `.wok` extension) contain collision geometry for game areas. The format uses a hierarchical block structure similar to ASCII model files, with a single "node aabb" block containing all walkmesh data.

The format is parsed by the game engine's `LoadMeshText` function:
- **KotOR I**: `CSWRoomSurfaceMesh::LoadMeshText` at `0x00582d70` in `swkotor.exe`
- **KotOR II**: `FUN_00577860` at `0x00577860` in `swkotor2.exe`

Both implementations are functionally identical, parsing the same format structure and applying the same logic.

## Format Structure

### Grammar

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

### Example File

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

## Parsing Process

The engine parses ASCII walkmesh files line-by-line using a helper function `LoadMeshString`:
- **KotOR I**: `CSWCollisionMesh::LoadMeshString` at `0x005968a0`
- **KotOR II**: `FUN_005573e0` at `0x005573e0`

Both implementations read up to 256 bytes per line, stopping at newline characters (0x0A) and null-terminating the result.

### Line Reading

```c
// Both K1 and TSL use identical logic
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

### Whitespace Handling

Leading whitespace (spaces and tabs) is stripped before keyword detection:

```c
// Both K1 and TSL: lines 131-135
char* src = line_buffer;
while (*src == 0x20) {  // Space character
    src++;
}
// Process keyword from 'src' position
```

## Field Specifications

### 1. Node Block

The walkmesh must start with `"node aabb"` and end with `"endnode"`.

**Detection Logic**:
```c
// Both K1 and TSL: lines 136-145
if (strncmp(src, "node", 4) == 0) {
    src += 4;
    if (strncmp(src, " aabb", 5) == 0) {
        in_node_block = 1;
    }
}

// End detection: lines 146-149
if (strncmp(src, "endnode", 7) == 0) {
    in_node_block = 0;
}
```

### 2. Position Field

**Format**: `"position" SPACE float SPACE float SPACE float`

**Parsing**:
```c
// Both K1 and TSL: lines 151-160
float x, y, z;
sscanf(src, "position %f %f %f", &x, &y, &z);
mesh->position.x = x;
mesh->position.y = y;
mesh->position.z = z;
```

**Storage**: Stored as a Vector3 in the mesh structure (offset 0x2C).

### 3. Orientation Field

**Format**: `"orientation" SPACE float SPACE float SPACE float SPACE float`

**Parsing**:
```c
// Both K1 and TSL: lines 162-185
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

### 4. Vertices Block

**Format**:
```
"verts" SPACE integer NEWLINE
(float SPACE float SPACE float NEWLINE)+
```

**Parsing**:
```c
// Both K1 and TSL: lines 187-230
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

**Coordinate Quantization**: The engine performs a quantization check on vertex coordinates (lines 206-225), but this appears to be for binary format optimization. For ASCII parsing, coordinates are read directly as floats.

### 5. Faces Block

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
// Both K1 and TSL: lines 232-333
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
// Both K1 and TSL: lines 255-327
// K1 uses: C2DA::GetINTEntry at 0x0041d630
// TSL uses: FUN_0041d630 at 0x0041d630 (same function, different name)
int walkable_count = 0;
int unwalkable_count = 0;
uint32_t* walkable_indices = malloc(face_count * 4);
uint32_t* unwalkable_indices = malloc(face_count * 4);

for (int i = 0; i < face_count; i++) {
    int walk_value;
    #ifdef KOTOR_1
        C2DA::GetINTEntry(surfacemat_2da, material_ids[i], "Walk", &walk_value);
    #else  // TSL
        FUN_0041d630(surfacemat_2da, material_ids[i], "Walk", &walk_value);
    #endif
    
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
// Both K1 and TSL: lines 289-327
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

### 6. AABB Block

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
// Both K1 and TSL: lines 334-697
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
    
    // Min/Max Swapping (lines 373-384)
    if (max_x < min_x) { float tmp = min_x; min_x = max_x; max_x = tmp; }
    if (max_y < min_y) { float tmp = min_y; min_y = max_y; max_y = tmp; }
    if (max_z < min_z) { float tmp = min_z; min_z = max_z; max_z = tmp; }
    
    // Epsilon Expansion (lines 438-450)
    const float EPSILON = 0.01f;  // 0x3C23D70A
    min_x -= EPSILON;
    min_y -= EPSILON;
    min_z -= EPSILON;
    max_x += EPSILON;
    max_y += EPSILON;
    max_z += EPSILON;
    
    // Face Index Mapping (lines 367-371)
    // Maps face indices to reordered array (walkable first, unwalkable second)
    if (face_index != -1) {
        // Map to correct position in reordered face array
        // (Implementation details omitted for brevity)
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

## Data Structures

### WalkmeshFace

```c
struct WalkmeshFace {
    uint32_t vertex_1;  // Offset 0x00
    uint32_t vertex_2;  // Offset 0x04
    uint32_t vertex_3;  // Offset 0x08
};  // 12 bytes total
```

### CSWCollisionMesh

The base collision mesh structure (136 bytes) containing:
- Position (Vector3, offset 0x2C)
- Orientation (Quaternion, offset 0x38)
- Vertex array (Vector3*, offset 0x54)
- Face indices array (WalkmeshFace*, offset 0x60)
- Material IDs array (uint32_t*, offset 0x64)
- `adjacency_count` (uint32_t, offset 0x5C) - Number of walkable faces

### CSWRoomSurfaceMesh

Extended structure (232 bytes) containing the base mesh plus:
- Adjacency table
- Edge list
- Perimeter data
- AABB tree (`aabbs` array)
- `aabb_root` (int, offset 0xD4) - Root node index
- Material masks

## Implementation Notes

### Critical Requirements

1. **8-Integer Face Format**: The format reads 8 integers per face, but only stores vertex indices (3 ints) and material ID (1 int). The adjacency integers (4 ints) are parsed but not stored in the face structure.

2. **Walkable/Unwalkable Separation**: Faces **MUST** be separated into walkable and unwalkable groups, with walkable faces stored first. This ordering is critical for adjacency table indexing in binary format.

3. **Material Lookup**: Walkability is determined by looking up the material ID in the `surfacemat.2DA` table using the "Walk" column. A value of 0 means unwalkable, non-zero means walkable.

4. **AABB Tree Construction**: The AABB tree construction is complex. For initial implementation, parsing AABB nodes and storing them is sufficient. Full tree reconstruction can be deferred to the writer, which regenerates AABB trees from geometry.

5. **Epsilon Expansion**: Apply 0.01 epsilon to all AABB bounding box coordinates to match engine behavior.

6. **Face Index Mapping**: When parsing AABB nodes, map face indices to the reordered face array (walkable first, unwalkable second).

### Error Handling

The engine handles errors by:
- Calling `LoadDefaultMesh` vtable function on parse errors
- Returning `1` on error (not `0`)
- Freeing all allocated memory on error

### Line Buffer

- **Buffer Size**: 256 bytes (0x100)
- **Behavior**: Stops reading at newline (0x0A) or buffer limit
- **Null Termination**: Adds null terminator after reading line

### Whitespace

- **Leading Whitespace**: Stripped before keyword detection
- **Inter-Token Whitespace**: Required between values (handled by `sscanf`)
- **Newlines**: Required after each line (0x0A, consumed by `LoadMeshString`)

## Engine References

### KotOR I (swkotor.exe)

- `0x00582d70` - `CSWRoomSurfaceMesh::LoadMeshText` (main ASCII parser, 3882 bytes)
- `0x005968a0` - `CSWCollisionMesh::LoadMeshString` (line reader, 95 bytes)
- `0x00596670` - `CSWCollisionMesh::LoadMesh` (entry point, detects ASCII vs binary)
- `0x0041d630` - `C2DA::GetINTEntry` (material lookup)

### KotOR II / TSL (swkotor2.exe)

- `0x00577860` - `FUN_00577860` (main ASCII parser, equivalent to LoadMeshText, 3882 bytes)
- `0x005573e0` - `FUN_005573e0` (line reader, equivalent to LoadMeshString, 95 bytes)
- `0x0041d630` - `FUN_0041d630` (material lookup, equivalent to C2DA::GetINTEntry)

## Notes

1. The ASCII format is primarily a development/toolset format, not typically used in-game
2. Binary format (BWM) is the runtime format used by the game
3. ASCII format enables human-readable editing and debugging
4. The engine supports both formats, detecting automatically in `LoadMesh`
5. Round-trip conversion (ASCII → BWM → ASCII) may not preserve exact field ordering, but should preserve data
