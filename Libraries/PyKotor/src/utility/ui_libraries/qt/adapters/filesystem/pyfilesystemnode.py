"""QFileSystemNode Python adapter matching Qt6 C++ source exactly.

This class matches qfilesystemmodel_p.h lines 74-196 (QFileSystemNode class).
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from qtpy.QtCore import QDateTime, QFileDevice, QFileInfo, QTimeZone  # noqa: E402
from qtpy.QtGui import QIcon  # noqa: E402

if TYPE_CHECKING:
    from qtpy.QtGui import QAbstractFileIconProvider

from utility.ui_libraries.qt.adapters.filesystem.pyextendedinformation import PyQExtendedInformation  # noqa: E402


class PyFileSystemNode:
    """Python adapter for QFileSystemNode matching Qt6 C++ source exactly.

    Matches qfilesystemmodel_p.h lines 74-196.
    
    C++ class definition:
    class QFileSystemNode {
    public:
        Q_DISABLE_COPY_MOVE(QFileSystemNode)
        explicit QFileSystemNode(const QString &filename = QString(), QFileSystemNode *p = nullptr)
            : fileName(filename), parent(p) {}
        ~QFileSystemNode() {
            qDeleteAll(children);
            delete info;
        }
        // ... member functions ...
    private:
        QString fileName;
    #if defined(Q_OS_WIN)
        QString volumeName;
    #endif
        QExtendedInformation *info = nullptr;
        QHash<QFileSystemModelNodePathKey, QFileSystemNode *> children;
        QList<QString> visibleChildren;
        QFileSystemNode *parent;
        int dirtyChildrenIndex = -1;
        bool populatedChildren = false;
        bool isVisible = false;
    };
    """

    def __init__(
        self,
        filename: str = "",
        parent: PyFileSystemNode | None = None,
    ):
        """Initialize QFileSystemNode.

        Matches C++ constructor lines 79-80 exactly:
        explicit QFileSystemNode(const QString &filename = QString(), QFileSystemNode *p = nullptr)
            : fileName(filename), parent(p) {}
        """
        # Matches C++ line 86: QString fileName;
        self.fileName: str = filename
        # Matches C++ lines 87-89: #if defined(Q_OS_WIN) QString volumeName; #endif
        if os.name == "nt":
            self.volumeName: str = ""
        # Matches C++ line 192: QFileSystemNode *parent;
        self.parent: PyFileSystemNode | None = parent
        # Matches C++ line 191: QExtendedInformation *info = nullptr;
        self.info: PyQExtendedInformation | None = None
        # Matches C++ line 189: QHash<QFileSystemModelNodePathKey, QFileSystemNode *> children;
        # NOTE: In Python, we use dict[str, PyFileSystemNode] instead of QHash
        self.children: dict[str, PyFileSystemNode] = {}
        # Matches C++ line 190: QList<QString> visibleChildren;
        self.visibleChildren: list[str] = []
        # Matches C++ line 193: int dirtyChildrenIndex = -1;
        self.dirtyChildrenIndex: int = -1
        # Matches C++ line 194: bool populatedChildren = false;
        self.populatedChildren: bool = False
        # Matches C++ line 195: bool isVisible = false;
        self.isVisible: bool = False

    def __del__(self):
        """Destructor matching C++ lines 81-84 exactly.

        Matches:
        ~QFileSystemNode() {
            qDeleteAll(children);
            delete info;
        }
        """
        # qDeleteAll(children) - Python's garbage collector will handle dict cleanup
        # delete info - Python will handle None assignment
        # NOTE: In Python, we can't explicitly delete like C++, but we clear references
        self.children.clear()
        self.info = None

    def size(self) -> int:
        """Return file size matching C++ line 91 exactly.

        Matches: inline qint64 size() const { if (info && !info->isDir()) return info->size(); return 0; }
        """
        if self.info and not self.info.isDir():
            return self.info.size()
        return 0

    def type(self) -> str:
        """Return file type matching C++ line 92 exactly.

        Matches: inline QString type() const { if (info) return info->displayType; return QLatin1StringView(""); }
        """
        if self.info:
            return self.info.displayType
        return ""

    def lastModified(self, tz: QTimeZone) -> QDateTime:  # type: ignore[attr-defined]
        """Return last modified time matching C++ line 93 exactly.

        Matches: inline QDateTime lastModified(const QTimeZone &tz) const { return info ? info->lastModified(tz) : QDateTime(); }
        """
        if self.info:
            return self.info.lastModified(tz)
        return QDateTime()

    def permissions(self) -> QFileDevice.Permission:  # type: ignore[attr-defined]
        """Return permissions matching C++ line 94 exactly.

        Matches: inline QFile::Permissions permissions() const { if (info) return info->permissions(); return { }; }
        """
        if self.info:
            return self.info.permissions()
        return QFileDevice.Permission()  # type: ignore[attr-defined]

    def isReadable(self) -> bool:
        """Check if readable matching C++ line 95 exactly.

        Matches: inline bool isReadable() const { return ((permissions() & QFile::ReadUser) != 0); }
        """
        return (self.permissions() & QFileDevice.Permission.ReadUser) != 0

    def isWritable(self) -> bool:
        """Check if writable matching C++ line 96 exactly.

        Matches: inline bool isWritable() const { return ((permissions() & QFile::WriteUser) != 0); }
        """
        return (self.permissions() & QFileDevice.Permission.WriteUser) != 0

    def isExecutable(self) -> bool:
        """Check if executable matching C++ line 97 exactly.

        Matches: inline bool isExecutable() const { return ((permissions() & QFile::ExeUser) != 0); }
        """
        return (self.permissions() & QFileDevice.Permission.ExeUser) != 0

    def isDir(self) -> bool:
        """Check if directory matching C++ lines 98-104 exactly.

        Matches:
        inline bool isDir() const {
            if (info)
                return info->isDir();
            if (children.size() > 0)
                return true;
            return false;
        }
        """
        if self.info:
            return self.info.isDir()
        if len(self.children) > 0:
            return True
        return False

    def fileInfo(self) -> QFileInfo:
        """Return QFileInfo matching C++ line 105 exactly.

        Matches: inline QFileInfo fileInfo() const { if (info) return info->fileInfo(); return QFileInfo(); }
        """
        if self.info:
            return self.info.fileInfo()
        return QFileInfo()

    def isFile(self) -> bool:
        """Check if file matching C++ line 106 exactly.

        Matches: inline bool isFile() const { if (info) return info->isFile(); return true; }
        """
        if self.info:
            return self.info.isFile()
        return True

    def isSystem(self) -> bool:
        """Check if system file matching C++ line 107 exactly.

        Matches: inline bool isSystem() const { if (info) return info->isSystem(); return true; }
        """
        if self.info:
            return self.info.isSystem()
        return True

    def isHidden(self) -> bool:
        """Check if hidden matching C++ line 108 exactly.

        Matches: inline bool isHidden() const { if (info) return info->isHidden(); return false; }
        """
        if self.info:
            return self.info.isHidden()
        return False

    def isSymLink(self, ignoreNtfsSymLinks: bool = False) -> bool:  # noqa: FBT001, FBT002
        """Check if symlink matching C++ line 109 exactly.

        Matches: inline bool isSymLink(bool ignoreNtfsSymLinks = false) const { return info && info->isSymLink(ignoreNtfsSymLinks); }
        """
        return bool(self.info and self.info.isSymLink(ignoreNtfsSymLinks))

    def caseSensitive(self) -> bool:
        """Check case sensitivity matching C++ line 110 exactly.

        Matches: inline bool caseSensitive() const { if (info) return info->isCaseSensitive(); return false; }
        """
        if self.info:
            return self.info.isCaseSensitive()
        return False

    def icon(self) -> QIcon:
        """Return icon matching C++ line 111 exactly.

        Matches: inline QIcon icon() const { if (info) return info->icon; return QIcon(); }
        """
        if self.info:
            return self.info.icon
        return QIcon()

    def __lt__(self, other: PyFileSystemNode) -> bool:
        """Less than operator matching C++ lines 113-117 exactly.

        Matches:
        inline bool operator <(const QFileSystemNode &node) const {
            if (caseSensitive() || node.caseSensitive())
                return fileName < node.fileName;
            return QString::compare(fileName, node.fileName, Qt::CaseInsensitive) < 0;
        }
        """
        if self.caseSensitive() or other.caseSensitive():
            return self.fileName < other.fileName
        # QString::compare with CaseInsensitive
        return self.fileName.lower() < other.fileName.lower()

    def __gt__(self, name: str) -> bool:
        """Greater than operator matching C++ lines 118-122 exactly.

        Matches:
        inline bool operator >(const QString &name) const {
            if (caseSensitive())
                return fileName > name;
            return QString::compare(fileName, name, Qt::CaseInsensitive) > 0;
        }
        """
        if self.caseSensitive():
            return self.fileName > name
        return self.fileName.lower() > name.lower()

    def __lt_str(self, name: str) -> bool:
        """Less than operator for string matching C++ lines 123-127.

        Note: Python doesn't support operator< for different types easily,
        so this is a helper method.
        """
        if self.caseSensitive():
            return self.fileName < name
        return self.fileName.lower() < name.lower()

    def __ne__(self, fileInfo: PyQExtendedInformation) -> bool:
        """Not equal operator matching C++ lines 128-130.

        Matches: inline bool operator !=(const QExtendedInformation &fileInfo) const { return !operator==(fileInfo); }
        """
        return not self.__eq__(fileInfo)

    def __eq__(self, other: object) -> bool:
        """Equality operators matching C++ lines 131-138.

        Matches:
        bool operator ==(const QString &name) const {
            if (caseSensitive())
                return fileName == name;
            return QString::compare(fileName, name, Qt::CaseInsensitive) == 0;
        }
        bool operator ==(const QExtendedInformation &fileInfo) const {
            return info && (*info == fileInfo);
        }
        """
        if isinstance(other, str):
            if self.caseSensitive():
                return self.fileName == other
            return self.fileName.lower() == other.lower()
        if isinstance(other, PyQExtendedInformation):
            return bool(self.info and self.info == other)
        return NotImplemented

    def __hash__(self) -> int:
        """Hash method to make PyFileSystemNode hashable for use as dictionary keys.

        Required because __eq__ is defined, which sets __hash__ to None by default.
        Nodes are used as keys in _bypassFilters dictionary, so they must be hashable.
        Uses filename and parent identity for consistent hashing.
        """
        # Hash based on filename (case-insensitive for consistency) and parent identity
        filename_hash = hash(self.fileName.lower())
        parent_hash = hash(id(self.parent)) if self.parent is not None else 0
        return hash((filename_hash, parent_hash))

    def hasInformation(self) -> bool:
        """Check if has information matching C++ line 140 exactly.

        Matches: inline bool hasInformation() const { return info != nullptr; }
        """
        return self.info is not None

    def populate(self, fileInfo: PyQExtendedInformation) -> None:
        """Populate node with file info matching C++ lines 142-146 exactly.

        Matches:
        void populate(const QExtendedInformation &fileInfo) {
            if (!info)
                info = new QExtendedInformation(fileInfo.fileInfo());
            (*info) = fileInfo;
        }
        
        Note: The C++ copy assignment operator copies all members. In Python,
        we create a new object if needed, then copy all fields.
        """
        if self.info is None:
            self.info = PyQExtendedInformation(fileInfo.fileInfo())
        # Copy assignment: (*info) = fileInfo;
        # This copies all members: mFileInfo, displayType, and icon
        self.info.mFileInfo = QFileInfo(fileInfo.fileInfo())
        self.info.displayType = fileInfo.displayType
        self.info.icon = fileInfo.icon

    def visibleLocation(self, childName: str) -> int:
        """Get visible location matching C++ lines 149-151 exactly.

        Matches:
        inline int visibleLocation(const QString &childName) {
            return visibleChildren.indexOf(childName);
        }
        """
        try:
            return self.visibleChildren.index(childName)
        except ValueError:
            return -1

    def updateIcon(self, iconProvider: QAbstractFileIconProvider | None, path: str) -> None:
        """Update icon matching C++ lines 152-169 exactly.

        Matches:
        void updateIcon(QAbstractFileIconProvider *iconProvider, const QString &path) {
            if (!iconProvider)
                return;

            if (info)
                info->icon = iconProvider->icon(QFileInfo(path));

            for (QFileSystemNode *child : std::as_const(children)) {
                //On windows the root (My computer) has no path so we don't want to add a / for nothing (e.g. /C:/)
                if (!path.isEmpty()) {
                    if (path.endsWith(u'/'))
                        child->updateIcon(iconProvider, path + child->fileName);
                    else
                        child->updateIcon(iconProvider, path + u'/' + child->fileName);
                } else
                    child->updateIcon(iconProvider, child->fileName);
            }
        }
        """
        from qtpy.QtGui import QAbstractFileIconProvider
        
        if iconProvider is None:
            return

        if self.info is not None:
            self.info.icon = iconProvider.icon(QFileInfo(path))

        for child in self.children.values():
            # On windows the root (My computer) has no path so we don't want to add a / for nothing (e.g. /C:/)
            if path:
                if path.endswith("/"):
                    child.updateIcon(iconProvider, path + child.fileName)
                else:
                    child.updateIcon(iconProvider, path + "/" + child.fileName)
            else:
                child.updateIcon(iconProvider, child.fileName)

    def retranslateStrings(self, iconProvider: QAbstractFileIconProvider | None, path: str) -> None:
        """Retranslate strings matching C++ lines 171-187 exactly.

        Matches:
        void retranslateStrings(QAbstractFileIconProvider *iconProvider, const QString &path) {
            if (!iconProvider)
                return;

            if (info)
                info->displayType = iconProvider->type(QFileInfo(path));
            for (QFileSystemNode *child : std::as_const(children)) {
                //On windows the root (My computer) has no path so we don't want to add a / for nothing (e.g. /C:/)
                if (!path.isEmpty()) {
                    if (path.endsWith(u'/'))
                        child->retranslateStrings(iconProvider, path + child->fileName);
                    else
                        child->retranslateStrings(iconProvider, path + u'/' + child->fileName);
                } else
                    child->retranslateStrings(iconProvider, child->fileName);
            }
        }
        """
        from qtpy.QtGui import QAbstractFileIconProvider
        
        if iconProvider is None:
            return

        if self.info is not None:
            self.info.displayType = iconProvider.type(QFileInfo(path))
        for child in self.children.values():
            # On windows the root (My computer) has no path so we don't want to add a / for nothing (e.g. /C:/)
            if path:
                if path.endswith("/"):
                    child.retranslateStrings(iconProvider, path + child.fileName)
                else:
                    child.retranslateStrings(iconProvider, path + "/" + child.fileName)
            else:
                child.retranslateStrings(iconProvider, child.fileName)
