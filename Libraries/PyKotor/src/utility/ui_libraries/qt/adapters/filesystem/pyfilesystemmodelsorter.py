"""QFileSystemModelSorter Python adapter matching Qt6 C++ source exactly.

This class matches qfilesystemmodel.cpp lines 1041-1110 (QFileSystemModelSorter class).
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from qtpy.QtCore import QCollator, QDateTime, QTimeZone, Qt  # type: ignore[attr-defined]

if TYPE_CHECKING:
    from utility.ui_libraries.qt.adapters.filesystem.pyfilesystemnode import PyFileSystemNode


class PyFileSystemModelSorter:
    """Python adapter for QFileSystemModelSorter matching Qt6 C++ source exactly.

    Matches qfilesystemmodel.cpp lines 1041-1110:
    class QFileSystemModelSorter
    {
    public:
        inline QFileSystemModelSorter(int column) : sortColumn(column)
        {
            naturalCompare.setNumericMode(true);
            naturalCompare.setCaseSensitivity(Qt::CaseInsensitive);
        }
        // ... compareNodes method ...
        bool operator()(const QFileSystemModelPrivate::QFileSystemNode *l,
                      const QFileSystemModelPrivate::QFileSystemNode *r) const
        {
            return compareNodes(l, r);
        }
    private:
        QCollator naturalCompare;
        int sortColumn;
    };
    """

    def __init__(self, column: int):
        """Initialize sorter matching C++ lines 1044-1048 exactly.

        Matches:
        inline QFileSystemModelSorter(int column) : sortColumn(column)
        {
            naturalCompare.setNumericMode(true);
            naturalCompare.setCaseSensitivity(Qt::CaseInsensitive);
        }
        """
        self.sortColumn: int = column
        # Matches C++ line 1108: QCollator naturalCompare;
        self.naturalCompare: QCollator = QCollator()  # type: ignore[attr-defined]
        # Matches C++ line 1046: naturalCompare.setNumericMode(true);
        self.naturalCompare.setNumericMode(True)  # type: ignore[attr-defined]
        # Matches C++ line 1047: naturalCompare.setCaseSensitivity(Qt::CaseInsensitive);
        self.naturalCompare.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)  # type: ignore[attr-defined]

    def compareNodes(
        self,
        l: PyFileSystemNode,  # noqa: E741
        r: PyFileSystemNode,
    ) -> bool:
        """Compare nodes matching C++ lines 1050-1098 exactly.

        Matches:
        bool compareNodes(const QFileSystemModelPrivate::QFileSystemNode *l,
                        const QFileSystemModelPrivate::QFileSystemNode *r) const
        {
            switch (sortColumn) {
            case QFileSystemModelPrivate::NameColumn: {
        #ifndef Q_OS_MAC
                // place directories before files
                bool left = l->isDir();
                bool right = r->isDir();
                if (left ^ right)
                    return left;
        #endif
                return naturalCompare.compare(l->fileName, r->fileName) < 0;
            }
            case QFileSystemModelPrivate::SizeColumn:
            {
                // Directories go first
                bool left = l->isDir();
                bool right = r->isDir();
                if (left ^ right)
                    return left;

                qint64 sizeDifference = l->size() - r->size();
                if (sizeDifference == 0)
                    return naturalCompare.compare(l->fileName, r->fileName) < 0;

                return sizeDifference < 0;
            }
            case QFileSystemModelPrivate::TypeColumn:
            {
                int compare = naturalCompare.compare(l->type(), r->type());
                if (compare == 0)
                    return naturalCompare.compare(l->fileName, r->fileName) < 0;

                return compare < 0;
            }
            case QFileSystemModelPrivate::TimeColumn:
            {
                const QDateTime left = l->lastModified(QTimeZone::UTC);
                const QDateTime right = r->lastModified(QTimeZone::UTC);
                if (left == right)
                    return naturalCompare.compare(l->fileName, r->fileName) < 0;

                return left < right;
            }
            }
            Q_ASSERT(false);
            return false;
        }
        """
        # Matches C++ lines 1053-1063: NameColumn case
        if self.sortColumn == 0:  # NameColumn
            # Matches C++ lines 1055-1061: #ifndef Q_OS_MAC
            # Check if not macOS (Q_OS_MAC is defined on macOS)
            is_mac = False
            if os.name == "posix":
                try:
                    import platform
                    is_mac = platform.system() == "Darwin"
                except Exception:
                    pass
            if not is_mac:  # Not macOS
                # place directories before files
                left = l.isDir()
                right = r.isDir()
                if left != right:  # XOR
                    return left
            # Matches C++ line 1062: return naturalCompare.compare(l->fileName, r->fileName) < 0;
            return self.naturalCompare.compare(l.fileName, r.fileName) < 0  # type: ignore[attr-defined]

        # Matches C++ lines 1064-1077: SizeColumn case
        if self.sortColumn == 1:  # SizeColumn
            # Directories go first
            left = l.isDir()
            right = r.isDir()
            if left != right:  # XOR
                return left

            sizeDifference = l.size() - r.size()
            if sizeDifference == 0:
                return self.naturalCompare.compare(l.fileName, r.fileName) < 0  # type: ignore[attr-defined]

            return sizeDifference < 0

        # Matches C++ lines 1078-1085: TypeColumn case
        if self.sortColumn == 2:  # TypeColumn
            compare = self.naturalCompare.compare(l.type(), r.type())  # type: ignore[attr-defined]
            if compare == 0:
                return self.naturalCompare.compare(l.fileName, r.fileName) < 0  # type: ignore[attr-defined]

            return compare < 0

        # Matches C++ lines 1086-1094: TimeColumn case
        if self.sortColumn == 3:  # TimeColumn
            left_dt = l.lastModified(QTimeZone.UTC)  # type: ignore[attr-defined]
            right_dt = r.lastModified(QTimeZone.UTC)  # type: ignore[attr-defined]
            if left_dt == right_dt:
                return self.naturalCompare.compare(l.fileName, r.fileName) < 0  # type: ignore[attr-defined]

            return left_dt < right_dt

        # Matches C++ lines 1096-1097: Q_ASSERT(false); return false;
        assert False, f"Invalid sort column: {self.sortColumn}"
        return False

    def __call__(
        self,
        l: PyFileSystemNode,  # noqa: E741
        r: PyFileSystemNode,
    ) -> bool:
        """Call operator matching C++ lines 1100-1104 exactly.

        Matches:
        bool operator()(const QFileSystemModelPrivate::QFileSystemNode *l,
                      const QFileSystemModelPrivate::QFileSystemNode *r) const
        {
            return compareNodes(l, r);
        }
        """
        return self.compareNodes(l, r)
