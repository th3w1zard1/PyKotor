# ASCII Walkmesh Format - Complete Engine Analysis

This document provides a comprehensive and exhaustive analysis of the ASCII walkmesh parsing functionality as implemented in both **KotOR I (swkotor.exe)** and **KotOR II / TSL (swkotor2.exe)**. The analysis is based on reverse-engineering both game engines' ASCII walkmesh parsing functions.

## Reference Implementations

### KotOR I (swkotor.exe)

**Function**: `CSWRoomSurfaceMesh::LoadMeshText`  
**Address**: `0x00582d70` in `swkotor.exe`  
**Size**: 3882 bytes (715 lines of decompiled code)  
**Signature**: `undefined4 __thiscall CSWRoomSurfaceMesh::LoadMeshText(CSWRoomSurfaceMesh *this, byte *param_1, ulong param_2)`

**Called From**: `CSWCollisionMesh::LoadMesh` (0x00596670) - entry point that detects ASCII vs binary format

### KotOR II / TSL (swkotor2.exe)

**Function**: `FUN_00577860` (equivalent to LoadMeshText)  
**Address**: `0x00577860` in `swkotor2.exe`  
**Size**: 3882 bytes (650 lines of decompiled code)  
**Signature**: `undefined4 __thiscall FUN_00577860(void *this, float param_1, float param_2)`

**Note**: Functionally identical to K1 implementation with the same parsing logic, format structure, and behavior.

## Helper Functions

### LoadMeshString

**KotOR I (swkotor.exe)**:
- **Function**: `CSWCollisionMesh::LoadMeshString`  
- **Address**: `0x005968a0` in `swkotor.exe`  
- **Size**: 95 bytes (27 lines of decompiled code)  
- **Signature**: `undefined4 __stdcall LoadMeshString(byte **param_1, ulong *param_2, byte *param_3, ulong param_4)`

**KotOR II / TSL (swkotor2.exe)**:
- **Function**: `FUN_005573e0` (equivalent to LoadMeshString)
- **Address**: `0x005573e0` in `swkotor2.exe`
- **Size**: 95 bytes (26 lines of decompiled code)
- **Signature**: `undefined4 __stdcall FUN_005573e0(int *param_1, int *param_2, int param_3, uint param_4)`

**Purpose**: Reads a single line from input data into a buffer. Both implementations are functionally identical.

**Parameters**:
- `param_1` (byte**): Pointer to current position in input data (updated on return)
- `param_2` (ulong*): Pointer to remaining bytes count (updated on return)
- `param_3` (byte*): Output buffer (256 bytes)
- `param_4` (ulong): Buffer size (256 bytes = 0x100)

**Return Value**:
- `1`: Success - line read
- `0`: Failure - EOF or buffer full

**Implementation Logic** (lines 13-25):
```c
do {
    uVar2 = uVar2 + 1;
    param_3[uVar2] = **param_1;
    *param_1 = *param_1 + 1;
    uVar1 = *param_2;
    *param_2 = uVar1 - 1;
    if ((param_4 - 1 <= uVar2) || (param_3[uVar2] == 10)) break;  // Newline (0x0A)
} while (uVar1 - 1 != 0);

if (param_4 <= uVar2) {
    return 0;  // Buffer overflow
}
param_3[uVar2] = 0;  // Null-terminate
return 1;
```

**Behavior**:
- Reads characters one-by-one until newline (0x0A) or buffer limit reached
- Advances input pointer and decrements remaining count
- Null-terminates the output string
- Stops on newline (does not include newline in output)

## ASCII Format Structure

The ASCII walkmesh format uses a hierarchical block structure similar to ASCII MDL files. The format consists of a single "node aabb" block containing all walkmesh data.

### Format Grammar

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

### Keyword Detection

The engine uses `_strncmp` (case-sensitive string comparison) to detect keywords:

