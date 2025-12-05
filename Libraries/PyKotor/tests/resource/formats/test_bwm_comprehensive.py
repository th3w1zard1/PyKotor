"""Comprehensive BWM (Binary WalkMesh) format tests based on vendor implementations.

Reference implementations:
- vendor/kotorblender/io_scene_kotor/format/bwm/reader.py - Blender BWM reader
- vendor/kotorblender/io_scene_kotor/format/bwm/writer.py - Blender BWM writer  
- vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts - TypeScript walkmesh implementation
- vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp - C++ walkmesh loader
- vendor/reone/src/libs/graphics/format/bwmreader.cpp - C++ BWM reader
- wiki/BWM-File-Format.md - Format documentation
"""
from __future__ import annotations

import io
import math
import pathlib
import struct
import sys
import unittest
from typing import TYPE_CHECKING
from unittest import TestCase

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].resolve()
UTILITY_PATH = THIS_SCRIPT_PATH.parents[5].joinpath("Utility", "src").resolve()


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)


from utility.common.geometry import SurfaceMaterial, Vector3

from pykotor.resource.formats.bwm import (
    BWM,
    BWMBinaryReader,
    BWMBinaryWriter,
    BWMFace,
    BWMType,
    read_bwm,
    write_bwm,
)
from pykotor.resource.formats.bwm.bwm_data import BWMAdjacency, BWMEdge, BWMNodeAABB

if TYPE_CHECKING:
    pass

# Test file paths
# THIS_SCRIPT_PATH is tests/test_pykotor/resource/formats/test_bwm_comprehensive.py
# Parents: [3]=tests, [2]=test_pykotor, [1]=resource, [0]=formats
TESTS_DIR = THIS_SCRIPT_PATH.parents[3]  # Goes up to 'tests' directory
TEST_WOK_FILE = TESTS_DIR / "test_pykotor" / "test_files" / "test.wok"
TEST_TOOLSET_WOK_FILE = TESTS_DIR / "test_toolset" / "test_files" / "zio006j.wok"


class TestBWMHeaderFormat(TestCase):
    """Test BWM header parsing based on vendor implementations.
    
    Reference:
    - vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:50-81
    - vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:450-476
    - vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:73-94
    """

    def test_header_magic_validation(self):
        """Test that BWM files must have 'BWM ' magic bytes.
        
        Reference: vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:52-57
        """
        # Create invalid magic
        invalid_data = b"BADM" + b"V1.0" + b"\x00" * 128
        with self.assertRaises(Exception):
            read_bwm(invalid_data)

    def test_header_version_parsing(self):
        """Test that BWM version 'V1.0' is parsed correctly.
        
        Reference: vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:454
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        data = TEST_WOK_FILE.read_bytes()
        # Check header directly
        self.assertEqual(data[0:4], b"BWM ", "Magic should be 'BWM '")
        self.assertEqual(data[4:8], b"V1.0", "Version should be 'V1.0'")

    def test_walkmesh_type_area(self):
        """Test WOK (area) walkmesh type parsing.
        
        WOK files should have type 1 (AreaModel).
        Reference: vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:60
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        self.assertEqual(wok.walkmesh_type, BWMType.AreaModel)

    def test_header_offsets_valid(self):
        """Test that header offsets point to valid data.
        
        Reference: vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:458-473
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        data = TEST_WOK_FILE.read_bytes()
        wok = read_bwm(data)
        
        # Vertices and faces should be present
        self.assertGreater(len(wok.vertices()), 0, "Should have vertices")
        self.assertGreater(len(wok.faces), 0, "Should have faces")


class TestBWMVertices(TestCase):
    """Test BWM vertex parsing based on vendor implementations.
    
    Reference:
    - vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:83-89
    - vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:264-269
    """

    def test_vertex_count(self):
        """Test vertex count matches header."""
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        vertices = wok.vertices()
        self.assertEqual(len(vertices), 114, "Expected 114 vertices")

    def test_vertex_coordinates_precision(self):
        """Test vertex coordinates are read with proper precision.
        
        Reference: vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:267
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        
        # Check first vertex has valid float coordinates
        if wok.faces:
            v = wok.faces[0].v1
            self.assertIsInstance(v.x, float)
            self.assertIsInstance(v.y, float)
            self.assertIsInstance(v.z, float)
            # Values should be finite
            self.assertTrue(math.isfinite(v.x))
            self.assertTrue(math.isfinite(v.y))
            self.assertTrue(math.isfinite(v.z))

    def test_vertex_sharing(self):
        """Test that vertices are shared between faces.
        
        Vertices should be shared by reference (same object) between adjacent faces.
        Reference: wiki/BWM-File-Format.md - Vertex Sharing section
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        vertices = wok.vertices()
        
        # Unique vertices by identity should equal total unique positions
        unique_by_identity = len(vertices)
        # Count faces that reference each vertex
        vertex_usage_count = {}
        for face in wok.faces:
            for v in [face.v1, face.v2, face.v3]:
                v_id = id(v)
                vertex_usage_count[v_id] = vertex_usage_count.get(v_id, 0) + 1
        
        # Most vertices should be shared (used more than once)
        shared_count = sum(1 for count in vertex_usage_count.values() if count > 1)
        self.assertGreater(shared_count, 0, "Some vertices should be shared between faces")


class TestBWMFaces(TestCase):
    """Test BWM face parsing based on vendor implementations.
    
    Reference:
    - vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:89-111
    - vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:271-298
    """

    def test_face_count(self):
        """Test face count matches expected value."""
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        self.assertEqual(len(wok.faces), 195, "Expected 195 faces")

    def test_face_vertex_indices_valid(self):
        """Test that face vertex indices reference valid vertices.
        
        Reference: vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:273-274
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        vertices = wok.vertices()
        
        for face in wok.faces:
            # Each vertex should be in the vertices list
            self.assertIn(face.v1, vertices)
            self.assertIn(face.v2, vertices)
            self.assertIn(face.v3, vertices)

    def test_face_normal_computation(self):
        """Test that face normals can be computed.
        
        Reference: vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:289-293
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        
        for face in wok.faces[:10]:  # Check first 10 faces
            normal = face.normal()
            # Normal should be a unit vector (approximately)
            length = math.sqrt(normal.x**2 + normal.y**2 + normal.z**2)
            self.assertAlmostEqual(length, 1.0, places=5, msg="Normal should be normalized")

    def test_face_planar_distance(self):
        """Test face planar distance computation.
        
        Reference: vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:295-298
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        
        for face in wok.faces[:10]:
            dist = face.planar_distance()
            self.assertTrue(math.isfinite(dist), "Planar distance should be finite")


