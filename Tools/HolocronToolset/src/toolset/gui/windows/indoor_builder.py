from __future__ import annotations

import json
import math
import os
import shutil
import zipfile

from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any, Callable, TextIO, cast

import qtpy

from qtpy import QtCore
from qtpy.QtCore import QEvent, QPoint, QPointF, QRectF, QSize, QTimer, Qt
from qtpy.QtGui import QColor, QIcon, QImage, QKeyEvent, QMouseEvent, QPainter, QPainterPath, QPen, QPixmap, QShortcut, QTransform, QWheelEvent
from qtpy.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QProgressDialog,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

if qtpy.QT5:
    from qtpy.QtGui import QCloseEvent, QPaintEvent
    from qtpy.QtWidgets import QUndoCommand, QUndoStack  # type: ignore[reportPrivateImportUsage]
elif qtpy.QT6:
    from qtpy.QtGui import QPaintEvent, QUndoCommand, QUndoStack  # type: ignore[assignment]  # pyright: ignore[reportPrivateImportUsage]

    try:
        from qtpy.QtGui import QCloseEvent
    except ImportError:
        # Fallback for Qt6 where QCloseEvent may be in QtCore
        from qtpy.QtCore import QCloseEvent  # type: ignore[assignment, attr-defined, no-redef]
else:
    raise ValueError(f"Invalid QT_API: '{qtpy.API_NAME}'")

from pykotor.common.misc import Color  # type: ignore[reportPrivateImportUsage]
from pykotor.common.stream import BinaryWriter  # type: ignore[reportPrivateImportUsage]
from pykotor.resource.formats.bwm import BWM, bytes_bwm, read_bwm  # type: ignore[reportPrivateImportUsage]
from pykotor.tools.indoormap import IndoorMap, IndoorMapRoom, extract_indoor_from_module_name
from toolset.blender import BlenderEditorMode, ConnectionState, check_blender_and_ask, get_blender_settings
from toolset.blender.integration import BlenderEditorMixin
from toolset.config import get_remote_toolset_update_info, is_remote_version_newer
from toolset.data.indoorkit import Kit, KitComponent, KitComponentHook, ModuleKit, ModuleKitManager, load_kits
from toolset.data.installation import HTInstallation
from toolset.gui.common.filters import NoScrollEventFilter
from toolset.gui.dialogs.asyncloader import AsyncLoader
from toolset.gui.dialogs.indoor_settings import IndoorMapSettings
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.gui.widgets.settings.widgets.module_designer import ModuleDesignerSettings
from toolset.gui.windows.help import HelpWindow
from toolset.gui.windows.indoor_builder_constants import (
    BACKGROUND_COLOR,
    COMPONENT_PREVIEW_SCALE,
    CONNECTION_LINE_COLOR,
    CONNECTION_LINE_WIDTH_SCALE,
    CURSOR_HOOK_ALPHA,
    CURSOR_PREVIEW_ALPHA,
    DEFAULT_CAMERA_POSITION_X,
    DEFAULT_CAMERA_POSITION_Y,
    DEFAULT_CAMERA_ROTATION,
    DEFAULT_CAMERA_ZOOM,
    DEFAULT_GRID_SIZE,
    DEFAULT_ROTATION_SNAP,
    DUPLICATE_OFFSET_X,
    DUPLICATE_OFFSET_Y,
    DUPLICATE_OFFSET_Z,
    GRID_COLOR,
    GRID_PEN_WIDTH,
    HOOK_COLOR_CONNECTED,
    HOOK_COLOR_SELECTED,
    HOOK_COLOR_UNCONNECTED,
    HOOK_CONNECTION_THRESHOLD,
    HOOK_DISPLAY_RADIUS,
    HOOK_HOVER_RADIUS,
    HOOK_PEN_COLOR_CONNECTED,
    HOOK_PEN_COLOR_SELECTED,
    HOOK_PEN_COLOR_UNCONNECTED,
    HOOK_SELECTED_RADIUS,
    HOOK_SNAP_BASE_THRESHOLD,
    HOOK_SNAP_DISCONNECT_BASE_THRESHOLD,
    HOOK_SNAP_DISCONNECT_SCALE_FACTOR,
    HOOK_SNAP_SCALE_FACTOR,
    MARQUEE_BORDER_COLOR,
    MARQUEE_FILL_COLOR,
    MARQUEE_MOVE_THRESHOLD_PIXELS,
    MAX_CAMERA_ZOOM,
    MIN_CAMERA_ZOOM,
    POSITION_CHANGE_EPSILON,
    RENDER_INTERVAL_MS,
    ROOM_HOVER_ALPHA,
    ROOM_HOVER_COLOR,
    ROOM_SELECTED_ALPHA,
    ROOM_SELECTED_COLOR,
    ROTATION_CHANGE_EPSILON,
    SNAP_INDICATOR_ALPHA,
    SNAP_INDICATOR_COLOR,
    SNAP_INDICATOR_PEN_WIDTH,
    SNAP_INDICATOR_RADIUS,
    WARP_POINT_ACTIVE_SCALE,
    WARP_POINT_ALPHA_ACTIVE,
    WARP_POINT_ALPHA_NORMAL,
    WARP_POINT_COLOR,
    WARP_POINT_CROSSHAIR_SCALE,
    WARP_POINT_PEN_WIDTH_ACTIVE,
    WARP_POINT_PEN_WIDTH_NORMAL,
    WARP_POINT_RADIUS,
    ZOOM_STEP_FACTOR,
    ZOOM_WHEEL_SENSITIVITY,
    DragMode,
)
from toolset.utils.misc import get_qt_button_string, get_qt_key_string
from utility.common.geometry import SurfaceMaterial, Vector2, Vector3
from utility.error_handling import format_exception_with_variables, universal_simplify_exception
from utility.misc import is_debug_mode
from utility.system.os_helper import is_frozen
from utility.updater.github import download_github_release_asset

if TYPE_CHECKING:
    from qtpy.QtGui import QFocusEvent

    from pykotor.resource.formats.bwm import BWMFace  # pyright: ignore[reportMissingImports]
    from toolset.data.indoormap import MissingRoomInfo


# =============================================================================
# Undo/Redo Commands
# =============================================================================


class AddRoomCommand(QUndoCommand):
    """Command to add a room to the map."""

    def __init__(
        self,
        indoor_map: IndoorMap,
        room: IndoorMapRoom,
        invalidate_cb: Callable[[list[IndoorMapRoom]], None] | None = None,
    ):
        super().__init__("Add Room")
        self.indoor_map = indoor_map
        self.room = room
        self._invalidate_cb = invalidate_cb

    def undo(self):
        if self.room in self.indoor_map.rooms:
            self.indoor_map.rooms.remove(self.room)
            self.indoor_map.rebuild_room_connections()
            if self._invalidate_cb:
                self._invalidate_cb([self.room])

    def redo(self):
        if self.room not in self.indoor_map.rooms:
            self.indoor_map.rooms.append(self.room)
            self.indoor_map.rebuild_room_connections()
            if self._invalidate_cb:
                self._invalidate_cb([self.room])


class DeleteRoomsCommand(QUndoCommand):
    """Command to delete rooms from the map."""

    def __init__(
        self,
        indoor_map: IndoorMap,
        rooms: list[IndoorMapRoom],
        invalidate_cb: Callable[[list[IndoorMapRoom]], None] | None = None,
    ):
        super().__init__(f"Delete {len(rooms)} Room(s)")
        self.indoor_map = indoor_map
        self.rooms = rooms.copy()
        self._invalidate_cb = invalidate_cb
        # Store indices for proper re-insertion order
        self.indices = [indoor_map.rooms.index(r) for r in rooms if r in indoor_map.rooms]

    def undo(self):
        # Re-add rooms in original order
        for idx, room in zip(sorted(self.indices), self.rooms):
            if room not in self.indoor_map.rooms:
                self.indoor_map.rooms.insert(idx, room)
        self.indoor_map.rebuild_room_connections()
        if self._invalidate_cb:
            self._invalidate_cb(self.rooms)

    def redo(self):
        for room in self.rooms:
            if room in self.indoor_map.rooms:
                self.indoor_map.rooms.remove(room)
        self.indoor_map.rebuild_room_connections()
        if self._invalidate_cb:
            self._invalidate_cb(self.rooms)
        # Note: Selected hook validation should be handled by the renderer


class MoveRoomsCommand(QUndoCommand):
    """Command to move rooms."""

    def __init__(
        self,
        indoor_map: IndoorMap,
        rooms: list[IndoorMapRoom],
        old_positions: list[Vector3],
        new_positions: list[Vector3],
        invalidate_cb: Callable[[list[IndoorMapRoom]], None] | None = None,
    ):
        super().__init__(f"Move {len(rooms)} Room(s)")
        self.indoor_map = indoor_map
        self.rooms = rooms.copy()
        self.old_positions = [Vector3(*p) for p in old_positions]
        self.new_positions = [Vector3(*p) for p in new_positions]
        self._invalidate_cb = invalidate_cb

    def undo(self):
        for room, pos in zip(self.rooms, self.old_positions):
            room.position = Vector3(*pos)
        self.indoor_map.rebuild_room_connections()
        if self._invalidate_cb:
            self._invalidate_cb(self.rooms)

    def redo(self):
        for room, pos in zip(self.rooms, self.new_positions):
            room.position = Vector3(*pos)
        self.indoor_map.rebuild_room_connections()
        if self._invalidate_cb:
            self._invalidate_cb(self.rooms)


class RotateRoomsCommand(QUndoCommand):
    """Command to rotate rooms."""

    def __init__(
        self,
        indoor_map: IndoorMap,
        rooms: list[IndoorMapRoom],
        old_rotations: list[float],
        new_rotations: list[float],
        invalidate_cb: Callable[[list[IndoorMapRoom]], None] | None = None,
    ):
        super().__init__(f"Rotate {len(rooms)} Room(s)")
        self.indoor_map = indoor_map
        self.rooms = rooms.copy()
        self.old_rotations = old_rotations.copy()
        self.new_rotations = new_rotations.copy()
        self._invalidate_cb = invalidate_cb

    def undo(self):
        for room, rot in zip(self.rooms, self.old_rotations):
            room.rotation = rot
        self.indoor_map.rebuild_room_connections()
        if self._invalidate_cb:
            self._invalidate_cb(self.rooms)

    def redo(self):
        for room, rot in zip(self.rooms, self.new_rotations):
            room.rotation = rot
        self.indoor_map.rebuild_room_connections()
        if self._invalidate_cb:
            self._invalidate_cb(self.rooms)


class FlipRoomsCommand(QUndoCommand):
    """Command to flip rooms."""

    def __init__(
        self,
        indoor_map: IndoorMap,
        rooms: list[IndoorMapRoom],
        flip_x: bool,
        flip_y: bool,
        invalidate_cb: Callable[[list[IndoorMapRoom]], None] | None = None,
    ):
        super().__init__(f"Flip {len(rooms)} Room(s)")
        self.indoor_map = indoor_map
        self.rooms = rooms.copy()
        self.flip_x = flip_x
        self.flip_y = flip_y
        self._invalidate_cb = invalidate_cb
        # Store original states
        self.old_flip_x = [r.flip_x for r in rooms]
        self.old_flip_y = [r.flip_y for r in rooms]

    def undo(self):
        for room, fx, fy in zip(self.rooms, self.old_flip_x, self.old_flip_y):
            room.flip_x = fx
            room.flip_y = fy
        self.indoor_map.rebuild_room_connections()
        if self._invalidate_cb:
            self._invalidate_cb(self.rooms)

    def redo(self):
        for room in self.rooms:
            if self.flip_x:
                room.flip_x = not room.flip_x
            if self.flip_y:
                room.flip_y = not room.flip_y
        self.indoor_map.rebuild_room_connections()
        if self._invalidate_cb:
            self._invalidate_cb(self.rooms)


class DuplicateRoomsCommand(QUndoCommand):
    """Command to duplicate rooms."""

    def __init__(
        self,
        indoor_map: IndoorMap,
        rooms: list[IndoorMapRoom],
        offset: Vector3,
        invalidate_cb: Callable[[list[IndoorMapRoom]], None] | None = None,
    ):
        super().__init__(f"Duplicate {len(rooms)} Room(s)")
        self.indoor_map = indoor_map
        self.original_rooms = rooms.copy()
        self.offset = offset
        self._invalidate_cb = invalidate_cb
        # Create duplicates
        self.duplicates: list[IndoorMapRoom] = []
        for room in rooms:
            # Deep copy component so hooks can be edited independently
            component_copy = deepcopy(room.component)
            new_room = IndoorMapRoom(
                component_copy,
                Vector3(room.position.x + offset.x, room.position.y + offset.y, room.position.z + offset.z),
                room.rotation,
                flip_x=room.flip_x,
                flip_y=room.flip_y,
            )
            new_room.walkmesh_override = deepcopy(room.walkmesh_override) if room.walkmesh_override is not None else None
            # Initialize hooks connections list to match hooks length
            new_room.hooks = [None] * len(component_copy.hooks)
            self.duplicates.append(new_room)

    def undo(self):
        for room in self.duplicates:
            if room in self.indoor_map.rooms:
                self.indoor_map.rooms.remove(room)
        self.indoor_map.rebuild_room_connections()
        if self._invalidate_cb:
            self._invalidate_cb(self.duplicates)

    def redo(self):
        for room in self.duplicates:
            if room not in self.indoor_map.rooms:
                self.indoor_map.rooms.append(room)
        self.indoor_map.rebuild_room_connections()
        if self._invalidate_cb:
            self._invalidate_cb(self.duplicates)


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
        self.old_position = Vector3(*old_position)
        self.new_position = Vector3(*new_position)

    def undo(self):
        self.indoor_map.warp_point = Vector3(*self.old_position)

    def redo(self):
        self.indoor_map.warp_point = Vector3(*self.new_position)


class PaintWalkmeshCommand(QUndoCommand):
    """Command to apply material changes to walkmesh faces."""

    def __init__(
        self,
        rooms: list[IndoorMapRoom],
        face_indices: list[int],
        old_materials: list[SurfaceMaterial],
        new_materials: list[SurfaceMaterial],
        invalidate_cb,
    ):
        super().__init__(f"Paint {len(face_indices)} Face(s)")
        self.rooms: list[IndoorMapRoom] = rooms
        self.face_indices: list[int] = face_indices
        self.old_materials: list[SurfaceMaterial] = old_materials
        self.new_materials: list[SurfaceMaterial] = new_materials
        self._invalidate_cb: Callable[[list[IndoorMapRoom]], None] = invalidate_cb

    def _apply(self, materials: list[SurfaceMaterial]):
        for room, face_index, material in zip(self.rooms, self.face_indices, materials):
            # Ensure we have a writable walkmesh override
            if room.walkmesh_override is None:
                room.walkmesh_override = deepcopy(room.component.bwm)
            base_bwm = room.walkmesh_override
            if 0 <= face_index < len(base_bwm.faces):
                base_bwm.faces[face_index].material = material
        self._invalidate_cb(self.rooms)

    def undo(self):
        self._apply(self.old_materials)

    def redo(self):
        self._apply(self.new_materials)


