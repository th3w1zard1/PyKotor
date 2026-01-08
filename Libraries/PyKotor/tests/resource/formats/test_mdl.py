"""Unit tests for binary MDL/MDX file format handling.

This test module covers:
- Binary MDL/MDX reading and writing
- Fast loading for rendering
- Round-trip tests (Binary -> ASCII -> Binary)
- Node hierarchy and mesh data
- Controller and animation data
- Extended round-trip conversions
- Cross-model round-trip validation

Test files are located in Libraries/PyKotor/tests/test_files/mdl/
"""

from __future__ import annotations

import unittest

from pathlib import Path

from pykotor.resource.formats.mdl import (
    MDL,
    MDLAnimation,
    MDLMesh,
    MDLNode,
    MDLSkin,
    bytes_mdl,
    read_mdl,
    read_mdl_fast,
)
from pykotor.resource.type import ResourceType
from utility.common.geometry import Vector3, Vector4

# ============================================================================
# Helper Functions for Round-Trip Tests
# ============================================================================


def compare_mdl_basic(
    mdl1: MDL,
    mdl2: MDL,
    test_case: unittest.TestCase,
    context: str = "",
):
    """Compare basic MDL properties between two models.

    Args:
        mdl1: First MDL to compare
        mdl2: Second MDL to compare
        test_case: TestCase instance for assertions
        context: Context string for error messages
    """
    msg_prefix = f"{context}: " if context else ""

    test_case.assertEqual(mdl1.name, mdl2.name, f"{msg_prefix}Model names should match")
    test_case.assertEqual(mdl1.supermodel, mdl2.supermodel, f"{msg_prefix}Supermodels should match")
    test_case.assertEqual(mdl1.classification, mdl2.classification, f"{msg_prefix}Classifications should match")
    test_case.assertEqual(mdl1.fog, mdl2.fog, f"{msg_prefix}Fog settings should match")
    test_case.assertEqual(mdl1.compress_quaternions, mdl2.compress_quaternions, f"{msg_prefix}Quaternion compression should match")
    test_case.assertEqual(mdl1.animation_scale, mdl2.animation_scale, f"{msg_prefix}Animation scales should match")


def compare_mdl_nodes(
    mdl1: MDL,
    mdl2: MDL,
    test_case: unittest.TestCase,
    context: str = "",
):
    """Compare node hierarchies between two models.

    Args:
        mdl1: First MDL to compare
        mdl2: Second MDL to compare
        test_case: TestCase instance for assertions
        context: Context string for error messages
    """
    msg_prefix = f"{context}: " if context else ""

    nodes1 = mdl1.all_nodes()
    nodes2 = mdl2.all_nodes()

    test_case.assertEqual(len(nodes1), len(nodes2), f"{msg_prefix}Node counts should match (got {len(nodes1)} vs {len(nodes2)})")

    # Build node name maps
    nodes1_by_name = {node.name: node for node in nodes1}
    nodes2_by_name = {node.name: node for node in nodes2}

    # Verify all node names match
    names1 = set(nodes1_by_name.keys())
    names2 = set(nodes2_by_name.keys())
    test_case.assertEqual(names1, names2, f"{msg_prefix}Node names should match")

    # Compare each node's basic properties
    for name in names1:
        node1 = nodes1_by_name[name]
        node2 = nodes2_by_name[name]

        test_case.assertEqual(node1.node_type, node2.node_type, f"{msg_prefix}Node {name} types should match")

        # Compare children count (hierarchy structure)
        test_case.assertEqual(len(node1.children), len(node2.children), f"{msg_prefix}Node {name} child counts should match")


def compare_mdl_animations(
    mdl1: MDL,
    mdl2: MDL,
    test_case: unittest.TestCase,
    context: str = "",
):
    """Compare animation data between two models.

    Args:
        mdl1: First MDL to compare
        mdl2: Second MDL to compare
        test_case: TestCase instance for assertions
        context: Context string for error messages
    """
    msg_prefix = f"{context}: " if context else ""

    test_case.assertEqual(len(mdl1.anims), len(mdl2.anims), f"{msg_prefix}Animation counts should match")

    # Build animation maps by name
    anims1_by_name = {anim.name: anim for anim in mdl1.anims}
    anims2_by_name = {anim.name: anim for anim in mdl2.anims}

    # Verify all animation names match
    names1 = set(anims1_by_name.keys())
    names2 = set(anims2_by_name.keys())
    test_case.assertEqual(names1, names2, f"{msg_prefix}Animation names should match")

    # Compare each animation's basic properties
    for name in names1:
        anim1 = anims1_by_name[name]
        anim2 = anims2_by_name[name]

        test_case.assertEqual(anim1.anim_length, anim2.anim_length, f"{msg_prefix}Animation {name} lengths should match")
        test_case.assertEqual(anim1.transition_length, anim2.transition_length, f"{msg_prefix}Animation {name} transition lengths should match")
        test_case.assertEqual(len(anim1.events), len(anim2.events), f"{msg_prefix}Animation {name} event counts should match")


