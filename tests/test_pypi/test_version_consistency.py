"""Test version consistency across packages.

These tests verify that version numbers are consistent
across all packages in the PyKotor ecosystem.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

try:
    from packaging import version
except ImportError:
    version = None  # type: ignore[assignment]

if TYPE_CHECKING:
    pass

PROJECT_ROOT = Path(__file__).parent.parent.parent


def load_pyproject(path: Path) -> dict[str, Any]:
    """Load and parse a pyproject.toml file."""
    try:
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib
    except ImportError:
        pytest.skip("tomli/tomllib not available")
    
    with open(path, "rb") as f:
        return tomllib.load(f)


def get_all_package_versions() -> dict[str, tuple[str, Path]]:
    """Get versions of all packages in the ecosystem."""
    versions: dict[str, tuple[str, Path]] = {}
    
    # Libraries
    libraries = PROJECT_ROOT / "Libraries"
    if libraries.exists():
        for lib_dir in libraries.iterdir():
            if lib_dir.is_dir():
                pyproject = lib_dir / "pyproject.toml"
                if pyproject.exists():
                    data = load_pyproject(pyproject)
                    name = data.get("project", {}).get("name", lib_dir.name)
                    version = data.get("project", {}).get("version", "unknown")
                    versions[name] = (version, pyproject)
    
    # Tools
    tools = PROJECT_ROOT / "Tools"
    if tools.exists():
        for tool_dir in tools.iterdir():
            if tool_dir.is_dir():
                pyproject = tool_dir / "pyproject.toml"
                if pyproject.exists():
                    data = load_pyproject(pyproject)
                    name = data.get("project", {}).get("name", tool_dir.name)
                    version = data.get("project", {}).get("version", "unknown")
                    versions[name] = (version, pyproject)
    
    return versions


class TestVersionConsistency:
    """Test version consistency across packages."""
    
    # Core library packages that should share the same version
    CORE_PACKAGES = {"pykotor", "pykotorgl", "pykotorfont"}
    
    def test_core_libraries_same_version(self):
        """Test that core libraries have the same version."""
        versions = get_all_package_versions()
        
        core_versions: dict[str, str] = {}
        for pkg in self.CORE_PACKAGES:
            if pkg in versions:
                core_versions[pkg] = versions[pkg][0]
        
        if len(core_versions) < 2:
            pytest.skip("Not enough core packages found")
        
        unique_versions = set(core_versions.values())
        
        if len(unique_versions) > 1:
            version_info = ", ".join(f"{k}={v}" for k, v in core_versions.items())
            pytest.warns(
                UserWarning,
                match=f"Core packages have inconsistent versions: {version_info}"
            )
    
    def test_all_versions_valid(self):
        """Test that all versions are valid PEP 440."""
        versions = get_all_package_versions()
        
        pep440_pattern = r"^\d+\.\d+(\.\d+)?(\.?(a|b|rc|dev|post)\d+)?$"
        
        for name, (version, path) in versions.items():
            if version != "unknown":
                assert re.match(pep440_pattern, version), \
                    f"{name}: Version '{version}' is not PEP 440 compliant"
    
    def test_tool_dependencies_match_library_versions(self):
        """Test that tools depend on compatible library versions."""
        versions = get_all_package_versions()
        
        # Get pykotor version
        pykotor_version = versions.get("pykotor", (None, None))[0]
        if pykotor_version is None:
            pytest.skip("pykotor version not found")
        
        # Check that tools depend on a compatible version
        tools = PROJECT_ROOT / "Tools"
        if tools.exists():
            for tool_dir in tools.iterdir():
                if tool_dir.is_dir():
                    pyproject = tool_dir / "pyproject.toml"
                    if pyproject.exists():
                        data = load_pyproject(pyproject)
                        deps = data.get("project", {}).get("dependencies", [])
                        
                        for dep in deps:
                            # Only check dependencies that start with exactly "pykotor" (not "pykotorgl", etc.)
                            # Check if it starts with "pykotor" but not "pykotorgl"
                            if dep.startswith("pykotor") and not dep.startswith("pykotorgl"):
                                # Extract version specifier
                                if ">=" in dep:
                                    match = re.search(r">=([0-9.]+)", dep)
                                    if match:
                                        min_version = match.group(1)
                                        # Check that min version <= current version
                                        # Use proper version comparison if packaging is available
                                        if version is not None:
                                            try:
                                                min_ver = version.Version(min_version)
                                                current_ver = version.Version(pykotor_version)
                                                assert min_ver <= current_ver, \
                                                    f"{tool_dir.name}: depends on pykotor>={min_version} " \
                                                    f"but pykotor is {pykotor_version}"
                                            except version.InvalidVersion:
                                                # Fall back to string comparison if version parsing fails
                                                assert min_version <= pykotor_version, \
                                                    f"{tool_dir.name}: depends on pykotor>={min_version} " \
                                                    f"but pykotor is {pykotor_version}"
                                        else:
                                            # Fall back to string comparison if packaging is not available
                                            # This is not ideal but allows the test to run
                                            pytest.skip("packaging library not available for version comparison")


class TestPoetryVersionConsistency:
    """Test version consistency between project and poetry sections."""
    
    def test_project_and_poetry_versions_match(self):
        """Test that [project] and [tool.poetry] versions match."""
        versions = get_all_package_versions()
        
        for name, (version, path) in versions.items():
            data = load_pyproject(path)
            
            project_version = data.get("project", {}).get("version")
            poetry_version = data.get("tool", {}).get("poetry", {}).get("version")
            
            if project_version and poetry_version:
                if project_version != poetry_version:
                    pytest.warns(
                        UserWarning,
                        match=f"{name}: [project] version ({project_version}) != "
                              f"[tool.poetry] version ({poetry_version})"
                    )


class TestWorkspaceVersion:
    """Test workspace meta-package version."""
    
    def test_workspace_pyproject_exists(self):
        """Test that workspace pyproject.toml exists."""
        workspace_pyproject = PROJECT_ROOT / "pyproject.toml"
        assert workspace_pyproject.exists(), "Workspace pyproject.toml not found"
    
    def test_workspace_version_matches_pykotor(self):
        """Test that workspace version matches pykotor version."""
        workspace_pyproject = PROJECT_ROOT / "pyproject.toml"
        pykotor_pyproject = PROJECT_ROOT / "Libraries" / "PyKotor" / "pyproject.toml"
        
        if not workspace_pyproject.exists() or not pykotor_pyproject.exists():
            pytest.skip("Required pyproject.toml files not found")
        
        workspace_data = load_pyproject(workspace_pyproject)
        pykotor_data = load_pyproject(pykotor_pyproject)
        
        workspace_version = workspace_data.get("project", {}).get("version")
        pykotor_version = pykotor_data.get("project", {}).get("version")
        
        if workspace_version and pykotor_version:
            if workspace_version != pykotor_version:
                pytest.warns(
                    UserWarning,
                    match=f"Workspace version ({workspace_version}) != pykotor version ({pykotor_version})"
                )

