# Aspyr KOTOR I Executable Analysis: swkotor_aspyr.exe

## Overview

This document provides analysis instructions for `swkotor_aspyr.exe` (KOTOR I Aspyr version) to determine the presence of encryption, packing, or DRM protection.

## Analysis Status

**Current Status**: File not yet analyzed. This document provides the methodology and checklist for analysis once the file is available.

**To Begin Analysis**: Provide the full path to `swkotor_aspyr.exe` and it will be imported into the Ghidra project for analysis.

## Import Analysis Findings (Using `manage-symbols` Tool)

### Comparison: Known Executables

**`swkotor.exe` (KOTOR I in project)**:
- **No `STEAM_API.DLL` imports** - Indicates GOG or non-Steam version
- Standard game libraries: BINKW32, DINPUT8, GDI32, GLU32, IMM32, KERNEL32, MSS32, OLE32, OPENGL32, USER32, VERSION
- Total: 349 imports across 11 libraries
- **Status**: Unpacked (24,097 functions detected)

**`swkotor2_aspyr.exe` (KOTOR II Aspyr)**:
- **Has `STEAM_API.DLL` imports** (10 functions) - Steam integration present
  - `SteamAPI_Init`, `SteamAPI_RunCallbacks`, `SteamUser`, `SteamApps`, `SteamUGC`, `SteamUserStats`, etc.
- Also imports `SHELL32.DLL` (`ShellExecuteA`)
- Standard game libraries: BINKW32, DINPUT8, GDI32, GLU32, IMM32, KERNEL32, MSS32, MSS32MIDI, OLE32, OPENGL32, USER32, VERSION, WINMM
- Total: 352 imports across 14 libraries
- **Status**: Unpacked (15,313 functions detected)

**Key Insight**: The presence of `STEAM_API.DLL` imports does **not** indicate packing/DRM. It indicates Steam integration for features like achievements, cloud saves, and Steam Workshop. The executable is still unpacked and DRM-free.

## Expected Analysis Workflow

### Step 1: Import and Initial Inspection

1. Import `swkotor_aspyr.exe` into Ghidra project using REVA MCP tools
2. Check PE structure (sections, entry point)
3. Count functions detected by auto-analysis
4. Examine `.text` section content

### Step 2: Packing/DRM Indicators Checklist

Based on analysis of `swkotor2_aspyr.exe` (KOTOR II Aspyr version) and comparison with packed Steam versions, check the following:

#### Entry Point Analysis

**Unpacked (Expected for Aspyr)**:
- Entry point: `0x00401000` or similar (within `.text` section)
- Standard C runtime initialization sequence
- Direct execution of game code

**Packed (Steam-style)**:
- Entry point: `0x0086d2ed` or similar (in `.bind` or custom section)
- Execution starts in unpacker stub
- Jump to original entry point after decryption

#### Section Layout

**Unpacked (Expected)**:
- Standard PE sections: `.text`, `.rdata`, `.data`, `.rsrc`, `tdb`
- No `.bind` or other custom unpacker sections
- `.text` section contains valid x86 code

**Packed**:
- Additional section: `.bind` (typically 300-400 KB)
- `.text` section contains encrypted/garbage data
- Unpacker stub in `.bind` section

#### Function Count

**Unpacked (Expected)**:
- KOTOR I: ~24,000+ functions detected
- Functions distributed throughout `.text` section
- Standard x86 function prologues (`55 8B EC`)

**Packed**:
- Only ~6-20 functions detected
- All functions in unpacker stub section
- `.text` section shows no functions

#### Code Section Content

**Unpacked (Expected)**:
```
0x00401000: 55 8B EC          push ebp; mov ebp, esp  (valid function prologue)
0x00401003: 83 EC 20         sub esp, 0x20
0x00401006: C7 45 FC ...     mov dword ptr [ebp-4], ...
```

**Packed**:
```
0x00401000: A7 3F 92 1E      (garbage/encrypted data)
0x00401004: 8C D4 7A 3F      (no valid x86 patterns)
0x00401008: F2 9B 4E 8A      (high entropy, encrypted)
```

### Step 3: Import and String Analysis

**Check for DRM-related imports**:
- `steam_api.dll` (Steam DRM)
- Anti-debugging APIs (may be present but unused)

