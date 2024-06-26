from __future__ import annotations

import multiprocessing

from abc import abstractmethod
from time import sleep
from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtCore import QPoint, QSortFilterProxyModel, QThread, QTimer, Qt
from qtpy.QtGui import (
    QCursor,
    QIcon,
    QImage,
    QPixmap,
    QStandardItem,
    QStandardItemModel,
    QTransform,
)
from qtpy.QtWidgets import QHeaderView, QMenu, QToolTip, QWidget

from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.tpc import TPC, TPCTextureFormat
from toolset.gui.dialogs.load_from_location_result import ResourceItems
from utility.error_handling import format_exception_with_variables
from utility.logger_util import RobustRootLogger

if TYPE_CHECKING:
    from qtpy.QtCore import QModelIndex
    from qtpy.QtGui import (
        QMouseEvent,
        QResizeEvent,
    )

    from pykotor.common.misc import CaseInsensitiveDict
    from pykotor.extract.file import FileResource
    from pykotor.resource.type import ResourceType
    from toolset.data.installation import HTInstallation


class MainWindowList(QWidget):
    requestOpenResource = QtCore.Signal(object, object)
    requestExtractResource = QtCore.Signal(object)
    sectionChanged = QtCore.Signal(object)

    @abstractmethod
    def selectedResources(self) -> list[FileResource]: ...


