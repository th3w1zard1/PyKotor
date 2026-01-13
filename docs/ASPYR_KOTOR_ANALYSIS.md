# KOTOR Executable Protection Analysis and Unpacking Guide

## Overview

This document provides a comprehensive analysis of protection mechanisms (encryption, packing, DRM) in KOTOR executables and detailed instructions for identifying, analyzing, and unpacking protected executables using Ghidra and related tools.

## Executive Summary

**Analysis Result for `swkotor2_aspyr.exe`**: The Aspyr version of KOTOR II is **completely unpacked and DRM-free**. No encryption, packing, or obfuscation is present.

**However**, this guide also covers how to analyze and unpack **packed executables** (such as the Steam version of KOTOR I), which use runtime decryption packers.

## Protection Mechanism Types

### 1. Runtime Decryption Packer (Steam KOTOR I)

**What It Is**: A protection scheme that encrypts the executable's code section on disk and decrypts it in memory at runtime.

**Characteristics**:
- **Encrypted Section**: Only the `.text` section (executable code) is encrypted
- **Entry Point Redirection**: PE header's `AddressOfEntryPoint` points to unpacker stub instead of main code
- **Unpacker Stub**: Additional section (typically `.bind`) contains decryption code
- **Runtime Decryption**: Code is decrypted in memory before execution
- **Memory Layout**: Virtual addresses remain unchanged (no relocation)

**Indicators**:
- Entry point not in `.text` section (e.g., points to `.bind` section)
- Very few functions detected (~6 functions vs. thousands)
- `.text` section contains encrypted/garbage data
- Additional section with unusual name (`.bind`, `.upx`, `.pack`, etc.)

### 2. Code Obfuscation

**What It Is**: Code is transformed to make analysis difficult without encryption.

**Characteristics**:
- Code is valid x86 but uses obfuscated patterns
- Control flow flattening
- Dead code insertion
- Instruction substitution

**Indicators**:
- Functions detected but decompilation is nonsensical
- Unusual control flow patterns
- Excessive use of indirect jumps/calls

### 3. Anti-Debugging

**What It Is**: Code that detects and prevents debugging.

**Characteristics**:
- Calls to `IsDebuggerPresent()`, `CheckRemoteDebuggerPresent()`
- Timing checks using `GetTickCount()`, `QueryPerformanceCounter()`
- Exception-based anti-debugging
- Hardware breakpoint detection

**Indicators**:
- Imports include anti-debugging APIs
- Code checks for debugger presence
- Unusual exception handling

## Detailed Analysis: Identifying Protection

### Step 1: PE Structure Analysis

#### Check Entry Point Location

**In Ghidra**:
1. Load the executable
2. Navigate to `Edit` → `Program Information` (or press `I`)
3. Check `Entry Point` address
4. Determine which section contains the entry point

**Normal Executable**:
- Entry point: `0x00401000` (typical for x86 PE)
- Section: `.text`
- Behavior: Direct execution of main code

**Packed Executable**:
- Entry point: `0x0086d2ed` (example from Steam KOTOR I)
- Section: `.bind` or other non-standard section
- Behavior: Execution starts in unpacker stub

#### Check Section Headers

**In Ghidra**:
1. Open `Window` → `Defined Data`
2. Navigate to PE header structures
3. Examine section table

**Look for**:
- Unusual section names: `.bind`, `.upx`, `.pack`, `.themida`, `.vmp`
- Sections with `IMAGE_SCN_MEM_READ | IMAGE_SCN_MEM_WRITE` (unpacker stubs need write access)
- Large sections after `.data` (unpacker stub location)

**Example Steam KOTOR I**:
```
Section: .bind
VirtualAddress: 0x0086d000
SizeOfRawData: 0x00056000 (352,256 bytes)
Characteristics: IMAGE_SCN_CNT_INITIALIZED_DATA | IMAGE_SCN_MEM_READ | IMAGE_SCN_MEM_WRITE
```

#### Check Function Count

**In Ghidra**:
1. Run auto-analysis (`Analysis` → `Auto Analyze`)
2. Open `Window` → `Function Manager`
3. Count functions (filter out default names if needed)

**Normal Executable**:
- KOTOR I: ~24,000+ functions
- KOTOR II: ~15,000+ functions
- Functions distributed throughout `.text` section

**Packed Executable**:
- Only ~6-20 functions detected
- All functions in unpacker stub section (`.bind`)
- `.text` section shows no functions (encrypted)

### Step 2: Code Section Analysis

#### Examine `.text` Section Content