- `"node"` (4 chars) - Checks for node block start
- `" aabb"` (5 chars) - Checks for "node aabb" variant
- `"endnode"` (7 chars) - Marks end of node block
- `"position"` (8 chars) - Position field
- `"orientation"` (11 chars = 0xB) - Orientation field
- `"verts"` (5 chars) - Vertices block
- `"faces"` (5 chars) - Faces block
- `"aabb"` (4 chars) - AABB block

### Whitespace Handling

Leading whitespace (spaces and tabs) is stripped before keyword detection (engine lines 131-135):
```c
bVar2 = *_Src;
pbVar21 = _Src;
while (bVar2 == 0x20) {  // Space
    pbVar32 = pbVar21 + 1;
    pbVar21 = pbVar21 + 1;
    bVar2 = *pbVar32;
}
```

## Field Parsing Details

### 1. Node Block Detection

**Lines 136-145**: Detects "node" keyword and checks for "node aabb" variant.

```c
iVar10 = _strncmp((char *)pbVar21, "node", 4);
if (iVar10 == 0) {
    pbVar21 = pbVar21 + 4;
    local_d8 = iVar10;
    iVar10 = _strncmp((char *)pbVar21, " aabb", 5);
    if (iVar10 == 0) {
        local_d8 = 1;
        local_b4 = 1;  // Flag: in AABB node block
    }
}
```

**State Variables**:
- `local_d8`: Flag indicating if inside "node aabb" block (1 = inside, 0 = outside)
- `local_b4`: Flag indicating AABB node was detected (used for post-processing)

**End Node Detection** (lines 146-149):
```c
iVar10 = _strncmp((char *)pbVar21, "endnode", 7);
if (iVar10 == 0) {
    local_d8 = 0;  // Exit node block
}
```

### 2. Position Field

**Lines 151-160**: Parses position as 3 floats.

**Format**: `"position" SPACE float SPACE float SPACE float`

**Parser**: `_sscanf((char *)pbVar21, "%f %f %f")`

**Storage**:
```c
(this->mesh).position.x = local_b8;
(this->mesh).position.y = local_b0;
(this->mesh).position.z = local_ac;
```

**Structure**: Stored in `CSWCollisionMesh.mesh.position` (Vector3, offset 0x44)

### 3. Orientation Field

**Lines 162-185**: Parses orientation as quaternion (4 floats).

**Format**: `"orientation" SPACE float SPACE float SPACE float SPACE float`

**Parser**: `_sscanf((char *)pbVar21, "%f %f %f %f")`

**Special Case Handling** (lines 169-174):
- If all x, y, z components are zero (within float epsilon), creates identity quaternion (0, 0, 0, 1)
- Otherwise, constructs quaternion from axis-angle representation using `Quaternion::Quaternion(Vector, float)` constructor

**Identity Quaternion**:
```c
if (((local_c4 == float_0_0) && (local_c0 == float_0_0)) && (local_bc == float_0_0)) {
    local_6c.z = 0.0;
    local_6c.y = 0.0;
    local_6c.x = 0.0;
    local_6c.w = 1.0;
    FUN_00580700(this, &local_6c);  // Set orientation
}
```

**Axis-Angle Quaternion**:
```c
else {
    VVar7.y = local_c0;
    VVar7.x = local_c4;
    VVar7.z = local_bc;
    pQVar12 = Quaternion::Quaternion(&local_28, VVar7, local_78);  // Vector + angle
    (this->mesh).field7_0x38.w = pQVar12->w;
    (this->mesh).field7_0x38.x = pQVar12->x;
    (this->mesh).field7_0x38.y = pQVar12->y;
    (this->mesh).field7_0x38.z = pQVar12->z;
}
```

**Storage**: Stored in `CSWCollisionMesh.mesh.field7_0x38` (Quaternion, offset 0x38)

**Note**: The orientation field appears to use axis-angle representation (axis vector + angle), not direct xyzw quaternion. The engine converts this to a quaternion internally.

### 4. Vertices Block

**Lines 187-230**: Parses vertex array.

**Format**: 
```
"verts" SPACE integer NEWLINE
(float SPACE float SPACE float NEWLINE)+
```

