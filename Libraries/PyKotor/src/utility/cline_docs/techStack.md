# Tech Stack

## Programming Language

- **Python 3.9+**
  - Chosen for its readability, extensive libraries, and rapid development capabilities.

## GUI Framework

- **PyQt5 / PyQt6**
  - Enables the creation of a feature-rich, cross-platform graphical user interface.
  - Provides widgets like `QMainWindow`, `QSplitter`, `QTreeView`, `QTableView`, and various dialogs.

## Asynchronous Operations

- **ProcessPoolExecutor (from `concurrent.futures`)**
  - Used for executing CPU-bound tasks asynchronously to maintain a responsive UI.
  - Suitable for resource-intensive operations such as file previews, large directory scans, and batch file operations.

## File System Operations

- **Standard Libraries (`os`, `shutil`, `pathlib`)**
  - Handle basic file operations like copy, move, rename, delete, and directory traversing.
  - `pathlib` provides an object-oriented approach to filesystem paths.

## Search Functionality

- **Regex (with Python’s `re` module)**
  - Implements advanced search capabilities, allowing users to perform regex-based searches for enhanced filtering.

## File Previews

- **PyMuPDF (`fitz` library)**
  - Enables rendering of PDF previews within the application.
- **QPixmap and QImage**
  - Handle image rendering for supported file types (images, text previews).

## Model/View Architecture

- **`QFileSystemModel`**
  - Serves as the data model for file and directory listings.
- **`QSortFilterProxyModel`**
  - Facilitates sorting and filtering of the file system model based on user criteria.

## Icons and Thumbnails

- **IconLoader**
  - Custom utility for loading and caching file icons and thumbnails to optimize performance.

## Error Handling and Logging

- **Custom Error Handling (`error_handling.py`)**
  - Ensures robust error management with user-friendly dialogs.
- **`loggerplus` Library**
  - Provides advanced logging capabilities for tracking operations, errors, and warnings.

## User Notifications

- **`QStatusBar` and `QSystemTrayIcon`**
  - Display real-time updates and notifications to the user without blocking the main UI.

## File Comparison

- **Custom Comparison Algorithms**
  - Implemented using Python to compare file contents and display differences.

## Plugin and Extension Support

- **Custom Plugin Architecture**
  - Allows third-party developers to extend application functionality through a defined API.

## Task Scheduling and Management

- **Custom Scheduler (`scheduler.py`)**
  - Manages automated tasks like backups, synchronization, and other periodic file operations.

## Internationalization and Localization

- **PyQt’s Translation System (`QTranslator`)**
  - Supports multiple languages and regional settings for a global user base.

## Version Control and Undo/Redo

- **Action Stacks**
  - Implements undo and redo functionalities by maintaining action history.

## Security Features

- **Encrypted File Storage**
  - Utilizes Python’s encryption libraries to secure sensitive files.
- **Secure File Shredding**
  - Permanently deletes files by overwriting data multiple times.

## Cross-Platform Compatibility

- **Platform-Specific Modules (`win32` for Windows, etc.)**
  - Ensures consistent behavior across different operating systems by handling platform-specific features appropriately.

## Testing and Validation

- **Unit Tests (`src/utility/tests/`)**
  - Comprehensive testing to ensure all components function as intended.
- **Mock Executors for Testing**
  - Simulate file operations and task executions during testing.

## Documentation

- **Markdown Files in `cline_docs/`**
  - Maintain comprehensive project documentation including roadmap, current tasks, technology stack, and codebase summary.

## Development Tools

- **VSCode**
  - Primary development environment with relevant extensions.
- **Git**
  - Version control system for source code management.