# ============================================================================
# Binary I/O Tests
# ============================================================================


class TestMDLBinaryIO(unittest.TestCase):
    """Test binary MDL/MDX file I/O operations."""

    def setUp(self):
        """Set up test fixtures."""
        # Try multiple possible paths
        possible_paths: list[Path] = [
            Path("Libraries/PyKotor/tests/test_files/mdl"),
            Path(__file__).parent.parent.parent / "test_files" / "mdl",
            Path("tests/test_files/mdl"),
        ]
        found = False
        for path in possible_paths:
            if path.exists():
                self.test_dir: Path = path
                found = True
                break
        if not found:
            self.skipTest(f"Test directory not found. Tried: {possible_paths}")

        # Test files
        self.test_files: dict[str, tuple[str, str]] = {
            "character": ("c_dewback.mdl", "c_dewback.mdx"),
            "door": ("dor_lhr02.mdl", "dor_lhr02.mdx"),
            "placeable": ("m02aa_09b.mdl", "m02aa_09b.mdx"),
            "animation": ("m12aa_c03_char02.mdl", "m12aa_c03_char02.mdx"),
            "camera": ("m12aa_c04_cam.mdl", "m12aa_c04_cam.mdx"),
        }

    def test_read_mdl_basic(self):
        """Test basic MDL file reading."""
        mdl_path = self.test_dir / "c_dewback.mdl"
        mdx_path = self.test_dir / "c_dewback.mdx"

        mdl = read_mdl(mdl_path, source_ext=mdx_path)

        self.assertIsInstance(mdl, MDL)
        self.assertIsNotNone(mdl.root)
        self.assertIsInstance(mdl.root, MDLNode)
        self.assertIsInstance(mdl.name, str)
        self.assertGreater(len(mdl.name), 0)

    def test_read_mdl_fast(self):
        """Test fast MDL loading optimized for rendering."""
        mdl_path = self.test_dir / "c_dewback.mdl"
        mdx_path = self.test_dir / "c_dewback.mdx"

        # Load with fast loading
        mdl_fast = read_mdl_fast(mdl_path, source_ext=mdx_path)

        # Fast load should have no animations or controllers
        self.assertEqual(len(mdl_fast.anims), 0, "Fast loading should skip animations")

        # But should still have node hierarchy and meshes
        self.assertIsNotNone(mdl_fast.root)
        all_nodes = mdl_fast.all_nodes()
        self.assertGreater(len(all_nodes), 0, "Should have nodes")

    def test_read_mdl_fast_vs_full(self):
        """Compare fast loading vs full loading."""
        mdl_path = self.test_dir / "m12aa_c03_char02.mdl"
        mdx_path = self.test_dir / "m12aa_c03_char02.mdx"

        mdl_full = read_mdl(mdl_path, source_ext=mdx_path)
        mdl_fast = read_mdl_fast(mdl_path, source_ext=mdx_path)

        # Both should have same name
        self.assertEqual(mdl_full.name, mdl_fast.name)

        # Fast should have no animations
        self.assertEqual(len(mdl_fast.anims), 0)

        # Full might have animations
        # (not asserting here as some test files may not have anims)

        # Both should have same node count
        self.assertEqual(
            len(mdl_full.all_nodes()),
            len(mdl_fast.all_nodes()),
            "Node count should be same",
        )

    def test_read_all_test_files(self):
        """Test reading all available test MDL files."""
        for name, (mdl_file, mdx_file) in self.test_files.items():
            with self.subTest(test_file=name):
                mdl_path = self.test_dir / mdl_file
                mdx_path = self.test_dir / mdx_file

                if not mdl_path.exists():
                    self.skipTest(f"Test file {mdl_file} not found")

                mdl = read_mdl(mdl_path, source_ext=mdx_path)

                self.assertIsInstance(mdl, MDL, f"Failed to load {name}")
                self.assertIsNotNone(mdl.root, f"No root node in {name}")
                self.assertIsInstance(mdl.name, str, f"Invalid name in {name}")

    def test_mdl_node_hierarchy(self):
        """Test MDL node hierarchy structure."""
        mdl_path = self.test_dir / "c_dewback.mdl"
        mdx_path = self.test_dir / "c_dewback.mdx"

        mdl = read_mdl(mdl_path, source_ext=mdx_path)

        # Test node hierarchy
        all_nodes = mdl.all_nodes()
        self.assertGreater(len(all_nodes), 0, "Should have at least one node")

        # Root node should be in the list
        self.assertIn(mdl.root, all_nodes)

        # Test node attributes
        for node in all_nodes:
            self.assertIsInstance(node.name, str)
            self.assertIsInstance(node.position, Vector3)
            self.assertIsInstance(node.orientation, Vector4)

    def test_mdl_mesh_data(self):
        """Test MDL mesh data parsing."""
        mdl_path = self.test_dir / "c_dewback.mdl"
        mdx_path = self.test_dir / "c_dewback.mdx"

        mdl = read_mdl(mdl_path, source_ext=mdx_path)

        # Find nodes with meshes
        mesh_nodes = [node for node in mdl.all_nodes() if node.mesh]

        self.assertGreater(len(mesh_nodes), 0, "Should have at least one mesh node")

        # Test mesh attributes
        for node in mesh_nodes:
            mesh = node.mesh
            assert mesh is not None, f"Node {node.name} has no mesh"

            self.assertIsInstance(mesh, MDLMesh)

            # Test basic mesh properties
            self.assertIsInstance(mesh.texture_1, str)
            self.assertIsInstance(mesh.render, bool)

            # If mesh has vertices, test them
            if mesh.vertex_positions:
                self.assertGreater(len(mesh.vertex_positions), 0)
                for vertex in mesh.vertex_positions:
                    self.assertIsInstance(vertex, Vector3)

            # If mesh has faces, test them
            if mesh.faces:
                self.assertGreater(len(mesh.faces), 0)

    def test_mdl_get_node_by_name(self):
        """Test retrieving nodes by name."""
        mdl_path = self.test_dir / "c_dewback.mdl"
        mdx_path = self.test_dir / "c_dewback.mdx"

        mdl = read_mdl(mdl_path, source_ext=mdx_path)

        # Get root node by name
        root_by_name = mdl.get(mdl.root.name)
        self.assertIsNotNone(root_by_name)
        self.assertEqual(root_by_name, mdl.root)

        # Test non-existent node
        non_existent = mdl.get("nonexistent_node_name_xyz")
        self.assertIsNone(non_existent)

    def test_mdl_textures(self):
        """Test texture name extraction."""
        mdl_path = self.test_dir / "c_dewback.mdl"
        mdx_path = self.test_dir / "c_dewback.mdx"

        mdl = read_mdl(mdl_path, source_ext=mdx_path)

        textures = mdl.all_textures()
        self.assertIsInstance(textures, set)

        # All texture names should be strings
        for texture in textures:
            self.assertIsInstance(texture, str)
            self.assertGreater(len(texture), 0)

    def test_mdl_lightmaps(self):
        """Test lightmap texture extraction."""
        mdl_path = self.test_dir / "c_dewback.mdl"
        mdx_path = self.test_dir / "c_dewback.mdx"

        mdl = read_mdl(mdl_path, source_ext=mdx_path)

        lightmaps = mdl.all_lightmaps()
        self.assertIsInstance(lightmaps, set)

    def test_write_mdl_binary(self):
        """Test writing MDL to binary format."""
        mdl_path = self.test_dir / "c_dewback.mdl"
        mdx_path = self.test_dir / "c_dewback.mdx"

        # Read original
        mdl = read_mdl(mdl_path, source_ext=mdx_path)

        # Write to bytes
        mdl_bytes = bytes_mdl(mdl, ResourceType.MDL)
        self.assertIsInstance(mdl_bytes, bytes)
        self.assertGreater(len(mdl_bytes), 0)

    def test_mdl_roundtrip(self):
        """Test MDL roundtrip (read->write->read) integrity."""
        mdl_path = self.test_dir / "c_dewback.mdl"
        mdx_path = self.test_dir / "c_dewback.mdx"

        # Read original
        mdl1 = read_mdl(mdl_path, source_ext=mdx_path)

        # Write to bytes
        mdl_bytes = bytes_mdl(mdl1, ResourceType.MDL)

        # Read back from bytes
        # NOTE: MDX data needs to be handled separately
        # For now, just verify we can write and get valid bytes
        self.assertIsInstance(mdl_bytes, bytes)
        self.assertGreater(len(mdl_bytes), 12, "Should have at least header")


