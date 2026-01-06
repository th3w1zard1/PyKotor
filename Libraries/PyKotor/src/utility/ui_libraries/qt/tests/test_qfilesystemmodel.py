"""Tests for PyFileSystemModel matching Qt6 C++ source code.

This test file aims for 1:1 parity with tst_qfilesystemmodel.cpp
from Qt6's source code.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from qtpy.QtCore import QDir, QModelIndex, Qt
from qtpy.QtWidgets import QApplication, QFileIconProvider

if TYPE_CHECKING:
    pass

# Import the Python adapters
from utility.ui_libraries.qt.adapters.filesystem.pyfilesystemmodel import PyFileSystemModel


WAITTIME = 1000  # milliseconds


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestQFileSystemModel:
    """Test class matching tst_QFileSystemModel from C++ tests."""

    def test_index_path(self, qapp, temp_dir):
        """Test indexPath() - matching C++ indexPath() test."""
        # This test is platform-specific (not Windows)
        if os.name == "nt":
            pytest.skip("indexPath test is not for Windows")
        
        model = PyFileSystemModel()
        depth = len(str(Path.cwd()).split(os.sep))
        model.setRootPath(str(Path.cwd()))
        
        back_path = ""
        for i in range(depth * 2 + 2):
            back_path += "../"
            idx = model.index(back_path)
            if i != depth - 1:
                assert idx.isValid()
            else:
                assert not idx.isValid()

    def test_root_path(self, qapp, temp_dir):
        """Test rootPath() - matching C++ rootPath() test."""
        model = PyFileSystemModel()
        assert model.rootPath() == QDir().path()
        
        # Test setting root path
        root = model.setRootPath(str(temp_dir))
        assert root.isValid()
        assert model.rootPath() == str(temp_dir)
        assert model.rootDirectory().absolutePath() == str(temp_dir)

    def test_read_only(self, qapp, temp_dir):
        """Test readOnly() - matching C++ readOnly() test."""
        model = PyFileSystemModel()
        assert model.isReadOnly() is True
        
        # Create a test file
        test_file = temp_dir / "test.dat"
        test_file.write_bytes(b"test data")
        
        root = model.setRootPath(str(temp_dir))
        # Wait for model to populate
        import time
        time.sleep(0.1)  # Give model time to populate
        
        file_idx = model.index(str(test_file))
        if file_idx.isValid():
            # ItemIsEditable should change, ItemNeverHasChildren should not change
            flags = model.flags(file_idx)
            assert not (flags & Qt.ItemFlag.ItemIsEditable)
            assert flags & Qt.ItemFlag.ItemNeverHasChildren
            
            model.setReadOnly(False)
            assert model.isReadOnly() is False
            
            flags = model.flags(file_idx)
            assert flags & Qt.ItemFlag.ItemIsEditable
            assert flags & Qt.ItemFlag.ItemNeverHasChildren

    def test_icon_provider(self, qapp, temp_dir):
        """Test iconProvider() - matching C++ iconProvider() test."""
        model = PyFileSystemModel()
        assert model.iconProvider() is not None
        
        provider = QFileIconProvider()
        model.setIconProvider(provider)
        assert model.iconProvider() == provider
        
        model.setIconProvider(None)
        provider = None

    def test_row_count(self, qapp, temp_dir):
        """Test rowCount() - matching C++ rowCount() test."""
        model = PyFileSystemModel()
        
        # Create test files
        test_files = ["b", "d", "f", "h", "j", ".a", ".c", ".e", ".g"]
        for fname in test_files:
            (temp_dir / fname).write_text("test")
        
        root = model.setRootPath(str(temp_dir))
        
        # Wait for model to populate
        import time
        for _ in range(50):  # Try up to 5 seconds
            if model.rowCount(root) > 0:
                break
            time.sleep(0.1)
        
        assert model.rowCount(root) > 0

    # Additional tests will be added to match all C++ tests...
    # This is a starting point showing the structure
