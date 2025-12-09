from __future__ import annotations

import os
import pathlib
import sys
from typing import TYPE_CHECKING
import unittest
from unittest import TestCase

import pytest
from qtpy.QtGui import QStandardItem
from toolset.gui.editors.jrl import JRLEditor
from toolset.data.installation import HTInstallation
from pykotor.resource.generics.jrl import JRLQuest, JRLEntry, JRLQuestPriority
from pykotor.common.language import LocalizedString, Language, Gender
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot

try:
    from qtpy.QtTest import QTest
    from qtpy.QtWidgets import QApplication
except (ImportError, ModuleNotFoundError):
    if not TYPE_CHECKING:
        QTest, QApplication = None, None  # type: ignore[misc, assignment]

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

from pykotor.common.stream import BinaryReader  # pyright: ignore[reportMissingImports]
from pykotor.extract.installation import Installation  # pyright: ignore[reportMissingImports]
from pykotor.resource.formats.gff.gff_auto import read_gff  # pyright: ignore[reportMissingImports]
from pykotor.resource.type import ResourceType  # pyright: ignore[reportMissingImports]


@unittest.skipIf(
    not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
    "K2_PATH environment variable is not set or not found on disk.",
)
@unittest.skipIf(
    QTest is None or not QApplication,
    "qtpy is required, please run pip install -r requirements.txt before running this test.",
)
class JRLEditorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        # Make sure to configure this environment path before testing!
        from toolset.gui.editors.jrl import JRLEditor

        cls.JRLEditor = JRLEditor
        from toolset.data.installation import HTInstallation

        # cls.K1_INSTALLATION = HTInstallation(K1_PATH, "", tsl=False)
        cls.K2_INSTALLATION = HTInstallation(K2_PATH, "", tsl=True)

    def setUp(self):
        self.app: QApplication = QApplication([])
        self.editor = self.JRLEditor(None, self.K2_INSTALLATION)
        self.log_messages: list[str] = [os.linesep]

    def tearDown(self):
        self.app.deleteLater()

    def log_func(self, *args):
        self.log_messages.append("\t".join(args))

    def test_save_and_load(self):
        filepath = TESTS_FILES_PATH / "global.jrl"

        data = filepath.read_bytes()
        old = read_gff(data)
        self.editor.load(filepath, "global", ResourceType.JRL, data)

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
        for jrl_resource in (resource for resource in self.installation if resource.restype() is ResourceType.JRL):
            old = read_gff(jrl_resource.data())
            self.editor.load(jrl_resource.filepath(), jrl_resource.resname(), jrl_resource.restype(), jrl_resource.data())

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
        for jrl_resource in (resource for resource in self.installation if resource.restype() is ResourceType.JRL):
            old = read_gff(jrl_resource.data())
            self.editor.load(jrl_resource.filepath(), jrl_resource.resname(), jrl_resource.restype(), jrl_resource.data())

            data, _ = self.editor.build()
            new = read_gff(data)

            diff = old.compare(new, self.log_func, ignore_default_changes=True)
            assert diff, os.linesep.join(self.log_messages)

    def test_editor_init(self):
        self.JRLEditor(None, self.K2_INSTALLATION)


def test_jrl_editor_init(qtbot: QtBot, installation: HTInstallation):
    """Test JRL Editor initialization."""
    editor = JRLEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    
    assert editor.isVisible()
    assert "Journal Editor" in editor.windowTitle()

def test_jrl_add_quest_and_entry(qtbot: QtBot, installation: HTInstallation):
    """Test adding quests and entries."""
    editor = JRLEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()
    
    # Add Quest
    quest = JRLQuest()
    quest.name.set_string(0, "Test Quest")
    editor.add_quest(quest)
    
    assert editor._model.rowCount() == 1
    quest_item = editor._model.item(0)
    assert quest_item is not None
    assert "Test Quest" in quest_item.text()
    
    # Select Quest
    editor.ui.journalTree.setCurrentIndex(quest_item.index())
    
    # Check Quest fields
    assert editor.ui.questPages.currentIndex() == 0
    
    # Modify Quest
    editor.ui.categoryTag.setText("quest_tag")
    editor.on_value_updated()
    assert quest.tag == "quest_tag"
    
    # Add Entry
    entry = JRLEntry()
    entry.text.set_string(0, "Test Entry")
    entry.entry_id = 10
    editor.add_entry(quest_item, entry)
    
    assert quest_item.rowCount() == 1
    entry_item = quest_item.child(0)
    assert entry_item is not None
    assert "10" in entry_item.text()
    
    # Select Entry
    editor.ui.journalTree.setCurrentIndex(entry_item.index())
    
    # Check Entry fields
    assert editor.ui.questPages.currentIndex() == 1
    
    # Modify Entry
    editor.ui.entryXpSpin.setValue(50)
    editor.on_value_updated()
    assert entry.xp_percentage == 50

