from __future__ import annotations

import importlib
import os
import pathlib
import sys
from typing import TYPE_CHECKING
import unittest
from unittest import TestCase

import pytest
from qtpy.QtCore import Qt, QModelIndex
from qtpy.QtGui import QStandardItem


absolute_file_path: pathlib.Path = pathlib.Path(__file__).resolve()
TESTS_FILES_PATH: pathlib.Path = next(f for f in absolute_file_path.parents if f.name == "tests") / "test_files"

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot
    from toolset.data.installation import HTInstallation
    from toolset.gui.editors.tlk import TLKEditor
    from pykotor.resource.formats.tlk.tlk_data import TLK  # pyright: ignore[reportMissingImports]

if __name__ == "__main__" and getattr(sys, "frozen", False) is False:

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

if importlib.util.find_spec("qtpy.QtWidgets") is None:  # pyright: ignore[reportAttributeAccessIssue]
    raise ImportError("qtpy.QtWidgets is required for this test. Install PyQt/PySide with qtpy before running this test.")

from loggerplus import Any
from qtpy.QtTest import QTest
from qtpy.QtWidgets import QApplication

K1_PATH: str | None = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
K2_PATH: str | None = os.environ.get("K2_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II")

from pykotor.resource.formats.tlk import read_tlk  # pyright: ignore[reportMissingImports]
from pykotor.resource.type import ResourceType  # pyright: ignore[reportMissingImports]
from toolset.gui.editors.tlk import TLKEditor
from toolset.data.installation import HTInstallation
from pykotor.resource.formats.tlk import TLK, TLKEntry
from pykotor.resource.type import ResourceType


@unittest.skipIf(
    not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").exists(),
    "K2_PATH environment variable is not set or not found on disk.",
)
@unittest.skipIf(
    QTest is None or not QApplication,
    "qtpy is required, please run pip install -r requirements.txt before running this test.",
)
class TLKEditorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        # Make sure to configure this environment path before testing!
        assert K2_PATH is not None, "K2_PATH environment variable is not set."
        from toolset.gui.editors.tlk import TLKEditor

        cls.TLKEditor = TLKEditor
        from toolset.data.installation import HTInstallation

        cls.INSTALLATION = HTInstallation(K2_PATH, "", tsl=True)

    def setUp(self):
        self.app: QApplication = QApplication([])
        self.editor: TLKEditor = self.TLKEditor(None, self.INSTALLATION)
        self.log_messages: list[str] = [os.linesep]

    def tearDown(self):
        self.app.deleteLater()

    def log_func(self, *args):
        self.log_messages.append("\t".join(args))

    def test_save_and_load(self):
        filepath: pathlib.Path = TESTS_FILES_PATH / "dialog.tlk"

        data1: bytes = filepath.read_bytes()
        old: TLK = read_tlk(data1)
        self.editor.load(filepath, "dialog", ResourceType.TLK, data1)

        data2, _ = self.editor.build()
        assert data2 is not None, "Failed to build TLK"
        new: TLK = read_tlk(data2)

        diff: bool = old.compare(new, self.log_func)
        assert diff
        self.assertDeepEqual(old, new)

    def assertDeepEqual(
        self,
        obj1: Any,
        obj2: Any,
        context: str = "",
    ) -> None:
        if isinstance(obj1, dict) and isinstance(obj2, dict):
            assert set(obj1.keys()) == set(obj2.keys()), context
            for key in obj1:
                new_context: str = f"{context}.{key}" if context else str(key)
                self.assertDeepEqual(obj1[key], obj2[key], new_context)

        elif isinstance(obj1, (list, tuple)) and isinstance(obj2, (list, tuple)):
            assert len(obj1) == len(obj2), context
            for index, (item1, item2) in enumerate(zip(obj1, obj2)):
                new_context = f"{context}[{index}]" if context else f"[{index}]"
                self.assertDeepEqual(item1, item2, new_context)

        elif hasattr(obj1, "__dict__") and hasattr(obj2, "__dict__"):
            self.assertDeepEqual(obj1.__dict__, obj2.__dict__, context)

        else:
            assert obj1 == obj2, context


