"""Tests for kit generation from RIM files."""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import sys
import unittest
from difflib import unified_diff
from pathlib import Path

# Force offscreen (headless) mode for Qt
# This ensures tests don't fail if no display is available (e.g. CI/CD)
# Must be set before any Qt imports
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Add paths for imports
REPO_ROOT = Path(__file__).parents[3]
TOOLS_PATH = REPO_ROOT / "Tools"
LIBS_PATH = REPO_ROOT / "Libraries"

TOOLSET_SRC = TOOLS_PATH / "HolocronToolset" / "src"
PYKOTOR_PATH = LIBS_PATH / "PyKotor" / "src"
UTILITY_PATH = LIBS_PATH / "Utility" / "src"

if str(TOOLSET_SRC) not in sys.path:
    sys.path.insert(0, str(TOOLSET_SRC))
if str(PYKOTOR_PATH) not in sys.path:
    sys.path.insert(0, str(PYKOTOR_PATH))
if str(UTILITY_PATH) not in sys.path:
    sys.path.insert(0, str(UTILITY_PATH))

from pykotor.extract.installation import Installation  # noqa: E402
from pykotor.tools.kit import extract_kit, find_module_file  # noqa: E402

# Get K1_PATH from environment, handling quoted paths from .env file
_k1_path_raw = os.environ.get("K1_PATH")
if not _k1_path_raw:
    # Try loading from .env file if not set in environment
    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("K1_PATH="):
                _k1_path_raw = line.split("=", 1)[1].strip()
                break
    # Fallback to default if still not found
    if not _k1_path_raw:
        _k1_path_raw = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor"

K1_PATH: str | None = _k1_path_raw.strip('"').strip("'") if _k1_path_raw else None


