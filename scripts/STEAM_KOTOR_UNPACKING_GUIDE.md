# Unpacking Steam KOTOR for Ghidra Analysis

## The Problem

The Steam version of KOTOR (`swkotor.exe`) uses DRM/packing protection that encrypts the `.text` section (where all the game code lives). When you load it into Ghidra:

- The `.text` section (0x00401000 - 0x0073CFFF) contains encrypted/garbage bytes
- Ghidra only finds ~6 functions in the `.bind` section (the unpacker stub)
- The actual game code cannot be analyzed

## The Solution

You need to **dump the unpacked executable from memory** while the game is running.

### Method 1: Using Scylla (Recommended)

1. **Download Scylla**: https://github.com/NtQuery/Scylla/releases
2. **Run KOTOR** until you reach the main menu
3. **Open Scylla** (run as Administrator)
4. **Attach to swkotor.exe process**
5. Click **"IAT Autosearch"** then **"Get Imports"**
6. Click **"Dump"** to save the unpacked executable
7. Click **"Fix Dump"** to repair the import table
8. Import the fixed dump into Ghidra

### Method 2: Using x64dbg

1. **Download x64dbg**: https://x64dbg.com/
2. Open `swkotor.exe` in x64dbg (use x32dbg since KOTOR is 32-bit)
3. Run until the OEP (Original Entry Point) - usually after the unpacker finishes
4. Use **Scylla plugin** (built into x64dbg) to dump
5. Import the dump into Ghidra

### Method 3: Using pe-sieve

1. **Download pe-sieve**: https://github.com/hasherezade/pe-sieve/releases
2. Run KOTOR until main menu
3. Run: `pe-sieve.exe /pid <kotor_pid> /dump`
4. Import the dumped module into Ghidra

## Alternative: Use GOG Version

The GOG version of KOTOR is **DRM-free** and can be analyzed directly in Ghidra without any unpacking. If you have access to the GOG version, simply:

1. Import `swkotor.exe` (GOG) into Ghidra
2. Let Ghidra auto-analyze
3. Run the import script

## After Unpacking

Once you have an unpacked executable in Ghidra:

1. **Copy the generated script** (`scripts/ghidra_kotor_apply.py`) to your Ghidra scripts folder:
   - Windows: `%USERPROFILE%\ghidra_scripts\`
   - Or use: Ghidra → Window → Script Manager → Manage Script Directories

2. **Run the script** in Ghidra's Script Manager

3. The script will:
   - Create functions at all 24,232 known addresses
   - Apply function names (CSWSCreature::Attack, CExoResMan::LoadResource, etc.)
   - Add comments
   - The process may take several minutes

## Verifying Success

After running the script, you should see:
- Functions with meaningful names like `CSWSCreature::Attack` instead of `FUN_00401000`
- Class hierarchies visible in the Symbol Tree
- Comments explaining code behavior

## Files Generated

- `scripts/ghidra_kotor_apply.py` - Ghidra Python script to apply all data
- `scripts/kotor_re_full.json` - JSON export of all parsed data (for programmatic use)

## Statistics from KOTOR RE Things

- **24,232 functions** with names and signatures
- **40,159 symbols** (global variables, vtables, etc.)
- **38,411 data definitions** (typed data at specific addresses)
- **1,582 comments** explaining code behavior
- **791 struct/class definitions**

### Major Classes

| Class | Functions | Description |
|-------|-----------|-------------|
| CSWVirtualMachineCommands | 577 | NWScript VM implementation |
| CSWSCreature | 379 | Server-side creature logic |
| CSWSMessage | 210 | Network message handling |
| CClientExoApp | 208 | Client application |
| CSWCCreature | 182 | Client-side creature |
| CGuiInGame | 149 | In-game GUI |
| CSWSObject | 139 | Server-side game objects |
| CServerExoApp | 121 | Server application |
| CSWSArea | 119 | Area/level logic |
| Gob | 112 | Graphics object (Aurora engine) |

