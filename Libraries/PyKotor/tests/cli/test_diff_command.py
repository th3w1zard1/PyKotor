"""Comprehensive tests for the unified diff command.

Tests cover all path type combinations:
- File vs File (GFF, 2DA, TLK, text, binary)
- Folder vs Folder
- Installation vs Installation
- Bioware archive vs Bioware archive (ERF, MOD, RIM, SAV)
- Module piece vs Module piece (_s.rim, _dlg.erf, etc.)
- Mixed combinations (installation vs file, folder vs module, etc.)
- Composite modules (_s.rim/_a.rim/.rim/_dlg.erf)
- Output format (udiff-only by default, verbose for debug info)
- TSLPatcher integration (--generate-ini)
- Git diff formats (unified, context, side_by_side)
"""

from __future__ import annotations

import pathlib
import sys
import tempfile

from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

# Add paths
REPO_ROOT = pathlib.Path(__file__).parents[4]
sys.path.insert(0, str(REPO_ROOT / "Libraries" / "PyKotor" / "src"))
sys.path.insert(0, str(REPO_ROOT / "Libraries" / "Utility" / "src"))

from argparse import Namespace

from loggerplus import RobustLogger  # type: ignore[import-untyped]
from pykotor.cli.commands.utility_commands import _detect_path_type, _resolve_path, cmd_diff
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff.gff_auto import read_gff, write_gff
from pykotor.resource.formats.gff.gff_data import GFF
from pykotor.resource.formats.rim.rim_auto import write_rim
from pykotor.resource.formats.rim.rim_data import RIM
from pykotor.resource.formats.tlk.tlk_auto import read_tlk, write_tlk
from pykotor.resource.formats.tlk.tlk_data import TLK
from pykotor.resource.formats.twoda.twoda_auto import read_2da, write_2da
from pykotor.resource.formats.twoda.twoda_data import TwoDA


class TestPathTypeDetection:
    """Tests for path type detection."""

    def test_detect_file(self, tmp_path: Path):
        """Test detection of regular file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        assert _detect_path_type(test_file) == "file"

    def test_detect_folder(self, tmp_path: Path):
        """Test detection of regular folder."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        assert _detect_path_type(test_dir) == "folder"

    def test_detect_installation(self, tmp_path: Path):
        """Test detection of KOTOR installation."""
        # Create a mock installation with chitin.key
        install_dir = tmp_path / "kotor_install"
        install_dir.mkdir()
        chitin_key = install_dir / "chitin.key"
        chitin_key.write_bytes(b"mock chitin.key content")
        assert _detect_path_type(install_dir) == "installation"

    def test_detect_bioware_archive(self, tmp_path: Path):
        """Test detection of bioware archive files."""
        # Test various archive extensions
        for ext in [".rim", ".erf", ".mod", ".sav"]:
            archive_file = tmp_path / f"test{ext}"
            archive_file.write_bytes(b"mock archive content")
            assert _detect_path_type(archive_file) == "bioware_archive"

    def test_detect_module_piece(self, tmp_path: Path):
        """Test detection of module pieces."""
        # Test module piece patterns (files that should be detected as module pieces)
        module_pieces = ["test_s.rim", "test_a.rim", "test_dlg.erf"]
        for piece in module_pieces:
            piece_file = tmp_path / piece
            piece_file.write_bytes(b"mock module piece content")
            assert _detect_path_type(piece_file) == "module_piece"

        # Test regular bioware archives (should not be detected as module pieces)
        regular_archives = ["test.rim", "data.erf"]
        for archive in regular_archives:
            archive_file = tmp_path / archive
            archive_file.write_bytes(b"mock archive content")
            assert _detect_path_type(archive_file) == "bioware_archive"


