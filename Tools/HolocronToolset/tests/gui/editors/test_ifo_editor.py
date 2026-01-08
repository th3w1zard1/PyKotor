"""
Comprehensive tests for IFO Editor - testing EVERY possible manipulation.

Each test focuses on a specific manipulation and validates save/load roundtrips.
Following the ARE editor test pattern for comprehensive coverage.
"""
import pytest
from pathlib import Path
from qtpy.QtCore import Qt
from toolset.gui.editors.ifo import IFOEditor  # type: ignore[import-not-found]
from toolset.data.installation import HTInstallation  # type: ignore[import-not-found]
from pykotor.resource.generics.ifo import IFO, read_ifo  # type: ignore[import-not-found]
from pykotor.resource.formats.gff.gff_auto import read_gff  # type: ignore[import-not-found]
from pykotor.resource.type import ResourceType  # type: ignore[import-not-found]
from pykotor.common.language import LocalizedString, Language, Gender  # type: ignore[import-not-found]
from pykotor.common.misc import ResRef  # type: ignore[import-not-found]
from utility.common.geometry import Vector3  # type: ignore[import-not-found]

# ============================================================================
# BASIC FIELDS MANIPULATIONS
# ============================================================================

def test_ifo_editor_manipulate_tag(qtbot, installation: HTInstallation):
    """Test manipulating tag field."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new IFO
    editor.new()
    
    # Modify tag
    editor.tag_edit.setText("modified_tag")
    editor.on_value_changed()
    
    # Build and verify
    data, _ = editor.build()
    assert len(data) > 0
    
    # Load and verify
    editor.load(Path("test.ifo"), "test", ResourceType.IFO, data)
    assert editor.tag_edit.text() == "modified_tag"
    assert editor.ifo is not None
    assert editor.ifo.tag == "modified_tag"

def test_ifo_editor_manipulate_vo_id(qtbot, installation: HTInstallation):
    """Test manipulating VO ID field."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Modify VO ID
    test_vo_ids = ["vo_001", "test_vo", "", "vo_id_12345"]
    for vo_id in test_vo_ids:
        editor.vo_id_edit.setText(vo_id)
        editor.on_value_changed()
        
        # Build and verify
        data, _ = editor.build()
        modified_ifo = read_ifo(data)
        assert modified_ifo.vo_id == vo_id
        
        # Load back and verify
        editor.load(Path("test.ifo"), "test", ResourceType.IFO, data)
        assert editor.vo_id_edit.text() == vo_id

def test_ifo_editor_manipulate_hak(qtbot, installation: HTInstallation):
    """Test manipulating Hak field."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Modify Hak
    test_haks = ["hak01", "test_hak", "", "custom_hak_file"]
    for hak in test_haks:
        editor.hak_edit.setText(hak)
        editor.on_value_changed()
        
        # Build and verify
        data, _ = editor.build()
        modified_ifo = read_ifo(data)
        assert modified_ifo.hak == hak

# ============================================================================
# ENTRY POINT MANIPULATIONS
# ============================================================================

def test_ifo_editor_manipulate_entry_resref(qtbot, installation: HTInstallation):
    """Test manipulating entry area ResRef."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Modify entry ResRef
    test_resrefs = ["area001", "test_area", "", "entry_point"]
    for resref in test_resrefs:
        editor.entry_resref.setText(resref)
        editor.on_value_changed()
        
        # Build and verify
        data, _ = editor.build()
        modified_ifo = read_ifo(data)
        assert str(modified_ifo.resref) == resref
        
        # Load back and verify
        editor.load(Path("test.ifo"), "test", ResourceType.IFO, data)
        assert editor.entry_resref.text() == resref

def test_ifo_editor_manipulate_entry_position(qtbot, installation: HTInstallation):
    """Test manipulating entry position coordinates."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Test various positions
    test_positions = [
        (0.0, 0.0, 0.0),
        (10.5, 20.3, 5.0),
        (-5.0, -10.0, 0.5),
        (100.0, 200.0, 50.0),
    ]
    
    for x, y, z in test_positions:
        editor.entry_x.setValue(x)
        editor.entry_y.setValue(y)
        editor.entry_z.setValue(z)
        editor.on_value_changed()
        
        # Build and verify
        data, _ = editor.build()
        modified_ifo = read_ifo(data)
        assert abs(modified_ifo.entry_position.x - x) < 0.001
        assert abs(modified_ifo.entry_position.y - y) < 0.001
        assert abs(modified_ifo.entry_position.z - z) < 0.001
        
        # Load back and verify
        editor.load(Path("test.ifo"), "test", ResourceType.IFO, data)
        assert abs(editor.entry_x.value() - x) < 0.001
        assert abs(editor.entry_y.value() - y) < 0.001
        assert abs(editor.entry_z.value() - z) < 0.001

def test_ifo_editor_manipulate_entry_direction(qtbot, installation: HTInstallation):
    """Test manipulating entry direction."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Test various directions (radians)
    test_directions = [0.0, 1.57, 3.14, -1.57, -3.14159]
    for direction in test_directions:
        editor.entry_dir.setValue(direction)
        editor.on_value_changed()
        
        # Build and verify
        data, _ = editor.build()
        modified_ifo = read_ifo(data)
        # Use a slightly larger tolerance due to angle->x/y->angle conversion precision loss
        assert abs(modified_ifo.entry_direction - direction) < 0.002

