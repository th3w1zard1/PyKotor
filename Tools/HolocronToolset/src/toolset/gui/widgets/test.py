#!/usr/bin/env python3
from __future__ import annotations

from abc import abstractmethod
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from io import BytesIO
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar, cast

import qtpy

from loggerplus import RobustLogger
from qtpy.QtCore import QFileInfo, QPoint, QSize, QSortFilterProxyModel, QTimer, Qt, Signal
from qtpy.QtGui import QCursor, QImage, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QFileIconProvider, QHeaderView, QMenu, QToolTip, QWidget

from pykotor.extract.file import FileResource
from pykotor.resource.formats.tpc.tpc_auto import read_tpc
from pykotor.resource.formats.tpc.tpc_data import TPCGetResult, TPCTextureFormat
from pykotor.resource.type import ResourceType
from toolset.gui.dialogs.load_from_location_result import ResourceItems
from toolset.gui.widgets.settings.installations import GlobalSettings

if TYPE_CHECKING:
    from concurrent.futures import Future

    from qtpy.QtCore import QAbstractItemModel, QEvent, QModelIndex, QObject
    from qtpy.QtGui import QIcon, QMouseEvent, QPixmap, QResizeEvent, QShowEvent
    from qtpy.QtWidgets import QAbstractItemView, QScrollBar

    from toolset.data.installation import HTInstallation


class MainWindowList(QWidget):
    """A widget for displaying and interacting with a list of KOTOR resources."""

    request_open_resource: Signal = Signal(list, object)  # pyright: ignore[reportPrivateImportUsage]
    requestExtractResource: Signal = Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    section_changed: Signal = Signal(object)  # pyright: ignore[reportPrivateImportUsage]

    @abstractmethod
    def selected_resources(self) -> list[FileResource]: ...


class ResourceStandardItem(QStandardItem):
    """A standard item for a resource."""

    def __init__(self, *args: Any, resource: FileResource, **kwargs: Any):
        """Initialize the resource standard item.

        Args:
        ----
            resource (FileResource): The resource to display.
        """
        super().__init__(*args, **kwargs)
        self.resource: FileResource = resource


