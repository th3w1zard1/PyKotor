# ASCII MDL Support in swkotor.exe (K1) and swkotor2.exe (TSL) - Low-Level Analysis

**Last Updated:** 2026-01-XX  
**Status:** Both K1 and TSL support ASCII MDL format (TSL support was previously undocumented)

## Executive Summary

**YES**, ASCII MDL format is supported in **BOTH** `swkotor.exe` (K1) **AND** `swkotor2.exe` (TSL). The support is implemented through a line-by-line text parser that interprets ASCII commands and applies them to a model structure.

## Entry Point: `Input::Read` @ (K1: 0x004a14b0, TSL: 0x004ce9d0)

The main entry point for MDL loading is `Input::Read`, which performs format detection:

### Step 1: Format Detection (Lines 17-26)

```c
data = (FILE *)AurResGet(param_1);
if ((data != (FILE *)0x0) && (pFVar4 = AurResGetDataBytes(4,(FILE **)data), pFVar4 != (FILE *)0x0)) {
    if (*(char *)&pFVar4->_ptr == '\0') {
        // BINARY PATH: First byte is null (0x00)
        AurResFreeDataBytes((int *)data,pFVar4);
        ppFVar5 = (FILE **)AurResGet(param_2);
        this_00 = InputBinary::Read((InputBinary *)this,data,ppFVar5,'\0');
        pMVar6 = MaxTree::AsModel(this_00);
        return (ulong)pMVar6;
    }
    // ASCII PATH: First byte is NOT null
    AurResFreeDataBytes((int *)data,pFVar4);
```

**Key Logic:**
- Reads first 4 bytes of the file
- Checks if first byte is `'\0'` (null byte)
- **If null**: Routes to binary MDL parser (`InputBinary::Read`)
- **If NOT null**: Routes to ASCII MDL parser

### Step 2: ASCII Parsing Loop (Lines 28-46)

```c
uVar2 = CurrentModel;  // Save current model context
pcVar7 = (char *)AurResGetNextLine();  // Get first line
while (pcVar7 != (char *)0x0) {
    // Skip leading whitespace (spaces and tabs)
    for (; (*pcVar7 == ' ' || (*pcVar7 == '\t')); pcVar7 = pcVar7 + 1) {
    }
    
    // Process non-empty, non-comment lines
    if ((*pcVar7 != '\0') && (pcVar3 = pcVar7, *pcVar7 != '#')) {
        // Trim trailing whitespace (newlines, carriage returns, tabs, spaces)
        do {
            pcVar9 = pcVar3;
            pcVar3 = pcVar9 + 1;
        } while (*pcVar9 != '\0');
        while ((pcVar9 = pcVar9 + -1, pcVar7 <= pcVar9 &&
               ((((cVar1 = *pcVar9, cVar1 == '\n' || (cVar1 == '\r')) || (cVar1 == '\t')) ||
                (cVar1 == ' '))))) {
            *pcVar9 = '\0';
        }
        
        // INTERPRET THE LINE AS A FUNCTION CALL
        FuncInterp(pcVar7);
    }
    pcVar7 = (char *)AurResGetNextLine();  // Get next line
}
AurResFree((FILE **)data,0);
uVar8 = CurrentModel;
CurrentModel = uVar2;  // Restore previous model context
return uVar8;
```

**Key Features:**
- Line-by-line processing via `AurResGetNextLine()`
- Skips leading whitespace
- Skips comment lines (starting with `#`)
- Trims trailing whitespace (newlines, carriage returns, tabs, spaces)
- Each line is interpreted as a function call via `FuncInterp()`

## Line Reading: `AurResGetNextLine` @ (K1: 0x0044bfa0, TSL: 0x00460610)

```c
void AurResGetNextLine(void) {
    if (resources.size == 0) {
        return;
    }
    if (*(int *)resources.data[resources.size + -1] != 0) {
        getnextline_file((void *)0x0);  // Read from file
        return;
    }
    getnextline_res();  // Read from resource
    return;
}
```

**Purpose:** Retrieves the next line from either a file or resource stream.

## Function Interpreter: `FuncInterp` @ (K1: 0x0044c1f0, TSL: 0x00460860)

`FuncInterp` is a general-purpose script interpreter that:

1. **Parses function names** from the input line (lines 228-242)
   - Extracts the first word (function name) before `=` or space
   - Example: `"position = 1.0 2.0 3.0"` → function name: `"position"`

2. **Looks up function in callback table** (line 248 in K1, line 249 in TSL)
   ```c
   // K1:
   piVar12 = (int *)FindConCallBack(local_c080);
   // TSL:
   piVar12 = (int *)FUN_00460200(local_c080);  // FindConCallBack equivalent
   ```
   - `FindConCallBack` searches a global callback table (`consoleFuncs` in K1, `DAT_0082d4b8` array in TSL)
   - Returns a function pointer if found, NULL otherwise

3. **Calls the function** (line 272)
   ```c
   (**(code **)(*piVar12 + 4))();
   ```
   - Invokes the function via function pointer

4. **Handles nested expressions** (lines 124-217)
   - Supports bracket notation `[expression]` for nested function calls
   - Recursively calls `FuncInterp` on bracketed expressions

**Important:** `FuncInterp` is a **general script interpreter**, not MDL-specific. It relies on registered callbacks to handle specific commands.

## Model Field Parsing: `ModelParseField` → `Model::InternalParseField`

### `ModelParseField` @ (K1: 0x0043e1e0, TSL: N/A)