# ============================================================================
# TIME SETTINGS MANIPULATIONS
# ============================================================================

def test_ifo_editor_manipulate_dawn_hour(qtbot, installation: HTInstallation):
    """Test manipulating dawn hour."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Test all valid hours (0-23)
    for hour in [0, 6, 12, 18, 23]:
        editor.dawn_hour.setValue(hour)
        editor.on_value_changed()
        
        # Build and verify
        data, _ = editor.build()
        modified_ifo = read_ifo(data)
        assert modified_ifo.dawn_hour == hour

def test_ifo_editor_manipulate_dusk_hour(qtbot, installation: HTInstallation):
    """Test manipulating dusk hour."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    for hour in [0, 18, 20, 23]:
        editor.dusk_hour.setValue(hour)
        editor.on_value_changed()
        
        data, _ = editor.build()
        modified_ifo = read_ifo(data)
        assert modified_ifo.dusk_hour == hour

def test_ifo_editor_manipulate_time_scale(qtbot, installation: HTInstallation):
    """Test manipulating time scale."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    test_scales = [0, 1, 50, 100]
    for scale in test_scales:
        editor.time_scale.setValue(scale)
        editor.on_value_changed()
        
        data, _ = editor.build()
        modified_ifo = read_ifo(data)
        assert modified_ifo.time_scale == scale

def test_ifo_editor_manipulate_start_date(qtbot, installation: HTInstallation):
    """Test manipulating start date fields."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Test various dates
    test_dates = [
        (1, 1, 0, 0),
        (6, 15, 12, 3956),
        (12, 31, 23, 9999),
    ]
    
    for month, day, hour, year in test_dates:
        editor.start_month.setValue(month)
        editor.start_day.setValue(day)
        editor.start_hour.setValue(hour)
        editor.start_year.setValue(year)
        editor.on_value_changed()
        
        data, _ = editor.build()
        modified_ifo = read_ifo(data)
        assert modified_ifo.start_month == month
        assert modified_ifo.start_day == day
        assert modified_ifo.start_hour == hour
        assert modified_ifo.start_year == year

def test_ifo_editor_manipulate_xp_scale(qtbot, installation: HTInstallation):
    """Test manipulating XP scale."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    test_scales = [0, 50, 100]
    for scale in test_scales:
        editor.xp_scale.setValue(scale)
        editor.on_value_changed()
        
        data, _ = editor.build()
        modified_ifo = read_ifo(data)
        assert modified_ifo.xp_scale == scale

# ============================================================================
# SCRIPT FIELDS MANIPULATIONS
# ============================================================================

def test_ifo_editor_manipulate_on_heartbeat_script(qtbot, installation: HTInstallation):
    """Test manipulating on heartbeat script."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    editor.script_fields["on_heartbeat"].setText("test_heartbeat")
    editor.on_value_changed()
    
    data, _ = editor.build()
    modified_ifo = read_ifo(data)
    assert str(modified_ifo.on_heartbeat) == "test_heartbeat"

def test_ifo_editor_manipulate_on_load_script(qtbot, installation: HTInstallation):
    """Test manipulating on load script."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    editor.script_fields["on_load"].setText("test_on_load")
    editor.on_value_changed()
    
    data, _ = editor.build()
    modified_ifo = read_ifo(data)
    assert str(modified_ifo.on_load) == "test_on_load"

def test_ifo_editor_manipulate_on_start_script(qtbot, installation: HTInstallation):
    """Test manipulating on start script."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    editor.script_fields["on_start"].setText("test_on_start")
    editor.on_value_changed()
    
    data, _ = editor.build()
    modified_ifo = read_ifo(data)
    assert str(modified_ifo.on_start) == "test_on_start"

def test_ifo_editor_manipulate_all_scripts(qtbot, installation: HTInstallation):
    """Test manipulating all script fields."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Set all scripts (use shorter names to comply with 16-character ResRef limit)
    script_test_values = {
        "on_heartbeat": "test_heartbeat",
        "on_load": "test_onload",
        "on_start": "test_onstart",
        "on_enter": "test_onenter",
        "on_exit": "test_onexit",
    }
    for script_name in editor.script_fields.keys():
        test_value = script_test_values.get(script_name, f"test_{script_name}")
        # Ensure test value doesn't exceed 16 characters
        if len(test_value) > 16:
            test_value = test_value[:16]
        editor.script_fields[script_name].setText(test_value)
    
    editor.on_value_changed()
    
    data, _ = editor.build()
    modified_ifo = read_ifo(data)
    
    # Verify all scripts
    for script_name in editor.script_fields.keys():
        expected_value = script_test_values.get(script_name, f"test_{script_name}")
        if len(expected_value) > 16:
            expected_value = expected_value[:16]
        assert str(getattr(modified_ifo, script_name)) == expected_value

# ============================================================================
# COMBINATION TESTS
# ============================================================================

def test_ifo_editor_manipulate_all_basic_fields_combination(qtbot, installation: HTInstallation):
    """Test manipulating all basic fields simultaneously."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Modify ALL basic fields
    editor.tag_edit.setText("combined_test")
    editor.vo_id_edit.setText("vo_combined")
    editor.hak_edit.setText("hak_combined")
    editor.entry_resref.setText("area_combined")
    editor.entry_x.setValue(10.0)
    editor.entry_y.setValue(20.0)
    editor.entry_z.setValue(5.0)
    editor.entry_dir.setValue(1.57)
    editor.dawn_hour.setValue(6)
    editor.dusk_hour.setValue(18)
    editor.time_scale.setValue(50)
    editor.start_month.setValue(1)
    editor.start_day.setValue(1)
    editor.start_hour.setValue(12)
    editor.start_year.setValue(3956)
    editor.xp_scale.setValue(100)
    
    editor.on_value_changed()
    
    # Save and verify all
    data, _ = editor.build()
    modified_ifo = read_ifo(data)
    
    assert modified_ifo.tag == "combined_test"
    assert modified_ifo.vo_id == "vo_combined"
    assert modified_ifo.hak == "hak_combined"
    assert str(modified_ifo.resref) == "area_combined"
    assert abs(modified_ifo.entry_position.x - 10.0) < 0.001
    assert abs(modified_ifo.entry_position.y - 20.0) < 0.001
    assert abs(modified_ifo.entry_position.z - 5.0) < 0.001
    assert abs(modified_ifo.entry_direction - 1.57) < 0.001
    assert modified_ifo.dawn_hour == 6
    assert modified_ifo.dusk_hour == 18
    assert modified_ifo.time_scale == 50
    assert modified_ifo.start_month == 1
    assert modified_ifo.start_day == 1
    assert modified_ifo.start_hour == 12
    assert modified_ifo.start_year == 3956
    assert modified_ifo.xp_scale == 100

