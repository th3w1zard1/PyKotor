from __future__ import annotations

import os
import pathlib
import sys
import unittest
from unittest import TestCase

try:
    from qtpy.QtTest import QTest
    from qtpy.QtWidgets import QApplication
except (ImportError, ModuleNotFoundError):
    QTest, QApplication = object, object  # type: ignore[misc, assignment]

absolute_file_path = pathlib.Path(__file__).resolve()
TESTS_FILES_PATH = next(f for f in absolute_file_path.parents if f.name == "tests") / "test_files"

if (
    __name__ == "__main__"
    and getattr(sys, "frozen", False) is False
):
    def add_sys_path(p):
        working_dir = str(p)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.append(working_dir)

    pykotor_path = absolute_file_path.parents[6] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        add_sys_path(pykotor_path.parent)
    gl_path = absolute_file_path.parents[6] / "Libraries" / "PyKotorGL" / "src" / "pykotor"
    if gl_path.exists():
        add_sys_path(gl_path.parent)
    utility_path = absolute_file_path.parents[6] / "Libraries" / "Utility" / "src" / "utility"
    if utility_path.exists():
        add_sys_path(utility_path.parent)
    toolset_path = absolute_file_path.parents[6] / "Tools" / "HolocronToolset" / "src" / "toolset"
    if toolset_path.exists():
        add_sys_path(toolset_path.parent)


K1_PATH = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
K2_PATH = os.environ.get("K2_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II")

from pykotor.extract.installation import Installation
from pykotor.resource.formats.bwm.bwm_auto import read_bwm
from pykotor.resource.type import ResourceType


@unittest.skipIf(
    not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
    "K2_PATH environment variable is not set or not found on disk.",
)
@unittest.skipIf(
    QTest is None or not QApplication,
    "qtpy is required, please run pip install -r requirements.txt before running this test.",
)
class BWMEditorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        # Make sure to configure this environment path before testing!
        from toolset.gui.editors.bwm import BWMEditor

        cls.BWMEditor = BWMEditor
        from toolset.data.installation import HTInstallation

        # cls.INSTALLATION = HTInstallation(K1_PATH, "", tsl=False)
        assert K2_PATH is not None, "K2_PATH environment variable is not set"
        cls.K2_INSTALLATION = HTInstallation(K2_PATH, "", tsl=True)

    def setUp(self):
        self.app: QApplication = QApplication(sys.argv)  # type: ignore[assignment]
        self.editor = self.BWMEditor(None, self.K2_INSTALLATION)
        self.log_messages: list[str] = [os.linesep]

    def tearDown(self):
        self.app.deleteLater()

    def log_func(self, *args):
        self.log_messages.append("\t".join(args))

    def test_save_and_load(self):
        filepath = TESTS_FILES_PATH / "zio006j.wok"

        data = filepath.read_bytes()
        old = read_bwm(data)
        supported = [ResourceType.WOK, ResourceType.DWK, ResourceType.PWK]
        self.editor.load(filepath, "zio006j", ResourceType.WOK, data)

        data, _ = self.editor.build()
        new = read_bwm(data)

        # Compare by content, not by index (faces may be reordered: walkable first, then unwalkable)
        # Compare basic properties
        assert old.walkmesh_type == new.walkmesh_type
        assert old.position == new.position
        assert old.relative_hook1 == new.relative_hook1
        assert old.relative_hook2 == new.relative_hook2
        assert old.absolute_hook1 == new.absolute_hook1
        assert old.absolute_hook2 == new.absolute_hook2
        
        # Compare faces by content (set comparison since order may differ)
        assert len(old.faces) == len(new.faces), "Face count mismatch"
        old_faces_set = set(old.faces)
        new_faces_set = set(new.faces)
        assert old_faces_set == new_faces_set, "Face content mismatch - faces may have been reordered or modified"

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_bwm_reconstruct_from_k1_installation(self):
        self.installation = Installation(K1_PATH)  # type: ignore[arg-type]
        for bwm_resource in (resource for resource in self.installation if resource.restype() in {ResourceType.WOK, ResourceType.DWK, ResourceType.PWK}):
            old = read_bwm(bwm_resource.data())
            self.editor.load(bwm_resource.filepath(), bwm_resource.resname(), bwm_resource.restype(), bwm_resource.data())

            data, _ = self.editor.build()
            new = read_bwm(data)

            self.assertDeepEqual(old, new)

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_bwm_reconstruct_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for bwm_resource in (resource for resource in self.installation if resource.restype() in {ResourceType.WOK, ResourceType.DWK, ResourceType.PWK}):
            old = read_bwm(bwm_resource.data())
            self.editor.load(bwm_resource.filepath(), bwm_resource.resname(), bwm_resource.restype(), bwm_resource.data())

            data, _ = self.editor.build()
            new = read_bwm(data)

            self.assertDeepEqual(old, new)

    def assertDeepEqual(self, obj1, obj2, context=""):
        # Special handling for BWM faces - compare as sets since order may differ
        # Faces are reordered by writer: walkable first, then unwalkable
        if context.endswith(".faces") and isinstance(obj1, list) and isinstance(obj2, list):
            assert len(obj1) == len(obj2), f"{context}: Face count mismatch"
            # Compare as sets (faces may be reordered: walkable first, then unwalkable)
            obj1_set = set(obj1)
            obj2_set = set(obj2)
            assert obj1_set == obj2_set, f"{context}: Face content mismatch - faces may have been reordered or modified"
            return
        
        if isinstance(obj1, dict) and isinstance(obj2, dict):
            assert set(obj1.keys()) == set(obj2.keys()), context
            for key in obj1:
                new_context = f"{context}.{key}" if context else str(key)
                self.assertDeepEqual(obj1[key], obj2[key], new_context)

        elif isinstance(obj1, (list, tuple)) and isinstance(obj2, (list, tuple)):
            assert len(obj1) == len(obj2), context
            # Special handling for lists of BWMFace objects - compare as sets since order may differ
            # Faces are reordered by writer: walkable first, then unwalkable
            if (obj1 and obj2 and 
                hasattr(obj1[0], '__class__') and hasattr(obj2[0], '__class__') and
                obj1[0].__class__.__name__ == 'BWMFace' and obj2[0].__class__.__name__ == 'BWMFace'):
                obj1_set = set(obj1)
                obj2_set = set(obj2)
                assert obj1_set == obj2_set, f"{context}: Face content mismatch - faces may have been reordered or modified"
                return
            for index, (item1, item2) in enumerate(zip(obj1, obj2)):
                new_context = f"{context}[{index}]" if context else f"[{index}]"
                self.assertDeepEqual(item1, item2, new_context)

        elif hasattr(obj1, "__dict__") and hasattr(obj2, "__dict__"):
            self.assertDeepEqual(obj1.__dict__, obj2.__dict__, context)

        elif isinstance(obj1, float) and isinstance(obj2, float):
            # Use approximate equality for floating-point numbers (1e-3 tolerance)
            # Some game files have precision differences after roundtrip
            assert abs(obj1 - obj2) < 1e-3, f"{context}: {obj1} != {obj2} (diff: {abs(obj1 - obj2)})"

        else:
            assert obj1 == obj2, context

    def test_placeholder(self): ...


