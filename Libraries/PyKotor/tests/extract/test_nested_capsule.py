"""Tests for nested capsule extraction in FileResource.

This module tests the ability to extract resources from nested capsules,
e.g., a SAV file containing another SAV file containing a resource.
"""

from __future__ import annotations

from pathlib import Path

from pykotor.extract.capsule import Capsule
from pykotor.extract.file import (
    FileResource,
    ResourceIdentifier,
    _extract_from_nested_capsules,
    _find_real_filesystem_path,
)
from pykotor.resource.formats.erf import ERF, ERFType, write_erf
from pykotor.resource.formats.rim import RIM, write_rim
from pykotor.resource.type import ResourceType


class TestFindRealFilesystemPath:
    """Tests for _find_real_filesystem_path function."""

    def test_existing_file_returns_path_no_parts(self, tmp_path: Path):
        """A regular file should return (path, [])."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")

        real_path, parts = _find_real_filesystem_path(test_file)
        assert real_path == test_file
        assert parts == []

    def test_nested_path_returns_real_path_and_parts(self, tmp_path: Path):
        """A nested path should return (real_path, [nested_parts])."""
        outer_capsule = tmp_path / "outer.sav"
        outer_capsule.write_bytes(b"dummy")

        # Create a fake nested path that doesn't exist on filesystem
        nested_path = outer_capsule / "inner.sav" / "resource.utc"

        real_path, parts = _find_real_filesystem_path(nested_path)
        assert real_path == outer_capsule
        assert parts == ["inner.sav", "resource.utc"]

    def test_nonexistent_path_returns_none(self, tmp_path: Path):
        """A completely nonexistent path should return (None, [])."""
        fake_path = tmp_path / "nonexistent" / "path.txt"

        real_path, parts = _find_real_filesystem_path(fake_path)
        assert real_path is None
        assert parts == []


class TestNestedCapsuleExtraction:
    """Tests for extracting resources from nested capsules."""

    def test_single_level_capsule(self, tmp_path: Path):
        """Test extracting from a single-level capsule (no nesting)."""
        # Create an ERF with a single resource
        erf = ERF(ERFType.ERF)
        test_data = b"Hello, World!"
        erf.set_data("test", ResourceType.TXT, test_data)

        capsule_path = tmp_path / "test.erf"
        write_erf(erf, capsule_path)

        # Use FileResource to extract
        capsule = Capsule(capsule_path)
        result = capsule.resource("test", ResourceType.TXT)
        assert result == test_data

    def test_nested_erf_extraction(self, tmp_path: Path):
        """Test extracting from a nested ERF (capsule inside capsule)."""
        # Create inner ERF with a resource
        inner_erf = ERF(ERFType.MOD)  # Using MOD type for SAV-like behavior
        test_data = b"Nested resource data!"
        inner_erf.set_data("nested", ResourceType.UTC, test_data)

        # Write inner ERF to bytes
        inner_path = tmp_path / "inner_temp.sav"
        write_erf(inner_erf, inner_path)
        inner_data = inner_path.read_bytes()

        # Create outer ERF containing the inner ERF
        outer_erf = ERF(ERFType.MOD)
        outer_erf.set_data("inner", ResourceType.SAV, inner_data)

        outer_path = tmp_path / "outer.sav"
        write_erf(outer_erf, outer_path)

        # Now test extraction through nested path
        nested_parts = ["inner.sav", "nested.utc"]
        result = _extract_from_nested_capsules(outer_path, nested_parts)
        assert result == test_data

    def test_file_resource_data_nested(self, tmp_path: Path):
        """Test FileResource.data() works with nested capsule paths."""
        # Create inner ERF with a resource
        inner_erf = ERF(ERFType.MOD)
        test_data = b"FileResource nested test!"
        inner_erf.set_data("myres", ResourceType.TGA, test_data)

        inner_path = tmp_path / "inner_temp.sav"
        write_erf(inner_erf, inner_path)
        inner_data = inner_path.read_bytes()

        # Create outer ERF containing the inner ERF
        outer_erf = ERF(ERFType.MOD)
        outer_erf.set_data("savegame", ResourceType.SAV, inner_data)

        outer_path = tmp_path / "SAVEGAME.sav"
        write_erf(outer_erf, outer_path)

        # Create a FileResource with the nested path
        nested_path = outer_path / "savegame.sav" / "myres.tga"
        fr = FileResource(
            resname="myres",
            restype=ResourceType.TGA,
            size=len(test_data),
            offset=0,
            filepath=nested_path,
        )

        # This should work with nested capsule support
        result = fr.data()
        assert result == test_data

    def test_file_resource_exists_nested(self, tmp_path: Path):
        """Test FileResource.exists() works with nested capsule paths."""
        # Create inner ERF with a resource
        inner_erf = ERF(ERFType.MOD)
        test_data = b"Exists test data"
        inner_erf.set_data("check", ResourceType.ARE, test_data)

        inner_path = tmp_path / "inner_temp.sav"
        write_erf(inner_erf, inner_path)
        inner_data = inner_path.read_bytes()

        # Create outer ERF containing the inner ERF
        outer_erf = ERF(ERFType.MOD)
        outer_erf.set_data("nested", ResourceType.SAV, inner_data)

        outer_path = tmp_path / "SAVES.sav"
        write_erf(outer_erf, outer_path)

        # Test existing resource
        nested_path = outer_path / "nested.sav" / "check.are"
        fr_exists = FileResource(
            resname="check",
            restype=ResourceType.ARE,
            size=len(test_data),
            offset=0,
            filepath=nested_path,
        )
        assert fr_exists.exists() is True

        # Test non-existing resource
        nested_path_bad = outer_path / "nested.sav" / "nothere.utc"
        fr_not_exists = FileResource(
            resname="nothere",
            restype=ResourceType.UTC,
            size=0,
            offset=0,
            filepath=nested_path_bad,
        )
        assert fr_not_exists.exists() is False

    def test_triple_nested_capsule(self, tmp_path: Path):
        """Test extracting from a triple-nested capsule structure."""
        # Create innermost resource
        test_data = b"Triple nested data!!!"

        # Level 3 (innermost)
        inner3 = ERF(ERFType.ERF)
        inner3.set_data("deep", ResourceType.GIT, test_data)
        inner3_path = tmp_path / "level3.erf"
        write_erf(inner3, inner3_path)
        inner3_data = inner3_path.read_bytes()

        # Level 2
        inner2 = ERF(ERFType.MOD)
        inner2.set_data("level3", ResourceType.ERF, inner3_data)
        inner2_path = tmp_path / "level2.mod"
        write_erf(inner2, inner2_path)
        inner2_data = inner2_path.read_bytes()

        # Level 1 (outermost)
        outer = ERF(ERFType.MOD)
        outer.set_data("level2", ResourceType.MOD, inner2_data)
        outer_path = tmp_path / "outer.sav"
        write_erf(outer, outer_path)

        # Extract through triple nesting
        nested_parts = ["level2.mod", "level3.erf", "deep.git"]
        result = _extract_from_nested_capsules(outer_path, nested_parts)
        assert result == test_data

    def test_rim_nested_in_erf(self, tmp_path: Path):
        """Test extracting from a RIM inside an ERF."""
        # Create RIM with a resource
        rim = RIM()
        test_data = b"RIM inside ERF data"
        rim.set_data("rimres", ResourceType.NCS, test_data)

        rim_path = tmp_path / "module.rim"
        write_rim(rim, rim_path)
        rim_data = rim_path.read_bytes()

        # Create ERF containing the RIM
        erf = ERF(ERFType.MOD)
        erf.set_data("module", ResourceType.RIM, rim_data)

        erf_path = tmp_path / "game.sav"
        write_erf(erf, erf_path)

        # Extract through nested path
        nested_parts = ["module.rim", "rimres.ncs"]
        result = _extract_from_nested_capsules(erf_path, nested_parts)
        assert result == test_data

    def test_file_resource_exists_inside_bif_does_not_use_lazy_capsule(self, tmp_path: Path):
        """FileResource.exists() must not treat .bif as a capsule."""
        from pykotor.common.misc import ResRef
        from pykotor.resource.formats.bif import BIF, read_bif, write_bif

        bif_path = tmp_path / "sounds.bif"

        bif = BIF()
        bif.set_data(ResRef("some_resource"), ResourceType.TXT, b"hello", res_id=0)
        bif.set_data(ResRef("another_resource"), ResourceType.TXT, b"world", res_id=1)
        write_bif(bif, bif_path)

        parsed = read_bif(bif_path)
        assert len(parsed.resources) == 2
        entry1 = parsed.resources[0]
        entry2 = parsed.resources[1]

        fr1 = FileResource(
            resname="some_resource",
            restype=entry1.restype,
            size=entry1.size,
            offset=entry1.offset,
            filepath=bif_path,
        )
        assert fr1.inside_bif is True
        assert fr1.exists() is True
        assert fr1.data() == b"hello"
        assert fr1.offset() == entry1.offset
        assert fr1.size() == entry1.size

        fr2 = FileResource(
            resname="another_resource",
            restype=entry2.restype,
            size=entry2.size,
            offset=entry2.offset,
            filepath=bif_path,
        )
        assert fr2.inside_bif is True
        assert fr2.exists() is True
        assert fr2.data() == b"world"
        assert fr2.offset() == entry2.offset
        assert fr2.size() == entry2.size


class TestResourceIdentifierFromPath:
    """Tests for ResourceIdentifier.from_path with nested paths."""

    def test_nested_path_parses_correctly(self):
        """ResourceIdentifier should parse the last component of a nested path."""
        ident = ResourceIdentifier.from_path("SAVEGAME.sav/inner.sav/resource.utc")
        assert ident.resname == "resource"
        assert ident.restype == ResourceType.UTC

    def test_capsule_path_parses_correctly(self):
        """ResourceIdentifier should parse capsule extensions correctly."""
        ident = ResourceIdentifier.from_path("outer.sav/inner.sav")
        assert ident.resname == "inner"
        assert ident.restype == ResourceType.SAV
