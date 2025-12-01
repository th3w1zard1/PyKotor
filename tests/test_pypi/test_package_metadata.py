"""Test package metadata for PyPI compliance.

These tests verify that all packages have proper metadata required for
PyPI distribution including version, description, author, and classifiers.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def get_pyproject_paths() -> Generator[tuple[str, Path], None, None]:
    """Yield all pyproject.toml paths with their package names."""
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


class TestPackageMetadata:
    """Test package metadata compliance."""
    
    @pytest.fixture(params=list(get_pyproject_paths()))
    def package_info(self, request: pytest.FixtureRequest) -> tuple[str, Path, dict[str, Any]]:
        """Fixture providing package name, path, and parsed pyproject.toml."""
        name, path = request.param
        data = load_pyproject(path)
        return name, path, data
    
    def test_has_build_system(self, package_info: tuple[str, Path, dict[str, Any]]):
        """Test that package has a build-system section."""
        name, path, data = package_info
        assert "build-system" in data, f"{name}: Missing [build-system] section"
        assert "requires" in data["build-system"], f"{name}: Missing build-system.requires"
        assert "build-backend" in data["build-system"], f"{name}: Missing build-system.build-backend"
    
    def test_has_project_section(self, package_info: tuple[str, Path, dict[str, Any]]):
        """Test that package has a project section."""
        name, path, data = package_info
        assert "project" in data, f"{name}: Missing [project] section"
    
    def test_has_required_fields(self, package_info: tuple[str, Path, dict[str, Any]]):
        """Test that package has all required PyPI fields."""
        name, path, data = package_info
        project = data.get("project", {})
        
        required_fields = ["name", "version", "description"]
        for field in required_fields:
            assert field in project, f"{name}: Missing required field: {field}"
    
    def test_has_recommended_fields(self, package_info: tuple[str, Path, dict[str, Any]]):
        """Test that package has recommended PyPI fields."""
        name, path, data = package_info
        project = data.get("project", {})
        
        # These are recommended but not strictly required
        recommended = ["authors", "license", "requires-python"]
        missing = [f for f in recommended if f not in project]
        
        if missing:
            pytest.warns(UserWarning, match=f"{name}: Missing recommended fields: {missing}")
    
    def test_version_format(self, package_info: tuple[str, Path, dict[str, Any]]):
        """Test that version follows PEP 440."""
        import re
        
        name, path, data = package_info
        project = data.get("project", {})
        version = project.get("version", "")
        
        # PEP 440 compliant version pattern (simplified)
        pep440_pattern = r"^\d+\.\d+(\.\d+)?(\.?(a|b|rc|dev|post)\d+)?$"
        assert re.match(pep440_pattern, version), f"{name}: Version '{version}' is not PEP 440 compliant"
    
    def test_python_requires(self, package_info: tuple[str, Path, dict[str, Any]]):
        """Test that requires-python is properly specified."""
        name, path, data = package_info
        project = data.get("project", {})
        
        if "requires-python" in project:
            requires = project["requires-python"]
            # Should specify minimum Python version
            assert ">=" in requires or ">" in requires, \
                f"{name}: requires-python should specify minimum version"
    
    def test_has_urls(self, package_info: tuple[str, Path, dict[str, Any]]):
        """Test that package has project URLs."""
        name, path, data = package_info
        project = data.get("project", {})
        
        if "urls" not in project:
            pytest.warns(UserWarning, match=f"{name}: Missing project URLs")
            return
        
        urls = project["urls"]
        # At least one URL should be present
        assert len(urls) > 0, f"{name}: No URLs specified"


class TestPackageStructure:
    """Test package directory structure."""
    
    @pytest.fixture(params=list(get_pyproject_paths()))
    def package_dir(self, request: pytest.FixtureRequest) -> tuple[str, Path]:
        """Fixture providing package name and directory."""
        name, path = request.param
        return name, path.parent
    
    def test_has_src_directory(self, package_dir: tuple[str, Path]):
        """Test that package has src directory or package directory."""
        name, pkg_dir = package_dir
        
        src_dir = pkg_dir / "src"
        # Either has src/ directory or has a package directory directly
        has_src = src_dir.exists() and src_dir.is_dir()
        has_package = any(
            d.is_dir() and (d / "__init__.py").exists()
            for d in pkg_dir.iterdir()
            if d.name not in ("src", "tests", "docs", ".git", "__pycache__")
        )
        
        assert has_src or has_package, f"{name}: No src/ directory or package directory found"
    
    def test_has_readme(self, package_dir: tuple[str, Path]):
        """Test that package has a README file."""
        name, pkg_dir = package_dir
        
        readme_patterns = ["README.md", "README.rst", "README.txt", "README"]
        has_readme = any((pkg_dir / pattern).exists() for pattern in readme_patterns)
        
        if not has_readme:
            pytest.warns(UserWarning, match=f"{name}: No README file found")
    
    def test_has_license(self, package_dir: tuple[str, Path]):
        """Test that package has a LICENSE file."""
        name, pkg_dir = package_dir
        
        license_patterns = ["LICENSE", "LICENSE.txt", "LICENSE.md", "COPYING"]
        has_license = any((pkg_dir / pattern).exists() for pattern in license_patterns)
        
        if not has_license:
            pytest.warns(UserWarning, match=f"{name}: No LICENSE file found")


class TestDependencies:
    """Test package dependencies."""
    
    @pytest.fixture(params=list(get_pyproject_paths()))
    def package_deps(self, request: pytest.FixtureRequest) -> tuple[str, list[str]]:
        """Fixture providing package name and dependencies."""
        name, path = request.param
        data = load_pyproject(path)
        project = data.get("project", {})
        deps = project.get("dependencies", [])
        return name, deps
    
    def test_dependencies_format(self, package_deps: tuple[str, list[str]]):
        """Test that dependencies are properly formatted."""
        name, deps = package_deps
        
        for dep in deps:
            # Dependencies should be strings
            assert isinstance(dep, str), f"{name}: Invalid dependency format: {dep}"
            
            # Should not have leading/trailing whitespace
            assert dep == dep.strip(), f"{name}: Dependency has whitespace: '{dep}'"
    
    def test_no_pinned_dependencies(self, package_deps: tuple[str, list[str]]):
        """Test that dependencies use version ranges, not exact pins (where appropriate)."""
        name, deps = package_deps
        
        for dep in deps:
            # Extract the version specifier
            if "==" in dep and ";" not in dep.split("==")[1]:
                # Exact pin without environment marker
                pytest.warns(
                    UserWarning,
                    match=f"{name}: Dependency '{dep}' uses exact pin, consider version range"
                )


class TestEntryPoints:
    """Test package entry points (console scripts)."""
    
    EXPECTED_ENTRY_POINTS: dict[str, list[str]] = {
        "HoloPatcher": ["holopatcher"],
        "KotorDiff": ["kotor-diff", "kotordiff"],
        "KOTORNasher": ["kotornasher"],
        "KitGenerator": ["kit-generator", "kitgenerator"],
        "GuiConverter": ["gui-converter"],
    }
    
    @pytest.fixture(params=list(get_pyproject_paths()))
    def package_entry_points(self, request: pytest.FixtureRequest) -> tuple[str, dict[str, Any]]:
        """Fixture providing package name and entry points."""
        name, path = request.param
        data = load_pyproject(path)
        project = data.get("project", {})
        scripts = project.get("scripts", {})
        return name, scripts
    
    def test_cli_tools_have_entry_points(self, package_entry_points: tuple[str, dict[str, Any]]):
        """Test that CLI tools define console_scripts entry points."""
        name, scripts = package_entry_points
        
        if name in self.EXPECTED_ENTRY_POINTS:
            expected = self.EXPECTED_ENTRY_POINTS[name]
            has_entry_point = any(ep in scripts for ep in expected)
            
            if not has_entry_point:
                pytest.warns(
                    UserWarning,
                    match=f"{name}: Expected console script entry point (one of {expected})"
                )