class ResetWalkmeshCommand(QUndoCommand):
    """Command to reset walkmesh overrides for rooms."""

    def __init__(
        self,
        rooms: list[IndoorMapRoom],
        invalidate_cb,
    ):
        super().__init__(f"Reset Walkmesh ({len(rooms)} Room(s))")
        self.rooms: list[IndoorMapRoom] = rooms
        self._invalidate_cb: Callable[[list[IndoorMapRoom]], None] = invalidate_cb
        self._previous_overrides: list[BWM | None] = [None if room.walkmesh_override is None else deepcopy(room.walkmesh_override) for room in rooms]

    def undo(self):
        for room, previous in zip(self.rooms, self._previous_overrides):
            room.walkmesh_override = None if previous is None else deepcopy(previous)
        self._invalidate_cb(self.rooms)

    def redo(self):
        for room in self.rooms:
            room.clear_walkmesh_override()
        self._invalidate_cb(self.rooms)


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
    walkmesh_override: bytes | None = None


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
        self._blender_choice_made: bool = False
        self._view_stack: QStackedWidget | None = None
        self._blender_placeholder: QWidget | None = None
        self._blender_log_buffer: deque[str] = deque(maxlen=500)
        self._blender_log_path: Path | None = None
        self._blender_log_handle: TextIO | None = None
        self._blender_progress_dialog: QProgressDialog | None = None
        self._blender_log_view: QPlainTextEdit | None = None
        self._blender_connected_once: bool = False
        self._room_id_lookup: dict[int, IndoorMapRoom] = {}
        self._transform_sync_in_progress: bool = False
        self._property_sync_in_progress: bool = False

        self._installation: HTInstallation | None = installation
        self._kits: list[Kit] = []
        self._map: IndoorMap = IndoorMap()
        self._filepath: os.PathLike | str = ""
        self._preview_source_image: QImage | None = None

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

        # Get mainSplitter - handle cases where it might not exist (new UI uses dock widgets)
        # Fallback to finding it by object name if direct attribute access fails
        main_splitter = getattr(self.ui, "mainSplitter", None)
        if main_splitter is None:
            main_splitter = self.findChild(QSplitter, "mainSplitter")
            if main_splitter is None:
                # Last resort: find it in the central widget
                main_splitter = self.centralWidget().findChild(QSplitter, "mainSplitter")  # pyright: ignore[reportOptionalMemberAccess]
            if main_splitter is not None:
                # Store it for future access
                self.ui.mainSplitter = main_splitter

        if main_splitter is not None:
            # Set initial splitter sizes (left panel ~250px, rest to map renderer)
            # Set initial sizes: left panel gets ~250 pixels (a few inches), rest goes to map renderer
            total_width = self.width() if self.width() > 0 else 1024
            left_panel_size = min(300, max(200, total_width // 4))  # 200-300px or 1/4 of width, whichever is smaller
            main_splitter.setSizes([left_panel_size, total_width - left_panel_size])
            # Make splitter handle resizable
            main_splitter.setChildrenCollapsible(False)
            # Connect splitter resize to update preview image if needed
            main_splitter.splitterMoved.connect(self._on_splitter_moved)
        else:
            # New UI uses dock widgets - connect to dock widget signals for preview updates
            left_dock = getattr(self.ui, "leftDockWidget", None)
            if left_dock is not None:
                # Update preview when dock widget is resized or visibility changes
                left_dock.visibilityChanged.connect(self._on_dock_visibility_changed)
                # Use event filter to update preview after geometry changes
                left_dock.installEventFilter(self)
            right_dock = getattr(self.ui, "rightDockWidget", None)
            if right_dock is not None:
                right_dock.visibilityChanged.connect(self._on_dock_visibility_changed)

        self._setup_status_bar()
        # Walkmesh painter state
        self._painting_walkmesh: bool = False
        self._colorize_materials: bool = True
        self._material_colors: dict[SurfaceMaterial, QColor] = {}
        self._paint_stroke_active: bool = False
        self._paint_stroke_originals: dict[tuple[IndoorMapRoom, int], SurfaceMaterial] = {}
        self._paint_stroke_new: dict[tuple[IndoorMapRoom, int], SurfaceMaterial] = {}

        self._setup_signals()
        self._setup_walkmesh_painter()
        self._setup_undo_redo()
        self._setup_kits()
        self._setup_modules()
        self._refresh_window_title()

        self.ui.mapRenderer.set_map(self._map)
        self.ui.mapRenderer.set_undo_stack(self._undo_stack)
        self.ui.mapRenderer.set_status_callback(self._refresh_status_bar)

        # Initialize Options UI to match renderer state
        self._initialize_options_ui()

        # Setup Blender integration UI (deferred to avoid layout issues)
        QTimer.singleShot(0, self._install_view_stack)

        # Check for Blender on first map load
        if not self._blender_choice_made and self._installation:
            QTimer.singleShot(100, self._check_blender_on_load)

        # Setup NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

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
        self.ui.actionZoomIn.triggered.connect(lambda: self.ui.mapRenderer.zoom_in_camera(ZOOM_STEP_FACTOR))
        self.ui.actionZoomOut.triggered.connect(lambda: self.ui.mapRenderer.zoom_in_camera(1.0 / ZOOM_STEP_FACTOR))
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
        self.ui.mapRenderer.sig_rooms_rotated.connect(self.on_rooms_rotated)
        self.ui.mapRenderer.sig_warp_moved.connect(self.on_warp_moved)
        self.ui.mapRenderer.sig_marquee_select.connect(self.on_marquee_select)

        # Ensure renderer can receive keyboard focus for accessibility
        self.ui.mapRenderer.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Options checkboxes - use proper setters that trigger mark_dirty
        self.ui.snapToGridCheck.toggled.connect(self.ui.mapRenderer.set_snap_to_grid)
        self.ui.snapToHooksCheck.toggled.connect(self.ui.mapRenderer.set_snap_to_hooks)
        self.ui.showGridCheck.toggled.connect(self.ui.mapRenderer.set_show_grid)
        self.ui.showHooksCheck.toggled.connect(lambda v: self.ui.mapRenderer.set_hide_magnets(not v))
        self.ui.gridSizeSpin.valueChanged.connect(self.ui.mapRenderer.set_grid_size)
        self.ui.rotSnapSpin.valueChanged.connect(self.ui.mapRenderer.set_rotation_snap)

    def _setup_walkmesh_painter(self):
        """Initialize walkmesh painting UI and palette."""
        settings = ModuleDesignerSettings()

        def int_to_qcolor(intvalue: int) -> QColor:
            color = Color.from_rgba_integer(intvalue)
            return QColor(int(color.r * 255), int(color.g * 255), int(color.b * 255), int(color.a * 255))

        self._material_colors = {
            SurfaceMaterial.UNDEFINED: int_to_qcolor(settings.undefinedMaterialColour),
            SurfaceMaterial.OBSCURING: int_to_qcolor(settings.obscuringMaterialColour),
            SurfaceMaterial.DIRT: int_to_qcolor(settings.dirtMaterialColour),
            SurfaceMaterial.GRASS: int_to_qcolor(settings.grassMaterialColour),
            SurfaceMaterial.STONE: int_to_qcolor(settings.stoneMaterialColour),
            SurfaceMaterial.WOOD: int_to_qcolor(settings.woodMaterialColour),
            SurfaceMaterial.WATER: int_to_qcolor(settings.waterMaterialColour),
            SurfaceMaterial.NON_WALK: int_to_qcolor(settings.nonWalkMaterialColour),
            SurfaceMaterial.TRANSPARENT: int_to_qcolor(settings.transparentMaterialColour),
            SurfaceMaterial.CARPET: int_to_qcolor(settings.carpetMaterialColour),
            SurfaceMaterial.METAL: int_to_qcolor(settings.metalMaterialColour),
            SurfaceMaterial.PUDDLES: int_to_qcolor(settings.puddlesMaterialColour),
            SurfaceMaterial.SWAMP: int_to_qcolor(settings.swampMaterialColour),
            SurfaceMaterial.MUD: int_to_qcolor(settings.mudMaterialColour),
            SurfaceMaterial.LEAVES: int_to_qcolor(settings.leavesMaterialColour),
            SurfaceMaterial.LAVA: int_to_qcolor(settings.lavaMaterialColour),
            SurfaceMaterial.BOTTOMLESS_PIT: int_to_qcolor(settings.bottomlessPitMaterialColour),
            SurfaceMaterial.DEEP_WATER: int_to_qcolor(settings.deepWaterMaterialColour),
            SurfaceMaterial.DOOR: int_to_qcolor(settings.doorMaterialColour),
            SurfaceMaterial.NON_WALK_GRASS: int_to_qcolor(settings.nonWalkGrassMaterialColour),
            SurfaceMaterial.TRIGGER: int_to_qcolor(settings.nonWalkGrassMaterialColour),
        }

        self._populate_material_list()
        self._colorize_materials = True
        self.ui.colorizeMaterialsCheck.setChecked(True)
        self.ui.enablePaintCheck.setChecked(False)

        self.ui.mapRenderer.set_material_colors(self._material_colors)
        self.ui.mapRenderer.set_colorize_materials(self._colorize_materials)

        self.ui.materialList.currentItemChanged.connect(lambda _old, _new=None: self._refresh_status_bar())
        self.ui.enablePaintCheck.toggled.connect(self._toggle_paint_mode)
        self.ui.colorizeMaterialsCheck.toggled.connect(self._toggle_colorize_materials)
        self.ui.resetPaintButton.clicked.connect(self._reset_selected_walkmesh)

        # Shortcut to quickly toggle paint mode
        QShortcut(Qt.Key.Key_P, self).activated.connect(lambda: self.ui.enablePaintCheck.toggle())

    def _setup_undo_redo(self):
        """Setup undo/redo actions."""
        self.ui.actionUndo.triggered.connect(self._undo_stack.undo)
        self.ui.actionRedo.triggered.connect(self._undo_stack.redo)

        # Update action enabled states
        self._undo_stack.canUndoChanged.connect(self.ui.actionUndo.setEnabled)
        self._undo_stack.canRedoChanged.connect(self.ui.actionRedo.setEnabled)
        self._undo_stack.cleanChanged.connect(self._refresh_window_title)  # Update title when clean state changes

        # Update action text with command names
        self._undo_stack.undoTextChanged.connect(lambda text: self.ui.actionUndo.setText(f"Undo {text}" if text else "Undo"))
        self._undo_stack.redoTextChanged.connect(lambda text: self.ui.actionRedo.setText(f"Redo {text}" if text else "Redo"))

        # Initial state
        self.ui.actionUndo.setEnabled(False)
        self.ui.actionRedo.setEnabled(False)

    def _populate_material_list(self):
        """Populate the material list with colored swatches."""
        self.ui.materialList.clear()
        for material, color in self._material_colors.items():
            pix = QPixmap(16, 16)
            pix.fill(color)
            item = QListWidgetItem(QIcon(pix), material.name.replace("_", " ").title())
            item.setData(Qt.ItemDataRole.UserRole, material)
            self.ui.materialList.addItem(item)  # pyright: ignore[reportArgumentType, reportCallIssue]
        if self.ui.materialList.count() > 0:
            self.ui.materialList.setCurrentRow(0)

    def _current_material(self) -> SurfaceMaterial | None:
        if self.ui.materialList.currentItem():
            material = self.ui.materialList.currentItem().data(Qt.ItemDataRole.UserRole)  # type: ignore[union-attr]  # pyright: ignore[reportOptionalMemberAccess]
            if isinstance(material, SurfaceMaterial):
                return material
        return next(iter(self._material_colors.keys()), None)

    def _toggle_paint_mode(self, enabled: bool):
        self._painting_walkmesh = enabled
        self._paint_stroke_active = False
        self._paint_stroke_originals.clear()
        self._paint_stroke_new.clear()
        self._refresh_status_bar()

    def _toggle_colorize_materials(self, enabled: bool):
        self._colorize_materials = enabled
        self.ui.mapRenderer.set_colorize_materials(enabled)
        self.ui.mapRenderer.mark_dirty()
        self._refresh_status_bar()

    def _reset_selected_walkmesh(self):
        rooms = [room for room in self.ui.mapRenderer.selected_rooms() if room.walkmesh_override is not None]
        if not rooms:
            return
        cmd = ResetWalkmeshCommand(rooms, self._invalidate_rooms)
        self._undo_stack.push(cmd)
        self._refresh_window_title()

    def _invalidate_rooms(self, rooms: list[IndoorMapRoom]):
        self.ui.mapRenderer.invalidate_rooms(rooms)
        self._refresh_status_bar()

    def _setup_kits(self):
        self.ui.kitSelect.clear()
        self._kits, missing_files = load_kits("./kits")

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
            self.ui.modulesGroupBox.setEnabled(False)
            return

        # Get module roots from the kit manager
        module_roots: list[str] = self._module_kit_manager.get_module_roots()

        # Populate the combobox with module names
        for module_root in module_roots:
            assert isinstance(module_root, str)
            display_name = self._module_kit_manager.get_module_display_name(module_root)
            self.ui.moduleSelect.addItem(display_name, module_root)

    def _set_preview_image(self, image: QImage | None):
        """Render a component preview into the unified preview pane."""
        if image is None:
            self.ui.previewImage.clear()
            self._preview_source_image = None
            return

        # Store the original image for resizing
        self._preview_source_image = image
        # Scale to fit the label's current size
        self._update_preview_image_size()

    def _update_preview_image_size(self):
        """Update preview image to match current label size."""
        if self._preview_source_image is None:
            return

        # Get the label's available size
        label_size = self.ui.previewImage.size()
        if label_size.width() <= 0 or label_size.height() <= 0:
            # Label not yet sized, use a default
            label_size = self.ui.previewImage.sizeHint()
            if label_size.width() <= 0 or label_size.height() <= 0:
                label_size = QSize(128, 128)  # Fallback default

        # Scale the image to fit while maintaining aspect ratio
        pixmap = QPixmap.fromImage(self._preview_source_image)
        scaled = pixmap.scaled(
            label_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.ui.previewImage.setPixmap(scaled)

    def _on_splitter_moved(self, pos: int, index: int):
        """Handle splitter movement - update preview image if it exists."""
        # Refresh preview image to match new size if one is set
        if self._preview_source_image is not None:
            # Use QTimer to update after layout has adjusted
            QTimer.singleShot(10, self._update_preview_image_size)

    def _on_dock_visibility_changed(self, visible: bool):
        """Handle dock widget visibility changes - update preview image if it exists."""
        if visible and self._preview_source_image is not None:
            # Use QTimer to update after layout has adjusted
            QTimer.singleShot(10, self._update_preview_image_size)

    def eventFilter(self, obj, event):
        """Event filter for dock widgets to detect resize events."""
        if event.type() == QEvent.Type.Resize:
            if self._preview_source_image is not None:
                # Use QTimer to update after layout has adjusted
                QTimer.singleShot(10, self._update_preview_image_size)
        return super().eventFilter(obj, event)

    def _update_preview_from_selection(self):
        """Update preview image based on selected rooms.

        Shows the most recently selected room's component image.
        Only updates if no component is being dragged (cursor_component is None).
        """
        renderer = self.ui.mapRenderer
        # Don't update preview if we're dragging a component (placement mode)
        if renderer.cursor_component is not None:
            return

        # Get selected rooms - most recent is last in the list
        sel_rooms = renderer.selected_rooms()
        if sel_rooms:
            # Show the most recently selected room (last in list)
            most_recent_room = sel_rooms[-1]
            if hasattr(most_recent_room, "component") and hasattr(most_recent_room.component, "image"):
                self._set_preview_image(most_recent_room.component.image)
        else:
            # No rooms selected, clear preview (unless dragging)
            self._set_preview_image(None)

    # ------------------------------------------------------------------
    # Status bar
    # ------------------------------------------------------------------
    def _setup_status_bar(self):
        """Create a richer status bar mirroring the module designer style."""
        self._emoji_style = (
            "font-size:12pt; font-family:'Segoe UI Emoji','Apple Color Emoji','Noto Color Emoji',"
            "'EmojiOne','Twemoji Mozilla','Segoe UI Symbol',sans-serif; vertical-align:middle;"
        )

        bar = QStatusBar(self)
        bar.setContentsMargins(4, 0, 4, 0)
        self.setStatusBar(bar)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        first_row = QHBoxLayout()
        first_row.setContentsMargins(0, 0, 0, 0)
        first_row.setSpacing(8)

        self._mouse_label = QLabel("Coords:")
        self._hover_label = QLabel("Hover:")
        self._selection_label = QLabel("Selection:")
        self._keys_label = QLabel("Keys/Buttons:")
        for lbl in (self._mouse_label, self._hover_label, self._selection_label, self._keys_label):
            lbl.setTextFormat(Qt.TextFormat.RichText)
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        first_row.addWidget(self._mouse_label, 1)
        first_row.addWidget(self._hover_label, 1)
        first_row.addWidget(self._selection_label, 1)
        first_row.addWidget(self._keys_label, 1)

        self._mode_label = QLabel()
        self._mode_label.setTextFormat(Qt.TextFormat.RichText)
        self._mode_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        layout.addLayout(first_row)
        layout.addWidget(self._mode_label)

        bar.addWidget(container, 1)

    def on_module_selected(self, index: int = -1):
        """Handle module selection from the combobox.

        Loads module components lazily when a module is selected in the combobox.
        Uses ModuleKitManager to convert module resources into kit components.
        """
        self.ui.moduleComponentList.clear()
        self._set_preview_image(None)

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
                self.ui.moduleComponentList.addItem(item)  # pyright: ignore[reportArgumentType, reportCallIssue]

        except Exception:  # noqa: BLE001
            from loggerplus import RobustLogger  # type: ignore[import-untyped, note]  # pyright: ignore[reportMissingTypeStubs]

            RobustLogger().exception(f"Failed to load module '{module_root}'")

    def on_module_component_selected(self, item: QListWidgetItem | None = None):
        """Handle module component selection from the list."""
        if item is None:
            self._set_preview_image(None)
            self.ui.mapRenderer.set_cursor_component(None)
            return

        component: KitComponent | None = item.data(Qt.ItemDataRole.UserRole)
        if component is None:
            return

        # Toggle: if same component is already selected, deselect it
        if self.ui.mapRenderer.cursor_component is component:
            # Clicking the same component again = "pick it up" (deselect)
            self.ui.moduleComponentList.clearSelection()
            self.ui.moduleComponentList.setCurrentItem(None)
            self._set_preview_image(None)
            self.ui.mapRenderer.set_cursor_component(None)
            return

        # Display component image in the preview
        self._set_preview_image(component.image)

        # Set as current cursor component for placement
        self.ui.mapRenderer.set_cursor_component(component)

    def _refresh_window_title(self):
        from toolset.gui.common.localization import translate as tr, trf

        if not self._installation:
            title = tr("No installation - Indoor Map Builder")
        elif not self._filepath:
            title = trf("{name} - Indoor Map Builder", name=self._installation.name)
        else:
            title = trf("{path} - {name} - Indoor Map Builder", path=self._filepath, name=self._installation.name)

        # Add asterisk if there are unsaved changes (use isClean() instead of canUndo())
        # isClean() tracks whether the document matches the saved state
        if not self._undo_stack.isClean():
            title = "* " + title
        self.setWindowTitle(title)

    # =============================================================================
    # Blender Integration
    # =============================================================================

    def _install_view_stack(self):
        """Wrap the map renderer with a stacked widget so we can swap in Blender instructions."""
        if self._view_stack is not None:
            return

        # Find the parent layout that contains the map renderer
        # This will depend on the UI structure - adjust as needed
        parent_layout: QVBoxLayout | None = self.ui.mapRenderer.parent().layout() if self.ui.mapRenderer.parent() else None  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
        if not isinstance(parent_layout, QVBoxLayout):
            return  # Can't install view stack without a parent layout

        self._view_stack = QStackedWidget(self)
        parent_layout.removeWidget(self.ui.mapRenderer)
        self._view_stack.addWidget(self.ui.mapRenderer)
        self._blender_placeholder = self._create_blender_placeholder()
        self._view_stack.addWidget(self._blender_placeholder)
        parent_layout.addWidget(self._view_stack)

    def _create_blender_placeholder(self) -> QWidget:
        """Create placeholder pane shown while Blender drives the rendering."""
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        headline = QLabel(
            "<b>Blender mode is active.</b><br>"
            "The Holocron Toolset will defer all 3D rendering and editing to Blender. "
            "Use the Blender window to move rooms, edit textures/models, and "
            "manipulate the indoor map. This panel streams Blender's console output for diagnostics."
        )
        headline.setWordWrap(True)
        layout.addWidget(headline)

        self._blender_log_view = QPlainTextEdit(container)
        self._blender_log_view.setReadOnly(True)
        self._blender_log_view.setPlaceholderText("Blender log output will appear here once the IPC bridge starts…")
        layout.addWidget(self._blender_log_view, 1)

        return container

    def _show_blender_workspace(self):
        """Switch to Blender placeholder view."""
        if self._view_stack is not None and self._blender_placeholder is not None:
            self._view_stack.setCurrentWidget(self._blender_placeholder)

    def _show_internal_workspace(self):
        """Switch to internal renderer view."""
        if self._view_stack is not None:
            self._view_stack.setCurrentWidget(self.ui.mapRenderer)

    def _check_blender_on_load(self):
        """Check for Blender when a map is loaded."""
        if self._blender_choice_made or not self._installation:
            return

        self._blender_choice_made = True
        blender_settings = get_blender_settings()

        if blender_settings.remember_choice:
            self._use_blender_mode = blender_settings.prefer_blender
        else:
            blender_info = blender_settings.get_blender_info()
            if blender_info.is_valid:
                use_blender, _ = check_blender_and_ask(self, "Indoor Map Builder")
                if _ is not None:
                    self._use_blender_mode = use_blender

    def _refresh_room_id_lookup(self):
        """Cache Python object ids for fast lookup when Blender sends events."""
        self._room_id_lookup.clear()
        for room in self._map.rooms:
            self._room_id_lookup[id(room)] = room

    def _on_blender_material_changed(self, payload: dict):
        """Handle material/texture changes from Blender for real-time updates."""

        def _apply():
            object_name = payload.get("object_name", "")
            material_data = payload.get("material", {})
            model_name = payload.get("model_name")

            if not model_name:
                return

            from loggerplus import RobustLogger

            RobustLogger().debug(f"[Blender][Indoor Map Builder] Material changed for {object_name} (model: {model_name})")

            # Find the room that uses this model
            room: IndoorMapRoom | None = None
            for r in self._map.rooms:
                if r.component.mdl == model_name or (hasattr(r.component, "name") and r.component.name == model_name):
                    room = r
                    break

            if room is None:
                return

            # If textures were changed, we need to reload the model
            if "diffuse_texture" in material_data or "lightmap_texture" in material_data:
                # Request MDL export from Blender
                if self.is_blender_mode() and self._blender_controller is not None:
                    import tempfile

                    temp_mdl = tempfile.NamedTemporaryFile(suffix=".mdl", delete=False)
                    temp_mdl.close()

                    from toolset.blender.ipc_client import get_ipc_client

                    client = get_ipc_client()
                    if client and client.is_connected:
                        result = client.send_command(
                            "export_mdl",
                            {
                                "path": temp_mdl.name,
                                "object": object_name,
                            },
                        )
                        if result.success:
                            from loggerplus import RobustLogger

                            RobustLogger().info(f"[Blender][Indoor Map Builder] Exported updated MDL to {temp_mdl.name}")
                            # Reload the model in the renderer
                            self.ui.mapRenderer.invalidate_rooms([room])
                            self.ui.mapRenderer.update()

        QTimer.singleShot(0, _apply)

    def _on_blender_transform_changed(
        self,
        instance_id: int,
        position: dict | None,
        rotation: dict | None,
    ):
        """Handle room transform changes from Blender."""

        def _apply():
            prev = self._transform_sync_in_progress
            self._transform_sync_in_progress = True
            try:
                room = self._room_id_lookup.get(instance_id)
                if room is None:
                    return

                if position:
                    new_position = Vector3(
                        position.get("x", room.position.x),
                        position.get("y", room.position.y),
                        position.get("z", room.position.z),
                    )
                    if room.position != new_position:
                        old_positions = [Vector3(*room.position)]
                        new_positions = [new_position]
                        move_cmd = MoveRoomsCommand(
                            self._map,
                            [room],
                            old_positions,
                            new_positions,
                            self._invalidate_rooms,
                        )
                        self._undo_stack.push(move_cmd)

                if rotation and "euler" in rotation:
                    new_rotation = rotation["euler"].get("z", room.rotation)
                    if not math.isclose(room.rotation, new_rotation, abs_tol=1e-4):
                        old_rotations = [room.rotation]
                        new_rotations = [new_rotation]
                        rotate_cmd = RotateRoomsCommand(  # type: ignore[assignment]
                            self._map,
                            [room],
                            old_rotations,
                            new_rotations,
                            self._invalidate_rooms,
                        )
                        self._undo_stack.push(rotate_cmd)
            finally:
                self._transform_sync_in_progress = prev

        QTimer.singleShot(0, _apply)

    def _on_blender_selection_changed(self, instance_ids: list[int]):
        """Handle selection changes from Blender."""

        def _apply():
            rooms: list[IndoorMapRoom] = [room for room_id in instance_ids if (room := self._room_id_lookup.get(room_id)) is not None]
            if rooms:
                self.ui.mapRenderer.select_rooms(rooms)

        QTimer.singleShot(0, _apply)

    def _on_blender_state_change(self, state: ConnectionState):
        """Handle Blender connection state changes."""
        super()._on_blender_state_change(state)
        QTimer.singleShot(0, lambda: self._handle_blender_state_change(state))

    def _handle_blender_state_change(self, state: ConnectionState):
        """Handle Blender state change on UI thread."""
        if state.value == "connected":  # ConnectionState.CONNECTED
            self._blender_connected_once = True
            if self._blender_progress_dialog:
                self._blender_progress_dialog.hide()
        elif state.value == "error":
            if self._blender_progress_dialog:
                self._blender_progress_dialog.hide()
            QMessageBox.warning(
                self,
                "Blender Connection Error",
                "Failed to connect to Blender. Please check that Blender is running and kotorblender is installed.",
            )

    def _on_blender_module_loaded(self):
        """Called when indoor map is loaded in Blender."""
        super()._on_blender_module_loaded()
        QTimer.singleShot(0, lambda: self._blender_progress_dialog.hide() if self._blender_progress_dialog else None)
        self._refresh_room_id_lookup()

    def _on_blender_mode_stopped(self):
        """Called when Blender mode is stopped."""
        super()._on_blender_mode_stopped()
        QTimer.singleShot(0, self._show_internal_workspace)

    def _on_blender_output(self, line: str):
        """Handle Blender stdout/stderr output."""
        super()._on_blender_output(line)
        if self._blender_log_view:
            self._blender_log_view.appendPlainText(line)

    def sync_room_to_blender(self, room: IndoorMapRoom):
        """Sync a room's position/rotation to Blender."""
        if not self.is_blender_mode() or self._blender_controller is None:
            return

        # For indoor maps, we need to send room data differently
        # Since Blender expects LYT rooms, we'll need to convert
        # This is a simplified version - full implementation would need
        # to handle the conversion properly
        room_id = id(room)
        if self._blender_controller.session:
            # Map room to Blender object name
            object_name = f"Room_{room_id}"
            # Update position
            self._blender_controller.update_room_position(
                object_name,
                room.position.x,
                room.position.y,
                room.position.z,
            )

    def _initialize_options_ui(self):
        """Initialize Options UI to match renderer's initial state."""
        renderer = self.ui.mapRenderer
        # Block signals temporarily to avoid triggering updates during initialization
        self.ui.snapToGridCheck.blockSignals(True)
        self.ui.snapToHooksCheck.blockSignals(True)
        self.ui.showGridCheck.blockSignals(True)
        self.ui.showHooksCheck.blockSignals(True)
        self.ui.gridSizeSpin.blockSignals(True)
        self.ui.rotSnapSpin.blockSignals(True)

        # Set UI to match renderer state
        self.ui.snapToGridCheck.setChecked(renderer.snap_to_grid)
        self.ui.snapToHooksCheck.setChecked(renderer.snap_to_hooks)
        self.ui.showGridCheck.setChecked(renderer.show_grid)
        self.ui.showHooksCheck.setChecked(not renderer.hide_magnets)
        self.ui.gridSizeSpin.setValue(renderer.grid_size)
        self.ui.rotSnapSpin.setValue(int(renderer.rotation_snap))

        # Unblock signals
        self.ui.snapToGridCheck.blockSignals(False)
        self.ui.snapToHooksCheck.blockSignals(False)
        self.ui.showGridCheck.blockSignals(False)
        self.ui.showHooksCheck.blockSignals(False)
        self.ui.gridSizeSpin.blockSignals(False)
        self.ui.rotSnapSpin.blockSignals(False)

    def _refresh_status_bar(
        self,
        screen: QPoint | Vector2 | None = None,
        buttons: set[int | Qt.MouseButton] | None = None,
        keys: set[int | Qt.Key] | None = None,
    ):
        self._update_status_bar(screen, buttons, keys)

    def _update_status_bar(
        self,
        screen: QPoint | Vector2 | None = None,
        buttons: set[int | Qt.MouseButton] | None = None,
        keys: set[int | Qt.Key] | None = None,
    ):
        """Rich status bar mirroring Module Designer style."""
        renderer = self.ui.mapRenderer

        # Resolve screen coords
        if screen is None:
            cursor_pos = self.cursor().pos()
            screen_qp = renderer.mapFromGlobal(cursor_pos)
            screen_vec = Vector2(screen_qp.x(), screen_qp.y())
        elif isinstance(screen, QPoint):
            screen_vec = Vector2(screen.x(), screen.y())
        else:
            screen_vec = screen

        # Resolve buttons/keys - ensure they are sets
        if buttons is None:
            buttons = set(renderer.mouse_down())  # pyright: ignore[reportAttributeAccessIssue]
        elif not isinstance(buttons, set):
            # Convert to set if it's iterable, otherwise create empty set
            try:
                buttons = set(buttons)
            except (TypeError, ValueError):
                buttons = set()
        if keys is None:
            keys = set(renderer.keys_down())
        elif not isinstance(keys, set):
            # Convert to set if it's iterable, otherwise create empty set
            try:
                keys = set(keys)
            except (TypeError, ValueError):
                keys = set()

        world: Vector3 = renderer.to_world_coords(screen_vec.x, screen_vec.y)
        hover_room: IndoorMapRoom | None = renderer.room_under_mouse()
        sel_rooms = renderer.selected_rooms()
        sel_hook = renderer.selected_hook()

        # Mouse/hover
        hover_text = (
            f"<b><span style=\"{self._emoji_style}\">🧩</span>&nbsp;Hover:</b> <span style='color:#0055B0'>{hover_room.component.name}</span>"
            if hover_room
            else f"<b><span style=\"{self._emoji_style}\">🧩</span>&nbsp;Hover:</b> <span style='color:#a6a6a6'><i>None</i></span>"
        )
        self._hover_label.setText(hover_text)

        self._mouse_label.setText(
            f'<b><span style="{self._emoji_style}">🖱</span>&nbsp;Coords:</b> '
            f"<span style='color:#0055B0'>{world.x:.2f}</span>, "
            f"<span style='color:#228800'>{world.y:.2f}</span>"
        )

        # Selection
        if sel_hook is not None:
            hook_room, hook_idx = sel_hook
            sel_text = f"<b><span style=\"{self._emoji_style}\">🎯</span>&nbsp;Selected Hook:</b> <span style='color:#0055B0'>{hook_room.component.name}</span> (#{hook_idx})"
        elif sel_rooms:
            sel_text = f"<b><span style=\"{self._emoji_style}\">🟦</span>&nbsp;Selected Rooms:</b> <span style='color:#0055B0'>{len(sel_rooms)}</span>"
        else:
            sel_text = f"<b><span style=\"{self._emoji_style}\">🟦</span>&nbsp;Selected:</b> <span style='color:#a6a6a6'><i>None</i></span>"
        self._selection_label.setText(sel_text)

        # Update preview based on selection (only if not dragging a component)
        self._update_preview_from_selection()

        # Keys/buttons (sorted with modifiers first)
        def sort_with_modifiers(
            items: set[int | Qt.Key | Qt.MouseButton] | set[int | Qt.Key] | set[int | Qt.MouseButton],
            get_string_func: Callable[[int | Qt.Key | Qt.MouseButton], str],
            qt_enum_type: str,
        ) -> list[int | Qt.Key | Qt.MouseButton]:
            # Ensure items is a set and iterable
            if not isinstance(items, set):
                items = set(items) if hasattr(items, "__iter__") else set()

            # Convert to union type set for processing
            items_union: set[int | Qt.Key | Qt.MouseButton] = set(items)  # type: ignore[assignment]

            modifiers: list[int | Qt.Key | Qt.MouseButton] = []
            normal: list[int | Qt.Key | Qt.MouseButton] = []
            if qt_enum_type == "QtKey":
                modifier_set = {Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta}
                modifiers = [item for item in items_union if item in modifier_set]
                normal = [item for item in items_union if item not in modifier_set]
            else:
                normal = list(items_union)
            return sorted(modifiers, key=get_string_func) + sorted(normal, key=get_string_func)

        def get_qt_key_string_local(key: int | Qt.Key | Qt.MouseButton) -> str:
            """Get key string using utility function, with fallback."""
            # Only process keys, not mouse buttons
            if isinstance(key, Qt.MouseButton):
                return str(key)
            try:
                result = get_qt_key_string(key)  # type: ignore[arg-type]
                # Remove "Key_" prefix if present
                return result.replace("Key_", "").replace("KEY_", "")
            except (AttributeError, TypeError, ValueError):
                # Fallback: try to get name attribute
                try:
                    key_enum = Qt.Key(key) if isinstance(key, int) else key  # type: ignore[arg-type]
                    name = getattr(key_enum, "name", str(key_enum))
                    return name.replace("Key_", "").replace("KEY_", "")
                except (AttributeError, TypeError, ValueError):
                    return str(key)

        def get_qt_button_string_local(btn: int | Qt.MouseButton | Qt.Key) -> str:
            """Get button string using utility function, with fallback."""
            # Only process mouse buttons, not keys
            if isinstance(btn, Qt.Key):
                return str(btn)
            try:
                result = get_qt_button_string(btn)  # type: ignore[arg-type]
                # Remove "Button" suffix if present
                return result.replace("Button", "").replace("BUTTON", "")
            except (AttributeError, TypeError, ValueError):
                # Fallback: try to get name attribute
                try:
                    btn_enum = Qt.MouseButton(btn) if isinstance(btn, int) else btn  # type: ignore[arg-type]
                    name = getattr(btn_enum, "name", str(btn_enum))
                    return name.replace("Button", "").replace("BUTTON", "")
                except (AttributeError, TypeError, ValueError):
                    return str(btn)

        keys_sorted = sort_with_modifiers(keys, get_qt_key_string_local, "QtKey")
        buttons_sorted = sort_with_modifiers(buttons, get_qt_button_string_local, "QtMouse")

        def fmt(
            seq: list[int | Qt.Key | Qt.MouseButton],
            formatter: Callable[[int | Qt.Key | Qt.MouseButton], str],
            color: str,
        ) -> str:
            if not seq:
                return ""
            formatted_items = [formatter(item) for item in seq]
            # Properly escape and wrap each item in a colored span
            colored_items = [f"<span style='color: {color}'>{item}</span>" for item in formatted_items]
            return "&nbsp;+&nbsp;".join(colored_items)

        keys_text = fmt(keys_sorted, get_qt_key_string_local, "#a13ac8")
        buttons_text = fmt(buttons_sorted, get_qt_button_string_local, "#228800")
        sep = " + " if keys_text and buttons_text else ""
        self._keys_label.setText(
            f'<b><span style="{self._emoji_style}">⌨</span>&nbsp;Keys/<span style="{self._emoji_style}">🖱</span>&nbsp;Buttons:</b> {keys_text}{sep}{buttons_text}'
        )

        # Mode/status line
        mode_parts: list[str] = []
        if self._painting_walkmesh:
            material = self._current_material()
            mat_text = material.name.title().replace("_", " ") if material else "Material"
            mode_parts.append(f"<span style='color:#c46811'>Paint: {mat_text}</span>")
        if self._colorize_materials:
            mode_parts.append("Colorized")
        if renderer.snap_to_grid:
            mode_parts.append("Grid Snap")
        if renderer.snap_to_hooks:
            mode_parts.append("Hook Snap")
        self._mode_label.setText(
            '<b><span style="{style}">ℹ</span>&nbsp;Status:</b> {body}'.format(
                style=self._emoji_style,
                body=" | ".join(mode_parts) if mode_parts else "<span style='color:#a6a6a6'><i>Idle</i></span>",
            )
        )

    def show_help_window(self):
        window = HelpWindow(self, "./wiki/Indoor-Map-Builder-User-Guide.md")
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
            Path(self._filepath).name if self._filepath and str(self._filepath).strip() else "test.indoor",
            "Indoor Map File (*.indoor)",
        )
        if not filepath or not str(filepath).strip():
            return
        BinaryWriter.dump(Path(filepath), self._map.write())
        self._filepath = str(Path(filepath))
        self._undo_stack.setClean()
        self._refresh_window_title()

    def new(self):
        if not self._undo_stack.isClean():
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
        self.ui.mapRenderer._cached_walkmeshes.clear()
        self._undo_stack.clear()
        self._undo_stack.setClean()  # Mark as clean for new file
        self._refresh_window_title()

    def open(self):
        if not self._undo_stack.isClean():
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
                missing_rooms = self._map.load(Path(filepath).read_bytes(), self._kits, self._module_kit_manager)
                self._map.rebuild_room_connections()
                self.ui.mapRenderer._cached_walkmeshes.clear()
                self._filepath = filepath
                self._undo_stack.clear()
                self._undo_stack.setClean()  # Mark as clean after loading
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

    def _show_missing_rooms_dialog(
        self,
        missing_rooms: list[MissingRoomInfo],
    ):
        """Show a dialog with information about missing rooms/kits."""
        from toolset.gui.common.localization import translate as tr, trf

        missing_kits = [r for r in missing_rooms if r.reason == "kit_missing"]
        missing_components = [r for r in missing_rooms if r.reason == "component_missing"]

        room_count: int = len(missing_rooms)
        missing_kit_names: set[str] = {r.kit_name for r in missing_rooms if r.reason == "kit_missing"}
        missing_component_pairs: set[tuple[str, str]] = {(r.kit_name, r.component_name) for r in missing_rooms if r.reason == "component_missing" and r.component_name}

        main_parts: list[str] = []
        if missing_kit_names:
            kit_list: str = ", ".join(f"'{name}'" for name in sorted(missing_kit_names))
            main_parts.append(trf("Missing kit{plural}: {kits}", plural="s" if len(missing_kit_names) != 1 else "", kits=kit_list))
        if missing_component_pairs:
            component_list: str = ", ".join(f"'{comp}' ({kit})" for kit, comp in sorted(missing_component_pairs))
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
        old_module_id: str = self._map.module_id
        old_name: str | int | None = self._map.name.stringref if hasattr(self._map.name, "stringref") else None  # type: ignore[assignment, attr-defined]
        old_skybox: str | None = self._map.skybox if hasattr(self._map, "skybox") else None  # type: ignore[assignment, attr-defined]

        dialog = IndoorMapSettings(self, self._installation, self._map, self._kits)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Settings were accepted - check if anything actually changed
            module_id_changed: bool = old_module_id != self._map.module_id
            name_changed: bool = old_name != (self._map.name.stringref if hasattr(self._map.name, "stringref") else None)  # type: ignore[assignment, attr-defined]
            skybox_changed: bool = old_skybox != (self._map.skybox if hasattr(self._map, "skybox") else None)  # type: ignore[assignment, attr-defined]

            if module_id_changed or name_changed or skybox_changed:
                # Mark as having unsaved changes by pushing a no-op command
                # This ensures the asterisk appears in the window title
                from qtpy.QtWidgets import QUndoCommand  # pyright: ignore[reportPrivateImportUsage]

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

    def load_module_from_name(self, module_name: str) -> bool:
        """Load a module by extracting it from the installation.

        Args:
        ----
            module_name: The module name (e.g., "end_m01aa" or "end_m01aa.rim")

        Returns:
        -------
            bool: True if the module was successfully loaded, False otherwise
        """
        if not isinstance(self._installation, HTInstallation):
            from loggerplus import RobustLogger  # type: ignore[import-untyped, note]  # pyright: ignore[reportMissingTypeStubs]

            RobustLogger().error("No installation available to load module from")
            return False

        # Check for unsaved changes
        if not self._undo_stack.isClean():
            from toolset.gui.common.localization import translate as tr

            result = QMessageBox.question(
                self,
                tr("Unsaved Changes"),
                tr("You have unsaved changes. Do you want to save before loading a module?"),
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            )
            if result == QMessageBox.StandardButton.Save:
                self.save()
            elif result == QMessageBox.StandardButton.Cancel:
                return False

        try:
            from loggerplus import RobustLogger  # type: ignore[import-untyped, note]  # pyright: ignore[reportMissingTypeStubs]

            # Remove .rim or .mod extension if present
            module_root = module_name
            if module_root.endswith((".rim", ".mod")):
                module_root = module_root.rsplit(".", 1)[0]

            # Get installation path and kits path
            installation_path = self._installation.path()
            kits_path = Path("./kits").resolve()
            game = self._installation.game()

            # Extract the module
            def extract_task() -> IndoorMap:
                return extract_indoor_from_module_name(
                    module_root,
                    installation_path=installation_path,
                    kits_path=kits_path,
                    game=game,
                    strict=False,  # Don't fail on unmatched rooms
                    max_rms=1e-3,
                    logger=RobustLogger(),
                )

            loader = AsyncLoader(
                self,
                f"Extracting module '{module_root}'...",
                extract_task,
                f"Failed to extract module '{module_root}'",
            )

            if not loader.exec():
                return False

            extracted_map = loader.result()
            if extracted_map is None:
                return False

            # Load the extracted map into the builder
            self._map = extracted_map
            self._map.rebuild_room_connections()
            self.ui.mapRenderer._cached_walkmeshes.clear()
            self.ui.mapRenderer.set_map(self._map)
            self._undo_stack.clear()
            self._undo_stack.setClean()
            self._filepath = ""  # Clear filepath since this is extracted, not loaded from file
            self._refresh_window_title()

            # Show success message
            room_count = len(self._map.rooms)
            from toolset.gui.common.localization import translate as tr, trf

            QMessageBox(
                QMessageBox.Icon.Information,
                tr("Module Loaded"),
                trf("Successfully loaded module '{module}' with {count} room{plural}.", module=module_root, count=room_count, plural="s" if room_count != 1 else ""),
            ).exec()

            return True

        except Exception as e:  # noqa: BLE001
            from loggerplus import RobustLogger  # type: ignore[import-untyped, note]  # pyright: ignore[reportMissingTypeStubs]
            from toolset.gui.common.localization import translate as tr, trf
            from utility.error_handling import universal_simplify_exception

            RobustLogger().exception(f"Failed to load module '{module_name}'")
            QMessageBox(
                QMessageBox.Icon.Critical,
                tr("Failed to load module"),
                trf("Failed to load module '{module}': {error}", module=module_name, error=str(universal_simplify_exception(e))),
            ).exec()
            return False

    # =========================================================================
    # Edit operations
    # =========================================================================

    def delete_selected(self):
        # If a hook is selected, delete the hook instead of rooms
        hook_sel: tuple[IndoorMapRoom, int] | None = self.ui.mapRenderer.selected_hook()
        if hook_sel is not None:
            room, hook_index = hook_sel
            self.ui.mapRenderer.delete_hook(room, hook_index)
            self._refresh_window_title()
            return

        rooms: list[IndoorMapRoom] = self.ui.mapRenderer.selected_rooms()
        if not rooms:
            return
        delete_cmd = DeleteRoomsCommand(self._map, rooms, self._invalidate_rooms)
        self._undo_stack.push(delete_cmd)
        # Clear selected hook if any of the deleted rooms had the selected hook
        if self.ui.mapRenderer._selected_hook is not None:
            hook_room, _ = self.ui.mapRenderer._selected_hook
            if hook_room in rooms:
                self.ui.mapRenderer.clear_selected_hook()
        self.ui.mapRenderer.clear_selected_rooms()
        self._refresh_window_title()

    def duplicate_selected(self):
        hook_sel = self.ui.mapRenderer.selected_hook()
        if hook_sel is not None:
            room, hook_index = hook_sel
            self.ui.mapRenderer.duplicate_hook(room, hook_index)
            self._refresh_window_title()
            return

        rooms: list[IndoorMapRoom] = self.ui.mapRenderer.selected_rooms()
        if not rooms:
            return
        duplicate_cmd = DuplicateRoomsCommand(
            self._map,
            rooms,
            Vector3(DUPLICATE_OFFSET_X, DUPLICATE_OFFSET_Y, DUPLICATE_OFFSET_Z),
            self._invalidate_rooms,
        )
        self._undo_stack.push(duplicate_cmd)
        # Select the duplicates
        self.ui.mapRenderer.clear_selected_rooms()
        for room in duplicate_cmd.duplicates:
            self.ui.mapRenderer.select_room(room, clear_existing=False)
        # Force immediate update after duplicate
        self.ui.mapRenderer.update()
        self._refresh_window_title()

    def cut_selected(self):
        self.copy_selected()
        self.delete_selected()

    def copy_selected(self):
        rooms: list[IndoorMapRoom] = self.ui.mapRenderer.selected_rooms()
        if not rooms:
            return

        self._clipboard.clear()
        # Calculate centroid for relative positioning
        cx: float = sum(r.position.x for r in rooms) / len(rooms)
        cy: float = sum(r.position.y for r in rooms) / len(rooms)

        for room in rooms:
            clipboard_data: RoomClipboardData = RoomClipboardData(
                component_kit_name=room.component.kit.name,
                component_name=room.component.name,
                position=Vector3(room.position.x - cx, room.position.y - cy, room.position.z),
                rotation=room.rotation,
                flip_x=room.flip_x,
                flip_y=room.flip_y,
                walkmesh_override=bytes_bwm(room.walkmesh_override) if room.walkmesh_override is not None else None,
            )
            self._clipboard.append(clipboard_data)

    def paste(self):
        if not self._clipboard:
            return

        # Get paste position (cursor position or center of view)
        screen_center = QPointF(self.ui.mapRenderer.width() / 2, self.ui.mapRenderer.height() / 2)
        world_center = self.ui.mapRenderer.to_world_coords(screen_center.x(), screen_center.y())

        new_rooms: list[IndoorMapRoom] = []
        for data in self._clipboard:
            # Find the kit and component
            kit: Kit | None = next((k for k in self._kits if k.name == data.component_kit_name), None)
            if not kit:
                continue
            component: KitComponent | None = next((c for c in kit.components if c.name == data.component_name), None)
            if not component:
                continue

            # Deep copy component so hooks can be edited independently
            component_copy = deepcopy(component)
            room = IndoorMapRoom(
                component_copy,
                Vector3(world_center.x + data.position.x, world_center.y + data.position.y, data.position.z),
                data.rotation,
                flip_x=data.flip_x,
                flip_y=data.flip_y,
            )
            if data.walkmesh_override is not None:
                try:
                    room.walkmesh_override = read_bwm(data.walkmesh_override)
                except Exception:
                    pass
            # Initialize hooks connections list to match hooks length
            room.hooks = [None] * len(component_copy.hooks)
            new_rooms.append(room)

        if new_rooms:
            # Create a compound command for all pasted rooms
            for room in new_rooms:
                cmd = AddRoomCommand(self._map, room, self._invalidate_rooms)
                self._undo_stack.push(cmd)

            self.ui.mapRenderer.clear_selected_rooms()
            for room in new_rooms:
                self.ui.mapRenderer.select_room(room, clear_existing=False)
            # Force immediate update after paste
            self.ui.mapRenderer.update()
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
        self.ui.moduleComponentList.clearSelection()
        self.ui.moduleComponentList.setCurrentItem(None)
        self._set_preview_image(None)
        self._refresh_status_bar()

    # =========================================================================
    # View operations
    # =========================================================================

    def reset_view(self):
        self.ui.mapRenderer.set_camera_position(DEFAULT_CAMERA_POSITION_X, DEFAULT_CAMERA_POSITION_Y)
        self.ui.mapRenderer.set_camera_rotation(DEFAULT_CAMERA_ROTATION)
        self.ui.mapRenderer.set_camera_zoom(DEFAULT_CAMERA_ZOOM)

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
        """Return the currently selected component for placement.

        ONLY returns cursor_component to prevent state desync between
        the renderer and UI lists. The cursor_component is the single
        source of truth for what component will be placed on click.
        """
        return self.ui.mapRenderer.cursor_component

    def set_warp_point(self, x: float, y: float, z: float):
        self._map.warp_point = Vector3(x, y, z)

    def on_kit_selected(self):
        kit: Kit = self.ui.kitSelect.currentData()
        if not isinstance(kit, Kit):
            return
        self.ui.componentList.clear()
        self._set_preview_image(None)
        for component in kit.components:
            item = QListWidgetItem(component.name)
            item.setData(Qt.ItemDataRole.UserRole, component)
            self.ui.componentList.addItem(item)  # pyright: ignore[reportCallIssue, reportArgumentType]

    def onComponentSelected(self, item: QListWidgetItem):
        if item is None:
            self._set_preview_image(None)
            self.ui.mapRenderer.set_cursor_component(None)
            return

        component: KitComponent = item.data(Qt.ItemDataRole.UserRole)

        # Toggle: if same component is already selected, deselect it
        if self.ui.mapRenderer.cursor_component is component:
            # Clicking the same component again = "pick it up" (deselect)
            self.ui.componentList.clearSelection()
            self.ui.componentList.setCurrentItem(None)
            self._set_preview_image(None)
            self.ui.mapRenderer.set_cursor_component(None)
            return

        self._set_preview_image(component.image)
        self.ui.mapRenderer.set_cursor_component(component)

    # =========================================================================
    # Mouse event handlers
    # =========================================================================

    def on_mouse_moved(
        self,
        screen: Vector2,
        delta: Vector2,
        buttons: set[int | Qt.MouseButton],
        keys: set[int | Qt.Key],
    ):
        self._refresh_status_bar(screen=screen, buttons=buttons, keys=keys)
        world_delta: Vector2 = self.ui.mapRenderer.to_world_delta(delta.x, delta.y)

        # Walkmesh painting drag - Shift+Left drag should paint
        if (self._painting_walkmesh or Qt.Key.Key_Shift in keys) and Qt.MouseButton.LeftButton in buttons and Qt.Key.Key_Control not in keys:
            self._apply_paint_at_screen(screen)
            return

        # Pan camera with middle mouse or LMB + Ctrl
        if Qt.MouseButton.MiddleButton in buttons or (Qt.MouseButton.LeftButton in buttons and Qt.Key.Key_Control in keys):
            self.ui.mapRenderer.pan_camera(-world_delta.x, -world_delta.y)
        # Rotate camera with RMB + Ctrl
        elif Qt.MouseButton.RightButton in buttons and Qt.Key.Key_Control in keys:
            self.ui.mapRenderer.rotate_camera(delta.x / 50)

    def on_mouse_pressed(
        self,
        screen: Vector2,
        buttons: set[int | Qt.MouseButton],
        keys: set[int | Qt.Key],
    ):
        if Qt.MouseButton.LeftButton not in buttons:
            return
        if Qt.Key.Key_Control in keys:
            return  # Control is for camera pan

        # Check for walkmesh painting mode - Shift+Left click should paint
        if self._painting_walkmesh or Qt.Key.Key_Shift in keys:
            self._begin_paint_stroke(screen)
            return

        renderer = self.ui.mapRenderer
        world = renderer.to_world_coords(screen.x, screen.y)

        # Check if clicking on warp point first
        if renderer.is_over_warp_point(world):
            renderer.start_warp_drag()
            return

        # STEP 1: Check for existing room/hook at click position
        # Use pick_face which checks the actual walkmesh geometry
        clicked_room: IndoorMapRoom | None = None
        face_room, _ = renderer.pick_face(world)
        if face_room is not None:
            clicked_room = face_room
        hook_hit = renderer.hook_under_mouse(world)

        # STEP 2: If clicking on an existing room or hook, ALWAYS select/drag
        # This takes ABSOLUTE priority over placement mode
        if clicked_room is not None or hook_hit is not None:
            # Force clear placement mode when interacting with existing objects
            self._clear_placement_mode()

            # Handle hook selection/dragging first (hooks have priority over room body)
            if hook_hit is not None and Qt.Key.Key_Shift not in keys:
                hook_room, hook_index = hook_hit
                renderer.select_hook(hook_room, hook_index, clear_existing=True)
                renderer._dragging_hook = True
                renderer._drag_hook_start = Vector3(*renderer.cursor_point)
                return

            # Handle room selection and dragging
            if clicked_room is not None:
                if clicked_room in renderer.selected_rooms():
                    # Room already selected - just start drag
                    renderer.start_drag(clicked_room)
                else:
                    # Select the room first, then start drag
                    clear_existing = Qt.Key.Key_Shift not in keys
                    renderer.select_room(clicked_room, clear_existing=clear_existing)
                    renderer.start_drag(clicked_room)
                return

        # STEP 3: Clicked on empty space - check placement mode
        # ONLY use cursor_component, ignore UI list fallback to prevent desync
        if renderer.cursor_component is not None:
            self._place_new_room(renderer.cursor_component)
            if Qt.Key.Key_Shift not in keys:
                # Clear placement mode after placing
                self._clear_placement_mode()
            return

        # STEP 4: Empty space, no placement mode - start marquee or clear selection
        if Qt.Key.Key_Shift not in keys:
            renderer.clear_selected_rooms()
        renderer.start_marquee(screen)

    def _clear_placement_mode(self):
        """Clear all placement mode state - cursor component and UI selections."""
        renderer = self.ui.mapRenderer
        renderer.set_cursor_component(None)
        renderer.clear_selected_hook()
        # Block signals to prevent recursive calls during clear
        self.ui.componentList.blockSignals(True)
        self.ui.moduleComponentList.blockSignals(True)
        try:
            self.ui.componentList.clearSelection()
            self.ui.componentList.setCurrentItem(None)
            self.ui.moduleComponentList.clearSelection()
            self.ui.moduleComponentList.setCurrentItem(None)
        finally:
            self.ui.componentList.blockSignals(False)
            self.ui.moduleComponentList.blockSignals(False)
        # Update preview to show selected rooms (if any) now that placement mode is cleared
        self._update_preview_from_selection()

    def on_mouse_released(
        self,
        screen: Vector2,
        buttons: set[int | Qt.MouseButton],
        keys: set[int | Qt.Key],
    ):
        # NOTE: 'buttons' contains buttons STILL held after release (left button was just removed)
        # So if left button was just released, it will NOT be in buttons

        # ALWAYS end drag operations when ANY button is released
        # This is critical - marquee, room drag, hook drag, warp drag must all stop
        renderer = self.ui.mapRenderer

        # Finish paint stroke if active (including Shift+Left paint mode)
        if self._paint_stroke_active:
            self._finish_paint_stroke()

        # Stop hook drag if active - rebuild connections after hook position changes
        if renderer._dragging_hook:
            renderer._dragging_hook = False
            self._map.rebuild_room_connections()

        # CRITICAL: Always end any active drag operations on mouse release
        # This includes marquee selection, room dragging, warp dragging
        renderer.end_drag()

        self._refresh_status_bar(screen=screen, buttons=buttons, keys=keys)

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
        if any(old.distance(new) > POSITION_CHANGE_EPSILON for old, new in zip(old_positions, new_positions)):
            cmd = MoveRoomsCommand(self._map, rooms, old_positions, new_positions, self._invalidate_rooms)
            self._undo_stack.push(cmd)
            self._refresh_window_title()

            # Sync to Blender if not already syncing from Blender
            if self.is_blender_mode() and self._blender_controller is not None and not self._transform_sync_in_progress:
                for room in rooms:
                    self.sync_room_to_blender(room)

    def on_rooms_rotated(
        self,
        rooms: list[IndoorMapRoom],
        old_rotations: list[float],
        new_rotations: list[float],
    ):
        """Called when rooms have been rotated during drag."""
        if not rooms:
            return
        if any(abs(o - n) > ROTATION_CHANGE_EPSILON for o, n in zip(old_rotations, new_rotations)):
            cmd = RotateRoomsCommand(self._map, rooms, old_rotations, new_rotations, self._invalidate_rooms)
            self._undo_stack.push(cmd)
            self._refresh_window_title()

            # Sync to Blender if not already syncing from Blender
            if self.is_blender_mode() and self._blender_controller is not None and not self._transform_sync_in_progress:
                for room in rooms:
                    self.sync_room_to_blender(room)

    def on_warp_moved(
        self,
        old_position: Vector3,
        new_position: Vector3,
    ):
        """Called when warp point has been moved via drag."""
        if old_position.distance(new_position) > POSITION_CHANGE_EPSILON:
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
            Vector3(*self.ui.mapRenderer.cursor_point),
            self.ui.mapRenderer.cursor_rotation,
            flip_x=self.ui.mapRenderer.cursor_flip_x,
            flip_y=self.ui.mapRenderer.cursor_flip_y,
        )
        cmd = AddRoomCommand(self._map, room, self._invalidate_rooms)
        self._undo_stack.push(cmd)
        self.ui.mapRenderer.cursor_rotation = 0.0
        self.ui.mapRenderer.cursor_flip_x = False
        self.ui.mapRenderer.cursor_flip_y = False
        self._refresh_window_title()

    # =========================================================================
    # Walkmesh painting helpers
    # =========================================================================

    def _begin_paint_stroke(self, screen: Vector2):
        self._paint_stroke_active = True
        self._paint_stroke_originals.clear()
        self._paint_stroke_new.clear()
        self._apply_paint_at_screen(screen)

    def _apply_paint_at_screen(self, screen: Vector2):
        world = self.ui.mapRenderer.to_world_coords(screen.x, screen.y)
        self._apply_paint_at_world(world)

    def _apply_paint_at_world(self, world: Vector3):
        material = self._current_material()
        if material is None:
            return
        room, face_index = self.ui.mapRenderer.pick_face(world)
        if room is None or face_index is None:
            return
        # Ensure we have a writable walkmesh override
        if room.walkmesh_override is None:
            room.walkmesh_override = deepcopy(room.component.bwm)
        base_bwm = room.walkmesh_override
        if not (0 <= face_index < len(base_bwm.faces)):
            return

        key = (room, face_index)
        if key not in self._paint_stroke_originals:
            self._paint_stroke_originals[key] = base_bwm.faces[face_index].material

        if base_bwm.faces[face_index].material == material:
            return

        base_bwm.faces[face_index].material = material
        self._paint_stroke_new[key] = material
        self._invalidate_rooms([room])

    def _finish_paint_stroke(self):
        if not self._paint_stroke_active:
            return
        self._paint_stroke_active = False
        if not self._paint_stroke_new:
            return

        rooms: list[IndoorMapRoom] = []
        face_indices: list[int] = []
        old_materials: list[SurfaceMaterial] = []
        new_materials: list[SurfaceMaterial] = []

        for (room, face_index), new_material in self._paint_stroke_new.items():
            rooms.append(room)
            face_indices.append(face_index)
            old_materials.append(self._paint_stroke_originals.get((room, face_index), new_material))
            new_materials.append(new_material)

        cmd = PaintWalkmeshCommand(rooms, face_indices, old_materials, new_materials, self._invalidate_rooms)
        self._undo_stack.push(cmd)
        self._refresh_window_title()

    def on_mouse_scrolled(
        self,
        delta: Vector2,
        buttons: set[int | Qt.MouseButton],
        keys: set[int | Qt.Key],
    ):
        if Qt.Key.Key_Control in keys:
            # Use multiplicative zoom for linear visual zoom
            # Normalize delta.y by typical wheel click (120) to get number of clicks
            # Apply consistent percentage change per click
            # Positive delta.y means scrolling up (zoom in), negative means scrolling down (zoom out)
            clicks = delta.y / 120.0  # Normalize to number of wheel clicks
            # Calculate zoom factor: 1.0 + sensitivity for zoom in, 1.0 - sensitivity for zoom out
            zoom_factor = (1.0 + ZOOM_WHEEL_SENSITIVITY) ** clicks
            self.ui.mapRenderer.zoom_in_camera(zoom_factor)
            return

        # When dragging existing rooms, allow scroll-wheel rotation just like placement mode.
        if self.ui.mapRenderer.is_dragging_rooms():
            self.ui.mapRenderer.rotate_drag_selection(delta.y)
            return

        # Placement preview rotation
        if self.ui.mapRenderer.cursor_component is not None:
            snap = self.ui.mapRenderer.rotation_snap
            self.ui.mapRenderer.cursor_rotation += math.copysign(snap, delta.y)
        self._refresh_status_bar(screen=None, buttons=buttons, keys=keys)  # type: ignore[reportArgumentType]

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
        hook_hit = self.ui.mapRenderer.hook_under_mouse(world)
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

        # Hook actions (context under hook or room)
        if hook_hit is not None:
            hook_room, hook_index = hook_hit
            hook_select_action = menu.addAction("Select Hook")
            assert hook_select_action is not None
            hook_select_action.triggered.connect(lambda: self.ui.mapRenderer.select_hook(hook_room, hook_index, clear_existing=True))

            hook_delete_action = menu.addAction("Delete Hook")
            assert hook_delete_action is not None
            hook_delete_action.triggered.connect(lambda: self.ui.mapRenderer.delete_hook(hook_room, hook_index))

            hook_duplicate_action = menu.addAction("Duplicate Hook")
            assert hook_duplicate_action is not None
            hook_duplicate_action.triggered.connect(lambda: self.ui.mapRenderer.duplicate_hook(hook_room, hook_index))

            menu.addSeparator()

        add_hook_action = menu.addAction("Add Hook Here")
        assert add_hook_action is not None
        add_hook_action.triggered.connect(lambda: self.ui.mapRenderer.add_hook_at(world))

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
        cmd = RotateRoomsCommand(self._map, rooms, old_rotations, new_rotations, self._invalidate_rooms)
        self._undo_stack.push(cmd)
        # Force immediate update to prevent desync
        self.ui.mapRenderer.update()
        self._refresh_window_title()

    def _flip_selected(self, flip_x: bool, flip_y: bool):
        rooms = self.ui.mapRenderer.selected_rooms()
        if not rooms:
            return
        cmd = FlipRoomsCommand(self._map, rooms, flip_x, flip_y, self._invalidate_rooms)
        self._undo_stack.push(cmd)
        # Force immediate update to prevent desync
        self.ui.mapRenderer.update()
        self._refresh_window_title()

    def _cancel_all_operations(self):
        """Cancel all active operations and reset to safe state.

        This is the "panic button" - cancels everything to get out of stuck states:
        - Cancels marquee selection
        - Cancels room/hook/warp dragging
        - Cancels placement mode
        - Cancels walkmesh painting
        - Clears selections (optional, can be toggled)
        """
        renderer = self.ui.mapRenderer

        # Cancel marquee selection
        if renderer._marquee_active:
            renderer._marquee_active = False
            renderer._drag_mode = DragMode.NONE
            renderer.mark_dirty()

        # Cancel all drag operations
        if renderer._dragging or renderer._dragging_hook or renderer._dragging_warp:
            renderer.end_drag()
            renderer._dragging_hook = False
            renderer._dragging_warp = False

        # Cancel walkmesh painting
        if self._paint_stroke_active:
            self._paint_stroke_active = False
            self._paint_stroke_originals.clear()
            self._paint_stroke_new.clear()

        # Cancel placement mode (clear cursor component)
        if renderer.cursor_component is not None:
            renderer.set_cursor_component(None)
            renderer.clear_selected_hook()

        # Force repaint to clear any stuck visuals
        renderer.update()
        self._refresh_status_bar()

    def keyPressEvent(self, e: QKeyEvent):  # type: ignore[reportIncompatibleMethodOverride]
        # ESC key - Universal cancel/escape (standard Windows behavior)
        if e.key() == Qt.Key.Key_Escape:
            self._cancel_all_operations()
            # Also clear selection on ESC (standard behavior)
            self.ui.mapRenderer.clear_selected_rooms()
            self.ui.mapRenderer.clear_selected_hook()
            return

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
        # Ctrl+A - Select all (standard Windows behavior)
        elif e.key() == Qt.Key.Key_A and (e.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self.select_all()
        # Delete/Backspace - Delete selected (standard Windows behavior)
        elif e.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace) and not bool(e.modifiers()):
            self.delete_selected()
        # Space - Cancel placement mode (intuitive)
        elif e.key() == Qt.Key.Key_Space and not bool(e.modifiers()):
            if self.ui.mapRenderer.cursor_component is not None:
                self.ui.mapRenderer.set_cursor_component(None)
                self.ui.componentList.clearSelection()
                self.ui.componentList.setCurrentItem(None)
                self.ui.moduleComponentList.clearSelection()
                self.ui.moduleComponentList.setCurrentItem(None)
                self.ui.mapRenderer.clear_selected_hook()
        # Ctrl+0 or Home - Reset camera view (standard behavior)
        elif (e.key() == Qt.Key.Key_0 and (e.modifiers() & Qt.KeyboardModifier.ControlModifier)) or (e.key() == Qt.Key.Key_Home and not bool(e.modifiers())):
            self.ui.mapRenderer.set_camera_position(DEFAULT_CAMERA_POSITION_X, DEFAULT_CAMERA_POSITION_Y)
            self.ui.mapRenderer.set_camera_rotation(DEFAULT_CAMERA_ROTATION)
            self.ui.mapRenderer.set_camera_zoom(DEFAULT_CAMERA_ZOOM)
        # F5 - Refresh/Reset view (standard Windows behavior)
        elif e.key() == Qt.Key.Key_F5 and not bool(e.modifiers()):
            # Cancel all operations and refresh
            self._cancel_all_operations()
            self.ui.mapRenderer.update()
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
        # Stop renderer timer first
        try:
            if hasattr(self.ui.mapRenderer, "_render_timer"):
                self.ui.mapRenderer._render_timer.stop()
            # Process events to allow renderer to stop gracefully
            QApplication.processEvents()
        except Exception:
            pass

        # Disconnect all signals to prevent callbacks after destruction
        try:
            # Disconnect UI signals
            self.ui.kitSelect.currentIndexChanged.disconnect()
            self.ui.componentList.currentItemChanged.disconnect()
            self.ui.moduleSelect.currentIndexChanged.disconnect()
            self.ui.moduleComponentList.currentItemChanged.disconnect()

            # Disconnect renderer signals
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
            if self._undo_stack is not None:
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
        if self._module_kit_manager is not None:
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
            if hasattr(self, "isVisible"):
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
    sig_rooms_rotated = QtCore.Signal(object, object, object)  # rooms, old_rotations, new_rotations  # pyright: ignore[reportPrivateImportUsage]
    sig_warp_moved = QtCore.Signal(object, object)  # old_position, new_position  # pyright: ignore[reportPrivateImportUsage]
    sig_marquee_select = QtCore.Signal(object, object)  # rooms selected, additive  # pyright: ignore[reportPrivateImportUsage]

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self._map: IndoorMap = IndoorMap()
        self._undo_stack: QUndoStack | None = None
        self._under_mouse_room: IndoorMapRoom | None = None
        self._selected_rooms: list[IndoorMapRoom] = []

        # Camera
        self._cam_position: Vector2 = Vector2(DEFAULT_CAMERA_POSITION_X, DEFAULT_CAMERA_POSITION_Y)
        self._cam_rotation: float = DEFAULT_CAMERA_ROTATION
        self._cam_scale: float = DEFAULT_CAMERA_ZOOM

        # Cursor/placement state
        self.cursor_component: KitComponent | None = None
        self.cursor_point: Vector3 = Vector3.from_null()
        self.cursor_rotation: float = 0.0
        self.cursor_flip_x: bool = False
        self.cursor_flip_y: bool = False

        # Input state
        self._keys_down: set[int | Qt.Key] = set()
        self._mouse_down: set[int | Qt.MouseButton] = set()
        self._mouse_prev: Vector2 = Vector2.from_null()

        # Drag state
        self._dragging: bool = False
        self._drag_start_positions: list[Vector3] = []
        self._drag_start_rotations: list[float] = []
        self._drag_rooms: list[IndoorMapRoom] = []
        self._drag_mode: DragMode = DragMode.NONE

        # Snap state during drag (for soft snapping)
        self._snap_anchor_position: Vector3 | None = None  # Position where snap was first applied
        # Keep snaps easy to separate: small disconnect threshold, scaled later
        self._snap_disconnect_threshold: float = 1.0  # base units before scaling

        # Hook editing state
        self._selected_hook: tuple[IndoorMapRoom, int] | None = None
        self._dragging_hook: bool = False
        self._drag_hook_start: Vector3 = Vector3.from_null()

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
        self.grid_size: float = DEFAULT_GRID_SIZE
        self.rotation_snap: float = float(DEFAULT_ROTATION_SNAP)

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
        self.warp_point_radius: float = WARP_POINT_RADIUS

        # Status callback (set by parent window)
        self._status_callback = None

        # Walkmesh visualization
        self._material_colors: dict[SurfaceMaterial, QColor] = {}
        self._colorize_materials: bool = False
        # Walkable materials:
        #    UNDEFINED (0): walkable=False
        #    DIRT (1): walkable=True
        #    OBSCURING (2): walkable=False
        #    GRASS (3): walkable=True
        #    STONE (4): walkable=True
        #    WOOD (5): walkable=True
        #    WATER (6): walkable=True
        #    NON_WALK (7): walkable=False
        #    TRANSPARENT (8): walkable=False
        #    CARPET (9): walkable=True
        #    METAL (10): walkable=True
        #    PUDDLES (11): walkable=True
        #    SWAMP (12): walkable=True
        #    MUD (13): walkable=True
        #    LEAVES (14): walkable=True
        #    LAVA (15): walkable=False
        #    BOTTOMLESS_PIT (16): walkable=False
        #    DEEP_WATER (17): walkable=False
        #    DOOR (18): walkable=True
        #    NON_WALK_GRASS (19): walkable=False
        #    TRIGGER (30): walkable=True
        # This set must match SurfaceMaterial.walkable() exactly (see geometry.py)
        self._walkable_values: set[int] = {
            1,  # DIRT
            3,  # GRASS
            4,  # STONE
            5,  # WOOD
            6,  # WATER
            9,  # CARPET
            10,  # METAL
            11,  # PUDDLES
            12,  # SWAMP
            13,  # MUD
            14,  # LEAVES
            18,  # DOOR
            30,  # TRIGGER
        }

        # Render loop control - use QTimer instead of recursive singleShot
        self._render_timer = QTimer(self)
        self._render_timer.timeout.connect(self._on_render_timer)
        self._render_timer.setInterval(RENDER_INTERVAL_MS)
        self._render_timer.start()

        # Connect to destroyed signal as safety mechanism
        # This ensures the loop stops immediately when widget is destroyed
        self.destroyed.connect(self._on_destroyed)

    def _on_destroyed(self):
        """Called when widget is destroyed - ensures loop stops."""
        if hasattr(self, "_render_timer"):
            self._render_timer.stop()

    def _on_render_timer(self):
        """Timer callback for render loop - only repaint when dirty.

        Uses QTimer instead of recursive singleShot for better performance
        and proper resource management.
        """
        # Safety check: validate widget is still valid
        try:
            if not self.isVisible() and self.parent() is None:
                self._render_timer.stop()
                return
        except RuntimeError:
            # Widget is in process of destruction
            self._render_timer.stop()
            return

        # Perform repaint only if dirty or actively dragging/placing
        try:
            if self._dirty or self._dragging or self.cursor_component is not None:
                self.repaint()
                self._dirty = False
        except (RuntimeError, AttributeError):
            # Widget may be in process of destruction
            self._render_timer.stop()

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

    def set_status_callback(self, callback: Callable[[QPoint | Vector2 | None, set[int | Qt.MouseButton], set[int | Qt.Key]], None] | None) -> None:
        self._status_callback = callback  # type: ignore[assignment]  # pyright: ignore[reportAssignmentType]

    def select_room(self, room: IndoorMapRoom, *, clear_existing: bool):
        if clear_existing:
            self._selected_rooms.clear()
        if room in self._selected_rooms:
            self._selected_rooms.remove(room)
        self._selected_rooms.append(room)
        self.mark_dirty()

    def select_rooms(self, rooms: list[IndoorMapRoom], *, clear_existing: bool = True):
        """Select multiple rooms at once."""
        if clear_existing:
            self._selected_rooms.clear()
        for room in rooms:
            if room in self._selected_rooms:
                self._selected_rooms.remove(room)
            self._selected_rooms.append(room)
        self.mark_dirty()

    def room_under_mouse(self) -> IndoorMapRoom | None:
        return self._under_mouse_room

    def is_dragging_rooms(self) -> bool:
        return self._dragging and self._drag_mode == DragMode.ROOMS

    def selected_hook(self) -> tuple[IndoorMapRoom, int] | None:
        return self._selected_hook

    def hook_under_mouse(
        self,
        world: Vector3,
        *,
        radius: float = HOOK_HOVER_RADIUS,
    ) -> tuple[IndoorMapRoom, int] | None:
        """Return (room, hook_index) if a hook is under the given world position."""
        for room in reversed(self._map.rooms):
            for idx, hook in enumerate(room.component.hooks):
                hook_pos = room.hook_position(hook)
                if Vector2.from_vector3(hook_pos).distance(Vector2.from_vector3(world)) <= radius:
                    return room, idx
        return None

    def selected_rooms(self) -> list[IndoorMapRoom]:
        return self._selected_rooms

    def clear_selected_rooms(self):
        self._selected_rooms.clear()
        self.mark_dirty()

    def rotate_drag_selection(self, delta_y: float):
        """Rotate currently dragged rooms using mouse wheel delta."""
        if not self.is_dragging_rooms() or not self._drag_rooms:
            return
        step = math.copysign(self.rotation_snap, delta_y)
        for room in self._drag_rooms:
            room.rotation = (room.rotation + step) % 360
            # Invalidate cached walkmesh since rotation affects the geometry
            self._invalidate_walkmesh_cache(room)
        self._map.rebuild_room_connections()
        self.mark_dirty()

    def clear_selected_hook(self):
        self._selected_hook = None
        self.mark_dirty()

    def _validate_selected_hook(self):
        """Validate that the selected hook is still valid (room exists and hook index is valid)."""
        if self._selected_hook is None:
            return
        room, hook_index = self._selected_hook
        # Check if room still exists in map
        if room not in self._map.rooms:
            self._selected_hook = None
            self.mark_dirty()
            return
        # Check if hook index is still valid
        if hook_index < 0 or hook_index >= len(room.component.hooks):
            self._selected_hook = None
            self.mark_dirty()

    def select_hook(
        self,
        room: IndoorMapRoom,
        hook_index: int,
        *,
        clear_existing: bool,
    ):
        # Validate hook index
        if hook_index < 0 or hook_index >= len(room.component.hooks):
            return
        if clear_existing:
            self._selected_rooms.clear()
        self._selected_hook = (room, hook_index)
        self.mark_dirty()

    def set_material_colors(self, material_colors: dict[SurfaceMaterial, QColor]):
        self._material_colors = material_colors
        self.mark_dirty()

    def set_colorize_materials(self, enabled: bool):
        self._colorize_materials = enabled
        self.mark_dirty()

    def set_snap_to_grid(self, enabled: bool):
        self.snap_to_grid = enabled
        self.mark_dirty()

    def set_snap_to_hooks(self, enabled: bool):
        self.snap_to_hooks = enabled
        self.mark_dirty()

    def set_show_grid(self, enabled: bool):
        self.show_grid = enabled
        self.mark_dirty()

    def set_hide_magnets(self, enabled: bool):
        self.hide_magnets = enabled
        self.mark_dirty()

    def set_grid_size(self, size: float):
        self.grid_size = size
        self.mark_dirty()

    def set_rotation_snap(self, snap: float):
        self.rotation_snap = snap
        self.mark_dirty()

    def invalidate_rooms(self, rooms: list[IndoorMapRoom]):
        for room in rooms:
            self._invalidate_walkmesh_cache(room)
        # Validate selected hook in case the room was deleted or modified
        self._validate_selected_hook()
        self.mark_dirty()

    def pick_face(self, world: Vector3) -> tuple[IndoorMapRoom | None, int | None]:
        """Return the room and face index under the given world position."""
        for room in reversed(self._map.rooms):
            # Use transformed walkmesh for picking (to account for position/rotation/flip)
            walkmesh = self._get_room_walkmesh(room)
            face = walkmesh.faceAt(world.x, world.y)
            if face is None:
                continue
            # Find the index in the base walkmesh (not transformed) since that's what we modify
            base_bwm = room.base_walkmesh()
            face_index: int | None = None
            # The transformed walkmesh is a deepcopy, so we need to match by geometry
            # Since deepcopy preserves order, we can use the index from transformed walkmesh
            # But we need to ensure it's valid for the base walkmesh
            for idx, candidate in enumerate(walkmesh.faces):
                if candidate is face:
                    # Index should match base walkmesh since deepcopy preserves order
                    if idx < len(base_bwm.faces):
                        face_index = idx
                    break
            if face_index is not None:
                return room, face_index
        return None, None

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

        best_distance = float("inf")
        best_snap: SnapResult = SnapResult(position=position, snapped=False)
        # Snap threshold scales with zoom - reduced to keep snaps helpful but separable
        snap_threshold = max(HOOK_SNAP_BASE_THRESHOLD, HOOK_SNAP_SCALE_FACTOR / self._cam_scale)

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
                if distance_2d < HOOK_CONNECTION_THRESHOLD:
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

    def keys_down(self) -> set[int | Qt.Key]:
        return set(self._keys_down)

    def mouse_down(self) -> set[int | Qt.MouseButton]:
        return set(self._mouse_down)

    # =========================================================================
    # Drag operations
    # =========================================================================

    def start_drag(self, room: IndoorMapRoom):
        """Start dragging selected rooms.

        If the room is not in the selection, it will be added first.
        This ensures clicking on any room can start a drag.
        """
        # Ensure the room is in the selection (add it if not)
        if room not in self._selected_rooms:
            self._selected_rooms.append(room)

        # Now start the drag
        self._dragging = True
        self._drag_mode = DragMode.ROOMS
        self._drag_rooms = self._selected_rooms.copy()
        self._drag_start_positions = [Vector3(*r.position) for r in self._drag_rooms]
        self._drag_start_rotations = [r.rotation for r in self._drag_rooms]

        # Check if room is currently snapped and record snap anchor for soft snapping
        if self.snap_to_hooks and room:
            snap_result = self._find_hook_snap(room, room.position)
            if snap_result.snapped:
                # Check if room is actually at the snap position (within small threshold)
                distance_to_snap = Vector2.from_vector3(room.position).distance(Vector2.from_vector3(snap_result.position))
                # Use same threshold as _find_hook_snap for consistency
                snap_threshold = max(HOOK_SNAP_BASE_THRESHOLD, HOOK_SNAP_SCALE_FACTOR / self._cam_scale)
                if distance_to_snap <= snap_threshold:
                    # Room is snapped - record the snap anchor
                    self._snap_anchor_position = Vector3(*snap_result.position)
                else:
                    # Not actually snapped
                    self._snap_anchor_position = None
            else:
                self._snap_anchor_position = None
        else:
            self._snap_anchor_position = None

        self.mark_dirty()

    def start_warp_drag(self):
        """Start dragging the warp point."""
        self._dragging_warp = True
        self._drag_mode = DragMode.WARP
        self._warp_drag_start = Vector3(*self._map.warp_point)

    def start_marquee(self, screen_pos: Vector2):
        """Start marquee selection."""
        self._marquee_active = True
        self._drag_mode = DragMode.MARQUEE
        self._marquee_start = screen_pos
        self._marquee_end = screen_pos

    def end_drag(self):
        """End dragging and emit appropriate signal.

        CRITICAL: This MUST be called on mouse release to stop ALL drag operations.
        """
        # Handle room dragging
        if self._dragging:
            self._dragging = False
            if self._drag_rooms:
                new_positions = [Vector3(*r.position) for r in self._drag_rooms]
                self.sig_rooms_moved.emit(self._drag_rooms, self._drag_start_positions, new_positions)
                new_rotations = [r.rotation for r in self._drag_rooms]
                if self._drag_start_rotations:
                    self.sig_rooms_rotated.emit(self._drag_rooms, self._drag_start_rotations, new_rotations)
            self._drag_rooms = []
            self._drag_start_positions = []
            self._drag_start_rotations = []
            self._snap_indicator = None
            self._snap_anchor_position = None

        # Handle warp point dragging
        if self._dragging_warp:
            self._dragging_warp = False
            new_pos = Vector3(*self._map.warp_point)
            if self._warp_drag_start.distance(new_pos) > POSITION_CHANGE_EPSILON:
                self.sig_warp_moved.emit(self._warp_drag_start, new_pos)

        # Handle marquee selection - ALWAYS clear if active
        if self._marquee_active:
            self._marquee_active = False
            # Only select rooms if marquee actually moved (not just a click)
            marquee_moved = self._marquee_start.distance(self._marquee_end) > MARQUEE_MOVE_THRESHOLD_PIXELS
            if marquee_moved:
                # Select rooms within marquee
                rooms_in_marquee = self._get_rooms_in_marquee()
                additive = Qt.Key.Key_Shift in self._keys_down
                self.sig_marquee_select.emit(rooms_in_marquee, additive)

        # CRITICAL: Always reset drag mode to NONE
        self._drag_mode = DragMode.NONE
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
        self._cam_scale = max(MIN_CAMERA_ZOOM, min(zoom, MAX_CAMERA_ZOOM))
        self.mark_dirty()

    def zoom_in_camera(self, zoom_factor: float):
        """Zoom camera by a multiplicative factor for linear visual zoom.

        Args:
            zoom_factor: Multiplier for zoom (e.g., 1.15 to zoom in 15%, 0.869 to zoom out 15%)
        """
        self.set_camera_zoom(self._cam_scale * zoom_factor)

    def camera_position(self) -> Vector2:
        return Vector2(*self._cam_position)

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
        width, height = image.width() * COMPONENT_PREVIEW_SCALE, image.height() * COMPONENT_PREVIEW_SCALE

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

    def _face_color(
        self,
        material: SurfaceMaterial,
        *,
        alpha: int | None = None,
    ) -> QColor:
        """Resolve the display color for a face."""
        if self._colorize_materials and material in self._material_colors:
            color = QColor(self._material_colors[material])
        else:
            if isinstance(material, SurfaceMaterial):
                is_walkable = material.is_walkable()
            else:
                material_value = int(material)
                is_walkable = material_value in self._walkable_values
            color = QColor(180, 180, 180) if is_walkable else QColor(120, 120, 120)
        if alpha is not None:
            color.setAlpha(alpha)
        return color

    def _draw_hooks_for_component(
        self,
        painter: QPainter,
        component: KitComponent,
        position: Vector3,
        rotation: float,
        flip_x: bool,
        flip_y: bool,
        connections: list[IndoorMapRoom | None] | None = None,
        *,
        alpha: int = 255,
        selected: tuple[IndoorMapRoom, int] | None = None,
        room_for_selection: IndoorMapRoom | None = None,
    ):
        """Draw hook markers for a component at a transformed position."""
        # Use a temporary room to reuse hook_position logic
        temp_room = IndoorMapRoom(component, Vector3(*position), rotation, flip_x=flip_x, flip_y=flip_y)

        for hook_index, hook in enumerate(component.hooks):
            hook_pos = temp_room.hook_position(hook)
            is_connected = bool(connections and hook_index < len(connections) and connections[hook_index] is not None)
            is_selected = selected is not None and room_for_selection is not None and selected == (room_for_selection, hook_index)

            if is_selected:
                brush_color = QColor(HOOK_COLOR_SELECTED[0], HOOK_COLOR_SELECTED[1], HOOK_COLOR_SELECTED[2], alpha)
                pen_color = QColor(HOOK_PEN_COLOR_SELECTED[0], HOOK_PEN_COLOR_SELECTED[1], HOOK_PEN_COLOR_SELECTED[2], alpha)
                radius = HOOK_SELECTED_RADIUS
            elif is_connected:
                brush_color = QColor(HOOK_COLOR_CONNECTED[0], HOOK_COLOR_CONNECTED[1], HOOK_COLOR_CONNECTED[2], alpha)
                pen_color = QColor(HOOK_PEN_COLOR_CONNECTED[0], HOOK_PEN_COLOR_CONNECTED[1], HOOK_PEN_COLOR_CONNECTED[2], alpha)
                radius = HOOK_DISPLAY_RADIUS
            else:
                brush_color = QColor(HOOK_COLOR_UNCONNECTED[0], HOOK_COLOR_UNCONNECTED[1], HOOK_COLOR_UNCONNECTED[2], alpha)
                pen_color = QColor(HOOK_PEN_COLOR_UNCONNECTED[0], HOOK_PEN_COLOR_UNCONNECTED[1], HOOK_PEN_COLOR_UNCONNECTED[2], alpha)
                radius = HOOK_DISPLAY_RADIUS

            painter.setBrush(brush_color)
            painter.setPen(QPen(pen_color, GRID_PEN_WIDTH))
            painter.drawEllipse(QPointF(hook_pos.x, hook_pos.y), radius, radius)

    def _draw_room_walkmesh(
        self,
        painter: QPainter,
        room: IndoorMapRoom,
    ):
        """Draw a room using its walkmesh geometry (no QImage)."""
        bwm = self._get_room_walkmesh(room)

        # Draw each face with appropriate color based on material
        for face in bwm.faces:
            painter.setBrush(self._face_color(face.material))
            painter.setPen(Qt.PenStyle.NoPen)
            path = self._build_face(face)
            painter.drawPath(path)

        # Draw hooks (snap points) for this room
        self._draw_hooks_for_component(
            painter,
            room.component,
            room.position,
            room.rotation,
            room.flip_x,
            room.flip_y,
            connections=room.hooks,
            selected=self._selected_hook,
            room_for_selection=room,
        )

    def _draw_cursor_walkmesh(self, painter: QPainter):
        """Draw the cursor preview using walkmesh geometry.

        Draws the cursor component's walkmesh transformed by cursor position,
        rotation, and flip settings. Uses semi-transparent grey to indicate
        it's a preview.
        """
        if not self.cursor_component:
            return

        # Get a transformed copy of the component's BWM
        bwm: BWM = deepcopy(self.cursor_component.bwm)
        bwm.flip(self.cursor_flip_x, self.cursor_flip_y)
        bwm.rotate(self.cursor_rotation)
        bwm.translate(self.cursor_point.x, self.cursor_point.y, self.cursor_point.z)

        # Draw each face with semi-transparent color
        for face in bwm.faces:
            painter.setBrush(self._face_color(face.material, alpha=CURSOR_PREVIEW_ALPHA))
            painter.setPen(Qt.PenStyle.NoPen)
            path = self._build_face(face)
            painter.drawPath(path)

        # Draw hooks for the cursor preview (semi-transparent)
        self._draw_hooks_for_component(
            painter,
            self.cursor_component,
            self.cursor_point,
            self.cursor_rotation,
            self.cursor_flip_x,
            self.cursor_flip_y,
            connections=None,
            alpha=CURSOR_HOOK_ALPHA,
            selected=self._selected_hook,
            room_for_selection=None,
        )

    def _draw_room_highlight(
        self,
        painter: QPainter,
        room: IndoorMapRoom,
        alpha: int,
        color: QColor | None = None,
    ):
        bwm: BWM = self._get_room_walkmesh(room)
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
        room_id: int = id(room)
        if room_id not in self._cached_walkmeshes:
            self._cached_walkmeshes[room_id] = room.walkmesh()
        return self._cached_walkmeshes[room_id]

    def _invalidate_walkmesh_cache(self, room: IndoorMapRoom):
        """Invalidate cached walkmesh for a room."""
        room_id: int = id(room)
        self._cached_walkmeshes.pop(room_id, None)

    # ------------------------------------------------------------------
    # Hook editing helpers
    # ------------------------------------------------------------------
    def _ensure_room_component_unique(self, room: IndoorMapRoom):
        """Clone the component so hooks can be edited per-room."""
        # If any other room shares this component instance, clone
        shared: bool = any(r is not room and r.component is room.component for r in self._map.rooms)
        if not shared:
            return
        component_copy: KitComponent = deepcopy(room.component)
        room.component = component_copy
        # Rebuild connections list to match hooks length
        room.hooks = [None] * len(component_copy.hooks)  # type: ignore[assignment]
        self._invalidate_walkmesh_cache(room)

    def _world_to_local_hook(
        self,
        room: IndoorMapRoom,
        world_pos: Vector3,
    ) -> Vector3:
        """Convert world coordinates to local hook coordinates for the room."""
        pos: Vector3 = Vector3(*world_pos)
        # translate to room local
        pos.x -= room.position.x
        pos.y -= room.position.y
        # inverse rotation
        cos_r: float = math.cos(math.radians(-room.rotation))
        sin_r: float = math.sin(math.radians(-room.rotation))
        x: float = pos.x * cos_r - pos.y * sin_r
        y: float = pos.x * sin_r + pos.y * cos_r
        pos.x, pos.y = x, y
        # inverse flip
        if room.flip_x:
            pos.x = -pos.x
        if room.flip_y:
            pos.y = -pos.y
        return pos

    def add_hook_at(
        self,
        world_pos: Vector3,
    ):
        """Add a hook to the room under the mouse at world_pos."""
        room = self._under_mouse_room
        if room is None:
            return
        self._ensure_room_component_unique(room)
        local_pos = self._world_to_local_hook(room, world_pos)

        # Choose a door reference: prefer existing hook door, else first kit door
        door = room.component.hooks[0].door if room.component.hooks else (room.component.kit.doors[0] if room.component.kit.doors else None)
        if door is None:
            return  # cannot add without a door reference

        hook = KitComponentHook(position=local_pos, rotation=0.0, edge=str(len(room.component.hooks)), door=door)
        room.component.hooks.append(hook)
        room.hooks.append(None)
        self._selected_hook = (room, len(room.component.hooks) - 1)
        self._map.rebuild_room_connections()
        self._invalidate_walkmesh_cache(room)
        self.mark_dirty()

    def delete_hook(
        self,
        room: IndoorMapRoom,
        hook_index: int,
    ):
        """Delete a hook from a room."""
        if hook_index < 0 or hook_index >= len(room.component.hooks):
            return
        self._ensure_room_component_unique(room)
        # Clear selected hook if it's the one being deleted or if it becomes invalid
        if self._selected_hook is not None:
            sel_room, sel_index = self._selected_hook
            if sel_room is room and (sel_index == hook_index or sel_index >= len(room.component.hooks) - 1):
                self._selected_hook = None
        room.component.hooks.pop(hook_index)
        if hook_index < len(room.hooks):
            room.hooks.pop(hook_index)
        # Validate selected hook index is still valid after deletion
        if self._selected_hook is not None:
            sel_room, sel_index = self._selected_hook
            if sel_room is room and sel_index >= len(room.component.hooks):
                self._selected_hook = None
        self._map.rebuild_room_connections()
        self._invalidate_walkmesh_cache(room)
        self.mark_dirty()

    def duplicate_hook(
        self,
        room: IndoorMapRoom,
        hook_index: int,
    ):
        """Duplicate a hook in place."""
        if hook_index < 0 or hook_index >= len(room.component.hooks):
            return
        self._ensure_room_component_unique(room)
        src: KitComponentHook = room.component.hooks[hook_index]
        new_hook = KitComponentHook(
            position=Vector3(*src.position),
            rotation=src.rotation,
            edge=str(len(room.component.hooks)),
            door=src.door,
        )
        room.component.hooks.append(new_hook)
        room.hooks.append(None)
        self._selected_hook = (room, len(room.component.hooks) - 1)
        self._map.rebuild_room_connections()
        self._invalidate_walkmesh_cache(room)
        self.mark_dirty()

    def _draw_grid(self, painter: QPainter):
        """Draw grid overlay."""
        if not self.show_grid:
            return

        painter.setPen(QPen(QColor(GRID_COLOR[0], GRID_COLOR[1], GRID_COLOR[2]), GRID_PEN_WIDTH))

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

        # Prefer the exact hook-to position for visual cue; fall back to snap position.
        if self._snap_indicator.hook_to is not None and self._snap_indicator.target_room is not None:
            pos_vec = self._snap_indicator.target_room.hook_position(self._snap_indicator.hook_to)
        else:
            pos_vec = self._snap_indicator.position

        painter.setPen(QPen(QColor(SNAP_INDICATOR_COLOR[0], SNAP_INDICATOR_COLOR[1], SNAP_INDICATOR_COLOR[2]), SNAP_INDICATOR_PEN_WIDTH))
        painter.setBrush(QColor(SNAP_INDICATOR_COLOR[0], SNAP_INDICATOR_COLOR[1], SNAP_INDICATOR_COLOR[2], SNAP_INDICATOR_ALPHA))
        painter.drawEllipse(QPointF(pos_vec.x, pos_vec.y), SNAP_INDICATOR_RADIUS, SNAP_INDICATOR_RADIUS)

    def _draw_spawn_point(self, painter: QPainter, coords: Vector3):
        # Highlight when hovering or dragging
        is_active = self._hovering_warp or self._dragging_warp
        radius = self.warp_point_radius * (WARP_POINT_ACTIVE_SCALE if is_active else 1.0)
        alpha = WARP_POINT_ALPHA_ACTIVE if is_active else WARP_POINT_ALPHA_NORMAL

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(WARP_POINT_COLOR[0], WARP_POINT_COLOR[1], WARP_POINT_COLOR[2], alpha))
        painter.drawEllipse(QPointF(coords.x, coords.y), radius, radius)

        # Draw crosshair
        line_len = radius * WARP_POINT_CROSSHAIR_SCALE
        pen_width = WARP_POINT_PEN_WIDTH_ACTIVE if is_active else WARP_POINT_PEN_WIDTH_NORMAL
        painter.setPen(QPen(QColor(WARP_POINT_COLOR[0], WARP_POINT_COLOR[1], WARP_POINT_COLOR[2]), pen_width))
        painter.drawLine(QPointF(coords.x, coords.y - line_len), QPointF(coords.x, coords.y + line_len))
        painter.drawLine(QPointF(coords.x - line_len, coords.y), QPointF(coords.x + line_len, coords.y))

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
        painter.setBrush(QColor(MARQUEE_FILL_COLOR[0], MARQUEE_FILL_COLOR[1], MARQUEE_FILL_COLOR[2], MARQUEE_FILL_COLOR[3]))
        painter.setPen(QPen(QColor(MARQUEE_BORDER_COLOR[0], MARQUEE_BORDER_COLOR[1], MARQUEE_BORDER_COLOR[2], MARQUEE_BORDER_COLOR[3]), 1, Qt.PenStyle.DashLine))
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
        painter.setBrush(QColor(BACKGROUND_COLOR[0], BACKGROUND_COLOR[1], BACKGROUND_COLOR[2], BACKGROUND_COLOR[3]))
        painter.drawRect(0, 0, self.width(), self.height())
        painter.setTransform(transform)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        # Draw grid
        self._draw_grid(painter)

        # Draw rooms using walkmesh geometry (NOT QImage - QImage is only for sidebar preview)
        for room in self._map.rooms:
            self._draw_room_walkmesh(painter, room)

            # Draw hooks (magnets)
            if not self.hide_magnets:
                for hook_index, hook in enumerate(room.component.hooks):
                    hook_pos = room.hook_position(hook)
                    # Color: unconnected = red, connected = green
                    if room.hooks[hook_index] is None:
                        painter.setBrush(QColor(HOOK_COLOR_UNCONNECTED[0], HOOK_COLOR_UNCONNECTED[1], HOOK_COLOR_UNCONNECTED[2], HOOK_COLOR_UNCONNECTED[3]))
                        painter.setPen(
                            QPen(
                                QColor(HOOK_PEN_COLOR_UNCONNECTED[0], HOOK_PEN_COLOR_UNCONNECTED[1], HOOK_PEN_COLOR_UNCONNECTED[2], HOOK_PEN_COLOR_UNCONNECTED[3]),
                                GRID_PEN_WIDTH,
                            )
                        )
                    else:
                        painter.setBrush(QColor(HOOK_COLOR_CONNECTED[0], HOOK_COLOR_CONNECTED[1], HOOK_COLOR_CONNECTED[2], HOOK_COLOR_CONNECTED[3]))
                        painter.setPen(
                            QPen(QColor(HOOK_PEN_COLOR_CONNECTED[0], HOOK_PEN_COLOR_CONNECTED[1], HOOK_PEN_COLOR_CONNECTED[2], HOOK_PEN_COLOR_CONNECTED[3]), GRID_PEN_WIDTH)
                        )
                    painter.drawEllipse(QPointF(hook_pos.x, hook_pos.y), HOOK_DISPLAY_RADIUS, HOOK_DISPLAY_RADIUS)

        # Draw connections (green lines for connected hooks)
        for room in self._map.rooms:
            for hook_index, hook in enumerate(room.component.hooks):
                if room.hooks[hook_index] is None:
                    continue
                hook_pos = room.hook_position(hook)
                xd = math.cos(math.radians(hook.rotation + room.rotation)) * hook.door.width / 2
                yd = math.sin(math.radians(hook.rotation + room.rotation)) * hook.door.width / 2
                painter.setPen(
                    QPen(
                        QColor(CONNECTION_LINE_COLOR[0], CONNECTION_LINE_COLOR[1], CONNECTION_LINE_COLOR[2], CONNECTION_LINE_COLOR[3]),
                        CONNECTION_LINE_WIDTH_SCALE / self._cam_scale,
                    )
                )
                painter.drawLine(
                    QPointF(hook_pos.x - xd, hook_pos.y - yd),
                    QPointF(hook_pos.x + xd, hook_pos.y + yd),
                )

        # Draw cursor preview using walkmesh (NOT QImage)
        self._draw_cursor_walkmesh(painter)

        # Draw snap indicator
        self._draw_snap_indicator(painter)

        # Draw hover highlight
        if self._under_mouse_room and self._under_mouse_room not in self._selected_rooms:
            self._draw_room_highlight(
                painter, self._under_mouse_room, ROOM_HOVER_ALPHA, QColor(ROOM_HOVER_COLOR[0], ROOM_HOVER_COLOR[1], ROOM_HOVER_COLOR[2], ROOM_HOVER_COLOR[3])
            )

        # Draw selection highlights
        for room in self._selected_rooms:
            self._draw_room_highlight(
                painter, room, ROOM_SELECTED_ALPHA, QColor(ROOM_SELECTED_COLOR[0], ROOM_SELECTED_COLOR[1], ROOM_SELECTED_COLOR[2], ROOM_SELECTED_COLOR[3])
            )

        # Draw spawn point (warp point)
        self._draw_spawn_point(painter, self._map.warp_point)

        # Draw marquee selection (in screen space, so after transform reset)
        self._draw_marquee(painter)

    # =========================================================================
    # Events
    # =========================================================================

    def wheelEvent(self, e: QWheelEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        self.sig_mouse_scrolled.emit(
            Vector2(e.angleDelta().x(), e.angleDelta().y()),
            e.buttons(),
            self._keys_down,
        )
        self.mark_dirty()

    def mouseMoveEvent(self, e: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        coords: Vector2 = (
            Vector2(e.x(), e.y())  # pyright: ignore[reportAttributeAccessIssue]
            if qtpy.QT5
            else Vector2(e.position().toPoint().x(), e.position().toPoint().y())  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]
        )
        coords_delta = Vector2(coords.x - self._mouse_prev.x, coords.y - self._mouse_prev.y)
        self._mouse_prev = coords
        self.sig_mouse_moved.emit(coords, coords_delta, self._mouse_down, self._keys_down)

        world = self.to_world_coords(coords.x, coords.y)
        self.cursor_point = world

        # Keep status bar updated with live mouse state
        if self._status_callback is not None:
            self._status_callback(coords, self._mouse_down, self._keys_down)

        # Update warp point hover state
        self._hovering_warp = self.is_over_warp_point(world)

        # Handle marquee selection - ONLY if left button is still held
        if self._marquee_active:
            if Qt.MouseButton.LeftButton not in self._mouse_down:
                # Left button released but marquee still active - force end it
                self.end_drag()
                return
            self._marquee_end = coords
            self.mark_dirty()
            return

        # Handle warp point dragging - ONLY if left button still held
        if self._dragging_warp:
            if Qt.MouseButton.LeftButton not in self._mouse_down:
                self.end_drag()
                return
            world_delta = self.to_world_delta(coords_delta.x, coords_delta.y)
            self._map.warp_point.x += world_delta.x
            self._map.warp_point.y += world_delta.y
            # Apply grid snap to warp point if enabled
            if self.snap_to_grid:
                self._map.warp_point = self._snap_to_grid(self._map.warp_point)
            self.mark_dirty()
            return

        # Handle hook dragging (selected hook) - ONLY if left button still held
        if self._dragging_hook and self._selected_hook is not None:
            if Qt.MouseButton.LeftButton not in self._mouse_down:
                self._dragging_hook = False
                self._map.rebuild_room_connections()
                self.mark_dirty()
                return
            room, hook_index = self._selected_hook
            if hook_index < len(room.component.hooks):
                world_delta = self.to_world_delta(coords_delta.x, coords_delta.y)
                hook = room.component.hooks[hook_index]
                # Move in world space then convert to local
                new_world = room.hook_position(hook) + Vector3(world_delta.x, world_delta.y, 0)
                local = self._world_to_local_hook(room, new_world)
                hook.position = local
                self._invalidate_walkmesh_cache(room)
                self.mark_dirty()
            return

        # Handle room dragging - ONLY if left button still held
        if self._dragging and self._drag_rooms:
            if Qt.MouseButton.LeftButton not in self._mouse_down:
                self.end_drag()
                return
            world_delta = self.to_world_delta(coords_delta.x, coords_delta.y)

            # Move all selected rooms by delta first
            for room in self._drag_rooms:
                room.position.x += world_delta.x
                room.position.y += world_delta.y
                self._invalidate_walkmesh_cache(room)

            # Get the primary room for snapping calculations
            active_room = self._drag_rooms[-1] if self._drag_rooms else None
            snapped = False

            # Soft hook snapping: only apply if within threshold, allow disconnection when dragged away
            if active_room and self.snap_to_hooks:
                # Check if we have a snap anchor from previous snap
                if self._snap_anchor_position is not None:
                    # Calculate distance from current position to snap anchor
                    distance_from_anchor = Vector2.from_vector3(active_room.position).distance(Vector2.from_vector3(self._snap_anchor_position))

                    # Dynamic disconnect threshold tied to zoom (smaller to make separation easy)
                    dynamic_disconnect = max(
                        HOOK_SNAP_DISCONNECT_BASE_THRESHOLD,
                        HOOK_SNAP_DISCONNECT_SCALE_FACTOR * max(HOOK_SNAP_BASE_THRESHOLD, HOOK_SNAP_SCALE_FACTOR / self._cam_scale),
                    )
                    # If moved beyond disconnect threshold, clear snap and allow free movement
                    if distance_from_anchor > dynamic_disconnect:
                        self._snap_anchor_position = None
                        self._snap_indicator = None
                    else:
                        # Still within threshold - check if we can still snap
                        snap_result = self._find_hook_snap(active_room, active_room.position)
                        if snap_result.snapped:
                            # Check distance from current position to snap point
                            distance_to_snap = Vector2.from_vector3(active_room.position).distance(Vector2.from_vector3(snap_result.position))
                            snap_threshold = max(HOOK_SNAP_BASE_THRESHOLD, HOOK_SNAP_SCALE_FACTOR / self._cam_scale)

                            # Only apply snap if within threshold
                            if distance_to_snap <= snap_threshold:
                                # Calculate offset and apply to all rooms
                                offset_x = snap_result.position.x - active_room.position.x
                                offset_y = snap_result.position.y - active_room.position.y
                                for room in self._drag_rooms:
                                    room.position.x += offset_x
                                    room.position.y += offset_y
                                    self._invalidate_walkmesh_cache(room)
                                self._snap_indicator = snap_result
                                # Update snap anchor to new snap position
                                self._snap_anchor_position = Vector3(*snap_result.position)
                                snapped = True
                            else:
                                # Too far from snap point - disconnect
                                self._snap_anchor_position = None
                                self._snap_indicator = None
                        else:
                            # No snap available - disconnect
                            self._snap_anchor_position = None
                            self._snap_indicator = None
                else:
                    # No existing snap anchor - try to find a new snap
                    snap_result = self._find_hook_snap(active_room, active_room.position)
                    if snap_result.snapped:
                        # Check distance from current position to snap point
                        distance_to_snap = Vector2.from_vector3(active_room.position).distance(Vector2.from_vector3(snap_result.position))
                        snap_threshold = max(1.0, 2.0 / self._cam_scale)

                        # Only apply snap if within threshold
                        if distance_to_snap <= snap_threshold:
                            # Calculate offset and apply to all rooms
                            offset_x = snap_result.position.x - active_room.position.x
                            offset_y = snap_result.position.y - active_room.position.y
                            for room in self._drag_rooms:
                                room.position.x += offset_x
                                room.position.y += offset_y
                                self._invalidate_walkmesh_cache(room)
                            self._snap_indicator = snap_result
                            # Record snap anchor position
                            self._snap_anchor_position = Vector3(*snap_result.position)
                            snapped = True
                        else:
                            self._snap_indicator = None
                    else:
                        self._snap_indicator = None

            # Apply grid snapping if enabled (and not already snapped to hook)
            if self.snap_to_grid and not snapped and active_room:
                # Snap the active room to grid, then move others by same offset
                old_pos = Vector3(*active_room.position)
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
        self._under_mouse_room, _ = self.pick_face(world)
        self.mark_dirty()

    def mousePressEvent(self, e: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        event_mouse_button = e.button()
        if event_mouse_button is None:
            return
        self._mouse_down.add(event_mouse_button)
        coords: Vector2 = (
            Vector2(e.x(), e.y())  # pyright: ignore[reportAttributeAccessIssue]
            if qtpy.QT5
            else Vector2(e.position().toPoint().x(), e.position().toPoint().y())  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]
        )
        self.sig_mouse_pressed.emit(coords, self._mouse_down, self._keys_down)
        if self._status_callback is not None:
            self._status_callback(coords, self._mouse_down, self._keys_down)

    def mouseReleaseEvent(self, e: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        event_mouse_button = e.button()
        if event_mouse_button is None:
            return
        self._mouse_down.discard(event_mouse_button)
        coords: Vector2 = (
            Vector2(e.x(), e.y())  # pyright: ignore[reportAttributeAccessIssue]
            if qtpy.QT5
            else Vector2(e.position().toPoint().x(), e.position().toPoint().y())  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]
        )
        self.sig_mouse_released.emit(coords, self._mouse_down, self._keys_down)
        if self._status_callback is not None:
            self._status_callback(coords, self._mouse_down, self._keys_down)

    def mouseDoubleClickEvent(self, e: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        event_mouse_button = e.button()
        if event_mouse_button is None:
            return
        mouse_down: set[int | Qt.MouseButton] = set(self._mouse_down)
        mouse_down.add(event_mouse_button)
        coords: Vector2 = (
            Vector2(e.x(), e.y())  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]
            if qtpy.QT5
            else Vector2(e.position().toPoint().x(), e.position().toPoint().y())  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]
        )
        self.sig_mouse_double_clicked.emit(coords, mouse_down, self._keys_down)

    def keyPressEvent(self, e: QKeyEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        # ESC key handling at renderer level for immediate cancellation
        if e.key() == Qt.Key.Key_Escape:
            # Cancel all active operations immediately
            if self._marquee_active:
                self._marquee_active = False
                self._drag_mode = DragMode.NONE
            if self._dragging:
                self.end_drag()
            if self._dragging_hook:
                self._dragging_hook = False
            if self._dragging_warp:
                self._dragging_warp = False
            # Clear selections
            self.clear_selected_rooms()
            self.clear_selected_hook()
            # Cancel placement mode
            if self.cursor_component is not None:
                self.set_cursor_component(None)
            self.mark_dirty()
            return

        self._keys_down.add(e.key())
        self.mark_dirty()

    def keyReleaseEvent(self, e: QKeyEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        self._keys_down.discard(e.key())
        self.mark_dirty()

    def focusInEvent(self, e: QFocusEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle focus in - ensure we can receive keyboard input."""
        super().focusInEvent(e)
        self.mark_dirty()

    def focusOutEvent(self, e: QFocusEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle focus out - cancel operations that require focus (standard Windows behavior)."""
        super().focusOutEvent(e)
        # Cancel drag operations when focus is lost (prevents stuck states)
        if self._dragging or self._dragging_hook or self._dragging_warp or self._marquee_active:
            self.end_drag()
            self._dragging_hook = False
            self._dragging_warp = False
            self._marquee_active = False
            self._drag_mode = DragMode.NONE
        # Clear key states to prevent stuck modifier keys
        self._keys_down.clear()
        self.mark_dirty()

    def closeEvent(self, e: QCloseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle widget close event - stop render loop and clean up resources."""
        # Stop the render timer immediately
        if hasattr(self, "_render_timer"):
            self._render_timer.stop()

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
            if hasattr(self, "isVisible"):
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
            | Qt.WindowType.WindowStaysOnTopHint & ~Qt.WindowType.WindowContextHelpButtonHint & ~Qt.WindowType.WindowMinMaxButtonsHint,
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
        update_info_data: Exception | dict[str, Any] = get_remote_toolset_update_info(use_beta_channel=GlobalSettings().useBetaChannel)
        try:
            if not isinstance(update_info_data, dict):
                raise update_info_data  # type: ignore[reportUnnecessaryIsInstance]

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
                    lambda _=None, kit_dict=kit_dict, button=button: self._download_button_pressed(button, kit_dict),
                )

                layout: QFormLayout | None = self.ui.groupBox.layout()  # type: ignore[union-attr, assignment]  # pyright: ignore[reportAssignmentType]
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

    def _download_button_pressed(
        self,
        button: QPushButton,
        info_dict: dict[str, Any],
    ):
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

        update_info_data: Exception | dict[str, Any] = get_remote_toolset_update_info(use_beta_channel=GlobalSettings().useBetaChannel)

        if isinstance(update_info_data, Exception):
            print(f"Failed to get update info: {update_info_data}")
            return False

        kits_config = update_info_data.get("kits", {})
        repository: str = kits_config.get("repository", "th3w1zard1/ToolsetData")
        release_tag: str = kits_config.get("release_tag", "latest")

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
        layout: QFormLayout | None = self.ui.groupBox.layout()  # type: ignore[assignment]  # pyright: ignore[reportAssignmentType]
        if layout is None:
            return

        for i in range(layout.rowCount()):
            item = layout.itemAt(i, QFormLayout.ItemRole.FieldRole)
            if item and isinstance(item.widget(), QPushButton):
                button: QPushButton = cast(QPushButton, item.widget())
                button.setText("Already Downloaded")
                button.setEnabled(False)

    def _download_kit(self, kit_id: str) -> bool:
        kits_path: Path = Path("kits").resolve()
        kits_path.mkdir(parents=True, exist_ok=True)
        kits_zip_path: Path = Path("kits.zip")

        update_info_data: Exception | dict[str, Any] = get_remote_toolset_update_info(use_beta_channel=GlobalSettings().useBetaChannel)

        if isinstance(update_info_data, Exception):
            print(f"Failed to get update info: {update_info_data}")
            return False

        kits_config: dict[str, Any] = update_info_data.get("kits", {})
        repository: str = kits_config.get("repository", "th3w1zard1/ToolsetData")
        release_tag: str = kits_config.get("release_tag", "latest")

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