class ResourceList(MainWindowList):
    requestReload = QtCore.Signal(object)
    requestRefresh = QtCore.Signal()

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
            from toolset.uic.pyside2.widgets.resource_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.widgets.resource_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.widgets.resource_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.widgets.resource_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setupSignals()

        self.modulesModel = ResourceModel()
        self.modulesModel.proxyModel().setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.ui.resourceTree.setModel(self.modulesModel.proxyModel())
        self.ui.resourceTree.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)

        self.sectionModel = QStandardItemModel()
        self.ui.sectionCombo.setModel(self.sectionModel)
        self.tooltipTimer = QTimer(self)
        self.tooltipTimer.setSingleShot(True)
        self.tooltipTimer.timeout.connect(self.showTooltip)
        self.tooltipText = ""
        self.setMouseTracking(True)
        self.ui.resourceTree.setMouseTracking(True)
        self.ui.resourceTree.viewport().installEventFilter(self)  # Install event filter on the viewport

    def eventFilter(self, obj, event):
        if obj is self.ui.resourceTree.viewport() and event.type() == QtCore.QEvent.MouseMove:
            self.mouseMoveEvent(event)
            return True
        return super().eventFilter(obj, event)

    def showTooltip(self):
        QToolTip.showText(QCursor.pos(), self.tooltipText, self.ui.resourceTree)

    def setupSignals(self):
        self.ui.searchEdit.textEdited.connect(self.onFilterStringUpdated)
        self.ui.sectionCombo.currentIndexChanged.connect(self.onSectionChanged)
        self.ui.reloadButton.clicked.connect(self.onReloadClicked)
        self.ui.refreshButton.clicked.connect(self.onRefreshClicked)
        self.ui.resourceTree.customContextMenuRequested.connect(self.onResourceContextMenu)
        self.ui.resourceTree.doubleClicked.connect(self.onResourceDoubleClicked)

    def enterEvent(self, event):
        self.tooltipTimer.stop()
        QToolTip.hideText()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.tooltipTimer.stop()
        QToolTip.hideText()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        index = self.ui.resourceTree.indexAt(event.pos())
        if index.isValid():
            # Retrieve the QStandardItem from the model using the index
            model_index = self.ui.resourceTree.model().mapToSource(index)  # Map proxy index to source index
            item = self.ui.resourceTree.model().sourceModel().itemFromIndex(model_index)
            if item is not None:
                resource: FileResource | None = getattr(item, "resource", None)
                if resource is not None:
                    self.tooltipText = str(resource.filepath())
                    self.tooltipPos = event.globalPos()
                    self.tooltipTimer.start(1100)  # Set the delay to 3000ms (3 seconds)
                else:
                    self.tooltipTimer.stop()
                    QToolTip.hideText()
            else:
                self.tooltipTimer.stop()
                QToolTip.hideText()
        else:
            self.tooltipTimer.stop()
            QToolTip.hideText()
        super().mouseMoveEvent(event)

    def hideReloadButton(self):
        self.ui.reloadButton.setVisible(False)

    def hideSection(self):
        self.ui.line.setVisible(False)
        self.ui.sectionCombo.setVisible(False)
        self.ui.refreshButton.setVisible(False)

    def currentSection(self) -> str:
        return self.ui.sectionCombo.currentData()

    def changeSection(
        self,
        section: str,
    ):
        for i in range(self.ui.sectionCombo.count()):
            if section in self.ui.sectionCombo.itemText(i):
                RobustRootLogger().debug("changing to section '%s'", section)
                self.ui.sectionCombo.setCurrentIndex(i)

    def setResources(
        self,
        resources: list[FileResource],
        customCategory: str | None = None,
        *,
        clear_existing: bool = True,
    ):
        """Adds and removes FileResources from the modules model.

        Args:
        ----
            resources: {list[FileResource]}: List of FileResource objects to set

        Processing Logic:
        ----------------
            - Loops through allResources and resources to find matching resources and update references
            - Loops through allResources to find non-matching resources and removes them
            - Removes any unused categories from the model.
        """
        allResources: list[QStandardItem] = self.modulesModel.allResourcesItems()

        # Convert the list of resources to a set for O(1) lookup times
        resourceSet: set[FileResource] = set(resources)

        # Create a mapping of existing resources to their items for quick access
        resourceItemMap: dict[FileResource, QStandardItem] = {item.resource: item for item in allResources}

        # Add or update resources
        for resource in resourceSet:
            if resource in resourceItemMap:
                # Update existing resource item
                resourceItemMap[resource].resource = resource
            else:
                # Add new resource
                self.modulesModel.addResource(resource, customCategory)

        if clear_existing:
            # Identify and remove non-matching resources if they are not in the updated resources set
            for item in allResources:
                if item.resource in resourceSet:
                    continue
                item.parent().removeRow(item.row())

        # Remove unused categories
        self.modulesModel.removeUnusedCategories()

    def setSections(
        self,
        sections: list[QStandardItem],
    ):
        self.sectionModel.clear()
        for section in sections:
            self.sectionModel.insertRow(self.sectionModel.rowCount(), section)

    def setResourceSelection(
        self,
        resource: FileResource,
    ):
        """Sets the selected resource in the resource tree.

        Args:
        ----
            resource (FileResource): The resource to select

        Processing Logic:
        ----------------
            - Loops through all resources in the model to find matching resource
            - Expands the parent item in the tree
            - Scrolls to and selects the matching child item.
        """
        model = self.ui.resourceTree.model().sourceModel()

        def select(parent, child):
            self.ui.resourceTree.expand(parent)
            self.ui.resourceTree.scrollTo(child)
            self.ui.resourceTree.setCurrentIndex(child)

        for item in model.allResourcesItems():
            resource_from_item: FileResource = item.resource
            if resource_from_item.identifier() == resource.identifier():
                _parentIndex = model.proxyModel().mapFromSource(item.parent().index())  # TODO: why is this unused
                itemIndex = model.proxyModel().mapFromSource(item.index())
                QTimer.singleShot(1, lambda index=itemIndex, item=item: select(item.parent().index(), index))

    def selectedResources(self) -> list[FileResource]:
        return self.modulesModel.resourceFromIndexes(self.ui.resourceTree.selectedIndexes())

    def onFilterStringUpdated(self):
        self.modulesModel.proxyModel().setFilterFixedString(self.ui.searchEdit.text())

    def onSectionChanged(self):
        self.sectionChanged.emit(self.ui.sectionCombo.currentData(QtCore.Qt.ItemDataRole.UserRole))

    def onReloadClicked(self):
        self.requestReload.emit(self.ui.sectionCombo.currentData(QtCore.Qt.ItemDataRole.UserRole))

    def onRefreshClicked(self):
        self.requestRefresh.emit()

    def onResourceContextMenu(self, point: QPoint):
        """Shows context menu for selected resources.

        an Installation/HTInstallation instance is not available in this code, that is emitted back to the ToolWindow.

        Args:
        ----
            point: QPoint - Mouse position for context menu
        """
        resources: list[FileResource] = self.selectedResources()
        if not resources:
            return
        menu = QMenu(self)
        menu.addAction("Open").triggered.connect(lambda: self.requestOpenResource.emit(resources, True))
        if all(resource.restype().contents == "gff" for resource in resources):
            menu.addAction("Open with GFF Editor").triggered.connect(lambda: self.requestOpenResource.emit(resources, False))
        menu.addSeparator()
        builder = ResourceItems(resources=resources)
        builder.viewport = lambda: self.ui.resourceTree
        builder.runContextMenu(point, menu=menu)
        #menu.popup(self.ui.resourceTree.mapToGlobal(point))

    def onResourceDoubleClicked(self):
        self.requestOpenResource.emit(self.selectedResources(), None)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.ui.resourceTree.setColumnWidth(1, 10)
        self.ui.resourceTree.setColumnWidth(0, self.ui.resourceTree.width() - 80)
        self.ui.resourceTree.header().setSectionResizeMode(QHeaderView.Fixed)


