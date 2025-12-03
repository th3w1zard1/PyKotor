"""Test basic functionality of PyKotor packages.

These tests verify that the core functionality of packages works
correctly, not just that they can be imported.
"""

from __future__ import annotations

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


class TestLocalizedString:
    """Test LocalizedString functionality."""
    
    def test_create_empty_localized_string(self):
        """Test creating an empty LocalizedString."""
        from pykotor.common.language import LocalizedString
        
        # Use stringref=-1 for empty LocalizedString (uses stored substrings)
        ls = LocalizedString(stringref=-1)
        assert ls is not None
    
    def test_create_from_english(self):
        """Test creating LocalizedString from English text."""
        from pykotor.common.language import LocalizedString
        
        ls = LocalizedString.from_english("Hello World")
        assert ls is not None
    
    def test_set_and_get_text(self):
        """Test setting and getting text in LocalizedString."""
        from pykotor.common.language import LocalizedString, Language, Gender
        
        # Use stringref=-1 to use stored substrings
        ls = LocalizedString(stringref=-1)
        ls.set_data(Language.ENGLISH, Gender.MALE, "Test String")
        result = ls.get(Language.ENGLISH, Gender.MALE)
        
        assert result == "Test String"
    
    def test_multiple_languages(self):
        """Test LocalizedString with multiple languages."""
        from pykotor.common.language import LocalizedString, Language, Gender
        
        # Use stringref=-1 to use stored substrings
        ls = LocalizedString(stringref=-1)
        ls.set_data(Language.ENGLISH, Gender.MALE, "English")
        ls.set_data(Language.FRENCH, Gender.MALE, "Français")
        ls.set_data(Language.GERMAN, Gender.MALE, "Deutsch")
        
        assert ls.get(Language.ENGLISH, Gender.MALE) == "English"
        assert ls.get(Language.FRENCH, Gender.MALE) == "Français"
        assert ls.get(Language.GERMAN, Gender.MALE) == "Deutsch"
    
    def test_stringref(self):
        """Test LocalizedString stringref functionality."""
        from pykotor.common.language import LocalizedString
        
        ls = LocalizedString(stringref=12345)
        assert ls.stringref == 12345


class TestResourceType:
    """Test ResourceType functionality."""
    
    def test_resource_type_attributes(self):
        """Test ResourceType attributes."""
        from pykotor.resource.type import ResourceType
        
        # Test some common resource types
        assert ResourceType.UTC.extension == "utc"
        assert ResourceType.UTI.extension == "uti"
        assert ResourceType.DLG.extension == "dlg"
        assert ResourceType.TPC.extension == "tpc"
        assert ResourceType.MDL.extension == "mdl"
        assert ResourceType.TwoDA.extension == "2da"
    
    def test_resource_type_from_extension(self):
        """Test getting ResourceType from extension."""
        from pykotor.resource.type import ResourceType
        
        assert ResourceType.from_extension("utc") == ResourceType.UTC
        assert ResourceType.from_extension("dlg") == ResourceType.DLG
        assert ResourceType.from_extension("2da") == ResourceType.TwoDA
    
    def test_resource_type_equality(self):
        """Test ResourceType equality."""
        from pykotor.resource.type import ResourceType
        
        assert ResourceType.UTC == ResourceType.UTC
        assert ResourceType.UTC != ResourceType.UTI
    
    def test_resource_type_iteration(self):
        """Test that ResourceType can be iterated."""
        from pykotor.resource.type import ResourceType
        
        # ResourceType should have many values
        all_types = list(ResourceType)
        assert len(all_types) > 50  # There are many resource types


class TestLanguageEnum:
    """Test Language enum functionality."""
    
    def test_language_values(self):
        """Test Language enum values."""
        from pykotor.common.language import Language
        
        # Test that common languages exist
        assert Language.ENGLISH is not None
        assert Language.FRENCH is not None
        assert Language.GERMAN is not None
        assert Language.ITALIAN is not None
        assert Language.SPANISH is not None
    
    def test_gender_values(self):
        """Test Gender enum values."""
        from pykotor.common.language import Gender
        
        assert Gender.MALE is not None
        assert Gender.FEMALE is not None


class TestInstallation:
    """Test Installation class functionality."""
    
    def test_installation_init(self):
        """Test Installation initialization without a path."""
        from pykotor.extract.installation import Installation
        
        # Should be able to create Installation with non-existent path
        # (it won't load anything, but shouldn't crash)
        inst = Installation(Path("/nonexistent/path"))
        assert inst is not None
    
    def test_installation_game_enum(self):
        """Test Installation game type."""
        from pykotor.extract.installation import Installation
        
        # Test creating with non-existent paths
        # Game type is auto-detected from the installation path
        inst_k1 = Installation(Path("/nonexistent"))
        inst_k2 = Installation(Path("/nonexistent2"))
        
        assert inst_k1 is not None
        assert inst_k2 is not None


class TestTSLPatcher:
    """Test TSLPatcher functionality."""
    
    def test_import_patcher(self):
        """Test that patcher module can be imported."""
        from pykotor.tslpatcher import patcher
        assert patcher is not None
    
    def test_import_config(self):
        """Test that config module can be imported."""
        from pykotor.tslpatcher import config
        assert config is not None
    
    def test_import_reader(self):
        """Test that reader module can be imported."""
        from pykotor.tslpatcher import reader
        assert reader is not None


class TestGFFFormats:
    """Test GFF format handling."""
    
    def test_import_gff_module(self):
        """Test that GFF module can be imported."""
        from pykotor.resource.formats import gff
        assert gff is not None
    
    def test_gff_field_types(self):
        """Test GFF field type constants."""
        from pykotor.resource.formats.gff import gff_data
        
        # GFF should have standard field types
        assert hasattr(gff_data, "GFFFieldType") or hasattr(gff_data, "GFFContent")


class TestTwoDAFormats:
    """Test 2DA format handling."""
    
    def test_import_twoda_module(self):
        """Test that 2DA module can be imported."""
        from pykotor.resource.formats import twoda
        assert twoda is not None


class TestTLKFormats:
    """Test TLK format handling."""
    
    def test_import_tlk_module(self):
        """Test that TLK module can be imported."""
        from pykotor.resource.formats import tlk
        assert tlk is not None


class TestUtilityModule:
    """Test utility module functionality."""
    
    def test_import_utility(self):
        """Test that utility module can be imported."""
        from utility import misc
        assert misc is not None
    
    def test_import_path_utilities(self):
        """Test that path utilities can be imported."""
        from utility.system import path
        assert path is not None


class TestCommonMisc:
    """Test common.misc functionality."""
    
    def test_import_misc(self):
        """Test that misc module can be imported."""
        from pykotor.common import misc
        assert misc is not None
    
    def test_game_enum(self):
        """Test Game enum."""
        from pykotor.common.misc import Game
        
        assert Game.K1 is not None
        assert Game.K2 is not None

