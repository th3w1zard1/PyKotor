#!/usr/bin/env python3
"""Additional tests for CaseAwarePath based on pathlib2 compatibility and cross-version testing."""

import os
import pathlib
import sys
import tempfile
import unittest
from pathlib import PurePath

# Add the path to the PyKotor src
THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "PyKotor", "src")

def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.insert(0, working_dir)

if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)

from pykotor.tools.path import CaseAwarePath


class TestCaseAwarePathPathlib2Compat(unittest.TestCase):
    """Test CaseAwarePath compatibility with pathlib2 patterns and cross-version functionality."""

    def test_python_version_compatibility(self):
        """Test that CaseAwarePath works on the current Python version."""
        path = CaseAwarePath("/tmp/test")
        self.assertIsInstance(path, CaseAwarePath)
        self.assertTrue(hasattr(path, '__fspath__'))
        
        # Test that we can convert to string
        self.assertIsInstance(str(path), str)
        self.assertIsInstance(os.fspath(path), str)

    def test_pathlib2_like_behavior(self):
        """Test that CaseAwarePath behaves like pathlib2 classes."""
        path = CaseAwarePath("test/path")
        
        # Test basic pathlib-like properties
        self.assertTrue(hasattr(path, 'parts'))
        self.assertTrue(hasattr(path, 'name'))
        self.assertTrue(hasattr(path, 'suffix'))
        self.assertTrue(hasattr(path, 'stem'))
        self.assertTrue(hasattr(path, 'parent'))
        
        # Test parts decomposition
        self.assertEqual(path.parts, ('test', 'path'))
        self.assertEqual(path.name, 'path')
        self.assertEqual(path.parent.name, 'test')

    def test_case_insensitive_path_operations(self):
        """Test case-insensitive path operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files with different cases
            actual_file = CaseAwarePath(tmpdir) / "TestFile.TXT"
            actual_file.touch()
            
            # Test various case combinations
            test_cases = [
                "testfile.txt",
                "TESTFILE.TXT", 
                "TestFile.txt",
                "testFile.TXT"
            ]
            
            for case_variant in test_cases:
                variant_path = CaseAwarePath(tmpdir) / case_variant
                self.assertTrue(variant_path.exists(), 
                              f"Case variant {case_variant} should exist")
                
                # Test case-insensitive equality
                self.assertEqual(variant_path, actual_file,
                               f"Case variant {case_variant} should equal actual file")

    def test_cross_platform_path_normalization(self):
        """Test that path normalization works correctly across platforms."""
        # Test Windows-style paths on any platform
        win_path = CaseAwarePath("C:\\Users\\Test\\Documents\\file.txt")
        self.assertIsInstance(str(win_path), str)
        
        # Test Unix-style paths on any platform
        unix_path = CaseAwarePath("/home/test/documents/file.txt")
        self.assertIsInstance(str(unix_path), str)
        
        # Test mixed separators
        mixed_path = CaseAwarePath("test\\path/to\\file.txt")
        self.assertIsInstance(str(mixed_path), str)
        
        # Test that name property works correctly
        self.assertEqual(win_path.name, "file.txt")
        self.assertEqual(unix_path.name, "file.txt")
        self.assertEqual(mixed_path.name, "file.txt")

    def test_pathlib_compatibility_methods(self):
        """Test that CaseAwarePath implements key pathlib methods."""
        path = CaseAwarePath("test/path/file.txt")
        
        # Test joinpath
        joined = path.joinpath("subdir", "file2.txt")
        self.assertIsInstance(joined, CaseAwarePath)
        
        # Test with_name
        renamed = path.with_name("newfile.txt")
        self.assertEqual(renamed.name, "newfile.txt")
        
        # Test with_suffix
        new_suffix = path.with_suffix(".py")
        self.assertEqual(new_suffix.suffix, ".py")
        
        # Test parents
        self.assertTrue(hasattr(path, 'parents'))
        self.assertTrue(len(list(path.parents)) > 0)

    def test_relative_to_compatibility(self):
        """Test relative_to method compatibility."""
        base = CaseAwarePath("/home/user")
        full = CaseAwarePath("/home/user/documents/file.txt")
        
        relative = full.relative_to(base)
        
        # Test that result is pathlib-compatible
        self.assertTrue(hasattr(relative, '__fspath__'))
        self.assertIsInstance(str(relative), str)

    def test_case_insensitive_hashing(self):
        """Test that case-insensitive hashing works correctly."""
        path1 = CaseAwarePath("Test\\PATH\\File.TXT")
        path2 = CaseAwarePath("test\\path\\file.txt")
        path3 = CaseAwarePath("TEST\\PATH\\FILE.TXT")
        
        # All should have the same hash
        self.assertEqual(hash(path1), hash(path2))
        self.assertEqual(hash(path2), hash(path3))
        
        # All should be equal
        self.assertEqual(path1, path2)
        self.assertEqual(path2, path3)
        
        # Test in a set (should only contain one element)
        path_set = {path1, path2, path3}
        self.assertEqual(len(path_set), 1)

    def test_pathlib2_slots_compatibility(self):
        """Test that CaseAwarePath doesn't have __slots__ conflicts."""
        path = CaseAwarePath("test")
        
        # This should not raise an error about __slots__ conflicts
        try:
            # Try to access various attributes that might be affected by __slots__
            _ = path.parts
            _ = path.name
            _ = str(path)
            _ = path.parent
            success = True
        except (AttributeError, RecursionError) as e:
            success = False
            self.fail(f"__slots__ compatibility issue: {e}")
            
        self.assertTrue(success, "CaseAwarePath should be compatible with pathlib2 __slots__")

    def test_string_comparison_edge_cases(self):
        """Test edge cases for string comparison in CaseAwarePath."""
        path = CaseAwarePath("Test\\File.txt")
        
        # Test various string formats
        self.assertTrue(path == "test/file.txt")
        self.assertTrue(path == "Test\\File.txt")
        self.assertTrue(path == "TEST/FILE.TXT")
        
        # Test that non-matching strings return False
        self.assertFalse(path == "different/file.txt")
        self.assertFalse(path == "test/file.py")

    @unittest.skipIf(os.name == "nt", "Case-sensitive test only relevant on Unix-like systems")
    def test_case_sensitive_filesystem_behavior(self):
        """Test behavior on case-sensitive filesystems."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file with specific case
            actual_file = pathlib.Path(tmpdir) / "TestFile.txt"
            actual_file.touch()
            
            # Test that CaseAwarePath finds it with different case
            case_aware = CaseAwarePath(tmpdir) / "testfile.TXT"
            self.assertTrue(case_aware.exists())
            
            # Test case resolution in get_case_sensitive_path
            resolved = CaseAwarePath.get_case_sensitive_path(str(case_aware))
            self.assertTrue(resolved.exists())

    def test_endswith_method(self):
        """Test the custom endswith method."""
        path = CaseAwarePath("test/file.TXT")
        
        self.assertTrue(path.endswith(".txt"))
        self.assertTrue(path.endswith(".TXT"))
        self.assertTrue(path.endswith(".Txt"))
        self.assertFalse(path.endswith(".py"))

    def test_split_filename_method(self):
        """Test the split_filename method."""
        path = CaseAwarePath("test.file.txt")
        
        # Test default behavior (1 dot)
        stem, ext = path.split_filename()
        self.assertEqual(stem, "test.file")
        self.assertEqual(ext, "txt")
        
        # Test multiple dots
        stem, ext = path.split_filename(dots=2)
        self.assertEqual(stem, "test")
        self.assertEqual(ext, "file.txt")
        
        # Test negative dots (splits from left and reverses)
        stem, ext = path.split_filename(dots=-1)
        self.assertEqual(stem, "file.txt")
        self.assertEqual(ext, "test")


if __name__ == "__main__":
    unittest.main()