class ResourceList(MainWindowList):
    """A widget for displaying and interacting with a list of KOTOR resources."""

    request_reload: Signal = Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    request_refresh: Signal = Signal()  # pyright: ignore[reportPrivateImportUsage]

    HORIZONTAL_HEADER_LABELS: ClassVar[list[str]] = ["ResRef", "Type"]

    def __init__(self, parent: QWidget):
        """Initializes the ResourceList widget.

        Args:
        ----
            parent (QWidget): The parent widget

        Processing Logic:
        ----------------
            - Initializes the UI from the designer file
            - Sets up the signal connections
            - Creates a ResourceModel and sets it as the model for the tree view
            - Creates a QStandardItemModel for the section combo box
            - Sets the section model as the model for the combo box.
        """
        super().__init__(parent)
        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.widgets.resource_list import (
                Ui_Form,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.widgets.resource_list import (
                Ui_Form,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.widgets.resource_list import (
                Ui_Form,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.widgets.resource_list import (
                Ui_Form,  # noqa: PLC0415  # pylint: disable=C0415
            )
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.tooltip_text: str = ""
        self.tooltip_pos: QPoint = QPoint(0, 0)
        self.flattened: bool = False
        self.auto_resize_enabled: bool = True
        self.expanded_state: bool = False
        self.original_items: list[tuple[QStandardItem, list[list[QStandardItem]]]] = []

        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setupSignals()

        self.modules_model: ResourceModel = ResourceModel()
        self.modules_model.proxy_model().setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.resourceTree.setModel(self.modules_model.proxy_model())  # pyright: ignore[reportArgumentType]
        self.ui.resourceTree.sortByColumn(0, Qt.SortOrder.AscendingOrder)  # pyright: ignore[reportArgumentType]
        self.section_model: QStandardItemModel = QStandardItemModel()
        self.ui.sectionCombo.setModel(self.section_model)  # pyright: ignore[reportArgumentType]

        # Connect the header context menu request signal
        tree_view_header: QHeaderView | None = self.ui.resourceTree.header()  # pyright: ignore[reportAssignmentType]
        assert tree_view_header is not None
        tree_view_header.setSectionsClickable(True)
        tree_view_header.setSortIndicatorShown(True)
        tree_view_header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)  # pyright: ignore[reportArgumentType]
        tree_view_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)  # pyright: ignore[reportArgumentType]

        self.tooltip_timer = QTimer(self)
        self.tooltip_timer.setSingleShot(True)
        self.tooltip_timer.timeout.connect(self.show_tooltip)

    def _clear_modules_model(self):
        self.modules_model.clear()
        self.modules_model.setColumnCount(2)
        self.modules_model.setHorizontalHeaderLabels(["ResRef", "Type"])

    def show_tooltip(self):
        QToolTip.showText(QCursor.pos(), self.tooltip_text, self.ui.resourceTree)  # pyright: ignore[reportArgumentType]

    def setupSignals(self):
        self.ui.searchEdit.textEdited.connect(self.on_filter_string_updated)
        self.ui.sectionCombo.currentIndexChanged.connect(self.on_section_changed)
        self.ui.reloadButton.clicked.connect(self.on_reload_clicked)
        self.ui.refreshButton.clicked.connect(self.on_refresh_clicked)
        self.ui.resourceTree.customContextMenuRequested.connect(self.on_resource_context_menu)
        self.ui.resourceTree.doubleClicked.connect(self.on_resource_double_clicked)

    def enterEvent(self, event: QEvent):
        self.tooltip_timer.stop()
        QToolTip.hideText()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent):
        self.tooltip_timer.stop()
        QToolTip.hideText()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        index = self.ui.resourceTree.indexAt(event.pos())  # type: ignore[arg-type]
        if index.isValid():
            model_index: QModelIndex = cast(QSortFilterProxyModel, self.ui.resourceTree.model()).mapToSource(index)  # pyright: ignore[reportArgumentType]
            item: ResourceStandardItem | QStandardItem | None = cast(
                QStandardItemModel,
                cast(QSortFilterProxyModel, self.ui.resourceTree.model()).sourceModel(),
            ).itemFromIndex(model_index)
            if isinstance(item, ResourceStandardItem):
                self.tooltip_text = str(item.resource.filepath())
                self.tooltip_pos = event.globalPos()
                self.tooltip_timer.start(1100)  # Set the delay to 3000ms (3 seconds)
            else:
                self.tooltip_timer.stop()
                QToolTip.hideText()
        else:
            self.tooltip_timer.stop()
            QToolTip.hideText()
        super().mouseMoveEvent(event)

    def hide_reload_button(self):
        self.ui.reloadButton.setVisible(False)

    def hide_section(self):
        self.ui.line.setVisible(False)
        self.ui.sectionCombo.setVisible(False)
        self.ui.refreshButton.setVisible(False)

    def current_section(self) -> str:
        return self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)

    def change_section(
        self,
        section: str,
    ):
        for i in range(self.ui.sectionCombo.count()):
            if section not in self.ui.sectionCombo.itemText(i):
                continue
            self.ui.sectionCombo.setCurrentIndex(i)

    def set_resources(
        self,
        resources: list[FileResource],
        custom_category: str | None = None,
        *,
        clear_existing: bool = True,
    ):
        """Adds and removes FileResources from the modules model.

        Args:
        ----
            resources: {list[FileResource]}: List of FileResource objects to set
        """
        all_resources: list[QStandardItem] = self.modules_model.all_resources_items()
        resource_set: set[FileResource] = set(resources)
        resource_item_map: dict[FileResource, ResourceStandardItem] = {item.resource: item for item in all_resources if isinstance(item, ResourceStandardItem)}
        for resource in resource_set:
            if resource in resource_item_map:
                resource_item_map[resource].resource = resource
            else:
                self.modules_model.add_resource(resource, custom_category)
        if clear_existing:
            for item in all_resources:
                if not isinstance(item, ResourceStandardItem):
                    continue
                if item.resource in resource_set:
                    continue
                item.parent().removeRow(item.row())
        self.modules_model.remove_unused_categories()

    def set_sections(
        self,
        sections: list[QStandardItem],
    ):
        self.section_model.clear()
        for section in sections:
            self.section_model.insertRow(self.section_model.rowCount(), section)

    def set_resource_selection(
        self,
        resource: FileResource,
    ):
        model: ResourceModel = cast(QSortFilterProxyModel, self.ui.resourceTree.model()).sourceModel()  # type: ignore[attribute-access]
        assert isinstance(model, ResourceModel)

        def select(parent, child):
            self.ui.resourceTree.expand(parent)
            self.ui.resourceTree.scrollTo(child)
            self.ui.resourceTree.setCurrentIndex(child)

        for item in model.all_resources_items():
            if not isinstance(item, ResourceStandardItem):
                continue
            resource_from_item: FileResource = item.resource
            if resource_from_item == resource:
                itemIndex: QModelIndex = model.proxy_model().mapFromSource(item.index())
                QTimer.singleShot(0, lambda index=itemIndex, item=item: select(item.parent().index(), index))

    def selected_resources(self) -> list[FileResource]:
        return self.modules_model.resource_from_indexes(self.ui.resourceTree.selectedIndexes())  # pyright: ignore[reportArgumentType]

    def _get_section_user_role_data(self):
        return self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)

    def on_filter_string_updated(self):
        self.modules_model.proxy_model().set_filter_string(self.ui.searchEdit.text())

    def on_section_changed(self):
        data = self._get_section_user_role_data()
        print(data)
        self.section_changed.emit(data)

    def on_reload_clicked(self):
        data = self._get_section_user_role_data()
        print(data)
        self.request_reload.emit(data)

    def on_refresh_clicked(self):
        self._clear_modules_model()
        self.request_refresh.emit()

    def on_resource_context_menu(self, point: QPoint):
        resources: list[FileResource] = self.selected_resources()
        if not resources:
            return
        menu = QMenu(self)
        menu.addAction("Open").triggered.connect(lambda: self.request_open_resource.emit(resources, True))
        if all(resource.restype().contents == "gff" for resource in resources):
            menu.addAction("Open with GFF Editor").triggered.connect(lambda: self.request_open_resource.emit(resources, False))
        menu.addSeparator()
        builder = ResourceItems(resources=resources)
        builder.viewport = lambda: self.ui.resourceTree
        builder.run_context_menu(point, menu=menu)

    def on_resource_double_clicked(self):
        self.request_open_resource.emit(self.selected_resources(), None)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.ui.resourceTree.setColumnWidth(1, 10)
        self.ui.resourceTree.setColumnWidth(0, self.ui.resourceTree.width() - 80)
        header: QHeaderView | None = self.ui.resourceTree.header()  # pyright: ignore[reportAssignmentType]
        assert header is not None
        header.setSectionResizeMode(QHeaderView.Interactive)  # type: ignore[arg-type]


