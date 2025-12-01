"""Pytest configuration for PyPI package tests.

This module provides fixtures and configuration for testing
PyPI package compliance and functionality.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Any

# Ensure project source is available
PROJECT_ROOT = Path(__file__).parent.parent.parent
LIBRARY_PATHS = [
    PROJECT_ROOT / "Libraries" / "PyKotor" / "src",
    PROJECT_ROOT / "Libraries" / "PyKotorGL" / "src",
    PROJECT_ROOT / "Libraries" / "PyKotorFont" / "src",
    PROJECT_ROOT / "Libraries" / "Utility" / "src",
]
for lib_path in LIBRARY_PATHS:
    if lib_path.exists() and str(lib_path) not in sys.path:
        sys.path.insert(0, str(lib_path))


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "pypi: marks tests for PyPI package compliance"
    )
    config.addinivalue_line(
        "markers",
        "slow_network: marks tests that require network access"
    )


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture
def libraries_dir() -> Path:
    """Return the Libraries directory."""
    return PROJECT_ROOT / "Libraries"


@pytest.fixture
def tools_dir() -> Path:
    """Return the Tools directory."""
    return PROJECT_ROOT / "Tools"


@pytest.fixture
def all_pyproject_paths() -> Generator[tuple[str, Path], None, None]:
    """Yield all pyproject.toml paths in the project."""
    # Libraries
    libraries = PROJECT_ROOT / "Libraries"
    if libraries.exists():
        for lib_dir in libraries.iterdir():
            if lib_dir.is_dir():
                pyproject = lib_dir / "pyproject.toml"
                if pyproject.exists():
                    yield lib_dir.name, pyproject
    
    # Tools
    tools = PROJECT_ROOT / "Tools"
    if tools.exists():
        for tool_dir in tools.iterdir():
            if tool_dir.is_dir():
                pyproject = tool_dir / "pyproject.toml"
                if pyproject.exists():
                    yield tool_dir.name, pyproject


@pytest.fixture
def load_toml():
    """Fixture to load TOML files."""
    def _load(path: Path) -> dict[str, Any]:
        try:
            if sys.version_info >= (3, 11):
                import tomllib
            else:
                import tomli as tomllib
        except ImportError:
            pytest.skip("tomli/tomllib not available")
        
        with open(path, "rb") as f:
            return tomllib.load(f)
    
    return _load


@pytest.fixture
def core_package_versions(load_toml) -> dict[str, str]:
    """Return versions of core packages."""
    core_packages = {
        "pykotor": PROJECT_ROOT / "Libraries" / "PyKotor" / "pyproject.toml",
        "pykotorgl": PROJECT_ROOT / "Libraries" / "PyKotorGL" / "pyproject.toml",
        "pykotorfont": PROJECT_ROOT / "Libraries" / "PyKotorFont" / "pyproject.toml",
    }
    
    versions = {}
    for name, path in core_packages.items():
        if path.exists():
            data = load_toml(path)
            version = data.get("project", {}).get("version")
            if version:
                versions[name] = version
    
    return versions