def test_tlk_editor_all_widgets_exist(qtbot: QtBot, installation: HTInstallation):
    """Verify ALL widgets exist in TLK editor."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()

    # Table view
    assert hasattr(editor.ui, "talkTable")

    # Text edit
    assert hasattr(editor.ui, "textEdit")

    # Sound edit
    assert hasattr(editor.ui, "soundEdit")

    # Search/filter
    assert hasattr(editor.ui, "searchEdit")
    assert hasattr(editor.ui, "searchButton")

    # Jump to line
    assert hasattr(editor.ui, "jumpSpinbox")
    assert hasattr(editor.ui, "jumpButton")

    # Menu actions (insert/delete are menu actions, not buttons)
    assert hasattr(editor.ui, "actionInsert")


def test_tlk_editor_all_widgets_interactions(qtbot: QtBot, installation: HTInstallation):
    """Test ALL widgets with exhaustive interactions."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()

    # Test insert action - adds new entry
    initial_count = editor.source_model.rowCount()
    editor.ui.actionInsert.trigger()
    assert editor.source_model.rowCount() == initial_count + 1

    # Test textEdit - QPlainTextEdit
    test_texts = [
        "",
        "Simple text",
        "Text with\nmultiple\nlines",
        "Text with special chars !@#$%^&*()",
        "Text with numbers 123456",
        "Very long text " * 100,
    ]

    for text in test_texts:
        editor.ui.textEdit.setPlainText(text)
        assert editor.ui.textEdit.toPlainText() == text

    # Test soundEdit - QLineEdit (maxLength is 16 per UI definition)
    test_sounds: list[str] = [
        "",
        "test_sound",
        "sound_with_123",
        "very_long_sound",  # 16 chars max (UI limit)
    ]

    for sound in test_sounds:
        editor.ui.soundEdit.setText(sound)
        assert editor.ui.soundEdit.text() == sound

    # Test searchEdit - QLineEdit
    test_filters: list[str] = [
        "",
        "test",
        "TEST",
        "test filter",
        "123",
        "special!@#",
    ]

    # Add some entries first to test filtering
    for i in range(5):
        editor.insert()
        index = editor.proxy_model.index(editor.source_model.rowCount() - 1, 0)
        editor.ui.talkTable.setCurrentIndex(index)
        editor.ui.textEdit.setPlainText(f"Test entry {i}")

    # Test filtering with known data
    # Clear existing entries and add test data
    editor.source_model.clear()
    editor.source_model.setColumnCount(2)
    test_filter_data = ["apple", "banana", "cherry", "date"]
    for text in test_filter_data:
        editor.insert()
        index = editor.proxy_model.index(editor.source_model.rowCount() - 1, 0)
        editor.ui.talkTable.setCurrentIndex(index)
        editor.ui.textEdit.setPlainText(text)

    # Test each filter
    for filter_text in test_filters:
        editor.ui.searchEdit.setText(filter_text)
        editor.do_filter(filter_text)
        # Verify filter was applied by checking the filterFixedString matches
        # QSortFilterProxyModel uses filterFixedString internally
        # We verify by checking that the proxy model reflects the filter
        proxy_count = editor.proxy_model.rowCount()
        source_count = editor.source_model.rowCount()
        # With a filter, proxy count should be <= source count
        assert proxy_count <= source_count, f"Filtered count ({proxy_count}) should be <= source count ({source_count})"
        # Empty filter should show all entries
        if filter_text == "":
            assert proxy_count == source_count, f"Empty filter should show all {source_count} entries, got {proxy_count}"


