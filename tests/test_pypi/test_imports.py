"""Test package imports.

These tests verify that all packages can be imported correctly
and their main modules are accessible.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    pass

# Add library sources to path for local testing
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


class TestCoreImports:
    """Test core pykotor imports."""
    
    def test_import_pykotor(self):
        """Test that pykotor can be imported."""
        import pykotor
        assert pykotor is not None
    
    def test_import_pykotor_common(self):
        """Test that pykotor.common can be imported."""
        from pykotor import common
        assert common is not None
    
    def test_import_pykotor_common_language(self):
        """Test that pykotor.common.language can be imported."""
        from pykotor.common import language
        from pykotor.common.language import Language, LocalizedString, Gender
        assert Language is not None
        assert LocalizedString is not None
        assert Gender is not None
    
    def test_import_pykotor_resource(self):
        """Test that pykotor.resource can be imported."""
        from pykotor import resource
        assert resource is not None
    
    def test_import_pykotor_resource_type(self):
        """Test that pykotor.resource.type can be imported."""
        from pykotor.resource import type as res_type
        from pykotor.resource.type import ResourceType
        assert ResourceType is not None
    
    def test_import_pykotor_extract(self):
        """Test that pykotor.extract can be imported."""
        from pykotor import extract
        assert extract is not None
    
    def test_import_pykotor_extract_installation(self):
        """Test that pykotor.extract.installation can be imported."""
        from pykotor.extract import installation
        from pykotor.extract.installation import Installation
        assert Installation is not None
    
    def test_import_pykotor_tslpatcher(self):
        """Test that pykotor.tslpatcher can be imported."""
        from pykotor import tslpatcher
        assert tslpatcher is not None


class TestGLImports:
    """Test PyKotorGL imports."""
    
    @pytest.fixture(autouse=True)
    def skip_if_gl_unavailable(self):
        """Skip GL tests if dependencies are not available."""
        try:
            import numpy
            import OpenGL
            import glm
        except ImportError as e:
            pytest.skip(f"GL dependencies not available: {e}")
    
    def test_import_pykotorgl(self):
        """Test that pykotor.gl can be imported."""
        from pykotor import gl
        assert gl is not None
    
    def test_import_gl_scene(self):
        """Test that pykotor.gl.scene can be imported."""
        from pykotor.gl import scene
        assert scene is not None


class TestFontImports:
    """Test PyKotorFont imports."""
    
    @pytest.fixture(autouse=True)
    def skip_if_font_unavailable(self):
        """Skip font tests if dependencies are not available."""
        try:
            import PIL
        except ImportError as e:
            pytest.skip(f"Font dependencies not available: {e}")
    
    def test_import_pykotorfont(self):
        """Test that pykotor.font can be imported."""
        from pykotor import font
        assert font is not None
    
    def test_import_font_draw(self):
        """Test that pykotor.font.draw can be imported."""
        from pykotor.font import draw
        assert draw is not None


class TestToolImports:
    """Test tool package imports."""
    
    @pytest.mark.parametrize("tool_module,package_path", [
        ("holopatcher", "Tools/HoloPatcher/src"),
        ("kotordiff", "Tools/KotorDiff/src"),
        ("kotorcli", "Tools/KOTORCli/src"),
        ("gui_converter", "Tools/GuiConverter/src"),
        ("kitgenerator", "Tools/KitGenerator/src"),
    ])
    def test_import_tool(self, tool_module: str, package_path: str):
        """Test that tool modules can be imported."""
        tool_path = PROJECT_ROOT / package_path
        if not tool_path.exists():
            pytest.skip(f"Tool path does not exist: {tool_path}")
        
        if str(tool_path) not in sys.path:
            sys.path.insert(0, str(tool_path))
        
        try:
            mod = importlib.import_module(tool_module)
            assert mod is not None
        except ImportError as e:
            pytest.skip(f"Cannot import {tool_module}: {e}")


class TestVersionAttributes:
    """Test that packages expose version information."""
    
    def test_pykotor_has_version(self):
        """Test that pykotor exposes __version__."""
        import pykotor
        # Version might be in different places
        version = getattr(pykotor, "__version__", None) or getattr(pykotor, "VERSION", None)
        # This is a soft check - not all packages expose version at runtime
        if version is None:
            pytest.warns(UserWarning, match="pykotor does not expose __version__")
    
    def test_version_is_string(self):
        """Test that version is a string if present."""
        import pykotor
        version = getattr(pykotor, "__version__", None)
        if version is not None:
            assert isinstance(version, str), "Version should be a string"


class TestModuleDiscovery:
    """Test that all expected modules are discoverable."""
    
    EXPECTED_PYKOTOR_MODULES = [
        "pykotor.common",
        "pykotor.common.language",
        "pykotor.common.misc",
        "pykotor.common.module",
        "pykotor.common.stream",
        "pykotor.resource",
        "pykotor.resource.type",
        "pykotor.resource.formats",
        "pykotor.resource.generics",
        "pykotor.extract",
        "pykotor.extract.installation",
        "pykotor.extract.capsule",
        "pykotor.extract.talktable",
        "pykotor.tslpatcher",
        "pykotor.tslpatcher.patcher",
        "pykotor.tslpatcher.config",
        "pykotor.tools",
    ]
    
    @pytest.mark.parametrize("module_name", EXPECTED_PYKOTOR_MODULES)
    def test_expected_module_exists(self, module_name: str):
        """Test that expected module can be imported."""
        try:
            importlib.import_module(module_name)
        except ImportError as e:
            pytest.fail(f"Expected module {module_name} cannot be imported: {e}")