**Parser**: 
- Count: `_sscanf((char *)(pbVar21 + 5), "%d")`
- Per vertex: `_sscanf((char *)_Src, "%f %f %f")`

**Allocation** (line 192):
```c
CSWCollisionMesh::SetVertexCount(&this->mesh, *puVar1);
```

**Memory Layout**: Vertices stored as array of Vector3 (12 bytes each: 3 floats)

**Coordinate Quantization Check** (lines 206-225):
The engine performs a quantization check on vertex coordinates. This appears to detect if coordinates are "snapped" to a grid and applies inverse quantization if detected.

**Quantization Logic**:
```c
// For X coordinate (similar for Y, Z not shown)
uVar23 = __ftol2((float10)*(float *)((int)&pVVar3->x + iVar10) * 
                 (float10)FLOAT_007494b0 + (float10)FLOAT_0073e9ac);
uVar19 = (uint)uVar23 & 0x800001ff;
bVar22 = (uVar23 & 0x800001ff) == 0;
if ((int)uVar19 < 0) {
    bVar22 = (uVar19 - 1 | 0xfffffe00) == 0xffffffff;
}
if (bVar22) {
    *(float *)((int)&pVVar3->x + iVar10) = (float)((int)(uint)uVar23 >> 9);
}
```

**Constants**:
- `FLOAT_007494b0`: Unknown float constant (needs analysis)
- `FLOAT_0073e9ac`: Unknown float constant (needs analysis)

**Note**: This quantization check is complex and appears to detect if coordinates were previously quantized during export. For ASCII parsing, we can read floats directly without this check, but should preserve the raw values.

### 5. Faces Block

**Lines 232-333**: Parses face array with material lookup and walkable/unwalkable separation.

**Format**:
```
"faces" SPACE integer NEWLINE
(integer SPACE integer SPACE integer SPACE integer SPACE integer SPACE integer SPACE integer SPACE integer NEWLINE)+
```

**Face Line Format** (line 251):
`"%d %d %d %d %d %d %d %d"` - **8 integers per face**

**Memory Allocation** (lines 238-239):
```c
local_12c = operator_new(*puVar1 * 0xc);      // 12 bytes per face (3 vertex indices)
_Memory = operator_new(*puVar1 << 2);          // 4 bytes per face (1 material ID)
```

**Reading Loop** (lines 241-253):
```c
iVar10 = 0;
if (0 < (int)*puVar1) {
    do {
        iVar13 = CSWCollisionMesh::LoadMeshString(&local_108, (ulong *)&local_110, _Src, 0x100);
        if (iVar13 == 0) {
            // Error: EOF before all faces read
            (*(code *)((this->mesh).vtable)->LoadDefaultMesh)();
            _free(_Src);
            ExceptionList = local_14;
            return 1;
        }
        _sscanf((char *)_Src, "%d %d %d %d %d %d %d %d");
        iVar10 = iVar10 + 1;
    } while (iVar10 < (int)*puVar1);
}
```

**8 Integer Format Analysis**:

Based on memory allocations and access patterns:
- **Integers 1-3**: Vertex indices (v1, v2, v3) - stored in `local_12c` (12 bytes = 3 uint32s)
- **Integers 4-7**: Adjacency data or other metadata - **IMPORTANT**: The engine reads these but they may be stored in temporary buffers or discarded. The decompiler doesn't show explicit storage, suggesting they may be parsed but not directly stored in face structures.
- **Integer 8**: Material ID - stored in `_Memory` (4 bytes = 1 uint32)

**Material Lookup and Walkable Separation** (lines 255-327):

The engine performs material lookup using 2DA table to determine walkability:

```c
// For each face (lines 263-287)
do {
    CExoString::CExoString(&local_74, "Walk");
    local_c = 0;
    C2DA::GetINTEntry(((Rules->internal).all_2DAs)->surfacemat,
                      *(int *)(local_88 + (int)local_148), &local_74, &local_a8);
    local_c = 0xffffffff;
    CExoString::~CExoString(&local_74);
    
    if (local_a8 == 0) {
        // Material is NOT walkable
        *local_148 = 0xffffffff;
        *(int *)(((int)local_114 - (int)local_118) + (int)local_148) = local_128;
        *(int *)((int)_Memory_01 + local_128 * 4) = local_dc;
        local_128 = local_128 + 1;  // Unwalkable count
    }
    else {
        // Material IS walkable
        *local_148 = local_10c;
        *(undefined4 *)(((int)local_114 - (int)local_118) + (int)local_148) = 0xffffffff;
        *(int *)((int)_Memory_00 + local_10c * 4) = local_dc;
        local_10c = local_10c + 1;  // Walkable count
    }
    local_dc = local_dc + 1;  // Original face index
    local_148 = local_148 + 1;
} while (local_dc < (int)*puVar1);
```

**Material Lookup Process**:
1. Creates CExoString with "Walk" value
2. Calls `C2DA::GetINTEntry(surfacemat.2DA, material_id, "Walk", &result)`
3. If `result == 0`: Material is **NOT walkable**
4. If `result != 0`: Material **IS walkable**

**Face Reordering** (lines 289-327):

Walkable faces are placed first in the final array, followed by unwalkable faces:

```c
// Copy walkable faces first (lines 289-305)
iVar10 = 0;
if (0 < (int)local_10c) {
    local_148 = (ulong *)0x0;
    do {
        *(undefined4 *)((int)&((this->mesh).face_indices)->vertex_1 + (int)local_148) =
             *(undefined4 *)((int)local_12c + *(int *)((int)_Memory_00 + iVar10 * 4) * 0xc);
        *(undefined4 *)((int)&((this->mesh).face_indices)->vertex_2 + (int)local_148) =
             *(undefined4 *)((int)local_12c + *(int *)((int)_Memory_00 + iVar10 * 4) * 0xc + 4);
        *(undefined4 *)((int)&((this->mesh).face_indices)->vertex_3 + (int)local_148) =
             *(undefined4 *)((int)local_12c + *(int *)((int)_Memory_00 + iVar10 * 4) * 0xc + 8);
        (this->mesh).materials[iVar10] =
             *(ulong *)((int)_Memory + *(int *)((int)_Memory_00 + iVar10 * 4) * 4);
        iVar10 = iVar10 + 1;
        local_148 = (ulong *)((int)local_148 + 0xc);
    } while (iVar10 < (int)local_10c);
}

// Copy unwalkable faces after walkable faces (lines 307-327)
iVar10 = 0;
if (0 < local_128) {
    local_140 = local_10c * 4;
    iVar13 = local_10c * 0xc;
    do {
        *(undefined4 *)((int)&((this->mesh).face_indices)->vertex_1 + iVar13) =
             *(undefined4 *)((int)local_12c + *(int *)((int)_Memory_01 + iVar10 * 4) * 0xc);
        *(undefined4 *)((int)&((this->mesh).face_indices)->vertex_2 + iVar13) =
             *(undefined4 *)((int)local_12c + *(int *)((int)_Memory_01 + iVar10 * 4) * 0xc + 4);
        *(undefined4 *)((int)&((this->mesh).face_indices)->vertex_3 + iVar13) =
             *(undefined4 *)((int)local_12c + *(int *)((int)_Memory_01 + iVar10 * 4) * 0xc + 8);
        *(undefined4 *)(local_140 + (int)(this->mesh).materials) =
             *(undefined4 *)((int)_Memory + *(int *)((int)_Memory_01 + iVar10 * 4) * 4);
        local_140 = local_140 + 4;
        iVar10 = iVar10 + 1;
        iVar13 = iVar13 + 0xc;
        _Memory_00 = local_8c;
    } while (iVar10 < local_128);
}

(this->mesh).adjacency_count = local_10c;  // Number of walkable faces
```

**Final Structure**:
- **Walkable faces** (indices 0 to `adjacency_count - 1`): Stored first
- **Unwalkable faces** (indices `adjacency_count` to `face_count - 1`): Stored after walkable faces
- `adjacency_count`: Set to number of walkable faces (used for adjacency table size in binary format)

