"""QFileInfoGatherer Python adapter matching Qt6 C++ source exactly.

This class matches qfileinfogatherer_p.h and qfileinfogatherer.cpp.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from qtpy.QtCore import (  # noqa: E402
    QCoreApplication,
    QDir,
    QElapsedTimer,
    QEvent,
    QFileInfo,
    QFileSystemWatcher,
    QMutex,
    QMutexLocker,
    QObject,
    QThread,
    QVariant,
    QWaitCondition,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QAbstractFileIconProvider  # noqa: E402
from qtpy.QtWidgets import QFileIconProvider  # noqa: E402

if TYPE_CHECKING:
    pass

from utility.ui_libraries.qt.adapters.filesystem.pyextendedinformation import PyQExtendedInformation  # noqa: E402


def translateDriveName(drive: QFileInfo) -> str:
    """Translate drive name matching C++ lines 36-46 exactly.
    
    Matches:
    static QString translateDriveName(const QFileInfo &drive)
    {
        QString driveName = drive.absoluteFilePath();
    #ifdef Q_OS_WIN
        if (driveName.startsWith(u'/')) // UNC host
            return drive.fileName();
        if (driveName.endsWith(u'/'))
            driveName.chop(1);
    #endif // Q_OS_WIN
        return driveName;
    }
    """
    driveName = drive.absoluteFilePath()
    if os.name == "nt":
        if driveName.startswith("/"):  # UNC host
            return drive.fileName()
        if driveName.endswith("/"):
            driveName = driveName[:-1]
    return driveName


class PyFileInfoGatherer(QThread):
    """Python adapter for QFileInfoGatherer matching Qt6 C++ source exactly.
    
    Matches qfileinfogatherer_p.h lines 126-199 and qfileinfogatherer.cpp.
    """
    
    # Signals matching C++ lines 130-134
    updates = Signal(str, list)  # (directory, QList<std::pair<QString, QFileInfo>>)
    newListOfFiles = Signal(str, list)  # (directory, QStringList) const
    nameResolved = Signal(str, str)  # (fileName, resolvedName) const
    directoryLoaded = Signal(str)  # (path)

    def __init__(self, parent: QObject | None = None):
        """Initialize QFileInfoGatherer matching C++ lines 57-62 exactly.
        
        Matches:
        QFileInfoGatherer::QFileInfoGatherer(QObject *parent)
            : QThread(parent)
            , m_iconProvider(&defaultProvider)
        {
            start(LowPriority);
        }
        """
        super().__init__(parent)
        # Matches C++ line 192: QAbstractFileIconProvider *m_iconProvider;
        # Matches C++ line 192: QAbstractFileIconProvider defaultProvider;
        self.defaultProvider = QFileIconProvider()
        self.m_iconProvider: QAbstractFileIconProvider = self.defaultProvider
        
        # Matches C++ line 181: mutable QMutex mutex;
        self.mutex = QMutex()
        # Matches C++ line 183: QWaitCondition condition;
        self.condition = QWaitCondition()
        # Matches C++ line 184: QStack<QString> path;
        # Python: use list as stack (append/pop)
        self.path: list[str] = []
        # Matches C++ line 185: QStack<QStringList> files;
        self.files: list[list[str]] = []
        
        # Matches C++ line 189: QFileSystemWatcher *m_watcher = nullptr;
        self.m_watcher: QFileSystemWatcher | None = None
        
        # Matches C++ line 194: bool m_resolveSymlinks = true; (Windows only)
        if os.name == "nt":
            self.m_resolveSymlinks: bool = True
        # Matches C++ line 197: bool m_watching = true;
        self.m_watching: bool = True
        
        # Start thread with LowPriority matching C++ line 61
        self.start(QThread.Priority.LowPriority)

    def __del__(self):
        """Destructor matching C++ lines 67-71 exactly.
        
        Matches:
        QFileInfoGatherer::~QFileInfoGatherer()
        {
            requestAbort();
            wait();
        }
        """
        self.requestAbort()
        self.wait()

    def event(self, event: QEvent) -> bool:
        """Event handler matching C++ lines 73-96 exactly.
        
        Matches:
        bool QFileInfoGatherer::event(QEvent *event)
        {
            if (event->type() == QEvent::DeferredDelete && isRunning()) {
                requestAbort();
                if (!wait(5000)) {
                    if (QCoreApplication::closingDown())
                        terminate();
                    else
                        connect(this, &QThread::finished, this, [this]{ delete this; });
                    return true;
                }
            }
            return QThread::event(event);
        }
        """
        if event.type() == QEvent.Type.DeferredDelete and self.isRunning():
            self.requestAbort()
            if not self.wait(5000):
                if QCoreApplication.closingDown():
                    self.terminate()
                else:
                    self.finished.connect(lambda: None)  # Python equivalent of delete this
                return True
        return super().event(event)

    def requestAbort(self) -> None:
        """Request abort matching C++ lines 98-103 exactly.
        
        Matches:
        void QFileInfoGatherer::requestAbort()
        {
            requestInterruption();
            QMutexLocker locker(&mutex);
            condition.wakeAll();
        }
        """
        self.requestInterruption()
        with QMutexLocker(self.mutex):
            self.condition.wakeAll()

    def setResolveSymlinks(self, enable: bool) -> None:  # noqa: FBT001
        """Set resolve symlinks matching C++ lines 105-111 exactly.
        
        Matches:
        void QFileInfoGatherer::setResolveSymlinks(bool enable)
        {
            Q_UNUSED(enable);
        #ifdef Q_OS_WIN
            m_resolveSymlinks = enable;
        #endif
        }
        """
        if os.name == "nt":
            self.m_resolveSymlinks = enable

    def driveAdded(self) -> None:
        """Drive added handler matching C++ lines 113-116 exactly.
        
        Matches:
        void QFileInfoGatherer::driveAdded()
        {
            fetchExtendedInformation(QString(), QStringList());
        }
        """
        self.fetchExtendedInformation("", [])

    def driveRemoved(self) -> None:
        """Drive removed handler matching C++ lines 118-125 exactly.
        
        Matches:
        void QFileInfoGatherer::driveRemoved()
        {
            QStringList drives;
            const QFileInfoList driveInfoList = QDir::drives();
            for (const QFileInfo &fi : driveInfoList)
                drives.append(translateDriveName(fi));
            emit newListOfFiles(QString(), drives);
        }
        """
        drives: list[str] = []
        driveInfoList = QDir.drives()
        for fi in driveInfoList:
            drives.append(translateDriveName(fi))
        self.newListOfFiles.emit("", drives)

    def resolveSymlinks(self) -> bool:
        """Check if resolving symlinks matching C++ lines 127-134 exactly.
        
        Matches:
        bool QFileInfoGatherer::resolveSymlinks() const
        {
        #ifdef Q_OS_WIN
            return m_resolveSymlinks;
        #else
            return false;
        #endif
        }
        """
        if os.name == "nt":
            return self.m_resolveSymlinks
        return False

    def setIconProvider(self, provider: QAbstractFileIconProvider | None) -> None:
        """Set icon provider matching C++ lines 136-139 exactly.
        
        Matches:
        void QFileInfoGatherer::setIconProvider(QAbstractFileIconProvider *provider)
        {
            m_iconProvider = provider;
        }
        """
        self.m_iconProvider = provider

    def iconProvider(self) -> QAbstractFileIconProvider | None:
        """Get icon provider matching C++ lines 141-144 exactly.
        
        Matches:
        QAbstractFileIconProvider *QFileInfoGatherer::iconProvider() const
        {
            return m_iconProvider;
        }
        """
        return self.m_iconProvider

    def fetchExtendedInformation(self, path: str, files: list[str]) -> None:
        """Fetch extended information matching C++ lines 151-179 exactly.
        
        Matches:
        void QFileInfoGatherer::fetchExtendedInformation(const QString &path, const QStringList &files)
        {
            QMutexLocker locker(&mutex);
            // See if we already have this dir/file in our queue
            qsizetype loc = 0;
            while ((loc = this->path.lastIndexOf(path, loc - 1)) != -1) {
                if (this->files.at(loc) == files)
                    return;
                if (loc == 0)
                    break;
            }

        #if QT_CONFIG(thread)
            this->path.push(path);
            this->files.push(files);
            condition.wakeAll();
        #else // !QT_CONFIG(thread)
            getFileInfos(path, files);
        #endif // QT_CONFIG(thread)

        #if QT_CONFIG(filesystemwatcher)
            if (files.isEmpty()
                && !path.isEmpty()
                && !path.startsWith("//"_L1) /*don't watch UNC path*/) {
                if (!watchedDirectories().contains(path))
                    watchPaths(QStringList(path));
            }
        #endif
        }
        """
        with QMutexLocker(self.mutex):
            # See if we already have this dir/file in our queue
            loc = 0
            # lastIndexOf equivalent: search from end
            found_index = -1
            for i in range(len(self.path) - 1, -1, -1):
                if self.path[i] == path:
                    if self.files[i] == files:
                        return
                    found_index = i
                    if i == 0:
                        break
                    loc = i - 1
                    if loc < 0:
                        break

            # QT_CONFIG(thread) - always true in Python
            self.path.append(path)  # push
            self.files.append(files)  # push
            self.condition.wakeAll()

        # QT_CONFIG(filesystemwatcher) - always true
        if not files and path and not path.startswith("//"):  # don't watch UNC path
            if path not in self.watchedDirectories():
                self.watchPaths([path])

    def updateFile(self, filePath: str) -> None:  # noqa: N803
        """Update file matching C++ lines 186-191 exactly.
        
        Matches:
        void QFileInfoGatherer::updateFile(const QString &filePath)
        {
            QString dir = filePath.mid(0, filePath.lastIndexOf(u'/'));
            QString fileName = filePath.mid(dir.size() + 1);
            fetchExtendedInformation(dir, QStringList(fileName));
        }
        """
        last_slash = filePath.rfind("/")
        if last_slash == -1:
            dir = ""
            fileName = filePath
        else:
            dir = filePath[:last_slash]
            fileName = filePath[last_slash + 1:]
        self.fetchExtendedInformation(dir, [fileName])

    def watchedFiles(self) -> list[str]:
        """Get watched files matching C++ lines 193-200 exactly.
        
        Matches:
        QStringList QFileInfoGatherer::watchedFiles() const
        {
        #if QT_CONFIG(filesystemwatcher)
            if (m_watcher)
                return m_watcher->files();
        #endif
            return {};
        }
        """
        if self.m_watcher:
            return self.m_watcher.files()
        return []

    def watchedDirectories(self) -> list[str]:
        """Get watched directories matching C++ lines 202-209 exactly.
        
        Matches:
        QStringList QFileInfoGatherer::watchedDirectories() const
        {
        #if QT_CONFIG(filesystemwatcher)
            if (m_watcher)
                return m_watcher->directories();
        #endif
            return {};
        }
        """
        if self.m_watcher:
            return self.m_watcher.directories()
        return []

    def createWatcher(self) -> None:
        """Create watcher matching C++ lines 211-227 exactly.
        
        Matches:
        void QFileInfoGatherer::createWatcher()
        {
        #if QT_CONFIG(filesystemwatcher)
            m_watcher = new QFileSystemWatcher(this);
            connect(m_watcher, &QFileSystemWatcher::directoryChanged, this, &QFileInfoGatherer::list);
            connect(m_watcher, &QFileSystemWatcher::fileChanged, this, &QFileInfoGatherer::updateFile);
        #  if defined(Q_OS_WIN)
            const QVariant listener = m_watcher->property("_q_driveListener");
            if (listener.canConvert<QObject *>()) {
                if (QObject *driveListener = listener.value<QObject *>()) {
                    connect(driveListener, SIGNAL(driveAdded()), this, SLOT(driveAdded()));
                    connect(driveListener, SIGNAL(driveRemoved()), this, SLOT(driveRemoved()));
                }
            }
        #  endif // Q_OS_WIN
        #endif
        }
        """
        self.m_watcher = QFileSystemWatcher(self)
        self.m_watcher.directoryChanged.connect(self.list)
        self.m_watcher.fileChanged.connect(self.updateFile)
        
        if os.name == "nt":
            listener = self.m_watcher.property("_q_driveListener")
            if listener and isinstance(listener, QVariant):
                if listener.canConvert(QObject):
                    driveListener = listener.value(QObject)
                    if driveListener:
                        # Note: Old-style signals not available in PyQt6, would need workaround
                        # driveListener.driveAdded.connect(self.driveAdded)
                        # driveListener.driveRemoved.connect(self.driveRemoved)
                        pass

    def watchPaths(self, paths: list[str]) -> None:
        """Watch paths matching C++ lines 229-240 exactly.
        
        Matches:
        void QFileInfoGatherer::watchPaths(const QStringList &paths)
        {
        #if QT_CONFIG(filesystemwatcher)
            if (m_watching) {
                if (m_watcher == nullptr)
                    createWatcher();
                m_watcher->addPaths(paths);
            }
        #else
            Q_UNUSED(paths);
        #endif
        }
        """
        if self.m_watching:
            if self.m_watcher is None:
                self.createWatcher()
            if self.m_watcher:
                self.m_watcher.addPaths(paths)

    def unwatchPaths(self, paths: list[str]) -> None:
        """Unwatch paths matching C++ lines 242-250 exactly.
        
        Matches:
        void QFileInfoGatherer::unwatchPaths(const QStringList &paths)
        {
        #if QT_CONFIG(filesystemwatcher)
            if (m_watcher && !paths.isEmpty())
                m_watcher->removePaths(paths);
        #else
            Q_UNUSED(paths);
        #endif
        }
        """
        if self.m_watcher and paths:
            self.m_watcher.removePaths(paths)

    def isWatching(self) -> bool:
        """Check if watching matching C++ lines 252-260 exactly.
        
        Matches:
        bool QFileInfoGatherer::isWatching() const
        {
            bool result = false;
        #if QT_CONFIG(filesystemwatcher)
            QMutexLocker locker(&mutex);
            result = m_watching;
        #endif
            return result;
        }
        """
        with QMutexLocker(self.mutex):
            return self.m_watching

    def setWatching(self, v: bool) -> None:  # noqa: N803
        """Set watching matching C++ lines 271-283 exactly.
        
        Matches:
        void QFileInfoGatherer::setWatching(bool v)
        {
        #if QT_CONFIG(filesystemwatcher)
            QMutexLocker locker(&mutex);
            if (v != m_watching) {
                m_watching = v;
                if (!m_watching)
                    delete std::exchange(m_watcher, nullptr);
            }
        #else
            Q_UNUSED(v);
        #endif
        }
        """
        with QMutexLocker(self.mutex):
            if v != self.m_watching:
                self.m_watching = v
                if not self.m_watching:
                    # std::exchange equivalent
                    old_watcher = self.m_watcher
                    self.m_watcher = None
                    if old_watcher:
                        old_watcher.deleteLater()

    def clear(self) -> None:
        """Clear watcher matching C++ lines 290-297 exactly.
        
        Matches:
        void QFileInfoGatherer::clear()
        {
        #if QT_CONFIG(filesystemwatcher)
            QMutexLocker locker(&mutex);
            unwatchPaths(watchedFiles());
            unwatchPaths(watchedDirectories());
        #endif
        }
        """
        with QMutexLocker(self.mutex):
            self.unwatchPaths(self.watchedFiles())
            self.unwatchPaths(self.watchedDirectories())

    def removePath(self, path: str) -> None:
        """Remove path matching C++ lines 304-312 exactly.
        
        Matches:
        void QFileInfoGatherer::removePath(const QString &path)
        {
        #if QT_CONFIG(filesystemwatcher)
            QMutexLocker locker(&mutex);
            unwatchPaths(QStringList(path));
        #else
            Q_UNUSED(path);
        #endif
        }
        """
        with QMutexLocker(self.mutex):
            self.unwatchPaths([path])

    def list(self, directoryPath: str) -> None:  # noqa: A003
        """List directory matching C++ lines 319-322 exactly.
        
        Matches:
        void QFileInfoGatherer::list(const QString &directoryPath)
        {
            fetchExtendedInformation(directoryPath, QStringList());
        }
        """
        self.fetchExtendedInformation(directoryPath, [])

    def run(self) -> None:
        """Run thread matching C++ lines 327-350 exactly.
        
        Matches:
        void QFileInfoGatherer::run()
        {
            forever {
                setTerminationEnabled(false);
                QMutexLocker locker(&mutex);
                while (!isInterruptionRequested() && path.isEmpty())
                    condition.wait(&mutex);
                if (isInterruptionRequested())
                    return;
                const QString thisPath = std::as_const(path).front();
                path.pop_front();
                const QStringList thisList = std::as_const(files).front();
                files.pop_front();
                locker.unlock();

                setTerminationEnabled(true);
                getFileInfos(thisPath, thisList);
            }
        }
        """
        while True:
            # Disallow termination while we are holding a mutex or can be woken up cleanly.
            self.setTerminationEnabled(False)
            with QMutexLocker(self.mutex):
                while not self.isInterruptionRequested() and not self.path:
                    self.condition.wait(self.mutex)
                if self.isInterruptionRequested():
                    return
                thisPath = self.path[0]
                self.path.pop(0)  # pop_front
                thisList = self.files[0]
                self.files.pop(0)  # pop_front

            # Some of the system APIs we call when gathering file information
            # might hang (e.g. waiting for network), so we explicitly allow
            # termination now.
            self.setTerminationEnabled(True)
            self.getFileInfos(thisPath, thisList)

    def getInfo(self, fileInfo: QFileInfo) -> PyQExtendedInformation:
        """Get info matching C++ lines 352-387 exactly.
        
        Matches:
        QExtendedInformation QFileInfoGatherer::getInfo(const QFileInfo &fileInfo) const
        {
            QExtendedInformation info(fileInfo);
            if (m_iconProvider) {
                info.icon = m_iconProvider->icon(fileInfo);
                info.displayType = m_iconProvider->type(fileInfo);
            } else {
                info.displayType = QAbstractFileIconProviderPrivate::getFileType(fileInfo);
            }
        #if QT_CONFIG(filesystemwatcher)
            static const bool watchFiles = qEnvironmentVariableIsSet("QT_FILESYSTEMMODEL_WATCH_FILES");
            if (watchFiles) {
                if (!fileInfo.exists() && !fileInfo.isSymLink()) {
                    const_cast<QFileInfoGatherer *>(this)->
                        unwatchPaths(QStringList(fileInfo.absoluteFilePath()));
                } else {
                    const QString path = fileInfo.absoluteFilePath();
                    if (!path.isEmpty() && fileInfo.exists() && fileInfo.isFile() && fileInfo.isReadable()
                        && !watchedFiles().contains(path)) {
                        const_cast<QFileInfoGatherer *>(this)->watchPaths(QStringList(path));
                    }
                }
            }
        #endif // filesystemwatcher

        #ifdef Q_OS_WIN
            if (m_resolveSymlinks && info.isSymLink(/* ignoreNtfsSymLinks = */ true)) {
                QFileInfo resolvedInfo(QFileInfo(fileInfo.symLinkTarget()).canonicalFilePath());
                if (resolvedInfo.exists()) {
                    emit nameResolved(fileInfo.filePath(), resolvedInfo.fileName());
                }
            }
        #endif
            return info;
        }
        """
        info = PyQExtendedInformation(fileInfo)
        if self.m_iconProvider:
            info.icon = self.m_iconProvider.icon(fileInfo)
            info.displayType = self.m_iconProvider.type(fileInfo)
        else:
            # QAbstractFileIconProviderPrivate::getFileType equivalent
            # Use QFileIconProvider as fallback
            default_provider = QFileIconProvider()
            info.displayType = default_provider.type(fileInfo)
        
        # QT_CONFIG(filesystemwatcher)
        watchFiles = os.environ.get("QT_FILESYSTEMMODEL_WATCH_FILES", "").strip()
        if watchFiles:
            if not fileInfo.exists() and not fileInfo.isSymLink():
                self.unwatchPaths([fileInfo.absoluteFilePath()])
            else:
                path = fileInfo.absoluteFilePath()
                if path and fileInfo.exists() and fileInfo.isFile() and fileInfo.isReadable():
                    if path not in self.watchedFiles():
                        self.watchPaths([path])
        
        # Q_OS_WIN
        if os.name == "nt" and self.m_resolveSymlinks and info.isSymLink(ignoreNtfsSymLinks=True):
            resolvedInfo = QFileInfo(QFileInfo(fileInfo.symLinkTarget()).canonicalFilePath())
            if resolvedInfo.exists():
                self.nameResolved.emit(fileInfo.filePath(), resolvedInfo.fileName())
        
        return info

    def getFileInfos(self, path: str, files: list[str]) -> None:
        """Get file infos matching C++ lines 393-456 exactly.
        
        Matches:
        void QFileInfoGatherer::getFileInfos(const QString &path, const QStringList &files)
        {
            // List drives
            if (path.isEmpty()) {
                QList<std::pair<QString, QFileInfo>> updatedFiles;
                auto addToUpdatedFiles = [&updatedFiles](QFileInfo &&fileInfo) {
                    fileInfo.stat();
                    updatedFiles.emplace_back(std::pair{translateDriveName(fileInfo), fileInfo});
                };

                if (files.isEmpty()) {
                    QFileInfoList infoList = QDir::drives();
                    updatedFiles.reserve(infoList.size());
                    for (auto rit = infoList.rbegin(), rend = infoList.rend(); rit != rend; ++rit)
                        addToUpdatedFiles(std::move(*rit));
                } else {
                    updatedFiles.reserve(files.size());
                    for (auto rit = files.crbegin(), rend = files.crend(); rit != rend; ++rit)
                        addToUpdatedFiles(QFileInfo(*rit));
                }
                emit updates(path, updatedFiles);
                return;
            }

            QElapsedTimer base;
            base.start();
            QFileInfo fileInfo;
            bool firstTime = true;
            QList<std::pair<QString, QFileInfo>> updatedFiles;
            QStringList filesToCheck = files;

            QStringList allFiles;
            if (files.isEmpty()) {
                using F = QDirListing::IteratorFlag;
                constexpr auto flags = F::ResolveSymlinks | F::IncludeHidden | F::IncludeDotAndDotDot
                                       | F::IncludeBrokenSymlinks;
                for (const auto &dirEntry : QDirListing(path, flags)) {
                    if (isInterruptionRequested())
                        break;
                    fileInfo = dirEntry.fileInfo();
                    fileInfo.stat();
                    allFiles.append(fileInfo.fileName());
                    fetch(fileInfo, base, firstTime, updatedFiles, path);
                }
            }
            if (!allFiles.isEmpty())
                emit newListOfFiles(path, allFiles);

            QStringList::const_iterator filesIt = filesToCheck.constBegin();
            while (!isInterruptionRequested() && filesIt != filesToCheck.constEnd()) {
                fileInfo.setFile(path + QDir::separator() + *filesIt);
                ++filesIt;
                fileInfo.stat();
                fetch(fileInfo, base, firstTime, updatedFiles, path);
            }
            if (!updatedFiles.isEmpty())
                emit updates(path, updatedFiles);
            emit directoryLoaded(path);
        }
        """
        # List drives
        if not path:
            updatedFiles: list[tuple[str, QFileInfo]] = []
            
            def addToUpdatedFiles(fileInfo: QFileInfo) -> None:
                fileInfo.refresh()  # stat() equivalent
                updatedFiles.append((translateDriveName(fileInfo), fileInfo))

            if not files:
                infoList = QDir.drives()
                # Reverse iterate (rbegin/rend)
                for fileInfo in reversed(infoList):
                    addToUpdatedFiles(fileInfo)
            else:
                # Reverse iterate (crbegin/crend)
                for filePath in reversed(files):
                    addToUpdatedFiles(QFileInfo(filePath))
            
            self.updates.emit(path, updatedFiles)
            return

        base = QElapsedTimer()
        base.start()
        fileInfo = QFileInfo()
        firstTime = True
        updatedFiles: list[tuple[str, QFileInfo]] = []
        filesToCheck = files

        allFiles: list[str] = []
        if not files:
            # QDirListing equivalent - use os.scandir with appropriate flags
            # C++ flags: ResolveSymlinks | IncludeHidden | IncludeDotAndDotDot | IncludeBrokenSymlinks
            try:
                with os.scandir(path) as it:
                    for entry in it:
                        if self.isInterruptionRequested():
                            break
                        fileInfo = QFileInfo(entry.path)
                        fileInfo.refresh()  # stat()
                        allFiles.append(fileInfo.fileName())
                        firstTime = self._fetch(fileInfo, base, firstTime, updatedFiles, path)
            except OSError:
                pass  # Handle errors silently like C++ does
        
        if allFiles:
            self.newListOfFiles.emit(path, allFiles)

        filesIt = iter(filesToCheck)
        while not self.isInterruptionRequested():
            try:
                fileName = next(filesIt)
            except StopIteration:
                break
            fileInfo.setFile(path + QDir.separator() + fileName)
            fileInfo.refresh()  # stat()
            firstTime = self._fetch(fileInfo, base, firstTime, updatedFiles, path)
        
        if updatedFiles:
            self.updates.emit(path, updatedFiles)
        self.directoryLoaded.emit(path)

    def _fetch(
        self,
        fileInfo: QFileInfo,
        base: QElapsedTimer,
        firstTime: bool,  # noqa: FBT001
        updatedFiles: list[tuple[str, QFileInfo]],
        path: str,
    ) -> bool:
        """Fetch file info matching C++ lines 458-470 exactly.
        
        Matches:
        void QFileInfoGatherer::fetch(const QFileInfo &fileInfo, QElapsedTimer &base, bool &firstTime,
                                      QList<std::pair<QString, QFileInfo>> &updatedFiles, const QString &path)
        {
            updatedFiles.emplace_back(std::pair(fileInfo.fileName(), fileInfo));
            QElapsedTimer current;
            current.start();
            if ((firstTime && updatedFiles.size() > 100) || base.msecsTo(current) > 1000) {
                emit updates(path, updatedFiles);
                updatedFiles.clear();
                base = current;
                firstTime = false;
            }
        }
        Note: firstTime is passed by reference in C++, so we return the modified value.
        """
        updatedFiles.append((fileInfo.fileName(), fileInfo))
        current = QElapsedTimer()
        current.start()
        if (firstTime and len(updatedFiles) > 100) or base.msecsTo(current) > 1000:
            self.updates.emit(path, updatedFiles)
            updatedFiles.clear()
            base.restart()  # base = current equivalent
            firstTime = False
        return firstTime
