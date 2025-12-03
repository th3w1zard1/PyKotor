# KOTOR DRM Unpacker/Packer

## Overview

This script can unpack (dump) and pack (re-protect) the Steam version of KOTOR's DRM-protected executable.

## Installation

```bash
pip install pefile psutil
```

## Usage

### Unpacking (Dumping from Memory)

The Steam version encrypts the `.text` section. To get the unpacked code:

1. **Run KOTOR** until you reach the main menu (unpacker has finished)
2. **Dump the process**:

```bash
# Auto-detect KOTOR process
python scripts/kotor_drm_unpacker.py unpack --auto --output swkotor_unpacked.exe

# Or specify paths manually
python scripts/kotor_drm_unpacker.py unpack --exe "path/to/swkotor.exe" --output swkotor_unpacked.exe
```

**Important**: The game **must be running** for unpacking to work, as the code is only decrypted in memory.

### Packing (Re-applying Protection)

After modifying the unpacked executable, you can re-apply basic protection:

```bash
python scripts/kotor_drm_unpacker.py pack --exe swkotor_unpacked.exe --output swkotor_repacked.exe
```

**Note**: The packer creates a **basic protection layer**, not identical to Steam's original DRM. It:
- Encrypts the `.text` section with XOR
- Creates a minimal unpacker stub
- Modifies the entry point

For production use, you may want a more sophisticated packer.

## Limitations

### Unpacking
- Requires the game to be running (code is only decrypted in memory)
- IAT (Import Address Table) fixing is basic - you may need Scylla for complete fix
- Some sections may not dump correctly if memory protection prevents reading

### Packing
- **Not identical to Steam DRM** - this is a basic packer
- Uses simple XOR encryption (not cryptographically secure)
- Unpacker stub is minimal (may not handle all edge cases)
- Does not replicate SecuROM or other commercial DRM features

## Recommended Workflow

### For Reverse Engineering

1. **Unpack**:
   ```bash
   python scripts/kotor_drm_unpacker.py unpack --auto
   ```

2. **Fix IAT with Scylla** (recommended):
   - Open Scylla
   - Load the dumped executable
   - Click "IAT Autosearch" → "Get Imports" → "Fix Dump"

3. **Import into Ghidra**:
   - Create new project
   - Import the fixed dump
   - Auto-analyze
   - Run `ghidra_kotor_apply.py` to apply all function names

### For Modding/Testing

1. **Unpack** the original
2. **Modify** the unpacked executable
3. **Pack** it back (optional - for testing protection)
4. **Test** the modified executable

## Technical Details

### Unpacking Process

1. Finds the running KOTOR process
2. Reads the image base address (typically `0x00400000`)
3. Reads all PE sections from process memory
4. Reconstructs the PE file structure
5. Attempts basic IAT fixing

### Packing Process

1. Reads the unpacked PE file
2. Encrypts the `.text` section with XOR
3. Creates a minimal unpacker stub
4. Modifies the entry point to the stub
5. Saves the packed executable

### Memory Layout

Both GOG and Steam versions use the same memory layout:
- `.text`: `0x00401000 - 0x0073cfff` (code - encrypted in Steam)
- `.rdata`: `0x0073d000 - 0x0078cfff` (read-only data)
- `.data`: `0x0078d000 - 0x00835497` (writable data)
- `.bind`: `0x0086d000 - 0x008c2fff` (Steam DRM unpacker stub)

## Troubleshooting

### "KOTOR process not found"
- Make sure the game is running
- Run the script as Administrator
- Check that the process name is `swkotor.exe`

### "Failed to read memory"
- Run as Administrator
- Check if antivirus is blocking memory access
- Try closing other security software

### "Invalid PE header"
- The process may have been terminated
- Try dumping again while the game is running
- Verify the image base address is correct

### Dumped executable doesn't run
- Use Scylla to fix the IAT (Import Address Table)
- The basic IAT fix in this script is minimal
- Scylla's "Fix Dump" feature is more robust

## Alternative Tools

For more advanced unpacking:
- **Scylla**: https://github.com/NtQuery/Scylla - Better IAT fixing
- **x64dbg**: https://x64dbg.com/ - Debugger with Scylla plugin
- **pe-sieve**: https://github.com/hasherezade/pe-sieve - Process dumping

For production packing:
- **UPX**: https://upx.github.io/ - Universal packer (not DRM, but compression)
- **VMProtect**: Commercial packer (more sophisticated)
- **Themida**: Commercial packer (advanced protection)

## Legal Notice

This tool is for:
- ✅ Reverse engineering for modding
- ✅ Educational purposes
- ✅ Security research

**Not for**:
- ❌ Bypassing DRM for piracy
- ❌ Distributing cracked executables
- ❌ Circumventing license restrictions

Use responsibly and in accordance with applicable laws.

