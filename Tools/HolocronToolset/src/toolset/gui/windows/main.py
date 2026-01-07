from __future__ import annotations

import errno
import os
import shutil
import sys

from collections import defaultdict
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any, Callable, cast

import qtpy

from qtpy import QtCore
from qtpy.QtCore import (
    QCoreApplication,
    QFileSystemWatcher,
    QMimeData,
    QSortFilterProxyModel,
    QThread,
    QTimer,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
    Slot,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QIcon, QPixmap, QStandardItem
from qtpy.QtWidgets import (
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QApplication,
    QBoxLayout,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedLayout,
    QVBoxLayout,
)

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from pykotor.extract.file import FileResource, ResourceIdentifier, ResourceResult
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.erf import ERF, ERFType, read_erf, write_erf
from pykotor.resource.formats.mdl import read_mdl, write_mdl
from pykotor.resource.formats.rim import RIM, read_rim, write_rim
from pykotor.resource.formats.tpc import read_tpc, write_tpc
from pykotor.resource.type import ResourceType
from pykotor.tools import module
from pykotor.tools.misc import is_any_erf_type_file, is_bif_file, is_capsule_file, is_erf_file, is_mod_file, is_rim_file
from pykotor.tools.model import iterate_lightmaps, iterate_textures
from pykotor.tools.path import CaseAwarePath
from toolset.config import get_remote_toolset_update_info
from toolset.data.installation import HTInstallation
from toolset.gui.common.localization import (
    set_language,
    translate as tr,
    trf,
)
from toolset.gui.common.style.theme_manager import ThemeManager
from toolset.gui.dialogs.about import About
from toolset.gui.dialogs.asyncloader import AsyncLoader
from toolset.gui.dialogs.clone_module import CloneModuleDialog
from toolset.gui.dialogs.load_from_location_result import FileSelectionWindow
from toolset.gui.dialogs.save.generic_file_saver import FileSaveHandler
from toolset.gui.dialogs.search import FileResults, FileSearcher
from toolset.gui.dialogs.settings import SettingsDialog
from toolset.gui.dialogs.theme_selector import ThemeSelectorDialog
from toolset.gui.dialogs.tslpatchdata_editor import TSLPatchDataEditor
from toolset.gui.editors.dlg import DLGEditor
from toolset.gui.editors.erf import ERFEditor
from toolset.gui.editors.gff import GFFEditor
from toolset.gui.editors.nss import NSSEditor
from toolset.gui.editors.ssf import SSFEditor
from toolset.gui.editors.tlk import TLKEditor
from toolset.gui.editors.txt import TXTEditor
from toolset.gui.editors.utc import UTCEditor
from toolset.gui.editors.utd import UTDEditor
from toolset.gui.editors.ute import UTEEditor
from toolset.gui.editors.uti import UTIEditor
from toolset.gui.editors.utm import UTMEditor
from toolset.gui.editors.utp import UTPEditor
from toolset.gui.editors.uts import UTSEditor
from toolset.gui.editors.utt import UTTEditor
from toolset.gui.editors.utw import UTWEditor
from toolset.gui.widgets.kotor_filesystem_model import ResourceFileSystemWidget
from toolset.gui.widgets.main_widgets import ResourceList, ResourceStandardItem
from toolset.gui.widgets.settings.widgets.misc import GlobalSettings
from toolset.gui.windows.help import HelpWindow
from toolset.gui.windows.indoor_builder import IndoorMapBuilder
from toolset.gui.windows.kotordiff import KotorDiffWindow
from toolset.gui.windows.module_designer import ModuleDesigner
from toolset.gui.windows.update_manager import UpdateManager
from toolset.utils.misc import open_link
from toolset.utils.window import add_window, open_resource_editor
from utility.tricks import debug_reload_pymodules

if TYPE_CHECKING:
    from qtpy import QtGui
    from qtpy.QtCore import (
        QAbstractItemModel,
        QModelIndex,  # pyright: ignore[reportPrivateImportUsage]
        QPoint,
    )
    from qtpy.QtGui import QCloseEvent, QKeyEvent, QMouseEvent, QPalette, QShowEvent, QStandardItemModel
    from qtpy.QtWidgets import QBoxLayout, QComboBox, QStackedLayout, QStyle, QWidget
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.extract.file import LocationResult, ResourceResult
    from pykotor.resource.formats.mdl import MDL
    from pykotor.resource.formats.tpc import TPC
    from pykotor.resource.type import SOURCE_TYPES
    from toolset.gui.common.localization import ToolsetLanguage
    from toolset.gui.widgets.main_widgets import ResourceModel, TextureList
    from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTreeView


def run_module_designer(
    active_path: str,
    active_name: str,
    active_tsl: bool,  # noqa: FBT001
    module_path: str | None = None,
):
    """An alternative way to start the ModuleDesigner: run this function in a new process so the main tool window doesn't wait on the module designer."""
    from qtpy.QtGui import QSurfaceFormat

    from toolset.__main__ import main_init

    main_init()

    # Set default OpenGL surface format before creating QApplication
    # This is critical for PyPy and ensures proper OpenGL context initialization
    fmt = QSurfaceFormat()
    fmt.setDepthBufferSize(24)
    fmt.setStencilBufferSize(8)
    fmt.setVersion(3, 3)  # Request OpenGL 3.3
    # Use CompatibilityProfile instead of CoreProfile - CoreProfile requires VAO to be bound
    # before any buffer operations, which causes issues with PyOpenGL's lazy loading
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
    fmt.setSamples(4)  # Enable multisampling for antialiasing
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication([])
    designerUi = ModuleDesigner(
        None,
        HTInstallation(active_path, active_name, tsl=active_tsl),
        CaseAwarePath(module_path) if module_path is not None else None,
    )
    # Standardized resource path format
    icon_path = ":/images/icons/sith.png"

    # Debugging: Check if the resource path is accessible
    if not QPixmap(icon_path).isNull():
        designerUi.log.debug(f"HT main window Icon loaded successfully from {icon_path}")
        designerUi.setWindowIcon(QIcon(QPixmap(icon_path)))
        cast("QApplication", QApplication.instance()).setWindowIcon(QIcon(QPixmap(icon_path)))
    else:
        print(f"Failed to load HT main window icon from {icon_path}")
    add_window(designerUi, show=False)
    sys.exit(app.exec())


class UpdateCheckThread(QThread):
    update_info_fetched: Signal = Signal(dict, dict, bool)  # pyright: ignore[reportPrivateImportUsage]

    def __init__(self, tool_window: ToolWindow, *, silent: bool = False):
        super().__init__()
        self.toolWindow: ToolWindow = tool_window
        self.silent: bool = silent

    def get_latest_version_info(self) -> tuple[dict[str, Any], dict[str, Any]]:
        edge_info: dict[str, Any] = {}
        if self.toolWindow.settings.useBetaChannel:
            edge_info = self._get_remote_toolset_update_info(use_beta_channel=True)

        master_info: dict[str, Any] = self._get_remote_toolset_update_info(use_beta_channel=False)
        return master_info, edge_info

    def _get_remote_toolset_update_info(
        self,
        *,
        use_beta_channel: bool,
    ) -> dict[str, Any]:
        result: Exception | dict[str, Any] = get_remote_toolset_update_info(use_beta_channel=use_beta_channel, silent=self.silent)
        print(f"<SDM> [get_latest_version_info scope] {'edge_info' if use_beta_channel else 'master_info'}: ", result)

        if not isinstance(result, dict):
            if self.silent:
                result = {}
            elif isinstance(result, BaseException):
                raise result
            else:
                raise TypeError(f"Unexpected result type: {result}")

        return result

    def run(self):
        # This method is executed in a separate thread
        master_info, edge_info = self.get_latest_version_info()
        self.update_info_fetched.emit(master_info, edge_info, self.silent)


class ToolWindow(QMainWindow):
    """Main window for the Holocron Toolset."""

    sig_module_files_updated: Signal = Signal(str, str)  # pyright: ignore[reportPrivateImportUsage]
    sig_override_files_update: Signal = Signal(object, object)  # pyright: ignore[reportPrivateImportUsage]
    sig_installation_changed: Signal = Signal(HTInstallation)

    def __init__(self):
        """Initialize the main window for the Holocron Toolset."""
        super().__init__()

        # Core application state
        self.active: HTInstallation | None = None
        self.installations: dict[str, HTInstallation] = {}
        self.settings: GlobalSettings = GlobalSettings()
        self.update_manager: UpdateManager = UpdateManager(silent=True)

        # Theme and styling setup
        q_style: QStyle | None = self.style()
        assert q_style is not None, "window style was somehow None"
        self.original_style: str = q_style.objectName()
        self.original_palette: QPalette = self.palette()
        self.theme_manager: ThemeManager = ThemeManager(self.original_style)
        # Apply both theme and style on initialization
        self.theme_manager._apply_theme_and_style(self.settings.selectedTheme, self.settings.selectedStyle)

        # UI state management
        self.previous_game_combo_index: int = 0
        self._mouse_move_pos: QPoint | None = None

        # Dialog management (lazy-loaded)
        self._theme_dialog: ThemeSelectorDialog | None = None
        self._language_actions: dict[int, QAction] = {}

        # File system watcher for auto-detecting module/override changes
        self._file_watcher: QFileSystemWatcher = QFileSystemWatcher(self)
        self._pending_module_changes: list[str] = []
        self._pending_override_changes: list[str] = []
        self._last_watcher_update: datetime = datetime.now(tz=timezone.utc).astimezone()

        # Debounce timer to batch multiple rapid file changes
        self._watcher_debounce_timer: QTimer = QTimer(self)
        self._watcher_debounce_timer.setSingleShot(True)
        self._watcher_debounce_timer.setInterval(500)  # 500ms debounce
        self._watcher_debounce_timer.timeout.connect(self._process_pending_file_changes)

        RobustLogger().debug("TRACE: About to call _initUi()")
        # Initialize UI and setup
        self._initUi()
        self._setup_signals()

        # Language system will set the title in apply_translations()
        self.reload_settings()
        self.unset_installation()

    def _setup_file_watcher(self):
        """Set up file system watcher for the current installation's modules and override folders."""
        # Clear any existing watched paths
        watched_dirs = self._file_watcher.directories()
        if watched_dirs:
            self._file_watcher.removePaths(watched_dirs)
        watched_files = self._file_watcher.files()
        if watched_files:
            self._file_watcher.removePaths(watched_files)

        # Clear pending changes
        self._pending_module_changes.clear()
        self._pending_override_changes.clear()

        if self.active is None:
            return

        # Watch the modules directory
        module_path = self.active.module_path()
        if module_path.is_dir():
            self._file_watcher.addPath(str(module_path))
            RobustLogger().debug(f"File watcher watching modules directory: {module_path}")

        # Watch the override directory
        override_path = self.active.override_path()
        if override_path.is_dir():
            self._file_watcher.addPath(str(override_path))
            RobustLogger().debug(f"File watcher watching override directory: {override_path}")

    def _clear_file_watcher(self):
        """Clear all watched paths from the file system watcher."""
        watched_dirs = self._file_watcher.directories()
        if watched_dirs:
            self._file_watcher.removePaths(watched_dirs)
        watched_files = self._file_watcher.files()
        if watched_files:
            self._file_watcher.removePaths(watched_files)
        self._pending_module_changes.clear()
        self._pending_override_changes.clear()
        self._watcher_debounce_timer.stop()

    @Slot(str)
    def _on_watched_directory_changed(self, path: str):
        """Handle directory change events from QFileSystemWatcher."""
        if self.active is None:
            return

        normalized_path = os.path.normpath(path)
        module_path = os.path.normpath(str(self.active.module_path()))
        override_path = os.path.normpath(str(self.active.override_path()))

        RobustLogger().debug(f"File watcher detected directory change: {normalized_path}")

        # Determine which type of change this is
        if normalized_path.lower() == module_path.lower() or normalized_path.lower().startswith(module_path.lower()):
            if normalized_path not in self._pending_module_changes:
                self._pending_module_changes.append(normalized_path)
        elif normalized_path.lower() == override_path.lower() or normalized_path.lower().startswith(override_path.lower()):
            if normalized_path not in self._pending_override_changes:
                self._pending_override_changes.append(normalized_path)

        # Reset debounce timer
        self._watcher_debounce_timer.start()

    @Slot(str)
    def _on_watched_file_changed(self, path: str):
        """Handle file change events from QFileSystemWatcher."""
        if self.active is None:
            return

        normalized_path = os.path.normpath(path)
        module_path = os.path.normpath(str(self.active.module_path()))
        override_path = os.path.normpath(str(self.active.override_path()))

        RobustLogger().debug(f"File watcher detected file change: {normalized_path}")

        # Determine which type of change this is
        if module_path.lower() in normalized_path.lower():
            if normalized_path not in self._pending_module_changes:
                self._pending_module_changes.append(normalized_path)
        elif override_path.lower() in normalized_path.lower():
            if normalized_path not in self._pending_override_changes:
                self._pending_override_changes.append(normalized_path)

        # Reset debounce timer
        self._watcher_debounce_timer.start()

    @Slot()
    def _process_pending_file_changes(self):
        """Process accumulated file changes after debounce period."""
        if self.active is None:
            return

        has_module_changes = bool(self._pending_module_changes)
        has_override_changes = bool(self._pending_override_changes)

        if not has_module_changes and not has_override_changes:
            return

        # Check if window is active/focused
        is_focused = self.isActiveWindow()

        if is_focused:
            # Window is focused - ask user if they want to refresh
            self._show_refresh_dialog(has_module_changes, has_override_changes)
        else:
            # Window is not focused - auto-refresh
            self._auto_refresh_changes(has_module_changes, has_override_changes)

    def _show_refresh_dialog(self, has_module_changes: bool, has_override_changes: bool):
        """Show a dialog asking the user if they want to refresh after file changes."""
        from toolset.gui.common.localization import translate as local_tr

        # Build list of changed files for details
        changed_files: list[str] = []

        if has_module_changes:
            changed_files.append("=== Modules Directory ===")
            for path in self._pending_module_changes:
                changed_files.append(f"  {Path(path).name}")

        if has_override_changes:
            changed_files.append("=== Override Directory ===")
            for path in self._pending_override_changes:
                changed_files.append(f"  {Path(path).name}")

        # Build message
        changes_desc: list[str] = []
        if has_module_changes:
            changes_desc.append(local_tr("Modules"))
        if has_override_changes:
            changes_desc.append(local_tr("Override"))

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(local_tr("File Changes Detected"))
        msg_box.setText(
            local_tr("Changes were detected in the following directories:") + "\n" + ", ".join(changes_desc) + "\n\n" + local_tr("Would you like to refresh the file lists?")
        )
        msg_box.setDetailedText("\n".join(changed_files))
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
        msg_box.setIcon(QMessageBox.Icon.Question)

        result = msg_box.exec()

        if result == QMessageBox.StandardButton.Yes:
            self._auto_refresh_changes(has_module_changes, has_override_changes)
        else:
            # User declined, clear pending changes
            self._pending_module_changes.clear()
            self._pending_override_changes.clear()

    def _auto_refresh_changes(self, has_module_changes: bool, has_override_changes: bool):
        """Auto-refresh the appropriate lists based on detected changes."""
        if has_module_changes:
            RobustLogger().info(f"Auto-refreshing module list due to {len(self._pending_module_changes)} file changes")
            self.refresh_module_list(reload=True)
            self._pending_module_changes.clear()

        if has_override_changes:
            RobustLogger().info(f"Auto-refreshing override list due to {len(self._pending_override_changes)} file changes")
            self.refresh_override_list(reload=True)
            self._pending_override_changes.clear()

    def _initUi(self):
        """Initialize Holocron Toolset main window UI."""
        from toolset.uic.qtpy.windows.main import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Setup event filter to prevent scroll wheel interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter

        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        self.ui.coreWidget.hide_section()
        self.ui.coreWidget.hide_reload_button()

        if os.getenv("HOLOCRON_DEBUG_RELOAD") is not None:
            self.ui.menubar.addAction("Debug Reload").triggered.connect(debug_reload_pymodules)  # pyright: ignore[reportOptionalMemberAccess]

        self.setWindowIcon(cast("QApplication", QApplication.instance()).windowIcon())
        self.setup_modules_tab()

    def setup_modules_tab(self):
        """Set up the modules tab UI components and layout."""
        self._setup_erf_editor_button()
        self._reorganize_modules_ui_layout()

    def _setup_erf_editor_button(self):
        """Create and configure the ERF Editor button for the modules tab."""
        self.erf_editor_button = QPushButton(tr("ERF Editor"), self)
        self.erf_editor_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.erf_editor_button.clicked.connect(self._open_module_tab_erf_editor)
        self.ui.verticalLayoutRightPanel.insertWidget(2, self.erf_editor_button)  # pyright: ignore[reportArgumentType]
        self.erf_editor_button.hide()

    def _reorganize_modules_ui_layout(self):
        """Reorganize the modules UI layout to stack buttons vertically next to the section combo."""
        # Get references to UI components
        modules_resource_list = self.ui.modulesWidget.ui
        modules_section_combo: QComboBox = modules_resource_list.sectionCombo  # type: ignore[attr-defined]
        refresh_button: QPushButton = modules_resource_list.refreshButton  # type: ignore[attr-defined]
        designer_button: QPushButton = self.ui.specialActionButton  # type: ignore[attr-defined]
        level_builder_button: QPushButton = self.ui.levelBuilderButton  # type: ignore[attr-defined]

        # Remove existing horizontal layout containing combo and refresh button
        modules_resource_list.horizontalLayout_2.removeWidget(modules_section_combo)  # type: ignore[arg-type]
        modules_resource_list.horizontalLayout_2.removeWidget(refresh_button)  # type: ignore[arg-type]
        modules_resource_list.verticalLayout.removeItem(modules_resource_list.horizontalLayout_2)  # type: ignore[arg-type]

        # Configure button size policies
        refresh_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)  # type: ignore[arg-type]
        designer_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)  # type: ignore[arg-type]
        level_builder_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)  # type: ignore[arg-type]

        # Create vertical button stack layout
        stack_button_layout = QVBoxLayout()
        stack_button_layout.setSpacing(1)
        stack_button_layout.addWidget(refresh_button)  # type: ignore[arg-type]
        stack_button_layout.addWidget(designer_button)  # type: ignore[arg-type]
        stack_button_layout.addWidget(level_builder_button)  # type: ignore[arg-type]

        # Create top layout combining section combo with button stack
        top_layout = QHBoxLayout()
        top_layout.addWidget(modules_section_combo)  # type: ignore[arg-type]
        top_layout.addLayout(stack_button_layout)

        # Insert the new top layout at the beginning of the modules tab
        self.ui.verticalLayoutModulesTab.insertLayout(0, top_layout)  # type: ignore[attributeAccessIssue]

        # Add the resource tree widget to complete the layout
        modules_resource_list.verticalLayout.addWidget(modules_resource_list.resourceTree)  # type: ignore[arg-type]

    def _setup_signals(self):
        """Set up all signal connections for the main window."""
        self._setup_core_signals()
        self._setup_widget_signals()
        self._setup_action_signals()

    def _setup_core_signals(self):
        """Set up core application signals."""
        self.ui.gameCombo.currentIndexChanged.connect(self.change_active_installation)
        self.sig_module_files_updated.connect(self.on_module_file_updated)
        self.sig_override_files_update.connect(self.on_override_file_updated)

        # File system watcher signals for auto-detecting installation folder changes
        self._file_watcher.directoryChanged.connect(self._on_watched_directory_changed)
        self._file_watcher.fileChanged.connect(self._on_watched_file_changed)

    def _setup_widget_signals(self):
        """Set up signals for resource list widgets."""
        # Core widget signals
        self.ui.coreWidget.sig_request_extract_resource.connect(self.on_extract_resources)
        self.ui.coreWidget.sig_request_refresh.connect(self.on_core_refresh)
        self.ui.coreWidget.sig_request_open_resource.connect(self.on_open_resources)

        # Modules widget signals
        self.ui.modulesWidget.sig_section_changed.connect(self.on_module_changed)
        self.ui.modulesWidget.sig_request_reload.connect(self.on_module_reload)
        self.ui.modulesWidget.sig_request_refresh.connect(self.on_module_refresh)
        self.ui.modulesWidget.sig_request_extract_resource.connect(self.on_extract_resources)
        self.ui.modulesWidget.sig_request_open_resource.connect(self.on_open_resources)
        self.sig_installation_changed.connect(self.ui.modulesWidget.set_installation)

        # Saves widget signals
        self.ui.savesWidget.sig_section_changed.connect(self.on_savepath_changed)
        self.ui.savesWidget.sig_request_reload.connect(self.on_save_reload)
        self.ui.savesWidget.sig_request_refresh.connect(self.on_save_refresh)
        self.ui.savesWidget.sig_request_extract_resource.connect(self.on_extract_resources)
        self.ui.savesWidget.sig_request_open_resource.connect(self.on_open_resources)
        self.sig_installation_changed.connect(self.ui.savesWidget.set_installation)

        # Override widget signals
        self.ui.overrideWidget.sig_section_changed.connect(self.on_override_changed)
        self.ui.overrideWidget.sig_request_reload.connect(self.on_override_reload)
        self.ui.overrideWidget.sig_request_refresh.connect(self.on_override_refresh)
        self.ui.overrideWidget.sig_request_extract_resource.connect(self.on_extract_resources)
        self.ui.overrideWidget.sig_request_open_resource.connect(self.on_open_resources)
        self.sig_installation_changed.connect(self.ui.overrideWidget.set_installation)

        # Textures widget signals
        self.ui.texturesWidget.sig_section_changed.connect(self.on_textures_changed)
        self.ui.texturesWidget.sig_request_open_resource.connect(self.on_open_resources)
        self.sig_installation_changed.connect(self.ui.texturesWidget.set_installation)

    def _setup_action_signals(self):
        """Set up signals for action buttons and UI controls."""
        # Save Editor button
        self.ui.openSaveEditorButton.clicked.connect(self.on_open_save_editor)

        # Enable/disable Open Save Editor button based on selection
        selection_model = self.ui.savesWidget.ui.resourceTree.selectionModel()
        assert selection_model is not None, "Selection model not found in saves widget"
        selection_model.selectionChanged.connect(self.on_save_selection_changed)

        # Tab change signal
        self.ui.resourceTabs.currentChanged.connect(self.on_tab_changed)

        # Action button signals
        self.ui.specialActionButton.clicked.connect(self._open_module_designer_action)
        self.ui.levelBuilderButton.clicked.connect(self._open_indoor_map_builder_action)

    def _open_module_designer_action(self):
        """Open the module designer for the currently selected module."""
        assert self.active is not None
        module_data = self.ui.modulesWidget.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        module_path: Path | None = None
        if module_data:
            module_path = self.active.module_path() / Path(str(module_data))

        try:
            designer_window = ModuleDesigner(  # pyright: ignore[call-arg]
                None,
                self.active,
                mod_filepath=module_path,
            )
        except TypeError as exc:
            RobustLogger().warning(f"ModuleDesigner signature mismatch: {exc}. Falling back without module path.")
            designer_window = ModuleDesigner(None, self.active)
            if module_path is not None:
                QTimer.singleShot(33, lambda: designer_window.open_module(module_path))

        designer_window.setWindowIcon(cast("QApplication", QApplication.instance()).windowIcon())
        add_window(designer_window)

    def _open_indoor_map_builder_action(self):
        """Open the Indoor Map Builder with the currently selected module."""
        assert self.active is not None
        module_data = self.ui.modulesWidget.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        if not module_data:
            QMessageBox.warning(
                self,
                tr("No Module Selected"),
                tr("Please select a module from the Modules tab before opening the Level Builder."),
            )
            return

        # Use the selected module file name and strip extension robustly.
        module_name = PurePath(str(module_data)).stem

        builder = IndoorMapBuilder(None, self.active)
        builder.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        builder.show()
        builder.activateWindow()
        add_window(builder)

        # Load the selected module (use QTimer to ensure window is fully initialized)
        QTimer.singleShot(33, lambda: builder.load_module_from_name(module_name))

        self.ui.overrideWidget.sig_section_changed.connect(self.on_override_changed)
        self.ui.overrideWidget.sig_request_reload.connect(self.on_override_reload)
        self.ui.overrideWidget.sig_request_refresh.connect(self.on_override_refresh)
        self.ui.overrideWidget.sig_request_extract_resource.connect(self.on_extract_resources)
        self.ui.overrideWidget.sig_request_open_resource.connect(self.on_open_resources)
        self.sig_installation_changed.connect(self.ui.overrideWidget.set_installation)

        self.ui.texturesWidget.sig_section_changed.connect(self.on_textures_changed)
        self.ui.texturesWidget.sig_request_open_resource.connect(self.on_open_resources)
        self.sig_installation_changed.connect(self.ui.texturesWidget.set_installation)

        def extract_resources():
            self.on_extract_resources(
                self.get_active_resource_widget().selected_resources(),
                resource_widget=self.get_active_resource_widget(),
            )

        self.ui.extractButton.clicked.connect(extract_resources)
        self.ui.openButton.clicked.connect(lambda checked=False: self.get_active_resource_widget().on_resource_double_clicked(None))

        self.ui.openAction.triggered.connect(self.open_from_file)
        self.ui.actionSettings.triggered.connect(self.open_settings_dialog)
        self.ui.actionExit.triggered.connect(lambda *args: self.close() and None or None)

        self.ui.actionNewTLK.triggered.connect(lambda: add_window(TLKEditor(self, self.active)))
        self.ui.actionNewDLG.triggered.connect(lambda: add_window(DLGEditor(self, self.active)))
        self.ui.actionNewNSS.triggered.connect(lambda: add_window(NSSEditor(self, self.active)))
        self.ui.actionNewUTC.triggered.connect(lambda: add_window(UTCEditor(self, self.active)))  # type: ignore[arg-type]
        self.ui.actionNewUTP.triggered.connect(lambda: add_window(UTPEditor(self, self.active)))  # type: ignore[arg-type]
        self.ui.actionNewUTD.triggered.connect(lambda: add_window(UTDEditor(self, self.active)))  # type: ignore[arg-type]
        self.ui.actionNewUTI.triggered.connect(lambda: add_window(UTIEditor(self, self.active)))  # type: ignore[arg-type]
        self.ui.actionNewUTT.triggered.connect(lambda: add_window(UTTEditor(self, self.active)))
        self.ui.actionNewUTM.triggered.connect(lambda: add_window(UTMEditor(self, self.active)))
        self.ui.actionNewUTW.triggered.connect(lambda: add_window(UTWEditor(self, self.active)))
        self.ui.actionNewUTE.triggered.connect(lambda: add_window(UTEEditor(self, self.active)))
        self.ui.actionNewUTS.triggered.connect(lambda: add_window(UTSEditor(self, self.active)))  # type: ignore[arg-type]
        self.ui.actionNewGFF.triggered.connect(lambda: add_window(GFFEditor(self, self.active)))
        self.ui.actionNewERF.triggered.connect(lambda: add_window(ERFEditor(self, self.active)))
        self.ui.actionNewTXT.triggered.connect(lambda: add_window(TXTEditor(self, self.active)))
        self.ui.actionNewSSF.triggered.connect(lambda: add_window(SSFEditor(self, self.active)))
        self.ui.actionCloneModule.triggered.connect(lambda: add_window(CloneModuleDialog(self, self.active, self.installations)))  # type: ignore[arg-type]

        self.ui.actionModuleDesigner.triggered.connect(self.open_module_designer)
        self.ui.actionEditTLK.triggered.connect(self.open_active_talktable)
        self.ui.actionEditJRL.triggered.connect(self.open_active_journal)
        self.ui.actionFileSearch.triggered.connect(self.open_file_search_dialog)
        self.ui.actionIndoorMapBuilder.triggered.connect(self.open_indoor_map_builder)
        self.ui.actionKotorDiff.triggered.connect(self.open_kotordiff)
        self.ui.actionTSLPatchDataEditor.triggered.connect(self.open_tslpatchdata_editor)

        self.ui.actionInstructions.triggered.connect(self.open_instructions_window)
        self.ui.actionHelpUpdates.triggered.connect(self.update_manager.check_for_updates)
        self.ui.actionHelpAbout.triggered.connect(self.open_about_dialog)
        self.ui.actionDiscordDeadlyStream.triggered.connect(lambda: open_link("https://discord.com/invite/bRWyshn"))
        self.ui.actionDiscordKotOR.triggered.connect(lambda: open_link("http://discord.gg/kotor"))
        self.ui.actionDiscordHolocronToolset.triggered.connect(lambda: open_link("https://discord.gg/3ME278a9tQ"))

        # Setup Theme button to open theme selector dialog
        # Replace menuTheme with a button action
        if self.ui.menuTheme is not None:
            # Clear existing menu items
            self.ui.menuTheme.clear()
            # Create and add action that opens dialog
            theme_action = QAction(tr("Theme..."), self)
            theme_action.triggered.connect(self._open_theme_dialog)
            self.ui.menuTheme.addAction(theme_action)

        self.ui.menuRecentFiles.aboutToShow.connect(self.populate_recent_files_menu)

        # Setup Language menu
        self._setup_language_menu()

        # Setup View menu - Legacy Layout toggle
        self._use_legacy_layout: bool = self.settings.value("useLegacyLayout", False, type=bool)
        self.ui.actionLegacyLayout.setChecked(self._use_legacy_layout)
        self.ui.actionLegacyLayout.triggered.connect(self._on_legacy_layout_toggled)

        # Initialize view switching (will be set up after UI is ready)
        self._fs_core_widget: ResourceFileSystemWidget | None = None
        self._fs_modules_widget: ResourceFileSystemWidget | None = None
        self._fs_override_widget: ResourceFileSystemWidget | None = None
        self._fs_saves_widget: ResourceFileSystemWidget | None = None

    @Slot(bool)
    def _open_theme_dialog(
        self,
        checked: bool = False,  # pyright: ignore[reportUnusedParameter]
    ):
        """Open the theme selector dialog (non-blocking).

        Args:
        ----
            checked: Whether the action was checked (from triggered signal, ignored).
        """
        if self._theme_dialog is None or not self._theme_dialog.isVisible():
            current_theme = self.settings.selectedTheme or "sourcegraph-dark"
            current_style = self.settings.selectedStyle or "Fusion"
            available_themes = sorted(set(self.theme_manager.get_available_themes()))
            available_styles = list(self.theme_manager.get_default_styles())

            self._theme_dialog = ThemeSelectorDialog(
                parent=self,
                available_themes=available_themes,
                available_styles=available_styles,
                current_theme=current_theme,
                current_style=current_style,
            )

            # Connect signals to existing theme change logic
            self._theme_dialog.theme_changed.connect(self._on_theme_changed)
            self._theme_dialog.style_changed.connect(self._on_style_changed)

            # Make dialog non-blocking
            self._theme_dialog.show()
            self._theme_dialog.raise_()
            self._theme_dialog.activateWindow()
        else:
            # If dialog is already open, bring it to front
            self._theme_dialog.raise_()
            self._theme_dialog.activateWindow()

    def _on_theme_changed(
        self,
        theme_name: str,
    ):
        """Handle theme change from dialog."""
        self.theme_manager.change_theme(theme_name)
        self.settings.selectedTheme = theme_name
        # Update dialog selection if it's still open
        if self._theme_dialog and self._theme_dialog.isVisible():
            self._theme_dialog.update_current_selection(theme_name=theme_name, style_name=None)

    def _on_style_changed(
        self,
        style_name: str,
    ):
        """Handle style change from dialog."""
        self.theme_manager.change_style(style_name)
        self.settings.selectedStyle = style_name
        # Update dialog selection if it's still open
        if self._theme_dialog and self._theme_dialog.isVisible():
            self._theme_dialog.update_current_selection(theme_name=None, style_name=style_name)

    def _setup_language_menu(self):
        """Set up the Language menu with all available languages."""
        from toolset.gui.common.localization import ToolsetLanguage

        # Initialize language system from settings
        current_language_id = self.settings.selectedLanguage
        try:
            current_language = ToolsetLanguage(current_language_id)
        except ValueError:
            current_language = ToolsetLanguage.ENGLISH

        # Set the global language
        set_language(current_language)

        # Add language actions to the menu
        for language in ToolsetLanguage:

            def make_language_handler(lang=language):
                def change_language(*args):
                    self.settings.selectedLanguage = lang.value
                    set_language(lang)
                    self._update_language_menu_checkmarks(lang)
                    self.apply_translations()

                return change_language

            display_name = language.get_display_name()
            language_action: QAction | None = self.ui.menuLanguage.addAction(display_name)
            assert language_action is not None
            language_action.setCheckable(True)
            language_action.triggered.connect(make_language_handler())
            self._language_actions[language.value] = language_action

            # Mark current language as checked
            if language == current_language:
                language_action.setChecked(True)

        # Apply translations after setting up menu
        self.apply_translations()

    def _setup_view_switching(self):
        """Set up view switching between filesystem view and legacy layout."""
        # Apply initial view mode
        if self.active is not None:
            self._apply_view_mode()

    @Slot(bool)
    def _on_legacy_layout_toggled(self, checked: bool):
        """Handle Legacy Layout menu action toggle.

        Args:
        ----
            checked: Whether legacy layout is enabled
        """
        self._use_legacy_layout = checked
        self.settings.setValue("useLegacyLayout", checked)
        self._apply_view_mode()

    def _apply_view_mode(self):
        """Apply the current view mode (filesystem or legacy)."""
        if self._use_legacy_layout:
            self._switch_to_legacy_view()
        else:
            self._switch_to_filesystem_view()

    def _switch_to_legacy_view(self):
        """Switch to legacy ResourceList view."""
        # Hide filesystem widgets and show legacy widgets
        if self._fs_core_widget is not None:
            self._fs_core_widget.hide()
        self.ui.coreWidget.show()

        if self._fs_modules_widget is not None:
            self._fs_modules_widget.hide()
        self.ui.modulesWidget.show()

        if self._fs_override_widget is not None:
            self._fs_override_widget.hide()
        self.ui.overrideWidget.show()

        if self._fs_saves_widget is not None:
            self._fs_saves_widget.hide()
        self.ui.savesWidget.show()

    def _switch_to_filesystem_view(self):
        """Switch to filesystem view with archive-as-folder support."""
        if self.active is None:
            return

        # Store references to legacy widgets
        legacy_core = self.ui.coreWidget
        legacy_modules = self.ui.modulesWidget
        legacy_override = self.ui.overrideWidget
        legacy_saves = self.ui.savesWidget

        # Create filesystem widgets if they don't exist
        if self._fs_core_widget is None:
            # Get the parent widget (the tab container)
            core_parent = legacy_core.parent()
            if core_parent is not None and isinstance(core_parent, QWidget):
                self._fs_core_widget = ResourceFileSystemWidget(core_parent)
                # Insert into the same layout position as legacy widget
                layout = core_parent.layout()
                if layout is not None and isinstance(layout, (QBoxLayout, QStackedLayout)):
                    # Find the index of the legacy widget
                    for i in range(layout.count()):
                        item = layout.itemAt(i)
                        if item and item.widget() == legacy_core:
                            layout.insertWidget(i, self._fs_core_widget)
                            break
                # Set root path to installation path
                install_path = self.active.path()
                if install_path.exists():
                    self._fs_core_widget.setRootPath(install_path)

        if self._fs_modules_widget is None:
            modules_parent = legacy_modules.parent()
            if modules_parent is not None:
                self._fs_modules_widget = ResourceFileSystemWidget(modules_parent)
                layout = modules_parent.layout()
                if layout is not None:
                    for i in range(layout.count()):
                        item = layout.itemAt(i)
                        if item and item.widget() == legacy_modules:
                            layout.insertWidget(i, self._fs_modules_widget)
                            break
                # Set root path to modules directory
                module_path = self.active.module_path()
                if module_path.exists():
                    self._fs_modules_widget.setRootPath(module_path)

        if self._fs_override_widget is None:
            override_parent = legacy_override.parent()
            if override_parent is not None:
                self._fs_override_widget = ResourceFileSystemWidget(override_parent)
                layout = override_parent.layout()
                if layout is not None:
                    for i in range(layout.count()):
                        item = layout.itemAt(i)
                        if item and item.widget() == legacy_override:
                            layout.insertWidget(i, self._fs_override_widget)
                            break
                # Set root path to override directory
                override_path = self.active.override_path()
                if override_path.exists():
                    self._fs_override_widget.setRootPath(override_path)

        if self._fs_saves_widget is None:
            saves_parent = legacy_saves.parent()
            if saves_parent is not None:
                self._fs_saves_widget = ResourceFileSystemWidget(saves_parent)
                layout = saves_parent.layout()
                if layout is not None:
                    for i in range(layout.count()):
                        item = layout.itemAt(i)
                        if item and item.widget() == legacy_saves:
                            layout.insertWidget(i, self._fs_saves_widget)
                            break
                # Set root path to first save location, or installation path if no saves
                save_locations = self.active.save_locations()
                if save_locations and len(save_locations) > 0 and save_locations[0].exists() and save_locations[0].is_dir():
                    self._fs_saves_widget.setRootPath(save_locations[0])
                else:
                    install_path = self.active.path()
                    if install_path.exists():
                        self._fs_saves_widget.setRootPath(install_path)

        # Show filesystem widgets and hide legacy widgets
        if self._fs_core_widget is not None:
            self._fs_core_widget.show()
        legacy_core.hide()

        if self._fs_modules_widget is not None:
            self._fs_modules_widget.show()
        legacy_modules.hide()

        if self._fs_override_widget is not None:
            self._fs_override_widget.show()
        legacy_override.hide()

        if self._fs_saves_widget is not None:
            self._fs_saves_widget.show()
        legacy_saves.hide()

    def _update_language_menu_checkmarks(
        self,
        language: ToolsetLanguage,
    ):
        """Update checkmarks in the language menu based on current selection."""
        # Uncheck all language actions
        for action in self._language_actions.values():
            action.setChecked(False)

        # Check the selected language
        if language.value in self._language_actions:
            self._language_actions[language.value].setChecked(True)

    def apply_translations(self):
        """Apply translations to all UI strings in the main window."""
        # Translate menu titles
        self.ui.menuFile.setTitle(tr("File"))
        self.ui.menuEdit.setTitle(tr("Edit"))
        self.ui.menuView.setTitle(tr("View"))
        self.ui.menuTools.setTitle(tr("Tools"))
        self.ui.menuTheme.setTitle(tr("Theme"))
        self.ui.menuLanguage.setTitle(tr("Language"))
        self.ui.menuHelp.setTitle(tr("Help"))
        self.ui.menuNew.setTitle(tr("New"))
        self.ui.menuRecentFiles.setTitle(tr("Recent Files"))
        self.ui.menuDiscord.setTitle(tr("Discord"))

        # Translate menu actions
        self.ui.actionExit.setText(tr("Exit"))
        self.ui.actionSettings.setText(tr("Settings"))
        self.ui.actionHelpAbout.setText(tr("About"))
        self.ui.actionInstructions.setText(tr("Instructions"))
        self.ui.actionHelpUpdates.setText(tr("Check For Updates"))
        self.ui.actionEditTLK.setText(tr("Edit Talk Table"))
        self.ui.actionEditJRL.setText(tr("Edit Journal"))
        self.ui.actionModuleDesigner.setText(tr("Module Designer"))
        self.ui.actionIndoorMapBuilder.setText(tr("Indoor Map Builder"))
        self.ui.actionKotorDiff.setText(tr("KotorDiff"))
        self.ui.actionTSLPatchDataEditor.setText(tr("TSLPatchData Editor"))
        self.ui.actionFileSearch.setText(tr("File Search"))
        self.ui.actionCloneModule.setText(tr("Clone Module"))
        self.ui.actionLegacyLayout.setText(tr("Legacy Layout"))
        self.ui.actionDiscordHolocronToolset.setText(tr("Holocron Toolset"))
        self.ui.actionDiscordKotOR.setText(tr("KOTOR Community Portal"))
        self.ui.actionDiscordDeadlyStream.setText(tr("Deadly Stream"))

        # Translate new resource actions
        self.ui.actionNewDLG.setText(tr("Dialog"))
        self.ui.actionNewUTC.setText(tr("Creature"))
        self.ui.actionNewUTI.setText(tr("Item"))
        self.ui.actionNewUTD.setText(tr("Door"))
        self.ui.actionNewUTP.setText(tr("Placeable"))
        self.ui.actionNewUTM.setText(tr("Merchant"))
        self.ui.actionNewUTE.setText(tr("Encounter"))
        self.ui.actionNewUTT.setText(tr("Trigger"))
        self.ui.actionNewUTW.setText(tr("Waypoint"))
        self.ui.actionNewUTS.setText(tr("Sound"))
        self.ui.actionNewNSS.setText(tr("Script"))
        self.ui.actionNewTLK.setText(tr("TalkTable"))
        self.ui.actionNewGFF.setText(tr("GFF"))
        self.ui.actionNewERF.setText(tr("ERF"))
        self.ui.actionNewTXT.setText(tr("TXT"))
        self.ui.actionNewSSF.setText(tr("SSF"))

        # Translate tab titles
        self.ui.resourceTabs.setTabText(0, tr("Core"))
        self.ui.resourceTabs.setTabText(1, tr("Saves"))
        self.ui.resourceTabs.setTabText(2, tr("Modules"))
        self.ui.resourceTabs.setTabText(3, tr("Override"))
        self.ui.resourceTabs.setTabText(4, tr("Textures"))

        # Translate buttons
        self.ui.openButton.setText(tr("Open Selected"))
        self.ui.extractButton.setText(tr("Extract Selected"))
        self.ui.openSaveEditorButton.setText(tr("Open Save Editor"))
        self.ui.specialActionButton.setText(tr("Designer"))

        # Translate tooltips
        self.ui.openSaveEditorButton.setToolTip(tr("Open the selected save in the Save Editor"))

        # Translate group boxes
        self.ui.tpcGroup_2.setTitle(tr("TPC"))
        self.ui.mdlGroup_2.setTitle(tr("MDL"))

        # Translate checkboxes
        self.ui.tpcDecompileCheckbox.setText(tr("Decompile"))
        self.ui.tpcTxiCheckbox.setText(tr("Extract TXI"))
        self.ui.mdlDecompileCheckbox.setText(tr("Decompile"))
        self.ui.mdlDecompileCheckbox.setToolTip(tr("Decompile MDL to ASCII format"))
        self.ui.mdlTexturesCheckbox.setText(tr("Extract Textures"))

        # Update window title
        self.setWindowTitle(f"{tr('Holocron Toolset')} ({qtpy.API_NAME})")

    def on_open_resources(
        self,
        resources: list[FileResource],
        use_specialized_editor: bool | None = None,
        resource_widget: ResourceList | TextureList | None = None,
    ):
        assert self.active is not None
        for resource in resources:
            _filepath, _editor = open_resource_editor(resource, self.active, self, gff_specialized=use_specialized_editor)
        if resources:
            return
        if not isinstance(resource_widget, ResourceList):
            return
        filename = str(resource_widget.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole))
        if not filename:
            return
        erf_filepath = self.active.module_path() / filename
        if not erf_filepath.is_file():
            return
        res_ident = ResourceIdentifier.from_path(erf_filepath)
        if not res_ident.restype:
            return
        erf_resource = FileResource(res_ident.resname, res_ident.restype, os.path.getsize(erf_filepath), 0x0, erf_filepath)  # noqa: PTH202
        _filepath, _editor = open_resource_editor(erf_resource, self.active, self, gff_specialized=use_specialized_editor)

    def populate_recent_files_menu(
        self,
        _checked: bool | None = None,
    ):
        recent_files_setting: list[str] = self.settings.recentFiles
        recent_files: list[Path] = [Path(file) for file in recent_files_setting]
        self.ui.menuRecentFiles.clear()
        for file in recent_files:
            action = QAction(file.name, self)
            action.setData(file)
            action.triggered.connect(lambda *args, a=action: self.open_recent_file(action=a))
            self.ui.menuRecentFiles.addAction(action)  # type: ignore[arg-type]

    def open_recent_file(
        self,
        *args,
        action: QAction,
    ):
        file = action.data()
        if not file or not isinstance(file, Path):
            return
        resource = FileResource.from_path(file)
        open_resource_editor(resource, self.active, self)

    # region Signal callbacks
    def on_core_refresh(self):
        self.refresh_core_list(reload=True)

    @Slot(str)
    def on_module_changed(
        self,
        new_module_file: str,
    ):
        self.on_module_reload(new_module_file)

    @Slot(str)
    def on_module_reload(
        self,
        module_file: str,
    ):
        assert self.active is not None, "No active installation selected"
        if not module_file or not module_file.strip():
            return
        RobustLogger().info(f"Reloading module '{module_file}'")
        resources: list[FileResource] = self.active.module_resources(module_file)
        module_file_name = PurePath(module_file).name
        if self.settings.joinRIMsTogether and ((is_rim_file(module_file) or is_erf_file(module_file)) and not module_file_name.lower().endswith(("_s.rim", "_dlg.erf"))):
            resources.extend(self.active.module_resources(f"{PurePath(module_file).stem}_s.rim"))
            if self.active.game().is_k2():
                resources.extend(self.active.module_resources(f"{PurePath(module_file).stem}_dlg.erf"))

        RobustLogger().info(f"Setting {len(resources)} resources for module '{module_file}'")
        self.active.reload_module(module_file)
        self.ui.modulesWidget.set_resources(resources)

    @Slot(str, str)
    def on_module_file_updated(
        self,
        changed_file: str,
        event_type: str,
    ):
        assert self.active is not None, "No active installation selected"
        if event_type == "deleted":
            self.refresh_module_list()
        else:
            self.active.reload_module(changed_file)
            if self.ui.modulesWidget.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole) == changed_file:
                self.on_module_reload(changed_file)

    def on_module_refresh(self):  # noqa: FBT001, FBT002
        self.refresh_module_list()

    @Slot(str)
    def on_savepath_changed(
        self,
        new_save_dir: str,
    ):
        assert self.active is not None, "No active installation selected"
        self.ui.savesWidget.modules_model.invisibleRootItem().removeRows(0, self.ui.savesWidget.modules_model.rowCount())  # pyright: ignore[reportOptionalMemberAccess]
        new_save_dir_path = Path(new_save_dir)
        if new_save_dir_path not in self.active.saves:
            self.active.load_saves()
        if new_save_dir_path not in self.active.saves:
            return
        for save_path, resource_list in self.active.saves[new_save_dir_path].items():
            save_path_item = QStandardItem(str(save_path.relative_to(save_path.parent.parent)))

            self.ui.savesWidget.modules_model.invisibleRootItem().appendRow(save_path_item)  # pyright: ignore[reportOptionalMemberAccess]
            category_items_under_save_path: dict[str, QStandardItem] = {}
            for resource in resource_list:
                category: str = resource.restype().category
                if category not in category_items_under_save_path:
                    category_item = QStandardItem(category)
                    category_item.setSelectable(False)
                    unused_item = QStandardItem("")
                    unused_item.setSelectable(False)
                    save_path_item.appendRow([category_item, unused_item])
                    category_items_under_save_path[category] = category_item
                category_item = category_items_under_save_path[category]

                found_resource = False
                for i in range(category_item.rowCount()):
                    item = category_item.child(i)
                    if item is not None and isinstance(item, ResourceStandardItem) and item.resource == resource:
                        item.resource = resource
                        found_resource = True
                        break
                if not found_resource:
                    category_item.appendRow(
                        [
                            ResourceStandardItem(resource.resname(), resource=resource),
                            QStandardItem(resource.restype().extension.upper()),
                        ]
                    )

    def on_save_reload(
        self,
        save_dir: str,
    ):
        RobustLogger().info(f"Reloading save directory '{save_dir}'")
        self.on_savepath_changed(save_dir)

    def on_save_refresh(self):
        RobustLogger().info("Refreshing save list")
        self.refresh_saves_list()

    @Slot()
    def on_save_selection_changed(self):
        """Enable/disable Open Save Editor button based on selection."""
        has_selection: bool = len(self.ui.savesWidget.ui.resourceTree.selectedIndexes()) > 0
        self.ui.openSaveEditorButton.setEnabled(has_selection)

    @Slot(bool)
    def on_open_save_editor(
        self,
        checked: bool = False,  # pyright: ignore[reportUnusedParameter]
    ):
        """Open the Save Editor for the selected save.

        Args:
        ----
            checked: Whether the button was checked (from clicked signal, ignored).
        """
        try:
            if self.active is None:
                RobustLogger().warning("Cannot open save editor: no active installation")
                return

            # Safely get the saves widget and tree
            saves_widget: ResourceList = self.ui.savesWidget
            tree_view: RobustTreeView = saves_widget.ui.resourceTree

            # Get selected save folder
            selected_indexes: list[QModelIndex] = tree_view.selectedIndexes()
            if not selected_indexes:
                RobustLogger().debug("No selected indexes in saves tree")
                return

            # Get the top-level save folder item
            model: ResourceModel = saves_widget.modules_model
            proxy_model: QStandardItemModel | QAbstractItemModel | None = tree_view.model()
            if proxy_model is None or not isinstance(proxy_model, QSortFilterProxyModel):
                RobustLogger().error(f"Proxy model not found or not a QSortFilterProxyModel: {proxy_model.__class__.__name__}")
                return

            for index in selected_indexes:
                source_index: QModelIndex = proxy_model.mapToSource(index)
                item: QStandardItem | None = None
                if source_index.isValid():
                    item = model.itemFromIndex(source_index)

                if item is None:
                    continue

                # Navigate up to find the save folder item (top-level item)
                while item and item.parent():
                    item = item.parent()

                if item is not None:
                    save_name = item.text()
                    RobustLogger().debug(f"Looking for save folder: {save_name}")

                    # Get current save location from combo box
                    current_save_location_str: str | None = saves_widget.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
                    if not current_save_location_str:
                        RobustLogger().warning("No save location selected")
                        continue

                    current_save_location = Path(current_save_location_str)

                    # Find the save path
                    save_paths: dict[Path, list[FileResource]] = self.active.saves.get(current_save_location, {})
                    for save_path in save_paths:
                        # Match on the folder name (last part of path)
                        if save_path.name == save_name or save_name in str(save_path):
                            RobustLogger().info(f"Opening save editor for: {save_path}")
                            self.open_save_editor_for_path(save_path)
                            return  # Exit after opening

                    RobustLogger().warning(f"Could not find save path for: {save_name}")
                    break
        except Exception as e:
            RobustLogger().exception(f"Error opening save editor: {e.__class__.__name__}: {e}")

    def open_save_editor_for_path(
        self,
        save_path: Path,
    ):
        """Open the Save Editor for a specific save path."""
        from toolset.gui.editors.savegame import SaveGameEditor

        try:
            # Create and show the save editor
            editor = SaveGameEditor(self, self.active)

            # Load the save
            savegame_sav = save_path / "SAVEGAME.sav"
            if savegame_sav.exists():
                with open(savegame_sav, "rb") as f:
                    data = f.read()
                editor.load(str(save_path), save_path.name, ResourceType.SAV, data)
            else:
                # If SAVEGAME.sav doesn't exist, load the folder directly
                editor.load(str(save_path), save_path.name, ResourceType.SAV, b"")

            editor.show()

        except Exception as e:
            QMessageBox.critical(
                self,
                tr("Error Opening Save Editor"),
                trf("Failed to open save editor:\n{error}", error=str(e)),
            )
            RobustLogger().exception(f"Failed to open save editor for '{save_path}'")

    def on_override_file_updated(
        self,
        changed_file: str,
        event_type: str,
    ):
        if event_type == "deleted":
            self.refresh_override_list(reload=True)
        else:
            self.on_override_reload(changed_file)

    def on_override_changed(
        self,
        new_directory: str,
    ):
        assert self.active is not None, "No active installation selected"
        self.ui.overrideWidget.set_resources(self.active.override_resources(new_directory))

    def on_override_reload(
        self,
        file_or_folder: str,
    ):
        assert self.active is not None, "No active installation selected"
        override_path = self.active.override_path()

        file_or_folder_path = override_path.joinpath(file_or_folder)
        if file_or_folder_path.is_file():
            rel_folderpath = file_or_folder_path.parent.relative_to(self.active.override_path())
            self.active.reload_override_file(file_or_folder_path)
        else:
            rel_folderpath = file_or_folder_path.relative_to(self.active.override_path())
            self.active.load_override(str(rel_folderpath))
        self.ui.overrideWidget.set_resources(self.active.override_resources(str(rel_folderpath) if rel_folderpath.name else None))

    def on_override_refresh(self):
        self.refresh_override_list(reload=True)

    def on_textures_changed(
        self,
        texturepackName: str,
    ):
        assert self.active is not None, "No active installation selected"
        self.ui.texturesWidget.set_resources(self.active.texturepack_resources(texturepackName))

    @Slot(int)
    def change_active_installation(self, index: int):
        """Change the active game installation based on combo box selection.

        Args:
        ----
            index: The index of the selected installation in the combo box
        """
        if index < 0:  # self.ui.gameCombo.clear() will call this function with -1
            return

        prev_index: int = self.previous_game_combo_index
        # Only set index if it's different to avoid unnecessary signal emission
        current_index = self.ui.gameCombo.currentIndex()
        if current_index != index:
            self.ui.gameCombo.setCurrentIndex(index)

        if index == 0:
            self.unset_installation()
            self.previous_game_combo_index = 0
            return

        # Get installation details from settings
        name: str = self.ui.gameCombo.itemText(index)
        installation_config = self.settings.installations()[name]
        path: str = installation_config.path.strip()
        tsl: bool = installation_config.tsl

        # Validate and prompt for installation path if needed
        path = self._validate_installation_path(name, path, tsl, prev_index)
        if not path:
            return

        # Enable resource tabs for the selected installation
        self.ui.resourceTabs.setEnabled(True)

        # Load or create the installation
        self._load_installation(name, path, tsl, prev_index)

    def _validate_installation_path(self, name: str, path: str, tsl: bool, prev_index: int) -> str:
        """Validate the installation path and prompt user if needed.

        Args:
        ----
            name: Installation name
            path: Current path from settings
            tsl: Whether this is TSL installation
            prev_index: Previous combo box index for fallback

        Returns:
        -------
            Valid installation path or empty string if cancelled
        """
        # Check if path is valid
        if not path or not path.strip() or not Path(path).exists() or not Path(path).is_dir():
            if path and path.strip():
                QMessageBox(QMessageBox.Icon.Warning, trf("Installation '{path}' not found", path=path), tr("Select another path now.")).exec()

            # Prompt user for installation directory
            default_dir = "Knights of the Old Republic II" if tsl else "swkotor"
            path = QFileDialog.getExistingDirectory(self, trf("Select the game directory for {name}", name=name), default_dir)

        # Return to previous selection if no path provided
        if not path or not path.strip():
            self.ui.gameCombo.setCurrentIndex(prev_index)
            return ""

        return path

    def _load_installation(
        self,
        name: str,
        path: str,
        tsl: bool,
        prev_index: int,
    ) -> None:
        """Load or create the installation instance."""

        def create_installation_task(
            loader: AsyncLoader | None = None,
        ) -> HTInstallation:
            """Creates and returns a new HTInstallation instance.

            Returns:
            -------
                HTInstallation: The newly created installation instance
            """
            if loader is not None and loader._realtime_progress:  # noqa: SLF001
                return HTInstallation(
                    Path(path),
                    name,
                    tsl=tsl,
                    progress_callback=loader.progress_callback_api,
                )
            return HTInstallation(Path(path), name, tsl=tsl)

        # Get or create installation instance
        active: HTInstallation | None = self.installations.get(name)
        if active is None:

            def create_installation_with_loader() -> HTInstallation:
                return create_installation_task(loader=installation_loader)

            installation_loader: AsyncLoader = AsyncLoader(
                self,
                "Creating installation...",
                create_installation_with_loader,
                "Failed to create installation",
                realtime_progress=True,
            )
            if not installation_loader.exec():
                RobustLogger().error("Failed to create installation")
                self.ui.gameCombo.setCurrentIndex(prev_index)
                return
            self.active = installation_loader.value
            assert self.active is not None, "Active installation should not be None here after loading"
            self.installations[name] = self.active
        else:
            self.active = active

        # Prepare resource lists for the installation
        self._prepare_installation_resources(prev_index)

    def _prepare_installation_resources(
        self,
        prev_index: int,
    ) -> None:
        """Prepare and initialize all resource lists for the active installation."""

        def prepare_task(loader: AsyncLoader | None = None) -> tuple[list[QStandardItem] | None, ...]:
            """Prepare resource lists for modules, overrides, and textures."""
            return (
                self._get_modules_list(reload=False),
                self._get_override_list(reload=False),
                self._get_texture_pack_list(),
            )

        prepare_loader = AsyncLoader(
            self,
            "Preparing resources...",
            prepare_task,
            "Failed to prepare installation resources",
            realtime_progress=True,
        )
        if not prepare_loader.exec():
            RobustLogger().error("Failed to prepare installation resources")
            self.ui.gameCombo.setCurrentIndex(prev_index)
            return

        assert prepare_loader.value is not None
        assert self.active is not None

        # Initialize UI with prepared resource lists
        try:
            module_items, override_items, texture_items = prepare_loader.value
            assert module_items is not None, "Module items should not be None"
            assert override_items is not None, "Override items should not be None"
            assert texture_items is not None, "Texture items should not be None"

            self.ui.modulesWidget.set_sections(module_items)
            self.ui.overrideWidget.set_sections(override_items)
            self.ui.overrideWidget.ui.sectionCombo.setVisible(self.active.tsl)
            self.ui.overrideWidget.ui.refreshButton.setVisible(self.active.tsl)
            self.ui.texturesWidget.set_sections(texture_items)

            self.refresh_core_list(reload=False)
            self.refresh_saves_list(reload=False)

        except Exception as e:  # noqa: BLE001
            RobustLogger().exception("Failed to initialize the installation")
            QMessageBox(
                QMessageBox.Icon.Critical,
                "An unexpected error occurred initializing the installation.",
                f"Failed to initialize the installation {self.active.name}<br><br>{e}",
            ).exec()
            self.unset_installation()
            self.previous_game_combo_index = 0
            return

        # Finalize installation setup
        self._finalize_installation_setup()

    def _finalize_installation_setup(self):
        """Finalize the installation setup after successful loading."""
        assert self.active is not None, "Active installation should not be None here after loading"

        self.update_menus()
        RobustLogger().info(f"Successfully loaded installation: {self.active.name}")

        # Update settings and cache
        name = self.active.name
        self.settings.installations()[name].path = str(self.active.path())
        self.installations[name] = self.active

        # Show and activate window
        self.show()
        self.activateWindow()

        # Update UI state
        self.previous_game_combo_index = self.ui.gameCombo.currentIndex()

        # Emit installation changed signal
        self.sig_installation_changed.emit(self.active)

        # Set up file system watcher for auto-detecting changes
        self._setup_file_watcher()

        # Apply current view mode
        self._apply_view_mode()

    # FileSearcher/FileResults
    @Slot(list, HTInstallation)
    def handle_search_completed(
        self,
        results_list: list[FileResource],
        searched_installations: HTInstallation,
    ):
        """Event callback when the file searcher has completed its search."""
        results_dialog = FileResults(self, results_list, searched_installations)
        results_dialog.sig_searchresults_selected.connect(self.handle_results_selection)
        results_dialog.show()
        add_window(results_dialog)

    @Slot(FileResource)
    def handle_results_selection(
        self,
        selection: FileResource,
    ):
        assert self.active is not None
        # Open relevant tab then select resource in the tree
        if os.path.commonpath([selection.filepath(), self.active.module_path()]) == str(self.active.module_path()):
            self.ui.resourceTabs.setCurrentIndex(1)
            self.select_resource(self.ui.modulesWidget, selection)
        elif os.path.commonpath([selection.filepath(), self.active.override_path()]) == str(self.active.override_path()):
            self.ui.resourceTabs.setCurrentIndex(2)
            self.select_resource(self.ui.overrideWidget, selection)
        elif is_bif_file(selection.filepath().name):
            self.select_resource(self.ui.coreWidget, selection)

    # endregion

    # region Events
    def showEvent(
        self,
        event: QShowEvent | None = None,
    ) -> None:
        """Called when the window is shown."""
        super().showEvent(event)

    def closeEvent(
        self,
        e: QCloseEvent | None,  # pylint: disable=unused-argument  # pyright: ignore[reportIncompatibleMethodOverride]
    ):
        instance: QCoreApplication | None = QCoreApplication.instance()
        if instance is None:
            sys.exit()
        else:
            instance.quit()

    def mouseMoveEvent(
        self,
        event: QMouseEvent,  # pyright: ignore[reportIncompatibleMethodOverride]
    ):
        if event.buttons() == Qt.MouseButton.LeftButton:
            if self._mouse_move_pos is None:
                return
            globalPos = (
                event.globalPos()  # pyright: ignore[reportAttributeAccessIssue]  # type: ignore[attr-defined]
                if qtpy.QT5
                else event.globalPosition().toPoint()  # pyright: ignore[reportAttributeAccessIssue]  # type: ignore[attr-defined]
            )
            self.move(self.mapFromGlobal(self.mapToGlobal(self.pos()) + (globalPos - self._mouse_move_pos)))
            self._mouse_move_pos = globalPos

    def mousePressEvent(
        self,
        event: QMouseEvent,  # pyright: ignore[reportIncompatibleMethodOverride]
    ):
        if event.button() == Qt.MouseButton.LeftButton:
            self._mouse_move_pos = (
                event.globalPos()  # pyright: ignore[reportAttributeAccessIssue]  # type: ignore[attr-defined]
                if qtpy.QT5
                else event.globalPosition().toPoint()  # pyright: ignore[reportAttributeAccessIssue]  # type: ignore[attr-defined]
            )

    def mouseReleaseEvent(
        self,
        event: QMouseEvent,  # pyright: ignore[reportIncompatibleMethodOverride]
    ):
        if event.button() == Qt.MouseButton.LeftButton:
            self._mouse_move_pos = None

    def keyPressEvent(
        self,
        event: QKeyEvent,  # pyright: ignore[reportIncompatibleMethodOverride]
    ):
        super().keyPressEvent(event)

    def dragEnterEvent(
        self,
        e: QtGui.QDragEnterEvent | None,  # pyright: ignore[reportIncompatibleMethodOverride]
    ):
        if e is None:
            return
        event_mimedata: QMimeData | None = e.mimeData()
        if event_mimedata is None:
            return
        if not event_mimedata.hasUrls():
            return
        for url in event_mimedata.urls():
            try:
                filepath = url.toLocalFile()
                _resref, restype = ResourceIdentifier.from_path(filepath).unpack()
                if not restype.is_valid():
                    RobustLogger().debug(f"Not processing dragged-in item '{filepath}'. Unsupported restype '{restype}'.")
                    continue
            except Exception:  # noqa: BLE001, PERF203
                RobustLogger().exception("Could not process dragged-in item.")
                e.ignore()
                return
            else:
                if restype is not None:
                    continue
        e.accept()

    def dropEvent(
        self,
        e: QtGui.QDropEvent | None = None,  # pyright: ignore[reportIncompatibleMethodOverride]
    ) -> None:
        if e is None:
            return
        event_mimedata: QMimeData | None = e.mimeData()
        if event_mimedata is None:
            return
        if not event_mimedata.hasUrls():
            return
        for url in event_mimedata.urls():
            try:
                filepath: str = url.toLocalFile()
                resname, restype = ResourceIdentifier.from_path(filepath).unpack()
                if not restype or not restype.is_valid():
                    RobustLogger().debug(f"Not loading dropped file '{filepath}'. Unsupported restype '{restype}'.")
                    continue
                resource = FileResource(resname, restype, os.path.getsize(filepath), 0x0, filepath)  # noqa: PTH202
                editor_filepath, editor = open_resource_editor(resource, self.active, self, gff_specialized=GlobalSettings().gffSpecializedEditors)
            except Exception:  # noqa: BLE001, PERF203
                RobustLogger().exception("Could not process dropped file.")
                e.ignore()
            else:
                if editor_filepath is not None:
                    RobustLogger().debug(f"Dropped file '{str(editor_filepath)}' processed successfully.")
                    e.accept()
                    return
                if editor is None:
                    RobustLogger().warning(f"Dropped file '{filepath}' could not be processed. No editor nor filepath returned.")
                    e.ignore()
                    return

    # endregion

    # region Menu Bar
    def update_menus(self):
        version = "x" if self.active is None else "2" if self.active.tsl else "1"

        dialog_icon_path = f":/images/icons/k{version}/dialog.png"
        self.ui.actionNewDLG.setIcon(QIcon(QPixmap(dialog_icon_path)))  # pyright: ignore[reportArgumentType]  # type: ignore[arg-type]
        self.ui.actionNewDLG.setEnabled(self.active is not None)

        tlk_icon_path = f":/images/icons/k{version}/tlk.png"
        self.ui.actionNewTLK.setIcon(QIcon(QPixmap(tlk_icon_path)))  # pyright: ignore[reportArgumentType]  # type: ignore[arg-type]
        self.ui.actionNewTLK.setEnabled(True)

        script_icon_path = f":/images/icons/k{version}/script.png"
        self.ui.actionNewNSS.setIcon(QIcon(QPixmap(script_icon_path)))  # pyright: ignore[reportArgumentType]  # type: ignore[arg-type]
        self.ui.actionNewNSS.setEnabled(self.active is not None)

        creature_icon_path = f":/images/icons/k{version}/creature.png"
        self.ui.actionNewUTC.setIcon(QIcon(QPixmap(creature_icon_path)))  # pyright: ignore[reportArgumentType]  # type: ignore[arg-type]
        self.ui.actionNewUTC.setEnabled(self.active is not None)

        placeable_icon_path = f":/images/icons/k{version}/placeable.png"
        self.ui.actionNewUTP.setIcon(QIcon(QPixmap(placeable_icon_path)))  # pyright: ignore[reportArgumentType]  # type: ignore[arg-type]
        self.ui.actionNewUTP.setEnabled(self.active is not None)

        door_icon_path = f":/images/icons/k{version}/door.png"
        self.ui.actionNewUTD.setIcon(QIcon(QPixmap(door_icon_path)))  # pyright: ignore[reportArgumentType]  # type: ignore[arg-type]
        self.ui.actionNewUTD.setEnabled(self.active is not None)

        item_icon_path = f":/images/icons/k{version}/item.png"
        self.ui.actionNewUTI.setIcon(QIcon(QPixmap(item_icon_path)))  # pyright: ignore[reportArgumentType]  # type: ignore[arg-type]
        self.ui.actionNewUTI.setEnabled(self.active is not None)

        sound_icon_path = f":/images/icons/k{version}/sound.png"
        self.ui.actionNewUTS.setIcon(QIcon(QPixmap(sound_icon_path)))  # pyright: ignore[reportArgumentType]  # type: ignore[arg-type]
        self.ui.actionNewUTS.setEnabled(self.active is not None)

        trigger_icon_path = f":/images/icons/k{version}/trigger.png"
        self.ui.actionNewUTT.setIcon(QIcon(QPixmap(trigger_icon_path)))  # pyright: ignore[reportArgumentType]  # type: ignore[arg-type]
        self.ui.actionNewUTT.setEnabled(self.active is not None)

        merchant_icon_path = f":/images/icons/k{version}/merchant.png"
        self.ui.actionNewUTM.setIcon(QIcon(QPixmap(merchant_icon_path)))  # pyright: ignore[reportArgumentType]  # type: ignore[arg-type]
        self.ui.actionNewUTM.setEnabled(self.active is not None)

        waypoint_icon_path = f":/images/icons/k{version}/waypoint.png"
        self.ui.actionNewUTW.setIcon(QIcon(QPixmap(waypoint_icon_path)))  # pyright: ignore[reportArgumentType]  # type: ignore[arg-type]
        self.ui.actionNewUTW.setEnabled(self.active is not None)

        encounter_icon_path = f":/images/icons/k{version}/encounter.png"
        self.ui.actionNewUTE.setIcon(QIcon(QPixmap(encounter_icon_path)))  # pyright: ignore[reportArgumentType]  # type: ignore[arg-type]
        self.ui.actionNewUTE.setEnabled(self.active is not None)

        self.ui.actionEditTLK.setEnabled(self.active is not None)
        self.ui.actionEditJRL.setEnabled(self.active is not None)
        self.ui.actionFileSearch.setEnabled(self.active is not None)
        self.ui.actionModuleDesigner.setEnabled(self.active is not None)
        self.ui.actionIndoorMapBuilder.setEnabled(self.active is not None)

        # KotorDiff is always available
        self.ui.actionKotorDiff.setEnabled(True)

        # TSLPatchData editor is always available
        self.ui.actionTSLPatchDataEditor.setEnabled(True)

        self.ui.actionCloneModule.setEnabled(self.active is not None)

    def debounce_module_designer_load(self):
        """Prevents users from spamming the start button, which could easily result in a bad crash."""
        self.module_designer_load_processed = True

    @Slot(bool)
    def open_module_designer(self, checked: bool = False):
        """Open the module designer.

        Args:
        ----
            checked: Whether the action was checked (from triggered signal, ignored).
        """
        assert self.active is not None, "No installation loaded."
        selected_module: Path | None = None
        try:
            combo_data = self.ui.modulesWidget.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        except Exception:  # noqa: BLE001
            combo_data = None
        if combo_data:
            selected_module = self.active.module_path() / Path(str(combo_data))
        try:
            designer_window = ModuleDesigner(None, self.active, mod_filepath=selected_module)  # pyright: ignore[call-arg]
        except TypeError as exc:
            RobustLogger().warning(f"ModuleDesigner signature mismatch: {exc}. Falling back without module path.")
            designer_window = ModuleDesigner(None, self.active)
            if selected_module is not None:
                QTimer.singleShot(33, lambda: designer_window.open_module(selected_module))
        add_window(designer_window)

    @Slot(bool)
    def open_settings_dialog(
        self,
        checked: bool = False,  # pyright: ignore[reportUnusedParameter]
    ):
        """Opens the Settings dialog and refresh installation combo list if changes.

        Args:
        ----
            checked: Whether the action was checked (from triggered signal, ignored).
        """
        dialog = SettingsDialog(self)
        if (
            dialog.exec()
            and dialog.installation_edited
            and QMessageBox(
                QMessageBox.Icon.Question,
                "Reload the installations?",
                "You appear to have made changes to your installations, would you like to reload?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            ).exec()
            == QMessageBox.StandardButton.Yes
        ):
            self.reload_settings()

    @Slot(bool)
    def open_active_talktable(
        self,
        checked: bool = False,  # pyright: ignore[reportUnusedParameter]
    ):
        """Open the active talktable editor.

        Args:
        ----
            checked: Whether the action was checked (from triggered signal, ignored).
        """
        assert self.active is not None, "No installation loaded."
        c_filepath = self.active.path() / "dialog.tlk"
        if not c_filepath.exists() or not c_filepath.is_file():
            QMessageBox(
                QMessageBox.Icon.Information,
                "dialog.tlk not found",
                f"Could not open the TalkTable editor, dialog.tlk not found at the expected location<br><br>{c_filepath}.",
                # flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            ).exec()
            return
        resource = FileResource("dialog", ResourceType.TLK, os.path.getsize(c_filepath), 0x0, c_filepath)  # noqa: PTH202
        open_resource_editor(resource, self.active, self)

    @Slot(bool)
    def open_active_journal(
        self,
        checked: bool = False,  # pyright: ignore[reportUnusedParameter]
    ):
        """Open the active journal editor.

        Args:
        ----
            checked: Whether the action was checked (from triggered signal, ignored).
        """
        assert self.active is not None, "No active installation selected"
        jrl_ident: ResourceIdentifier = ResourceIdentifier("global", ResourceType.JRL)
        journal_resources: dict[ResourceIdentifier, list[LocationResult]] = self.active.locations(
            [jrl_ident],
            [SearchLocation.OVERRIDE, SearchLocation.CHITIN],
        )
        if not journal_resources or not journal_resources.get(jrl_ident):
            QMessageBox(
                QMessageBox.Icon.Critical,
                "global.jrl not found",
                "Could not open the journal editor: 'global.jrl' not found.",
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            ).exec()
            return
        relevant: list[LocationResult] = journal_resources[jrl_ident]
        if len(relevant) > 1:
            dialog = FileSelectionWindow(relevant, self.active)
            dialog.show()
            add_window(dialog)
        else:
            open_resource_editor(relevant[0].as_file_resource(), self.active, self)

    @Slot(bool)
    def open_file_search_dialog(
        self,
        checked: bool = False,  # pyright: ignore[reportUnusedParameter]
    ):
        """Open the file search dialog.

        Args:
        ----
            checked: Whether the action was checked (from triggered signal, ignored).
        """
        assert self.active is not None, "No installation active"
        file_searcher_dialog = FileSearcher(self, self.installations)
        file_searcher_dialog.setModal(False)  # Make the dialog non-modal
        file_searcher_dialog.file_results.connect(self.handle_search_completed)
        add_window(file_searcher_dialog)
        file_searcher_dialog.show()  # Show the dialog without blocking

    @Slot(bool)
    def open_indoor_map_builder(
        self,
        checked: bool = False,  # pyright: ignore[reportUnusedParameter]
    ):
        """Open the indoor map builder.

        Args:
        ----
            checked: Whether the action was checked (from triggered signal, ignored).
        """
        builder = IndoorMapBuilder(None, self.active)
        builder.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        builder.show()
        builder.activateWindow()
        add_window(builder)

    @Slot(bool)
    def open_kotordiff(
        self,
        checked: bool = False,  # pyright: ignore[reportUnusedParameter]
    ):
        """Open the KotorDiff window.

        Args:
        ----
            checked: Whether the action was checked (from triggered signal, ignored).
        """
        kotordiff_window = KotorDiffWindow(
            None,
            self.installations,
            self.active,
        )
        kotordiff_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        kotordiff_window.show()
        kotordiff_window.activateWindow()
        add_window(kotordiff_window)

    @Slot(bool)
    def open_tslpatchdata_editor(
        self,
        checked: bool = False,  # pyright: ignore[reportUnusedParameter]
    ):
        """Open the TSLPatchData editor dialog.

        Args:
        ----
            checked: Whether the action was checked (from triggered signal, ignored).
        """
        editor = TSLPatchDataEditor(None, self.active)
        editor.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        editor.show()
        editor.activateWindow()
        add_window(editor)

    @Slot(bool)
    def open_instructions_window(
        self,
        checked: bool = False,  # pyright: ignore[reportUnusedParameter]
    ):
        """Opens the instructions window.

        Args:
        ----
            checked: Whether the action was checked (from triggered signal, ignored).
        """
        window = HelpWindow(None)
        window.setWindowIcon(self.windowIcon())
        window.show()
        window.activateWindow()
        add_window(window)

    @Slot(bool)
    def open_about_dialog(
        self,
        checked: bool = False,  # pyright: ignore[reportUnusedParameter]
    ):
        """Opens the about dialog.

        Args:
        ----
            checked: Whether the action was checked (from triggered signal, ignored).
        """
        About(self).exec()

    # endregion

    # region Other
    def get_active_tab_index(self) -> int:
        return self.ui.resourceTabs.currentIndex()

    def get_active_resource_tab(self) -> QWidget:
        return self.ui.resourceTabs.currentWidget()  # pyright: ignore[reportReturnType]

    def get_active_resource_widget(self) -> ResourceList | TextureList:
        current_widget: QWidget = self.get_active_resource_tab()
        if current_widget is self.ui.coreTab:
            return self.ui.coreWidget
        if current_widget is self.ui.modulesTab:
            return self.ui.modulesWidget
        if current_widget is self.ui.overrideTab:
            return self.ui.overrideWidget
        if current_widget is self.ui.texturesTab:
            return self.ui.texturesWidget
        if current_widget is self.ui.savesTab:
            return self.ui.savesWidget
        raise ValueError(f"Unknown current widget: {current_widget}")

    def reload_settings(self):
        self.reload_installations()

    @Slot(bool)
    def _open_module_tab_erf_editor(
        self,
        checked: bool = False,  # pyright: ignore[reportUnusedParameter]
    ):
        """Open the ERF editor for the module tab.

        Args:
        ----
            checked: Whether the button was checked (from clicked signal, ignored).
        """
        assert self.active is not None
        reslist = self.get_active_resource_widget()
        assert isinstance(reslist, ResourceList)
        filename = reslist.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        if not filename:
            return
        erf_filepath = self.active.module_path() / filename
        if not erf_filepath.is_file():
            return
        res_ident: ResourceIdentifier = ResourceIdentifier.from_path(erf_filepath)
        if not res_ident.restype:
            return
        erf_file_resource = FileResource(res_ident.resname, res_ident.restype, os.path.getsize(erf_filepath), 0x0, erf_filepath)  # noqa: PTH202
        _filepath, _editor = open_resource_editor(
            erf_file_resource,
            self.active,
            self,
            gff_specialized=self.settings.gffSpecializedEditors,
        )

    @Slot(int)
    def on_tab_changed(
        self,
        index: int,  # pyright: ignore[reportUnusedParameter]
    ):
        current_widget: QWidget = self.get_active_resource_tab()
        if current_widget is self.ui.modulesTab:
            self.erf_editor_button.show()
        else:
            self.erf_editor_button.hide()

    def select_resource(
        self,
        tree: ResourceList,
        resource: FileResource,
    ):
        """This function seems to reload the resource after determining the ui widget containing it.

        Seems to only be used for the FileSearcher dialog.
        """
        if tree == self.ui.coreWidget:
            self.ui.resourceTabs.setCurrentWidget(self.ui.coreTab)  # pyright: ignore[reportArgumentType]
            self.ui.coreWidget.set_resource_selection(resource)

        elif tree == self.ui.modulesWidget:
            self.ui.resourceTabs.setCurrentWidget(self.ui.modulesTab)  # pyright: ignore[reportArgumentType]
            filename = resource.filepath().name
            self.change_module(filename)
            self.ui.modulesWidget.set_resource_selection(resource)

        elif tree == self.ui.overrideWidget:
            self._select_override_resource(resource)
        elif tree == self.ui.savesWidget:
            self.ui.resourceTabs.setCurrentWidget(self.ui.savesTab)  # pyright: ignore[reportArgumentType]
            filename = resource.filepath().name
            self.on_save_reload(filename)

    def _select_override_resource(
        self,
        resource: FileResource,
    ):
        assert self.active is not None
        self.ui.resourceTabs.setCurrentWidget(self.ui.overrideTab)  # pyright: ignore[reportArgumentType]
        self.ui.overrideWidget.set_resource_selection(resource)
        subfolder: str = "."
        for folder_name in self.active.override_list():
            folder_path = self.active.override_path() / folder_name
            if os.path.commonpath([resource.filepath(), folder_path]) == str(folder_path) and len(subfolder) < len(folder_path.name):
                subfolder = folder_name
        self.change_override_folder(subfolder)

    def reload_installations(self):
        """Refresh the list of installations available in the combobox."""
        try:
            self.ui.gameCombo.currentIndexChanged.disconnect(self.change_active_installation)
        except (TypeError, RuntimeError):
            # Signal may not be connected yet during initialization
            pass
        self.ui.gameCombo.clear()  # without above disconnect, would call ToolWindow().changeActiveInstallation(-1)
        self.ui.gameCombo.addItem(tr("[None]"))  # without above disconnect, would call ToolWindow().changeActiveInstallation(0)

        for installation in self.settings.installations().values():
            self.ui.gameCombo.addItem(installation.name)
        self.ui.gameCombo.currentIndexChanged.connect(self.change_active_installation)

    @Slot()
    def unset_installation(self):
        """Unset the current installation and clear all UI state."""
        # Clear file system watcher before clearing the installation
        self._clear_file_watcher()

        # Disconnect signal to prevent recursive call when setting index to 0
        try:
            self.ui.gameCombo.currentIndexChanged.disconnect(self.change_active_installation)
        except (TypeError, RuntimeError):
            # Signal may not be connected yet during initialization
            pass

        self.ui.gameCombo.setCurrentIndex(0)

        # Reconnect signal after setting index
        self.ui.gameCombo.currentIndexChanged.connect(self.change_active_installation)

        # Clear all resource lists
        self.ui.coreWidget.set_resources([])
        self.ui.modulesWidget.set_sections([])
        self.ui.modulesWidget.set_resources([])
        self.ui.overrideWidget.set_sections([])
        self.ui.overrideWidget.set_resources([])

        # Disable resource tabs and update menus
        self.ui.resourceTabs.setEnabled(False)
        self.update_menus()
        self.active = None

    # endregion

    # region ResourceList handlers
    def refresh_core_list(self, *, reload: bool = True):
        """Rebuilds the tree in the Core tab. Used with the flatten/unflatten logic."""
        if self.active is None:
            return
        try:
            self.ui.coreWidget.set_resources(self.active.core_resources())
        except Exception:  # noqa: BLE001
            RobustLogger().exception("Failed to setResources of the core list")
        try:
            self.ui.coreWidget.modules_model.remove_unused_categories()
        except Exception:  # noqa: BLE001
            RobustLogger().exception("Failed to remove unused categories in the core list")

    def change_module(self, module_name: str):
        self.ui.modulesWidget.change_section(module_name)

    def refresh_module_list(
        self,
        *,
        reload: bool = True,
        module_items: list[QStandardItem] | None = None,
    ):
        """Refreshes the list of modules in the modulesCombo combobox."""
        RobustLogger().info("Refreshing module list")
        module_items = [] if module_items is None else module_items
        action: Literal["Reload", "Refresh"] = "Reload" if reload else "Refresh"
        if not module_items:
            try:
                module_items = self._get_modules_list(reload=reload)
            except Exception:  # noqa: BLE001
                RobustLogger().exception(f"Failed to get the list of {action}ed modules!")

        try:
            self.ui.modulesWidget.set_sections(module_items)
        except Exception:  # noqa: BLE001
            RobustLogger().exception(f"Failed to call setSections on the {action}ed modulesWidget!")

    def _get_modules_list(self, *, reload: bool = True) -> list[QStandardItem]:  # noqa: C901
        """Refreshes the list of modules in the modulesCombo combobox."""
        if self.active is None:
            return []
        # If specified the user can forcibly reload the resource list for every module
        if reload:
            try:
                # Force reload by clearing the loaded flag, so deleted files are removed from the list
                self.active._modules_loaded = False  # pyright: ignore[reportPrivateUsage]
                self.active.load_modules()
            except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
                RobustLogger().exception("Failed to reload the list of modules (load_modules function)")

        try:
            area_names: dict[str, str | None] = self.active.module_names()
        except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            RobustLogger().exception("Failed to get the list of area names from the modules!")
            area_names = {k: (str(v[0].filepath()) if v else "unknown filepath") for k, v in self.active._modules.items()}

        def sort_algo(module_file_name: str) -> str:
            """Sorts the modules in the modulesCombo combobox."""
            lower_module_file_name: str = module_file_name.lower()
            sort_str: str = ""
            with suppress(Exception):
                if "stunt" in lower_module_file_name:  # keep the stunt modules at the bottom.
                    sort_str = "zzzzz"
                elif self.settings.moduleSortOption == 0:  # "Sort by filename":
                    sort_str = ""
                elif self.settings.moduleSortOption == 1:  # "Sort by humanized area name":
                    sort_str = (area_names.get(module_file_name, "y") or "unknown_area_name").lower()
                else:  # alternate mod id that attempts to match to filename.
                    assert self.active is not None, "self.active is None"
                    sort_str = self.active.module_id(module_file_name, use_alternate=True)
            sort_str += f"_{lower_module_file_name}".lower()
            return sort_str

        try:
            sorted_keys: list[str] = sorted(area_names, key=sort_algo)
        except Exception:  # noqa: BLE001
            RobustLogger().exception("Failed to sort the list of modules")
            sorted_keys = list(area_names.keys())

        modules: list[QStandardItem] = []
        for module_name in sorted_keys:
            try:
                # Some users may choose to have their RIM files for the same module merged into a single option for the
                # dropdown menu.
                lower_module_name = module_name.lower()
                if self.settings.joinRIMsTogether:
                    if lower_module_name.endswith("_s.rim"):
                        continue
                    if self.active.game().is_k2() and lower_module_name.endswith("_dlg.erf"):
                        continue

                area_text: str = area_names.get(module_name) or "<Missing ARE>"
                item: QStandardItem = QStandardItem(f"{area_text} [{module_name}]")
                item.setData(f"{area_text}\n{module_name}", Qt.ItemDataRole.DisplayRole)
                item.setData(module_name, Qt.ItemDataRole.UserRole)  # Set area name
                item.setData(module_name, Qt.ItemDataRole.UserRole + 11)  # Set module name

                # Some users may choose to have items representing RIM files to have grey text.
                if self.settings.greyRIMText and lower_module_name.endswith(("_dlg.erf", ".rim")):
                    item.setForeground(self.palette().shadow())

                modules.append(item)
            except Exception:  # noqa: PERF203, BLE001
                RobustLogger().exception(f"Unexpected exception thrown while parsing module '{module_name}', skipping...")
        return modules

    def change_override_folder(
        self,
        subfolder: str,
    ):
        self.ui.overrideWidget.change_section(subfolder)

    def _get_override_list(self, *, reload: bool = True) -> list[QStandardItem]:
        if self.active is None:
            print("No installation is currently loaded, cannot refresh override list")
            return []
        if reload:
            try:
                self.active.load_override()
            except Exception:  # noqa: BLE001
                RobustLogger().exception("Failed to call load_override in getOverrideList")

        sections: list[QStandardItem] = []
        for directory in self.active.override_list():
            section = QStandardItem(str(directory if directory.strip() else "[Root]"))
            section.setData(directory, QtCore.Qt.ItemDataRole.UserRole)
            sections.append(section)
        return sections

    def refresh_override_list(
        self,
        *,
        reload: bool = True,
        override_items: list[QStandardItem] | None = None,
    ):
        """Refreshes the list of override directories in the overrideFolderCombo combobox."""
        override_items = self._get_override_list(reload=reload)
        self.ui.overrideWidget.set_sections(override_items)

    def _get_texture_pack_list(self) -> list[QStandardItem] | None:
        assert self.active is not None, "No installation set. This should never happen!"
        texture_pack_list: list[QStandardItem] = []
        for texturepack in self.active.texturepacks_list():
            section = QStandardItem(str(texturepack))
            section.setData(texturepack, QtCore.Qt.ItemDataRole.UserRole)
            texture_pack_list.append(section)
        return texture_pack_list

    def refresh_saves_list(
        self,
        *,
        reload: bool = True,
    ):
        assert self.active is not None, "No installation set, this should never happen!"
        try:
            if reload:
                self.active.load_saves()

            saves_list: list[QStandardItem] = []
            for save_path in self.active.saves:
                save_path_str = str(save_path)
                section = QStandardItem(save_path_str)
                section.setData(save_path_str, QtCore.Qt.ItemDataRole.UserRole)
                saves_list.append(section)
            self.ui.savesWidget.set_sections(saves_list)
        except Exception:  # noqa: BLE001
            RobustLogger().exception("Failed to load/refresh the saves list")

    # endregion

    # region Extract
    @Slot(str)
    def _save_capsule_from_tool_ui(self, module_name: str):
        assert self.active is not None
        c_filepath = self.active.module_path() / module_name
        capsule_filter: str = "Module (*.mod);;Encapsulated Resource File (*.erf);;Resource Image File (*.rim);;Save (*.sav);;All Capsule Types (*.erf; *.mod; *.rim; *.sav)"
        capsule_type: str = "mod"
        if is_erf_file(c_filepath):
            capsule_type = "erf"
        elif is_rim_file(c_filepath):
            capsule_type = "rim"
        extension_to_filter: dict[str, str] = {
            ".mod": tr("Module (*.mod)"),
            ".erf": tr("Encapsulated Resource File (*.erf)"),
            ".rim": tr("Resource Image File (*.rim)"),
            ".sav": "Save ERF (*.sav)",
        }
        filepath_str, _filter = QFileDialog.getSaveFileName(
            self,
            trf("Save extracted {type} '{name}' as...", type=capsule_type, name=c_filepath.stem),
            str(Path.cwd().resolve()),
            capsule_filter,
            extension_to_filter[c_filepath.suffix.lower()],  # defaults to the original extension.
        )
        if not filepath_str or not filepath_str.strip():
            return
        r_save_filepath = Path(filepath_str)
        try:
            if is_mod_file(r_save_filepath):
                if capsule_type == "mod":
                    write_erf(read_erf(c_filepath), r_save_filepath)
                    QMessageBox(QMessageBox.Icon.Information, tr("Module Saved"), trf("Module saved to '{r_save_filepath}'", r_save_filepath=r_save_filepath)).exec()
                else:
                    module.rim_to_mod(r_save_filepath, self.active.module_path(), module_name, self.active.game())
                    QMessageBox(QMessageBox.Icon.Information, tr("Module Built"), trf("Module built from relevant RIMs/ERFs and saved to '{r_save_filepath}'", r_save_filepath=r_save_filepath)).exec()
                return

            erf_or_rim: ERF | RIM = read_erf(c_filepath) if is_any_erf_type_file(c_filepath) else read_rim(c_filepath)
            if is_rim_file(r_save_filepath):
                if isinstance(erf_or_rim, ERF):
                    erf_or_rim = erf_or_rim.to_rim()
                write_rim(erf_or_rim, r_save_filepath)
                QMessageBox(QMessageBox.Icon.Information, tr("RIM Saved"), trf("Resource Image File saved to '{r_save_filepath}'", r_save_filepath=r_save_filepath)).exec()

            elif is_any_erf_type_file(r_save_filepath):
                if isinstance(erf_or_rim, RIM):
                    erf_or_rim = erf_or_rim.to_erf()
                erf_or_rim.erf_type = ERFType.from_extension(r_save_filepath)
                write_erf(erf_or_rim, r_save_filepath)
                QMessageBox(QMessageBox.Icon.Information, tr("ERF Saved"), trf("Encapsulated Resource File saved to '{r_save_filepath}'", r_save_filepath=r_save_filepath)).exec()

        except Exception as e:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            RobustLogger().exception("Error extracting capsule file '%s'", module_name)
            QMessageBox(QMessageBox.Icon.Critical, tr("Error saving capsule file"), str((e.__class__.__name__, str(e)))).exec()

    def build_extract_save_paths(
        self,
        resources: list[FileResource],
    ) -> tuple[Path, dict[FileResource, Path]] | tuple[None, None]:
        """Build extraction save paths for resources, handling filename conflicts for extra extracts.

        This method ensures that when extracting resources with additional files (like TXI files
        for textures or texture subfolders for models), no filename conflicts occur between
        different resources that might have the same base name.

        Args:
        ----
            resources: List of FileResource objects to extract

        Returns:
        -------
            Tuple of (folder_path, paths_to_write_dict) or (None, None) if cancelled
        """
        paths_to_write: dict[FileResource, Path] = {}

        folder_path_str: str = QFileDialog.getExistingDirectory(self, tr("Extract to folder"))
        if not folder_path_str or not folder_path_str.strip():
            RobustLogger().debug("User cancelled folderpath extraction.")
            return None, None

        folder_path = Path(folder_path_str)

        # Track all potential output filenames to detect conflicts
        used_filenames: set[str] = set()
        resource_conflict_counts: dict[str, int] = {}

        for resource in resources:
            identifier: ResourceIdentifier = resource.identifier()
            base_name: str = identifier.resname
            base_path: Path = folder_path / base_name

            # Determine the main file save path based on UI checks
            main_save_path: Path = base_path
            if resource.restype() is ResourceType.TPC and self.ui.tpcDecompileCheckbox.isChecked():
                main_save_path = main_save_path.with_suffix(".tga")
            elif resource.restype() is ResourceType.MDL and self.ui.mdlDecompileCheckbox.isChecked():
                main_save_path = main_save_path.with_suffix(".mdl.ascii")
            else:
                main_save_path = main_save_path.with_suffix(f".{identifier.restype.extension}")

            # Check for conflicts with the main file and adjust if necessary
            main_filename: str = main_save_path.name
            if main_filename in used_filenames:
                # Increment conflict count for this base name
                conflict_count = resource_conflict_counts.get(base_name, 0) + 1
                resource_conflict_counts[base_name] = conflict_count

                # Create unique filename by appending suffix
                stem = main_save_path.stem
                suffix = main_save_path.suffix
                main_save_path = main_save_path.with_name(f"{stem}_{conflict_count}{suffix}")

            used_filenames.add(main_save_path.name)

            # For TPC resources, also check TXI file conflicts if that option is enabled
            if resource.restype() is ResourceType.TPC and self.ui.tpcTxiCheckbox.isChecked():
                txi_path: Path = main_save_path.with_suffix(".txi")
                txi_filename: str = txi_path.name
                if txi_filename in used_filenames:
                    # Use the same conflict resolution as the main file
                    conflict_count = resource_conflict_counts.get(base_name, 0)
                    if conflict_count > 0:
                        stem = txi_path.stem
                        txi_path = txi_path.with_name(f"{stem}_{conflict_count}.txi")

                used_filenames.add(txi_path.name)

            # For MDL resources, check potential texture subfolder conflicts if texture extraction is enabled
            if resource.restype() is ResourceType.MDL and self.ui.mdlTexturesCheckbox.isChecked():
                model_subfolder_name: str = f"model_{base_name}"
                if model_subfolder_name in used_filenames:
                    conflict_count = resource_conflict_counts.get(base_name, 0)
                    if conflict_count > 0:
                        model_subfolder_name = f"model_{base_name}_{conflict_count}"

                used_filenames.add(model_subfolder_name)

            paths_to_write[resource] = main_save_path

        return folder_path, paths_to_write

    @Slot(list, object)
    def on_extract_resources(
        self,
        selected_resources: list[FileResource],
        resource_widget: ResourceList | TextureList | None = None,
    ):
        if selected_resources:
            folder_path, paths_to_write = self.build_extract_save_paths(selected_resources)
            if folder_path is None or paths_to_write is None:
                return
            failed_savepath_handlers: dict[Path, Exception] = {}
            resource_save_paths: dict[FileResource, Path] = FileSaveHandler(selected_resources).determine_save_paths(
                paths_to_write,
                failed_savepath_handlers,
            )
            if not resource_save_paths:
                return
            loader = AsyncLoader.__new__(AsyncLoader)
            seen_resources: dict[LocationResult, Path] = {}

            def _make_extract_task(
                resource: FileResource,
                save_path: Path,
                loader: AsyncLoader = loader,
                seen_resources: dict[LocationResult, Path] = seen_resources,
            ) -> Callable[[], None]:
                def task():
                    self._extract_resource(
                        resource=resource,
                        save_path=save_path,
                        loader=loader,
                        seen_resources=seen_resources,
                    )

                return task

            tasks: list[Callable[[], None]] = [
                _make_extract_task(
                    resource=resource,
                    save_path=save_path,
                    loader=loader,
                    seen_resources=seen_resources,
                )
                for resource, save_path in resource_save_paths.items()
            ]

            loader.__init__(  # pylint: disable=unnecessary-dunder-call
                self,
                "Extracting Resources",
                tasks,
                "Failed to Extract Resources",
            )
            loader.errors.extend(failed_savepath_handlers.values())
            loader.exec()

            # quick main thread/ui check.
            if QThread.currentThread() != cast(QApplication, QApplication.instance()).thread():
                print("on_extract_resources: Not on main thread, returning")
                return

            num_errors = len(loader.errors)
            num_successes = len(resource_save_paths) - num_errors

            # Always show one message box, with both successes and errors listed intuitively.
            if num_errors or num_successes:
                if num_errors and num_successes > 0:
                    title = tr("Extraction completed with some errors.")
                    summary = trf(
                        "Saved {success_count} files to {path}.\nFailed to save {error_count} files.",
                        success_count=num_successes,
                        error_count=num_errors,
                        path=folder_path,
                    )
                elif num_errors:
                    title = tr("Failed to extract all items.")
                    summary = trf("Failed to save all {count} files!", count=num_errors)
                else:
                    title = tr("Extraction successful.")
                    summary = trf(
                        "Successfully saved {count} files to {path}",
                        count=len(resource_save_paths),
                        path=folder_path,
                    )

                msg_box = QMessageBox(
                    QMessageBox.Icon.Information,
                    title,
                    summary,
                    flags=(
                        Qt.WindowType.Dialog
                        | Qt.WindowType.WindowTitleHint
                        | Qt.WindowType.WindowCloseButtonHint
                        | Qt.WindowType.WindowStaysOnTopHint
                    ),
                )
                details_lines: list[str] = []
                if num_successes > 0:
                    details_lines.append(tr("Saved files:"))
                    for p in resource_save_paths.values():
                        details_lines.append(f"   {p}")
                if num_errors:
                    if details_lines:
                        details_lines.append("")  # blank line
                    details_lines.append(tr("Errors:"))
                    for e in loader.errors:
                        details_lines.append(f"   {e.__class__.__name__}: {e}")
                msg_box.setDetailedText("\n".join(details_lines))
                msg_box.exec()
        elif isinstance(resource_widget, ResourceList) and is_capsule_file(resource_widget.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)):
            module_name = resource_widget.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
            self._save_capsule_from_tool_ui(module_name)

    def _extract_resource(
        self,
        resource: FileResource,
        save_path: Path,
        loader: AsyncLoader,
        seen_resources: dict[LocationResult, Path],
    ):
        loader._worker.progress.emit(  # noqa: SLF001  # pylint: disable=protected-access
            f"Processing resource: {resource.identifier()}",
            "update_maintask_text",
        )
        r_folderpath: Path = save_path.parent
        data: bytes = resource.data()
        if resource.restype() is ResourceType.MDX and self.ui.mdlDecompileCheckbox.isChecked():
            return
        if resource.restype() is ResourceType.TPC:
            tpc: TPC = read_tpc(data, txi_source=save_path)
            try:
                if self.ui.tpcTxiCheckbox.isChecked():
                    self._extract_txi(tpc, save_path.with_suffix(".txi"))
            except Exception as e:  # noqa: BLE001  # pylint: disable=broad-exception-caught
                loader.errors.append(e)
            try:
                if self.ui.tpcDecompileCheckbox.isChecked():
                    data = self._decompile_tpc(tpc)
            except Exception as e:  # noqa: BLE001  # pylint: disable=broad-exception-caught
                loader.errors.append(e)
        if resource.restype() is ResourceType.MDL:
            if self.ui.mdlTexturesCheckbox.isChecked():
                self._extract_mdl_textures(resource, r_folderpath, loader, data, seen_resources)  # pyright: ignore[reportArgumentType]
            if self.ui.mdlDecompileCheckbox.isChecked():
                data = bytes(self._decompile_mdl(resource, data))
        with save_path.open("wb") as file:
            file.write(data)

    def _extract_txi(self, tpc: TPC, filepath: Path):
        if not tpc.txi or not tpc.txi.strip():
            return
        with filepath.open("wb") as file:
            file.write(tpc.txi.encode("ascii", errors="ignore"))

    def _decompile_tpc(self, tpc: TPC) -> bytes:
        data = bytearray()
        write_tpc(tpc, data, ResourceType.TGA)
        return bytes(data)

    def _decompile_mdl(
        self,
        resource: FileResource,
        data: SOURCE_TYPES,
    ) -> bytearray:
        assert self.active is not None
        mdx_resource_lookup: ResourceResult | None = self.active.resource(resource.resname(), ResourceType.MDX)
        if mdx_resource_lookup is None:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), repr(resource))
        mdxData: bytes = mdx_resource_lookup.data
        mdl: MDL | None = read_mdl(data, 0, 0, mdxData, 0, 0)
        assert mdl is not None, "mdl is None in _decompile_mdl"
        data = bytearray()
        write_mdl(mdl, data, ResourceType.MDL_ASCII)
        return data

    def _extract_mdl_textures(
        self,
        resource: FileResource,
        folderpath: Path,
        loader: AsyncLoader,
        data: bytes,
        seen_resources: dict[LocationResult | Literal["all_locresults"], Path | Any],
    ):
        assert self.active is not None, "self.active is None in _extract_mdl_textures"
        textures_and_lightmaps = set(iterate_textures(data)) | set(iterate_lightmaps(data))
        main_subfolder = folderpath / f"model_{resource.resname()}"

        all_locresults: dict[str, dict[ResourceIdentifier, list[LocationResult]]] = defaultdict(lambda: defaultdict(list))
        seen_resources.setdefault(
            "all_locresults",
            all_locresults,
        )

        for item in textures_and_lightmaps:
            tex_type = "texture" if item in iterate_textures(data) else "lightmap"
            location_results = all_locresults.get(item) or self._locate_texture(item)
            all_locresults[item] = location_results

            if not self._process_texture(item, tex_type, location_results, resource, main_subfolder, seen_resources, loader):
                loader.errors.append(ValueError(f"Missing {tex_type} '{item}' for model '{resource.identifier()}'"))

    def _locate_texture(
        self,
        texture: str,
    ) -> dict[ResourceIdentifier, list[LocationResult]]:
        assert self.active is not None, "self.active is None in _locate_texture"
        return self.active.locations(
            [
                ResourceIdentifier(resname=texture, restype=rt)
                for rt in (ResourceType.TPC, ResourceType.TGA)
            ],
            [
                SearchLocation.OVERRIDE,
                SearchLocation.TEXTURES_GUI,
                SearchLocation.TEXTURES_TPA,
                SearchLocation.CHITIN,
            ],
        )

    def _process_texture(
        self,
        texture: str,
        tex_type: str,
        location_results: dict[ResourceIdentifier, list[LocationResult]],
        resource: FileResource,
        main_subfolder: Path,
        seen_resources: dict[LocationResult | Literal["all_locresults"], Path | Any],
        loader: AsyncLoader,
    ) -> bool:
        for resident, loclist in location_results.items():
            for location in loclist:
                subfolder = main_subfolder / location.filepath.stem
                if location in seen_resources:
                    self._copy_existing_texture(seen_resources[location], subfolder)
                    continue

                try:
                    self._save_texture(location, resident, subfolder, seen_resources)
                except Exception as e:  # noqa: BLE001  # pylint: disable=broad-exception-caught
                    RobustLogger().exception(f"Failed to save {tex_type} '{resident}' ({texture}) for model '{resource.identifier()}'")
                    loader.errors.append(
                        ValueError(f"Failed to save {tex_type} '{resident}' ({texture}) for model '{resource.identifier()}':<br>    {e.__class__.__name__}: {e}")
                    )

        return bool(location_results)

    def _copy_existing_texture(
        self,
        previous_save_path: Path,
        subfolder: Path,
    ):
        subfolder.mkdir(parents=True, exist_ok=True)
        shutil.copy(str(previous_save_path), str(subfolder))
        if self.ui.tpcTxiCheckbox.isChecked():
            txi_path = previous_save_path.with_suffix(".txi")
            if txi_path.exists() and txi_path.is_file():
                shutil.copy(str(txi_path), str(subfolder))

    def _save_texture(
        self,
        location: LocationResult,
        resident: ResourceIdentifier,
        subfolder: Path,
        seen_resources: dict[LocationResult, Path],
    ):
        file_format = ResourceType.TGA if self.ui.tpcDecompileCheckbox.isChecked() else ResourceType.TPC
        seen_resources[location] = savepath = subfolder / f"{resident.resname}.{file_format.extension}"

        if self.ui.tpcTxiCheckbox.isChecked() or (resident.restype == ResourceType.TPC and self.ui.tpcDecompileCheckbox.isChecked()):
            tpc = read_tpc(location.filepath, location.offset, location.size)
            subfolder.mkdir(parents=True, exist_ok=True)
            if self.ui.tpcTxiCheckbox.isChecked():
                self._extract_txi(tpc, savepath.with_suffix(".txi"))
            write_tpc(tpc, savepath, file_format)
        else:
            # Ensure the destination directory exists before opening the output stream.
            # (When extracting selected models, the location stem is often a new subfolder,
            # e.g. `swpc_tex_tpa`, and opening the file would otherwise raise FileNotFoundError.)
            savepath.parent.mkdir(parents=True, exist_ok=True)
            with location.filepath.open("rb") as r_stream, savepath.open("wb") as w_stream:
                r_stream.seek(location.offset)
                w_stream.write(r_stream.read(location.size))

    @Slot(bool)
    def open_from_file(
        self,
        checked: bool = False,  # pyright: ignore[reportUnusedParameter]
    ):
        """Open files from the file system.

        Args:
        ----
            checked: Whether the action was checked (from triggered signal, ignored).
        """
        filepaths: list[str] = QFileDialog.getOpenFileNames(self, "Select files to open")[:-1][0]

        for filepath in filepaths:
            r_filepath = Path(filepath)
            try:
                file_res = FileResource(
                    r_filepath.stem,
                    ResourceType.from_extension(r_filepath.suffix),
                    r_filepath.stat().st_size,
                    0x0,
                    r_filepath,
                )
                open_resource_editor(file_res, self.active, self)
            except (ValueError, OSError) as e:
                etype, msg = (e.__class__.__name__, str(e))
                QMessageBox(QMessageBox.Icon.Critical, f"Failed to open file ({etype})", msg).exec()

    # endregion


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ToolWindow()
    window.show()
    sys.exit(app.exec())