### 6. AABB Block

**Lines 334-697**: Parses AABB tree nodes and constructs tree structure.

**Format**:
```
"aabb" NEWLINE
(float SPACE float SPACE float SPACE float SPACE float SPACE float SPACE integer NEWLINE)*
```

**AABB Line Format** (line 362):
`"%f %f %f %f %f %f %d"` - **7 values**: 6 floats (bbox) + 1 integer (face index)

**Values**:
1. `min_x` (float): Minimum X bound
2. `min_y` (float): Minimum Y bound
3. `min_z` (float): Minimum Z bound
4. `max_x` (float): Maximum X bound
5. `max_y` (float): Maximum Y bound
6. `max_z` (float): Maximum Z bound
7. `face_index` (int): Face index for leaf nodes (-1 or 0xFFFFFFFF for internal nodes)

**Min/Max Swapping** (lines 373-384):

The engine ensures min < max by swapping if needed:

```c
if ((float)local_104 < (float)local_f8) {
    local_104 = local_f8;
    local_f8 = pbVar32;  // Swap min_x and max_x
}
if (local_100 < local_f4) {
    local_100 = local_f4;
    local_f4 = fVar11;  // Swap min_y and max_y
}
if (local_fc < local_f0) {
    local_fc = local_f0;
    local_f0 = fVar8;  // Swap min_z and max_z
}
```

**Epsilon Expansion** (lines 438-450):

The engine applies a small epsilon value to bounding boxes to prevent floating-point precision issues:

```c
local_90 = local_f0 - FLOAT_0073dfec;  // min_z - epsilon
local_94 = local_f4 - FLOAT_0073dfec;  // min_y - epsilon
local_98 = (float)local_f8 - FLOAT_0073dfec;  // min_x - epsilon
*pfVar14 = local_98;
pfVar14[1] = local_94;
pfVar14[2] = local_90;

local_7c = local_fc + FLOAT_0073dfec;  // max_z + epsilon
local_80 = local_100 + FLOAT_0073dfec;  // max_y + epsilon
local_84 = (float)local_104 + FLOAT_0073dfec;  // max_x + epsilon
pfVar14[3] = local_84;
pfVar14[4] = local_80;
pfVar14[5] = local_7c;
```

**Epsilon Constant**: `FLOAT_0073dfec` = `0x3C23D70A` = **0.01** (IEEE 754 float)

**Face Index Mapping** (lines 367-371):

The engine performs complex face index mapping:

```c
if ((local_d4 != -NAN) &&
   (fVar9 = (float)local_118[(int)local_d4], (float)local_118[(int)local_d4] == -NAN)) {
    fVar9 = (float)(*(int *)((int)local_114 + (int)local_d4 * 4) +
                   (this->mesh).adjacency_count);
}
local_d4 = fVar9;
```

**Mapping Logic**:
- If `face_index != 0xFFFFFFFF` (not -1/NAN) and the face is walkable, uses walkable face index
- If face is unwalkable, maps to unwalkable face index (walkable_count + unwalkable_index)
- This maps AABB face references to the reordered face array (walkable first, unwalkable second)

**AABB Node Structure** (lines 385-405):

Each AABB node is allocated as 44 bytes (0x2c):

```c
pfVar14 = operator_new(0x2c);  // 44 bytes per AABB node
```

**Node Layout** (based on field assignments):
- Offset 0x00-0x17 (24 bytes): Bounding box (6 floats: min_x, min_y, min_z, max_x, max_y, max_z)
- Offset 0x18 (4 bytes): Face index (int32, -1 for internal nodes)
- Offset 0x1C (4 bytes): Unknown field (set to 5.60519e-45, likely 0x00000001 or similar)
- Offset 0x20 (4 bytes): Split plane axis (int32, used for tree traversal)
- Offset 0x24 (4 bytes): Left child pointer/index
- Offset 0x28 (4 bytes): Right child pointer/index

**Tree Construction** (lines 451-650):

