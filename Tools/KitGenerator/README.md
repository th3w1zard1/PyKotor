# Kit Generator

Kit Generator GUI for PyKotor CLI - generates Holocron-compatible kits from KOTOR module files (RIM/ERF).

This is a shim package that provides a standalone GUI entry point. The core functionality is in `pykotor.cli.commands.kit_generate`.

## Installation

```bash
pip install kit-generator
```

Or install from source:

```bash
cd Tools/KitGenerator
pip install -e .
```

## Usage

### GUI Mode

Launch the GUI:

```bash
kit-generator
# or
python -m kitgenerator
```

### CLI Mode

Use via PyKotor CLI:

```bash
python Libraries/PyKotor/src/pykotor/cli/__main__.py kit-generate --installation <path> --module <module> --output <dir>
```

Or launch GUI from CLI:

```bash
python Libraries/PyKotor/src/pykotor/cli/__main__.py kit-generate --gui
```

## Features

- Extract kit resources from KOTOR module files (RIM/ERF)
- Generate Holocron-compatible kit structures
- Interactive GUI for selecting installation, module, and output directory
- Headless CLI mode for automation

## License

LGPL-3.0-or-later
