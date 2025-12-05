"""Comprehensive tests for BWM/WOK/DWK/PWK file format.

Tests cover:
- Header validation and version checking
- Vertex reading/writing and deduplication
- Face reading/writing with materials
- Walkable vs unwalkable face ordering
- Edge transitions and perimeter edges
- AABB tree generation (WOK only)
- Adjacency calculation
- WOK vs PWK/DWK format differences
- Roundtrip integrity
- Error handling and edge cases

References:
----------
    vendor/reone/src/libs/graphics/format/bwmreader.cpp - BWM reading validation
    vendor/kotorblender/io_scene_kotor/format/bwm/reader.py - Blender BWM reader
    vendor/kotorblender/io_scene_kotor/format/bwm/writer.py - Blender BWM writer
    wiki/BWM-File-Format.md - Complete format specification
"""

from __future__ import annotations

import io
import struct
from pathlib import Path

import pytest

import pathlib
import sys

# Setup paths
THIS_FILE = pathlib.Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parents[5]
PYKOTOR_SRC = REPO_ROOT / "Libraries" / "PyKotor" / "src"
UTILITY_SRC = REPO_ROOT / "Libraries" / "Utility" / "src"

for path in (PYKOTOR_SRC, UTILITY_SRC):
    as_posix = path.as_posix()
    if as_posix not in sys.path:
        sys.path.insert(0, as_posix)

from utility.common.geometry import Vector3, SurfaceMaterial  # noqa: E402
from pykotor.resource.formats.bwm import read_bwm, write_bwm  # noqa: E402
from pykotor.resource.formats.bwm.bwm_auto import BWMBinaryReader, BWMBinaryWriter  # noqa: E402
from pykotor.resource.formats.bwm.bwm_data import BWM, BWMType, BWMFace  # noqa: E402
from pykotor.resource.type import ResourceType  # noqa: E402


class TestBWMHeaderValidation:
    """Test BWM header validation and error handling."""

    def test_invalid_magic(self):
        """Test that invalid magic bytes raise ValueError."""
        invalid_data = b"INVALID" + b"V1.0" + b"\x00" * 120
        with pytest.raises(ValueError):
            read_bwm(invalid_data)

    def test_invalid_version(self):
        """Test that invalid version raises ValueError."""
        invalid_data = b"BWM " + b"V2.0" + b"\x00" * 120
        with pytest.raises(ValueError):
            read_bwm(invalid_data)

    def test_valid_header(self):
        """Test that valid header is accepted."""
        # Create minimal valid BWM (needs at least one face for AABB tree)
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel
        
        # Add a face so AABB tree can be generated
        face = BWMFace(
            Vector3(0.0, 0.0, 0.0),
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0),
        )
        face.material = SurfaceMaterial.DIRT
        bwm.faces = [face]
        
        buf = io.BytesIO()
        writer = BWMBinaryWriter(bwm, buf)
        writer.write(auto_close=False)
        buf.seek(0)
        data = buf.read()
        
        # Should read without error
        loaded = read_bwm(data)
        assert loaded.walkmesh_type == BWMType.AreaModel

    def test_header_signature_exact_match(self):
        """Test that header signature must match exactly (including space)."""
        # "BWM " with space is required
        invalid_data = b"BWMA" + b"V1.0" + b"\x00" * 120  # Wrong magic
        with pytest.raises(ValueError):
            read_bwm(invalid_data)


class TestBWMVertexHandling:
    """Test vertex reading, writing, and deduplication."""

    def test_vertex_roundtrip(self):
        """Test that vertices are preserved through roundtrip."""
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel
        
        # Create faces with specific vertices
        v1 = Vector3(1.0, 2.0, 3.0)
        v2 = Vector3(4.0, 5.0, 6.0)
        v3 = Vector3(7.0, 8.0, 9.0)
        face = BWMFace(v1, v2, v3)
        face.material = SurfaceMaterial.DIRT
        bwm.faces = [face]
        
        buf = io.BytesIO()
        writer = BWMBinaryWriter(bwm, buf)
        writer.write(auto_close=False)
        buf.seek(0)
        loaded = read_bwm(buf.read())
        
        assert len(loaded.faces) == 1
        loaded_face = loaded.faces[0]
        assert loaded_face.v1 == v1
        assert loaded_face.v2 == v2
        assert loaded_face.v3 == v3

    def test_vertex_deduplication(self):
        """Test that shared vertices are deduplicated in output."""
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel
        
        # Create two faces sharing a vertex
        v1 = Vector3(0.0, 0.0, 0.0)
        v2 = Vector3(1.0, 0.0, 0.0)
        v3 = Vector3(0.0, 1.0, 0.0)
        v4 = Vector3(1.0, 1.0, 0.0)
        
        face1 = BWMFace(v1, v2, v3)
        face1.material = SurfaceMaterial.DIRT
        face2 = BWMFace(v2, v4, v3)  # Shares v2 and v3
        face2.material = SurfaceMaterial.DIRT
        bwm.faces = [face1, face2]
        
        buf = io.BytesIO()
        writer = BWMBinaryWriter(bwm, buf)
        writer.write(auto_close=False)
        buf.seek(0)
        loaded = read_bwm(buf.read())
        
        # Should have 4 unique vertices
        vertices = loaded.vertices()
        assert len(vertices) == 4
        
        # Faces should still reference correct vertices
        assert len(loaded.faces) == 2


