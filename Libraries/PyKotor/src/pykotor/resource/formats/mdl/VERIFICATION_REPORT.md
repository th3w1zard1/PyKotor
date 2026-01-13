# MDL Format Implementation Verification Report

## Executive Summary

This report compares the Python MDL/MDX implementation in `pykotor.resource.formats.mdl` against the actual game engine implementations in `swkotor.exe` (K1) and `swkotor2.exe` (TSL) using REVA MCP analysis.

**Status**: ✅ **Mostly Correct** - The implementation matches the engine logic with minor documentation clarifications needed.

---

## 1. Model Header Reading (_ModelHeader)

### Engine Implementation
- **Reset() @ (K1: 0x004a1030, TSL: 0x004ce550)**: Parses model structure from binary data
- Reads model name at offset 0x88 (K1) / 0x22 (TSL) - corresponds to `geometry.model_name`
- Reads parent model pointer at offset 0x64 (K1) / 0x19 (TSL) - corresponds to `parent_model_pointer`
- Reads MDX data buffer offset at 0xac (K1) / 0x2b (TSL) - corresponds to `mdx_data_buffer_offset`
- Reads MDX size at 0xb0 (K1) / 0x2c (TSL) - corresponds to `mdx_size`
- Processes animations at offset 0x58 (K1) / 0x16 (TSL) - corresponds to `offset_to_animations`
- Processes root node at offset 0x28 (K1) / 0x0a (TSL) - corresponds to `root_node_offset`

### Python Implementation
**Location**: `io_mdl.py:675-793` (_ModelHeader class)

✅ **VERIFIED CORRECT**:
- All field offsets match engine implementation
- Field types match (uint8, uint32, Vector3, float, string)
- Reading order matches engine parsing order
- Clamping of animation_count and name_offsets_count to 0x7FFFFFFF is correct (prevents signed integer overflow)

**Docstring Accuracy**: ✅ Correct - References match actual engine addresses

---

## 2. Node Header Reading (_NodeHeader)

### Engine Implementation
- **ResetMdlNode() @ (K1: 0x004a0900)**: Processes nodes based on `node_type` field
- Node type is determined by flag combinations stored in the first byte of the node
- Uses `param_1->node_type` to determine which Reset function to call

### Python Implementation
**Location**: `io_mdl.py:1554-1655` (_NodeHeader class)

✅ **VERIFIED CORRECT**:
- Reads 4 uint16 fields (type_id, padding0, node_id, name_id) - matches MDLOps template "SSSS"
- Reads position (Vector3) and orientation (Vector4) correctly
- Reads offset arrays correctly
- Clamping of children_count and controller_data_length to 0x7FFFFFFF is correct

**Docstring Accuracy**: ✅ Correct - MDLOps template documented correctly

---

## 3. Node Flag Detection and Type Assignment

### Engine Implementation
- **MdlNode::AsMdlNodeTriMesh @ (K1: 0x0043e400, TSL: 0x004501d0)**: 
  - Checks `(*param_1 & 0x21) == 0x21` (HEADER + MESH flags)
- **MdlNode::AsMdlNodeDanglyMesh @ (K1: 0x0043e380, TSL: 0x00450150)**:
  - Checks `(*param_1 & 0x121) == 0x121` (HEADER + MESH + DANGLY flags)
- **MdlNode::AsMdlNodeSkin @ (K1: 0x0043e3f0, TSL: 0x004501c0)**:
  - Checks `(*param_1 & 0x61) == 0x61` (HEADER + MESH + SKIN flags)
- **MdlNode::AsMdlNodeAABB @ (K1: 0x0043e340, TSL: 0x00450110)**:
  - Checks `(*param_1 & 0x221) == 0x221` (HEADER + MESH + AABB flags)
- **MdlNode::AsMdlNodeLightsaber @ (K1: 0x0043e3a0, TSL: 0x00450170)**:
  - Checks `(*param_1 & 0x821) == 0x821` (HEADER + MESH + SABER flags)

### Python Implementation
**Location**: `io_mdl.py:3033-3261` (_load_node method)

✅ **VERIFIED CORRECT**:
- Checks flags in correct priority order (AABB first, then LIGHT, EMITTER, REFERENCE, then MESH variants)
- Node type assignment matches engine logic:
  - AABB nodes: `if bin_node.header.type_id & MDLNodeFlags.AABB`
  - Light nodes: `if bin_node.header.type_id & MDLNodeFlags.LIGHT`
  - Emitter nodes: `if bin_node.header.type_id & MDLNodeFlags.EMITTER`
  - Reference nodes: `if bin_node.header.type_id & MDLNodeFlags.REFERENCE`
  - Skin nodes: `if bin_node.header.type_id & MDLNodeFlags.SKIN`
  - Dangly nodes: `if bin_node.header.type_id & MDLNodeFlags.DANGLY`
  - Trimesh nodes: Default for MESH without other flags

**Note**: The Python code checks individual flags (e.g., `MDLNodeFlags.MESH`) rather than flag combinations (e.g., `0x21`). This is **functionally correct** because:
1. HEADER flag is always present when reading a valid node
2. The flag checks are done in priority order, so combinations are handled correctly
3. The engine's `AsMdlNode*` functions check combinations for type safety, but the Python code's approach is equivalent

**Docstring Accuracy**: ✅ Correct - Flag combinations documented in `mdl_types.py:77-103`

---

## 4. AABB/Walkmesh Reading

### Engine Implementation
- **ResetAABBTree()**: Called from ResetMdlNode() for AABB nodes
- Reads AABB tree recursively (depth-first traversal)
- Each AABB node: 6 floats (bbox min/max) + 4 int32s (left child, right child, face index, unknown)

