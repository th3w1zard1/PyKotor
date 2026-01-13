# Ghidra Documentation Setup Guide

## Overview

This guide explains how to document functions from `swkotor2.exe.re.txt` in the Ghidra project "Andastra Ghidra Project.gpr".

## Prerequisites

1. **Ghidra MCP Server Running**: The Ghidra MCP server must be running and accessible on port 8084
2. **Ghidra Project Open**: The "Andastra Ghidra Project.gpr" project must be open in Ghidra with `swkotor2.exe` loaded

## Current Status

- ✅ Parsed 470 functions from `swkotor2.exe.re.txt`
- ✅ Generated documentation scripts
- ❌ Ghidra MCP server connection not available (connection refused on port 8084)

## Files Generated

1. **`document_swkotor2_functions.py`**: Script to parse the RE file and generate documentation data
2. **`apply_ghidra_documentation.py`**: Python script containing all 470 functions with their addresses and signatures
3. **`ghidra_documentation_commands.txt`**: Text file with MCP commands for each function

## Setting Up Ghidra MCP Server

1. Ensure the Ghidra MCP server is installed and configured
2. Start the MCP server (typically runs on port 8084)
3. Verify connection by checking if the server responds

## Next Steps

Once the Ghidra MCP server is connected:

1. Open the "Andastra Ghidra Project.gpr" project in Ghidra
2. Ensure `swkotor2.exe` is loaded in the project
3. The AI agent can then use the MCP tools to:
   - Set function prototypes using `mcp_ghidra_set_function_prototype`
   - Add decompiler comments using `mcp_ghidra_set_decompiler_comment`
   - Add disassembly comments using `mcp_ghidra_set_disassembly_comment`
   - Rename functions if needed using `mcp_ghidra_rename_function_by_address`

## Function Documentation Format

Each function will be documented with:
- **Function Name**: As extracted from the RE file
- **Address**: Hex address (e.g., `0x0077e358`)
- **Signature**: Full function signature with parameter types
- **Line Count**: Number of lines in the function (for reference)

## Example Documentation

For function `___add_12` at address `0x0077e358`:
- Signature: `undefined ___add_12(uint * param_1, uint * param_2)`
- Lines: 94

## Batch Processing

The documentation will be applied to all 470 functions in batches to avoid overwhelming the MCP server. The process will:
1. Set function prototypes for each function
2. Add decompiler comments with function information
3. Verify each function exists before documenting

## Troubleshooting

### Connection Refused Error
- Ensure the Ghidra MCP server is running
- Check that port 8084 is not blocked by firewall
- Verify the MCP server configuration

### Function Not Found
- Ensure `swkotor2.exe` is loaded in the Ghidra project
- Verify the base address matches the addresses in the RE file
- Check if the function address needs adjustment for the loaded binary

### Address Format Issues
- All addresses are in hex format with `0x` prefix
- Addresses from the RE file are already in the correct format

## Contact

If you encounter issues, ensure:
1. Ghidra MCP server is running
2. Project is open with the correct binary loaded
3. Then re-run the documentation process
