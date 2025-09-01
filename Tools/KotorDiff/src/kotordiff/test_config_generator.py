"""
Test suite for the KOTOR Configuration Generator.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Add the PyKotor library to the path
if getattr(sys, "frozen", False) is False:
    def update_sys_path(path):
        working_dir = str(path)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.append(working_dir)

    pykotor_path = Path(__file__).parents[4] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        update_sys_path(pykotor_path.parent)

from kotordiff.config_generator import ConfigurationGenerator
from kotordiff.differ import DiffResult, FileChange, KotorDiffer
from kotordiff.generators.changes_ini import ChangesIniGenerator


class TestKotorDiffer(unittest.TestCase):
    """Test the KotorDiffer class."""
    
    def setUp(self):
        self.differ = KotorDiffer()
    
    def test_is_kotor_install_valid(self):
        """Test KOTOR installation detection with valid directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)
            (test_dir / "chitin.key").touch()
            
            self.assertTrue(self.differ._is_kotor_install(test_dir))
    
    def test_is_kotor_install_invalid(self):
        """Test KOTOR installation detection with invalid directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)
            # No chitin.key file
            
            self.assertFalse(self.differ._is_kotor_install(test_dir))
    
    def test_get_resource_type(self):
        """Test resource type detection."""
        self.assertEqual(self.differ._get_resource_type("test.gff"), "gff")
        self.assertEqual(self.differ._get_resource_type("file.2da"), "2da")
        self.assertEqual(self.differ._get_resource_type(Path("path/to/file.tlk")), "tlk")
    
    def test_gff_to_text(self):
        """Test GFF to text conversion."""
        # Mock GFF object
        mock_gff = Mock()
        mock_gff.root = "MockGFFRoot"
        
        result = self.differ._gff_to_text(mock_gff)
        self.assertIsInstance(result, str)
        self.assertEqual(result, "MockGFFRoot")
    
    def test_2da_to_text(self):
        """Test 2DA to text conversion."""
        # Mock 2DA object
        mock_2da = Mock()
        mock_2da.columns = ["col1", "col2"]
        mock_2da.rows = [{"col1": "value1", "col2": "value2"}]
        
        result = self.differ._2da_to_text(mock_2da)
        self.assertIsInstance(result, str)
        self.assertIn("2DA V2.b", result)
        self.assertIn("col1", result)
        self.assertIn("value1", result)


class TestFileChange(unittest.TestCase):
    """Test the FileChange class."""
    
    def test_file_change_creation(self):
        """Test FileChange object creation."""
        change = FileChange(
            path="test/file.gff",
            change_type="modified",
            resource_type="gff",
            old_content="old",
            new_content="new"
        )
        
        self.assertEqual(change.path, "test/file.gff")
        self.assertEqual(change.change_type, "modified")
        self.assertEqual(change.resource_type, "gff")
        self.assertEqual(change.old_content, "old")
        self.assertEqual(change.new_content, "new")


class TestDiffResult(unittest.TestCase):
    """Test the DiffResult class."""
    
    def setUp(self):
        self.result = DiffResult()
    
    def test_add_change(self):
        """Test adding changes to result."""
        change = FileChange("test.gff", "modified", "gff")
        self.result.add_change(change)
        
        self.assertEqual(len(self.result.changes), 1)
        self.assertEqual(self.result.changes[0], change)
    
    def test_add_error(self):
        """Test adding errors to result."""
        self.result.add_error("Test error")
        
        self.assertEqual(len(self.result.errors), 1)
        self.assertEqual(self.result.errors[0], "Test error")
    
    def test_get_changes_by_type(self):
        """Test filtering changes by type."""
        change1 = FileChange("test1.gff", "modified", "gff")
        change2 = FileChange("test2.gff", "added", "gff")
        change3 = FileChange("test3.gff", "modified", "gff")
        
        self.result.add_change(change1)
        self.result.add_change(change2)
        self.result.add_change(change3)
        
        modified_changes = self.result.get_changes_by_type("modified")
        self.assertEqual(len(modified_changes), 2)
        
        added_changes = self.result.get_changes_by_type("added")
        self.assertEqual(len(added_changes), 1)
    
    def test_get_changes_by_resource_type(self):
        """Test filtering changes by resource type."""
        change1 = FileChange("test1.gff", "modified", "gff")
        change2 = FileChange("test2.2da", "modified", "2da")
        change3 = FileChange("test3.gff", "added", "gff")
        
        self.result.add_change(change1)
        self.result.add_change(change2)
        self.result.add_change(change3)
        
        gff_changes = self.result.get_changes_by_resource_type("gff")
        self.assertEqual(len(gff_changes), 2)
        
        twoda_changes = self.result.get_changes_by_resource_type("2da")
        self.assertEqual(len(twoda_changes), 1)


class TestChangesIniGenerator(unittest.TestCase):
    """Test the ChangesIniGenerator class."""
    
    def setUp(self):
        self.generator = ChangesIniGenerator()
    
    def test_generate_from_diff_empty(self):
        """Test generating INI from empty diff result."""
        diff_result = DiffResult()
        result = self.generator.generate_from_diff(diff_result)
        
        self.assertIsInstance(result, str)
        self.assertIn("[Settings]", result)
        self.assertIn("WindowCaption=Generated Mod Configuration", result)
    
    def test_generate_from_diff_with_changes(self):
        """Test generating INI with actual changes."""
        diff_result = DiffResult()
        
        # Add a modified GFF file
        gff_change = FileChange(
            path="Override/test.utc",
            change_type="modified",
            resource_type="utc",
            diff_lines=["+ modified line"]
        )
        diff_result.add_change(gff_change)
        
        # Add an added file
        added_change = FileChange(
            path="Override/newfile.2da",
            change_type="added",
            resource_type="2da"
        )
        diff_result.add_change(added_change)
        
        result = self.generator.generate_from_diff(diff_result)
        
        self.assertIn("[Settings]", result)
        self.assertIn("[GFFList]", result)
        self.assertIn("[InstallList]", result)
        self.assertIn("test.utc", result)
        self.assertIn("newfile.2da", result)
    
    def test_process_added_file(self):
        """Test processing added file changes."""
        ini_sections = {}
        change = FileChange("Override/test.2da", "added", "2da")
        
        self.generator._process_added_file(change, ini_sections)
        
        self.assertIn("InstallList", ini_sections)
        self.assertIn("Override", ini_sections)
    
    def test_process_gff_change(self):
        """Test processing GFF file changes."""
        ini_sections = {}
        change = FileChange(
            path="Override/test.utc",
            change_type="modified",
            resource_type="utc",
            diff_lines=["+ some change"]
        )
        
        self.generator._process_gff_change(change, ini_sections)
        
        self.assertIn("GFFList", ini_sections)
        self.assertIn("test.utc", ini_sections)


class TestConfigurationGenerator(unittest.TestCase):
    """Test the ConfigurationGenerator class."""
    
    def setUp(self):
        self.generator = ConfigurationGenerator()
    
    @patch('kotordiff.config_generator.KotorDiffer')
    @patch('kotordiff.config_generator.ChangesIniGenerator')
    def test_generate_config(self, mock_ini_gen, mock_differ):
        """Test configuration generation."""
        # Mock the differ and generator
        mock_diff_result = DiffResult()
        mock_differ.return_value.diff_installations.return_value = mock_diff_result
        mock_ini_gen.return_value.generate_from_diff.return_value = "[Settings]\nTest=True"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path1 = Path(tmpdir) / "install1"
            path2 = Path(tmpdir) / "install2"
            output_path = Path(tmpdir) / "changes.ini"
            
            result = self.generator.generate_config(path1, path2, output_path)
            
            self.assertIsInstance(result, str)
            self.assertIn("[Settings]", result)
            mock_differ.return_value.diff_installations.assert_called_once_with(path1, path2)
            mock_ini_gen.return_value.generate_from_diff.assert_called_once_with(mock_diff_result)


if __name__ == "__main__":
    unittest.main()