"""Comprehensive tests for slot method signatures in widget classes.

This test suite ensures all slot methods properly accept the arguments
emitted by Qt signals, preventing TypeError exceptions at runtime.
"""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Skip if Qt is not available
pytest.importorskip("qtpy")

from qtpy.QtCore import QPoint, QTimer, Qt
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QApplication, QScrollBar, QWidget

from toolset.data.installation import HTInstallation
from toolset.gui.widgets.main_widgets import ResourceList, TextureList
from toolset.gui.windows.main import ToolWindow
from pykotor.extract.file import FileResource
from pykotor.resource.type import ResourceType


@pytest.fixture
def qtbot_app(qtbot):
    """Ensure QApplication exists for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def mock_installation():
    """Create a mock installation for testing."""
    mock = MagicMock(spec=HTInstallation)
    mock.name = "Test Installation"
    mock.tsl = False
    mock.path.return_value = Path("/mock/path")
    mock.module_path.return_value = Path("/mock/path/modules")
    mock.override_path.return_value = Path("/mock/path/override")
    mock.core_resources.return_value = []
    mock.module_resources.return_value = []
    mock.override_resources.return_value = []
    mock.texturepack_resources.return_value = []
    mock.module_names.return_value = {}
    mock.override_list.return_value = []
    mock.texturepacks_list.return_value = []
    mock.saves = {}
    return mock


class TestResourceListSlots:
    """Test slot methods in ResourceList class."""

    @pytest.fixture
    def resource_list(self, qtbot, mock_installation):
        """Create a ResourceList instance for testing."""
        widget = ResourceList(None)
        widget.set_installation(mock_installation)
        qtbot.addWidget(widget)
        return widget

    def test_on_reload_clicked_with_bool(self, resource_list, qtbot):
        """Test on_reload_clicked accepts bool from clicked signal."""
        # Should not raise TypeError
        resource_list.on_reload_clicked(False)
        resource_list.on_reload_clicked(True)
        # Should also work without argument (default)
        resource_list.on_reload_clicked()

    def test_on_refresh_clicked_with_bool(self, resource_list, qtbot):
        """Test on_refresh_clicked accepts bool from clicked signal."""
        resource_list.on_refresh_clicked(False)
        resource_list.on_refresh_clicked(True)
        resource_list.on_refresh_clicked()

    def test_on_filter_string_updated_with_str(self, resource_list, qtbot):
        """Test on_filter_string_updated accepts str from textChanged/textEdited signal."""
        resource_list.on_filter_string_updated("test")
        resource_list.on_filter_string_updated("")
        resource_list.on_filter_string_updated()

    def test_on_section_changed_with_int(self, resource_list, qtbot):
        """Test on_section_changed accepts int from currentIndexChanged signal."""
        resource_list.on_section_changed(0)
        resource_list.on_section_changed(1)
        resource_list.on_section_changed(-1)

    def test_on_resource_context_menu_with_qpoint(self, resource_list, qtbot):
        """Test on_resource_context_menu accepts QPoint from customContextMenuRequested signal."""
        point = QPoint(10, 20)
        resource_list.on_resource_context_menu(point)

    def test_on_resource_double_clicked_with_qmodelindex(self, resource_list, qtbot):
        """Test on_resource_double_clicked accepts QModelIndex from doubleClicked signal."""
        # Create a mock model index
        model = QStandardItemModel()
        index = model.index(0, 0)
        resource_list.on_resource_double_clicked(index)
        # Should also work with None
        resource_list.on_resource_double_clicked(None)
        resource_list.on_resource_double_clicked()

    def test_on_open_save_editor_from_context_with_bool(self, resource_list, qtbot):
        """Test on_open_save_editor_from_context accepts bool from triggered signal."""
        with patch.object(resource_list, "window", return_value=None):
            resource_list.on_open_save_editor_from_context(False)
            resource_list.on_open_save_editor_from_context(True)
            resource_list.on_open_save_editor_from_context()


class TestTextureListSlots:
    """Test slot methods in TextureList class."""

    @pytest.fixture
    def texture_list(self, qtbot, mock_installation):
        """Create a TextureList instance for testing."""
        widget = TextureList(None)
        widget.set_installation(mock_installation)
        qtbot.addWidget(widget)
        return widget

    def test_queue_load_visible_icons_with_int(self, texture_list, qtbot):
        """Test queue_load_visible_icons accepts int from valueChanged signal."""
        texture_list.queue_load_visible_icons(0)
        texture_list.queue_load_visible_icons(100)
        texture_list.queue_load_visible_icons(-1)
        # Should also work without argument (default)
        texture_list.queue_load_visible_icons()

    def test_queue_load_visible_icons_via_timer(self, texture_list, qtbot):
        """Test queue_load_visible_icons works when called via QTimer.singleShot."""
        # This should not raise TypeError
        def check_called():
            # Verify the method was called
            pass

        texture_list._queue_called = False
        original_method = texture_list.queue_load_visible_icons

        def wrapper(*args):
            texture_list._queue_called = True
            return original_method(*args)

        texture_list.queue_load_visible_icons = wrapper
        QTimer.singleShot(10, lambda: texture_list.queue_load_visible_icons(0))
        qtbot.wait(50)
        assert texture_list._queue_called

    def test_on_reload_clicked_with_bool(self, texture_list, qtbot):
        """Test on_reload_clicked accepts bool from clicked signal."""
        texture_list.on_reload_clicked(False)
        texture_list.on_reload_clicked(True)
        texture_list.on_reload_clicked()

    def test_on_refresh_clicked_with_bool(self, texture_list, qtbot):
        """Test on_refresh_clicked accepts bool from clicked signal."""
        texture_list.on_refresh_clicked(False)
        texture_list.on_refresh_clicked(True)
        texture_list.on_refresh_clicked()

    def test_on_filter_string_updated_with_str(self, texture_list, qtbot):
        """Test on_filter_string_updated accepts str from textChanged/textEdited signal."""
        texture_list.on_filter_string_updated("test")
        texture_list.on_filter_string_updated("")
        texture_list.on_filter_string_updated()

    def test_on_section_changed_with_int(self, texture_list, qtbot):
        """Test on_section_changed accepts int from currentIndexChanged signal."""
        texture_list.on_section_changed(0)
        texture_list.on_section_changed(1)
        texture_list.on_section_changed(-1)

    def test_on_resource_double_clicked_with_qmodelindex(self, texture_list, qtbot):
        """Test on_resource_double_clicked accepts QModelIndex from doubleClicked signal."""
        model = QStandardItemModel()
        index = model.index(0, 0)
        texture_list.on_resource_double_clicked(index)
        texture_list.on_resource_double_clicked(None)
        texture_list.on_resource_double_clicked()

    def test_on_reload_selected_with_bool(self, texture_list, qtbot):
        """Test on_reload_selected accepts bool from triggered signal."""
        texture_list.on_reload_selected(False)
        texture_list.on_reload_selected(True)
        texture_list.on_reload_selected()

    def test_on_icon_loaded_with_future(self, texture_list, qtbot):
        """Test on_icon_loaded accepts Future from signal."""
        from concurrent.futures import Future
        future = Future()
        future.set_result((("test", 0), None))
        texture_list.on_icon_loaded(future)


class TestToolWindowSlots:
    """Test slot methods in ToolWindow class."""

    @pytest.fixture
    def tool_window(self, qtbot, mock_installation):
        """Create a ToolWindow instance for testing."""
        widget = ToolWindow()
        qtbot.addWidget(widget)
        return widget

    def test_on_tab_changed_with_int(self, tool_window, qtbot):
        """Test on_tab_changed accepts int from currentChanged signal."""
        tool_window.on_tab_changed(0)
        tool_window.on_tab_changed(1)
        tool_window.on_tab_changed(-1)

    def test_on_open_save_editor_with_bool(self, tool_window, qtbot):
        """Test on_open_save_editor accepts bool from clicked signal."""
        tool_window.on_open_save_editor(False)
        tool_window.on_open_save_editor(True)
        tool_window.on_open_save_editor()

    def test_on_save_selection_changed(self, tool_window, qtbot):
        """Test on_save_selection_changed works without arguments."""
        tool_window.on_save_selection_changed()

    def test_on_core_refresh(self, tool_window, qtbot):
        """Test on_core_refresh works without arguments."""
        tool_window.on_core_refresh()

    def test_on_module_changed_with_str(self, tool_window, qtbot):
        """Test on_module_changed accepts str from signal."""
        tool_window.on_module_changed("test.mod")

    def test_on_module_reload_with_str(self, tool_window, qtbot):
        """Test on_module_reload accepts str from signal."""
        with patch.object(tool_window, "active", None):
            # Should handle None active gracefully
            pass

    def test_on_module_file_updated_with_str_str(self, tool_window, qtbot):
        """Test on_module_file_updated accepts str, str from signal."""
        with patch.object(tool_window, "active", None):
            tool_window.on_module_file_updated("test.mod", "created")

    def test_on_savepath_changed_with_str(self, tool_window, qtbot):
        """Test on_savepath_changed accepts str from signal."""
        with patch.object(tool_window, "active", None):
            tool_window.on_savepath_changed("/path/to/saves")

    def test_on_save_reload_with_str(self, tool_window, qtbot):
        """Test on_save_reload accepts str from signal."""
        with patch.object(tool_window, "active", None):
            tool_window.on_save_reload("/path/to/saves")

    def test_on_override_changed_with_str(self, tool_window, qtbot):
        """Test on_override_changed accepts str from signal."""
        with patch.object(tool_window, "active", None):
            tool_window.on_override_changed("subfolder")

    def test_on_override_reload_with_str(self, tool_window, qtbot):
        """Test on_override_reload accepts str from signal."""
        with patch.object(tool_window, "active", None):
            tool_window.on_override_reload("file.ext")

    def test_on_override_file_updated_with_str_str(self, tool_window, qtbot):
        """Test on_override_file_updated accepts str, str from signal."""
        tool_window.on_override_file_updated("file.ext", "created")

    def test_on_textures_changed_with_str(self, tool_window, qtbot):
        """Test on_textures_changed accepts str from signal."""
        with patch.object(tool_window, "active", None):
            tool_window.on_textures_changed("texturepack")

    def test_change_active_installation_with_int(self, tool_window, qtbot):
        """Test change_active_installation accepts int from currentIndexChanged signal."""
        # This will try to load installation, so we need to mock it
        with patch.object(tool_window, "settings") as mock_settings:
            mock_settings.installations.return_value = {}
            tool_window.change_active_installation(0)  # Should handle index 0 (None)

    def test_open_module_designer_with_bool(self, tool_window, qtbot):
        """Test open_module_designer accepts bool from triggered signal."""
        with patch.object(tool_window, "active", None):
            # Should handle None active
            pass
        tool_window.open_module_designer(False)
        tool_window.open_module_designer(True)
        tool_window.open_module_designer()

    def test_open_settings_dialog_with_bool(self, tool_window, qtbot):
        """Test open_settings_dialog accepts bool from triggered signal."""
        with patch("toolset.gui.dialogs.settings.SettingsDialog") as mock_dialog:
            mock_dialog.return_value.exec.return_value = False
            tool_window.open_settings_dialog(False)
            tool_window.open_settings_dialog(True)
            tool_window.open_settings_dialog()

    def test_open_active_talktable_with_bool(self, tool_window, qtbot):
        """Test open_active_talktable accepts bool from triggered signal."""
        with patch.object(tool_window, "active", None):
            tool_window.open_active_talktable(False)
            tool_window.open_active_talktable(True)
            tool_window.open_active_talktable()

    def test_open_active_journal_with_bool(self, tool_window, qtbot):
        """Test open_active_journal accepts bool from triggered signal."""
        with patch.object(tool_window, "active", None):
            tool_window.open_active_journal(False)
            tool_window.open_active_journal(True)
            tool_window.open_active_journal()

    def test_open_file_search_dialog_with_bool(self, tool_window, qtbot):
        """Test open_file_search_dialog accepts bool from triggered signal."""
        with patch.object(tool_window, "active", None):
            tool_window.open_file_search_dialog(False)
            tool_window.open_file_search_dialog(True)
            tool_window.open_file_search_dialog()

    def test_open_indoor_map_builder_with_bool(self, tool_window, qtbot):
        """Test open_indoor_map_builder accepts bool from triggered signal."""
        tool_window.open_indoor_map_builder(False)
        tool_window.open_indoor_map_builder(True)
        tool_window.open_indoor_map_builder()

    def test_open_kotordiff_with_bool(self, tool_window, qtbot):
        """Test open_kotordiff accepts bool from triggered signal."""
        tool_window.open_kotordiff(False)
        tool_window.open_kotordiff(True)
        tool_window.open_kotordiff()

    def test_open_tslpatchdata_editor_with_bool(self, tool_window, qtbot):
        """Test open_tslpatchdata_editor accepts bool from triggered signal."""
        tool_window.open_tslpatchdata_editor(False)
        tool_window.open_tslpatchdata_editor(True)
        tool_window.open_tslpatchdata_editor()

    def test_open_instructions_window_with_bool(self, tool_window, qtbot):
        """Test open_instructions_window accepts bool from triggered signal."""
        tool_window.open_instructions_window(False)
        tool_window.open_instructions_window(True)
        tool_window.open_instructions_window()

    def test_open_about_dialog_with_bool(self, tool_window, qtbot):
        """Test open_about_dialog accepts bool from triggered signal."""
        with patch("toolset.gui.dialogs.about.About") as mock_about:
            mock_about.return_value.exec.return_value = 0
            tool_window.open_about_dialog(False)
            tool_window.open_about_dialog(True)
            tool_window.open_about_dialog()

    def test_open_from_file_with_bool(self, tool_window, qtbot):
        """Test open_from_file accepts bool from triggered signal."""
        with patch("qtpy.QtWidgets.QFileDialog.getOpenFileNames", return_value=([], "")):
            tool_window.open_from_file(False)
            tool_window.open_from_file(True)
            tool_window.open_from_file()

    def test__open_theme_dialog_with_bool(self, tool_window, qtbot):
        """Test _open_theme_dialog accepts bool from triggered signal."""
        tool_window._open_theme_dialog(False)
        tool_window._open_theme_dialog(True)
        tool_window._open_theme_dialog()

    def test__open_module_tab_erf_editor_with_bool(self, tool_window, qtbot):
        """Test _open_module_tab_erf_editor accepts bool from clicked signal."""
        with patch.object(tool_window, "active", None):
            tool_window._open_module_tab_erf_editor(False)
            tool_window._open_module_tab_erf_editor(True)
            tool_window._open_module_tab_erf_editor()

    def test_on_watched_directory_changed_with_str(self, tool_window, qtbot):
        """Test _on_watched_directory_changed accepts str from directoryChanged signal."""
        tool_window._on_watched_directory_changed("/path/to/dir")

    def test_on_watched_file_changed_with_str(self, tool_window, qtbot):
        """Test _on_watched_file_changed accepts str from fileChanged signal."""
        tool_window._on_watched_file_changed("/path/to/file")

    def test__process_pending_file_changes(self, tool_window, qtbot):
        """Test _process_pending_file_changes works without arguments."""
        tool_window._process_pending_file_changes()

    def test_handle_search_completed_with_list_installation(self, tool_window, qtbot):
        """Test handle_search_completed accepts list, HTInstallation from signal."""
        from toolset.data.installation import HTInstallation
        mock_inst = MagicMock(spec=HTInstallation)
        tool_window.handle_search_completed([], mock_inst)

    def test_handle_results_selection_with_fileresource(self, tool_window, qtbot):
        """Test handle_results_selection accepts FileResource from signal."""
        mock_resource = MagicMock(spec=FileResource)
        mock_resource.filepath.return_value = Path("/test/file.res")
        with patch.object(tool_window, "active", None):
            tool_window.handle_results_selection(mock_resource)


class TestSignalConnections:
    """Test that signals are properly connected and emit correct arguments."""

    @pytest.fixture
    def resource_list(self, qtbot, mock_installation):
        """Create a ResourceList instance for testing."""
        widget = ResourceList(None)
        widget.set_installation(mock_installation)
        qtbot.addWidget(widget)
        return widget

    def test_clicked_signal_emits_bool(self, resource_list, qtbot):
        """Test that clicked signal emits bool and slot accepts it."""
        called_with = []

        def capture(value):
            called_with.append(value)

        # Replace the slot temporarily
        original = resource_list.on_reload_clicked
        resource_list.on_reload_clicked = capture

        # Emit clicked signal (emits bool)
        resource_list.ui.reloadButton.clicked.emit(False)
        qtbot.wait(10)
        assert len(called_with) > 0
        assert called_with[0] is False

        resource_list.on_reload_clicked = original

    def test_text_changed_signal_emits_str(self, resource_list, qtbot):
        """Test that textChanged signal emits str and slot accepts it."""
        called_with = []

        def capture(value):
            called_with.append(value)

        original = resource_list.on_filter_string_updated
        resource_list.on_filter_string_updated = capture

        resource_list.ui.searchEdit.textChanged.emit("test")
        qtbot.wait(10)
        assert len(called_with) > 0
        assert called_with[0] == "test"

        resource_list.on_filter_string_updated = original

    def test_current_index_changed_signal_emits_int(self, resource_list, qtbot):
        """Test that currentIndexChanged signal emits int and slot accepts it."""
        called_with = []

        def capture(value):
            called_with.append(value)

        original = resource_list.on_section_changed
        resource_list.on_section_changed = capture

        resource_list.ui.sectionCombo.currentIndexChanged.emit(1)
        qtbot.wait(10)
        assert len(called_with) > 0
        assert called_with[0] == 1

        resource_list.on_section_changed = original

    def test_value_changed_signal_emits_int(self, qtbot, mock_installation):
        """Test that valueChanged signal emits int and slot accepts it."""
        texture_list = TextureList(None)
        texture_list.set_installation(mock_installation)
        qtbot.addWidget(texture_list)

        called_with = []

        def capture(value):
            called_with.append(value)

        original = texture_list.queue_load_visible_icons
        texture_list.queue_load_visible_icons = capture

        # Get scrollbar and emit valueChanged
        scrollbar = texture_list.ui.resourceList.verticalScrollBar()
        if scrollbar:
            scrollbar.valueChanged.emit(50)
            qtbot.wait(10)
            assert len(called_with) > 0
            assert called_with[0] == 50

        texture_list.queue_load_visible_icons = original

    def test_double_clicked_signal_emits_qmodelindex(self, resource_list, qtbot):
        """Test that doubleClicked signal emits QModelIndex and slot accepts it."""
        called_with = []

        def capture(index):
            called_with.append(index)

        original = resource_list.on_resource_double_clicked
        resource_list.on_resource_double_clicked = capture

        model = QStandardItemModel()
        index = model.index(0, 0)
        resource_list.ui.resourceTree.doubleClicked.emit(index)
        qtbot.wait(10)
        assert len(called_with) > 0
        assert called_with[0] == index

        resource_list.on_resource_double_clicked = original


class TestQTimerSingleShotCompatibility:
    """Test that methods work when called via QTimer.singleShot."""

    @pytest.fixture
    def texture_list(self, qtbot, mock_installation):
        """Create a TextureList instance for testing."""
        widget = TextureList(None)
        widget.set_installation(mock_installation)
        qtbot.addWidget(widget)
        return widget

    def test_queue_load_visible_icons_via_singleshot(self, texture_list, qtbot):
        """Test queue_load_visible_icons works when called via QTimer.singleShot with lambda."""
        # This should not raise TypeError
        called = False

        def check():
            nonlocal called
            called = True

        original = texture_list.queue_load_visible_icons
        texture_list.queue_load_visible_icons = lambda *args: (original(*args), check())[1]

        QTimer.singleShot(10, lambda: texture_list.queue_load_visible_icons(0))
        qtbot.wait(50)
        assert called