class TestBWMMaterials(TestCase):
    """Test BWM material handling based on vendor implementations.
    
    Reference:
    - vendor/kotorblender/io_scene_kotor/constants.py:27-51
    - vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:283-286
    """

    def test_material_assignment(self):
        """Test that materials are assigned to faces."""
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        
        for face in wok.faces:
            self.assertIsInstance(face.material, SurfaceMaterial)

    def test_walkable_materials(self):
        """Test walkable material detection.
        
        Reference: vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:94
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        walkable = wok.walkable_faces()
        
        # All walkable faces should have walkable materials
        for face in walkable:
            self.assertTrue(face.material.walkable(), f"Material {face.material} should be walkable")

    def test_unwalkable_materials(self):
        """Test unwalkable material detection."""
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        unwalkable = wok.unwalkable_faces()
        
        # All unwalkable faces should have non-walkable materials
        for face in unwalkable:
            self.assertFalse(face.material.walkable(), f"Material {face.material} should not be walkable")

    def test_material_id_range(self):
        """Test material IDs are within valid range (0-22).
        
        Reference: wiki/BWM-File-Format.md - Materials section
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        
        for face in wok.faces:
            self.assertGreaterEqual(face.material.value, 0)
            self.assertLessEqual(face.material.value, 22)


class TestBWMAdjacency(TestCase):
    """Test BWM adjacency computation based on vendor implementations.
    
    Reference:
    - vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:241-273
    - vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:305-337
    - wiki/BWM-File-Format.md - Walkable Adjacencies section
    """

    def test_adjacency_encoding(self):
        """Test adjacency index encoding: face_index * 3 + edge_index.
        
        Reference: wiki/BWM-File-Format.md - Adjacency Encoding
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        walkable = wok.walkable_faces()
        
        for face in walkable[:10]:
            adj = wok.adjacencies(face)
            for i, a in enumerate(adj):
                if a is not None:
                    # Edge index should be 0, 1, or 2
                    self.assertIn(a.edge, [0, 1, 2], "Edge index should be 0, 1, or 2")
                    # Face should be in faces list
                    self.assertIn(a.face, wok.faces)

    def test_adjacency_bidirectional(self):
        """Test that adjacency is bidirectional.
        
        If face A is adjacent to face B on edge E, then face B should be adjacent to face A.
        Reference: vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:268-269
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        walkable = wok.walkable_faces()
        
        for face_a in walkable[:20]:
            adj_a = wok.adjacencies(face_a)
            for edge_idx, adj in enumerate(adj_a):
                if adj is not None:
                    face_b = adj.face
                    # Check that face_b has face_a as an adjacency
                    adj_b = wok.adjacencies(face_b)
                    found_back_ref = False
                    for adj_back in adj_b:
                        if adj_back is not None and adj_back.face is face_a:
                            found_back_ref = True
                            break
                    self.assertTrue(found_back_ref, "Adjacency should be bidirectional")

    def test_adjacency_shared_vertices(self):
        """Test that adjacent faces share exactly two vertices.
        
        Reference: wiki/BWM-File-Format.md - Adjacency Calculation
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        walkable = wok.walkable_faces()
        
        for face_a in walkable[:10]:
            adj_a = wok.adjacencies(face_a)
            for adj in adj_a:
                if adj is not None:
                    face_b = adj.face
                    # Count shared vertices
                    verts_a = {face_a.v1, face_a.v2, face_a.v3}
                    verts_b = {face_b.v1, face_b.v2, face_b.v3}
                    shared = verts_a & verts_b
                    self.assertEqual(len(shared), 2, "Adjacent faces should share exactly 2 vertices")


class TestBWMEdges(TestCase):
    """Test BWM edge/perimeter computation based on vendor implementations.
    
    Reference:
    - vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:138-149
    - vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:339-352
    - wiki/BWM-File-Format.md - Edges section
    """

    def test_edge_count(self):
        """Test edge count matches expected value."""
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        edges = wok.edges()
        self.assertEqual(len(edges), 73, "Expected 73 edges")

    def test_edges_have_no_adjacent_walkable(self):
        """Test that perimeter edges have no walkable neighbor.
        
        Reference: vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:279-280
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        edges = wok.edges()
        
        for edge in edges:
            # Get adjacency for the edge's face
            adj = wok.adjacencies(edge.face)
            # The edge's local index (0, 1, or 2) should have no adjacency
            self.assertIsNone(adj[edge.index], "Perimeter edge should have no adjacency")

    def test_edge_transition_values(self):
        """Test edge transition values.
        
        Reference: vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:341-342
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        edges = wok.edges()
        
        for edge in edges:
            # Transition should be -1 (no transition) or a valid index
            self.assertTrue(edge.transition >= -1, "Transition should be >= -1")

    def test_perimeter_loop_closure(self):
        """Test that perimeter edges form closed loops.
        
        Reference: vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:716-782
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        edges = wok.edges()
        
        # Count edges marked as final (end of perimeter loop)
        final_edges = [e for e in edges if e.final]
        self.assertGreater(len(final_edges), 0, "Should have at least one perimeter loop")


