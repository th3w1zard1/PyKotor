import pytest
from qtpy.QtWidgets import QWidget, QDialog
from toolset.data.installation import HTInstallation
from unittest.mock import MagicMock, patch

# Import dialogs to test
from toolset.gui.dialogs.extract_options import ExtractOptionsDialog
from toolset.gui.dialogs.select_module import SelectModuleDialog
from toolset.gui.dialogs.indoor_settings import IndoorMapSettings

def test_extract_options_dialog(qtbot):
    """Test ExtractOptionsDialog."""
    parent = QWidget()
    dialog = ExtractOptionsDialog(parent)
    qtbot.addWidget(dialog)
    dialog.show()
    
    assert dialog.isVisible()
    
    # Test checkbox toggles - use the correct attribute names
    dialog.ui.tpcDecompileCheckbox.setChecked(True)
    qtbot.wait(10)  # Ensure Qt processes the checkbox state change in headless mode
    assert dialog.tpc_decompile is True
    
    dialog.ui.tpcDecompileCheckbox.setChecked(False)
    qtbot.wait(10)  # Ensure Qt processes the checkbox state change in headless mode
    assert dialog.tpc_decompile is False
    
    # Test TPC TXI extraction checkbox
    dialog.ui.tpcTxiCheckbox.setChecked(True)
    qtbot.wait(10)  # Ensure Qt processes the checkbox state change in headless mode
    assert dialog.tpc_extract_txi is True
    
    dialog.ui.tpcTxiCheckbox.setChecked(False)
    qtbot.wait(10)  # Ensure Qt processes the checkbox state change in headless mode
    assert dialog.tpc_extract_txi is False
    
    # Test MDL decompile checkbox
    dialog.ui.mdlDecompileCheckbox.setChecked(True)
    qtbot.wait(10)  # Ensure Qt processes the checkbox state change in headless mode
    assert dialog.mdl_decompile is True
    
    # Test MDL texture extraction checkbox
    dialog.ui.mdlTexturesCheckbox.setChecked(True)
    qtbot.wait(10)  # Ensure Qt processes the checkbox state change in headless mode
    assert dialog.mdl_extract_textures is True

def test_select_module_dialog(qtbot, installation: HTInstallation):
    """Test SelectModuleDialog."""
    parent = QWidget()
    
    # Mock modules list
    installation.module_names = lambda use_hardcoded=True: {"test_mod": "Test Module", "other_mod": "Other Module"}
    
    dialog = SelectModuleDialog(parent, installation)
    qtbot.addWidget(dialog)
    dialog.show()
    
    assert dialog.isVisible()
    assert dialog.ui.moduleList.count() >= 2
    
    # Filter functionality
    dialog.ui.filterEdit.setText("Other")
    # Check if list filtered (if implemented)
    # Assuming QListWidget or similar
    
    # Select item
    # dialog.ui.moduleList.setCurrentRow(0)
    # assert dialog.selected_module() == ...

def test_indoor_settings_dialog(qtbot, installation: HTInstallation):
    """Test IndoorMapSettings."""
    from toolset.data.indoormap import IndoorMap
    from toolset.data.indoorkit import Kit
    
    parent = QWidget()
    indoor_map = IndoorMap()
    kits: list[Kit] = []
    dialog = IndoorMapSettings(parent, installation, indoor_map, kits)
    qtbot.addWidget(dialog)
    dialog.show()
    
    assert dialog.isVisible()
    # Test generic settings widgets

def test_inventory_editor(qtbot, installation: HTInstallation):
    """Test InventoryEditor."""
    from toolset.gui.dialogs.inventory import InventoryEditor
    from pykotor.extract.capsule import LazyCapsule
    
    # Mock parent and data
    parent = QWidget()
    capsules = [] # No capsules for now
    inventory = []
    equipment = []
    
    dialog = InventoryEditor(parent, installation, capsules, [], inventory, equipment, droid=False)
    qtbot.addWidget(dialog)
    dialog.show()
    
    assert dialog.isVisible()
    # Check for inventory lists
    assert hasattr(dialog.ui, "inventoryList")
    assert hasattr(dialog.ui, "equipmentList")
    
    # Test add/remove logic if possible without heavy data
    # Usually requires drag/drop or button clicks


def test_file_selection_window_resize_to_content_no_qdesktopwidget_import(qtbot, installation: HTInstallation):
    """Test that FileSelectionWindow.resize_to_content() doesn't try to import QDesktopWidget.
    
    This test ensures the fix for the ImportError: cannot import name 'QDesktopWidget' from 'qtpy.QtGui'
    when using Qt6. The method should use QApplication.primaryScreen() instead, which works for both Qt5 and Qt6.
    """
    from toolset.gui.dialogs.load_from_location_result import FileSelectionWindow
    from pykotor.extract.file import FileResource
    from unittest.mock import MagicMock, patch
    import qtpy
    
    # Create a mock FileResource for testing
    mock_resource = MagicMock(spec=FileResource)
    mock_resource.identifier.return_value = "test_resource"
    mock_resource.filepath.return_value = installation.path() / "test.utc"
    mock_resource.offset.return_value = 0
    mock_resource.size.return_value = 100
    mock_resource.filename.return_value = "test.utc"
    
    # Create FileSelectionWindow with empty resources list
    search_results = []
    window = FileSelectionWindow(search_results, installation)
    qtbot.addWidget(window)
    
    # Add a mock resource to the table
    window.resource_table.resources = [mock_resource]
    window.resource_table.setRowCount(1)
    window.resource_table.setColumnCount(4)
    
    # Mock the table methods needed for resize_to_content
    window.resource_table.columnCount = MagicMock(return_value=4)
    window.resource_table.columnWidth = MagicMock(return_value=100)
    window.resource_table.verticalHeader = MagicMock()
    mock_vert_header = MagicMock()
    mock_vert_header.width.return_value = 50
    window.resource_table.verticalHeader.return_value = mock_vert_header
    
    # Ensure QApplication.primaryScreen() is available
    from qtpy.QtWidgets import QApplication
    app = QApplication.instance()
    assert app is not None, "QApplication instance should exist"
    
    # The key test: resize_to_content should NOT try to import QDesktopWidget
    # It should use QApplication.primaryScreen() instead
    try:
        # This should work without importing QDesktopWidget
        window.resize_to_content()
        
        # If we get here, the method worked without trying to import QDesktopWidget
        # Verify the window was resized
        assert window.width() > 0
        assert window.height() > 0
        
    except ImportError as e:
        if "QDesktopWidget" in str(e):
            pytest.fail(f"resize_to_content() tried to import QDesktopWidget, which doesn't exist in Qt6: {e}")
        raise