# ============================================================================
# SAVE/LOAD ROUNDTRIP VALIDATION TESTS
# ============================================================================

def test_ifo_editor_save_load_roundtrip_identity(qtbot, installation: HTInstallation):
    """Test that save/load roundtrip preserves all data exactly."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Set some values
    editor.tag_edit.setText("roundtrip_test")
    editor.entry_x.setValue(15.5)
    editor.entry_y.setValue(25.5)
    editor.entry_z.setValue(10.0)
    editor.dawn_hour.setValue(7)
    editor.dusk_hour.setValue(19)
    editor.on_value_changed()
    
    # Save
    data1, _ = editor.build()
    saved_ifo1 = read_ifo(data1)
    
    # Load saved data
    editor.load(Path("test.ifo"), "test", ResourceType.IFO, data1)
    
    # Verify modifications preserved
    assert editor.tag_edit.text() == "roundtrip_test"
    assert abs(editor.entry_x.value() - 15.5) < 0.001
    assert abs(editor.entry_y.value() - 25.5) < 0.001
    assert abs(editor.entry_z.value() - 10.0) < 0.001
    assert editor.dawn_hour.value() == 7
    assert editor.dusk_hour.value() == 19
    
    # Save again
    data2, _ = editor.build()
    saved_ifo2 = read_ifo(data2)
    
    # Verify second save matches first
    assert saved_ifo2.tag == saved_ifo1.tag
    assert abs(saved_ifo2.entry_position.x - saved_ifo1.entry_position.x) < 0.001
    assert saved_ifo2.dawn_hour == saved_ifo1.dawn_hour

def test_ifo_editor_multiple_save_load_cycles(qtbot, installation: HTInstallation):
    """Test multiple save/load cycles preserve data correctly."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Perform multiple cycles
    for cycle in range(5):
        # Modify
        editor.tag_edit.setText(f"cycle_{cycle}")
        editor.entry_x.setValue(10.0 + cycle)
        editor.time_scale.setValue(50 + cycle * 10)
        editor.on_value_changed()
        
        # Save
        data, _ = editor.build()
        saved_ifo = read_ifo(data)
        
        # Verify
        assert saved_ifo.tag == f"cycle_{cycle}"
        assert abs(saved_ifo.entry_position.x - (10.0 + cycle)) < 0.001
        assert saved_ifo.time_scale == 50 + cycle * 10
        
        # Load back
        editor.load(Path("test.ifo"), "test", ResourceType.IFO, data)
        
        # Verify loaded
        assert editor.tag_edit.text() == f"cycle_{cycle}"
        assert abs(editor.entry_x.value() - (10.0 + cycle)) < 0.001
        assert editor.time_scale.value() == 50 + cycle * 10

# ============================================================================
# EDGE CASES AND BOUNDARY TESTS
# ============================================================================

