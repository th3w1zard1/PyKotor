from __future__ import annotations

import os
import pathlib
import sys
import unittest
from unittest import TestCase

from pykotor.extract.file import ResourceIdentifier, ResourceResult

try:
    from qtpy.QtTest import QTest
    from qtpy.QtWidgets import QApplication
except (ImportError, ModuleNotFoundError):
    QTest, QApplication = None, None  # type: ignore[misc, assignment]

absolute_file_path = pathlib.Path(__file__).resolve()
TESTS_FILES_PATH = next(f for f in absolute_file_path.parents if f.name == "tests") / "test_toolset/test_files"

if (
    __name__ == "__main__"
    and getattr(sys, "frozen", False) is False
):
    pykotor_path = pathlib.Path(__file__).parents[6] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        working_dir = str(pykotor_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.append(working_dir)
    gl_path = pathlib.Path(__file__).parents[6] / "Libraries" / "PyKotorGL" / "src" / "pykotor"
    if gl_path.exists():
        working_dir = str(gl_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.append(working_dir)
    utility_path = pathlib.Path(__file__).parents[6] / "Libraries" / "Utility" / "src" / "utility"
    if utility_path.exists():
        working_dir = str(utility_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.append(working_dir)
    toolset_path = pathlib.Path(__file__).parents[3] / "toolset"
    if toolset_path.exists():
        working_dir = str(toolset_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.append(working_dir)


K1_PATH = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
K2_PATH = os.environ.get("K2_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II")

from pykotor.common.stream import BinaryReader
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.type import ResourceType


@unittest.skipIf(
    not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
    "K2_PATH environment variable is not set or not found on disk.",
)
@unittest.skipIf(
    QTest is None or not QApplication,
    "qtpy is required, please run pip install -r requirements.txt before running this test.",
)
class GITEditorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        # Make sure to configure this environment path before testing!
        from toolset.gui.editors.git import GITEditor

        cls.GITEditor = GITEditor
        from toolset.data.installation import HTInstallation

        # cls.K1_INSTALLATION = HTInstallation(K1_PATH, "", tsl=False)
        cls.INSTALLATION = HTInstallation(K2_PATH, "", tsl=True)

    def setUp(self):
        self.app = QApplication([])  # pyright: ignore[reportOptionalCall]
        self.editor = self.GITEditor(None, self.INSTALLATION)
        self.log_messages: list[str] = [os.linesep]

    def tearDown(self):
        self.app.deleteLater()

    def log_func(self, *args):
        self.log_messages.append("\t".join(args))

    def test_save_and_load(self):
        filepath = TESTS_FILES_PATH / "zio001.git"

        data = filepath.read_bytes()
        old = read_gff(data)
        self.editor.load(filepath, "zio001", ResourceType.GIT, data)

        data, _ = self.editor.build()
        new = read_gff(data)

        diff = old.compare(new, self.log_func)
        assert diff, os.linesep.join(self.log_messages)

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k1_installation(self):
        self.installation = Installation(K1_PATH)  # type: ignore[arg-type]
        for git_resource in (resource for resource in self.installation if resource.restype() is ResourceType.GIT):
            old = read_gff(git_resource.data())
            self.editor.load(git_resource.filepath(), git_resource.resname(), git_resource.restype(), git_resource.data())

            data, _ = self.editor.build()
            new = read_gff(data)

            diff = old.compare(new, self.log_func, ignore_default_changes=True)
            assert diff, os.linesep.join(self.log_messages)

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_gff_reconstruct_from_k2_installation(self):
        self.installation = Installation(K2_PATH)  # type: ignore[arg-type]
        for git_resource in (resource for resource in self.installation if resource.restype() is ResourceType.GIT):
            old = read_gff(git_resource.data())
            self.editor.load(git_resource.filepath(), git_resource.resname(), git_resource.restype(), git_resource.data())

            data, _ = self.editor.build()
            new = read_gff(data)

            diff = old.compare(new, self.log_func, ignore_default_changes=True)
            assert diff, os.linesep.join(self.log_messages)

    def test_placeholder(self): ...


if __name__ == "__main__":
    unittest.main()


# ============================================================================
# Additional UI tests (merged from test_ui_gff_editors.py)
# ============================================================================

import pytest
from toolset.gui.editors.git import GITEditor
from toolset.data.installation import HTInstallation
from pykotor.resource.type import ResourceType

def test_git_editor_headless_ui_load_build(qtbot, installation: HTInstallation, test_files_dir: pathlib.Path):
    """Test GIT Editor in headless UI - loads real file and builds data."""
    editor = GITEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Try to find a GIT file
    git_file = test_files_dir / "zio001.git"
    if not git_file.exists():
        # Try to get one from installation
        git_resources: dict[ResourceIdentifier, ResourceResult | None] = installation.resources(([ResourceIdentifier("zio001", ResourceType.GIT)]))
        if not git_resources:
            pytest.skip("No GIT files available for testing")
        git_resource: ResourceResult | None = git_resources.get(ResourceIdentifier("zio001", ResourceType.GIT))
        if git_resource is None:
            pytest.fail("No GIT files found with name 'zio001.git'!")
        git_data = git_resource.data
        if not git_data:
            pytest.fail(f"Could not load GIT data for 'zio001.git'!")
        editor.load(
            git_resource.filepath if hasattr(git_resource, 'filepath') else pathlib.Path("module.git"),
            git_resource.resname,
            ResourceType.GIT,
            git_data
        )
    else:
        original_data = git_file.read_bytes()
        editor.load(git_file, "zio001", ResourceType.GIT, original_data)
    
    # Verify editor loaded the data
    assert editor is not None
    
    # Build and verify it works
    data, _ = editor.build()
    assert len(data) > 0
    
    # Verify we can read it back
    from pykotor.resource.formats.gff.gff_auto import read_gff
    loaded_git = read_gff(data)
    assert loaded_git is not None


def test_giteditor_editor_help_dialog_opens_correct_file(qtbot, installation: HTInstallation):
    """Test that GITEditor help dialog opens and displays the correct help file (not 'Help File Not Found')."""
    from toolset.gui.dialogs.editor_help import EditorHelpDialog
    
    editor = GITEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Trigger help dialog with the correct file for GITEditor
    editor._show_help_dialog("GFF-GIT.md")
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
        f"Help file 'GFF-GIT.md' should be found, but error was shown. HTML: {html[:500]}"
    
    # Assert that some content is present (file was loaded successfully)
    assert len(html) > 100, "Help dialog should contain content"
