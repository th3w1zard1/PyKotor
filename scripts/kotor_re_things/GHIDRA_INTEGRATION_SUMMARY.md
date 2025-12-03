# Kotor RE Things - Ghidra Integration Summary

## Overview

This document summarizes the integration of reverse engineering data from the GOG version of KOTOR into Ghidra (Steam version). The data includes:

- **24,232 functions** with names, prototypes, and metadata
- **40,159 symbols** with addresses and names
- **38,411 data definitions** with types and addresses
- **1,582 comments** with addresses and text

## Important Note: Address Differences

⚠️ **The GOG and Steam versions may have different addresses.** The XML data is from the GOG version with base address `0x00400000`, while the Steam version may have different offsets. Some addresses may not match exactly.

## Integration Status

### Completed
- ✅ Parsed all data from XML export
- ✅ Applied sample comments (15+ comments successfully added)
- ✅ Created helper scripts for batch processing
- ✅ Generated JSON file with all parsed data (`scripts/kotor_re_parsed.json`)

### In Progress
- 🔄 Applying function names (addresses may need adjustment)
- 🔄 Applying symbol names
- 🔄 Applying data type definitions
- 🔄 Applying remaining comments

## Files Created

1. **`scripts/integrate_kotor_re_things.py`** - Main parser for XML data
2. **`scripts/apply_ghidra_integration.py`** - Script to parse and save JSON
3. **`scripts/batch_apply_ghidra.py`** - Batch processing helper
4. **`scripts/kotor_re_parsed.json`** - All parsed data in JSON format
5. **`scripts/ghidra_batches.txt`** - Batch reference file

## Data Structure

### Functions
Each function entry contains:
- `address`: Function entry point (hex)
- `name`: Function name (e.g., "CAppManager::GetObjectTableManager")
- `return_type`: Return type if available
- `parameters`: List of parameters with types and names
- `comments`: Associated comments

### Symbols
Each symbol entry contains:
- `address`: Symbol address
- `name`: Symbol name

### Data Definitions
Each data definition contains:
- `address`: Data address
- `datatype`: Type name
- `size`: Size in bytes

### Comments
Each comment contains:
- `address`: Comment address
- `type`: Comment type (pre, post, end-of-line, plate, repeatable)
- `text`: Comment text

## Usage

### Applying Functions

Use `mcp_ghidra_rename_function_by_address`:
```python
mcp_ghidra_rename_function_by_address(
    function_address="0x00401000",
    new_name="CSWReentrantServerStats::~CSWReentrantServerStats"
)
```

If function has a prototype, use `mcp_ghidra_set_function_prototype`:
```python
mcp_ghidra_set_function_prototype(
    function_address="0x00401060",
    prototype="undefined4 CAppManager::GetObjectTableManager(void)"
)
```

### Applying Symbols

Use `mcp_ghidra_rename_data`:
```python
mcp_ghidra_rename_data(
    address="0x00402718",
    new_name="symbol_name"
)
```

### Applying Comments

Use `mcp_ghidra_set_decompiler_comment` or `mcp_ghidra_set_disassembly_comment`:
```python
mcp_ghidra_set_decompiler_comment(
    address="0x00402127",
    comment="normalize the pointer to be relative to zero"
)
```

## Sample Applied Items

### Comments Applied (Sample)
- `0x00402127`: "normalize the pointer to be relative to zero, rather than relative to CONSOLE_INPUT"
- `0x0040a140`: "CSWGuiManager::PlayGuiSound(char)"
- `0x00422d60`: "some safe pointer bullshit"
- `0x0043e1c0`: "Returns `(Model *)this` if the MaxTree is a Model, otherwise returns NULL"
- `0x0045c3a3`: "Non Virtual Thunk from the GOB component of the Camera to the desturtcor"
- `0x0047ecd0`: "std::vector<MyFace>"
- `0x004ae770`: "CServerExoApp::GetPlayerCreature()"
- `0x004ae7b0`: "CServerExoAppInternal::GetStoreByGameObjectID(unsigned long)"
- `0x004aec90`: "CServerExoApp::GetServerInfo()"
- `0x004aee70`: "CServerExoApp::GetPartyTable()"
- `0x004c4f50`: "Allocate for 64-bit items"
- `0x004d1b58`: "Check effect is temporary"
- `0x004d824c`: "Clamp index to postive int between 0 and 8192, and access object array"
- `0x004edd90`: "CSWSCreature::SetGold(int)"
- `0x004ef770`: "CSWSCreature::GetItemRepository(int)"

## Next Steps

1. **Address Verification**: Verify which addresses match between GOG and Steam versions
2. **Batch Application**: Apply functions, symbols, and data in batches
3. **Error Handling**: Handle cases where addresses don't match
4. **Function Creation**: If functions don't exist at addresses, may need to create them first
5. **Type Definitions**: Apply struct/class definitions from the header file

## Header File Integration

The `swkotor.exe.h` file contains:
- Type definitions (structs, unions, enums)
- Function pointer types
- Class structures

These should be integrated into Ghidra's data type manager.

## Automation

For large-scale integration, consider:
1. Creating a Ghidra script (Python) that reads the JSON and applies changes
2. Using Ghidra's batch processing capabilities
3. Writing a headless Ghidra script for automation

## References

- Source: `vendor/Kotor RE Things/swkotor.exe.xml` (Ghidra XML export)
- Header: `vendor/Kotor RE Things/swkotor.exe.h` (C header with types)
- Parsed Data: `scripts/kotor_re_parsed.json`