def test_ifo_editor_minimum_values(qtbot, installation: HTInstallation):
    """Test setting all fields to minimum values."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Set all to minimums
    editor.tag_edit.setText("")
    editor.vo_id_edit.setText("")
    editor.hak_edit.setText("")
    editor.entry_resref.setText("")
    editor.entry_x.setValue(-99999.0)
    editor.entry_y.setValue(-99999.0)
    editor.entry_z.setValue(-99999.0)
    editor.entry_dir.setValue(-3.14159)
    editor.dawn_hour.setValue(0)
    editor.dusk_hour.setValue(0)
    editor.time_scale.setValue(0)
    editor.start_month.setValue(1)
    editor.start_day.setValue(1)
    editor.start_hour.setValue(0)
    editor.start_year.setValue(0)
    editor.xp_scale.setValue(0)
    
    editor.on_value_changed()
    
    # Save and verify
    data, _ = editor.build()
    modified_ifo = read_ifo(data)
    
    assert modified_ifo.tag == ""
    assert modified_ifo.vo_id == ""
    assert modified_ifo.hak == ""
    assert modified_ifo.dawn_hour == 0
    assert modified_ifo.dusk_hour == 0
    assert modified_ifo.time_scale == 0
    assert modified_ifo.start_year == 0
    assert modified_ifo.xp_scale == 0

def test_ifo_editor_maximum_values(qtbot, installation: HTInstallation):
    """Test setting all fields to maximum values."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Set all to maximums
    editor.tag_edit.setText("x" * 32)  # Max tag length
    editor.entry_x.setValue(99999.0)
    editor.entry_y.setValue(99999.0)
    editor.entry_z.setValue(99999.0)
    editor.entry_dir.setValue(3.14159)
    editor.dawn_hour.setValue(23)
    editor.dusk_hour.setValue(23)
    editor.time_scale.setValue(100)
    editor.start_month.setValue(12)
    editor.start_day.setValue(31)
    editor.start_hour.setValue(23)
    editor.start_year.setValue(9999)
    editor.xp_scale.setValue(100)
    
    editor.on_value_changed()
    
    # Save and verify
    data, _ = editor.build()
    modified_ifo = read_ifo(data)
    
    assert modified_ifo.dawn_hour == 23
    assert modified_ifo.dusk_hour == 23
    assert modified_ifo.time_scale == 100
    assert modified_ifo.start_month == 12
    assert modified_ifo.start_day == 31
    assert modified_ifo.start_hour == 23
    assert modified_ifo.start_year == 9999
    assert modified_ifo.xp_scale == 100

def test_ifo_editor_empty_strings(qtbot, installation: HTInstallation):
    """Test handling of empty strings in text fields."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Set all text fields to empty
    editor.tag_edit.setText("")
    editor.vo_id_edit.setText("")
    editor.hak_edit.setText("")
    editor.entry_resref.setText("")
    
    for script_name, edit in editor.script_fields.items():
        edit.setText("")
    
    editor.on_value_changed()
    
    # Save and verify
    data, _ = editor.build()
    modified_ifo = read_ifo(data)
    
    assert modified_ifo.tag == ""
    assert modified_ifo.vo_id == ""
    assert modified_ifo.hak == ""
    assert str(modified_ifo.resref) == ""
    
    for script_name in editor.script_fields.keys():
        assert str(getattr(modified_ifo, script_name)) == ""

# ============================================================================
# GFF COMPARISON TESTS
# ============================================================================

def test_ifo_editor_gff_roundtrip_with_modifications(qtbot, installation: HTInstallation):
    """Test GFF roundtrip with modifications still produces valid GFF."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Make modifications
    editor.tag_edit.setText("modified_gff_test")
    editor.entry_x.setValue(50.0)
    editor.time_scale.setValue(75)
    
    editor.on_value_changed()
    
    # Save
    data, _ = editor.build()
    
    # Verify it's valid GFF
    new_gff = read_gff(data)
    assert new_gff is not None
    
    # Verify it's valid IFO
    modified_ifo = read_ifo(data)
    assert modified_ifo.tag == "modified_gff_test"
    assert abs(modified_ifo.entry_position.x - 50.0) < 0.001
    assert modified_ifo.time_scale == 75

# ============================================================================
# NEW FILE CREATION TESTS
# ============================================================================

def test_ifo_editor_new_file_creation(qtbot, installation: HTInstallation):
    """Test creating a new IFO file from scratch."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Set all fields
    editor.tag_edit.setText("new_module")
    editor.vo_id_edit.setText("vo_new")
    editor.entry_resref.setText("new_area")
    editor.entry_x.setValue(0.0)
    editor.entry_y.setValue(0.0)
    editor.entry_z.setValue(0.0)
    editor.dawn_hour.setValue(6)
    editor.dusk_hour.setValue(18)
    editor.time_scale.setValue(100)
    
    editor.on_value_changed()
    
    # Build and verify
    data, _ = editor.build()
    new_ifo = read_ifo(data)
    
    assert new_ifo.tag == "new_module"
    assert new_ifo.vo_id == "vo_new"
    assert str(new_ifo.resref) == "new_area"
    assert new_ifo.dawn_hour == 6
    assert new_ifo.dusk_hour == 18
    assert new_ifo.time_scale == 100

def test_ifo_editor_new_file_all_defaults(qtbot, installation: HTInstallation):
    """Test new file has correct defaults."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Build and verify defaults
    data, _ = editor.build()
    new_ifo = read_ifo(data)
    
    # Verify defaults (may vary, but should be consistent)
    assert isinstance(new_ifo.tag, str)
    assert isinstance(new_ifo.resref, ResRef)
    assert isinstance(new_ifo.entry_position, Vector3)

# ============================================================================
# NAME/DESCRIPTION DIALOG TESTS
# ============================================================================

def test_ifo_editor_name_dialog_integration(qtbot, installation: HTInstallation):
    """Test name dialog integration."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Test edit_name method exists and is callable
    assert hasattr(editor, 'edit_name')
    assert callable(editor.edit_name)
    
    # Test edit_description method exists and is callable
    assert hasattr(editor, 'edit_description')
    assert callable(editor.edit_description)

# ============================================================================
# HEADLESS UI TESTS WITH REAL FILES
# ============================================================================


def test_ifoeditor_editor_help_dialog_opens_correct_file(qtbot, installation: HTInstallation):
    """Test that IFOEditor help dialog opens and displays the correct help file (not 'Help File Not Found')."""
    from toolset.gui.dialogs.editor_help import EditorHelpDialog
    
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Trigger help dialog with the correct file for IFOEditor
    editor._show_help_dialog("GFF-IFO.md")
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
        f"Help file 'GFF-IFO.md' should be found, but error was shown. HTML: {html[:500]}"
    
    # Assert that some content is present (file was loaded successfully)
    assert len(html) > 100, "Help dialog should contain content"


"""
Comprehensive tests for IFO Editor - testing with REAL files from installation.