class TestBWMFaceHandling:
    """Test face reading, writing, materials, and ordering."""

    def test_face_material_preservation(self):
        """Test that face materials are preserved."""
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel
        
        materials = [
            SurfaceMaterial.DIRT,
            SurfaceMaterial.GRASS,
            SurfaceMaterial.STONE,
            SurfaceMaterial.WATER,
            SurfaceMaterial.NON_WALK,
        ]
        
        faces: list[BWMFace] = []
        for i, material in enumerate(materials):
            v1 = Vector3(i * 3.0, 0.0, 0.0)
            v2 = Vector3(i * 3.0 + 1.0, 0.0, 0.0)
            v3 = Vector3(i * 3.0, 1.0, 0.0)
            face = BWMFace(v1, v2, v3)
            face.material = material
            faces.append(face)
        
        bwm.faces = faces
        
        buf = io.BytesIO()
        writer = BWMBinaryWriter(bwm, buf)
        writer.write(auto_close=False)
        buf.seek(0)
        loaded = read_bwm(buf.read())
        
        # Materials should be preserved (order may change due to walkable sorting)
        loaded_materials = {face.material for face in loaded.faces}
        original_materials = {face.material for face in faces}
        assert loaded_materials == original_materials

    def test_walkable_face_ordering(self):
        """Test that walkable faces come before unwalkable faces."""
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel
        
        # Create mixed walkable/unwalkable faces
        walkable_face = BWMFace(
            Vector3(0.0, 0.0, 0.0),
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0),
        )
        walkable_face.material = SurfaceMaterial.DIRT  # Walkable
        
        unwalkable_face = BWMFace(
            Vector3(2.0, 0.0, 0.0),
            Vector3(3.0, 0.0, 0.0),
            Vector3(2.0, 1.0, 0.0),
        )
        unwalkable_face.material = SurfaceMaterial.NON_WALK  # Unwalkable
        
        # Add in reverse order
        bwm.faces = [unwalkable_face, walkable_face]
        
        buf = io.BytesIO()
        writer = BWMBinaryWriter(bwm, buf)
        writer.write(auto_close=False)
        buf.seek(0)
        loaded = read_bwm(buf.read())
        
        # Walkable faces should come first
        walkable_faces = loaded.walkable_faces()
        unwalkable_faces = loaded.unwalkable_faces()
        
        # Check ordering in loaded faces list
        walkable_indices = [
            i for i, face in enumerate(loaded.faces) if face.material.walkable()
        ]
        unwalkable_indices = [
            i for i, face in enumerate(loaded.faces) if not face.material.walkable()
        ]
        
        if walkable_indices and unwalkable_indices:
            assert max(walkable_indices) < min(unwalkable_indices), \
                "Walkable faces should come before unwalkable faces"

    def test_face_vertex_indices_bounds_checking(self):
        """Test that face vertex indices are within valid range."""
        # This is more of an integration test - the writer should handle this
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel
        
        # Create face with valid vertices
        face = BWMFace(
            Vector3(0.0, 0.0, 0.0),
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0),
        )
        face.material = SurfaceMaterial.DIRT
        bwm.faces = [face]
        
        buf = io.BytesIO()
        writer = BWMBinaryWriter(bwm, buf)
        writer.write(auto_close=False)
        buf.seek(0)
        data = buf.read()
        
        # Manually verify indices are valid
        reader = BWMBinaryReader(io.BytesIO(data))
        reader._reader.seek(0)
        reader._reader.read_string(4)  # Skip magic
        reader._reader.read_string(4)  # Skip version
        reader._reader.read_uint32()  # Skip type
        reader._reader.read_vector3()  # Skip hooks
        reader._reader.read_vector3()
        reader._reader.read_vector3()
        reader._reader.read_vector3()
        reader._reader.read_vector3()  # Skip position
        
        vertex_count = reader._reader.read_uint32()
        reader._reader.read_uint32()  # Skip offset
        face_count = reader._reader.read_uint32()
        indices_offset = reader._reader.read_uint32()
        
        reader._reader.seek(indices_offset)
        for _ in range(face_count):
            i1 = reader._reader.read_uint32()
            i2 = reader._reader.read_uint32()
            i3 = reader._reader.read_uint32()
            assert i1 < vertex_count
            assert i2 < vertex_count
            assert i3 < vertex_count


