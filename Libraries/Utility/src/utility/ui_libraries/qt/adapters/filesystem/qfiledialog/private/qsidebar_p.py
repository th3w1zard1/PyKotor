from __future__ import annotations

import os

from typing import TYPE_CHECKING, Any, Iterable, cast

from qtpy.QtCore import (
    QDir,
    QEvent,
    QFileInfo,
    QItemSelectionModel,
    QMimeData,
    QModelIndex,
    QPersistentModelIndex,
    QSize,
    QUrl,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import (
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QIcon,
    QKeyEvent,
    QStandardItemModel,
)
from qtpy.QtWidgets import QAbstractItemView, QAbstractScrollArea, QFileIconProvider, QFileSystemModel, QListView, QMenu, QStyle, QStyledItemDelegate

if TYPE_CHECKING:
    from qtpy.QtCore import QModelIndex, QObject, QPoint
    from qtpy.QtGui import QDragEnterEvent, QFocusEvent
    from qtpy.QtWidgets import QStyleOptionViewItem, QWidget  # pyright: ignore[reportPrivateImportUsage]


class QSideBarDelegate(QStyledItemDelegate):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

    def initStyleOption(self, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        super().initStyleOption(option, index)
        value = index.data(QUrlModel.EnabledRole)
        if value is not None and not value:
            option.state &= ~QStyle.StateFlag.State_Enabled  # pyright: ignore[reportAttributeAccessIssue]


class QUrlModel(QStandardItemModel):
    """QUrlModel lets you have indexes from a QFileSystemModel to a list.  When QFileSystemModel
    changes them QUrlModel will automatically update.

    Example usage: File dialog sidebar and combo box
    """

    UrlRole = Qt.ItemDataRole.UserRole + 1
    EnabledRole = Qt.ItemDataRole.UserRole + 2

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.showFullPath = False
        self.fileSystemModel: QFileSystemModel | None = None
        self.watching: list[QUrlModel.WatchItem] = []
        self.invalidUrls: list[QUrl] = []

    def mimeTypes(self) -> list[str]:
        return ["text/uri-list"]

    def flags(self, index: QModelIndex) -> Qt.ItemFlag | Qt.ItemFlags:  # pyright: ignore[reportIncompatibleMethodOverride]
        flags = super().flags(index)
        if index.isValid():
            flags &= ~Qt.ItemFlag.ItemIsEditable
            flags &= ~Qt.ItemFlag.ItemIsDropEnabled

        if index.data(Qt.ItemDataRole.DecorationRole) is None:
            flags &= ~Qt.ItemFlag.ItemIsEnabled

        return flags

    def mimeData(self, indexes: Iterable[QModelIndex]) -> QMimeData:
        list_: list[QUrl] = []
        for index in indexes:
            if index.column() == 0:
                list_.append(index.data(self.UrlRole))  # noqa: PERF401
        data = QMimeData()
        data.setUrls(list_)
        return data

    def canDrop(self, event: QDragEnterEvent) -> bool:
        if self.mimeTypes()[0] not in event.mimeData().formats():
            return False

        list_ = event.mimeData().urls()
        assert self.fileSystemModel is not None, "fileSystemModel is None"
        for url in list_:
            idx = self.fileSystemModel.index(url.toLocalFile())
            if not self.fileSystemModel.isDir(idx):
                return False
        return True

    def dropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex,
    ) -> bool:
        if self.mimeTypes()[0] not in data.formats():
            return False
        self.addUrls(data.urls(), row)
        return True

    def setData(
        self,
        index: QModelIndex,
        value: Any,
        role: int = Qt.ItemDataRole.EditRole,
    ) -> bool:
        if isinstance(value, QUrl):
            url = value
            assert self.fileSystemModel is not None, "fileSystemModel is None"
            dirIndex = self.fileSystemModel.index(url.toLocalFile())
            if self.showFullPath:
                super().setData(index, QDir.toNativeSeparators(self.fileSystemModel.data(dirIndex, QFileSystemModel.Roles.FilePathRole)))
            else:
                super().setData(index, QDir.toNativeSeparators(self.fileSystemModel.data(dirIndex, QFileSystemModel.Roles.FilePathRole)), Qt.ItemDataRole.ToolTipRole)
                super().setData(index, self.fileSystemModel.data(dirIndex))
            super().setData(index, self.fileSystemModel.data(dirIndex, Qt.ItemDataRole.DecorationRole),
                            Qt.ItemDataRole.DecorationRole)
            super().setData(index, url, self.UrlRole)
            return True
        return super().setData(index, value, role)

    def setUrl(
        self,
        index: QModelIndex,
        url: QUrl,
        dirIndex: QModelIndex,  # noqa: N803
    ):
        self.setData(index, url, self.UrlRole)
        if not url.path().strip():
            assert self.fileSystemModel is not None, "fileSystemModel is None"
            self.setData(index, self.fileSystemModel.myComputer())
            self.setData(index, self.fileSystemModel.myComputer(Qt.ItemDataRole.DecorationRole), Qt.ItemDataRole.DecorationRole)
        else:
            if self.showFullPath:
                newName = QDir.toNativeSeparators(dirIndex.data(QFileSystemModel.Roles.FilePathRole))
            else:
                newName = dirIndex.data()

            assert self.fileSystemModel is not None, "fileSystemModel is None"
            newIcon = dirIndex.data(Qt.ItemDataRole.DecorationRole)
            if not dirIndex.isValid():
                provider = self.fileSystemModel.iconProvider()
                if provider:
                    newIcon = provider.icon(QFileIconProvider.IconType.Folder)
                newName = QFileInfo(url.toLocalFile()).fileName()
                if url not in self.invalidUrls:
                    self.invalidUrls.append(url)
                self.setData(index, False, self.EnabledRole)  # noqa: FBT003
            else:
                self.setData(index, True, self.EnabledRole)  # noqa: FBT003

            size = newIcon.actualSize(QSize(32, 32))
            if size.width() < 32:  # noqa: PLR2004
                smallPixmap = newIcon.pixmap(QSize(32, 32))
                newIcon.addPixmap(smallPixmap.scaledToWidth(32, Qt.TransformationMode.SmoothTransformation))

            if index.data() != newName:
                self.setData(index, newName)
            oldIcon = cast(QIcon, index.data(Qt.ItemDataRole.DecorationRole))
            if oldIcon.cacheKey() != newIcon.cacheKey():
                self.setData(index, newIcon, Qt.ItemDataRole.DecorationRole)

    def setUrls(self, list_: list[QUrl]):
        self.removeRows(0, self.rowCount())
        self.invalidUrls.clear()
        self.watching.clear()
        self.addUrls(list_, 0)

    def addUrls(
        self,
        list_: list[QUrl],
        row: int,
        *,
        move: bool = True,
    ):
        if row == -1:
            row = self.rowCount()
        row = min(row, self.rowCount())
        assert self.fileSystemModel is not None, "fileSystemModel is None"
        for it in reversed(list_):
            url = it
            if not url.isValid() or url.scheme() != "file":
                continue
            cleanUrl = QDir.cleanPath(url.toLocalFile())
            if not cleanUrl:
                continue
            url = QUrl.fromLocalFile(cleanUrl)

            for j in range(self.rowCount()):
                if move:
                    local = cast(QUrl, self.index(j, 0).data(self.UrlRole)).toLocalFile()
                    if (
                        cleanUrl.casefold() == local.casefold()
                        if os.name == "nt"
                        else cleanUrl == local
                    ):
                        self.removeRow(j)
                        if j <= row:
                            row -= 1
                        break
            row = max(row, 0)
            idx = self.fileSystemModel.index(cleanUrl)
            if not self.fileSystemModel.isDir(idx):
                continue
            self.insertRows(row, 1)
            self.setUrl(self.index(row, 0), url, idx)
            self.watching.append(self.WatchItem(idx, cleanUrl))

    def urls(self) -> list[QUrl]:
        list_: list[QUrl] = []
        for i in range(self.rowCount()):
            list_.append(self.data(self.index(i, 0), self.UrlRole))  # noqa: PERF401
        return list_

    def setFileSystemModel(self, model: QFileSystemModel):
        if model == self.fileSystemModel:
            return
        if self.fileSystemModel is not None:
            self.fileSystemModel.dataChanged.disconnect(self.dataChanged)
            self.fileSystemModel.layoutChanged.disconnect(self.layoutChanged)
            self.fileSystemModel.rowsRemoved.disconnect(self.layoutChanged)
        self.fileSystemModel = model
        if self.fileSystemModel is not None:
            self.fileSystemModel.dataChanged.connect(self.dataChanged)
            self.fileSystemModel.layoutChanged.connect(self.layoutChanged)
            self.fileSystemModel.rowsRemoved.connect(self.layoutChanged)
        self.clear()
        self.insertColumns(0, 1)

    def dataChanged(self, topLeft: QModelIndex, bottomRight: QModelIndex):  # noqa: N803
        parent = topLeft.parent()
        for i in range(len(self.watching)):
            index = self.watching[i].index
            if (
                index.row() >= topLeft.row()
                and index.row() <= bottomRight.row()
                and index.column() >= topLeft.column()
                and index.column() <= bottomRight.column()
                and index.parent() == parent
            ):
                self.changed(self.watching[i].path)

    def layoutChanged(self):
        paths: list[str] = [item.path for item in self.watching]
        self.watching.clear()
        assert self.fileSystemModel is not None, "fileSystemModel is None"
        for path in paths:
            newIndex = self.fileSystemModel.index(path)
            self.watching.append(self.WatchItem(newIndex, path))
            if newIndex.isValid():
                self.changed(path)

    def changed(self, path: str):
        for i in range(self.rowCount()):
            idx = self.index(i, 0)
            if cast(QUrl, idx.data(self.UrlRole)).toLocalFile() == path:
                self.setData(idx, idx.data(self.UrlRole))

    class WatchItem:  # noqa: D106
        def __init__(self, index: QModelIndex, path: str):
            self.index: QModelIndex = index
            self.path: str = path


class QSidebar(QListView):
    goToUrl = Signal(QUrl)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.urlModel: QUrlModel | None = None

    def urls(self) -> list[QUrl]:
        assert self.urlModel is not None, f"{type(self).__name__}.urls: No URL model setup."
        return self.urlModel.urls()

    def setUrls(self, urls: list[QUrl]) -> None:
        assert self.urlModel is not None, f"{type(self).__name__}.setUrls: No URL model setup."
        self.urlModel.setUrls(urls)

    def setModelAndUrls(self, model: QFileSystemModel, newUrls: list[QUrl]) -> None:  # noqa: N803
        self.setUniformItemSizes(True)
        self.urlModel = QUrlModel(self)
        self.urlModel.setFileSystemModel(model)
        self.setModel(self.urlModel)
        self.setItemDelegate(QSideBarDelegate(self))

        self.selectionModel().currentChanged.connect(self.clicked)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.urlModel.setUrls(newUrls)
        self.setCurrentIndex(self.model().index(0, 0))

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self.urlModel and self.urlModel.canDrop(event):
            QListView.dragEnterEvent(self, event)

    def sizeHint(self) -> QSize:
        if self.model():
            return self.sizeHintForIndex(self.model().index(0, 0)) + QSize(
                2 * self.frameWidth(), 2 * self.frameWidth()
            )
        return QListView.sizeHint(self)

    def selectUrl(self, url: QUrl) -> None:
        self.selectionModel().currentChanged.disconnect(self.clicked)
        self.selectionModel().clear()
        for i in range(self.model().rowCount()):
            if self.model().index(i, 0).data(QUrlModel.UrlRole) == url:
                self.selectionModel().select(self.model().index(i, 0), QItemSelectionModel.SelectionFlag.Select)
                break
        self.selectionModel().currentChanged.connect(self.clicked)

    def showContextMenu(self, position: QPoint) -> None:
        actions: list[QAction] = []
        if self.indexAt(position).isValid():
            action = QAction(self.tr("Remove"), self)
            if cast(QUrl, self.indexAt(position).data(QUrlModel.UrlRole)).path().strip():
                action.setEnabled(False)
            action.triggered.connect(self.removeEntry)
            actions.append(action)
        if actions:
            QMenu.exec(actions, self.mapToGlobal(position))

    def removeEntry(self) -> None:
        indexes: list[QModelIndex] = self.selectionModel().selectedIndexes()
        persistent_indexes: list[QPersistentModelIndex] = [QPersistentModelIndex(idx) for idx in indexes]
        for persistent in persistent_indexes:
            if not cast(QUrl, persistent.data(QUrlModel.UrlRole)).path().strip():
                self.model().removeRow(persistent.row())

    def clicked(self, index: QModelIndex) -> None:
        url = self.model().index(index.row(), 0).data(QUrlModel.UrlRole)
        self.goToUrl.emit(url)
        self.selectUrl(url)

    def focusInEvent(self, event: QFocusEvent) -> None:
        QAbstractScrollArea.focusInEvent(self, event)
        self.viewport().update()

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.KeyRelease:
            key_event = cast(QKeyEvent, event)
            if key_event.key() == Qt.Key.Key_Delete:
                self.removeEntry()
                return True
        return QListView.event(self, event)