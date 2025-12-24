# Contributing to PyKotor

Thank you for your interest in contributing to PyKotor! This guide will help you set up a development environment and get started.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
  - [Using uv (Recommended)](#using-uv-recommended)
  - [Using Poetry](#using-poetry)
  - [Using pip](#using-pip)
- [Running Tools](#running-tools)
- [Development Workflow](#development-workflow)
- [Code Style and Standards](#code-style-and-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)

## Prerequisites

- **Python 3.8+** (3.9+ recommended)
- **Git** for version control
- One of the following package managers:
  - `uv` (recommended - fastest, written in Rust)
  - `poetry` (good for dependency management)
  - `pip` (standard, always available)

## Development Setup

### Using uv (Recommended)

`uv` is a modern Python package installer written in Rust, offering significantly faster dependency resolution and installation.

#### Installing uv

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Setup Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/th3w1zard1/PyKotor.git
   cd PyKotor
   ```

2. **Install the core library and tools:**
   ```bash
   uv pip install -e "Libraries/PyKotor[all]"
   uv pip install -e "Tools/HolocronToolset"
   uv pip install -e "Tools/HoloPatcher"
   uv pip install -e "Tools/KotorCLI"
   uv pip install -e "Tools/KotorDiff"
   ```

   Or install everything at once:
   ```bash
   uv pip install -e "Libraries/PyKotor[all]" -e "Tools/HolocronToolset" -e "Tools/HoloPatcher" -e "Tools/KotorCLI" -e "Tools/KotorDiff"
   ```

3. **Install development dependencies:**
   ```bash
   uv pip install -e "Libraries/PyKotor[dev]"
   ```

#### Alternatively, use uv sync (workspace mode):

If the project supports workspace mode:
```bash
uv sync
```

This will:
- Create a virtual environment (`.venv`)
- Install all dependencies from `pyproject.toml`
- Install the workspace in editable mode

### Using Poetry

1. **Install Poetry** (if not already installed):
   ```bash
   pip install poetry
   ```

   Or use the official installer:
   ```bash
   # Windows (PowerShell)
   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

   # macOS/Linux
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Clone and install:**
   ```bash
   git clone https://github.com/th3w1zard1/PyKotor.git
   cd PyKotor
   poetry install
   ```

3. **Activate the virtual environment:**
   ```bash
   poetry shell
   ```

4. **Install development dependencies:**
   ```bash
   poetry install --with dev
   ```

### Using pip

1. **Clone the repository:**
   ```bash
   git clone https://github.com/th3w1zard1/PyKotor.git
   cd PyKotor
   ```

2. **Create a virtual environment:**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install the project:**
   ```bash
   pip install -e "Libraries/PyKotor[all]"
   pip install -e "Tools/HolocronToolset"
   pip install -e "Tools/HoloPatcher"
   pip install -e "Tools/KotorCLI"
   pip install -e "Tools/KotorDiff"
   ```

4. **Install development dependencies:**
   ```bash
   pip install -r requirements-dev.txt --prefer-binary
   ```

## Running Tools

After installation, you can run the tools in several ways:

### Using uv (Recommended)

**From source (development mode):**
```bash
# HolocronToolset
uv --directory="Tools/HolocronToolset/src" run --module toolset

# HoloPatcher
uv --directory="Tools/HoloPatcher/src" run --module holopatcher

# KotorCLI
uv --directory="Tools/KotorCLI/src" run --module kotorcli --help

# KotorDiff
uv --directory="Tools/KotorDiff/src" run --module kotordiff --help
```

**If installed via uv pip:**
```bash
uv run holocrontoolset
uv run holopatcher
uv run kotorcli --help
uv run kotordiff --help
```

### Using uvx (Run from PyPI without installation)

Run the latest version directly from PyPI:

**Windows (PowerShell):**
```powershell
uvx holocrontoolset
uvx holopatcher
uvx kotorcli --help
uvx kotordiff --help
```

**macOS/Linux:**
```bash
uvx holocrontoolset
uvx holopatcher
uvx kotorcli --help
uvx kotordiff --help
```

### Using Poetry

After activating the poetry shell:
```bash
python Tools/HolocronToolset/src/toolset/__main__.py
python Tools/HoloPatcher/src/holopatcher/__main__.py
python Tools/KotorCLI/src/kotorcli/__main__.py
python Tools/KotorDiff/src/kotordiff/__main__.py
```

### Using pip

After activating your virtual environment:
```bash
# If installed as console scripts
holocrontoolset
holopatcher
kotorcli --help
kotordiff --help

# Or run as modules
python -m toolset
python -m holopatcher
python -m kotorcli --help
python -m kotordiff --help
```

## Development Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write clean, readable code
   - Follow the project's code style (see below)
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests:**
   ```bash
   # Using pytest
   pytest

   # With coverage
   pytest --cov=pykotor --cov-report=html
   ```

4. **Check code quality:**
   ```bash
   # Linting with ruff
   ruff check .

   # Type checking with mypy
   mypy Libraries/PyKotor/src/pykotor

   # Formatting check
   ruff format --check .
   ```

5. **Commit your changes:**
   ```bash
   git add file1.py file2.py
   git commit -m "type: descriptive message"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `refactor:` for code refactoring
   - `test:` for test additions/changes
   - `chore:` for maintenance tasks

6. **Push and create a pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style and Standards

- **Python Version:** Support Python 3.8 through 3.12+ (and newer, e.g. 3.13)
- **Linting:** We use `ruff` for linting and formatting
- **Type Hints:** Use type hints where appropriate
- **Docstrings:** Follow Google-style docstrings
- **Imports:** Use absolute imports, organize with `isort` (via ruff)
- **Testing:** Write tests for new features and bug fixes

### Running Linters

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

## Testing

### Running Tests

**Using pytest:**
```bash
# All tests
pytest

# Specific test file
pytest tests/test_specific.py

# With verbose output
pytest -v

# With coverage
pytest --cov=pykotor --cov-report=term-missing
```

**Using uv:**
```bash
uv run pytest
```

**Using Poetry:**
```bash
poetry run pytest
```

### Writing Tests

- Place tests in the `tests/` directory
- Use descriptive test names
- Follow the `test_*.py` naming convention
- Use pytest fixtures for common setup
- Aim for good test coverage, especially for new features

## Submitting Changes

1. **Ensure your code passes all checks:**
   - Tests pass
   - Linting passes
   - Type checking passes (if applicable)
   - Documentation is updated

2. **Create a pull request:**
   - Provide a clear description of your changes
   - Reference any related issues
   - Include screenshots for UI changes
   - Be responsive to feedback

3. **Code review:**
   - Address review comments promptly
   - Keep commits focused and logical
   - Squash commits if requested

## Additional Resources

- [PyKotor Documentation](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/docs)
- [Project Wiki](https://github.com/th3w1zard1/PyKotor/wiki)
- [Issue Tracker](https://github.com/th3w1zard1/PyKotor/issues)

## Questions?

If you have questions or need help, please:
- Open an issue on GitHub
- Check existing documentation
- Review similar code in the codebase

Thank you for contributing to PyKotor!

