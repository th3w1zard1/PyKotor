# PyKotor

A comprehensive Python library that can read and modify most file formats used by the game [Knights of the Old Republic](https://en.wikipedia.org/wiki/Star_Wars:_Knights_of_the_Old_Republic_(video_game)) and its [sequel](https://en.wikipedia.org/wiki/Star_Wars_Knights_of_the_Old_Republic_II:_The_Sith_Lords).

## Features

- **Complete file format support** for KotOR and TSL game files
- **Cross-platform** support (Windows, macOS, Linux)
- **Comprehensive toolset** for modding and development
- **Modern Python** support (3.8+)
- **Well-documented** API and examples

## Requirements

- Python 3.8 through 3.12+ (including 3.13)
- Supported on Windows, macOS, and Linux (including case-sensitive filesystems)

## Installation

### From PyPI

> **Note:** The PyPI package is currently in maintenance. Please check back later or install from source.

```bash
pip install pykotor
```

### From Source

#### Using uv (Recommended - Fastest)

`uv` is a modern Python package installer written in Rust, offering significantly faster dependency resolution and installation.

**Install uv:**

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Install PyKotor:**
```bash
git clone https://github.com/th3w1zard1/PyKotor.git
cd PyKotor
uv pip install -e "Libraries/PyKotor[all]"
uv pip install -e "Tools/HolocronToolset"
uv pip install -e "Tools/HoloPatcher"
uv pip install -e "Tools/KotorCLI"
```

#### Using Poetry

```bash
git clone https://github.com/th3w1zard1/PyKotor.git
cd PyKotor
pip install poetry
poetry install
poetry shell
```

#### Using pip

```bash
git clone https://github.com/th3w1zard1/PyKotor.git
cd PyKotor
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -e "Libraries/PyKotor[all]"
pip install -e "Tools/HolocronToolset"
pip install -e "Tools/HoloPatcher"
pip install -e "Tools/KotorCLI"
```

## Running Tools

PyKotor includes several powerful tools for working with KotOR files. You can run them in multiple ways:

### Quick Start with uvx (No Installation Required)

Run the latest version directly from PyPI without installing:

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"; uvx holocrontoolset
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh && uvx holocrontoolset
```

### Running Installed Tools

#### Using uv

**From source (development mode):**
```bash
uv --directory="Tools/HolocronToolset/src" run --module toolset
uv --directory="Tools/HoloPatcher/src" run --module holopatcher
uv --directory="Tools/KotorCLI/src" run --module kotorcli --help
uv --directory="Tools/KotorDiff/src" run --module kotordiff --help
```

**If installed via uv pip:**
```bash
uv run holocrontoolset
uv run holopatcher
uv run kotorcli --help
uv run kotordiff --help
```

#### Using uvx (Run from PyPI)

```bash
uvx holocrontoolset
uvx holopatcher
uvx kotorcli --help
uvx kotordiff --help
```

#### Using Poetry or pip

After activating your virtual environment:

```bash
# Run as console scripts (if installed)
holocrontoolset
holopatcher
kotorcli --help
kotordiff --help

# Or run as Python modules
python Tools/HolocronToolset/src/toolset/__main__.py
python Tools/HoloPatcher/src/holopatcher/__main__.py
python Tools/KotorCLI/src/kotorcli/__main__.py
python Tools/KotorDiff/src/kotordiff/__main__.py
```

### Available Tools

- **HolocronToolset** - A PyQt5 application for editing KotOR files
- **HoloPatcher** - A faster, cross-platform alternative to TSLPatcher
- **KotorCLI** - A comprehensive command-line build tool for KOTOR projects
- **KotorDiff** - Generates TSLPatcher patch data from file differences

See individual tool READMEs for more information:
- [HolocronToolset](https://github.com/th3w1zard1/PyKotor/tree/master/Tools/HolocronToolset#readme)
- [HoloPatcher](https://github.com/th3w1zard1/PyKotor/tree/master/Tools/HoloPatcher#readme)
- [KotorCLI](https://github.com/th3w1zard1/PyKotor/tree/master/Tools/KotorCLI#readme)
- [KotorDiff](https://github.com/th3w1zard1/PyKotor/tree/master/Tools/KotorDiff#readme)

## Usage Example

Simple example of loading data from a game directory, searching for a specific texture, and exporting it to the TGA format:

```python
from pykotor.resource.type import ResourceType
from pykotor.extract.installation import Installation
from pykotor.resource.formats.tpc import write_tpc

inst = Installation("C:/Program Files (x86)/Steam/steamapps/common/swkotor")
tex = inst.texture("C_Gammorean01")
write_tpc(tex, "./C_Gammorean01.tga", ResourceType.TGA)
```

This saves `C_Gammorean01.tga` to the current directory.

[More examples](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/docs/installation.md)

## Development

For development setup, see [CONTRIBUTING.md](CONTRIBUTING.md).

### Quick Development Setup

**Using uv:**
```bash
git clone https://github.com/th3w1zard1/PyKotor.git
cd PyKotor
uv pip install -e "Libraries/PyKotor[all,dev]"
uv pip install -e "Tools/HolocronToolset"
uv pip install -e "Tools/HoloPatcher"
uv pip install -e "Tools/KotorCLI"
```

**Using Poetry:**
```bash
poetry install --with dev
```

**Using pip:**
```bash
pip install -r requirements-dev.txt --prefer-binary
```

This installs development tools like `mypy`, `ruff`, `pylint`, `pytest`, etc.

### Code Quality

```bash
# Linting
ruff check .

# Formatting
ruff format .

# Type checking
mypy Libraries/PyKotor/src/pykotor

# Testing
pytest
```

## Building Standalone Executables

After cloning the repository, you can build standalone executables using the PowerShell scripts in the `compile` folder:

1. Run dependency setup scripts first:
   - `deps_holopatcher.ps1`
   - `deps_toolset.ps1`

2. Then run compilation scripts:
   - `compile_holopatcher.ps1`
   - `compile_toolset.ps1`

This will:
- Find a compatible Python interpreter (or install Python 3.8)
- Set up the environment (venv and PYTHONPATH)
- Install the tool's dependencies
- Install PyInstaller
- Compile to a single executable binary in the `dist` folder

## Additional Resources

- [Contributing Guide](CONTRIBUTING.md)
- [PyKotor Documentation](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/docs)
- [Project Wiki](https://github.com/th3w1zard1/PyKotor/wiki)
- [POWERSHELL.md](https://github.com/th3w1zard1/PyKotor/blob/master/POWERSHELL.md) - PowerShell script information

## License

This repository falls under the [LGPL-3.0-or-later License](https://github.com/th3w1zard1/PyKotor/blob/master/LICENSE).
