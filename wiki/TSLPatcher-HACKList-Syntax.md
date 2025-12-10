# TSLPatcher HACKList Syntax Documentation

This guide explains how to modify [NCS files](NCS-File-Format) directly using TSLPatcher syntax. For the complete [NCS file](NCS-File-Format) format specification, see [NCS File Format](NCS-File-Format). For general TSLPatcher information, see [TSLPatcher's Official Readme](TSLPatcher's-Official-Readme). For HoloPatcher-specific information, see [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.#hacklist-editing-ncs-directly).

## Overview

The `[HACKList]` section in TSLPatcher's changes.ini file enables you to modify compiled NCS (Neverwinter Compiled Script) [bytecode](https://en.wikipedia.org/wiki/Bytecode) files directly at the binary level. This advanced feature allows precise [byte](GFF-File-Format#gff-data-types)-level modifications to script files without recompiling from [NSS](NSS-File-Format) source code, making it ideal for:

- Patching numerical values in existing compiled scripts
- Injecting dynamically-generated string references (StrRefs) and [2DA](2DA-File-Format) memory values
- Performing surgical modifications to hardcoded constants
- Updating scripts to reference new [TLK entries](TSLPatcher-TLKList-Syntax) or [2DA row numbers](TSLPatcher-2DAList-Syntax)

**Important:** HACKList is executed **after** `[CompileList]` during patcher execution, allowing compiled scripts to be modified after compilation if needed.

## Table of Contents

- [Basic Structure](#basic-structure)
- [File-Level Configuration](#file-level-configuration)
- [Token Types and Data Sizes](#token-types-and-data-sizes)
- [Memory Token Integration](#memory-token-integration)
- [Offset Calculation](#offset-calculation)
- [Examples](#examples)
- [DeNCS Reference](#dencs-reference)
- [Common Use Cases](#common-use-cases)
- [Troubleshooting](#troubleshooting)

## Basic structure

```ini
[HACKList]
!DefaultDestination=override
!DefaultSourceFolder=.  ; Note: `.` refers to the tslpatchdata folder (where changes.ini is located)
File0=myscript.ncs
Replace0=otherscript.ncs

[myscript.ncs]
!Destination=override
!SourceFile=source.ncs
!SaveAs=mypatched.ncs
ReplaceFile=0

; Byte-level modifications
0x15=12345
32=u16:2DAMEMORY1
64=u8:255
0x100=StrRef5
0x200=u32:2DAMEMORY10
```

The `[HACKList]` section declares [NCS files](NCS-File-Format) to modify. Each entry references another section with the same name as the filename.

## file-Level Configuration

### Top-Level Keys in [HACKList]

| [KEY](KEY-File-Format) | type | Default | Description |
|-----|------|---------|-------------|
| `!DefaultDestination` | string | `override` | Default destination for all [NCS files](NCS-File-Format) in this section |
| `!DefaultSourceFolder` | string | `.` | Default source folder for [NCS files](NCS-File-Format). This is a relative path from `mod_path`, which is typically the `tslpatchdata` folder (the parent directory of the `changes.ini` file). The default value `.` refers to the `tslpatchdata` folder itself. Path resolution: `mod_path / !DefaultSourceFolder / filename` |

### file Section Configuration

Each [NCS file](NCS-File-Format) requires its own section (e.g., `[myscript.ncs]`).

| Key | type | Default | Description |
|-----|------|---------|-------------|
| `!Destination` | string | Inherited from `!DefaultDestination` | Where to save the modified file (`override` or `path\to\file.mod`) |
| `!SourceFolder` | string | Inherited from `!DefaultSourceFolder` | Source folder for the [NCS file](NCS-File-Format). Relative path from `mod_path` (typically the tslpatchdata folder). When `.`, refers to the tslpatchdata folder itself. |
| `!SourceFile` | string | Same as section name | Alternative source filename to load |
| `!SaveAs` or `!Filename` | string | Same as section name | Final filename to save as |
| `ReplaceFile` | 0/1 | 0 | **Note:** Unlike other patch lists, HACKList uses `ReplaceFile` (without exclamation point) |

**Destination values:**

- `override` or empty: Save to the Override folder
- `Modules\module.mod`: Insert into an [ERF](ERF-File-Format)/MOD/RIM archive
- Use backslashes for path separators

**Important:** The `ReplaceFile` [KEY](KEY-File-Format) in HACKList does NOT use an exclamation point prefix. This is unique to HACKList compared to other patch lists.

## Token types and data Sizes

Each modification requires specifying an offset and a value. values can include type specifiers to control data size.

### Syntax

```ini
offset=value
offset=type:value
```

- **offset**: Decimal number (e.g., `32`) or hexadecimal (e.g., `0x20`)
- **type** (optional): One of `u8`, `u16`, or `u32` to specify data width
- **value**: Numeric value, token reference, or hex literal

### Supported value types

| value format | type | size | Description |
|--------------|------|------|-------------|
| Numeric (no prefix) | u16 | 2 bytes | 16-bit unsigned integer (default) |
| `u8:123` | u8 | 1 [byte](GFF-File-Format#gff-data-types) | 8-bit unsigned integer (0-255) |
| `u16:12345` | u16 | 2 bytes | 16-bit unsigned integer (0-65535) |
| `u32:123456` | u32 | 4 bytes | 32-bit unsigned integer |
| `StrRef0` | [StrRef](TLK-File-Format#string-references-strref) | Varies* | Reference to [TLK](TLK-File-Format) string from memory |
| `StrRefN` | strref32 | 4 bytes | 32-bit signed [TLK](TLK-File-Format) reference (CONSTI) |
| `2DAMEMORY1` | 2damemory | Varies* | Reference to [2DA](2DA-File-Format) memory value |
| `2DAMEMORYN` | 2damemory32 | 4 bytes | 32-bit signed [2DA](2DA-File-Format) reference (CONSTI) |

*`strref` and `2damemory` without explicit sizes default to `strref32` and `2damemory32` respectively in PyKotor's implementation.

### Endianness

All multi-[byte](GFF-File-Format#gff-data-types) values [ARE](GFF-File-Format#are-area) written in **[big-endian](https://en.wikipedia.org/wiki/Endianness)** (network [byte](GFF-File-Format#gff-data-types) order), which is standard for KOTOR's binary formats.

### type Compatibility Notes

**Historical Background:** TSLPatcher originally distinguished between `strref` and `strref32` (and `2damemory` vs `2damemory32`), but PyKotor's implementation unifies these:

- `[StrRef](TLK-File-Format#string-references-strref)#` tokens [ARE](GFF-File-Format#are-area) automatically handled as 32-bit values
- `2DAMEMORY#` tokens [ARE](GFF-File-Format#are-area) automatically handled as 32-bit values

If you need legacy 16-bit compatibility, use explicit type specifiers like `u16:StrRef5`, though this is not typically necessary.

## Memory Token Integration

HACKList integrates seamlessly with TSLPatcher's memory token system, allowing dynamic value injection from other patch sections.

### [StrRef](TLK-File-Format#string-references-strref) Tokens

Reference values stored in TLKList memory:

```ini
; In TLKList section, this would define StrRef5
StrRef5=123456

; In HACKList, inject it into bytecode
[HACKList]
File0=myscript.ncs

[myscript.ncs]
; At offset 0x100, write the StrRef value
0x100=StrRef5
```

**Use Cases:**

- Injecting dynamically-added [dialog.tlk](TLK-File-Format) string references
- Patching scripts to reference custom text entries
- Updating hardcoded string IDs to mod-added entries

### [2DA](2DA-File-Format) Memory Tokens

Reference values stored in 2DAList memory:

```ini
; In 2DAList section, this would store a row number
Add2DALine1=appearance.2da
[Add2DALine1]
2DAMEMORY1=RowIndex

; In HACKList, inject it into bytecode
[HACKList]
File0=myscript.ncs

[myscript.ncs]
; At offset 0x50, write the 2DA memory value
0x50=2DAMEMORY1
```

**Use Cases:**

- Injecting dynamically-added [2DA](2DA-File-Format) row numbers
- Patching appearance/spell IDs to reference new rows
- Updating hardcoded IDs to mod-added entries

**Important Limitation:** `!FieldPath` values [ARE](GFF-File-Format#are-area) NOT supported in HACKList. Only numeric memory values can be used.

## offset Calculation

Determining the correct [byte](GFF-File-Format#gff-data-types) offset is the most critical aspect of HACKList usage.

### [NCS files](NCS-File-Format) structure

```ncs
Byte Offset  Description
-----------  --------------------------------------------
0x00-0x03    File signature: "NCS " (ASCII)
0x04-0x07    Version: "V1.0" (ASCII)
0x08         Magic byte: 0x42
0x09-0x0C    Total file size (4 bytes, big-endian)
0x0D+        Compiled bytecode instructions
```

The header is 13 bytes (0x0D), so the first instruction [byte](GFF-File-Format#gff-data-types) is at offset 0x0D.

### Finding offsets with DeNCS

**DeNCS** (Decompiler for [NCS](NCS-File-Format)) is a Java-based disassembler that can help you locate exact [byte](GFF-File-Format#gff-data-types) offsets in [NCS files](NCS-File-Format).

#### Using DeNCS

1. Load your [NCS file](NCS-File-Format) in DeNCS
2. Disassemble to view instruction-level operations
3. Identify the target instruction and note its [byte](GFF-File-Format#gff-data-types) offset
4. If modifying an instruction's operand, add to the instruction's offset:
   - For CONSTI operands: offset + 1 (skip the opcode [byte](GFF-File-Format#gff-data-types))
   - For other operands: depends on instruction type

#### Example Disassembly

```ncs
Offset  Inst                Args
------  ----                ----
0x0D    NOP
0x0E    CONSTI              10000
        (opcode at 0x0E, operand at 0x0F-0x12)
0x13    CPDOWNSP            -4
0x15    CONSTS              "Hello World"
        (opcode at 0x15, string offset at 0x16-0x19)
```

To modify the CONSTI value at 0x0E, you'd patch bytes 0x0F-0x12.

### Common Instruction Layouts

| Instruction | Opcode size | Operand size | Example offset to Patch |
|-------------|-------------|--------------|-------------------------|
| `CONSTI` | 1 byte | 4 bytes | offset + 1 |
| `CONSTF` | 1 byte | 4 bytes | offset + 1 |
| `CONSTS` | 1 byte | 4 bytes | offset + 1 |
| `CPDOWNSP` | 1 byte | 4 bytes | offset + 1 |
| `ACTION` | 1 byte | 4 bytes | offset + 1 |
| `JMP` | 1 byte | 4 bytes | offset + 1 |
| `JZ` | 1 byte | 4 bytes | offset + 1 |

### Hex vs Decimal offsets

Both formats [ARE](GFF-File-Format#are-area) supported:

- **Hexadecimal**: `0x20`, `0x100`, `0xFF`
- **Decimal**: `32`, `256`, `255`

Use hexadecimal for convenience when working with [byte](GFF-File-Format#gff-data-types)-aligned operations.

## Examples

### Example 1: Modifying a Hardcoded Integer

Replace a hardcoded constant in a compiled script:

```ini
[HACKList]
File0=combat_script.ncs

[combat_script.ncs]
; At offset 0x50, change a damage value from 10 to 50
0x50=u16:50
```

### Example 2: Injecting Dynamic [TLK](TLK-File-Format) Reference

Inject a dynamically-added string reference:

```ini
[TLKList]
StrRef1=My New Dialog Entry

[HACKList]
File0=dialog_script.ncs

[dialog_script.ncs]
; At offset 0x100, inject the StrRef value
0x100=StrRef1
```

### Example 3: Patching Multiple values

Modify several offsets in the same file:

```ini
[HACKList]
File0=spell_script.ncs

[spell_script.ncs]
; Patch spell ID at 0x30
0x30=u16:123

; Patch damage amount at 0x50
0x50=u32:999

; Patch duration at 0x70
0x70=u16:60
```

### Example 4: Using [2DA](2DA-File-Format) Memory values

Inject a dynamically-added [2DA](2DA-File-Format) row number:

```ini
[2DAList]
Add2DALine1=spells.2da

[Add2DALine1]
2DAMEMORY5=RowIndex

[HACKList]
File0=spell_handler.ncs

[spell_handler.ncs]
; Inject the row number at offset 0x88
0x88=2DAMEMORY5
```

### Example 5: Advanced Multi-type Patching

Combine different data sizes and token types:

```ini
[HACKList]
File0=complex_script.ncs
Replace0=old_script.ncs

[complex_script.ncs]
ReplaceFile=1

; 8-bit flag value
0x20=u8:1

; 16-bit numeric literal
0x30=u16:4096

; 32-bit StrRef from memory
0x40=StrRef10

; 32-bit 2DA memory reference
0x50=2DAMEMORY3

; Direct hex value
0x60=u32:0xDEADBEEF
```

### Example 6: Saving to Archive

Save modified scripts to a [module archives](ERF-File-Format):

```ini
[HACKList]
!DefaultDestination=Modules\mymod.mod
File0=modified_script.ncs

[modified_script.ncs]
!Destination=Modules\mymod.mod
ReplaceFile=1

; Multiple modifications
0x50=u16:100
0x60=StrRef5
```

## DeNCS Reference

DeNCS provides comprehensive [NCS](NCS-File-Format) disassembly capabilities for locating exact [byte](GFF-File-Format#gff-data-types) offsets. Understanding its output is essential for HACKList usage.

### [KEY](KEY-File-Format) DeNCS Features

- **Instruction-level disassembly**: See each bytecode instruction
- **offset mapping**: Exact [byte](GFF-File-Format#gff-data-types) positions for each instruction
- **Operand extraction**: View data embedded in instructions
- **Jump resolution**: Understand control flow

### Reading DeNCS Output

```ncs
Offset  Instruction    Args
------  -------------  ----
0x0D    NOP
0x0E    CONSTI         0x00002710 (10000)
0x13    CPDOWNSP       -4
0x15    CONSTI         0x00000064 (100)
0x1A    CPDOWNSP       -4
0x1B    ACTION         0x00401048 (AddObjectToInventory)
0x20    MOVSP          -4
0x22    RETN

Stack:
Before NOP: []
After NOP: []
...
```

To modify the CONSTI at 0x0E, you'd patch bytes 0x0F-0x12 (the 4-[byte](GFF-File-Format#gff-data-types) operand).

### Common Instruction Patterns

Many scripts follow predictable patterns you can target:

**Setting a constant value:**

```ncs
CONSTI <value>
CPDOWNSP -4
```

This pushes a 4-[byte](GFF-File-Format#gff-data-types) integer onto the stack. The value is at offset +1.

**Calling a function:**

```ncs
ACTION <function_pointer>
```

The function pointer is a 4-[byte](GFF-File-Format#gff-data-types) address at offset +1.

**Conditional jumps:**

```ncs
JZ <offset>
```

The jump offset is a 4-[byte](GFF-File-Format#gff-data-types) signed integer at offset +1.

## Common Use Cases

### 1. Updating Hardcoded string References

Many vanilla scripts have hardcoded [StrRef](TLK-File-Format#string-references-strref) values. HACKList lets you redirect them to mod-added entries:

```ini
[TLKList]
; Add your custom string
StrRef99=New Dialog Text

[HACKList]
File0=old_dialog.ncs

[old_dialog.ncs]
; Replace hardcoded StrRef 12345 with your new one
0x100=StrRef99
```

### 2. Patching Spell/Item IDs

When adding new spells or items, existing scripts may need to reference them:

```ini
[2DAList]
Add2DALine1=spells.2da

[Add2DALine1]
2DAMEMORY7=RowIndex

[HACKList]
File0=spell_handler.ncs

[spell_handler.ncs]
; Inject the new spell's row number
0x88=2DAMEMORY7
```

### 3. Adjusting Combat values

Modify damage, duration, or other gameplay values without recompiling:

```ini
[HACKList]
File0=combat_init.ncs

[combat_init.ncs]
; Change damage from 10 to 50
0x30=u16:50

; Change duration from 30 to 60 seconds
0x50=u16:60

; Change cooldown from 5 to 10 seconds
0x70=u16:10
```

### 4. Enabling Debug Features

Some scripts have debug [flags](GFF-File-Format#gff-data-types) that can be enabled:

```ini
[HACKList]
File0=debug_script.ncs

[debug_script.ncs]
; Enable debug flag (assuming it's a boolean at 0x20)
0x20=u8:1
```

### 5. Fixing Known Bugs

Patch bugs in vanilla scripts without distributing modified source:

```ini
[HACKList]
File0=buggy_script.ncs

[buggy_script.ncs]
; Fix incorrect check value
0x50=u16:1

; Fix incorrect comparison
0x70=u32:1000
```

## Troubleshooting

### offset Calculation Errors

**Problem:** Patched value doesn't seem to take effect

**Solutions:**

1. Verify the offset using DeNCS
2. Check if you're modifying the correct bytes (instruction vs operand)
3. Ensure you're not overwriting opcodes accidentally
4. Verify big-endian [byte](GFF-File-Format#gff-data-types) order for multi-[byte](GFF-File-Format#gff-data-types) values

### Memory Token Not Defined

**Problem:** `StrRefN was not defined before use`

**Solutions:**

1. Ensure the token is defined in TLKList/2DAList **before** HACKList execution
2. Check the token number for typos
3. Verify token definition syntax in the appropriate section

**Important:** HACKList executes **after** CompileList and **after** TLKList and 2DAList in HoloPatcher, so memory tokens should be available.

### Wrong data size

**Problem:** Script crashes or behaves unexpectedly after patching

**Solutions:**

1. Verify you're using the correct data size (u8/u16/u32)
2. Check DeNCS output to confirm operand size
3. Ensure you're not truncating large values with u8/u16
4. Verify signed vs unsigned behavior for large values

### file Not Found

**Problem:** `File not found` error during patching

**Solutions:**

1. Verify `!SourceFile` points to correct filename
2. Check `!DefaultSourceFolder` and `!SourceFolder` paths
3. Ensure source file exists in tslpatchdata folder
4. Verify file extension is `.ncs`

### Archival Insertion Issues

**Problem:** Modified script not appearing in [ERF](ERF-File-Format)/MOD/RIM archive

**Solutions:**

1. Verify `!Destination` path uses backslashes
2. Check archive exists before insertion
3. Ensure destination folder structure is correct
4. Verify `ReplaceFile` setting (0 = skip if exists, 1 = overwrite)

## Technical Details

### Execution Order

**HoloPatcher** processes patch lists in this order:

1. InstallList (install files)
2. TLKList (add dialog entries)
3. 2DAList (modify [2DA files](2DA-File-Format))
4. GFFList (modify [GFF](GFF-File-Format) files)
5. **CompileList** (compile [NSS](NSS-File-Format) to [NCS](NCS-File-Format))
6. **HACKList** (modify [NCS](NCS-File-Format) bytecode) ← **You [ARE](GFF-File-Format#are-area) here**
7. SSFList (modify soundset files)

**Important:** This differs from TSLPatcher's original order, where HACKList executes before CompileList. HoloPatcher runs CompileList first to allow scripts to be compiled and then potentially edited. This order change is intentional and should not affect mod compatibility in practice.

All memory tokens from TLKList and 2DAList [ARE](GFF-File-Format#are-area) available during HACKList processing.

### Byte-Level Writing

All multi-[byte](GFF-File-Format#gff-data-types) values [ARE](GFF-File-Format#are-area) written in **[big-endian](https://en.wikipedia.org/wiki/Endianness)** format:

- `u16:0x1234` writes `12 34`
- `u32:0x12345678` writes `12 34 56 78`
- Bytes [ARE](GFF-File-Format#are-area) written from most significant to least significant

### ReplaceFile Behavior

Unlike other patch lists, HACKList's `ReplaceFile` [KEY](KEY-File-Format) does **not** use an exclamation point:

```ini
; CORRECT (HACKList syntax)
ReplaceFile=1

; INCORRECT (this is for other sections)
!ReplaceFile=1
```

`ReplaceFile=0` means "skip if file exists", while `ReplaceFile=1` means "overwrite existing file".

I have no idea why this is the exclusive instance of Stoffe's variables that doesn't use exclamation-point syntax but whatever.

### Compatibility Notes

- PyKotor's HACKList implementation is compatible with TSLPatcher v1.2.10b+
- All [NCS](NCS-File-Format) versions V1.0 are supported
- Archive insertion works for [ERF](ERF-File-Format), MOD, and RIM formats
- Memory tokens from TLKList and 2DAList [ARE](GFF-File-Format#are-area) fully supported
- `!FieldPath` is **not** supported (only numeric values)

## See Also

- [TSLPatcher-GFFList-Syntax.md](TSLPatcher-GFFList-Syntax.md) - [GFF file](GFF-File-Format) modifications
- [TSLPatcher's Official Readme](TSLPatcher's-Official-Readme.md) - General TSLPatcher documentation
- [DeNCS Documentation](http://nwvault.ign.com/View.php?view=Other.Detail&id=416) - [NCS](NCS-File-Format) disassembler
- [NCS Instruction Reference](https://nwn.wiki/compiler/instructions) - Detailed bytecode documentation

## Advanced Topics

### offset Alignment

When working with [NCS](NCS-File-Format) bytecode, be aware of alignment requirements:

- Instructions start on any [byte](GFF-File-Format#gff-data-types) boundary (no alignment enforced)
- Operands follow immediately after opcodes
- Multi-[byte](GFF-File-Format#gff-data-types) values [ARE](GFF-File-Format#are-area) written as-is without padding

### Inserting vs Modifying

**Important:** HACKList can only **modify existing bytes**. It cannot:

- Insert new bytes (files would shift offsets)
- Delete bytes (files would shrink)
- Resize instruction arrays

For structural changes, use CompileList to recompile from [NSS](NSS-File-Format) source.

### Debugging Tips

Enable verbose logging to see HACKList operations:

```ini
[Settings]
LogLevel=4
```

This will show detailed output like:

```ncs
Loading [HACKList] patches from ini...
HACKList myscript.ncs: seeking to offset 0x20
HACKList myscript.ncs: writing unsigned WORD (16-bit) 12345 at offset 0x20
```

### Performance Considerations

HACKList modifications [ARE](GFF-File-Format#are-area) very fast since they're simple binary writes. However:

- Large files with many patches may take slightly longer
- Archive insertion requires archive rewriting
- Always test thoroughly as [byte](GFF-File-Format#gff-data-types)-level modifications can break scripts

### Security Warnings

**Never** patch untrusted [NCS files](NCS-File-Format) without verifying their contents. Malicious bytecode modifications could:

- Execute arbitrary code
- Corrupt save games
- Crash the game
- Exploit vulnerabilities

Always validate offsets and values before distribution.

## Conclusion

HACKList provides powerful [byte](GFF-File-Format#gff-data-types)-level control over compiled [NCS](NCS-File-Format) scripts, enabling surgical modifications without source code access. While it requires understanding [NCS](NCS-File-Format) bytecode structure and careful offset calculation, it's essential for advanced modding scenarios involving dynamic value injection and hardcoded constant patching.

For most modding needs, CompileList ([NSS](NSS-File-Format) source compilation) is preferred. HACKList should be reserved for cases where source code is unavailable or where [byte](GFF-File-Format#gff-data-types)-level precision is required.