class ResourceModel(QStandardItemModel):
    """A data model used by the different trees (Core, Modules, Override).

    This class provides an easy way to add resources while sorting them into categories.
    """

    def __init__(self):
        super().__init__()
        self._categoryItems: dict[str, QStandardItem] = {}
        self._proxyModel = QSortFilterProxyModel(self)
        self._proxyModel.setSourceModel(self)
        self._proxyModel.setRecursiveFilteringEnabled(True)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["ResRef", "Type"])

    def proxyModel(self) -> QSortFilterProxyModel:
        return self._proxyModel

    def clear(self):
        super().clear()
        self._categoryItems = {}
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["ResRef", "Type"])

    def _addResourceIntoCategory(
        self,
        resourceType: ResourceType,
        customCategory: str | None = None,
    ) -> QStandardItem:
        chosen_category = resourceType.category if customCategory is None else customCategory
        if chosen_category not in self._categoryItems:
            categoryItem = QStandardItem(chosen_category)
            categoryItem.setSelectable(False)
            unusedItem = QStandardItem("")
            unusedItem.setSelectable(False)
            self._categoryItems[chosen_category] = categoryItem
            self.appendRow([categoryItem, unusedItem])
        return self._categoryItems[chosen_category]

    def addResource(
        self,
        resource: FileResource,
        customCategory: str | None = None,
    ):
        item1 = QStandardItem(resource.resname())
        item1.resource = resource
        #item1.setToolTip(str(resource.filepath()))
        item2 = QStandardItem(resource.restype().extension.upper())
        self._addResourceIntoCategory(resource.restype(), customCategory).appendRow([item1, item2])

    def resourceFromIndexes(
        self,
        indexes: list[QModelIndex],
        *,
        proxy: bool = True,
    ) -> list[FileResource]:
        items = []
        for index in indexes:
            sourceIndex = self._proxyModel.mapToSource(index) if proxy else index
            items.append(self.itemFromIndex(sourceIndex))
        return self.resourceFromItems(items)

    def resourceFromItems(
        self,
        items: list[QStandardItem],
    ) -> list[FileResource]:
        return [item.resource for item in items if hasattr(item, "resource")]  # type: ignore[reportAttributeAccessIssue]

    def allResourcesItems(self) -> list[QStandardItem]:
        """Returns a list of all QStandardItem objects in the model that represent resource files."""
        resources = (
            category.child(i, 0)
            for category in self._categoryItems.values()
            for i in range(category.rowCount())
        )
        return [item for item in resources if item is not None]

    def removeUnusedCategories(self):
        for row in range(self.rowCount())[::-1]:
            item = self.item(row)
            if item.rowCount() != 0:
                continue
            text = item.text()
            if text not in self._categoryItems:
                continue
            del self._categoryItems[text]
            self.removeRow(row)


