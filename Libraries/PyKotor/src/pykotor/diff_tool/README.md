# PyKotor Diff Tool

This directory contains the core diff functionality for PyKotor CLI's `diff` command.

## Path Types and Combinations

The `pykotorcli diff` command automatically detects path types and handles **ALL combinations** of different path types. Path1 and path2 can be **any** of the supported types below - they do not need to be the same type.

### Supported Path Types

#### 1. **File Paths**

Individual files of any supported format:

- **GFF files**: `.utc`, `.utd`, `.utp`, `.uti`, `.utm`, `.uts`, `.utt`, `.utw`, `.ute`, `.are`, `.ifo`, `.git`, `.dlg`, `.gui`, etc.
- **TalkTable files**: `.tlk`
- **2DA files**: `.2da`
- **Text files**: `.txt`, `.nss` (scripts), etc.
- **Binary files**: Any unsupported format (compared by hash)

#### 2. **Folder/Directory Paths**

Any directory containing KOTOR files:

- **Override folders**: `C:\Games\KOTOR\Override`
- **Module folders**: `C:\Games\KOTOR\Modules`
- **Custom mod folders**: Any directory with KOTOR files
- **Working directories**: Development folders with source files

#### 3. **Installation Paths**

Complete KOTOR game installations:

- **Full game paths**: `C:\Games\KOTOR`, `C:\Games\TSL`
- **Must contain `chitin.key`** in the root directory
- **Supports all KOTOR 1 and TSL installations**

#### 4. **Bioware Archive Paths**

Various archive formats used by KOTOR:

##### **Composite Modules**

Complete module packages with multiple files:

```bash
# Example: tat_m17ac module consists of:
tat_m17ac.rim      # Main module data
tat_m17ac_s.rim    # Supplementary data (sounds/models)
tat_m17ac_dlg.erf  # Dialog data (TSL only)

# Usage: specify any one file, diff detects the composite
pykotorcli diff tat_m17ac.rim another_module.rim
```

##### **Single-File Modules**

Standalone module files:

```bash
# .mod files (community overrides, highest priority)
pykotorcli diff custom_module.mod vanilla_module.mod

# .rim files when _s.rim/_dlg.erf don't exist
pykotorcli diff standalone.rim another.rim

# .sav files (savegames)
pykotorcli diff savegame1.sav savegame2.sav
```

##### **Generic Archives**

Non-module archives treated as generic containers:

```bash
# .erf files (patches, generic data)
pykotorcli diff patch.erf another_patch.erf

# .bif files (from chitin.key, compared as archives)
pykotorcli diff data.bif modified_data.bif
```

**Priority Order for Archives:**

1. `.mod` files (highest - community override)
2. `.rim` + `_s.rim` + `_dlg.erf` (composite modules)
3. Single `.rim`, `.erf`, `.sav` files
4. `.bif` files (lowest priority)

### Path1 vs Path2 Combinations

The diff command supports **ALL possible combinations** of the above path types. Here are examples of how different path types work together:

#### File vs File

```bash
pykotorcli diff character1.utc character2.utc
pykotorcli diff dialog1.dlg dialog2.dlg
pykotorcli diff script1.nss script2.nss
```

#### File vs Folder

```bash
# Compare a single file against all files in a folder
pykotorcli diff character.utc "Override/"
# Finds character.utc in Override/ and compares it
```

#### File vs Installation

```bash
# Compare a file against the entire game installation
pykotorcli diff custom_character.utc "C:\Games\KOTOR"
# Searches entire installation for matching resources
```

#### File vs Archive

```bash
# Compare a file against contents of an archive
pykotorcli diff character.utc module.rim
pykotorcli diff dialog.dlg savegame.sav
```

#### Folder vs Folder

```bash
pykotorcli diff "mod_folder_1/" "mod_folder_2/"
pykotorcli diff "Override/" "Backup_Override/"
```

#### Folder vs Installation

```bash
# Compare a mod folder against a full installation
pykotorcli diff "My_Mod_Override/" "C:\Games\KOTOR"
```

#### Folder vs Archive

```bash
# Compare folder contents against archive contents
pykotorcli diff "Override/" module.rim
pykotorcli diff "source_files/" patch.erf
```

#### Installation vs Installation

```bash
pykotorcli diff "C:\Games\KOTOR" "C:\Games\KOTOR_Modded"
pykotorcli diff "vanilla_kotor/" "modded_kotor/"
```

#### Installation vs Archive

```bash
# Compare entire installation against a module
pykotorcli diff "C:\Games\KOTOR" tat_m17ac.rim
```

#### Archive vs Archive

```bash
pykotorcli diff module1.rim module2.rim
pykotorcli diff savegame1.sav savegame2.sav
pykotorcli diff patch1.erf patch2.erf
```

#### Advanced Examples

```bash
# Mix any types - these all work:
pykotorcli diff character.utc module.rim           # File vs Archive
pykotorcli diff "Override/" "C:\Games\KOTOR"      # Folder vs Installation
pykotorcli diff tat_m17ac.rim "Modules/"          # Archive vs Folder
pykotorcli diff savegame.sav character.utc        # Archive vs File
pykotorcli diff "C:\Games\KOTOR" patch.erf        # Installation vs Archive

# Cross-game comparisons work too:
pykotorcli diff "C:\Games\KOTOR" "C:\Games\TSL"    # K1 vs TSL installations

```

## How Path Resolution Works

When you specify path1 and path2, the system:

1. **Detects the type** of each path automatically
2. **Collects resources** from each path according to its type:
   - **Files**: Single resource
   - **Folders**: All files in directory tree
   - **Installations**: All resources via KOTOR's resolution order
   - **Archives**: All resources within the archive
3. **Matches resources** between the two paths by filename/resref
4. **Compares matching resources** using appropriate comparison methods

## Resource Resolution Order (for Installations)

When comparing installations, resources are resolved in KOTOR's standard priority order:

1. **Override folder** (highest priority)
2. **Modules** (.mod files)
3. **Modules (.rim + _s.rim + _dlg.erf composites)**
4. **Chitin BIFs** (lowest priority)

## Comparison Methods

- **Structured comparison** for GFF, 2DA, TLK files using `ComparableMixin`
- **Text comparison** using `difflib` for text-based files
- **Hash comparison** for binary/unsupported files
- **Container comparison** for archives (compares internal resources)

## Output Formats

- **Unified diff** (default, git-compatible)
- **Context diff**
- **Side-by-side diff** (planned)

The output is designed to be machine-readable for automation and scripting.