def test_jrl_editor_headless_ui_load_build(qtbot: QtBot, installation: HTInstallation, test_files_dir: pathlib.Path):
    """Test JRL Editor in headless UI - loads real file and builds data."""
    editor = JRLEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Try to find a JRL file
    jrl_file = test_files_dir / "global.jrl"
    if not jrl_file.exists():
        pytest.skip("No JRL files available for testing")
    else:
        original_data = jrl_file.read_bytes()
        editor.load(jrl_file, "global", ResourceType.JRL, original_data)
    
    # Verify editor loaded the data
    assert editor is not None
    assert editor._model.rowCount() > 0
    
    # Build and verify it works
    data, _ = editor.build()
    assert len(data) > 0
    
    # Verify we can read it back
    from pykotor.resource.formats.gff.gff_auto import read_gff
    loaded_jrl = read_gff(data)
    assert loaded_jrl is not None


def test_jrleditor_editor_help_dialog_opens_correct_file(qtbot: QtBot, installation: HTInstallation, test_files_dir: pathlib.Path):
    """Test that JRLEditor help dialog opens and displays the correct help file (not 'Help File Not Found')."""
    from toolset.gui.dialogs.editor_help import EditorHelpDialog
    
    editor = JRLEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Trigger help dialog with the correct file for JRLEditor
    editor._show_help_dialog("GFF-JRL.md")
    def has_dialog():
        return len([child for child in editor.findChildren(EditorHelpDialog)]) > 0
    qtbot.waitUntil(has_dialog, timeout=1000)
    
    # Find the help dialog
    dialogs = [child for child in editor.findChildren(EditorHelpDialog)]
    assert len(dialogs) > 0, "Help dialog should be opened"
    
    dialog = dialogs[0]
    qtbot.waitUntil(lambda: dialog.isVisible(), timeout=1000)
    
    # Get the HTML content
    html = dialog.text_browser.toHtml()
    
    # Assert that "Help File Not Found" error is NOT shown
    assert "Help File Not Found" not in html, \
        f"Help file 'GFF-JRL.md' should be found, but error was shown. HTML: {html[:500]}"
    
    # Assert that some content is present (file was loaded successfully)
    assert len(html) > 100, "Help dialog should contain content"
    
    # Close dialog to avoid dangling widgets during teardown
    dialog.close()
    qtbot.wait(50)

    """Test loading a JRL file."""
    editor = JRLEditor(None, installation)
    qtbot.addWidget(editor)
    
    jrl_file = test_files_dir / "global.jrl"
    if not jrl_file.exists():
        pytest.skip("global.jrl not found")
        
    editor.load(jrl_file, "global", ResourceType.JRL, jrl_file.read_bytes())
    
    assert editor._model.rowCount() > 0
    # Verify tree populated


def test_jrl_editor_change_quest_name_via_locstring_dialog(qtbot: QtBot, installation: HTInstallation, monkeypatch: pytest.MonkeyPatch):
    """Ensure quest name editing uses the locstring dialog and updates model/JRL."""
    from toolset.gui.editors import jrl as jrl_module

    editor = JRLEditor(None, installation)
    qtbot.addWidget(editor)

    quest = JRLQuest()
    quest.name = LocalizedString.from_english("Old Name")
    editor.add_quest(quest)

    quest_item = editor._model.item(0)
    assert quest_item is not None
    editor.ui.journalTree.setCurrentIndex(quest_item.index())

    new_loc = LocalizedString.from_english("Renamed Quest")

    class DummyDialog:
        def __init__(self, *_args, **_kwargs):
            self.locstring = new_loc

        def exec(self):
            return True

    monkeypatch.setattr(jrl_module, "LocalizedStringDialog", DummyDialog)

    editor.change_quest_name()

    assert quest.name.get(Language.ENGLISH, Gender.MALE) == "Renamed Quest"
    assert "Renamed Quest" in quest_item.text()


