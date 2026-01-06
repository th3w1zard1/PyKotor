# Qt6 C++ to Python Alignment Plan

This document tracks the 1:1 alignment of Python adapters with Qt6 C++ source code.

## Status

### Filesystem Adapters
- [ ] `pyfilesystemmodel.py` - Core model implementation
- [ ] `pyfilesystemnode.py` - Node structure
- [ ] `pyextendedinformation.py` - Extended file information
- [ ] `pyfileinfogatherer.py` - File info gathering thread
- [ ] `pyfilesystemwatcher.py` - File system watcher
- [ ] `pyfilesystemmodelsorter.py` - Sorting logic
- [ ] `pyfileitem.py` - File item representation
- [ ] `qfilesystemmodelnodekey.py` - Node key for Windows

### QFileDialog Adapters
- [ ] `qfiledialog/qfiledialog.py` - Main dialog class
- [ ] `qfiledialog/private/qfiledialog_p.py` - Private implementation
- [ ] `qfiledialog/private/qsidebar_p.py` - Sidebar implementation
- [ ] `qfiledialog/ui_qfiledialog.py` - UI definition

### QPlatformDialogHelper
- [ ] `adapters/kernel/qplatformdialoghelper/` - Platform dialog helpers
- [ ] `adapters/kernel/qplatformdialoghelper.py` - Main helper

### Tests
- [ ] `tests/test_qfilesystemmodel.py` - FileSystemModel tests
- [ ] `tests/test_qfiledialog.py` - FileDialog tests
- [ ] `tests/test_qfilesystemwatcher.py` - FileSystemWatcher tests

## Key Alignment Points

### 1. Method Signatures
All public methods must match C++ signatures exactly, including:
- Parameter types and order
- Return types
- Optional parameters with defaults

### 2. Internal Implementation
Private methods and data structures should match:
- `QFileSystemModelPrivate` structure
- `QFileSystemNode` implementation
- `QExtendedInformation` structure
- `QFileInfoGatherer` thread implementation

### 3. Signal/Slot Connections
All Qt signals and slots must match:
- Signal names and signatures
- Slot connections
- Event handling

### 4. Platform-Specific Code
Windows-specific code (UNC paths, drive handling) must be preserved:
- `QFileSystemModelNodePathKey` for Windows
- Volume name handling
- Long path name resolution

### 5. Test Coverage
All C++ tests must have Python equivalents:
- Same test cases
- Same assertions
- Same edge cases

## Reference Files

### C++ Source
- `relevant_qt_src/qfilesystemmodel.h`
- `relevant_qt_src/qfilesystemmodel.cpp`
- `relevant_qt_src/qfilesystemmodel_p.h`
- `relevant_qt_src/qfileinfogatherer_p.h`
- `relevant_qt_src/qfileinfogatherer.cpp`
- `relevant_qt_src/qfiledialog.h`
- `relevant_qt_src/qfiledialog.cpp`
- `relevant_qt_src/qplatformdialoghelper.h`
- `relevant_qt_src/qplatformdialoghelper.cpp`

### C++ Tests
- `relevant_qt_src/tests/tst_qfilesystemmodel.cpp`
- `relevant_qt_src/tests/tst_qfiledialog.cpp`
- `relevant_qt_src/tests/tst_qfilesystemwatcher.cpp`

## Progress Tracking

Work will be done systematically, file by file, ensuring each file is fully aligned before moving to the next.
