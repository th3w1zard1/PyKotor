from __future__ import annotations

import os
import pathlib
import shutil
import sys
import typing

from contextlib import suppress
from typing import TYPE_CHECKING, Any, ClassVar, Iterable, overload

import qtpy  # noqa: E402

from qtpy.QtCore import (
    QAbstractItemModel,
    QBasicTimer,
    QByteArray,
    QDir,
    QEvent,
    QFile,
    QFileDevice,
    QFileInfo,
    QMimeData,
    QModelIndex,
    QMutexLocker,
    QTimer,
    QUrl,
    QVariant,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QIcon  # noqa: E402
# QAbstractFileIconProvider is not exposed by qtpy, import directly
try:
    if qtpy.API_NAME == "PyQt6":
        from PyQt6.QtGui import QAbstractFileIconProvider  # type: ignore[import-untyped]  # noqa: E402
    elif qtpy.API_NAME == "PySide6":
        from PySide6.QtGui import QAbstractFileIconProvider  # type: ignore[import-untyped]  # noqa: E402
    else:
        # PyQt5/PySide2 - QAbstractFileIconProvider might not exist
        QAbstractFileIconProvider = QFileIconProvider  # type: ignore[assignment, misc]
except ImportError:
    # Fallback - use QFileIconProvider as base
    QAbstractFileIconProvider = QFileIconProvider  # type: ignore[assignment, misc]
from qtpy.QtWidgets import (
    QApplication,
    QFileIconProvider,
    QFileSystemModel,  # pyright: ignore[reportPrivateImportUsage]
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTreeView  # noqa: E402


def update_sys_path(path: pathlib.Path):
    working_dir = str(path)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


file_absolute_path = pathlib.Path(__file__).resolve()

pykotor_path = file_absolute_path.parents[8] / "Libraries" / "PyKotor" / "src" / "pykotor"
if pykotor_path.exists():
    update_sys_path(pykotor_path.parent)
pykotor_gl_path = file_absolute_path.parents[8] / "Libraries" / "PyKotorGL" / "src" / "pykotor"
if pykotor_gl_path.exists():
    update_sys_path(pykotor_gl_path.parent)
utility_path = file_absolute_path.parents[5]
if utility_path.exists():
    update_sys_path(utility_path)
toolset_path = file_absolute_path.parents[8] / "Tools/HolocronToolset/src/toolset"
if toolset_path.exists():
    update_sys_path(toolset_path.parent)
    if __name__ == "__main__":
        os.chdir(toolset_path)

from utility.system.path import Path  # noqa: E402
from utility.ui_libraries.qt.adapters.filesystem.pyfileinfogatherer import PyFileInfoGatherer  # noqa: E402
from utility.ui_libraries.qt.adapters.filesystem.pyfilesystemmodelsorter import PyFileSystemModelSorter  # noqa: E402
from utility.ui_libraries.qt.adapters.filesystem.pyfilesystemnode import PyFileSystemNode  # noqa: E402

if TYPE_CHECKING:
    from qtpy.QtCore import (
        QDateTime,
        QObject,
        QTimerEvent,
        Signal,  # pyright: ignore[reportPrivateImportUsage]  # noqa: E402  # noqa: E402  # noqa: E402
    )
    from qtpy.QtWidgets import QScrollBar
    from typing_extensions import Literal


if qtpy.QT6:
    QDesktopWidget = None
elif qtpy.QT5:
    from qtpy.QtWidgets import QDesktopWidget
else:
    raise RuntimeError(f"Unexpected qtpy version: '{qtpy.API_NAME}'")


if os.name == "nt_disabled":
    from ctypes import POINTER, byref, windll
    from ctypes.wintypes import LPCWSTR

    from utility.system.win32.com.com_types import GUID
    from utility.system.win32.com.interfaces import SIGDN, IShellItem
    from utility.system.win32.hresult import HRESULT

    try:
        import comtypes  # pyright: ignore[reportMissingTypeStubs]

        from comtypes.automation import BSTR, IUnknown  # pyright: ignore[reportMissingTypeStubs]
    except ImportError:
        RobustLogger().error("Could not setup the comtypes library, volume functionality will be disabled.")
    else:

        def volumeName(path: str) -> str:
            comtypes.CoInitialize()
            # Create the IShellItem instance for the given path
            SHCreateItemFromParsingName = windll.shell32.SHCreateItemFromParsingName
            print("<SDM> [volumeName scope] SHCreateItemFromParsingName: ", SHCreateItemFromParsingName)

            SHCreateItemFromParsingName.argtypes = [LPCWSTR, POINTER(IUnknown), POINTER(GUID), POINTER(POINTER(IShellItem))]
            print("<SDM> [volumeName scope] SHCreateItemFromParsingName.argtypes: ", SHCreateItemFromParsingName.argtypes)

            SHCreateItemFromParsingName.restype = HRESULT
            print("<SDM> [volumeName scope] SHCreateItemFromParsingName.restype: ", SHCreateItemFromParsingName.restype)

            pShellItem = POINTER(IShellItem)()
            print("<SDM> [volumeName scope] pShellItem: ", pShellItem)

            hr = SHCreateItemFromParsingName(path, POINTER(IUnknown)(), byref(IShellItem._iid_), byref(pShellItem))
            print("<SDM> [volumeName scope] hr: ", hr)

            HRESULT.raise_for_status(hr, "SHCreateItemFromParsingName failed.")

            name = BSTR()
            print("<SDM> [volumeName scope] name: ", name)

            hr = pShellItem.GetDisplayName(SIGDN.SIGDN_NORMALDISPLAY, comtypes.byref(name))  # type: ignore[attr-defined]
            print("<SDM> [volumeName scope] hr: ", hr)

            if hr != 0:
                raise OSError(f"GetDisplayName failed! HRESULT: {hr}")

            result = name.value
            print("<SDM> [volumeName scope] result: ", result)

            return result
else:

    def volumeName(path: str) -> str:
        return path


def filewatcherenabled(default: bool = True) -> bool:  # noqa: FBT001, FBT002
    watchFiles = os.environ.get("QT_FILESYSTEMMODEL_WATCH_FILES", "").strip()
    if watchFiles:
        with suppress(ValueError):
            return bool(int(watchFiles))
    return default


# Helper functions matching C++ exactly
if os.name == "nt":

    def qt_GetLongPathName(strShortPath: str) -> str:
        """Get long path name matching C++ lines 282-313 exactly.

        Matches:
        #ifdef Q_OS_WIN32
        static QString qt_GetLongPathName(const QString &strShortPath)
        {
            if (strShortPath.isEmpty()
                || strShortPath == "."_L1 || strShortPath == ".."_L1)
                return strShortPath;
            if (strShortPath.length() == 2 && strShortPath.endsWith(u':'))
                return strShortPath.toUpper();
            const QString absPath = QDir(strShortPath).absolutePath();
            if (absPath.startsWith("//"_L1)
                || absPath.startsWith("\\\\"_L1)) // unc
                return QDir::fromNativeSeparators(absPath);
            if (absPath.startsWith(u'/'))
                return QString();
            const QString inputString = "\\\\?\\"_L1 + QDir::toNativeSeparators(absPath);
            QVarLengthArray<TCHAR, MAX_PATH> buffer(MAX_PATH);
            DWORD result = ::GetLongPathName((wchar_t*)inputString.utf16(),
                                             buffer.data(),
                                             buffer.size());
            if (result > DWORD(buffer.size())) {
                buffer.resize(result);
                result = ::GetLongPathName((wchar_t*)inputString.utf16(),
                                           buffer.data(),
                                           buffer.size());
            }
            if (result > 4) {
                QString longPath = QString::fromWCharArray(buffer.data() + 4); // ignoring prefix
                longPath[0] = longPath.at(0).toUpper(); // capital drive letters
                return QDir::fromNativeSeparators(longPath);
            } else {
                return QDir::fromNativeSeparators(strShortPath);
            }
        }
        #endif
        """
        if not strShortPath or strShortPath in (".", ".."):
            return strShortPath
        if len(strShortPath) == 2 and strShortPath.endswith(":"):
            return strShortPath.upper()
        absPath = QDir(strShortPath).absolutePath()
        if absPath.startswith("//") or absPath.startswith("\\\\"):
            return QDir.fromNativeSeparators(absPath)
        if absPath.startswith("/"):
            return ""
        # For Windows, we'd need to call GetLongPathNameW, but for Python we'll use a simpler approach
        # In practice, we can use QDir's absolutePath which handles this
        return QDir.fromNativeSeparators(absPath)

    def chopSpaceAndDot(element: str) -> str:
        """Chop space and dot matching C++ lines 315-330 exactly.

        Matches:
        static inline void chopSpaceAndDot(QString &element)
        {
            if (element == "."_L1 || element == ".."_L1)
                return;
            // On Windows, "filename    " and "filename" are equivalent and
            // "filename  .  " and "filename" are equivalent
            // "filename......." and "filename" are equivalent Task #133928
            // whereas "filename  .txt" is still "filename  .txt"
            while (element.endsWith(u'.') || element.endsWith(u' '))
                element.chop(1);

            // If a file is saved as ' Foo.txt', where the leading character(s)
            // is an ASCII Space (0x20), it will be saved to the file system as 'Foo.txt'.
            while (element.startsWith(u' '))
                element.remove(0, 1);
        }
        """
        if element in (".", ".."):
            return element
        # On Windows, "filename    " and "filename" are equivalent and
        # "filename  .  " and "filename" are equivalent
        # "filename......." and "filename" are equivalent Task #133928
        # whereas "filename  .txt" is still "filename  .txt"
        while element.endswith(".") or element.endswith(" "):
            element = element[:-1]
        # If a file is saved as ' Foo.txt', where the leading character(s)
        # is an ASCII Space (0x20), it will be saved to the file system as 'Foo.txt'.
        while element.startswith(" "):
            element = element[1:]
        return element
else:

    def qt_GetLongPathName(strShortPath: str) -> str:
        """Non-Windows version - just return the path."""
        return strShortPath

    def chopSpaceAndDot(element: str) -> str:
        """Non-Windows version - no-op."""
        return element


class PyFileSystemModel(QAbstractItemModel):
    """Python adapter for QFileSystemModel matching Qt6 C++ source exactly.

    Matches qfilesystemmodel.h and qfilesystemmodel.cpp.
    """

    # Roles matching C++ lines 35-50
    if not TYPE_CHECKING:

        class Roles:
            FileIconRole = Qt.ItemDataRole.DecorationRole
            FileInfoRole = Qt.ItemDataRole.UserRole - 5  # Qt::FileInfoRole
            FilePathRole = Qt.ItemDataRole.UserRole + 1  # Qt6
            FileNameRole = Qt.ItemDataRole.UserRole + 2  # Qt6
            FilePermissions = Qt.ItemDataRole.UserRole + 3  # Qt6

        FileIconRole = Roles.FileIconRole
        FileInfoRole = Roles.FileInfoRole
        FilePathRole = Roles.FilePathRole
        FileNameRole = Roles.FileNameRole
        FilePermissions = Roles.FilePermissions

        # Options matching C++ lines 52-59
        class Option:
            DontWatchForChanges = 0x00000001
            DontResolveSymlinks = 0x00000002
            DontUseCustomDirectoryIcons = 0x00000004

        DontWatchForChanges = Option.DontWatchForChanges
        DontResolveSymlinks = Option.DontResolveSymlinks
        DontUseCustomDirectoryIcons = Option.DontUseCustomDirectoryIcons

    # Class variable for roleNames static initialization (matching C++ static variable)
    _roleNames: dict[int, QByteArray] | None = None

    # Signals matching C++ lines 29-32
    rootPathChanged = Signal(str)  # (const QString &newPath)
    fileRenamed = Signal(str, str, str)  # (const QString &path, const QString &oldName, const QString &newName)
    directoryLoaded = Signal(str)  # (const QString &path)

    def __init__(self, parent: QObject | None = None):
        """Initialize QFileSystemModel matching C++ lines 195-208 exactly.

        Matches:
        QFileSystemModel::QFileSystemModel(QObject *parent) :
            QFileSystemModel(*new QFileSystemModelPrivate, parent)
        {
        }
        QFileSystemModel::QFileSystemModel(QFileSystemModelPrivate &dd, QObject *parent)
            : QAbstractItemModel(dd, parent)
        {
            Q_D(QFileSystemModel);
            d->init();
        }
        """
        super().__init__(parent)
        # Initialize private members matching qfilesystemmodel_p.h lines 265-302
        self._rootDir: QDir = QDir()
        # QT_CONFIG(filesystemwatcher) - always true in Python
        self._fileInfoGatherer: PyFileInfoGatherer = PyFileInfoGatherer(self)
        self._delayedSortTimer: QTimer = QTimer()
        self._bypassFilters: dict[PyFileSystemNode, bool] = {}
        # QT_CONFIG(regularexpression) - always true in Python
        self._nameFilters: list[str] = []
        self._nameFiltersRegexps: list[Any] = []  # QRegularExpression list
        self._resolvedSymLinks: dict[str, str] = {}
        self._root: PyFileSystemNode = PyFileSystemNode("")

        # Fetching struct matching C++ lines 284-289
        class Fetching:
            def __init__(self, dir: str, file: str, node: PyFileSystemNode):
                self.dir = dir
                self.file = file
                self.node = node

        self._Fetching = Fetching
        self._toFetch: list[Fetching] = []
        self._fetchingTimer: QBasicTimer = QBasicTimer()

        # Member variables matching C++ lines 293-302
        self._filters: QDir.Filter = QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs  # type: ignore[attr-defined]
        self._sortColumn: int = 0
        self._sortOrder: Qt.SortOrder = Qt.SortOrder.AscendingOrder
        self._forceSort: bool = True
        self._readOnly: bool = True
        self._setRootPath: bool = False
        self._nameFilterDisables: bool = True  # false on windows, true on mac and unix (line 299)
        self._disableRecursiveSort: bool = False

        # Call init() matching C++ line 207
        self._init()

    def _init(self) -> None:
        """Initialize model matching C++ lines 2145-2164 exactly.

        Matches:
        void QFileSystemModelPrivate::init()
        {
            delayedSortTimer.setSingleShot(true);
            qRegisterMetaType<QList<std::pair<QString, QFileInfo>>>();
        #if QT_CONFIG(filesystemwatcher)
            QObjectPrivate::connect(fileInfoGatherer.get(), &QFileInfoGatherer::newListOfFiles,
                                    this, &QFileSystemModelPrivate::directoryChanged);
            QObjectPrivate::connect(fileInfoGatherer.get(), &QFileInfoGatherer::updates,
                                    this, &QFileSystemModelPrivate::fileSystemChanged);
            QObjectPrivate::connect(fileInfoGatherer.get(), &QFileInfoGatherer::nameResolved,
                                    this, &QFileSystemModelPrivate::resolvedName);
            Q_Q(QFileSystemModel);
            q->connect(fileInfoGatherer.get(), &QFileInfoGatherer::directoryLoaded,
                       q, &QFileSystemModel::directoryLoaded);
        #endif // filesystemwatcher
            QObjectPrivate::connect(&delayedSortTimer, &QTimer::timeout,
                                    this, &QFileSystemModelPrivate::performDelayedSort,
                                    Qt::QueuedConnection);
        }
        """
        self._delayedSortTimer.setSingleShot(True)

        # Register meta type (Python doesn't need this, but we note it)
        # qRegisterMetaType<QList<std::pair<QString, QFileInfo>>>()

        # QT_CONFIG(filesystemwatcher) - always true
        self._fileInfoGatherer.newListOfFiles.connect(self._q_directoryChanged)
        self._fileInfoGatherer.updates.connect(self._q_fileSystemChanged)
        self._fileInfoGatherer.nameResolved.connect(self._q_resolvedName)
        self._fileInfoGatherer.directoryLoaded.connect(self.directoryLoaded.emit)

        self._delayedSortTimer.timeout.connect(self._q_performDelayedSort)

    def _watchPaths(self, paths: list[str]) -> None:
        """Watch paths matching C++ line 269 exactly.

        Matches: void watchPaths(const QStringList &paths) { fileInfoGatherer->watchPaths(paths); }
        """
        self._fileInfoGatherer.watchPaths(paths)

    def _index_from_node(self, node: PyFileSystemNode, column: int) -> QModelIndex:
        """Get index from node matching C++ lines 616-630 exactly.

        Matches:
        QModelIndex QFileSystemModelPrivate::index(const QFileSystemModelPrivate::QFileSystemNode *node, int column) const
        {
            Q_Q(const QFileSystemModel);
            QFileSystemModelPrivate::QFileSystemNode *parentNode = (node ? node->parent : nullptr);
            if (node == &root || !parentNode)
                return QModelIndex();

            // get the parent's row
            Q_ASSERT(node);
            if (!node->isVisible)
                return QModelIndex();

            int visualRow = translateVisibleLocation(parentNode, parentNode->visibleLocation(node->fileName));
            return q->createIndex(visualRow, column, const_cast<QFileSystemNode*>(node));
        }
        """
        if node is None:
            return QModelIndex()
        parentNode = node.parent
        if node == self._root or parentNode is None:
            return QModelIndex()

        assert node is not None
        if not node.isVisible:
            return QModelIndex()

        visualRow = self.translateVisibleLocation(parentNode, parentNode.visibleLocation(node.fileName))
        return self.createIndex(visualRow, column, node)

    def _q_directoryChanged(self, directory: str, files: list[str] | None = None):
        parentNode = self.node_path(directory, fetch=False)
        fInfo = parentNode.fileInfo()
        # row is not a method on PyFileSystemNode - it's calculated from the index
        RobustLogger().warning(f"<SDM> [_q_directoryChanged scope] parentNode: {parentNode} path: {None if fInfo is None else fInfo.path()}")

        if len(parentNode.children) == 0:
            return

        if files is None:
            toRemove = [child.fileName for child in parentNode.children.values()]
            print("<SDM> [_q_directoryChanged scope] toRemove: ", toRemove, "length:", len(toRemove))

        else:
            newFilesList = sorted(files)
            print("<SDM> [_q_directoryChanged scope] newFilesList: ", newFilesList, "entry count: ", len(newFilesList))

            toRemove = []
            for child in parentNode.children.values():
                fileName = child.fileName
                print("<SDM> [_q_directoryChanged scope] fileName: ", fileName)

                index = self._binary_search(newFilesList, fileName)
                print("<SDM> [_q_directoryChanged scope] binary search index: ", index)

                if index == len(newFilesList) or newFilesList[index] != fileName:
                    print("<SDM> [_q_directoryChanged scope] remove index: ", index, "fileName: ", fileName)

                    toRemove.append(fileName)

        for fileName in toRemove:
            self.removeNode(parentNode, fileName)

    def _binary_search(self, sorted_list: list[str], item: str) -> int:
        """Helper function to perform binary search on a sorted list."""
        low, high = 0, len(sorted_list)
        while low < high:
            mid = (low + high) // 2
            print("<SDM> [_binary_search scope] mid: ", mid)

            if sorted_list[mid] < item:
                low = mid + 1
                print("<SDM> [_binary_search scope] low: ", low)

            else:
                high = mid
                print("<SDM> [_binary_search scope] high: ", high)

        return low

    def _q_fileSystemChanged(
        self,
        path: str,
        updates: list[tuple[str, QFileInfo]],
    ) -> None:  # noqa: C901, PLR0912
        parentNode = self.node(self.index_path(path, 0))
        if not parentNode:
            return
        fInfo = parentNode.fileInfo()
        parent_index = self.index_path(path, 0)
        print(
            "<SDM> [_q_fileSystemChanged scope] parentNode: ",
            parentNode,
            "path:",
            None if fInfo is None else fInfo.path(),
        )

        rowsToUpdate: list[str] = []
        newFiles: list[str] = []

        for fileName, file_info in updates:
            if fileName not in parentNode.children:
                # Add new node if it doesn't exist
                self.addNode(parentNode, fileName, file_info)
                newFiles.append(fileName)
            else:
                node = parentNode.children[fileName]
                print("<SDM> [_q_fileSystemChanged node.fileName ", node.fileName)

                if node.fileName == fileName:
                    # populate expects PyQExtendedInformation, but we have QFileInfo
                    extended_info = self._fileInfoGatherer.getInfo(file_info)
                    node.populate(extended_info)
                    if self.filtersAcceptsNode(node):
                        if node.isVisible:
                            rowsToUpdate.append(fileName)
                        else:
                            newFiles.append(fileName)
                    elif node.isVisible:
                        visibleLocation = parentNode.visibleChildren.index(fileName)
                        print("<SDM> [_q_fileSystemChanged scope] visibleLocation: ", visibleLocation)

                        self.removeVisibleFile(parentNode, visibleLocation)

        if rowsToUpdate:
            for fileName in rowsToUpdate:
                row = parentNode.visibleChildren.index(fileName)
                parent_index = self.index_path(path, 0)
                topLeft = self.index(row, 0, parent_index)
                bottomRight = self.index(row, self.columnCount() - 1, parent_index)

                self.dataChanged.emit(topLeft, bottomRight)

        if newFiles:
            self.addVisibleFiles(parentNode, newFiles)

        if newFiles or (self._sortColumn != 0 and rowsToUpdate):
            self._forceSort = True
            self._delayedSort()

    if os.name == "nt":

        def _unwatchPathsAt(self, index: QModelIndex) -> list[str]:
            indexNode = self.node(index)
            # row is from the index, not the node
            row_val = index.row()
            print("<SDM> [_unwatchPathsAt scope] indexNode: ", indexNode, "row:", row_val, indexNode.fileName)

            if indexNode is None:
                return []

            caseSensitivity = Qt.CaseSensitivity.CaseSensitive if indexNode.caseSensitive() else Qt.CaseSensitivity.CaseInsensitive
            fInfo = indexNode.fileInfo()

            path = None if fInfo is None else fInfo.filePath()
            print("<SDM> [_unwatchPathsAt scope] path: ", path)
            if path is None:
                return []

            result: list[str] = []

            def filter_paths(watchedPath: str) -> bool:  # noqa: N803
                pathSize = len(path)
                print("<SDM> [filter_paths scope] pathSize: ", pathSize)

                if len(watchedPath) == pathSize:
                    print("<SDM> [filter_paths scope] path: ", path)
                    return (path == watchedPath) if caseSensitivity == Qt.CaseSensitivity.CaseSensitive else (path.lower() == watchedPath.lower())

                if len(watchedPath) > pathSize:
                    print("<SDM> [filter_paths scope] watchedPath[pathSize]: ", watchedPath[pathSize])
                    return watchedPath[pathSize] == "/" and (
                        watchedPath.startswith(path) if caseSensitivity == Qt.CaseSensitivity.CaseSensitive else watchedPath.lower().startswith(path.lower())
                    )

                return False

            # Get watched files and directories
            watchedFiles: list[str] = self._fileInfoGatherer.watchedFiles()
            watchedDirectories: list[str] = self._fileInfoGatherer.watchedDirectories()

            # Apply filter to watched files and directories
            result.extend(filter(filter_paths, watchedFiles))
            result.extend(filter(filter_paths, watchedDirectories))

            # Unwatch the filtered paths
            self._fileInfoGatherer.unwatchPaths(result)

            return result

    def addVisibleFiles(self, parentNode: PyFileSystemNode, newFiles: list[str]):  # noqa: N803
        parentIndex = self._index_from_node(parentNode, 0)
        indexHidden = self.isHiddenByFilter(parentNode, parentIndex)

        if not indexHidden:
            self.beginInsertRows(
                parentIndex,
                len(parentNode.visibleChildren),
                len(parentNode.visibleChildren) + len(newFiles) - 1,
            )

        if parentNode.dirtyChildrenIndex == -1:
            parentNode.dirtyChildrenIndex = len(parentNode.visibleChildren)

        for new_file in newFiles:
            parentNode.visibleChildren.append(new_file)
            parentNode.children[new_file].isVisible = True

        if not indexHidden:
            self.endInsertRows()

    def removeVisibleFile(self, parentNode: PyFileSystemNode, vLocation: int):  # noqa: N803
        if vLocation == -1:
            return
        parent = self._index_from_node(parentNode, 0)
        indexHidden = self.isHiddenByFilter(parentNode, parent)
        if not indexHidden:
            self.beginRemoveRows(
                parent,
                self.translateVisibleLocation(parentNode, vLocation),
                self.translateVisibleLocation(parentNode, vLocation),
            )
        parentNode.children[parentNode.visibleChildren[vLocation]].isVisible = False
        parentNode.visibleChildren.pop(vLocation)
        if not indexHidden:
            self.endRemoveRows()

    def _q_resolvedName(self, fileName: str, resolvedName: str):  # noqa: N803
        print(f"<SDM> [_q_resolvedName(fileName={fileName}, resolvedName={resolvedName})", self._resolvedSymLinks[fileName])
        # C++ uses fileInfoGatherer->mutex, but in Python we use the gatherer's mutex directly
        with QMutexLocker(self._fileInfoGatherer.mutex):
            print("<SDM> [_q_resolvedName scope] before self._resolvedSymLinks[fileName]: ", self._resolvedSymLinks[fileName])
            self._resolvedSymLinks[fileName] = resolvedName
            print("<SDM> [_q_resolvedName scope] after self._resolvedSymLinks[fileName]: ", self._resolvedSymLinks[fileName])

        node = self.node(self.index_path(fileName, 0))
        print("<SDM> [_q_resolvedName node.fileName ", node.fileName)

        if node and node.isSymLink():
            node.fileName = resolvedName
            print(f"<SDM> [_q_resolvedName scope] node.fileName<{node.fileName}: ")

            if node.parent:
                try:
                    row = node.parent.visibleChildren.index(fileName)
                    print(f"<SDM> [_q_resolvedName scope] row<{row}>: ", node.parent.visibleChildren[row])

                    node.parent.visibleChildren[row] = resolvedName
                    print(
                        f"<SDM> [_q_resolvedName scope] node<{node.fileName}>.parent<{node.parent.fileName}.visibleChildren<{node.parent.visibleChildren.__len__()}>[row<{row}>]: ",
                        node.parent.visibleChildren[row],
                    )

                    self.dataChanged.emit(self.index(row, 0), self.index(row, self.columnCount() - 1))
                except ValueError:  # noqa: S110
                    RobustLogger().exception(f"Internal issue trying to access '{fileName}' and resolved '{resolvedName}'")

    def _delayedSort(self) -> None:
        """Delayed sort matching C++ lines 246-249 exactly.

        Matches:
        inline void delayedSort() {
            if (!delayedSortTimer.isActive())
                delayedSortTimer.start(0);
        }
        """
        if not self._delayedSortTimer.isActive():
            self._delayedSortTimer.start(0)

    def _q_performDelayedSort(self) -> None:
        """Perform delayed sort matching C++ lines 1030-1034 exactly.

        Matches:
        void QFileSystemModelPrivate::performDelayedSort()
        {
            Q_Q(QFileSystemModel);
            q->sort(sortColumn, sortOrder);
        }
        """
        self.sort(self._sortColumn, self._sortOrder)

    def myComputer(self, role: int = Qt.ItemDataRole.DisplayRole) -> QVariant:
        """Return data for "My Computer" item matching C++ lines 707-723 exactly.

        Matches:
        QVariant QFileSystemModel::myComputer(int role) const
        {
        #if QT_CONFIG(filesystemwatcher)
            Q_D(const QFileSystemModel);
        #endif
            switch (role) {
            case Qt::DisplayRole:
                return QFileSystemModelPrivate::myComputer();
        #if QT_CONFIG(filesystemwatcher)
            case Qt::DecorationRole:
                if (auto *provider = d->fileInfoGatherer->iconProvider())
                    return provider->icon(QAbstractFileIconProvider::Computer);
            break;
        #endif
            }
            return QVariant();
        }
        """
        # QT_CONFIG(filesystemwatcher) - always true
        if role == Qt.ItemDataRole.DisplayRole:
            return QVariant(self._myComputer())
        if role == Qt.ItemDataRole.DecorationRole:
            provider = self._fileInfoGatherer.iconProvider()
            if provider:
                return QVariant(provider.icon(QFileIconProvider.IconType.Computer))  # type: ignore[attr-defined]
        return QVariant()

    @overload
    def node(self, index: QModelIndex) -> PyFileSystemNode: ...

    @overload
    def node(self, path: str, fetch: bool = True) -> PyFileSystemNode: ...

    def node(self, *args, **kwargs) -> PyFileSystemNode:  # noqa: PLR0911
        """Get node from index or path matching C++ overloads.

        Matches:
        - QFileSystemModelPrivate::QFileSystemNode *QFileSystemModelPrivate::node(const QModelIndex &index) const
        - QFileSystemModelPrivate::QFileSystemNode *QFileSystemModelPrivate::node(const QString &path, bool fetch) const
        """
        if args and isinstance(args[0], QModelIndex):
            index = args[0]
            if not index.isValid():
                return self._root
            indexNode = index.internalPointer()
            assert indexNode is not None
            return indexNode
        if args and isinstance(args[0], str):
            path = args[0]
            fetch = args[1] if len(args) > 1 else kwargs.get("fetch", True)
            return self.node_path(path, fetch)
        raise TypeError("node() requires QModelIndex or str argument")

    def node_path(self, path: str, fetch: bool = True) -> PyFileSystemNode:  # noqa: FBT001, FBT002
        """Get node from path matching C++ lines 339-489 exactly.

        Matches:
        QFileSystemModelPrivate::QFileSystemNode *QFileSystemModelPrivate::node(const QString &path, bool fetch) const
        {
            Q_Q(const QFileSystemModel);
            Q_UNUSED(q);
            if (path.isEmpty() || path == myComputer() || path.startsWith(u':'))
                return const_cast<QFileSystemModelPrivate::QFileSystemNode*>(&root);

            // Construct the nodes up to the new root path if they need to be built
            QString absolutePath;
        #ifdef Q_OS_WIN32
            QString longPath = qt_GetLongPathName(path);
        #else
            QString longPath = path;
        #endif
            if (longPath == rootDir.path())
                absolutePath = rootDir.absolutePath();
            else
                absolutePath = QDir(longPath).absolutePath();

            // ### TODO can we use bool QAbstractFileEngine::caseSensitive() const?
            QStringList pathElements = absolutePath.split(u'/', Qt::SkipEmptyParts);
            if ((pathElements.isEmpty())
        #if !defined(Q_OS_WIN)
                && QDir::fromNativeSeparators(longPath) != "/"_L1
        #endif
                )
                return const_cast<QFileSystemModelPrivate::QFileSystemNode*>(&root);
            QModelIndex index = QModelIndex(); // start with "My Computer"
            QString elementPath;
            QChar separator = u'/';
            QString trailingSeparator;
        #if defined(Q_OS_WIN)
            if (absolutePath.startsWith("//"_L1)) { // UNC path
                QString host = "\\\\"_L1 + pathElements.constFirst();
                if (absolutePath == QDir::fromNativeSeparators(host))
                    absolutePath.append(u'/');
                if (longPath.endsWith(u'/') && !absolutePath.endsWith(u'/'))
                    absolutePath.append(u'/');
                if (absolutePath.endsWith(u'/'))
                    trailingSeparator = "\\"_L1;
                int r = 0;
                auto rootNode = const_cast<QFileSystemModelPrivate::QFileSystemNode*>(&root);
                auto it = root.children.constFind(host);
                if (it != root.children.cend()) {
                    host = it.key(); // Normalize case for lookup in visibleLocation()
                } else {
                    if (pathElements.count() == 1 && !absolutePath.endsWith(u'/'))
                        return rootNode;
                    QFileInfo info(host);
                    if (!info.exists())
                        return rootNode;
                    QFileSystemModelPrivate *p = const_cast<QFileSystemModelPrivate*>(this);
                    p->addNode(rootNode, host,info);
                    p->addVisibleFiles(rootNode, QStringList(host));
                }
                r = rootNode->visibleLocation(host);
                r = translateVisibleLocation(rootNode, r);
                index = q->index(r, 0, QModelIndex());
                pathElements.pop_front();
                separator = u'\\';
                elementPath = host;
                elementPath.append(separator);
            } else {
                if (!pathElements.at(0).contains(u':')) {
                    QString rootPath = QDir(longPath).rootPath();
                    pathElements.prepend(rootPath);
                }
            }
        #else
            // add the "/" item, since it is a valid path element on Unix
            if (absolutePath[0] == u'/')
                pathElements.prepend("/"_L1);
        #endif

            QFileSystemModelPrivate::QFileSystemNode *parent = node(index);

            for (int i = 0; i < pathElements.size(); ++i) {
                QString element = pathElements.at(i);
                if (i != 0)
                    elementPath.append(separator);
                elementPath.append(element);
                if (i == pathElements.size() - 1)
                    elementPath.append(trailingSeparator);
        #ifdef Q_OS_WIN
                // If after stripping the characters there is nothing left then we
                // just return the parent directory as it is assumed that the path
                // is referring to the parent.
                chopSpaceAndDot(element);
                // Only filenames that can't possibly exist will be end up being empty
                if (element.isEmpty())
                    return parent;
        #endif
                bool alreadyExisted = parent->children.contains(element);

                // we couldn't find the path element, we create a new node since we
                // _know_ that the path is valid
                if (alreadyExisted) {
                    if ((parent->children.size() == 0)
                        || (parent->caseSensitive()
                            && parent->children.value(element)->fileName != element)
                        || (!parent->caseSensitive()
                            && parent->children.value(element)->fileName.toLower() != element.toLower()))
                        alreadyExisted = false;
                }

                QFileSystemModelPrivate::QFileSystemNode *node;
                if (!alreadyExisted) {
        #ifdef Q_OS_WIN
                    // Special case: elementPath is a drive root path (C:). If we do not have the trailing
                    // '/' it will be read as a relative path (QTBUG-133746)
                    if (elementPath.length() == 2 && elementPath.at(0).isLetter()
                        && elementPath.at(1) == u':') {
                        elementPath.append(u'/');
                    }
        #endif
                    // Someone might call ::index("file://cookie/monster/doesn't/like/veggies"),
                    // a path that doesn't exists, I.E. don't blindly create directories.
                    QFileInfo info(elementPath);
                    if (!info.exists())
                        return const_cast<QFileSystemModelPrivate::QFileSystemNode*>(&root);
                    QFileSystemModelPrivate *p = const_cast<QFileSystemModelPrivate*>(this);
                    node = p->addNode(parent, element,info);
        #if QT_CONFIG(filesystemwatcher)
                    node->populate(fileInfoGatherer->getInfo(info));
        #endif
                } else {
                    node = parent->children.value(element);
                }

                Q_ASSERT(node);
                if (!node->isVisible) {
                    // It has been filtered out
                    if (alreadyExisted && node->hasInformation() && !fetch)
                        return const_cast<QFileSystemModelPrivate::QFileSystemNode*>(&root);

                    QFileSystemModelPrivate *p = const_cast<QFileSystemModelPrivate*>(this);
                    p->addVisibleFiles(parent, QStringList(element));
                    if (!p->bypassFilters.contains(node))
                        p->bypassFilters[node] = 1;
                    QString dir = q->filePath(this->index(parent));
                    if (!node->hasInformation() && fetch) {
                        Fetching f = { std::move(dir), std::move(element), node };
                        p->toFetch.append(std::move(f));
                        p->fetchingTimer.start(0, const_cast<QFileSystemModel*>(q));
                    }
                }
                parent = node;
            }

            return parent;
        }
        """
        if not path or path == self._myComputer() or path.startswith(":"):
            return self._root

        # Construct the nodes up to the new root path if they need to be built
        if os.name == "nt":
            longPath = qt_GetLongPathName(path)
        else:
            longPath = path

        if longPath == self._rootDir.path():
            absolutePath = self._rootDir.absolutePath()
        else:
            absolutePath = QDir(longPath).absolutePath()

        # Split path elements
        pathElements = absolutePath.split("/")
        pathElements = [p for p in pathElements if p]  # Remove empty parts (Qt::SkipEmptyParts)

        if not pathElements:
            if os.name != "nt" and QDir.fromNativeSeparators(longPath) != "/":
                return self._root
            if os.name == "nt":
                return self._root

        index = QModelIndex()  # start with "My Computer"
        elementPath = ""
        separator = "/"
        trailingSeparator = ""

        if os.name == "nt":
            if absolutePath.startswith("//"):  # UNC path
                host = "\\\\" + pathElements[0]
                if absolutePath == QDir.fromNativeSeparators(host):
                    absolutePath += "/"
                if longPath.endswith("/") and not absolutePath.endswith("/"):
                    absolutePath += "/"
                if absolutePath.endswith("/"):
                    trailingSeparator = "\\"
                rootNode = self._root
                if host in rootNode.children:
                    # Normalize case for lookup in visibleLocation()
                    host = next(k for k in rootNode.children.keys() if k.lower() == host.lower())
                else:
                    if len(pathElements) == 1 and not absolutePath.endswith("/"):
                        return rootNode
                    info = QFileInfo(host)
                    if not info.exists():
                        return rootNode
                    self.addNode(rootNode, host, info)
                    self.addVisibleFiles(rootNode, [host])
                r = rootNode.visibleLocation(host)
                r = self.translateVisibleLocation(rootNode, r)
                index = self.index(r, 0, QModelIndex())
                pathElements.pop(0)
                separator = "\\"
                elementPath = host + separator
            else:
                if pathElements and ":" not in pathElements[0]:
                    rootPath = QDir(longPath).rootPath()
                    pathElements.insert(0, rootPath)
        else:
            # add the "/" item, since it is a valid path element on Unix
            if absolutePath and absolutePath[0] == "/":
                pathElements.insert(0, "/")

        parent = self.node(index)

        for i in range(len(pathElements)):
            element = pathElements[i]
            if i != 0:
                elementPath += separator
            elementPath += element
            if i == len(pathElements) - 1:
                elementPath += trailingSeparator

            if os.name == "nt":
                # If after stripping the characters there is nothing left then we
                # just return the parent directory as it is assumed that the path
                # is referring to the parent.
                element = chopSpaceAndDot(element)
                # Only filenames that can't possibly exist will be end up being empty
                if not element:
                    return parent

            alreadyExisted = element in parent.children

            # we couldn't find the path element, we create a new node since we
            # _know_ that the path is valid
            if alreadyExisted:
                if (
                    len(parent.children) == 0
                    or (parent.caseSensitive() and parent.children[element].fileName != element)
                    or (not parent.caseSensitive() and parent.children[element].fileName.lower() != element.lower())
                ):
                    alreadyExisted = False

            if not alreadyExisted:
                if os.name == "nt":
                    # Special case: elementPath is a drive root path (C:). If we do not have the trailing
                    # '/' it will be read as a relative path (QTBUG-133746)
                    if len(elementPath) == 2 and elementPath[0].isalpha() and elementPath[1] == ":":
                        elementPath += "/"
                # Someone might call ::index("file://cookie/monster/doesn't/like/veggies"),
                # a path that doesn't exists, I.E. don't blindly create directories.
                info = QFileInfo(elementPath)
                if not info.exists():
                    return self._root
                node_obj = self.addNode(parent, element, info)
                # QT_CONFIG(filesystemwatcher) - always true
                node_obj.populate(self._fileInfoGatherer.getInfo(info))
            else:
                node_obj = parent.children[element]

            assert node_obj is not None
            if not node_obj.isVisible:
                # It has been filtered out
                if alreadyExisted and node_obj.hasInformation() and not fetch:
                    return self._root

                self.addVisibleFiles(parent, [element])
                if node_obj not in self._bypassFilters:
                    self._bypassFilters[node_obj] = True
                dir_path = self.filePath(self._index_from_node(parent, 0))
                if not node_obj.hasInformation() and fetch:
                    f = self._Fetching(dir_path, element, node_obj)
                    self._toFetch.append(f)
                    self._fetchingTimer.start(0, self)
            parent = node_obj

        return parent

    def _myComputer(self) -> str:
        """Get my computer string matching C++ lines 234-244 exactly.

        Matches:
        inline static QString myComputer() {
            // ### TODO We should query the system to find out what the string should be
            // XP == "My Computer",
            // Vista == "Computer",
            // OS X == "Computer" (sometime user generated) "Benjamin's PowerBook G4"
        #ifdef Q_OS_WIN
            return QFileSystemModel::tr("My Computer");
        #else
            return QFileSystemModel::tr("Computer");
        #endif
        }
        """
        if os.name == "nt":
            return "My Computer"
        return "Computer"

    def _handle_node_path_arg(self, path: os.PathLike | str, fetch: bool) -> PyFileSystemNode:  # noqa: FBT001, C901, PLR0911, PLR0912, PLR0915
        # sourcery skip: low-code-quality
        pathObj = Path(path)
        if not pathObj.parent.name or pathObj.anchor.startswith(":"):
            print("<SDM> [_handle_node_arg_str scope] path: ", path)

            return self._root

        index = QModelIndex()  # root
        print("<SDM> [_handle_node_arg_str scope] index: ", index)
        print("<SDM> [_handle_node_arg_str scope] index: ", index, "index.row():", index.row(), "index.column():", index.column(), "index.isValid():", index.isValid())

        resolvedPath = Path(os.path.normpath(path)).resolve()
        print("<SDM> [_handle_node_arg_str scope] resolvedPath: ", resolvedPath)

        if os.name == "nt":
            host = resolvedPath.anchor
            print("<SDM> [_handle_node_arg_str scope] host: ", host)

            if host.startswith("\\\\"):  # UNC path
                rootNode = self._root
                if host not in self._root.children:
                    return self._handle_unc_path(resolvedPath, rootNode, host)
                r = rootNode.visibleLocation(host)
                r = self.translateVisibleLocation(rootNode, r)
                index = self.index(r, 0, QModelIndex())

        parent = self.node(index)
        print("<SDM> [_handle_node_arg_str scope] parent: ", parent, "child count:", parent.children.__len__())

        for thisFile in (resolvedPath, *resolvedPath.parents):
            alreadyExisted = str(thisFile).strip() in parent.children
            print("<SDM> [_handle_node_arg_str scope] alreadyExisted: ", alreadyExisted)

            # If the element already exists, ensure it matches case sensitivity requirements
            if alreadyExisted:
                childNode = parent.children[str(thisFile)]
                print("<SDM> [_handle_node_arg_str scope] child_node: ", childNode.fileInfo().path())  # pyright: ignore[reportOptionalMemberAccess]

                if (
                    parent.children and parent.caseSensitive() and childNode.fileInfo().path() != thisFile  # pyright: ignore[reportOptionalMemberAccess]
                ) or (
                    not parent.caseSensitive() and childNode.fileInfo().path().lower() != thisFile.name.lower()  # pyright: ignore[reportOptionalMemberAccess]
                ):
                    alreadyExisted = False

            # Create a new node if the path element does not exist
            if not alreadyExisted:
                info = QFileInfo(str(thisFile.parent))
                if not info.exists():
                    return self._root  # Return root if the path is invalid
                node = self.addNode(parent, str(thisFile), info)
                print("<SDM> [_handle_node_arg_str node.fileName ", node.fileName)

                if fetch:
                    node.populate(self._fileInfoGatherer.getInfo(info))
            else:
                node = parent.children[str(thisFile)]
                print("<SDM> [_handle_node_arg_str node.fileName ", node.fileName)

            if not node.isVisible:
                if alreadyExisted and node.hasInformation() and not fetch:
                    return self._root

                self.addVisibleFiles(parent, [str(thisFile)])
                if node not in self._bypassFilters:
                    self._bypassFilters[node] = True

                dirPath = str(thisFile.parent)
                if not node.hasInformation() and fetch:
                    self._toFetch.append(self._Fetching(dirPath, str(thisFile), node))
                    self._fetchingTimer.start(0, self)  # pyright: ignore[reportOptionalMemberAccess]
            parent = node
        return parent

    def _handle_unc_path(
        self,
        resolvedPath: Path, rootNode: PyFileSystemNode, host: str,
    ) -> PyFileSystemNode:  # noqa: N803
        if len(resolvedPath.parts) == 1 and not resolvedPath.name.endswith("/"):
            return rootNode
        info = QFileInfo(host)
        print("<SDM> [_handle_unc_path scope] info.path(): ", info.path())

        if not info.exists():
            return rootNode
        node = self.addNode(rootNode, host, info)
        print("<SDM> [_handle_unc_path node.fileName ", node.fileName)

        self.addVisibleFiles(rootNode, [host])
        return node

    def isHiddenByFilter(
        self,
        indexNode: PyFileSystemNode,
        index: QModelIndex,
    ) -> bool:  # noqa: N803
        """Return true if index which is owned by node is hidden by the filter."""
        return indexNode is not self._root and not index.isValid()

    def gatherFileInfo(
        self,
        path: str,
        files: list[str] | None = None,
    ):
        self._fileInfoGatherer.fetchExtendedInformation(path, files or [])

    def _fetchingTimerEvent(self):
        self._fetchingTimer.stop()
        for fetch in self._toFetch:
            node: PyFileSystemNode = fetch.node
            # row is not a method on PyFileSystemNode
            print("<SDM> [_fetchPendingItems scope] PyFileSystemNode: ", node.fileName, "children:", len(node.children))

            if not node.hasInformation():
                self.gatherFileInfo(fetch.dir, [fetch.file])
        self._toFetch.clear()

    def translateVisibleLocation(
        self,
        node: PyFileSystemNode,
        location: int,
    ) -> int:
        print("<SDM> [translateVisibleLocation scope] location: ", location)
        return -1 if location == -1 or not node.isVisible else location

    def sort(
        self,
        column: int,
        order: Qt.SortOrder = Qt.SortOrder.AscendingOrder,
    ) -> None:
        """Sort model matching C++ lines 1159-1187 exactly.

        Matches:
        void QFileSystemModel::sort(int column, Qt::SortOrder order)
        {
            Q_D(QFileSystemModel);
            if (d->sortOrder == order && d->sortColumn == column && !d->forceSort)
                return;

            emit layoutAboutToBeChanged();
            QModelIndexList oldList = persistentIndexList();
            QList<std::pair<QFileSystemModelPrivate::QFileSystemNode *, int>> oldNodes;
            oldNodes.reserve(oldList.size());
            for (const QModelIndex &oldNode : oldList)
                oldNodes.emplace_back(d->node(oldNode), oldNode.column());

            if (!(d->sortColumn == column && d->sortOrder != order && !d->forceSort)) {
                //we sort only from where we are, don't need to sort all the model
                d->sortChildren(column, index(rootPath()));
                d->sortColumn = column;
                d->forceSort = false;
            }
            d->sortOrder = order;

            QModelIndexList newList;
            newList.reserve(oldNodes.size());
            for (const auto &[node, col]: std::as_const(oldNodes))
                newList.append(d->index(node, col));

            changePersistentIndexList(oldList, newList);
            emit layoutChanged({}, VerticalSortHint);
        }
        """
        if self._sortOrder == order and self._sortColumn == column and not self._forceSort:
            return

        self.layoutAboutToBeChanged.emit()
        old_list = self.persistentIndexList()
        # Build list of old nodes with their columns (matching C++ oldNodes)
        old_nodes: list[tuple[PyFileSystemNode, int]] = []
        for old_node_index in old_list:
            old_nodes.append((self.node(old_node_index), old_node_index.column()))

        if not (self._sortColumn == column and self._sortOrder != order and not self._forceSort):
            # we sort only from where we are, don't need to sort all the model
            self.sortChildren(column, self.index(self.rootPath()))
            self._sortColumn = column
            self._forceSort = False

        self._sortOrder = order

        # Build new list from old nodes (matching C++ newList)
        new_list: list[QModelIndex] = []
        for node, col in old_nodes:
            new_list.append(self._index_from_node(node, col))

        self.changePersistentIndexList(old_list, new_list)
        # layoutChanged signal - in PyQt6, the signal signature is layoutChanged(parents, hint)
        # C++: emit layoutChanged({}, VerticalSortHint)
        # PyQt6: layoutChanged.emit([], QAbstractItemModel.LayoutChangeHint.VerticalSortHint)
        self.layoutChanged.emit([], QAbstractItemModel.LayoutChangeHint.VerticalSortHint)  # type: ignore[attr-defined]

    def rmdir(
        self,
        index: QModelIndex,
    ) -> bool:
        path = self.filePath(index)
        print("<SDM> [rmdir scope] path: ", path, "index.row()", index.row())

        try:
            shutil.rmtree(path, ignore_errors=False)  # noqa: PTH106
        except OSError as e:
            RobustLogger().exception(f"Failed to rmdir: {e.__class__.__name__}: {e}")
            return False
        else:
            self._fileInfoGatherer.removePath(path)
            return True

    def addNode(
        self,
        parentNode: PyFileSystemNode,
        fileName: str,
        info: QFileInfo,
    ) -> PyFileSystemNode:  # noqa: N803
        node = PyFileSystemNode(fileName, parentNode)
        print("<SDM> [addNode node.fileName ", node.fileName, "parentNode.fileName:", parentNode.fileName if parentNode is not None else None)

        # populate expects PyQExtendedInformation, so convert QFileInfo
        extended_info = self._fileInfoGatherer.getInfo(info)
        node.populate(extended_info)
        if os.name == "nt" and not parentNode.fileName:
            node.volumeName = volumeName(fileName)
            RobustLogger().warning(f"<SDM> [addNode scope] node.volumeName: '{node.volumeName}'")

        # assert fileName not in parentNode.children
        parentNode.children[fileName] = node
        print(f"<SDM> [addNode scope] parentNode<{parentNode.fileName}>.children<{parentNode.children.__len__()}[fileName<{fileName}>]: ", parentNode.children[fileName])

        return node

    def removeNode(
        self,
        parentNode: PyFileSystemNode,
        name: str,
    ):  # noqa: N803
        indexHidden = not self.filtersAcceptsNode(parentNode)
        v_location = parentNode.visibleLocation(name)
        print("<SDM> [removeNode scope] indexHidden: ", indexHidden, "name:", name, "parentNode.fileName", parentNode.fileName, "v_location", v_location)
        parent_index = self._index_from_node(parentNode, 0)
        if v_location >= 0 and not indexHidden:
            print("<SDM> [removeNode scope] parentIndex: ", parent_index)

            self.beginRemoveRows(parent_index, self.translateVisibleLocation(parentNode, v_location), self.translateVisibleLocation(parentNode, v_location))

        node = parentNode.children.pop(name, None)
        print("<SDM> [removeNode node.fileName ", None if node is None else node.fileName)

        if node:
            del node

        if v_location >= 0:
            parentNode.visibleChildren.remove(name)

        if v_location >= 0 and not indexHidden:
            self.endRemoveRows()

    def sortChildren(
        self,
        column: int,
        parent: QModelIndex,
    ):
        """Sort children matching C++ lines 1117-1154 exactly.

        Matches:
        void QFileSystemModelPrivate::sortChildren(int column, const QModelIndex &parent)
        {
            Q_Q(QFileSystemModel);
            QFileSystemModelPrivate::QFileSystemNode *indexNode = node(parent);
            if (indexNode->children.size() == 0)
                return;

            QList<QFileSystemModelPrivate::QFileSystemNode *> values;

            for (auto iterator = indexNode->children.constBegin(), cend = indexNode->children.constEnd(); iterator != cend; ++iterator) {
                if (filtersAcceptsNode(iterator.value())) {
                    values.append(iterator.value());
                } else {
                    iterator.value()->isVisible = false;
                }
            }
            QFileSystemModelSorter ms(column);
            std::sort(values.begin(), values.end(), ms);
            // First update the new visible list
            indexNode->visibleChildren.clear();
            //No more dirty item we reset our internal dirty index
            indexNode->dirtyChildrenIndex = -1;
            indexNode->visibleChildren.reserve(values.size());
            for (QFileSystemNode *node : std::as_const(values)) {
                indexNode->visibleChildren.append(node->fileName);
                node->isVisible = true;
            }

            if (!disableRecursiveSort) {
                for (int i = 0; i < q->rowCount(parent); ++i) {
                    const QModelIndex childIndex = q->index(i, 0, parent);
                    QFileSystemModelPrivate::QFileSystemNode *indexNode = node(childIndex);
                    //Only do a recursive sort on visible nodes
                    if (indexNode->isVisible)
                        sortChildren(column, childIndex);
                }
            }
        }
        """
        index_node = self.node(parent)

        if len(index_node.children) == 0:
            return

        # Matches C++ lines 1124-1132: Build values list and set isVisible = false for non-accepting nodes
        values: list[PyFileSystemNode] = []
        for child in index_node.children.values():
            if self.filtersAcceptsNode(child):
                values.append(child)
            else:
                child.isVisible = False

        # Matches C++ lines 1133-1134: Create sorter and sort
        # QFileSystemModelSorter ms(column);
        # std::sort(values.begin(), values.end(), ms);
        ms = PyFileSystemModelSorter(column)
        # Python's sort with a key function that uses the sorter's __call__ operator
        # We need to create a stable sort key. Since we can't use a comparison function directly
        # in Python 3 (no cmp parameter), we'll use a workaround with a key that preserves order.
        # However, the C++ code uses std::sort with a functor, which is a comparison-based sort.
        # We'll use a key function that creates a sortable tuple based on the sorter's comparison.
        # Actually, we need to use a comparison-based sort. Let's use a wrapper class.
        class SortKey:
            def __init__(self, node: PyFileSystemNode, sorter: PyFileSystemModelSorter):
                self.node = node
                self.sorter = sorter

            def __lt__(self, other: SortKey) -> bool:
                return self.sorter.compareNodes(self.node, other.node)

        # Create sort keys and sort
        sort_keys = [SortKey(node, ms) for node in values]
        sort_keys.sort()
        values = [key.node for key in sort_keys]

        # Matches C++ lines 1136-1143: Update visibleChildren and set isVisible = true
        # First update the new visible list
        index_node.visibleChildren.clear()
        # No more dirty item we reset our internal dirty index
        index_node.dirtyChildrenIndex = -1
        # Reserve is not needed in Python, but we can pre-allocate if desired
        for node in values:
            index_node.visibleChildren.append(node.fileName)
            node.isVisible = True

        # Matches C++ lines 1145-1153: Recursive sort
        if not self._disableRecursiveSort:
            for i in range(self.rowCount(parent)):
                child_index = self.index(i, 0, parent)
                child_node = self.node(child_index)
                # Only do a recursive sort on visible nodes
                if child_node.isVisible:
                    self.sortChildren(column, child_index)

    def filtersAcceptsNode(
        self,
        node: PyFileSystemNode,
    ) -> bool:
        """Filters accepts node matching C++ lines 2174-2218 exactly.

        Matches:
        bool QFileSystemModelPrivate::filtersAcceptsNode(const QFileSystemNode *node) const
        {
            // When the model is set to only show files, then a node representing a dir
            // should be hidden regardless of bypassFilters.
            // QTBUG-74471
            const bool hideDirs = (filters & (QDir::Dirs | QDir::AllDirs)) == 0;
            const bool shouldHideDirNode = hideDirs && node->isDir();

            // always accept drives
            if (node->parent == &root || (!shouldHideDirNode && bypassFilters.contains(node)))
                return true;

            // If we don't know anything yet don't accept it
            if (!node->hasInformation())
                return false;

            const bool filterPermissions = ((filters & QDir::PermissionMask)
                                           && (filters & QDir::PermissionMask) != QDir::PermissionMask);
            const bool hideFiles         = !(filters & QDir::Files);
            const bool hideReadable      = !(!filterPermissions || (filters & QDir::Readable));
            const bool hideWritable      = !(!filterPermissions || (filters & QDir::Writable));
            const bool hideExecutable    = !(!filterPermissions || (filters & QDir::Executable));
            const bool hideHidden        = !(filters & QDir::Hidden);
            const bool hideSystem        = !(filters & QDir::System);
            const bool hideSymlinks      = (filters & QDir::NoSymLinks);
            const bool hideDot           = (filters & QDir::NoDot);
            const bool hideDotDot        = (filters & QDir::NoDotDot);

            // Note that we match the behavior of entryList and not QFileInfo on this.
            bool isDot    = (node->fileName == "."_L1);
            bool isDotDot = (node->fileName == ".."_L1);
            if (   (hideHidden && !(isDot || isDotDot) && node->isHidden())
                || (hideSystem && node->isSystem())
                || (hideDirs && node->isDir())
                || (hideFiles && node->isFile())
                || (hideSymlinks && node->isSymLink())
                || (hideReadable && node->isReadable())
                || (hideWritable && node->isWritable())
                || (hideExecutable && node->isExecutable())
                || (hideDot && isDot)
                || (hideDotDot && isDotDot))
                return false;

            return nameFilterDisables || passNameFilters(node);
        }
        """
        # When the model is set to only show files, then a node representing a dir
        # should be hidden regardless of bypassFilters.
        # QTBUG-74471
        hideDirs = (self._filters & (QDir.Filter.Dirs | QDir.Filter.AllDirs)) == 0  # type: ignore[attr-defined]
        shouldHideDirNode = hideDirs and node.isDir()

        # always accept drives
        if node.parent == self._root or (not shouldHideDirNode and node in self._bypassFilters):
            return True

        # If we don't know anything yet don't accept it
        if not node.hasInformation():
            return False

        filterPermissions = ((self._filters & QDir.Filter.PermissionMask)  # type: ignore[attr-defined]
                            and (self._filters & QDir.Filter.PermissionMask) != QDir.Filter.PermissionMask)  # type: ignore[attr-defined]
        hideFiles = not bool(self._filters & QDir.Filter.Files)  # type: ignore[attr-defined]
        hideReadable = not (not filterPermissions or bool(self._filters & QDir.Filter.Readable))  # type: ignore[attr-defined]
        hideWritable = not (not filterPermissions or bool(self._filters & QDir.Filter.Writable))  # type: ignore[attr-defined]
        hideExecutable = not (not filterPermissions or bool(self._filters & QDir.Filter.Executable))  # type: ignore[attr-defined]
        hideHidden = not bool(self._filters & QDir.Filter.Hidden)  # type: ignore[attr-defined]
        hideSystem = not bool(self._filters & QDir.Filter.System)  # type: ignore[attr-defined]
        hideSymlinks = bool(self._filters & QDir.Filter.NoSymLinks)  # type: ignore[attr-defined]
        hideDot = bool(self._filters & QDir.Filter.NoDot)  # type: ignore[attr-defined]
        hideDotDot = bool(self._filters & QDir.Filter.NoDotDot)  # type: ignore[attr-defined]

        # Note that we match the behavior of entryList and not QFileInfo on this.
        isDot = node.fileName == "."
        isDotDot = node.fileName == ".."
        if (
            (hideHidden and not (isDot or isDotDot) and node.isHidden())
            or (hideSystem and node.isSystem())
            or (hideDirs and node.isDir())
            or (hideFiles and node.isFile())
            or (hideSymlinks and node.isSymLink())
            or (hideReadable and node.isReadable())
            or (hideWritable and node.isWritable())
            or (hideExecutable and node.isExecutable())
            or (hideDot and isDot)
            or (hideDotDot and isDotDot)
        ):
            return False

        return self._nameFilterDisables or self._passNameFilters(node)

    def _passNameFilters(
        self,
        node: PyFileSystemNode,
    ) -> bool:
        """Pass name filters matching C++ lines 2225-2245 exactly.

        Matches:
        bool QFileSystemModelPrivate::passNameFilters(const QFileSystemNode *node) const
        {
        #if QT_CONFIG(regularexpression)
            if (nameFilters.isEmpty())
                return true;

            // Check the name regularexpression filters
            if (!(node->isDir() && (filters & QDir::AllDirs))) {
                const auto matchesNodeFileName = [node](const QRegularExpression &re)
                {
                    return node->fileName.contains(re);
                };
                return std::any_of(nameFiltersRegexps.begin(),
                                   nameFiltersRegexps.end(),
                                   matchesNodeFileName);
            }
        #else
            Q_UNUSED(node);
        #endif
            return true;
        }
        """
        # QT_CONFIG(regularexpression) - always true in Python
        if not self._nameFilters:
            return True

        # Check the name regularexpression filters
        if not (node.isDir() and bool(self._filters & QDir.Filter.AllDirs)):  # type: ignore[attr-defined]
            from qtpy.QtCore import QRegularExpression
            
            # C++: node->fileName.contains(re) where re is QRegularExpression
            # In Qt, QString::contains(QRegularExpression) checks if string contains a match
            # In Python/PyQt6, we use match().hasMatch()
            def matchesNodeFileName(regexp: QRegularExpression) -> bool:
                match = regexp.match(node.fileName)
                return match.hasMatch()
            
            return any(matchesNodeFileName(regexp) for regexp in self._nameFiltersRegexps)
        return True

    def _rebuildNameFilterRegexps(self) -> None:
        """Rebuild name filter regexps matching C++ lines 2248-2261 exactly.

        Matches:
        #if QT_CONFIG(regularexpression)
        void QFileSystemModelPrivate::rebuildNameFilterRegexps()
        {
            nameFiltersRegexps.clear();
            nameFiltersRegexps.reserve(nameFilters.size());
            const auto cs = (filters & QDir::CaseSensitive) ? Qt::CaseSensitive : Qt::CaseInsensitive;
            const auto convertWildcardToRegexp = [cs](const QString &nameFilter)
            {
                return QRegularExpression::fromWildcard(nameFilter, cs);
            };
            std::transform(nameFilters.constBegin(),
                           nameFilters.constEnd(),
                           std::back_inserter(nameFiltersRegexps),
                           convertWildcardToRegexp);
        }
        #endif
        """
        # QT_CONFIG(regularexpression) - always true in Python
        from qtpy.QtCore import QRegularExpression
        
        self._nameFiltersRegexps.clear()
        self._nameFiltersRegexps = []
        # Reserve equivalent - pre-allocate list size
        self._nameFiltersRegexps = [None] * len(self._nameFilters)  # type: ignore[list-item]
        
        cs = Qt.CaseSensitivity.CaseSensitive if bool(self._filters & QDir.Filter.CaseSensitive) else Qt.CaseSensitivity.CaseInsensitive  # type: ignore[attr-defined]
        
        for i, nameFilter in enumerate(self._nameFilters):
            # QRegularExpression::fromWildcard equivalent
            regexp = QRegularExpression.fromWildcard(nameFilter, cs)
            self._nameFiltersRegexps[i] = regexp

    def _natural_compare(
        self,
        node: PyFileSystemNode,
        column: int,
    ) -> Any:
        if column == 0:
            return node.fileName.lower()
        if column == 1:
            return node.size()
        if column == 2:
            return node.type()
        if column == 3:
            return node.lastModified(QTimeZone.UTC).toPyDateTime()  # type: ignore[attr-defined]
        raise ValueError(f"No column with value of '{column}'")

    def icon(
        self,
        index: QModelIndex,
    ) -> QIcon:
        node = self.node(index)
        print("<SDM> [icon node.fileName ", node.fileName)

        return node.icon()

    def displayName(
        self,
        index: QModelIndex,
    ) -> str:
        node = self.node(index)
        print("<SDM> [displayName node.fileName ", node.fileName)

        return node.fileName

    def roleNames(self) -> dict[int, QByteArray]:
        """Return role names matching C++ lines 1277-1289 exactly.

        Matches:
        QHash<int, QByteArray> QFileSystemModel::roleNames() const
        {
            static auto ret = [] {
                auto ret = QAbstractItemModelPrivate::defaultRoleNames();
                ret.insert(QFileSystemModel::FileIconRole, "fileIcon"_ba);
                ret.insert(QFileSystemModel::FilePathRole, "filePath"_ba);
                ret.insert(QFileSystemModel::FileNameRole, "fileName"_ba);
                ret.insert(QFileSystemModel::FilePermissions, "filePermissions"_ba);
                ret.insert(QFileSystemModel::FileInfoRole, "fileInfo"_ba);
                return ret;
            }();
            return ret;
        }
        """
        # Static initialization matching C++ implementation
        # Use class variable to store the static result (initialized once)
        if PyFileSystemModel._roleNames is None:
            # Get default role names from QAbstractItemModel
            temp_model = QAbstractItemModel()
            default_roles = temp_model.roleNames()
            ret = dict(default_roles)

            # Add QFileSystemModel-specific roles
            ret[self.FileIconRole] = QByteArray(b"fileIcon")  # type: ignore[attr-defined]
            ret[self.FilePathRole] = QByteArray(b"filePath")  # type: ignore[attr-defined]
            ret[self.FileNameRole] = QByteArray(b"fileName")  # type: ignore[attr-defined]
            ret[self.FilePermissions] = QByteArray(b"filePermissions")  # type: ignore[attr-defined]
            ret[self.FileInfoRole] = QByteArray(b"fileInfo")  # type: ignore[attr-defined]

            PyFileSystemModel._roleNames = ret

        assert PyFileSystemModel._roleNames is not None
        return PyFileSystemModel._roleNames

    def options(self) -> QFileSystemModel.Option:  # type: ignore[attr-defined]
        result = 0
        if not self.resolveSymlinks():
            result |= QFileSystemModel.DontResolveSymlinks  # type: ignore[attr-defined]

        # TODO:
        # if not self._fileInfoGatherer.isWatching():
        #    result |= QFileSystemModel.DontWatchForChanges

        provider = self.iconProvider()
        print("<SDM> [options scope] provider: ", provider)

        if provider and bool(provider.options() & QFileIconProvider.DontUseCustomDirectoryIcons):  # type: ignore[attr-defined]
            result |= QFileSystemModel.DontUseCustomDirectoryIcons  # type: ignore[attr-defined]

        return result

    def setOptions(
        self,
        options: QFileSystemModel.Option,  # type: ignore[attr-defined]
    ):
        changed = options ^ self.options()
        print("<SDM> [setOptions scope] changed: ", changed)

        if bool(changed & QFileSystemModel.DontResolveSymlinks):  # type: ignore[attr-defined]
            self.setResolveSymlinks(not bool(options & QFileSystemModel.DontResolveSymlinks))  # type: ignore[attr-defined]

        # TODO:
        # if bool(changed & QFileSystemModel.DontWatchForChanges):
        #    self._fileInfoGatherer.setWatching(not bool(options & QFileSystemModel.DontWatchForChanges))

        if bool(changed & QFileSystemModel.DontUseCustomDirectoryIcons):  # type: ignore[attr-defined]
            provider = self.iconProvider()
            if provider:
                providerOptions = provider.options()
                if bool(options & QFileSystemModel.DontUseCustomDirectoryIcons):  # type: ignore[attr-defined]
                    providerOptions |= QFileIconProvider.DontUseCustomDirectoryIcons  # type: ignore[attr-defined]
                else:
                    providerOptions &= ~QFileIconProvider.DontUseCustomDirectoryIcons  # type: ignore[attr-defined]
                provider.setOptions(providerOptions)
            else:
                RobustLogger().warning("Setting PyFileSystemModel::DontUseCustomDirectoryIcons has no effect when no provider is used")

    def testOption(
        self,
        option: QFileSystemModel.Option,
    ) -> bool:
        print("<SDM> [testOption scope] option: ", option)
        return bool(self.options() & option) == option  # type: ignore[attr-defined]

    def setOption(
        self,
        option: QFileSystemModel.Option,
        on: bool = True,
    ):  # noqa: FBT001, FBT002
        self.setOptions(self.options() | option if on else self.options() & ~option)  # type: ignore[attr-defined]

    def sibling(
        self,
        row: int,
        column: int,
        idx: QModelIndex,
    ) -> QModelIndex:
        return self.index(row, column, self.parent(idx))

    def event(self, event: QEvent) -> bool:
        """Handle events matching C++ lines 1776-1786 exactly.

        Matches:
        bool QFileSystemModel::event(QEvent *event)
        {
        #if QT_CONFIG(filesystemwatcher)
            Q_D(QFileSystemModel);
            if (event->type() == QEvent::LanguageChange) {
                d->root.retranslateStrings(d->fileInfoGatherer->iconProvider(), QString());
                return true;
            }
        #endif
            return QAbstractItemModel::event(event);
        }
        """
        # QT_CONFIG(filesystemwatcher) - always true
        if event.type() == QEvent.Type.LanguageChange:
            self._root.retranslateStrings(self._fileInfoGatherer.iconProvider(), "")
            return True
        return super().event(event)

    def timerEvent(
        self,
        event: QTimerEvent,
    ):
        if event.timerId() == self._fetchingTimer.timerId():
            self._fetchingTimerEvent()

    def remove(
        self,
        index: QModelIndex,
    ) -> bool:
        path = self.filePath(index)
        print("<SDM> [remove scope] path:", path, "index.row():", index.row())

        self._fileInfoGatherer.removePath(path)
        try:
            if os.path.isdir(path):  # noqa: PTH112, PTH110
                shutil.rmtree(path, ignore_errors=False)
            else:
                Path(path).unlink(missing_ok=False)  # noqa: PTH107
        except OSError:
            RobustLogger().exception(f"Failed to rmdir '{path}'")
            return False
        else:
            return True

    def mkdir(
        self,
        parent: QModelIndex,
        name: str,
    ) -> QModelIndex:
        dirPath = os.path.join(self.filePath(parent), name)  # noqa: PTH118
        print("<SDM> [mkdir scope] dirPath: ", dirPath)

        try:
            os.mkdir(dirPath)  # noqa: PTH102
        except OSError:
            RobustLogger().exception(f"Failed to mkdir at '{dirPath}'")
            return QModelIndex()
        else:  # sourcery skip: extract-method
            parentNode = self.node(parent)
            # row is not a method on PyFileSystemNode
            print("<SDM> [mkdir scope] parentNode: ", parentNode, "parentNode.fileName:", parentNode.fileName)

            _newNode = self.addNode(parentNode, name, QFileInfo(dirPath))
            assert name in parentNode.children
            node = parentNode.children[name]
            print("<SDM> [mkdir scope] node: ", node, "name:", name, "node.fileName", node.fileName)

            node.populate(self._fileInfoGatherer.getInfo(QFileInfo(os.path.abspath(os.path.join(dirPath, name)))))  # noqa: PTH118, PTH100
            self.addVisibleFiles(parentNode, [name])
            # index requires row, column, parent - need to find the row of this node
            parent_index = self.index_path(self.filePath(parent), 0)
            row = parentNode.visibleChildren.index(name) if name in parentNode.visibleChildren else 0
            return self.index(row, 0, parent_index)

    def permissions(
        self,
        index: QModelIndex,
    ) -> QFileDevice.Permission:  # type: ignore[attr-defined]
        r1 = QFileInfo(self.filePath(index)).permissions()
        print("<SDM> [permissions scope] r1: ", r1)

        return QFileDevice.Permission() if r1 is None else r1  # type: ignore[attr-defined]

    @overload
    def lastModified(self, index: QModelIndex) -> QDateTime: ...

    @overload
    def lastModified(self, index: QModelIndex, tz: QTimeZone) -> QDateTime: ...

    def lastModified(
        self,
        index: QModelIndex,
        tz: QTimeZone | None = None,
    ) -> QDateTime:
        """Return last modified time matching C++ lines 562-585 exactly.

        Matches:
        QDateTime QFileSystemModel::lastModified(const QModelIndex &index) const
        {
            Q_D(const QFileSystemModel);
            if (!index.isValid())
                return QDateTime();
            return d->node(index)->lastModified(QTimeZone::LocalTime);
        }

        QDateTime QFileSystemModel::lastModified(const QModelIndex &index, const QTimeZone &tz) const
        {
            Q_D(const QFileSystemModel);
            if (!index.isValid())
                return QDateTime();
            return d->node(index)->lastModified(tz);
        }
        """
        if not index.isValid():
            return QDateTime()
        node = self.node(index)
        if tz is None:
            return node.lastModified(QTimeZone.LocalTime)  # type: ignore[attr-defined]
        return node.lastModified(tz)

    def type(
        self,
        index: QModelIndex,
    ) -> str:
        node = self.node(index)
        return node.type()

    def size(
        self,
        index: QModelIndex,
    ) -> int:
        node = self.node(index)
        return node.size()

    def isDir(
        self,
        index: QModelIndex,
    ) -> bool:
        node = self.node(index)
        return node.isDir()

    def index(
        self,
        row: int,
        column: int,
        parent: QModelIndex = QModelIndex(),
    ) -> QModelIndex:
        """Index method matching C++ lines 218-238 exactly.

        Matches:
        QModelIndex QFileSystemModel::index(int row, int column, const QModelIndex &parent) const
        {
            Q_D(const QFileSystemModel);
            if (row < 0 || column < 0 || row >= rowCount(parent) || column >= columnCount(parent))
                return QModelIndex();

            // get the parent node
            QFileSystemModelPrivate::QFileSystemNode *parentNode = (d->indexValid(parent) ? d->node(parent) :
                                                           const_cast<QFileSystemModelPrivate::QFileSystemNode*>(&d->root));
            Q_ASSERT(parentNode);

            // now get the internal pointer for the index
            const int i = d->translateVisibleLocation(parentNode, row);
            if (i >= parentNode->visibleChildren.size())
                return QModelIndex();
            const QString &childName = parentNode->visibleChildren.at(i);
            const QFileSystemModelPrivate::QFileSystemNode *indexNode = parentNode->children.value(childName);
            Q_ASSERT(indexNode);

            return createIndex(row, column, indexNode);
        }
        """
        if row < 0 or column < 0 or row >= self.rowCount(parent) or column >= self.columnCount(parent):
            return QModelIndex()

        # get the parent node
        # indexValid equivalent: parent.isValid() and parent.model() == self
        if parent.isValid() and parent.model() == self:
            parentNode = self.node(parent)
        else:
            parentNode = self._root
        assert parentNode is not None

        # now get the internal pointer for the index
        i = self.translateVisibleLocation(parentNode, row)
        if i >= len(parentNode.visibleChildren):
            return QModelIndex()
        childName = parentNode.visibleChildren[i]
        indexNode = parentNode.children.get(childName)
        assert indexNode is not None

        return self.createIndex(row, column, indexNode)

    def index_path(
        self,
        path: str,
        column: int = 0,
    ) -> QModelIndex:
        """Index overload for path matching C++ lines 260-265 exactly.

        Matches:
        QModelIndex QFileSystemModel::index(const QString &path, int column) const
        {
            Q_D(const QFileSystemModel);
            QFileSystemModelPrivate::QFileSystemNode *node = d->node(path, false);
            return d->index(node, column);
        }
        """
        node = self.node(path, fetch=False)
        return self._index_from_node(node, column)

    def _handle_from_path_arg(
        self,
        path: str,
        column: int,
    ) -> QModelIndex:
        print("<SDM> [_handle_from_path_arg scope] path: ", path)
        pathNodeResult = self.node_path(path)
        fInfo = pathNodeResult.fileInfo()
        print(
            "<SDM> [_handle_from_path_arg scope] pathNodeResult: ",
            None if fInfo is None else fInfo.path(),
            "children count:",
            len(pathNodeResult.children),
        )  # noqa: E501

        idx = self._index_from_node(pathNodeResult, column)

        if not idx.isValid():
            return QModelIndex()
        if idx.column() != column:
            idx = idx.sibling(idx.row(), column)
        fInfo = typing.cast("PyFileSystemNode", idx.internalPointer()).fileInfo()
        print("<SDM> [_handle_from_path_arg scope] final idx: ", fInfo and fInfo.path())

        return idx

    def _handle_from_node_arg(self, node: PyFileSystemNode, column: int) -> QModelIndex:
        print("<SDM> [_handle_from_node_arg node.fileName ", node.fileName)
        parentNode: PyFileSystemNode | None = None if node is None else node.parent
        if node is self._root or parentNode is None or not node.isVisible:
            return QModelIndex()

        assert node is not None
        visualRow = self.translateVisibleLocation(parentNode, parentNode.visibleLocation(node.fileName))
        print("<SDM> [_handle_from_node_arg scope] visualRow: ", visualRow)

        return self.createIndex(visualRow, column, node)

    def parent(self, index: QModelIndex) -> QModelIndex:
        """Parent method matching C++ lines 590-609 exactly.

        Matches:
        QModelIndex QFileSystemModel::parent(const QModelIndex &index) const
        {
            Q_D(const QFileSystemModel);
            if (!d->indexValid(index))
                return QModelIndex();

            QFileSystemModelPrivate::QFileSystemNode *indexNode = d->node(index);
            Q_ASSERT(indexNode != nullptr);
            QFileSystemModelPrivate::QFileSystemNode *parentNode = indexNode->parent;
            if (parentNode == nullptr || parentNode == &d->root)
                return QModelIndex();

            // get the parent's row
            QFileSystemModelPrivate::QFileSystemNode *grandParentNode = parentNode->parent;
            Q_ASSERT(grandParentNode->children.contains(parentNode->fileName));
            int visualRow = d->translateVisibleLocation(grandParentNode, grandParentNode->visibleLocation(grandParentNode->children.value(parentNode->fileName)->fileName));
            if (visualRow == -1)
                return QModelIndex();
            return createIndex(visualRow, 0, parentNode);
        }
        """
        # indexValid equivalent: index.isValid() and index.model() == self
        if not index.isValid() or index.model() != self:
            return QModelIndex()

        indexNode = self.node(index)
        assert indexNode is not None
        parentNode = indexNode.parent
        if parentNode is None or parentNode == self._root:
            return QModelIndex()

        # get the parent's row
        grandParentNode = parentNode.parent
        assert grandParentNode is not None
        assert parentNode.fileName in grandParentNode.children
        childNode = grandParentNode.children[parentNode.fileName]
        visualRow = self.translateVisibleLocation(grandParentNode, grandParentNode.visibleLocation(childNode.fileName))
        if visualRow == -1:
            return QModelIndex()
        return self.createIndex(visualRow, 0, parentNode)

    def hasChildren(self, parent: QModelIndex = QModelIndex()) -> bool:  # noqa: B008
        """Has children matching C++ lines 635-647 exactly.

        Matches:
        bool QFileSystemModel::hasChildren(const QModelIndex &parent) const
        {
            Q_D(const QFileSystemModel);
            if (parent.column() > 0)
                return false;

            if (!parent.isValid()) // drives
                return true;

            const QFileSystemModelPrivate::QFileSystemNode *indexNode = d->node(parent);
            Q_ASSERT(indexNode);
            return (indexNode->isDir());
        }
        """
        if parent.column() > 0:
            return False

        if not parent.isValid():  # drives
            return True

        indexNode = self.node(parent)
        assert indexNode is not None
        return indexNode.isDir()

    def canFetchMore(self, parent: QModelIndex) -> bool:
        """Can fetch more matching C++ lines 652-659 exactly.

        Matches:
        bool QFileSystemModel::canFetchMore(const QModelIndex &parent) const
        {
            Q_D(const QFileSystemModel);
            if (!d->setRootPath)
                return false;
            const QFileSystemModelPrivate::QFileSystemNode *indexNode = d->node(parent);
            return (!indexNode->populatedChildren);
        }
        """
        if not self._setRootPath:
            return False
        indexNode = self.node(parent)
        return not indexNode.populatedChildren

    def fetchMore(self, parent: QModelIndex) -> None:
        """Fetch more matching C++ lines 664-676 exactly.

        Matches:
        void QFileSystemModel::fetchMore(const QModelIndex &parent)
        {
            Q_D(QFileSystemModel);
            if (!d->setRootPath)
                return;
            QFileSystemModelPrivate::QFileSystemNode *indexNode = d->node(parent);
            if (indexNode->populatedChildren)
                return;
            indexNode->populatedChildren = true;
        #if QT_CONFIG(filesystemwatcher)
            d->fileInfoGatherer->list(filePath(parent));
        #endif
        }
        """
        if not self._setRootPath:
            return
        indexNode = self.node(parent)
        if indexNode.populatedChildren:
            return
        indexNode.populatedChildren = True
        # QT_CONFIG(filesystemwatcher) - always true
        self._fileInfoGatherer.list(self.filePath(parent))

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        """Row count matching C++ lines 681-692 exactly.

        Matches:
        int QFileSystemModel::rowCount(const QModelIndex &parent) const
        {
            Q_D(const QFileSystemModel);
            if (parent.column() > 0)
                return 0;

            if (!parent.isValid())
                return d->root.visibleChildren.size();

            const QFileSystemModelPrivate::QFileSystemNode *parentNode = d->node(parent);
            return parentNode->visibleChildren.size();
        }
        """
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            return len(self._root.visibleChildren)

        parentNode = self.node(parent)
        return len(parentNode.visibleChildren)

    def columnCount(
        self,
        parent: QModelIndex = QModelIndex(),
    ) -> int:  # noqa: B008
        """Column count matching C++ lines 697-700 exactly.

        Matches:
        int QFileSystemModel::columnCount(const QModelIndex &parent) const
        {
            return (parent.column() > 0) ? 0 : QFileSystemModelPrivate::NumColumns;
        }
        """
        if parent.column() > 0:
            return 0
        return 4  # NumColumns

    def _name(
        self,
        index: QModelIndex,
    ) -> str:
        """Name method matching C++ QFileSystemModelPrivate::name (lines 836-850) exactly.

        Matches:
        QString QFileSystemModelPrivate::name(const QModelIndex &index) const
        {
            if (!index.isValid())
                return QString();
            QFileSystemNode *dirNode = node(index);
            if (
        #if QT_CONFIG(filesystemwatcher)
                fileInfoGatherer->resolveSymlinks() &&
        #endif
                !resolvedSymLinks.isEmpty() && dirNode->isSymLink(/* ignoreNtfsSymLinks = */ true)) {
                QString fullPath = QDir::fromNativeSeparators(filePath(index));
                return resolvedSymLinks.value(fullPath, dirNode->fileName);
            }
            return dirNode->fileName;
        }
        """
        if not index.isValid():
            return ""
        dirNode = self.node(index)
        # QT_CONFIG(filesystemwatcher) - always true
        if (
            self._fileInfoGatherer.resolveSymlinks()
            and self._resolvedSymLinks
            and dirNode.isSymLink(ignoreNtfsSymLinks=True)
        ):
            fullPath = QDir.fromNativeSeparators(self.filePath(index))
            return self._resolvedSymLinks.get(fullPath, dirNode.fileName)
        return dirNode.fileName

    def _displayName(
        self,
        index: QModelIndex,
    ) -> str:
        """Matches C++ QFileSystemModelPrivate::displayName (lines 855-863)."""
        if os.name == "nt":
            dir_node = self.node(index)
            if dir_node.volumeName:
                return dir_node.volumeName
        return self._name(index)

    def _size(
        self,
        index: QModelIndex,
    ) -> str:
        """Matches C++ QFileSystemModelPrivate::size (lines 784-801)."""
        if not index.isValid():
            return ""
        n = self.node(index)
        if n.isDir():
            # Windows - ""
            # OS X - "--"
            # For now, return "" for all platforms (Windows behavior)
            return ""
        return self._size_bytes(n.size())

    def _size_bytes(
        self,
        bytes: int,
    ) -> str:
        """Matches C++ QFileSystemModelPrivate::size(qint64 bytes) (lines 803-806)."""
        from qtpy.QtCore import QLocale

        return QLocale.system().formattedDataSize(bytes)

    def _type(
        self,
        index: QModelIndex,
    ) -> str:
        """Matches C++ QFileSystemModelPrivate::type (lines 826-831)."""
        if not index.isValid():
            return ""
        return self.node(index).type()

    def _time(
        self,
        index: QModelIndex,
    ) -> str:
        """Matches C++ QFileSystemModelPrivate::time (lines 811-821)."""
        if not index.isValid():
            return ""
        # QT_CONFIG(datestring) - assume true
        from qtpy.QtCore import QLocale, QTimeZone

        # QTimeZone.LocalTime - matches usage in pyextendedinformation.py
        local_tz = QTimeZone.LocalTime  # type: ignore[attr-defined]
        return QLocale.system().toString(self.node(index).lastModified(local_tz), QLocale.FormatType.ShortFormat)

    def _icon(
        self,
        index: QModelIndex,
    ) -> QIcon:
        """Matches C++ QFileSystemModelPrivate::icon (lines 868-873)."""
        if not index.isValid():
            return QIcon()
        return self.node(index).icon()

    def data(
        self,
        index: QModelIndex,
        role: Qt.ItemDataRole | int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:  # noqa: C901, PLR0911, PLR0912
        """Data method matching C++ lines 728-779 exactly.

        Matches:
        QVariant QFileSystemModel::data(const QModelIndex &index, int role) const
        {
            Q_D(const QFileSystemModel);
            if (!index.isValid() || index.model() != this)
                return QVariant();

            switch (role) {
            case Qt::EditRole:
                if (index.column() == QFileSystemModelPrivate::NameColumn)
                    return d->name(index);
                Q_FALLTHROUGH();
            case Qt::DisplayRole:
                switch (index.column()) {
                case QFileSystemModelPrivate::NameColumn: return d->displayName(index);
                case QFileSystemModelPrivate::SizeColumn: return d->size(index);
                case QFileSystemModelPrivate::TypeColumn: return d->type(index);
                case QFileSystemModelPrivate::TimeColumn: return d->time(index);
                default:
                    qWarning("data: invalid display value column %d", index.column());
                    break;
                }
                break;
            case FilePathRole:
                return filePath(index);
            case FileNameRole:
                return d->name(index);
            case FileInfoRole:
                return QVariant::fromValue(fileInfo(index));
            case Qt::DecorationRole:
                if (index.column() == QFileSystemModelPrivate::NameColumn) {
                    QIcon icon = d->icon(index);
        #if QT_CONFIG(filesystemwatcher)
                    if (icon.isNull()) {
                        using P = QAbstractFileIconProvider;
                        if (auto *provider = d->fileInfoGatherer->iconProvider())
                            icon = provider->icon(d->node(index)->isDir() ? P::Folder: P::File);
                    }
        #endif // filesystemwatcher
                    return icon;
                }
                break;
            case Qt::TextAlignmentRole:
                if (index.column() == QFileSystemModelPrivate::SizeColumn)
                    return QVariant(Qt::AlignTrailing | Qt::AlignVCenter);
                break;
            case FilePermissions:
                int p = permissions(index);
                return p;
            }

            return QVariant();
        }
        """
        if not index.isValid() or index.model() != self:
            return QVariant()

        # NameColumn = 0, SizeColumn = 1, TypeColumn = 2, TimeColumn = 3
        if role == Qt.ItemDataRole.EditRole:
            if index.column() == 0:  # NameColumn
                return self._name(index)
            # Fall through to DisplayRole
        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:  # NameColumn
                return self._displayName(index)
            if index.column() == 1:  # SizeColumn
                return self._size(index)
            if index.column() == 2:  # TypeColumn
                return self._type(index)
            if index.column() == 3:  # TimeColumn
                return self._time(index)
            # qWarning equivalent
            return QVariant()

        if role == self.FilePathRole:
            return self.filePath(index)
        if role == self.FileNameRole:
            return self._name(index)
        if role == self.FileInfoRole:
            # QVariant::fromValue equivalent - in PyQt6/PySide6, QVariant can be constructed directly
            return QVariant(self.fileInfo(index))
        if role == Qt.ItemDataRole.DecorationRole:
            if index.column() == 0:  # NameColumn
                icon = self._icon(index)
                # QT_CONFIG(filesystemwatcher) - always true
                if icon.isNull():
                    provider = self._fileInfoGatherer.iconProvider()
                    if provider:
                        node_obj = self.node(index)
                        icon = provider.icon(QFileIconProvider.IconType.Folder if node_obj.isDir() else QFileIconProvider.IconType.File)
                return icon
        if role == Qt.ItemDataRole.TextAlignmentRole:
            if index.column() == 1:  # SizeColumn
                return QVariant(Qt.AlignmentFlag.AlignTrailing | Qt.AlignmentFlag.AlignVCenter)
        if role == self.FilePermissions:
            p = self.permissions(index)
            return p

        return QVariant()

    def setData(
        self,
        index: QModelIndex,
        value: Any,
        role: Qt.ItemDataRole | int = Qt.ItemDataRole.EditRole,
    ) -> bool:
        print(
            f"<SDM> [setData scope] index.row(): {index.row()}, index.internalPointer().fileName: {index and index.internalPointer() and index.internalPointer().fileName}, role: ",
            role,
        )

        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False

        new_name = value
        print("<SDM> [setData scope] new_name: ", new_name)

        old_name = self.data(index)
        print("<SDM> [setData scope] old_name: ", old_name)

        if new_name == old_name:
            return True

        path = self.filePath(index.parent())
        print("<SDM> [setData scope] path: ", path)

        old_path = os.path.join(path, old_name)  # noqa: PTH118
        print("<SDM> [setData scope] old_path: ", old_path)

        new_path = os.path.join(path, new_name)  # noqa: PTH118
        print("<SDM> [setData scope] new_path: ", new_path)

        if not os.rename(old_path, new_path):  # noqa: PTH104
            return False

        node = self.node(index)
        print("<SDM> [setData node.fileName ", node.fileName)

        parent_node = node.parent
        print("<SDM> [setData scope] parent_node.fileName ", None if parent_node is None else parent_node.fileName)

        if parent_node is not None:
            self.removeNode(parent_node, old_name)
            self.addNode(parent_node, new_name, QFileInfo(new_path))
        return True

    def flags(
        self,
        index: QModelIndex,
    ) -> Qt.ItemFlag:  # type: ignore[attr-defined]
        flags = super().flags(index)
        print("<SDM> [flags scope] flags: ", flags)

        if not index.isValid():
            return flags

        node = self.node(index)
        print("<SDM> [flags node.fileName ", node.fileName)

        if not self._readOnly and index.column() == 0 and bool(node.permissions() & QFileDevice.Permission.WriteUser):  # type: ignore[attr-defined]
            flags |= Qt.ItemFlag.ItemIsEditable
            if node.isDir():
                flags |= Qt.ItemFlag.ItemIsDropEnabled
        return flags

    def mimeTypes(self) -> list[str]:
        return ["text/uri-list"]

    def mimeData(
        self,
        indexes: Iterable[QModelIndex],
    ) -> QMimeData:
        urls: list[QUrl] = [QUrl.fromLocalFile(self.filePath(index)) for index in indexes if index.column() == 0]
        mime_data = QMimeData()
        mime_data.setUrls(urls)
        return mime_data

    def dropMimeData(
        self,
        data: QMimeData | None,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex,
    ) -> bool:
        """Handle drop mime data matching C++ lines 1226-1264 exactly.

        Matches:
        bool QFileSystemModel::dropMimeData(const QMimeData *data, Qt::DropAction action,
                                     int row, int column, const QModelIndex &parent)
        {
            Q_UNUSED(row);
            Q_UNUSED(column);
            if (!parent.isValid() || isReadOnly())
                return false;

            bool success = true;
            QString to = filePath(parent) + QDir::separator();

            QList<QUrl> urls = data->urls();
            QList<QUrl>::const_iterator it = urls.constBegin();

            switch (action) {
            case Qt::CopyAction:
                for (; it != urls.constEnd(); ++it) {
                    QString path = (*it).toLocalFile();
                    success = QFile::copy(path, to + QFileInfo(path).fileName()) && success;
                }
                break;
            case Qt::LinkAction:
                for (; it != urls.constEnd(); ++it) {
                    QString path = (*it).toLocalFile();
                    success = QFile::link(path, to + QFileInfo(path).fileName()) && success;
                }
                break;
            case Qt::MoveAction:
                for (; it != urls.constEnd(); ++it) {
                    QString path = (*it).toLocalFile();
                    success = QFile::rename(path, to + QFileInfo(path).fileName()) && success;
                }
                break;
            default:
                return false;
            }

            return success;
        }
        """
        # Q_UNUSED(row) and Q_UNUSED(column) - parameters unused in C++
        if not parent.isValid() or self.isReadOnly():
            return False

        if data is None:
            return False

        success = True
        to = self.filePath(parent) + QDir.separator()

        urls = data.urls()

        if action == Qt.DropAction.CopyAction:
            for url in urls:
                path = url.toLocalFile()
                success = QFile.copy(path, to + QFileInfo(path).fileName()) and success
        elif action == Qt.DropAction.LinkAction:
            for url in urls:
                path = url.toLocalFile()
                success = QFile.link(path, to + QFileInfo(path).fileName()) and success
        elif action == Qt.DropAction.MoveAction:
            for url in urls:
                path = url.toLocalFile()
                success = QFile.rename(path, to + QFileInfo(path).fileName()) and success
        else:
            return False

        return success

    def supportedDropActions(self) -> Qt.DropAction:  # type: ignore[attr-defined]
        return Qt.DropAction.CopyAction | Qt.DropAction.MoveAction | Qt.DropAction.LinkAction

    def filePath(
        self,
        index: QModelIndex,
    ) -> str:
        path: list[str] = []
        print("<SDM> [filePath scope] path: ", path)

        while index.isValid():
            node = self.node(index)
            fInfo = node.fileInfo()
            print("<SDM> [filePath scope] node.fileName", node.fileName, "node.fileInfo.path()", None if fInfo is None else fInfo.path())

            path.insert(0, node.fileName)
            index = index.parent()
            print("<SDM> [filePath scope] index.row(): ", None if index is None else index.row(), "internalPointer:", index.internalPointer())

        return str(pathlib.Path(*path))

    def fileInfo(
        self,
        index: QModelIndex,
    ) -> QFileInfo:
        return QFileInfo(self.filePath(index))

    def fileIcon(
        self,
        index: QModelIndex,
    ) -> QIcon:
        return self.node(index).icon()

    def fileName(
        self,
        index: QModelIndex,
    ) -> str:
        return self.node(index).fileName

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: Qt.ItemDataRole | int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:  # noqa: PLR0911
        if role == Qt.ItemDataRole.DecorationRole and section == 0:
            return QIcon()
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignLeft

        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if section == 0:
                return "Name"
            if section == 1:
                return "Size"
            if section == 2:  # noqa: PLR2004
                return "Type"
            if section == 3:  # noqa: PLR2004
                return "Date Modified"

        return super().headerData(section, orientation, role)

    def setRootPath(
        self,
        newPath: str,
    ) -> QModelIndex:  # noqa: N803
        """Set root path matching C++ lines 1502-1564 exactly.

        Matches:
        QModelIndex QFileSystemModel::setRootPath(const QString &newPath)
        {
            Q_D(QFileSystemModel);
        #ifdef Q_OS_WIN
        #ifdef Q_OS_WIN32
            QString longNewPath = qt_GetLongPathName(newPath);
        #else
            QString longNewPath = QDir::fromNativeSeparators(newPath);
        #endif
        #else
            QString longNewPath = newPath;
        #endif
            //we remove .. and . from the given path if exist
            if (!newPath.isEmpty())
                longNewPath = QDir::cleanPath(longNewPath);

            d->setRootPath = true;

            //user don't ask for the root path ("") but the conversion failed
            if (!newPath.isEmpty() && longNewPath.isEmpty())
                return d->index(rootPath());

            if (d->rootDir.path() == longNewPath)
                return d->index(rootPath());

            auto node = d->node(longNewPath);
            QFileInfo newPathInfo;
            if (node && node->hasInformation())
                newPathInfo = node->fileInfo();
            else
                newPathInfo = QFileInfo(longNewPath);

            bool showDrives = (longNewPath.isEmpty() || longNewPath == QFileSystemModelPrivate::myComputer());
            if (!showDrives && !newPathInfo.exists())
                return d->index(rootPath());

            //We remove the watcher on the previous path
            if (!rootPath().isEmpty() && rootPath() != "."_L1) {
                //This remove the watcher for the old rootPath
        #if QT_CONFIG(filesystemwatcher)
                d->fileInfoGatherer->removePath(rootPath());
        #endif
                //This line "marks" the node as dirty, so the next fetchMore
                //call on the path will ask the gatherer to install a watcher again
                //But it doesn't re-fetch everything
                d->node(rootPath())->populatedChildren = false;
            }

            // We have a new valid root path
            d->rootDir = QDir(longNewPath);
            QModelIndex newRootIndex;
            if (showDrives) {
                // otherwise dir will become '.'
                d->rootDir.setPath(""_L1);
            } else {
                newRootIndex = d->index(d->rootDir.path());
            }
            fetchMore(newRootIndex);
            emit rootPathChanged(longNewPath);
            d->forceSort = true;
            d->delayedSort();
            return newRootIndex;
        }
        """
        # Get long path name matching C++ lines 1505-1513
        if os.name == "nt":
            longNewPath = qt_GetLongPathName(newPath)
        else:
            longNewPath = newPath
        
        # Remove .. and . from the given path if exist (line 1515-1516)
        if newPath:
            longNewPath = QDir.cleanPath(longNewPath)
        
        self._setRootPath = True
        
        # User don't ask for the root path ("") but the conversion failed (lines 1521-1522)
        if newPath and not longNewPath:
            return self._index_from_node(self.node(self.rootPath()), 0)
        
        # If root path unchanged, return existing index (lines 1524-1525)
        if self._rootDir.path() == longNewPath:
            return self._index_from_node(self.node(self.rootPath()), 0)
        
        # Get node and file info (lines 1527-1532)
        node = self.node(longNewPath)
        if node and node.hasInformation():
            newPathInfo = node.fileInfo()
        else:
            newPathInfo = QFileInfo(longNewPath)
        
        # Check if we should show drives (line 1534)
        showDrives = not longNewPath or longNewPath == self._myComputer()
        if not showDrives and not newPathInfo.exists():
            return self._index_from_node(self.node(self.rootPath()), 0)
        
        # Remove watcher on previous path (lines 1538-1548)
        if self.rootPath() and self.rootPath() != ".":
            # QT_CONFIG(filesystemwatcher) - always true
            self._fileInfoGatherer.removePath(self.rootPath())
            # Mark node as dirty
            self.node(self.rootPath()).populatedChildren = False
        
        # We have a new valid root path (lines 1550-1558)
        self._rootDir = QDir(longNewPath)
        newRootIndex = QModelIndex()
        if showDrives:
            # otherwise dir will become '.'
            self._rootDir.setPath("")
        else:
            newRootIndex = self._index_from_node(self.node(self._rootDir.path()), 0)
        
        self.fetchMore(newRootIndex)
        self.rootPathChanged.emit(longNewPath)
        self._forceSort = True
        self._delayedSort()
        
        return newRootIndex

    def rootPath(self) -> str:
        return self._rootDir.path()

    def rootDirectory(self) -> QDir:
        dir_ = QDir(self._rootDir)
        print("<SDM> [rootDirectory scope] dir_ = QDir(self._rootDir): ", dir_.path())

        dir_.setNameFilters(self.nameFilters())
        dir_.setFilter(self.filter())  # pyright: ignore[reportArgumentType]
        return dir_

    def setIconProvider(
        self,
        provider: QFileIconProvider,
    ):
        if self._fileInfoGatherer.m_iconProvider == provider:
            return
        self._fileInfoGatherer.m_iconProvider = provider
        self._q_performDelayedSort()

    def iconProvider(self) -> QAbstractFileIconProvider | None:
        """Return icon provider matching C++ QAbstractFileIconProvider *iconProvider() const (line 99)."""
        return self._fileInfoGatherer.m_iconProvider

    def setFilter(
        self,
        filters: QDir.Filter,  # type: ignore[attr-defined]
    ):
        """Set filter matching C++ lines 1624-1636 exactly.

        Matches:
        void QFileSystemModel::setFilter(QDir::Filters filters)
        {
            Q_D(QFileSystemModel);
            if (d->filters == filters)
                return;
            const bool changingCaseSensitivity =
                filters.testFlag(QDir::CaseSensitive) != d->filters.testFlag(QDir::CaseSensitive);
            d->filters = filters;
            if (changingCaseSensitivity)
                d->rebuildNameFilterRegexps();
            d->forceSort = true;
            d->delayedSort();
        }
        """
        if self._filters == filters:
            return
        changingCaseSensitivity = (
            bool(filters & QDir.Filter.CaseSensitive) != bool(self._filters & QDir.Filter.CaseSensitive)  # type: ignore[attr-defined]
        )
        self._filters = filters
        if changingCaseSensitivity:
            self._rebuildNameFilterRegexps()
        self._forceSort = True
        self._delayedSort()

    def filter(self) -> QDir.Filter:  # type: ignore[attr-defined]
        return self._filters

    def setResolveSymlinks(self, enable: bool):  # noqa: FBT001
        """Set resolve symlinks matching C++ lines 1662-1670 exactly.

        Matches:
        void QFileSystemModel::setResolveSymlinks(bool enable)
        {
        #if QT_CONFIG(filesystemwatcher)
            Q_D(QFileSystemModel);
            d->fileInfoGatherer->setResolveSymlinks(enable);
        #else
            Q_UNUSED(enable);
        #endif
        }
        """
        # QT_CONFIG(filesystemwatcher) - always true
        self._fileInfoGatherer.setResolveSymlinks(enable)
        self._forceSort = True
        self._delayedSort()

    def resolveSymlinks(self) -> bool:
        """Resolve symlinks matching C++ lines 1672-1680 exactly.

        Matches:
        bool QFileSystemModel::resolveSymlinks() const
        {
        #if QT_CONFIG(filesystemwatcher)
            Q_D(const QFileSystemModel);
            return d->fileInfoGatherer->resolveSymlinks();
        #else
            return false;
        #endif
        }
        """
        # QT_CONFIG(filesystemwatcher) - always true
        return self._fileInfoGatherer.resolveSymlinks()

    def setReadOnly(
        self,
        enable: bool,
    ):
        self._readOnly = enable
        print("<SDM> [setReadOnly scope] self._readOnly: ", self._readOnly)

    def isReadOnly(self) -> bool:
        return self._readOnly

    def setNameFilterDisables(self, enable: bool):  # noqa: FBT001
        if self._nameFilterDisables == enable:
            return
        self._nameFilterDisables = enable
        self._forceSort = True
        self._delayedSort()

    def nameFilterDisables(self) -> bool:
        return self._nameFilterDisables

    def setNameFilters(self, filters: list[str]):
        if self._nameFilters == filters:
            return
        self._nameFilters = filters
        # Rebuild name filter regexps matching C++ line 1752
        self._rebuildNameFilterRegexps()
        self._forceSort = True
        self._delayedSort()

    def nameFilters(self) -> list[str]:
        return self._nameFilters

    directoryLoaded: ClassVar[Signal] = QFileSystemModel.directoryLoaded
    rootPathChanged: ClassVar[Signal] = QFileSystemModel.rootPathChanged
    fileRenamed: ClassVar[Signal] = QFileSystemModel.fileRenamed

    # Option and Roles are defined as inner classes above (lines 275-272)
    # These are class attributes that reference the inner classes
    # In PyQt6, Options doesn't exist as a separate type - Option is a Flag enum

    DontWatchForChanges: QFileSystemModel.Option = QFileSystemModel.Option.DontWatchForChanges  # type: ignore[attr-defined]
    DontResolveSymlinks: QFileSystemModel.Option = QFileSystemModel.Option.DontResolveSymlinks  # type: ignore[attr-defined]
    DontUseCustomDirectoryIcons: QFileSystemModel.Option = QFileSystemModel.Option.DontUseCustomDirectoryIcons  # type: ignore[attr-defined]

    FileIconRole: QFileSystemModel.Roles | Qt.ItemDataRole | Literal[1] = Qt.ItemDataRole.DecorationRole
    FilePathRole: QFileSystemModel.Roles | Qt.ItemDataRole | Literal[257] = Qt.ItemDataRole.UserRole + 1
    FileNameRole: QFileSystemModel.Roles | Qt.ItemDataRole | Literal[258] = Qt.ItemDataRole.UserRole + 2
    FilePermissions: QFileSystemModel.Roles | Qt.ItemDataRole | Literal[259] = Qt.ItemDataRole.UserRole + 3
    FileInfoRole: QFileSystemModel.Roles | Qt.ItemDataRole | Literal[260] = Qt.ItemDataRole.UserRole + 4

    NumColumns: int = 4


class MainWindow(QMainWindow):
    def __init__(
        self,
        rootPath: Path,
    ):  # noqa: N803
        super().__init__()

        self.setWindowTitle("QTreeView with HTMLDelegate")

        self.fsTreeView: RobustTreeView = RobustTreeView(self, use_columns=True)
        self.fsModel: PyFileSystemModel = PyFileSystemModel(self)
        self.fsTreeView.setModel(self.fsModel)
        self.fsModel.setRootPath(str(rootPath))

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.fsTreeView)
        self.setCentralWidget(central_widget)
        self.setMinimumSize(824, 568)
        self.resize_and_center()

    def resize_and_center(self):
        """Resize and center the window on the screen."""
        self.adjust_view_size()
        screen = QApplication.primaryScreen().geometry()  # pyright: ignore[reportOptionalMemberAccess]
        print("<SDM> [resize_and_center scope] screen: ", screen)

        new_x = (screen.width() - self.width()) // 2
        print("<SDM> [resize_and_center scope] new_x: ", new_x)

        new_y = (screen.height() - self.height()) // 2
        print("<SDM> [resize_and_center scope] new_y: ", new_y)

        new_x = max(0, min(new_x, screen.width() - self.width()))
        print("<SDM> [resize_and_center scope] new_x: ", new_x)

        new_y = max(0, min(new_y, screen.height() - self.height()))
        print("<SDM> [resize_and_center scope] new_y: ", new_y)

        self.move(new_x, new_y)

    def adjust_view_size(self):
        """Adjust the view size based on content."""
        sb: QScrollBar | None = self.fsTreeView.verticalScrollBar()
        print("<SDM> [adjust_view_size scope] sb: ", sb)

        assert sb is not None
        width = sb.width() + 4  # Add some padding
        print("<SDM> [adjust_view_size scope] width: ", width)

        for i in range(self.fsModel.columnCount()):
            width += self.fsTreeView.columnWidth(i)
        print("all column's widths:", width)
        if QDesktopWidget is None:
            app = typing.cast("QApplication", QApplication.instance())
            screen = app.primaryScreen()
            print("<SDM> [adjust_view_size scope] screen: ", screen)

            assert screen is not None
            screen_width = screen.geometry().width()
        else:
            screen_width = QDesktopWidget().availableGeometry().width()
        print("<SDM> [adjust_view_size scope] screen_width: ", screen_width)

        print("Screen width:", screen_width)
        self.resize(min(width, screen_width), self.height())


if __name__ == "__main__":
    print("<SDM> [main block scope] __name__: ", __name__)
    app = QApplication(sys.argv)
    print("<SDM> [adjust_view_size scope] app: ", app)

    base_path = Path(r"C:\Program Files (x86)\Steam\steamapps\common\swkotor").resolve()
    print("<SDM> [adjust_view_size scope] base_path: ", base_path)

    main_window = MainWindow(base_path)
    print("<SDM> [adjust_view_size scope] main_window: ", main_window)

    main_window.show()

    sys.exit(app.exec())  # type: ignore[attr-defined]