class BWMTransitionIntegrityTest(TestCase):
    """Tests for BWM walkmesh transition integrity.
    
    These tests ensure that transitions (which are critical for pathfinding between
    rooms in KotOR) remain on walkable faces after serialization/deserialization.
    
    Bug reference: Indoor map builder was creating modules where characters couldn't
    walk because transitions were being assigned to unwalkable faces due to a dict
    key collision bug in io_bwm.py (using value-based equality instead of identity).
    """

    def test_transitions_remain_on_walkable_faces_after_roundtrip(self):
        """Test that transitions on walkable faces remain on walkable faces after roundtrip.
        
        This is a critical regression test for the walkmesh serialization bug where
        transitions could end up on unwalkable faces due to dict key collisions when
        BWMFace objects with the same vertex coordinates and transitions were present.
        """
        from pykotor.resource.formats.bwm import BWM, bytes_bwm, read_bwm
        from pykotor.resource.formats.bwm.bwm_data import BWMFace
        from utility.common.geometry import SurfaceMaterial, Vector3
        
        # Create a BWM with walkable and unwalkable faces
        bwm = BWM()
        
        # Create vertices
        v1 = Vector3(0, 0, 0)
        v2 = Vector3(1, 0, 0)
        v3 = Vector3(0, 1, 0)
        v4 = Vector3(1, 1, 0)
        v5 = Vector3(2, 0, 0)
        v6 = Vector3(2, 1, 0)
        
        # Create walkable faces (METAL = 10, walkable)
        walkable_face1 = BWMFace(v1, v2, v3)
        walkable_face1.material = SurfaceMaterial.METAL
        walkable_face1.trans1 = 1  # This is the transition we want to preserve
        walkable_face1.trans2 = 1
        
        walkable_face2 = BWMFace(v2, v4, v3)
        walkable_face2.material = SurfaceMaterial.METAL
        
        # Create unwalkable faces (NON_WALK = 7, not walkable)
        unwalkable_face1 = BWMFace(v2, v5, v4)
        unwalkable_face1.material = SurfaceMaterial.NON_WALK
        
        unwalkable_face2 = BWMFace(v5, v6, v4)
        unwalkable_face2.material = SurfaceMaterial.NON_WALK
        
        bwm.faces = [walkable_face1, walkable_face2, unwalkable_face1, unwalkable_face2]
        
        # Verify initial state: transition should be on walkable face
        assert walkable_face1.trans1 == 1, "Initial: walkable face should have transition"
        assert walkable_face1.material.walkable(), "Initial: face with transition should be walkable"
        
        # Serialize and deserialize
        data = bytes_bwm(bwm)
        loaded_bwm = read_bwm(data)
        
        # Find faces with transitions in the loaded BWM
        faces_with_transitions = [
            (i, face) for i, face in enumerate(loaded_bwm.faces)
            if face.trans1 is not None or face.trans2 is not None or face.trans3 is not None
        ]
        
        # Verify: all faces with transitions should be walkable
        for idx, face in faces_with_transitions:
            assert face.material.walkable(), (
                f"CRITICAL BUG: Transition on face {idx} which has material {face.material} "
                f"(walkable={face.material.walkable()}). Transitions should only be on walkable faces. "
                "This bug causes characters to be stuck in indoor map builder modules."
            )
        
        # Verify we still have at least one transition
        assert len(faces_with_transitions) > 0, "Should have at least one face with transitions"
    
    def test_roundtrip_with_working_module_data(self):
        """Test roundtrip with real module data from v2.0.4 (working version).
        
        This uses the actual test files from the indoormap_bug_inspect_workspace
        to ensure the fix works with real game data.
        """
        from pykotor.resource.formats.erf import read_erf
        from pykotor.resource.formats.bwm import read_bwm, bytes_bwm
        from pykotor.resource.type import ResourceType
        
        # Load the working v2.0.4 module
        # TESTS_FILES_PATH is tests/test_files, we need Libraries/PyKotor/tests/test_files
        v2_mod_path = Path(__file__).parents[6] / "Libraries" / "PyKotor" / "tests" / "test_files" / "indoormap_bug_inspect_workspace" / "v2.0.4-toolset" / "step01" / "step01.mod"
        if not v2_mod_path.exists():
            self.skipTest(f"Test file not found: {v2_mod_path}")
        
        v2_erf = read_erf(v2_mod_path)
        
        for res in v2_erf:
            if res.restype == ResourceType.WOK and 'room0' in str(res.resref):
                original_bwm = read_bwm(res.data)
                
                # Find original transitions
                original_transitions = [
                    (i, face.trans1, face.trans2, face.trans3, face.material.walkable())
                    for i, face in enumerate(original_bwm.faces)
                    if face.trans1 is not None or face.trans2 is not None or face.trans3 is not None
                ]
                
                # Verify original has transitions on walkable faces
                for idx, t1, t2, t3, is_walkable in original_transitions:
                    assert is_walkable, f"Original face {idx} with transition should be walkable"
                
                # Roundtrip
                new_data = bytes_bwm(original_bwm)
                new_bwm = read_bwm(new_data)
                
                # Find new transitions
                new_transitions = [
                    (i, face.trans1, face.trans2, face.trans3, face.material.walkable())
                    for i, face in enumerate(new_bwm.faces)
                    if face.trans1 is not None or face.trans2 is not None or face.trans3 is not None
                ]
                
                # Verify roundtrip preserved transitions on walkable faces
                for idx, t1, t2, t3, is_walkable in new_transitions:
                    assert is_walkable, (
                        f"After roundtrip: face {idx} with transition (trans1={t1}, trans2={t2}, trans3={t3}) "
                        f"should be walkable, but is not. This causes the indoor map builder bug."
                    )
                
                # Verify we didn't lose transitions
                assert len(new_transitions) == len(original_transitions), (
                    f"Transition count changed: {len(original_transitions)} -> {len(new_transitions)}"
                )
                break
        else:
            self.skipTest("No room0 WOK found in test module")
    
    def test_identity_based_face_lookup_not_value_based(self):
        """Test that face lookup uses identity, not value equality.
        
        This tests the specific bug where two faces with the same vertex coordinates
        and transitions (but different materials) would collide in a dict lookup.
        """
        from pykotor.resource.formats.bwm import BWM, bytes_bwm, read_bwm
        from pykotor.resource.formats.bwm.bwm_data import BWMFace
        from utility.common.geometry import SurfaceMaterial, Vector3
        
        # Create a BWM with two faces that have SAME vertices and transitions
        # but DIFFERENT materials (one walkable, one not)
        bwm = BWM()
        
        # Shared vertices
        v1 = Vector3(0, 0, 0)
        v2 = Vector3(1, 0, 0)
        v3 = Vector3(0, 1, 0)
        
        # Walkable face with transition
        walkable = BWMFace(v1, v2, v3)
        walkable.material = SurfaceMaterial.METAL  # Walkable (METAL = 10)
        walkable.trans1 = 1
        
        # Different vertices for the unwalkable face (so it's a valid walkmesh)
        v4 = Vector3(1, 1, 0)
        v5 = Vector3(2, 0, 0)
        v6 = Vector3(2, 1, 0)
        
        unwalkable = BWMFace(v4, v5, v6)
        unwalkable.material = SurfaceMaterial.NON_WALK  # NOT walkable (NON_WALK = 7)
        
        # Add a third walkable face so there's something to compute edges from
        walkable2 = BWMFace(v2, v4, v3)
        walkable2.material = SurfaceMaterial.METAL
        
        bwm.faces = [walkable, walkable2, unwalkable]
        
        # Serialize and deserialize
        data = bytes_bwm(bwm)
        loaded_bwm = read_bwm(data)
        
        # The transition should be on a walkable face, not the unwalkable one
        for i, face in enumerate(loaded_bwm.faces):
            if face.trans1 is not None:
                assert face.material.walkable(), (
                    f"Face {i} has trans1={face.trans1} but material={face.material} "
                    f"(walkable={face.material.walkable()}). "
                    "This indicates the identity-based lookup bug is present."
                )


