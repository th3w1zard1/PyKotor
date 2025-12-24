# Reverse Engineering Findings: swkotor.exe and swkotor2.exe

## Overview

This document contains findings from reverse engineering the Star Wars: Knights of the Old Republic game executables using Ghidra and the Reva MCP tools. The analysis provides insights into the game's engine architecture that can inform improvements to the PyKotor library and toolset.

## Engine Architecture

### Scripting Engine (NWScript Virtual Machine)

**Key Components:**
- `CVirtualMachine`: Main virtual machine class that manages script execution
- `CVirtualMachineInternal`: Core VM implementation with stack management
- `CVirtualMachineStack`: Stack-based execution environment
- `CVirtualMachineCmdImplementer`: Command implementation interface

**Execution Flow:**
1. `CVirtualMachine::RunScript()` loads and executes scripts
2. `ReadScriptFile()` parses NCS bytecode from files
3. `ExecuteCode()` interprets bytecode using a large switch-based interpreter (5529 bytes)
4. Stack operations handle data types: int, float, string, object, vector
5. Call stack tracks function execution depth

**Key Insights:**
- Scripts are loaded synchronously via resource system
- Bytecode execution is stack-based with typed operations
- Error handling includes stack unwinding on failures
- Command callbacks allow engine integration

### Resource Management System

**Core Classes:**
- `CRes`: Base resource class for all file formats
- `CResRef`: 16-byte resource reference (ResRef) with string conversion
- `CResGFF`: GFF file format handler
- `CRes2DA`: 2DA file format handler
- `CResHelper<T>`: Template for type-specific resource handlers

**GFF Structure (from CResGFF):**
```cpp
struct CResGFF {
    CRes resource;                    // Base resource
    GFFHeaderInfo* header;            // File header
    GFFStructData* structs;           // Struct definitions
    GFFFieldData* fields;             // Field definitions
    char (*labels)[16];               // 16-byte labels
    void* field_data;                 // Raw field data
    ulong* field_indices_data;        // Field index arrays
    ulong* list_indices_data;         // List index arrays
    // Capacity tracking for dynamic arrays
};
```

**Key Functions:**
- `CResRef::CopyToString()`: Converts ResRef to string
- `CResGFF::ReadFieldCResRef()`: Reads ResRef fields from GFF
- `CResGFF::WriteFieldCResRef()`: Writes ResRef fields to GFF

### Graphics and Rendering System

**OpenGL Setup:**
```cpp
void SetupOpenGL() {
    glClearColor(0, 0, 0, 0);
    glEnable(GL_CULL_FACE);
    glEnable(GL_DEPTH_TEST);
    glEnable(GL_LIGHTING);
    glEnable(GL_TEXTURE_2D);
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    glEnable(GL_ALPHA_TEST);
}
```

**Features:**
- Standard OpenGL 1.x pipeline
- Depth testing and face culling
- Multi-texturing support
- Alpha blending for transparency
- Lighting system integration

### Model Loading System

**Architecture:**
- `IODispatcher`: Central I/O system for resource loading
- `MaxTree`: Tree-based model representation
- Model caching with `modelsList` global array
- Synchronous loading via `IODispatcher::ReadSync()`

**Key Functions:**
- `LoadModel()`: Main model loading function
- `FindModel()`: Model cache lookup
- `AddModel()`: Cache management
- `MaxTree::AsModel()`: Tree to model conversion

## Binary Differences: KOTOR vs TSL

**swkotor.exe:**
- 24,096 functions
- .text section: 3,391,488 bytes
- Extensive function naming preserved

**swkotor2.exe:**
- 13,787 functions
- .text section: 3,883,008 bytes
- Heavier optimization, fewer named functions
- Different compilation approach

## Implications for PyKotor

### Potential Improvements

1. **Script Engine:**
   - Validate NWScript bytecode against VM expectations
   - Improve stack-based execution simulation
   - Better error handling for malformed scripts

2. **Resource System:**
   - Enhanced ResRef validation (16-byte limit)
   - Improved GFF field parsing based on engine structures
   - Better resource type detection

3. **Model System:**
   - Tree-based model validation
   - Improved MDL/MDX loading efficiency
   - Better cache management

4. **Graphics:**
   - OpenGL-compatible model rendering
   - Proper alpha blending implementation
   - Lighting system compatibility

### Code Relationship Insights

**CResGFF Structure Alignment:**
The reverse engineering confirms PyKotor's GFF implementation matches the engine's expectations:
- Header parsing is correct
- Struct/field relationships are properly handled
- Label handling (16-byte strings) is accurate

**NWScript VM Compatibility:**
The stack-based execution model validates PyKotor's script interpretation approach. The large `ExecuteCode` function suggests comprehensive opcode coverage.

## Future Research Areas

1. **NCS Bytecode Format:** Detailed opcode analysis
2. **MDL Internal Structure:** Tree node relationships
3. **Resource Loading Pipeline:** Complete IODispatcher analysis
4. **Memory Management:** Heap allocation patterns
5. **Optimization Differences:** TSL-specific improvements

## Tools Used

- **Reva MCP:** Ghidra integration for reverse engineering
- **Ghidra:** Binary analysis and decompilation
- **Function Analysis:** Cross-referencing and call graph analysis

## References

- Original game executables: swkotor.exe, swkotor2.exe
- Analysis conducted using Reva MCP tools in Ghidra
- Findings validated against PyKotor library implementation