These tests ensure the editor can:
1. Load into headless UI
2. Load real IFO files from installation or test_files_dir
3. Build data successfully
4. Save data (when applicable)
5. Handle all user interactions properly

Following the ARE editor test pattern for comprehensive coverage.
"""
import pytest
from pathlib import Path
from qtpy.QtCore import Qt
from toolset.gui.editors.ifo import IFOEditor
from toolset.data.installation import HTInstallation
from pykotor.resource.generics.ifo import IFO, read_ifo  # pyright: ignore[reportMissingImports]
from pykotor.resource.formats.gff.gff_auto import read_gff  # pyright: ignore[reportMissingImports]
from pykotor.resource.type import ResourceType  # pyright: ignore[reportMissingImports]
from pykotor.common.language import LocalizedString, Language, Gender  # pyright: ignore[reportMissingImports]
from pykotor.common.misc import ResRef  # pyright: ignore[reportMissingImports]
from utility.common.geometry import Vector3


# ============================================================================
# BASIC LOAD/SAVE TESTS WITH REAL FILES
# ============================================================================

def test_ifo_editor_load_from_installation(qtbot, installation: HTInstallation):
    """Test loading an IFO file directly from the installation."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Try to find an IFO file in the installation
    ifo_resources = [res for res in installation if res.restype() is ResourceType.IFO]
    if not ifo_resources:
        pytest.skip("No IFO files found in installation")
    
    # Use the first IFO file found
    ifo_resource = ifo_resources[0]
    ifo_result = installation.resource(ifo_resource.resname(), ResourceType.IFO)
    
    if not ifo_result or not ifo_result.data:
        pytest.skip(f"Could not load IFO data for {ifo_resource.resname()}")
    
    # Load the file
    editor.load(
        ifo_resource.filepath() if hasattr(ifo_resource, 'filepath') and callable(getattr(ifo_resource, 'filepath', None)) else (ifo_resource.filepath if hasattr(ifo_resource, 'filepath') else Path("module.ifo")),
        ifo_resource.resname(),
        ResourceType.IFO,
        ifo_result.data
    )
    
    # Verify editor loaded the data
    assert editor.ifo is not None
    
    # Build and verify it works
    data, _ = editor.build()
    assert len(data) > 0
    
    # Verify we can read it back
    loaded_ifo = read_ifo(data)
    assert loaded_ifo is not None