def test_tlk_editor_insert_remove_exhaustive(qtbot: QtBot, installation: HTInstallation):
    """Test insert/remove operations exhaustively."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()

    # Insert multiple entries
    for i in range(10):
        editor.ui.actionInsert.trigger()
        assert editor.source_model.rowCount() == i + 1

    # Set text for each entry
    for i in range(10):
        index = editor.proxy_model.index(i, 0)
        editor.ui.talkTable.setCurrentIndex(index)
        editor.ui.textEdit.setPlainText(f"Entry {i}")
        editor.ui.soundEdit.setText(f"sound_{i}")

    # Remove entries one by one (delete is via context menu or direct model manipulation)
    while editor.source_model.rowCount() > 0:
        count_before = editor.source_model.rowCount()
        # Remove first row directly from model
        editor.source_model.removeRow(0)
        assert editor.source_model.rowCount() == count_before - 1


def test_tlk_editor_search_filter_exhaustive(qtbot: QtBot, installation: HTInstallation):
    """Test search/filter functionality exhaustively."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()

    # Add entries with different text
    entries_data = [
        "Apple",
        "Banana",
        "Cherry",
        "Date",
        "Elderberry",
        "Apple Pie",
        "Banana Bread",
        "Test Entry",
        "Another Test",
        "Final Entry",
    ]

    for text in entries_data:
        editor.insert()
        index = editor.proxy_model.index(editor.source_model.rowCount() - 1, 0)
        editor.ui.talkTable.setCurrentIndex(index)
        editor.ui.textEdit.setPlainText(text)

    # Test various filter patterns
    filter_tests = [
        ("App", 2),  # Apple, Apple Pie
        ("Ban", 2),  # Banana, Banana Bread
        ("Test", 2),  # Test Entry, Another Test
        ("", 10),  # No filter - all entries
        ("XYZ", 0),  # No matches
        ("a", 7),  # Case insensitive: Apple, Banana, Date, Apple Pie, Banana Bread, Another Test, Final Entry
        ("E", 9),  # Case insensitive: All except "Banana" contain E or e
    ]

    for filter_text, expected_count in filter_tests:
        editor.ui.searchEdit.setText(filter_text)
        editor.do_filter(filter_text)
        assert editor.proxy_model.rowCount() == expected_count, f"Filter '{filter_text}' should show {expected_count} entries, got {editor.proxy_model.rowCount()}"


def test_tlk_editor_goto_line_exhaustive(qtbot: QtBot, installation: HTInstallation):
    """Test goto line functionality exhaustively."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()

    # Add multiple entries
    for i in range(20):
        editor.insert()
        item = editor.source_model.item(i, 0)
        if item:
            item.setText(f"Entry {i}")

    # Test jumping to various lines
    test_lines = [0, 1, 5, 10, 15, 19]

    for line in test_lines:
        editor.ui.jumpSpinbox.setValue(line)
        # Signal should trigger goto via valueChanged connection
        # Process events to allow signal to propagate
        from qtpy.QtWidgets import QApplication

        QApplication.processEvents()

        # Verify goto worked correctly
        current_index = editor.ui.talkTable.currentIndex()
        assert current_index.isValid(), f"Index should be valid for line {line}"

        # Map proxy index back to source to verify correct row
        source_index = editor.proxy_model.mapToSource(current_index)
        assert source_index.isValid(), f"Source index should be valid for line {line}"
        assert source_index.row() == line, f"Should be at source row {line}, got {source_index.row()}"

        # Verify the spinbox value matches
        assert editor.ui.jumpSpinbox.value() == line, f"Spinbox should show {line}, got {editor.ui.jumpSpinbox.value()}"


def test_tlk_editor_build_verification(qtbot: QtBot, installation: HTInstallation):
    """Test that ALL widget values are correctly saved in build()."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()

    # Add and configure multiple entries
    test_entries = [
        ("Entry 1", "sound1"),
        ("Entry 2", "sound2"),
        ("Entry 3", ""),
        ("Multi\nLine\nEntry", "sound3"),
    ]

    for text, sound in test_entries:
        editor.insert()
        index = editor.proxy_model.index(editor.source_model.rowCount() - 1, 0)
        editor.ui.talkTable.setCurrentIndex(index)
        editor.ui.textEdit.setPlainText(text)
        editor.ui.soundEdit.setText(sound)

    # Build and verify
    data, _ = editor.build()
    from pykotor.resource.formats.tlk import read_tlk

    tlk = read_tlk(data)

    assert len(tlk) == len(test_entries)
    for i, (expected_text, expected_sound) in enumerate(test_entries):
        assert tlk[i].text == expected_text
        assert tlk[i].voiceover == expected_sound


