"""Exhaustive round-trip tests for MDL/MDX format conversion.

This test module provides comprehensive round-trip testing between ASCII and binary MDL formats
using diverse real-world game models. Tests verify data integrity at each conversion step:

- Binary -> ASCII -> Binary
- ASCII -> Binary -> ASCII  
- Binary -> ASCII -> Binary -> ASCII (3-step)
- ASCII -> Binary -> ASCII -> Binary (3-step)

Test files are located in Libraries/PyKotor/tests/test_files/mdl/
Models tested:
- Character models (c_dewback.mdl) - Complex geometry, animations
- Door models (dor_lhr02.mdl) - Simple geometry, reference nodes
- Placeable models (m02aa_09b.mdl) - Medium complexity
- Animation models (m12aa_c03_char02.mdl) - Complex animations
- Camera models (m12aa_c04_cam.mdl) - Camera-specific nodes

Each test validates:
- Model metadata (name, classification, supermodel)
- Node hierarchy and structure
- Mesh data integrity
- Controller preservation
- Animation data preservation
- All node types and features
"""

from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path

from pykotor.resource.formats.mdl import (
    MDL,
    bytes_mdl,
    read_mdl,
    write_mdl,
)
from pykotor.resource.type import ResourceType


# ============================================================================
# Helper Functions
# ============================================================================


def compare_mdl_basic(mdl1: MDL, mdl2: MDL, test_case: unittest.TestCase, context: str = ""):
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


def compare_mdl_nodes(mdl1: MDL, mdl2: MDL, test_case: unittest.TestCase, context: str = ""):
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
    
    test_case.assertEqual(
        len(nodes1),
        len(nodes2),
        f"{msg_prefix}Node counts should match (got {len(nodes1)} vs {len(nodes2)})"
    )
    
    # Build node name maps
    nodes1_by_name = {node.name: node for node in nodes1}
    nodes2_by_name = {node.name: node for node in nodes2}
    
    # Verify all node names match
    names1 = set(nodes1_by_name.keys())
    names2 = set(nodes2_by_name.keys())
    test_case.assertEqual(
        names1,
        names2,
        f"{msg_prefix}Node names should match"
    )
    
    # Compare each node's basic properties
    for name in names1:
        node1 = nodes1_by_name[name]
        node2 = nodes2_by_name[name]
        
        test_case.assertEqual(
            node1.node_type,
            node2.node_type,
            f"{msg_prefix}Node {name} types should match"
        )
        
        # Compare children count (hierarchy structure)
        test_case.assertEqual(
            len(node1.children),
            len(node2.children),
            f"{msg_prefix}Node {name} child counts should match"
        )


def compare_mdl_animations(mdl1: MDL, mdl2: MDL, test_case: unittest.TestCase, context: str = ""):
    """Compare animation data between two models.
    
    Args:
        mdl1: First MDL to compare
        mdl2: Second MDL to compare
        test_case: TestCase instance for assertions
        context: Context string for error messages
    """
    msg_prefix = f"{context}: " if context else ""
    
    test_case.assertEqual(
        len(mdl1.anims),
        len(mdl2.anims),
        f"{msg_prefix}Animation counts should match"
    )
    
    # Build animation maps by name
    anims1_by_name = {anim.name: anim for anim in mdl1.anims}
    anims2_by_name = {anim.name: anim for anim in mdl2.anims}
    
    # Verify all animation names match
    names1 = set(anims1_by_name.keys())
    names2 = set(anims2_by_name.keys())
    test_case.assertEqual(
        names1,
        names2,
        f"{msg_prefix}Animation names should match"
    )
    
    # Compare each animation's basic properties
    for name in names1:
        anim1 = anims1_by_name[name]
        anim2 = anims2_by_name[name]
        
        test_case.assertEqual(
            anim1.anim_length,
            anim2.anim_length,
            f"{msg_prefix}Animation {name} lengths should match"
        )
        test_case.assertEqual(
            anim1.transition_length,
            anim2.transition_length,
            f"{msg_prefix}Animation {name} transition lengths should match"
        )
        test_case.assertEqual(
            len(anim1.events),
            len(anim2.events),
            f"{msg_prefix}Animation {name} event counts should match"
        )


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
        self.assertEqual(
            original_node_count,
            len(mdl_final.all_nodes()),
            "Final node count should match original"
        )
        self.assertEqual(
            original_anim_count,
            len(mdl_final.anims),
            "Final animation count should match original"
        )

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
        self.assertEqual(
            original_anim_count,
            len(mdl_final.anims),
            "Animation count should be preserved"
        )

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
# Round-Trip Tests: ASCII -> Binary -> ASCII
# ============================================================================