The engine builds a hierarchical AABB tree structure:

1. **Leaf Nodes** (`face_index != -1`): Reference specific faces
   - Stored in `local_124` array
   - Tracked with `local_120` count

2. **Internal Nodes** (`face_index == -1`): Contain child nodes
   - Stored in `local_ec` array
   - Tracked with `local_e8` count
   - Left child at offset 0x24, right child at offset 0x28

3. **Tree Building Loop** (lines 451-523):
   - Processes AABB nodes in order
   - If node has no parent (`pfVar14[6] == -NAN`), adds to root nodes
   - Otherwise, links to parent as left or right child
   - Reads next AABB line until no more nodes

4. **Parent-Child Linking** (lines 524-648):
   - Maintains stack of nodes with unresolved children (`local_124` array)
   - Tracks parent indices in `local_138` array
   - Links nodes when child count matches parent's expected children
   - Calculates split plane axis based on bounding box dimensions (lines 553-573)

**Split Plane Calculation** (lines 553-573):

The engine determines the split plane axis based on bounding box dimensions:

```c
if ((ABS(local_58) <= fVar9) || (ABS(local_58) <= ABS(fVar11))) {
    if (fVar9 <= ABS(fVar11)) {
        uVar18 = 4;  // Z-axis
        if (fVar11 <= float_0_0) {
            uVar18 = 0x20;  // Negative Z-axis
        }
        goto LAB_00583b2f;
    }
    uVar18 = 2;  // Y-axis
    if (float_0_0 < fVar8) goto LAB_00583b2f;
    *(undefined4 *)(iVar4 + 0x20) = 0x10;  // Negative Y-axis
}
else {
    uVar18 = 1;  // X-axis
    if (float_0_0 < local_58) {
LAB_00583b2f:
        *(undefined4 *)(iVar4 + 0x20) = uVar18;
    }
    else {
        *(undefined4 *)(iVar4 + 0x20) = 8;  // Negative X-axis
    }
}
```

**Split Plane Values**:
- `1` = Positive X-axis
- `2` = Positive Y-axis
- `4` = Positive Z-axis
- `8` = Negative X-axis
- `0x10` = Negative Y-axis
- `0x20` = Negative Z-axis

**Tree Root Assignment** (line 652):
```c
this->aabb_root = (int)local_148;
```

The root node index is stored in `CSWRoomSurfaceMesh.aabb_root` field.

**AABB Storage** (lines 653-689):

After tree construction, AABB nodes are stored in the `aabbs` array:

```c
if (this->aabbs_initialized_ == 0) {
    // Copy AABB node structure (44 bytes = 0x2c)
    CVar6.field1_0x4 = uVar24;
    CVar6.field0_0x0 = in_stack_fffffe7c;
    CVar6.field2_0x8 = pbVar25;
    CVar6.field3_0xc = pcVar26;
    CVar6.field4_0x10 = ppbVar27;
    CVar6.field5_0x14 = pfVar28;
    CVar6.field6_0x18 = pfVar29;
    CVar6.field7_0x1c = ppbVar30;
    CVar6.field8_0x20 = pfVar31;
    CVar6.field9_0x24 = pbVar32;
    CVar6.field10_0x28 = puVar33;
    CExoArrayList<CSWRoomSurfaceMeshAABBNode>::Add
              ((CExoArrayList<CSWRoomSurfaceMeshAABBNode> *)&this->aabbs, CVar6);
}
```

## Data Structures

### CSWCollisionMesh