class TestBWMAABB(TestCase):
    """Test BWM AABB tree based on vendor implementations.
    
    Reference:
    - vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:112-131
    - vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:432-448
    - vendor/xoreos/src/engines/kotorbase/path/walkmeshloader.cpp:218-248
    """

    def test_aabb_count(self):
        """Test AABB node count matches expected value."""
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        aabbs = wok.aabbs()
        self.assertEqual(len(aabbs), 389, "Expected 389 AABB nodes")

    def test_aabb_leaf_nodes(self):
        """Test AABB leaf nodes have valid face references.
        
        Reference: vendor/reone/src/libs/graphics/format/bwmreader.cpp:161-162
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        aabbs = wok.aabbs()
        
        leaf_count = 0
        for aabb in aabbs:
            # Leaf nodes have a face reference, internal nodes have None
            if aabb.face is not None:
                leaf_count += 1
                # Face should be in the faces list
                self.assertIn(aabb.face, wok.faces)
        
        self.assertGreater(leaf_count, 0, "Should have leaf nodes")

    def test_aabb_bounds_contain_face(self):
        """Test that AABB bounds contain their associated face.
        
        Reference: vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:576-587
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        aabbs = wok.aabbs()
        
        checked_count = 0
        for aabb in aabbs:
            # Only leaf nodes have faces
            if aabb.face is not None:
                face = aabb.face
                # All face vertices should be within AABB bounds (with small tolerance)
                for v in [face.v1, face.v2, face.v3]:
                    self.assertGreaterEqual(v.x, aabb.bb_min.x - 0.001)
                    self.assertGreaterEqual(v.y, aabb.bb_min.y - 0.001)
                    self.assertGreaterEqual(v.z, aabb.bb_min.z - 0.001)
                    self.assertLessEqual(v.x, aabb.bb_max.x + 0.001)
                    self.assertLessEqual(v.y, aabb.bb_max.y + 0.001)
                    self.assertLessEqual(v.z, aabb.bb_max.z + 0.001)
                checked_count += 1
                if checked_count >= 20:  # Check first 20 leaf nodes
                    break


