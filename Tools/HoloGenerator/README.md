# HoloGenerator - KOTOR Configuration Generator for HoloPatcher

HoloGenerator is a comprehensive tool for automatically generating `changes.ini` files compatible with HoloPatcher by comparing two KOTOR installations.

## Features

- **Multiple Interfaces**: Command-line, desktop GUI (tkinter), and web-based (React)
- **Real-time Diffing**: Fast, real-time comparison with visual highlighting
- **Multi-format Support**: GFF, 2DA, TLK, SSF, LIP, and other KOTOR file formats
- **Web Interface**: Intuitive side-by-side comparison with undo/redo functionality
- **Sequential File Addition**: Build complex configurations by adding multiple file diffs
- **Import/Export**: Support for importing existing `changes.ini` files

## Usage

### Command Line
```bash
python -m hologenerator /path/to/original/kotor /path/to/modified/kotor -o changes.ini
```

### Desktop GUI
```bash
python -m hologenerator --gui
```

### Web Interface
Visit: https://th3w1zard1.github.io/hologenerator

## Installation

The tool is included as part of the PyKotor toolkit. No additional dependencies are required for the command-line interface. For the GUI interface, tkinter must be available.

## File Support

| Format | Description | Supported |
|--------|-------------|-----------|
| GFF | Game resource files (.utc, .uti, .dlg, etc.) | ✓ |
| 2DA | Table files | ✓ |
| TLK | Dialog/string files | ✓ |
| SSF | Sound set files | ✓ |
| LIP | Lip-sync files | ✓ |
| Others | Binary files (hash comparison) | ✓ |

## Architecture

- `cli.py` - Command-line interface
- `gui/` - Desktop GUI implementation (tkinter)
- `web/` - React web application
- `core/` - Core diffing and generation logic
- `tests/` - Comprehensive unit tests