**In Ghidra**:
1. Navigate to `.text` section start (`0x00401000`)
2. View memory in hex editor
3. Check for valid x86 instructions

**Normal Executable**:
```
0x00401000: 55 8B EC          push ebp; mov ebp, esp  (valid function prologue)
0x00401003: 83 EC 20         sub esp, 0x20
0x00401006: C7 45 FC ...     mov dword ptr [ebp-4], ...
```

**Packed Executable**:
```
0x00401000: A7 3F 92 1E      (garbage/encrypted data)
0x00401004: 8C D4 7A 3F      (no valid x86 patterns)
0x00401008: F2 9B 4E 8A      (high entropy, encrypted)
```

#### Check for Encryption Patterns

**In Ghidra**:
1. Use `Search` → `Memory` → `Search All`
2. Search for common x86 patterns:
   - `55 8B EC` (function prologue)
   - `CC CC CC CC` (padding/breakpoints)
   - `E8 ?? ?? ?? ??` (call instruction)

**Normal Executable**:
- Many matches for `55 8B EC` (function prologues)
- Regular patterns indicating structured code

**Packed Executable**:
- Very few or no matches
- High entropy (random-looking data)
- No recognizable instruction patterns

### Step 3: Import Analysis

#### Check for Anti-Debugging Imports

**In Ghidra**:
1. Open `Window` → `Symbol Table`
2. Filter by imports
3. Search for anti-debugging APIs

**Common Anti-Debugging APIs**:
- `IsDebuggerPresent()` (KERNEL32.DLL)
- `CheckRemoteDebuggerPresent()` (KERNEL32.DLL)
- `NtQueryInformationProcess()` (NTDLL.DLL)
- `OutputDebugStringA()` (KERNEL32.DLL)

**Note**: Presence of these imports doesn't necessarily mean the executable is packed, but indicates anti-debugging measures.

### Step 4: String Analysis

#### Search for Packer/DRM Strings

**In Ghidra**:
1. Use `Search` → `Memory` → `Search All`
2. Search for packer-related strings

**Common Packer Strings**:
- `.bind`, `.upx`, `.pack`
- `UPX!`, `Themida`, `VMProtect`
- `SecuROM`, `StarForce`
- `steam_api.dll` (Steam DRM)

**Note**: Absence of these strings doesn't guarantee no packing, but their presence is a strong indicator.

## Unpacking Methodology

### Method 1: Memory Dumping (Recommended for Runtime Decryption Packers)

This method works for executables that decrypt themselves in memory at runtime.

#### Prerequisites

- **Debugger**: x64dbg (recommended) or OllyDbg
- **Dumper**: Scylla (x64dbg plugin) or LordPE
- **Import Fixer**: Scylla (built-in) or ImportREC

#### Step-by-Step Process

**1. Identify Original Entry Point (OEP)**

**In Ghidra** (static analysis):
1. Analyze the unpacker stub
2. Trace execution flow from entry point
3. Find the jump/call to original entry point (typically `0x00401000`)
4. Note the OEP address

**In x64dbg** (dynamic analysis):
1. Load the packed executable
2. Set breakpoint on entry point
3. Step through unpacker stub
4. Find jump to `0x00401000` (or calculated OEP)
5. Set breakpoint on OEP
6. Continue execution until OEP breakpoint hits

**2. Dump Process Memory**

**Using Scylla (x64dbg plugin)**:
1. When execution reaches OEP, pause
2. Open Scylla plugin (`Plugins` → `Scylla`)
3. Click `IAT Autosearch`
4. Click `Get Imports`
5. Verify imports are correct
6. Click `Dump` → Save as `unpacked.exe`
7. Click `Fix Dump` → Select `unpacked.exe`
8. Save fixed executable

**Using LordPE**:
1. When execution reaches OEP, pause
2. Open LordPE
3. Right-click process → `Dump Full`
4. Save as `unpacked.exe`
5. Use ImportREC to fix imports

**3. Verify Unpacked Executable**

**In Ghidra**:
1. Load the dumped executable
2. Run auto-analysis
3. Check function count (should match unpacked version)
4. Verify `.text` section contains valid code
5. Check entry point is in `.text` section

### Method 2: Static Unpacking (Advanced)

This method involves reverse engineering the unpacker stub to extract the decryption algorithm.

#### Step-by-Step Process

**1. Analyze Unpacker Stub**

**In Ghidra**:
1. Navigate to entry point (e.g., `0x0086d2ed` in `.bind` section)
2. Decompile the unpacker stub
3. Identify decryption function
4. Trace decryption algorithm

**2. Identify Decryption Algorithm**

