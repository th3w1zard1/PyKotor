# PyKotor CLI

A build tool for KOTOR projects with cli-compatible syntax, integrated into PyKotor.

## Overview

PyKotor CLI is a command-line tool for converting KOTOR modules, ERFs, and haks between binary and text-based source files. This allows git-based version control and team collaboration for KOTOR modding projects.

**Part of PyKotor** - The CLI functionality is now integrated directly into PyKotor, providing a unified library and tool experience.

### Features

- **cli-compatible syntax** - Uses the same command structure as cli for familiarity
- **Git-friendly workflow** - Convert binary KOTOR files to JSON for version control
- **Built-in NSS compiler** - Compile scripts without external dependencies using PyKotor's native compiler
- **Fast** - Built on PyKotor's high-performance libraries
- **Multiple targets** - Support for modules, ERFs, haks, and more
- **Flexible source trees** - Organize your source files however you want
- **Pure Python** - No external tool dependencies required (nwnnsscomp optional)
- **Holocron kit generator** - Generate Holocron-compatible kits via `kit-generate` in headless mode or by launching the Tkinter GUI when no CLI args are provided
- **GUI converter** - Resize KotOR `.gui` layouts to common resolutions (`gui-convert` headless, GUI when arguments are omitted)
- **Integrated KotorDiff** - Structured comparisons across files, modules, and installations; stays headless when CLI args are provided and launches the KotorDiff GUI when omitted or `--gui` is passed

## Installation

### From PyPI

```bash
pip install pykotor
```

The CLI is available via:
- `python -m pykotor` - Run as a module
- `pykotor` - Console script entry point (after installation)
- `pykotorcli` - Alternative console script entry point

### From Source

```bash
cd Libraries/PyKotor
pip install -e .
```

### Requirements

- Python 3.8+
- nwnnsscomp (optional - falls back to built-in compiler)

## Quick Start

### 1. Initialize a new project

```bash
pykotor init myproject
cd myproject
```

### 2. Unpack an existing module

```bash
pykotor unpack --file path/to/mymodule.mod
```

### 3. Edit source files

Edit the files in the `src/` directory as needed.

### 4. Pack and install

```bash
pykotor install
```

### 5. Generate a kit (GUI or headless)

Headless CLI (recommended for automation):

```bash
pykotor kit-generate --installation "C:\Games\KOTOR" --module danm13 --output .\kits --kit-id danm13
```

GUI (no arguments provided):

```bash
python -m pykotor
```

### 6. Convert GUI layouts (GUI or headless)

Headless CLI:

```bash
pykotor gui-convert --input ./gui_inputs --output ./gui_outputs --resolution 1920x1080,1280x720 --log-level info
```

Interactive GUI (omit args):

```bash
pykotor gui-convert
```

### 7. Run KotorDiff comparisons (headless or GUI)

Headless CLI (stays in the console when paths are provided):

```bash
pykotor diff-installation --path1 "C:\Games\KOTOR" --path2 "C:\Games\KOTOR_Modded" --filter tat_m17ac --output-mode diff_only
# Write TSLPatcher output incrementally while diffing
pykotor diff-installation --path1 "C:\Games\KOTOR" --path2 "C:\Games\KOTOR_Modded" --tslpatchdata .\tslpatchdata --incremental
```

GUI (omit paths or pass `--gui`):

```bash
pykotor diff-installation --gui
```

## PyKotor Integration

The CLI is built directly into PyKotor and uses the following modules:

- **GFF/JSON Conversion**: `pykotor.resource.formats.gff` - Reads/writes GFF files in binary and JSON format
- **ERF/Module Handling**: `pykotor.resource.formats.erf` - Reads/writes ERF, MOD, SAV files
- **RIM Handling**: `pykotor.resource.formats.rim` - Reads/writes RIM files
- **NSS Compilation**: `pykotor.resource.formats.ncs.compilers` - Built-in NWScript compiler
- **Resource Types**: `pykotor.resource.type` - KOTOR resource type system

### Vendor Code References

The CLI implementation is informed by code from PyKotor's vendor directory:

- **xoreos-tools** (`vendor/xoreos-tools/`) - C++ reference for GFF, ERF, and NSS formats
- **KotOR.js** (`vendor/KotOR.js/`) - TypeScript reference for all KOTOR formats
- **Kotor.NET** (`vendor/Kotor.NET/`) - C# reference implementations
- **reone** (`vendor/reone/`) - Comprehensive C++ engine reimplementation

## Commands

### config

Get, set, or unset user-defined configuration options.

```bash
pykotor config <key> [<value>]
pykotor config --list
pykotor config --global nssCompiler /path/to/nwnnsscomp
```

### init

Create a new PyKotor package.

```bash
pykotor init [dir] [file]
pykotor init myproject
pykotor init myproject --file mymodule.mod
```

### list

List all targets defined in pykotor.cfg.

```bash
pykotor list
pykotor list [target]
pykotor list --verbose
```

### unpack

Unpack a file into the project source tree.

```bash
pykotor unpack [target] [file]
pykotor unpack
pykotor unpack --file mymodule.mod
```

### extract

Extract resources from archive files (`.key`, `.bif`, `.rim`, `.erf/.mod/.sav/.hak`).

**Filtering** (`--filter`) supports:

- `resref` prefix (example: `p_cand` matches `p_cand.*`, `p_cand01.*`, etc.)
- exact `resref.ext` filename (example: `p_cand.utc`)
- glob patterns (examples: `p_cand*`, `p_bastila*`, `p_bastila.utc`)

Examples (PowerShell):

```powershell
$Env:PYTHONIOENCODING='utf-8'; pykotor --no-color extract --file "C:\Program Files (x86)\Steam\steamapps\common\swkotor\data\templates.bif" --key-file "C:\Program Files (x86)\Steam\steamapps\common\swkotor\chitin.key" --output "tmp\utc_templates" --filter "p_bastila.utc"
$Env:PYTHONIOENCODING='utf-8'; pykotor --no-color extract --file "C:\Program Files (x86)\Steam\steamapps\common\swkotor\chitin.key" --output "tmp\utc_templates" --filter "p_cand.utc"
$Env:PYTHONIOENCODING='utf-8'; pykotor --no-color extract --file "C:\Program Files (x86)\Steam\steamapps\common\swkotor\chitin.key" --output "tmp\utc_templates" --filter "p_cand"
```

### list-archive (ls-archive)

List resources inside an archive file (`.key`, `.bif`, `.rim`, `.erf/.mod/.sav/.hak`). Use `--key-file` when listing a `.bif` if you want proper resource names.

```powershell
$Env:PYTHONIOENCODING='utf-8'; pykotor --no-color list-archive --help
$Env:PYTHONIOENCODING='utf-8'; pykotor --no-color list-archive --file "C:\Program Files (x86)\Steam\steamapps\common\swkotor\data\templates.bif" --key-file "C:\Program Files (x86)\Steam\steamapps\common\swkotor\chitin.key" --resources --filter "p_bastila*" --verbose
$Env:PYTHONIOENCODING='utf-8'; pykotor --no-color list-archive --file "C:\Program Files (x86)\Steam\steamapps\common\swkotor\data\templates.bif" --key-file "C:\Program Files (x86)\Steam\steamapps\common\swkotor\chitin.key" --filter "p_bastila*"
$Env:PYTHONIOENCODING='utf-8'; pykotor --no-color list-archive --file "C:\Program Files (x86)\Steam\steamapps\common\swkotor\chitin.key" --resources --filter "p_cand*"
```

### search-archive (grep-archive)

Search for resources in an archive by name (glob patterns) or by content (`--content`).

```powershell
$Env:PYTHONIOENCODING='utf-8'; pykotor --no-color search-archive --help
$Env:PYTHONIOENCODING='utf-8'; pykotor --no-color search-archive --file "C:\Program Files (x86)\Steam\steamapps\common\swkotor\data\templates.bif" --key-file "C:\Program Files (x86)\Steam\steamapps\common\swkotor\chitin.key" "p_cand*"
```

### convert

Convert all JSON sources to their GFF counterparts.

```bash
pykotor convert [targets...]
pykotor convert
pykotor convert all
pykotor convert demo test
```

### compile

Compile all NWScript sources for target.

**Note**: Uses PyKotor's built-in compiler by default. External compiler (nwnnsscomp) used if found in PATH.