**Size**: 136 bytes  
**Structure** (from Ghidra analysis):
```c
struct CSWCollisionMesh {
    CSWCollisionMeshMethods * vtable;          // Offset 0x00 (4 bytes)
    int world_coords;                          // Offset 0x04 (4 bytes)
    undefined reserved_0x8[1];                 // Offset 0x08-0x0B (4 bytes)
    CResRef resref;                            // Offset 0x0C (16 bytes)
    CResBWM * res;                             // Offset 0x1C (4 bytes)
    Vector obj_position?;                      // Offset 0x20 (12 bytes)
    Vector position;                           // Offset 0x2C (12 bytes)
    undefined reserved_0x38[3];                // Offset 0x38-0x4F (24 bytes)
    Quaternion field7_0x38;                    // Offset 0x38 (16 bytes) - orientation
    ulong vertex_count;                        // Offset 0x50 (4 bytes)
    Vector * vertices;                         // Offset 0x54 (4 bytes)
    ulong face_count;                          // Offset 0x58 (4 bytes)
    ulong adjacency_count;                     // Offset 0x5C (4 bytes)
    WalkmeshFace * face_indices;               // Offset 0x60 (4 bytes)
    ulong * materials;                         // Offset 0x64 (4 bytes)
    Vector * normals;                          // Offset 0x68 (4 bytes)
    undefined reserved_0x6c[1];                // Offset 0x6C-0x6F (4 bytes)
    Vector relative_use_position_1;            // Offset 0x70 (12 bytes)
    Vector relative_use_position_2;            // Offset 0x7C (12 bytes)
};
```

### WalkmeshFace

**Size**: 12 bytes  
**Structure**:
```c
struct WalkmeshFace {
    ulong vertex_1;    // Offset 0x00 (4 bytes)
    ulong vertex_2;    // Offset 0x04 (4 bytes)
    ulong vertex_3;    // Offset 0x08 (4 bytes)
};
```

### CSWRoomSurfaceMesh

**Size**: 232 bytes  
**Structure** (from Ghidra analysis):
```c
struct CSWRoomSurfaceMesh {
    CSWCollisionMesh mesh;                   // Offset 0x00 (136 bytes)
    SurfaceMeshAdjacency * adjacencies;       // Offset 0x88 (4 bytes)
    CExoArrayList<SurfaceMeshEdge> edges;     // Offset 0x8C (12 bytes)
    int edges_initialized?;                   // Offset 0x98 (4 bytes)
    CExoArrayList<uint> perimeters;           // Offset 0x9C (12 bytes)
    int perimeters_initialized?;              // Offset 0xA8 (4 bytes)
    CExoArrayList<SurfaceMeshAABB> aabbs;     // Offset 0xAC (12 bytes)
    int aabbs_initialized?;                   // Offset 0xB8 (4 bytes)
    undefined reserved_0xbc[6];               // Offset 0xBC-0xD3 (24 bytes)
    int aabb_root;                            // Offset 0xD4 (4 bytes)
    ulong los_material_mask;                  // Offset 0xD8 (4 bytes)
    ulong walkable_material_mask;             // Offset 0xDC (4 bytes)
    ulong walk_check_material_mask;           // Offset 0xE0 (4 bytes)
    ulong all_material_mask;                  // Offset 0xE4 (4 bytes)
};
```

## Parsing Flow Summary

1. **Initialization** (lines 109-125):
   - Allocates 256-byte line buffer (`_Src`)
   - Initializes parsing state variables
   - Sets `local_b4 = 0` (AABB node not detected yet)

2. **Main Loop** (lines 126-699):
   - Reads lines using `LoadMeshString`
   - Strips leading whitespace
   - Detects keywords using `_strncmp`
   - Processes fields based on keyword

3. **Field Processing Order**:
   - Node block entry/exit
   - Position (if present)
   - Orientation (if present, may default to identity)
   - Vertices block (required)
   - Faces block (required)
   - AABB block (optional, only for WOK files)

4. **Face Processing**:
   - Reads all faces into temporary buffers
   - Looks up material walkability using 2DA table
   - Separates walkable vs unwalkable faces
   - Reorders faces: walkable first, unwalkable second
   - Sets `adjacency_count` = walkable face count

5. **AABB Tree Construction**:
   - Parses AABB nodes line-by-line
   - Builds hierarchical tree structure
   - Links parent-child relationships
   - Calculates split planes
   - Stores in `aabbs` array

6. **Post-Processing** (lines 704-710):
   - If AABB node was detected (`local_b4 == 1`), calls post-processing functions
   - Otherwise, calls `LoadDefaultMesh` to set defaults

