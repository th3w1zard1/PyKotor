# KotorCLI Quick Start Guide

## Installation

```bash
cd Tools/KotorCLI
pip install -e .
```

## 5-Minute Tutorial

### 1. Create a new project

```bash
KotorCLI init mymod
cd mymod
```

This creates:

- `KotorCLI.cfg` - Configuration file
- `src/` - Source directory structure
- `.gitignore` - Git ignore file
- `.KotorCLI/` - Local config directory

### 2. Unpack an existing module (optional)

```bash
KotorCLI unpack --file ~/path/to/mymodule.mod
```

This extracts all files from the module into your `src/` directory, converting GFF files to JSON format.

### 3. View your targets

```bash
KotorCLI list
```

Shows all configured targets in your `KotorCLI.cfg`.

### 4. Make changes

Edit files in the `src/` directory:

- Scripts: `src/scripts/*.nss`
- Dialogs: `src/dialogs/*.dlg.json`
- Creatures: `src/blueprints/creatures/*.utc.json`
- Areas: `src/areas/*.git.json`, `*.are.json`
- etc.

### 5. Pack your module

```bash
KotorCLI pack
```

This will:

1. Convert JSON files to GFF
2. Compile NWScript files
3. Pack everything into a module file

### 6. Install and test

```bash
KotorCLI install
```

This installs the packed module to your KOTOR directory.

Or launch the game directly:

```bash
KotorCLI play
```

### 7. Diff installs/files with KotorDiff (headless or GUI)

Headless CLI (preferred for automation):

```bash
python -m kotorcli diff-installation --path1 "C:\Games\KOTOR" --path2 "C:\Games\KOTOR_Modded" --filter tat_m17ac --output-mode diff_only
# Generate incremental TSLPatcher data while diffing
python -m kotorcli diff-installation --path1 "C:\Games\KOTOR" --path2 "C:\Games\KOTOR_Modded" --tslpatchdata .\tslpatchdata --incremental
```

GUI (omit paths or pass `--gui`):

```bash
kotordiff
# or
python -m kotorcli diff-installation --gui
```

## Common Workflows

### Starting from scratch

```bash
KotorCLI init mynewmod
cd mynewmod
# Create/edit source files
KotorCLI pack
```

### Working with an existing module

```bash
KotorCLI init mynewmod
cd mynewmod
KotorCLI unpack --file ~/modules/existing.mod
# Edit source files
KotorCLI install
```

### Testing changes quickly

```bash
KotorCLI play
```

This runs convert, compile, pack, install, and launches the game in one command.

### Building multiple targets

```toml
# In KotorCLI.cfg
[target]
name = "demo"
file = "demo.mod"

[target]
name = "full"
file = "full.mod"
```

```bash
KotorCLI pack all        # Build all targets
KotorCLI pack demo       # Build specific target
KotorCLI install full    # Install specific target
```

## Configuration

### Global settings

```bash
# Set script compiler path
KotorCLI config --global nssCompiler /path/to/nwnnsscomp

# Set KOTOR install directory
KotorCLI config --global installDir ~/Documents/KotOR

# List all settings
KotorCLI config --list --global
```

### Local (per-project) settings

```bash
KotorCLI config --local modName "My Awesome Mod"
KotorCLI config --list --local
```

## Tips & Tricks

### Use version control

```bash
cd mymod
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/mymod
git push -u origin main
```

### Clean builds

```bash
KotorCLI pack --clean
```

Clears the cache before building.

### Skip steps

```bash
KotorCLI pack --noConvert    # Don't convert JSON
KotorCLI pack --noCompile    # Don't compile scripts
KotorCLI install --noPack    # Just install existing file
```

### Compile specific files

```bash
KotorCLI compile --file myscript.nss
```

### Verbose output

```bash
KotorCLI pack --verbose
KotorCLI pack --debug
```

### Quiet mode

```bash
KotorCLI pack --quiet
```

## Next Steps

- Read the [README.md](README.md) for full command documentation
- Check [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md) for technical details
- See [KotorCLI.cfg examples](https://github.com/squattingmonk/cli#clicfg) (cli-compatible)

## Getting Help

```bash
KotorCLI --help
KotorCLI <command> --help
```

For issues or questions, visit the [PyKotor repository](https://github.com/OldRepublicDevs/PyKotor).