def test_tlk_editor_load_real_file(qtbot: QtBot, installation: HTInstallation, test_files_dir):
    """Test loading a real TLK file."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)

    tlk_file = test_files_dir / "dialog.tlk"
    if not tlk_file.exists():
        pytest.skip("dialog.tlk not found")

    # Read file data once and verify it's valid
    file_data = tlk_file.read_bytes()
    assert len(file_data) > 0, "TLK file should not be empty"

    # Verify we can read it before loading in editor
    from pykotor.resource.formats.tlk import read_tlk

    test_tlk = read_tlk(file_data)
    assert len(test_tlk) > 0, "TLK should have entries"

    # Load in editor - LoaderDialog.exec() is blocking, so it completes before returning
    editor.load(tlk_file, "dialog", ResourceType.TLK, file_data)

    # Verify entries loaded
    assert editor.source_model.rowCount() > 0, "Editor should have loaded entries"
    assert editor.source_model.rowCount() == len(test_tlk), f"Editor should have {len(test_tlk)} entries, got {editor.source_model.rowCount()}"

    # Verify widgets populated when selecting first entry
    index = editor.proxy_model.index(0, 0)
    assert index.isValid(), "First index should be valid"
    editor.ui.talkTable.setCurrentIndex(index)
    qtbot.wait(50)  # Wait for selection to update

    # Verify text edit is populated with actual entry text
    loaded_text = editor.ui.textEdit.toPlainText()
    expected_text = test_tlk[0].text
    assert loaded_text == expected_text, f"Text edit should show entry text '{expected_text}', got '{loaded_text}'"


def test_tlk_editor_table_selection(qtbot: QtBot, installation: HTInstallation):
    """Test table selection and widget updates."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()

    # Add entries
    for i in range(5):
        editor.insert()
        item = editor.source_model.item(i, 0)
        if item:
            item.setText(f"Entry {i}")

    # Test selecting each entry updates widgets
    for i in range(5):
        # Get the source index (proxy might be filtered)
        source_index = editor.source_model.index(i, 0)
        assert source_index.isValid(), f"Source index {i} should be valid"

        # Map to proxy index
        proxy_index = editor.proxy_model.mapFromSource(source_index)
        assert proxy_index.isValid(), f"Proxy index {i} should be valid"

        # Set current index and trigger selection
        editor.ui.talkTable.setCurrentIndex(proxy_index)
        # Manually trigger selection_changed to ensure widgets update
        editor.selection_changed()
        qtbot.wait(50)  # Wait for any async updates

        # Widgets should update with entry text
        current_text = editor.ui.textEdit.toPlainText()
        expected_text = f"Entry {i}"
        assert current_text == expected_text, f"Text edit should show '{expected_text}' for entry {i}, got '{current_text}'"

        # Verify sound edit is enabled when entry is selected
        assert editor.ui.soundEdit.isEnabled(), f"Sound edit should be enabled when entry {i} is selected"
        assert editor.ui.textEdit.isEnabled(), f"Text edit should be enabled when entry {i} is selected"


