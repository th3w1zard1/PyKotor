# Qt Item View selection (Qt6) and PyKotor `RobustTableView`

## Key concepts (Qt)

- **Selection is managed by `QItemSelectionModel`** (not by the view itself). See `QItemSelectionModel` docs: `https://doc.qt.io/qt-6/qitemselectionmodel.html`.
- **“Current index” and “selected indexes” are different things**:
  - `QAbstractItemView::clearSelection()` **deselects items but does not change the current index** (so keyboard/shift-range “anchor” behavior can still reference the previous current index). See `QAbstractItemView` docs: `https://doc.qt.io/qt-6/qabstractitemview.html`.
  - `QItemSelectionModel` explicitly describes a “two layer” approach (committed selection + current interactive selection), and exposes APIs like `setCurrentIndex()`, `clearCurrentIndex()`, `clearSelection()`, and selection flag combinations like `ClearAndSelect`. See `https://doc.qt.io/qt-6/qitemselectionmodel.html`.

## Why subclassing must delegate to Qt

Qt’s built-in selection behavior for mouse interactions is implemented inside `QAbstractItemView` / `QTableView` (and interacts with `QItemSelectionModel` using selection flags such as `ClearAndSelect`).

If a subclass **skips** calling the base implementation for mouse/selection handling (for example, by overriding `mousePressEvent()` / `setSelection()` but not forwarding in the normal case), Qt cannot update the selection model’s current index/anchor correctly, leading to “sticky” anchors and ranges that keep extending from an old drag start.

One place to inspect how Qt drives selection from mouse events is the Qt source for `QAbstractItemView`: `https://codebrowser.dev/qt6/qtbase/src/widgets/itemviews/qabstractitemview.cpp.html`.

## PyKotor: `RobustTableView`

PyKotor provides `RobustTableView` (`Libraries/PyKotor/src/utility/ui_libraries/qt/widgets/itemviews/tableview.py`) which adds convenience behavior and also supports an optional mode that restricts selection to the first column.

To keep Qt’s selection model behavior correct, `RobustTableView` must:

- **Delegate to Qt** (`QTableView`/`QAbstractItemView`) for the normal “all columns selectable” behavior.
- Only apply the custom restriction logic in the “first column only” mode.