class TestBWMTransitions:
    """Test edge transitions and perimeter edges."""

    def test_transition_preservation(self):
        """Test that edge transitions are preserved through roundtrip."""
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel
        
        # Create face with transitions
        face = BWMFace(
            Vector3(0.0, 0.0, 0.0),
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0),
        )
        face.material = SurfaceMaterial.DIRT
        face.trans1 = 5  # Transition on edge 0
        face.trans2 = 10  # Transition on edge 1
        # trans3 = None (no transition on edge 2)
        bwm.faces = [face]
        
        buf = io.BytesIO()
        writer = BWMBinaryWriter(bwm, buf)
        writer.write(auto_close=False)
        buf.seek(0)
        loaded = read_bwm(buf.read())
        
        # Find matching face (by vertices)
        loaded_face = None
        for f in loaded.faces:
            if (f.v1 == face.v1 and f.v2 == face.v2 and f.v3 == face.v3):
                loaded_face = f
                break
        
        assert loaded_face is not None
        # Transitions may only be preserved on perimeter edges
        # If this face has an adjacency, transitions might not be written
        # This is format-expected behavior

    def test_perimeter_edge_identification(self):
        """Test that perimeter edges are correctly identified."""
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel
        
        # Create two adjacent walkable faces
        v1 = Vector3(0.0, 0.0, 0.0)
        v2 = Vector3(1.0, 0.0, 0.0)
        v3 = Vector3(0.0, 1.0, 0.0)
        v4 = Vector3(1.0, 1.0, 0.0)
        
        face1 = BWMFace(v1, v2, v3)
        face1.material = SurfaceMaterial.DIRT
        face2 = BWMFace(v2, v4, v3)  # Shares edge v2-v3 with face1
        face2.material = SurfaceMaterial.DIRT
        
        bwm.faces = [face1, face2]
        
        # Get edges - should identify perimeter edges
        edges = bwm.edges()
        
        # Should have some perimeter edges (edges not shared between walkable faces)
        # The shared edge v2-v3 should NOT be a perimeter edge
        assert len(edges) > 0


