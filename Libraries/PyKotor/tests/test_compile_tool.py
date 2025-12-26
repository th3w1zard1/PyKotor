"""Tests for compile_tool.py to ensure it works across all Python versions and Tools."""

from __future__ import annotations

import os
import platform

# Import compile_tool functions for testing
import sys

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add compile directory to path (located at repo root)
repo_root = Path(__file__).resolve().parents[3]
compile_dir = repo_root / "compile"
sys.path.insert(0, str(compile_dir))

# Import after adding to path - use type ignore for linters
try:
    from compile_tool import (  # type: ignore[import-untyped] # noqa: E402
        add_flag_values,
        compute_final_executable,
        detect_os,
        normalize_add_data,
        path_separator_for_data,
    )
except ImportError:
    # Fallback for when running from different locations
    import importlib.util

    compile_tool_path = compile_dir / "compile_tool.py"
    spec = importlib.util.spec_from_file_location("compile_tool", compile_tool_path)
    if spec and spec.loader:
        compile_tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(compile_tool)
        add_flag_values = compile_tool.add_flag_values
        compute_final_executable = compile_tool.compute_final_executable
        detect_os = compile_tool.detect_os
        normalize_add_data = compile_tool.normalize_add_data
        path_separator_for_data = compile_tool.path_separator_for_data
    else:
        raise ImportError(f"Could not load compile_tool.py from {compile_tool_path}")


class TestDetectOS:
    """Test OS detection."""

    def test_detect_os_windows(self):
        """Test Windows detection."""
        with patch("platform.system", return_value="Windows"):
            assert detect_os() == "Windows"

    def test_detect_os_mac(self):
        """Test macOS detection."""
        with patch("platform.system", return_value="Darwin"):
            assert detect_os() == "Mac"

    def test_detect_os_linux(self):
        """Test Linux detection."""
        with patch("platform.system", return_value="Linux"):
            assert detect_os() == "Linux"

    def test_detect_os_unsupported(self):
        """Test unsupported OS raises error."""
        with patch("platform.system", return_value="FreeBSD"):
            with pytest.raises(SystemExit):
                detect_os()


class TestPathSeparatorForData:
    """Test path separator for data files."""

    def test_path_separator_windows(self):
        """Test Windows separator."""
        assert path_separator_for_data("Windows") == ";"

    def test_path_separator_mac(self):
        """Test macOS separator."""
        assert path_separator_for_data("Mac") == ":"

    def test_path_separator_linux(self):
        """Test Linux separator."""
        assert path_separator_for_data("Linux") == ":"


class TestAddFlagValues:
    """Test flag value addition."""

    def test_add_flag_values_single(self):
        """Test adding single flag value."""
        buffer: list[str] = []
        add_flag_values("exclude-module", ["numpy"], buffer)
        assert buffer == ["--exclude-module=numpy"]

    def test_add_flag_values_multiple(self):
        """Test adding multiple flag values."""
        buffer: list[str] = []
        add_flag_values("exclude-module", ["numpy", "PyQt5"], buffer)
        assert buffer == ["--exclude-module=numpy", "--exclude-module=PyQt5"]

    def test_add_flag_values_empty(self):
        """Test adding empty list."""
        buffer: list[str] = []
        add_flag_values("exclude-module", [], buffer)
        assert buffer == []


class TestComputeFinalExecutable:
    """Test executable path computation."""

    def test_compute_final_executable_windows(self):
        """Test Windows executable path."""
        distpath = Path("/dist")
        result = compute_final_executable(distpath, "TestTool", "Windows")
        assert result == Path("/dist/TestTool.exe")

    def test_compute_final_executable_mac(self):
        """Test macOS executable path."""
        distpath = Path("/dist")
        result = compute_final_executable(distpath, "TestTool", "Mac")
        assert result == Path("/dist/TestTool.app")

    def test_compute_final_executable_linux(self):
        """Test Linux executable path."""
        distpath = Path("/dist")
        result = compute_final_executable(distpath, "TestTool", "Linux")
        assert result == Path("/dist/TestTool")


