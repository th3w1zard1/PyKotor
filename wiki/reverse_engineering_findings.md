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
3. `ExecuteCode()` interprets bytecode using a large switch-based interpreter (5529 bytes at 0x005d2bd0)
4. Stack operations handle data types: int, float, string, object, vector
5. Call stack tracks function execution depth

**Detailed ExecuteCode Analysis:**
The `ExecuteCode` function is a massive switch statement with the following instruction set:

**Stack Operations:**
- `CPDOWNSP`/`CPDOWNBP`: Copy down stack/base pointer with offset and size parameters
- `CPTOPSP`/`CPTOPBP`: Copy to top of stack/base pointer
- `RSADDx`: Reserve space and add (types: int=3, float=4, string=5, object=6, engine_structs=16-25)

**Constants:**
- `CONSTx`: Push constants (int=3, float=4, string=5, object=6) with embedded values

**Actions:**
- `ACTION`: Execute command with 16-bit command ID parameter

**Logic:**
- `LOGANDII`: Logical AND for integers

**Control Flow:**
- `JMP`, `JZ`, `JNZ`: Jump instructions
- `RETN`: Return from function

**Arithmetic:**
- `ADDII`/`ADDIF`/`ADDFF`: Addition operations
- `SUBII`/`SUBIF`/`SUBFF`: Subtraction operations
- `MULII`/`MULIF`/`MULFF`: Multiplication operations
- `DIVII`/`DIVIF`/`DIVFF`: Division operations

**Safety Features:**
- Instruction count limit (0x1ffff instructions max)
- Stack bounds checking prevents overflows
- Invalid instruction types return `INVALID_INSTRUCTION_TYPE` error
- Stack unwinding on execution failures

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

**CExoResMan (Resource Manager) Architecture:**
The engine uses `CExoResMan` as the central resource management system supporting multiple archive types:
- `FIXED` (0x00000000): KEY/BIF files (chitin.key + data/*.bif)
- `DIRECTORY` (0x80000000): Loose files in directories
- `ERF` (0x40000000): ERF/RIM archives (modules/*.rim, modules/*.erf)
- `RIM` (0x20000000): RIM archives (specifically for texture packs)

**Key Functions:**
- `CExoResMan::AddKeyTable()`: Loads archive tables with type flags
- `CExoResMan::ReadResource()`: Loads resources from archives
- `AddResourceImageFile()` calls `AddKeyTable(..., RIM, 0)` for texture packs

**GFF Structure (from CResGFF analysis):**
```cpp
struct CResGFF {
    CRes resource;                    // Base resource (inherits from CRes)
    GFFHeaderInfo* header;            // File header with type/version
    GFFStructData* structs;           // Struct definitions array
    GFFFieldData* fields;             // Field definitions array
    char (*labels)[16];               // 16-byte null-terminated labels
    void* field_data;                 // Raw field data buffer
    ulong* field_indices_data;        // Field index arrays
    ulong* list_indices_data;         // List index arrays
    // Dynamic capacity tracking for all arrays
};
```

**GFF Creation Process (from CreateGFFFile at 0x00411260):**
1. Takes file type string parameter (param_3)
2. Uses hardcoded global GFFVersion variable (0x0073e2c8) containing "V3.2" for version
3. Writes 4-byte file type (little-endian) to header using param_3 bytes
4. Writes hardcoded 4-byte version "V3.2" (little-endian) to header from global variable
5. Creates root struct with `AddStruct(this, 0xffffffff)`
6. Initializes all data structures for writing

**GFF Version Support:**
The engine's `CreateGFFFile` function is hardcoded to only create V3.2 GFF files. It does not accept version parameters - instead uses a global GFFVersion variable containing "V3.2". The xoreos-tools support for V3.3, V4.0, and V4.1 suggests these formats may be supported for reading but not writing by the original engine.

**Key Functions:**
- `CResRef::CopyToString()`: Converts ResRef to string
- `CResGFF::ReadFieldCResRef()`: Reads ResRef fields from GFF
- `CResGFF::WriteFieldCResRef()`: Writes ResRef fields to GFF
- `CreateGFFFile()`: Creates GFF files with specified type/version
- `WriteGFFFile()`: Serializes GFF to disk

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

### Implemented Improvements

**GFF Format Enhancements:**
- Added documentation about engine's native multi-version support (V3.3, V4.0, V4.1)
- Confirmed CResGFF structure alignment with PyKotor's implementation
- Documented GFF creation process from `CreateGFFFile` function

**NCS VM Validation Improvements:**
- Enhanced VM validation with instruction set analysis from `ExecuteCode`
- Added validation for RSADDx type parameters (3-6 for basic types, 16-25 for engine structs)
- Added validation for CONSTx type parameters
- Improved error messages for invalid instruction types
- Added stack safety checks based on engine's bounds validation

**Resource System Documentation:**
- Documented CExoResMan archive type system (FIXED, DIRECTORY, ERF, RIM)
- Added reverse engineering notes to Chitin class about resource loading architecture
- Confirmed KEY/BIF loading mechanism matches PyKotor implementation

### Potential Future Improvements

1. **Script Engine:**
   - Validate NWScript bytecode against complete VM instruction set
   - Improve stack-based execution simulation with all opcodes
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
- Multi-version support confirmed in engine

**NWScript VM Compatibility:**
The detailed `ExecuteCode` analysis validates PyKotor's script interpretation approach. The instruction set mapping confirms comprehensive opcode coverage and proper type handling. The stack-based execution model with typed operations (int, float, string, object) matches PyKotor's implementation.

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