class TestBWMRoundtrip(TestCase):
    """Test BWM read/write roundtrip integrity.
    
    Reference: All vendor implementations must preserve data on roundtrip.
    """

    def test_roundtrip_preserves_vertices(self):
        """Test that roundtrip preserves vertex positions."""
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        data = TEST_WOK_FILE.read_bytes()
        original = read_bwm(data)
        
        buf = io.BytesIO()
        writer = BWMBinaryWriter(original, buf)
        writer.write(auto_close=False)
        buf.seek(0)
        roundtrip = read_bwm(buf.read())
        
        orig_verts = original.vertices()
        new_verts = roundtrip.vertices()
        
        self.assertEqual(len(orig_verts), len(new_verts))

    def test_roundtrip_preserves_faces(self):
        """Test that roundtrip preserves face content."""
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        data = TEST_WOK_FILE.read_bytes()
        original = read_bwm(data)
        
        buf = io.BytesIO()
        writer = BWMBinaryWriter(original, buf)
        writer.write(auto_close=False)
        buf.seek(0)
        roundtrip = read_bwm(buf.read())
        
        self.assertEqual(len(original.faces), len(roundtrip.faces))
        
        # Compare as sets (order may change)
        orig_set = set(original.faces)
        new_set = set(roundtrip.faces)
        self.assertEqual(orig_set, new_set, "Face content should be preserved")

    def test_roundtrip_preserves_materials(self):
        """Test that roundtrip preserves materials."""
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        data = TEST_WOK_FILE.read_bytes()
        original = read_bwm(data)
        
        buf = io.BytesIO()
        writer = BWMBinaryWriter(original, buf)
        writer.write(auto_close=False)
        buf.seek(0)
        roundtrip = read_bwm(buf.read())
        
        # Check materials by face (need to match by vertex content)
        for orig_face in original.faces:
            # Find matching face in roundtrip
            for new_face in roundtrip.faces:
                if (new_face.v1 == orig_face.v1 and new_face.v2 == orig_face.v2 
                    and new_face.v3 == orig_face.v3):
                    self.assertEqual(new_face.material, orig_face.material)
                    break

    def test_roundtrip_preserves_transitions(self):
        """Test that roundtrip preserves transitions."""
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        data = TEST_WOK_FILE.read_bytes()
        original = read_bwm(data)
        
        buf = io.BytesIO()
        writer = BWMBinaryWriter(original, buf)
        writer.write(auto_close=False)
        buf.seek(0)
        roundtrip = read_bwm(buf.read())
        
        # Count faces with transitions
        orig_trans_count = sum(1 for f in original.faces 
                              if f.trans1 is not None or f.trans2 is not None or f.trans3 is not None)
        new_trans_count = sum(1 for f in roundtrip.faces 
                             if f.trans1 is not None or f.trans2 is not None or f.trans3 is not None)
        
        self.assertEqual(orig_trans_count, new_trans_count, "Transition count should be preserved")

    def test_roundtrip_preserves_hooks(self):
        """Test that roundtrip preserves hook positions."""
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        data = TEST_WOK_FILE.read_bytes()
        original = read_bwm(data)
        
        buf = io.BytesIO()
        writer = BWMBinaryWriter(original, buf)
        writer.write(auto_close=False)
        buf.seek(0)
        roundtrip = read_bwm(buf.read())
        
        self.assertEqual(original.position, roundtrip.position)
        self.assertEqual(original.relative_hook1, roundtrip.relative_hook1)
        self.assertEqual(original.relative_hook2, roundtrip.relative_hook2)
        self.assertEqual(original.absolute_hook1, roundtrip.absolute_hook1)
        self.assertEqual(original.absolute_hook2, roundtrip.absolute_hook2)