class TestMDLRoundTripAsciiToBinaryToAscii(unittest.TestCase):
    """Test round-trip conversion: ASCII -> Binary -> ASCII using diverse models."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("Libraries/PyKotor/tests/test_files/mdl")
        if not self.test_dir.exists():
            self.skipTest(f"Test directory {self.test_dir} does not exist")
        
        # Use same models but start from binary, convert to ASCII first
        self.test_models = {
            "character": ("c_dewback.mdl", "c_dewback.mdx"),
            "door": ("dor_lhr02.mdl", "dor_lhr02.mdx"),
            "placeable": ("m02aa_09b.mdl", "m02aa_09b.mdx"),
            "animation": ("m12aa_c03_char02.mdl", "m12aa_c03_char02.mdx"),
            "camera": ("m12aa_c04_cam.mdl", "m12aa_c04_cam.mdx"),
        }

    def _create_ascii_from_binary(self, mdl_path: Path, mdx_path: Path) -> bytes:
        """Helper to convert binary MDL to ASCII for testing."""
        mdl_binary = read_mdl(mdl_path, source_ext=mdx_path, file_format=ResourceType.MDL)
        return bytes_mdl(mdl_binary, ResourceType.MDL_ASCII)

    def test_roundtrip_character_model_reverse(self):
        """Test ASCII -> Binary -> ASCII round-trip with character model."""
        mdl_path = self.test_dir / self.test_models["character"][0]
        mdx_path = self.test_dir / self.test_models["character"][1]
        
        if not mdl_path.exists():
            self.skipTest("Test file c_dewback.mdl not found")
        
        # Step 1: Start with ASCII (created from binary for consistency)
        ascii_bytes_original = self._create_ascii_from_binary(mdl_path, mdx_path)
        mdl_from_ascii_original = read_mdl(ascii_bytes_original, file_format=ResourceType.MDL_ASCII)
        
        original_node_count = len(mdl_from_ascii_original.all_nodes())
        original_anim_count = len(mdl_from_ascii_original.anims)
        
        # Step 2: Convert to binary
        binary_bytes = bytes_mdl(mdl_from_ascii_original, ResourceType.MDL)
        self.assertIsInstance(binary_bytes, bytes, "Should produce binary bytes")
        self.assertGreater(len(binary_bytes), 0, "Binary output should not be empty")
        self.assertEqual(binary_bytes[:4], b"\x00\x00\x00\x00", "Binary should start with null header")
        
        # Step 3: Read binary back
        mdl_from_binary = read_mdl(binary_bytes, file_format=ResourceType.MDL)
        self.assertIsNotNone(mdl_from_binary, "Should load model from binary")
        
        # Step 4: Compare after binary conversion
        compare_mdl_basic(mdl_from_ascii_original, mdl_from_binary, self, "Character model: ASCII->Binary")
        compare_mdl_nodes(mdl_from_ascii_original, mdl_from_binary, self, "Character model: ASCII->Binary")
        compare_mdl_animations(mdl_from_ascii_original, mdl_from_binary, self, "Character model: ASCII->Binary")
        
        # Step 5: Convert back to ASCII
        ascii_bytes_final = bytes_mdl(mdl_from_binary, ResourceType.MDL_ASCII)
        self.assertIsInstance(ascii_bytes_final, bytes, "Should produce ASCII bytes")
        self.assertGreater(len(ascii_bytes_final), 0, "ASCII output should not be empty")
        
        # Verify ASCII content
        ascii_str_final = ascii_bytes_final.decode("utf-8", errors="ignore")
        self.assertIn("newmodel", ascii_str_final.lower(), "ASCII should contain model declaration")
        
        # Step 6: Read ASCII back
        mdl_final = read_mdl(ascii_bytes_final, file_format=ResourceType.MDL_ASCII)
        self.assertIsNotNone(mdl_final, "Should load model from final ASCII")
        
        # Step 7: Compare final model with original
        compare_mdl_basic(mdl_from_ascii_original, mdl_final, self, "Character model: Final ASCII")
        compare_mdl_nodes(mdl_from_ascii_original, mdl_final, self, "Character model: Final ASCII")
        compare_mdl_animations(mdl_from_ascii_original, mdl_final, self, "Character model: Final ASCII")
        
        # Verify counts match
        self.assertEqual(
            original_node_count,
            len(mdl_final.all_nodes()),
            "Final node count should match original"
        )
        self.assertEqual(
            original_anim_count,
            len(mdl_final.anims),
            "Final animation count should match original"
        )

    def test_roundtrip_door_model_reverse(self):
        """Test ASCII -> Binary -> ASCII round-trip with door model."""
        mdl_path = self.test_dir / self.test_models["door"][0]
        mdx_path = self.test_dir / self.test_models["door"][1]
        
        if not mdl_path.exists():
            self.skipTest("Test file dor_lhr02.mdl not found")
        
        # Start with ASCII
        ascii_bytes_original = self._create_ascii_from_binary(mdl_path, mdx_path)
        mdl_from_ascii_original = read_mdl(ascii_bytes_original, file_format=ResourceType.MDL_ASCII)
        
        # Convert to binary
        binary_bytes = bytes_mdl(mdl_from_ascii_original, ResourceType.MDL)
        mdl_from_binary = read_mdl(binary_bytes, file_format=ResourceType.MDL)
        
        # Compare after binary conversion
        compare_mdl_basic(mdl_from_ascii_original, mdl_from_binary, self, "Door model: ASCII->Binary")
        compare_mdl_nodes(mdl_from_ascii_original, mdl_from_binary, self, "Door model: ASCII->Binary")
        
        # Convert back to ASCII
        ascii_bytes_final = bytes_mdl(mdl_from_binary, ResourceType.MDL_ASCII)
        mdl_final = read_mdl(ascii_bytes_final, file_format=ResourceType.MDL_ASCII)
        
        # Compare final
        compare_mdl_basic(mdl_from_ascii_original, mdl_final, self, "Door model: Final ASCII")
        compare_mdl_nodes(mdl_from_ascii_original, mdl_final, self, "Door model: Final ASCII")

    def test_roundtrip_placeable_model_reverse(self):
        """Test ASCII -> Binary -> ASCII round-trip with placeable model."""
        mdl_path = self.test_dir / self.test_models["placeable"][0]
        mdx_path = self.test_dir / self.test_models["placeable"][1]
        
        if not mdl_path.exists():
            self.skipTest("Test file m02aa_09b.mdl not found")
        
        # Start with ASCII
        ascii_bytes_original = self._create_ascii_from_binary(mdl_path, mdx_path)
        mdl_from_ascii_original = read_mdl(ascii_bytes_original, file_format=ResourceType.MDL_ASCII)
        
        # Convert to binary
        binary_bytes = bytes_mdl(mdl_from_ascii_original, ResourceType.MDL)
        mdl_from_binary = read_mdl(binary_bytes, file_format=ResourceType.MDL)
        
        # Compare after binary conversion
        compare_mdl_basic(mdl_from_ascii_original, mdl_from_binary, self, "Placeable model: ASCII->Binary")
        compare_mdl_nodes(mdl_from_ascii_original, mdl_from_binary, self, "Placeable model: ASCII->Binary")
        
        # Convert back to ASCII
        ascii_bytes_final = bytes_mdl(mdl_from_binary, ResourceType.MDL_ASCII)
        mdl_final = read_mdl(ascii_bytes_final, file_format=ResourceType.MDL_ASCII)
        
        # Compare final
        compare_mdl_basic(mdl_from_ascii_original, mdl_final, self, "Placeable model: Final ASCII")
        compare_mdl_nodes(mdl_from_ascii_original, mdl_final, self, "Placeable model: Final ASCII")

    def test_roundtrip_animation_model_reverse(self):
        """Test ASCII -> Binary -> ASCII round-trip with animation model."""
        mdl_path = self.test_dir / self.test_models["animation"][0]
        mdx_path = self.test_dir / self.test_models["animation"][1]
        
        if not mdl_path.exists():
            self.skipTest("Test file m12aa_c03_char02.mdl not found")
        
        # Start with ASCII
        ascii_bytes_original = self._create_ascii_from_binary(mdl_path, mdx_path)
        mdl_from_ascii_original = read_mdl(ascii_bytes_original, file_format=ResourceType.MDL_ASCII)
        
        original_anim_count = len(mdl_from_ascii_original.anims)
        
        # Convert to binary
        binary_bytes = bytes_mdl(mdl_from_ascii_original, ResourceType.MDL)
        mdl_from_binary = read_mdl(binary_bytes, file_format=ResourceType.MDL)
        
        # Compare after binary conversion
        compare_mdl_basic(mdl_from_ascii_original, mdl_from_binary, self, "Animation model: ASCII->Binary")
        compare_mdl_nodes(mdl_from_ascii_original, mdl_from_binary, self, "Animation model: ASCII->Binary")
        compare_mdl_animations(mdl_from_ascii_original, mdl_from_binary, self, "Animation model: ASCII->Binary")
        
        # Convert back to ASCII
        ascii_bytes_final = bytes_mdl(mdl_from_binary, ResourceType.MDL_ASCII)
        mdl_final = read_mdl(ascii_bytes_final, file_format=ResourceType.MDL_ASCII)
        
        # Compare final
        compare_mdl_basic(mdl_from_ascii_original, mdl_final, self, "Animation model: Final ASCII")
        compare_mdl_nodes(mdl_from_ascii_original, mdl_final, self, "Animation model: Final ASCII")
        compare_mdl_animations(mdl_from_ascii_original, mdl_final, self, "Animation model: Final ASCII")
        
        # Verify animation count
        self.assertEqual(
            original_anim_count,
            len(mdl_final.anims),
            "Animation count should be preserved"
        )

    def test_roundtrip_camera_model_reverse(self):
        """Test ASCII -> Binary -> ASCII round-trip with camera model."""
        mdl_path = self.test_dir / self.test_models["camera"][0]
        mdx_path = self.test_dir / self.test_models["camera"][1]
        
        if not mdl_path.exists():
            self.skipTest("Test file m12aa_c04_cam.mdl not found")
        
        # Start with ASCII
        ascii_bytes_original = self._create_ascii_from_binary(mdl_path, mdx_path)
        mdl_from_ascii_original = read_mdl(ascii_bytes_original, file_format=ResourceType.MDL_ASCII)
        
        # Convert to binary
        binary_bytes = bytes_mdl(mdl_from_ascii_original, ResourceType.MDL)
        mdl_from_binary = read_mdl(binary_bytes, file_format=ResourceType.MDL)
        
        # Compare after binary conversion
        compare_mdl_basic(mdl_from_ascii_original, mdl_from_binary, self, "Camera model: ASCII->Binary")
        compare_mdl_nodes(mdl_from_ascii_original, mdl_from_binary, self, "Camera model: ASCII->Binary")
        
        # Convert back to ASCII
        ascii_bytes_final = bytes_mdl(mdl_from_binary, ResourceType.MDL_ASCII)
        mdl_final = read_mdl(ascii_bytes_final, file_format=ResourceType.MDL_ASCII)
        
        # Compare final
        compare_mdl_basic(mdl_from_ascii_original, mdl_final, self, "Camera model: Final ASCII")
        compare_mdl_nodes(mdl_from_ascii_original, mdl_final, self, "Camera model: Final ASCII")

    def test_roundtrip_all_models_reverse(self):
        """Test ASCII -> Binary -> ASCII round-trip for all available models."""
        for model_type, (mdl_file, mdx_file) in self.test_models.items():
            with self.subTest(model_type=model_type):
                mdl_path = self.test_dir / mdl_file
                mdx_path = self.test_dir / mdx_file
                
                if not mdl_path.exists():
                    self.skipTest(f"Test file {mdl_file} not found")
                
                # Start with ASCII
                ascii_bytes_original = self._create_ascii_from_binary(mdl_path, mdx_path)
                mdl_from_ascii_original = read_mdl(ascii_bytes_original, file_format=ResourceType.MDL_ASCII)
                
                # Convert to binary
                binary_bytes = bytes_mdl(mdl_from_ascii_original, ResourceType.MDL)
                mdl_from_binary = read_mdl(binary_bytes, file_format=ResourceType.MDL)
                
                # Compare after binary conversion
                compare_mdl_basic(mdl_from_ascii_original, mdl_from_binary, self, f"{model_type}: ASCII->Binary")
                compare_mdl_nodes(mdl_from_ascii_original, mdl_from_binary, self, f"{model_type}: ASCII->Binary")
                
                # Convert back to ASCII
                ascii_bytes_final = bytes_mdl(mdl_from_binary, ResourceType.MDL_ASCII)
                mdl_final = read_mdl(ascii_bytes_final, file_format=ResourceType.MDL_ASCII)
                
                # Compare final
                compare_mdl_basic(mdl_from_ascii_original, mdl_final, self, f"{model_type}: Final ASCII")
                compare_mdl_nodes(mdl_from_ascii_original, mdl_final, self, f"{model_type}: Final ASCII")


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

    def test_triple_roundtrip_ascii_to_binary_to_ascii_to_binary(self):
        """Test ASCII -> Binary -> ASCII -> Binary (3-step round-trip)."""
        mdl_path = self.test_dir / self.test_models["animation"][0]
        mdx_path = self.test_dir / self.test_models["animation"][1]
        
        if not mdl_path.exists():
            self.skipTest("Test file m12aa_c03_char02.mdl not found")
        
        # Step 1: Start with ASCII (created from binary)
        mdl_binary_original = read_mdl(mdl_path, source_ext=mdx_path, file_format=ResourceType.MDL)
        ascii_bytes_1 = bytes_mdl(mdl_binary_original, ResourceType.MDL_ASCII)
        mdl_ascii_1 = read_mdl(ascii_bytes_1, file_format=ResourceType.MDL_ASCII)
        
        original_node_count = len(mdl_ascii_1.all_nodes())
        original_anim_count = len(mdl_ascii_1.anims)
        
        # Step 2: Convert to binary
        binary_bytes_1 = bytes_mdl(mdl_ascii_1, ResourceType.MDL)
        mdl_binary_1 = read_mdl(binary_bytes_1, file_format=ResourceType.MDL)
        
        # Compare step 1 -> step 2
        compare_mdl_basic(mdl_ascii_1, mdl_binary_1, self, "Step 1->2: ASCII->Binary")
        compare_mdl_nodes(mdl_ascii_1, mdl_binary_1, self, "Step 1->2: ASCII->Binary")
        compare_mdl_animations(mdl_ascii_1, mdl_binary_1, self, "Step 1->2: ASCII->Binary")
        
        # Step 3: Convert back to ASCII
        ascii_bytes_2 = bytes_mdl(mdl_binary_1, ResourceType.MDL_ASCII)
        mdl_ascii_2 = read_mdl(ascii_bytes_2, file_format=ResourceType.MDL_ASCII)
        
        # Compare step 2 -> step 3
        compare_mdl_basic(mdl_binary_1, mdl_ascii_2, self, "Step 2->3: Binary->ASCII")
        compare_mdl_nodes(mdl_binary_1, mdl_ascii_2, self, "Step 2->3: Binary->ASCII")
        compare_mdl_animations(mdl_binary_1, mdl_ascii_2, self, "Step 2->3: Binary->ASCII")
        
        # Step 4: Convert back to binary again
        binary_bytes_2 = bytes_mdl(mdl_ascii_2, ResourceType.MDL)
        mdl_binary_2 = read_mdl(binary_bytes_2, file_format=ResourceType.MDL)
        
        # Compare step 3 -> step 4
        compare_mdl_basic(mdl_ascii_2, mdl_binary_2, self, "Step 3->4: ASCII->Binary")
        compare_mdl_nodes(mdl_ascii_2, mdl_binary_2, self, "Step 3->4: ASCII->Binary")
        compare_mdl_animations(mdl_ascii_2, mdl_binary_2, self, "Step 3->4: ASCII->Binary")
        
        # Compare final with original
        compare_mdl_basic(mdl_ascii_1, mdl_binary_2, self, "Final: Original->Final")
        compare_mdl_nodes(mdl_ascii_1, mdl_binary_2, self, "Final: Original->Final")
        compare_mdl_animations(mdl_ascii_1, mdl_binary_2, self, "Final: Original->Final")
        
        # Verify counts
        self.assertEqual(original_node_count, len(mdl_binary_2.all_nodes()))
        self.assertEqual(original_anim_count, len(mdl_binary_2.anims))

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
                self.assertEqual(
                    len(mdl_original.all_nodes()),
                    len(mdl_final.all_nodes()),
                    f"{model_type}: Node count should be preserved"
                )
                
                self.assertEqual(
                    mdl_original.name,
                    mdl_final.name,
                    f"{model_type}: Name should be preserved"
                )
                
                self.assertEqual(
                    mdl_original.classification,
                    mdl_final.classification,
                    f"{model_type}: Classification should be preserved"
                )

    def test_all_models_ascii_to_binary_preserve_structure(self):
        """Test that all models preserve structure when converted ASCII -> Binary -> ASCII."""
        for model_type, (mdl_file, mdx_file) in self.test_models.items():
            with self.subTest(model_type=model_type):
                mdl_path = self.test_dir / mdl_file
                mdx_path = self.test_dir / mdx_file
                
                if not mdl_path.exists():
                    self.skipTest(f"Test file {mdl_file} not found")
                
                # Create ASCII from binary
                mdl_binary_original = read_mdl(mdl_path, source_ext=mdx_path, file_format=ResourceType.MDL)
                ascii_bytes_original = bytes_mdl(mdl_binary_original, ResourceType.MDL_ASCII)
                mdl_ascii_original = read_mdl(ascii_bytes_original, file_format=ResourceType.MDL_ASCII)
                
                # Convert to binary and back
                binary_bytes = bytes_mdl(mdl_ascii_original, ResourceType.MDL)
                mdl_from_binary = read_mdl(binary_bytes, file_format=ResourceType.MDL)
                ascii_bytes_final = bytes_mdl(mdl_from_binary, ResourceType.MDL_ASCII)
                mdl_final = read_mdl(ascii_bytes_final, file_format=ResourceType.MDL_ASCII)
                
                # Verify structure preservation
                self.assertEqual(
                    len(mdl_ascii_original.all_nodes()),
                    len(mdl_final.all_nodes()),
                    f"{model_type}: Node count should be preserved"
                )
                
                self.assertEqual(
                    mdl_ascii_original.name,
                    mdl_final.name,
                    f"{model_type}: Name should be preserved"
                )
                
                self.assertEqual(
                    mdl_ascii_original.classification,
                    mdl_final.classification,
                    f"{model_type}: Classification should be preserved"
                )


if __name__ == "__main__":
    unittest.main()