if __name__ == "__main__":
    unittest.main()


# ============================================================================
# Additional UI tests (merged from test_ui_other_editors.py)
# ============================================================================

import pytest
from toolset.gui.editors.bwm import BWMEditor
from toolset.data.installation import HTInstallation

def test_bwm_editor_headless_ui_load_build(qtbot, installation: HTInstallation, test_files_dir: pathlib.Path):
    """Test BWM Editor in headless UI - loads real file and builds data."""
    editor = BWMEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Try to find a BWM/WOK file
    bwm_file = test_files_dir / "zio006j.wok"
    if not bwm_file.exists():
        # Try to get one from installation
        bwm_resources = list(installation.resources(ResourceType.WOK))[:1]
        if not bwm_resources:
            bwm_resources = list(installation.resources(ResourceType.DWK))[:1]
        if not bwm_resources:
            pytest.skip("No BWM files available for testing")
        bwm_resource = bwm_resources[0]
        bwm_data = installation.resource(bwm_resource.identifier)
        if not bwm_data:
            pytest.skip(f"Could not load BWM data for {bwm_resource.identifier}")
        editor.load(
            bwm_resource.filepath if hasattr(bwm_resource, 'filepath') else pathlib.Path("module.wok"),
            bwm_resource.resname,
            bwm_resource.restype,
            bwm_data
        )
    else:
        original_data = bwm_file.read_bytes()
        editor.load(bwm_file, "zio006j", ResourceType.WOK, original_data)
    
    # Verify editor loaded the data
    assert editor is not None
    
    # Build and verify it works
    data, _ = editor.build()
    assert len(data) > 0
    
    # Verify we can read it back
    from pykotor.resource.formats.bwm.bwm_auto import read_bwm
    loaded_bwm = read_bwm(data)
    assert loaded_bwm is not None


def test_bwmeditor_editor_help_dialog_opens_correct_file(qtbot, installation: HTInstallation):
    """Test that BWMEditor help dialog opens and displays the correct help file (not 'Help File Not Found')."""
    from toolset.gui.dialogs.editor_help import EditorHelpDialog
    
    editor = BWMEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Trigger help dialog with the correct file for BWMEditor
    editor._show_help_dialog("BWM-File-Format.md")
    qtbot.wait(200)  # Wait for dialog to be created
    
    # Find the help dialog
    dialogs = [child for child in editor.findChildren(EditorHelpDialog)]
    assert len(dialogs) > 0, "Help dialog should be opened"
    
    dialog = dialogs[0]
    qtbot.waitExposed(dialog)
    
    # Get the HTML content
    html = dialog.text_browser.toHtml()
    
    # Assert that "Help File Not Found" error is NOT shown
    assert "Help File Not Found" not in html, \
        f"Help file 'BWM-File-Format.md' should be found, but error was shown. HTML: {html[:500]}"
    
    # Assert that some content is present (file was loaded successfully)
    assert len(html) > 100, "Help dialog should contain content"

    """Test BWM Editor."""
    editor = BWMEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    
    assert editor.isVisible()
    # Walkmesh editor might have GL view or property lists