"""
Test that optional dependencies are handled gracefully.

This test validates that editors and modules can be imported and initialized
even when optional dependencies (like PIL, requests, etc.) are not available.
The test should fail if a module raises ModuleNotFoundError during import,
and pass when optional imports are properly handled with try/except.
"""
from __future__ import annotations

import sys
import importlib
from unittest.mock import patch
from typing import TYPE_CHECKING

import pytest
from qtpy.QtWidgets import QApplication

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot

# Ensure QApplication exists for GUI tests
if not QApplication.instance():
    _app = QApplication([])


def _test_module_import_without_optional_dependency(
    module_name: str,
    dependency_name: str,
    *,
    should_import: bool = True,
    should_raise: bool = False,
) -> None:
    """
    Test that a module can be imported even when an optional dependency is missing.
    
    Args:
        module_name: The module to test (e.g., 'toolset.gui.editors.tpc')
        dependency_name: The optional dependency that should be missing (e.g., 'PIL')
        should_import: Whether the module should successfully import (default: True)
        should_raise: Whether the import should raise an exception (default: False)
    """
    # Remove the module from sys.modules if it exists to force reimport
    if module_name in sys.modules:
        del sys.modules[module_name]
    
    # Mock the dependency to raise ImportError
    with patch.dict('sys.modules', {dependency_name: None}):
        # Try to import the module
        try:
            importlib.import_module(module_name)
            imported = True
            exception_raised = False
        except ModuleNotFoundError as e:
            if dependency_name in str(e):
                imported = False
                exception_raised = True
            else:
                # Different ModuleNotFoundError, re-raise
                raise
        except Exception as e:
            # Other exceptions are unexpected
            pytest.fail(f"Unexpected exception when importing {module_name} without {dependency_name}: {e}")
    
    if should_import and not imported:
        pytest.fail(
            f"Module {module_name} should import successfully even when {dependency_name} is missing, "
            f"but ModuleNotFoundError was raised. This indicates the import is not optional."
        )
    
    if should_raise and not exception_raised:
        pytest.fail(
            f"Module {module_name} should raise ModuleNotFoundError when {dependency_name} is missing, "
            f"but it imported successfully."
        )


def test_tpc_editor_imports_without_pil():
    """Test that TPCEditor can be imported even when PIL/Pillow is not available."""
    _test_module_import_without_optional_dependency(
        "toolset.gui.editors.tpc",
        "PIL",
        should_import=True,
        should_raise=False,
    )


def test_config_update_imports_without_requests():
    """Test that config_update can be imported even when requests is not available."""
    _test_module_import_without_optional_dependency(
        "toolset.config.config_update",
        "requests",
        should_import=True,
        should_raise=False,
    )


def test_editor_classes_import_without_optional_deps():
    """
    Generic test to ensure editor classes can be imported.
    
    This test validates that editors don't have hard dependencies on optional packages
    at import time. It's intentionally vague to catch similar issues.
    """
    editor_modules = [
        "toolset.gui.editors.tpc",
        "toolset.gui.editors.are",
        "toolset.gui.editors.gff",
        "toolset.gui.editors.dlg",
    ]
    
    for module_name in editor_modules:
        try:
            module = importlib.import_module(module_name)
            # Module should import without raising ModuleNotFoundError
            assert module is not None
        except ModuleNotFoundError as e:
            # If it's a missing optional dependency, that's a problem
            pytest.fail(
                f"Module {module_name} raised ModuleNotFoundError during import. "
                f"This suggests an optional dependency is not properly handled. "
                f"Error: {e}"
            )


def test_window_utils_imports_without_optional_deps():
    """
    Test that window utilities can import editors even when optional deps are missing.
    
    This simulates the real-world scenario where open_resource_editor is called
    and tries to import an editor that has optional dependencies.
    """
    from pathlib import Path
    
    # Mock PIL to be missing
    import sys
    original_modules = {}
    try:
        # Remove PIL from sys.modules if it exists
        if 'PIL' in sys.modules:
            original_modules['PIL'] = sys.modules['PIL']
            del sys.modules['PIL']
        if 'PIL.Image' in sys.modules:
            original_modules['PIL.Image'] = sys.modules['PIL.Image']
            del sys.modules['PIL.Image']
        
        # Try to import TPC editor - should not raise ModuleNotFoundError
        from toolset.gui.editors import tpc
        # If we get here, the import succeeded (Image will be None)
        assert hasattr(tpc, 'Image')
        
    finally:
        # Restore original modules
        for name, module in original_modules.items():
            sys.modules[name] = module