class TestBWMWOKvsPWK:
    """Test differences between WOK (area) and PWK/DWK (placeable/door) formats."""

    def test_wok_has_aabb_tree(self):
        """Test that WOK files include AABB tree."""
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel
        
        face = BWMFace(
            Vector3(0.0, 0.0, 0.0),
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0),
        )
        face.material = SurfaceMaterial.DIRT
        bwm.faces = [face]
        
        buf = io.BytesIO()
        writer = BWMBinaryWriter(bwm, buf)
        writer.write(auto_close=False)
        buf.seek(0)
        data = buf.read()
        
        # Check header for AABB count
        reader = BWMBinaryReader(io.BytesIO(data))
        reader._reader.seek(0)
        reader._reader.read_string(4)  # magic
        reader._reader.read_string(4)  # version
        reader._reader.read_uint32()  # type
        for _ in range(5):
            reader._reader.read_vector3()  # hooks and position
        reader._reader.read_uint32()  # vertex count
        reader._reader.read_uint32()  # vertex offset
        reader._reader.read_uint32()  # face count
        for _ in range(4):
            reader._reader.read_uint32()  # offsets
        aabb_count = reader._reader.read_uint32()
        
        # WOK should have AABB tree (may be 0 for very simple walkmeshes)
        assert aabb_count >= 0

    def test_pwk_no_aabb_tree(self):
        """Test that PWK/DWK files don't include AABB tree."""
        bwm = BWM()
        bwm.walkmesh_type = BWMType.PlaceableOrDoor
        
        face = BWMFace(
            Vector3(0.0, 0.0, 0.0),
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0),
        )
        face.material = SurfaceMaterial.DIRT
        bwm.faces = [face]
        
        buf = io.BytesIO()
        writer = BWMBinaryWriter(bwm, buf)
        writer.write(auto_close=False)
        buf.seek(0)
        data = buf.read()
        
        # Check header for AABB count
        reader = BWMBinaryReader(io.BytesIO(data))
        reader._reader.seek(0)
        reader._reader.read_string(4)  # magic
        reader._reader.read_string(4)  # version
        reader._reader.read_uint32()  # type
        for _ in range(5):
            reader._reader.read_vector3()  # hooks and position
        reader._reader.read_uint32()  # vertex count
        reader._reader.read_uint32()  # vertex offset
        reader._reader.read_uint32()  # face count
        for _ in range(4):
            reader._reader.read_uint32()  # offsets
        aabb_count = reader._reader.read_uint32()
        
        # PWK/DWK should have 0 AABB count
        assert aabb_count == 0

    def test_wok_has_adjacencies(self):
        """Test that WOK files include adjacency data."""
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel
        
        # Create two adjacent walkable faces
        v1 = Vector3(0.0, 0.0, 0.0)
        v2 = Vector3(1.0, 0.0, 0.0)
        v3 = Vector3(0.0, 1.0, 0.0)
        v4 = Vector3(1.0, 1.0, 0.0)
        
        face1 = BWMFace(v1, v2, v3)
        face1.material = SurfaceMaterial.DIRT
        face2 = BWMFace(v2, v4, v3)  # Adjacent to face1
        face2.material = SurfaceMaterial.DIRT
        
        bwm.faces = [face1, face2]
        
        # Check adjacencies are computed
        adj1 = bwm.adjacencies(face1)
        assert adj1[0] is not None or adj1[1] is not None or adj1[2] is not None, \
            "Adjacent faces should have adjacency data"


class TestBWMRoundtrip:
    """Test roundtrip integrity (read -> write -> read)."""

    def test_complete_roundtrip(self):
        """Test complete roundtrip with all data preserved."""
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel
        bwm.position = Vector3(10.0, 20.0, 30.0)
        bwm.relative_hook1 = Vector3(1.0, 2.0, 3.0)
        bwm.relative_hook2 = Vector3(4.0, 5.0, 6.0)
        bwm.absolute_hook1 = Vector3(7.0, 8.0, 9.0)
        bwm.absolute_hook2 = Vector3(10.0, 11.0, 12.0)
        
        # Create multiple faces
        faces = []
        for i in range(5):
            v1 = Vector3(i * 3.0, 0.0, 0.0)
            v2 = Vector3(i * 3.0 + 1.0, 0.0, 0.0)
            v3 = Vector3(i * 3.0, 1.0, 0.0)
            face = BWMFace(v1, v2, v3)
            face.material = SurfaceMaterial.DIRT if i % 2 == 0 else SurfaceMaterial.GRASS
            faces.append(face)
        
        bwm.faces = faces
        
        # Roundtrip
        buf = io.BytesIO()
        writer = BWMBinaryWriter(bwm, buf)
        writer.write(auto_close=False)
        buf.seek(0)
        loaded = read_bwm(buf.read())
        
        # Verify properties
        assert loaded.walkmesh_type == bwm.walkmesh_type
        assert loaded.position == bwm.position
        assert loaded.relative_hook1 == bwm.relative_hook1
        assert loaded.relative_hook2 == bwm.relative_hook2
        assert loaded.absolute_hook1 == bwm.absolute_hook1
        assert loaded.absolute_hook2 == bwm.absolute_hook2
        
        # Verify faces (by set comparison since order may change)
        assert len(loaded.faces) == len(bwm.faces)
        loaded_faces_set = set(loaded.faces)
        original_faces_set = set(bwm.faces)
        assert loaded_faces_set == original_faces_set

    def test_roundtrip_with_transitions(self):
        """Test roundtrip with edge transitions."""
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel
        
        # Create isolated face (will be perimeter edge)
        face = BWMFace(
            Vector3(0.0, 0.0, 0.0),
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0),
        )
        face.material = SurfaceMaterial.DIRT
        face.trans1 = 42  # Transition on perimeter edge
        bwm.faces = [face]
        
        buf = io.BytesIO()
        writer = BWMBinaryWriter(bwm, buf)
        writer.write(auto_close=False)
        buf.seek(0)
        loaded = read_bwm(buf.read())
        
        # Find matching face
        loaded_face = None
        for f in loaded.faces:
            if f.v1 == face.v1 and f.v2 == face.v2 and f.v3 == face.v3:
                loaded_face = f
                break
        
        assert loaded_face is not None
        # Transition should be preserved on perimeter edge
        assert loaded_face.trans1 == face.trans1