**Check for packer/DRM strings**:
- `.bind`, `.upx`, `.pack`
- `SecuROM`, `Denuvo`, `StarForce`, `VMProtect`
- `steam_api.dll`

## Comparison Reference

### Known Unpacked Executable: swkotor2_aspyr.exe (KOTOR II)

| Aspect | Value | Analysis |
|--------|-------|----------|
| **Entry Point** | `0x0091d5a2` | In `.text` section (normal) |
| **Functions** | 15,313 | All game functions visible |
| **`.text` Section** | Plain code | Valid x86, fully analyzable |
| **Additional Sections** | None | Standard PE sections only |
| **DRM Protection** | None | Completely unpacked |

### Known Packed Executable: swkotor.exe (Steam KOTOR I)

| Aspect | Value | Analysis |
|--------|-------|----------|
| **Entry Point** | `0x0086d2ed` | In `.bind` section (unpacker stub) |
| **Functions** | ~6 | Only unpacker stub functions |
| **`.text` Section** | Encrypted | Garbage data, unanalyzable |
| **Additional Sections** | `.bind` (352 KB) | Unpacker stub and DRM code |
| **DRM Protection** | Runtime decryption packer | Requires memory dump |

## Expected Results for swkotor_aspyr.exe

Based on the analysis of `swkotor2_aspyr.exe` (KOTOR II Aspyr version), which was confirmed to be **completely unpacked and DRM-free**, it is **highly likely** that `swkotor_aspyr.exe` (KOTOR I Aspyr version) will also be unpacked.

**Expected Characteristics**:
- Entry point in `.text` section
- ~24,000+ functions detected
- Valid x86 code in `.text` section
- No `.bind` or other unpacker sections
- No DRM-related imports or strings
- Standard PE structure

## Unpacking Methodology (If Packed)

If analysis reveals that `swkotor_aspyr.exe` is packed (unlikely based on Aspyr's distribution model), use the following methodology:

### Method 1: Memory Dumping (Recommended)

1. **Identify Original Entry Point (OEP)**
   - Analyze unpacker stub in Ghidra
   - Find jump/call to original entry point (typically `0x00401000`)

2. **Dynamic Analysis**
   - Load in x64dbg
   - Set breakpoint on entry point
   - Step through unpacker stub
   - Set breakpoint on OEP

3. **Memory Dumping**
   - When OEP breakpoint hits, pause execution
   - Use Scylla (x64dbg plugin) to dump process
   - Fix imports with Scylla
   - Save as `swkotor_aspyr_unpacked.exe`

4. **Verification**
   - Load dumped executable in Ghidra
   - Run auto-analysis
   - Verify ~24,000+ functions detected
   - Confirm `.text` section contains valid code

### Method 2: Static Unpacking (Advanced)

1. Analyze unpacker stub in Ghidra
2. Identify decryption algorithm
3. Extract decryption key
4. Implement decryption script
5. Fix PE structure (update entry point, remove `.bind` section)

## Analysis Tools

### REVA MCP Tools (Used for Analysis)

- `mcp_reva_open`: Import executable into Ghidra project
- `mcp_reva_inspect-memory`: Examine memory segments and content
- `mcp_reva_list-functions`: Count and list functions
- `mcp_reva_get-function`: Decompile and analyze functions
- `mcp_reva_manage-strings`: Search for packer/DRM strings
- `mcp_reva_manage-symbols`: Examine imports and exports

### External Tools (For Unpacking if Needed)

- **Ghidra**: Static analysis and reverse engineering
- **x64dbg**: Dynamic debugging and memory dumping
- **Scylla**: Memory dumping and import fixing
- **LordPE**: PE structure analysis

## Next Steps

1. **Provide File Path**: Share the full path to `swkotor_aspyr.exe`
2. **Import into Project**: File will be imported using REVA MCP tools
3. **Perform Analysis**: Execute the analysis workflow above
4. **Document Results**: Update this document with findings
5. **Compare with Known Versions**: Compare against `swkotor2_aspyr.exe` and packed Steam versions

## Conclusion

Once `swkotor_aspyr.exe` is available for analysis, this document will be updated with:
- Confirmed packing/DRM status
- Detailed PE structure analysis
- Function count and distribution
- Code section content analysis
- Import and string analysis results
- Comparison with other KOTOR executables
- Unpacking methodology (if packed)

**Current Status**: Awaiting file path for analysis.