class ResourceProxyModel(QSortFilterProxyModel):
    """A proxy model for the resource model."""

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.filter_string: str = ""

    def set_filter_string(self, filter_string: str):
        """Set the filter string for the proxy model."""
        self.filter_string = filter_string.lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """Check if a row should be filtered out."""
        model = self.sourceModel()  # pyright: ignore[reportAssignmentType]
        assert isinstance(model, QStandardItemModel)
        resref_index = model.index(source_row, 0, source_parent)
        item: ResourceStandardItem | QStandardItem | None = model.itemFromIndex(resref_index)
        if isinstance(item, ResourceStandardItem):
            # Get the file name and resource name
            filename = item.resource.filepath().name.lower()
            resname = item.resource.filename().lower()

            # Check if the filter string is a substring of either the filename or the resource name
            if self.filter_string in filename or self.filter_string in resname:
                return True

        return False


class ResourceModel(QStandardItemModel):
    """A data model used by the different trees (Core, Modules, Override).

    This class provides an easy way to add resources while sorting them into categories.
    """

    def __init__(self):
        super().__init__()
        self._category_items: dict[str, QStandardItem] = {}
        self._proxy_model: ResourceProxyModel = ResourceProxyModel(self)
        self._proxy_model.setSourceModel(self)
        self._proxy_model.setRecursiveFilteringEnabled(True)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["ResRef", "Type"])

    def proxy_model(self) -> ResourceProxyModel:
        """Get the proxy model for the resource model."""
        return self._proxy_model

    def clear(self):
        """Clear the resource model."""
        super().clear()
        self._category_items = {}
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["ResRef", "Type"])

    def _add_resource_into_category(
        self,
        resource_type: ResourceType,
        custom_category: str | None = None,
    ) -> QStandardItem:
        """Add a resource to the resource model.

        Args:
        ----
            resource_type (ResourceType): The type of resource to add.
            custom_category (str | None): The custom category to add the resource to.

        Returns:
        ----
            The category item for the resource.
        """
        chosen_category = resource_type.category if custom_category is None else custom_category
        if chosen_category not in self._category_items:
            category_item = QStandardItem(chosen_category)
            category_item.setSelectable(False)
            unused_item = QStandardItem("")
            unused_item.setSelectable(False)
            self._category_items[chosen_category] = category_item
            self.appendRow([category_item, unused_item])
        return self._category_items[chosen_category]

    def add_resource(
        self,
        resource: FileResource,
        custom_category: str | None = None,
    ):
        """Add a resource to the resource model.

        Args:
        ----
            resource (FileResource): The resource to add.
            custom_category (str | None): The custom category to add the resource to.
        """
        self._add_resource_into_category(resource.restype(), custom_category).appendRow(
            [
                ResourceStandardItem(resource.resname(), resource=resource),
                QStandardItem(resource.restype().extension.upper()),
            ]
        )

    def resource_from_indexes(
        self,
        indexes: list[QModelIndex],
        *,
        proxy: bool = True,
    ) -> list[FileResource]:
        """Get the resources from the resource model.

        Args:
        ----
            indexes (list[QModelIndex]): The indexes to get the resources from.
            proxy (bool): Whether to use the proxy model.

        Returns:
        ----
            The resources from the resource model.
        """
        items: list[QStandardItem] = []
        for index in indexes:
            source_index = self._proxy_model.mapToSource(index) if proxy else index
            items.append(self.itemFromIndex(source_index))
        return self.resource_from_items(items)

    def resource_from_items(
        self,
        items: list[QStandardItem],
    ) -> list[FileResource]:
        """Get the resources from the resource model.

        Args:
        ----
            items (list[QStandardItem]): The items to get the resources from.

        Returns:
        ----
            The resources from the resource model.
        """
        return [item.resource for item in items if isinstance(item, ResourceStandardItem)]  # pyright: ignore[reportAttributeAccessIssue]

    def all_resources_items(self) -> list[QStandardItem]:
        """Get all the resource items from the resource model.

        Returns:
        ----
            A list of all QStandardItem objects in the model that represent resource files.
        """
        resources = (category.child(i, 0) for category in self._category_items.values() for i in range(category.rowCount()))
        return [item for item in resources if item is not None]

    def remove_unused_categories(self):
        """Remove unused categories from the resource model."""
        for row in range(self.rowCount())[::-1]:
            item = self.item(row)
            if item.rowCount() != 0:
                continue
            text = item.text()
            if text not in self._category_items:
                continue
            del self._category_items[text]
            self.removeRow(row)