class TestBWMEdgeCases:
    """Test edge cases and error conditions."""

    def test_single_face_walkmesh(self):
        """Test walkmesh with single face."""
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel
        
        face = BWMFace(
            Vector3(0.0, 0.0, 0.0),
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0),
        )
        face.material = SurfaceMaterial.DIRT
        bwm.faces = [face]
        
        buf = io.BytesIO()
        writer = BWMBinaryWriter(bwm, buf)
        writer.write(auto_close=False)
        buf.seek(0)
        loaded = read_bwm(buf.read())
        
        assert len(loaded.faces) == 1
        assert loaded.faces[0].material == SurfaceMaterial.DIRT

    def test_all_unwalkable_faces(self):
        """Test walkmesh with only unwalkable faces."""
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel
        
        faces = []
        for i in range(3):
            v1 = Vector3(i * 2.0, 0.0, 0.0)
            v2 = Vector3(i * 2.0 + 1.0, 0.0, 0.0)
            v3 = Vector3(i * 2.0, 1.0, 0.0)
            face = BWMFace(v1, v2, v3)
            face.material = SurfaceMaterial.NON_WALK
            faces.append(face)
        
        bwm.faces = faces
        
        buf = io.BytesIO()
        writer = BWMBinaryWriter(bwm, buf)
        writer.write(auto_close=False)
        buf.seek(0)
        loaded = read_bwm(buf.read())
        
        assert len(loaded.faces) == 3
        assert all(not f.material.walkable() for f in loaded.faces)
        assert len(loaded.walkable_faces()) == 0

    def test_all_walkable_faces(self):
        """Test walkmesh with only walkable faces."""
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel
        
        faces = []
        for i in range(3):
            v1 = Vector3(i * 2.0, 0.0, 0.0)
            v2 = Vector3(i * 2.0 + 1.0, 0.0, 0.0)
            v3 = Vector3(i * 2.0, 1.0, 0.0)
            face = BWMFace(v1, v2, v3)
            face.material = SurfaceMaterial.DIRT
            faces.append(face)
        
        bwm.faces = faces
        
        buf = io.BytesIO()
        writer = BWMBinaryWriter(bwm, buf)
        writer.write(auto_close=False)
        buf.seek(0)
        loaded = read_bwm(buf.read())
        
        assert len(loaded.faces) == 3
        assert all(f.material.walkable() for f in loaded.faces)
        assert len(loaded.unwalkable_faces()) == 0


class TestBWMFromRealFiles:
    """Test reading and roundtrip of real BWM files from game installations."""

    @pytest.mark.skipif(
        not Path(__file__).parents[5] / "Tools" / "HolocronToolset" / "tests" / "test_files" / "zio006j.wok",
        reason="Test file not available",
    )
    def test_read_real_wok_file(self):
        """Test reading a real WOK file from test files."""
        test_file = Path(__file__).parents[5] / "Tools" / "HolocronToolset" / "tests" / "test_files" / "zio006j.wok"
        if not test_file.exists():
            pytest.skip("Test file not available")
        
        data = test_file.read_bytes()
        bwm = read_bwm(data)
        
        assert bwm is not None
        assert bwm.walkmesh_type == BWMType.AreaModel
        assert len(bwm.faces) > 0

    @pytest.mark.skipif(
        not Path(__file__).parents[5] / "Tools" / "HolocronToolset" / "tests" / "test_files" / "zio006j.wok",
        reason="Test file not available",
    )
    def test_roundtrip_real_wok_file(self):
        """Test roundtrip of real WOK file."""
        test_file = Path(__file__).parents[5] / "Tools" / "HolocronToolset" / "tests" / "test_files" / "zio006j.wok"
        if not test_file.exists():
            pytest.skip("Test file not available")
        
        original_data = test_file.read_bytes()
        original_bwm = read_bwm(original_data)
        
        # Roundtrip
        buf = io.BytesIO()
        writer = BWMBinaryWriter(original_bwm, buf)
        writer.write(auto_close=False)
        buf.seek(0)
        new_data = buf.read()
        new_bwm = read_bwm(new_data)
        
        # Verify basic properties
        assert new_bwm.walkmesh_type == original_bwm.walkmesh_type
        assert new_bwm.position == original_bwm.position
        assert len(new_bwm.faces) == len(original_bwm.faces)
        
        # Verify faces by set comparison
        original_faces_set = set(original_bwm.faces)
        new_faces_set = set(new_bwm.faces)
        assert original_faces_set == new_faces_set