```bash
pykotor compile [targets...]
pykotor compile
pykotor compile --file myscript.nss
```

### pack

Convert, compile, and pack all sources for target.

```bash
pykotor pack [targets...]
pykotor pack
pykotor pack all
pykotor pack demo --clean
```

### install

Convert, compile, pack, and install target.

```bash
pykotor install [targets...]
pykotor install
pykotor install demo
pykotor install --installDir /path/to/kotor
```

### kit-generate (Holocron kits)

Generate a Holocron-compatible kit from a module. When no CLI args are supplied (`python -m pykotor`), the Tkinter GUI launches; supplying required args keeps execution headless for CI.

```bash
pykotor kit-generate --installation "C:\Games\KOTOR" --module danm13 --output .\kits --kit-id danm13 --log-level info
```

### diff-installation (KotorDiff)

Structured comparisons for files, folders, modules, or full installations. Stays headless when paths are supplied; falls back to the GUI when arguments are omitted or `--gui` is passed.

```bash
# Installation vs installation with filtering
pykotor diff-installation --path1 "C:\Games\KOTOR" --path2 "C:\Games\KOTOR_Modded" --filter tat_m17ac --output-mode diff_only --log-level info

# Generate incremental TSLPatcher output while diffing
pykotor diff-installation --path1 "C:\Games\KOTOR" --path2 "C:\Games\KOTOR_Modded" --tslpatchdata .\tslpatchdata --ini changes.ini --incremental

# Launch the GUI explicitly
pykotor diff-installation --gui
```

Key options:

- `--path1/--path2/--path3/--path`: up to N-way comparisons
- `--filter`: limit comparisons to specific modules/resources (e.g., `tat_m17ac`, `dialog.tlk`)
- `--output-mode`: `full`, `diff_only`, or `quiet`
- `--output-log`: write logs to a file (UTF-8)
- `--tslpatchdata` + `--ini`: emit TSLPatcher-ready output; add `--incremental` to stream writes during diffing
- `--compare-hashes/--no-compare-hashes`: toggle hash comparison for unsupported resource types

### launch

Convert, compile, pack, install, and launch target in-game.

```bash
pykotor launch [target]
pykotor serve [target]
pykotor play [target]
pykotor test [target]
```

## Configuration File

The `pykotor.cfg` file uses TOML format and is compatible with cli's syntax.

### Example Configuration

```toml
[package]
name = "My KOTOR Mod"
description = "An awesome mod"
version = "1.0.0"
author = "Your Name <your.email@example.com>"

  [package.sources]
  include = "src/**/*.{nss,json,ncs}"
  exclude = "**/test_*.nss"

  [package.rules]
  "*.nss" = "src/scripts"
  "*.ncs" = "src/scripts"
  "*.utc" = "src/blueprints/creatures"
  "*" = "src"

[target]
name = "default"
file = "mymod.mod"
description = "Default module target"
```

## Differences from cli

While PyKotor CLI maintains cli's command syntax for familiarity, it has key differences:

1. **Built on PyKotor** - Uses PyKotor's native Python libraries instead of neverwinter.nim
2. **Built-in Compiler** - Includes a native NSS compiler, no external tools required
3. **KOTOR-specific** - Targets KOTOR/KOTOR2 instead of Neverwinter Nights
4. **Python ecosystem** - Easier to extend and integrate with Python tools

## Backward Compatibility

The `kotorcli` package is still available as a shim that depends on `pykotor` and forwards all functionality. This ensures existing scripts and workflows continue to work:

```bash
# These all work the same way:
python -m kotorcli --help
python -m pykotor --help
pykotor --help
pykotorcli --help
```

## License

MIT License - See LICENSE file for details.

## Credits

- **Syntax inspired by**: [cli](https://github.com/squattingmonk/cli) by squattingmonk
- **Built on**: [PyKotor](https://github.com/OldRepublicDevs/PyKotor)
- **Format references**: xoreos-tools, KotOR.js, reone, Kotor.NET (in vendor/)

## Contributing

Contributions welcome! Please see the main PyKotor repository for contribution guidelines.

## Documentation

- [Installation Guide](installation.md) - Installation instructions
- Additional documentation available in the main PyKotor repository
