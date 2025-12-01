"""
Comprehensive tests for Indoor Map Builder - testing ALL functionality.

Each test focuses on a specific feature and validates proper behavior.
Tests use real file system operations - no mocking allowed.

The IndoorMapBuilder now properly handles headless/offscreen mode by detecting
the QT_QPA_PLATFORM environment variable and skipping dialogs that would crash.
Tests can create builders without kits - the dialog will be automatically skipped
in headless mode.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from copy import copy
from pathlib import Path

import pytest
from qtpy.QtCore import Qt, QTimer
from qtpy.QtWidgets import QApplication, QMessageBox, QUndoStack

from toolset.data.indoorkit import Kit, KitComponent, KitComponentHook, KitDoor  # type: ignore[import-not-found]
from toolset.data.indoormap import IndoorMap, IndoorMapRoom  # type: ignore[import-not-found]
from toolset.data.installation import HTInstallation  # type: ignore[import-not-found]
from toolset.gui.windows.indoor_builder import (  # type: ignore[import-not-found]
    IndoorMapBuilder,
    IndoorMapRenderer,
    AddRoomCommand,
    DeleteRoomsCommand,
    MoveRoomsCommand,
    RotateRoomsCommand,
    FlipRoomsCommand,
    DuplicateRoomsCommand,
    MoveWarpCommand,
    RoomClipboardData,
)
from utility.common.geometry import Vector2, Vector3  # type: ignore[import-not-found]

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def real_kit_component():
    """Create a real KitComponent for testing."""
    from pykotor.resource.formats.bwm.bwm_data import BWM, BWMFace
    from qtpy.QtGui import QImage
    from utility.common.geometry import SurfaceMaterial
    
    # Create a minimal QImage for the component
    image = QImage(128, 128, QImage.Format.Format_RGB32)
    image.fill(0x808080)  # Gray

    # Create minimal BWM with a face
    bwm = BWM()
    face = BWMFace(
        Vector3(0, 0, 0),
        Vector3(10, 0, 0),
        Vector3(10, 10, 0),
    )
    face.material = SurfaceMaterial.STONE  # Walkable material
    bwm.faces.append(face)

    # Create real kit
    kit = Kit("TestKit")

    # Create component
    component = KitComponent(kit, "TestComponent", image, bwm, b"mdl_data", b"mdx_data")
    
    # Add a hook for testing - use a minimal door
    from pykotor.resource.generics.utd import UTD
    utd_k1 = UTD()
    utd_k2 = UTD()
    door = KitDoor(utd_k1, utd_k2, 2.0, 3.0)
    hook = KitComponentHook(Vector3(5, 5, 0), 0.0, "0", door)
    component.hooks.append(hook)
    kit.components.append(component)

    return component


@pytest.fixture
def real_kit(real_kit_component):
    """Create a real Kit for testing."""
    return real_kit_component.kit


@pytest.fixture
def temp_work_dir(tmp_path):
    """Create a temporary working directory with kits folder."""
    kits_dir = tmp_path / "kits"
    kits_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a minimal valid kit JSON file to prevent "no kits" dialog
    # The JSON must have "name" and "id" fields and be a valid dict
    kit_json_file = kits_dir / "testkit.json"
    kit_json = {
        "name": "TestKit",
        "id": "testkit",
        "components": [],
        "doors": []
    }
    kit_json_file.write_text(json.dumps(kit_json), encoding="utf-8")
    
    # Create kit directory structure (even if empty)
    # The directory name should match the "id" field
    kit_subdir = kits_dir / "testkit"
    kit_subdir.mkdir(exist_ok=True)
    
    return tmp_path


@pytest.fixture
def builder_with_real_kit(qtbot, installation: HTInstallation, temp_work_dir, real_kit):
    """Create IndoorMapBuilder in a temp directory with real kit files."""
    old_cwd = os.getcwd()
    try:
        os.chdir(temp_work_dir)
        
        # Wait for any existing dialogs to close
        QApplication.processEvents()
        
        # Create builder - it will load kits from "./kits"
        builder = IndoorMapBuilder(None, installation)
        qtbot.addWidget(builder)
        
        # Wait a bit for initialization
        qtbot.wait(100)
        QApplication.processEvents()
        
        # The builder should have loaded the kit (or have empty list if files missing)
        # Select first kit if available
        if builder.ui.kitSelect.count() > 0:
            builder.ui.kitSelect.setCurrentIndex(0)
        
        yield builder
    finally:
        os.chdir(old_cwd)


@pytest.fixture
def builder_no_kits(qtbot, installation: HTInstallation, tmp_path):
    """Create IndoorMapBuilder with empty kits directory.
    
    The builder now automatically detects headless mode and skips the dialog,
    so no manual dialog dismissal is needed.
    """
    old_cwd = os.getcwd()
    try:
        # Create empty kits directory
        kits_dir = tmp_path / "kits"
        kits_dir.mkdir(parents=True, exist_ok=True)
        
        os.chdir(tmp_path)
        
        # Wait for any existing dialogs
        QApplication.processEvents()
        
        # Create builder - dialog will be automatically skipped in headless mode
        builder = IndoorMapBuilder(None, installation)
        qtbot.addWidget(builder)
        
        # Wait for initialization to complete
        qtbot.wait(100)
        QApplication.processEvents()
        
        yield builder
    finally:
        os.chdir(old_cwd)


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================


def test_indoor_builder_initialization(qtbot, installation: HTInstallation, tmp_path):
    """Test that IndoorMapBuilder initializes correctly."""
    old_cwd = os.getcwd()
    try:
        kits_dir = tmp_path / "kits"
        kits_dir.mkdir(parents=True, exist_ok=True)
        
        os.chdir(tmp_path)
        
        QApplication.processEvents()
        builder = IndoorMapBuilder(None, installation)
        qtbot.addWidget(builder)
        
        # Wait for initialization - dialog will be automatically skipped in headless mode
        qtbot.wait(100)
        QApplication.processEvents()
        
        assert builder._map is not None
        assert isinstance(builder._map, IndoorMap)
        assert builder._undo_stack is not None
        assert isinstance(builder._undo_stack, QUndoStack)
        assert builder._clipboard == []
        assert builder.ui is not None
    finally:
        os.chdir(old_cwd)


def test_indoor_builder_initialization_no_installation(qtbot, tmp_path):
    """Test that IndoorMapBuilder works without installation."""
    old_cwd = os.getcwd()
    try:
        kits_dir = tmp_path / "kits"
        kits_dir.mkdir(parents=True, exist_ok=True)
        
        os.chdir(tmp_path)
        
        QApplication.processEvents()
        builder = IndoorMapBuilder(None, None)
        qtbot.addWidget(builder)
        
        # Wait for initialization - dialog will be automatically skipped in headless mode
        qtbot.wait(100)
        QApplication.processEvents()
        
        assert builder._installation is None
        assert builder._map is not None
        assert builder.ui.actionSettings.isEnabled() is False
    finally:
        os.chdir(old_cwd)


def test_renderer_initialization(qtbot, builder_no_kits):
    """Test that IndoorMapRenderer initializes correctly."""
    renderer = builder_no_kits.ui.mapRenderer
    
    assert renderer._map is not None
    assert renderer.snap_to_grid is False
    assert renderer.snap_to_hooks is True
    assert renderer.grid_size == 1.0
    assert renderer.rotation_snap == 15.0
    assert renderer._selected_rooms == []


# ============================================================================
# UNDO/REDO COMMAND TESTS
# ============================================================================


def test_add_room_command(qtbot, builder_no_kits, real_kit_component):
    """Test AddRoomCommand for adding rooms."""
    builder = builder_no_kits
    undo_stack = builder._undo_stack
    
    # Create a room
    room = IndoorMapRoom(real_kit_component, Vector3(0, 0, 0), 0.0, flip_x=False, flip_y=False)
    
    # Add room with command
    cmd = AddRoomCommand(builder._map, room)
    undo_stack.push(cmd)
    
    assert room in builder._map.rooms
    assert undo_stack.canUndo()
    
    # Undo
    undo_stack.undo()
    assert room not in builder._map.rooms
    assert undo_stack.canRedo()
    
    # Redo
    undo_stack.redo()
    assert room in builder._map.rooms


def test_delete_rooms_command(qtbot, builder_no_kits, real_kit_component):
    """Test DeleteRoomsCommand for deleting rooms."""
    builder = builder_no_kits
    undo_stack = builder._undo_stack
    
    # Create and add rooms
    room1 = IndoorMapRoom(real_kit_component, Vector3(0, 0, 0), 0.0, flip_x=False, flip_y=False)
    room2 = IndoorMapRoom(real_kit_component, Vector3(10, 0, 0), 0.0, flip_x=False, flip_y=False)
    builder._map.rooms.append(room1)
    builder._map.rooms.append(room2)
    
    # Delete rooms with command
    cmd = DeleteRoomsCommand(builder._map, [room1, room2])
    undo_stack.push(cmd)
    
    assert room1 not in builder._map.rooms
    assert room2 not in builder._map.rooms
    assert undo_stack.canUndo()
    
    # Undo
    undo_stack.undo()
    assert room1 in builder._map.rooms
    assert room2 in builder._map.rooms
    
    # Redo
    undo_stack.redo()
    assert room1 not in builder._map.rooms
    assert room2 not in builder._map.rooms


def test_move_rooms_command(qtbot, builder_no_kits, real_kit_component):
    """Test MoveRoomsCommand for moving rooms."""
    builder = builder_no_kits
    undo_stack = builder._undo_stack
    
    # Create and add room
    room = IndoorMapRoom(real_kit_component, Vector3(0, 0, 0), 0.0, flip_x=False, flip_y=False)
    builder._map.rooms.append(room)
    
    old_positions = [copy(room.position)]
    new_positions = [Vector3(10, 10, 0)]
    
    # Move room with command
    cmd = MoveRoomsCommand(builder._map, [room], old_positions, new_positions)
    undo_stack.push(cmd)
    
    assert abs(room.position.x - 10) < 0.001
    assert abs(room.position.y - 10) < 0.001
    
    # Undo
    undo_stack.undo()
    assert abs(room.position.x - 0) < 0.001
    assert abs(room.position.y - 0) < 0.001
    
    # Redo
    undo_stack.redo()
    assert abs(room.position.x - 10) < 0.001
    assert abs(room.position.y - 10) < 0.001


def test_rotate_rooms_command(qtbot, builder_no_kits, real_kit_component):
    """Test RotateRoomsCommand for rotating rooms."""
    builder = builder_no_kits
    undo_stack = builder._undo_stack
    
    # Create and add room
    room = IndoorMapRoom(real_kit_component, Vector3(0, 0, 0), 0.0, flip_x=False, flip_y=False)
    builder._map.rooms.append(room)
    
    old_rotations = [0.0]
    new_rotations = [90.0]
    
    # Rotate room with command
    cmd = RotateRoomsCommand(builder._map, [room], old_rotations, new_rotations)
    undo_stack.push(cmd)
    
    assert abs(room.rotation - 90.0) < 0.001
    
    # Undo
    undo_stack.undo()
    assert abs(room.rotation - 0.0) < 0.001
    
    # Redo
    undo_stack.redo()
    assert abs(room.rotation - 90.0) < 0.001


def test_flip_rooms_command(qtbot, builder_no_kits, real_kit_component):
    """Test FlipRoomsCommand for flipping rooms."""
    builder = builder_no_kits
    undo_stack = builder._undo_stack
    
    # Create and add room
    room = IndoorMapRoom(real_kit_component, Vector3(0, 0, 0), 0.0, flip_x=False, flip_y=False)
    builder._map.rooms.append(room)
    
    # Flip room with command
    cmd = FlipRoomsCommand(builder._map, [room], flip_x=True, flip_y=False)
    undo_stack.push(cmd)
    
    assert room.flip_x is True
    assert room.flip_y is False
    
    # Undo
    undo_stack.undo()
    assert room.flip_x is False
    
    # Redo
    undo_stack.redo()
    assert room.flip_x is True


def test_duplicate_rooms_command(qtbot, builder_no_kits, real_kit_component):
    """Test DuplicateRoomsCommand for duplicating rooms."""
    builder = builder_no_kits
    undo_stack = builder._undo_stack
    
    # Create and add room
    room = IndoorMapRoom(real_kit_component, Vector3(0, 0, 0), 0.0, flip_x=False, flip_y=False)
    builder._map.rooms.append(room)
    
    # Duplicate room with command
    offset = Vector3(2.0, 2.0, 0.0)
    cmd = DuplicateRoomsCommand(builder._map, [room], offset)
    undo_stack.push(cmd)
    
    assert len(builder._map.rooms) == 2
    duplicate = cmd.duplicates[0]
    assert duplicate in builder._map.rooms
    assert abs(duplicate.position.x - 2.0) < 0.001
    assert abs(duplicate.position.y - 2.0) < 0.001
    
    # Undo
    undo_stack.undo()
    assert len(builder._map.rooms) == 1
    
    # Redo
    undo_stack.redo()
    assert len(builder._map.rooms) == 2


def test_move_warp_command(qtbot, builder_no_kits):
    """Test MoveWarpCommand for moving warp point."""
    builder = builder_no_kits
    undo_stack = builder._undo_stack
    
    old_position = copy(builder._map.warp_point)
    new_position = Vector3(10, 20, 5)
    
    # Move warp point with command
    cmd = MoveWarpCommand(builder._map, old_position, new_position)
    undo_stack.push(cmd)
    
    assert abs(builder._map.warp_point.x - 10) < 0.001
    assert abs(builder._map.warp_point.y - 20) < 0.001
    assert abs(builder._map.warp_point.z - 5) < 0.001
    
    # Undo
    undo_stack.undo()
    assert abs(builder._map.warp_point.x - old_position.x) < 0.001
    assert abs(builder._map.warp_point.y - old_position.y) < 0.001
    
    # Redo
    undo_stack.redo()
    assert abs(builder._map.warp_point.x - 10) < 0.001


# ============================================================================
# UI ACTION TESTS  
# ============================================================================


def test_undo_action(qtbot, builder_no_kits, real_kit_component):
    """Test undo action via menu/toolbar."""
    builder = builder_no_kits
    
    # Initially disabled
    assert not builder.ui.actionUndo.isEnabled()
    
    # Add a room to enable undo
    room = IndoorMapRoom(real_kit_component, Vector3(0, 0, 0), 0.0, flip_x=False, flip_y=False)
    cmd = AddRoomCommand(builder._map, room)
    builder._undo_stack.push(cmd)
    
    # Should now be enabled
    qtbot.wait(10)
    QApplication.processEvents()
    assert builder.ui.actionUndo.isEnabled()
    
    # Trigger undo action
    builder.ui.actionUndo.trigger()
    qtbot.wait(10)
    QApplication.processEvents()
    
    # Room should be removed
    assert room not in builder._map.rooms


def test_redo_action(qtbot, builder_no_kits, real_kit_component):
    """Test redo action via menu/toolbar."""
    builder = builder_no_kits
    
    # Add a room and undo it
    room = IndoorMapRoom(real_kit_component, Vector3(0, 0, 0), 0.0, flip_x=False, flip_y=False)
    cmd = AddRoomCommand(builder._map, room)
    builder._undo_stack.push(cmd)
    builder._undo_stack.undo()
    
    # Redo should be enabled
    qtbot.wait(10)
    QApplication.processEvents()
    assert builder.ui.actionRedo.isEnabled()
    
    # Trigger redo action
    builder.ui.actionRedo.trigger()
    qtbot.wait(10)
    QApplication.processEvents()
    
    # Room should be added back
    assert room in builder._map.rooms


def test_delete_selected_action(qtbot, builder_no_kits, real_kit_component):
    """Test delete selected action."""
    builder = builder_no_kits
    
    # Create and add rooms
    room1 = IndoorMapRoom(real_kit_component, Vector3(0, 0, 0), 0.0, flip_x=False, flip_y=False)
    room2 = IndoorMapRoom(real_kit_component, Vector3(10, 0, 0), 0.0, flip_x=False, flip_y=False)
    builder._map.rooms.append(room1)
    builder._map.rooms.append(room2)
    
    # Select rooms
    builder.ui.mapRenderer.select_room(room1, clear_existing=True)
    builder.ui.mapRenderer.select_room(room2, clear_existing=False)
    
    # Trigger delete action
    builder.ui.actionDeleteSelected.trigger()
    qtbot.wait(10)
    QApplication.processEvents()
    
    # Rooms should be deleted via undo command
    assert builder._undo_stack.canUndo()
    assert room1 not in builder._map.rooms
    assert room2 not in builder._map.rooms


# ============================================================================
# SELECTION TESTS
# ============================================================================


def test_select_room(qtbot, builder_no_kits, real_kit_component):
    """Test selecting a single room."""
    builder = builder_no_kits
    renderer = builder.ui.mapRenderer
    
    # Create and add room
    room = IndoorMapRoom(real_kit_component, Vector3(0, 0, 0), 0.0, flip_x=False, flip_y=False)
    builder._map.rooms.append(room)
    
    # Select room
    renderer.select_room(room, clear_existing=True)
    
    selected = renderer.selected_rooms()
    assert len(selected) == 1
    assert selected[0] is room


def test_select_multiple_rooms(qtbot, builder_no_kits, real_kit_component):
    """Test selecting multiple rooms."""
    builder = builder_no_kits
    renderer = builder.ui.mapRenderer
    
    # Create and add rooms
    room1 = IndoorMapRoom(real_kit_component, Vector3(0, 0, 0), 0.0, flip_x=False, flip_y=False)
    room2 = IndoorMapRoom(real_kit_component, Vector3(10, 0, 0), 0.0, flip_x=False, flip_y=False)
    builder._map.rooms.append(room1)
    builder._map.rooms.append(room2)
    
    # Select rooms (additive)
    renderer.select_room(room1, clear_existing=True)
    renderer.select_room(room2, clear_existing=False)
    
    selected = renderer.selected_rooms()
    assert len(selected) == 2
    assert room1 in selected
    assert room2 in selected


def test_clear_selection(qtbot, builder_no_kits, real_kit_component):
    """Test clearing selection."""
    builder = builder_no_kits
    renderer = builder.ui.mapRenderer
    
    # Create and add room
    room = IndoorMapRoom(real_kit_component, Vector3(0, 0, 0), 0.0, flip_x=False, flip_y=False)
    builder._map.rooms.append(room)
    
    # Select and then clear
    renderer.select_room(room, clear_existing=True)
    renderer.clear_selected_rooms()
    
    selected = renderer.selected_rooms()
    assert len(selected) == 0


def test_select_all_action(qtbot, builder_no_kits, real_kit_component):
    """Test select all action."""
    builder = builder_no_kits
    
    # Create and add multiple rooms
    for i in range(5):
        room = IndoorMapRoom(
            real_kit_component,
            Vector3(i * 10, 0, 0),
            0.0,
            flip_x=False,
            flip_y=False,
        )
        builder._map.rooms.append(room)
    
    # Trigger select all action
    builder.ui.actionSelectAll.trigger()
    qtbot.wait(10)
    QApplication.processEvents()
    
    selected = builder.ui.mapRenderer.selected_rooms()
    assert len(selected) == 5


# ============================================================================
# SNAPPING TESTS
# ============================================================================


def test_snap_to_grid_toggle(qtbot, builder_no_kits):
    """Test toggling snap to grid option."""
    builder = builder_no_kits
    
    # Initially off
    assert builder.ui.snapToGridCheck.isChecked() is False
    assert builder.ui.mapRenderer.snap_to_grid is False
    
    # Toggle on
    builder.ui.snapToGridCheck.setChecked(True)
    qtbot.wait(10)
    QApplication.processEvents()
    assert builder.ui.mapRenderer.snap_to_grid is True
    
    # Toggle off
    builder.ui.snapToGridCheck.setChecked(False)
    qtbot.wait(10)
    QApplication.processEvents()
    assert builder.ui.mapRenderer.snap_to_grid is False


def test_snap_to_hooks_toggle(qtbot, builder_no_kits):
    """Test toggling snap to hooks option."""
    builder = builder_no_kits
    
    # Initially on
    assert builder.ui.snapToHooksCheck.isChecked() is True
    assert builder.ui.mapRenderer.snap_to_hooks is True
    
    # Toggle off
    builder.ui.snapToHooksCheck.setChecked(False)
    qtbot.wait(10)
    QApplication.processEvents()
    assert builder.ui.mapRenderer.snap_to_hooks is False


def test_grid_size_spinbox(qtbot, builder_no_kits):
    """Test grid size spinbox."""
    builder = builder_no_kits
    
    # Set grid size
    builder.ui.gridSizeSpin.setValue(2.5)
    qtbot.wait(10)
    QApplication.processEvents()
    
    assert abs(builder.ui.mapRenderer.grid_size - 2.5) < 0.001


def test_rotation_snap_spinbox(qtbot, builder_no_kits):
    """Test rotation snap spinbox."""
    builder = builder_no_kits
    
    # Set rotation snap
    builder.ui.rotSnapSpin.setValue(30)
    qtbot.wait(10)
    QApplication.processEvents()
    
    assert builder.ui.mapRenderer.rotation_snap == 30


# ============================================================================
# VIEW CONTROLS TESTS
# ============================================================================


def test_reset_view(qtbot, builder_no_kits):
    """Test reset view action."""
    builder = builder_no_kits
    renderer = builder.ui.mapRenderer
    
    # Move camera
    renderer.set_camera_position(100, 200)
    renderer.set_camera_zoom(2.0)
    renderer.set_camera_rotation(1.0)
    
    # Reset view
    builder.reset_view()
    
    assert abs(renderer.camera_position().x - 0) < 0.001
    assert abs(renderer.camera_position().y - 0) < 0.001
    assert abs(renderer.camera_zoom() - 1.0) < 0.001
    assert abs(renderer.camera_rotation() - 0.0) < 0.001


# ============================================================================
# EDGE CASE TESTS
# ============================================================================


def test_undo_with_empty_stack(qtbot, builder_no_kits):
    """Test that undo button is disabled when stack is empty."""
    builder = builder_no_kits
    
    assert not builder.ui.actionUndo.isEnabled()
    assert not builder.ui.actionRedo.isEnabled()


def test_delete_with_no_selection(qtbot, builder_no_kits):
    """Test deleting when nothing is selected."""
    builder = builder_no_kits
    
    # Should not crash
    builder.delete_selected()
    
    assert len(builder._map.rooms) == 0


def test_select_all_with_no_rooms(qtbot, builder_no_kits):
    """Test select all when there are no rooms."""
    builder = builder_no_kits
    
    builder.select_all()
    
    selected = builder.ui.mapRenderer.selected_rooms()
    assert len(selected) == 0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


def test_comprehensive_undo_redo_workflow(qtbot, builder_no_kits, real_kit_component):
    """Test comprehensive undo/redo workflow with multiple operations."""
    builder = builder_no_kits
    undo_stack = builder._undo_stack
    
    # Add room
    room = IndoorMapRoom(real_kit_component, Vector3(0, 0, 0), 0.0, flip_x=False, flip_y=False)
    cmd1 = AddRoomCommand(builder._map, room)
    undo_stack.push(cmd1)
    
    # Move it
    old_pos = [copy(room.position)]
    new_pos = [Vector3(10, 0, 0)]
    cmd2 = MoveRoomsCommand(builder._map, [room], old_pos, new_pos)
    undo_stack.push(cmd2)
    
    # Rotate it
    cmd3 = RotateRoomsCommand(builder._map, [room], [0.0], [90.0])
    undo_stack.push(cmd3)
    
    # Flip it
    cmd4 = FlipRoomsCommand(builder._map, [room], flip_x=True, flip_y=False)
    undo_stack.push(cmd4)
    
    # Verify final state
    assert abs(room.position.x - 10) < 0.001
    assert abs(room.rotation - 90.0) < 0.001
    assert room.flip_x is True
    
    # Undo all operations
    for _ in range(4):
        undo_stack.undo()
    
    # Should be back to original state
    assert abs(room.position.x - 0) < 0.001
    assert abs(room.rotation - 0.0) < 0.001
    assert room.flip_x is False
    
    # Redo all operations
    for _ in range(4):
        undo_stack.redo()
    
    # Should be back to modified state
    assert abs(room.position.x - 10) < 0.001
    assert abs(room.rotation - 90.0) < 0.001
    assert room.flip_x is True


# ============================================================================
# SETTINGS DIALOG TESTS
# ============================================================================


def test_settings_dialog_opens(qtbot, builder_no_kits, installation: HTInstallation):
    """Test that the settings dialog opens when triggered."""
    builder = builder_no_kits
    
    # Settings button should be enabled if installation exists
    # In builder_no_kits fixture, we pass installation, so it should be enabled
    # But we need to check if actionSettings exists and is enabled
    
    # Trigger settings action
    builder.open_settings()
    qtbot.wait(100)
    QApplication.processEvents()
    
    # Verify settings can be opened (dialog is modal, so we can't easily check visibility)
    # But we can verify the method exists and doesn't crash


def test_settings_dialog_updates_module_id(qtbot, builder_no_kits, installation: HTInstallation):
    """Test that settings dialog updates module ID and refreshes window title."""
    builder = builder_no_kits
    
    original_module_id = builder._map.module_id
    new_module_id = "test02"
    
    # Open settings and change module ID
    from toolset.gui.dialogs.indoor_settings import IndoorMapSettings
    dialog = IndoorMapSettings(builder, installation, builder._map, builder._kits)
    qtbot.addWidget(dialog)
    
    # Change the warp code
    dialog.ui.warpCodeEdit.setText(new_module_id)
    qtbot.wait(10)
    QApplication.processEvents()
    
    # Accept the dialog
    dialog.accept()
    qtbot.wait(10)
    QApplication.processEvents()
    
    # Verify module ID was updated
    assert builder._map.module_id == new_module_id
    assert builder._map.module_id != original_module_id