class TextureList(MainWindowList):
    requestReload = QtCore.Signal(object)  # TODO:

    requestRefresh = QtCore.Signal()  # TODO:
    iconUpdate = QtCore.Signal(object, object)

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.widgets.texture_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.widgets.texture_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.widgets.texture_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.widgets.texture_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setupSignals()

        self._installation: HTInstallation | None = None
        self._scannedTextures: set[str] = set()

        self.texturesModel = QStandardItemModel()
        self.texturesProxyModel = QSortFilterProxyModel()
        self.texturesProxyModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.texturesProxyModel.setSourceModel(self.texturesModel)
        self.ui.resourceList.setModel(self.texturesProxyModel)

        self.sectionModel = QStandardItemModel()
        self.ui.sectionCombo.setModel(self.sectionModel)

        self._taskQueue = multiprocessing.JoinableQueue()
        self._resultQueue = multiprocessing.Queue()
        self._consumers: list[TextureListConsumer] = [TextureListConsumer(self._taskQueue, self._resultQueue) for _ in range(multiprocessing.cpu_count())]
        for consumer in self._consumers:
            consumer.start()

        self._scanner = QThread(self)
        self._scanner.run = self.scan
        self._scanner.start()

    def setupSignals(self):
        self.ui.searchEdit.textEdited.connect(self.onFilterStringUpdated)
        self.ui.sectionCombo.currentIndexChanged.connect(self.onSectionChanged)
        self.ui.resourceList.doubleClicked.connect(self.onResourceDoubleClicked)
        self.iconUpdate.connect(self.onIconUpdate)

        self.ui.resourceList.verticalScrollBar().valueChanged.connect(self.onTextureListScrolled)
        self.ui.searchEdit.textChanged.connect(self.onTextureListScrolled)

    def doTerminations(self):
        self._scanner.terminate()
        for consumer in self._consumers:
            consumer.terminate()

    def setInstallation(self, installation: HTInstallation):
        self._installation = installation

    def setResources(
        self,
        resources: list[FileResource],
    ):
        blankImage = QImage(bytes(0 for _ in range(64 * 64 * 3)), 64, 64, QImage.Format_RGB888)
        blankIcon = QIcon(QPixmap.fromImage(blankImage))

        self.texturesModel.clear()
        for resource in resources:
            item = QStandardItem(blankIcon, resource.resname())
            item.setToolTip(resource.resname())
            item.setData(False, QtCore.Qt.ItemDataRole.UserRole)
            item.setData(resource, QtCore.Qt.ItemDataRole.UserRole + 1)
            self.texturesModel.appendRow(item)

        if self._installation is not None:
            self.onTextureListScrolled()

    def setSections(
        self,
        sections: list[QStandardItem],
    ):
        self.sectionModel.clear()
        for section in sections:
            self.sectionModel.insertRow(self.sectionModel.rowCount(), section)

    def selectedResources(self) -> list[FileResource]:
        resources: list[FileResource] = []
        for proxyIndex in self.ui.resourceList.selectedIndexes():
            sourceIndex = self.texturesProxyModel.mapToSource(proxyIndex)
            item = self.texturesModel.item(sourceIndex.row())
            resources.append(item.data(QtCore.Qt.ItemDataRole.UserRole + 1))
        return resources

    def visibleItems(self) -> list[QStandardItem]:
        if self.texturesModel.rowCount() == 0:
            return []

        scanWidth: int = self.parent().width()
        scanHeight: int = self.parent().height()

        proxyModel = self.texturesProxyModel
        model = self.texturesModel

        firstItem = None
        firstIndex = None

        for y in range(2, 92, 2):
            for x in range(2, 92, 2):
                proxyIndex = self.ui.resourceList.indexAt(QPoint(x, y))
                index = proxyModel.mapToSource(proxyIndex)
                item = model.itemFromIndex(index)
                if not firstItem and item:
                    firstItem = item
                    firstIndex = proxyIndex
                    break

        items: list[QStandardItem] = []

        if firstItem:
            _startRow: int = firstItem.row()
            widthCount: int = scanWidth // 92
            heightCount: int = scanHeight // 92 + 2
            numVisible: int = min(proxyModel.rowCount(), widthCount * heightCount)

            for i in range(numVisible):
                proxyIndex: QModelIndex = proxyModel.index(firstIndex.row() + i, 0)
                sourceIndex: QModelIndex = proxyModel.mapToSource(proxyIndex)
                item: QStandardItem | None = model.itemFromIndex(sourceIndex)
                if item is not None:
                    items.append(item)

        return items

    def scan(self):
        while True:
            for row, _resname, width, height, data in iter(self._resultQueue.get, None):
                image = QImage(data, width, height, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(image).transformed(QTransform().scale(1, -1))
                item = self.texturesModel.item(row, 0)
                if item is not None:
                    self.iconUpdate.emit(item, QIcon(pixmap))

            sleep(0.1)

    def onFilterStringUpdated(self):
        self.texturesProxyModel.setFilterFixedString(self.ui.searchEdit.text())

    def onSectionChanged(self):
        self.sectionChanged.emit(self.ui.sectionCombo.currentData(QtCore.Qt.ItemDataRole.UserRole))

    def onReloadClicked(self):
        self.requestReload.emit(self.ui.sectionCombo.currentData(QtCore.Qt.ItemDataRole.UserRole))

    def onRefreshClicked(self):
        self.requestRefresh.emit()

    def onTextureListScrolled(self):
        if self._installation is None:
            print("No installation loaded, nothing to scroll through?")
            return
        # Note: Avoid redundantly loading textures that have already been loaded
        textures: CaseInsensitiveDict[TPC | None] = self._installation.textures(
            [item.text() for item in self.visibleItems() if item.text().casefold() not in self._scannedTextures],
            [SearchLocation.TEXTURES_GUI, SearchLocation.TEXTURES_TPA],
        )

        # Emit signals to load textures that have not had their icons assigned
        for item in iter(self.visibleItems()):
            if item.text().casefold() in self._scannedTextures:
                continue
            item_text = item.text()

            # Avoid trying to load the same texture multiple times.
            self._scannedTextures.add(item_text.casefold())

            cache_tpc: TPC | None = textures.get(item_text)
            tpc: TPC = TPC() if cache_tpc is None else cache_tpc

            task = TextureListTask(item.row(), tpc, item_text)
            self._taskQueue.put(task)
            item.setData(True, QtCore.Qt.ItemDataRole.UserRole)

    def onIconUpdate(
        self,
        item: QStandardItem,
        icon: QIcon | QPixmap,
    ):
        try:  # FIXME: there's a race condition happening somewhere, causing the item to have previously been deleted.
            item.setIcon(icon)
        except RuntimeError as e:
            print(format_exception_with_variables(e, message="This exception has been suppressed."))

    def onResourceDoubleClicked(self):
        self.requestOpenResource.emit(self.selectedResources(), None)

    def resizeEvent(self, a0: QResizeEvent):  # pylint: disable=W0613
        # Trigger the scroll slot method - this will cause any newly visible icons to load.
        self.onTextureListScrolled()


class TextureListConsumer(multiprocessing.Process):
    def __init__(
        self,
        taskQueue: multiprocessing.JoinableQueue,
        resultQueue: multiprocessing.Queue,
    ):
        multiprocessing.Process.__init__(self)
        self.taskQueue: multiprocessing.JoinableQueue = taskQueue
        self.resultQueue: multiprocessing.Queue = resultQueue
        self.stopLoop: bool = False

    def run(self):
        while not self.stopLoop:
            next_task = self.taskQueue.get()

            answer = next_task()
            self.taskQueue.task_done()
            self.resultQueue.put(answer)


class TextureListTask:
    def __init__(
        self,
        row: int,
        tpc: TPC,
        resname: str,
    ):
        self.row: int = row
        self.tpc: TPC = tpc
        self.resname: str = resname

    def __repr__(self):
        return str(self.row)

    def __call__(self, *args, **kwargs) -> tuple[int, str, int, int, bytearray]:
        width, height, data = self.tpc.convert(TPCTextureFormat.RGB, self.bestMipmap(self.tpc))
        return self.row, self.resname, width, height, data

    def bestMipmap(self, tpc: TPC) -> int:
        for i in range(tpc.mipmap_count()):
            size = tpc.get(i).width
            if size <= 64:
                return i
        return 0