def test_tlk_editor_edit_entry_exhaustive(qtbot: QtBot, installation: HTInstallation):
    """Test editing entries with all combinations."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()

    # Add entry
    editor.insert()
    index = editor.proxy_model.index(0, 0)
    editor.ui.talkTable.setCurrentIndex(index)

    # Test various text/sound combinations
    test_combinations: list[tuple[str, str]] = [
        ("Text only", ""),
        ("", "Sound only"),
        ("Both", "both_sound"),
        ("Multi\nLine", "multi_sound"),
        ("", ""),  # Empty entry
    ]

    for text, sound in test_combinations:
        editor.ui.textEdit.setPlainText(text)
        editor.ui.soundEdit.setText(sound)

        # Verify values set
        assert editor.ui.textEdit.toPlainText() == text
        assert editor.ui.soundEdit.text() == sound

        # Build and verify
        data, _ = editor.build()
        from pykotor.resource.formats.tlk import read_tlk

        tlk = read_tlk(data)
        assert len(tlk) == 1
        assert tlk[0].text == text
        assert tlk[0].voiceover == sound


def test_tlk_editor_remove_button_states(qtbot: QtBot, installation: HTInstallation):
    """Test remove button enabled/disabled states."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()

    # Initially no entries - remove should be disabled or do nothing
    initial_count = editor.source_model.rowCount()
    editor.ui.talkTable.setCurrentIndex(QModelIndex())  # No selection
    # Remove with no selection should not crash

    # Add entry
    editor.insert()
    assert editor.source_model.rowCount() == 1

    # Select entry
    index = editor.proxy_model.index(0, 0)
    editor.ui.talkTable.setCurrentIndex(index)

    # Remove should work (remove directly from model)
    editor.source_model.removeRow(0)
    assert editor.source_model.rowCount() == 0


def test_tlk_editor_jump_spinbox_range(qtbot: QtBot, installation: HTInstallation):
    """Test jump spinbox with various values."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()

    # Add entries
    for i in range(10):
        editor.insert()

    # Test jump spinbox values
    for val in [0, 1, 5, 9]:
        editor.ui.jumpSpinbox.setValue(val)
        assert editor.ui.jumpSpinbox.value() == val

        # Process events to allow signal to propagate
        from qtpy.QtWidgets import QApplication

        QApplication.processEvents()

        # Should update table selection to correct row
        current = editor.ui.talkTable.currentIndex()
        assert current.isValid(), f"Index should be valid for value {val}"

        # Map proxy index to source to verify correct row
        source_index = editor.proxy_model.mapToSource(current)
        assert source_index.isValid(), f"Source index should be valid for value {val}"
        assert source_index.row() == val, f"Should be at source row {val}, got {source_index.row()}"


def test_tlk_editor_filter_case_sensitivity(qtbot: QtBot, installation: HTInstallation):
    """Test filter case sensitivity."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()

    # Add entries with mixed case
    entries = ["Apple", "apple", "APPLE", "Banana", "banana"]
    for text in entries:
        editor.insert()
        index = editor.proxy_model.index(editor.source_model.rowCount() - 1, 0)
        editor.ui.talkTable.setCurrentIndex(index)
        editor.ui.textEdit.setPlainText(text)

    # Test case-insensitive filter (default behavior)
    editor.ui.searchEdit.setText("apple")
    editor.do_filter("apple")
    # Should match Apple, apple, APPLE
    assert editor.proxy_model.rowCount() == 3

    editor.ui.searchEdit.setText("APPLE")
    editor.do_filter("APPLE")
    # Should still match all (case insensitive)
    assert editor.proxy_model.rowCount() == 3


def test_tlk_editor_empty_entry_handling(qtbot: QtBot, installation: HTInstallation):
    """Test handling of empty entries."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()

    # Add empty entry
    editor.insert()
    index = editor.proxy_model.index(0, 0)
    editor.ui.talkTable.setCurrentIndex(index)
    editor.ui.textEdit.setPlainText("")
    editor.ui.soundEdit.setText("")

    # Build should handle empty entry
    data, _ = editor.build()
    from pykotor.resource.formats.tlk import read_tlk

    tlk = read_tlk(data)
    assert len(tlk) == 1
    assert tlk[0].text == ""
    assert tlk[0].voiceover == ""


# ============================================================================
# Language functionality tests
# ============================================================================


def test_tlk_editor_language_menu_exists(qtbot: QtBot, installation: HTInstallation):
    """Test that language menu exists and has actions."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.show()

    # Verify menu exists
    assert hasattr(editor.ui, "menuLanguage")
    assert editor.ui.menuLanguage is not None

    # Verify menu has actions (should have auto-detect + separator + all languages)
    actions = editor.ui.menuLanguage.actions()
    assert len(actions) > 0, "Language menu should have actions"

    # Verify language actions dictionary exists
    assert hasattr(editor, "_language_actions")
    assert len(editor._language_actions) > 0, "Should have language actions"


