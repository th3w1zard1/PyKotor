# Steam vs GOG KOTOR: Technical Differences

## Overview

This document describes the technical differences between the Steam and GOG versions of Star Wars: Knights of the Old Republic (`swkotor.exe`) as observed through static analysis in Ghidra. The GOG version is DRM-free and can be analyzed directly, while the Steam version uses packing/DRM protection that encrypts the executable's code section.

## Executive Summary

| Aspect | GOG Version | Steam Version |
|--------|-------------|--------------|
| **DRM Protection** | None | Packed/Encrypted |
| **Entry Point** | `0x00401000` (`.text` section) | `0x0086d2ed` (`.bind` section) |
| **`.text` Section** | Plain code, analyzable | Encrypted, unanalyzable |
| **Functions Detected** | ~24,232 functions | ~6 functions (unpacker stub only) |
| **Memory Layout** | Standard PE | Standard PE (identical to GOG) |
| **Additional Sections** | Standard sections | `.bind` section (unpacker stub) |

## PE Structure Analysis

### Entry Point Differences

**GOG Version:**
- **Entry Point RVA**: `0x00401000`
- **Section**: `.text`
- **Behavior**: Direct execution of game code
- **Ghidra Analysis**: Auto-analysis successfully identifies all functions

**Steam Version:**
- **Entry Point RVA**: `0x0086d2ed`
- **Section**: `.bind`
- **Behavior**: Execution begins in unpacker stub, which decrypts `.text` section before jumping to original entry point
- **Ghidra Analysis**: Only detects functions within the unpacker stub (~6 functions)

### Section Layout

Both versions share identical section layouts with one key difference:

#### Common Sections (Both Versions)

| Section | RVA Start | RVA End | Size | Purpose |
|---------|-----------|---------|------|---------|
| `.text` | `0x00401000` | `0x0073cfff` | `0x0033c000` (3,388,416 bytes) | Executable code |
| `.rdata` | `0x0073d000` | `0x0078cfff` | `0x00050000` (327,680 bytes) | Read-only data (strings, constants) |
| `.data` | `0x0078d000` | `0x00835497` | `0x000a8498` (689,304 bytes) | Writable data (global variables) |

#### Steam-Specific Section

| Section | RVA Start | RVA End | Size | Purpose |
|---------|-----------|---------|------|---------|
| `.bind` | `0x0086d000` | `0x008c2fff` | `0x00056000` (352,256 bytes) | Unpacker stub and DRM code |

**Note**: The `.bind` section is unique to the Steam version and contains the unpacker stub that decrypts the `.text` section at runtime.

## Memory Layout Compatibility

**Critical Finding**: Both versions use **identical memory layouts** for all game code and data sections. This means:

1. **Address Compatibility**: Once the Steam version is unpacked (dumped from memory), all addresses from GOG version reverse engineering data apply directly
2. **No Code Relocation**: The packing protection does not relocate code - it only encrypts the `.text` section at rest
3. **Runtime Decryption**: The `.text` section is decrypted in memory at runtime, but the virtual addresses remain unchanged

### Memory Map (Both Versions)

```
0x00400000  ┌─────────────────┐
            │   PE Header     │
            │   DOS Stub      │
0x00401000  ├─────────────────┤
            │                 │
            │   .text         │  ← Game code (encrypted in Steam)
            │   (3.3 MB)      │
0x0073d000  ├─────────────────┤
            │                 │
            │   .rdata        │  ← Strings, constants
            │   (320 KB)      │
0x0078d000  ├─────────────────┤
            │                 │
            │   .data         │  ← Global variables
            │   (673 KB)      │
0x00835497  ├─────────────────┤
            │   (gap)         │
0x0086d000  ├─────────────────┤  ← Steam only
            │                 │
            │   .bind         │  ← Unpacker stub (Steam only)
            │   (344 KB)      │
0x008c2fff  └─────────────────┘
```

## Packing Methodology

### Protection Type

The Steam version uses a **runtime decryption packer** (similar to SecuROM or other commercial DRM solutions). The protection methodology follows this pattern:

1. **Static Encryption**: The `.text` section is encrypted on disk
2. **Entry Point Redirection**: PE header's `AddressOfEntryPoint` is modified to point to the unpacker stub
3. **Runtime Decryption**: The unpacker stub decrypts the `.text` section in memory
4. **Control Transfer**: After decryption, execution jumps to the original entry point (`0x00401000`)

### Unpacker Stub Location

The unpacker stub resides in the `.bind` section:

- **Section RVA**: `0x0086d000`
- **Entry Point RVA**: `0x0086d2ed` (offset `0x2ed` from section start)
- **Size**: Approximately 344 KB (sufficient for complex decryption logic)

### Encryption Characteristics

Based on Ghidra analysis of the packed executable:

1. **Encrypted Section**: Only the `.text` section is encrypted
2. **Other Sections**: `.rdata` and `.data` sections remain unencrypted (strings and data are visible)
3. **Encryption Method**: Unknown algorithm (not simple XOR - requires analysis of unpacker stub)
4. **Decryption Timing**: Occurs during process initialization, before main game code executes

## Ghidra Analysis Results

### GOG Version Analysis

When loading the GOG version into Ghidra:

- **Auto-Analysis**: Successfully identifies ~24,232 functions
- **Function Recognition**: Standard x86 function prologues detected (`push ebp`, `mov ebp, esp`, etc.)
- **Code Analysis**: Full disassembly and decompilation available
- **Symbol Resolution**: Import tables, exports, and internal symbols resolved

### Steam Version Analysis (Packed)

When loading the Steam version into Ghidra:

- **Auto-Analysis**: Only identifies ~6 functions (all within `.bind` section)
- **Function Recognition**: Limited to unpacker stub code
- **Code Analysis**: `.text` section appears as encrypted/garbage data
- **Symbol Resolution**: Import tables visible (in `.rdata`), but no internal function symbols

### Steam Version Analysis (After Unpacking)

After dumping the unpacked executable from memory and loading into Ghidra:

- **Auto-Analysis**: Identifies all ~24,232 functions (identical to GOG)
- **Address Compatibility**: All addresses match GOG version exactly
- **Function Recognition**: Standard x86 prologues detected throughout `.text` section
- **Code Analysis**: Full disassembly and decompilation available

## Low-Level PE Structure Details

### Optional Header Differences

**GOG Version:**
```
AddressOfEntryPoint: 0x00401000
```

**Steam Version:**
```
AddressOfEntryPoint: 0x0086d2ed
```

The entry point difference is the primary indicator of packing. The Steam version's entry point points into the `.bind` section rather than the standard `.text` section.

### Section Headers

Both versions have identical section headers for `.text`, `.rdata`, and `.data`:

- **VirtualAddress**: Same in both versions
- **SizeOfRawData**: Same in both versions
- **Characteristics**: Same flags (executable, readable, writable as appropriate)

The Steam version has one additional section header for `.bind`:

```
Name: .bind
VirtualAddress: 0x0086d000
SizeOfRawData: 0x00056000
Characteristics: IMAGE_SCN_CNT_INITIALIZED_DATA | IMAGE_SCN_MEM_READ | IMAGE_SCN_MEM_WRITE
```

### Import Address Table (IAT)

Both versions have identical import tables:

- **Location**: `.rdata` section
- **Imports**: Same DLLs and functions
- **Addresses**: Resolved at runtime (not encrypted)

The IAT is not encrypted because it's in the `.rdata` section, which remains unencrypted.

## Code Analysis Implications

### Function Detection

**GOG Version:**
- Ghidra's auto-analysis uses pattern matching to detect function prologues
- Standard x86 calling conventions recognized
- Function boundaries identified automatically

**Steam Version (Packed):**
- Function detection fails in `.text` section due to encryption
- Only unpacker stub functions detected (in `.bind` section)
- Encrypted data does not match x86 instruction patterns

### String Analysis

Both versions have identical string data in `.rdata` section:

- **Visibility**: Strings are visible in both versions (not encrypted)
- **Location**: Same addresses in both versions
- **Content**: Identical strings (game text, error messages, etc.)

This allows partial analysis of the Steam version even when packed - string references can be analyzed, but code cannot.

### Data Structure Analysis

Both versions have identical data structures in `.data` section:

- **Global Variables**: Same addresses and layouts
- **VTables**: Same virtual function table addresses
- **Static Data**: Same initialization data

## Reverse Engineering Implications

### Address Compatibility

**Key Finding**: Once the Steam version is unpacked (dumped from memory), all reverse engineering data from the GOG version applies directly:

- Function addresses match exactly
- Data structure addresses match exactly
- String addresses match exactly
- VTable addresses match exactly

This means reverse engineering work done on the GOG version (such as "KOTOR RE Things") can be directly applied to the Steam version after unpacking.

### Analysis Workflow

**For GOG Version:**
1. Load `swkotor.exe` directly into Ghidra
2. Run auto-analysis
3. Apply reverse engineering data (function names, comments, etc.)

**For Steam Version:**
1. Load `swkotor.exe` into Ghidra (only unpacker stub visible)
2. Dump unpacked executable from memory (using Scylla, x64dbg, or similar)
3. Load dumped executable into Ghidra
4. Run auto-analysis (now all functions visible)
5. Apply reverse engineering data (addresses match GOG version)

## Technical Specifications

### Executable Format

- **Architecture**: x86 (32-bit)
- **Format**: PE32 (Portable Executable)
- **Image Base**: `0x00400000` (both versions)
- **Subsystem**: Windows GUI

### Compiler Characteristics

Both versions appear to be compiled with the same compiler and settings:

- **Calling Convention**: `__cdecl` and `__thiscall` (C++ classes)
- **Stack Alignment**: 4-byte aligned
- **Frame Pointers**: Standard `ebp`-based stack frames
- **Exception Handling**: Structured Exception Handling (SEH)

### Code Generation

The identical memory layout and function addresses indicate:

- Same compiler version
- Same optimization settings
- Same linker settings
- Same source code base

The only difference is the addition of the packing/DRM layer in the Steam version.

## Conclusion

The Steam and GOG versions of KOTOR are functionally identical at the code level. The Steam version adds a packing/DRM layer that:

1. Encrypts the `.text` section on disk
2. Redirects the entry point to an unpacker stub in the `.bind` section
3. Decrypts the `.text` section at runtime before executing game code
4. Maintains identical memory layout and addresses

This design allows the Steam version to be analyzed identically to the GOG version once the unpacked code is extracted from memory. All reverse engineering data, function addresses, and structure definitions apply to both versions without modification.

