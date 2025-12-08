# Steam vs GOG KOTOR: Technical Differences

## Overview

This document describes the technical differences between the Steam and GOG versions of Star Wars: Knights of the Old Republic (`swkotor.exe`) as observed through static analysis in Ghidra. The GOG version is DRM-free and can be analyzed directly, while the Steam version uses packing/DRM protection that encrypts the executable's code section.

## Quick Summary

**Key Finding**: Both versions are functionally identical. The Steam version adds a runtime decryption packer that:
- Encrypts the `.text` section (3.3 MB of game code) on disk
- Redirects entry point from `0x00401000` (`.text`) to `0x0086d2ed` (`.bind` section unpacker stub)
- Decrypts `.text` in memory at runtime before executing game code
- Maintains identical memory layout - all addresses match once unpacked

**Ghidra Analysis**: GOG version shows ~24,232 functions; Steam packed version shows only ~6 functions (unpacker stub). After dumping Steam from memory, all addresses and functions match GOG exactly.

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

**Critical Finding**: Both versions use **identical memory layouts** for all game code and data sections. Once unpacked, all addresses match exactly.

**Memory Map**: `.text` (0x00401000-0x0073cfff, 3.3 MB), `.rdata` (0x0073d000-0x0078cfff, 320 KB), `.data` (0x0078d000-0x00835497, 673 KB). Steam adds `.bind` (0x0086d000-0x008c2fff, 344 KB) for unpacker stub.

## Packing Methodology

**Protection Type**: Runtime decryption packer (SecuROM-like). Process: (1) `.text` encrypted on disk, (2) Entry point redirected to unpacker stub at `0x0086d2ed` (`.bind` section), (3) Stub decrypts `.text` in memory, (4) Jumps to original entry point `0x00401000`.

**Encryption**: Only `.text` section encrypted; `.rdata` and `.data` remain unencrypted (strings/data visible). Encryption algorithm unknown (requires unpacker stub analysis). Decryption occurs during process initialization.

## Ghidra Analysis Results

**GOG**: Auto-analysis identifies ~24,232 functions; full disassembly/decompilation available.

**Steam (Packed)**: Only ~6 functions detected (unpacker stub in `.bind`); `.text` appears as encrypted garbage; import tables visible but no internal symbols.

**Steam (Unpacked)**: Identical to GOG - all ~24,232 functions detected, addresses match exactly.

## Low-Level PE Structure Details

**Entry Point**: GOG = `0x00401000` (`.text`), Steam = `0x0086d2ed` (`.bind`). This is the primary packing indicator.

**Section Headers**: `.text`, `.rdata`, `.data` identical in both (same VirtualAddress, SizeOfRawData, Characteristics). Steam adds `.bind` section (0x0086d000, 0x00056000, read/write).

**IAT**: Identical in both versions, located in `.rdata` (unencrypted), same DLLs/functions.

## Code Analysis Implications

**Function Detection**: GOG - standard x86 prologue pattern matching works. Steam (packed) - fails in `.text` (encrypted), only stub functions detected.

**String Analysis**: Identical strings in `.rdata` (unencrypted), same addresses. Allows partial Steam analysis when packed.

**Data Structures**: Identical global variables, VTables, and static data in `.data` section (same addresses/layouts).

## Reverse Engineering Implications

**Address Compatibility**: Once Steam is unpacked, all GOG reverse engineering data applies directly (functions, data structures, strings, VTables - all addresses match exactly).

**Workflow**: GOG - load directly, auto-analyze, apply RE data. Steam - load packed (stub only), dump from memory, load dump, auto-analyze, apply RE data (addresses match).

## Technical Specifications

**Format**: x86 PE32, Image Base `0x00400000`, Windows GUI subsystem (both versions).

**Compiler**: Same compiler/settings (identical memory layout/addresses indicate same version, optimization, linker, source code). Calling conventions: `__cdecl`/`__thiscall`, 4-byte stack alignment, `ebp`-based frames, SEH.

**Code Generation**: Identical except Steam adds packing/DRM layer.

## Conclusion

Steam and GOG versions are functionally identical. Steam adds a packing layer that encrypts `.text` on disk, redirects entry point to `.bind` unpacker stub, decrypts at runtime, and maintains identical memory layout. Once unpacked, all reverse engineering data applies to both versions without modification.