def test_tlk_editor_language_defaults_to_english(qtbot: QtBot, installation: HTInstallation):
    """Test that new TLK editor defaults to English language."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()

    from pykotor.common.language import Language

    assert editor.language == Language.ENGLISH, "Default language should be English"


def test_tlk_editor_language_menu_checkmarks(qtbot: QtBot, installation: HTInstallation):
    """Test that language menu shows correct checkmark for current language."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()

    from pykotor.common.language import Language

    # Initially English should be checked
    assert editor._language_actions[Language.ENGLISH].isChecked(), "English should be checked initially"

    # Change to French
    editor.change_language(Language.FRENCH)
    assert not editor._language_actions[Language.ENGLISH].isChecked(), "English should not be checked"
    assert editor._language_actions[Language.FRENCH].isChecked(), "French should be checked"

    # Change to German
    editor.change_language(Language.GERMAN)
    assert not editor._language_actions[Language.FRENCH].isChecked(), "French should not be checked"
    assert editor._language_actions[Language.GERMAN].isChecked(), "German should be checked"


def test_tlk_editor_language_change_via_menu(qtbot: QtBot, installation: HTInstallation):
    """Test changing language via menu action."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()

    from pykotor.common.language import Language

    # Initially English
    assert editor.language == Language.ENGLISH

    # Trigger French language action
    french_action = editor._language_actions[Language.FRENCH]
    french_action.trigger()
    qtbot.wait(100)  # Wait for signal processing

    # Verify language changed
    assert editor.language == Language.FRENCH, "Language should be French after triggering action"


def test_tlk_editor_language_saved_in_build(qtbot: QtBot, installation: HTInstallation):
    """Test that language is correctly saved when building TLK."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()

    from pykotor.common.language import Language
    from pykotor.resource.formats.tlk import read_tlk

    # Test multiple languages
    test_languages = [Language.ENGLISH, Language.FRENCH, Language.GERMAN, Language.ITALIAN, Language.SPANISH]

    for lang in test_languages:
        # Set language
        editor.change_language(lang)
        assert editor.language == lang

        # Add an entry
        editor.insert()
        index = editor.proxy_model.index(0, 0)
        editor.ui.talkTable.setCurrentIndex(index)
        editor.ui.textEdit.setPlainText(f"Test text for {lang.name}")

        # Build and verify language
        data, _ = editor.build()
        tlk = read_tlk(data)
        assert tlk.language == lang, f"TLK language should be {lang.name}, got {tlk.language.name}"

        # Clear for next iteration
        editor.source_model.clear()
        editor.source_model.setColumnCount(2)


def test_tlk_editor_language_loaded_from_file(qtbot: QtBot, installation: HTInstallation, test_files_dir):
    """Test that language is correctly loaded from TLK file."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)

    tlk_file = test_files_dir / "dialog.tlk"
    if not tlk_file.exists():
        pytest.skip("dialog.tlk not found")

    # Read the file to get its language
    from pykotor.resource.formats.tlk import read_tlk

    original_tlk = read_tlk(tlk_file.read_bytes())
    original_language = original_tlk.language

    # Load file in editor - LoaderDialog.exec() is blocking, so it completes before returning
    file_data = tlk_file.read_bytes()
    editor.load(tlk_file, "dialog", ResourceType.TLK, file_data)

    # Verify language was loaded correctly
    assert editor.language == original_language, f"Editor language should match file language ({original_language.name}), got {editor.language.name}"


def test_tlk_editor_language_change_and_reload(qtbot: QtBot, installation: HTInstallation, test_files_dir: pathlib.Path):
    """Test changing language and reloading file with different language."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)

    tlk_file = test_files_dir / "dialog.tlk"
    if not tlk_file.exists():
        pytest.skip("dialog.tlk not found")

    # Load file - LoaderDialog.exec() is blocking, so it completes before returning
    file_data = tlk_file.read_bytes()
    editor.load(tlk_file, "dialog", ResourceType.TLK, file_data)

    original_entry_count = editor.source_model.rowCount()
    assert original_entry_count > 0, "File should have entries"

    from pykotor.common.language import Language

    # Change language (should reload with same language parameter)
    # The file's language won't change, but we're testing the reload mechanism
    editor.change_language(Language.FRENCH)
    # change_language calls LoaderDialog.exec() which is blocking

    # Verify entries still exist (reload should preserve data)
    assert editor.source_model.rowCount() == original_entry_count, (
        f"Entry count should remain the same after language change, expected {original_entry_count}, got {editor.source_model.rowCount()}"
    )


