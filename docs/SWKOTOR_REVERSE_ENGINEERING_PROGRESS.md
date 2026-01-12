# SWKOTOR Reverse Engineering TODO

This document lists **everything that must be done** to achieve 100% comprehension in regards to reverse engineering of both `swkotor.exe` (KotOR I) and `swkotor2.exe` (KotOR II/TSL). All functions, structures, data types, strings, imports, exports, and cross-references must be documented with both K1 and TSL addresses together.

**Format**: All functions documented as `FunctionName - K1: 0xADDRESS, TSL: 0xADDRESS`

**Current Status**: K1: 24,231 functions, TSL: 22,596 functions (46,827 total). 1,009+ structures found. 349 imports each.

## Table of Contents

- [Functions](#functions)
  - [For EVERY Function](#for-every-function)
  - [Undefined Function Candidates](#undefined-function-candidates)
- [Structures](#structures)
  - [For EVERY Structure](#for-every-structure)
  - [Priority Structures](#priority-structures)
- [Data Types](#data-types)
  - [Built-in Types](#built-in-types)
  - [Custom Types](#custom-types)
  - [Enums](#enums)
  - [Typedefs](#typedefs)
  - [Unions](#unions)
  - [Arrays](#arrays)
- [Strings](#strings)
  - [String Extraction](#string-extraction)
  - [String Analysis](#string-analysis)
- [Symbols](#symbols)
  - [Symbol Analysis](#symbol-analysis)
  - [Labels](#labels)
- [Imports](#imports)
  - [Import Analysis](#import-analysis)
  - [Import Libraries](#import-libraries)
- [Exports](#exports)
  - [Export Analysis](#export-analysis)
- [Memory Blocks](#memory-blocks)
  - [Memory Block Analysis](#memory-block-analysis)
- [Cross-References](#cross-references)
  - [Cross-Reference Analysis](#cross-reference-analysis)
  - [Call Graph](#call-graph)
  - [Data Flow](#data-flow)
- [Constants](#constants)
  - [Constant Analysis](#constant-analysis)
- [Virtual Function Tables (VTables)](#virtual-function-tables-vtables)
  - [VTable Analysis](#vtable-analysis)
- [Comments](#comments)
  - [Comment Management](#comment-management)
- [Bookmarks](#bookmarks)
  - [Bookmark Management](#bookmark-management)
- [Thunks](#thunks)
  - [Thunk Analysis](#thunk-analysis)
- [Data Type Archives](#data-type-archives)
  - [Archive Analysis](#archive-analysis)
- [Address Tables](#address-tables)
  - [Address Table Analysis](#address-table-analysis)
- [Data Analysis](#data-analysis)
  - [Data at Addresses](#data-at-addresses)
- [Function Tags](#function-tags)
  - [Tagging](#tagging)
- [Variable Renaming](#variable-renaming)
  - [Renaming](#renaming)
- [Data Type Correction](#data-type-correction)
  - [Type Correction](#type-correction)
- [C Headers Generation](#c-headers-generation)
  - [Header Files](#header-files)
- [Function Prototypes](#function-prototypes)
  - [Prototype Management](#prototype-management)
- [Decompilation Comments](#decompilation-comments)
  - [Decompilation Enhancement](#decompilation-enhancement)
- [Code Discovery](#code-discovery)
  - [Discovery Tasks](#discovery-tasks)
- [Control Flow Analysis](#control-flow-analysis)
- [Data Flow Analysis](#data-flow-analysis)
- [Exception Handling](#exception-handling)
- [Optimization Analysis](#optimization-analysis)
- [Reva MCP Tools](#reva-mcp-tools)
  - [Tools Not Yet Used](#tools-not-yet-used)
- [Verification and Quality Assurance](#verification-and-quality-assurance)
- [Summary Statistics](#summary-statistics)

## Functions

### For EVERY Function

- [ ] Get decompilation for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Match TSL addresses to all K1 functions (K1: 0/24231 matched, TSL: 0/22596 matched)
- [ ] Verify/improve signature for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Identify and name all parameters for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Verify return type for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Get callers (who calls this) for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Get callees (what this calls) for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Get cross-references for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Analyze variable usage for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Improve variable names in decompiled code for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Correct variable data types for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Set function prototype explicitly for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Verify calling convention for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Document logic differences between K1/TSL for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Analyze stack frame for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Identify and type all local variables for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Document all global variables accessed by all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Analyze exception handling for applicable functions (K1: count TBD, TSL: count TBD)
- [ ] Analyze inline assembly for functions that have it (K1: count TBD, TSL: count TBD)
- [ ] Add pre-line comments for all significant code blocks in all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Add end-of-line comments for complex operations in all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Add plate comments for function headers in all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Comments must reference both K1/TSL addresses where applicable (K1: 0/24231, TSL: 0/22596)
- [ ] Add bookmarks for all significant functions (K1: count TBD, TSL: count TBD)
- [ ] Add bookmarks for all entry points (K1: 0/unknown, TSL: 0/unknown)
- [ ] Tag functions appropriately for categorization (K1: 0/24231, TSL: 0/22596)
- [ ] Trace data flow for complex functions (K1: count TBD, TSL: count TBD)
- [ ] Analyze control flow for complex functions (K1: count TBD, TSL: count TBD)
- [ ] Document in progress file (K1: 0/24231, TSL: 0/22596)

### Undefined Function Candidates

- [ ] Get undefined function candidates count for TSL (K1: 3521, TSL: count TBD)
- [ ] Review all undefined candidates (K1: 0/3521 reviewed, TSL: 0/count TBD reviewed)
- [ ] Identify valid functions from candidates (K1: 0/3521+, TSL: 0/count TBD+)
- [ ] Create functions from valid candidates (K1: 0/3521+, TSL: 0/count TBD+)
- [ ] Determine function signatures for valid candidates (K1: 0/3521+, TSL: 0/count TBD+)
- [ ] Document invalid candidates as data/code (K1: 0/3521+, TSL: 0/count TBD+)
- [ ] Compare K1/TSL candidates and document address differences (K1: 0/3521+, TSL: 0/count TBD+)

## Structures

### For EVERY Structure

- [ ] Get full list of all structures (K1: 1009+ found, need complete list, TSL: count TBD - likely similar count)
- [ ] Match structures between K1 and TSL (K1: 0/1009+ matched, TSL: 0/count TBD matched)
- [ ] Get structure info (size, alignment, fields) for all structures (K1: 0/1009+, TSL: 0/count TBD)
- [ ] Verify structure size in both K1 and TSL for all structures (K1: 0/1009+, TSL: 0/count TBD)
- [ ] Verify structure alignment in both K1 and TSL for all structures (K1: 0/1009+, TSL: 0/count TBD)
- [ ] Document all fields with correct types for all structures (K1: 0/1009+, TSL: 0/count TBD)
- [ ] Determine meaningful field names for all structures (K1: 0/1009+ - all currently use placeholders, TSL: 0/count TBD - all currently use placeholders)
- [ ] Verify field offsets in both versions for all structures (K1: 0/1009+, TSL: 0/count TBD)
- [ ] Verify field types in both versions for all structures (K1: 0/1009+, TSL: 0/count TBD)
- [ ] Document field differences between K1/TSL for all structures (K1: 0/1009+, TSL: 0/count TBD)
- [ ] Add field comments for all structures (K1: 0/1009+, TSL: 0/count TBD)
- [ ] Analyze field usage in functions for all structures (K1: 0/1009+, TSL: 0/count TBD)
- [ ] Find all functions using each structure (K1: 0/1009+, TSL: 0/count TBD)
- [ ] Document structure purpose for all structures (K1: 0/1009+, TSL: 0/count TBD)
- [ ] Identify related structures for all structures (K1: 0/1009+, TSL: 0/count TBD)
- [ ] Document inheritance hierarchy for applicable structures (K1: count TBD, TSL: count TBD)
- [ ] Identify virtual function tables for applicable structures (K1: count TBD, TSL: count TBD)
- [ ] Analyze structure packing/padding for all structures (K1: 0/1009+, TSL: 0/count TBD)
- [ ] Generate C header representation for all structures (K1: 0/1009+, TSL: 0/count TBD)
- [ ] Verify structure size matches usage for all structures (K1: 0/1009+, TSL: 0/count TBD)

### Priority Structures

- [ ] CAppManager - find, document, verify (K1: 0/1, TSL: 0/1)
- [ ] CServerExoApp - find, document, verify (K1: 0/1, TSL: 0/1)
- [ ] CClientExoApp - find, document, verify (K1: 0/1, TSL: 0/1)
- [ ] CObjectTableManager - find, document, verify (K1: 0/1, TSL: 0/1)
- [ ] CSWReentrantServerStats - complete documentation (field names need improvement) (K1: 0/1, TSL: 0/1)
- [ ] CExoString - verify completeness (K1: 0/1, TSL: 0/1)
- [ ] CGameObject - find, document, verify (K1: 0/1, TSL: 0/1)
- [ ] CSWSCreature - find, document, verify (K1: 0/1, TSL: 0/1)
- [ ] CSWSItem - find, document, verify (K1: 0/1, TSL: 0/1)
- [ ] CResRef - find, document, verify (K1: 0/1, TSL: 0/1)
- [ ] All Exo engine structures - find, document, verify (K1: count TBD, 0/count TBD, TSL: count TBD, 0/count TBD)
- [ ] All Star Wars game-specific structures - find, document, verify (K1: count TBD, 0/count TBD, TSL: count TBD, 0/count TBD)
- [ ] All remaining structures - complete (K1: 0/1009+, TSL: 0/count TBD+)

## Data Types

### Built-in Types

- [ ] Verify built-in types archive (K1: verified, TSL: count TBD)
- [ ] Document all built-in types (K1: 0/116, TSL: 0/116)

### Custom Types

- [ ] Get custom types archive (K1: 2653 types, TSL: count TBD)
- [ ] Extract and list all types from archive (K1: 0/2653, TSL: 0/count TBD)
- [ ] Match types between K1 and TSL (K1: 0/2653+, TSL: 0/count TBD+)
- [ ] Document all custom types (K1: 0/2653+, TSL: 0/count TBD+)
- [ ] Compare types between K1/TSL and document differences (K1: 0/2653+, TSL: 0/count TBD+)
- [ ] Categorize all types appropriately (K1: 0/2653+, TSL: 0/count TBD+)
- [ ] Map type dependencies for all types (K1: 0/2769+, TSL: 0/count TBD+)

### Enums

- [ ] Identify all enums (K1: count TBD, TSL: count TBD)
- [ ] Document enum values with names for all enums (K1: 0/count TBD, TSL: 0/count TBD)
- [ ] Cross-reference enum usage for all enums (K1: 0/count TBD, TSL: 0/count TBD)
- [ ] Map enum values to constants (K1: 0/count TBD, TSL: 0/count TBD)

### Typedefs

- [ ] Identify all typedefs (K1: count TBD, TSL: count TBD)
- [ ] Document typedef base types for all typedefs (K1: 0/count TBD, TSL: 0/count TBD)
- [ ] Cross-reference typedef usage for all typedefs (K1: 0/count TBD, TSL: 0/count TBD)

### Unions

- [ ] Identify all unions (K1: count TBD, TSL: count TBD)
- [ ] Document union fields for all unions (K1: 0/count TBD, TSL: 0/count TBD)
- [ ] Cross-reference union usage for all unions (K1: 0/count TBD, TSL: 0/count TBD)

### Arrays

- [ ] Document all array types (K1: count TBD, TSL: count TBD)
- [ ] Verify array element types for all arrays (K1: 0/count TBD, TSL: 0/count TBD)
- [ ] Determine array sizes for all arrays (K1: 0/count TBD, TSL: 0/count TBD)

## Strings

### String Extraction

- [ ] Get total string count (K1: count TBD, TSL: count TBD)
- [ ] Extract all strings (K1: 0/unknown, TSL: 0/unknown)
- [ ] Match strings between K1 and TSL (same string, different addresses) (K1: 0/unknown, TSL: 0/unknown)
- [ ] Identify string encoding for all strings (ASCII/Unicode/UTF-8/etc.) (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document string addresses for both versions together (K1: 0/unknown, TSL: 0/unknown)
- [ ] Identify and consolidate duplicate strings (K1: 0/unknown, TSL: 0/unknown)

### String Analysis

- [ ] Cross-reference all strings to functions (K1: 0/unknown, TSL: 0/unknown)
- [ ] Cross-reference all strings to data (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document string usage contexts for all strings (K1: 0/unknown, TSL: 0/unknown)
- [ ] Identify format strings (printf-style, etc.) for all applicable strings (K1: 0/unknown, TSL: 0/unknown)
- [ ] Categorize error messages (K1: 0/unknown, TSL: 0/unknown)
- [ ] Identify debug strings (K1: 0/unknown, TSL: 0/unknown)
- [ ] Identify resource strings (K1: 0/unknown, TSL: 0/unknown)
- [ ] Perform string similarity analysis to find variations (K1: 0/unknown, TSL: 0/unknown)
- [ ] Add comments at all string locations (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document string content differences between versions (K1: 0/unknown, TSL: 0/unknown)

## Symbols

### Symbol Analysis

- [ ] List all symbols (K1: count TBD, 0 listed, TSL: count TBD, 0 listed)
- [ ] Match symbols between K1/TSL (same symbol, different addresses) (K1: 0/unknown, TSL: 0/unknown)
- [ ] Categorize symbol types (function/data/label) for all symbols (K1: 0/unknown, TSL: 0/unknown)
- [ ] Replace default names (FUN_, DAT_, etc.) with meaningful names for all symbols (K1: 0/unknown - unified names, TSL: 0/unknown - unified names)
- [ ] Identify external symbols (K1: 0/unknown, TSL: 0/unknown)
- [ ] Verify symbol addresses (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document symbol sizes (K1: 0/unknown, TSL: 0/unknown)
- [ ] Map symbol references (K1: 0/unknown, TSL: 0/unknown)

### Labels

- [ ] Create labels at all significant addresses (K1: count TBD, TSL: count TBD)
- [ ] Make label names meaningful (K1: 0/count TBD, TSL: 0/count TBD)
- [ ] Categorize labels (function entry, loop start, data, etc.) (K1: 0/count TBD, TSL: 0/count TBD)

## Imports

### Import Analysis

- [ ] Document all imports with signatures and addresses (K1: 0/349, TSL: 0/349)
- [ ] Match imports between K1 and TSL (same import, different addresses) (K1: 0/349, TSL: 0/349)
- [ ] Compare import addresses (K1 vs TSL) for each import (K1: 0/349, TSL: 0/349)
- [ ] Find all call sites for each import (K1: 0/349, TSL: 0/349)
- [ ] Document usage context for each import (K1: 0/349, TSL: 0/349)
- [ ] Resolve import thunks (K1: 0/349, TSL: 0/349)
- [ ] Document import thunk chains (K1: 0/349, TSL: 0/349)
- [ ] Analyze IAT (Import Address Table) (K1: 0/1, TSL: 0/1)
- [ ] Document import ordinal numbers (K1: 0/349, TSL: 0/349)
- [ ] Analyze import name vs ordinal usage (K1: 0/349, TSL: 0/349)

### Import Libraries

- [ ] BINKW32.DLL - 19 imports (K1: 0/19 documented with both addresses, TSL: 0/19 documented with both addresses)
- [ ] DINPUT8.DLL - 1 import (K1: 0/1 documented with both addresses, TSL: 0/1 documented with both addresses)
- [ ] GDI32.DLL - 7 imports (K1: 0/7 documented with both addresses, TSL: 0/7 documented with both addresses)
- [ ] GLU32.DLL - 3 imports (K1: 0/3 documented with both addresses, TSL: 0/3 documented with both addresses)
- [ ] IMM32.DLL - 5 imports (K1: 0/5 documented with both addresses, TSL: 0/5 documented with both addresses)
- [ ] KERNEL32.DLL - Many imports (K1: count TBD, 0 documented with both addresses, TSL: count TBD, 0 documented with both addresses)
- [ ] Additional libraries - identify all, document all (K1: count TBD, 0 documented, TSL: count TBD, 0 documented)

## Exports

### Export Analysis

- [ ] Get export list (K1: 1, TSL: count TBD)
- [ ] Match exports between K1 and TSL (same export, different addresses) (K1: 0/1, TSL: 0/count TBD)
- [ ] Document export signatures (K1: 0/1+, TSL: 0/count TBD+)
- [ ] Analyze export usage (who calls exported functions) (K1: 0/1+, TSL: 0/count TBD+)
- [ ] Compare export addresses between versions (K1: 0/1+, TSL: 0/count TBD+)
- [ ] Document export ordinal numbers (K1: 0/1+, TSL: 0/count TBD+)
- [ ] Analyze export names vs ordinals (K1: 0/1+, TSL: 0/count TBD+)

## Memory Blocks

### Memory Block Analysis

- [ ] Get memory blocks (K1: 7, TSL: count TBD)
- [ ] Compare memory block layouts (K1 vs TSL) (K1: 0/7, TSL: 0/count TBD)
- [ ] Document memory block purposes (K1: 0/7, TSL: 0/count TBD)
- [ ] Verify memory block permissions (K1: 0/7, TSL: 0/count TBD)
- [ ] Verify memory block sizes (K1: 0/7, TSL: 0/count TBD)
- [ ] Analyze memory block mappings (K1: 0/7, TSL: 0/count TBD)
- [ ] Identify overlay memory blocks (K1: 0/7, TSL: 0/count TBD)
- [ ] Identify volatile memory blocks (K1: 0/7, TSL: 0/count TBD)
- [ ] Verify memory block initialization status (K1: 0/7, TSL: 0/count TBD)
- [ ] Analyze memory block contents where applicable (K1: 0/7, TSL: 0/count TBD)
- [ ] Document .text section organization (K1: 0/1, TSL: 0/1, compare)
- [ ] Document .rdata section (read-only data) (K1: 0/1, TSL: 0/1, compare)
- [ ] Document .data section (initialized data) (K1: 0/1, TSL: 0/1, compare)
- [ ] Document .rsrc section (resources) (K1: 0/1, TSL: 0/1, compare)
- [ ] Identify and document data structures in memory (K1: 0/unknown, TSL: 0/unknown)
- [ ] Map global variables to memory addresses (unified names) (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document memory layout (both versions side by side) (K1: 0/1, TSL: 0/1)
- [ ] Compare memory layout between K1 and TSL (address differences, size differences) (K1: 0/1, TSL: 0/1)

## Cross-References

### Cross-Reference Analysis

- [ ] Verify all code references (K1: 0/unknown, TSL: 0/unknown)
- [ ] Verify all data references (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document reference directions (to/from/both) for all references (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document reference context (call site, usage context) for all references (K1: 0/unknown, TSL: 0/unknown)
- [ ] Categorize reference types (call/jump/read/write/offset) for all references (K1: 0/unknown, TSL: 0/unknown)
- [ ] Resolve all indirect references (K1: 0/unknown, TSL: 0/unknown)
- [ ] Trace all reference chains (K1: 0/unknown, TSL: 0/unknown)

### Call Graph

- [ ] Generate call graph for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Generate call trees (callers and callees) for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Identify common callers for related functions (K1: 0/unknown, TSL: 0/unknown)
- [ ] Detect call cycles (K1: 0/unknown, TSL: 0/unknown)
- [ ] Identify all entry points (main, WinMain, DLL exports, etc.) (K1: 0/unknown, TSL: 0/unknown)

### Data Flow

- [ ] Trace data flow forward for all variables (K1: 0/unknown, TSL: 0/unknown)
- [ ] Trace data flow backward for all variables (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document variable accesses (reads/writes) for all variables (K1: 0/unknown, TSL: 0/unknown)
- [ ] Map data dependencies for all variables (K1: 0/unknown, TSL: 0/unknown)

## Constants

### Constant Analysis

- [ ] Identify common constants (top 50+ constants) (K1: 0/50, TSL: 0/50)
- [ ] Identify and name all magic numbers (K1: 0/unknown, TSL: 0/unknown)
- [ ] Find constant value uses for all constants (K1: 0/unknown, TSL: 0/unknown)
- [ ] Analyze constant ranges (K1: 0/unknown, TSL: 0/unknown)
- [ ] Map enum values to constants (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document error codes (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document flags and bitmasks (K1: 0/unknown, TSL: 0/unknown)

## Virtual Function Tables (VTables)

### VTable Analysis

- [ ] Find all vtables (K1: count TBD, 0 found, TSL: count TBD, 0 found)
- [ ] Match vtables between K1 and TSL (same class, different addresses) (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document vtable addresses for all vtables (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document all function pointers in all vtables (K1: 0/unknown, TSL: 0/unknown)
- [ ] Map slot indices to functions for all vtables (K1: 0/unknown, TSL: 0/unknown)
- [ ] Find all classes using each vtable (K1: 0/unknown, TSL: 0/unknown)
- [ ] Find all call sites for each vtable function (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document vtable inheritance for all vtables (K1: 0/unknown, TSL: 0/unknown)
- [ ] Compare vtable between K1 and TSL (size, function pointers, slot differences) for all vtables (K1: 0/unknown, TSL: 0/unknown)
- [ ] Build vtable inheritance hierarchy (unified hierarchy) (K1: 0/1, TSL: 0/1)
- [ ] Document C++ class structures (K1: 0/unknown, TSL: 0/unknown)

## Comments

### Comment Management

- [ ] Add comments to all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Add pre-line comments for all significant code blocks in all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Add end-of-line comments for complex operations in all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Add plate comments for function headers in all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Ensure comments reference both K1/TSL addresses where applicable (K1: 0/24231, TSL: 0/22596)
- [ ] Add repeatable comments where needed (K1: count TBD, TSL: count TBD)
- [ ] Use comment search functionality to find existing patterns (K1: 0/unknown, TSL: 0/unknown)
- [ ] Verify comment accuracy (K1: 0/24231, TSL: 0/22596)

## Bookmarks

### Bookmark Management

- [ ] Add bookmarks to all significant functions (K1: 0/24231, TSL: 0/22596)
- [ ] Add bookmarks to all entry points (K1: 0/unknown, TSL: 0/unknown)
- [ ] Add bookmarks to important data structures (K1: 0/unknown, TSL: 0/unknown)
- [ ] Categorize all bookmarks appropriately (K1: 0/unknown, TSL: 0/unknown)
- [ ] Use bookmark search functionality to find existing bookmarks (K1: 0/unknown, TSL: 0/unknown)
- [ ] Update bookmark comments with detailed information (K1: 0/unknown, TSL: 0/unknown)
- [ ] Link bookmarks between K1/TSL equivalent locations (K1: 0/unknown, TSL: 0/unknown)

## Thunks

### Thunk Analysis

- [ ] Identify all thunks (K1: count TBD, 0 identified, TSL: count TBD, 0 identified)
- [ ] Resolve all thunk chains (target functions found) (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document thunk purposes (import thunks, export thunks, etc.) for all thunks (K1: 0/unknown, TSL: 0/unknown)
- [ ] Identify thunk call sites for all thunks (K1: 0/unknown, TSL: 0/unknown)

## Data Type Archives

### Archive Analysis

- [ ] Extract all types from BuiltInTypes archive (K1: 0/116, TSL: 0/116)
- [ ] Extract all types from archive (K1: 0/2653, TSL: count TBD, 0/count TBD)
- [ ] Analyze type categories for all types (K1: 0/2769+, TSL: 0/count TBD+)
- [ ] Document type dependencies for all types (K1: 0/2769+, TSL: 0/count TBD+)
- [ ] Understand archive structure (K1: 0/1, TSL: 0/1)

## Address Tables

### Address Table Analysis

- [ ] Identify all address tables (K1: count TBD, 0 identified, TSL: count TBD, 0 identified)
- [ ] Document address table sizes for all tables (K1: 0/unknown, TSL: 0/unknown)
- [ ] Determine address table purposes (switch tables, vtables, jump tables, etc.) for all tables (K1: 0/unknown, TSL: 0/unknown)
- [ ] Resolve address table entries for all tables (K1: 0/unknown, TSL: 0/unknown)
- [ ] Cross-reference address table usage for all tables (K1: 0/unknown, TSL: 0/unknown)

## Data Analysis

### Data at Addresses

- [ ] Analyze significant data addresses (K1: 0/unknown, TSL: 0/unknown)
- [ ] Identify and type all global variables (K1: 0/unknown, TSL: 0/unknown)
- [ ] Identify all static variables (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document data initialization values for all data (K1: 0/unknown, TSL: 0/unknown)
- [ ] Cross-reference data usage for all data (K1: 0/unknown, TSL: 0/unknown)

## Function Tags

### Tagging

- [ ] Create function tags for categorization (K1: 0/24231, TSL: 0/22596)
- [ ] Define tag taxonomy (K1: 0/1, TSL: 0/1)
- [ ] Apply tags consistently to all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Ensure tagged functions are searchable (K1: 0/1, TSL: 0/1)

## Variable Renaming

### Renaming

- [ ] Improve variable names in decompiled code for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Improve parameter names for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Improve local variable names for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Improve global variable names (K1: 0/unknown, TSL: 0/unknown)
- [ ] Establish and document naming conventions (K1: 0/1, TSL: 0/1)

## Data Type Correction

### Type Correction

- [ ] Correct variable data types in decompiled code for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Verify and correct parameter types for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Verify and correct return types for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Correct structure field types for all structures (K1: 0/1009+, TSL: 0/count TBD+)
- [ ] Identify and resolve all type mismatches (K1: 0/unknown, TSL: 0/unknown)

## C Headers Generation

### Header Files

- [ ] Generate C header files for all structures (K1: 0/1009+, TSL: 0/count TBD+)
- [ ] Generate C header files for all enums (K1: 0/unknown, TSL: 0/unknown)
- [ ] Generate C header files for all typedefs (K1: 0/unknown, TSL: 0/unknown)
- [ ] Organize headers by category (K1: 0/1, TSL: 0/1)
- [ ] Add proper documentation to all headers (K1: 0/unknown, TSL: 0/unknown)
- [ ] Add include guards to all headers (K1: 0/unknown, TSL: 0/unknown)
- [ ] Add dependency includes to all headers (K1: 0/unknown, TSL: 0/unknown)
- [ ] Verify all headers compile (K1: 0/unknown, TSL: 0/unknown)

## Function Prototypes

### Prototype Management

- [ ] Set function prototypes explicitly for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Verify calling conventions for all prototypes (K1: 0/24231, TSL: 0/22596)
- [ ] Verify parameter types for all prototypes (K1: 0/24231, TSL: 0/22596)
- [ ] Verify return types for all prototypes (K1: 0/24231, TSL: 0/22596)

## Decompilation Comments

### Decompilation Enhancement

- [ ] Add line-by-line comments to decompiled code for all functions (K1: 0/24231, TSL: 0/22596)
- [ ] Explain complex operations for all applicable functions (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document algorithm logic for all applicable functions (K1: 0/unknown, TSL: 0/unknown)
- [ ] Identify and comment optimization patterns (K1: 0/unknown, TSL: 0/unknown)

## Code Discovery

### Discovery Tasks

- [ ] Analyze all undefined function candidates (K1: 0/3521+, TSL: 0/count TBD+)
- [ ] Create functions from valid candidates (K1: 0/3521+, TSL: 0/count TBD+)
- [ ] Analyze code found from operand references (K1: many bookmarks exist, 0 analyzed, TSL: count TBD, 0 analyzed)
- [ ] Identify and document non-returning functions (K1: 0/unknown, TSL: 0/unknown)
- [ ] Identify and document exception handlers (K1: 0/unknown, TSL: 0/unknown)
- [ ] Analyze SEH (Structured Exception Handling) (K1: 0/1, TSL: 0/1)

## Control Flow Analysis

- [ ] Identify all loops in all functions (K1: 0/unknown, TSL: 0/unknown)
- [ ] Identify all branches in all functions (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document control flow patterns for all applicable functions (K1: 0/unknown, TSL: 0/unknown)
- [ ] Identify state machines (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document algorithm implementations for all algorithms (K1: 0/unknown, TSL: 0/unknown)

## Data Flow Analysis

- [ ] Trace all significant data flows (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document data transformations for all applicable functions (K1: 0/unknown, TSL: 0/unknown)
- [ ] Identify data validation points (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document data corruption vulnerabilities if any (K1: 0/unknown, TSL: 0/unknown)

## Exception Handling

- [ ] Identify all exception handlers (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document SEH structures (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document C++ exception handling (K1: 0/unknown, TSL: 0/unknown)
- [ ] Map exception handling flow (K1: 0/unknown, TSL: 0/unknown)

## Optimization Analysis

- [ ] Identify compiler optimizations (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document inline functions (K1: 0/unknown, TSL: 0/unknown)
- [ ] Document optimized patterns (K1: 0/unknown, TSL: 0/unknown)
- [ ] Identify hand-optimized assembly (K1: 0/unknown, TSL: 0/unknown)

## Reva MCP Tools

### Tools Not Yet Used

- [ ] mcp_reva_get-functions-by-similarity - Find similar functions (K1: 0/24231, TSL: 0/22596)
- [ ] mcp_reva_set-function-prototype - Set explicit prototypes (K1: 0/24231, TSL: 0/22596)
- [ ] mcp_reva_create-function - Create undefined functions (K1: 0/3521+ candidates, TSL: 0/count TBD+ candidates)
- [ ] mcp_reva_function-tags - Tag functions for categorization (K1: 0/24231, TSL: 0/22596)
- [ ] mcp_reva_rename-variables - Rename variables in decompiled code (K1: 0/24231, TSL: 0/22596)
- [ ] mcp_reva_change-variable-datatypes - Correct variable types (K1: 0/24231, TSL: 0/22596)
- [ ] mcp_reva_set-decompilation-comment - Add decompilation comments (K1: 0/24231, TSL: 0/22596)
- [ ] mcp_reva_get-callers-decompiled - Bulk decompilation of callers (K1: 0/24231, TSL: 0/22596)
- [ ] mcp_reva_get-referencers-decompiled - Bulk decompilation of referencers (K1: 0/unknown, TSL: 0/unknown)
- [ ] mcp_reva_read-memory - Read memory at specific addresses (K1: 0/unknown, TSL: 0/unknown)
- [ ] mcp_reva_list-project-files - Project structure analysis (K1: 0/1, TSL: 0/1)
- [ ] mcp_reva_checkin-program - Version control checkins (K1: 0/1, TSL: 0/1)
- [ ] mcp_reva_analyze-program - Run auto-analysis (verify both versions) (K1: 0/1, TSL: 0/1)
- [ ] mcp_reva_change-processor - Verify processor settings (K1: 0/1, TSL: 0/1)
- [ ] mcp_reva_import-file - Import additional files if needed (K1: TBD, TSL: TBD)
- [ ] mcp_reva_find-cross-references - Get cross-references (K1: 0/24231 functions, TSL: 0/22596 functions)
- [ ] mcp_reva_get-data-types - Get data types from archives (K1: 0/2769+, TSL: 0/count TBD+)
- [ ] mcp_reva_get-data-type-by-string - Find specific types (K1: 0/unknown, TSL: 0/unknown)
- [ ] mcp_reva_parse-c-structure - Parse C structures (K1: 0/1009+, TSL: 0/count TBD+)
- [ ] mcp_reva_validate-c-structure - Validate structure definitions (K1: 0/1009+, TSL: 0/count TBD+)
- [ ] mcp_reva_create-structure - Create new structures if needed (K1: TBD, TSL: TBD)
- [ ] mcp_reva_add-structure-field - Add fields to structures (K1: 0/1009+, TSL: 0/count TBD+)
- [ ] mcp_reva_modify-structure-field - Modify structure fields (K1: 0/1009+, TSL: 0/count TBD+)
- [ ] mcp_reva_apply-structure - Apply structures at addresses (K1: 0/unknown, TSL: 0/unknown)
- [ ] mcp_reva_parse-c-header - Parse C headers in bulk (K1: 0/1009+, TSL: 0/count TBD+)
- [ ] mcp_reva_get-comments - Get comments at addresses (K1: 0/unknown, TSL: 0/unknown)
- [ ] mcp_reva_search-comments - Search for comment patterns (K1: 0/unknown, TSL: 0/unknown)
- [ ] mcp_reva_get-bookmarks - Search bookmarks (K1: 0/unknown, TSL: 0/unknown)
- [ ] mcp_reva_search-bookmarks - Search bookmark patterns (K1: 0/unknown, TSL: 0/unknown)
- [ ] mcp_reva_find-import-references - Find import usage (K1: 0/349, TSL: 0/349)
- [ ] mcp_reva_resolve-thunk - Resolve thunk chains (K1: 0/unknown, TSL: 0/unknown)
- [ ] mcp_reva_trace-data-flow-backward - Trace data flow (K1: 0/unknown, TSL: 0/unknown)
- [ ] mcp_reva_trace-data-flow-forward - Trace data flow (K1: 0/unknown, TSL: 0/unknown)
- [ ] mcp_reva_find-variable-accesses - Find variable accesses (K1: 0/unknown, TSL: 0/unknown)
- [ ] mcp_reva_get-call-graph - Get call graphs (K1: 0/24231, TSL: 0/22596)
- [ ] mcp_reva_get-call-tree - Get call trees (K1: 0/24231, TSL: 0/22596)
- [ ] mcp_reva_find-common-callers - Find common callers (K1: 0/unknown, TSL: 0/unknown)
- [ ] mcp_reva_find-constant-uses - Find constant usage (K1: 0/unknown, TSL: 0/unknown)
- [ ] mcp_reva_find-constants-in-range - Find constants in ranges (K1: 0/unknown, TSL: 0/unknown)
- [ ] mcp_reva_analyze-vtable - Analyze vtables (K1: 0/unknown, TSL: 0/unknown)
- [ ] mcp_reva_find-vtable-callers - Find vtable callers (K1: 0/unknown, TSL: 0/unknown)
- [ ] mcp_reva_find-vtables-containing-function - Find vtables with function (K1: 0/unknown, TSL: 0/unknown)
- [ ] mcp_reva_get-strings-by-similarity - Find similar strings (K1: 0/unknown, TSL: 0/unknown)
- [ ] mcp_reva_search-strings-regex - Search strings with regex (K1: 0/unknown, TSL: 0/unknown)
- [ ] mcp_reva_get-data - Get data at addresses (K1: 0/unknown, TSL: 0/unknown)
- [ ] mcp_reva_create-label - Create labels at addresses (K1: 0/unknown, TSL: 0/unknown)
- [ ] mcp_reva_get-memory-blocks - Get memory blocks (K1: 7, 0/7, TSL: count TBD, 0/count TBD)
- [ ] mcp_reva_list-structures - Get full structure list for both versions (K1: 0/1, TSL: 0/1)
- [ ] mcp_reva_get-structure-info - Get info for all structures (K1: 0/1009+, TSL: 0/count TBD+)
- [ ] mcp_reva_list-exports - Get exports (K1: 0/1, TSL: 0/1)
- [ ] mcp_reva_get-undefined-function-candidates - Get undefined function candidates (K1: 3521, 0/3521, TSL: count TBD, 0/count TBD)

## Verification and Quality Assurance

- [ ] Verify all function signatures are correct (K1: 0/24231, TSL: 0/22596)
- [ ] Verify all structure definitions are correct (K1: 0/1009+, TSL: 0/count TBD+)
- [ ] Verify all cross-references are accurate (K1: 0/unknown, TSL: 0/unknown)
- [ ] Verify all addresses are correct (K1: 0/unknown, TSL: 0/unknown)
- [ ] Verify all comments are accurate (K1: 0/24231, TSL: 0/22596)
- [ ] Verify C headers compile and match structures (K1: 0/1009+, TSL: 0/count TBD+)
- [ ] Verify naming consistency (unified names for both versions) (K1: 0/1, TSL: 0/1)
- [ ] Verify documentation completeness (K1: 0/1, TSL: 0/1)
- [ ] Test generated code against original (K1: 0/1, TSL: 0/1)

## Summary Statistics

- **Total Functions to Complete**: 46,827 (24,231 K1 + 22,596 TSL)
- **Total Structures to Complete**: 1,009+ (both versions)
- **Total Data Types to Complete**: 2,769+ (both versions)
- **Total Imports to Document**: 698 (349 K1 + 349 TSL)
- **Total Strings to Extract**: Unknown (both versions)
- **Total Symbols to Process**: Unknown (both versions)
- **Total VTables to Document**: Unknown (both versions)
- **Total Thunks to Resolve**: Unknown (both versions)
- **Total Comments to Add**: 46,827+ functions (both versions)
- **Total Bookmarks to Add**: Unknown (both versions)
- **Total Cross-References to Verify**: Unknown (both versions)

**Goal**: 100% exhaustive reverse engineering documentation within Ghidra for both executables. Every function, structure, data type, string, import, export, cross-reference, vtable, thunk, comment, and bookmark must be documented with both K1 and TSL addresses together.
