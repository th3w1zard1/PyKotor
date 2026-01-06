"""QExtendedInformation Python adapter matching Qt6 C++ source exactly.

This class matches qfileinfogatherer_p.h lines 42-122 (QExtendedInformation class).

C++ class definition:
class QExtendedInformation {
public:
    enum Type { Dir, File, System };
    QExtendedInformation() {}
    QExtendedInformation(const QFileInfo &info) : mFileInfo(info) {}
    // ... member functions ...
private:
    QFileInfo mFileInfo;
    QString displayType;
    QIcon icon;
};
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from qtpy.QtCore import QDateTime, QFileDevice, QFileInfo, QTimeZone  # noqa: E402
from qtpy.QtGui import QIcon  # noqa: E402

if TYPE_CHECKING:
    pass


class PyQExtendedInformation:
    """Python adapter for QExtendedInformation matching Qt6 C++ source exactly.
    
    Matches qfileinfogatherer_p.h lines 42-122.
    """
    
    # Matches C++ line 44: enum Type { Dir, File, System };
    class Type:
        """Type enum matching C++ QExtendedInformation::Type exactly."""
        Dir = 0
        File = 1
        System = 2
    
    # Convenience constants matching C++ enum values
    Dir: int = Type.Dir
    File: int = Type.File
    System: int = Type.System

    def __init__(self, info: QFileInfo | None = None):
        """Initialize QExtendedInformation matching C++ constructors exactly.
        
        Matches C++ lines 46-47:
        QExtendedInformation() {}
        QExtendedInformation(const QFileInfo &info) : mFileInfo(info) {}
        """
        # Matches C++ line 121: QFileInfo mFileInfo;
        if info is None:
            self.mFileInfo: QFileInfo = QFileInfo()
        else:
            self.mFileInfo: QFileInfo = QFileInfo(info)
        # Matches C++ line 117: QString displayType;
        self.displayType: str = ""
        # Matches C++ line 118: QIcon icon;
        self.icon: QIcon = QIcon()

    def isDir(self) -> bool:
        """Return true if type() == Dir.
        
        Matches C++: inline bool isDir() { return type() == Dir; }
        """
        return self.type() == PyQExtendedInformation.Dir

    def isFile(self) -> bool:
        """Return true if type() == File.
        
        Matches C++: inline bool isFile() { return type() == File; }
        """
        return self.type() == PyQExtendedInformation.File

    def isSystem(self) -> bool:
        """Return true if type() == System.
        
        Matches C++: inline bool isSystem() { return type() == System; }
        """
        return self.type() == PyQExtendedInformation.System

    def __eq__(self, other: object) -> bool:
        """Equality operator matching C++ exactly.
        
        Matches C++ lines 53-58:
        bool operator ==(const QExtendedInformation &fileInfo) const {
           return mFileInfo == fileInfo.mFileInfo
           && displayType == fileInfo.displayType
           && permissions() == fileInfo.permissions()
           && lastModified(QTimeZone::UTC) == fileInfo.lastModified(QTimeZone::UTC);
        }
        """
        if not isinstance(other, PyQExtendedInformation):
            return False
        return (
            self.mFileInfo == other.mFileInfo
            and self.displayType == other.displayType
            and self.permissions() == other.permissions()
            and self.lastModified(QTimeZone.UTC) == other.lastModified(QTimeZone.UTC)
        )

    def isCaseSensitive(self) -> bool:
        """Return case sensitivity.
        
        Matches C++ lines 60-65 (QT_NO_FSFILEENGINE version not implemented,
        using platform check instead).
        """
        # C++ uses qt_isCaseSensitive from QFileInfoPrivate, we use platform check
        return os.name == "posix"

    def permissions(self) -> QFileDevice.Permissions:
        """Return file permissions.
        
        Matches C++ lines 67-69:
        QFile::Permissions permissions() const {
            return mFileInfo.permissions();
        }
        """
        return self.mFileInfo.permissions()

    def type(self) -> int:
        """Return Type enum value.
        
        Matches C++ lines 71-82:
        Type type() const {
            if (mFileInfo.isDir()) {
                return QExtendedInformation::Dir;
            }
            if (mFileInfo.isFile()) {
                return QExtendedInformation::File;
            }
            if (!mFileInfo.exists() && mFileInfo.isSymLink()) {
                return QExtendedInformation::System;
            }
            return QExtendedInformation::System;
        }
        """
        if self.mFileInfo.isDir():
            return PyQExtendedInformation.Dir
        if self.mFileInfo.isFile():
            return PyQExtendedInformation.File
        if not self.mFileInfo.exists() and self.mFileInfo.isSymLink():
            return PyQExtendedInformation.System
        return PyQExtendedInformation.System

    def isSymLink(self, ignoreNtfsSymLinks: bool = False) -> bool:  # noqa: FBT001, FBT002
        """Check if symlink, matching C++ exactly.
        
        Matches C++ lines 84-92:
        bool isSymLink(bool ignoreNtfsSymLinks = false) const
        {
            if (ignoreNtfsSymLinks) {
        #ifdef Q_OS_WIN
                return !mFileInfo.suffix().compare(QLatin1StringView("lnk"), Qt::CaseInsensitive);
        #endif
            }
            return mFileInfo.isSymLink();
        }
        """
        if ignoreNtfsSymLinks:
            if os.name == "nt":
                # C++: !mFileInfo.suffix().compare(QLatin1StringView("lnk"), Qt::CaseInsensitive)
                # This means: suffix equals "lnk" (case insensitive)
                return self.mFileInfo.suffix().lower() == "lnk"
        return self.mFileInfo.isSymLink()

    def isHidden(self) -> bool:
        """Return true if file is hidden.
        
        Matches C++ lines 94-96:
        bool isHidden() const {
            return mFileInfo.isHidden();
        }
        """
        return self.mFileInfo.isHidden()

    def fileInfo(self) -> QFileInfo:
        """Return QFileInfo.
        
        Matches C++ lines 98-100:
        QFileInfo fileInfo() const {
            return mFileInfo;
        }
        """
        return self.mFileInfo

    def lastModified(self, tz: QTimeZone = QTimeZone.LocalTime) -> QDateTime:
        """Return last modified time in timezone.
        
        Matches C++ lines 102-104:
        QDateTime lastModified(const QTimeZone &tz) const {
            return mFileInfo.lastModified(tz);
        }
        """
        return self.mFileInfo.lastModified(tz)

    def size(self) -> int:
        """Return file size.
        
        Matches C++ lines 106-115:
        qint64 size() const {
            qint64 size = -1;
            if (type() == QExtendedInformation::Dir)
                size = 0;
            if (type() == QExtendedInformation::File)
                size = mFileInfo.size();
            if (!mFileInfo.exists() && !mFileInfo.isSymLink())
                size = -1;
            return size;
        }
        """
        size = -1
        if self.type() == PyQExtendedInformation.Dir:
            size = 0
        if self.type() == PyQExtendedInformation.File:
            size = self.mFileInfo.size()
        if not self.mFileInfo.exists() and not self.mFileInfo.isSymLink():
            size = -1
        return size