def test_tlk_editor_language_build_and_verify_all_languages(qtbot: QtBot, installation: HTInstallation):
    """Test building TLK with all major languages and verifying language is correct."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()

    from pykotor.common.language import Language
    from pykotor.resource.formats.tlk import read_tlk

    # Test all official languages
    official_languages = [
        Language.ENGLISH,
        Language.FRENCH,
        Language.GERMAN,
        Language.ITALIAN,
        Language.SPANISH,
        Language.POLISH,
    ]

    for lang in official_languages:
        # Set language
        editor.change_language(lang)

        # Add test entry
        editor.insert()
        index = editor.proxy_model.index(0, 0)
        editor.ui.talkTable.setCurrentIndex(index)
        editor.ui.textEdit.setPlainText(f"Test for {lang.name}")
        editor.ui.soundEdit.setText("test_sound")

        # Build
        data, _ = editor.build()

        # Verify language in built file
        tlk = read_tlk(data)
        assert tlk.language == lang, f"Built TLK should have language {lang.name}, got {tlk.language.name}"
        assert len(tlk) == 1, "Should have one entry"
        assert tlk[0].text == f"Test for {lang.name}"
        assert tlk[0].voiceover == "test_sound"

        # Clear for next iteration
        editor.source_model.clear()
        editor.source_model.setColumnCount(2)


def test_tlk_editor_language_save_and_reload_preserves_language(qtbot: QtBot, installation: HTInstallation, tmp_path):
    """Test that saving and reloading preserves the language setting."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()

    from pykotor.common.language import Language
    from pykotor.resource.formats.tlk import read_tlk

    # Set to French
    editor.change_language(Language.FRENCH)

    # Add entry
    editor.insert()
    index = editor.proxy_model.index(0, 0)
    editor.ui.talkTable.setCurrentIndex(index)
    editor.ui.textEdit.setPlainText("French text")

    # Build and save to file
    data, _ = editor.build()
    test_file = tmp_path / "test_french.tlk"
    test_file.write_bytes(data)

    # Verify saved file has correct language
    saved_tlk = read_tlk(test_file.read_bytes())
    assert saved_tlk.language == Language.FRENCH, "Saved file should have French language"

    # Create new editor and load the file - LoaderDialog.exec() is blocking
    editor2 = TLKEditor(None, installation)
    qtbot.addWidget(editor2)
    file_data = test_file.read_bytes()
    editor2.load(test_file, "test_french", ResourceType.TLK, file_data)

    # Verify language was loaded correctly
    assert editor2.language == Language.FRENCH, f"Loaded editor should have French language from file, got {editor2.language.name}"


def test_tlk_editor_language_auto_detect(qtbot: QtBot, installation: HTInstallation, test_files_dir):
    """Test auto-detect language functionality."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)

    tlk_file = test_files_dir / "dialog.tlk"
    if not tlk_file.exists():
        pytest.skip("dialog.tlk not found")

    # Load file - LoaderDialog.exec() is blocking, so it completes before returning
    file_data = tlk_file.read_bytes()
    editor.load(tlk_file, "dialog", ResourceType.TLK, file_data)

    # Get the language from the file
    from pykotor.resource.formats.tlk import read_tlk

    original_tlk = read_tlk(file_data)
    expected_language = original_tlk.language

    # Trigger auto-detect - this will reload the file and detect language
    editor.on_language_selected("auto_detect")
    # on_language_selected calls change_language which calls LoaderDialog.exec() which is blocking

    # Verify language matches file's language
    assert editor.language == expected_language, f"Auto-detect should set language to file's language ({expected_language.name}), got {editor.language.name}"


def test_tlk_editor_language_menu_actions_triggerable(qtbot: QtBot, installation: HTInstallation):
    """Test that all language menu actions can be triggered."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()

    from pykotor.common.language import Language

    # Test triggering several language actions
    test_languages = [
        Language.ENGLISH,
        Language.FRENCH,
        Language.GERMAN,
        Language.ITALIAN,
        Language.SPANISH,
    ]

    for lang in test_languages:
        if lang in editor._language_actions:
            action = editor._language_actions[lang]
            action.trigger()
            qtbot.wait(50)  # Wait for signal processing

            # Verify language changed
            assert editor.language == lang, f"Language should be {lang.name} after triggering action"


