# TSLPatcher InstallList Syntax Documentation

This guide explains how to install [files](GFF-File-Format) using TSLPatcher syntax. For general TSLPatcher information, see [TSLPatcher's Official Readme](TSLPatcher's-Official-Readme). For HoloPatcher-specific information, see [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.).

**Implementation:** [`Libraries/PyKotor/src/pykotor/tslpatcher/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/tslpatcher/)

**Vendor References:**

- [`vendor/TSLPatcher/`](https://github.com/th3w1zard1/TSLPatcher) - Original Perl TSLPatcher by stoffe
- [`Tools/HolocronToolset/src/toolset/gui/dialogs/install_mod.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/dialogs/install_mod.py) - HoloPatcher [GUI](GFF-File-Format#gui-graphical-user-interface) implementation
- [`vendor/KotOR.js/src/manager/`](https://github.com/th3w1zard1/KotOR.js/tree/master/src/manager) - TypeScript mod management (different approach)

**See Also:**

- [TSLPatcher 2DAList Syntax](TSLPatcher-2DAList-Syntax) - Patching [2DA files](2DA-File-Format)
- [TSLPatcher GFFList Syntax](TSLPatcher-GFFList-Syntax) - Patching [GFF files](GFF-File-Format)
- [TSLPatcher TLKList Syntax](TSLPatcher-TLKList-Syntax) - Patching [TLK files](TLK-File-Format)
- [TSLPatcher SSFList Syntax](TSLPatcher-SSFList-Syntax) - Patching [SSF files](SSF-File-Format)
- [TSLPatcher HACKList Syntax](TSLPatcher-HACKList-Syntax) - Binary patching [NCS files](NCS-File-Format)
- [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.) - HoloPatcher extensions

## Overview

The `[InstallList]` section in TSLPatcher's changes.ini [file](GFF-File-Format) enables you to copy [files](GFF-File-Format) from your mod's `tslpatchdata` folder to their proper location in the game installation. This includes installing [files](GFF-File-Format) to folders (such as `Override`, `Modules`, `StreamVoice`, etc.) or directly into [ERF](ERF-File-Format)/RIM/MOD archive [files](GFF-File-Format). Unlike other patch lists, InstallList is designed for copying [files](GFF-File-Format) that haven't been modified by other sections.

**Important:** Do **not** add any [files](GFF-File-Format) that have been modified by any of the other sections ([GFFList](TSLPatcher-GFFList-Syntax), CompileList, [2DAList](TSLPatcher-2DAList-Syntax), etc.) to the InstallList, or the modified [files](GFF-File-Format) might be overwritten! The other sections already handle saving [files](GFF-File-Format) to their proper locations. The only exception to this is [ERF files](ERF-File-Format) which have had [files](GFF-File-Format) added to them by those sections. They must still be added to the InstallList to be put in their proper places.

## Table of Contents

- [Basic Structure](#basic-structure)
- [Processing Order](#processing-order)
- [Folder-Level Configuration](#folder-level-configuration)
- [File-Level Configuration](#file-level-configuration)
- [File Replacement Behavior](#file-replacement-behavior)
- [Installing to Folders](#installing-to-folders)
- [Installing to Archives](#installing-to-archives)
- [Renaming Files](#renaming-files)
- [Source Folder Configuration](#source-folder-configuration)
- [Override Type Handling](#override-type-handling)
- [Examples](#examples)
- [Special Cases and Edge Cases](#special-cases-and-edge-cases)
- [Troubleshooting](#troubleshooting)

## Basic [structure](GFF-File-Format#file-structure)

The InstallList uses a two-level hierarchical [structure](GFF-File-Format#file-structure):

```ini
[InstallList]
Folder0=Override
Folder1=Modules
Folder2=StreamVoice\AVO\_HuttHap

[Override]
File0=my_texture.tpc
File1=my_script.ncs
Replace0=existing_file.tpc

[Modules]
!SourceFolder=modules
File0=new_module.mod

[StreamVoice\AVO\_HuttHap]
File0=sound1.wav
File1=sound2.wav
```

### [structure](GFF-File-Format#file-structure) Explanation

1. **`[InstallList]` section**: Contains keys that map to folder destination names. Each key (like `Folder0`, `Folder1`, etc.) should reference a section with the same name as the value (the destination folder).

2. **Folder sections** (e.g., `[Override]`, `[Modules]`): Contain the list of [files](GFF-File-Format) to install to that folder, along with optional folder-level configuration.

3. **[file](GFF-File-Format) sections** (optional): Individual [files](GFF-File-Format) can have their own sections for per-[file](GFF-File-Format) configuration options.

## Processing Order

In **HoloPatcher**, the InstallList runs **first** in the patch execution order:

1. **[InstallList]** - [files](GFF-File-Format) [ARE](GFF-File-Format#are-area) installed first
2. **[TLKList]** - [TLK](TLK-File-Format) modifications
3. **[2DAList]** - [2DA file](2DA-File-Format) modifications
4. **[GFFList]** - [GFF file](GFF-File-Format) modifications
5. **[CompileList]** - Script compilation
6. **[HACKList]** - Binary hacking
7. **[SSFList]** - Sound set modifications

**Note:** In original TSLPatcher, InstallList executes **after** TLKList, but HoloPatcher changed this order to allow installing a whole [dialog.tlk](TLK-File-Format) [file](GFF-File-Format) before [TLK](TLK-File-Format) modifications [ARE](GFF-File-Format#are-area) applied. This priority change should not affect the output of mods.

## Folder-Level Configuration

Each folder section (e.g., `[Override]`) supports the following configuration keys:

| [KEY](KEY-File-Format) | [type](GFF-File-Format#data-types) | Default | Description |
|-----|------|---------|-------------|
| `!SourceFolder` | [string](GFF-File-Format#cexostring) | `.` (tslpatchdata folder) | Relative path from `mod_path` (typically the `tslpatchdata` folder, the parent directory of `changes.ini` or `namespaces.ini`) where [files](GFF-File-Format) should be sourced from. The default [value](GFF-File-Format#data-types) `.` refers to the `tslpatchdata` folder itself, not its parent directory. Path resolution: `mod_path / !SourceFolder / filename`. **HoloPatcher extension** - allows subfolder organization within tslpatchdata. |

### Folder Section [file](GFF-File-Format) List Keys

The folder section contains the list of [files](GFF-File-Format) to install. Each [file](GFF-File-Format) entry uses one of two syntaxes:

| [KEY](KEY-File-Format) [format](GFF-File-Format) | Replace Behavior | Description |
|------------|-----------------|-------------|
| `File#=filename.ext` | No replacement | Install the [file](GFF-File-Format) only if it doesn't already exist at the destination. If the [file](GFF-File-Format) exists, it will be skipped (warning logged). |
| `Replace#=filename.ext` | Replacement enabled | Install the [file](GFF-File-Format) and overwrite any existing [file](GFF-File-Format) at the destination. |

**Syntax Notes:**

- `#` is a sequential number starting from 0 (File0, File1, File2, ..., Replace0, Replace1, etc.)
- Numbers can be sequential, but gaps [ARE](GFF-File-Format#are-area) allowed (File0, File2, File5 is valid)
- Case-insensitive matching is used for the prefix ([file](GFF-File-Format), replace, [file](GFF-File-Format), Replace all work)
- The filename can include subdirectories if using `!SourceFolder`

**Examples:**

```ini
[Override]
File0=texture1.tpc
File1=texture2.tpc
Replace0=existing.tpc
Replace1=another_existing.tpc
File2=subfolder\texture3.tpc
```

## [file](GFF-File-Format)-Level Configuration

Each [file](GFF-File-Format) can optionally have its own section (e.g., `[my_texture.tpc]`) for per-[file](GFF-File-Format) configuration:

| [KEY](KEY-File-Format) | [type](GFF-File-Format#data-types) | Default | Description |
|-----|------|---------|-------------|
| `!SourceFile` | [string](GFF-File-Format#cexostring) | Same as filename in [file](GFF-File-Format)#/Replace# entry | Alternative source filename to load from tslpatchdata. The [file](GFF-File-Format) will be installed with the name specified in the [file](GFF-File-Format)#/Replace# entry (or `!SaveAs`/`!Filename` if specified). |
| `!SaveAs` | [string](GFF-File-Format#cexostring) | Same as `!SourceFile` | The final filename to save the [file](GFF-File-Format) as at the destination. Allows renaming during installation. |
| `!Filename` | [string](GFF-File-Format#cexostring) | Same as `!SaveAs` | Alias for `!SaveAs`. Both keys [ARE](GFF-File-Format#are-area) equivalent. |
| `!Destination` | [string](GFF-File-Format#cexostring) | Inherited from folder section name | Override the destination folder for this specific [file](GFF-File-Format). Can specify a different folder or archive path. |
| `!ReplaceFile` | 0/1 | Determined by [file](GFF-File-Format)#/Replace# prefix | Whether to replace existing [files](GFF-File-Format). Takes priority over the [file](GFF-File-Format)#/Replace# prefix syntax. `1` = replace, `0` = don't replace. |
| `!SourceFolder` | [string](GFF-File-Format#cexostring) | Inherited from folder section `!SourceFolder` | Override the source folder for this specific [file](GFF-File-Format). Relative path within tslpatchdata. |
| `!OverrideType` | `ignore`/`warn`/`rename` | `warn` (HoloPatcher) / `ignore` (TSLPatcher) | How to handle conflicts when installing to archives. See [Override Type Handling](#override-type-handling) section. |

### Example with [file](GFF-File-Format)-Level Configuration

```ini
[InstallList]
Folder0=Override

[Override]
File0=source_texture.tpc
File1=renamed_script.ncs

[source_texture.tpc]
!SourceFile=original_name.tpc
!SaveAs=final_texture.tpc
!Destination=textures

[renamed_script.ncs]
!Filename=custom_name.ncs
!ReplaceFile=1
```

## [file](GFF-File-Format) Replacement Behavior

InstallList has special behavior regarding [file](GFF-File-Format) replacement that differs from other patch lists:

### Skip If Not Replace

InstallList (and CompileList) use `skip_if_not_replace=True`, which means:

- If `!ReplaceFile=0` (or using `File#=` syntax) **and** the [file](GFF-File-Format) already exists at the destination:
  - The [file](GFF-File-Format) will be **skipped** (not installed)
  - A note is logged: `'filename.ext' already exists in the 'destination' folder. Skipping file...`
  - No error is raised - this is expected behavior

- If `!ReplaceFile=1` (or using `Replace#=` syntax) **and** the [file](GFF-File-Format) already exists:
  - The [file](GFF-File-Format) will be **replaced** (overwritten)
  - A note is logged: `Copying 'filename.ext' and replacing existing file in the 'destination' folder`

- If the [file](GFF-File-Format) does **not** exist:
  - The [file](GFF-File-Format) will be installed normally
  - A note is logged: `Copying 'filename.ext' and saving to the 'destination' folder`

### Replacement Priority

1. **`!ReplaceFile`** key (if present) takes **highest priority**
2. **`Replace#=`** prefix syntax (if `!ReplaceFile` not specified)
3. **`File#=`** prefix syntax (default, no replacement)

**Example:**

```ini
[Override]
Replace0=example.tpc

[example.tpc]
!ReplaceFile=0
```

In this case, even though `Replace0=` was used, `!ReplaceFile=0` takes priority, so the [file](GFF-File-Format) will NOT replace existing [files](GFF-File-Format).

## Installing to Folders

### Standard Game Folders

The most common use case is installing [files](GFF-File-Format) to standard game folders:

```ini
[InstallList]
Folder0=Override
Folder1=Modules
Folder2=StreamVoice
Folder3=StreamMusic
Folder4=StreamWaves

[Override]
File0=my_texture.tpc
File1=my_item.uti

[Modules]
File0=custom_module.mod

[StreamVoice]
File0=voice_line.wav

[StreamMusic]
File0=background_music.mp3

[StreamWaves]
File0=sound_effect.wav
```

### Subdirectories

You can install [files](GFF-File-Format) into subdirectories by specifying the relative path with backslashes:

```ini
[InstallList]
Folder0=StreamVoice\AVO\_HuttHap

[StreamVoice\AVO\_HuttHap]
File0=conversation1.wav
File1=conversation2.wav
```

**Important Notes:**

- Use **backslashes** (`\`) for path separators (TSLPatcher convention)
- HoloPatcher/PyKotor will normalize both forward slashes (`/`) and backslashes (`\`)
- If the specified folder path does not exist, it will be **automatically created**
- Folder creation happens recursively (parent folders [ARE](GFF-File-Format#are-area) created as needed)

### Game Root Folder

To install [files](GFF-File-Format) directly into the game root folder, use `.\` as the folder name:

```ini
[InstallList]
Folder0=.\

[.\]
File0=readme.txt
File1=config.ini
```

**Note:** In logs, `.\` is reported as the "Game" folder for clarity.

### Default Destination

You can set a default destination for all [files](GFF-File-Format) in InstallList using `!DefaultDestination`:

```ini
[InstallList]
!DefaultDestination=Override
Folder0=Override
Folder1=Modules

[Override]
File0=file1.tpc

[Modules]
File0=file2.mod
```

**Note:** `!DefaultDestination` is highly undocumented in TSLPatcher. In PyKotor/HoloPatcher, it is believed to take priority over folder section destinations, except when `!Destination` is explicitly set in a [file](GFF-File-Format) section.

## Installing to Archives

InstallList supports installing [files](GFF-File-Format) directly into [ERF](ERF-File-Format)/MOD/RIM archive [files](GFF-File-Format). This is done by specifying the archive [file](GFF-File-Format) path (relative to the game folder) as the destination.

### Archive [file](GFF-File-Format) Syntax

```ini
[InstallList]
Folder0=Modules\901myn.mod
Folder1=Modules\custom_module.rim

[Modules\901myn.mod]
File0=new_resource.uti
File1=new_texture.tpc
Replace0=existing_resource.uti

[Modules\custom_module.rim]
File0=another_resource.2da
```

### Archive Behavior

- If the archive **does not exist** at the specified path:
  - An error is logged: `The capsule 'Modules\901myn.mod' did not exist when attempting to copy 'filename.ext'. Skipping file...`
  - The patch is skipped (no error is raised, execution continues)

- If the archive **exists**:
  - The [file](GFF-File-Format) is added to the archive
  - If a resource with the same name already exists in the archive:
    - If `!ReplaceFile=1` or `Replace#=`: The existing resource is overwritten
    - If `!ReplaceFile=0` or `File#=`: The [file](GFF-File-Format) is skipped (see [File Replacement Behavior](#file-replacement-behavior))

- **Archive [types](GFF-File-Format#data-types) Supported:**
  - `.mod` (MOD/[ERF](ERF-File-Format) [format](GFF-File-Format))
  - `.erf` ([ERF](ERF-File-Format) [format](GFF-File-Format))
  - `.rim` (RIM [format](GFF-File-Format))
  - `.sav` (Save game [ERF](ERF-File-Format) [format](GFF-File-Format))

### Installing Modified Archives

If you've modified an archive using GFFList or CompileList (e.g., added resources to it), you **must** include that archive in InstallList to save it to its proper location:

```ini
[GFFList]
File0=Modules\901myn.mod

[Modules\901myn.mod]
; ... GFF modifications ...

[InstallList]
Folder0=Modules

[Modules]
Replace0=901myn.mod  ; Must include to save the modified archive
```

## Renaming [files](GFF-File-Format)

You can rename [files](GFF-File-Format) during installation using `!SaveAs` or `!Filename`:

```ini
[InstallList]
Folder0=Override

[Override]
File0=source_name.tpc

[source_name.tpc]
!SourceFile=original_filename.tpc
!SaveAs=final_filename.tpc
```

This will:

1. Load `original_filename.tpc` from tslpatchdata
2. Install it as `final_filename.tpc` to the Override folder

**Notes:**

- `!SaveAs` and `!Filename` [ARE](GFF-File-Format#are-area) equivalent - use either one
- If `!SourceFile` is not specified, the filename from the [file](GFF-File-Format)#/Replace# entry is used as the source
- The source [file](GFF-File-Format) must exist in the tslpatchdata folder (or `!SourceFolder` if specified)

## Source Folder Configuration

### Folder-Level Source Folder

You can specify a source folder for all [files](GFF-File-Format) in a folder section:

```ini
[InstallList]
Folder0=Override

[Override]
!SourceFolder=textures
File0=texture1.tpc
File1=texture2.tpc
```

This will look for [files](GFF-File-Format) in `tslpatchdata\textures\` instead of `tslpatchdata\`.

### [file](GFF-File-Format)-Level Source Folder

You can override the source folder for individual [files](GFF-File-Format):

```ini
[InstallList]
Folder0=Override

[Override]
!SourceFolder=default_folder
File0=file1.tpc
File1=file2.tpc

[file1.tpc]
!SourceFolder=custom_folder
```

In this example:

- `file1.tpc` is loaded from `tslpatchdata\custom_folder\`
- `file2.tpc` is loaded from `tslpatchdata\default_folder\`

### Source Folder Notes

- `!SourceFolder` is a **HoloPatcher extension** - original TSLPatcher may not support this feature
- Paths [ARE](GFF-File-Format#are-area) relative to the `tslpatchdata` folder
- Use `.` (period) to reference the root tslpatchdata folder explicitly
- Supports subdirectory paths: `!SourceFolder=subfolder\deeper\folder`
- Backslashes and forward slashes [ARE](GFF-File-Format#are-area) both normalized

## Override [type](GFF-File-Format#data-types) Handling

When installing [files](GFF-File-Format) to archives ([ERF](ERF-File-Format)/MOD/RIM), there's a potential conflict: a [file](GFF-File-Format) might already exist in the Override folder with the same name. The `!OverrideType` setting controls how this conflict is handled:

| [value](GFF-File-Format#data-types) | Behavior | Description |
|-------|----------|-------------|
| `ignore` | No action | Do nothing - don't even check for conflicts. This is the TSLPatcher default. |
| `warn` | Log warning | Check for conflicts and log a warning if found, but continue with installation. This is the HoloPatcher default. |
| `rename` | Rename override [file](GFF-File-Format) | If a conflicting [file](GFF-File-Format) exists in Override, rename it with an `old_` prefix (e.g., `old_filename.ext`) and log a warning. |

**Example:**

```ini
[Modules\901myn.mod]
File0=resource.uti
!OverrideType=warn
```

**Why This Matters:**

The game's resource loading system checks folders in this order:

1. Override folder (highest priority)
2. Module archives (.mod [files](GFF-File-Format))
3. RIM [files](GFF-File-Format)
4. Other archives

If a [file](GFF-File-Format) exists in both Override and an archive, the Override version takes precedence. The `!OverrideType` setting helps manage this shadowing behavior.

## Examples

### Example 1: Basic Installation to Override

```ini
[InstallList]
Folder0=Override

[Override]
File0=my_texture.tpc
File1=my_item.uti
File2=my_script.ncs
Replace0=existing_file.tpc
```

### Example 2: Installing to Multiple Folders with Source Folders

```ini
[InstallList]
Folder0=Override
Folder1=StreamVoice\AVO\_HuttHap
Folder2=Modules

[Override]
!SourceFolder=override_files
File0=texture1.tpc
File1=texture2.tpc

[StreamVoice\AVO\_HuttHap]
!SourceFolder=voice_files
File0=conv1.wav
File1=conv2.wav

[Modules]
!SourceFolder=modules
File0=custom.mod
```

### Example 3: Renaming [files](GFF-File-Format) During Installation

```ini
[InstallList]
Folder0=Override

[Override]
File0=renamed_texture.tpc
File1=renamed_item.uti

[renamed_texture.tpc]
!SourceFile=original_texture.tpc
!SaveAs=final_texture_name.tpc

[renamed_item.uti]
!SourceFile=source_item.uti
!Filename=custom_item_name.uti
```

### Example 4: Installing to Archives

```ini
[InstallList]
Folder0=Modules\901myn.mod
Folder1=Modules\custom.rim

[Modules\901myn.mod]
File0=new_creature.utc
File1=new_dialog.dlg
Replace0=existing_item.uti
!OverrideType=warn

[Modules\custom.rim]
File0=custom_2da.2da
!ReplaceFile=1
```

### Example 5: Complex Example with All Features

```ini
[InstallList]
!DefaultDestination=Override
Folder0=Override
Folder1=Modules
Folder2=Modules\901myn.mod
Folder3=StreamVoice\AVO\_HuttHap

[Override]
!SourceFolder=textures
File0=texture1.tpc
File1=texture2.tpc
Replace0=existing_texture.tpc

[texture1.tpc]
!SourceFile=original_name.tpc
!SaveAs=final_texture.tpc
!Destination=textures
!OverrideType=rename

[Modules]
!SourceFolder=modules
Replace0=modified_module.mod

[Modules\901myn.mod]
File0=new_resource.uti
File1=new_texture.tpc
Replace0=modified_resource.utc
!SourceFolder=archive_resources

[new_resource.uti]
!Filename=custom_name.uti
!ReplaceFile=1

[StreamVoice\AVO\_HuttHap]
!SourceFolder=voice
File0=line1.wav
File1=line2.wav
```

## Special Cases and [edge](BWM-File-Format#edges) Cases

### Empty InstallList

An empty `[InstallList]` section is valid and will be skipped:

```ini
[InstallList]
```

No [files](GFF-File-Format) will be installed, and a note will be logged: `[InstallList] section missing from ini.` (if the section doesn't exist) or no error if the section exists but is empty.

### Missing Folder Sections

If a folder [KEY](KEY-File-Format) in `[InstallList]` references a section that doesn't exist, a `KeyError` is raised:

```ini
[InstallList]
Folder0=NonExistentFolder
; Error: Section [NonExistentFolder] not found
```

### Missing Source [files](GFF-File-Format)

If a source [file](GFF-File-Format) specified in a [file](GFF-File-Format)#/Replace# entry doesn't exist in tslpatchdata (or the specified `!SourceFolder`), an error is logged:

```
Could not locate resource to copy: 'missing_file.tpc'
```

The patcher will continue with the next [file](GFF-File-Format).

### Automatic Folder Creation

Folders [ARE](GFF-File-Format#are-area) automatically created if they don't exist:

```ini
[InstallList]
Folder0=NewFolder\SubFolder\DeepFolder

[NewFolder\SubFolder\DeepFolder]
File0=file.tpc
```

All parent folders (`NewFolder`, `SubFolder`, `DeepFolder`) will be created automatically.

### Archive [file](GFF-File-Format) Handling

- **Archive doesn't exist**: Error logged, patch skipped
- **Archive exists but is read-only**: Permission error logged, patch skipped
- **Archive exists, [file](GFF-File-Format) already in archive**: See [File Replacement Behavior](#file-replacement-behavior)
- **Archive exists, [file](GFF-File-Format) doesn't exist in archive**: [file](GFF-File-Format) is added normally

### Case Sensitivity

- Folder and [file](GFF-File-Format) keys [ARE](GFF-File-Format#are-area) **case-insensitive**: `File0`, `file0`, `FILE0` all work
- `Replace#` prefix detection is **case-insensitive**: `Replace0`, `replace0`, `REPLACE0` all work
- [file](GFF-File-Format) paths on Windows [ARE](GFF-File-Format#are-area) case-insensitive, but PyKotor uses `CaseAwarePath` to preserve case when possible

### Path Separators

- TSLPatcher convention: Use backslashes (`\`) for Windows paths
- PyKotor/HoloPatcher: Normalizes both backslashes (`\`) and forward slashes (`/`)
- Archive paths: Use backslashes: `Modules\901myn.mod`

### nwscript.nss Automatic Installation

If the mod contains `nwscript.nss` in the tslpatchdata folder and there [ARE](GFF-File-Format#are-area) scripts to compile (`[CompileList]`), HoloPatcher will automatically append an InstallFile entry to install `nwscript.nss` to the Override folder. This is required for some versions of nwnnsscomp.exe that expect nwscript.nss to be in Override rather than tslpatchdata.

This happens during the `_prepare_compilelist` phase before the main patch loop runs.

## Troubleshooting

### [file](GFF-File-Format) Not Installing

**Problem:** [file](GFF-File-Format) listed in InstallList but not being installed.

**Possible Causes:**

1. [file](GFF-File-Format) already exists and `Replace#=` or `!ReplaceFile=1` not set
   - **Solution:** Check logs for "already exists... Skipping [file](GFF-File-Format)" message
   - **Fix:** Use `Replace#=` or set `!ReplaceFile=1`

2. Source [file](GFF-File-Format) doesn't exist in tslpatchdata
   - **Solution:** Check logs for "Could not locate resource" error
   - **Fix:** Ensure [file](GFF-File-Format) exists in tslpatchdata (or specified `!SourceFolder`)

3. Archive doesn't exist
   - **Solution:** Check logs for "capsule did not exist" error
   - **Fix:** Create the archive first or ensure the path is correct

4. Permission errors
   - **Solution:** Check logs for permission/access denied errors
   - **Fix:** Run with appropriate permissions, check [file](GFF-File-Format)/folder permissions

### Wrong Destination

**Problem:** [file](GFF-File-Format) installing to wrong location.

**Possible Causes:**

1. `!Destination` override in [file](GFF-File-Format) section
2. `!DefaultDestination` set incorrectly
3. Folder section name typo

**Solution:** Check [file](GFF-File-Format) section for `!Destination`, verify folder section names match destination paths.

### Archive Not Updating

**Problem:** [file](GFF-File-Format) not appearing in archive after installation.

**Possible Causes:**

1. Archive doesn't exist (error logged)
2. [file](GFF-File-Format) already exists and replacement not enabled
3. Archive is read-only or locked

**Solution:** Check logs for errors, ensure `Replace#=` or `!ReplaceFile=1` is set, verify archive permissions.

### [files](GFF-File-Format) Being Skipped Unexpectedly

**Problem:** [files](GFF-File-Format) that should install [ARE](GFF-File-Format#are-area) being skipped.

**Possible Causes:**

1. `File#=` syntax used with existing files (expected behavior - use `Replace#=`)
2. `!ReplaceFile=0` explicitly set
3. [file](GFF-File-Format) already exists in archive without replacement enabled

**Solution:** Review [File Replacement Behavior](#file-replacement-behavior) section, use `Replace#=` or `!ReplaceFile=1` to enable replacement.

## Reference: Complete Syntax Summary

### Top-Level [InstallList] Section

```ini
[InstallList]
!DefaultDestination=<folder_path>  ; Optional: default destination for all files
Folder#=<destination_path>          ; Required: map to folder section
```

### Folder Section (e.g., [Override])

```ini
[<destination_path>]
!SourceFolder=<relative_path>        ; Optional: source folder within tslpatchdata
File#=<filename.ext>                ; Install file (skip if exists)
Replace#=<filename.ext>             ; Install file (replace if exists)
```

### [file](GFF-File-Format) Section (e.g., [filename.ext])

```ini
[<filename.ext>]
!SourceFile=<source_filename.ext>  ; Optional: alternative source file
!SaveAs=<final_filename.ext>       ; Optional: rename during installation
!Filename=<final_filename.ext>      ; Optional: alias for !SaveAs
!Destination=<destination_path>     ; Optional: override folder destination
!ReplaceFile=<0|1>                  ; Optional: override replacement behavior
!SourceFolder=<relative_path>      ; Optional: override source folder
!OverrideType=<ignore|warn|rename> ; Optional: conflict resolution mode
```

## Additional Notes

- All paths in TSLPatcher use backslashes (`\`) by convention, but HoloPatcher/PyKotor normalizes both slashes
- Folder paths [ARE](GFF-File-Format#are-area) created automatically if they don't exist
- Archive paths must exist before [files](GFF-File-Format) can be installed to them
- InstallList runs before other patch lists in HoloPatcher (but after TLKList in original TSLPatcher)
- [files](GFF-File-Format) [ARE](GFF-File-Format#are-area) backed up before installation (if they exist)
- Uninstall scripts [ARE](GFF-File-Format#are-area) generated automatically in the backup folder

## See Also

- [TSLPatcher's Official Readme](TSLPatcher's-Official-Readme.md) - Original TSLPatcher documentation
- [Explanations on HoloPatcher Internal Logic](Explanations-on-HoloPatcher-Internal-Logic.md) - Internal implementation details
- [TSLPatcher GFFList Syntax](TSLPatcher-GFFList-Syntax.md) - Documentation for [GFF](GFF-File-Format) modifications
- [Mod Creation Best Practices](Mod-Creation-Best-Practices.md) - Best practices for mod development
