# KotorCLI

A build tool for KOTOR projects with cli-compatible syntax.

## Overview

KotorCLI is a command-line tool for converting KOTOR modules, ERFs, and haks between binary and text-based source files. This allows git-based version control and team collaboration for KOTOR modding projects.

**Built on PyKotor** - KotorCLI leverages PyKotor's comprehensive KOTOR file format libraries, providing native support for all KOTOR formats without external dependencies.

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

## Installation

### From Source

```bash
cd Tools/KotorCLI
pip install -e .
```

### Requirements

- Python 3.8+
- PyKotor library (automatically installed)
- nwnnsscomp (optional - falls back to built-in compiler)

## Quick Start

### 1. Initialize a new project

```bash
KotorCLI init myproject
cd myproject
```

### 2. Unpack an existing module

```bash
KotorCLI unpack --file path/to/mymodule.mod
```

### 3. Edit source files

Edit the files in the `src/` directory as needed.

### 4. Pack and install

```bash
KotorCLI install
```

### 5. Generate a kit (GUI or headless)

Headless CLI (recommended for automation):

```bash
python -m kotorcli kit-generate --installation "C:\Games\KOTOR" --module danm13 --output .\kits --kit-id danm13
```

GUI (no arguments provided):

```bash
python -m kotorcli
```

### 6. Convert GUI layouts (GUI or headless)

Headless CLI:

```bash
python -m kotorcli gui-convert --input ./gui_inputs --output ./gui_outputs --resolution 1920x1080,1280x720 --log-level info
```

Interactive GUI (omit args):

```bash
python -m kotorcli gui-convert
```

## PyKotor Integration

KotorCLI is built on PyKotor and uses the following modules:

- **GFF/JSON Conversion**: `pykotor.resource.formats.gff` - Reads/writes GFF files in binary and JSON format
- **ERF/Module Handling**: `pykotor.resource.formats.erf` - Reads/writes ERF, MOD, SAV files
- **RIM Handling**: `pykotor.resource.formats.rim` - Reads/writes RIM files
- **NSS Compilation**: `pykotor.resource.formats.ncs.compilers` - Built-in NWScript compiler
- **Resource Types**: `pykotor.resource.type` - KOTOR resource type system

### Vendor Code References

KotorCLI's implementation is informed by code from PyKotor's vendor directory:

- **xoreos-tools** (`vendor/xoreos-tools/`) - C++ reference for GFF, ERF, and NSS formats
- **KotOR.js** (`vendor/KotOR.js/`) - TypeScript reference for all KOTOR formats
- **Kotor.NET** (`vendor/Kotor.NET/`) - C# reference implementations
- **reone** (`vendor/reone/`) - Comprehensive C++ engine reimplementation

## Commands

### config

Get, set, or unset user-defined configuration options.

```bash
KotorCLI config <key> [<value>]
KotorCLI config --list
KotorCLI config --global nssCompiler /path/to/nwnnsscomp
```

### init

Create a new KotorCLI package.

```bash
KotorCLI init [dir] [file]
KotorCLI init myproject
KotorCLI init myproject --file mymodule.mod
```

### list

List all targets defined in KotorCLI.cfg.

```bash
KotorCLI list
KotorCLI list [target]
KotorCLI list --verbose
```

### unpack

Unpack a file into the project source tree.

```bash
KotorCLI unpack [target] [file]
KotorCLI unpack
KotorCLI unpack --file mymodule.mod
```

### convert

Convert all JSON sources to their GFF counterparts.

```bash
KotorCLI convert [targets...]
KotorCLI convert
KotorCLI convert all
KotorCLI convert demo test
```

### compile

Compile all NWScript sources for target.

**Note**: Uses PyKotor's built-in compiler by default. External compiler (nwnnsscomp) used if found in PATH.

```bash
KotorCLI compile [targets...]
KotorCLI compile
KotorCLI compile --file myscript.nss
```

### pack

Convert, compile, and pack all sources for target.

```bash
KotorCLI pack [targets...]
KotorCLI pack
KotorCLI pack all
KotorCLI pack demo --clean
```

### install

Convert, compile, pack, and install target.

```bash
KotorCLI install [targets...]
KotorCLI install
KotorCLI install demo
KotorCLI install --installDir /path/to/kotor
```

### kit-generate (Holocron kits)

Generate a Holocron-compatible kit from a module. When no CLI args are supplied (`python -m kotorcli`), the Tkinter GUI launches; supplying required args keeps execution headless for CI.

```bash
python -m kotorcli kit-generate --installation "C:\Games\KOTOR" --module danm13 --output .\kits --kit-id danm13 --log-level info
```

### launch

Convert, compile, pack, install, and launch target in-game.

```bash
KotorCLI launch [target]
KotorCLI serve [target]
KotorCLI play [target]
KotorCLI test [target]
```

## Configuration File

The `KotorCLI.cfg` file uses TOML format and is compatible with cli's syntax.

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

While KotorCLI maintains cli's command syntax for familiarity, it has key differences:

1. **Built on PyKotor** - Uses PyKotor's native Python libraries instead of neverwinter.nim
2. **Built-in Compiler** - Includes a native NSS compiler, no external tools required
3. **KOTOR-specific** - Targets KOTOR/KOTOR2 instead of Neverwinter Nights
4. **Python ecosystem** - Easier to extend and integrate with Python tools

## License

MIT License - See LICENSE file for details.

## Credits

- **Syntax inspired by**: [cli](https://github.com/squattingmonk/cli) by squattingmonk
- **Built on**: [PyKotor](https://github.com/th3w1zard1/PyKotor)
- **Format references**: xoreos-tools, KotOR.js, reone, Kotor.NET (in vendor/)

## Contributing

Contributions welcome! Please see the main PyKotor repository for contribution guidelines.

## Documentation

- [QUICKSTART.md](QUICKSTART.md) - 5-minute tutorial
- [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md) - Technical details
- [CHANGELOG.md](CHANGELOG.md) - Version history
