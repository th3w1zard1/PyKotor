from __future__ import annotations

import json
import math
import shutil
import zipfile

from copy import copy
from dataclasses import dataclass
from pathlib import Path
import os
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any

import qtpy

from qtpy import QtCore
from qtpy.QtCore import QPointF, QRectF, QTimer, Qt
from qtpy.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap, QTransform
from qtpy.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFormLayout,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QWidget,
)

if qtpy.QT5:
    from qtpy.QtWidgets import QUndoCommand, QUndoStack
elif qtpy.QT6:
    from qtpy.QtGui import QUndoCommand, QUndoStack  # pyright: ignore[reportPrivateImportUsage]
else:
    raise ValueError(f"Invalid QT_API: '{qtpy.API_NAME}'")

from pykotor.common.stream import BinaryWriter
from toolset.blender import BlenderEditorMode
from toolset.blender.integration import BlenderEditorMixin
from toolset.config import get_remote_toolset_update_info, is_remote_version_newer
from toolset.data.indoorkit import Kit, ModuleKit, ModuleKitManager, load_kits
from toolset.data.indoormap import IndoorMap, IndoorMapRoom
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.asyncloader import AsyncLoader
from toolset.gui.dialogs.indoor_settings import IndoorMapSettings
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.gui.windows.help import HelpWindow
from utility.common.geometry import Vector2, Vector3
from utility.error_handling import format_exception_with_variables, universal_simplify_exception
from utility.misc import is_debug_mode
from utility.system.os_helper import is_frozen
from utility.updater.github import download_github_release_asset

if TYPE_CHECKING:
    from qtpy.QtCore import QPoint
    from qtpy.QtGui import QCloseEvent, QImage, QKeyEvent, QMouseEvent, QPaintEvent, QWheelEvent

    from pykotor.resource.formats.bwm import BWMFace
    from pykotor.resource.formats.bwm.bwm_data import BWM
    from toolset.data.indoorkit import KitComponent, KitComponentHook
    from toolset.data.indoormap import MissingRoomInfo
    try:
        from qtpy.QtGui import QCloseEvent  # type: ignore[assignment]
    except ImportError:
        # Fallback for Qt6 where QCloseEvent may be in QtCore
        from qtpy.QtCore import QCloseEvent  # type: ignore[assignment]


# =============================================================================
# Undo/Redo Commands
# =============================================================================

class AddRoomCommand(QUndoCommand):
    """Command to add a room to the map."""

    def __init__(
        self,
        indoor_map: IndoorMap,
        room: IndoorMapRoom,
    ):
        super().__init__("Add Room")
        self.indoor_map = indoor_map
        self.room = room

    def undo(self):
        if self.room in self.indoor_map.rooms:
            self.indoor_map.rooms.remove(self.room)
            self.indoor_map.rebuild_room_connections()

    def redo(self):
        if self.room not in self.indoor_map.rooms:
            self.indoor_map.rooms.append(self.room)
            self.indoor_map.rebuild_room_connections()


class DeleteRoomsCommand(QUndoCommand):
    """Command to delete rooms from the map."""

    def __init__(
        self,
        indoor_map: IndoorMap,
        rooms: list[IndoorMapRoom],
    ):
        super().__init__(f"Delete {len(rooms)} Room(s)")
        self.indoor_map = indoor_map
        self.rooms = rooms.copy()
        # Store indices for proper re-insertion order
        self.indices = [indoor_map.rooms.index(r) for r in rooms if r in indoor_map.rooms]

    def undo(self):
        # Re-add rooms in original order
        for idx, room in zip(sorted(self.indices), self.rooms):
            if room not in self.indoor_map.rooms:
                self.indoor_map.rooms.insert(idx, room)
        self.indoor_map.rebuild_room_connections()

    def redo(self):
        for room in self.rooms:
            if room in self.indoor_map.rooms:
                self.indoor_map.rooms.remove(room)
        self.indoor_map.rebuild_room_connections()


class MoveRoomsCommand(QUndoCommand):
    """Command to move rooms."""

    def __init__(
        self,
        indoor_map: IndoorMap,
        rooms: list[IndoorMapRoom],
        old_positions: list[Vector3],
        new_positions: list[Vector3],
    ):
        super().__init__(f"Move {len(rooms)} Room(s)")
        self.indoor_map = indoor_map
        self.rooms = rooms.copy()
        self.old_positions = [copy(p) for p in old_positions]
        self.new_positions = [copy(p) for p in new_positions]

    def undo(self):
        for room, pos in zip(self.rooms, self.old_positions):
            room.position = copy(pos)
        self.indoor_map.rebuild_room_connections()

    def redo(self):
        for room, pos in zip(self.rooms, self.new_positions):
            room.position = copy(pos)
        self.indoor_map.rebuild_room_connections()


class RotateRoomsCommand(QUndoCommand):
    """Command to rotate rooms."""

    def __init__(
        self,
        indoor_map: IndoorMap,
        rooms: list[IndoorMapRoom],
        old_rotations: list[float],
        new_rotations: list[float],
    ):
        super().__init__(f"Rotate {len(rooms)} Room(s)")
        self.indoor_map = indoor_map
        self.rooms = rooms.copy()
        self.old_rotations = old_rotations.copy()
        self.new_rotations = new_rotations.copy()

    def undo(self):
        for room, rot in zip(self.rooms, self.old_rotations):
            room.rotation = rot
        self.indoor_map.rebuild_room_connections()

    def redo(self):
        for room, rot in zip(self.rooms, self.new_rotations):
            room.rotation = rot
        self.indoor_map.rebuild_room_connections()


class FlipRoomsCommand(QUndoCommand):
    """Command to flip rooms."""

    def __init__(
        self,
        indoor_map: IndoorMap,
        rooms: list[IndoorMapRoom],
        flip_x: bool,
        flip_y: bool,
    ):
        super().__init__(f"Flip {len(rooms)} Room(s)")
        self.indoor_map = indoor_map
        self.rooms = rooms.copy()
        self.flip_x = flip_x
        self.flip_y = flip_y
        # Store original states
        self.old_flip_x = [r.flip_x for r in rooms]
        self.old_flip_y = [r.flip_y for r in rooms]

    def undo(self):
        for room, fx, fy in zip(self.rooms, self.old_flip_x, self.old_flip_y):
            room.flip_x = fx
            room.flip_y = fy
        self.indoor_map.rebuild_room_connections()

    def redo(self):
        for room in self.rooms:
            if self.flip_x:
                room.flip_x = not room.flip_x
            if self.flip_y:
                room.flip_y = not room.flip_y
        self.indoor_map.rebuild_room_connections()


class DuplicateRoomsCommand(QUndoCommand):
    """Command to duplicate rooms."""

    def __init__(
        self,
        indoor_map: IndoorMap,
        rooms: list[IndoorMapRoom],
        offset: Vector3,
    ):
        super().__init__(f"Duplicate {len(rooms)} Room(s)")
        self.indoor_map = indoor_map
        self.original_rooms = rooms.copy()
        self.offset = offset
        # Create duplicates
        self.duplicates: list[IndoorMapRoom] = []
        for room in rooms:
            new_room = IndoorMapRoom(
                room.component,
                Vector3(room.position.x + offset.x, room.position.y + offset.y, room.position.z + offset.z),
                room.rotation,
                flip_x=room.flip_x,
                flip_y=room.flip_y,
            )
            self.duplicates.append(new_room)

    def undo(self):
        for room in self.duplicates:
            if room in self.indoor_map.rooms:
                self.indoor_map.rooms.remove(room)
        self.indoor_map.rebuild_room_connections()

    def redo(self):
        for room in self.duplicates:
            if room not in self.indoor_map.rooms:
                self.indoor_map.rooms.append(room)
        self.indoor_map.rebuild_room_connections()


class MoveWarpCommand(QUndoCommand):
    """Command to move the warp point."""

    def __init__(
        self,
        indoor_map: IndoorMap,
        old_position: Vector3,
        new_position: Vector3,
    ):
        super().__init__("Move Warp Point")
        self.indoor_map = indoor_map
        self.old_position = copy(old_position)
        self.new_position = copy(new_position)

    def undo(self):
        self.indoor_map.warp_point = copy(self.old_position)

    def redo(self):
        self.indoor_map.warp_point = copy(self.new_position)


# =============================================================================
# Data structures for clipboard
# =============================================================================

@dataclass
class RoomClipboardData:
    """Stores room data for clipboard operations."""
    component_kit_name: str
    component_name: str
    position: Vector3
    rotation: float
    flip_x: bool
    flip_y: bool


@dataclass
class SnapResult:
    """Result of a snap operation."""
    position: Vector3
    snapped: bool = False
    hook_from: KitComponentHook | None = None
    hook_to: KitComponentHook | None = None
    target_room: IndoorMapRoom | None = None


# =============================================================================
# Main Window
# =============================================================================