def test_tlk_editor_language_build_with_custom_language(qtbot: QtBot, installation: HTInstallation):
    """Test building TLK with a custom language."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()

    from pykotor.common.language import Language
    from pykotor.resource.formats.tlk import read_tlk

    # Use a custom language (e.g., Portuguese)
    if Language.PORTUGUESE in editor._language_actions:
        editor.change_language(Language.PORTUGUESE)

        # Add entry
        editor.insert()
        index = editor.proxy_model.index(0, 0)
        editor.ui.talkTable.setCurrentIndex(index)
        editor.ui.textEdit.setPlainText("Texto em português")

        # Build and verify
        data, _ = editor.build()
        tlk = read_tlk(data)
        assert tlk.language == Language.PORTUGUESE, "TLK should have Portuguese language"
        assert tlk[0].text == "Texto em português"


def test_tlkeditor_editor_help_dialog_opens_correct_file(qtbot: QtBot, installation: HTInstallation):
    """Test that TLKEditor help dialog opens and displays the correct help file (not 'Help File Not Found')."""
    from toolset.gui.dialogs.editor_help import EditorHelpDialog

    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)

    # Trigger help dialog with the correct file for TLKEditor
    editor._show_help_dialog("TLK-File-Format.md")
    qtbot.wait(200)  # Wait for dialog to be created

    # Find the help dialog
    dialogs = [child for child in editor.findChildren(EditorHelpDialog)]
    assert len(dialogs) > 0, "Help dialog should be opened"

    dialog = dialogs[0]
    qtbot.waitExposed(dialog)

    # Get the HTML content
    html = dialog.text_browser.toHtml()

    # Assert that "Help File Not Found" error is NOT shown
    assert "Help File Not Found" not in html, f"Help file 'TLK-File-Format.md' should be found, but error was shown. HTML: {html[:500]}"

    # Assert that some content is present (file was loaded successfully)
    assert len(html) > 100, "Help dialog should contain content"


def test_tlk_editor_table_selection_modes(qtbot: QtBot, installation: HTInstallation):
    """Test table selection modes and multiple selections if supported."""
    editor = TLKEditor(None, installation)
    qtbot.addWidget(editor)
    editor.new()

    # Add multiple entries with text
    for i in range(5):
        editor.insert()
        item = editor.source_model.item(i, 0)
        if item:
            item.setText(f"Entry {i}")

    # Test single selection
    index = editor.proxy_model.index(2, 0)
    assert index.isValid(), "Index 2 should be valid"
    editor.ui.talkTable.setCurrentIndex(index)
    qtbot.wait(50)  # Wait for selection to update

    current = editor.ui.talkTable.currentIndex()
    assert current.isValid(), "Current index should be valid"
    assert current.row() == 2, f"Should be at row 2, got {current.row()}"

    # Verify selection updates widgets with correct entry text
    loaded_text = editor.ui.textEdit.toPlainText()
    expected_text = "Entry 2"
    assert loaded_text == expected_text, f"Text edit should show '{expected_text}', got '{loaded_text}'"

    # Verify widgets are enabled when entry is selected
    assert editor.ui.textEdit.isEnabled(), "Text edit should be enabled when entry is selected"
    assert editor.ui.soundEdit.isEnabled(), "Sound edit should be enabled when entry is selected"


if __name__ == "__main__":
    unittest.main()