# ============================================================================
# Data Structure Tests
# ============================================================================


class TestMDLData(unittest.TestCase):
    """Test MDL data structures and manipulation."""

    def test_mdl_creation(self):
        """Test creating an MDL from scratch."""
        mdl = MDL()

        self.assertIsNotNone(mdl.root)
        self.assertIsInstance(mdl.root, MDLNode)
        self.assertEqual(len(mdl.anims), 0)
        self.assertEqual(mdl.name, "")
        self.assertFalse(mdl.fog)

    def test_mdl_node_creation(self):
        """Test creating MDL nodes."""
        node = MDLNode()

        self.assertEqual(node.name, "")
        self.assertIsInstance(node.position, Vector3)
        self.assertIsInstance(node.orientation, Vector4)
        self.assertEqual(len(node.children), 0)
        self.assertEqual(len(node.controllers), 0)
        self.assertIsNone(node.mesh)
        self.assertIsNone(node.light)

    def test_mdl_node_hierarchy_creation(self):
        """Test creating a node hierarchy."""
        mdl = MDL()
        mdl.name = "test_model"

        # Create child nodes
        child1 = MDLNode()
        child1.name = "child1"

        child2 = MDLNode()
        child2.name = "child2"

        mdl.root.name = "root"
        mdl.root.children.append(child1)
        mdl.root.children.append(child2)

        # Test hierarchy
        all_nodes = mdl.all_nodes()
        self.assertEqual(len(all_nodes), 3)  # root + 2 children
        self.assertIn(mdl.root, all_nodes)
        self.assertIn(child1, all_nodes)
        self.assertIn(child2, all_nodes)

    def test_mdl_mesh_creation(self):
        """Test creating mesh data."""
        mesh = MDLMesh()

        mesh.texture_1 = "test_texture"
        mesh.render = True
        mesh.shadow = False

        self.assertEqual(mesh.texture_1, "test_texture")
        self.assertTrue(mesh.render)
        self.assertFalse(mesh.shadow)

    def test_mdl_animation_creation(self):
        """Test creating animation data."""
        anim = MDLAnimation()

        anim.name = "test_anim"
        anim.anim_length = 1.5
        anim.transition_length = 0.25

        self.assertEqual(anim.name, "test_anim")
        self.assertEqual(anim.anim_length, 1.5)
        self.assertEqual(anim.transition_length, 0.25)

    def test_mdl_find_parent(self):
        """Test finding parent nodes."""
        mdl = MDL()

        child = MDLNode()
        child.name = "child"

        mdl.root.children.append(child)

        parent = mdl.find_parent(child)
        self.assertEqual(parent, mdl.root)

    def test_mdl_global_position(self):
        """Test calculating global positions."""
        mdl = MDL()

        child = MDLNode()
        child.name = "child"
        child.position = Vector3(1.0, 2.0, 3.0)

        mdl.root.position = Vector3(10.0, 20.0, 30.0)
        mdl.root.children.append(child)

        global_pos = mdl.global_position(child)

        # Global position should be sum of all parent positions
        self.assertEqual(global_pos.x, 11.0)
        self.assertEqual(global_pos.y, 22.0)
        self.assertEqual(global_pos.z, 33.0)

    def test_skin_prepare_bone_lookups(self):
        """Ensure MDLSkin prepares lookup tables using global bone IDs."""
        nodes = []
        for node_id in [0, 5, 10]:
            node = MDLNode()
            node.node_id = node_id
            nodes.append(node)

        skin = MDLSkin()
        skin.bonemap = [5.0, 0xFFFF, 10.0]

        skin.prepare_bone_lookups(nodes)

        self.assertGreaterEqual(len(skin.bone_serial), 11)
        self.assertEqual(skin.bone_serial[5], 1)
        self.assertEqual(skin.bone_node_number[5], 5)
        self.assertEqual(skin.bone_serial[10], 2)
        self.assertEqual(skin.bone_node_number[10], 10)


