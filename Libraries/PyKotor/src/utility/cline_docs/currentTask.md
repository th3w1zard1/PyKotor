# Current Task

## Current Objectives

- **Add advanced search with regex support**
  - Implement regex-based search functionality in the search bar.
  - Ensure the search is efficient and does not block the UI.
  - Provide user feedback for invalid regex patterns.

- **Implement file preview panel**
  - Develop a preview panel that supports images, text files, and PDFs.
  - Integrate the preview panel with the main file explorer view.
  - Ensure previews are generated asynchronously to maintain UI responsiveness.

- **Develop sorting and filtering capabilities**
  - Enable sorting of files by name, date modified, size, and type.
  - Implement advanced filtering options with customizable criteria.
  - Ensure sorting and filtering operations are efficient with large directories.

- **Enhance toolbar with additional action buttons**
  - Add buttons for common actions such as Create New Folder, Refresh, and View Mode Toggle.
  - Ensure buttons are intuitive and provide tooltips for better user experience.
  - Implement keyboard shortcuts for toolbar actions to support power users.

- **Integrate asynchronous operations using ProcessPoolExecutor**
  - Refactor resource-intensive tasks to use `ProcessPoolExecutor` for better performance.
  - Ensure that asynchronous operations do not block the main UI thread.
  - Handle task completion and error reporting effectively.

## Context

The project aims to develop a feature-rich file explorer application using PyQt, incorporating functionalities inspired by popular tools like Krusader, Total Commander, and Explorer++. The current focus is on enhancing search capabilities, preview functionalities, sorting/filtering mechanisms, toolbar enhancements, and optimizing performance through asynchronous operations.

## Next Steps

1. **Add Advanced Search with Regex Support**
   - Design the UI for regex input in the search bar.
   - Implement backend logic to handle regex-based filtering.
   - Validate user input and provide error messages for invalid patterns.

2. **Implement File Preview Panel**
   - Design the layout for the preview panel within the main window.
   - Integrate support for displaying images, text files, and PDFs.
   - Implement asynchronous loading of previews to ensure UI remains responsive.

3. **Develop Sorting and Filtering Capabilities**
   - Extend the current file model to support sorting by various attributes.
   - Implement a filtering interface allowing users to set custom criteria.
   - Optimize the sorting and filtering algorithms for performance.

4. **Enhance Toolbar with Additional Action Buttons**
   - Identify and design the additional action buttons needed.
   - Integrate the buttons into the existing toolbar layout.
   - Implement the functionality for each new toolbar button.

5. **Integrate Asynchronous Operations Using ProcessPoolExecutor**
   - Identify tasks that can benefit from asynchronous execution.
   - Refactor existing synchronous code to use `ProcessPoolExecutor`.
   - Implement proper task management and error handling for asynchronous operations.