class TextureList(MainWindowList):
    """A list widget for displaying tpc/tga textures, providing functionality to load images without blocking the UI."""

    request_reload: Signal = Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    request_refresh: Signal = Signal()  # pyright: ignore[reportPrivateImportUsage]
    icon_loaded: Signal = Signal(object)  # pyright: ignore[reportPrivateImportUsage]

    BLANK_IMAGE: QImage = QImage(bytes(0 for _ in range(64 * 64 * 3)), 64, 64, QImage.Format.Format_RGB888)

    def __init__(self, parent: QWidget):
        """Initialize the texture list."""
        super().__init__(parent)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.widgets.texture_list import (
                Ui_Form,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.widgets.texture_list import (
                Ui_Form,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.widgets.texture_list import (
                Ui_Form,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.widgets.texture_list import (
                Ui_Form,  # noqa: PLC0415  # pylint: disable=C0415
            )
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setup_signals()

        self._installation: HTInstallation | None = None

        self.texture_models: defaultdict[str, QStandardItemModel] = defaultdict(QStandardItemModel)
        self.textures_proxy_model: QSortFilterProxyModel = QSortFilterProxyModel()
        self.textures_proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.resourceList.setModel(self.textures_proxy_model)  # type: ignore[arg-type]
        self.ui.resourceList.setIconSize(QSize(64, 64))  # pyright: ignore[reportArgumentType]

        self.section_model: QStandardItemModel = QStandardItemModel()
        self.ui.sectionCombo.setModel(self.section_model)  # type: ignore[arg-type]

        self._executor: ProcessPoolExecutor = ProcessPoolExecutor(max_workers=GlobalSettings().max_child_processes)

        self.ui.resourceList.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)  # pyright: ignore[reportArgumentType]
        self.ui.resourceList.customContextMenuRequested.connect(self.show_context_menu)
        self._loading_resources: set[FileResource] = set()

    def __del__(self):
        """Shutdown the executor when the texture list is deleted."""
        self._executor.shutdown(wait=False)

    def setup_signals(self):
        """Setup the signals for the texture list."""
        self.ui.searchEdit.textEdited.connect(self.on_filter_string_updated)
        self.ui.sectionCombo.currentIndexChanged.connect(self.on_section_changed)
        self.ui.resourceList.doubleClicked.connect(self.on_resource_double_clicked)

        vert_scroll_bar: QScrollBar | None = self.ui.resourceList.verticalScrollBar()  # pyright: ignore[reportAssignmentType]
        assert vert_scroll_bar is not None
        vert_scroll_bar.valueChanged.connect(self.queue_load_visible_icons)
        self.ui.searchEdit.textChanged.connect(self.queue_load_visible_icons)
        self.icon_loaded.connect(self.on_icon_loaded)

    def show_context_menu(self, position: QPoint):
        """Show the context menu for the texture list."""
        menu = QMenu(self)
        reload_action = menu.addAction("Reload")
        reload_action.triggered.connect(self.on_reload_clicked)
        action = menu.exec_(self.ui.resourceList.mapToGlobal(position))  # pyright: ignore[reportArgumentType, reportCallIssue]
        if action != reload_action:
            return
        index = self.ui.resourceList.indexAt(position)  # pyright: ignore[reportArgumentType]
        if not index.isValid():
            return
        source_index = self.textures_proxy_model.mapToSource(index)  # pyright: ignore[reportArgumentType]
        if not source_index.isValid():
            return
        section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        item = self.texture_models[section_name].itemFromIndex(source_index)
        self.offload_texture_load(item, reload=True)

    def resizeEvent(self, a0: QResizeEvent):  # pylint: disable=W0613
        """Ensures icons that come into view are queued to load when the widget is resized."""
        QTimer.singleShot(0, self.queue_load_visible_icons)

    def showEvent(self, a0: QShowEvent):  # pylint: disable=W0613
        """Ensures icons that come into view are queued to load when the widget is shown."""
        QTimer.singleShot(0, self.queue_load_visible_icons)

    def mouseMoveEvent(self, event: QMouseEvent):  # pylint: disable=W0613
        """Prioritize loading textures for the currently hovered item."""
        super().mouseMoveEvent(event)
        global_pos = self.mapToGlobal(event.pos())
        proxy_index: QModelIndex = self.ui.resourceList.indexAt(self.ui.resourceList.mapFromGlobal(global_pos))  # pyright: ignore[reportAssignmentType, reportCallIssue, reportArgumentType]
        source_index: QModelIndex = self.map_to_source_index(proxy_index, self.ui.resourceList.model())  # pyright: ignore[reportArgumentType]
        section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        item: QStandardItem | None = self.texture_models[section_name].itemFromIndex(source_index)
        assert item is not None, "Could not find item in the texture model for row %d"
        self.offload_texture_load(item, reload=False)

    def set_resources(self, resources: list[FileResource]):
        """Set the resources to be displayed in the texture list."""
        section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        model: QStandardItemModel = self.texture_models[section_name]
        model.clear()

        for resource in resources:
            resname, restype = resource.resname(), resource.restype()
            if restype not in (ResourceType.TGA, ResourceType.TPC):
                continue
            item = ResourceStandardItem(resname, resource=resource)
            item.setData(resource, Qt.ItemDataRole.UserRole + 1)
            model.appendRow(item)

        self.ui.resourceList.setModel(model)  # pyright: ignore[reportArgumentType]

        self.queue_load_visible_icons()

    def set_sections(self, items: list[QStandardItem]):
        """Set the sections to be displayed in the texture list combobox."""
        current_sections: set[str] = {
            self.ui.sectionCombo.itemData(i, Qt.ItemDataRole.UserRole)
            for i in range(self.ui.sectionCombo.count())
        }
        new_sections: set[str] = {item.data(Qt.ItemDataRole.UserRole) for item in items}

        # Remove sections that are no longer present
        for section in current_sections - new_sections:
            del self.texture_models[section]

        self.ui.sectionCombo.clear()

        for item in items:
            section = item.data(Qt.ItemDataRole.UserRole)
            self.ui.sectionCombo.addItem(item.text(), section)
            if section not in self.texture_models:
                self.texture_models[section] = QStandardItemModel()

        # Set the model for the current section
        if self.ui.sectionCombo.count() > 0:
            current_section: str = self.ui.sectionCombo.itemData(0, Qt.ItemDataRole.UserRole)
            self.textures_proxy_model.setSourceModel(self.texture_models[current_section])

    @classmethod
    def get_selected_source_indexes(cls, resource_list: QAbstractItemView) -> list[QModelIndex]:
        """Retrieve the selected source indexes from the given resource list view.

        This method handles both direct model and proxy model scenarios, mapping
        proxy indexes to their source indexes when necessary.

        Args:
            resource_list (QAbstractItemView): The view containing the selected items.

        Returns:
            list[QModelIndex]: A list of valid source model indexes for the selected items.

        Note:
            - If the view uses a proxy model (QSortFilterProxyModel), the returned indexes
                will be mapped to their corresponding source model indexes.
            - Invalid source indexes are logged as warnings and excluded from the result.
        """
        return [
            source_index
            for source_index in (
                cls.map_to_source_index(index, resource_list.model())
                for index in resource_list.selectedIndexes()
            )
            if source_index.isValid()
        ]

    @staticmethod
    def map_to_source_index(index: QModelIndex, model: QAbstractItemModel) -> QModelIndex:
        """Map a proxy index to its corresponding source index.

        Args:
            index (QModelIndex): The index to map.
            model (QAbstractItemModel): The model containing the index.

        Returns:
            QModelIndex: The corresponding source index.

        Note:
            - If the model is a QSortFilterProxyModel, the index is mapped to its source.
            - If the resulting source index is invalid, a warning is logged.
        """
        source_index = (
            model.mapToSource(index)  # pyright: ignore[reportArgumentType]
            if isinstance(model, QSortFilterProxyModel)
            else index
        )
        if not source_index.isValid():
            RobustLogger().warning("Invalid source index for row %d", index.row())
        return source_index

    def selected_resources(self) -> list[FileResource]:
        """Get the user selected resources from the texture list."""
        section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        texture_model: QStandardItemModel = self.texture_models[section_name]
        resources: list[FileResource] = [
            item.data(Qt.ItemDataRole.UserRole + 1)
            for index in self.get_selected_source_indexes(self.ui.resourceList)  # pyright: ignore[reportArgumentType]
            for item in [texture_model.itemFromIndex(index)]
            if item is not None
        ]
        return resources

    @staticmethod
    def visible_indexes(view: QAbstractItemView) -> list[QModelIndex]:
        """Get the visible indexes from the resource list utilizing the viewport."""
        if not view.isVisible() or view.model().rowCount() == 0:
            return []

        visible_rect = view.viewport().rect()  # pyright: ignore[reportOptionalMemberAccess]

        model = view.model()
        visible_indexes: list[QModelIndex] = []
        for row in range(model.rowCount()):
            idx = model.index(row, 0)
            src_idx = (
                model.mapToSource(idx)  # pyright: ignore[reportArgumentType]
                if isinstance(model, QSortFilterProxyModel)
                else idx
            )
            if not view.visualRect(idx).intersects(visible_rect):  # pyright: ignore[reportArgumentType]
                continue
            if not src_idx.isValid():
                RobustLogger().warning("Could not find item in the texture model for row %d", row)
                continue
            visible_indexes.append(src_idx)

        return visible_indexes

    def on_filter_string_updated(self):
        """Handle the filter string update."""
        filter_string = self.ui.searchEdit.text()
        self.textures_proxy_model.setFilterFixedString(filter_string)

    def on_section_changed(self):
        """Handle the section combobox selection change."""
        section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        self.textures_proxy_model.setSourceModel(self.texture_models[section_name])
        self.section_changed.emit(section_name)

    def on_reload_clicked(self):
        """Handle the reload button click."""
        section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        for row in range(self.texture_models[section_name].rowCount()):
            item = self.texture_models[section_name].item(row)
            if item is None:
                RobustLogger().warning("Could not find item in the texture model for row %d", row)
                continue
            self.offload_texture_load(item, reload=True)

    def on_refresh_clicked(self):
        """Handle the refresh button click."""
        section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        for row in range(self.texture_models[section_name].rowCount()):
            item = self.texture_models[section_name].item(row)
            if item is None:
                RobustLogger().warning("Could not find item in the texture model for row %d", row)
                continue
            self.offload_texture_load(item, reload=False)
            self.ui.resourceList.update(item.index())  # pyright: ignore[reportArgumentType]
        viewport: QWidget | None = self.ui.resourceList.viewport()  # pyright: ignore[reportAssignmentType]
        assert viewport is not None, "Could not find viewport for resource list"
        viewport.update(0, 0, viewport.width(), viewport.height())

    def queue_load_visible_icons(self):
        """Queue the loading of icons for visible items."""
        visible_indexes = self.visible_indexes(self.ui.resourceList)  # pyright: ignore[reportArgumentType]
        if not visible_indexes:
            return
        section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        for index in visible_indexes:
            item = self.texture_models[section_name].itemFromIndex(index)
            if item is None:
                RobustLogger().warning("Could not find item in the texture model for row %d", index.row())
                continue
            self.offload_texture_load(item, reload=False)

    def offload_texture_load(
        self,
        item: QStandardItem,
        desired_mipmap: int = 64,
        *,
        reload: bool = False,
    ):
        """Queue the loading of an icon for a given item."""
        section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        resource: Any = item.data(Qt.ItemDataRole.UserRole + 1)
        assert isinstance(resource, FileResource), f"Expected FileResource, got {type(resource).__name__}"
        if reload:
            self._loading_resources.discard(resource)
        if resource in self._loading_resources:
            return
        self._loading_resources.add(resource)
        row = item.row()
        try:
            future = self._executor.submit(get_image_from_resource, (section_name, row), resource, desired_mipmap)
        except BrokenProcessPool as e:
            RobustLogger().warning("Process pool is broken, recreating...", exc_info=e)
            self._executor = ProcessPoolExecutor(max_workers=GlobalSettings().max_child_processes)
            future = self._executor.submit(get_image_from_resource, (section_name, row), resource, desired_mipmap)
        future.add_done_callback(self.icon_loaded.emit)

    def on_icon_loaded(
        self,
        future: Future[tuple[tuple[str, int], TPCGetResult]],
    ):
        """Handle the completion of an icon load."""
        item_context, tpc_get_result = future.result()
        section_name, row = item_context
        item: QStandardItem | None = self.texture_models[section_name].item(row)
        if item is None:
            RobustLogger().warning("Could not find item in the texture model for row %d", row)
            return
        item.setIcon(tpc_get_result.to_qicon())
        self.ui.resourceList.update(item.index())  # pyright: ignore[reportArgumentType]

    def on_resource_double_clicked(self):
        """Handle the double click event on a resource."""
        selected = self.selected_resources()
        if not selected:
            RobustLogger().warning("No resources selected in texture list for double click event")
            return
        self.request_open_resource.emit(selected, None)


T = TypeVar("T")


def get_image_from_resource(
    context: T,
    resource: FileResource,
    desired_mipmap: int = 64,
) -> tuple[T, TPCGetResult]:
    """Get an image from a resource."""
    if resource.restype() is ResourceType.TPC:
        tpc = read_tpc(resource.data())
        best_mipmap = next((i for i in range(tpc.mipmap_count()) if tpc.get(i).width <= desired_mipmap), 0)
        width, height, data = tpc.convert(TPCTextureFormat.RGBA, best_mipmap)
        return context, TPCGetResult(width, height, TPCTextureFormat.RGBA, data)

    try:
        from PIL import Image

        if resource.restype().extension.lower() in Image.registered_extensions():
            with Image.open(BytesIO(resource.data())) as img:
                pil_img = img.convert("RGBA")
            return context, TPCGetResult(pil_img.width, pil_img.height, TPCTextureFormat.RGBA, pil_img.tobytes())
    except ImportError:  # noqa: S110
        RobustLogger().warning(f"Pillow not available for resource type: {resource.restype()!r}")

    try:
        from qtpy.QtCore import Qt  # pylint: disable=redefined-outer-name,reimported
        from qtpy.QtGui import QImage, QImageReader  # pylint: disable=redefined-outer-name,reimported

        if resource.restype().extension.lower() in [
            bytes(x.data()).decode().lower()
            for x in QImageReader.supportedImageFormats()
        ]:
            qimg = QImage()
            if qimg.loadFromData(resource.data()):
                qimg = qimg.convertToFormat(QImage.Format.Format_RGBA8888)
                if (
                    desired_mipmap < qimg.width()
                    or desired_mipmap < qimg.height()
                ):
                    qimg = qimg.scaled(desired_mipmap, desired_mipmap, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                return context, TPCGetResult(
                    qimg.width(),
                    qimg.height(),
                    TPCTextureFormat.RGBA,
                    bytes(qimg.constBits().asarray()),
                )
        else:  # use QFileIconProvider
            icon_provider: QFileIconProvider = QFileIconProvider()
            icon: QIcon = icon_provider.icon(QFileInfo(str(resource.filepath())))
            pixmap: QPixmap = icon.pixmap(desired_mipmap, desired_mipmap)
            qimg: QImage = pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
            return context, TPCGetResult(
                qimg.width(),
                qimg.height(),
                TPCTextureFormat.RGBA,
                bytes(qimg.constBits().asarray()),
            )
    except ImportError:  # noqa: S110
        RobustLogger().warning(f"Qt not available for resource type: {resource.restype()!r}")

    raise ValueError(f"No suitable image processing library available for resource type: {resource!r}")