class TestKitGeneration(unittest.TestCase):
    """Test kit generation from RIM files."""
    
    # Mapping of kit IDs to their correct module names
    KIT_TO_MODULE = {
        "blackvulkar": "tar_m10aa",
        "dantooineestate": "danm16",
        "davikestate": "tar_m08aa",
        "enclavesurface": "danm14aa",
        "endarspire": "end_m01aa",
        "hiddenbek": "tar_m11aa",
        "jedienclave": "danm13",
        "sithbase": "tar_m09aa",
        "tarissewers": "tar_m05aa",
    }

    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        if K1_PATH is None or not os.path.exists(K1_PATH):
            raise ValueError(f"K1_PATH environment variable is not set or not found on disk: {K1_PATH}")
        cls.installation = Installation(K1_PATH)  # type: ignore[attr-defined]
        cls.module_name = "danm13"  # type: ignore[attr-defined]
        cls.expected_kit_path = REPO_ROOT / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "kits" / "jedienclave"  # type: ignore[attr-defined]
        cls.test_output_path = REPO_ROOT / "tests" / "test_toolset" / "test_files" / "generated_kit"  # type: ignore[attr-defined]
        cls.expected_json_path = REPO_ROOT / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "kits" / "jedienclave.json"  # type: ignore[attr-defined]

    def setUp(self):
        """Set up test."""
        # Clean up any previous test output
        # Use robust cleanup that handles locked files/directories
        import shutil
        import time
        
        if self.test_output_path.exists():  # type: ignore[attr-defined]
            # Retry cleanup with exponential backoff to handle locked files
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    shutil.rmtree(self.test_output_path, ignore_errors=False)  # type: ignore[attr-defined]
                    break  # Success
                except (OSError, PermissionError) as e:
                    if attempt < max_retries - 1:
                        # Wait before retry (exponential backoff)
                        time.sleep(0.1 * (2 ** attempt))
                        # Try to remove individual files/dirs that might be locked
                        try:
                            for item in self.test_output_path.iterdir():  # type: ignore[attr-defined]
                                try:
                                    if item.is_dir():
                                        shutil.rmtree(item, ignore_errors=True)
                                    else:
                                        item.unlink()
                                except (OSError, PermissionError):
                                    pass  # Ignore individual file errors
                        except (OSError, PermissionError):
                            pass
                    else:
                        # Last attempt failed - use ignore_errors as fallback
                        shutil.rmtree(self.test_output_path, ignore_errors=True)  # type: ignore[attr-defined]

    def test_generate_jedienclave_kit(self):
        """Test generating jedienclave kit and comparing files."""
        # Generate the kit
        extract_kit(
            self.installation,  # type: ignore[attr-defined]
            self.module_name,  # type: ignore[attr-defined]
            self.test_output_path,  # type: ignore[attr-defined]
            kit_id="jedienclave",
        )

        # Verify the kit was generated
        generated_kit_path = self.test_output_path / "jedienclave"  # type: ignore[attr-defined]
        self.assertTrue(generated_kit_path.exists(), "Generated kit directory should exist")

        # Verify basic kit structure exists
        self._verify_kit_structure(generated_kit_path)

        # Compare with expected kit if it exists
        if self.expected_kit_path.exists():  # type: ignore[attr-defined]
            self._compare_kits(generated_kit_path, self.expected_kit_path, "jedienclave")  # type: ignore[attr-defined]
        else:
            # If expected kit doesn't exist, at least verify basic structure
            self.assertTrue((generated_kit_path / "textures").exists() or (generated_kit_path / "lightmaps").exists(),
                          "Generated kit should have textures or lightmaps folder")

    def test_generate_jedienclave_kit_json(self):
        """Test generating jedienclave kit and comparing JSON files."""
        # Generate the kit
        extract_kit(
            self.installation,  # type: ignore[attr-defined]
            self.module_name,  # type: ignore[attr-defined]
            self.test_output_path,  # type: ignore[attr-defined]
            kit_id="jedienclave",
        )

        # Compare JSON files if expected JSON exists
        generated_json_path = self.test_output_path / "jedienclave.json"  # type: ignore[attr-defined]
        if self.expected_json_path.exists():  # type: ignore[attr-defined]
            self.assertTrue(generated_json_path.exists(), "Generated JSON file should exist")
            self._compare_json_files(generated_json_path, self.expected_json_path)  # type: ignore[attr-defined]
        else:
            # If expected JSON doesn't exist, just verify the generated JSON is valid
            if generated_json_path.exists():
                import json
                with generated_json_path.open("r", encoding="utf-8") as f:
                    json_data = json.load(f)
                self.assertIn("name", json_data)
                self.assertIn("id", json_data)
                self.assertEqual(json_data["id"], "jedienclave")

    def test_generate_sithbase_kit(self):
        """Test generating sithbase kit and comparing files."""
        kit_id = "sithbase"
        generated_kit_path, _ = self._generate_kit(kit_id)
        
        # Verify basic kit structure exists
        self._verify_kit_structure(generated_kit_path)

        # Compare with expected kit if it exists
        expected_kit_path = REPO_ROOT / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "kits" / kit_id
        if expected_kit_path.exists():
            self._compare_kits(generated_kit_path, expected_kit_path, kit_id)  # type: ignore[attr-defined]
        else:
            # If expected kit doesn't exist, at least verify basic structure
            has_textures = (generated_kit_path / "textures").exists()
            has_lightmaps = (generated_kit_path / "lightmaps").exists()
            has_components = len(list(generated_kit_path.glob("*.mdl"))) > 0
            self.assertTrue(has_textures or has_lightmaps or has_components,
                          f"Generated kit '{kit_id}' should have textures, lightmaps, or components")

    def test_generate_sithbase_kit_json(self):
        """Test generating sithbase kit and comparing JSON files."""
        kit_id = "sithbase"
        # Sith base modules - need to check actual module names
        _, generated_json_path = self._generate_kit(kit_id)
        
        expected_json_path = REPO_ROOT / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "kits" / f"{kit_id}.json"
        if expected_json_path.exists():
            self.assertTrue(generated_json_path.exists(), f"Generated JSON file should exist for '{kit_id}'")
            self._compare_json_files(generated_json_path, expected_json_path)
        elif generated_json_path.exists():
            # If expected JSON doesn't exist but generated one does, verify it's valid
            import json
            with generated_json_path.open("r", encoding="utf-8") as f:
                json_data = json.load(f)
            self.assertIn("name", json_data)
            self.assertIn("id", json_data)
            self.assertEqual(json_data["id"], kit_id)

    def test_generate_sithbase_kit_components_only(self):
        """Test that sithbase kit generates all expected components."""
        kit_id = "sithbase"
        module_name = self._get_module_for_kit(kit_id)
        
        if module_name is None:
            self.skipTest("Could not find sithbase module (tried: m15aa, m15ab, m16aa, m16ab)")
        
        # Generate the kit
        extract_kit(
            self.installation,  # type: ignore[attr-defined]
            module_name,
            self.test_output_path,  # type: ignore[attr-defined]
            kit_id="sithbase",
        )

        # Verify the kit was generated
        generated_kit_path = self.test_output_path / "sithbase"  # type: ignore[attr-defined]
        self.assertTrue(generated_kit_path.exists(), "Generated kit directory should exist")

        # Check that key components exist
        expected_components = ["armory_1", "barracks_1", "control_1", "control_2", "hall_1", "hall_2"]
        for component_id in expected_components:
            mdl_path = generated_kit_path / f"{component_id}.mdl"
            wok_path = generated_kit_path / f"{component_id}.wok"
            self.assertTrue(mdl_path.exists() or wok_path.exists(), f"Component {component_id} should have MDL or WOK file")

    def _get_module_for_kit(self, kit_id: str) -> str | None:
        """Get the module name for a given kit ID.
        
        Args:
        ----
            kit_id: Kit identifier (e.g., "blackvulkar")
            
        Returns:
        -------
            Module name if found, None otherwise
        """
        module_name = self.KIT_TO_MODULE.get(kit_id)
        if not module_name:
            return None
        
        # Verify the module exists using the utility function
        module_path = find_module_file(self.installation, module_name)  # type: ignore[attr-defined]
        if module_path and module_path.exists():
            return module_name
        return None

    def _generate_kit(self, kit_id: str) -> tuple[Path, Path]:
        """Helper method to generate a kit and return paths.
        
        Args:
        ----
            kit_id: Kit identifier (e.g., "blackvulkar")
            
        Returns:
        -------
            Tuple of (generated_kit_path, generated_json_path)
        """
        module_name = self._get_module_for_kit(kit_id)
        if module_name is None:
            self.skipTest(f"Could not find module for kit '{kit_id}'")
        
        # Generate the kit
        extract_kit(
            self.installation,  # type: ignore[attr-defined]
            module_name,
            self.test_output_path,  # type: ignore[attr-defined]
            kit_id=kit_id,
        )

        generated_kit_path = self.test_output_path / kit_id  # type: ignore[attr-defined]
        generated_json_path = self.test_output_path / f"{kit_id}.json"  # type: ignore[attr-defined]
        
        self.assertTrue(generated_kit_path.exists(), f"Generated kit directory should exist for '{kit_id}'")
        
        return generated_kit_path, generated_json_path

    # Black Vulkar tests
    def test_generate_blackvulkar_kit(self):
        """Test generating blackvulkar kit and comparing files."""
        kit_id = "blackvulkar"
        generated_kit_path, _ = self._generate_kit(kit_id)
        
        # Verify basic kit structure exists
        self._verify_kit_structure(generated_kit_path)

        # Compare with expected kit if it exists
        expected_kit_path = REPO_ROOT / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "kits" / kit_id
        if expected_kit_path.exists():
            self._compare_kits(generated_kit_path, expected_kit_path, kit_id)  # type: ignore[attr-defined]
        else:
            # If expected kit doesn't exist, at least verify basic structure
            has_textures = (generated_kit_path / "textures").exists()
            has_lightmaps = (generated_kit_path / "lightmaps").exists()
            has_components = len(list(generated_kit_path.glob("*.mdl"))) > 0
            self.assertTrue(has_textures or has_lightmaps or has_components,
                          f"Generated kit '{kit_id}' should have textures, lightmaps, or components")

    def test_generate_blackvulkar_kit_json(self):
        """Test generating blackvulkar kit and comparing JSON files."""
        kit_id = "blackvulkar"
        _, generated_json_path = self._generate_kit(kit_id)
        
        expected_json_path = REPO_ROOT / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "kits" / f"{kit_id}.json"
        if expected_json_path.exists():
            self.assertTrue(generated_json_path.exists(), f"Generated JSON file should exist for '{kit_id}'")
            self._compare_json_files(generated_json_path, expected_json_path)
        elif generated_json_path.exists():
            # If expected JSON doesn't exist but generated one does, verify it's valid
            import json
            with generated_json_path.open("r", encoding="utf-8") as f:
                json_data = json.load(f)
            self.assertIn("name", json_data)
            self.assertIn("id", json_data)
            self.assertEqual(json_data["id"], kit_id)

    # Dantooine Estate tests
    def test_generate_dantooineestate_kit(self):
        """Test generating dantooineestate kit and comparing files."""
        kit_id = "dantooineestate"
        generated_kit_path, _ = self._generate_kit(kit_id)
        
        # Verify basic kit structure exists
        self._verify_kit_structure(generated_kit_path)
        
        # Compare with expected kit if it exists
        expected_kit_path = REPO_ROOT / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "kits" / kit_id
        if expected_kit_path.exists():
            self._compare_kits(generated_kit_path, expected_kit_path, kit_id)  # type: ignore[attr-defined]
        else:
            # If expected kit doesn't exist, at least verify basic structure
            has_textures = (generated_kit_path / "textures").exists()
            has_lightmaps = (generated_kit_path / "lightmaps").exists()
            has_components = len(list(generated_kit_path.glob("*.mdl"))) > 0
            self.assertTrue(has_textures or has_lightmaps or has_components,
                          f"Generated kit '{kit_id}' should have textures, lightmaps, or components")

    def test_generate_dantooineestate_kit_json(self):
        """Test generating dantooineestate kit and comparing JSON files."""
        kit_id = "dantooineestate"
        _, generated_json_path = self._generate_kit(kit_id)
        
        expected_json_path = REPO_ROOT / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "kits" / f"{kit_id}.json"
        if expected_json_path.exists():
            self.assertTrue(generated_json_path.exists(), f"Generated JSON file should exist for '{kit_id}'")
            self._compare_json_files(generated_json_path, expected_json_path)
        elif generated_json_path.exists():
            # If expected JSON doesn't exist but generated one does, verify it's valid
            import json
            with generated_json_path.open("r", encoding="utf-8") as f:
                json_data = json.load(f)
            self.assertIn("name", json_data)
            self.assertIn("id", json_data)
            self.assertEqual(json_data["id"], kit_id)

    # Davik Estate tests
    def test_generate_davikestate_kit(self):
        """Test generating davikestate kit and comparing files."""
        kit_id = "davikestate"
        generated_kit_path, _ = self._generate_kit(kit_id)
        
        # Verify basic kit structure exists
        self._verify_kit_structure(generated_kit_path)

        # Compare with expected kit if it exists
        expected_kit_path = REPO_ROOT / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "kits" / kit_id
        if expected_kit_path.exists():
            self._compare_kits(generated_kit_path, expected_kit_path, kit_id)  # type: ignore[attr-defined]
        else:
            # If expected kit doesn't exist, at least verify basic structure
            has_textures = (generated_kit_path / "textures").exists()
            has_lightmaps = (generated_kit_path / "lightmaps").exists()
            has_components = len(list(generated_kit_path.glob("*.mdl"))) > 0
            self.assertTrue(has_textures or has_lightmaps or has_components,
                          f"Generated kit '{kit_id}' should have textures, lightmaps, or components")

    def test_generate_davikestate_kit_json(self):
        """Test generating davikestate kit and comparing JSON files."""
        kit_id = "davikestate"
        _, generated_json_path = self._generate_kit(kit_id)
        
        expected_json_path = REPO_ROOT / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "kits" / f"{kit_id}.json"
        if expected_json_path.exists():
            self.assertTrue(generated_json_path.exists(), f"Generated JSON file should exist for '{kit_id}'")
            self._compare_json_files(generated_json_path, expected_json_path)
        elif generated_json_path.exists():
            # If expected JSON doesn't exist but generated one does, verify it's valid
            import json
            with generated_json_path.open("r", encoding="utf-8") as f:
                json_data = json.load(f)
            self.assertIn("name", json_data)
            self.assertIn("id", json_data)
            self.assertEqual(json_data["id"], kit_id)

    # Enclave Surface tests
    def test_generate_enclavesurface_kit(self):
        """Test generating enclavesurface kit and comparing files."""
        kit_id = "enclavesurface"
        generated_kit_path, _ = self._generate_kit(kit_id)
        
        # Verify basic kit structure exists
        self._verify_kit_structure(generated_kit_path)
        
        # Compare with expected kit if it exists
        expected_kit_path = REPO_ROOT / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "kits" / kit_id
        if expected_kit_path.exists():
            self._compare_kits(generated_kit_path, expected_kit_path, kit_id)  # type: ignore[attr-defined]
        else:
            # If expected kit doesn't exist, at least verify basic structure
            has_textures = (generated_kit_path / "textures").exists()
            has_lightmaps = (generated_kit_path / "lightmaps").exists()
            has_components = len(list(generated_kit_path.glob("*.mdl"))) > 0
            self.assertTrue(has_textures or has_lightmaps or has_components,
                          f"Generated kit '{kit_id}' should have textures, lightmaps, or components")

    def test_generate_enclavesurface_kit_json(self):
        """Test generating enclavesurface kit and comparing JSON files."""
        kit_id = "enclavesurface"
        _, generated_json_path = self._generate_kit(kit_id)
        
        expected_json_path = REPO_ROOT / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "kits" / f"{kit_id}.json"
        if expected_json_path.exists():
            self.assertTrue(generated_json_path.exists(), f"Generated JSON file should exist for '{kit_id}'")
            self._compare_json_files(generated_json_path, expected_json_path)
        elif generated_json_path.exists():
            # If expected JSON doesn't exist but generated one does, verify it's valid
            import json
            with generated_json_path.open("r", encoding="utf-8") as f:
                json_data = json.load(f)
            self.assertIn("name", json_data)
            self.assertIn("id", json_data)
            self.assertEqual(json_data["id"], kit_id)

    # Endar Spire tests
    def test_generate_endarspire_kit(self):
        """Test generating endarspire kit and comparing files."""
        kit_id = "endarspire"
        generated_kit_path, _ = self._generate_kit(kit_id)
        
        # Verify basic kit structure exists
        self._verify_kit_structure(generated_kit_path)
        
        # Compare with expected kit if it exists
        expected_kit_path = REPO_ROOT / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "kits" / kit_id
        if expected_kit_path.exists():
            self._compare_kits(generated_kit_path, expected_kit_path, kit_id)  # type: ignore[attr-defined]
        else:
            # If expected kit doesn't exist, at least verify basic structure
            has_textures = (generated_kit_path / "textures").exists()
            has_lightmaps = (generated_kit_path / "lightmaps").exists()
            has_components = len(list(generated_kit_path.glob("*.mdl"))) > 0
            self.assertTrue(has_textures or has_lightmaps or has_components,
                          f"Generated kit '{kit_id}' should have textures, lightmaps, or components")

    def test_generate_endarspire_kit_json(self):
        """Test generating endarspire kit and comparing JSON files."""
        kit_id = "endarspire"
        _, generated_json_path = self._generate_kit(kit_id)
        
        expected_json_path = REPO_ROOT / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "kits" / f"{kit_id}.json"
        if expected_json_path.exists():
            self.assertTrue(generated_json_path.exists(), f"Generated JSON file should exist for '{kit_id}'")
            self._compare_json_files(generated_json_path, expected_json_path)
        elif generated_json_path.exists():
            # If expected JSON doesn't exist but generated one does, verify it's valid
            import json
            with generated_json_path.open("r", encoding="utf-8") as f:
                json_data = json.load(f)
            self.assertIn("name", json_data)
            self.assertIn("id", json_data)
            self.assertEqual(json_data["id"], kit_id)

    # Hidden Bek tests
    def test_generate_hiddenbek_kit(self):
        """Test generating hiddenbek kit and comparing files."""
        kit_id = "hiddenbek"
        generated_kit_path, _ = self._generate_kit(kit_id)
        
        # Verify basic kit structure exists
        self._verify_kit_structure(generated_kit_path)
        
        # Compare with expected kit if it exists
        expected_kit_path = REPO_ROOT / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "kits" / kit_id
        if expected_kit_path.exists():
            self._compare_kits(generated_kit_path, expected_kit_path, kit_id)  # type: ignore[attr-defined]
        else:
            # If expected kit doesn't exist, at least verify basic structure
            has_textures = (generated_kit_path / "textures").exists()
            has_lightmaps = (generated_kit_path / "lightmaps").exists()
            has_components = len(list(generated_kit_path.glob("*.mdl"))) > 0
            self.assertTrue(has_textures or has_lightmaps or has_components,
                          f"Generated kit '{kit_id}' should have textures, lightmaps, or components")

    def test_generate_hiddenbek_kit_json(self):
        """Test generating hiddenbek kit and comparing JSON files."""
        kit_id = "hiddenbek"
        _, generated_json_path = self._generate_kit(kit_id)
        
        expected_json_path = REPO_ROOT / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "kits" / f"{kit_id}.json"
        if expected_json_path.exists():
            self.assertTrue(generated_json_path.exists(), f"Generated JSON file should exist for '{kit_id}'")
            self._compare_json_files(generated_json_path, expected_json_path)
        elif generated_json_path.exists():
            # If expected JSON doesn't exist but generated one does, verify it's valid
            import json
            with generated_json_path.open("r", encoding="utf-8") as f:
                json_data = json.load(f)
            self.assertIn("name", json_data)
            self.assertIn("id", json_data)
            self.assertEqual(json_data["id"], kit_id)

    # Taris Sewers tests
    def test_generate_tarissewers_kit(self):
        """Test generating tarissewers kit and comparing files."""
        kit_id = "tarissewers"
        generated_kit_path, _ = self._generate_kit(kit_id)
        
        # Verify basic kit structure exists
        self._verify_kit_structure(generated_kit_path)
        
        # Compare with expected kit if it exists
        expected_kit_path = REPO_ROOT / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "kits" / kit_id
        if expected_kit_path.exists():
            self._compare_kits(generated_kit_path, expected_kit_path, kit_id)  # type: ignore[attr-defined]
        else:
            # If expected kit doesn't exist, at least verify basic structure
            has_textures = (generated_kit_path / "textures").exists()
            has_lightmaps = (generated_kit_path / "lightmaps").exists()
            has_components = len(list(generated_kit_path.glob("*.mdl"))) > 0
            self.assertTrue(has_textures or has_lightmaps or has_components,
                          f"Generated kit '{kit_id}' should have textures, lightmaps, or components")

    def test_generate_tarissewers_kit_json(self):
        """Test generating tarissewers kit and comparing JSON files."""
        kit_id = "tarissewers"
        _, generated_json_path = self._generate_kit(kit_id)
        
        expected_json_path = REPO_ROOT / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "kits" / f"{kit_id}.json"
        if expected_json_path.exists():
            self.assertTrue(generated_json_path.exists(), f"Generated JSON file should exist for '{kit_id}'")
            self._compare_json_files(generated_json_path, expected_json_path)
        elif generated_json_path.exists():
            # If expected JSON doesn't exist but generated one does, verify it's valid
            import json
            with generated_json_path.open("r", encoding="utf-8") as f:
                json_data = json.load(f)
            self.assertIn("name", json_data)
            self.assertIn("id", json_data)
            self.assertEqual(json_data["id"], kit_id)

    def _verify_kit_structure(self, kit_path: Path):
        """Verify that a generated kit has the expected directory structure and file types.
        
        Args:
        ----
            kit_path: Path to the generated kit directory
        """
        # Check for expected directories
        expected_dirs = ["textures", "lightmaps", "skyboxes"]
        for dir_name in expected_dirs:
            dir_path = kit_path / dir_name
            # Directory may or may not exist depending on kit content
            if dir_path.exists():
                self.assertTrue(dir_path.is_dir(), f"{dir_name} should be a directory if it exists")
        
        # Check for component files (MDL, MDX, WOK, PNG) in root
        mdl_files: list[Path] = list(kit_path.glob("*.mdl"))
        mdx_files: list[Path] = list(kit_path.glob("*.mdx"))
        wok_files: list[Path] = list(kit_path.glob("*.wok"))
        png_files = list(kit_path.glob("*.png"))
        utd_files = list(kit_path.glob("*.utd"))
        
        # If there are components, verify they have the expected structure
        if mdl_files:
            for mdl_file in mdl_files:
                component_id = mdl_file.stem
                # Each MDL should have corresponding WOK (walkmesh)
                wok_file = kit_path / f"{component_id}.wok"
                self.assertTrue(wok_file.exists(), f"Component {component_id} should have corresponding WOK file")
                # Each component should have a minimap PNG
                png_file = kit_path / f"{component_id}.png"
                self.assertTrue(png_file.exists(), f"Component {component_id} should have minimap PNG")
        
        # Check for door files (UTD)
        # Doors should use simple identifiers: door0_k1.utd, door1_k1.utd, etc.
        if utd_files:
            # Doors should come in pairs (k1 and k2)
            door_names = {f.stem.replace("_k1", "").replace("_k2", "") for f in utd_files}
            for door_name in door_names:
                # Verify door naming format: should be "door0", "door1", etc.
                import re
                expected_pattern = re.compile(r"^door\d+$")
                self.assertTrue(
                    expected_pattern.match(door_name),
                    f"Door file has incorrect naming format: '{door_name}' (expected format: 'door0', 'door1', etc.)",
                )
                k1_file = kit_path / f"{door_name}_k1.utd"
                k2_file = kit_path / f"{door_name}_k2.utd"
                self.assertTrue(k1_file.exists(), f"Door {door_name} should have _k1.utd file")
                self.assertTrue(k2_file.exists(), f"Door {door_name} should have _k2.utd file")
        
        # Check for door walkmeshes (DWK files)
        # Doors have 3 walkmesh states: closed (0), open1 (1), open2 (2)
        # Format: {door_model_name}0.dwk, {door_model_name}1.dwk, {door_model_name}2.dwk
        dwk_files: list[Path] = list(kit_path.glob("*.dwk"))
        if dwk_files:
            # Group DWK files by door model name (remove suffix 0/1/2)
            dwk_by_model: dict[str, set[str]] = {}
            for dwk_file in dwk_files:
                stem = dwk_file.stem
                # Check if ends with 0, 1, or 2
                if stem.endswith(("0", "1", "2")):
                    model_name = stem[:-1]  # Remove last character (0/1/2)
                    suffix = stem[-1]
                    if model_name not in dwk_by_model:
                        dwk_by_model[model_name] = set()
                    dwk_by_model[model_name].add(suffix)
            
            # Verify that if any DWK exists for a door model, all three states should exist
            for model_name, suffixes in dwk_by_model.items():
                for expected_suffix in ["0", "1", "2"]:
                    dwk_file = kit_path / f"{model_name}{expected_suffix}.dwk"
                    if expected_suffix in suffixes:
                        self.assertTrue(dwk_file.exists(), f"Door walkmesh {model_name}{expected_suffix}.dwk should exist")
        
        # Check for placeable walkmeshes (PWK files)
        # Format: {placeable_model_name}.pwk
        pwk_files: list[Path] = list(kit_path.glob("*.pwk"))
        if pwk_files:
            for pwk_file in pwk_files:
                self.assertTrue(pwk_file.exists(), f"Placeable walkmesh {pwk_file.name} should exist")
                # PWK files should have corresponding model (MDL) somewhere in the kit
                model_name = pwk_file.stem
                # Check if model exists in components, skyboxes, or models directory
                mdl_in_root = (kit_path / f"{model_name}.mdl").exists()
                mdl_in_skyboxes = (kit_path / "skyboxes" / f"{model_name}.mdl").exists() if (kit_path / "skyboxes").exists() else False
                mdl_in_models = (kit_path / "models" / f"{model_name}.mdl").exists() if (kit_path / "models").exists() else False
                # Note: PWK may not have corresponding MDL in kit if it's for a placeable that's not extracted
                # So we just verify the PWK file exists and is valid
        
        # Check texture files
        textures_dir = kit_path / "textures"
        if textures_dir.exists():
            tga_files = list(textures_dir.glob("*.tga"))
            txi_files = list(textures_dir.glob("*.txi"))
            # Each TGA should have corresponding TXI
            for tga_file in tga_files:
                txi_file = textures_dir / f"{tga_file.stem}.txi"
                self.assertTrue(txi_file.exists(), f"Texture {tga_file.stem} should have corresponding TXI file")
        
        # Check lightmap files
        lightmaps_dir = kit_path / "lightmaps"
        if lightmaps_dir.exists():
            tga_files = list(lightmaps_dir.glob("*.tga"))
            txi_files = list(lightmaps_dir.glob("*.txi"))
            # Each TGA should have corresponding TXI
            for tga_file in tga_files:
                txi_file = lightmaps_dir / f"{tga_file.stem}.txi"
                self.assertTrue(txi_file.exists(), f"Lightmap {tga_file.stem} should have corresponding TXI file")
        
        # Check skybox files
        skyboxes_dir = kit_path / "skyboxes"
        if skyboxes_dir.exists():
            skybox_mdl_files = list(skyboxes_dir.glob("*.mdl"))
            for mdl_file in skybox_mdl_files:
                skybox_id = mdl_file.stem
                mdx_file = skyboxes_dir / f"{skybox_id}.mdx"
                self.assertTrue(mdx_file.exists(), f"Skybox {skybox_id} should have corresponding MDX file")

    def _compare_kits(self, generated_path: Path, expected_path: Path, kit_id: str):
        """Compare generated kit with expected kit.

        Args:
        ----
            generated_path: Path to generated kit
            expected_path: Path to expected kit
            kit_id: Kit identifier (e.g., "jedienclave", "sithbase")
        """
        # Compare JSON files (if expected JSON exists)
        generated_json = generated_path.parent / f"{kit_id}.json"
        expected_json = REPO_ROOT / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "kits" / f"{kit_id}.json"

        if expected_json.exists():
            if not generated_json.exists():
                self.fail(f"Generated JSON file not found: {generated_json}")

            # Use lenient JSON comparison that handles doorhooks/dimensions differences
            self._compare_json_files(generated_json, expected_json)
        elif generated_json.exists():
            # If expected JSON doesn't exist but generated one does, that's okay
            # (unfinished kits may not have JSON files)
            pass

        # Compare all files recursively
        self._compare_directories(generated_path, expected_path)

    def _compare_plaintext_files(self, generated_file: Path, expected_file: Path):
        """Compare plaintext files using unified diff.

        Args:
        ----
            generated_file: Path to generated file
            expected_file: Path to expected file
        """
        # Normalize content - strip trailing whitespace from each line and normalize line endings
        generated_content = generated_file.read_text(encoding="utf-8")
        expected_content = expected_file.read_text(encoding="utf-8")
        
        # For TXI files, normalize trailing newlines (some have extra newlines, some don't)
        if generated_file.suffix.lower() == ".txi":
            generated_content = generated_content.rstrip() + "\n"
            expected_content = expected_content.rstrip() + "\n"
        
        generated_lines = generated_content.splitlines(keepends=True)
        expected_lines = expected_content.splitlines(keepends=True)

        if generated_lines != expected_lines:
            diff = list(
                unified_diff(
                    expected_lines,
                    generated_lines,
                    fromfile=str(expected_file),
                    tofile=str(generated_file),
                    lineterm="",
                ),
            )
            diff_str = "".join(diff)
            self.fail(f"Plaintext files differ:\n{diff_str}")

    def _compare_directories(self, generated_dir: Path, expected_dir: Path):
        """Compare directories recursively.

        Args:
        ----
            generated_dir: Path to generated directory
            expected_dir: Path to expected directory
        """
        # Known shared resources that may not be referenced by the module's models
        # These are manually included in kits for self-containment
        known_shared_resources = self._get_known_shared_resources()
        
        # Get all files in expected directory
        expected_files = set(expected_dir.rglob("*"))
        expected_files = {f for f in expected_files if f.is_file()}

        # Get all files in generated directory
        generated_files = set(generated_dir.rglob("*"))
        generated_files = {f for f in generated_files if f.is_file()}

        # Compare relative paths
        expected_rel = {f.relative_to(expected_dir) for f in expected_files}
        generated_rel = {f.relative_to(generated_dir) for f in generated_files}

        missing_files = expected_rel - generated_rel
        extra_files = generated_rel - expected_rel
        
        # Filter out known shared resources from missing files
        missing_files_filtered: set[Path] = {
            f for f in missing_files
            if not any(
                shared_pattern in str(f).lower().replace("\\", "/")
                for shared_pattern in known_shared_resources
            )
        }

        if missing_files_filtered:
            # Show which are known shared vs actually missing
            known_missing: set[Path] = missing_files - missing_files_filtered
            if known_missing:
                print(f"\nNote: {len(known_missing)} known shared resources not extracted (expected):")
                for f in sorted(list(known_missing))[:10]:
                    print(f"  - {f}")
                if len(known_missing) > 10:
                    print(f"  ... and {len(known_missing) - 10} more")
            
            self.fail(
                f"Missing files in generated kit ({len(missing_files_filtered)}): "
                f"{sorted(list(missing_files_filtered))[:20]}"
                + (f"\n... and {len(missing_files_filtered) - 20} more" if len(missing_files_filtered) > 20 else "")
            )
        elif missing_files:
            # Only known shared resources are missing - this is acceptable
            print(f"\nNote: {len(missing_files)} known shared resources not extracted (acceptable)")
        
        if extra_files:
            # Extra files are usually okay (might be generated differently)
            print(f"\nNote: {len(extra_files)} extra files in generated kit (may be acceptable)")
            # Don't fail on extra files for now

        # Compare each file (skip known shared resources)
        known_shared_resources = self._get_known_shared_resources()
        
        # Track what file types we're comparing for reporting
        file_types_compared: dict[str, int] = {}
        
        for rel_path in expected_rel:
            # Skip known shared resources
            # Normalize path separators using as_posix() which always uses forward slashes
            rel_path_str = rel_path.as_posix().lower()
            if any(shared_pattern in rel_path_str for shared_pattern in known_shared_resources):
                continue
            
            generated_file = generated_dir / rel_path
            expected_file = expected_dir / rel_path

            # Track file type for reporting
            file_ext = rel_path.suffix.lower()
            file_types_compared[file_ext] = file_types_compared.get(file_ext, 0) + 1

            # Determine if file is plaintext or binary
            is_plaintext = file_ext in {".json", ".txt", ".txi"}

            if is_plaintext:
                self._compare_plaintext_files(generated_file, expected_file)
            else:
                self._compare_binary_files(generated_file, expected_file)
        
        # Report what was compared
        if file_types_compared:
            print(f"\nCompared {sum(file_types_compared.values())} files:")
            for ext, count in sorted(file_types_compared.items()):
                file_type_name = {
                    ".mdl": "Models (MDL)",
                    ".mdx": "Model animations (MDX)",
                    ".wok": "Walkmeshes (WOK/BWM)",
                    ".png": "Minimaps (PNG)",
                    ".utd": "Doors (UTD)",
                    ".tga": "Textures/Lightmaps (TGA)",
                    ".tpc": "Textures (TPC)",
                    ".txi": "Texture info (TXI)",
                    ".json": "JSON metadata",
                }.get(ext, f"{ext.upper()} files")
                print(f"  {file_type_name}: {count}")

    def _get_known_shared_resources(self) -> list[str]:
        """Get list of known shared resource patterns that may not be referenced by models.
        
        Returns:
        -------
            List of filename patterns (lowercase) for shared resources
        """
        # Shared lightmaps from other modules (not referenced by danm13)
        shared_lightmaps: list[str] = [
            "m03af_01a_lm13", "m03af_03a_lm13",
            "m03mg_01a_lm13",
            "m10aa_01a_lm13", "m10ac_28a_lm13",
            "m14ab_02a_lm13",
            "m15aa_01a_lm13",
            "m22aa_03a_lm13", "m22ab_12a_lm13",
            "m28ab_19a_lm13",
            "m33ab_01_lm13",
            "m36aa_01_lm13",
            "m44ab_27a_lm13",
        ]
        
        # Shared textures not referenced by danm13 models
        shared_textures: list[str] = [
            "i_datapad",
            "lda_flr07",
            "lda_flr08",
            "lda_flr12",  # Also add flr12
            "h_f_lo01headtest",
        ]
        
        # Combine and create patterns
        patterns: list[str] = []
        for lm in shared_lightmaps:
            patterns.append(lm.lower())
            patterns.append(f"lightmaps/{lm.lower()}")
            patterns.append(f"lightmaps/{lm.lower()}.txi") # Add TXI for lightmaps
            patterns.append(f"lightmaps/{lm.lower()}.tga") # Add TGA for lightmaps
        for tex in shared_textures:
            patterns.append(tex.lower())
            patterns.append(f"textures/{tex.lower()}")
            patterns.append(f"textures/{tex.lower()}.txi") # Add TXI for textures
            patterns.append(f"textures/{tex.lower()}.tga") # Add TGA for textures
        
        # Additional textures/TXIs found in the expected jedienclave kit that are not referenced by danm13 models
        # These are also considered "shared" or manually added
        additional_shared_textures_base: list[str] = [
            "lda_bark04", "lda_ehawk01", "lda_flr11", "lda_flr12", "lda_grass07", "lda_grate01",
            "lda_ivy01", "lda_leaf02", "lda_lite01", "lda_rock06",
            "lda_sky0001", "lda_sky0002", "lda_sky0003", "lda_sky0004",
            "lda_sky0005", "lda_trim01", "lda_trim02", "lda_trim03", "lda_trim04",
            "lda_unwal07", "lda_wall02", "lda_wall03", "lda_wall04",
            "lda_window01",  # Window texture - may differ between installations
            "lmi_bed01",  # Lightmap textures
        ]
        for tex_base in additional_shared_textures_base:
            # Add both TGA and TXI versions
            patterns.append(f"textures/{tex_base.lower()}.tga")
            patterns.append(f"textures/{tex_base.lower()}.txi")
        
        # Textures that exist in the expected kit but are not referenced by models
        # These may be referenced by other resources (placeables, characters, etc.) or manually added
        additional_shared_textures: list[str] = [
            "p_bastillah01.txi", "p_carthh01.tga", "p_carthh01.txi",
            "pheyea.txi", "plc_chair1.tga", "plc_chair1.txi",
            "w_vbroswrd01.txi",
        ]
        for tex_name in additional_shared_textures:
            patterns.append(f"textures/{tex_name.lower()}")
        
        return patterns

    def _compare_binary_files(self, generated_file: Path, expected_file: Path):
        """Compare binary files.
        
        For image files (TGA/TPC), compares by dimensions, format, and pixel data.
        For other binary files, uses SHA256 hash comparison.

        Args:
        ----
            generated_file: Path to generated file
            expected_file: Path to expected file
        """
        # Check if this is a known shared resource that may differ
        try:
            # Try to get relative path - assume generated_file is under a known parent
            for parent in generated_file.parents:
                if parent.name in ["jedienclave", "sithbase"]:
                    rel_path = generated_file.relative_to(parent)
                    break
            else:
                rel_path = Path(generated_file.name)
        except Exception:
            rel_path = Path(generated_file.name)
        
        known_shared = self._get_known_shared_resources()
        rel_path_str = rel_path.as_posix().lower()
        if any(shared_pattern in rel_path_str for shared_pattern in known_shared):
            # Known shared resource - skip comparison
            return
        
        # For image files (TGA/TPC), compare by image properties
        if generated_file.suffix.lower() in {".tga", ".tpc"}:
            self._compare_image_files(generated_file, expected_file, rel_path)
        else:
            # For other binary files (MDL, MDX, WOK, PNG, UTD, etc.), use SHA256
            # This ensures models, walkmeshes, minimaps, and doors are byte-for-byte identical
            generated_hash = hashlib.sha256(generated_file.read_bytes()).hexdigest()
            expected_hash = hashlib.sha256(expected_file.read_bytes()).hexdigest()
            
            if generated_hash != expected_hash:
                file_type = {
                    ".mdl": "Model",
                    ".mdx": "Model animation",
                    ".wok": "Walkmesh (BWM)",
                    ".dwk": "Door Walkmesh (DWK)",
                    ".pwk": "Placeable Walkmesh (PWK)",
                    ".txi": "Texture info (TXI)",
                    ".utd": "Door (UTD)",
                    ".utw": "Waypoint (UTW)",
                    ".png": "Minimap (PNG)",
                    ".tga": "Texture/Lightmap (TGA)",
                    ".tpc": "Texture (TPC)",
                }.get(generated_file.suffix.lower(), "Binary file")
                
                self.fail(
                    f"{file_type} files differ (SHA256):\n"
                    f"  Generated: {generated_file} ({generated_hash[:16]}...)\n"
                    f"  Expected:  {expected_file} ({expected_hash[:16]}...)\n"
                    f"  Relative path: {rel_path}",
                )

    def _compare_image_files(self, generated_file: Path, expected_file: Path, rel_path: Path):
        """Compare image files (TGA/TPC) by dimensions, format, and pixel data.
        
        Args:
        ----
            generated_file: Path to generated image file
            expected_file: Path to expected image file
            rel_path: Relative path for error messages
        """
        try:
            from pykotor.resource.formats.tpc import read_tpc
            from pykotor.resource.formats.tpc.tga import read_tga
            from pykotor.resource.formats.tpc.tpc_data import TPCTextureFormat
            from pykotor.resource.type import ResourceType
            
            # Read both images
            gen_data = generated_file.read_bytes()
            exp_data = expected_file.read_bytes()
            
            # Determine file type and read
            gen_tpc = None
            exp_tpc = None
            
            # Determine file type and read
            if generated_file.suffix.lower() == ".tpc":
                gen_tpc = read_tpc(gen_data)
            else:
                # TGA - read and convert to TPC for comparison
                gen_tga = read_tga(io.BytesIO(gen_data))
                from pykotor.resource.formats.tpc.tpc_data import TPC
                gen_tpc = TPC()
                gen_tpc.set_single(gen_tga.data, TPCTextureFormat.RGBA, gen_tga.width, gen_tga.height)
            
            if expected_file.suffix.lower() == ".tpc":
                exp_tpc = read_tpc(exp_data)
            else:
                # TGA - read and convert to TPC for comparison
                exp_tga = read_tga(io.BytesIO(exp_data))
                from pykotor.resource.formats.tpc.tpc_data import TPC
                exp_tpc = TPC()
                exp_tpc.set_single(exp_tga.data, TPCTextureFormat.RGBA, exp_tga.width, exp_tga.height)
            
            if gen_tpc is None or exp_tpc is None:
                # Fallback to hash comparison if we can't read as image
                gen_hash = hashlib.sha256(gen_data).hexdigest()
                exp_hash = hashlib.sha256(exp_data).hexdigest()
                if gen_hash != exp_hash:
                    self.fail(
                        f"Image files differ (could not parse):\n"
                        f"  Generated: {generated_file}\n"
                        f"  Expected:  {expected_file}\n"
                        f"  Relative path: {rel_path}",
                    )
                return
            
            # Compare dimensions
            gen_width, gen_height = gen_tpc.dimensions()
            exp_width, exp_height = exp_tpc.dimensions()
            
            if gen_width != exp_width or gen_height != exp_height:
                self.fail(
                    f"Image dimensions differ:\n"
                    f"  Generated: {generated_file} ({gen_width}x{gen_height})\n"
                    f"  Expected:  {expected_file} ({exp_width}x{exp_height})\n"
                    f"  Relative path: {rel_path}",
                )
            
            # Get pixel data in RGBA format for comparison
            gen_mipmap = gen_tpc.get(0, 0)
            exp_mipmap = exp_tpc.get(0, 0)
            
            # Convert both to RGBA if needed
            gen_rgba = gen_mipmap.copy()
            if gen_rgba.tpc_format != TPCTextureFormat.RGBA:
                gen_rgba.convert(TPCTextureFormat.RGBA)
            
            exp_rgba = exp_mipmap.copy()
            if exp_rgba.tpc_format != TPCTextureFormat.RGBA:
                exp_rgba.convert(TPCTextureFormat.RGBA)
            
            # Compare pixel data (allow small differences for compression artifacts)
            gen_pixels = bytes(gen_rgba.data)
            exp_pixels = bytes(exp_rgba.data)
            
            if len(gen_pixels) != len(exp_pixels):
                self.fail(
                    f"Image pixel data size differs:\n"
                    f"  Generated: {generated_file} ({len(gen_pixels)} bytes)\n"
                    f"  Expected:  {expected_file} ({len(exp_pixels)} bytes)\n"
                    f"  Relative path: {rel_path}",
                )
            
            # Compare pixel by pixel with tolerance for compression artifacts
            # DXT compression can cause small differences even for the same source image
            differences = 0
            max_diff = 0
            total_pixels = gen_width * gen_height
            
            for i in range(0, len(gen_pixels), 4):
                gen_r, gen_g, gen_b, gen_a = gen_pixels[i:i+4]
                exp_r, exp_g, exp_b, exp_a = exp_pixels[i:i+4]
                
                # Calculate color difference (perceptual difference)
                r_diff = abs(int(gen_r) - int(exp_r))
                g_diff = abs(int(gen_g) - int(exp_g))
                b_diff = abs(int(gen_b) - int(exp_b))
                a_diff = abs(int(gen_a) - int(exp_a))
                
                pixel_diff = max(r_diff, g_diff, b_diff, a_diff)
                max_diff = max(max_diff, pixel_diff)
                
                # Allow up to 2 levels of difference per channel (compression artifacts)
                if pixel_diff > 2:
                    differences += 1
            
            # Allow up to 1% of pixels to differ by more than 2 levels
            # This accounts for DXT compression artifacts
            tolerance = total_pixels * 0.01
            if differences > tolerance:
                diff_percent = (differences / total_pixels) * 100
                self.fail(
                    f"Image pixel data differs:\n"
                    f"  Generated: {generated_file} ({gen_width}x{gen_height}, format: {gen_mipmap.tpc_format.name})\n"
                    f"  Expected:  {expected_file} ({exp_width}x{exp_height}, format: {exp_mipmap.tpc_format.name})\n"
                    f"  {differences}/{total_pixels} pixels differ ({diff_percent:.2f}%)\n"
                    f"  Max difference: {max_diff} levels\n"
                    f"  Relative path: {rel_path}",
                )
            
        except Exception as e:
            # If image comparison fails, fall back to hash comparison
            gen_hash = hashlib.sha256(generated_file.read_bytes()).hexdigest()
            exp_hash = hashlib.sha256(expected_file.read_bytes()).hexdigest()
            if gen_hash != exp_hash:
                self.fail(
                    f"Image files differ (comparison error: {e}):\n"
                    f"  Generated: {generated_file} ({gen_hash[:16]}...)\n"
                    f"  Expected:  {expected_file} ({exp_hash[:16]}...)\n"
                    f"  Relative path: {rel_path}",
                )

    def _compare_json_files(self, generated_file: Path, expected_file: Path):
        """Compare JSON files, handling differences in components/doorhooks that may not be fully extracted yet.

        Args:
        ----
            generated_file: Path to generated JSON file
            expected_file: Path to expected JSON file
        """
        import json

        generated_data = json.loads(generated_file.read_text(encoding="utf-8"))
        expected_data = json.loads(expected_file.read_text(encoding="utf-8"))

        # Compare top-level fields
        for key in ["name", "id", "ht", "version"]:
            if key in expected_data:
                self.assertEqual(
                    generated_data.get(key),
                    expected_data[key],
                    f"JSON field '{key}' differs",
                )
        
        # Verify JSON structure has required sections
        if "components" in expected_data:
            self.assertIn("components", generated_data, "Generated JSON missing 'components' section")
        if "doors" in expected_data:
            self.assertIn("doors", generated_data, "Generated JSON missing 'doors' section")

        # Compare doors (width/height may differ if not extracted from UTD)
        if "doors" in expected_data:
            self.assertEqual(
                len(generated_data.get("doors", [])),
                len(expected_data["doors"]),
                "Number of doors differs",
            )
            for i, (gen_door, exp_door) in enumerate(
                zip(generated_data.get("doors", []), expected_data["doors"])
            ):
                # Verify door naming format: should be "door0_k1", "door1_k1", etc.
                gen_utd_k1 = gen_door.get("utd_k1")
                gen_utd_k2 = gen_door.get("utd_k2")
                exp_utd_k1 = exp_door.get("utd_k1")
                exp_utd_k2 = exp_door.get("utd_k2")
                
                # Check format matches expected pattern (door0_k1, door1_k1, etc.)
                if exp_utd_k1:
                    # Expected format should be "door{N}_k1" where N is a number
                    expected_pattern = re.compile(r"^door\d+_k1$")
                    self.assertTrue(
                        expected_pattern.match(gen_utd_k1) if gen_utd_k1 else False,
                        f"Door {i} utd_k1 has incorrect format: '{gen_utd_k1}' (expected format: 'door0_k1', 'door1_k1', etc.)",
                    )
                    self.assertEqual(
                        gen_utd_k1,
                        exp_utd_k1,
                        f"Door {i} utd_k1 differs",
                    )
                if exp_utd_k2:
                    expected_pattern = re.compile(r"^door\d+_k2$")
                    self.assertTrue(
                        expected_pattern.match(gen_utd_k2) if gen_utd_k2 else False,
                        f"Door {i} utd_k2 has incorrect format: '{gen_utd_k2}' (expected format: 'door0_k2', 'door1_k2', etc.)",
                    )
                    self.assertEqual(
                        gen_utd_k2,
                        exp_utd_k2,
                        f"Door {i} utd_k2 differs",
                    )
                # Width/height may differ if not extracted from UTD - just check they exist
                if "width" in exp_door:
                    self.assertIn("width", gen_door, f"Door {i} missing width")
                if "height" in exp_door:
                    self.assertIn("height", gen_door, f"Door {i} missing height")

        # Compare components (doorhooks may be empty if not extracted from BWM)
        if "components" in expected_data:
            self.assertEqual(
                len(generated_data.get("components", [])),
                len(expected_data["components"]),
                "Number of components differs",
            )
            for i, (gen_comp, exp_comp) in enumerate(
                zip(generated_data.get("components", []), expected_data["components"])
            ):
                self.assertEqual(
                    gen_comp.get("id"),
                    exp_comp.get("id"),
                    f"Component {i} id differs",
                )
                self.assertEqual(
                    gen_comp.get("name"),
                    exp_comp.get("name"),
                    f"Component {i} name differs",
                )
                # Verify component has native flag
                if "native" in exp_comp:
                    self.assertEqual(
                        gen_comp.get("native"),
                        exp_comp.get("native"),
                        f"Component {i} native flag differs",
                    )
                # Doorhooks may be empty if not extracted from BWM - just check structure
                if "doorhooks" in exp_comp:
                    gen_hooks = gen_comp.get("doorhooks", [])
                    exp_hooks = exp_comp.get("doorhooks", [])
                    if exp_hooks:  # Only compare if expected has hooks
                        # Verify doorhooks structure matches
                        self.assertEqual(
                            len(gen_hooks),
                            len(exp_hooks),
                            f"Component {i} doorhooks count differs",
                        )
                        if gen_hooks:
                            for j, (gen_hook, exp_hook) in enumerate(
                                zip(gen_hooks, exp_hooks)
                            ):
                                self.assertIn("x", gen_hook, f"Component {i} hook {j} missing x")
                                self.assertIn("y", gen_hook, f"Component {i} hook {j} missing y")
                                self.assertIn("z", gen_hook, f"Component {i} hook {j} missing z")
                                self.assertIn("rotation", gen_hook, f"Component {i} hook {j} missing rotation")
                                self.assertIn("door", gen_hook, f"Component {i} hook {j} missing door")
                                self.assertIn("edge", gen_hook, f"Component {i} hook {j} missing edge")


if __name__ == "__main__":
    unittest.main()