## Implementation Notes for PyKotor

### Critical Implementation Requirements

1. **8-Integer Face Format**: The ASCII format reads 8 integers per face, but only stores vertex indices (3 ints) and material ID (1 int). The adjacency integers (4 ints) are parsed but may not be directly stored in the face structure. They may be used for toolset compatibility or discarded.

2. **Walkable/Unwalkable Separation**: **MUST** separate faces into walkable and unwalkable groups and store walkable faces first. This ordering is critical for adjacency table indexing in binary format.

3. **Material Lookup**: Use `SurfaceMaterial` enum's `walkable()` method to determine walkability. The engine uses 2DA::GetINTEntry, but PyKotor can use the enum directly.

4. **AABB Tree Construction**: The AABB tree construction is complex. For initial implementation, parsing AABB nodes and storing them is sufficient. Full tree reconstruction can be deferred to the writer, which regenerates AABB trees from geometry.

5. **Epsilon Expansion**: Apply 0.01 epsilon to AABB bounding boxes to match engine behavior.

6. **Face Index Mapping**: When parsing AABB nodes, map face indices to the reordered face array (walkable first, unwalkable second).

7. **Coordinate Quantization**: The vertex coordinate quantization check appears to be for binary format optimization. For ASCII parsing, read floats directly.

8. **Orientation Parsing**: The orientation field uses axis-angle representation (x, y, z axis + w angle), not direct xyzw quaternion. Convert to quaternion using axis-angle formula.

### Error Handling

The engine handles errors by:
- Calling `LoadDefaultMesh` vtable function on parse errors
- Returning `1` on error (not `0` - this is unusual but matches engine behavior)
- Freeing all allocated memory on error

### Line Buffer Size

- **Buffer Size**: 256 bytes (0x100)
- **Behavior**: Stops reading at newline (0x0A) or buffer limit
- **Null Termination**: Adds null terminator after reading line

### Whitespace Handling

- **Leading Whitespace**: Stripped before keyword detection
- **Inter-Token Whitespace**: Required between values (handled by `_sscanf`)
- **Newlines**: Required after each line (0x0A, consumed by `LoadMeshString`)

## Complete Example ASCII Format

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

## Additional Analysis Needed

1. **8-Integer Face Format**: The exact meaning of integers 4-7 needs verification through additional analysis or testing with real ASCII walkmesh files.

2. **Quaternion Conversion**: The exact axis-angle to quaternion conversion needs verification against Quaternion constructor.

3. **AABB Tree Structure**: The complete tree building algorithm (lines 524-650) needs deeper analysis to understand parent-child linking.

4. **Post-Processing Functions**: `func_0x005803c0()` and `FUN_005821e0()` need analysis to understand what post-processing occurs.

5. **Default Mesh Loading**: `LoadDefaultMesh` vtable function needs analysis to understand default values.

## References

### KotOR I (swkotor.exe)
- **0x00582d70** - CSWRoomSurfaceMesh::LoadMeshText (main ASCII parser)
- **0x005968a0** - CSWCollisionMesh::LoadMeshString (line reader)
- **0x00596670** - CSWCollisionMesh::LoadMesh (entry point)
- **0x005807c0** - LoadMeshBinary (binary parser, for comparison)

### KotOR II / TSL (swkotor2.exe)
- **0x00577860** - FUN_00577860 (main ASCII parser, equivalent to LoadMeshText)
- **0x005573e0** - FUN_005573e0 (line reader, equivalent to LoadMeshString)

### Additional References
- **vendor/swkotor.c** - Reference implementation (if available)

## Notes for Implementation

1. The ASCII format appears to be a development/toolset format, not typically used in-game
2. Binary format (BWM) is the runtime format used by the game
3. ASCII format enables human-readable editing and debugging
4. The engine supports both formats, detecting automatically in `LoadMesh`
5. Round-trip conversion (ASCII → BWM → ASCII) may not preserve exact field ordering, but should preserve data
