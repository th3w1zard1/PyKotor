from __future__ import annotations

import json
import math
import os
import tempfile
import time
from collections import deque

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Sequence, TextIO, Union, cast

import qtpy

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import QPoint, QTimer, Qt
from qtpy.QtGui import QColor, QCursor, QIcon, QPixmap
from qtpy.QtWidgets import (
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QProgressDialog,
    QStatusBar,
    QStackedWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pykotor.common.misc import Color, ResRef
from pykotor.common.module import Module, ModuleResource
from pykotor.extract.file import ResourceIdentifier
from pykotor.gl.scene import Camera
from pykotor.resource.formats.bwm import BWM
from pykotor.resource.formats.lyt import LYT, LYTDoorHook, LYTObstacle, LYTRoom, LYTTrack
from pykotor.resource.generics.git import (
    GITCamera,
    GITCreature,
    GITDoor,
    GITEncounter,
    GITEncounterSpawnPoint,
    GITInstance,
    GITPlaceable,
    GITSound,
    GITStore,
    GITTrigger,
    GITWaypoint,
)
from pykotor.resource.generics.utd import read_utd
from pykotor.resource.generics.utt import read_utt
from pykotor.resource.generics.utw import read_utw
from pykotor.resource.type import ResourceType
from pykotor.tools import module
from pykotor.tools.misc import is_mod_file
from toolset.blender import BlenderEditorMode, ConnectionState, check_blender_and_ask, get_blender_settings
from toolset.blender.integration import BlenderEditorMixin
from toolset.blender.serializers import deserialize_git_instance, serialize_module_data
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.insert_instance import InsertInstanceDialog
from toolset.gui.dialogs.select_module import SelectModuleDialog
from toolset.gui.editor import Editor
from toolset.gui.editors.git import DeleteCommand, MoveCommand, RotateCommand, _GeometryMode, _InstanceMode, _SpawnMode, open_instance_dialog
from toolset.gui.widgets.renderer.module import ModuleRenderer
from toolset.gui.widgets.settings.widgets.module_designer import ModuleDesignerSettings
from toolset.gui.windows.designer_controls import ModuleDesignerControls2d, ModuleDesignerControls3d, ModuleDesignerControlsFreeCam
from toolset.gui.windows.help import HelpWindow
from toolset.utils.misc import MODIFIER_KEY_NAMES, get_qt_button_string, get_qt_key_string
from toolset.utils.window import open_resource_editor
from utility.common.geometry import Polygon3, SurfaceMaterial, Vector2, Vector3, Vector4
from utility.error_handling import safe_repr


if TYPE_CHECKING:
    from qtpy.QtGui import QCloseEvent, QFont, QKeyEvent, QShowEvent
    from qtpy.QtWidgets import QCheckBox, _QMenu
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.common.module import UTT, UTW
    from pykotor.gl.scene import Camera
    from pykotor.resource.formats.bwm import BWM
    from pykotor.resource.generics.are import ARE
    from pykotor.resource.generics.git import GIT
    from pykotor.resource.generics.ifo import IFO
    from toolset.gui.widgets.renderer.lyt_renderer import LYTRenderer
    from toolset.gui.widgets.renderer.walkmesh import WalkmeshRenderer

if qtpy.QT5:
    from qtpy.QtWidgets import QUndoCommand, QUndoStack
elif qtpy.QT6:
    from qtpy.QtGui import QUndoCommand, QUndoStack  # pyright: ignore[reportPrivateImportUsage]
else:
    raise ValueError(f"Invalid QT_API: '{qtpy.API_NAME}'")


class _BlenderPropertyCommand(QUndoCommand):
    def __init__(
        self,
        instance: GITInstance,
        apply_func: Callable[[GITInstance, Any], None],
        old_value: Any,
        new_value: Any,
        on_change: Callable[[GITInstance], None],
        label: str,
    ):
        super().__init__(label)
        self._instance = instance
        self._apply = apply_func
        self._old = old_value
        self._new = new_value
        self._on_change = on_change

    def undo(self):
        self._apply(self._instance, self._old)
        self._on_change(self._instance)

    def redo(self):
        self._apply(self._instance, self._new)
        self._on_change(self._instance)


class _BlenderInsertCommand(QUndoCommand):
    def __init__(self, git: GIT, instance: GITInstance, editor: "ModuleDesigner"):
        super().__init__("Blender add instance")
        self._git = git
        self._instance = instance
        self._editor = editor

    def undo(self):
        if self._instance in self._git.instances():
            self._git.remove(self._instance)
        self._editor.rebuild_instance_list()

    def redo(self):
        if self._instance not in self._git.instances():
            self._git.add(self._instance)
        self._editor.rebuild_instance_list()


class _BlenderDeleteCommand(QUndoCommand):
    def __init__(self, git: GIT, instance: GITInstance, editor: "ModuleDesigner"):
        super().__init__("Blender delete instance")
        self._git = git
        self._instance = instance
        self._editor = editor

    def undo(self):
        if self._instance not in self._git.instances():
            self._git.add(self._instance)
        self._editor.rebuild_instance_list()

    def redo(self):
        if self._instance in self._git.instances():
            self._git.remove(self._instance)
        self._editor.rebuild_instance_list()


_RESREF_CLASSES = (
    GITCreature,
    GITDoor,
    GITEncounter,
    GITPlaceable,
    GITSound,
    GITStore,
    GITTrigger,
    GITWaypoint,
)
_TAG_CLASSES = (GITDoor, GITTrigger, GITWaypoint, GITPlaceable)
_BEARING_CLASSES = (GITCreature, GITDoor, GITPlaceable, GITStore, GITWaypoint)

ResrefInstance = Union[
    GITCreature,
    GITDoor,
    GITEncounter,
    GITPlaceable,
    GITSound,
    GITStore,
    GITTrigger,
    GITWaypoint,
]
TagInstance = Union[GITDoor, GITTrigger, GITWaypoint, GITPlaceable]
BearingInstance = Union[GITCreature, GITDoor, GITPlaceable, GITStore, GITWaypoint]


def run_module_designer(
    active_path: str,
    active_name: str,
    active_tsl: bool,  # noqa: FBT001
    module_path: str | None = None,
):
    """An alternative way to start the ModuleDesigner: run thisfunction in a new process so the main tool window doesn't wait on the module designer."""
    import sys

    from toolset.__main__ import main_init

    main_init()
    app = QApplication(sys.argv)
    designer_ui = ModuleDesigner(
        None,
        HTInstallation(active_path, active_name, tsl=active_tsl),
        Path(module_path) if module_path is not None else None,
    )
    # Standardized resource path format
    icon_path = ":/images/icons/sith.png"

    # Debugging: Check if the resource path is accessible
    if not QPixmap(icon_path).isNull():
        designer_ui.log.debug(f"HT main window Icon loaded successfully from {icon_path}")
        designer_ui.setWindowIcon(QIcon(QPixmap(icon_path)))
        cast("QApplication", QApplication.instance()).setWindowIcon(QIcon(QPixmap(icon_path)))
    else:
        print(f"Failed to load HT main window icon from {icon_path}")
    sys.exit(app.exec())


class ModuleDesigner(QMainWindow, BlenderEditorMixin):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation,
        mod_filepath: Path | None = None,
        use_blender: bool = False,
    ):
        super().__init__(parent)
        self.setWindowTitle("Module Designer")

        # Initialize Blender integration
        self._init_blender_integration(BlenderEditorMode.MODULE_DESIGNER)
        self._use_blender_mode: bool = use_blender
        self._blender_choice_made: bool = False  # Track if we've already asked about Blender
        self._view_stack: QStackedWidget | None = None
        self._blender_placeholder: QWidget | None = None
        self._blender_log_buffer: deque[str] = deque(maxlen=500)
        self._blender_log_path: Path | None = None
        self._blender_log_handle: TextIO | None = None
        self._blender_progress_dialog: QProgressDialog | None = None
        self._blender_log_view: QPlainTextEdit | None = None
        self._blender_connected_once: bool = False
        self._selection_sync_from_blender: bool = False
        self._selection_sync_in_progress: bool = False
        self._transform_sync_in_progress: bool = False
        self._property_sync_in_progress: bool = False
        self._instance_sync_in_progress: bool = False
        self._instance_id_lookup: dict[int, GITInstance] = {}
        self._last_walkmeshes: list[BWM] = []
        self._fallback_session_path: Path | None = None

        self._installation: HTInstallation = installation
        self._module: Module | None = None
        self._orig_filepath: Path | None = mod_filepath

        self.initial_positions: dict[GITInstance, Vector3] = {}
        self.initial_rotations: dict[GITCamera | GITCreature | GITDoor | GITPlaceable | GITStore | GITWaypoint, Vector4 | float] = {}
        self.undo_stack: QUndoStack = QUndoStack(self)

        self.selected_instances: list[GITInstance] = []
        self.settings: ModuleDesignerSettings = ModuleDesignerSettings()
        self.log: RobustLogger = RobustLogger()

        self.target_frame_rate = 120  # Target higher for smoother camera
        self.camera_update_timer = QTimer()
        self.camera_update_timer.timeout.connect(self.update_camera)
        self.camera_update_timer.start(int(1000 / self.target_frame_rate))
        self.last_frame_time: float = time.time()
        self.frame_time_samples: list[float] = []  # For adaptive timing

        self.hide_creatures: bool = False
        self.hide_placeables: bool = False
        self.hide_doors: bool = False
        self.hide_triggers: bool = False
        self.hide_encounters: bool = False
        self.hide_waypoints: bool = False
        self.hide_sounds: bool = False
        self.hide_stores: bool = False
        self.hide_cameras: bool = False
        self.lock_instances: bool = False
        # used for the undo/redo events, don't create undo/redo events until the drag finishes.
        self.is_drag_moving: bool = False
        self.is_drag_rotating: bool = False
        self.mouse_pos_history: list[Vector2] = [Vector2(0, 0), Vector2(0, 0)]

        from toolset.uic.qtpy.windows.module_designer import Ui_MainWindow

        self.ui: Ui_MainWindow = Ui_MainWindow()
        self.ui.setupUi(self)
        self._init_ui()
        self._install_view_stack()
        self._setup_signals()

        self.last_free_cam_time: float = 0.0  # Initialize the last toggle time

        def int_color_to_qcolor(int_value: int) -> QColor:
            color = Color.from_rgba_integer(int_value)
            return QColor(
                int(color.r * 255),
                int(color.g * 255),
                int(color.b * 255),
                int(color.a * 255),
            )

        self.material_colors: dict[SurfaceMaterial, QColor] = {
            SurfaceMaterial.UNDEFINED: int_color_to_qcolor(self.settings.undefinedMaterialColour),
            SurfaceMaterial.OBSCURING: int_color_to_qcolor(self.settings.obscuringMaterialColour),
            SurfaceMaterial.DIRT: int_color_to_qcolor(self.settings.dirtMaterialColour),
            SurfaceMaterial.GRASS: int_color_to_qcolor(self.settings.grassMaterialColour),
            SurfaceMaterial.STONE: int_color_to_qcolor(self.settings.stoneMaterialColour),
            SurfaceMaterial.WOOD: int_color_to_qcolor(self.settings.woodMaterialColour),
            SurfaceMaterial.WATER: int_color_to_qcolor(self.settings.waterMaterialColour),
            SurfaceMaterial.NON_WALK: int_color_to_qcolor(self.settings.nonWalkMaterialColour),
            SurfaceMaterial.TRANSPARENT: int_color_to_qcolor(self.settings.transparentMaterialColour),
            SurfaceMaterial.CARPET: int_color_to_qcolor(self.settings.carpetMaterialColour),
            SurfaceMaterial.METAL: int_color_to_qcolor(self.settings.metalMaterialColour),
            SurfaceMaterial.PUDDLES: int_color_to_qcolor(self.settings.puddlesMaterialColour),
            SurfaceMaterial.SWAMP: int_color_to_qcolor(self.settings.swampMaterialColour),
            SurfaceMaterial.MUD: int_color_to_qcolor(self.settings.mudMaterialColour),
            SurfaceMaterial.LEAVES: int_color_to_qcolor(self.settings.leavesMaterialColour),
            SurfaceMaterial.LAVA: int_color_to_qcolor(self.settings.lavaMaterialColour),
            SurfaceMaterial.BOTTOMLESS_PIT: int_color_to_qcolor(self.settings.bottomlessPitMaterialColour),
            SurfaceMaterial.DEEP_WATER: int_color_to_qcolor(self.settings.deepWaterMaterialColour),
            SurfaceMaterial.DOOR: int_color_to_qcolor(self.settings.doorMaterialColour),
            SurfaceMaterial.NON_WALK_GRASS: int_color_to_qcolor(self.settings.nonWalkGrassMaterialColour),
            SurfaceMaterial.TRIGGER: int_color_to_qcolor(self.settings.nonWalkGrassMaterialColour),
        }

        self.ui.flatRenderer.material_colors = self.material_colors
        self.ui.flatRenderer.hide_walkmesh_edges = True
        self.ui.flatRenderer.highlight_boundaries = False

        self._controls3d: ModuleDesignerControls3d | ModuleDesignerControlsFreeCam = ModuleDesignerControls3d(self, self.ui.mainRenderer)
        # self._controls3d: ModuleDesignerControls3d | ModuleDesignerControlsFreeCam = ModuleDesignerControlsFreeCam(self, self.ui.mainRenderer)  # Doesn't work when set in __init__, trigger this in onMousePressed
        self._controls2d: ModuleDesignerControls2d = ModuleDesignerControls2d(self, self.ui.flatRenderer)

        # LYT renderer for layout tab
        self._lyt_renderer: LYTRenderer | None = None

        if mod_filepath is None:  # Use singleShot timer so the ui window opens while the loading is happening.
            QTimer().singleShot(33, self.open_module_with_dialog)
        else:
            QTimer().singleShot(33, lambda: self.open_module(mod_filepath))

    def showEvent(self, a0: QShowEvent):
        if self.ui.mainRenderer._scene is None:  # noqa: SLF001
            return  # Don't show the window if the scene isn't ready, otherwise the gl context stuff will start prematurely.
        super().showEvent(a0)

    def closeEvent(self, event: QCloseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        from toolset.gui.common.localization import translate as tr

        reply = QMessageBox.question(
            self,
            tr("Confirm Exit"),
            tr("Really quit the module designer? You may lose unsaved changes."),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Stop Blender mode if active
            if self.is_blender_mode():
                self.stop_blender_mode()
            event.accept()  # Let the window close
        else:
            event.ignore()  # Ignore the close event

    def _setup_signals(self):
        self.ui.actionOpen.triggered.connect(self.open_module_with_dialog)
        self.ui.actionSave.triggered.connect(self.save_git)
        self.ui.actionInstructions.triggered.connect(self.show_help_window)

        self.ui.actionUndo.triggered.connect(self._on_undo)
        self.ui.actionRedo.triggered.connect(self._on_redo)

        # Connect undo stack signals for Blender sync
        self.undo_stack.indexChanged.connect(self._on_undo_stack_changed)

        # Layout tab actions
        self.ui.actionAddRoom.triggered.connect(self.on_add_room)
        self.ui.actionAddDoorHook.triggered.connect(self.on_add_door_hook)
        self.ui.actionAddTrack.triggered.connect(self.on_add_track)
        self.ui.actionAddObstacle.triggered.connect(self.on_add_obstacle)
        self.ui.actionImportTexture.triggered.connect(self.on_import_texture)
        self.ui.actionGenerateWalkmesh.triggered.connect(self.on_generate_walkmesh)

        # Connect LYT editor signals to update UI
        self.ui.mainRenderer.sig_lyt_updated.connect(self.on_lyt_updated)

        self.ui.resourceTree.clicked.connect(self.on_resource_tree_single_clicked)
        self.ui.resourceTree.doubleClicked.connect(self.on_resource_tree_double_clicked)
        self.ui.resourceTree.customContextMenuRequested.connect(self.on_resource_tree_context_menu)

        self.ui.viewCreatureCheck.toggled.connect(self.update_toggles)
        self.ui.viewPlaceableCheck.toggled.connect(self.update_toggles)
        self.ui.viewDoorCheck.toggled.connect(self.update_toggles)
        self.ui.viewSoundCheck.toggled.connect(self.update_toggles)
        self.ui.viewTriggerCheck.toggled.connect(self.update_toggles)
        self.ui.viewEncounterCheck.toggled.connect(self.update_toggles)
        self.ui.viewWaypointCheck.toggled.connect(self.update_toggles)
        self.ui.viewCameraCheck.toggled.connect(self.update_toggles)
        self.ui.viewStoreCheck.toggled.connect(self.update_toggles)
        self.ui.backfaceCheck.toggled.connect(self.update_toggles)
        self.ui.lightmapCheck.toggled.connect(self.update_toggles)
        self.ui.cursorCheck.toggled.connect(self.update_toggles)

        self.ui.viewCreatureCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewCreatureCheck)  # type: ignore[method-assign]  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewPlaceableCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewPlaceableCheck)  # type: ignore[method-assign]  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewDoorCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewDoorCheck)  # type: ignore[method-assign]  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewSoundCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewSoundCheck)  # type: ignore[method-assign]  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewTriggerCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewTriggerCheck)  # type: ignore[method-assign]  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewEncounterCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewEncounterCheck)  # type: ignore[method-assign]  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewWaypointCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewWaypointCheck)  # type: ignore[method-assign]  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewCameraCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewCameraCheck)  # type: ignore[method-assign]  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewStoreCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewStoreCheck)  # type: ignore[method-assign]  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]

        self.ui.instanceList.clicked.connect(self.on_instance_list_single_clicked)
        self.ui.instanceList.doubleClicked.connect(self.on_instance_list_double_clicked)
        self.ui.instanceList.customContextMenuRequested.connect(self.on_instance_list_right_clicked)

        self.ui.mainRenderer.sig_renderer_initialized.connect(self.on_3d_renderer_initialized)
        self.ui.mainRenderer.sig_scene_initialized.connect(self.on_3d_scene_initialized)
        self.ui.mainRenderer.sig_mouse_pressed.connect(self.on_3d_mouse_pressed)
        self.ui.mainRenderer.sig_mouse_released.connect(self.on_3d_mouse_released)
        self.ui.mainRenderer.sig_mouse_moved.connect(self.on_3d_mouse_moved)
        self.ui.mainRenderer.sig_mouse_scrolled.connect(self.on_3d_mouse_scrolled)
        self.ui.mainRenderer.sig_keyboard_pressed.connect(self.on_3d_keyboard_pressed)
        self.ui.mainRenderer.sig_object_selected.connect(self.on_3d_object_selected)
        self.ui.mainRenderer.sig_keyboard_released.connect(self.on_3d_keyboard_released)

        self.ui.flatRenderer.sig_mouse_pressed.connect(self.on_2d_mouse_pressed)
        self.ui.flatRenderer.sig_mouse_moved.connect(self.on_2d_mouse_moved)
        self.ui.flatRenderer.sig_mouse_scrolled.connect(self.on_2d_mouse_scrolled)
        self.ui.flatRenderer.sig_key_pressed.connect(self.on_2d_keyboard_pressed)
        self.ui.flatRenderer.sig_mouse_released.connect(self.on_2d_mouse_released)
        self.ui.flatRenderer.sig_key_released.connect(self.on_2d_keyboard_released)

        # Layout tree signals
        self.ui.lytTree.itemSelectionChanged.connect(self.on_lyt_tree_selection_changed)
        self.ui.lytTree.customContextMenuRequested.connect(self.on_lyt_tree_context_menu)

        # Position/rotation spinbox signals
        self.ui.posXSpin.valueChanged.connect(self.on_room_position_changed)
        self.ui.posYSpin.valueChanged.connect(self.on_room_position_changed)
        self.ui.posZSpin.valueChanged.connect(self.on_room_position_changed)
        self.ui.rotXSpin.valueChanged.connect(self.on_room_rotation_changed)
        self.ui.rotYSpin.valueChanged.connect(self.on_room_rotation_changed)
        self.ui.rotZSpin.valueChanged.connect(self.on_room_rotation_changed)

        # Model edit signals
        self.ui.modelEdit.textChanged.connect(self.on_room_model_changed)
        self.ui.browseModelButton.clicked.connect(self.on_browse_model)

        # Door hook signals
        self.ui.roomNameCombo.currentTextChanged.connect(self.on_doorhook_room_changed)
        self.ui.doorNameEdit.textChanged.connect(self.on_doorhook_name_changed)

    def _init_ui(self):
        self.custom_status_bar = QStatusBar(self)
        self.setStatusBar(self.custom_status_bar)

        # Remove default margins/spacing for better space usage
        self.custom_status_bar.setContentsMargins(4, 0, 4, 0)

        # Emoji styling constant for consistent, crisp rendering
        # Uses proper emoji font fallback and slightly larger size for clarity
        self._emoji_style = "font-size:12pt; font-family:'Segoe UI Emoji','Apple Color Emoji','Noto Color Emoji','EmojiOne','Twemoji Mozilla','Segoe UI Symbol',sans-serif; vertical-align:middle;"

        # Create a main container widget that spans the full width
        self.custom_status_bar_container = QWidget()
        self.custom_status_bar_layout = QVBoxLayout(self.custom_status_bar_container)
        self.custom_status_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.custom_status_bar_layout.setSpacing(2)

        # Create labels for the status bar with proper styling
        self.mouse_pos_label = QLabel("Mouse Coords: ")
        self.buttons_keys_pressed_label = QLabel("Keys/Buttons: ")
        self.selected_instance_label = QLabel("Selected Instance: ")
        self.view_camera_label = QLabel("View: ")

        # Set labels to allow rich text
        for label in [self.mouse_pos_label, self.buttons_keys_pressed_label, self.selected_instance_label, self.view_camera_label]:
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # First row: distribute evenly across full width
        first_row = QHBoxLayout()
        first_row.setContentsMargins(0, 0, 0, 0)
        first_row.setSpacing(8)

        first_row.addWidget(self.mouse_pos_label, 1)
        first_row.addWidget(self.selected_instance_label, 2)
        first_row.addWidget(self.buttons_keys_pressed_label, 1)

        # Second row: camera info spans full width
        self.custom_status_bar_layout.addLayout(first_row)
        self.custom_status_bar_layout.addWidget(self.view_camera_label)

        self.blender_status_chip = QLabel("Blender: idle")
        self.blender_status_chip.setTextFormat(Qt.TextFormat.RichText)
        self.blender_status_chip.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.custom_status_bar_layout.addWidget(self.blender_status_chip)

        # Add the container as a regular widget (not permanent) to use full width
        self.custom_status_bar.addWidget(self.custom_status_bar_container, 1)

    def _install_view_stack(self):
        """Wrap the GL/2D split with a stacked widget so we can swap in Blender instructions."""
        if self._view_stack is not None:
            return

        self._view_stack = QStackedWidget(self)
        self.ui.verticalLayout_2.removeWidget(self.ui.splitter)
        self._view_stack.addWidget(self.ui.splitter)
        self._blender_placeholder = self._create_blender_placeholder()
        self._view_stack.addWidget(self._blender_placeholder)
        self.ui.verticalLayout_2.addWidget(self._view_stack)

    def _create_blender_placeholder(self) -> QWidget:
        """Create placeholder pane shown while Blender drives the rendering."""
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        headline = QLabel(
            "<b>Blender mode is active.</b><br>"
            "The Holocron Toolset will defer all 3D rendering and editing to Blender. "
            "Use the Blender window to move the camera, manipulate instances, and "
            "open object context menus. This panel streams Blender's console output for diagnostics."
        )
        headline.setWordWrap(True)
        layout.addWidget(headline)

        self._blender_log_view = QPlainTextEdit(container)
        self._blender_log_view.setReadOnly(True)
        self._blender_log_view.setPlaceholderText("Blender log output will appear here once the IPC bridge starts…")
        layout.addWidget(self._blender_log_view, 1)

        return container

    def _show_blender_workspace(self):
        if self._view_stack is not None and self._blender_placeholder is not None:
            self._view_stack.setCurrentWidget(self._blender_placeholder)

    def _show_internal_workspace(self):
        if self._view_stack is not None:
            self._view_stack.setCurrentWidget(self.ui.splitter)

    def _invoke_on_ui_thread(self, func: Callable[[], None]):
        """Ensure UI mutations run on the main Qt thread."""
        QTimer.singleShot(0, func)

    def _prepare_for_blender_session(self, module_root: str):
        """Initialize UI elements before launching Blender."""
        self._blender_connected_once = False
        self._show_blender_workspace()
        self._start_blender_log_capture(module_root)
        self._update_blender_status_chip("Launching…", severity="info")
        self._show_blender_progress_dialog(f"Launching Blender for '{module_root}'…")

    def _start_blender_log_capture(self, module_root: str):
        log_dir = Path(tempfile.gettempdir()) / "HolocronToolset" / "blender_logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self._blender_log_path = log_dir / f"{module_root}_{timestamp}.log"
        try:
            self._blender_log_handle = self._blender_log_path.open("w", encoding="utf-8", buffering=1)
        except OSError as exc:
            self.log.error("Failed to open blender log file %s: %s", self._blender_log_path, exc)
            self._blender_log_handle = None
        self._blender_log_buffer.clear()
        if self._blender_log_view:
            self._blender_log_view.clear()

    def _close_blender_log_capture(self):
        if self._blender_log_handle:
            try:
                self._blender_log_handle.close()
            except OSError:
                pass
        self._blender_log_handle = None
        if self._blender_log_path:
            self.log.debug("Blender log saved to %s", self._blender_log_path)

    def _append_blender_log_line(self, line: str):
        self._blender_log_buffer.append(line)
        if self._blender_log_handle:
            try:
                self._blender_log_handle.write(line + "\n")
            except OSError:
                self._blender_log_handle = None
        if self._blender_log_view:
            self._blender_log_view.appendPlainText(line)

    def _update_blender_status_chip(self, message: str, *, severity: str = "info"):
        if not hasattr(self, "blender_status_chip"):
            return
        palette = {
            "info": "#0055B0",
            "ok": "#228800",
            "warn": "#c46811",
            "error": "#b00020",
        }
        color = palette.get(severity, "#0055B0")
        self.blender_status_chip.setText(f"<b><span style='{self._emoji_style}'>🧠</span>&nbsp;Blender:</b> <span style='color:{color}'>{message}</span>")

    def _show_blender_progress_dialog(self, message: str):
        if self._blender_progress_dialog is None:
            dialog = QProgressDialog(self)
            dialog.setLabelText(message)
            dialog.setCancelButtonText("Cancel launch")
            dialog.setWindowTitle("Connecting to Blender")
            dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
            dialog.setMinimum(0)
            dialog.setMaximum(0)
            dialog.canceled.connect(self._cancel_blender_launch)
            self._blender_progress_dialog = dialog
        else:
            self._blender_progress_dialog.setLabelText(message)
        self._blender_progress_dialog.show()

    def _dismiss_blender_progress_dialog(self):
        if self._blender_progress_dialog is not None:
            self._blender_progress_dialog.hide()

    def _cancel_blender_launch(self):
        self.log.warning("User cancelled Blender launch")
        self.stop_blender_mode()
        self._close_blender_log_capture()
        self._show_internal_workspace()
        self._dismiss_blender_progress_dialog()

    def _on_blender_output(self, line: str):
        super()._on_blender_output(line)

        def _append():
            self._append_blender_log_line(line)

        self._invoke_on_ui_thread(_append)

    def _on_blender_state_change(self, state: ConnectionState):
        super()._on_blender_state_change(state)
        self._invoke_on_ui_thread(lambda: self._handle_blender_state_change(state))

    def _handle_blender_state_change(self, state: ConnectionState):
        if state == ConnectionState.CONNECTING:
            self._update_blender_status_chip("Connecting…", severity="info")
        elif state == ConnectionState.CONNECTED:
            self._blender_connected_once = True
            self._dismiss_blender_progress_dialog()
            self._update_blender_status_chip("Connected", severity="ok")
        elif state == ConnectionState.ERROR:
            self._update_blender_status_chip("Connection error", severity="error")
        elif state == ConnectionState.DISCONNECTED and self._blender_connected_once:
            self._update_blender_status_chip("Disconnected", severity="warn")

    def _on_blender_connection_failed(self):
        self._invoke_on_ui_thread(lambda: self._handle_blender_launch_failure("IPC handshake failed"))

    def _handle_blender_launch_failure(self, reason: str):
        self._dismiss_blender_progress_dialog()
        self._update_blender_status_chip(f"Failed: {reason}", severity="error")
        self._close_blender_log_capture()
        self._show_internal_workspace()
        self._emit_blender_fallback_package(reason)

    def _emit_blender_fallback_package(self, failure_reason: str):
        if self._module is None:
            return
        try:
            lyt_module = self._module.layout()
            git_module = self._module.git()
            if not lyt_module or not git_module:
                self.log.warning("Cannot export fallback session: missing LYT or GIT resource")
                return
            lyt_resource = lyt_module.resource()
            git_resource = git_module.resource()
            if lyt_resource is None or git_resource is None:
                self.log.warning("Cannot export fallback session: resources not loaded")
                return
            payload = serialize_module_data(
                lyt_resource,
                git_resource,
                self._last_walkmeshes,
                self._module.root(),
                str(self._installation.path()),
            )
            fallback_dir = Path(tempfile.gettempdir()) / "HolocronToolset" / "sessions"
            fallback_dir.mkdir(parents=True, exist_ok=True)
            fallback_path = fallback_dir / f"{self._module.root()}_{int(time.time())}.json"
            fallback_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            self._fallback_session_path = fallback_path
            QMessageBox.information(
                self,
                "Blender IPC failed",
                (
                    f"Blender could not be reached ({failure_reason}).\n\n"
                    f"A fallback session was exported to:\n{fallback_path}\n\n"
                    "Open Blender manually and choose File ▸ Import ▸ Holocron Toolset Session (.json) "
                    "to continue inside Blender."
                ),
            )
        except Exception as exc:  # noqa: BLE001
            self.log.error("Failed to export fallback session: %s", exc)

    def _on_blender_module_loaded(self):
        super()._on_blender_module_loaded()
        self._invoke_on_ui_thread(self._dismiss_blender_progress_dialog)

    def _on_blender_mode_stopped(self):
        super()._on_blender_mode_stopped()
        self._invoke_on_ui_thread(self._close_blender_log_capture)
        self._invoke_on_ui_thread(self._show_internal_workspace)

    def _on_blender_selection_changed(self, instance_ids: list[int]):
        def _apply():
            prev = self._selection_sync_in_progress
            self._selection_sync_in_progress = True
            try:
                resolved = [
                    inst
                    for inst in (
                        self._instance_id_lookup.get(instance_id)
                        for instance_id in instance_ids
                    )
                    if inst is not None
                ]
                self.set_selection(cast(list[GITInstance], resolved))
            finally:
                self._selection_sync_in_progress = prev

        self._invoke_on_ui_thread(_apply)

    def _on_blender_transform_changed(
        self,
        instance_id: int,
        position: dict | None,
        rotation: dict | None,
    ):
        def _apply():
            # Set flag to prevent sync loop
            prev = self._transform_sync_in_progress
            self._transform_sync_in_progress = True
            try:
                instance = self._instance_id_lookup.get(instance_id)
                if instance is None:
                    return
                mutated = False

                if position:
                    current_position = Vector3(
                        instance.position.x,
                        instance.position.y,
                        instance.position.z,
                    )
                    new_position = Vector3(
                        position.get("x", current_position.x),
                        position.get("y", current_position.y),
                        position.get("z", current_position.z),
                    )
                    if not self._vector3_close(current_position, new_position):
                        self.undo_stack.push(MoveCommand(instance, current_position, new_position))
                        mutated = True

                if rotation and isinstance(instance, _BEARING_CLASSES) and "euler" in rotation:
                    new_bearing = rotation["euler"].get("z")
                    if new_bearing is not None and not math.isclose(instance.bearing, new_bearing, abs_tol=1e-4):
                        self.undo_stack.push(RotateCommand(instance, instance.bearing, float(new_bearing)))
                        mutated = True

                if rotation and isinstance(instance, GITCamera) and "quaternion" in rotation:
                    quat = rotation["quaternion"]
                    current_orientation = Vector4(
                        instance.orientation.x,
                        instance.orientation.y,
                        instance.orientation.z,
                        instance.orientation.w,
                    )
                    new_orientation = Vector4(
                        quat.get("x", current_orientation.x),
                        quat.get("y", current_orientation.y),
                        quat.get("z", current_orientation.z),
                        quat.get("w", current_orientation.w),
                    )
                    if not self._vector4_close(current_orientation, new_orientation):
                        self.undo_stack.push(RotateCommand(instance, current_orientation, new_orientation))
                        mutated = True

                if mutated:
                    self._after_instance_mutation(instance)
            finally:
                self._transform_sync_in_progress = prev

        self._invoke_on_ui_thread(_apply)

    def _on_blender_context_menu_requested(self, instance_ids: list[int]):
        def _apply():
            resolved = [
                inst
                for inst in (
                    self._instance_id_lookup.get(instance_id)
                    for instance_id in instance_ids
                )
                if inst is not None
            ]
            if not resolved:
                return
            prev = self._selection_sync_in_progress
            self._selection_sync_in_progress = True
            try:
                self.set_selection(cast(list[GITInstance], resolved))
            finally:
                self._selection_sync_in_progress = prev
            menu = self.on_context_menu_selection_exists(instances=resolved, get_menu=True)
            if menu is not None:
                self.show_final_context_menu(menu)

        self._invoke_on_ui_thread(_apply)

    def _on_blender_instance_changed(self, action: str, payload: dict):
        def _apply():
            if action == "added":
                self._handle_blender_instance_added(payload)
            elif action == "removed":
                self._handle_blender_instance_removed(payload)

        self._invoke_on_ui_thread(_apply)

    def _on_blender_instance_updated(self, instance_id: int, properties: dict):
        def _apply():
            instance = self._instance_id_lookup.get(instance_id)
            if instance is None:
                return
            self._apply_blender_property_updates(instance, properties)

        self._invoke_on_ui_thread(_apply)

    def _on_blender_material_changed(self, payload: dict):
        """Handle material/texture changes from Blender."""
        def _apply():
            object_name = payload.get("object_name", "")
            material_data = payload.get("material", {})
            model_name = payload.get("model_name")
            
            if not model_name:
                return
            
            self.log.info(f"Material changed for {object_name} (model: {model_name})")
            
            # If textures were changed, we need to export the MDL and reload it
            if "diffuse_texture" in material_data or "lightmap_texture" in material_data:
                # Request MDL export from Blender
                if self.is_blender_mode() and self._blender_controller is not None:
                    # Export MDL to a temp location
                    import tempfile
                    temp_mdl = tempfile.NamedTemporaryFile(suffix=".mdl", delete=False)
                    temp_mdl.close()
                    
                    # Use IPC to export MDL
                    from toolset.blender.ipc_client import get_ipc_client
                    client = get_ipc_client()
                    if client and client.is_connected:
                        result = client.send_command("export_mdl", {
                            "path": temp_mdl.name,
                            "object": object_name,
                        })
                        if result.success:
                            self.log.info(f"Exported updated MDL to {temp_mdl.name}")
                            # TODO: Reload the MDL in the toolset and update the module
                            # This would require finding the MDL resource in the module
                            # and replacing it with the exported version

        self._invoke_on_ui_thread(_apply)

    def update_status_bar(
        self,
        mouse_pos: QPoint | Vector2,
        buttons: set[Qt.MouseButton],
        keys: set[Qt.Key],
        renderer: WalkmeshRenderer | ModuleRenderer,
    ):
        """Update the status bar, using rich text formatting for improved clarity."""

        if isinstance(mouse_pos, QPoint):
            assert not isinstance(mouse_pos, Vector2)
            norm_mouse_pos = Vector2(float(mouse_pos.x()), float(mouse_pos.y()))
        else:
            norm_mouse_pos = mouse_pos

        # Mouse and camera info
        if isinstance(renderer, ModuleRenderer):
            pos = renderer.scene.cursor.position()
            world_pos_3d = Vector3(pos.x, pos.y, pos.z)
            world_pos = world_pos_3d
            self.mouse_pos_label.setText(
                f"<b><span style='{self._emoji_style}'>🖱</span>&nbsp;Coords:</b> "
                f"<span style='color:#0055B0'>{world_pos_3d.y:.2f}</span>, "
                f"<span style='color:#228800'>{world_pos_3d.z:.2f}</span>"
            )

            camera = renderer.scene.camera
            cam_text = (
                f"<b><span style='{self._emoji_style}'>🎥</span>&nbsp;View:</b> "
                f"<span style='color:#c46811'>Pos ("
                f"{camera.x:.2f}, {camera.y:.2f}, {camera.z:.2f}</span>), "
                f"Pitch: <span style='color:#a13ac8'>{camera.pitch:.2f}</span>, "
                f"Yaw: <span style='color:#a13ac8'>{camera.yaw:.2f}</span>, "
                f"FOV: <span style='color:#0b7d96'>{camera.fov:.2f}</span>"
            )
            self.view_camera_label.setText(cam_text)
        else:
            if isinstance(norm_mouse_pos, Vector2):
                norm_mouse_pos = Vector2(float(norm_mouse_pos.x), float(norm_mouse_pos.y))
            else:
                norm_mouse_pos = Vector2(float(norm_mouse_pos.x()), float(norm_mouse_pos.y()))
            world_pos = renderer.to_world_coords(norm_mouse_pos.x, norm_mouse_pos.y)
            self.mouse_pos_label.setText(f"<b><span style='{self._emoji_style}'>🖱</span>&nbsp;Coords:</b> <span style='color:#0055B0'>{world_pos.y:.2f}</span>")
            self.view_camera_label.setText(
                f"<b><span style='{self._emoji_style}'>🎥</span>&nbsp;View:</b> <span style='font-style:italic; color:#888'>— not available —</span>"
            )

        # Sort keys and buttons with modifiers at the beginning
        def sort_with_modifiers(
            items: set[Qt.Key] | set[Qt.MouseButton],
            get_string_func: Callable[[Any], str],
            qt_enum_type: Literal["QtKey", "QtMouse"],
        ) -> Sequence[Qt.Key | Qt.MouseButton]:
            modifiers = []
            if qt_enum_type == "QtKey":
                modifiers = [item for item in items if item in MODIFIER_KEY_NAMES]
                normal = [item for item in items if item not in MODIFIER_KEY_NAMES]
            else:
                normal = list(items)
            return sorted(modifiers, key=get_string_func) + sorted(normal, key=get_string_func)

        sorted_buttons = sort_with_modifiers(buttons, get_qt_button_string, "QtMouse")
        sorted_keys = sort_with_modifiers(keys, get_qt_key_string, "QtKey")

        # Keys/Buttons format: use color and separation for modifiers vs interaction
        def fmt_keys_str(keys_seq):
            return (
                "<span style='color:#a13ac8'>" + "</span>&nbsp;+&nbsp;<span style='color:#a13ac8'>".join([get_qt_key_string(key) for key in keys_seq]) + "</span>"
                if keys_seq
                else ""
            )

        def fmt_buttons_str(btn_seq):
            return (
                "<span style='color:#228800'>" + "</span>&nbsp;+&nbsp;<span style='color:#228800'>".join([get_qt_button_string(button) for button in btn_seq]) + "</span>"
                if btn_seq
                else ""
            )

        keys_str = fmt_keys_str(sorted_keys)
        buttons_str = fmt_buttons_str(sorted_buttons)
        sep = " + " if keys_str and buttons_str else ""
        self.buttons_keys_pressed_label.setText(
            f"<b><span style='{self._emoji_style}'>⌨</span>&nbsp;Keys/<span style='{self._emoji_style}'>🖱</span>&nbsp;Buttons:</b> {keys_str}{sep}{buttons_str}"
        )

        # Selected instance with better style
        if self.selected_instances:
            instance = self.selected_instances[0]
            if isinstance(instance, GITCamera):
                instance_name = f"<span style='color:#B05500'>[Camera]</span> <code>{repr(instance)}</code>"
            else:
                instance_name = f"<span style='color:#0055B0'>{instance.identifier()}</span>"
            self.selected_instance_label.setText(f"<b><span style='{self._emoji_style}'>🟦</span>&nbsp;Selected Instance:</b> {instance_name}")
        else:
            self.selected_instance_label.setText(f"<b><span style='{self._emoji_style}'>🟦</span>&nbsp;Selected Instance:</b> <span style='color:#a6a6a6'><i>None</i></span>")

    def _refresh_window_title(self):
        if self._module is None:
            title = f"No Module - {self._installation.name} - Module Designer"
        else:
            title = f"{self._module.root()} - {self._installation.name} - Module Designer"
        self.setWindowTitle(title)

    def on_lyt_updated(self, lyt: LYT):
        """Handle LYT updates from the editor."""
        if self._module is not None:
            layout = self._module.layout()
            if layout is not None:
                layout.save()
            self.rebuild_resource_tree()

    def open_module_with_dialog(self):
        dialog = SelectModuleDialog(self, self._installation)

        if dialog.exec():
            mod_filepath = self._installation.module_path().joinpath(dialog.module)

            # Check for Blender and ask user preference
            self._blender_choice_made = True  # Mark that we've checked
            use_blender, blender_info = check_blender_and_ask(self, "Module Designer")
            if blender_info is not None:
                self._use_blender_mode = use_blender

            self.open_module(mod_filepath)

    #    @with_variable_trace(Exception)
    def open_module(
        self,
        mod_filepath: Path,
    ):
        """Opens a module."""
        # Check for Blender if not already checked (when opening directly via constructor or file)
        if not self._blender_choice_made:
            self._blender_choice_made = True
            blender_settings = get_blender_settings()

            # Check if user has a remembered preference
            if blender_settings.remember_choice:
                # Use remembered preference
                self._use_blender_mode = blender_settings.prefer_blender
            else:
                # Show dialog to ask user (if Blender is detected)
                blender_info = blender_settings.get_blender_info()
                if blender_info.is_valid:
                    use_blender, blender_info_result = check_blender_and_ask(self, "Module Designer")
                    if blender_info_result is not None:
                        self._use_blender_mode = use_blender
                    # If user cancelled, default to built-in
                    elif use_blender is False and blender_info_result is None:
                        self._use_blender_mode = False
                else:
                    # Blender not available, use built-in
                    self._use_blender_mode = False

        mod_root: str = self._installation.get_module_root(mod_filepath)
        mod_filepath = self._ensure_mod_file(mod_filepath, mod_root)

        self.unload_module()
        combined_module = Module(mod_root, self._installation, use_dot_mod=is_mod_file(mod_filepath))
        git_module = combined_module.git()
        if git_module is None:
            raise ValueError(f"This module '{mod_root}' is missing a GIT!")
        git: GIT | None = git_module.resource()
        if git is None:
            raise ValueError(f"This module '{mod_root}' is missing a GIT!")

        walkmeshes: list[BWM] = []
        for mod_resource in combined_module.resources.values():
            res_obj = mod_resource.resource()
            if res_obj is not None and mod_resource.restype() == ResourceType.WOK:
                walkmeshes.append(res_obj)
        self._last_walkmeshes = walkmeshes
        result: tuple[Module, GIT, list[BWM]] = (combined_module, git, walkmeshes)
        new_module, git, walkmeshes = result
        self._module = new_module

        # Get LYT for Blender mode
        lyt: LYT | None = None
        lyt_module = combined_module.layout()
        if lyt_module is not None:
            lyt = lyt_module.resource()
        if lyt is None:
            lyt = LYT()

        # Start Blender mode if requested
        if self._use_blender_mode:
            self._prepare_for_blender_session(mod_root)
            blender_started = self.start_blender_mode(
                lyt=lyt,
                git=git,
                walkmeshes=walkmeshes,
                module_root=mod_root,
                installation_path=self._installation.path(),
            )
            if blender_started:
                self.setWindowTitle(f"Module Designer - {mod_root} (Blender Mode)")
            else:
                # Fall back to built-in if Blender fails
                self._use_blender_mode = False
                self.log.warning("Blender mode failed, using built-in renderer")

        if not self._use_blender_mode:
            self.ui.flatRenderer.set_git(git)
            self.ui.mainRenderer.initialize_renderer(self._installation, new_module)
            self.ui.mainRenderer.scene.show_cursor = self.ui.cursorCheck.isChecked()
            self.ui.flatRenderer.set_walkmeshes(walkmeshes)
            self.ui.flatRenderer.center_camera()
            self.setWindowTitle(f"Module Designer - {mod_root}")
        else:
            self._show_blender_workspace()

        self.show()
        # Inherently calls On3dSceneInitialized when done.

    def _ensure_mod_file(self, mod_filepath: Path, mod_root: str) -> Path:
        mod_file = mod_filepath.with_name(f"{mod_root}.mod")
        if not mod_file.is_file():
            if self._confirm_create_mod(mod_root):
                self._create_mod(mod_file, mod_root)
                return mod_file
            return mod_filepath

        if mod_file != mod_filepath and not self._confirm_use_mod(mod_filepath, mod_file):
            return mod_filepath
        return mod_file

    def _confirm_create_mod(self, mod_root: str) -> bool:
        return (
            QMessageBox.question(
                self,
                "Editing .RIM/.ERF modules is discouraged.",
                f"The Module Designer would like to create a .mod for module '{mod_root}', would you like to do this now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            == QMessageBox.StandardButton.Yes
        )

    def _create_mod(self, mod_file: Path, mod_root: str):
        self.log.info("Creating '%s.mod' from the rims/erfs...", mod_root)
        module.rim_to_mod(mod_file, game=self._installation.game())
        self._installation.reload_module(mod_file.name)

    def _confirm_use_mod(self, orig_filepath: Path, mod_filepath: Path) -> bool:
        return (
            QMessageBox.question(
                self,
                f"{orig_filepath.suffix} file chosen when {mod_filepath.suffix} preferred.",
                (
                    f"You've chosen '{orig_filepath.name}' with a '{orig_filepath.suffix}' extension.<br><br>"
                    f"The Module Designer recommends modifying .mod's.<br><br>"
                    f"Use '{mod_filepath.name}' instead?"
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            == QMessageBox.StandardButton.Yes
        )

    def unload_module(self):
        self._module = None
        self.ui.mainRenderer.shutdown_renderer()

    def show_help_window(self):
        window = HelpWindow(self, "./help/tools/1-moduleEditor.md")
        window.show()

    def git(self) -> GIT:
        assert self._module is not None
        git = self._module.git()
        assert git is not None
        git_resource = git.resource()
        assert git_resource is not None
        return git_resource

    def are(self) -> ARE:
        assert self._module is not None
        are = self._module.are()
        assert are is not None
        are_resource = are.resource()
        assert are_resource is not None
        return are_resource

    def ifo(self) -> IFO:
        assert self._module is not None
        ifo = self._module.info()
        assert ifo is not None
        ifo_resource = ifo.resource()
        assert ifo_resource is not None
        return ifo_resource

    def save_git(self):
        assert self._module is not None
        git_module = self._module.git()
        assert git_module is not None
        git_module.save()

        # Also save the layout if it has been modified
        layout_module = self._module.layout()
        if layout_module is not None:
            layout_module.save()

    def rebuild_resource_tree(self):
        """Rebuilds the resource tree widget.

        Rebuilds the resource tree widget by:
            - Clearing existing items
            - Enabling the tree
            - Grouping resources by type into categories
            - Adding category items and resource items
            - Sorting items alphabetically.
        """
        # Only build if module is loaded
        if self._module is None:
            self.ui.resourceTree.setEnabled(False)
            return

        # Block signals and sorting during bulk update for better performance
        self.ui.resourceTree.blockSignals(True)
        self.ui.resourceTree.setSortingEnabled(False)
        self.ui.resourceTree.clear()
        self.ui.resourceTree.setEnabled(True)

        categories: dict[ResourceType, QTreeWidgetItem] = {
            ResourceType.UTC: QTreeWidgetItem(["Creatures"]),
            ResourceType.UTP: QTreeWidgetItem(["Placeables"]),
            ResourceType.UTD: QTreeWidgetItem(["Doors"]),
            ResourceType.UTI: QTreeWidgetItem(["Items"]),
            ResourceType.UTE: QTreeWidgetItem(["Encounters"]),
            ResourceType.UTT: QTreeWidgetItem(["Triggers"]),
            ResourceType.UTW: QTreeWidgetItem(["Waypoints"]),
            ResourceType.UTS: QTreeWidgetItem(["Sounds"]),
            ResourceType.UTM: QTreeWidgetItem(["Merchants"]),
            ResourceType.DLG: QTreeWidgetItem(["Dialogs"]),
            ResourceType.FAC: QTreeWidgetItem(["Factions"]),
            ResourceType.MDL: QTreeWidgetItem(["Models"]),
            ResourceType.TGA: QTreeWidgetItem(["Textures"]),
            ResourceType.NCS: QTreeWidgetItem(["Scripts"]),
            ResourceType.IFO: QTreeWidgetItem(["Module Data"]),
            ResourceType.INVALID: QTreeWidgetItem(["Other"]),
        }
        categories[ResourceType.MDX] = categories[ResourceType.MDL]
        categories[ResourceType.WOK] = categories[ResourceType.MDL]
        categories[ResourceType.TPC] = categories[ResourceType.TGA]
        categories[ResourceType.IFO] = categories[ResourceType.IFO]
        categories[ResourceType.ARE] = categories[ResourceType.IFO]
        categories[ResourceType.GIT] = categories[ResourceType.IFO]
        categories[ResourceType.LYT] = categories[ResourceType.IFO]
        categories[ResourceType.VIS] = categories[ResourceType.IFO]
        categories[ResourceType.PTH] = categories[ResourceType.IFO]
        categories[ResourceType.NSS] = categories[ResourceType.NCS]

        for value in categories.values():
            self.ui.resourceTree.addTopLevelItem(value)

        for resource in self._module.resources.values():
            item = QTreeWidgetItem([f"{resource.resname()}.{resource.restype().extension}"])
            item.setData(0, Qt.ItemDataRole.UserRole, resource)
            category: QTreeWidgetItem = categories.get(resource.restype(), categories[ResourceType.INVALID])
            category.addChild(item)

        self.ui.resourceTree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.ui.resourceTree.setSortingEnabled(True)

        # Restore signals after bulk update
        self.ui.resourceTree.blockSignals(False)

    def open_module_resource(self, resource: ModuleResource):
        active_path = resource.active()
        if active_path is None:
            QMessageBox(
                QMessageBox.Icon.Critical,
                "Failed to open editor",
                f"Resource {resource.identifier()} has no active file path.",
            ).exec()
            return
        editor: Editor | QMainWindow | None = open_resource_editor(
            active_path,
            installation=self._installation,
            parent_window=self,
            resname=resource.resname(),
            restype=resource.restype(),
            data=resource.data(),
        )[1]

        if editor is None:
            QMessageBox(
                QMessageBox.Icon.Critical,
                "Failed to open editor",
                f"Failed to open editor for file: {resource.identifier()}",
            ).exec()
        elif isinstance(editor, Editor):
            editor.sig_saved_file.connect(lambda: self._on_saved_resource(resource))

    def copy_resource_to_override(self, resource: ModuleResource):
        location = self._installation.override_path() / f"{resource.identifier()}"
        data = resource.data()
        if data is None:
            RobustLogger().error(f"Cannot find resource {resource.identifier()} anywhere to copy to Override. Locations: {resource.locations()}")
            return
        location.write_bytes(data)
        resource.add_locations([location])
        resource.activate(location)
        scene = self.ui.mainRenderer.scene
        if scene is not None:
            scene.clear_cache_buffer.append(resource.identifier())

    def activate_resource_file(
        self,
        resource: ModuleResource,
        location: os.PathLike | str,
    ):
        resource.activate(location)
        scene = self.ui.mainRenderer.scene
        if scene is not None:
            scene.clear_cache_buffer.append(resource.identifier())

    def select_resource_item(
        self,
        instance: GITInstance,
        *,
        clear_existing: bool = True,
    ):
        if clear_existing:
            self.ui.resourceTree.clearSelection()
        this_ident = instance.identifier()
        if this_ident is None:  # Should only ever be None for GITCamera.
            assert isinstance(instance, GITCamera), f"Should only ever be None for GITCamera, not {type(instance).__name__}."
            return

        for i in range(self.ui.resourceTree.topLevelItemCount()):
            parent: QTreeWidgetItem | None = self.ui.resourceTree.topLevelItem(i)
            if parent is None:
                self.log.warning("parent was None in ModuleDesigner.selectResourceItem()")
                continue
            for j in range(parent.childCount()):
                item = parent.child(j)
                if item is None:
                    self.log.warning(f"parent.child({j}) was somehow None in selectResourceItem")
                    continue
                res: ModuleResource = item.data(0, Qt.ItemDataRole.UserRole)
                if not isinstance(res, ModuleResource):
                    self.log.warning("item.data(0, Qt.ItemDataRole.UserRole) returned non ModuleResource in ModuleDesigner.selectResourceItem(): %s", safe_repr(res))
                    continue
                if res.identifier() != this_ident:
                    continue
                self.log.debug("Selecting ModuleResource in selectResourceItem loop: %s", res.identifier())
                parent.setExpanded(True)
                item.setSelected(True)
                self.ui.resourceTree.scrollToItem(item)

    def rebuild_instance_list(self):
        self.log.debug("rebuildInstanceList called.")

        # Only build if module is loaded
        if self._module is None:
            self.ui.instanceList.setEnabled(False)
            self.ui.instanceList.setVisible(False)
            return

        # Block signals during bulk update for better performance
        self.ui.instanceList.blockSignals(True)
        self.ui.instanceList.clear()
        self.ui.instanceList.setEnabled(True)
        self.ui.instanceList.setVisible(True)

        visible_mapping = {
            GITCreature: self.hide_creatures,
            GITPlaceable: self.hide_placeables,
            GITDoor: self.hide_doors,
            GITTrigger: self.hide_triggers,
            GITEncounter: self.hide_encounters,
            GITWaypoint: self.hide_waypoints,
            GITSound: self.hide_sounds,
            GITStore: self.hide_stores,
            GITCamera: self.hide_cameras,
            GITInstance: False,
        }
        icon_mapping = {
            GITCreature: QPixmap(":/images/icons/k1/creature.png"),
            GITPlaceable: QPixmap(":/images/icons/k1/placeable.png"),
            GITDoor: QPixmap(":/images/icons/k1/door.png"),
            GITSound: QPixmap(":/images/icons/k1/sound.png"),
            GITTrigger: QPixmap(":/images/icons/k1/trigger.png"),
            GITEncounter: QPixmap(":/images/icons/k1/encounter.png"),
            GITWaypoint: QPixmap(":/images/icons/k1/waypoint.png"),
            GITCamera: QPixmap(":/images/icons/k1/camera.png"),
            GITStore: QPixmap(":/images/icons/k1/merchant.png"),
            GITInstance: QPixmap(32, 32),
        }

        self.ui.instanceList.clear()
        items: list[QListWidgetItem] = []

        if self._module is None:
            return
        git_module = self._module.git()
        if git_module is None:
            return
        git_resource = git_module.resource()
        if git_resource is None:
            return
        git: GIT = git_resource

        for instance in git.instances():
            if visible_mapping[instance.__class__]:
                continue

            struct_index: int = git.index(instance)

            icon = QIcon(icon_mapping[instance.__class__])
            item = QListWidgetItem(icon, "")
            font: QFont = item.font()

            if isinstance(instance, GITCamera):
                item.setText(f"Camera #{instance.camera_id}")
                item.setToolTip(f"Struct Index: {struct_index}\nCamera ID: {instance.camera_id}\nFOV: {instance.fov}")
                item.setData(Qt.ItemDataRole.UserRole + 1, "cam" + str(instance.camera_id).rjust(10, "0"))
            else:
                this_ident = instance.identifier()
                assert this_ident is not None
                resname: str = this_ident.resname
                name: str = resname
                tag: str = ""
                module_resource: ModuleResource[ARE] | None = self._module.resource(this_ident.resname, this_ident.restype)
                if module_resource is None:
                    continue
                abstracted_resource = module_resource.resource()
                if abstracted_resource is None:
                    continue

                if isinstance(instance, GITDoor) or (isinstance(instance, GITTrigger) and module_resource):
                    # Tag is stored in the GIT
                    name = module_resource.localized_name() or resname
                    tag = instance.tag
                elif isinstance(instance, GITWaypoint):
                    # Name and tag are stored in the GIT
                    name = self._installation.string(instance.name)
                    tag = instance.tag
                elif module_resource:
                    name = module_resource.localized_name() or resname
                    tag = abstracted_resource.tag

                if module_resource is None:
                    font.setItalic(True)

                item.setText(name)
                item.setToolTip(f"Struct Index: {struct_index}\nResRef: {resname}\nName: {name}\nTag: {tag}")
                ident = instance.identifier()
                assert ident is not None
                item.setData(Qt.ItemDataRole.UserRole + 1, ident.restype.extension + name)

            item.setFont(font)
            item.setData(Qt.ItemDataRole.UserRole, instance)
            items.append(item)

        for item in sorted(items, key=lambda i: i.data(Qt.ItemDataRole.UserRole + 1)):
            self.ui.instanceList.addItem(item)

        # Restore signals after bulk update
        self.ui.instanceList.blockSignals(False)
        self._refresh_instance_id_lookup()

    def _refresh_instance_id_lookup(self):
        """Cache Python object ids for fast lookup when Blender sends events."""
        self._instance_id_lookup.clear()
        if self._module is None:
            return
        git_module = self._module.git()
        if git_module is None:
            return
        git_resource = git_module.resource()
        if git_resource is None:
            return
        if hasattr(git_resource, "instances"):
            for instance in git_resource.instances():
                self._instance_id_lookup[id(instance)] = instance

    @staticmethod
    def _vector3_close(a: Vector3, b: Vector3, epsilon: float = 1e-4) -> bool:
        return abs(a.x - b.x) <= epsilon and abs(a.y - b.y) <= epsilon and abs(a.z - b.z) <= epsilon

    @staticmethod
    def _vector4_close(a: Vector4, b: Vector4, epsilon: float = 1e-4) -> bool:
        return abs(a.x - b.x) <= epsilon and abs(a.y - b.y) <= epsilon and abs(a.z - b.z) <= epsilon and abs(a.w - b.w) <= epsilon

    def _after_instance_mutation(
        self,
        instance: GITInstance | None,
        *,
        refresh_lists: bool = False,
    ):
        scene = self.ui.mainRenderer.scene
        if scene is not None:
            scene.invalidate_cache()
        self.ui.mainRenderer.update()
        self.ui.flatRenderer.update()

        # Sync instance to Blender if not already syncing from Blender
        if (
            instance is not None
            and self.is_blender_mode()
            and self._blender_controller is not None
            and not self._transform_sync_in_progress
            and not self._property_sync_in_progress
        ):
            self.sync_instance_to_blender(instance)

        if refresh_lists:
            selected = list(self.selected_instances)
            self.rebuild_instance_list()
            if selected:
                self.set_selection(selected)

    def _construct_instance_from_blender_payload(self, payload: dict[str, Any]) -> GITInstance | None:
        instance_block = payload.get("instance") or payload
        data = deserialize_git_instance(instance_block)
        type_name = data.get("type")
        position = data.get("position", (0.0, 0.0, 0.0))

        type_map: dict[str, type[GITInstance]] = {
            "GITCamera": GITCamera,
            "GITCreature": GITCreature,
            "GITDoor": GITDoor,
            "GITEncounter": GITEncounter,
            "GITPlaceable": GITPlaceable,
            "GITSound": GITSound,
            "GITStore": GITStore,
            "GITTrigger": GITTrigger,
            "GITWaypoint": GITWaypoint,
        }

        cls = type_map.get(type_name or "")
        if cls is None:
            self.log.warning("Blender requested unsupported instance type: %s", type_name)
            return None

        instance = cls(position[0], position[1], position[2])
        self._apply_deserialized_instance_data(instance, data)
        return instance

    def _apply_deserialized_instance_data(self, instance: GITInstance, data: dict[str, Any]):
        pos = data.get("position")
        if pos is not None:
            instance.position = Vector3(*pos)

        if "resref" in data and isinstance(instance, _RESREF_CLASSES):
            cast(ResrefInstance, instance).resref = ResRef(str(data["resref"]))
        if "tag" in data and isinstance(instance, _TAG_CLASSES):
            cast(TagInstance, instance).tag = str(data["tag"])
        if "bearing" in data and isinstance(instance, _BEARING_CLASSES):
            typed_instance = cast(BearingInstance, instance)
            typed_instance.bearing = float(data["bearing"])

        if isinstance(instance, GITCamera) and "orientation" in data:
            instance.orientation = Vector4(*data["orientation"])

        if isinstance(instance, GITPlaceable) and "tweak_color" in data:
            tweak_color = data.get("tweak_color")
            instance.tweak_color = Color.from_bgr_integer(int(tweak_color)) if tweak_color is not None else None

        if isinstance(instance, GITTrigger) and "geometry" in data:
            polygon = Polygon3()
            for vertex in data.get("geometry", []):
                polygon.append(Vector3(*vertex))
            instance.geometry = polygon
            instance.tag = data.get("tag", instance.tag)

        if isinstance(instance, GITEncounter):
            polygon = Polygon3()
            for vertex in data.get("geometry", []):
                polygon.append(Vector3(*vertex))
            instance.geometry = polygon
            spawn_points: list[dict[str, Any]] = data.get("spawn_points", [])
            instance.spawn_points.clear()
            for sp_data in spawn_points:
                pos_data = sp_data.get("position", {})
                spawn = GITEncounterSpawnPoint(
                    pos_data.get("x", 0.0),
                    pos_data.get("y", 0.0),
                    pos_data.get("z", 0.0),
                )
                spawn.orientation = sp_data.get("orientation", 0.0)
                instance.spawn_points.append(spawn)

    def _handle_blender_instance_added(self, payload: dict[str, Any]):
        instance = self._construct_instance_from_blender_payload(payload)
        if instance is None:
            return
        git_resource = self.git()
        cmd = _BlenderInsertCommand(git_resource, instance, self)
        self.undo_stack.push(cmd)
        self.set_selection([instance])
        runtime_id = payload.get("runtime_id")
        if runtime_id is not None and self._blender_controller is not None:
            try:
                runtime_key = int(runtime_id)
            except (TypeError, ValueError):
                runtime_key = None
            if runtime_key is not None:
                self._blender_controller.bind_runtime_instance(
                    runtime_key,
                    instance,
                    payload.get("name"),
                )

    def _handle_blender_instance_removed(self, payload: dict[str, Any]):
        instance_id = payload.get("id")
        runtime_id = payload.get("runtime_id")
        instance: GITInstance | None = None
        if instance_id is not None:
            try:
                instance = self._instance_id_lookup.get(int(instance_id))
            except (TypeError, ValueError):
                instance = None
        if instance is None and runtime_id is not None:
            try:
                instance = self._instance_id_lookup.get(int(runtime_id))
            except (TypeError, ValueError):
                instance = None
        if instance is None:
            self.log.warning("Blender removed instance that is unknown to the toolset: %s", payload)
            return
        self.selected_instances = [inst for inst in self.selected_instances if inst is not instance]
        cmd = _BlenderDeleteCommand(self.git(), instance, self)
        self.undo_stack.push(cmd)

    def _queue_blender_property_update(
        self,
        instance: GITInstance,
        key: str,
        value: Any,
    ) -> bool:
        refresh_lists = False
        setter_func: Callable[[GITInstance, Any], None] | None = None
        old_value: Any | None = None
        new_value: Any = value

        def _on_change(refresh: bool) -> Callable[[GITInstance], None]:
            def _handler(inst: GITInstance) -> None:
                self._after_instance_mutation(inst, refresh_lists=refresh)

            return _handler

        if key == "resref" and isinstance(instance, _RESREF_CLASSES):
            typed_instance = cast(ResrefInstance, instance)
            old_value = str(typed_instance.resref)
            new_value = str(value or "")
            refresh_lists = True

            def resref_setter(inst: GITInstance, val: Any) -> None:
                cast(ResrefInstance, inst).resref = ResRef(str(val or ""))

            setter_func = resref_setter

        elif key == "tag" and isinstance(instance, _TAG_CLASSES):
            typed_instance = cast(TagInstance, instance)
            old_value = typed_instance.tag
            new_value = str(value or "")
            refresh_lists = True

            def tag_setter(inst: GITInstance, val: Any) -> None:
                cast(TagInstance, inst).tag = str(val or "")

            setter_func = tag_setter

        elif key == "tweak_color" and isinstance(instance, GITPlaceable):
            current = instance.tweak_color.bgr_integer() if instance.tweak_color else None
            try:
                new_value = int(value) if value is not None else None
            except (TypeError, ValueError):
                new_value = None
            old_value = current
            refresh_lists = False

            def color_setter(inst: GITInstance, val: Any) -> None:
                placeable = cast(GITPlaceable, inst)
                placeable.tweak_color = (
                    Color.from_bgr_integer(int(val)) if val is not None else None
                )

            setter_func = color_setter
        else:
            self.log.debug("Ignoring unsupported Blender property update '%s'", key)
            return False

        if old_value == new_value or setter_func is None:
            return False

        command = _BlenderPropertyCommand(
            instance,
            setter_func,
            old_value,
            new_value,
            _on_change(refresh_lists),
            f"Blender set {key}",
        )
        self.undo_stack.push(command)
        return True

    def _apply_blender_property_updates(self, instance: GITInstance, properties: dict[str, Any]):
        any_updates = False
        for key, value in properties.items():
            any_updates |= self._queue_blender_property_update(instance, key, value)

    def select_instance_item_on_list(self, instance: GITInstance):
        self.ui.instanceList.clearSelection()
        for i in range(self.ui.instanceList.count()):
            item: QListWidgetItem | None = self.ui.instanceList.item(i)
            if item is None:
                self.log.warning("item was somehow None at index %s in selectInstanceItemOnList", i)
                continue
            data: GITInstance = item.data(Qt.ItemDataRole.UserRole)
            if data is instance:
                item.setSelected(True)
                self.ui.instanceList.scrollToItem(item)

    def update_toggles(self):
        scene = self.ui.mainRenderer.scene
        if scene is None:
            return

        self.hide_creatures = scene.hide_creatures = self.ui.flatRenderer.hide_creatures = not self.ui.viewCreatureCheck.isChecked()
        self.hide_placeables = scene.hide_placeables = self.ui.flatRenderer.hide_placeables = not self.ui.viewPlaceableCheck.isChecked()
        self.hide_doors = scene.hide_doors = self.ui.flatRenderer.hide_doors = not self.ui.viewDoorCheck.isChecked()
        self.hide_triggers = scene.hide_triggers = self.ui.flatRenderer.hide_triggers = not self.ui.viewTriggerCheck.isChecked()
        self.hide_encounters = scene.hide_encounters = self.ui.flatRenderer.hide_encounters = not self.ui.viewEncounterCheck.isChecked()
        self.hide_waypoints = scene.hide_waypoints = self.ui.flatRenderer.hide_waypoints = not self.ui.viewWaypointCheck.isChecked()
        self.hide_sounds = scene.hide_sounds = self.ui.flatRenderer.hide_sounds = not self.ui.viewSoundCheck.isChecked()
        self.hide_stores = scene.hide_stores = self.ui.flatRenderer.hide_stores = not self.ui.viewStoreCheck.isChecked()
        self.hide_cameras = scene.hide_cameras = self.ui.flatRenderer.hide_cameras = not self.ui.viewCameraCheck.isChecked()

        scene.backface_culling = self.ui.backfaceCheck.isChecked()
        scene.use_lightmap = self.ui.lightmapCheck.isChecked()
        scene.show_cursor = self.ui.cursorCheck.isChecked()

        # Sync to Blender if active
        if self.is_blender_mode() and self._blender_controller is not None:
            visibility_map = {
                "creature": not self.hide_creatures,
                "placeable": not self.hide_placeables,
                "door": not self.hide_doors,
                "trigger": not self.hide_triggers,
                "encounter": not self.hide_encounters,
                "waypoint": not self.hide_waypoints,
                "sound": not self.hide_sounds,
                "store": not self.hide_stores,
                "camera": not self.hide_cameras,
            }
            for instance_type, visible in visibility_map.items():
                self._blender_controller.set_visibility(instance_type, visible)

            self._blender_controller.set_render_settings(
                backface_culling=scene.backface_culling,
                use_lightmap=scene.use_lightmap,
                show_cursor=scene.show_cursor,
            )

        self.rebuild_instance_list()

    #    @with_variable_trace(Exception)
    def add_instance(
        self,
        instance: GITInstance,
        *,
        walkmesh_snap: bool = True,
    ):
        """Adds a GIT instance to the editor.

        Args:
        ----
            instance: {The instance to add}
            walkmesh_snap (optional): {Whether to snap the instance to the walkmesh}.
        """
        scene = self.ui.mainRenderer.scene
        if walkmesh_snap and scene is not None:
            instance.position.z = self.ui.mainRenderer.walkmesh_point(
                instance.position.x,
                instance.position.y,
                scene.camera.z,
            ).z

        if not isinstance(instance, GITCamera):
            assert self._module is not None
            ident = instance.identifier()
            assert ident is not None
            dialog = InsertInstanceDialog(self, self._installation, self._module, ident.restype)

            if dialog.exec():
                self.rebuild_resource_tree()
                instance.resref = ResRef(dialog.resname)  # pyright: ignore[reportAttributeAccessIssue]
                assert self._module is not None
                git = self._module.git()
                assert git is not None
                git_resource = git.resource()
                assert git_resource is not None
                git_resource.add(instance)

                if isinstance(instance, GITWaypoint):
                    utw: UTW = read_utw(dialog.data)
                    instance.tag = utw.tag
                    instance.name = utw.name
                elif isinstance(instance, GITTrigger):
                    utt: UTT = read_utt(dialog.data)
                    instance.tag = utt.tag
                    if not instance.geometry:
                        RobustLogger().info("Creating default triangle trigger geometry for %s.%s...", instance.resref, "utt")
                        instance.geometry.create_triangle(origin=instance.position)
                elif isinstance(instance, GITEncounter):
                    if not instance.geometry:
                        RobustLogger().info("Creating default triangle trigger geometry for %s.%s...", instance.resref, "ute")
                        instance.geometry.create_triangle(origin=instance.position)
                elif isinstance(instance, GITDoor):
                    utd: module.UTD = read_utd(dialog.data)
                    instance.tag = utd.tag
        else:
            assert self._module is not None
            git_module = self._module.git()
            assert git_module is not None
            git_resource = git_module.resource()
            assert git_resource is not None
            git_resource.add(instance)
        if scene is not None:
            scene.invalidate_cache()
        self.rebuild_instance_list()

    #    @with_variable_trace()
    def add_instance_at_cursor(
        self,
        instance: GITInstance,
    ):
        scene = self.ui.mainRenderer.scene
        if scene is None:
            self.log.warning("Cannot add instance at cursor while Blender mode controls rendering.")
            return

        instance.position.x = scene.cursor.position().x
        instance.position.y = scene.cursor.position().y
        instance.position.z = scene.cursor.position().z

        if not isinstance(instance, GITCamera):
            assert self._module is not None
            ident = instance.identifier()
            assert ident is not None
            dialog = InsertInstanceDialog(self, self._installation, self._module, ident.restype)

            if dialog.exec():
                self.rebuild_resource_tree()
                instance.resref = ResRef(dialog.resname)  # pyright: ignore[reportAttributeAccessIssue]
                assert self._module is not None
                git = self._module.git()
                assert git is not None
                git_resource = git.resource()
                assert git_resource is not None
                git_resource.add(instance)
        else:
            assert self._module is not None
            if isinstance(instance, (GITEncounter, GITTrigger)) and not instance.geometry:
                self.log.info("Creating default triangle geometry for %s.%s", instance.resref, "utt" if isinstance(instance, GITTrigger) else "ute")
                instance.geometry.create_triangle(origin=instance.position)
            git_module = self._module.git()
            assert git_module is not None
            git_resource = git_module.resource()
            assert git_resource is not None
            git_resource.add(instance)
        self.rebuild_instance_list()

    #    @with_variable_trace()
    def edit_instance(
        self,
        instance: GITInstance | None = None,
    ):
        if instance is None:
            if not self.selected_instances:
                return
            instance = self.selected_instances[0]
        if open_instance_dialog(self, instance, self._installation):
            if not isinstance(instance, GITCamera):
                ident = instance.identifier()
                if ident is not None:
                    scene = self.ui.mainRenderer.scene
                    if scene is not None:
                        scene.clear_cache_buffer.append(ident)

            # Sync property changes to Blender
            if self.is_blender_mode() and self._blender_controller is not None:
                self.sync_instance_to_blender(instance)

            self.rebuild_instance_list()

    def snap_camera_to_view(
        self,
        git_camera_instance: GITCamera,
    ):
        try:
            view_camera: Camera = self._get_scene_camera()
        except RuntimeError:
            return
        true_pos = view_camera.true_position()
        # Convert vec3 to Vector3
        git_camera_instance.position = Vector3(float(true_pos.x), float(true_pos.y), float(true_pos.z))

        self.undo_stack.push(MoveCommand(git_camera_instance, git_camera_instance.position, git_camera_instance.position))

        self.log.debug("Create RotateCommand for undo/redo functionality")
        pitch = math.pi - (view_camera.pitch + (math.pi / 2))
        yaw = math.pi / 2 - view_camera.yaw
        new_orientation = Vector4.from_euler(yaw, 0, pitch)
        self.undo_stack.push(RotateCommand(git_camera_instance, git_camera_instance.orientation, new_orientation))
        git_camera_instance.orientation = new_orientation

        # Sync to Blender
        if self.is_blender_mode() and self._blender_controller is not None:
            self._blender_controller.update_instance_position(
                git_camera_instance,
                git_camera_instance.position.x,
                git_camera_instance.position.y,
                git_camera_instance.position.z,
            )
            self._blender_controller.update_instance_rotation(
                git_camera_instance,
                orientation=(new_orientation.x, new_orientation.y, new_orientation.z, new_orientation.w),
            )

    def snap_view_to_git_camera(
        self,
        git_camera_instance: GITCamera,
    ):
        try:
            view_camera: Camera = self._get_scene_camera()
        except RuntimeError:
            return
        euler: Vector3 = git_camera_instance.orientation.to_euler()
        view_camera.pitch = math.pi - euler.z - math.radians(git_camera_instance.pitch)
        view_camera.yaw = math.pi / 2 - euler.x
        view_camera.x = git_camera_instance.position.x
        view_camera.y = git_camera_instance.position.y
        view_camera.z = git_camera_instance.position.z + git_camera_instance.height
        view_camera.distance = 0

        # Sync viewport to Blender
        if self.is_blender_mode() and self._blender_controller is not None:
            self._blender_controller.set_camera_view(
                view_camera.x,
                view_camera.y,
                view_camera.z,
                yaw=view_camera.yaw,
                pitch=view_camera.pitch,
                distance=view_camera.distance,
            )

    def snap_view_to_git_instance(
        self,
        git_instance: GITInstance,
    ):
        try:
            camera: Camera = self._get_scene_camera()
        except RuntimeError:
            return
        yaw: float | None = git_instance.yaw()
        camera.yaw = camera.yaw if yaw is None else yaw
        camera.x, camera.y, camera.z = git_instance.position
        camera.y = git_instance.position.y
        camera.z = git_instance.position.z + 2
        camera.distance = 0

        # Sync viewport to Blender
        if self.is_blender_mode() and self._blender_controller is not None:
            self._blender_controller.set_camera_view(
                camera.x,
                camera.y,
                camera.z,
                yaw=camera.yaw,
                pitch=camera.pitch,
                distance=camera.distance,
            )

    def _get_scene_camera(self) -> Camera:
        scene = self.ui.mainRenderer.scene
        if scene is None:
            raise RuntimeError("Internal renderer is unavailable while Blender controls the viewport.")
        result: Camera = scene.camera
        return result

    def snap_camera_to_entry_location(self):
        scene = self.ui.mainRenderer.scene
        if scene is None:
            if self.is_blender_mode() and self._blender_controller is not None:
                entry_pos = self.ifo().entry_position
                self._blender_controller.set_camera_view(
                    entry_pos.x,
                    entry_pos.y,
                    entry_pos.z,
                )
            return

        scene.camera.x = self.ifo().entry_position.x
        scene.camera.y = self.ifo().entry_position.y
        scene.camera.z = self.ifo().entry_position.z

        # Sync to Blender
        if self.is_blender_mode() and self._blender_controller is not None:
            self._blender_controller.set_camera_view(
                scene.camera.x,
                scene.camera.y,
                scene.camera.z,
                yaw=scene.camera.yaw,
                pitch=scene.camera.pitch,
                distance=scene.camera.distance,
            )

    def toggle_free_cam(self):
        if isinstance(self._controls3d, ModuleDesignerControls3d):
            self.log.info("Enabling ModuleDesigner free cam")
            self._controls3d = ModuleDesignerControlsFreeCam(self, self.ui.mainRenderer)
        else:
            self.log.info("Disabling ModuleDesigner free cam")
            self._controls3d = ModuleDesignerControls3d(self, self.ui.mainRenderer)

    # region Selection Manipulations
    def set_selection(self, instances: list[GITInstance]):
        was_syncing = self._selection_sync_in_progress
        self._selection_sync_in_progress = True
        scene = self.ui.mainRenderer.scene
        try:
            if instances:
                if scene is not None:
                    scene.select(instances[0])
                self.ui.flatRenderer.instance_selection.select(instances)
                self.select_instance_item_on_list(instances[0])
                self.select_resource_item(instances[0])
                self.selected_instances = instances
            else:
                if scene is not None:
                    scene.selection.clear()
                self.ui.flatRenderer.instance_selection.clear()
                self.selected_instances.clear()
        finally:
            self._selection_sync_in_progress = was_syncing

        if self.is_blender_mode() and not was_syncing:
            self.sync_selection_to_blender(instances)

    def delete_selected(
        self,
        *,
        no_undo_stack: bool = False,
    ):
        assert self._module is not None
        instances_to_delete = self.selected_instances.copy()
        if not no_undo_stack:
            self.undo_stack.push(DeleteCommand(self.git(), instances_to_delete, self))  # noqa: SLF001
        git_module = self._module.git()
        assert git_module is not None
        git_resource = git_module.resource()
        if git_resource is not None:
            for instance in instances_to_delete:
                git_resource.remove(instance)
                # Sync deletion to Blender
                if self.is_blender_mode() and self._blender_controller is not None:
                    self._blender_controller.remove_instance(instance)
        self.selected_instances.clear()
        scene = self.ui.mainRenderer.scene
        if scene is not None:
            scene.selection.clear()
            scene.invalidate_cache()
        self.ui.flatRenderer.instance_selection.clear()
        self.rebuild_instance_list()

    def move_selected(  # noqa: PLR0913
        self,
        x: float,
        y: float,
        z: float | None = None,
        *,
        no_undo_stack: bool = False,
        no_z_coord: bool = False,
    ):
        if self.ui.lockInstancesCheck.isChecked():
            return

        walkmesh_renderer: ModuleRenderer | None = self.ui.mainRenderer if self.ui.mainRenderer.scene is not None else None
        for instance in self.selected_instances:
            self.log.debug("Moving %s", instance.resref)
            new_x = instance.position.x + x
            new_y = instance.position.y + y
            if no_z_coord:
                new_z = instance.position.z
            else:
                if walkmesh_renderer is not None:
                    new_z = instance.position.z + (z or walkmesh_renderer.walkmesh_point(instance.position.x, instance.position.y).z)
                else:
                    new_z = instance.position.z + (z or 0.0)
            old_position: Vector3 = instance.position
            new_position: Vector3 = Vector3(new_x, new_y, new_z)
            if not no_undo_stack:
                self.undo_stack.push(MoveCommand(instance, old_position, new_position))
            instance.position = new_position

            # Sync to Blender if not already syncing from Blender
            if self.is_blender_mode() and self._blender_controller is not None and not self._transform_sync_in_progress:
                self._blender_controller.update_instance_position(instance, new_x, new_y, new_z)

    def rotate_selected(self, x: float, y: float):
        if self.ui.lockInstancesCheck.isChecked():
            return

        for instance in self.selected_instances:
            new_yaw = x / 60
            new_pitch = (y or 1) / 60
            new_roll = 0.0
            if not isinstance(instance, (GITCamera, GITCreature, GITDoor, GITPlaceable, GITStore, GITWaypoint)):
                continue  # doesn't support rotations.
            instance.rotate(new_yaw, new_pitch, new_roll)

            # Sync to Blender if not already syncing from Blender
            if self.is_blender_mode() and self._blender_controller is not None and not self._transform_sync_in_progress:
                if isinstance(instance, GITCamera):
                    ori = instance.orientation
                    self._blender_controller.update_instance_rotation(
                        instance,
                        orientation=(ori.x, ori.y, ori.z, ori.w),
                    )
                else:
                    self._blender_controller.update_instance_rotation(
                        instance,
                        bearing=instance.bearing,
                    )

    # endregion

    # region Signal Callbacks
    def _on_saved_resource(
        self,
        resource: ModuleResource,
    ):
        resource.reload()
        scene = self.ui.mainRenderer.scene
        if scene is not None:
            scene.clear_cache_buffer.append(ResourceIdentifier(resource.resname(), resource.restype()))

    def handle_undo_redo_from_long_action_finished(self):
        if self.is_drag_moving:
            for instance, old_position in self.initial_positions.items():
                new_position = instance.position
                if old_position and new_position != old_position:
                    self.log.debug("Create the MoveCommand for undo/redo functionality")
                    move_command = MoveCommand(instance, old_position, new_position)
                    self.undo_stack.push(move_command)
                elif not old_position:
                    self.log.debug("No old position for %s", instance.resref)
                else:
                    self.log.debug("Both old and new positions are the same %s", instance.resref)

            # Reset for the next drag operation
            self.initial_positions.clear()
            self.log.debug("No longer drag moving")
            self.is_drag_moving = False

        if self.is_drag_rotating:
            for instance, old_rotation in self.initial_rotations.items():
                new_rotation = instance.orientation if isinstance(instance, GITCamera) else instance.bearing
                if old_rotation and new_rotation != old_rotation:
                    self.log.debug("Create the RotateCommand for undo/redo functionality")
                    self.undo_stack.push(RotateCommand(instance, old_rotation, new_rotation))
                elif not old_rotation:
                    self.log.debug("No old rotation for %s", instance.resref)
                else:
                    self.log.debug("Both old and new rotations are the same for %s", instance.resref)
            self.initial_rotations.clear()
            self.log.debug("No longer drag rotating")
            self.is_drag_rotating = False

    def on_instance_list_single_clicked(self):
        if self.ui.instanceList.selectedItems():
            instance = self.get_git_instance_from_highlighted_list_item()
            self.set_selection([instance])

    def on_instance_list_double_clicked(self):
        if self.ui.instanceList.selectedItems():
            instance = self.get_git_instance_from_highlighted_list_item()
            self.set_selection([instance])
            self.ui.mainRenderer.snap_camera_to_point(instance.position)
            self.ui.flatRenderer.snap_camera_to_point(instance.position)

    def get_git_instance_from_highlighted_list_item(self) -> GITInstance:
        item: QListWidgetItem = self.ui.instanceList.selectedItems()[0]
        result: GITInstance = item.data(Qt.ItemDataRole.UserRole)
        return result

    def on_instance_visibility_double_click(self, checkbox: QCheckBox):
        self.ui.viewCreatureCheck.setChecked(False)
        self.ui.viewPlaceableCheck.setChecked(False)
        self.ui.viewDoorCheck.setChecked(False)
        self.ui.viewSoundCheck.setChecked(False)
        self.ui.viewTriggerCheck.setChecked(False)
        self.ui.viewEncounterCheck.setChecked(False)
        self.ui.viewWaypointCheck.setChecked(False)
        self.ui.viewCameraCheck.setChecked(False)
        self.ui.viewStoreCheck.setChecked(False)

        checkbox.setChecked(True)

    def enter_instance_mode(self):
        instance_mode = _InstanceMode.__new__(_InstanceMode)
        # HACK:
        instance_mode.delete_selected = self.delete_selected  # type: ignore[method-assign]
        instance_mode.edit_selected_instance = self.edit_instance  # type: ignore[method-assign]
        instance_mode.build_list = self.rebuild_instance_list  # type: ignore[method-assign]
        instance_mode.update_visibility = self.update_toggles  # type: ignore[method-assign]
        instance_mode.select_underneath = lambda: self.set_selection(self.ui.flatRenderer.instances_under_mouse())  # type: ignore[method-assign]
        instance_mode.__init__(self, self._installation, self.git())  # type: ignore[misc]
        # self._controls2d._mode.rotateSelectedToPoint = self.rotateSelected
        self._controls2d._mode = instance_mode  # noqa: SLF001

    def enter_geometry_mode(self):
        self._controls2d._mode = _GeometryMode(self, self._installation, self.git(), hide_others=False)  # noqa: SLF001

    def enter_spawn_mode(self):
        # TODO(NickHugi): _SpawnMode is incomplete - needs to implement all abstract methods from _Mode
        # Temporarily disabled until _SpawnMode is fully implemented
        # self._controls2d._mode = _SpawnMode(self, self._installation, self.git())
        self.log.warning("Spawn mode is not yet implemented")

    def on_resource_tree_context_menu(self, point: QPoint):
        menu = QMenu(self)
        cur_item = self.ui.resourceTree.currentItem()
        if cur_item is None:
            return
        data = cur_item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(data, ModuleResource):
            self._active_instance_location_menu(data, menu)
        menu.exec(self.ui.resourceTree.mapToGlobal(point))

    def on_resource_tree_double_clicked(self, point: QPoint):
        cur_item = self.ui.resourceTree.currentItem()
        assert cur_item is not None
        data = cur_item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(data, ModuleResource):
            self.open_module_resource(data)

    def on_resource_tree_single_clicked(self, point: QPoint):
        cur_item = self.ui.resourceTree.currentItem()
        assert cur_item is not None
        data = cur_item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(data, ModuleResource):
            self.jump_to_instance_list_action(data=data)

    def jump_to_instance_list_action(self, *args, data: ModuleResource, **kwargs):
        this_ident = data.identifier()
        instances = self.git().instances()
        for instance in instances:
            if instance.identifier() == this_ident:
                self.select_instance_item_on_list(instance)
                return

    def _active_instance_location_menu(self, data: ModuleResource, menu: _QMenu):
        """Builds an active override menu for a module resource.

        Args:
        ----
            data: ModuleResource - The module resource data
            menu: QMenu - The menu to build actions on
        """
        copy_to_override_action = QAction("Copy To Override", self)
        copy_to_override_action.triggered.connect(lambda _=None, r=data: self.copy_resource_to_override(r))

        menu.addAction("Edit Active File").triggered.connect(lambda _=None, r=data: self.open_module_resource(r))
        menu.addAction("Reload Active File").triggered.connect(lambda _=None: data.reload())
        menu.addAction(copy_to_override_action)
        menu.addSeparator()
        for location in data.locations():
            location_action = QAction(str(location), self)
            location_action.triggered.connect(lambda _=None, loc=location: self.activate_resource_file(data, loc))
            if location == data.active():
                location_action.setEnabled(False)
            if os.path.commonpath([str(location.absolute()), str(self._installation.override_path())]) == str(self._installation.override_path()):
                copy_to_override_action.setEnabled(False)
            menu.addAction(location_action)

        def jump_to_instance_list_action(*args, data=data, **kwargs):
            this_ident = data.identifier()
            instances = self.git().instances()
            for instance in instances:
                if instance.identifier() == this_ident:
                    # self.selectInstanceItemOnList(instance)
                    self.set_selection([instance])
                    return

        menu.addAction("Find in Instance List").triggered.connect(jump_to_instance_list_action)

    def on_3d_mouse_moved(self, screen: Vector2, screen_delta: Vector2, world: Vector3, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        self.update_status_bar(screen, buttons, keys, self.ui.mainRenderer)
        self._controls3d.on_mouse_moved(screen, screen_delta, world, buttons, keys)

    def on_3d_mouse_scrolled(self, delta: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        self.update_status_bar(QCursor.pos(), buttons, keys, self.ui.mainRenderer)
        self._controls3d.on_mouse_scrolled(delta, buttons, keys)

    def on_3d_mouse_pressed(self, screen: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        self.update_status_bar(screen, buttons, keys, self.ui.mainRenderer)
        self._controls3d.on_mouse_pressed(screen, buttons, keys)

    def do_cursor_lock(
        self,
        mut_scr: Vector2,
        *,
        center_mouse: bool = True,
        do_rotations: bool = True,
    ):
        new_pos: QPoint = QCursor.pos()
        renderer: ModuleRenderer = self.ui.mainRenderer
        if center_mouse:
            old_pos = renderer.mapToGlobal(renderer.rect().center())
            QCursor.setPos(old_pos.x(), old_pos.y())
        else:
            old_pos = renderer.mapToGlobal(QPoint(int(renderer._mouse_prev.x), int(renderer._mouse_prev.y)))
            QCursor.setPos(old_pos)
            local_old_pos: QPoint = renderer.mapFromGlobal(QPoint(old_pos.x(), old_pos.y()))
            mut_scr.x, mut_scr.y = local_old_pos.x(), local_old_pos.y()

        if do_rotations:
            yaw_delta = old_pos.x() - new_pos.x()
            pitch_delta = old_pos.y() - new_pos.y()
            if isinstance(self._controls3d, ModuleDesignerControlsFreeCam):
                strength = self.settings.rotateCameraSensitivityFC / 10000
                clamp = False
            else:
                strength = self.settings.rotateCameraSensitivity3d / 10000
                clamp = True
            renderer.rotate_camera(yaw_delta * strength, -pitch_delta * strength, clamp_rotations=clamp)

    def on_3d_mouse_released(self, screen: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        self.update_status_bar(screen, buttons, keys, self.ui.mainRenderer)
        self._controls3d.on_mouse_released(screen, buttons, keys)

    def on_3d_keyboard_released(self, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        self.update_status_bar(QCursor.pos(), buttons, keys, self.ui.mainRenderer)
        self._controls3d.on_keyboard_released(buttons, keys)

    def on_3d_keyboard_pressed(self, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        self.update_status_bar(QCursor.pos(), buttons, keys, self.ui.mainRenderer)
        self._controls3d.on_keyboard_pressed(buttons, keys)

    def on_3d_object_selected(self, instance: GITInstance):
        if instance is not None:
            self.set_selection([instance])
        else:
            self.set_selection([])

    def on_context_menu(self, world: Vector3, point: QPoint, *, is_flat_renderer_call: bool | None = None):
        self.log.debug(f"onContextMenu(world={world}, point={point}, isFlatRendererCall={is_flat_renderer_call})")
        if self._module is None:
            self.log.warning("onContextMenu No module.")
            return
        scene = self.ui.mainRenderer.scene
        if scene is None:
            QMessageBox.information(
                self,
                "Use Blender",
                "Spatial context menus are managed by Blender while Blender mode is active. Right-click the object inside Blender to see the Holocron context menu.",
            )
            return

        if len(scene.selection) == 0:
            self.log.debug("onContextMenu No selection")
            menu = self.build_insert_instance_menu(world)
        else:
            menu = self.on_context_menu_selection_exists(world, is_flat_renderer_call=is_flat_renderer_call, get_menu=True)

        if menu is None:
            return
        self.show_final_context_menu(menu)

    def build_insert_instance_menu(self, world: Vector3):
        menu = QMenu(self)

        scene = self.ui.mainRenderer.scene
        if scene is None:
            return menu

        rot = scene.camera
        menu.addAction("Insert Camera").triggered.connect(lambda: self.add_instance(GITCamera(*world), walkmesh_snap=False))  # pyright: ignore[reportArgumentType]
        menu.addAction("Insert Camera at View").triggered.connect(lambda: self.add_instance(GITCamera(rot.x, rot.y, rot.z, rot.yaw, rot.pitch, 0, 0), walkmesh_snap=False))
        menu.addSeparator()
        menu.addAction("Insert Creature").triggered.connect(lambda: self.add_instance(GITCreature(*world), walkmesh_snap=True))
        menu.addAction("Insert Door").triggered.connect(lambda: self.add_instance(GITDoor(*world), walkmesh_snap=False))
        menu.addAction("Insert Placeable").triggered.connect(lambda: self.add_instance(GITPlaceable(*world), walkmesh_snap=False))
        menu.addAction("Insert Store").triggered.connect(lambda: self.add_instance(GITStore(*world), walkmesh_snap=False))
        menu.addAction("Insert Sound").triggered.connect(lambda: self.add_instance(GITSound(*world), walkmesh_snap=False))
        menu.addAction("Insert Waypoint").triggered.connect(lambda: self.add_instance(GITWaypoint(*world), walkmesh_snap=False))
        menu.addAction("Insert Encounter").triggered.connect(lambda: self.add_instance(GITEncounter(*world), walkmesh_snap=False))
        menu.addAction("Insert Trigger").triggered.connect(lambda: self.add_instance(GITTrigger(*world), walkmesh_snap=False))
        return menu

    def on_instance_list_right_clicked(
        self,
        *args,
        **kwargs,
    ):
        item: QListWidgetItem = self.ui.instanceList.selectedItems()[0]
        instance: GITInstance = item.data(Qt.ItemDataRole.UserRole)
        self.on_context_menu_selection_exists(instances=[instance])

    def on_context_menu_selection_exists(
        self,
        world: Vector3 | None = None,
        *,
        is_flat_renderer_call: bool | None = None,
        get_menu: bool | None = None,
        instances: Sequence[GITInstance] | None = None,
    ) -> _QMenu | None:  # sourcery skip: extract-method
        self.log.debug(f"onContextMenuSelectionExists(isFlatRendererCall={is_flat_renderer_call}, getMenu={get_menu})")
        menu = QMenu(self)
        instances = self.selected_instances if instances is None else instances

        if instances:
            instance = instances[0]
            if isinstance(instance, GITCamera):
                menu.addAction("Snap Camera to 3D View").triggered.connect(lambda: self.snap_camera_to_view(instance))
                menu.addAction("Snap 3D View to Camera").triggered.connect(lambda: self.snap_view_to_git_camera(instance))
            else:
                menu.addAction("Snap 3D View to Instance Position").triggered.connect(lambda: self.snap_view_to_git_instance(instance))
            menu.addSeparator()
            menu.addAction("Copy position to clipboard").triggered.connect(lambda: QApplication.clipboard().setText(str(instance.position)))
            menu.addAction("Edit Instance").triggered.connect(lambda: self.edit_instance(instance))
            menu.addAction("Remove").triggered.connect(self.delete_selected)
            menu.addSeparator()
            if world is not None and not isinstance(self._controls2d._mode, _SpawnMode):
                self._controls2d._mode._get_render_context_menu(Vector2(world.x, world.y), menu)
        if not get_menu:
            self.show_final_context_menu(menu)
            return None
        return menu

    def show_final_context_menu(self, menu: _QMenu):
        menu.popup(self.cursor().pos())
        menu.aboutToHide.connect(self.ui.mainRenderer.reset_all_down)
        menu.aboutToHide.connect(self.ui.flatRenderer.reset_all_down)

    def on_3d_renderer_initialized(self):
        self.log.debug("ModuleDesigner on3dRendererInitialized")
        self.show()
        self.activateWindow()

    def on_3d_scene_initialized(self):
        self.log.debug("ModuleDesigner on3dSceneInitialized")
        self._refresh_window_title()
        self.show()
        self.activateWindow()

        # Defer UI population to avoid blocking during module load
        QTimer.singleShot(50, self._deferred_initialization)

    def _deferred_initialization(self):
        """Complete initialization after window is shown."""
        self.log.debug("Building resource tree and instance list...")
        self.rebuild_resource_tree()
        self.rebuild_instance_list()
        self.rebuild_layout_tree()
        self.enter_instance_mode()
        self.log.info("Module designer ready")

    def on_2d_mouse_moved(self, screen: Vector2, delta: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        # self.log.debug("on2dMouseMoved, screen: %s, delta: %s, buttons: %s, keys: %s", screen, delta, buttons, keys)
        world_delta: Vector2 = self.ui.flatRenderer.to_world_delta(delta.x, delta.y)
        world: Vector3 = self.ui.flatRenderer.to_world_coords(screen.x, screen.y)
        self._controls2d.on_mouse_moved(screen, delta, Vector2.from_vector3(world), world_delta, buttons, keys)
        self.update_status_bar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)

    def on_2d_mouse_released(self, screen: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        # self.log.debug("on2dMouseReleased, screen: %s, buttons: %s, keys: %s", screen, buttons, keys)
        self._controls2d.on_mouse_released(screen, buttons, keys)
        self.update_status_bar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)

    def on_2d_keyboard_pressed(self, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        # self.log.debug("on2dKeyboardPressed, buttons: %s, keys: %s", buttons, keys)
        self._controls2d.on_keyboard_pressed(buttons, keys)
        self.update_status_bar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)

    def on_2d_keyboard_released(self, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        # self.log.debug("on2dKeyboardReleased, buttons: %s, keys: %s", buttons, keys)
        self._controls2d.on_keyboard_released(buttons, keys)
        self.update_status_bar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)

    def on_2d_mouse_scrolled(self, delta: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        # self.log.debug("on2dMouseScrolled, delta: %s, buttons: %s, keys: %s", delta, buttons, keys)
        self.update_status_bar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)
        self._controls2d.on_mouse_scrolled(delta, buttons, keys)

    def on_2d_mouse_pressed(self, screen: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        # self.log.debug("on2dMousePressed, screen: %s, buttons: %s, keys: %s", screen, buttons, keys)
        self._controls2d.on_mouse_pressed(screen, buttons, keys)
        self.update_status_bar(screen, buttons, keys, self.ui.flatRenderer)

    # endregion

    # region Layout Tab Handlers
    def on_add_room(self):
        """Add a new room to the layout."""
        if self._module is None:
            return

        layout_module = self._module.layout()
        if layout_module is None:
            self.log.warning("No layout resource found in module")
            return

        lyt: LYT | None = layout_module.resource()
        if lyt is None:
            lyt = LYT()
            layout_module._resource_obj = lyt  # noqa: SLF001

        # Create a new room at origin
        room = LYTRoom(model="newroom", position=Vector3(0, 0, 0))
        lyt.rooms.append(room)

        # Sync to Blender
        if self.is_blender_mode() and self._blender_controller is not None:
            self._blender_controller.add_room(room.model, room.position.x, room.position.y, room.position.z)

        self.rebuild_layout_tree()
        self.log.info(f"Added room '{room.model}' to layout")

    def on_add_door_hook(self):
        """Add a new door hook to the layout."""
        if self._module is None:
            return

        layout_module = self._module.layout()
        if layout_module is None:
            self.log.warning("No layout resource found in module")
            return

        lyt: LYT | None = layout_module.resource()
        if lyt is None or not lyt.rooms:
            self.log.warning("Cannot add door hook: no rooms in layout")
            return

        # Create a new door hook
        doorhook = LYTDoorHook(room=lyt.rooms[0].model, door=f"door{len(lyt.doorhooks)}", position=Vector3(0, 0, 0), orientation=Vector4(0, 0, 0, 1))
        lyt.doorhooks.append(doorhook)

        # Sync to Blender
        if self.is_blender_mode() and self._blender_controller is not None:
            self._blender_controller.add_door_hook(
                doorhook.room,
                doorhook.door,
                doorhook.position.x,
                doorhook.position.y,
                doorhook.position.z,
                orientation=(doorhook.orientation.x, doorhook.orientation.y, doorhook.orientation.z, doorhook.orientation.w),
            )

        self.rebuild_layout_tree()
        self.log.info(f"Added door hook '{doorhook.door}' to layout")

    def on_add_track(self):
        """Add a new track to the layout."""
        if self._module is None:
            return

        layout_module = self._module.layout()
        if layout_module is None:
            self.log.warning("No layout resource found in module")
            return

        lyt: LYT | None = layout_module.resource()
        if lyt is None:
            lyt = LYT()
            layout_module._resource_obj = lyt  # noqa: SLF001

        # Create a new track
        track = LYTTrack(model="newtrack", position=Vector3(0, 0, 0))
        lyt.tracks.append(track)

        # Sync to Blender
        if self.is_blender_mode() and self._blender_controller is not None:
            self._blender_controller.add_track(track.model, track.position.x, track.position.y, track.position.z)

        self.rebuild_layout_tree()
        self.log.info(f"Added track '{track.model}' to layout")

    def on_add_obstacle(self):
        """Add a new obstacle to the layout."""
        if self._module is None:
            return

        layout_module = self._module.layout()
        if layout_module is None:
            self.log.warning("No layout resource found in module")
            return

        lyt: LYT | None = layout_module.resource()
        if lyt is None:
            lyt = LYT()
            layout_module._resource_obj = lyt  # noqa: SLF001

        # Create a new obstacle
        obstacle = LYTObstacle(model="newobstacle", position=Vector3(0, 0, 0))
        lyt.obstacles.append(obstacle)

        # Sync to Blender
        if self.is_blender_mode() and self._blender_controller is not None:
            self._blender_controller.add_obstacle(obstacle.model, obstacle.position.x, obstacle.position.y, obstacle.position.z)

        self.rebuild_layout_tree()
        self.log.info(f"Added obstacle '{obstacle.model}' to layout")

    def on_import_texture(self):
        """Import a texture for use in the layout."""
        from qtpy.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(self, "Import Texture", "", "Image Files (*.tga *.tpc *.dds *.png *.jpg)")

        if file_path:
            self.log.info(f"Importing texture from {file_path}")
            # TODO: Implement texture import logic

    def on_generate_walkmesh(self):
        """Generate walkmesh from the current layout."""
        if self._module is None:
            return

        layout_module = self._module.layout()
        if layout_module is None:
            self.log.warning("No layout resource found in module")
            return

        lyt: LYT | None = layout_module.resource()
        if lyt is None or not lyt.rooms:
            self.log.warning("Cannot generate walkmesh: no rooms in layout")
            return

        self.log.info("Generating walkmesh from layout...")
        # TODO: Implement walkmesh generation logic

    def rebuild_layout_tree(self):
        """Rebuild the layout tree widget to show current LYT structure."""
        if self._module is None:
            return

        layout_module = self._module.layout()
        if layout_module is None:
            return

        lyt: LYT | None = layout_module.resource()
        if lyt is None:
            return

        self.ui.lytTree.blockSignals(True)
        self.ui.lytTree.clear()

        # Add rooms
        if lyt.rooms:
            rooms_item = QTreeWidgetItem(["Rooms"])
            self.ui.lytTree.addTopLevelItem(rooms_item)
            for room in lyt.rooms:
                room_item = QTreeWidgetItem([room.model])
                room_item.setData(0, Qt.ItemDataRole.UserRole, room)
                rooms_item.addChild(room_item)
            rooms_item.setExpanded(True)

        # Add door hooks
        if lyt.doorhooks:
            doors_item = QTreeWidgetItem(["Door Hooks"])
            self.ui.lytTree.addTopLevelItem(doors_item)
            for doorhook in lyt.doorhooks:
                door_item = QTreeWidgetItem([doorhook.door])
                door_item.setData(0, Qt.ItemDataRole.UserRole, doorhook)
                doors_item.addChild(door_item)
            doors_item.setExpanded(True)

        # Add tracks
        if lyt.tracks:
            tracks_item = QTreeWidgetItem(["Tracks"])
            self.ui.lytTree.addTopLevelItem(tracks_item)
            for track in lyt.tracks:
                track_item = QTreeWidgetItem([track.model])
                track_item.setData(0, Qt.ItemDataRole.UserRole, track)
                tracks_item.addChild(track_item)
            tracks_item.setExpanded(True)

        # Add obstacles
        if lyt.obstacles:
            obstacles_item = QTreeWidgetItem(["Obstacles"])
            self.ui.lytTree.addTopLevelItem(obstacles_item)
            for obstacle in lyt.obstacles:
                obstacle_item = QTreeWidgetItem([obstacle.model])
                obstacle_item.setData(0, Qt.ItemDataRole.UserRole, obstacle)
                obstacles_item.addChild(obstacle_item)
            obstacles_item.setExpanded(True)

        self.ui.lytTree.blockSignals(False)

        # Update LYT renderer if it exists
        if self._lyt_renderer:
            self._lyt_renderer.set_lyt(lyt)

    def on_lyt_tree_selection_changed(self):
        """Handle selection change in the layout tree."""
        selected_items: list[QTreeWidgetItem] = self.ui.lytTree.selectedItems()
        if not selected_items:
            return

        item = selected_items[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)

        if isinstance(data, LYTRoom):
            self.ui.lytElementTabs.setCurrentIndex(0)  # Room tab
            self.update_room_properties(data)
        elif isinstance(data, LYTDoorHook):
            self.ui.lytElementTabs.setCurrentIndex(1)  # Door Hook tab
            self.update_doorhook_properties(data)

    def update_room_properties(self, room: LYTRoom):
        """Update the room property editors with the selected room's data."""
        self.ui.modelEdit.blockSignals(True)
        self.ui.posXSpin.blockSignals(True)
        self.ui.posYSpin.blockSignals(True)
        self.ui.posZSpin.blockSignals(True)
        self.ui.rotXSpin.blockSignals(True)
        self.ui.rotYSpin.blockSignals(True)
        self.ui.rotZSpin.blockSignals(True)

        self.ui.modelEdit.setText(room.model)
        self.ui.posXSpin.setValue(room.position.x)
        self.ui.posYSpin.setValue(room.position.y)
        self.ui.posZSpin.setValue(room.position.z)

        # LYTRoom doesn't have orientation - reset rotation spinboxes
        self.ui.rotXSpin.setValue(0)
        self.ui.rotYSpin.setValue(0)
        self.ui.rotZSpin.setValue(0)

        self.ui.modelEdit.blockSignals(False)
        self.ui.posXSpin.blockSignals(False)
        self.ui.posYSpin.blockSignals(False)
        self.ui.posZSpin.blockSignals(False)
        self.ui.rotXSpin.blockSignals(False)
        self.ui.rotYSpin.blockSignals(False)
        self.ui.rotZSpin.blockSignals(False)

    def update_doorhook_properties(self, doorhook: LYTDoorHook):
        """Update the door hook property editors with the selected door hook's data."""
        if self._module is None:
            return

        layout_module = self._module.layout()
        if layout_module is None:
            return

        lyt: LYT | None = layout_module.resource()
        if lyt is None:
            return

        self.ui.roomNameCombo.blockSignals(True)
        self.ui.doorNameEdit.blockSignals(True)

        # Populate room combo
        self.ui.roomNameCombo.clear()
        for room in lyt.rooms:
            self.ui.roomNameCombo.addItem(room.model)

        # Set current values
        self.ui.roomNameCombo.setCurrentText(doorhook.room)
        self.ui.doorNameEdit.setText(doorhook.door)

        self.ui.roomNameCombo.blockSignals(False)
        self.ui.doorNameEdit.blockSignals(False)

    def get_selected_lyt_element(self) -> LYTRoom | LYTDoorHook | LYTTrack | LYTObstacle | None:
        """Get the currently selected LYT element from the tree."""
        selected_items = self.ui.lytTree.selectedItems()
        if not selected_items:
            return None
        return selected_items[0].data(0, Qt.ItemDataRole.UserRole)

    def on_room_position_changed(self):
        """Handle room position change from spinboxes."""
        element = self.get_selected_lyt_element()
        if not isinstance(element, LYTRoom):
            return

        element.position.x = self.ui.posXSpin.value()
        element.position.y = self.ui.posYSpin.value()
        element.position.z = self.ui.posZSpin.value()

    def on_room_rotation_changed(self):
        """Handle room rotation change from spinboxes."""
        element = self.get_selected_lyt_element()
        if not isinstance(element, LYTRoom):
            return

        # LYTRoom doesn't have orientation property - this is a no-op
        # Rotation is handled at the model level, not the room level

    def on_room_model_changed(self):
        """Handle room model name change."""
        element = self.get_selected_lyt_element()
        if not isinstance(element, LYTRoom):
            return

        element.model = self.ui.modelEdit.text()
        self.rebuild_layout_tree()

    def on_browse_model(self):
        """Browse for a model file to assign to the room."""
        from qtpy.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(self, "Select Model", "", "Model Files (*.mdl)")

        if file_path:
            model_name = Path(file_path).stem
            self.ui.modelEdit.setText(model_name)

    def on_doorhook_room_changed(self):
        """Handle door hook room change."""
        element = self.get_selected_lyt_element()
        if not isinstance(element, LYTDoorHook):
            return

        element.room = self.ui.roomNameCombo.currentText()

        # Sync to Blender (would need object name mapping)
        # For now, skip as this is less critical

    def on_doorhook_name_changed(self):
        """Handle door hook name change."""
        element = self.get_selected_lyt_element()
        if not isinstance(element, LYTDoorHook):
            return

        element.door = self.ui.doorNameEdit.text()
        self.rebuild_layout_tree()

    def on_lyt_tree_context_menu(self, point: QPoint):
        """Show context menu for layout tree items."""
        item = self.ui.lytTree.itemAt(point)
        if not item:
            return

        element = item.data(0, Qt.ItemDataRole.UserRole)
        if not element:
            return

        menu = QMenu(self)

        # Common operations
        edit_action = QAction("Edit Properties", self)
        edit_action.triggered.connect(lambda: self.edit_lyt_element(element))
        menu.addAction(edit_action)

        duplicate_action = QAction("Duplicate", self)
        duplicate_action.triggered.connect(lambda: self.duplicate_lyt_element(element))
        menu.addAction(duplicate_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_lyt_element(element))
        menu.addAction(delete_action)

        menu.addSeparator()

        # Type-specific operations
        if isinstance(element, LYTRoom):
            load_model_action = QAction("Load Room Model", self)
            load_model_action.triggered.connect(lambda: self.load_room_model(element))
            menu.addAction(load_model_action)

        elif isinstance(element, LYTDoorHook):
            place_action = QAction("Place in 3D View", self)
            place_action.triggered.connect(lambda: self.place_doorhook_in_view(element))
            menu.addAction(place_action)

        menu.exec(self.ui.lytTree.mapToGlobal(point))

    def edit_lyt_element(self, element: LYTRoom | LYTDoorHook | LYTTrack | LYTObstacle):
        """Open editor dialog for LYT element."""
        # Select the element in the tree
        for i in range(self.ui.lytTree.topLevelItemCount()):
            parent = self.ui.lytTree.topLevelItem(i)
            if parent:
                for j in range(parent.childCount()):
                    child = parent.child(j)
                    if child and child.data(0, Qt.ItemDataRole.UserRole) == element:
                        self.ui.lytTree.setCurrentItem(child)
                        break

    def duplicate_lyt_element(self, element: LYTRoom | LYTDoorHook | LYTTrack | LYTObstacle):
        """Duplicate the selected LYT element."""
        if self._module is None:
            return

        layout_module = self._module.layout()
        if layout_module is None:
            return

        lyt: LYT | None = layout_module.resource()
        if lyt is None:
            return

        # Create duplicate with offset
        offset = Vector3(10, 10, 0)

        if isinstance(element, LYTRoom):
            new_element = LYTRoom(f"{element.model}_copy", element.position + offset)
            lyt.rooms.append(new_element)
        elif isinstance(element, LYTDoorHook):
            new_element = LYTDoorHook(element.room, f"{element.door}_copy", element.position + offset, element.orientation)
            lyt.doorhooks.append(new_element)
        elif isinstance(element, LYTTrack):
            new_element = LYTTrack(f"{element.model}_copy", element.position + offset)
            lyt.tracks.append(new_element)
        elif isinstance(element, LYTObstacle):
            new_element = LYTObstacle(f"{element.model}_copy", element.position + offset)
            lyt.obstacles.append(new_element)

        self.rebuild_layout_tree()
        self.log.info(f"Duplicated {type(element).__name__}")

    def delete_lyt_element(self, element: LYTRoom | LYTDoorHook | LYTTrack | LYTObstacle):
        """Delete the selected LYT element."""
        if self._module is None:
            return

        layout_module = self._module.layout()
        if layout_module is None:
            return

        lyt: LYT | None = layout_module.resource()
        if lyt is None:
            return

        # Confirm deletion
        element_type = type(element).__name__
        if isinstance(element, LYTRoom):
            element_name = element.model
        elif isinstance(element, LYTDoorHook):
            element_name = element.door
        elif isinstance(element, LYTTrack):
            element_name = element.model
        elif isinstance(element, LYTObstacle):
            element_name = element.model
        else:
            element_name = "element"

        reply = QMessageBox.question(
            self, "Confirm Delete", f"Delete {element_type} '{element_name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Determine element type for Blender
        blender_type_map = {
            LYTRoom: "room",
            LYTDoorHook: "door_hook",
            LYTTrack: "track",
            LYTObstacle: "obstacle",
        }
        blender_type = blender_type_map.get(type(element))

        # Remove element
        if isinstance(element, LYTRoom):
            lyt.rooms.remove(element)
        elif isinstance(element, LYTDoorHook):
            lyt.doorhooks.remove(element)
        elif isinstance(element, LYTTrack):
            lyt.tracks.remove(element)
        elif isinstance(element, LYTObstacle):
            lyt.obstacles.remove(element)

        # Sync to Blender (would need object name, but we can try to find it)
        if self.is_blender_mode() and self._blender_controller is not None and blender_type:
            # Try to find object by name pattern
            obj_name = None
            if isinstance(element, LYTRoom):
                obj_name = f"Room_{element.model}"
            elif isinstance(element, LYTDoorHook):
                obj_name = f"DoorHook_{element.door}"
            elif isinstance(element, LYTTrack):
                obj_name = f"Track_{element.model}"
            elif isinstance(element, LYTObstacle):
                obj_name = f"Obstacle_{element.model}"

            if obj_name:
                self._blender_controller.remove_lyt_element(obj_name, blender_type)

        self.rebuild_layout_tree()
        self.log.info(f"Deleted {element_type} '{element_name}'")

    def load_room_model(self, room: LYTRoom):
        """Load and display a room model in the 3D view."""
        if self._module is None:
            return

        # Try to load the MDL file
        mdl_resource = self._module.resource(room.model, ResourceType.MDL)
        if mdl_resource:
            self.log.info(f"Loading room model: {room.model}")
            # The model will be loaded and positioned at room.position
            # This would integrate with the 3D renderer's model loading system
        else:
            self.log.warning(f"Room model not found: {room.model}")
            QMessageBox.warning(self, "Model Not Found", f"Could not find model '{room.model}.mdl' in the module.")

    def place_doorhook_in_view(self, doorhook: LYTDoorHook):
        """Place the door hook at the current 3D view position."""
        # Get the cursor position from the 3D view
        scene = self.ui.mainRenderer.scene
        if scene:
            doorhook.position.x = scene.cursor.position().x
            doorhook.position.y = scene.cursor.position().y
            doorhook.position.z = scene.cursor.position().z
            self.rebuild_layout_tree()
            self.log.info(f"Placed door hook '{doorhook.door}' in 3D view")

    # endregion

    # region Events
    def keyPressEvent(self, e: QKeyEvent | None):  # noqa: FBT001, FBT002  # pyright: ignore[reportIncompatibleMethodOverride]
        if e is None:
            return
        super().keyPressEvent(e)
        self.ui.mainRenderer.keyPressEvent(e)
        self.ui.flatRenderer.keyPressEvent(e)

    def keyReleaseEvent(self, e: QKeyEvent | None):  # noqa: FBT001, FBT002  # pyright: ignore[reportIncompatibleMethodOverride]
        if e is None:
            return
        super().keyReleaseEvent(e)
        self.ui.mainRenderer.keyReleaseEvent(e)
        self.ui.flatRenderer.keyReleaseEvent(e)

    # endregion

    def _on_undo(self):
        """Handle undo action."""
        self.undo_stack.undo()
        # Blender sync is handled by _on_undo_stack_changed

    def _on_redo(self):
        """Handle redo action."""
        self.undo_stack.redo()
        # Blender sync is handled by _on_undo_stack_changed

    def _on_undo_stack_changed(self, index: int):
        """Handle undo stack index changes to sync with Blender."""
        if not self.is_blender_mode() or self._blender_controller is None:
            return

        # Don't sync if we're in the middle of applying a Blender change
        if self._transform_sync_in_progress or self._property_sync_in_progress:
            return

        # The undo/redo commands themselves don't need to sync to Blender
        # because Blender will receive the actual transform/property updates
        # when the commands execute. This is just for notification purposes.
        pass

    def update_camera(self):
        if self._use_blender_mode and self.ui.mainRenderer.scene is None:
            return
        # For standard 3D orbit controls, require the mouse to be over the 3D view
        # before applying keyboard-driven camera updates. In free-cam mode we allow
        # movement even when the cursor isn't strictly over the widget so that
        # "press F then WASD to fly" behaves as expected.
        from toolset.gui.windows.designer_controls import ModuleDesignerControlsFreeCam

        if not self.ui.mainRenderer.underMouse() and not isinstance(self._controls3d, ModuleDesignerControlsFreeCam):
            return

        # Check camera rotation and movement keys
        keys: set[Qt.Key] = self.ui.mainRenderer.keys_down()
        buttons: set[Qt.MouseButton] = self.ui.mainRenderer.mouse_down()
        rotation_keys: dict[str, bool] = {
            "left": self._controls3d.rotate_camera_left.satisfied(buttons, keys),
            "right": self._controls3d.rotate_camera_right.satisfied(buttons, keys),
            "up": self._controls3d.rotate_camera_up.satisfied(buttons, keys),
            "down": self._controls3d.rotate_camera_down.satisfied(buttons, keys),
        }
        movement_keys: dict[str, bool] = {
            "up": self._controls3d.move_camera_up.satisfied(buttons, keys),
            "down": self._controls3d.move_camera_down.satisfied(buttons, keys),
            "left": self._controls3d.move_camera_left.satisfied(buttons, keys),
            "right": self._controls3d.move_camera_right.satisfied(buttons, keys),
            "forward": self._controls3d.move_camera_forward.satisfied(buttons, keys),
            "backward": self._controls3d.move_camera_backward.satisfied(buttons, keys),
            "in": self._controls3d.zoom_camera_in.satisfied(buttons, keys),
            "out": self._controls3d.zoom_camera_out.satisfied(buttons, keys),
        }

        # Determine last frame time to determine the delta modifiers
        cur_time = time.time()
        time_since_last_frame = cur_time - self.last_frame_time
        self.last_frame_time = cur_time

        # Skip if frame time is too large (e.g., window was minimized)
        if time_since_last_frame > 0.1:
            return

        # Calculate rotation delta with frame-independent timing
        norm_rotate_units_setting: float = self.settings.rotateCameraSensitivity3d / 1000
        norm_rotate_units_setting *= self.target_frame_rate * time_since_last_frame
        angle_units_delta: float = (math.pi / 4) * norm_rotate_units_setting

        # Rotate camera based on key inputs
        if rotation_keys["left"]:
            self.ui.mainRenderer.rotate_camera(angle_units_delta, 0)
        elif rotation_keys["right"]:
            self.ui.mainRenderer.rotate_camera(-angle_units_delta, 0)
        if rotation_keys["up"]:
            self.ui.mainRenderer.rotate_camera(0, angle_units_delta)
        elif rotation_keys["down"]:
            self.ui.mainRenderer.rotate_camera(0, -angle_units_delta)

        # Calculate movement delta
        if self._controls3d.speed_boost_control.satisfied(
            self.ui.mainRenderer.mouse_down(),
            self.ui.mainRenderer.keys_down(),
            exact_keys_and_buttons=False,
        ):
            move_units_delta: float = (
                self.settings.boostedFlyCameraSpeedFC
                if isinstance(self._controls3d, ModuleDesignerControlsFreeCam)
                else self.settings.boostedMoveCameraSensitivity3d
            )
        else:
            move_units_delta = (
                self.settings.flyCameraSpeedFC
                if isinstance(self._controls3d, ModuleDesignerControlsFreeCam)
                else self.settings.moveCameraSensitivity3d
            )

        move_units_delta /= 500  # normalize
        move_units_delta *= time_since_last_frame * self.target_frame_rate  # apply modifier based on frame time

        # Zoom camera based on inputs
        if movement_keys["in"]:
            self.ui.mainRenderer.zoom_camera(move_units_delta)
        if movement_keys["out"]:
            self.ui.mainRenderer.zoom_camera(-move_units_delta)

        # Move camera based on key inputs
        if movement_keys["up"]:
            if isinstance(self._controls3d, ModuleDesignerControls3d):
                self.ui.mainRenderer.scene.camera.z += move_units_delta
            else:
                self.ui.mainRenderer.move_camera(0, 0, move_units_delta)
        if movement_keys["down"]:
            if isinstance(self._controls3d, ModuleDesignerControls3d):
                self.ui.mainRenderer.scene.camera.z -= move_units_delta
            else:
                self.ui.mainRenderer.move_camera(0, 0, -move_units_delta)

        if movement_keys["left"]:
            if isinstance(self._controls3d, ModuleDesignerControls3d):
                self.ui.mainRenderer.pan_camera(0, -move_units_delta, 0)
            else:
                self.ui.mainRenderer.move_camera(0, -move_units_delta, 0)
        if movement_keys["right"]:
            if isinstance(self._controls3d, ModuleDesignerControls3d):
                self.ui.mainRenderer.pan_camera(0, move_units_delta, 0)
            else:
                self.ui.mainRenderer.move_camera(0, move_units_delta, 0)

        if movement_keys["forward"]:
            if isinstance(self._controls3d, ModuleDesignerControls3d):
                self.ui.mainRenderer.pan_camera(move_units_delta, 0, 0)
            else:
                self.ui.mainRenderer.move_camera(move_units_delta, 0, 0)
        if movement_keys["backward"]:
            if isinstance(self._controls3d, ModuleDesignerControls3d):
                self.ui.mainRenderer.pan_camera(-move_units_delta, 0, 0)
            else:
                self.ui.mainRenderer.move_camera(-move_units_delta, 0, 0)