```c
void __cdecl ModelParseField(Model *param_1,char *param_2) {
    Model::InternalParseField(param_1,param_2);
    return;
}
```

**Purpose:** Wrapper that calls `Model::InternalParseField` to parse a single field line.

### `Model::InternalParseField` @ (K1: 0x00465560, TSL: N/A)

This function parses ASCII field names and applies them to model nodes. Key field types:

#### Node-Level Fields (via `MdlNode::InternalParseField`)

1. **Position** (lines 20-24, 30-40)
   - Format: `position = <x> <y> <z>`
   - Example: `position = 1.0 2.0 3.0`
   - Also supports animated: `positionkey`, `positionbezierkey`

2. **Orientation** (lines 25-29, 67-77, 78-102)
   - Format: `orientation = <w> <x> <y> <z>` (quaternion)
   - Also supports animated: `orientationkey`, `orientationbezierkey`

3. **Scale** (lines 112-147)
   - Format: `scale = <value>`
   - Also supports animated: `scalekey`, `scalebezierkey`

4. **Parent** (lines 150-168)
   - Format: `parent = <node_name>` or `parent = NULL`
   - Establishes parent-child relationships in the node hierarchy

5. **Wire Color** (lines 107-111)
   - Format: `wirecolor = <r> <g> <b>`

#### Node-Type-Specific Fields

Different node types have specialized `InternalParseField` implementations:

- **MdlNodeEmitter** @ 0x004658b0: Parses emitter-specific fields like `p2p`, `bounce`, `texture`, `blurlength`, etc.
- **MdlNodeLight**: Parses light-specific fields
- **MdlNodeTriMesh**: Parses mesh-specific fields
- **MdlNodeSkin**: Parses skin-specific fields
- **MdlNodeDangly**: Parses dangly-specific fields

## How It All Connects

1. **Model Creation**: When a model is loaded via binary path, `InputBinary::Reset` sets up the model structure and registers `ModelParseField` as the field parser (line 90 of `Reset`):
   ```c
   *(code **)param_1 = ModelDestructor;
   *(code **)(param_1 + 4) = ModelParseField;  // Register parser
   InsertModel((Model *)param_1);
   ```

2. **ASCII Parsing**: When ASCII path is taken:
   - `Input::Read` reads lines via `AurResGetNextLine()`
   - Each line is passed to `FuncInterp()`
   - `FuncInterp()` looks up the function name in the callback table
   - If the function is registered (e.g., as a console command that calls `ModelParseField`), it gets executed
   - The function applies the parsed values to `CurrentModel`

3. **CurrentModel Global**: The global variable `CurrentModel` (address 0x007fbae4) maintains the active model context during parsing.

## Format Specification (Inferred from Code)

Based on the parsing logic, ASCII MDL files appear to follow this structure:

```
# Comments start with #
# Each line is a function call: <function_name> = <arguments>

# Model-level commands (if any)
# Node definitions
node_name {
    position = <x> <y> <z>
    orientation = <w> <x> <y> <z>
    scale = <value>
    parent = <parent_name>
    # Node-type-specific fields...
}

# Animation controllers
positionkey = <time> <x> <y> <z>
orientationkey = <time> <w> <x> <y> <z>
# etc.
```

## TSL (swkotor2.exe) Status

**TSL DOES support ASCII MDL** (previously undocumented):

The ASCII MDL support in TSL is implemented identically to K1, but with different function addresses:

### Key Functions in TSL

1. **`Input::Read`** @ 0x004ce9d0
   - **NOT** 0x004ce780 (that's `InputBinary::Read`)
   - Contains the same format detection logic (check first byte for null)
   - Routes to ASCII parser if first byte is NOT null
   - Uses `FUN_00460610()` (AurResGetNextLine) and `FUN_00460860()` (FuncInterp)

2. **`AurResGetNextLine`** @ 0x00460610
   - Equivalent to K1's 0x0044bfa0
   - Reads lines from resource or file

3. **`FuncInterp`** @ 0x00460860
   - Equivalent to K1's 0x0044c1f0
   - Parses function names and calls registered callbacks

4. **`FindConCallBack`** @ 0x00460200
   - Equivalent to K1's 0x0044bb90
   - Looks up function names in callback table

### Differences from K1

- Function addresses are different (expected due to code reorganization)
- Global variable names differ (e.g., `DAT_008804bc` instead of `CurrentModel`)
- Internal data structures may have different layouts, but the logic is identical

**Conclusion:** Both K1 and TSL support ASCII MDL format with identical parsing logic.

## References

### K1 (swkotor.exe)
- `Input::Read` @ 0x004a14b0
- `AurResGetNextLine` @ 0x0044bfa0
- `FuncInterp` @ 0x0044c1f0
- `ModelParseField` @ 0x0043e1e0
- `Model::InternalParseField` @ 0x00465560
- `MdlNode::InternalParseField` @ 0x00465560
- `MdlNodeEmitter::InternalParseField` @ 0x004658b0
- `FindConCallBack` @ 0x0044bb90
- `CurrentModel` global @ 0x007fbae4

### TSL (swkotor2.exe)
- `Input::Read` @ 0x004ce9d0 (NOT 0x004ce780, which is `InputBinary::Read`)
- `AurResGetNextLine` @ 0x00460610
- `FuncInterp` @ 0x00460860
- `FindConCallBack` @ 0x00460200
- `CurrentModel` global @ 0x008804bc (DAT_008804bc)
- `InputBinary::Read` @ 0x004ce780
- `IODispatcher::ReadSync` @ 0x004cead0 (single param) and 0x004ceaf0 (two params)