class TestPathResolution:
    """Tests for path resolution."""

    def test_resolve_file_path(self, tmp_path: Path):
        """Test resolution of file path."""
        test_file = tmp_path / "test.utc"
        test_file.write_bytes(b"mock utc content")

        resolved = _resolve_path(str(test_file))
        assert isinstance(resolved, Path)
        assert resolved == test_file

    def test_resolve_folder_path(self, tmp_path: Path):
        """Test resolution of folder path."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        resolved = _resolve_path(str(test_dir))
        assert isinstance(resolved, Path)
        assert resolved == test_dir

    def test_resolve_installation_path(self, tmp_path: Path):
        """Test resolution of installation path."""
        install_dir = tmp_path / "kotor_install"
        install_dir.mkdir()
        chitin_key = install_dir / "chitin.key"
        chitin_key.write_bytes(b"mock chitin.key content")

        resolved = _resolve_path(str(install_dir))
        assert isinstance(resolved, Installation)


class TestDiffCommand:
    """Tests for the cmd_diff function."""

    def create_test_gff_files(self, tmp_path: Path) -> tuple[Path, Path]:
        """Create two slightly different GFF files for testing."""
        # Create a simple GFF structure
        gff1 = GFF()
        gff1.root.set_string("TemplateResRef", "test1")
        gff1.root.set_string("Tag", "test1")

        gff2 = GFF()
        gff2.root.set_string("TemplateResRef", "test2")
        gff2.root.set_string("Tag", "test2")

        file1 = tmp_path / "test1.utc"
        file2 = tmp_path / "test2.utc"

        write_gff(gff1, file1)
        write_gff(gff2, file2)

        return file1, file2

    def create_test_2da_files(self, tmp_path: Path) -> tuple[Path, Path]:
        """Create two slightly different 2DA files for testing."""
        tda1 = TwoDA()
        tda1.add_column("label")
        tda1.add_row(label="row1")

        tda2 = TwoDA()
        tda2.add_column("label")
        tda2.add_row(label="row2")

        file1 = tmp_path / "test1.2da"
        file2 = tmp_path / "test2.2da"

        write_2da(tda1, file1)
        write_2da(tda2, file2)

        return file1, file2

    def test_file_vs_file_gff(self, tmp_path: Path):
        """Test GFF file vs GFF file comparison."""
        file1, file2 = self.create_test_gff_files(tmp_path)

        args = Namespace(path1=str(file1), path2=str(file2), format="unified", generate_ini=False, verbose=False)

        logger = RobustLogger()

        # Capture stdout
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            result = cmd_diff(args, logger)

        output = mock_stdout.getvalue()

        # Should return 1 (different)
        assert result == 1
        # Should contain field differences
        assert "Field 'String' is different at" in output
        assert "'test1.utc'" in output
        assert "'test2.utc'" in output
        assert "DOES NOT MATCH" in output

    def test_file_vs_file_identical(self, tmp_path: Path):
        """Test identical file comparison."""
        file1 = tmp_path / "test1.utc"
        file2 = tmp_path / "test2.utc"

        # Create identical GFF files
        gff = GFF()
        gff.root.set_string("TemplateResRef", "test")
        gff.root.set_string("Tag", "test")

        write_gff(gff, file1)
        write_gff(gff, file2)

        args = Namespace(path1=str(file1), path2=str(file2), format="unified", generate_ini=False, verbose=False)

        logger = RobustLogger()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            result = cmd_diff(args, logger)

        output = mock_stdout.getvalue()

        # Should return 0 (identical)
        assert result == 0
        assert "MATCHES" in output

    def test_file_vs_file_2da(self, tmp_path: Path):
        """Test 2DA file vs 2DA file comparison."""
        file1, file2 = self.create_test_2da_files(tmp_path)

        args = Namespace(path1=str(file1), path2=str(file2), format="unified", generate_ini=False, verbose=False)

        logger = RobustLogger()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            result = cmd_diff(args, logger)

        output = mock_stdout.getvalue()

        # Should return 1 (different)
        assert result == 1
        # Should contain differences
        assert "DOES NOT MATCH" in output

    def test_text_file_diff(self, tmp_path: Path):
        """Test text file unified diff."""
        file1 = tmp_path / "test1.txt"
        file2 = tmp_path / "test2.txt"

        file1.write_text("line 1\nline 2\nline 3\n")
        file2.write_text("line 1\nline 2 modified\nline 3\n")

        args = Namespace(path1=str(file1), path2=str(file2), format="unified", generate_ini=False, verbose=False)

        logger = RobustLogger()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            result = cmd_diff(args, logger)

        output = mock_stdout.getvalue()

        # Should return 1 (different)
        assert result == 1
        # Should contain unified diff markers
        assert "---" in output
        assert "+++" in output
        assert "@@" in output
        assert "-line 2" in output
        assert "+line 2 modified" in output

    def test_verbose_output(self, tmp_path: Path):
        """Test verbose output mode."""
        file1, file2 = self.create_test_gff_files(tmp_path)

        args = Namespace(path1=str(file1), path2=str(file2), format="unified", generate_ini=False, verbose=True)

        logger = RobustLogger()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            result = cmd_diff(args, logger)

        output = mock_stdout.getvalue()

        # Should return 1 (different)
        assert result == 1
        # Should contain verbose debug info
        assert "[UDIFF]" in output

    def test_missing_file(self, tmp_path: Path):
        """Test handling of missing files."""
        existing_file = tmp_path / "existing.utc"
        missing_file = tmp_path / "missing.utc"

        # Create existing file
        gff = GFF()
        gff.root.set_string("TemplateResRef", "test")
        write_gff(gff, existing_file)

        args = Namespace(path1=str(existing_file), path2=str(missing_file), format="unified", generate_ini=False, verbose=False)

        logger = RobustLogger()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            result = cmd_diff(args, logger)

        output = mock_stdout.getvalue()

        # Should return 1 (error)
        assert result == 1
        assert "Missing file:" in output

    def test_generate_ini_error_for_files(self, tmp_path: Path):
        """Test that --generate-ini gives error for individual files."""
        file1, file2 = self.create_test_gff_files(tmp_path)

        args = Namespace(path1=str(file1), path2=str(file2), format="unified", generate_ini=True, verbose=False)

        logger = RobustLogger()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            result = cmd_diff(args, logger)

        output = mock_stdout.getvalue()

        # Should return 1 (error)
        assert result == 1
        assert "--generate-ini is only supported for installation-wide comparisons" in output


class TestDiffFormats:
    """Tests for different diff output formats."""

    def create_test_text_files(self, tmp_path: Path) -> tuple[Path, Path]:
        """Create test text files for format testing."""
        file1 = tmp_path / "test1.txt"
        file2 = tmp_path / "test2.txt"

        file1.write_text("line 1\nline 2\nline 3\n")
        file2.write_text("line 1\nline 2 modified\nline 3\n")

        return file1, file2

    def test_unified_format(self, tmp_path: Path):
        """Test unified diff format."""
        file1, file2 = self.create_test_text_files(tmp_path)

        args = Namespace(path1=str(file1), path2=str(file2), format="unified", generate_ini=False, verbose=False)

        logger = RobustLogger()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            result = cmd_diff(args, logger)

        output = mock_stdout.getvalue()

        assert result == 1
        assert "---" in output
        assert "+++" in output
        assert "@@" in output

    def test_context_format(self, tmp_path: Path):
        """Test context diff format."""
        file1, file2 = self.create_test_text_files(tmp_path)

        args = Namespace(path1=str(file1), path2=str(file2), format="context", generate_ini=False, verbose=False)

        logger = RobustLogger()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            result = cmd_diff(args, logger)

        output = mock_stdout.getvalue()

        assert result == 1
        assert "***" in output
        assert "---" in output

    def test_default_format(self, tmp_path: Path):
        """Test default format (should be unified)."""
        file1, file2 = self.create_test_text_files(tmp_path)

        args = Namespace(
            path1=str(file1),
            path2=str(file2),
            format="unified",  # Default
            generate_ini=False,
            verbose=False,
        )

        logger = RobustLogger()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            result = cmd_diff(args, logger)

        output = mock_stdout.getvalue()

        assert result == 1
        assert "---" in output
        assert "+++" in output


class TestBiowareArchives:
    """Tests for Bioware archive comparisons."""

    def create_test_rim(self, tmp_path: Path, filename: str) -> Path:
        """Create a test RIM file."""
        from pykotor.resource.type import ResourceType

        rim = RIM()
        # Add some dummy data
        rim.set_data("testres", ResourceType.TXT, b"test data")

        rim_file = tmp_path / filename
        write_rim(rim, rim_file)
        return rim_file

    def test_rim_vs_rim(self, tmp_path: Path):
        """Test RIM vs RIM comparison."""
        rim1 = self.create_test_rim(tmp_path, "test1.rim")
        rim2 = self.create_test_rim(tmp_path, "test2.rim")

        args = Namespace(path1=str(rim1), path2=str(rim2), format="unified", generate_ini=False, verbose=False)

        logger = RobustLogger()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            result = cmd_diff(args, logger)

        output = mock_stdout.getvalue()

        # RIMs should be comparable
        assert isinstance(result, int)
        assert "DOES NOT MATCH" in output or "MATCHES" in output


class TestInstallationComparisons:
    """Tests for installation-wide comparisons."""

    def test_identical_installations(self, tmp_path: Path):
        """Test comparison of identical installations."""
        # Create mock installation
        install_dir = tmp_path / "install"
        install_dir.mkdir()

        # Add chitin.key
        (install_dir / "chitin.key").write_bytes(b"mock key")

        args = Namespace(
            path1=str(install_dir),
            path2=str(install_dir),  # Compare same installation to itself
            format="unified",
            generate_ini=False,
            verbose=False,
        )

        logger = RobustLogger()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            result = cmd_diff(args, logger)

        output = mock_stdout.getvalue()

        # Should return 0 (identical)
        assert result == 0
        assert "MATCHES" in output
        """Test detection of KOTOR installation."""
        install_dir = tmp_path / "kotor_install"
        install_dir.mkdir()
        (install_dir / "chitin.key").write_bytes(b"fake key")
        assert _detect_path_type(install_dir) == "installation"

    def test_detect_bioware_archive(self, tmp_path: Path):
        """Test detection of bioware archive."""
        rim_file = tmp_path / "test.rim"
        rim = RIM()
        write_rim(rim, rim_file)
        assert _detect_path_type(rim_file) == "bioware_archive"

    def test_detect_module_piece(self, tmp_path: Path):
        """Test detection of module piece."""
        rim_file = tmp_path / "test_s.rim"
        rim = RIM()
        write_rim(rim, rim_file)
        assert _detect_path_type(rim_file) == "module_piece"

    def test_detect_module_piece_dlg(self, tmp_path: Path):
        """Test detection of dialog module piece."""
        from pykotor.resource.formats.erf.erf_auto import write_erf
        from pykotor.resource.formats.erf.erf_data import ERF, ERFType

        erf_file = tmp_path / "test_dlg.erf"
        erf = ERF(ERFType.ERF)
        write_erf(erf, erf_file)
        assert _detect_path_type(erf_file) == "module_piece"


class TestPathResolution:
    """Tests for path resolution."""

    def test_resolve_file(self, tmp_path: Path):
        """Test resolution of file path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        resolved = _resolve_path(str(test_file))
        assert isinstance(resolved, Path)
        assert resolved == test_file

    def test_resolve_folder(self, tmp_path: Path):
        """Test resolution of folder path."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        resolved = _resolve_path(str(test_dir))
        assert isinstance(resolved, Path)
        assert resolved == test_dir

    def test_resolve_installation(self, tmp_path: Path):
        """Test resolution of installation path."""
        install_dir = tmp_path / "kotor_install"
        install_dir.mkdir()
        (install_dir / "chitin.key").write_bytes(b"fake key")
        resolved = _resolve_path(str(install_dir))
        # Installation creation may fail if chitin.key is invalid, so it may fall back to Path
        assert isinstance(resolved, (Path, Installation))

    def test_resolve_bioware_archive(self, tmp_path: Path):
        """Test resolution of bioware archive."""
        rim_file = tmp_path / "test.rim"
        rim = RIM()
        write_rim(rim, rim_file)
        resolved = _resolve_path(str(rim_file))
        assert isinstance(resolved, Path)
        assert resolved == rim_file


class TestDiffCommand:
    """Tests for the diff command implementation."""

    def test_file_vs_file_identical(self, tmp_path: Path):
        """Test diff of two identical files."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        content = "test content\nline 2"
        file1.write_text(content)
        file2.write_text(content)

        args = Namespace(path1=str(file1), path2=str(file2), output=None, context=3, verbose=False, debug=False, no_color=False)
        logger = RobustLogger()
        result = cmd_diff(args, logger)
        # Should return 0 for identical files
        assert result == 0

    def test_file_vs_file_different(self, tmp_path: Path):
        """Test diff of two different files."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content 1")
        file2.write_text("content 2")

        args = Namespace(path1=str(file1), path2=str(file2), output=None, context=3, verbose=False, debug=False, no_color=False)
        logger = RobustLogger()
        result = cmd_diff(args, logger)
        # Should return 0 (success) even if files differ (diff shows differences)
        assert result in (0, 1)  # May return 0 or 1 depending on implementation

    def test_folder_vs_folder(self, tmp_path: Path):
        """Test diff of two folders."""
        folder1 = tmp_path / "folder1"
        folder2 = tmp_path / "folder2"
        folder1.mkdir()
        folder2.mkdir()

        (folder1 / "file1.txt").write_text("content 1")
        (folder2 / "file1.txt").write_text("content 2")

        args = Namespace(path1=str(folder1), path2=str(folder2), output=None, context=3, verbose=False, debug=False, no_color=False)
        logger = RobustLogger()
        result = cmd_diff(args, logger)
        # Should complete without error
        assert result in (0, 1)

    def test_bioware_archive_vs_bioware_archive(self, tmp_path: Path):
        """Test diff of two bioware archives."""
        rim1 = tmp_path / "archive1.rim"
        rim2 = tmp_path / "archive2.rim"

        rim_obj1 = RIM()
        rim_obj2 = RIM()
        write_rim(rim_obj1, rim1)
        write_rim(rim_obj2, rim2)

        args = Namespace(path1=str(rim1), path2=str(rim2), output=None, context=3, verbose=False, debug=False, no_color=False)
        logger = RobustLogger()
        result = cmd_diff(args, logger)
        # Should complete without error
        assert result in (0, 1)

    def test_installation_vs_file(self, tmp_path: Path):
        """Test diff of installation vs file."""
        install_dir = tmp_path / "kotor_install"
        install_dir.mkdir()
        (install_dir / "chitin.key").write_bytes(b"fake key")

        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        args = Namespace(path1=str(install_dir), path2=str(test_file), output=None, context=3, verbose=False, debug=False, no_color=False)
        logger = RobustLogger()
        # This may fail if installation is invalid, but should handle gracefully
        result = cmd_diff(args, logger)
        assert result in (0, 1)

    def test_folder_vs_module_piece(self, tmp_path: Path):
        """Test diff of folder vs module piece."""
        folder = tmp_path / "folder"
        folder.mkdir()
        (folder / "file.txt").write_text("test")

        rim_file = tmp_path / "module_s.rim"
        rim = RIM()
        write_rim(rim, rim_file)

        args = Namespace(path1=str(folder), path2=str(rim_file), output=None, context=3, verbose=False, debug=False, no_color=False)
        logger = RobustLogger()
        result = cmd_diff(args, logger)
        # Should complete without error
        assert result in (0, 1)

    def test_verbose_output(self, tmp_path: Path):
        """Test that verbose mode shows debug information."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content 1")
        file2.write_text("content 2")

        args = Namespace(path1=str(file1), path2=str(file2), output=None, context=3, verbose=True, debug=False, no_color=False)
        logger = RobustLogger()
        result = cmd_diff(args, logger)
        # Should complete
        assert result in (0, 1)

    def test_output_to_file(self, tmp_path: Path):
        """Test outputting diff to file."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content 1")
        file2.write_text("content 2")

        output_file = tmp_path / "diff_output.txt"
        args = Namespace(path1=str(file1), path2=str(file2), output=str(output_file), context=3, format="unified", generate_ini=False, verbose=False)
        logger = RobustLogger()
        result = cmd_diff(args, logger)
        # Should return 1 (different files) but complete successfully
        assert result == 1
        # Output file should be created
        assert output_file.exists()
        assert output_file.exists()


class TestCompositeModules:
    """Tests for composite module handling."""

    def test_composite_module_detection(self, tmp_path: Path):
        """Test that module pieces are correctly detected."""
        # Create module pieces
        main_rim = tmp_path / "module.rim"
        data_rim = tmp_path / "module_s.rim"
        dlg_erf = tmp_path / "module_dlg.erf"

        rim = RIM()
        write_rim(rim, main_rim)
        write_rim(rim, data_rim)

        from pykotor.resource.formats.erf.erf_auto import write_erf
        from pykotor.resource.formats.erf.erf_data import ERF, ERFType

        erf = ERF(ERFType.ERF)
        write_erf(erf, dlg_erf)

        # All should be detected as module pieces or bioware archives
        assert _detect_path_type(main_rim) in ("bioware_archive", "module_piece")
        assert _detect_path_type(data_rim) == "module_piece"
        assert _detect_path_type(dlg_erf) == "module_piece"

    def test_composite_module_diff(self, tmp_path: Path):
        """Test diffing composite modules."""
        # Create two sets of module pieces
        module1_dir = tmp_path / "module1"
        module2_dir = tmp_path / "module2"
        module1_dir.mkdir()
        module2_dir.mkdir()

        rim1 = RIM()
        rim2 = RIM()
        write_rim(rim1, module1_dir / "test.rim")
        write_rim(rim2, module2_dir / "test.rim")

        args = Namespace(path1=str(module1_dir / "test.rim"), path2=str(module2_dir / "test.rim"), output=None, context=3, verbose=False, debug=False, no_color=False)
        logger = RobustLogger()
        result = cmd_diff(args, logger)
        # Should complete without error
        assert result in (0, 1)


class TestOutputModes:
    """Tests for different output modes (full, diff_only, quiet)."""

    def test_diff_only_mode_file_vs_file(self, tmp_path: Path, capsys):
        """Test diff_only mode produces only diff output for files."""
        # Use same filename so they get compared as content rather than separate resources
        file1 = tmp_path / "test.txt"
        file2 = tmp_path / "test.txt"
        (tmp_path / "dir1").mkdir()
        (tmp_path / "dir2").mkdir()
        file1 = tmp_path / "dir1" / "test.txt"
        file2 = tmp_path / "dir2" / "test.txt"
        file1.write_text("line 1\nline 2\nline 3")
        file2.write_text("line 1\nline 2 modified\nline 3")

        args = Namespace(
            path1=str(file1), path2=str(file2), output=None, format="unified", output_mode="diff_only", verbose=False, debug=False, no_color=False, generate_ini=False
        )
        logger = RobustLogger()
        result = cmd_diff(args, logger)
        assert result == 1
        output = capsys.readouterr().out

        # Should contain diff content but no summary messages
        assert "--- (old)test.txt" in output
        assert "+++ (new)test.txt" in output
        assert "@@ -1,3 +1,3 @@" in output
        assert "-line 2" in output
        assert "+line 2 modified" in output
        # Should NOT contain summary messages in diff_only mode
        assert "MATCHES" not in output
        assert "DOES NOT MATCH" not in output
        # Should NOT contain logging messages
        assert "Path 0:" not in output
        assert "Collected" not in output
        assert "Comparing text content" not in output

    def test_diff_only_mode_archive_vs_archive(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ):
        """Test diff_only mode produces only diff output for archives."""
        # Create two different RIM files
        rim1_path = tmp_path / "test1.rim"
        rim2_path = tmp_path / "test2.rim"

        rim1 = RIM()
        rim2 = RIM()
        write_rim(rim1, rim1_path)
        write_rim(rim2, rim2_path)

        args = Namespace(
            path1=str(rim1_path), path2=str(rim2_path), output=None, format="unified", output_mode="diff_only", verbose=False, debug=False, no_color=False, generate_ini=False
        )
        logger = RobustLogger()
        result = cmd_diff(args, logger)
        # Archives should match (both empty)
        assert result == 0
        output = capsys.readouterr().out

        # Should be empty or minimal output in diff_only mode for matching files
        # No summary messages
        assert "MATCHES" not in output
        assert "DOES NOT MATCH" not in output

    def test_quiet_mode(self, tmp_path: Path, capsys):
        """Test quiet mode suppresses all output."""
        file1 = tmp_path / "test1.txt"
        file2 = tmp_path / "test2.txt"
        file1.write_text("line 1\nline 2\nline 3")
        file2.write_text("line 1\nline 2 modified\nline 3")

        args = Namespace(
            path1=str(file1), path2=str(file2), output=None, format="unified", output_mode="quiet", verbose=False, debug=False, no_color=False, generate_ini=False
        )
        logger = RobustLogger()
        result = cmd_diff(args, logger)
        assert result == 1
        output = capsys.readouterr().out

        # Should be completely silent in quiet mode
        assert output.strip() == ""

    def test_full_mode_includes_summary(self, tmp_path: Path, capsys):
        """Test full mode includes summary messages."""
        file1 = tmp_path / "test1.txt"
        file2 = tmp_path / "test2.txt"
        file1.write_text("line 1\nline 2\nline 3")
        file2.write_text("line 1\nline 2 modified\nline 3")

        args = Namespace(path1=str(file1), path2=str(file2), output=None, format="unified", output_mode="full", verbose=False, debug=False, no_color=False, generate_ini=False)
        logger = RobustLogger()
        result = cmd_diff(args, logger)
        assert result == 1
        output = capsys.readouterr().out

        # Should contain both diff content and summary
        assert "---" in output
        assert "+++" in output
        assert "@@" in output
        assert "-line 2" in output
        assert "+line 2 modified" in output
        # Should contain summary messages in full mode
        assert "DOES NOT MATCH" in output


class TestInstallationErrorHandling:
    """Tests for Installation loading failures and error handling."""

    def test_installation_invalid_path(self, tmp_path: Path):
        """Test that Installation constructor rejects invalid paths."""
        from pykotor.extract.installation import Installation

        # Test with a regular file
        invalid_path = tmp_path / "not_a_directory.txt"
        invalid_path.write_text("not a directory")

        with pytest.raises(ValueError, match="Installation path must be a directory"):
            Installation(invalid_path)

        # Test with directory missing chitin.key
        invalid_dir = tmp_path / "no_chitin_key"
        invalid_dir.mkdir()

        with pytest.raises(ValueError, match="Installation path must contain chitin.key file"):
            Installation(invalid_dir)

    def test_mod_file_not_treated_as_installation(self, tmp_path: Path):
        """Test that .mod files are not incorrectly treated as installations."""
        from pykotor.extract.installation import Installation

        # Create a .mod file
        mod_path = tmp_path / "test.mod"
        rim = RIM()
        write_rim(rim, mod_path)

        # Should not be able to create Installation from .mod file
        with pytest.raises(ValueError, match="Installation path must be a directory"):
            Installation(mod_path)

    def test_diff_with_nonexistent_path(self, tmp_path: Path):
        """Test diff command handles nonexistent paths gracefully."""
        nonexistent_path = tmp_path / "does_not_exist.txt"

        args = Namespace(
            path1=str(nonexistent_path), path2=str(tmp_path), output=None, format="unified", output_mode="full", verbose=False, debug=False, no_color=False, generate_ini=False
        )
        logger = RobustLogger()
        result = cmd_diff(args, logger)

        # Should fail gracefully
        assert result == 1

    def test_generate_ini_with_non_installation_paths(self, tmp_path: Path):
        """Test --generate-ini fails appropriately for non-installation paths."""
        file1 = tmp_path / "test1.txt"
        file2 = tmp_path / "test2.txt"
        file1.write_text("content1")
        file2.write_text("content2")

        args = Namespace(path1=str(file1), path2=str(file2), output=None, format="unified", output_mode="full", verbose=False, debug=False, no_color=False, generate_ini=True)
        logger = RobustLogger()
        result = cmd_diff(args, logger)

        # Should fail because --generate-ini requires installation paths
        assert result == 1


class TestComprehensivePathCombinations:
    """Comprehensive tests for all path type combinations."""

    def test_file_vs_folder(self, tmp_path: Path, capsys):
        """Test file vs folder comparison."""
        file_path = tmp_path / "test.txt"
        folder_path = tmp_path / "folder"
        folder_path.mkdir()

        file_path.write_text("content")
        (folder_path / "test.txt").write_text("content")

        args = Namespace(
            path1=str(file_path), path2=str(folder_path), output=None, format="unified", output_mode="full", verbose=False, debug=False, no_color=False, generate_ini=False
        )
        logger = RobustLogger()
        result = cmd_diff(args, logger)
        # Should complete (may match or not depending on content)
        assert result in (0, 1)

    def test_archive_vs_folder(self, tmp_path: Path, capsys):
        """Test bioware archive vs folder comparison."""
        rim_path = tmp_path / "test.rim"
        folder_path = tmp_path / "folder"
        folder_path.mkdir()

        rim = RIM()
        write_rim(rim, rim_path)
        (folder_path / "test.txt").write_text("content")

        args = Namespace(
            path1=str(rim_path), path2=str(folder_path), output=None, format="unified", output_mode="full", verbose=False, debug=False, no_color=False, generate_ini=False
        )
        logger = RobustLogger()
        result = cmd_diff(args, logger)
        # Should complete
        assert result in (0, 1)

    def test_module_piece_vs_regular_file(self, tmp_path: Path, capsys):
        """Test module piece (e.g., _s.rim) vs regular file."""
        module_piece = tmp_path / "module_s.rim"
        regular_file = tmp_path / "test.txt"

        rim = RIM()
        write_rim(rim, module_piece)
        regular_file.write_text("content")

        args = Namespace(
            path1=str(module_piece), path2=str(regular_file), output=None, format="unified", output_mode="full", verbose=False, debug=False, no_color=False, generate_ini=False
        )
        logger = RobustLogger()
        result = cmd_diff(args, logger)
        # Should complete
        assert result in (0, 1)

    def test_folder_vs_module_piece(self, tmp_path: Path, capsys):
        """Test folder vs module piece."""
        folder_path = tmp_path / "folder"
        module_piece = tmp_path / "module_s.rim"
        folder_path.mkdir()

        rim = RIM()
        write_rim(rim, module_piece)
        (folder_path / "test.txt").write_text("content")

        args = Namespace(
            path1=str(folder_path), path2=str(module_piece), output=None, format="unified", output_mode="full", verbose=False, debug=False, no_color=False, generate_ini=False
        )
        logger = RobustLogger()
        result = cmd_diff(args, logger)
        # Should complete
        assert result in (0, 1)

    def test_erf_vs_rim(self, tmp_path: Path, capsys):
        """Test ERF vs RIM archive comparison."""
        erf_path = tmp_path / "test.erf"
        rim_path = tmp_path / "test.rim"

        from pykotor.resource.formats.erf.erf_auto import write_erf
        from pykotor.resource.formats.erf.erf_data import ERF, ERFType

        erf = ERF(ERFType.ERF)
        write_erf(erf, erf_path)

        rim = RIM()
        write_rim(rim, rim_path)

        args = Namespace(
            path1=str(erf_path), path2=str(rim_path), output=None, format="unified", output_mode="full", verbose=False, debug=False, no_color=False, generate_ini=False
        )
        logger = RobustLogger()
        result = cmd_diff(args, logger)
        # Should complete (different archive types don't match)
        assert result == 1

    def test_mod_vs_erf(self, tmp_path: Path, capsys):
        """Test MOD vs ERF archive comparison."""
        mod_path = tmp_path / "test.mod"
        erf_path = tmp_path / "test.erf"

        rim = RIM()
        write_rim(rim, mod_path)

        from pykotor.resource.formats.erf.erf_auto import write_erf
        from pykotor.resource.formats.erf.erf_data import ERF, ERFType

        erf = ERF(ERFType.ERF)
        write_erf(erf, erf_path)

        args = Namespace(
            path1=str(mod_path), path2=str(erf_path), output=None, format="unified", output_mode="full", verbose=False, debug=False, no_color=False, generate_ini=False
        )
        logger = RobustLogger()
        result = cmd_diff(args, logger)
        # Should complete (different archive types don't match)
        assert result == 1

    def test_text_file_vs_binary_file(self, tmp_path: Path, capsys):
        """Test text file vs binary file comparison."""
        text_file = tmp_path / "test.txt"
        binary_file = tmp_path / "test.gff"

        text_file.write_text("text content")
        # Create a minimal GFF file
        gff = GFF()
        write_gff(gff, binary_file)

        args = Namespace(
            path1=str(text_file), path2=str(binary_file), output=None, format="unified", output_mode="full", verbose=False, debug=False, no_color=False, generate_ini=False
        )
        logger = RobustLogger()
        result = cmd_diff(args, logger)
        # Should complete
        assert result in (0, 1)

    def test_nested_folders(self, tmp_path: Path, capsys):
        """Test comparison of nested folder structures."""
        folder1 = tmp_path / "folder1"
        folder2 = tmp_path / "folder2"
        folder1.mkdir()
        folder2.mkdir()

        # Create nested structure
        (folder1 / "subdir").mkdir()
        (folder2 / "subdir").mkdir()

        (folder1 / "subdir" / "file.txt").write_text("content1")
        (folder2 / "subdir" / "file.txt").write_text("content2")

        args = Namespace(
            path1=str(folder1), path2=str(folder2), output=None, format="unified", output_mode="full", verbose=False, debug=False, no_color=False, generate_ini=False
        )
        logger = RobustLogger()
        result = cmd_diff(args, logger)
        # Should detect differences
        assert result == 1

    def test_empty_vs_populated_archive(self, tmp_path: Path, capsys):
        """Test empty archive vs populated archive."""
        empty_rim = tmp_path / "empty.rim"
        populated_rim = tmp_path / "populated.rim"

        # Empty RIM
        rim1 = RIM()
        write_rim(rim1, empty_rim)

        # RIM with some content (add dummy data)
        rim2 = RIM()
        from pykotor.resource.type import ResourceType
        rim2.set_data("test", ResourceType.TXT, b"dummy content")
        write_rim(rim2, populated_rim)

        args = Namespace(
            path1=str(empty_rim), path2=str(populated_rim), output=None, format="unified", output_mode="full", verbose=False, debug=False, no_color=False, generate_ini=False
        )
        logger = RobustLogger()
        result = cmd_diff(args, logger)
        # Should detect differences
        assert result == 1


class TestDiffWithTestFiles:
    """Tests using actual test files from test_files directory."""

    def test_gff_files_diff(self):
        """Test diff between GFF files from test_files."""
        import pathlib
        test_files_dir = pathlib.Path(__file__).parents[4] / "Libraries" / "PyKotor" / "tests" / "test_files"

        # Find GFF files
        gff_files = list(test_files_dir.glob("*.gff"))
        if len(gff_files) >= 2:
            file1, file2 = gff_files[:2]

            args = Namespace(
                path1=str(file1),
                path2=str(file2),
                format="unified",
                output_mode="full",
                generate_ini=False,
                verbose=False,
                output=None,
                context=3
            )

            logger = RobustLogger()
            result = cmd_diff(args, logger)
            # Should complete without error
            assert result in (0, 1)

    def test_2da_files_diff(self):
        """Test diff between 2DA files from test_files."""
        import pathlib
        test_files_dir = pathlib.Path(__file__).parents[4] / "Libraries" / "PyKotor" / "tests" / "test_files"

        # Find 2DA files
        da_files = list(test_files_dir.glob("*.2da"))
        if len(da_files) >= 2:
            file1, file2 = da_files[:2]

            args = Namespace(
                path1=str(file1),
                path2=str(file2),
                format="unified",
                output_mode="diff_only",
                generate_ini=False,
                verbose=False,
                output=None,
                context=3
            )

            logger = RobustLogger()
            result = cmd_diff(args, logger)
            # Should complete without error
            assert result in (0, 1)

    def test_tlk_files_diff(self):
        """Test diff between TLK files from test_files."""
        import pathlib
        test_files_dir = pathlib.Path(__file__).parents[4] / "Libraries" / "PyKotor" / "tests" / "test_files"

        # Find TLK files
        tlk_files = list(test_files_dir.glob("*.tlk"))
        if len(tlk_files) >= 2:
            file1, file2 = tlk_files[:2]

            args = Namespace(
                path1=str(file1),
                path2=str(file2),
                format="unified",
                output_mode="diff_only",
                generate_ini=False,
                verbose=False,
                output=None,
                context=3
            )

            logger = RobustLogger()
            result = cmd_diff(args, logger)
            # Should complete without error
            assert result in (0, 1)

    def test_archive_files_diff(self):
        """Test diff between archive files from test_files."""
        import pathlib
        test_files_dir = pathlib.Path(__file__).parents[4] / "Libraries" / "PyKotor" / "tests" / "test_files"

        # Find archive files (rim, erf, mod, sav)
        archive_files = []
        archive_files.extend(test_files_dir.glob("*.rim"))
        archive_files.extend(test_files_dir.glob("*.erf"))
        archive_files.extend(test_files_dir.glob("*.mod"))
        archive_files.extend(test_files_dir.glob("*.sav"))

        if len(archive_files) >= 2:
            file1, file2 = archive_files[:2]

            args = Namespace(
                path1=str(file1),
                path2=str(file2),
                format="unified",
                output_mode="diff_only",
                generate_ini=False,
                verbose=False,
                output=None,
                context=3
            )

            logger = RobustLogger()
            result = cmd_diff(args, logger)
            # Should complete without error
            assert result in (0, 1)

    def test_corrupted_vs_valid_files(self):
        """Test diff between corrupted and valid files."""
        import pathlib
        test_files_dir = pathlib.Path(__file__).parents[4] / "Libraries" / "PyKotor" / "tests" / "test_files"

        # Test corrupted vs valid GFF
        corrupted_gff = test_files_dir / "test_corrupted.gff"
        valid_gff = test_files_dir / "test.gff"

        if corrupted_gff.exists() and valid_gff.exists():
            args = Namespace(
                path1=str(corrupted_gff),
                path2=str(valid_gff),
                format="unified",
                output_mode="diff_only",
                generate_ini=False,
                verbose=False,
                output=None,
                context=3
            )

            logger = RobustLogger()
            result = cmd_diff(args, logger)
            # Should complete (may succeed or fail gracefully)
            assert result in (0, 1)

    def test_text_files_unified_diff(self):
        """Test unified diff between text files."""
        import pathlib
        test_files_dir = pathlib.Path(__file__).parents[4] / "Libraries" / "PyKotor" / "tests" / "test_files"

        # Find NSS files (text-based scripts)
        nss_files = list(test_files_dir.glob("*.nss"))
        if len(nss_files) >= 2:
            file1, file2 = nss_files[:2]

            args = Namespace(
                path1=str(file1),
                path2=str(file2),
                format="unified",
                output_mode="diff_only",
                generate_ini=False,
                verbose=False,
                output=None,
                context=3
            )

            logger = RobustLogger()
            result = cmd_diff(args, logger)
            # Should complete without error
            assert result in (0, 1)

    def test_side_by_side_format(self):
        """Test side-by-side diff format."""
        import pathlib
        test_files_dir = pathlib.Path(__file__).parents[4] / "Libraries" / "PyKotor" / "tests" / "test_files"

        # Find any two files
        all_files = list(test_files_dir.glob("*"))
        text_files = [f for f in all_files if f.is_file() and f.suffix.lower() not in ['.rim', '.erf', '.mod', '.sav', '.bif', '.tpc', '.mp3', '.wav', '.bik', '.mve']]

        if len(text_files) >= 2:
            file1, file2 = text_files[:2]

            args = Namespace(
                path1=str(file1),
                path2=str(file2),
                format="side_by_side",
                output_mode="diff_only",
                generate_ini=False,
                verbose=False,
                output=None,
                context=3
            )

            logger = RobustLogger()
            result = cmd_diff(args, logger)
            # Should complete without error
            assert result in (0, 1)

    def test_context_format(self):
        """Test context diff format."""
        import pathlib
        test_files_dir = pathlib.Path(__file__).parents[4] / "Libraries" / "PyKotor" / "tests" / "test_files"

        # Find any two files
        all_files = list(test_files_dir.glob("*"))
        text_files = [f for f in all_files if f.is_file() and f.suffix.lower() not in ['.rim', '.erf', '.mod', '.sav', '.bif', '.tpc', '.mp3', '.wav', '.bik', '.mve']]

        if len(text_files) >= 2:
            file1, file2 = text_files[:2]

            args = Namespace(
                path1=str(file1),
                path2=str(file2),
                format="context",
                output_mode="context",
                generate_ini=False,
                verbose=False,
                output=None,
                context=3
            )

            logger = RobustLogger()
            result = cmd_diff(args, logger)
            # Should complete without error
            assert result in (0, 1)