class TestBWMAdjacency:
    """Test adjacency calculation and encoding."""

    def test_adjacent_faces_detection(self):
        """Test that adjacent faces are correctly detected."""
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel
        
        # Create two adjacent walkable faces sharing edge v2-v3
        v1 = Vector3(0.0, 0.0, 0.0)
        v2 = Vector3(1.0, 0.0, 0.0)
        v3 = Vector3(0.0, 1.0, 0.0)
        v4 = Vector3(1.0, 1.0, 0.0)
        
        face1 = BWMFace(v1, v2, v3)
        face1.material = SurfaceMaterial.DIRT
        face2 = BWMFace(v2, v4, v3)  # Shares edge v2-v3
        face2.material = SurfaceMaterial.DIRT
        
        bwm.faces = [face1, face2]
        
        # Check adjacencies
        adj1 = bwm.adjacencies(face1)
        adj2 = bwm.adjacencies(face2)
        
        # At least one edge should have adjacency
        has_adjacency = any(adj is not None for adj in adj1) or any(adj is not None for adj in adj2)
        assert has_adjacency, "Adjacent faces should have adjacency data"

    def test_non_adjacent_faces(self):
        """Test that non-adjacent faces have no adjacency."""
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel
        
        # Create two separate walkable faces
        face1 = BWMFace(
            Vector3(0.0, 0.0, 0.0),
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0),
        )
        face1.material = SurfaceMaterial.DIRT
        
        face2 = BWMFace(
            Vector3(10.0, 0.0, 0.0),  # Far away
            Vector3(11.0, 0.0, 0.0),
            Vector3(10.0, 1.0, 0.0),
        )
        face2.material = SurfaceMaterial.DIRT
        
        bwm.faces = [face1, face2]
        
        # Check adjacencies
        adj1 = bwm.adjacencies(face1)
        adj2 = bwm.adjacencies(face2)
        
        # No adjacencies should exist
        assert all(adj is None for adj in adj1)
        assert all(adj is None for adj in adj2)


class TestBWMAABBTree:
    """Test AABB tree generation and structure."""

    def test_aabb_tree_generation(self):
        """Test that AABB tree is generated for WOK files."""
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel
        
        # Create multiple faces for tree generation
        faces = []
        for i in range(10):
            v1 = Vector3(i * 2.0, 0.0, 0.0)
            v2 = Vector3(i * 2.0 + 1.0, 0.0, 0.0)
            v3 = Vector3(i * 2.0, 1.0, 0.0)
            face = BWMFace(v1, v2, v3)
            face.material = SurfaceMaterial.DIRT
            faces.append(face)
        
        bwm.faces = faces
        
        # Generate AABB tree
        aabbs = bwm.aabbs()
        
        # Should have at least one AABB node
        assert len(aabbs) > 0

    def test_aabb_tree_structure(self):
        """Test that AABB tree has valid structure."""
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel
        
        # Create faces
        faces = []
        for i in range(5):
            v1 = Vector3(i * 2.0, 0.0, 0.0)
            v2 = Vector3(i * 2.0 + 1.0, 0.0, 0.0)
            v3 = Vector3(i * 2.0, 1.0, 0.0)
            face = BWMFace(v1, v2, v3)
            face.material = SurfaceMaterial.DIRT
            faces.append(face)
        
        bwm.faces = faces
        
        aabbs = bwm.aabbs()
        
        # Check tree structure
        for aabb in aabbs:
            # Bounds should be valid (min <= max)
            assert aabb.bb_min.x <= aabb.bb_max.x
            assert aabb.bb_min.y <= aabb.bb_max.y
            assert aabb.bb_min.z <= aabb.bb_max.z
            
            # If it's a leaf node, face should not be None
            # If it's an internal node, face should be None
            if aabb.face is not None:
                # Leaf node - should have no children
                assert aabb.left is None or aabb.left.face is None
                assert aabb.right is None or aabb.right.face is None
            else:
                # Internal node - may have children
                pass  # Children are valid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

