# PyKotor

A comprehensive Python library for reading and modifying file formats used by the game [Knights of the Old Republic](https://en.wikipedia.org/wiki/Star_Wars:_Knights_of_the_Old_Republic_(video_game)) and its [sequel](https://en.wikipedia.org/wiki/Star_Wars_Knights_of_the_Old_Republic_II:_The_Sith_Lords).

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Available Tools](#available-tools)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Complete file format support** for KotOR and TSL game files
- **Cross-platform** (Windows, macOS, Linux)
- **Comprehensive toolset** for modding and development
- **Modern Python** (3.8+)
- **Type-annotated** API with extensive documentation

## Requirements

- Python 3.8+
- Windows 7+, macOS, or Linux

## Installation

### Quick Install

The fastest way to get started is using `uvx` (no installation required):

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
uvx holocrontoolset
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uvx holocrontoolset
```

### Standard Install

**Install the library:**
```bash
pip install pykotor
```

**Install tools:**
```bash
pip install holocrontoolset holopatcher kotordiff
```

**Or use pipx for isolated tool installation:**
```bash
pipx install holocrontoolset
pipx install holopatcher
pipx install kotordiff
```

**Note:** The PyKotor CLI is included with the `pykotor` package and accessible via `pykotor` or `pykotorcli` commands.

See [CONTRIBUTING.md](CONTRIBUTING.md) for development installation.

## Quick Start

### Using the Library

```python
from pykotor.resource.type import ResourceType
from pykotor.extract.installation import Installation
from pykotor.resource.formats.tpc import write_tpc

# Load game installation
inst = Installation("C:/Program Files (x86)/Steam/steamapps/common/swkotor")

# Extract a texture
texture = inst.texture("C_Gammorean01")
write_tpc(texture, "./C_Gammorean01.tga", ResourceType.TGA)
```

### Using the Tools

**HolocronToolset** - GUI editor for KotOR files:
```bash
uvx holocrontoolset
```

**HoloPatcher** - Cross-platform TSLPatcher alternative:
```bash
uvx holopatcher --help
```

**PyKotor CLI** - Command-line build tool (included with pykotor):
```bash
# After installing pykotor package
pykotor init mymod
cd mymod
pykotor pack
```

**KotorDiff** - Compare and generate patches:
```bash
uvx kotordiff
# or if installed via pip/pipx
kotordiff
kotor-diff  # alternative name
```

See individual tool documentation for detailed usage.

## Available Tools

| Tool | Description | Documentation |
|------|-------------|---------------|
| **HolocronToolset** | Full-featured GUI editor for KotOR files | [README](https://github.com/OldRepublicDevs/PyKotor/tree/master/Tools/HolocronToolset#readme) |
| **HoloPatcher** | Fast, cross-platform mod installer | [README](https://github.com/OldRepublicDevs/PyKotor/tree/master/Tools/HoloPatcher#readme) |
| **PyKotor CLI** | Command-line build tool (part of pykotor package) | [Docs](https://github.com/OldRepublicDevs/PyKotor/tree/master/Libraries/PyKotor/docs) |
| **KotorDiff** | File comparison and TSLPatcher data generator | [README](https://github.com/OldRepublicDevs/PyKotor/tree/master/Tools/KotorDiff#readme) |

## Documentation

- **[Installation & Usage](https://github.com/OldRepublicDevs/PyKotor/tree/master/Libraries/PyKotor/docs)** - Detailed library documentation
- **[Contributing Guide](CONTRIBUTING.md)** - Development setup and guidelines
- **[Project Wiki](https://github.com/OldRepublicDevs/PyKotor/wiki)** - Community documentation
- **[PowerShell Setup](POWERSHELL.md)** - Windows PowerShell configuration

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development environment setup
- Code style guidelines
- Testing procedures
- Pull request process

## License

This project is licensed under the [LGPL-3.0-or-later License](https://github.com/OldRepublicDevs/PyKotor/blob/master/LICENSE).
