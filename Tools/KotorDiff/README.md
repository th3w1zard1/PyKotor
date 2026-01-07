# KotorDiff

- ![Screenshot 1](https://deadlystream.com/downloads/screens/monthly_2023_09/Code_B7XMgAobTn.thumb.png.031c5f751b0fc2255f2de5300d42af7f.png)
- ![Screenshot 2](https://deadlystream.com/downloads/screens/monthly_2023_09/Code_sUtiSdkEsB.thumb.png.bff397075b009ba2140696ed3c38deed.png)

## About This Tool

### **A powerful CLI to easily compare KOTOR file formats, installations, and modules.**

KotorDiff is a comprehensive command-line tool built on PyKotor that allows you to compare KOTOR files, directories, modules, and entire installations with detailed, structured unified diff output. Whether you're debugging TSLPatcher issues, validating mod installations, or analyzing differences between game versions, KotorDiff provides the precision you need.

The `pykotorcli diff` command produces output identical to `git diff`, making it machine-readable for other tools and scripts.

### **Why KotorDiff?**

It is (or should be) common knowledge that Kotor Tool is not safe to use for anything besides extraction. But have you ever wondered *why* that is?

Let's take a look at a **.utc** file extracted directly from the BIFs (the OG vanilla **p_bastilla.utc**). Extract it with **KTool** and name it **p_bastilla_ktool.utc**. Now open the same file in ktool's UTC character editor, change a single field (literally anything, hp, strength, whatever you fancy), and save it as **p_bastilla_ktool_edited.utc**.

KotorDiff's output reveals the shocking truth - changing a single field results in dozens of unintended modifications, corrupted data, and broken references. This tool saved the day by showing exactly what KTool did wrong.

## Features

- **Git Diff Compatible**: Produces unified diff output identical to `git diff`, making it machine-readable for other tools
- **Multiple Comparison Types**: Compare files, directories, modules, or entire installations
- **Advanced Module Resolution**: Intelligent handling of composite modules (`.rim` + `_s.rim` + `_dlg.erf`)
- **Flexible Filtering**: Target specific modules or resources during installation-wide comparisons
- **Detailed Logging**: Comprehensive resource resolution tracking with verbose search information
- **Format-Aware Diffing**: Structured comparison of GFF, TLK, and capsule files using ComparableMixin
- **TSLPatcher Integration**: Generate `changes.ini` and `tslpatchdata` for mod creation
- **Multiple Output Formats**: Unified (default), context, and side-by-side diff formats
- **Comprehensive Testing**: 27 test cases covering all path types and comparison scenarios

## Installation

The diff functionality is now integrated into PyKotor CLI:

```bash
# Install PyKotor
pip install pykotor

# Run the diff command
pykotorcli diff <path1> <path2> [options]
```

## Usage

### Basic Syntax

```bash
# Compare two paths (files, folders, installations, or archives)
pykotorcli diff <path1> <path2> [options]

# Examples
pykotorcli diff path/to/file1.utc path/to/file2.utc
pykotorcli diff path/to/folder1 path/to/folder2
pykotorcli diff /path/to/kotor1 /path/to/kotor2
pykotorcli diff module.rim another_module.rim
```

### Comparison Types

The `pykotorcli diff` command automatically detects path types and handles **ALL combinations** of different path types. Path1 and path2 can be **any** of the supported types below - they do not need to be the same type.

#### Supported Path Types

##### 1. **File Paths**
Individual files of any supported format:
- **GFF files**: `.utc`, `.utd`, `.utp`, `.uti`, `.utm`, `.uts`, `.utt`, `.utw`, `.ute`, `.are`, `.ifo`, `.git`, `.dlg`, `.gui`, etc.
- **TalkTable files**: `.tlk`
- **2DA files**: `.2da`
- **Text files**: `.txt`, `.nss` (scripts), etc.
- **Binary files**: Any unsupported format (compared by hash)

##### 2. **Folder/Directory Paths**
Any directory containing KOTOR files:
- **Override folders**: `C:\Games\KOTOR\Override`
- **Module folders**: `C:\Games\KOTOR\Modules`
- **Custom mod folders**: Any directory with KOTOR files
- **Working directories**: Development folders with source files

##### 3. **Installation Paths**
Complete KOTOR game installations:
- **Full game paths**: `C:\Games\KOTOR`, `C:\Games\TSL`
- **Must contain `chitin.key`** in the root directory
- **Supports all KOTOR 1 and TSL installations**

##### 4. **Bioware Archive Paths**
Various archive formats used by KOTOR:

###### **Composite Modules**
Complete module packages with multiple files:
```bash
# Example: tat_m17ac module consists of:
tat_m17ac.rim      # Main module data
tat_m17ac_s.rim    # Supplementary data (sounds/models)
tat_m17ac_dlg.erf  # Dialog data (TSL only)

# Usage: specify any one file, diff detects the composite
pykotorcli diff tat_m17ac.rim another_module.rim
```

###### **Single-File Modules**
Standalone module files:
```bash
# .mod files (community overrides, highest priority)
pykotorcli diff custom_module.mod vanilla_module.mod

# .rim files when _s.rim/_dlg.erf don't exist
pykotorcli diff standalone.rim another.rim

# .sav files (savegames)
pykotorcli diff savegame1.sav savegame2.sav
```

###### **Generic Archives**
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

#### Path1 vs Path2 Combinations

The diff command supports **ALL possible combinations** of the above path types. Here are examples of how different path types work together:

##### File vs File
```bash
pykotorcli diff character1.utc character2.utc
pykotorcli diff dialog1.dlg dialog2.dlg
pykotorcli diff script1.nss script2.nss
```

##### File vs Folder
```bash
# Compare a single file against all files in a folder
pykotorcli diff character.utc "Override/"
# Finds character.utc in Override/ and compares it
```

##### File vs Installation
```bash
# Compare a file against the entire game installation
pykotorcli diff custom_character.utc "C:\Games\KOTOR"
# Searches entire installation for matching resources
```

##### File vs Archive
```bash
# Compare a file against contents of an archive
pykotorcli diff character.utc module.rim
pykotorcli diff dialog.dlg savegame.sav
```

##### Folder vs Folder
```bash
pykotorcli diff "mod_folder_1/" "mod_folder_2/"
pykotorcli diff "Override/" "Backup_Override/"
```

##### Folder vs Installation
```bash
# Compare a mod folder against a full installation
pykotorcli diff "My_Mod_Override/" "C:\Games\KOTOR"
```

##### Folder vs Archive
```bash
# Compare folder contents against archive contents
pykotorcli diff "Override/" module.rim
pykotorcli diff "source_files/" patch.erf
```

##### Installation vs Installation
```bash
pykotorcli diff "C:\Games\KOTOR" "C:\Games\KOTOR_Modded"
pykotorcli diff "vanilla_kotor/" "modded_kotor/"
```

##### Installation vs Archive
```bash
# Compare entire installation against a module
pykotorcli diff "C:\Games\KOTOR" tat_m17ac.rim
```

##### Archive vs Archive
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

### Output Formats

Choose from multiple diff output formats (default: unified):

```bash
# Unified diff (git-style, default)
pykotorcli diff file1.utc file2.utc

# Context diff
pykotorcli diff file1.utc file2.utc --format context

# Side-by-side (not fully implemented)
pykotorcli diff file1.utc file2.utc --format side_by_side
```

### TSLPatcher Integration

Generate TSLPatcher `changes.ini` and `tslpatchdata` folder:

```bash
# Generate TSLPatcher files for installation differences
pykotorcli diff "vanilla_install" "modded_install" --generate-ini
```

### Output Control

```bash
# Write diff to file
pykotorcli diff file1.utc file2.utc --output diff.patch

# Show verbose debug information
pykotorcli diff file1.utc file2.utc --verbose

# Show debug information
pykotorcli diff file1.utc file2.utc --debug
```

## Module Resolution System

KotorDiff includes an advanced module resolution system that understands KOTOR's composite module structure:

### Automatic Module Detection

When you specify a module name without extension (e.g., `tat_m17ac`), KotorDiff automatically:

1. **Searches for related files**: `.mod`, `.rim`, `_s.rim`, `_dlg.erf`
2. **Applies priority order**: `.mod` > `.rim` + `_s.rim` + `_dlg.erf`
3. **Uses composite loading**: Combines multiple files when appropriate
4. **Provides detailed logging**: Shows which files were found and used

### Module Priority System

```bash
1. .mod files (highest priority - community override)
2. .rim files (main module data)
3. _s.rim files (supplementary data)
4. _dlg.erf files (K2 dialog data)
```

### Resource Resolution Logging

With verbose logging enabled, you'll see detailed information about where each resource was found:

```bash
Constraining search to module root 'tat_m17ac'
Installation-wide search for 'module.ifo':
  Checking each location:
    1. Custom folders -> not found
    2. Override folders -> not found
    3. Custom modules -> FOUND at Modules\tat_m17ac.rim -> SELECTED
    4. Module capsules -> (filtered to tat_m17ac only)
    5. Chitin BIFs -> not found
```

## Supported File Formats

### Fully Supported (Structured Comparison)

- **GFF Files**: UTC, UTD, UTP, UTI, UTM, UTS, UTT, UTW, UTE, ARE, IFO, GIT, DLG, GUI, etc.
- **TalkTable Files**: TLK (with string reference resolution)
- **Capsule Files**: ERF, MOD, RIM, SAV (with internal resource comparison)
- **Layout Files**: LYT
- **Path Files**: PTH
- **Vision Files**: VIS
- **2DA Files**: Tabular data comparison

### Hash-Based Comparison

- **Script Files**: NCS, NSS
- **Texture Files**: TPC, TGA
- **Model Files**: MDL, MDX
- **Audio Files**: WAV, MP3
- **Other**: Any unsupported format falls back to SHA256 hash comparison

## Output Format

The `pykotorcli diff` command produces unified diff output identical to `git diff`, making it machine-readable for scripts and automation tools. The output format is:

1. **Field difference descriptions**: Shows which fields differ with their paths
2. **Unified diff blocks**: Standard `---`, `+++`, `@@` format showing exact changes
3. **Final summary**: Either `MATCHES` or `DOES NOT MATCH` indicating overall result

Exit codes follow standard conventions:
- `0`: Files/paths are identical
- `1`: Files/paths differ
- `2`: Error occurred

## Output Examples

### GFF File Differences

```bash
Field 'Int16' is different at 'character.utc\HitPoints':
--- (old)HitPoints
+++ (new)HitPoints
@@ -1 +1 @@
-18
+24

Field 'String' is different at 'character.utc\Tag':
--- (old)Tag
+++ (new)Tag
@@ -1 +1 @@
-OldTag
+NewTag
'C:\path\to\character.utc' DOES NOT MATCH 'C:\path\to\modified_character.utc'
```

### Module Comparison

```bash
Using composite module loading for tat_m17ac.rim
Combined module capsules for tat_m17ac.rim: ['tat_m17ac.rim', 'tat_m17ac_s.rim']

Processing resource: module.ifo
Constraining search to module root 'tat_m17ac'
Found 'module.ifo' at: Modules\tat_m17ac.rim

Processing resource: m17ac.are
Found 'm17ac.are' at: Modules\tat_m17ac.rim
```

### Installation Comparison with Filtering

```bash
Using filter: tat_m17ac
Comparing installations with 1 filter(s) active
Processing only resources matching: tat_m17ac

Found 15 resources in tat_m17ac module
Compared 15/15 resources
Installation comparison complete
```

## File Formats Handled

- TalkTable files (TLK)
- Any GFF file (DLG, UTC, GUI, UTP, UTD, etc.)
- Any capsule (ERF, MOD, RIM, SAV, etc.)

## Exit Codes

PyKotor CLI diff uses standard exit codes for integration with scripts and automation:

- **0**: Files/paths match perfectly (`MATCHES`)
- **1**: Files/paths differ (`DOES NOT MATCH`) or system error
- **2**: Error occurred during comparison

Legacy KotorDiff uses different exit codes:

- **0**: Files/installations match perfectly
- **1**: System error (file not found, permission denied, etc.)
- **2**: Files/installations differ
- **3**: Known application error (invalid arguments, unsupported format, etc.)

## Integration Examples

### Batch Script Integration

```batch
@echo off
kotordiff --path1 "original" --path2 "modified" --output-mode quiet
if %ERRORLEVEL% == 0 (
    echo Files are identical
) else if %ERRORLEVEL% == 2 (
    echo Files differ - check log for details
) else (
    echo Error occurred
)
```

### **PyKotor CLI Diff Command (Recommended):**

The `pykotorcli diff` command provides unified diff output identical to `git diff`, making it machine-readable for scripts and other tools.

```bash
pykotorcli diff <path1> <path2> [--format FORMAT] [--generate-ini] [--verbose] [--debug] [--quiet] [--no-color]
```

- `path1`: First path (file, folder, installation, or bioware archive)
- `path2`: Second path (file, folder, installation, or bioware archive)
- `--format`: Diff output format: `unified` (default), `context`, or `side_by_side`
- `--generate-ini`: Generate TSLPatcher changes.ini and tslpatchdata folder (installation comparisons only)
- `--verbose`: Increase output verbosity
- `--debug`: Enable debug logging
- `--quiet`: Disable all logging except errors
- `--no-color`: Disable colored output

### **Legacy KotorDiff Options:**

```bash
kotordiff [--path1 PATH1] [--path2 PATH2] [--output-log FILE] [--ignore-rims] [--ignore-tlk] [--ignore-lips] [--compare-hashes] [--logging] [--use-profiler]
```

- `--path1`: Path to the first K1/TSL install, file, or directory to diff
- `--path2`: Path to the second K1/TSL install, file, or directory to diff
- `--output-log`: Filepath of the desired output logfile
- `--ignore-rims`: Whether to compare RIMS (default is False)
- `--ignore-tlk`: Whether to compare TLK files (default is False)
- `--ignore-lips`: Whether to compare LIPS (default is False)
- `--compare-hashes`: Compare hashes of any unsupported file/resource type (default is True)
- `--logging`: Whether to log the results to a file or not (default is True)
- `--use-profiler`: Use cProfile to find where most of the execution time is taking place in source code

### PowerShell Integration

```powershell
$result = & kotordiff --path1 "install1" --path2 "install2" --filter "tat_m17ac"
switch ($LASTEXITCODE) {
    0 { Write-Host "Modules are identical" -ForegroundColor Green }
    2 { Write-Host "Modules differ" -ForegroundColor Yellow }
    default { Write-Host "Error occurred" -ForegroundColor Red }
}
```

## Performance Tips

1. **Use filtering** for large installation comparisons to focus on specific areas
2. **Enable quiet mode** (`--output-mode quiet`) for automated scripts
3. **Ignore unnecessary file types** using `--ignore-*` flags
4. **Use specific module names** instead of wildcards when possible

## Troubleshooting

### Common Issues

**Q: "Invalid path" error when specifying module names**
A: Ensure the module files exist in the specified directory. KotorDiff looks for `.mod`, `.rim`, `_s.rim`, and `_dlg.erf` files.

**Q: Too much output when comparing installations**
A: Use `--filter` to target specific modules or `--output-mode diff_only` to see only differences.

**Q: Module resolution seems wrong**
A: Check the verbose logs to see which files were found and prioritized. The tool follows KOTOR's standard module loading order.

**Q: Antivirus flagging the executable**
A: This is a false positive common with PyInstaller-compiled executables. You can run from source using `uv run src/kotordiff/__main__.py` instead.

**TLDR:** PyInstaller is an amazing tool, but antiviruses may flag it. This is not the fault of PyInstaller or my tool, but rather the fault of how some scummy users have chosen to use PyInstaller in the past. Please report any false positives you encounter to your antivirus's website, as reports not only improve the accuracy of everybody's AV experience overall but also indirectly support the [PyInstaller project](https://github.com/pyinstaller/pyinstaller).

### Debug Mode

For troubleshooting, enable maximum verbosity:

```bash
kotordiff --path1 file1 --path2 file2 --log-level debug --output-mode full
```

**Q: Is there a GUI version available?**

A: No, KotorDiff is designed as a lightweight, command-line only tool. If you need a GUI for configuration generation, check out [HoloGenerator](https://github.com/OldRepublicDevs/PyKotor/tree/main/Tools/HoloGenerator) which provides a web-based interface for generating HoloPatcher configurations.

## Contributing

KotorDiff is part of the PyKotor project. Contributions are welcome!

- **Source**: [https://github.com/OldRepublicDevs/PyKotor](https://github.com/OldRepublicDevs/PyKotor)
- **Issues**: Report bugs and feature requests on GitHub
- **Documentation**: Help improve this README and inline documentation

## License

This tool is open source and part of the PyKotor project. See the main repository for license information.