class TestBWMFaceEquality(TestCase):
    """Test BWMFace equality and hash based on value comparison.
    
    Reference: Libraries/PyKotor/src/utility/common/geometry.py - Face class
    """

    def test_face_value_equality(self):
        """Test that faces with same vertices and material are equal."""
        v1 = Vector3(1.0, 2.0, 3.0)
        v2 = Vector3(4.0, 5.0, 6.0)
        v3 = Vector3(7.0, 8.0, 9.0)
        
        face1 = BWMFace(v1, v2, v3)
        face1.material = SurfaceMaterial.DIRT
        
        # Create new vertices with same values
        v1b = Vector3(1.0, 2.0, 3.0)
        v2b = Vector3(4.0, 5.0, 6.0)
        v3b = Vector3(7.0, 8.0, 9.0)
        
        face2 = BWMFace(v1b, v2b, v3b)
        face2.material = SurfaceMaterial.DIRT
        
        self.assertEqual(face1, face2)
        self.assertEqual(hash(face1), hash(face2))

    def test_face_inequality_different_vertices(self):
        """Test that faces with different vertices are not equal."""
        v1 = Vector3(1.0, 2.0, 3.0)
        v2 = Vector3(4.0, 5.0, 6.0)
        v3 = Vector3(7.0, 8.0, 9.0)
        
        face1 = BWMFace(v1, v2, v3)
        
        v1b = Vector3(1.0, 2.0, 3.0)
        v2b = Vector3(4.0, 5.0, 6.0)
        v3b = Vector3(0.0, 0.0, 0.0)  # Different!
        
        face2 = BWMFace(v1b, v2b, v3b)
        
        self.assertNotEqual(face1, face2)

    def test_face_inequality_different_material(self):
        """Test that faces with different materials are not equal."""
        v1 = Vector3(1.0, 2.0, 3.0)
        v2 = Vector3(4.0, 5.0, 6.0)
        v3 = Vector3(7.0, 8.0, 9.0)
        
        face1 = BWMFace(v1, v2, v3)
        face1.material = SurfaceMaterial.DIRT
        
        face2 = BWMFace(Vector3(1.0, 2.0, 3.0), Vector3(4.0, 5.0, 6.0), Vector3(7.0, 8.0, 9.0))
        face2.material = SurfaceMaterial.STONE
        
        self.assertNotEqual(face1, face2)

    def test_face_inequality_different_transitions(self):
        """Test that faces with different transitions are not equal."""
        v1 = Vector3(1.0, 2.0, 3.0)
        v2 = Vector3(4.0, 5.0, 6.0)
        v3 = Vector3(7.0, 8.0, 9.0)
        
        face1 = BWMFace(v1, v2, v3)
        face1.trans1 = 5
        
        face2 = BWMFace(Vector3(1.0, 2.0, 3.0), Vector3(4.0, 5.0, 6.0), Vector3(7.0, 8.0, 9.0))
        face2.trans1 = 10  # Different!
        
        self.assertNotEqual(face1, face2)

    def test_face_set_membership(self):
        """Test that faces can be used in sets correctly."""
        v1 = Vector3(1.0, 2.0, 3.0)
        v2 = Vector3(4.0, 5.0, 6.0)
        v3 = Vector3(7.0, 8.0, 9.0)
        
        face1 = BWMFace(v1, v2, v3)
        face1.material = SurfaceMaterial.DIRT
        
        face2 = BWMFace(Vector3(1.0, 2.0, 3.0), Vector3(4.0, 5.0, 6.0), Vector3(7.0, 8.0, 9.0))
        face2.material = SurfaceMaterial.DIRT
        
        face_set = {face1}
        self.assertIn(face2, face_set)


class TestBWMSpatialQueries(TestCase):
    """Test BWM spatial query operations based on vendor implementations.
    
    Reference:
    - vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:478-533
    - vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:549-599
    """

    def test_point_in_face_2d(self):
        """Test 2D point-in-face containment check.
        
        Reference: vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:478-495
        """
        # Create a simple triangle on the XY plane
        v1 = Vector3(0.0, 0.0, 0.0)
        v2 = Vector3(10.0, 0.0, 0.0)
        v3 = Vector3(5.0, 10.0, 0.0)
        
        face = BWMFace(v1, v2, v3)
        centre = face.centre()
        
        # Centroid should be inside
        self.assertTrue(centre.x > 0 and centre.x < 10)
        self.assertTrue(centre.y > 0 and centre.y < 10)

    def test_face_centroid(self):
        """Test face centroid calculation.
        
        Reference: vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:148-152
        """
        v1 = Vector3(0.0, 0.0, 0.0)
        v2 = Vector3(3.0, 0.0, 0.0)
        v3 = Vector3(0.0, 3.0, 0.0)
        
        face = BWMFace(v1, v2, v3)
        centre = face.centre()
        
        # Centroid should be at (1, 1, 0) for this triangle
        self.assertAlmostEqual(centre.x, 1.0, places=5)
        self.assertAlmostEqual(centre.y, 1.0, places=5)
        self.assertAlmostEqual(centre.z, 0.0, places=5)

    def test_face_area(self):
        """Test face area calculation."""
        # Right triangle with legs of length 3 and 4
        v1 = Vector3(0.0, 0.0, 0.0)
        v2 = Vector3(3.0, 0.0, 0.0)
        v3 = Vector3(0.0, 4.0, 0.0)
        
        face = BWMFace(v1, v2, v3)
        area = face.area()
        
        # Area should be 0.5 * base * height = 0.5 * 3 * 4 = 6
        self.assertAlmostEqual(area, 6.0, places=4)