def test_jrl_editor_change_entry_text_via_locstring_dialog(qtbot: QtBot, installation: HTInstallation, monkeypatch: pytest.MonkeyPatch):
    """Ensure entry text editing uses locstring dialog and refreshes display."""
    from toolset.gui.editors import jrl as jrl_module

    editor = JRLEditor(None, installation)
    qtbot.addWidget(editor)

    quest = JRLQuest()
    quest.name = LocalizedString.from_english("Quest")
    editor.add_quest(quest)

    entry = JRLEntry()
    entry.text = LocalizedString.from_english("Old Entry")
    entry.entry_id = 5
    quest_item = editor._model.item(0)
    assert quest_item is not None
    editor.add_entry(quest_item, entry)

    entry_item = quest_item.child(0)
    assert entry_item is not None
    editor.ui.journalTree.setCurrentIndex(entry_item.index())

    new_loc = LocalizedString.from_english("New Entry Text")

    class DummyDialog:
        def __init__(self, *_args, **_kwargs):
            self.locstring = new_loc

        def exec(self):
            return True

    monkeypatch.setattr(jrl_module, "LocalizedStringDialog", DummyDialog)

    editor.change_entry_text()

    assert entry.text.get(Language.ENGLISH, Gender.MALE) == "New Entry Text"
    assert "New Entry Text" in entry_item.text()


def test_jrl_editor_on_value_updated_for_quest_and_entry(qtbot: QtBot, installation: HTInstallation):
    """Verify on_value_updated propagates UI edits into quest/entry data and refreshes labels."""
    editor = JRLEditor(None, installation)
    qtbot.addWidget(editor)

    quest = JRLQuest()
    quest.name = LocalizedString.from_english("Initial Quest")
    quest.tag = "old_tag"
    quest.plot_index = 0
    quest.planet_id = -1
    quest.priority = JRLQuestPriority.LOW
    editor.add_quest(quest)

    quest_item = editor._model.item(0)
    assert quest_item is not None
    editor.ui.journalTree.setCurrentIndex(quest_item.index())

    editor.ui.categoryTag.setText("new_tag")
    editor.ui.categoryPlotSelect.setCurrentIndex(1)
    editor.ui.categoryPlanetSelect.setCurrentIndex(1)
    editor.ui.categoryPrioritySelect.setCurrentIndex(JRLQuestPriority.HIGH.value)
    editor.on_value_updated()

    assert quest.tag == "new_tag"
    assert quest.plot_index == 1
    assert quest.planet_id == 0
    assert quest.priority == JRLQuestPriority.HIGH

    entry = JRLEntry()
    entry.text = LocalizedString.from_english("Entry Text")
    editor.add_entry(quest_item, entry)

    entry_item = quest_item.child(0)
    assert entry_item is not None
    editor.ui.journalTree.setCurrentIndex(entry_item.index())

    editor.ui.entryEndCheck.setChecked(True)
    editor.ui.entryXpSpin.setValue(75)
    editor.ui.entryIdSpin.setValue(42)
    editor.on_value_updated()

    assert entry.end is True
    assert entry.xp_percentage == 75
    assert entry.entry_id == 42
    assert "[42]" in entry_item.text()


def test_jrl_editor_add_remove_quest_and_entry(qtbot: QtBot, installation: HTInstallation):
    """Exercise add/remove flows to keep model and JRL in sync."""
    editor = JRLEditor(None, installation)
    qtbot.addWidget(editor)

    quest = JRLQuest()
    quest.name = LocalizedString.from_english("Quest Sync")
    editor.add_quest(quest)
    assert editor._model.rowCount() == 1
    assert len(editor._jrl.quests) == 1

    quest_item = editor._model.item(0)
    assert quest_item is not None

    entry = JRLEntry()
    entry.text = LocalizedString.from_english("Entry Sync")
    editor.add_entry(quest_item, entry)
    assert quest_item.rowCount() == 1
    assert len(quest.entries) == 1

    entry_item = quest_item.child(0)
    assert entry_item is not None
    editor.remove_entry(entry_item)
    assert quest_item.rowCount() == 0
    assert len(quest.entries) == 0

    editor.remove_quest(quest_item)
    assert editor._model.rowCount() == 0
    assert len(editor._jrl.quests) == 0


if __name__ == "__main__":
    unittest.main()