### Python Implementation
**Location**: `io_mdl.py:3063-3114` (_read_aabb_recursive function)

✅ **VERIFIED CORRECT**:
- Recursive depth-first traversal matches engine
- Reads 6 floats (bbox_min, bbox_max) correctly
- Reads 4 int32s (left_child, right_child, face_index, unknown) correctly
- Handles face_index == -1 as branch node indicator
- Proper bounds checking before reading

**Docstring Accuracy**: ✅ Correct - Structure documented correctly

---

## 5. Name Table Parsing (_load_names)

### Engine Implementation
- Names are stored as null-terminated strings in a contiguous block
- Name offsets array points into the names block
- Reset() function processes name offsets at offset 0xbc (K1) / 0x2f (TSL)

### Python Implementation
**Location**: `io_mdl.py:2974-3011` (_load_names method)

✅ **VERIFIED CORRECT**:
- Reads name_indexes as signed int32s (matches MDLOps)
- Calculates names_size correctly: `offset_to_animations - (offset_to_name_offsets + (4 * name_indexes_count))`
- Parses null-terminated strings correctly
- Handles edge cases (null_pos == -1, current_pos >= len)

**Docstring Accuracy**: ✅ Correct - Logic matches engine behavior

---

## 6. Node Reading Order (_get_node_order)

### Engine Implementation
- ResetMdlNode() processes nodes recursively
- Children are processed via ResetMdlNodeParts() which iterates through child array

### Python Implementation
**Location**: `io_mdl.py:3013-3031` (_get_node_order method)

✅ **VERIFIED CORRECT**:
- Recursive traversal matches engine
- Reads name_index from node header correctly
- Handles child_array_offset and child_array_length correctly
- Validates offsets (not 0 or 0xFFFFFFFF)

**Docstring Accuracy**: ✅ Correct - Traversal order matches engine

---

## 7. Controller and Animation Reading

### Engine Implementation
- **ResetAnimation() @ (K1: 0x004a0060)**: Processes animation data
- Controllers are stored with type_id, row_count, column_count, and data arrays
- Compressed quaternions use uint32 encoding

### Python Implementation
**Location**: `io_mdl.py:989-1050` (_Controller class), `915-960` (_Animation class)

✅ **VERIFIED CORRECT**:
- Reads controller type_id, unknown0, row_count, column_count correctly
- Handles compressed quaternions (type 20, column_count 2) correctly
- Animation header reading matches engine structure

**Docstring Accuracy**: ✅ Correct - Controller types documented in `mdl_types.py:138-260`

---

## 8. Geometry/Mesh Reading (_TrimeshHeader)

### Engine Implementation
- **PartTriMesh::PartTriMesh @ (K1: 0x00445840, TSL: 0x00459be0)**: Creates tri-mesh part from MDL node
- Reads vertex data, face data, texture coordinates from MDX file
- Different sizes for K1 (332 bytes) vs TSL (340 bytes)

### Python Implementation
**Location**: `io_mdl.py:1783-2089` (_TrimeshHeader class)

✅ **VERIFIED CORRECT**:
- K1_SIZE = 332 bytes, K2_SIZE = 340 bytes (matches engine)
- Reads all fields in correct order
- Handles MDX data offsets correctly
- Texture reading logic matches engine

**Docstring Accuracy**: ✅ Correct - Sizes and offsets documented correctly

---

## 9. LoadModel Function Documentation

### Engine Implementation
- **LoadModel @ (K1: 0x00464200, TSL: 0x0047a570)**: Main entry point
- Calls IODispatcher::ReadSync()
- Checks for duplicate models by name
- Returns cached model if duplicate found

### Python Implementation Documentation
**Location**: `io_mdl.py:1-500` (docstring)

✅ **VERIFIED CORRECT**:
- Function addresses match engine
- Logic description matches decompiled code
- Callees and callers documented correctly
- Differences between K1 and TSL documented

**Docstring Accuracy**: ✅ Correct - Comprehensive documentation matches engine behavior

---

## 10. Issues Found

### Minor Issues

1. **Flag Combination Checking** (Informational, not a bug):
   - The Python code checks individual flags (e.g., `MDLNodeFlags.MESH`) rather than combinations (e.g., `0x21`)
   - This is functionally correct but could be more explicit about requiring HEADER flag
   - **Recommendation**: Add comment clarifying that HEADER is always present when reading valid nodes

2. **Offset Documentation** (Clarification needed):
   - Some docstrings reference offsets relative to file start, others relative to structure start
   - **Recommendation**: Clarify in docstrings whether offsets are file-relative or structure-relative

### No Critical Issues Found

All major logic blocks match the engine implementation correctly.

---

## 11. Recommendations

1. ✅ **Keep current implementation** - Logic is correct
2. 📝 **Add clarifying comments** about HEADER flag always being present
3. 📝 **Clarify offset documentation** (file-relative vs structure-relative)
4. ✅ **Docstrings are accurate** - All addresses and references verified

---

## 12. Verification Methodology

1. Opened Ghidra project with both K1 and TSL executables
2. Located key functions via cross-reference search
3. Decompiled functions and compared with Python implementation
4. Verified field offsets, data types, and reading order
5. Checked flag combinations and node type detection logic
6. Verified recursive traversal patterns

---

## Conclusion

The Python MDL/MDX implementation is **functionally correct** and matches the game engine behavior. All critical logic blocks have been verified against the actual engine code. The implementation correctly handles:

- ✅ Model header parsing
- ✅ Node structure reading
- ✅ Flag-based node type detection
- ✅ AABB tree traversal
- ✅ Name table parsing
- ✅ Controller and animation data
- ✅ Geometry/mesh data
- ✅ K1 vs TSL differences

**REVA status: Completed - Analyzed both K1 and TSL :)**
