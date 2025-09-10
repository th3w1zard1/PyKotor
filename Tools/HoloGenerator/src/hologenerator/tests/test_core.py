"""
Test suite for HoloGenerator core functionality.
"""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from hologenerator.core.differ import KotorDiffer, DiffResult, FileChange
from hologenerator.core.changes_ini import ChangesIniGenerator
from hologenerator.core.generator import ConfigurationGenerator


class TestKotorDiffer(unittest.TestCase):
    """Test cases for the KotorDiffer class."""
    
    def setUp(self):
        self.differ = KotorDiffer()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """Test KotorDiffer initialization."""
        self.assertIsInstance(self.differ.gff_types, set)
        self.assertGreater(len(self.differ.gff_types), 0)
    
    def test_is_kotor_install_valid(self):
        """Test valid KOTOR installation detection."""
        kotor_dir = self.temp_path / "kotor"
        kotor_dir.mkdir()
        (kotor_dir / "chitin.key").touch()
        
        self.assertTrue(self.differ._is_kotor_install(kotor_dir))
    
    def test_is_kotor_install_invalid(self):
        """Test invalid KOTOR installation detection."""
        invalid_dir = self.temp_path / "invalid"
        invalid_dir.mkdir()
        
        self.assertFalse(self.differ._is_kotor_install(invalid_dir))


class TestChangesIniGenerator(unittest.TestCase):
    """Test cases for the ChangesIniGenerator class."""
    
    def setUp(self):
        self.generator = ChangesIniGenerator()
    
    def test_init(self):
        """Test ChangesIniGenerator initialization."""
        self.assertIsInstance(self.generator.gff_extensions, set)
        self.assertGreater(len(self.generator.gff_extensions), 0)
    
    def test_generate_empty_diff(self):
        """Test generating config from empty diff result."""
        diff_result = DiffResult()
        
        config = self.generator.generate_from_diff(diff_result)
        
        self.assertIn("[Settings]", config)
        self.assertIn("WindowCaption=Generated Mod Configuration", config)


class TestConfigurationGenerator(unittest.TestCase):
    """Test cases for the ConfigurationGenerator class."""
    
    def setUp(self):
        self.generator = ConfigurationGenerator()
    
    def test_init(self):
        """Test ConfigurationGenerator initialization."""
        self.assertIsNotNone(self.generator.differ)
        self.assertIsNotNone(self.generator.generator)


if __name__ == '__main__':
    unittest.main()