**Common Patterns**:
- **XOR**: `data[i] ^= key`
- **Additive**: `data[i] += key`
- **RC4**: Stream cipher
- **AES**: Block cipher (rare in packers)
- **Custom**: Proprietary algorithm

**3. Extract Decryption Key**

**In Ghidra**:
1. Find key generation/retrieval
2. Trace key source (may be hardcoded, calculated, or from file)
3. Note key value or calculation method

**4. Implement Decryption Script**

**Python Example (XOR decryption)**:
```python
def decrypt_text_section(encrypted_data, key):
    decrypted = bytearray(encrypted_data)
    for i in range(len(decrypted)):
        decrypted[i] ^= key[i % len(key)]
    return bytes(decrypted)

# Read encrypted .text section
with open('packed.exe', 'rb') as f:
    pe_data = f.read()
    text_section = extract_text_section(pe_data)  # Extract .text section
    
# Decrypt
key = b'\x12\x34\x56\x78'  # Key from analysis
decrypted = decrypt_text_section(text_section, key)

# Write decrypted section back
with open('unpacked.exe', 'wb') as f:
    f.write(replace_text_section(pe_data, decrypted))
```

**5. Fix PE Structure**

After decryption:
1. Update entry point to original (`0x00401000`)
2. Remove `.bind` section (optional)
3. Fix checksums
4. Verify PE structure is valid

### Method 3: Ghidra Scripting (Automated Unpacking)

For advanced users, Ghidra scripts can automate unpacking.

#### Example Ghidra Script Structure

```python
from ghidra.program.model.address import Address
from ghidra.program.model.mem import MemoryAccessException

def find_unpacker_stub():
    """Locate unpacker stub in .bind section"""
    # Implementation here
    pass

def trace_decryption():
    """Trace decryption algorithm"""
    # Implementation here
    pass

def decrypt_text_section():
    """Decrypt .text section"""
    # Implementation here
    pass

# Main execution
if __name__ == "__main__":
    find_unpacker_stub()
    trace_decryption()
    decrypt_text_section()
```

## Detailed Analysis: swkotor2_aspyr.exe

### PE Structure

**Entry Point**: `0x0091d5a2`
- **Location**: `.text` section (normal)
- **Function**: `entry()` → `___security_init_cookie()` → `___tmainCRTStartup()`
- **Analysis**: Standard C runtime initialization

**Sections**:
```
Headers:     0x00400000 - 0x004003ff (1,024 bytes)
.text:       0x00401000 - 0x009857ff (5,785,600 bytes) - Executable code
.rdata:      0x00986000 - 0x009f31ff (446,976 bytes) - Read-only data
.data:       0x009f4000 - 0x00a81f3b (581,436 bytes) - Writable data
.rsrc:       0x00a82000 - 0x00ab8bff (224,256 bytes) - Resources
tdb:         0xffdff000 - 0xffdfffff (4,096 bytes) - Thread data
```

**Analysis**: No `.bind` section present. Standard PE structure.

### Function Detection

**Functions Detected**: 15,313
- **Distribution**: Throughout `.text` section
- **Pattern**: Standard x86 function prologues (`55 8B EC`)
- **Analysis**: Normal function count for KOTOR II

**Comparison**:
- **Packed executable**: ~6 functions (unpacker stub only)
- **Unpacked executable**: 15,313 functions (normal)

### Code Section Analysis

**`.text` Section at `0x00401000`**:
```
0x00401000: 55 8B EC          push ebp; mov ebp, esp
0x00401003: C6 05 20 3C A1 00 mov byte ptr [0x00a13c20], 0x0
0x0040100A: C6 05 21 3C A1 00 mov byte ptr [0x00a13c21], 0x0
...
```

**Analysis**: Valid x86 instructions. No encryption detected.

### Import Analysis

**Imports**: Standard Windows APIs
- KERNEL32.DLL: File I/O, process management
- USER32.DLL: Window management
- GDI32.DLL: Graphics
- BINKW32.DLL: Video playback
- DINPUT8.DLL: Input handling

**Analysis**: No DRM libraries. No anti-debugging APIs (except standard `IsDebuggerPresent` which is unused).

### String Analysis

**Searched for**:
- `.bind`: Not found
- `pack`: Found only `texturepacks` (game-related)
- `drm`: Not found
- `securom`: Not found
- `encrypt`: Not found

**Analysis**: No packer/DRM strings detected.

### Conclusion for swkotor2_aspyr.exe

**Status**: **Completely unpacked and DRM-free**