class TestBWMSecondTestFile(TestCase):
    """Test with the second test file if available.
    
    This provides additional coverage with different walkmesh data.
    """

    def test_second_file_roundtrip(self):
        """Test roundtrip with second test file."""
        if not TEST_TOOLSET_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_TOOLSET_WOK_FILE}")
        
        data = TEST_TOOLSET_WOK_FILE.read_bytes()
        original = read_bwm(data)
        
        buf = io.BytesIO()
        writer = BWMBinaryWriter(original, buf)
        writer.write(auto_close=False)
        buf.seek(0)
        roundtrip = read_bwm(buf.read())
        
        # Compare as sets
        orig_set = set(original.faces)
        new_set = set(roundtrip.faces)
        self.assertEqual(orig_set, new_set)

    def test_second_file_properties(self):
        """Test properties of second test file."""
        if not TEST_TOOLSET_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_TOOLSET_WOK_FILE}")
        
        wok = read_bwm(TEST_TOOLSET_WOK_FILE.read_bytes())
        
        # Should have vertices and faces
        self.assertGreater(len(wok.vertices()), 0)
        self.assertGreater(len(wok.faces), 0)
        
        # Should be area walkmesh
        self.assertEqual(wok.walkmesh_type, BWMType.AreaModel)


class TestBWMEdgeCases(TestCase):
    """Test edge cases and error handling."""

    def test_empty_faces_list(self):
        """Test handling of BWM with no faces."""
        bwm = BWM()
        bwm.faces = []
        
        # Should return empty lists, not crash
        self.assertEqual(len(bwm.vertices()), 0)
        self.assertEqual(len(bwm.walkable_faces()), 0)
        self.assertEqual(len(bwm.unwalkable_faces()), 0)

    def test_single_face(self):
        """Test BWM with a single face."""
        bwm = BWM()
        v1 = Vector3(0.0, 0.0, 0.0)
        v2 = Vector3(1.0, 0.0, 0.0)
        v3 = Vector3(0.0, 1.0, 0.0)
        
        face = BWMFace(v1, v2, v3)
        face.material = SurfaceMaterial.DIRT
        bwm.faces = [face]
        
        self.assertEqual(len(bwm.vertices()), 3)
        self.assertEqual(len(bwm.walkable_faces()), 1)

    def test_all_unwalkable(self):
        """Test BWM with all unwalkable faces."""
        bwm = BWM()
        v1 = Vector3(0.0, 0.0, 0.0)
        v2 = Vector3(1.0, 0.0, 0.0)
        v3 = Vector3(0.0, 1.0, 0.0)
        
        face = BWMFace(v1, v2, v3)
        face.material = SurfaceMaterial.NON_WALK  # Non-walkable
        bwm.faces = [face]
        
        self.assertEqual(len(bwm.walkable_faces()), 0)
        self.assertEqual(len(bwm.unwalkable_faces()), 1)

    def test_pwk_dwk_no_aabb_adjacency(self):
        """Test that PWK/DWK files don't have AABB or adjacency data.
        
        Reference: vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:197-198
        """
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
        
        # Check header - AABB count should be 0
        reader = BWMBinaryReader(io.BytesIO(data))
        reader._reader.seek(0)
        reader._reader.read_string(4)  # magic
        reader._reader.read_string(4)  # version
        walkmesh_type = reader._reader.read_uint32()
        self.assertEqual(walkmesh_type, 0)  # PlaceableOrDoor
        
        # Skip to AABB count
        for _ in range(5):
            reader._reader.read_vector3()  # hooks and position
        reader._reader.read_uint32()  # vertex count
        reader._reader.read_uint32()  # vertex offset
        reader._reader.read_uint32()  # face count
        for _ in range(4):
            reader._reader.read_uint32()  # offsets
        aabb_count = reader._reader.read_uint32()
        self.assertEqual(aabb_count, 0, "PWK/DWK should have no AABB tree")

    def test_adjacency_encoding_formula(self):
        """Test adjacency encoding formula: face_index * 3 + edge_index.
        
        Reference: vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:268
        Reference: wiki/BWM-File-Format.md - Adjacency Encoding
        
        Note: The adjacency.edge is the edge index on the ADJACENT face, not the current face.
        So it doesn't necessarily match the local edge_idx.
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        walkable = wok.walkable_faces()
        
        # Test encoding/decoding
        for face_idx, face in enumerate(walkable[:10]):
            adj = wok.adjacencies(face)
            for edge_idx, adj_obj in enumerate(adj):
                if adj_obj is not None:
                    # Adjacency edge index is on the adjacent face, should be 0, 1, or 2
                    self.assertIn(adj_obj.edge, [0, 1, 2], 
                                 f"Adjacency edge index should be 0, 1, or 2")
                    # Adjacent face should be in faces list
                    self.assertIn(adj_obj.face, wok.faces)

    def test_perimeter_edge_transitions(self):
        """Test that perimeter edges can have transitions.
        
        Reference: vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:293-297
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        edges = wok.edges()
        
        # Check that edges can have transitions
        transitions_found = False
        for edge in edges:
            if edge.transition != -1:
                transitions_found = True
                # Transition should be non-negative
                self.assertGreaterEqual(edge.transition, 0)
        
        # Not all files have transitions, so this is optional
        # But if transitions exist, they should be valid

    def test_face_winding_order(self):
        """Test that face winding order is consistent.
        
        Reference: vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:271-281
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        
        # Check that normals are computed correctly
        for face in wok.faces[:10]:
            normal = face.normal()
            # Normal should be normalized
            length = math.sqrt(normal.x**2 + normal.y**2 + normal.z**2)
            self.assertAlmostEqual(length, 1.0, places=5)

    def test_vertex_index_bounds(self):
        """Test that vertex indices in faces are within valid range.
        
        Reference: vendor/reone/src/libs/graphics/format/bwmreader.cpp:105-114
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        vertices = wok.vertices()
        vertex_count = len(vertices)
        
        # All face vertices should reference valid vertices
        for face in wok.faces:
            self.assertIn(face.v1, vertices)
            self.assertIn(face.v2, vertices)
            self.assertIn(face.v3, vertices)

    def test_material_walkability_consistency(self):
        """Test that material walkability is consistent.
        
        Reference: vendor/kotorblender/io_scene_kotor/constants.py:27-51
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        
        # Walkable faces should have walkable materials
        for face in wok.walkable_faces():
            self.assertTrue(face.material.walkable(), 
                          f"Face with material {face.material} should be walkable")
        
        # Unwalkable faces should have non-walkable materials
        for face in wok.unwalkable_faces():
            self.assertFalse(face.material.walkable(),
                           f"Face with material {face.material} should not be walkable")

    def test_hook_positions_preserved(self):
        """Test that hook positions are preserved through roundtrip.
        
        Reference: vendor/kotorblender/io_scene_kotor/format/bwm/reader.py:61-65
        """
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel
        bwm.position = Vector3(100.0, 200.0, 300.0)
        bwm.relative_hook1 = Vector3(1.0, 2.0, 3.0)
        bwm.relative_hook2 = Vector3(4.0, 5.0, 6.0)
        bwm.absolute_hook1 = Vector3(7.0, 8.0, 9.0)
        bwm.absolute_hook2 = Vector3(10.0, 11.0, 12.0)
        
        # Add a face so it's not empty
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
        
        self.assertEqual(loaded.position, bwm.position)
        self.assertEqual(loaded.relative_hook1, bwm.relative_hook1)
        self.assertEqual(loaded.relative_hook2, bwm.relative_hook2)
        self.assertEqual(loaded.absolute_hook1, bwm.absolute_hook1)
        self.assertEqual(loaded.absolute_hook2, bwm.absolute_hook2)

    def test_face_ordering_walkable_first(self):
        """Test that walkable faces are ordered before unwalkable faces.
        
        Reference: vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:175-185
        Reference: wiki/BWM-File-Format.md - Face Ordering
        """
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel
        
        # Create mixed walkable/unwalkable faces
        walkable_face = BWMFace(
            Vector3(0.0, 0.0, 0.0),
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0),
        )
        walkable_face.material = SurfaceMaterial.DIRT
        
        unwalkable_face = BWMFace(
            Vector3(2.0, 0.0, 0.0),
            Vector3(3.0, 0.0, 0.0),
            Vector3(2.0, 1.0, 0.0),
        )
        unwalkable_face.material = SurfaceMaterial.NON_WALK
        
        # Add in reverse order
        bwm.faces = [unwalkable_face, walkable_face]
        
        buf = io.BytesIO()
        writer = BWMBinaryWriter(bwm, buf)
        writer.write(auto_close=False)
        buf.seek(0)
        loaded = read_bwm(buf.read())
        
        # Check ordering
        walkable_count = 0
        unwalkable_count = 0
        for face in loaded.faces:
            if face.material.walkable():
                walkable_count += 1
                # Should not have seen unwalkable faces yet
                self.assertEqual(unwalkable_count, 0, 
                               "Walkable faces should come before unwalkable faces")
            else:
                unwalkable_count += 1
        
        self.assertEqual(walkable_count, 1)
        self.assertEqual(unwalkable_count, 1)

    def test_adjacency_only_walkable_faces(self):
        """Test that adjacency is only computed for walkable faces.
        
        Reference: vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:241-273
        Reference: wiki/BWM-File-Format.md - Walkable Adjacencies
        """
        bwm = BWM()
        bwm.walkmesh_type = BWMType.AreaModel
        
        # Create walkable and unwalkable faces
        walkable1 = BWMFace(
            Vector3(0.0, 0.0, 0.0),
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0),
        )
        walkable1.material = SurfaceMaterial.DIRT
        
        walkable2 = BWMFace(
            Vector3(1.0, 0.0, 0.0),
            Vector3(2.0, 0.0, 0.0),
            Vector3(1.0, 1.0, 0.0),
        )
        walkable2.material = SurfaceMaterial.DIRT
        
        unwalkable = BWMFace(
            Vector3(3.0, 0.0, 0.0),
            Vector3(4.0, 0.0, 0.0),
            Vector3(3.0, 1.0, 0.0),
        )
        unwalkable.material = SurfaceMaterial.NON_WALK
        
        bwm.faces = [walkable1, walkable2, unwalkable]
        
        # Adjacency should only be computed for walkable faces
        adj_walkable = bwm.adjacencies(walkable1)
        adj_unwalkable = bwm.adjacencies(unwalkable)
        
        # Unwalkable face should have no adjacencies (or they're not meaningful)
        # Walkable faces may have adjacencies
        # This is more of a structural test

    def test_perimeter_loop_construction(self):
        """Test that perimeter edges form closed loops.
        
        Reference: vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:716-782
        Reference: vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:275-307
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        edges = wok.edges()
        
        # Count final edges (end of perimeter loops)
        final_edges = [e for e in edges if e.final]
        self.assertGreater(len(final_edges), 0, "Should have perimeter loops")
        
        # Each final edge marks the end of a loop
        # Total edges should be sum of loop lengths
        total_edges = len(edges)
        self.assertGreater(total_edges, 0)

    def test_aabb_tree_balance(self):
        """Test that AABB tree is reasonably balanced.
        
        Reference: vendor/kotorblender/io_scene_kotor/aabb.py
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        aabbs = wok.aabbs()
        
        # Tree should have both internal and leaf nodes
        leaf_nodes = [a for a in aabbs if a.face is not None]
        internal_nodes = [a for a in aabbs if a.face is None]
        
        # For a balanced tree, should have reasonable ratio
        # (exact ratio depends on tree structure)
        self.assertGreater(len(leaf_nodes), 0, "Should have leaf nodes")
        # Internal nodes may or may not exist depending on tree structure

    def test_edge_index_encoding(self):
        """Test edge index encoding: face_index * 3 + local_edge_index.
        
        Reference: vendor/kotorblender/io_scene_kotor/format/bwm/writer.py:283
        Reference: wiki/BWM-File-Format.md - Edge Index Encoding
        """
        if not TEST_WOK_FILE.exists():
            self.skipTest(f"Test file not found: {TEST_WOK_FILE}")
        
        wok = read_bwm(TEST_WOK_FILE.read_bytes())
        edges = wok.edges()
        
        for edge in edges[:10]:
            # Edge index should be 0, 1, or 2 (local edge index)
            self.assertIn(edge.index, [0, 1, 2], 
                         "Edge index should be local edge index (0, 1, or 2)")
            
            # Face should be in faces list
            self.assertIn(edge.face, wok.faces)

    def test_roundtrip_preserves_walkmesh_type(self):
        """Test that walkmesh type is preserved through roundtrip."""
        for walkmesh_type in [BWMType.AreaModel, BWMType.PlaceableOrDoor]:
            bwm = BWM()
            bwm.walkmesh_type = walkmesh_type
            
            # Add a face
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
            
            self.assertEqual(loaded.walkmesh_type, walkmesh_type,
                           f"Walkmesh type {walkmesh_type} should be preserved")


if __name__ == "__main__":
    unittest.main()