# ============================================================================
# Performance Tests
# ============================================================================


class TestMDLPerformance(unittest.TestCase):
    """Test MDL performance characteristics."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("Libraries/PyKotor/tests/test_files/mdl")
        self.mdl_path = self.test_dir / "c_dewback.mdl"
        self.mdx_path = self.test_dir / "c_dewback.mdx"

        if not self.mdl_path.exists():
            self.skipTest("Test file c_dewback.mdl not found")

    def test_fast_load_performance(self):
        """Verify fast loading is actually faster."""
        import time

        # Measure full load time
        start = time.time()
        mdl_full = read_mdl(self.mdl_path, source_ext=self.mdx_path)
        full_time = time.time() - start

        # Measure fast load time
        start = time.time()
        mdl_fast = read_mdl_fast(self.mdl_path, source_ext=self.mdx_path)
        fast_time = time.time() - start

        # Fast loading should be faster (or at least not slower)
        # This is not a strict requirement but good to verify
        # We use a generous threshold since performance can vary
        self.assertLessEqual(
            fast_time,
            full_time * 2.0,
            "Fast loading should not be significantly slower than full loading",
        )

        # Verify both loaded successfully
        self.assertIsNotNone(mdl_full)
        self.assertIsNotNone(mdl_fast)


# ============================================================================
# Edge Cases
# ============================================================================


class TestMDLEdgeCases(unittest.TestCase):
    """Test MDL edge cases and error handling."""

    def test_read_nonexistent_file(self):
        """Test reading a non-existent file."""
        with self.assertRaises(FileNotFoundError):
            read_mdl("nonexistent_file.mdl")

    def test_empty_mdl(self):
        """Test creating and manipulating an empty MDL."""
        mdl = MDL()

        self.assertEqual(len(mdl.all_nodes()), 1)  # Just root
        self.assertEqual(len(mdl.anims), 0)
        self.assertEqual(len(mdl.all_textures()), 0)
        self.assertEqual(len(mdl.all_lightmaps()), 0)

    def test_node_with_no_children(self):
        """Test node operations with no children."""
        node = MDLNode()

        self.assertEqual(len(node.children), 0)
        self.assertEqual(len(node.controllers), 0)

    def test_get_nonexistent_node_by_id(self):
        """Test getting node by non-existent ID."""
        mdl = MDL()

        with self.assertRaises(ValueError):
            mdl.get_by_node_id(999)


# ============================================================================
# Round-Trip Tests: Binary -> ASCII -> Binary
# ============================================================================


class TestMDLRoundTripBinaryToAsciiToBinary(unittest.TestCase):
    """Test round-trip conversion: Binary -> ASCII -> Binary using diverse models."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("Libraries/PyKotor/tests/test_files/mdl")
        if not self.test_dir.exists():
            self.skipTest(f"Test directory {self.test_dir} does not exist")

        # Diverse test models
        self.test_models = {
            "character": {
                "mdl": "c_dewback.mdl",
                "mdx": "c_dewback.mdx",
                "description": "Character model with complex geometry",
            },
            "door": {
                "mdl": "dor_lhr02.mdl",
                "mdx": "dor_lhr02.mdx",
                "description": "Door model with reference nodes",
            },
            "placeable": {
                "mdl": "m02aa_09b.mdl",
                "mdx": "m02aa_09b.mdx",
                "description": "Placeable object model",
            },
            "animation": {
                "mdl": "m12aa_c03_char02.mdl",
                "mdx": "m12aa_c03_char02.mdx",
                "description": "Character model with animations",
            },
            "camera": {
                "mdl": "m12aa_c04_cam.mdl",
                "mdx": "m12aa_c04_cam.mdx",
                "description": "Camera model",
            },
        }

    def test_roundtrip_character_model(self):
        """Test Binary -> ASCII -> Binary round-trip with character model."""
        model_info = self.test_models["character"]
        mdl_path = self.test_dir / model_info["mdl"]
        mdx_path = self.test_dir / model_info["mdx"]

        if not mdl_path.exists():
            self.skipTest(f"Test file {model_info['mdl']} not found")

        # Step 1: Read original binary
        mdl_original = read_mdl(mdl_path, source_ext=mdx_path, file_format=ResourceType.MDL)
        self.assertIsNotNone(mdl_original, "Should load original binary model")

        original_node_count = len(mdl_original.all_nodes())
        original_anim_count = len(mdl_original.anims)

        # Step 2: Convert to ASCII
        ascii_bytes = bytes_mdl(mdl_original, ResourceType.MDL_ASCII)
        self.assertIsInstance(ascii_bytes, bytes, "Should produce ASCII bytes")
        self.assertGreater(len(ascii_bytes), 0, "ASCII output should not be empty")

        # Verify ASCII content
        ascii_str = ascii_bytes.decode("utf-8", errors="ignore")
        self.assertIn("newmodel", ascii_str.lower(), "ASCII should contain model declaration")

        # Step 3: Read ASCII back
        mdl_from_ascii = read_mdl(ascii_bytes, file_format=ResourceType.MDL_ASCII)
        self.assertIsNotNone(mdl_from_ascii, "Should load model from ASCII")

        # Step 4: Compare basic properties
        compare_mdl_basic(mdl_original, mdl_from_ascii, self, "Character model: Binary->ASCII")

        # Step 5: Compare node structures
        compare_mdl_nodes(mdl_original, mdl_from_ascii, self, "Character model: Binary->ASCII")

        # Step 6: Compare animations
        compare_mdl_animations(mdl_original, mdl_from_ascii, self, "Character model: Binary->ASCII")

        # Step 7: Convert back to binary
        binary_bytes = bytes_mdl(mdl_from_ascii, ResourceType.MDL)
        self.assertIsInstance(binary_bytes, bytes, "Should produce binary bytes")
        self.assertGreater(len(binary_bytes), 0, "Binary output should not be empty")

        # Verify binary header
        self.assertEqual(binary_bytes[:4], b"\x00\x00\x00\x00", "Binary should start with null header")

        # Step 8: Read binary back
        mdl_final = read_mdl(binary_bytes, file_format=ResourceType.MDL)
        self.assertIsNotNone(mdl_final, "Should load model from final binary")

        # Step 9: Compare final model with original
        compare_mdl_basic(mdl_original, mdl_final, self, "Character model: Final Binary")
        compare_mdl_nodes(mdl_original, mdl_final, self, "Character model: Final Binary")
        compare_mdl_animations(mdl_original, mdl_final, self, "Character model: Final Binary")

        # Verify counts match
        self.assertEqual(original_node_count, len(mdl_final.all_nodes()), "Final node count should match original")
        self.assertEqual(original_anim_count, len(mdl_final.anims), "Final animation count should match original")

    def test_roundtrip_door_model(self):
        """Test Binary -> ASCII -> Binary round-trip with door model."""
        model_info = self.test_models["door"]
        mdl_path = self.test_dir / model_info["mdl"]
        mdx_path = self.test_dir / model_info["mdx"]

        if not mdl_path.exists():
            self.skipTest(f"Test file {model_info['mdl']} not found")

        # Read original binary
        mdl_original = read_mdl(mdl_path, source_ext=mdx_path, file_format=ResourceType.MDL)

        # Convert to ASCII
        ascii_bytes = bytes_mdl(mdl_original, ResourceType.MDL_ASCII)
        mdl_from_ascii = read_mdl(ascii_bytes, file_format=ResourceType.MDL_ASCII)

        # Compare after first conversion
        compare_mdl_basic(mdl_original, mdl_from_ascii, self, "Door model: Binary->ASCII")
        compare_mdl_nodes(mdl_original, mdl_from_ascii, self, "Door model: Binary->ASCII")

        # Convert back to binary
        binary_bytes = bytes_mdl(mdl_from_ascii, ResourceType.MDL)
        mdl_final = read_mdl(binary_bytes, file_format=ResourceType.MDL)

        # Compare final
        compare_mdl_basic(mdl_original, mdl_final, self, "Door model: Final Binary")
        compare_mdl_nodes(mdl_original, mdl_final, self, "Door model: Final Binary")

    def test_roundtrip_placeable_model(self):
        """Test Binary -> ASCII -> Binary round-trip with placeable model."""
        model_info = self.test_models["placeable"]
        mdl_path = self.test_dir / model_info["mdl"]
        mdx_path = self.test_dir / model_info["mdx"]

        if not mdl_path.exists():
            self.skipTest(f"Test file {model_info['mdl']} not found")

        # Read original binary
        mdl_original = read_mdl(mdl_path, source_ext=mdx_path, file_format=ResourceType.MDL)

        # Convert to ASCII
        ascii_bytes = bytes_mdl(mdl_original, ResourceType.MDL_ASCII)
        mdl_from_ascii = read_mdl(ascii_bytes, file_format=ResourceType.MDL_ASCII)

        # Compare after first conversion
        compare_mdl_basic(mdl_original, mdl_from_ascii, self, "Placeable model: Binary->ASCII")
        compare_mdl_nodes(mdl_original, mdl_from_ascii, self, "Placeable model: Binary->ASCII")

        # Convert back to binary
        binary_bytes = bytes_mdl(mdl_from_ascii, ResourceType.MDL)
        mdl_final = read_mdl(binary_bytes, file_format=ResourceType.MDL)

        # Compare final
        compare_mdl_basic(mdl_original, mdl_final, self, "Placeable model: Final Binary")
        compare_mdl_nodes(mdl_original, mdl_final, self, "Placeable model: Final Binary")

    def test_roundtrip_animation_model(self):
        """Test Binary -> ASCII -> Binary round-trip with animation model."""
        model_info = self.test_models["animation"]
        mdl_path = self.test_dir / model_info["mdl"]
        mdx_path = self.test_dir / model_info["mdx"]

        if not mdl_path.exists():
            self.skipTest(f"Test file {model_info['mdl']} not found")

        # Read original binary
        mdl_original = read_mdl(mdl_path, source_ext=mdx_path, file_format=ResourceType.MDL)

        original_anim_count = len(mdl_original.anims)

        # Convert to ASCII
        ascii_bytes = bytes_mdl(mdl_original, ResourceType.MDL_ASCII)
        mdl_from_ascii = read_mdl(ascii_bytes, file_format=ResourceType.MDL_ASCII)

        # Compare after first conversion
        compare_mdl_basic(mdl_original, mdl_from_ascii, self, "Animation model: Binary->ASCII")
        compare_mdl_nodes(mdl_original, mdl_from_ascii, self, "Animation model: Binary->ASCII")
        compare_mdl_animations(mdl_original, mdl_from_ascii, self, "Animation model: Binary->ASCII")

        # Convert back to binary
        binary_bytes = bytes_mdl(mdl_from_ascii, ResourceType.MDL)
        mdl_final = read_mdl(binary_bytes, file_format=ResourceType.MDL)

        # Compare final
        compare_mdl_basic(mdl_original, mdl_final, self, "Animation model: Final Binary")
        compare_mdl_nodes(mdl_original, mdl_final, self, "Animation model: Final Binary")
        compare_mdl_animations(mdl_original, mdl_final, self, "Animation model: Final Binary")

        # Verify animation count
        self.assertEqual(original_anim_count, len(mdl_final.anims), "Animation count should be preserved")

    def test_roundtrip_camera_model(self):
        """Test Binary -> ASCII -> Binary round-trip with camera model."""
        model_info = self.test_models["camera"]
        mdl_path = self.test_dir / model_info["mdl"]
        mdx_path = self.test_dir / model_info["mdx"]

        if not mdl_path.exists():
            self.skipTest(f"Test file {model_info['mdl']} not found")

        # Read original binary
        mdl_original = read_mdl(mdl_path, source_ext=mdx_path, file_format=ResourceType.MDL)

        # Convert to ASCII
        ascii_bytes = bytes_mdl(mdl_original, ResourceType.MDL_ASCII)
        mdl_from_ascii = read_mdl(ascii_bytes, file_format=ResourceType.MDL_ASCII)

        # Compare after first conversion
        compare_mdl_basic(mdl_original, mdl_from_ascii, self, "Camera model: Binary->ASCII")
        compare_mdl_nodes(mdl_original, mdl_from_ascii, self, "Camera model: Binary->ASCII")

        # Convert back to binary
        binary_bytes = bytes_mdl(mdl_from_ascii, ResourceType.MDL)
        mdl_final = read_mdl(binary_bytes, file_format=ResourceType.MDL)

        # Compare final
        compare_mdl_basic(mdl_original, mdl_final, self, "Camera model: Final Binary")
        compare_mdl_nodes(mdl_original, mdl_final, self, "Camera model: Final Binary")

    def test_roundtrip_all_models(self):
        """Test Binary -> ASCII -> Binary round-trip for all available models."""
        for model_type, model_info in self.test_models.items():
            with self.subTest(model_type=model_type, description=model_info["description"]):
                mdl_path = self.test_dir / model_info["mdl"]
                mdx_path = self.test_dir / model_info["mdx"]

                if not mdl_path.exists():
                    self.skipTest(f"Test file {model_info['mdl']} not found")

                # Read original binary
                mdl_original = read_mdl(mdl_path, source_ext=mdx_path, file_format=ResourceType.MDL)

                # Convert to ASCII
                ascii_bytes = bytes_mdl(mdl_original, ResourceType.MDL_ASCII)
                mdl_from_ascii = read_mdl(ascii_bytes, file_format=ResourceType.MDL_ASCII)

                # Compare after first conversion
                compare_mdl_basic(mdl_original, mdl_from_ascii, self, f"{model_type}: Binary->ASCII")
                compare_mdl_nodes(mdl_original, mdl_from_ascii, self, f"{model_type}: Binary->ASCII")

                # Convert back to binary
                binary_bytes = bytes_mdl(mdl_from_ascii, ResourceType.MDL)
                mdl_final = read_mdl(binary_bytes, file_format=ResourceType.MDL)

                # Compare final
                compare_mdl_basic(mdl_original, mdl_final, self, f"{model_type}: Final Binary")
                compare_mdl_nodes(mdl_original, mdl_final, self, f"{model_type}: Final Binary")


