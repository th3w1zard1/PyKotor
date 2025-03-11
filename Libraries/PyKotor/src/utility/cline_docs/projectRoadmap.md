# Project Roadmap

## High-Level Goals

- Develop a comprehensive file explorer application using PyQt.
- Incorporate essential features from popular tools like Krusader, Total Commander, and Explorer++.
- Ensure the application is user-friendly and supports both basic and advanced user needs.
- Maintain high performance and responsiveness through asynchronous operations.

## Key Features

- **Dual-Pane Interface**
  - Resizable panes using `QSplitter`.
  - `QTreeView` for directory structure and `QTableView` for file listing.
- **File Operations**
  - Copy, move, rename, delete with context menus and toolbar buttons.
  - Batch operations with multi-select capabilities.
- **Search Functionality**
  - Basic and regex-based search using `QLineEdit` and `QSortFilterProxyModel`.
- **File Previews**
  - Preview panel supporting images, text files, and PDFs.
- **Sorting and Filtering**
  - Sort by name, date, size, and type.
  - Advanced filtering options with customizable criteria.
- **Toolbar and Menu**
  - Common action buttons and extensive keyboard shortcuts.
  - Menu bar with File, Edit, View, and Tools categories.
- **Status Bar**
  - Display directory path, selected items count, and disk space.
- **Asynchronous Operations**
  - Utilize `ProcessPoolExecutor` for resource-intensive tasks.
- **Drag and Drop**
  - Enable drag-and-drop between the application and external programs.
- **Context Menus**
  - Dynamic context menus based on file type and selection.
- **Error Handling and Logging**
  - Robust error management with user-friendly dialogs and logging.
- **Additional Features**
  - Tabbed browsing, bookmarks, hidden files toggle, file permissions management, and more as detailed in the task description.

## Completion Criteria

- All key features are implemented and tested across supported platforms.
- The user interface is intuitive and matches the functionality of established file explorers.
- Documentation is comprehensive and maintained throughout development.
- Performance is optimized to handle large directories and file operations efficiently.
- The application is stable with robust error handling and logging mechanisms.

## Progress Tracker

### Completed Tasks

- [x] Set up project structure and initial documentation.
- [x] Implemented basic UI layout with `QMainWindow` and `QSplitter`.
- [x] Integrated `QFileSystemModel` with `QTreeView` and `QTableView`.
- [x] Added basic file operations: copy, move, delete.
- [x] Implemented search functionality with `QLineEdit`.

### In Progress

- [ ] Add advanced search with regex support.
- [ ] Implement file preview panel.
- [ ] Develop sorting and filtering capabilities.
- [ ] Enhance toolbar with additional action buttons.
- [ ] Integrate asynchronous operations using `ProcessPoolExecutor`.

### Upcoming Tasks

- [ ] Implement drag and drop functionality.
- [ ] Create dynamic context menus.
- [ ] Develop status bar information display.
- [ ] Add error handling and logging systems.
- [ ] Finalize additional features as outlined in the project description.

### Future Enhancements

- [ ] Support for network drives and shared locations.
- [ ] Bookmarking system for quick access.
- [ ] Customizable interface and themes.
- [ ] Plugin system for third-party extensions.
- [ ] Comprehensive in-app help and documentation.
