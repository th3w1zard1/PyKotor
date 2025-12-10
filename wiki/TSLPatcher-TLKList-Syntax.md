# TSLPatcher TLKList Syntax Documentation

This guide explains how to modify [TLK files](TLK-File-Format) using TSLPatcher syntax. For the complete [TLK file](TLK-File-Format) [format](GFF-File-Format) specification, see [TLK File Format](TLK-File-Format). For general TSLPatcher information, see [TSLPatcher's Official Readme](TSLPatcher's-Official-Readme). For HoloPatcher-specific information, see [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.).

## Overview

The `[TLKList]` section in TSLPatcher's changes.ini [file](GFF-File-Format) enables you to modify TLK ([Talk Table](TLK-File-Format)) [files](GFF-File-Format) used throughout KotOR. [TLK files](TLK-File-Format) store all in-game text [strings](GFF-File-Format#gff-data-types) and their associated voiceover sound references. The most important [TLK file](TLK-File-Format) is [`dialog.tlk`](TLK-File-Format), which contains all dialog, item descriptions, conversations, and other text displayed in the game.

TSLPatcher was designed by Stoffe with an **append-only philosophy** for [TLK](TLK-File-Format) modifications. This design maximizes mod compatibility by non-destructively adding new entries to the end of [`dialog.tlk`](TLK-File-Format), allowing multiple mods to safely coexist without conflicts.

## Benefits of [TLK](TLK-File-Format) Modification

TSLPatcher's [TLK](TLK-File-Format) modification system provides several [KEY](KEY-File-Format) advantages:

- **Avoid distributing large [files](GFF-File-Format)**: The [`dialog.tlk`](TLK-File-Format) [file](GFF-File-Format) is approximately 10 MB. Instead of distributing the entire modified [file](GFF-File-Format), TSLPatcher allows you to add only your new entries, significantly reducing mod [file](GFF-File-Format) [size](GFF-File-Format#file-structure-overview).

- **Memory system integration**: TSLPatcher keeps StrRefs of newly added entries in memory, allowing you to insert those StrRefs into [2DA](2DA-File-Format) and [GFF files](GFF-File-Format) as needed. For example, if you add the name of a new force power to [`dialog.tlk`](TLK-File-Format), TSLPatcher can memorize the [StrRef](TLK-File-Format#string-references-strref) the name [string](GFF-File-Format#gff-data-types) ended up as, and insert that [value](GFF-File-Format#gff-data-types) into the "name" column in `spells.2da`.

- **Cross-section token usage**: [StrRef](TLK-File-Format#string-references-strref) tokens created in `[TLKList]` can be used throughout other sections:
  - In `[2DAList]` to assign stringrefs to [2DA](2DA-File-Format) cells
  - In `[GFFList]` to assign stringrefs to [GFF](GFF-File-Format) fields (including ExoLocString [fields](GFF-File-Format#file-structure-overview))
  - In `[CompileList]` scripts where `#StrRef#` tokens [ARE](GFF-File-Format#are-area) replaced during compilation
  - In `[SSFList]` to assign stringrefs to soundset entries

## Glossary

- **TLK ([Talk Table](TLK-File-Format))**: Binary [file](GFF-File-Format) [format](GFF-File-Format) storing text [strings](GFF-File-Format#gff-data-types) and voiceover references. The primary [file](GFF-File-Format) is [`dialog.tlk`](TLK-File-Format).

- **StringRef ([StrRef](TLK-File-Format#string-references-strref))**: Short for "[string](GFF-File-Format#gff-data-types) Reference", this is a numeric identifier/[index](2DA-File-Format#row-labels) for an entry in a [TLK file](TLK-File-Format). StringRefs start at 0 and increment sequentially. Example: StringRef 12345 refers to the 12346th entry in a [TLK file](TLK-File-Format). The [StrRef](TLK-File-Format#string-references-strref) is the identifier number that the game engine uses to retrieve text [strings](GFF-File-Format#gff-data-types) from [`dialog.tlk`](TLK-File-Format).

- **[KEY](KEY-File-Format)**: The left side of the `=` symbol in an INI entry (e.g., `StrRef0`, `AppendFile0`)

- **[value](GFF-File-Format#gff-data-types)**: The right side of the `=` symbol in an INI entry. In `[TLKList]`, [values](GFF-File-Format#gff-data-types) specify the [index](2DA-File-Format#row-labels) into [TLK](TLK-File-Format) source [files](GFF-File-Format) to read from.

- **Token**: A placeholder like `StrRef0` or `StrRef1` that gets replaced with an actual StringRef during patching.

- **Append**: Non-destructive operation that adds new entries to the end of [`dialog.tlk`](TLK-File-Format). This is TSLPatcher's primary and recommended method.

- **Replace**: Destructive operation that overwrites existing entries in [`dialog.tlk`](TLK-File-Format). **Should ONLY be used for fixing grammar, spelling, or typographical errors in existing game content.** See [Replace Functionality Warning](#replace-functionality-warning) for details.

- **append.tlk**: Default source [file](GFF-File-Format) containing new [strings](GFF-File-Format#gff-data-types) to append. Created using TalkEd.exe (see [Creating TLK Files](#creating-tlk-files)). Located in `tslpatchdata` folder.

- **appendf.tlk**: Feminine/non-English localized version of `append.tlk`. Used exclusively for KotOR1 Polish localization. Must have exactly the same number of entries as `append.tlk`. See [Localized Versions](#localized-versions) for details.

- **dialog.tlk**: The game's main [TLK file](TLK-File-Format) containing all in-game text (typically ~10 MB). Modified [files](GFF-File-Format) [ARE](GFF-File-Format#are-area) written to the game's root directory (not override folder). TSLPatcher allows you to add new entries without distributing the entire large [file](GFF-File-Format).

## Table of Contents

- [Glossary](#glossary)
- [Benefits of TLK Modification](#benefits-of-tlk-modification)
- [Replace Functionality Warning](#replace-functionality-warning)
- [Creating TLK Files](#creating-tlk-files)
- [Basic Structure](#basic-structure)
- [Configuration Keys](#configuration-keys)
- [Entry Syntax](#entry-syntax)
  - [How Token Creation Works](#how-token-creation-works)
  - [StrRef Entries](#strref-entries)
  - [AppendFile Syntax](#appendfile-syntax)
- [Localized Versions](#localized-versions)
- [Memory System](#memory-system)
- [Processing Order](#processing-order)
- [File Structure](#file-structure-overview)
- [Complete Examples](#complete-examples)
- [Common Use Cases](#common-use-cases)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [Reference](#reference)

## Replace Functionality Warning

⚠️ **CRITICAL: Replace functionality should ONLY be used for fixing grammar, spelling, or typographical errors in existing game content.**

TSLPatcher was designed by Stoffe to be **append-only** for [TLK](TLK-File-Format) modifications. The original TSLPatcher exclusively appended new entries to the end of [`dialog.tlk`](TLK-File-Format) and never replaced existing entries. This design was intentional to maximize mod compatibility:

### Why Replace Should Be Avoided for New Content

- **Breaks mod compatibility**: If two mods replace the same stringref, they conflict irreconcilably
- **Destroys vanilla content**: Replaces original game text permanently, making it impossible to restore
- **Prevents mod stacking**: Can't safely use multiple mods that replace different entries simultaneously
- **Defeats TSLPatcher's design**: The tool was specifically designed for non-destructive appending to avoid conflicts

### Why Append Works Better

- **Non-destructive**: Appending preserves all existing game text, preventing conflicts between mods
- **Dynamic indexing**: Uses tokens (`[StrRef](TLK-File-Format#string-references-strref)#`) to handle variable stringref assignments without hard-coding [indices](2DA-File-Format#row-labels)
- **Mod stacking**: Multiple mods can safely add entries without interfering with each other
- **Compatibility**: Avoids the need to distribute full [`dialog.tlk`](TLK-File-Format) files (10+ MB), reducing mod [size](GFF-File-Format#file-structure-overview)

### Acceptable Uses of Replace

- ✅ Fixing typos in base game text (e.g., "teh" → "the")
- ✅ Correcting grammar mistakes in vanilla content
- ✅ Fixing broken or corrupted entries
- ✅ Community patch projects (like K1CP) that systematically fix errors

### When NOT to Use Replace

- ❌ Adding new content (use AppendFile or [StrRef](TLK-File-Format#string-references-strref) syntax instead)
- ❌ Modifying existing text for flavor/preference
- ❌ Any scenario where append would work

**For all new content, always use the append-based syntaxes described in [Entry Syntax](#entry-syntax).**

## Creating [TLK](TLK-File-Format) [files](GFF-File-Format)

To use custom [dialog.tlk](TLK-File-Format) entries in your mod, you must create source [TLK files](TLK-File-Format) containing your new [strings](GFF-File-Format#gff-data-types):

### Using TalkEd.exe

1. **Create a new [TLK file](TLK-File-Format)**: Use TalkEd.exe (a [TLK](TLK-File-Format) editor tool) to create a new [TLK file](TLK-File-Format)
2. **Add your entries**: Add all your new text [strings](GFF-File-Format#gff-data-types) and voiceover sound references to this [file](GFF-File-Format)
3. **Save as append.tlk**: Name the [file](GFF-File-Format) exactly `append.tlk` (case-sensitive)
4. **Place in tslpatchdata**: Save `append.tlk` in the `tslpatchdata` folder

### Localized Versions (KotOR1 Polish only)

If you [ARE](GFF-File-Format#are-area) using a non-English version of KotOR1 that has a `dialogf.tlk` file (Polish localization), you must also:

1. **Create appendf.tlk**: Create a new [file](GFF-File-Format) with the feminine form of your [strings](GFF-File-Format#gff-data-types)
2. **Name it appendf.tlk**: Must be named exactly `appendf.tlk` (case-sensitive)
3. **Match entry [count](GFF-File-Format#file-structure-overview)**: **`appendf.tlk` must have exactly the same number of entries as `append.tlk`**
4. **Matching [indices](2DA-File-Format#row-labels)**: Each [index](2DA-File-Format#row-labels) in `appendf.tlk` should correspond to the same [index](2DA-File-Format#row-labels) in `append.tlk`
5. **Handle missing forms**: If a [string](GFF-File-Format#gff-data-types) has no specific feminine form, put the same text in both [files](GFF-File-Format)

**Important**: The entry [count](GFF-File-Format#file-structure-overview) must match exactly. If `append.tlk` has 100 entries, `appendf.tlk` must also have exactly 100 entries, even if some [ARE](GFF-File-Format#are-area) identical between the two [files](GFF-File-Format).

### Using ChangeEdit (Optional)

The ChangeEdit application provides a user-friendly [GUI](GFF-File-Format#gui-graphical-user-interface) interface for configuring [TLK](TLK-File-Format) entries without manually editing the INI [file](GFF-File-Format):

1. **Open append.tlk**: In ChangeEdit, navigate to the "[TLK](TLK-File-Format) Entries" section in the tree view
2. **Load [file](GFF-File-Format)**: Press the "Open append.tlk [file](GFF-File-Format)..." button on top of the right list
3. **View entries**: This lists all your custom text entries in the list to the right
4. **Select entries**: Select an entry you wish TSLPatcher to add to [`dialog.tlk`](TLK-File-Format)
5. **Add to list**: Press the left arrow icon (←) to add the entry to the list on the left
6. **Token creation**: Take note of the [value](GFF-File-Format#gff-data-types) in the left column, which should look like `StrRef0` for the first entry, with an incrementing number (`StrRef1`, `StrRef2`, etc.) for each subsequent entry
7. **Use tokens**: This token (e.g., `StrRef0`) is what you'll use in the [2DA](2DA-File-Format) and [GFF](GFF-File-Format) sections to assign the resulting [StrRef](TLK-File-Format#string-references-strref) [value](GFF-File-Format#gff-data-types) to a [2DA](2DA-File-Format) cell or [GFF](GFF-File-Format) [field](GFF-File-Format#file-structure-overview)

**Manual Editing**: While ChangeEdit provides a [GUI](GFF-File-Format#gui-graphical-user-interface) interface, you can also edit the `changes.ini` [file](GFF-File-Format) directly with any text editor (Notepad, VS Code, etc.). The INI [format](GFF-File-Format) is plain text and human-readable.

**Important**: When using ChangeEdit, always verify the generated INI entries match your expectations, especially for token names and entry [indices](2DA-File-Format#row-labels).

## Basic [structure](GFF-File-Format#file-structure-overview)

```ini
[TLKList]
!DefaultDestination=.
!DefaultSourceFolder=.
!SourceFile=append.tlk
!SourceFileF=appendf.tlk

; Append new entries
StrRef0=0
StrRef1=1

; Append from custom file (Useful if you have a LOT of TLK entries and want to organize within multiple [TLK files](TLK-File-Format))
AppendFile0=custom_entries.tlk

[custom_entries.tlk]
0=10
1=11
```

**[KEY](KEY-File-Format) Points:**

- All examples use **append** operations - the recommended approach
- [values](GFF-File-Format#gff-data-types) specify which [StrRef](TLK-File-Format#string-references-strref) [indices](2DA-File-Format#row-labels) to read from source [files](GFF-File-Format)

## Configuration Keys

### `!DefaultDestination`

- **type**: String (path)
- **Default**: `.` (kotor game installation path root)
- **Description**: Default destination folder for [TLK files](TLK-File-Format) when not overridden
- **Example**: `!DefaultDestination=override`

### `!DefaultSourceFolder`

- **type**: String (path)
- **Default**: `.` (tslpatchdata folder)
- **Description**: Default folder to search for [TLK](TLK-File-Format) source files (e.g., `append.tlk`). This is a relative path from `mod_path`, which is typically the `tslpatchdata` folder (the parent directory of the `changes.ini` [file](GFF-File-Format)). The default [value](GFF-File-Format#gff-data-types) `.` refers to the `tslpatchdata` folder itself.
- **Path Resolution**: [files](GFF-File-Format) [ARE](GFF-File-Format#are-area) resolved as `mod_path / !DefaultSourceFolder / filename`. When `mod_path = "C:/Mod/tslpatchdata"`:
  - `!DefaultSourceFolder=.` resolves to e.g. `"C:/Mod/tslpatchdata"`
  - `!DefaultSourceFolder=tlk_files` resolves to e.g. `"C:/Mod/tslpatchdata/tlk_files"`
- **Example**: `!DefaultSourceFolder=.` (default, refers to tslpatchdata folder)

### `!SourceFile`

- **type**: String (filename)
- **Default**: `append.tlk`
- **Description**: Name of the [TLK file](TLK-File-Format) to use when appending entries via [StrRef](TLK-File-Format#string-references-strref) syntax
- **Example**: `!SourceFile=my_strings.tlk`

### `!SourceFileF`

- **type**: String (filename)
- **Default**: `appendf.tlk`
- **Description**: Name of the [TLK file](TLK-File-Format) to use for feminine/non-English localized versions (exclusively KotOR1 Polish)
- **Version Added**: 1.2.8b6
- **Note**: Must have exactly the same number of entries as `!SourceFile`. Each [index](2DA-File-Format#row-labels) in `appendf.tlk` maps directly to the same [index](2DA-File-Format#row-labels) in `append.tlk`. If a [string](GFF-File-Format#gff-data-types) has no specific feminine form, put the same text in both [files](GFF-File-Format).
- **Example**: `!SourceFileF=my_strings_f.tlk`

### Unsupported Keys

The following keys [ARE](GFF-File-Format#are-area) **NOT** supported in `[TLKList]`:

- `!ReplaceFile` - Not applicable to [TLK files](TLK-File-Format)
- `!OverrideType` - Not applicable to [TLK files](TLK-File-Format)

## Entry Syntax

The `[TLKList]` section supports two primary entry syntax patterns, both using **append** operations:

1. **[StrRef](TLK-File-Format#string-references-strref) Entries** - Append from the default source file (`append.tlk`)
2. **AppendFile Syntax** - Append from custom [TLK files](TLK-File-Format) with flexible mappings

### How Token Creation Works

**Important**: Tokens [ARE](GFF-File-Format#are-area) created from the **[value](GFF-File-Format#gff-data-types)** (the number on the right side of `=`). For `StrRef<number>=<number>` entries, the number in the [KEY](KEY-File-Format) and [value](GFF-File-Format#gff-data-types) must match, and this matching number determines the token name.

- `StrRef0=0` creates token `StrRef0` (reads [index](2DA-File-Format#row-labels) 0 from `append.tlk`)
- `StrRef5=5` creates token `StrRef5` (reads [index](2DA-File-Format#row-labels) 5 from `append.tlk`)
- For AppendFile subsections, `10=10` creates token `StrRef10` (reads [index](2DA-File-Format#row-labels) 10 from the source [TLK](TLK-File-Format))

The token name `[StrRef](TLK-File-Format#string-references-strref)<number>` is created from the matching number, and this token stores the new stringref that gets appended to [`dialog.tlk`](TLK-File-Format) for use in other sections.

### [StrRef](TLK-File-Format#string-references-strref) Entries

**Purpose**: Append new entries to [`dialog.tlk`](TLK-File-Format) from the default source file (`append.tlk`)

**Syntax**:

```ini
StrRef<number>=<number>
```

**Parameters**:

- `<number>` - The [index](2DA-File-Format#row-labels) into `append.tlk` (or `!SourceFile`) to read from. This number must match in both the [KEY](KEY-File-Format) and [value](GFF-File-Format#gff-data-types).

**Behavior**:

- Appends a new entry to the end of [`dialog.tlk`](TLK-File-Format) (non-destructive)
- Reads text and sound from `append.tlk` at the specified [index](2DA-File-Format#row-labels)
- The new entry receives the next available stringref automatically
- Creates token `StrRef<number>` from the matching number (see [How Token Creation Works](#how-token-creation-works))
- Stores that new stringref in memory for use in other sections via the token

**Examples**:

```ini
[TLKList]
StrRef0=0  ; Reads index 0 from append.tlk, creates token StrRef0
StrRef1=1  ; Reads index 1 from append.tlk, creates token StrRef1
StrRef2=2  ; Reads index 2 from append.tlk, creates token StrRef2
```

### AppendFile Syntax

**Purpose**: Add entries from a custom [TLK file](TLK-File-Format) using [index](2DA-File-Format#row-labels) mappings

**Syntax**:

```ini
AppendFile<anything>=<tlk_filename>
```

**Parameters**:

- `<tlk_filename>` - Name of a [TLK file](TLK-File-Format) in the source folder OR name of a subsection in the INI

**Behavior**:

- Creates a **new section** `[<tlk_filename>]` if the [file](GFF-File-Format) doesn't exist in source
- Maps entries from the source [TLK](TLK-File-Format) to [`dialog.tlk`](TLK-File-Format) using the subsection mappings
- All entries [ARE](GFF-File-Format#are-area) **added** (not replaced) to [`dialog.tlk`](TLK-File-Format)
- For AppendFile, entries [ARE](GFF-File-Format#are-area) appended and tokens [ARE](GFF-File-Format#are-area) created from the mapping [values](GFF-File-Format#gff-data-types)

**Subsection Syntax**:

```ini
[<tlk_filename>]
<token_identifier>=<source_index>
StrRef<token_identifier>=StrRef<source_index>  ; Alternative explicit syntax
```

**Subsection Parameters**:

- `<source_index>` - The [index](2DA-File-Format#row-labels) into the source [TLK file](TLK-File-Format) to read from. Token `StrRef{source_index}` is created from this [value](GFF-File-Format#gff-data-types). The number in the [KEY](KEY-File-Format) should match the number in the [value](GFF-File-Format#gff-data-types) for clarity.

**Examples**:

```ini
[TLKList]
AppendFile0=planets.tlk  ; Creates subsection [planets.tlk] for mappings

[planets.tlk]
10=10  ; Reads index 10, creates token StrRef10
11=11  ; Reads index 11, creates token StrRef11
12=12  ; Reads index 12, creates token StrRef12 (alternative: StrRef12=StrRef12)
```

**Important Notes**:

- The `<anything>` in `AppendFile<anything>` is arbitrary and ignored
- The subsection `[planets.tlk]` can define mappings using numeric [indices](2DA-File-Format#row-labels) or `[StrRef](TLK-File-Format#string-references-strref)` syntax

## Localized Versions

### KotOR1 Polish Localization

KotOR1 Polish edition uses both [`dialog.tlk`](TLK-File-Format) and `dialogf.tlk` [files](GFF-File-Format). If your mod supports this localization:

1. **Create both [files](GFF-File-Format)**: Create `append.tlk` (masculine/standard) and `appendf.tlk` (feminine/localized)
2. **Match entry counts**: Both [files](GFF-File-Format) must have exactly the same number of entries
3. **Map [indices](2DA-File-Format#row-labels)**: Entry at [index](2DA-File-Format#row-labels) 0 in `append.tlk` corresponds to [index](2DA-File-Format#row-labels) 0 in `appendf.tlk`
4. **Handle duplicates**: If a [string](GFF-File-Format#gff-data-types) doesn't have a feminine form, use the same text in both [files](GFF-File-Format)

### Configuration

```ini
[TLKList]
!SourceFile=append.tlk
!SourceFileF=appendf.tlk
StrRef0=0
StrRef1=1
```

When TSLPatcher processes entries, it automatically uses `appendf.tlk` when the target game has `dialogf.tlk` present.

### Non-English Localization Notes

- **KotOR2**: Does not use `dialogf.tlk` - only [`dialog.tlk`](TLK-File-Format) is used
- **Other Languages**: Currently only KotOR1 Polish uses the dual-[TLK](TLK-File-Format) system
- **Entry Matching**: The strict requirement for matching entry counts ensures proper localization mapping

## Memory System

When [TLK](TLK-File-Format) entries [ARE](GFF-File-Format#are-area) **added** via append operations, TSLPatcher stores them in memory for use in other patch sections.

### Memory Storage

```python
# After append operation (StrRef or AppendFile)
memory.memory_str[token_identifier] = new_stringref
```

**Behavior**:

- For **append** operations: Stores the new stringref that was added, mapped to the token identifier (see [How Token Creation Works](#how-token-creation-works))
- For **replace** operations: Memory is not typically stored (no need since stringref is static)

### Token Creation from [values](GFF-File-Format#gff-data-types)

Tokens [ARE](GFF-File-Format#are-area) created from the matching number in both the [KEY](KEY-File-Format) and [value](GFF-File-Format#gff-data-types). See [How Token Creation Works](#how-token-creation-works) for details. After processing, tokens [ARE](GFF-File-Format#are-area) available for use in other sections like `[2DAList]`, `[GFFList]`, and `[CompileList]`.

### Using [TLK](TLK-File-Format) Memory in Other Sections

**In [2DA files](2DA-File-Format)**:

```ini
[TLKList]
StrRef0=0  ; Creates token StrRef0

[2DAList]
Table0=spells.2da

[spells.2da]
AddRow0=new_spell
2DAMEMORY0=StrRef0  ; Store stringref in 2DA memory for cross-file use

[new_spell]
name=StrRef0  ; Token gets replaced with actual stringref
```

**In [GFF files](GFF-File-Format)**:

```ini
[TLKList]
StrRef0=0  ; Creates token StrRef0

[GFFList]
File0=item.uti

[item.uti]
LocalizedName=StrRef0  ; Token gets replaced with actual stringref
```

**In [NSS](NSS-File-Format) Scripts (CompileList)**:

```nss
// Script compilation will replace #StrRef# tokens
void main() {
    // #StrRef0# token gets replaced with actual stringref during compilation
    SendMessageToPC(GetFirstPC(), #StrRef0#);
}
```

## Processing Order

### TSLPatcher Execution Order

In **TSLPatcher v1.2.8 and later**, the TLKList section is processed **first** in the patching pipeline (before InstallList):

```text
TSLPatcher Execution Order (v1.2.8+):
1. [TLKList]         - Add TLK entries (append operations)
2. [InstallList]     - Copy files to installation
3. [2DAList]         - Add/Modify 2DA entries
4. [GFFList]         - Add/Modify GFF entries
5. [CompileList]     - Compile NSS scripts (replaces #StrRef# tokens)
6. [SSFList]         - Modify soundset files
```

**Note**: In TSLPatcher v1.2.8b0 (2006-08-06), the processing order was changed so that [TLK](TLK-File-Format) Appending happens before Install List. According to the official change log, this allows [ERF](ERF-File-Format)/MOD/RIM [files](GFF-File-Format) to be placed in their proper locations before [GFF](GFF-File-Format) and script compilation sections run, so modified [files](GFF-File-Format) can be saved into those archive [files](GFF-File-Format).

**Older TSLPatcher versions** (before 1.2.8) processed InstallList before TLKList.

### HoloPatcher Execution Order

**HoloPatcher** (a modern Python drop-in replacement for TSLPatcher) uses a **different execution order**:

```text
HoloPatcher Execution Order:
1. [InstallList]     - Copy files to installation
2. [TLKList]         - Add TLK entries (append operations) ← HERE
3. [2DAList]         - Add/Modify 2DA entries
4. [GFFList]         - Add/Modify GFF entries
5. [CompileList]     - Compile NSS scripts (replaces #StrRef# tokens)
6. [HACKList]        - Patch [NCS files](NCS-File-Format)
7. [SSFList]         - Modify soundset files
```

**Important Compatibility Note**: This is a **backwards-compatible discrepancy** between TSLPatcher and HoloPatcher. HoloPatcher processes InstallList before TLKList to allow users to install a base [`dialog.tlk`](TLK-File-Format) file (or other [files](GFF-File-Format)) via InstallList, which can then be modified by [TLK](TLK-File-Format) appending operations. This order provides greater flexibility for mod workflows.

### Analysis: Order Comparison

**TSLPatcher's reasoning** (TLKList → InstallList):

- Allows [ERF](ERF-File-Format)/MOD/RIM [files](GFF-File-Format) to be placed before [GFF](GFF-File-Format)/Compile sections that save into them

**HoloPatcher's reasoning** (InstallList → TLKList):

- ✅ **More flexible**: Users can install a custom base [`dialog.tlk`](TLK-File-Format) [file](GFF-File-Format) via InstallList, then [TLK](TLK-File-Format) appending modifies it
- ✅ **Better for testing**: Allows installing known-good [TLK files](TLK-File-Format) before appending new entries
- ✅ **Preserves dependencies**: [TLK](TLK-File-Format) entries [ARE](GFF-File-Format#are-area) still processed before [2DA](2DA-File-Format)/[GFF](GFF-File-Format)/Compile/[SSF](SSF-File-Format) sections that reference them
- ✅ **More intuitive**: [file](GFF-File-Format) installation happens first, then modifications [ARE](GFF-File-Format#are-area) applied

**Critical Timing** (applies to both TSLPatcher and HoloPatcher):

- [TLK](TLK-File-Format) entries [ARE](GFF-File-Format#are-area) added to the destination target [`dialog.tlk`](TLK-File-Format) **before** [2DA](2DA-File-Format) and [GFF](GFF-File-Format) modifications
- This ensures stringrefs/[TLK](TLK-File-Format) entries [ARE](GFF-File-Format#are-area) available when referenced by other sections
- Script compilation happens **after** [TLK](TLK-File-Format) processing, so `#[StrRef](TLK-File-Format#string-references-strref)#` tokens can be resolved
- Tokens [ARE](GFF-File-Format#are-area) substituted in [2DA](2DA-File-Format), [GFF](GFF-File-Format), and script [files](GFF-File-Format) after [TLK](TLK-File-Format) entries have been appended

## [file](GFF-File-Format) [structure](GFF-File-Format#file-structure-overview)

### [TLK](TLK-File-Format) [file](GFF-File-Format) [format](GFF-File-Format)

A [TLK file](TLK-File-Format) is a binary [format](GFF-File-Format) containing:

- **[header](GFF-File-Format#file-header)**: [file](GFF-File-Format) type (`TLK`), version (`V3.0`), language ID, [string](GFF-File-Format#gff-data-types) [count](GFF-File-Format#file-structure-overview), entries [offset](GFF-File-Format#file-structure-overview)
- **Entry [headers](GFF-File-Format#file-header)**: [flags](GFF-File-Format#gff-data-types), sound ResRef (16 bytes), volume/pitch variance (unused), text [offset](GFF-File-Format#file-structure-overview), text length, sound length (unused)
- **Text [data](GFF-File-Format#file-structure-overview)**: Actual [string](GFF-File-Format#gff-data-types) content stored at the specified [offsets](GFF-File-Format#file-structure-overview)

**[TLK](TLK-File-Format) Entry [structure](GFF-File-Format#file-structure-overview)**:

```python
class TLKEntry:
    text: str              # The display text (UTF-8 or cp1252 encoding)
    voiceover: ResRef      # Sound file ResRef (max 16 characters)
    sound_length: float    # Unused by KotOR (present in format but ignored)
```

**[string](GFF-File-Format#gff-data-types) Length Limitations**:

- **TSLPatcher v1.2.8b6 and later**: Can handle [TLK](TLK-File-Format) entries with [strings](GFF-File-Format#gff-data-types) of **any [size](GFF-File-Format#file-structure-overview)** (no practical limit)
- **Earlier versions**: Had a bug that prevented proper handling of [strings](GFF-File-Format#gff-data-types) longer than 4096 characters
- If you encounter issues with long [strings](GFF-File-Format#gff-data-types), ensure you're using TSLPatcher v1.2.8b6 or later. HoloPatcher does **NOT** have this bug.

### KotOR [TLK](TLK-File-Format) [files](GFF-File-Format)

**Standard [files](GFF-File-Format)**:

- [`dialog.tlk`](TLK-File-Format) - Main English dialog (always present in game directory)

**Localized Versions** (exclusively KotOR1 Polish):

- `dialogf.tlk` - Feminine/non-English localized version
- Must match the number of entries in [`dialog.tlk`](TLK-File-Format) exactly

**Entry [indices](2DA-File-Format#row-labels)**:

- StringRefs start at 0 and increment sequentially
- Valid entries: 0 to (total_entries - 1)
- Reference entries as integers throughout the game and mod [files](GFF-File-Format)

## Complete Examples

### Example 1: Simple Append with [StrRef](TLK-File-Format#string-references-strref)

Add new [string](GFF-File-Format#gff-data-types) entries from `append.tlk` to [`dialog.tlk`](TLK-File-Format):

```ini
[TLKList]
StrRef0=0
StrRef1=1
StrRef2=2
```

**[files](GFF-File-Format)**: `tslpatchdata/append.tlk` contains entries 0, 1, 2 with your custom text

**Result**: Each entry from `append.tlk` is appended to [`dialog.tlk`](TLK-File-Format) and assigned the next available stringref (e.g., 123456, 123457, 123458). These new stringrefs [ARE](GFF-File-Format#are-area) stored in memory as tokens `StrRef0`, `StrRef1`, `StrRef2` for use in other sections.

### Example 2: Append with Custom [file](GFF-File-Format)

Add entries from a custom [TLK file](TLK-File-Format) using [index](2DA-File-Format#row-labels) mappings:

```ini
[TLKList]
AppendFile0=planets.tlk

[planets.tlk]
0=10   ; Reads index 10, creates token StrRef10
1=11   ; Reads index 11, creates token StrRef11
2=12   ; Reads index 12, creates token StrRef12
```

**[files](GFF-File-Format)**: `tslpatchdata/planets.tlk` contains entries at [indices](2DA-File-Format#row-labels) 10, 11, 12, etc.

**Result**: Each entry from `planets.tlk` is appended to [`dialog.tlk`](TLK-File-Format) and tokens `StrRef10`, `StrRef11`, `StrRef12` [ARE](GFF-File-Format#are-area) created (from the [values](GFF-File-Format#gff-data-types), not the keys).

### Example 3: Combined Append Operations

Use multiple append methods together:

```ini
[TLKList]
!SourceFile=append.tlk
StrRef0=0
StrRef1=1
AppendFile0=items.tlk

[items.tlk]
0=100   ; Creates token StrRef100
1=101   ; Creates token StrRef101
```

**[files](GFF-File-Format)**: `tslpatchdata/append.tlk` (entries 0, 1), `tslpatchdata/items.tlk` (entries 100, 101)

**Processing Order**: Entries [ARE](GFF-File-Format#are-area) processed sequentially, creating tokens `StrRef0`, `StrRef1`, `StrRef100`, `StrRef101`.

### Example 4: Localized Version (Polish KotOR1)

Support for feminine/localized versions:

```ini
[TLKList]
!SourceFile=append.tlk
!SourceFileF=appendf.tlk
StrRef0=0
StrRef1=1
StrRef2=2
```

**[files](GFF-File-Format)**:

- `append.tlk` (masculine/English) - Contains 3 entries ([indices](2DA-File-Format#row-labels) 0, 1, 2)
- `appendf.tlk` (feminine/Polish) - Must have exactly 3 entries ([indices](2DA-File-Format#row-labels) 0, 1, 2)

**Requirements**:

- Both [files](GFF-File-Format) must have **exactly the same number of entries**
- Entry at [index](2DA-File-Format#row-labels) 0 in `append.tlk` maps to [index](2DA-File-Format#row-labels) 0 in `appendf.tlk`
- If a [string](GFF-File-Format#gff-data-types) has no feminine form, use the same text in both [files](GFF-File-Format)
- TSLPatcher automatically uses `appendf.tlk` when the target game has `dialogf.tlk` present

## Common Use Cases

### Adding New Dialog for NPCs

**Scenario**: Add custom lines for a new NPC

**Solution**:

```ini
[TLKList]
StrRef0=0  ; Greeting line
StrRef1=1  ; Quest offer
StrRef2=2  ; Refusal response

[GFFList]
File0=my_npc.dlg

[my_npc.dlg]
; Reference tokens StrRef0, StrRef1, StrRef2 in dialog entries
```

### Adding Item Descriptions

**Scenario**: Add descriptions for new items

**Solution**:

```ini
[TLKList]
AppendFile0=items.tlk

[items.tlk]
0=10  ; Item name → token StrRef10
1=11  ; Item description → token StrRef11
2=12  ; Another item name → token StrRef12
3=13  ; Another item description → token StrRef13

[GFFList]
File0=new_item.uti

[new_item.uti]
LocalizedName=StrRef10
DescIdentified=StrRef11
```

### Translating Mod Content

**Scenario**: Create English and non-English versions

**Solution**:

```ini
[TLKList]
!SourceFile=append_en.tlk
!SourceFileF=append_de.tlk
StrRef0=0
StrRef1=1
StrRef2=2
```

**[files](GFF-File-Format)**: Both `append_en.tlk` (English) and `append_de.tlk` (German) must match entry [count](GFF-File-Format#file-structure-overview) exactly. TSLPatcher uses the appropriate [file](GFF-File-Format) based on game localization.

## Troubleshooting

### Error: "Invalid syntax found in [TLKList]"

**Cause**: Unrecognized [KEY](KEY-File-Format) [format](GFF-File-Format)

**Solutions**:

- Check for typos in [KEY](KEY-File-Format) names
- Ensure you're using one of the supported syntaxes: `[StrRef](TLK-File-Format#string-references-strref)<key>=<value>` or `AppendFile<key>=<value>`
- Verify the [KEY](KEY-File-Format) matches the expected pattern

**Correct Syntaxes**:

```ini
; StrRef syntax: Key can be anything, value must be numeric
StrRef0=0
StrRef1=1

; AppendFile syntax: Key starts with "AppendFile", value is filename
AppendFile0=file.tlk
AppendFile1=another.tlk
```

### Error: "Could not parse '[KEY](KEY-File-Format)=[value](GFF-File-Format#gff-data-types)' in [TLKList]"

**Cause**: Invalid numeric [values](GFF-File-Format#gff-data-types) or malformed entries

**Solutions**:

- Ensure [values](GFF-File-Format#gff-data-types) [ARE](GFF-File-Format#are-area) valid integers for [StrRef](TLK-File-Format#string-references-strref)/AppendFile mappings
- Check that numeric keys can be parsed as integers if using numeric [format](GFF-File-Format)
- Verify no extra spaces or invalid characters

**Correct**:

```ini
StrRef0=0
StrRef123=123
```

**Incorrect**:

```ini
StrRef0=abc  ; Value must be numeric
StrRef=0  ; Missing numeric part in key
```

### Error: "Section [filename] not found"

**Cause**: Referenced [TLK file](TLK-File-Format) or subsection doesn't exist

**Solutions**:

- Create the subsection in the INI if using internal mappings:

  ```ini
  AppendFile0=myfile.tlk
  [myfile.tlk]  ; Must create this subsection
  0=1
  ```

- Or ensure the [file](GFF-File-Format) exists in the source folder if using external [TLK files](TLK-File-Format)
- Check `!DefaultSourceFolder` path is correct

### Error: "Cannot replace nonexistent stringref in [dialog.tlk](TLK-File-Format)"

**Cause**: Trying to replace an entry that doesn't exist (if using replace functionality)

**Solutions**:

- For new content, use append syntax (`[StrRef](TLK-File-Format#string-references-strref)` or `AppendFile`) instead of replace
- Verify the stringref number is correct if you must use replace for error fixing
- Remember: **Always use append for new content** - see [Replace Functionality Warning](#replace-functionality-warning)

**Adding New** (use this):

```ini
StrRef0=0  ; Appends new entry, creates token StrRef0
```

### Issue: Entries Not Appearing

**Cause**: Multiple possible issues

**Solutions**:

- Check [file](GFF-File-Format) paths: `!DefaultSourceFolder` and [file](GFF-File-Format) locations
- Verify [TLK file](TLK-File-Format) [format](GFF-File-Format): must be valid binary [TLK](TLK-File-Format)
- Check [file](GFF-File-Format) encoding: should be UTF-8 or cp1252
- Ensure the [file](GFF-File-Format) is in the tslpatchdata folder (or specified source folder)
- Review the log for processing errors
- Verify keys and [values](GFF-File-Format#gff-data-types) [ARE](GFF-File-Format#are-area) correctly formatted

### Issue: Wrong Token Created

**Cause**: Confusion about token creation from keys vs [values](GFF-File-Format#gff-data-types)

**Solutions**:

- See [How Token Creation Works](#how-token-creation-works) - tokens [ARE](GFF-File-Format#are-area) created from the **[value](GFF-File-Format#gff-data-types)** (matching number)
- `StrRef0=0` creates token `StrRef0`
- `StrRef5=5` creates token `StrRef5`

### Issue: Memory Tokens Not Working

**Cause**: Token not created or not accessible in other sections

**Solutions**:

- Verify the stringref was actually added (check logs)
- Ensure you're using the correct token name (created from matching number)
- Check memory is being used in the correct execution order
- Tokens [ARE](GFF-File-Format#are-area) only created for **append** operations, not replace operations

**Example**:

```ini
[TLKList]
StrRef0=0  ; Creates token StrRef0

[2DAList]
Table0=spells.2da

[spells.2da]
name=StrRef0  ; Use the token
```

### Issue: [files](GFF-File-Format) with Many Entries

**Best Practice**: Use AppendFile with subsections for clarity and organization

**Good** (Organized by content type):

```ini
[TLKList]
AppendFile0=items.tlk
AppendFile1=npcs.tlk

[items.tlk]
0=100   ; Token: StrRef100 - Item name
1=101   ; Token: StrRef101 - Item description
; ... many more entries

[npcs.tlk]
0=200   ; Token: StrRef200 - NPC greeting
1=201   ; Token: StrRef201 - NPC dialogue
; ... many more entries
```

**Less Ideal** (but still works for small mods):

```ini
[TLKList]
StrRef0=0
StrRef1=1
StrRef2=2
; ... 200 more lines becomes hard to manage
```

### Issue: Write-Protected [dialog.tlk](TLK-File-Format)

**Cause**: Some systems have [`dialog.tlk`](TLK-File-Format) set to read-only or write-protected

**Solutions**:

- Check [file](GFF-File-Format) permissions on [`dialog.tlk`](TLK-File-Format) in the game directory
- Run TSLPatcher with administrator privileges if needed
- Ensure the game is not running when installing mods
- Check if antivirus software is blocking [file](GFF-File-Format) modification

**Note**: TSLPatcher v1.2.8b8 fixed a bug where installation would stop when [`dialog.tlk`](TLK-File-Format) was write-protected. If using an older version, ensure the [file](GFF-File-Format) is writable.

## Best Practices

### 1. Organization

- Group related entries in separate [TLK files](TLK-File-Format)
- Use descriptive [file](GFF-File-Format) names: `npcs.tlk`, `items.tlk`, `planets.tlk`
- Keep the main INI clean with AppendFile/[StrRef](TLK-File-Format#string-references-strref) references
- Document which tokens correspond to which content

### 2. Token Management

- See [How Token Creation Works](#how-token-creation-works) for token creation details
- Use consistent numbering to create predictable token names
- Document token usage in comments when helpful:

  ```ini
  StrRef0=0  ; NPC greeting
  ```

### 3. Compatibility

- **Always use append for new content** - this is TSLPatcher's design
- Never use replace functionality except for fixing existing errors (see [Replace Functionality Warning](#replace-functionality-warning))
- Document which stringrefs [ARE](GFF-File-Format#are-area) custom vs modified
- Use descriptive token names by choosing appropriate numbers

### 4. Testing

- Verify all [TLK files](TLK-File-Format) [ARE](GFF-File-Format#are-area) valid before packaging
- Check stringref assignments in logs
- Test with multiple mods installed to check compatibility
- Use `KotorDiff` to compare before/after [`dialog.tlk`](TLK-File-Format)
- Verify tokens [ARE](GFF-File-Format#are-area) correctly created and accessible

### 5. [file](GFF-File-Format) Management

- **Create with TalkEd.exe**: Use TalkEd.exe to create and edit your source [TLK](TLK-File-Format) files (see [Creating TLK Files](#creating-tlk-files))
- **Keep source [TLK files](TLK-File-Format) readable**: Use JSON export for debugging if your [TLK](TLK-File-Format) editor supports it
- **Maintain consistent naming**: Always use `append.tlk` and `appendf.tlk` (or set `!SourceFile`/`!SourceFileF` if using custom names)
- **Version control**: Keep [TLK files](TLK-File-Format) separately from other mod [files](GFF-File-Format) for easier management
- **Match entry counts**: If using localized versions, ensure `append.tlk` and `appendf.tlk` have **exactly the same number of entries**
- **[file](GFF-File-Format) [size](GFF-File-Format#file-structure-overview) considerations**: The [`dialog.tlk`](TLK-File-Format) [file](GFF-File-Format) is ~10 MB, but you only need to distribute small `append.tlk` [files](GFF-File-Format) with your mod

### 6. Localization

- **KotOR1 Polish only**: The dual-[TLK](TLK-File-Format) system ([`dialog.tlk`](TLK-File-Format) + `dialogf.tlk`) is exclusively for KotOR1 Polish localization
- **Maintain parallel [files](GFF-File-Format)**: If supporting Polish, maintain both `append.tlk` and `appendf.tlk`
- **Exact entry matching**: Entry counts must match exactly between `append.tlk` and `appendf.tlk`
- **Map [indices](2DA-File-Format#row-labels)**: Each [index](2DA-File-Format#row-labels) must correspond between the two files ([index](2DA-File-Format#row-labels) 0 → [index](2DA-File-Format#row-labels) 0, [index](2DA-File-Format#row-labels) 1 → [index](2DA-File-Format#row-labels) 1, etc.)
- **Handle duplicates**: If a [string](GFF-File-Format#gff-data-types) has no feminine form, use the same text in both [files](GFF-File-Format)
- **Use configuration keys**: Set `!SourceFileF` to specify the feminine version filename
- **Documentation**: Document language support in your mod's README
- **KotOR2/TSL**: Does not use `dialogf.tlk` - only create `append.tlk` for KotOR2 mods

### 7. Key/[value](GFF-File-Format#gff-data-types) Clarity

- Keys appear on the left side of `=`, [values](GFF-File-Format#gff-data-types) on the right
- For `[StrRef](TLK-File-Format#string-references-strref)<number>=<number>`, numbers must match for proper token creation
- Use consistent numbering for readability

## Reference

### Supported Entry Patterns

| Pattern | Syntax | Purpose | Replacement |
|---------|--------|---------|-------------|
| [StrRef](TLK-File-Format#string-references-strref) | `[StrRef](TLK-File-Format#string-references-strref)<number>=<number>` | Append from default [file](GFF-File-Format) | No |
| AppendFile | `AppendFile<anything>=<filename>` | Append from custom [file](GFF-File-Format) | No |

### Memory System Reference

```python
# After StrRef append
# StrRef0=0 → Creates token StrRef0
# Memory: memory.memory_str[0] = new_stringref (from dialog.tlk append)

# After AppendFile append
# Subsection: 10=10 → Creates token StrRef10
# Memory: memory.memory_str[10] = new_stringref (from dialog.tlk append)
```

**[KEY](KEY-File-Format) Points**: See [How Token Creation Works](#how-token-creation-works) and [Memory System](#memory-system) for details. Tokens [ARE](GFF-File-Format#are-area) available for use in `[2DAList]`, `[GFFList]`, and `[CompileList]` sections.

### Processing Flow

1. Parse [TLKList] section
2. Load source [TLK files](TLK-File-Format) from `!SourceFile`/`!SourceFileF` e.g. `!SourceFile=append.tlk`
3. For each [StrRef](TLK-File-Format#string-references-strref) entry:
   - Parse: *[KEY](KEY-File-Format)* (ignored), *[value](GFF-File-Format#gff-data-types)* (source [index](2DA-File-Format#row-labels))
   - Load entry from source [file](GFF-File-Format) at *[value](GFF-File-Format#gff-data-types)* [index](2DA-File-Format#row-labels)
   - Append to dialog.tlk (gets new stringref)
   - Create token [StrRef](TLK-File-Format#string-references-strref){[value](GFF-File-Format#gff-data-types)} from *[value](GFF-File-Format#gff-data-types)* to store the new stringref
4. For each AppendFile entry:
   - Parse: Key (part after the word 'append' is ignored), *[value](GFF-File-Format#gff-data-types)* (filename) e.g. `AppendFile0=some_append_contents.tlk`
   - Parse subsection [filename] mappings
   - For each mapping:
     - Parse: *[KEY](KEY-File-Format)* (ignored), *[value](GFF-File-Format#gff-data-types)* (source [index](2DA-File-Format#row-labels))
     - Load entry from referenced [file](GFF-File-Format) at *[value](GFF-File-Format#gff-data-types)* [index](2DA-File-Format#row-labels)
     - Append to dialog.tlk (gets new stringref)
     - Create token [StrRef](TLK-File-Format#string-references-strref){[value](GFF-File-Format#gff-data-types)} from *[value](GFF-File-Format#gff-data-types)* to store the new stringref
5. Tokens [ARE](GFF-File-Format#are-area) now available for substitution in:
   - [2DAList] sections (2DAMEMORY#=[StrRef](TLK-File-Format#string-references-strref)#)
   - [GFFList] sections (FieldName=[StrRef](TLK-File-Format#string-references-strref)#)
   - [CompileList] scripts (#[StrRef](TLK-File-Format#string-references-strref)# tokens)

### Token Substitution Examples

**In [2DA files](2DA-File-Format)**: `name=StrRef0` (token gets replaced with actual stringref)

**In [GFF files](GFF-File-Format)**: `LocalizedName=StrRef0` (token gets replaced with actual stringref)

**In [NSS](NSS-File-Format) scripts**: `SendMessageToPC(GetFirstPC(), #StrRef0#);` (token gets replaced during compilation)

### Version History Notes

**TSLPatcher v1.2.8b6 (2006-10-03)**:

- Added optional `!SourceFile` and `!SourceFileF` keys to the `[TLKList]` section
- If present, these can be used to set an alternative name of the [TLK file](TLK-File-Format) to use
- If left out, default [values](GFF-File-Format#gff-data-types) [ARE](GFF-File-Format#are-area) `append.tlk` and `appendf.tlk` as before
- **Fixed bug**: Previously couldn't handle [TLK](TLK-File-Format) entries with [strings](GFF-File-Format#gff-data-types) longer than 4096 characters - now supports [strings](GFF-File-Format#gff-data-types) of any [size](GFF-File-Format#file-structure-overview)

**TSLPatcher v1.2.8b0 (2006-08-06)**:

- Changed processing order: [TLK](TLK-File-Format) Appending now happens before Install List
- This allows [ERF](ERF-File-Format)/MOD/RIM [files](GFF-File-Format) to be placed before [GFF](GFF-File-Format) and script compilation sections run

**TSLPatcher v1.2.8b8 (2006-12-02)**:

- Fixed bug that caused TSLPatcher to stop installation into games where the [`dialog.tlk`](TLK-File-Format) [file](GFF-File-Format) was write-protected

## Related Documentation

- [TSLPatcher's Official Readme](TSLPatcher's-Official-Readme.md) - General TSLPatcher information and ChangeEdit usage
- [TSLPatcher 2DAList Syntax](TSLPatcher-2DAList-Syntax.md) - How to modify [2DA](2DA-File-Format) files (can use [StrRef](TLK-File-Format#string-references-strref) tokens)
- [TSLPatcher GFFList Syntax](TSLPatcher-GFFList-Syntax.md) - How to modify [GFF](GFF-File-Format) files (can use [StrRef](TLK-File-Format#string-references-strref) tokens)
- [TSLPatcher SSFList Syntax](TSLPatcher-SSFList-Syntax.md) - How to modify soundset files (can use [StrRef](TLK-File-Format#string-references-strref) tokens)
- [TSLPatcher InstallList Syntax](TSLPatcher-InstallList-Syntax) - How to install files (includes script compilation)
- [Mod Creation Best Practices](Mod-Creation-Best-Practices.md) - Best practices for modding
- [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.) - PyKotor implementation details