**Evidence**:
1. Entry point in `.text` section (normal)
2. 15,313 functions detected (normal for KOTOR II)
3. Valid x86 code in `.text` section
4. No `.bind` or other unpacker sections
5. No DRM-related imports or strings
6. Standard PE structure

**Analysis Method**: Direct analysis in Ghidra. No unpacking required.

## Comparison: Packed vs Unpacked

### Steam KOTOR I (Packed)

| Aspect | Value | Analysis |
|--------|-------|----------|
| **Entry Point** | `0x0086d2ed` | In `.bind` section (unpacker stub) |
| **Functions** | ~6 | Only unpacker stub functions |
| **`.text` Section** | Encrypted | Garbage data, unanalyzable |
| **Additional Sections** | `.bind` (352 KB) | Unpacker stub and DRM code |
| **Analysis** | Requires memory dump | Must dump from memory after decryption |

### Aspyr KOTOR II (Unpacked)

| Aspect | Value | Analysis |
|--------|-------|----------|
| **Entry Point** | `0x0091d5a2` | In `.text` section (normal) |
| **Functions** | 15,313 | All game functions visible |
| **`.text` Section** | Plain code | Valid x86, fully analyzable |
| **Additional Sections** | None | Standard PE sections only |
| **Analysis** | Direct analysis | Load and analyze immediately |

## Practical Unpacking Workflow

### For Packed Executables (Steam KOTOR I)

**Step 1: Initial Analysis in Ghidra**
1. Load packed executable
2. Identify entry point location (`.bind` section)
3. Note function count (~6 functions)
4. Confirm `.text` section is encrypted

**Step 2: Dynamic Analysis**
1. Load in x64dbg
2. Set breakpoint on entry point
3. Step through unpacker stub
4. Identify OEP (`0x00401000`)
5. Set breakpoint on OEP

**Step 3: Memory Dumping**
1. When OEP breakpoint hits, pause execution
2. Use Scylla to dump process
3. Fix imports with Scylla
4. Save as `unpacked.exe`

**Step 4: Verification**
1. Load `unpacked.exe` in Ghidra
2. Run auto-analysis
3. Verify ~24,000+ functions detected
4. Confirm `.text` section contains valid code
5. Verify entry point is `0x00401000`

### For Unpacked Executables (Aspyr KOTOR II)

**Step 1: Direct Analysis**
1. Load executable in Ghidra
2. Run auto-analysis
3. Begin reverse engineering immediately

**No additional steps required.**

## Advanced Topics

### Analyzing Unpacker Stub

**In Ghidra**:
1. Navigate to entry point in `.bind` section
2. Decompile unpacker stub
3. Identify decryption loop
4. Extract decryption algorithm
5. Note decryption key source

**Common Unpacker Patterns**:
```c
// Pattern 1: Simple XOR loop
for (int i = 0; i < text_size; i++) {
    text_section[i] ^= key[i % key_size];
}

// Pattern 2: Additive cipher
for (int i = 0; i < text_size; i++) {
    text_section[i] = (text_section[i] + key) & 0xFF;
}

// Pattern 3: RC4 stream cipher
RC4_Decrypt(text_section, text_size, key, key_size);
```

### Anti-Debugging Bypass

If unpacker stub has anti-debugging:
1. Patch `IsDebuggerPresent()` to return `FALSE`
2. Use hardware breakpoints instead of software
3. Use stealth debugging techniques
4. Patch timing checks

### Import Table Reconstruction

After dumping:
1. Use Scylla's IAT autosearch
2. Manually verify imports
3. Fix any missing imports
4. Rebuild import table

## Tools and Resources

### Essential Tools

- **Ghidra**: Static analysis and reverse engineering
- **x64dbg**: Dynamic debugging and memory dumping
- **Scylla**: Memory dumping and import fixing
- **LordPE**: PE structure analysis and dumping
- **ImportREC**: Import table reconstruction

### Ghidra Plugins

- **Ghidra SRE**: Enhanced scripting capabilities
- **Ghidra RE**: Additional reverse engineering features

### Learning Resources

- PE file format specification
- x86 assembly and calling conventions
- Windows API documentation
- Reverse engineering techniques

## Conclusion

**For `swkotor2_aspyr.exe`**: The executable is completely unpacked and can be analyzed directly in Ghidra without any unpacking steps.

**For Packed Executables**: Use memory dumping techniques (Scylla + x64dbg) to extract the decrypted code from memory after the unpacker stub executes. The unpacked executable will have identical memory layout and addresses to the original, allowing direct application of reverse engineering data.

**Key Takeaway**: Always verify protection status before attempting unpacking. Many modern executables (including Aspyr versions) are distributed without protection, making analysis straightforward.