class IndoorMapBuilder(QMainWindow, BlenderEditorMixin):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation | None = None,
        use_blender: bool = False,
    ):
        super().__init__(parent)

        # Initialize Blender integration
        self._init_blender_integration(BlenderEditorMode.INDOOR_BUILDER)
        self._use_blender_mode: bool = use_blender

        self._installation: HTInstallation | None = installation
        self._kits: list[Kit] = []
        self._map: IndoorMap = IndoorMap()
        self._filepath: str = ""
        
        # Module kit management (lazy loading)
        # ModuleKitManager handles converting game modules to kit-like components
        if installation is not None:
            self._module_kit_manager: ModuleKitManager = ModuleKitManager(installation)
        else:
            self._module_kit_manager = None  # type: ignore[assignment]
        self._current_module_kit: ModuleKit | None = None

        # Undo/Redo stack
        self._undo_stack: QUndoStack = QUndoStack(self)

        # Clipboard for copy/paste
        self._clipboard: list[RoomClipboardData] = []

        from toolset.uic.qtpy.windows.indoor_builder import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._setup_signals()
        self._setup_undo_redo()
        self._setup_kits()
        self._setup_modules()
        self._refresh_window_title()

        self.ui.mapRenderer.set_map(self._map)
        self.ui.mapRenderer.set_undo_stack(self._undo_stack)

    def _setup_signals(self):
        """Connect signals to slots."""
        # Kit/component selection
        self.ui.kitSelect.currentIndexChanged.connect(self.on_kit_selected)
        self.ui.componentList.currentItemChanged.connect(self.onComponentSelected)
        
        # Module/component selection
        self.ui.moduleSelect.currentIndexChanged.connect(self.on_module_selected)
        self.ui.moduleComponentList.currentItemChanged.connect(self.on_module_component_selected)

        # File menu
        self.ui.actionNew.triggered.connect(self.new)
        self.ui.actionOpen.triggered.connect(self.open)
        self.ui.actionSave.triggered.connect(self.save)
        self.ui.actionSaveAs.triggered.connect(self.save_as)
        self.ui.actionBuild.triggered.connect(self.build_map)
        self.ui.actionDownloadKits.triggered.connect(self.open_kit_downloader)
        self.ui.actionExit.triggered.connect(self.close)

        # Settings
        if self._installation:
            assert isinstance(self._installation, HTInstallation)
            self.ui.actionSettings.triggered.connect(self.open_settings)
        else:
            self.ui.actionSettings.setEnabled(False)

        # Edit menu
        self.ui.actionDeleteSelected.triggered.connect(self.delete_selected)
        self.ui.actionDuplicate.triggered.connect(self.duplicate_selected)
        self.ui.actionCut.triggered.connect(self.cut_selected)
        self.ui.actionCopy.triggered.connect(self.copy_selected)
        self.ui.actionPaste.triggered.connect(self.paste)
        self.ui.actionSelectAll.triggered.connect(self.select_all)
        self.ui.actionDeselectAll.triggered.connect(self.deselect_all)

        # View menu
        self.ui.actionZoomIn.triggered.connect(lambda: self.ui.mapRenderer.zoom_in_camera(0.2))
        self.ui.actionZoomOut.triggered.connect(lambda: self.ui.mapRenderer.zoom_in_camera(-0.2))
        self.ui.actionResetView.triggered.connect(self.reset_view)
        self.ui.actionCenterOnSelection.triggered.connect(self.center_on_selection)

        # Help menu
        self.ui.actionInstructions.triggered.connect(self.show_help_window)

        # Renderer signals
        self.ui.mapRenderer.customContextMenuRequested.connect(self.on_context_menu)
        self.ui.mapRenderer.sig_mouse_moved.connect(self.on_mouse_moved)
        self.ui.mapRenderer.sig_mouse_pressed.connect(self.on_mouse_pressed)
        self.ui.mapRenderer.sig_mouse_released.connect(self.on_mouse_released)
        self.ui.mapRenderer.sig_mouse_scrolled.connect(self.on_mouse_scrolled)
        self.ui.mapRenderer.sig_mouse_double_clicked.connect(self.onMouseDoubleClicked)
        self.ui.mapRenderer.sig_rooms_moved.connect(self.on_rooms_moved)
        self.ui.mapRenderer.sig_warp_moved.connect(self.on_warp_moved)
        self.ui.mapRenderer.sig_marquee_select.connect(self.on_marquee_select)

        # Options checkboxes
        self.ui.snapToGridCheck.toggled.connect(lambda v: setattr(self.ui.mapRenderer, 'snap_to_grid', v))
        self.ui.snapToHooksCheck.toggled.connect(lambda v: setattr(self.ui.mapRenderer, 'snap_to_hooks', v))
        self.ui.showGridCheck.toggled.connect(lambda v: setattr(self.ui.mapRenderer, 'show_grid', v))
        self.ui.showHooksCheck.toggled.connect(lambda v: setattr(self.ui.mapRenderer, 'hide_magnets', not v))
        self.ui.gridSizeSpin.valueChanged.connect(lambda v: setattr(self.ui.mapRenderer, 'grid_size', v))
        self.ui.rotSnapSpin.valueChanged.connect(lambda v: setattr(self.ui.mapRenderer, 'rotation_snap', v))

    def _setup_undo_redo(self):
        """Setup undo/redo actions."""
        self.ui.actionUndo.triggered.connect(self._undo_stack.undo)
        self.ui.actionRedo.triggered.connect(self._undo_stack.redo)

        # Update action enabled states
        self._undo_stack.canUndoChanged.connect(self.ui.actionUndo.setEnabled)
        self._undo_stack.canRedoChanged.connect(self.ui.actionRedo.setEnabled)

        # Update action text with command names
        self._undo_stack.undoTextChanged.connect(
            lambda text: self.ui.actionUndo.setText(f"Undo {text}" if text else "Undo")
        )
        self._undo_stack.redoTextChanged.connect(
            lambda text: self.ui.actionRedo.setText(f"Redo {text}" if text else "Redo")
        )

        # Initial state
        self.ui.actionUndo.setEnabled(False)
        self.ui.actionRedo.setEnabled(False)

    def _setup_kits(self):
        self.ui.kitSelect.clear()
        self._kits, missing_files = load_kits("./kits")

        # In test/headless environments the missing-files dialog can interfere
        # with automated runs (pytest-qt, CI).  Headless mode is indicated by
        # Qt using the offscreen platform plugin; in that case we suppress the
        # dialog entirely and rely on logging instead.
        if missing_files and os.environ.get("QT_QPA_PLATFORM", "").lower() not in {"offscreen", "minimal"}:
            self._show_missing_files_dialog(missing_files)

        # Kits are deprecated and optional - modules provide the same functionality
        # No need to show a dialog when kits are missing since modules can be used instead
        # if len(self._kits) == 0:
        #     ... (removed - kits are deprecated, modules handle this functionality)

        for kit in self._kits:
            self.ui.kitSelect.addItem(kit.name, kit)

    def _show_no_kits_dialog(self):
        """Show dialog asking if user wants to open kit downloader.
        
        This is called asynchronously via QTimer.singleShot to avoid blocking initialization.
        Headless mode is already checked before this method is scheduled, so it will only
        be called in GUI mode where exec() is safe.
        """
        from toolset.gui.common.localization import translate as tr
        
        # Show dialog in GUI mode using exec()
        # Headless check happens before this method is scheduled, so this is safe
        no_kit_prompt = QMessageBox(self)
        no_kit_prompt.setIcon(QMessageBox.Icon.Warning)
        no_kit_prompt.setWindowTitle(tr("No Kits Available"))
        no_kit_prompt.setText(tr("No kits were detected, would you like to open the Kit downloader?"))
        no_kit_prompt.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        no_kit_prompt.setDefaultButton(QMessageBox.StandardButton.No)
        
        # Use exec() for proper modal behavior in GUI mode
        result = no_kit_prompt.exec()
        if result == QMessageBox.StandardButton.Yes or no_kit_prompt.clickedButton() == QMessageBox.StandardButton.Yes:
            self.open_kit_downloader()

    def _setup_modules(self):
        """Set up the module selection combobox with available modules from the installation.
        
        Uses ModuleKitManager to get module roots and display names.
        Modules are loaded lazily when selected.
        """
        self.ui.moduleSelect.clear()
        self.ui.moduleComponentList.clear()
        
        if not self._installation:
            # Disable modules UI if no installation is available
            if hasattr(self.ui, 'modulesGroupBox'):
                self.ui.modulesGroupBox.setEnabled(False)
            return
        
        # Get module roots from the kit manager
        module_roots = self._module_kit_manager.get_module_roots()
        
        # Populate the combobox with module names
        for module_root in module_roots:
            display_name = self._module_kit_manager.get_module_display_name(module_root)
            self.ui.moduleSelect.addItem(display_name, module_root)
    
    def on_module_selected(self, index: int = -1):
        """Handle module selection from the combobox.
        
        Loads module components lazily when a module is selected in the combobox.
        Uses ModuleKitManager to convert module resources into kit components.
        """
        self.ui.moduleComponentList.clear()
        
        if hasattr(self.ui, 'moduleComponentImage'):
            self.ui.moduleComponentImage.clear()
        
        module_root: str | None = self.ui.moduleSelect.currentData()
        if not module_root or not self._installation:
            return
        
        try:
            # Use the ModuleKitManager to get a ModuleKit for this module
            module_kit = self._module_kit_manager.get_module_kit(module_root)
            
            # Ensure the kit is loaded (lazy loading)
            if not module_kit.ensure_loaded():
                from loggerplus import RobustLogger
                RobustLogger().warning(f"No components found for module '{module_root}'")
                return
            
            # Populate the list with components from the module kit
            for component in module_kit.components:
                item = QListWidgetItem(component.name)
                item.setData(Qt.ItemDataRole.UserRole, component)
                self.ui.moduleComponentList.addItem(item)
                
        except Exception:  # noqa: BLE001
            from loggerplus import RobustLogger
            RobustLogger().exception(f"Failed to load module '{module_root}'")
    
    def on_module_component_selected(self, item: QListWidgetItem | None = None):
        """Handle module component selection from the list."""
        if item is None:
            if hasattr(self.ui, 'moduleComponentImage'):
                self.ui.moduleComponentImage.clear()
            self.ui.mapRenderer.set_cursor_component(None)
            return
        
        component: KitComponent | None = item.data(Qt.ItemDataRole.UserRole)
        if component is None:
            return
        
        # Display component image in the preview
        if hasattr(self.ui, 'moduleComponentImage') and component.image is not None:
            pixmap = QPixmap.fromImage(component.image)
            scaled = pixmap.scaled(
                self.ui.moduleComponentImage.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.ui.moduleComponentImage.setPixmap(scaled)
        
        # Set as current cursor component for placement
        self.ui.mapRenderer.set_cursor_component(component)

    def _refresh_window_title(self):
        from toolset.gui.common.localization import translate as tr, trf
        if not self._installation:
            title = tr("No installation - Map Builder")
        elif not self._filepath:
            title = trf("{name} - Map Builder", name=self._installation.name)
        else:
            title = trf("{path} - {name} - Map Builder", path=self._filepath, name=self._installation.name)
        
        # Add asterisk if there are unsaved changes
        if self._undo_stack.canUndo():
            title = "* " + title
        self.setWindowTitle(title)

    def _refresh_status_bar(self):
        screen: QPoint = self.ui.mapRenderer.mapFromGlobal(self.cursor().pos())
        world: Vector3 = self.ui.mapRenderer.to_world_coords(screen.x(), screen.y())
        obj: IndoorMapRoom | None = self.ui.mapRenderer.room_under_mouse()
        selected_count = len(self.ui.mapRenderer.selected_rooms())

        parts = [f"X: {world.x:.2f}, Y: {world.y:.2f}"]
        if obj:
            parts.append(f"Hover: {obj.component.name}")
        if selected_count > 0:
            parts.append(f"Selected: {selected_count}")
        
        # Add snap indicators
        if self.ui.mapRenderer.snap_to_grid:
            parts.append("[Grid Snap]")
        if self.ui.mapRenderer.snap_to_hooks:
            parts.append("[Hook Snap]")

        status_bar: QStatusBar | None = self.statusBar()
        assert isinstance(status_bar, QStatusBar)
        status_bar.showMessage(" | ".join(parts))

    def show_help_window(self):
        window = HelpWindow(self, "./wiki/LYT-File-Format.md")
        window.setWindowIcon(self.windowIcon())
        window.show()
        window.activateWindow()

    # =========================================================================
    # File operations
    # =========================================================================

    def save(self):
        self._map.generate_mipmap()
        if not self._filepath:
            self.save_as()
        else:
            BinaryWriter.dump(self._filepath, self._map.write())
            self._undo_stack.setClean()
            self._refresh_window_title()

    def save_as(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Map",
            Path(self._filepath).name if self._filepath and self._filepath.strip() else "test.indoor",
            "Indoor Map File (*.indoor)",
        )
        if not filepath or not filepath.strip():
            return
        BinaryWriter.dump(filepath, self._map.write())
        self._filepath = filepath
        self._undo_stack.setClean()
        self._refresh_window_title()

    def new(self):
        if self._undo_stack.canUndo():
            result = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before creating a new map?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            )
            if result == QMessageBox.StandardButton.Save:
                self.save()
            elif result == QMessageBox.StandardButton.Cancel:
                return

        self._filepath = ""
        self._map.reset()
        self._undo_stack.clear()
        self._refresh_window_title()

    def open(self):
        if self._undo_stack.canUndo():
            result = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before opening another map?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            )
            if result == QMessageBox.StandardButton.Save:
                self.save()
            elif result == QMessageBox.StandardButton.Cancel:
                return

        filepath, _ = QFileDialog.getOpenFileName(self, "Open Map", "", "Indoor Map File (*.indoor)")
        if filepath and str(filepath).strip():
            try:
                missing_rooms = self._map.load(Path(filepath).read_bytes(), self._kits)
                self._map.rebuild_room_connections()
                self._filepath = filepath
                self._undo_stack.clear()
                self._refresh_window_title()
                
                if missing_rooms:
                    self._show_missing_rooms_dialog(missing_rooms)
            except OSError as e:
                from toolset.gui.common.localization import translate as tr, trf
                QMessageBox(
                    QMessageBox.Icon.Critical,
                    tr("Failed to load file"),
                    trf("{error}", error=str(universal_simplify_exception(e))),
                ).exec()

    def _show_missing_files_dialog(self, missing_files: list[tuple[str, Path, str]]):
        """Show a dialog with information about missing kit files."""
        from toolset.gui.common.localization import translate as tr, trf
        
        # Don't show dialog in frozen code (PyInstaller _MEIPASS)
        if is_frozen():
            return
        
        if not missing_files:
            return
        
        # Check if all missing files are PNGs (component images)
        # If so, don't show the dialog
        non_png_files = [f for f in missing_files if f[2] != "component image"]
        if not non_png_files:
            return
        
        # If there are non-PNG files missing, show all missing files (including PNGs)
        filtered_files = missing_files
        
        files_by_kit: dict[str, list[tuple[Path, str]]] = {}
        for kit_name, file_path, file_type in filtered_files:
            if kit_name not in files_by_kit:
                files_by_kit[kit_name] = []
            files_by_kit[kit_name].append((file_path, file_type))
        
        file_count = len(filtered_files)
        kit_count = len(files_by_kit)
        kit_names = sorted(files_by_kit.keys())
        
        main_text = trf(
            "{count} file{plural} missing from {kit_count} kit{kit_plural}.\n\n"
            "Kit{kit_plural}: {kits}",
            count=file_count,
            plural="s" if file_count != 1 else "",
            kit_count=kit_count,
            kit_plural="s" if kit_count != 1 else "",
            kits=", ".join(f"'{name}'" for name in kit_names),
        )
        
        detailed_lines: list[str] = []
        for kit_name in sorted(files_by_kit.keys()):
            detailed_lines.append(f"\n=== Kit: '{kit_name}' ===")
            files = files_by_kit[kit_name]
            files_by_type: dict[str, list[Path]] = {}
            for file_path, file_type in files:
                if file_type not in files_by_type:
                    files_by_type[file_type] = []
                files_by_type[file_type].append(file_path)
            
            for file_type in sorted(files_by_type.keys()):
                detailed_lines.append(f"\n  {file_type}:")
                for file_path in sorted(files_by_type[file_type]):
                    detailed_lines.append(f"    - {file_path}")
        
        msg_box = QMessageBox(
            QMessageBox.Icon.Warning,
            tr("Missing Kit Files"),
            main_text,
            flags=Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint,
        )
        msg_box.setDetailedText("\n".join(detailed_lines))
        msg_box.exec()

    def _show_missing_rooms_dialog(self, missing_rooms: list[MissingRoomInfo]):
        """Show a dialog with information about missing rooms/kits."""
        from toolset.gui.common.localization import translate as tr, trf
        
        missing_kits = [r for r in missing_rooms if r.reason == "kit_missing"]
        missing_components = [r for r in missing_rooms if r.reason == "component_missing"]
        
        room_count = len(missing_rooms)
        missing_kit_names = {r.kit_name for r in missing_rooms if r.reason == "kit_missing"}
        missing_component_pairs = {
            (r.kit_name, r.component_name)
            for r in missing_rooms
            if r.reason == "component_missing" and r.component_name
        }
        
        main_parts: list[str] = []
        if missing_kit_names:
            kit_list = ", ".join(f"'{name}'" for name in sorted(missing_kit_names))
            main_parts.append(trf("Missing kit{plural}: {kits}", plural="s" if len(missing_kit_names) != 1 else "", kits=kit_list))
        if missing_component_pairs:
            component_list = ", ".join(f"'{comp}' ({kit})" for kit, comp in sorted(missing_component_pairs))
            main_parts.append(trf("Missing component{plural}: {components}", plural="s" if len(missing_component_pairs) != 1 else "", components=component_list))
        
        main_text = trf(
            "{count} room{plural} failed to load.\n\n{details}",
            count=room_count,
            plural="s" if room_count != 1 else "",
            details="\n".join(main_parts),
        )
        
        detailed_lines: list[str] = []
        if missing_kits:
            detailed_lines.append("=== Missing Kits ===")
            for room_info in missing_kits:
                kit_name = room_info.kit_name
                kit_json_path = Path("./kits") / f"{kit_name}.json"
                detailed_lines.append(f"\nRoom: Kit '{kit_name}'")
                if room_info.component_name:
                    detailed_lines.append(f"  Component: {room_info.component_name}")
                detailed_lines.append(f"  Expected Kit JSON: {kit_json_path}")
                detailed_lines.append(f"  Expected Kit Directory: {Path('./kits') / kit_name}")
        
        if missing_components:
            detailed_lines.append("\n=== Missing Components ===")
            for room_info in missing_components:
                kit_name = room_info.kit_name
                component_name = room_info.component_name or "Unknown"
                component_path = Path("./kits") / kit_name / "components" / component_name
                detailed_lines.append(f"\nRoom: Kit '{kit_name}', Component '{component_name}'")
                detailed_lines.append(f"  Expected Component Directory: {component_path}")
        
        msg_box = QMessageBox(
            QMessageBox.Icon.Warning,
            tr("Some Rooms Failed to Load"),
            main_text,
            flags=Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint,
        )
        msg_box.setDetailedText("\n".join(detailed_lines))
        msg_box.exec()

    def open_kit_downloader(self):
        KitDownloader(self).exec()
        self._setup_kits()

    def open_settings(self):
        """Open the settings dialog and update the map if changes are made."""
        if not isinstance(self._installation, HTInstallation):
            return
        
        # Store original values to detect changes
        old_module_id = self._map.module_id
        old_name = self._map.name.stringref if hasattr(self._map.name, 'stringref') else None
        old_skybox = self._map.skybox
        
        dialog = IndoorMapSettings(self, self._installation, self._map, self._kits)
        if dialog.exec():
            # Settings were accepted - check if anything actually changed
            module_id_changed = old_module_id != self._map.module_id
            name_changed = old_name != (self._map.name.stringref if hasattr(self._map.name, 'stringref') else None)
            skybox_changed = old_skybox != self._map.skybox
            
            if module_id_changed or name_changed or skybox_changed:
                # Mark as having unsaved changes by pushing a no-op command
                # This ensures the asterisk appears in the window title
                from qtpy.QtWidgets import QUndoCommand
                
                class SettingsChangedCommand(QUndoCommand):
                    def __init__(self):
                        super().__init__("Settings Changed")
                    
                    def undo(self): ...
                    def redo(self): ...
                
                # Only push if stack is clean to avoid unnecessary undo entries
                if not self._undo_stack.canUndo():
                    self._undo_stack.push(SettingsChangedCommand())
                
                # Refresh window title to reflect any changes (especially module_id)
                self._refresh_window_title()

    def build_map(self):
        if not isinstance(self._installation, HTInstallation):
            QMessageBox.warning(self, "No Installation", "Please select an installation first.")
            return
        path: Path = self._installation.module_path() / f"{self._map.module_id}.mod"

        def task():
            assert isinstance(self._installation, HTInstallation)
            return self._map.build(self._installation, self._kits, path)

        msg = f"You can warp to the game using the code 'warp {self._map.module_id}'. "
        msg += f"Map files can be found in:\n{path}"
        loader = AsyncLoader(self, "Building Map...", task, "Failed to build map.")
        if loader.exec():
            QMessageBox(QMessageBox.Icon.Information, "Map built", msg).exec()

    # =========================================================================
    # Edit operations
    # =========================================================================

    def delete_selected(self):
        rooms = self.ui.mapRenderer.selected_rooms()
        if not rooms:
            return
        cmd = DeleteRoomsCommand(self._map, rooms)
        self._undo_stack.push(cmd)
        self.ui.mapRenderer.clear_selected_rooms()
        self._refresh_window_title()

    def duplicate_selected(self):
        rooms = self.ui.mapRenderer.selected_rooms()
        if not rooms:
            return
        cmd = DuplicateRoomsCommand(self._map, rooms, Vector3(2.0, 2.0, 0.0))
        self._undo_stack.push(cmd)
        # Select the duplicates
        self.ui.mapRenderer.clear_selected_rooms()
        for room in cmd.duplicates:
            self.ui.mapRenderer.select_room(room, clear_existing=False)
        self._refresh_window_title()

    def cut_selected(self):
        self.copy_selected()
        self.delete_selected()

    def copy_selected(self):
        rooms = self.ui.mapRenderer.selected_rooms()
        if not rooms:
            return

        self._clipboard.clear()
        # Calculate centroid for relative positioning
        cx = sum(r.position.x for r in rooms) / len(rooms)
        cy = sum(r.position.y for r in rooms) / len(rooms)

        for room in rooms:
            data = RoomClipboardData(
                component_kit_name=room.component.kit.name,
                component_name=room.component.name,
                position=Vector3(room.position.x - cx, room.position.y - cy, room.position.z),
                rotation=room.rotation,
                flip_x=room.flip_x,
                flip_y=room.flip_y,
            )
            self._clipboard.append(data)

    def paste(self):
        if not self._clipboard:
            return

        # Get paste position (cursor position or center of view)
        screen_center = QPointF(self.ui.mapRenderer.width() / 2, self.ui.mapRenderer.height() / 2)
        world_center = self.ui.mapRenderer.to_world_coords(screen_center.x(), screen_center.y())

        new_rooms: list[IndoorMapRoom] = []
        for data in self._clipboard:
            # Find the kit and component
            kit = next((k for k in self._kits if k.name == data.component_kit_name), None)
            if not kit:
                continue
            component = next((c for c in kit.components if c.name == data.component_name), None)
            if not component:
                continue

            room = IndoorMapRoom(
                component,
                Vector3(world_center.x + data.position.x, world_center.y + data.position.y, data.position.z),
                data.rotation,
                flip_x=data.flip_x,
                flip_y=data.flip_y,
            )
            new_rooms.append(room)

        if new_rooms:
            # Create a compound command for all pasted rooms
            for room in new_rooms:
                cmd = AddRoomCommand(self._map, room)
                self._undo_stack.push(cmd)

            self.ui.mapRenderer.clear_selected_rooms()
            for room in new_rooms:
                self.ui.mapRenderer.select_room(room, clear_existing=False)
            self._refresh_window_title()

    def select_all(self):
        self.ui.mapRenderer.clear_selected_rooms()
        for room in self._map.rooms:
            self.ui.mapRenderer.select_room(room, clear_existing=False)

    def deselect_all(self):
        self.ui.mapRenderer.clear_selected_rooms()
        self.ui.mapRenderer.set_cursor_component(None)
        self.ui.componentList.clearSelection()
        self.ui.componentList.setCurrentItem(None)

    # =========================================================================
    # View operations
    # =========================================================================

    def reset_view(self):
        self.ui.mapRenderer.set_camera_position(0, 0)
        self.ui.mapRenderer.set_camera_rotation(0)
        self.ui.mapRenderer.set_camera_zoom(1.0)

    def center_on_selection(self):
        rooms = self.ui.mapRenderer.selected_rooms()
        if not rooms:
            return

        cx = sum(r.position.x for r in rooms) / len(rooms)
        cy = sum(r.position.y for r in rooms) / len(rooms)
        self.ui.mapRenderer.set_camera_position(cx, cy)

    # =========================================================================
    # Component selection
    # =========================================================================

    def selected_component(self) -> KitComponent | None:
        """Return the currently selected component from either kits or modules.

        The renderer tracks the active cursor component; prefer that when
        available so that module-derived components behave exactly like kit
        components during placement.
        """
        renderer = self.ui.mapRenderer
        if renderer.cursor_component is not None:
            return renderer.cursor_component

        # Fallback to the kits list selection for legacy behaviour.
        kit_item: QListWidgetItem | None = self.ui.componentList.currentItem()
        if kit_item is not None:
            component = kit_item.data(Qt.ItemDataRole.UserRole)
            if isinstance(component, KitComponent):
                return component

        # Finally, consider the modules list selection if present.
        if hasattr(self.ui, "moduleComponentList"):
            module_item: QListWidgetItem | None = self.ui.moduleComponentList.currentItem()
            if module_item is not None:
                component = module_item.data(Qt.ItemDataRole.UserRole)
                if isinstance(component, KitComponent):
                    return component

        return None

    def set_warp_point(self, x: float, y: float, z: float):
        self._map.warp_point = Vector3(x, y, z)

    def on_kit_selected(self):
        kit: Kit = self.ui.kitSelect.currentData()
        if not isinstance(kit, Kit):
            return
        self.ui.componentList.clear()
        for component in kit.components:
            item = QListWidgetItem(component.name)
            item.setData(Qt.ItemDataRole.UserRole, component)
            self.ui.componentList.addItem(item)

    def onComponentSelected(self, item: QListWidgetItem):
        if item is None:
            return
        component: KitComponent = item.data(Qt.ItemDataRole.UserRole)
        self.ui.componentImage.setPixmap(QPixmap.fromImage(component.image))
        self.ui.mapRenderer.set_cursor_component(component)

    # =========================================================================
    # Mouse event handlers
    # =========================================================================

    def on_mouse_moved(
        self,
        screen: Vector2,
        delta: Vector2,
        buttons: set[int],
        keys: set[int],
    ):
        self._refresh_status_bar()
        world_delta: Vector2 = self.ui.mapRenderer.to_world_delta(delta.x, delta.y)

        # Pan camera with middle mouse or LMB + Ctrl
        if Qt.MouseButton.MiddleButton in buttons or (Qt.MouseButton.LeftButton in buttons and Qt.Key.Key_Control in keys):
            self.ui.mapRenderer.pan_camera(-world_delta.x, -world_delta.y)
        # Rotate camera with RMB + Ctrl
        elif Qt.MouseButton.RightButton in buttons and Qt.Key.Key_Control in keys:
            self.ui.mapRenderer.rotate_camera(delta.x / 50)

    def on_mouse_pressed(
        self,
        screen: Vector2,
        buttons: set[int],
        keys: set[int],
    ):
        if Qt.MouseButton.LeftButton not in buttons:
            return
        if Qt.Key.Key_Control in keys:
            return  # Control is for camera pan

        renderer = self.ui.mapRenderer
        world = renderer.to_world_coords(screen.x, screen.y)

        # Check if clicking on warp point first
        if renderer.is_over_warp_point(world):
            renderer.start_warp_drag()
            return

        # Check if we're in placement mode (component selected for placing)
        if renderer.cursor_component is not None:
            # Place new room
            component: KitComponent | None = self.selected_component()
            if component is not None:
                self._place_new_room(component)
                if Qt.Key.Key_Shift not in keys:
                    renderer.set_cursor_component(None)
                    # Clear selection from both kits and modules lists so the
                    # cursor cleanly exits placement mode regardless of source.
                    self.ui.componentList.clearSelection()
                    self.ui.componentList.setCurrentItem(None)
                    if hasattr(self.ui, "moduleComponentList"):
                        self.ui.moduleComponentList.clearSelection()
                        self.ui.moduleComponentList.setCurrentItem(None)
                return  # Exit after placing room
        
        # Not in placement mode - handle room selection and dragging
        room: IndoorMapRoom | None = renderer.room_under_mouse()
        if room is not None:
            # Clicking on a room
            if room in renderer.selected_rooms():
                # Room already selected - start drag without changing selection
                renderer.start_drag(room)
            else:
                # Select room (shift to add to selection, otherwise clear existing)
                clear_existing: bool = Qt.Key.Key_Shift not in keys
                renderer.select_room(room, clear_existing=clear_existing)
                # Start drag tracking
                renderer.start_drag(room)
        else:
            # No room clicked - start marquee selection OR clear selection
            if Qt.Key.Key_Shift not in keys:
                renderer.clear_selected_rooms()
            # Start marquee selection
            renderer.start_marquee(screen)

    def on_mouse_released(
        self,
        screen: Vector2,
        buttons: set[int],
        keys: set[int],
    ):
        self.ui.mapRenderer.end_drag()

    def on_rooms_moved(
        self,
        rooms: list[IndoorMapRoom],
        old_positions: list[Vector3],
        new_positions: list[Vector3],
    ):
        """Called when rooms have been moved via drag."""
        if not rooms:
            return
        # Only create command if positions actually changed
        if any(old.distance(new) > 0.001 for old, new in zip(old_positions, new_positions)):
            cmd = MoveRoomsCommand(self._map, rooms, old_positions, new_positions)
            self._undo_stack.push(cmd)
            self._refresh_window_title()

    def on_warp_moved(
        self,
        old_position: Vector3,
        new_position: Vector3,
    ):
        """Called when warp point has been moved via drag."""
        if old_position.distance(new_position) > 0.001:
            cmd = MoveWarpCommand(self._map, old_position, new_position)
            self._undo_stack.push(cmd)
            self._refresh_window_title()

    def on_marquee_select(
        self,
        rooms: list[IndoorMapRoom],
        additive: bool,
    ):
        """Called when marquee selection completes."""
        if not additive:
            self.ui.mapRenderer.clear_selected_rooms()
        for room in rooms:
            self.ui.mapRenderer.select_room(room, clear_existing=False)

    def _place_new_room(self, component: KitComponent):
        """Place a new room at cursor position with undo support."""
        room = IndoorMapRoom(
            component,
            copy(self.ui.mapRenderer.cursor_point),
            self.ui.mapRenderer.cursor_rotation,
            flip_x=self.ui.mapRenderer.cursor_flip_x,
            flip_y=self.ui.mapRenderer.cursor_flip_y,
        )
        cmd = AddRoomCommand(self._map, room)
        self._undo_stack.push(cmd)
        self.ui.mapRenderer.cursor_rotation = 0.0
        self.ui.mapRenderer.cursor_flip_x = False
        self.ui.mapRenderer.cursor_flip_y = False
        self._refresh_window_title()

    def on_mouse_scrolled(
        self,
        delta: Vector2,
        buttons: set[int],
        keys: set[int],
    ):
        if Qt.Key.Key_Control in keys:
            self.ui.mapRenderer.zoom_in_camera(delta.y / 50)
        else:
            snap = self.ui.mapRenderer.rotation_snap
            self.ui.mapRenderer.cursor_rotation += math.copysign(snap, delta.y)

    def onMouseDoubleClicked(
        self,
        delta: Vector2,
        buttons: set[int],
        keys: set[int],
    ):
        room: IndoorMapRoom | None = self.ui.mapRenderer.room_under_mouse()
        if Qt.MouseButton.LeftButton not in buttons or room is None:
            return
        self.ui.mapRenderer.clear_selected_rooms()
        self.add_connected_to_selection(room)

    def on_context_menu(self, point: QPoint):
        world: Vector3 = self.ui.mapRenderer.to_world_coords(point.x(), point.y())
        room: IndoorMapRoom | None = self.ui.mapRenderer.room_under_mouse()
        menu = QMenu(self)

        # Room-specific actions
        if room:
            if room not in self.ui.mapRenderer.selected_rooms():
                self.ui.mapRenderer.select_room(room, clear_existing=True)

            selected = self.ui.mapRenderer.selected_rooms()
            count = len(selected)

            duplicate_action = menu.addAction(f"Duplicate ({count} room{'s' if count > 1 else ''})")
            assert duplicate_action is not None
            duplicate_action.triggered.connect(self.duplicate_selected)

            delete_action = menu.addAction(f"Delete ({count} room{'s' if count > 1 else ''})")
            assert delete_action is not None
            delete_action.triggered.connect(self.delete_selected)

            menu.addSeparator()

            # Rotation submenu
            rotate_menu = menu.addMenu("Rotate")
            assert rotate_menu is not None
            for angle in [90, 180, 270]:
                action = rotate_menu.addAction(f"{angle}°")
                assert action is not None
                action.triggered.connect(lambda _, a=angle: self._rotate_selected(a))

            # Flip submenu
            flip_menu = menu.addMenu("Flip")
            assert flip_menu is not None
            flip_x_action = flip_menu.addAction("Flip Horizontal")
            assert flip_x_action is not None
            flip_x_action.triggered.connect(lambda: self._flip_selected(True, False))
            flip_y_action = flip_menu.addAction("Flip Vertical")
            assert flip_y_action is not None
            flip_y_action.triggered.connect(lambda: self._flip_selected(False, True))

            menu.addSeparator()

        # General actions
        warp_set_action = menu.addAction("Set Warp Point Here")
        assert warp_set_action is not None
        warp_set_action.triggered.connect(lambda: self.set_warp_point(world.x, world.y, world.z))

        center_action = menu.addAction("Center View Here")
        assert center_action is not None
        center_action.triggered.connect(lambda: self.ui.mapRenderer.set_camera_position(world.x, world.y))

        menu.popup(self.ui.mapRenderer.mapToGlobal(point))

    def _rotate_selected(self, angle: float):
        rooms = self.ui.mapRenderer.selected_rooms()
        if not rooms:
            return
        old_rotations = [r.rotation for r in rooms]
        new_rotations = [(r.rotation + angle) % 360 for r in rooms]
        cmd = RotateRoomsCommand(self._map, rooms, old_rotations, new_rotations)
        self._undo_stack.push(cmd)
        self._refresh_window_title()

    def _flip_selected(self, flip_x: bool, flip_y: bool):
        rooms = self.ui.mapRenderer.selected_rooms()
        if not rooms:
            return
        cmd = FlipRoomsCommand(self._map, rooms, flip_x, flip_y)
        self._undo_stack.push(cmd)
        self._refresh_window_title()

    def keyPressEvent(self, e: QKeyEvent):  # type: ignore[reportIncompatibleMethodOverride]
        # Handle toggle keys
        if e.key() == Qt.Key.Key_G and not bool(e.modifiers()):
            self.ui.snapToGridCheck.setChecked(not self.ui.snapToGridCheck.isChecked())
        elif e.key() == Qt.Key.Key_H and not bool(e.modifiers()):
            self.ui.snapToHooksCheck.setChecked(not self.ui.snapToHooksCheck.isChecked())
        elif e.key() == Qt.Key.Key_R and not bool(e.modifiers()):
            # Quick rotate selected by rotation snap amount
            rooms = self.ui.mapRenderer.selected_rooms()
            if rooms:
                self._rotate_selected(self.ui.rotSnapSpin.value())
        elif e.key() == Qt.Key.Key_F and not bool(e.modifiers()):
            # Quick flip
            rooms = self.ui.mapRenderer.selected_rooms()
            if rooms:
                self._flip_selected(True, False)
        else:
            self.ui.mapRenderer.keyPressEvent(e)

    def keyReleaseEvent(self, e: QKeyEvent):  # type: ignore[reportIncompatibleMethodOverride]
        self.ui.mapRenderer.keyReleaseEvent(e)

    def add_connected_to_selection(self, room: IndoorMapRoom):
        self.ui.mapRenderer.select_room(room, clear_existing=False)
        for hook_index, _hook in enumerate(room.component.hooks):
            hook: IndoorMapRoom | None = room.hooks[hook_index]
            if hook is None or hook in self.ui.mapRenderer.selected_rooms():
                continue
            self.add_connected_to_selection(hook)

    def closeEvent(self, e: QCloseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle window close event - ensure proper cleanup of all resources."""
        # Stop renderer loop first
        if hasattr(self.ui, 'mapRenderer'):
            try:
                self.ui.mapRenderer._loop_active = False
                # Process events to allow renderer to stop gracefully
                QApplication.processEvents()
            except Exception:
                pass
        
        # Disconnect all signals to prevent callbacks after destruction
        try:
            # Disconnect UI signals
            if hasattr(self.ui, 'kitSelect'):
                self.ui.kitSelect.currentIndexChanged.disconnect()
            if hasattr(self.ui, 'componentList'):
                self.ui.componentList.currentItemChanged.disconnect()
            if hasattr(self.ui, 'moduleSelect'):
                self.ui.moduleSelect.currentIndexChanged.disconnect()
            if hasattr(self.ui, 'moduleComponentList'):
                self.ui.moduleComponentList.currentItemChanged.disconnect()
            
            # Disconnect renderer signals
            if hasattr(self.ui, 'mapRenderer'):
                renderer = self.ui.mapRenderer
                try:
                    renderer.customContextMenuRequested.disconnect()
                    renderer.sig_mouse_moved.disconnect()
                    renderer.sig_mouse_pressed.disconnect()
                    renderer.sig_mouse_released.disconnect()
                    renderer.sig_mouse_scrolled.disconnect()
                    renderer.sig_mouse_double_clicked.disconnect()
                    renderer.sig_rooms_moved.disconnect()
                    renderer.sig_warp_moved.disconnect()
                    renderer.sig_marquee_select.disconnect()
                except Exception:
                    pass
            
            # Disconnect undo stack signals
            if hasattr(self, '_undo_stack') and self._undo_stack is not None:
                try:
                    self._undo_stack.canUndoChanged.disconnect()
                    self._undo_stack.canRedoChanged.disconnect()
                    self._undo_stack.undoTextChanged.disconnect()
                    self._undo_stack.redoTextChanged.disconnect()
                except Exception:
                    pass
        except Exception:
            # Some signals may already be disconnected
            pass
        
        # Clear references
        self._kits.clear()
        self._clipboard.clear()
        self._current_module_kit = None
        if hasattr(self, '_module_kit_manager') and self._module_kit_manager is not None:
            try:
                self._module_kit_manager.clear_cache()
            except Exception:
                pass
        
        # Process any pending events before destruction
        QApplication.processEvents()
        
        # Call parent closeEvent (this will trigger BlenderEditorMixin cleanup if needed)
        # Wrap in try-except to handle case where widget is already being destroyed
        try:
            # Check if widget is still valid by accessing a safe property
            if hasattr(self, 'isVisible'):
                super().closeEvent(e)
            else:
                # Widget is already destroyed, just accept the event
                e.accept()
        except RuntimeError:
            # Widget has been deleted, just accept the event
            e.accept()
        except Exception:
            # Any other error, try to accept the event
            try:
                e.accept()
            except Exception:
                pass


# =============================================================================
# Renderer Widget
# =============================================================================

class IndoorMapRenderer(QWidget):
    sig_mouse_moved = QtCore.Signal(object, object, object, object)  # pyright: ignore[reportPrivateImportUsage]
    sig_mouse_scrolled = QtCore.Signal(object, object, object)  # pyright: ignore[reportPrivateImportUsage]
    sig_mouse_released = QtCore.Signal(object, object, object)  # pyright: ignore[reportPrivateImportUsage]
    sig_mouse_pressed = QtCore.Signal(object, object, object)  # pyright: ignore[reportPrivateImportUsage]
    sig_mouse_double_clicked = QtCore.Signal(object, object, object)  # pyright: ignore[reportPrivateImportUsage]
    sig_rooms_moved = QtCore.Signal(object, object, object)  # rooms, old_positions, new_positions  # pyright: ignore[reportPrivateImportUsage]
    sig_warp_moved = QtCore.Signal(object, object)  # old_position, new_position  # pyright: ignore[reportPrivateImportUsage]
    sig_marquee_select = QtCore.Signal(object, object)  # rooms selected, additive  # pyright: ignore[reportPrivateImportUsage]

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self._map: IndoorMap = IndoorMap()
        self._undo_stack: QUndoStack | None = None
        self._under_mouse_room: IndoorMapRoom | None = None
        self._selected_rooms: list[IndoorMapRoom] = []

        # Camera
        self._cam_position: Vector2 = Vector2.from_null()
        self._cam_rotation: float = 0.0
        self._cam_scale: float = 1.0

        # Cursor/placement state
        self.cursor_component: KitComponent | None = None
        self.cursor_point: Vector3 = Vector3.from_null()
        self.cursor_rotation: float = 0.0
        self.cursor_flip_x: bool = False
        self.cursor_flip_y: bool = False

        # Input state
        self._keys_down: set[int] = set()
        self._mouse_down: set[int] = set()
        self._mouse_prev: Vector2 = Vector2.from_null()

        # Drag state
        self._dragging: bool = False
        self._drag_start_positions: list[Vector3] = []
        self._drag_rooms: list[IndoorMapRoom] = []
        self._drag_mode: str = ""  # "rooms", "warp", "marquee"

        # Marquee selection state
        self._marquee_active: bool = False
        self._marquee_start: Vector2 = Vector2.from_null()
        self._marquee_end: Vector2 = Vector2.from_null()

        # Warp point drag state
        self._dragging_warp: bool = False
        self._warp_drag_start: Vector3 = Vector3.from_null()

        # Snapping options
        self.snap_to_grid: bool = False
        self.snap_to_hooks: bool = True
        self.grid_size: float = 1.0
        self.rotation_snap: float = 15.0

        # Visual options
        self.hide_magnets: bool = False
        self.show_grid: bool = False
        self.highlight_rooms_hover: bool = True

        # Snap visualization
        self._snap_indicator: SnapResult | None = None

        # Performance: dirty flag for rendering
        self._dirty: bool = True
        self._cached_walkmeshes: dict[int, BWM] = {}

        # Warp point hover detection
        self._hovering_warp: bool = False
        self.warp_point_radius: float = 1.0

        # Render loop control
        self._loop_active: bool = True
        
        # Connect to destroyed signal as safety mechanism
        # This ensures the loop stops immediately when widget is destroyed
        self.destroyed.connect(self._on_destroyed)

        self._loop()
    
    def _on_destroyed(self):
        """Called when widget is destroyed - ensures loop stops."""
        self._loop_active = False

    def _loop(self):
        """Optimized render loop - only repaint when dirty.
        
        Uses standard safety checks to prevent access violations:
        - Checks loop_active flag before any operations
        - Validates widget state before repainting
        - Handles RuntimeError from widget destruction
        - Only schedules next iteration if widget is still valid
        """
        # Primary safety check: stop if loop is deactivated
        if not self._loop_active:
            return
        
        # Secondary safety check: validate widget is still valid
        # Qt widgets can be in various states during destruction
        try:
            # Check if widget is being destroyed or already destroyed
            # QWidget.isVisible() returns False during destruction
            # parent() becomes None during destruction
            widget_valid = (
                self.isVisible() or 
                self.parent() is not None or
                hasattr(self, '_loop_active')  # Widget still has attributes
            )
            
            if not widget_valid:
                self._loop_active = False
                return
        except RuntimeError:
            # Widget is in process of destruction - Qt may raise RuntimeError
            # when accessing properties of a destroyed widget
            self._loop_active = False
            return
        
        # Perform repaint only if widget is still valid
        try:
            if self._dirty or self._dragging or self.cursor_component is not None:
                # Only repaint if widget is still valid
                if self._loop_active and widget_valid:
                    self.repaint()
                    self._dirty = False
        except (RuntimeError, AttributeError):
            # Widget may be in process of destruction
            # AttributeError can occur if widget properties are accessed during destruction
            self._loop_active = False
            return
        
        # Only schedule next loop iteration if still active and widget is valid
        if self._loop_active and widget_valid:
            try:
                QTimer.singleShot(16, self._loop)  # ~60 FPS
            except RuntimeError:
                # Cannot schedule timer if widget is being destroyed
                self._loop_active = False
                return

    def mark_dirty(self):
        """Mark the renderer as needing a repaint."""
        self._dirty = True

    def set_map(self, indoor_map: IndoorMap):
        self._map = indoor_map
        self._cached_walkmeshes.clear()
        self.mark_dirty()

    def set_undo_stack(self, undo_stack: QUndoStack):
        self._undo_stack = undo_stack

    def set_cursor_component(self, component: KitComponent | None):
        self.cursor_component = component
        self.mark_dirty()

    def select_room(self, room: IndoorMapRoom, *, clear_existing: bool):
        if clear_existing:
            self._selected_rooms.clear()
        if room in self._selected_rooms:
            self._selected_rooms.remove(room)
        self._selected_rooms.append(room)
        self.mark_dirty()

    def room_under_mouse(self) -> IndoorMapRoom | None:
        return self._under_mouse_room

    def selected_rooms(self) -> list[IndoorMapRoom]:
        return self._selected_rooms

    def clear_selected_rooms(self):
        self._selected_rooms.clear()
        self.mark_dirty()

    # =========================================================================
    # Coordinate conversions
    # =========================================================================

    def to_render_coords(self, x: float, y: float) -> Vector2:
        cos = math.cos(self._cam_rotation)
        sin = math.sin(self._cam_rotation)
        x -= self._cam_position.x
        y -= self._cam_position.y
        x2 = (x * cos - y * sin) * self._cam_scale + self.width() / 2
        y2 = (x * sin + y * cos) * self._cam_scale + self.height() / 2
        return Vector2(x2, y2)

    def to_world_coords(self, x: float, y: float) -> Vector3:
        cos = math.cos(-self._cam_rotation)
        sin = math.sin(-self._cam_rotation)
        x = (x - self.width() / 2) / self._cam_scale
        y = (y - self.height() / 2) / self._cam_scale
        x2 = x * cos - y * sin + self._cam_position.x
        y2 = x * sin + y * cos + self._cam_position.y
        return Vector3(x2, y2, 0)

    def to_world_delta(self, x: float, y: float) -> Vector2:
        cos = math.cos(-self._cam_rotation)
        sin = math.sin(-self._cam_rotation)
        x /= self._cam_scale
        y /= self._cam_scale
        x2 = x * cos - y * sin
        y2 = x * sin + y * cos
        return Vector2(x2, y2)

    # =========================================================================
    # Snapping
    # =========================================================================

    def _snap_to_grid(self, pos: Vector3) -> Vector3:
        """Snap position to grid."""
        if not self.snap_to_grid:
            return pos
        return Vector3(
            round(pos.x / self.grid_size) * self.grid_size,
            round(pos.y / self.grid_size) * self.grid_size,
            pos.z,
        )

    def _find_hook_snap(
        self,
        room: IndoorMapRoom | None,
        position: Vector3,
        component: KitComponent | None = None,
        rotation: float = 0.0,
        flip_x: bool = False,
        flip_y: bool = False,
    ) -> SnapResult:
        """Find if position can snap to a hook on existing rooms.
        
        This checks ALL possible hook pairs between the room being placed/dragged
        and existing rooms, calculating the snap position for each pair and
        returning the closest one within the snap threshold.
        """
        if not self.snap_to_hooks:
            return SnapResult(position=position, snapped=False)

        # Create a temporary room to test snapping
        if component is None and room is not None:
            component = room.component
            rotation = room.rotation
            flip_x = room.flip_x
            flip_y = room.flip_y

        if component is None:
            return SnapResult(position=position, snapped=False)

        # Create fake room for hook position calculations
        test_room = IndoorMapRoom(component, position, rotation, flip_x=flip_x, flip_y=flip_y)
        
        best_distance = float('inf')
        best_snap: SnapResult = SnapResult(position=position, snapped=False)
        # Snap threshold scales with zoom - larger when zoomed out for easier snapping
        snap_threshold = max(3.0, 5.0 / self._cam_scale)

        for existing_room in self._map.rooms:
            if room is not None and existing_room is room:
                continue
            if existing_room in self._selected_rooms:
                continue

            # Check ALL hook pairs for potential snap positions
            for test_hook in test_room.component.hooks:
                test_hook_local = test_room.hook_position(test_hook, world_offset=False)
                
                for existing_hook in existing_room.component.hooks:
                    existing_hook_world = existing_room.hook_position(existing_hook)
                    
                    # Calculate where test_room would need to be positioned
                    # so that test_hook aligns with existing_hook
                    snapped_pos = Vector3(
                        existing_hook_world.x - test_hook_local.x,
                        existing_hook_world.y - test_hook_local.y,
                        existing_hook_world.z - test_hook_local.z,
                    )

                    distance = Vector2.from_vector3(position).distance(Vector2.from_vector3(snapped_pos))
                    if distance < snap_threshold and distance < best_distance:
                        best_distance = distance
                        best_snap = SnapResult(
                            position=snapped_pos,
                            snapped=True,
                            hook_from=test_hook,
                            hook_to=existing_hook,
                            target_room=existing_room,
                        )

        return best_snap

    def get_connected_hooks(
        self,
        room1: IndoorMapRoom,
        room2: IndoorMapRoom,
    ) -> tuple[KitComponentHook | None, KitComponentHook | None]:
        """Get connected hooks between two rooms."""
        hook1: KitComponentHook | None = None
        hook2: KitComponentHook | None = None

        for hook in room1.component.hooks:
            hook_pos = room1.hook_position(hook)
            for other_hook in room2.component.hooks:
                other_hook_pos = room2.hook_position(other_hook)
                distance_2d = Vector2.from_vector3(hook_pos).distance(Vector2.from_vector3(other_hook_pos))
                if distance_2d < 1.5:  # Slightly more forgiving threshold
                    hook1 = hook
                    hook2 = other_hook

        return hook1, hook2

    def toggle_cursor_flip(self):
        if self.cursor_flip_x:
            self.cursor_flip_x = False
            self.cursor_flip_y = True
        elif self.cursor_flip_y:
            self.cursor_flip_x = False
            self.cursor_flip_y = False
        else:
            self.cursor_flip_x = True
            self.cursor_flip_y = False
        self.mark_dirty()

    # =========================================================================
    # Drag operations
    # =========================================================================

    def start_drag(self, room: IndoorMapRoom):
        """Start dragging selected rooms."""
        if room not in self._selected_rooms:
            return
        self._dragging = True
        self._drag_mode = "rooms"
        self._drag_rooms = self._selected_rooms.copy()
        self._drag_start_positions = [copy(r.position) for r in self._drag_rooms]

    def start_warp_drag(self):
        """Start dragging the warp point."""
        self._dragging_warp = True
        self._drag_mode = "warp"
        self._warp_drag_start = copy(self._map.warp_point)

    def start_marquee(self, screen_pos: Vector2):
        """Start marquee selection."""
        self._marquee_active = True
        self._drag_mode = "marquee"
        self._marquee_start = screen_pos
        self._marquee_end = screen_pos

    def end_drag(self):
        """End dragging and emit appropriate signal."""
        if self._drag_mode == "rooms" and self._dragging:
            self._dragging = False
            if self._drag_rooms:
                new_positions = [copy(r.position) for r in self._drag_rooms]
                self.sig_rooms_moved.emit(self._drag_rooms, self._drag_start_positions, new_positions)
            self._drag_rooms = []
            self._drag_start_positions = []
            self._snap_indicator = None

        elif self._drag_mode == "warp" and self._dragging_warp:
            self._dragging_warp = False
            new_pos = copy(self._map.warp_point)
            if self._warp_drag_start.distance(new_pos) > 0.001:
                self.sig_warp_moved.emit(self._warp_drag_start, new_pos)

        elif self._drag_mode == "marquee" and self._marquee_active:
            self._marquee_active = False
            # Select rooms within marquee
            rooms_in_marquee = self._get_rooms_in_marquee()
            additive = Qt.Key.Key_Shift in self._keys_down
            self.sig_marquee_select.emit(rooms_in_marquee, additive)

        self._drag_mode = ""
        self.mark_dirty()

    def _get_rooms_in_marquee(self) -> list[IndoorMapRoom]:
        """Get all rooms that intersect with the marquee rectangle."""
        # Convert screen coords to world coords
        start_world = self.to_world_coords(self._marquee_start.x, self._marquee_start.y)
        end_world = self.to_world_coords(self._marquee_end.x, self._marquee_end.y)

        min_x = min(start_world.x, end_world.x)
        max_x = max(start_world.x, end_world.x)
        min_y = min(start_world.y, end_world.y)
        max_y = max(start_world.y, end_world.y)

        selected: list[IndoorMapRoom] = []
        for room in self._map.rooms:
            # Check if room center is within marquee
            if min_x <= room.position.x <= max_x and min_y <= room.position.y <= max_y:
                selected.append(room)
                continue

            # Also check if any walkmesh vertex is within marquee
            walkmesh = self._get_room_walkmesh(room)
            for vertex in walkmesh.vertices():
                if min_x <= vertex.x <= max_x and min_y <= vertex.y <= max_y:
                    selected.append(room)
                    break

        return selected

    def is_over_warp_point(self, world_pos: Vector3) -> bool:
        """Check if world position is over the warp point."""
        return world_pos.distance(self._map.warp_point) < self.warp_point_radius

    # =========================================================================
    # Camera controls
    # =========================================================================

    def camera_zoom(self) -> float:
        return self._cam_scale

    def set_camera_zoom(self, zoom: float):
        self._cam_scale = max(zoom, 0.1)  # Allow more zoom out
        self.mark_dirty()

    def zoom_in_camera(self, zoom: float):
        self.set_camera_zoom(self._cam_scale + zoom)

    def camera_position(self) -> Vector2:
        return copy(self._cam_position)

    def set_camera_position(self, x: float, y: float):
        self._cam_position.x = x
        self._cam_position.y = y
        self.mark_dirty()

    def pan_camera(self, x: float, y: float):
        self._cam_position.x += x
        self._cam_position.y += y
        self.mark_dirty()

    def camera_rotation(self) -> float:
        return self._cam_rotation

    def set_camera_rotation(self, radians: float):
        self._cam_rotation = radians
        self.mark_dirty()

    def rotate_camera(self, radians: float):
        self._cam_rotation += radians
        self.mark_dirty()

    # =========================================================================
    # Drawing
    # =========================================================================

    def _draw_image(
        self,
        painter: QPainter,
        image: QImage,
        coords: Vector2,
        rotation: float,
        flip_x: bool,
        flip_y: bool,
    ):
        original = painter.transform()
        true_width, true_height = image.width(), image.height()
        width, height = image.width() / 10, image.height() / 10

        transform = self._apply_transformation()
        transform.translate(coords.x, coords.y)
        transform.rotate(rotation)
        transform.scale(-1.0 if flip_x else 1.0, -1.0 if flip_y else 1.0)
        transform.translate(-width / 2, -height / 2)

        painter.setTransform(transform)
        source = QRectF(0, 0, true_width, true_height)
        rect = QRectF(0, 0, width, height)
        painter.drawImage(rect, image, source)
        painter.setTransform(original)

    def _draw_room_highlight(self, painter: QPainter, room: IndoorMapRoom, alpha: int, color: QColor | None = None):
        bwm = self._get_room_walkmesh(room)
        if color is None:
            color = QColor(255, 255, 255, alpha)
        else:
            color.setAlpha(alpha)
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        for face in bwm.faces:
            path = self._build_face(face)
            painter.drawPath(path)

    def _get_room_walkmesh(self, room: IndoorMapRoom) -> BWM:
        """Get cached walkmesh for room."""
        room_id = id(room)
        if room_id not in self._cached_walkmeshes:
            self._cached_walkmeshes[room_id] = room.walkmesh()
        return self._cached_walkmeshes[room_id]

    def _invalidate_walkmesh_cache(self, room: IndoorMapRoom):
        """Invalidate cached walkmesh for a room."""
        room_id = id(room)
        self._cached_walkmeshes.pop(room_id, None)

    def _draw_grid(self, painter: QPainter):
        """Draw grid overlay."""
        if not self.show_grid:
            return

        painter.setPen(QPen(QColor(50, 50, 50), 0.05))

        # Calculate visible area
        top_left = self.to_world_coords(0, 0)
        bottom_right = self.to_world_coords(self.width(), self.height())

        min_x = min(top_left.x, bottom_right.x)
        max_x = max(top_left.x, bottom_right.x)
        min_y = min(top_left.y, bottom_right.y)
        max_y = max(top_left.y, bottom_right.y)

        # Snap to grid
        min_x = math.floor(min_x / self.grid_size) * self.grid_size
        max_x = math.ceil(max_x / self.grid_size) * self.grid_size
        min_y = math.floor(min_y / self.grid_size) * self.grid_size
        max_y = math.ceil(max_y / self.grid_size) * self.grid_size

        # Draw vertical lines
        x = min_x
        while x <= max_x:
            painter.drawLine(QPointF(x, min_y), QPointF(x, max_y))
            x += self.grid_size

        # Draw horizontal lines
        y = min_y
        while y <= max_y:
            painter.drawLine(QPointF(min_x, y), QPointF(max_x, y))
            y += self.grid_size

    def _draw_snap_indicator(self, painter: QPainter):
        """Draw snap indicator when snapping is active."""
        if self._snap_indicator is None or not self._snap_indicator.snapped:
            return

        pos = self._snap_indicator.position
        painter.setPen(QPen(QColor(0, 255, 255), 0.3))
        painter.setBrush(QColor(0, 255, 255, 100))
        painter.drawEllipse(QPointF(pos.x, pos.y), 0.8, 0.8)

    def _draw_spawn_point(self, painter: QPainter, coords: Vector3):
        # Highlight when hovering or dragging
        is_active = self._hovering_warp or self._dragging_warp
        radius = self.warp_point_radius * (1.3 if is_active else 1.0)
        alpha = 180 if is_active else 127
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 255, 0, alpha))
        painter.drawEllipse(QPointF(coords.x, coords.y), radius, radius)

        # Draw crosshair
        line_len = radius * 1.2
        painter.setPen(QPen(QColor(0, 255, 0), 0.4 if not is_active else 0.6))
        painter.drawLine(QPointF(coords.x, coords.y - line_len), QPointF(coords.x, coords.y + line_len))
        painter.drawLine(QPointF(coords.x - line_len, coords.y), QPointF(coords.x + line_len, coords.y))
        
        # Draw "W" label when active
        if is_active:
            painter.setPen(QPen(QColor(255, 255, 255), 0.1))

    def _draw_marquee(self, painter: QPainter):
        """Draw the marquee selection rectangle."""
        if not self._marquee_active:
            return
        
        # Reset transform to draw in screen coords
        painter.resetTransform()
        
        # Calculate rectangle
        x1, y1 = self._marquee_start.x, self._marquee_start.y
        x2, y2 = self._marquee_end.x, self._marquee_end.y
        
        rect = QRectF(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
        
        # Draw semi-transparent fill
        painter.setBrush(QColor(100, 150, 255, 50))
        painter.setPen(QPen(QColor(100, 150, 255), 1, Qt.PenStyle.DashLine))
        painter.drawRect(rect)

    def _build_face(self, face: BWMFace) -> QPainterPath:
        v1 = Vector2(face.v1.x, face.v1.y)
        v2 = Vector2(face.v2.x, face.v2.y)
        v3 = Vector2(face.v3.x, face.v3.y)

        path = QPainterPath()
        path.moveTo(v1.x, v1.y)
        path.lineTo(v2.x, v2.y)
        path.lineTo(v3.x, v3.y)
        path.lineTo(v1.x, v1.y)
        path.closeSubpath()
        return path

    def _apply_transformation(self) -> QTransform:
        result = QTransform()
        result.translate(self.width() / 2, self.height() / 2)
        result.rotate(math.degrees(self._cam_rotation))
        result.scale(self._cam_scale, self._cam_scale)
        result.translate(-self._cam_position.x, -self._cam_position.y)
        return result

    def paintEvent(self, e: QPaintEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        transform = self._apply_transformation()
        painter = QPainter(self)
        painter.setBrush(QColor(20, 20, 25))  # Slightly blue-tinted dark background
        painter.drawRect(0, 0, self.width(), self.height())
        painter.setTransform(transform)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        # Draw grid
        self._draw_grid(painter)

        # Draw rooms
        for room in self._map.rooms:
            self._draw_image(
                painter,
                room.component.image,
                Vector2.from_vector3(room.position),
                room.rotation,
                room.flip_x,
                room.flip_y,
            )

            # Draw hooks (magnets)
            if not self.hide_magnets:
                for hook_index, hook in enumerate(room.component.hooks):
                    if room.hooks[hook_index] is None:
                        continue  # Connected hook

                    hook_pos = room.hook_position(hook)
                    painter.setBrush(QColor(255, 80, 80))  # Brighter red
                    painter.setPen(QPen(QColor(255, 200, 200), 0.1))
                    painter.drawEllipse(QPointF(hook_pos.x, hook_pos.y), 0.4, 0.4)

        # Draw connections (green lines for connected hooks)
        for room in self._map.rooms:
            for hook_index, hook in enumerate(room.component.hooks):
                if room.hooks[hook_index] is None:
                    continue
                hook_pos = room.hook_position(hook)
                xd = math.cos(math.radians(hook.rotation + room.rotation)) * hook.door.width / 2
                yd = math.sin(math.radians(hook.rotation + room.rotation)) * hook.door.width / 2
                painter.setPen(QPen(QColor(80, 255, 80), 2 / self._cam_scale))
                painter.drawLine(
                    QPointF(hook_pos.x - xd, hook_pos.y - yd),
                    QPointF(hook_pos.x + xd, hook_pos.y + yd),
                )

        # Draw cursor preview
        if self.cursor_component:
            painter.setOpacity(0.6)
            self._draw_image(
                painter,
                self.cursor_component.image,
                Vector2.from_vector3(self.cursor_point),
                self.cursor_rotation,
                self.cursor_flip_x,
                self.cursor_flip_y,
            )
            painter.setOpacity(1.0)

        # Draw snap indicator
        self._draw_snap_indicator(painter)

        # Draw hover highlight
        if self._under_mouse_room and self._under_mouse_room not in self._selected_rooms:
            self._draw_room_highlight(painter, self._under_mouse_room, 40, QColor(100, 150, 255))

        # Draw selection highlights
        for room in self._selected_rooms:
            self._draw_room_highlight(painter, room, 80, QColor(255, 200, 100))

        # Draw spawn point (warp point)
        self._draw_spawn_point(painter, self._map.warp_point)

        # Draw marquee selection (in screen space, so after transform reset)
        self._draw_marquee(painter)

    # =========================================================================
    # Events
    # =========================================================================

    def wheelEvent(self, e: QWheelEvent):
        self.sig_mouse_scrolled.emit(
            Vector2(e.angleDelta().x(), e.angleDelta().y()),
            e.buttons(),
            self._keys_down,
        )
        self.mark_dirty()

    def mouseMoveEvent(self, e: QMouseEvent):
        event_pos = e.pos()
        coords = Vector2(event_pos.x(), event_pos.y())
        coords_delta = Vector2(coords.x - self._mouse_prev.x, coords.y - self._mouse_prev.y)
        self._mouse_prev = coords
        self.sig_mouse_moved.emit(coords, coords_delta, self._mouse_down, self._keys_down)

        world = self.to_world_coords(coords.x, coords.y)
        self.cursor_point = world

        # Update warp point hover state
        self._hovering_warp = self.is_over_warp_point(world)

        # Handle marquee selection
        if self._marquee_active:
            self._marquee_end = coords
            self.mark_dirty()
            return

        # Handle warp point dragging
        if self._dragging_warp:
            world_delta = self.to_world_delta(coords_delta.x, coords_delta.y)
            self._map.warp_point.x += world_delta.x
            self._map.warp_point.y += world_delta.y
            # Apply grid snap to warp point if enabled
            if self.snap_to_grid:
                self._map.warp_point = self._snap_to_grid(self._map.warp_point)
            self.mark_dirty()
            return

        # Handle room dragging
        if self._dragging and self._drag_rooms:
            world_delta = self.to_world_delta(coords_delta.x, coords_delta.y)
            
            # Move all selected rooms by delta first
            for room in self._drag_rooms:
                room.position.x += world_delta.x
                room.position.y += world_delta.y
                self._invalidate_walkmesh_cache(room)

            # Get the primary room for snapping calculations
            active_room = self._drag_rooms[-1] if self._drag_rooms else None
            snapped = False

            # Try hook snapping first (takes priority if enabled)
            if active_room and self.snap_to_hooks:
                snap_result = self._find_hook_snap(active_room, active_room.position)
                if snap_result.snapped:
                    # Calculate offset and apply to all rooms
                    offset_x = snap_result.position.x - active_room.position.x
                    offset_y = snap_result.position.y - active_room.position.y
                    for room in self._drag_rooms:
                        room.position.x += offset_x
                        room.position.y += offset_y
                        self._invalidate_walkmesh_cache(room)
                    self._snap_indicator = snap_result
                    snapped = True
                else:
                    self._snap_indicator = None

            # Apply grid snapping if enabled (and not already snapped to hook)
            if self.snap_to_grid and not snapped and active_room:
                # Snap the active room to grid, then move others by same offset
                old_pos = copy(active_room.position)
                snapped_pos = self._snap_to_grid(active_room.position)
                offset_x = snapped_pos.x - old_pos.x
                offset_y = snapped_pos.y - old_pos.y
                
                for room in self._drag_rooms:
                    room.position.x += offset_x
                    room.position.y += offset_y
                    self._invalidate_walkmesh_cache(room)

            self._map.rebuild_room_connections()
            self.mark_dirty()
            return

        # Handle cursor component snapping
        if self.cursor_component:
            snapped = False
            
            # Try hook snap first (it's more important for connections)
            if self.snap_to_hooks:
                snap_result = self._find_hook_snap(
                    None,
                self.cursor_point,
                    self.cursor_component,
                self.cursor_rotation,
                    self.cursor_flip_x,
                    self.cursor_flip_y,
                )
                if snap_result.snapped:
                    self.cursor_point = snap_result.position
                    self._snap_indicator = snap_result
                    snapped = True
                else:
                    self._snap_indicator = None

            # Apply grid snap if not snapped to hook
            if self.snap_to_grid and not snapped:
                self.cursor_point = self._snap_to_grid(self.cursor_point)
                
            self.mark_dirty()

        # Find room under mouse
        self._under_mouse_room = None
        for room in reversed(self._map.rooms):  # Check topmost first
            walkmesh = self._get_room_walkmesh(room)
            if walkmesh.faceAt(world.x, world.y):
                self._under_mouse_room = room
                break
        self.mark_dirty()

    def mousePressEvent(self, e: QMouseEvent):
        event_mouse_button = e.button()
        if event_mouse_button is None:
            return
        self._mouse_down.add(event_mouse_button)
        event_pos = e.pos()
        coords = Vector2(event_pos.x(), event_pos.y())
        self.sig_mouse_pressed.emit(coords, self._mouse_down, self._keys_down)

    def mouseReleaseEvent(self, e: QMouseEvent):
        event_mouse_button = e.button()
        if event_mouse_button is None:
            return
        self._mouse_down.discard(event_mouse_button)
        event_pos = e.pos()
        coords = Vector2(event_pos.x(), event_pos.y())
        self.sig_mouse_released.emit(coords, self._mouse_down, self._keys_down)

    def mouseDoubleClickEvent(self, e: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        event_mouse_button = e.button()
        if event_mouse_button is None:
            return
        mouse_down = copy(self._mouse_down)
        mouse_down.add(event_mouse_button)
        self.sig_mouse_double_clicked.emit(Vector2(e.x(), e.y()), mouse_down, self._keys_down)

    def keyPressEvent(self, e: QKeyEvent):
        self._keys_down.add(e.key())
        self.mark_dirty()

    def keyReleaseEvent(self, e: QKeyEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        self._keys_down.discard(e.key())
        self.mark_dirty()

    def closeEvent(self, e: QCloseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle widget close event - stop render loop and clean up resources."""
        # Stop the render loop immediately - this prevents any further timer callbacks
        # Setting this flag ensures _loop() will return early and not schedule more timers
        self._loop_active = False
        
        # Disconnect all signals to prevent callbacks after destruction
        try:
            self.sig_mouse_moved.disconnect()
            self.sig_mouse_scrolled.disconnect()
            self.sig_mouse_released.disconnect()
            self.sig_mouse_pressed.disconnect()
            self.sig_mouse_double_clicked.disconnect()
            self.sig_rooms_moved.disconnect()
            self.sig_warp_moved.disconnect()
            self.sig_marquee_select.disconnect()
        except Exception:
            # Signals may already be disconnected
            pass
        
        # Clear references to prevent circular dependencies
        self._map = IndoorMap()
        self._undo_stack = None
        self._selected_rooms.clear()
        self._cached_walkmeshes.clear()
        self.cursor_component = None
        
        # Process any pending events before destruction
        QApplication.processEvents()
        
        # Call parent closeEvent
        # Wrap in try-except to handle case where widget is already being destroyed
        try:
            if hasattr(self, 'isVisible'):
                super().closeEvent(e)
            else:
                e.accept()
        except RuntimeError:
            e.accept()
        except Exception:
            try:
                e.accept()
            except Exception:
                pass


# =============================================================================
# Kit Downloader Dialog
# =============================================================================

class KitDownloader(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
            & ~Qt.WindowType.WindowMinMaxButtonsHint,
        )

        from toolset.uic.qtpy.dialogs.indoor_downloader import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)
        
        self.ui.downloadAllButton.clicked.connect(self._download_all_button_pressed)
        self._setup_downloads()

    def _setup_downloads(self):
        update_info_data: Exception | dict[str, Any] = get_remote_toolset_update_info(
            use_beta_channel=GlobalSettings().useBetaChannel,
        )
        try:
            if not isinstance(update_info_data, dict):
                raise update_info_data  # noqa: TRY301

            for kit_name, kit_dict in update_info_data["kits"].items():
                kit_id = kit_dict["id"]
                kit_path = Path(f"kits/{kit_id}.json")
                if kit_path.is_file():
                    button = QPushButton("Already Downloaded")
                    button.setEnabled(True)
                    local_kit_dict = None
                    try:
                        local_kit_dict = json.loads(kit_path.read_text())
                    except Exception as e:  # noqa: BLE001
                        print(universal_simplify_exception(e), "\n in _setup_downloads for kit update check")
                        button.setText("Missing JSON - click to redownload.")
                        button.setEnabled(True)
                    else:
                        local_kit_version = str(local_kit_dict["version"])
                        retrieved_kit_version = str(kit_dict["version"])
                        if is_remote_version_newer(local_kit_version, retrieved_kit_version) is not False:
                            button.setText("Update Available")
                            button.setEnabled(True)
                else:
                    button = QPushButton("Download")
                button.clicked.connect(
                    lambda _=None, kit_dict=kit_dict, button=button: self._download_button_pressed(button, kit_dict)
                )

                layout: QFormLayout | None = self.ui.groupBox.layout()
                if layout is None:
                    msg = "Kit downloader group box layout is None"
                    raise RuntimeError(msg)  # noqa: TRY301
                layout.addRow(kit_name, button)
        except Exception as e:  # noqa: BLE001
            error_msg = str(universal_simplify_exception(e)).replace("\n", "<br>")
            err_msg_box = QMessageBox(
                QMessageBox.Icon.Information,
                "An unexpected error occurred while setting up the kit downloader.",
                error_msg,
                QMessageBox.StandardButton.Ok,
                parent=None,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            )
            err_msg_box.setWindowIcon(self.windowIcon())
            err_msg_box.exec()

    def _download_button_pressed(self, button: QPushButton, info_dict: dict):
        button.setText("Downloading")
        button.setEnabled(False)

        def task() -> bool:
            try:
                return self._download_kit(info_dict["id"])
            except Exception as e:
                print(format_exception_with_variables(e))
                raise

        if is_debug_mode() and not is_frozen():
            try:
                task()
                button.setText("Download Complete")
            except Exception as e:  # noqa: BLE001
                print(format_exception_with_variables(e, message="Error downloading kit"))
                button.setText("Download Failed")
                button.setEnabled(True)
        else:
            loader = AsyncLoader(self, "Downloading Kit...", task, "Failed to download.")
            if loader.exec():
                button.setText("Download Complete")
            else:
                button.setText("Download Failed")
                button.setEnabled(True)

    def _download_all_kits(self) -> bool:
        kits_path = Path("kits").resolve()
        kits_path.mkdir(parents=True, exist_ok=True)
        kits_zip_path = Path("kits.zip")
        
        update_info_data: Exception | dict[str, Any] = get_remote_toolset_update_info(
            use_beta_channel=GlobalSettings().useBetaChannel,
        )
        
        if isinstance(update_info_data, Exception):
            print(f"Failed to get update info: {update_info_data}")
            return False
        
        kits_config = update_info_data.get("kits", {})
        repository = kits_config.get("repository", "th3w1zard1/ToolsetData")
        release_tag = kits_config.get("release_tag", "latest")
        
        try:
            owner, repo = repository.split("/")
            print(f"Downloading kits.zip from {repository} release {release_tag}...")
            download_github_release_asset(
                owner=owner,
                repo=repo,
                tag_name=release_tag,
                asset_name="kits.zip",
                local_path=kits_zip_path,
            )
        except Exception as e:
            print(format_exception_with_variables(e, message="Failed to download kits.zip"))
            return False
        
        try:
            with zipfile.ZipFile(kits_zip_path) as zip_file:
                print(f"Extracting all kits to {kits_path}")
                with TemporaryDirectory() as tmp_dir:
                    tempdir_path = Path(tmp_dir)
                    zip_file.extractall(tmp_dir)
                    
                    for item in tempdir_path.iterdir():
                        if item.is_dir():
                            dst_path = kits_path / item.name
                            if dst_path.is_dir():
                                print(f"Removing old {item.name} kit...")
                                shutil.rmtree(dst_path)
                            print(f"Copying {item.name} kit...")
                            shutil.copytree(item, dst_path)
                        elif item.suffix.lower() == ".json" and item.stem != "available_kits":
                            dst_file = kits_path / item.name
                            print(f"Copying {item.name}...")
                            shutil.copy(item, dst_file)
        except Exception as e:
            print(format_exception_with_variables(e, message="Failed to extract kits"))
            return False
        finally:
            if kits_zip_path.is_file():
                kits_zip_path.unlink()
        
        return True
    
    def _download_all_button_pressed(self):
        self.ui.downloadAllButton.setText("Downloading All...")
        self.ui.downloadAllButton.setEnabled(False)
        
        def task() -> bool:
            try:
                return self._download_all_kits()
            except Exception as e:
                print(format_exception_with_variables(e))
                raise
        
        if is_debug_mode() and not is_frozen():
            try:
                task()
                self.ui.downloadAllButton.setText("Download All Complete")
                self._refresh_kit_buttons()
            except Exception as e:  # noqa: BLE001
                print(format_exception_with_variables(e, message="Error downloading all kits"))
                self.ui.downloadAllButton.setText("Download All Failed")
                self.ui.downloadAllButton.setEnabled(True)
        else:
            loader = AsyncLoader(self, "Downloading All Kits...", task, "Failed to download all kits.")
            if loader.exec():
                self.ui.downloadAllButton.setText("Download All Complete")
                self._refresh_kit_buttons()
            else:
                self.ui.downloadAllButton.setText("Download All Failed")
                self.ui.downloadAllButton.setEnabled(True)
    
    def _refresh_kit_buttons(self):
        layout: QFormLayout | None = self.ui.groupBox.layout()
        if layout is None:
            return
        
        for i in range(layout.rowCount()):
            item = layout.itemAt(i, QFormLayout.ItemRole.FieldRole)
            if item and isinstance(item.widget(), QPushButton):
                button: QPushButton = item.widget()
                button.setText("Already Downloaded")
                button.setEnabled(False)

    def _download_kit(self, kit_id: str) -> bool:
        kits_path = Path("kits").resolve()
        kits_path.mkdir(parents=True, exist_ok=True)
        kits_zip_path = Path("kits.zip")
        
        update_info_data: Exception | dict[str, Any] = get_remote_toolset_update_info(
            use_beta_channel=GlobalSettings().useBetaChannel,
        )
        
        if isinstance(update_info_data, Exception):
            print(f"Failed to get update info: {update_info_data}")
            return False
        
        kits_config = update_info_data.get("kits", {})
        repository = kits_config.get("repository", "th3w1zard1/ToolsetData")
        release_tag = kits_config.get("release_tag", "latest")
        
        try:
            owner, repo = repository.split("/")
            print(f"Downloading kits.zip from {repository} release {release_tag}...")
            download_github_release_asset(
                owner=owner,
                repo=repo,
                tag_name=release_tag,
                asset_name="kits.zip",
                local_path=kits_zip_path,
            )
        except Exception as e:
            print(format_exception_with_variables(e, message="Failed to download kits.zip"))
            return False

        try:
            with zipfile.ZipFile(kits_zip_path) as zip_file:
                print(f"Extracting {kit_id} kit to {kits_path}")
                with TemporaryDirectory() as tmp_dir:
                    tempdir_path = Path(tmp_dir)
                    zip_file.extractall(tmp_dir)
                    src_path = tempdir_path / kit_id
                    this_kit_dst_path = kits_path / kit_id
                    
                    if not src_path.exists():
                        msg = f"Kit '{kit_id}' not found in kits.zip"
                        print(msg)
                        return False
                    
                    print(f"Copying '{src_path}' to '{this_kit_dst_path}'...")
                    if this_kit_dst_path.is_dir():
                        print(f"Deleting old {kit_id} kit folder/files...")
                        shutil.rmtree(this_kit_dst_path)
                    shutil.copytree(src_path, str(this_kit_dst_path))
                    
                    this_kit_json_filename = f"{kit_id}.json"
                    src_kit_json_path = tempdir_path / this_kit_json_filename
                    if not src_kit_json_path.is_file():
                        msg = f"Kit '{kit_id}' is missing the '{this_kit_json_filename}' file, cannot complete download"
                        print(msg)
                        return False
                    shutil.copy(src_kit_json_path, kits_path / this_kit_json_filename)
        except Exception as e:
            print(format_exception_with_variables(e, message=f"Failed to extract kit {kit_id}"))
            return False
        finally:
            if kits_zip_path.is_file():
                kits_zip_path.unlink()
        
        return True