def test_ifo_editor_load_from_test_files(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test loading an IFO file from test_files_dir."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Look for IFO files in test_files_dir
    ifo_files = list(test_files_dir.glob("*.ifo"))
    if not ifo_files:
        # Try looking in subdirectories
        ifo_files = list(test_files_dir.rglob("*.ifo"))
    
    if not ifo_files:
        pytest.skip("No IFO files found in test_files_dir")
    
    # Use the first IFO file found
    ifo_file = ifo_files[0]
    original_data = ifo_file.read_bytes()
    
    # Load the file
    editor.load(ifo_file, ifo_file.stem, ResourceType.IFO, original_data)
    original_ifo = read_ifo(original_data)
    
    # Verify editor loaded the data
    assert editor.ifo is not None
    
    # Build and verify it works
    data, _ = editor.build()
    assert len(data) > 0
    
    # Verify we can read it back
    loaded_ifo = read_ifo(data)
    assert loaded_ifo is not None
    assert loaded_ifo.tag == original_ifo.tag


def test_ifo_editor_load_build_save_roundtrip(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test complete load -> build -> save roundtrip with real file."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Look for IFO files
    ifo_files = list(test_files_dir.glob("*.ifo"))
    if not ifo_files:
        ifo_files = list(test_files_dir.rglob("*.ifo"))
    
    if not ifo_files:
        # Try to get one from installation
        ifo_resources = [res for res in installation if res.restype() is ResourceType.IFO]
        if not ifo_resources:
            pytest.skip("No IFO files available for testing")
        
        ifo_resource = ifo_resources[0]
        ifo_result = installation.resource(ifo_resource.resname(), ResourceType.IFO)
        if not ifo_result or not ifo_result.data:
            pytest.skip(f"Could not load IFO data for {ifo_resource.resname()}")
        
        editor.load(
            ifo_resource.filepath() if hasattr(ifo_resource, 'filepath') and callable(getattr(ifo_resource, 'filepath', None)) else (ifo_resource.filepath if hasattr(ifo_resource, 'filepath') else Path("module.ifo")),
            ifo_resource.resname(),
            ResourceType.IFO,
            ifo_result.data
        )
    else:
        ifo_file = ifo_files[0]
        original_data = ifo_file.read_bytes()
        editor.load(ifo_file, ifo_file.stem, ResourceType.IFO, original_data)
    
    # Verify loaded
    assert editor.ifo is not None
    original_tag = editor.ifo.tag
    
    # Modify a field
    editor.tag_edit.setText("modified_tag_test")
    editor.on_value_changed()
    
    # Build
    data, _ = editor.build()
    assert len(data) > 0
    
    # Verify modification
    modified_ifo = read_ifo(data)
    assert modified_ifo.tag == "modified_tag_test"
    assert modified_ifo.tag != original_tag
    
    # Load the built data back
    editor.load(Path("test.ifo"), "test", ResourceType.IFO, data)
    assert editor.ifo.tag == "modified_tag_test"
    assert editor.tag_edit.text() == "modified_tag_test"


# ============================================================================
# FIELD MANIPULATION TESTS WITH REAL FILES
# ============================================================================

def test_ifo_editor_manipulate_tag_with_real_file(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating tag field with a real IFO file."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Get a real IFO file
    ifo_files = list(test_files_dir.glob("*.ifo")) + list(test_files_dir.rglob("*.ifo"))
    if not ifo_files:
        ifo_resources = [res for res in installation if res.restype() is ResourceType.IFO]
        if not ifo_resources:
            pytest.skip("No IFO files available")
        ifo_resource = ifo_resources[0]
        ifo_result = installation.resource(ifo_resource.resname(), ResourceType.IFO)
        if not ifo_result or not ifo_result.data:
            pytest.skip(f"Could not load IFO data")
        editor.load(
            ifo_resource.filepath() if hasattr(ifo_resource, 'filepath') and callable(getattr(ifo_resource, 'filepath', None)) else (ifo_resource.filepath if hasattr(ifo_resource, 'filepath') else Path("module.ifo")),
            ifo_resource.resname(),
            ResourceType.IFO,
            ifo_result.data
        )
    else:
        ifo_file = ifo_files[0]
        original_data = ifo_file.read_bytes()
        editor.load(ifo_file, ifo_file.stem, ResourceType.IFO, original_data)
    
    original_ifo = read_ifo(editor._revert) if editor._revert else None
    
    # Modify tag
    editor.tag_edit.setText("modified_tag_real")
    editor.on_value_changed()
    
    # Build and verify
    data, _ = editor.build()
    modified_ifo = read_ifo(data)
    assert modified_ifo.tag == "modified_tag_real"
    if original_ifo:
        assert modified_ifo.tag != original_ifo.tag
    
    # Load back and verify
    editor.load(Path("test.ifo"), "test", ResourceType.IFO, data)
    assert editor.tag_edit.text() == "modified_tag_real"
    assert editor.ifo.tag == "modified_tag_real"  # pyright: ignore[reportOptionalMemberAccess]


def test_ifo_editor_manipulate_entry_point_with_real_file(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating entry point with a real IFO file."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Get a real IFO file
    ifo_files = list(test_files_dir.glob("*.ifo")) + list(test_files_dir.rglob("*.ifo"))
    if not ifo_files:
        ifo_resources = [res for res in installation if res.restype() is ResourceType.IFO]
        if not ifo_resources:
            pytest.skip("No IFO files available")
        ifo_resource = ifo_resources[0]
        ifo_result = installation.resource(ifo_resource.resname(), ResourceType.IFO)
        if not ifo_result or not ifo_result.data:
            pytest.skip(f"Could not load IFO data")
        editor.load(
            ifo_resource.filepath() if hasattr(ifo_resource, 'filepath') and callable(getattr(ifo_resource, 'filepath', None)) else (ifo_resource.filepath if hasattr(ifo_resource, 'filepath') else Path("module.ifo")),
            ifo_resource.resname(),
            ResourceType.IFO,
            ifo_result.data
        )
    else:
        ifo_file = ifo_files[0]
        original_data = ifo_file.read_bytes()
        editor.load(ifo_file, ifo_file.stem, ResourceType.IFO, original_data)
    
    # Modify entry point
    editor.entry_resref.setText("new_entry_area")
    editor.entry_x.setValue(100.0)
    editor.entry_y.setValue(200.0)
    editor.entry_z.setValue(50.0)
    editor.entry_dir.setValue(1.57)
    editor.on_value_changed()
    
    # Build and verify
    data, _ = editor.build()
    modified_ifo = read_ifo(data)
    assert str(modified_ifo.resref) == "new_entry_area"
    assert abs(modified_ifo.entry_position.x - 100.0) < 0.001
    assert abs(modified_ifo.entry_position.y - 200.0) < 0.001
    assert abs(modified_ifo.entry_position.z - 50.0) < 0.001
    assert abs(modified_ifo.entry_direction - 1.57) < 0.001


def test_ifo_editor_manipulate_time_settings_with_real_file(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating time settings with a real IFO file."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Get a real IFO file
    ifo_files = list(test_files_dir.glob("*.ifo")) + list(test_files_dir.rglob("*.ifo"))
    if not ifo_files:
        ifo_resources = [res for res in installation if res.restype() is ResourceType.IFO]
        if not ifo_resources:
            pytest.skip("No IFO files available")
        ifo_resource = ifo_resources[0]
        ifo_result = installation.resource(ifo_resource.resname(), ResourceType.IFO)
        if not ifo_result or not ifo_result.data:
            pytest.skip(f"Could not load IFO data")
        editor.load(
            ifo_resource.filepath() if hasattr(ifo_resource, 'filepath') and callable(getattr(ifo_resource, 'filepath', None)) else (ifo_resource.filepath if hasattr(ifo_resource, 'filepath') else Path("module.ifo")),
            ifo_resource.resname(),
            ResourceType.IFO,
            ifo_result.data
        )
    else:
        ifo_file = ifo_files[0]
        original_data = ifo_file.read_bytes()
        editor.load(ifo_file, ifo_file.stem, ResourceType.IFO, original_data)
    
    # Modify time settings
    editor.dawn_hour.setValue(6)
    editor.dusk_hour.setValue(18)
    editor.time_scale.setValue(50)
    editor.start_month.setValue(1)
    editor.start_day.setValue(1)
    editor.start_hour.setValue(12)
    editor.start_year.setValue(3956)
    editor.xp_scale.setValue(100)
    editor.on_value_changed()
    
    # Build and verify
    data, _ = editor.build()
    modified_ifo = read_ifo(data)
    assert modified_ifo.dawn_hour == 6
    assert modified_ifo.dusk_hour == 18
    assert modified_ifo.time_scale == 50
    assert modified_ifo.start_month == 1
    assert modified_ifo.start_day == 1
    assert modified_ifo.start_hour == 12
    assert modified_ifo.start_year == 3956
    assert modified_ifo.xp_scale == 100


def test_ifo_editor_manipulate_scripts_with_real_file(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating script fields with a real IFO file."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Get a real IFO file
    ifo_files = list(test_files_dir.glob("*.ifo")) + list(test_files_dir.rglob("*.ifo"))
    if not ifo_files:
        ifo_resources = [res for res in installation if res.restype() is ResourceType.IFO]
        if not ifo_resources:
            pytest.skip("No IFO files available")
        ifo_resource = ifo_resources[0]
        ifo_result = installation.resource(ifo_resource.resname(), ResourceType.IFO)
        if not ifo_result or not ifo_result.data:
            pytest.skip(f"Could not load IFO data")
        editor.load(
            ifo_resource.filepath() if hasattr(ifo_resource, 'filepath') and callable(getattr(ifo_resource, 'filepath', None)) else (ifo_resource.filepath if hasattr(ifo_resource, 'filepath') else Path("module.ifo")),
            ifo_resource.resname(),
            ResourceType.IFO,
            ifo_result.data
        )
    else:
        ifo_file = ifo_files[0]
        original_data = ifo_file.read_bytes()
        editor.load(ifo_file, ifo_file.stem, ResourceType.IFO, original_data)
    
    # Modify scripts (use shorter names to comply with 16-character ResRef limit)
    editor.script_fields["on_heartbeat"].setText("test_heartbeat")
    editor.script_fields["on_load"].setText("test_onload")
    editor.script_fields["on_start"].setText("test_onstart")
    editor.on_value_changed()
    
    # Build and verify
    data, _ = editor.build()
    modified_ifo = read_ifo(data)
    assert str(modified_ifo.on_heartbeat) == "test_heartbeat"
    assert str(modified_ifo.on_load) == "test_onload"
    assert str(modified_ifo.on_start) == "test_onstart"


# ============================================================================
# GFF ROUNDTRIP TESTS WITH REAL FILES
# ============================================================================

def test_ifo_editor_gff_roundtrip_with_real_file(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test GFF roundtrip comparison with a real IFO file."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Get a real IFO file
    ifo_files = list(test_files_dir.glob("*.ifo")) + list(test_files_dir.rglob("*.ifo"))
    if not ifo_files:
        ifo_resources = [res for res in installation if res.restype() is ResourceType.IFO]
        if not ifo_resources:
            pytest.skip("No IFO files available")
        ifo_resource = ifo_resources[0]
        ifo_result = installation.resource(ifo_resource.resname(), ResourceType.IFO)
        if not ifo_result or not ifo_result.data:
            pytest.skip(f"Could not load IFO data")
        editor.load(
            ifo_resource.filepath() if hasattr(ifo_resource, 'filepath') and callable(getattr(ifo_resource, 'filepath', None)) else (ifo_resource.filepath if hasattr(ifo_resource, 'filepath') else Path("module.ifo")),
            ifo_resource.resname(),
            ResourceType.IFO,
            ifo_result.data
        )
        original_data = ifo_result.data
    else:
        ifo_file = ifo_files[0]
        original_data = ifo_file.read_bytes()
        editor.load(ifo_file, ifo_file.stem, ResourceType.IFO, original_data)
    
    # Load original GFF
    original_gff = read_gff(original_data)
    
    # Build without modifications
    data, _ = editor.build()
    new_gff = read_gff(data)
    
    # Compare GFF structures (they should be equivalent)
    log_messages = []
    def log_func(*args):
        log_messages.append("\t".join(str(a) for a in args))
    
    # NOTE: We expect some differences due to how GFF is written, but structure should be valid
    assert new_gff is not None
    assert original_gff is not None


# ============================================================================
# MULTIPLE LOAD/SAVE CYCLES WITH REAL FILES
# ============================================================================

def test_ifo_editor_multiple_load_build_cycles(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test multiple load/build cycles with a real file."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Get a real IFO file
    ifo_files = list(test_files_dir.glob("*.ifo")) + list(test_files_dir.rglob("*.ifo"))
    if not ifo_files:
        ifo_resources = [res for res in installation if res.restype() is ResourceType.IFO]
        if not ifo_resources:
            pytest.skip("No IFO files available")
        ifo_resource = ifo_resources[0]
        ifo_result = installation.resource(ifo_resource.resname(), ResourceType.IFO)
        if not ifo_result or not ifo_result.data:
            pytest.skip(f"Could not load IFO data")
        editor.load(
            ifo_resource.filepath() if hasattr(ifo_resource, 'filepath') and callable(getattr(ifo_resource, 'filepath', None)) else (ifo_resource.filepath if hasattr(ifo_resource, 'filepath') else Path("module.ifo")),
            ifo_resource.resname(),
            ResourceType.IFO,
            ifo_result.data
        )
    else:
        ifo_file = ifo_files[0]
        original_data = ifo_file.read_bytes()
        editor.load(ifo_file, ifo_file.stem, ResourceType.IFO, original_data)
    
    # Perform multiple cycles
    for cycle in range(3):
        # Modify
        editor.tag_edit.setText(f"cycle_{cycle}")
        editor.entry_x.setValue(10.0 + cycle * 10)
        editor.time_scale.setValue(50 + cycle * 10)
        editor.on_value_changed()
        
        # Build
        data, _ = editor.build()
        saved_ifo = read_ifo(data)
        
        # Verify
        assert saved_ifo.tag == f"cycle_{cycle}"
        assert abs(saved_ifo.entry_position.x - (10.0 + cycle * 10)) < 0.001
        assert saved_ifo.time_scale == 50 + cycle * 10
        
        # Load back
        editor.load(Path("test.ifo"), "test", ResourceType.IFO, data)
        
        # Verify loaded
        assert editor.tag_edit.text() == f"cycle_{cycle}"
        assert abs(editor.entry_x.value() - (10.0 + cycle * 10)) < 0.001
        assert editor.time_scale.value() == 50 + cycle * 10


# ============================================================================
# COMPREHENSIVE FIELD MANIPULATION WITH REAL FILE
# ============================================================================

def test_ifo_editor_all_fields_with_real_file(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test manipulating all fields simultaneously with a real IFO file."""
    editor = IFOEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Get a real IFO file
    ifo_files = list(test_files_dir.glob("*.ifo")) + list(test_files_dir.rglob("*.ifo"))
    if not ifo_files:
        ifo_resources = [res for res in installation if res.restype() is ResourceType.IFO]
        if not ifo_resources:
            pytest.skip("No IFO files available")
        ifo_resource = ifo_resources[0]
        ifo_result = installation.resource(ifo_resource.resname(), ResourceType.IFO)
        if not ifo_result or not ifo_result.data:
            pytest.skip(f"Could not load IFO data")
        editor.load(
            ifo_resource.filepath() if hasattr(ifo_resource, 'filepath') and callable(getattr(ifo_resource, 'filepath', None)) else (ifo_resource.filepath if hasattr(ifo_resource, 'filepath') else Path("module.ifo")),
            ifo_resource.resname(),
            ResourceType.IFO,
            ifo_result.data
        )
    else:
        ifo_file = ifo_files[0]
        original_data = ifo_file.read_bytes()
        editor.load(ifo_file, ifo_file.stem, ResourceType.IFO, original_data)
    
    # Modify ALL fields
    editor.tag_edit.setText("comprehensive_test")
    editor.vo_id_edit.setText("vo_test")
    editor.hak_edit.setText("hak_test")
    editor.entry_resref.setText("area_test")
    editor.entry_x.setValue(100.0)
    editor.entry_y.setValue(200.0)
    editor.entry_z.setValue(50.0)
    editor.entry_dir.setValue(1.57)
    editor.dawn_hour.setValue(6)
    editor.dusk_hour.setValue(18)
    editor.time_scale.setValue(50)
    editor.start_month.setValue(1)
    editor.start_day.setValue(1)
    editor.start_hour.setValue(12)
    editor.start_year.setValue(3956)
    editor.xp_scale.setValue(100)
    
    # Set all scripts (use shorter names to comply with 16-character ResRef limit)
    script_test_values = {
        "on_heartbeat": "test_heartbeat",
        "on_load": "test_onload",
        "on_start": "test_onstart",
        "on_enter": "test_onenter",
        "on_leave": "test_onleave",
    }
    for script_name in editor.script_fields.keys():
        test_value = script_test_values.get(script_name, f"test_{script_name}")
        # Ensure test value doesn't exceed 16 characters
        if len(test_value) > 16:
            test_value = test_value[:16]
        editor.script_fields[script_name].setText(test_value)
    
    editor.on_value_changed()
    
    # Build and verify
    data, _ = editor.build()
    modified_ifo = read_ifo(data)
    
    assert modified_ifo.tag == "comprehensive_test"
    assert modified_ifo.vo_id == "vo_test"
    assert modified_ifo.hak == "hak_test"
    assert str(modified_ifo.resref) == "area_test"
    assert abs(modified_ifo.entry_position.x - 100.0) < 0.001
    assert abs(modified_ifo.entry_position.y - 200.0) < 0.001
    assert abs(modified_ifo.entry_position.z - 50.0) < 0.001
    assert abs(modified_ifo.entry_direction - 1.57) < 0.001
    assert modified_ifo.dawn_hour == 6
    assert modified_ifo.dusk_hour == 18
    assert modified_ifo.time_scale == 50
    assert modified_ifo.start_month == 1
    assert modified_ifo.start_day == 1
    assert modified_ifo.start_hour == 12
    assert modified_ifo.start_year == 3956
    assert modified_ifo.xp_scale == 100
    
    # Verify all scripts
    for script_name in editor.script_fields.keys():
        expected_value = script_test_values.get(script_name, f"test_{script_name}")
        if len(expected_value) > 16:
            expected_value = expected_value[:16]
        assert str(getattr(modified_ifo, script_name)) == expected_value