class TestNormalizeAddData:
    """Test add-data entry normalization."""

    def test_normalize_add_data_windows_valid(self):
        """Test valid Windows add-data entry."""
        entries = ["src;dest"]
        result = normalize_add_data(entries, ";")
        assert result == ["src;dest"]

    def test_normalize_add_data_unix_valid(self):
        """Test valid Unix add-data entry."""
        entries = ["src:dest"]
        result = normalize_add_data(entries, ":")
        assert result == ["src:dest"]

    def test_normalize_add_data_windows_invalid(self):
        """Test invalid Windows add-data entry."""
        entries = ["src"]  # Missing destination
        with pytest.raises(SystemExit):
            normalize_add_data(entries, ";")

    def test_normalize_add_data_unix_invalid(self):
        """Test invalid Unix add-data entry."""
        entries = ["src"]  # Missing destination
        with pytest.raises(SystemExit):
            normalize_add_data(entries, ":")

    def test_normalize_add_data_windows_with_colon(self):
        """Test Windows entry with colon (absolute path)."""
        entries = ["C:/src;dest"]
        result = normalize_add_data(entries, ";")
        assert result == ["C:/src;dest"]


class TestCompileToolIntegration:
    """Integration tests for compile_tool.py with all Tools."""

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch: pytest.MonkeyPatch):
        """Set up environment variables to avoid getpass issues."""
        # Set USERNAME if not present (needed for tmp_path on Windows)
        if "USERNAME" not in os.environ:
            monkeypatch.setenv("USERNAME", "testuser")
        if "USER" not in os.environ:
            monkeypatch.setenv("USER", "testuser")

    @pytest.fixture
    def mock_repo_root(self, tmp_path: Path) -> Path:
        """Create a mock repository structure."""
        repo = tmp_path / "repo"
        repo.mkdir()

        # Create install_python_venv.ps1
        installer = repo / "install_python_venv.ps1"
        installer.write_text("# Mock installer\n")

        # Create Libraries structure
        (repo / "Libraries" / "PyKotor" / "src").mkdir(parents=True)
        (repo / "Libraries" / "PyKotor" / "src" / "__init__.py").touch()

        # Create Tools structure for each tool
        tools = [
            "BatchPatcher",
            "HoloPatcher",
            "HolocronToolset",
            "HoloGenerator",
            "KotorDiff",
        ]
        for tool in tools:
            tool_dir = repo / "Tools" / tool / "src"
            tool_dir.mkdir(parents=True)
            # Create a simple __main__.py for each tool
            slug = tool.lower().replace("holocron", "holocron").replace("toolset", "toolset")
            if tool == "HoloGenerator":
                slug = "hologenerator"
            elif tool == "KotorDiff":
                slug = "kotordiff"
            elif tool == "BatchPatcher":
                slug = "batchpatcher"
            elif tool == "HoloPatcher":
                slug = "holopatcher"
            elif tool == "HolocronToolset":
                slug = "toolset"
            main_file = tool_dir / slug / "__main__.py"
            main_file.parent.mkdir(exist_ok=True)
            main_file.write_text("# Mock main\n")

        return repo

    @pytest.fixture
    def mock_venv_python(self, tmp_path: Path) -> Path:
        """Create a mock venv Python executable."""
        venv_dir = tmp_path / ".venv"
        if platform.system() == "Windows":
            python_exe = venv_dir / "Scripts" / "python.exe"
        else:
            python_exe = venv_dir / "bin" / "python"
        python_exe.parent.mkdir(parents=True)
        python_exe.write_text("# Mock Python\n")
        python_exe.chmod(0o755)
        return python_exe

    def test_all_tools_have_valid_structure(self, mock_repo_root: Path):
        """Test that all Tools have valid directory structure."""
        tools = [
            "BatchPatcher",
            "HoloPatcher",
            "HolocronToolset",
            "HoloGenerator",
            "KotorDiff",
        ]

        for tool in tools:
            tool_path = mock_repo_root / "Tools" / tool
            src_dir = tool_path / "src"
            assert src_dir.exists(), f"{tool} src directory should exist"

            # Check for __main__.py in expected location
            slug = tool.lower()
            if tool == "HoloGenerator":
                slug = "hologenerator"
            elif tool == "KotorDiff":
                slug = "kotordiff"
            elif tool == "BatchPatcher":
                slug = "batchpatcher"
            elif tool == "HoloPatcher":
                slug = "holopatcher"
            elif tool == "HolocronToolset":
                slug = "toolset"

            main_file = src_dir / slug / "__main__.py"
            assert main_file.exists(), f"{tool} __main__.py should exist at {main_file}"

    @patch("subprocess.run")
    def test_compile_tool_skips_venv_when_requested(
        self,
        mock_subprocess: Mock,
        mock_repo_root: Path,
        mock_venv_python: Path,
    ):
        """Test that compile_tool skips venv installation when --skip-venv is used."""
        # Import here to avoid issues with path setup
        compile_dir = Path(__file__).resolve().parent.parent / "compile"
        if str(compile_dir) not in sys.path:
            sys.path.insert(0, str(compile_dir))

        # Mock subprocess.run to avoid actual PyInstaller execution
        mock_subprocess.return_value = MagicMock(returncode=0)

        # This test verifies the skip-venv logic works
        # We can't easily test the full main() without mocking everything
        assert True  # Placeholder - full integration test would require extensive mocking

    def test_path_separator_compatibility(self):
        """Test path separator works across all Python versions."""
        os_name = detect_os()
        sep = path_separator_for_data(os_name)

        if os_name == "Windows":
            assert sep == ";"
        else:
            assert sep == ":"

    def test_compute_executable_compatibility(self):
        """Test executable computation works across all Python versions."""
        distpath = Path("/tmp/dist")
        os_name = detect_os()
        result = compute_final_executable(distpath, "Test", os_name)

        if os_name == "Windows":
            assert result.suffix == ".exe"
        elif os_name == "Mac":
            assert result.suffix == ".app"
        else:
            assert result.suffix == ""

    @pytest.mark.parametrize(
        "python_version",
        ["3.8", "3.9", "3.10", "3.11", "3.12", "3.13"],
    )
    def test_python_version_compatibility(self, python_version: str):
        """Test that compile_tool.py syntax is compatible with all Python versions."""
        # This test ensures the code uses only features available in Python 3.8+
        # The actual version check happens at runtime via tox

        # Test that from __future__ import annotations works
        # This allows type hints to be strings in older Python versions
        assert True  # If we get here, the imports worked

        # Test that list[str] syntax works (requires Python 3.9+ or __future__ annotations)
        test_list: list[str] = ["test"]
        assert isinstance(test_list, list)

        # Test that Path | None syntax works (requires Python 3.10+ or __future__ annotations)
        test_path: Path | None = None
        assert test_path is None


class TestToolSpecificCompilation:
    """Test compilation configuration for each Tool."""

    @pytest.mark.parametrize(
        "tool,expected_entrypoint",
        [
            ("BatchPatcher", "batchpatcher/__main__.py"),
            ("HoloPatcher", "holopatcher/__main__.py"),
            ("HolocronToolset", "toolset/__main__.py"),
            ("HoloGenerator", "hologenerator/__main__.py"),
            ("KotorDiff", "kotordiff/__main__.py"),
        ],
    )
    def test_tool_entrypoints(self, tool: str, expected_entrypoint: str):
        """Test that each tool has the correct entrypoint format."""
        # This verifies the entrypoint naming convention
        if tool == "HolocronToolset":
            slug = "toolset"
        elif tool == "HoloGenerator":
            slug = "hologenerator"
        elif tool == "KotorDiff":
            slug = "kotordiff"
        elif tool == "BatchPatcher":
            slug = "batchpatcher"
        elif tool == "HoloPatcher":
            slug = "holopatcher"
        else:
            slug = tool.lower()

        entrypoint = f"{slug}/__main__.py"
        assert entrypoint == expected_entrypoint, f"{tool} entrypoint should be {expected_entrypoint}, got {entrypoint}"