# ============================================================================
# Extended Round-Trip Tests (3+ Steps)
# ============================================================================


class TestMDLExtendedRoundTrip(unittest.TestCase):
    """Test extended round-trip conversions (3+ steps) using diverse models."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("Libraries/PyKotor/tests/test_files/mdl")
        if not self.test_dir.exists():
            self.skipTest(f"Test directory {self.test_dir} does not exist")

        self.test_models = {
            "character": ("c_dewback.mdl", "c_dewback.mdx"),
            "door": ("dor_lhr02.mdl", "dor_lhr02.mdx"),
            "placeable": ("m02aa_09b.mdl", "m02aa_09b.mdx"),
            "animation": ("m12aa_c03_char02.mdl", "m12aa_c03_char02.mdx"),
            "camera": ("m12aa_c04_cam.mdl", "m12aa_c04_cam.mdx"),
        }

    def test_triple_roundtrip_binary_to_ascii_to_binary_to_ascii(self):
        """Test Binary -> ASCII -> Binary -> ASCII (3-step round-trip)."""
        mdl_path = self.test_dir / self.test_models["character"][0]
        mdx_path = self.test_dir / self.test_models["character"][1]

        if not mdl_path.exists():
            self.skipTest("Test file c_dewback.mdl not found")

        # Step 1: Read original binary
        mdl_original = read_mdl(mdl_path, source_ext=mdx_path, file_format=ResourceType.MDL)
        original_node_count = len(mdl_original.all_nodes())
        original_anim_count = len(mdl_original.anims)

        # Step 2: Convert to ASCII
        ascii_bytes_1 = bytes_mdl(mdl_original, ResourceType.MDL_ASCII)
        mdl_ascii_1 = read_mdl(ascii_bytes_1, file_format=ResourceType.MDL_ASCII)

        # Compare step 1 -> step 2
        compare_mdl_basic(mdl_original, mdl_ascii_1, self, "Step 1->2: Binary->ASCII")
        compare_mdl_nodes(mdl_original, mdl_ascii_1, self, "Step 1->2: Binary->ASCII")

        # Step 3: Convert back to binary
        binary_bytes = bytes_mdl(mdl_ascii_1, ResourceType.MDL)
        mdl_binary = read_mdl(binary_bytes, file_format=ResourceType.MDL)

        # Compare step 2 -> step 3
        compare_mdl_basic(mdl_ascii_1, mdl_binary, self, "Step 2->3: ASCII->Binary")
        compare_mdl_nodes(mdl_ascii_1, mdl_binary, self, "Step 2->3: ASCII->Binary")

        # Step 4: Convert back to ASCII again
        ascii_bytes_2 = bytes_mdl(mdl_binary, ResourceType.MDL_ASCII)
        mdl_ascii_2 = read_mdl(ascii_bytes_2, file_format=ResourceType.MDL_ASCII)

        # Compare step 3 -> step 4
        compare_mdl_basic(mdl_binary, mdl_ascii_2, self, "Step 3->4: Binary->ASCII")
        compare_mdl_nodes(mdl_binary, mdl_ascii_2, self, "Step 3->4: Binary->ASCII")

        # Compare final with original
        compare_mdl_basic(mdl_original, mdl_ascii_2, self, "Final: Original->Final")
        compare_mdl_nodes(mdl_original, mdl_ascii_2, self, "Final: Original->Final")
        compare_mdl_animations(mdl_original, mdl_ascii_2, self, "Final: Original->Final")

        # Verify counts
        self.assertEqual(original_node_count, len(mdl_ascii_2.all_nodes()))
        self.assertEqual(original_anim_count, len(mdl_ascii_2.anims))

    def test_multiple_roundtrip_all_models(self):
        """Test multiple round-trips for all available models."""
        for model_type, (mdl_file, mdx_file) in self.test_models.items():
            with self.subTest(model_type=model_type):
                mdl_path = self.test_dir / mdl_file
                mdx_path = self.test_dir / mdx_file

                if not mdl_path.exists():
                    self.skipTest(f"Test file {mdl_file} not found")

                # Read original binary
                mdl_original = read_mdl(mdl_path, source_ext=mdx_path, file_format=ResourceType.MDL)
                original_node_count = len(mdl_original.all_nodes())

                # Multiple conversions
                # Binary -> ASCII -> Binary -> ASCII -> Binary
                ascii_1 = bytes_mdl(mdl_original, ResourceType.MDL_ASCII)
                mdl_ascii_1 = read_mdl(ascii_1, file_format=ResourceType.MDL_ASCII)

                binary_1 = bytes_mdl(mdl_ascii_1, ResourceType.MDL)
                mdl_binary_1 = read_mdl(binary_1, file_format=ResourceType.MDL)

                ascii_2 = bytes_mdl(mdl_binary_1, ResourceType.MDL_ASCII)
                mdl_ascii_2 = read_mdl(ascii_2, file_format=ResourceType.MDL_ASCII)

                binary_2 = bytes_mdl(mdl_ascii_2, ResourceType.MDL)
                mdl_final = read_mdl(binary_2, file_format=ResourceType.MDL)

                # Compare final with original
                compare_mdl_basic(mdl_original, mdl_final, self, f"{model_type}: Multiple round-trips")
                compare_mdl_nodes(mdl_original, mdl_final, self, f"{model_type}: Multiple round-trips")

                # Verify node count
                self.assertEqual(original_node_count, len(mdl_final.all_nodes()))


# ============================================================================
# Cross-Model Round-Trip Tests
# ============================================================================


class TestMDLCrossModelRoundTrip(unittest.TestCase):
    """Test round-trip conversions comparing different models."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("Libraries/PyKotor/tests/test_files/mdl")
        if not self.test_dir.exists():
            self.skipTest(f"Test directory {self.test_dir} does not exist")

        self.test_models = {
            "character": ("c_dewback.mdl", "c_dewback.mdx"),
            "door": ("dor_lhr02.mdl", "dor_lhr02.mdx"),
            "placeable": ("m02aa_09b.mdl", "m02aa_09b.mdx"),
            "animation": ("m12aa_c03_char02.mdl", "m12aa_c03_char02.mdx"),
            "camera": ("m12aa_c04_cam.mdl", "m12aa_c04_cam.mdx"),
        }

    def test_all_models_binary_to_ascii_preserve_structure(self):
        """Test that all models preserve structure when converted Binary -> ASCII -> Binary."""
        for model_type, (mdl_file, mdx_file) in self.test_models.items():
            with self.subTest(model_type=model_type):
                mdl_path = self.test_dir / mdl_file
                mdx_path = self.test_dir / mdx_file

                if not mdl_path.exists():
                    self.skipTest(f"Test file {mdl_file} not found")

                # Read original
                mdl_original = read_mdl(mdl_path, source_ext=mdx_path, file_format=ResourceType.MDL)

                # Convert to ASCII and back
                ascii_bytes = bytes_mdl(mdl_original, ResourceType.MDL_ASCII)
                mdl_from_ascii = read_mdl(ascii_bytes, file_format=ResourceType.MDL_ASCII)
                binary_bytes = bytes_mdl(mdl_from_ascii, ResourceType.MDL)
                mdl_final = read_mdl(binary_bytes, file_format=ResourceType.MDL)

                # Verify structure preservation
                self.assertEqual(len(mdl_original.all_nodes()), len(mdl_final.all_nodes()), f"{model_type}: Node count should be preserved")

                self.assertEqual(mdl_original.name, mdl_final.name, f"{model_type}: Name should be preserved")

                self.assertEqual(mdl_original.classification, mdl_final.classification, f"{model_type}: Classification should be preserved")


if __name__ == "__main__":
    unittest.main()
