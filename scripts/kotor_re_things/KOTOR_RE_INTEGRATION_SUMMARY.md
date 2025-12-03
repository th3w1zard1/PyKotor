# KOTOR Reverse Engineering Integration Summary

## Current Status

### Steam Version Issue
The Steam version of `swkotor.exe` loaded in Ghidra is **packed/encrypted**:
- Entry point: `0x0086d2ed` (in `.bind` section - the unpacker stub)
- `.text` section: `0x00401000 - 0x0073cfff` (encrypted, not analyzed)
- Only 6 functions detected (all in the packer stub)

### KOTOR RE Things Data Parsed
Successfully parsed all data from `vendor/Kotor RE Things/`:

| Data Type | Count |
|-----------|-------|
| Functions | 24,232 |
| Symbols | 40,159 |
| Data Definitions | 38,411 |
| Comments | 1,582 |
| Struct Definitions | 791 |

### Address Compatibility
The GOG version (source of KOTOR RE Things) and Steam version have **identical memory layouts**:
- `.text` section: `0x00401000 - 0x0073cfff` (same in both)
- `.rdata` section: `0x0073d000 - 0x0078cfff` (same in both)
- `.data` section: `0x0078d000 - 0x00835497` (same in both)

**Once the Steam version is unpacked, all addresses from KOTOR RE Things will apply directly.**

## Files Generated

### For Ghidra Import
1. **`scripts/ghidra_kotor_apply.py`** (1.2MB)
   - Complete Ghidra Python script
   - Contains all 24,232 function definitions
   - Contains 1,582 comments
   - Run in Ghidra's Script Manager

2. **`scripts/ghidra_force_analyze.py`**
   - Helper script to force-analyze .text section
   - Detects if binary is still encrypted
   - Creates functions at prologue patterns

### For Programmatic Use
3. **`scripts/kotor_re_things/kotor_re_full.json`** (large)
   - Complete JSON export of all parsed data
   - Includes full function signatures, parameters, local variables
   - Includes all struct definitions with field layouts

4. **`scripts/ghidra_kotor_import.py`**
   - Python parser for KOTOR RE Things files
   - Can regenerate all output files
   - Standalone (works outside Ghidra)

### Documentation
5. **`scripts/STEAM_KOTOR_UNPACKING_GUIDE.md`**
   - Step-by-step instructions for unpacking Steam KOTOR
   - Methods: Scylla, x64dbg, pe-sieve
   - Alternative: Use GOG version

## How to Complete the Integration

### Option A: Unpack Steam KOTOR (Recommended if you want Steam version)

1. **Run KOTOR** until main menu appears
2. **Dump with Scylla**:
   ```
   - Download Scylla: https://github.com/NtQuery/Scylla/releases
   - Attach to swkotor.exe
   - IAT Autosearch → Get Imports → Dump → Fix Dump
   ```
3. **Import dump into Ghidra** (new project)
4. **Run analysis** (auto-analyze)
5. **Run `ghidra_kotor_apply.py`** in Script Manager

### Option B: Use GOG Version (Easiest)

1. **Get GOG KOTOR** (DRM-free)
2. **Import `swkotor.exe`** into Ghidra
3. **Run analysis** (auto-analyze)
4. **Run `ghidra_kotor_apply.py`** in Script Manager

### Option C: Apply to Current Ghidra Project (Limited)

Since the Steam `.text` is encrypted, you can only apply:
- Comments to `.rdata` section (strings are visible)
- Data definitions to `.rdata` and `.data` sections

The function names **cannot** be applied until the code is unpacked.

## Major Classes Identified

| Class | Functions | Purpose |
|-------|-----------|---------|
| CSWVirtualMachineCommands | 577 | NWScript VM (all script commands) |
| CSWSCreature | 379 | Server-side creature logic |
| CSWSMessage | 210 | Network messages |
| CClientExoApp | 208 | Client application main |
| CSWCCreature | 182 | Client-side creature |
| CGuiInGame | 149 | In-game GUI panels |
| CSWSObject | 139 | Base server object |
| CServerExoApp | 121 | Server application main |
| CSWSArea | 119 | Area/module logic |
| Gob | 112 | Graphics object (Aurora 3D) |
| GLRender | 89 | OpenGL rendering |
| CTwoDimArrays | 82 | 2DA file handling |
| Scene | 78 | Scene graph |
| CResGFF | 64 | GFF file format |
| CExoResMan | 60 | Resource manager |

## Key Functions for Modding

### Save/Load
- `CServerExoApp::SaveGame` - Save game logic
- `CServerExoApp::LoadGame` - Load game logic
- `CResGFF::*` - GFF file reading/writing

### Combat
- `CSWSCreature::Attack` - Attack execution
- `CSWSCreature::ApplyDamage` - Damage application
- `CSWSCreatureStats::*` - Character stats

### Scripts
- `CSWVirtualMachineCommands::*` - All 577 NWScript commands
- `CVirtualMachine::*` - Script VM execution

### Rendering
- `GLRender::*` - OpenGL rendering
- `Scene::*` - Scene management
- `Gob::*` - 3D object handling

### Resources
- `CExoResMan::*` - Resource loading
- `CExoKeyTable::*` - KEY/BIF handling

## Next Steps

1. **Unpack the Steam EXE** or **obtain GOG version**
2. **Import into Ghidra** and auto-analyze
3. **Run `ghidra_kotor_apply.py`** to apply all 24,232 function names
4. **Verify** by checking known functions like `WinMain` at `0x004041f0`

## Technical Notes

### Why Addresses Match
Both GOG and Steam versions are compiled from the same source code with the same compiler settings. The only difference is:
- GOG: Unprotected, code visible
- Steam: SecuROM-like protection wraps the executable

The protection doesn't relocate code - it just encrypts `.text` at rest and decrypts at runtime. Once dumped from memory, addresses are identical.

### Struct Definitions
791 struct definitions were parsed from `swkotor.exe.h`, including:
- Game object classes (CSWSCreature, CSWSArea, etc.)
- Aurora engine types (Vector, Quaternion, Scene, Gob)
- File format structures (GFF, KEY, BIF headers)
- Win32/DirectX types

These can be imported into Ghidra's Data Type Manager for proper struct typing.

