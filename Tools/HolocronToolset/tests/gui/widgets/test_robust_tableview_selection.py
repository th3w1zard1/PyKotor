from __future__ import annotations

import pytest

from typing import TYPE_CHECKING

import qtpy

from qtpy.QtCore import QEvent, Qt, QPoint, QPointF
from qtpy.QtGui import QMouseEvent, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QApplication
from qtpy.QtTest import QTest

from utility.ui_libraries.qt.widgets.itemviews.tableview import RobustTableView

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot
    from qtpy.QtCore import QPoint
    from qtpy.QtWidgets import QWidget


def _model(rows: int = 10, cols: int = 10) -> QStandardItemModel:
    model = QStandardItemModel(rows, cols)
    for r in range(rows):
        for c in range(cols):
            model.setItem(r, c, QStandardItem(f"{r},{c}"))
    return model


def _center_pos(view: RobustTableView, row: int, col: int):
    idx = view.model().index(row, col)  # type: ignore[union-attr]
    rect = view.visualRect(idx)
    assert rect.isValid()
    return rect.center()


def _drag_select(qtbot: QtBot, view_or_viewport: RobustTableView | QWidget, start_pos: QPoint, end_pos: QPoint):
    """Perform a *real* drag selection (mouse moves with LeftButton held).

    `qtbot.mouseMove()` does not include the mouse button state, so it doesn't
    trigger Qt's drag/rubber-band selection. We therefore synthesize MouseMove
    events that include `buttons=LeftButton` while the button is pressed.
    """
    # Handle both view and viewport being passed
    if isinstance(view_or_viewport, RobustTableView):
        view: RobustTableView = view_or_viewport
        viewport = view.viewport()
        assert viewport is not None
        # Resolve indexes *before* any scrolling, then recompute the local coords *after* scrolling.
        # Otherwise, the incoming QPoint can become stale when the view scrolls horizontally.
        start_idx = view.indexAt(start_pos)
        end_idx = view.indexAt(end_pos)

        if start_idx.isValid():
            view.scrollTo(start_idx, view.ScrollHint.EnsureVisible)
        if end_idx.isValid():
            view.scrollTo(end_idx, view.ScrollHint.EnsureVisible)
        qtbot.wait(20)
        QApplication.processEvents()

        if start_idx.isValid():
            start_pos = view.visualRect(start_idx).center()
        if end_idx.isValid():
            end_pos = view.visualRect(end_idx).center()
    else:
        viewport = view_or_viewport
    assert viewport is not None

    qtbot.mousePress(viewport, Qt.MouseButton.LeftButton, pos=start_pos)
    qtbot.wait(5)
    QApplication.processEvents()

    steps = 12
    dx = (end_pos.x() - start_pos.x()) / steps
    dy = (end_pos.y() - start_pos.y()) / steps
    for i in range(1, steps + 1):
        p = QPoint(int(round(start_pos.x() + dx * i)), int(round(start_pos.y() + dy * i)))
        global_p = viewport.mapToGlobal(p)

        if qtpy.QT5:
            move_ev = QMouseEvent(
                QEvent.Type.MouseMove,
                p,  # type: ignore[arg-type]  # qtpy stubs may prefer QPointF in some environments
                Qt.MouseButton.NoButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
        else:
            move_ev = QMouseEvent(
                QEvent.Type.MouseMove,
                QPointF(p),
                QPointF(global_p),
                Qt.MouseButton.NoButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )

        QApplication.sendEvent(viewport, move_ev)
        qtbot.wait(1)

    QApplication.processEvents()
    qtbot.mouseRelease(viewport, Qt.MouseButton.LeftButton, pos=end_pos)
    qtbot.wait(20)
    QApplication.processEvents()


def test_click_resets_selection_anchor_when_all_columns_selectable(qtbot: QtBot):
    """
    Regression test:
    When RobustTableView is in the normal (all columns selectable) mode, a plain click
    must clear any previous drag selection and establish a new anchor/current index.
    """
    view = RobustTableView()
    qtbot.addWidget(view)

    model = _model()
    view.setModel(model)
    view.setSelectionMode(view.SelectionMode.ContiguousSelection)
    view.setSelectionBehavior(view.SelectionBehavior.SelectItems)

    # "First Column Interactable" == False => do NOT restrict selection to the first column.
    view.setFirstColumnInteractable(False)

    view.resize(600, 400)
    view.show()
    qtbot.waitExposed(view)

    # Drag-select a block (rows 5-8, cols 1-3)
    start = _center_pos(view, 5, 1)
    end = _center_pos(view, 8, 3)
    _drag_select(qtbot, view, start, end)
    assert view.selectedIndexes(), "precondition: drag must select at least one cell"

    # Plain click elsewhere should reset selection to the clicked cell only.
    click_pos = _center_pos(view, 1, 1)
    qtbot.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=click_pos)

    selected = view.selectedIndexes()
    assert len(selected) == 1
    assert selected[0].row() == 1
    assert selected[0].column() == 1


def test_first_column_only_mode_restricts_selection(qtbot: QtBot):
    """
    Ensure that when "first column only" mode is enabled, clicking/dragging
    from non-first columns clears selection (the intended restriction behavior).
    """
    view = RobustTableView()
    qtbot.addWidget(view)

    model = _model()
    view.setModel(model)
    view.setSelectionMode(view.SelectionMode.ContiguousSelection)
    view.setSelectionBehavior(view.SelectionBehavior.SelectItems)

    # Enable "First Column Only" mode (default is True)
    view.setFirstColumnInteractable(True)

    view.resize(600, 400)
    view.show()
    qtbot.waitExposed(view)

    # Click on first column should select it
    click_pos_col0 = _center_pos(view, 3, 0)
    qtbot.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=click_pos_col0)
    selected = view.selectedIndexes()
    assert len(selected) > 0, "First column click should select something"
    # All selected items should be in column 0
    assert all(idx.column() == 0 for idx in selected), "Selection should only be in column 0"

    # Click on a non-first column should clear selection (restriction mode)
    click_pos_other = _center_pos(view, 5, 2)
    qtbot.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=click_pos_other)
    selected_after = view.selectedIndexes()
    assert len(selected_after) == 0, "Clicking non-first column should clear selection in restriction mode"

    # Drag starting from first column should work
    start_col0 = _center_pos(view, 1, 0)
    end_col0 = _center_pos(view, 3, 0)
    _drag_select(qtbot, view, start_col0, end_col0)
    selected_drag = view.selectedIndexes()
    assert len(selected_drag) > 0, "Drag from first column should select"
    assert all(idx.column() == 0 for idx in selected_drag), "Drag selection should only be in column 0"

    # Drag starting from non-first column should clear selection
    start_other = _center_pos(view, 5, 2)
    end_other = _center_pos(view, 7, 2)
    _drag_select(qtbot, view, start_other, end_other)
    selected_drag_other = view.selectedIndexes()
    assert len(selected_drag_other) == 0, "Drag from non-first column should clear selection in restriction mode"


def _get_selected_cells(selected_indexes):
    """Helper to get a sorted list of (row, col) tuples from selected indexes."""
    return sorted([(idx.row(), idx.column()) for idx in selected_indexes])


def test_select_deselect_reselect_exact_cells(qtbot: QtBot):
    """
    Test selecting specific cells, deselecting, then selecting again.
    Verifies exact cell coordinates at each step.
    """
    view = RobustTableView()
    qtbot.addWidget(view)

    model = _model(rows=15, cols=15)
    view.setModel(model)
    view.setSelectionMode(view.SelectionMode.ExtendedSelection)
    view.setSelectionBehavior(view.SelectionBehavior.SelectItems)
    view.setFirstColumnInteractable(False)

    view.resize(800, 600)
    view.show()
    qtbot.waitExposed(view)
    
    # Ensure all cells are visible by resizing columns and rows
    view.resizeColumnsToContents()
    view.resizeRowsToContents()
    qtbot.wait(50)
    QApplication.processEvents()

    # Step 1: Select cells (2,2) through (4,4) - a 3x3 block
    start = _center_pos(view, 2, 2)
    end = _center_pos(view, 4, 4)
    _drag_select(qtbot, view, start, end)

    selected1 = _get_selected_cells(view.selectedIndexes())
    expected1 = [(r, c) for r in range(2, 5) for c in range(2, 5)]
    assert selected1 == expected1, f"First selection: expected {expected1}, got {selected1}"

    # Step 2: Click elsewhere to deselect (should select only the clicked cell)
    click_pos = _center_pos(view, 7, 7)
    qtbot.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=click_pos)

    selected2 = _get_selected_cells(view.selectedIndexes())
    expected2 = [(7, 7)]
    assert selected2 == expected2, f"After deselect click: expected {expected2}, got {selected2}"

    # Step 3: Select again - cells (9,1) through (11,3) - a 3x3 block
    start2 = _center_pos(view, 9, 1)
    end2 = _center_pos(view, 11, 3)
    _drag_select(qtbot, view, start2, end2)

    selected3 = _get_selected_cells(view.selectedIndexes())
    expected3 = [(r, c) for r in range(9, 12) for c in range(1, 4)]
    assert selected3 == expected3, f"Second selection: expected {expected3}, got {selected3}"


def test_drag_selection_exact_rectangular_block(qtbot: QtBot):
    """
    Test drag-selection of a rectangular block with exact cell-by-cell verification.
    Tests a 5x4 block starting at (1,2) ending at (5,5).
    """
    view = RobustTableView()
    qtbot.addWidget(view)

    model = _model(rows=12, cols=12)
    view.setModel(model)
    view.setSelectionMode(view.SelectionMode.ContiguousSelection)
    view.setSelectionBehavior(view.SelectionBehavior.SelectItems)
    view.setFirstColumnInteractable(False)

    view.resize(800, 600)
    view.show()
    qtbot.waitExposed(view)
    # Drag from (1,2) to (5,5) - should select rows 1-5, columns 2-5
    start = _center_pos(view, 1, 2)
    end = _center_pos(view, 5, 5)
    _drag_select(qtbot, view, start, end)

    selected = _get_selected_cells(view.selectedIndexes())
    expected = [(r, c) for r in range(1, 6) for c in range(2, 6)]
    assert len(selected) == 20, f"Expected 20 cells (5x4), got {len(selected)}"
    assert selected == expected, f"Expected {expected}, got {selected}"


def test_multiple_sequential_selections_with_verification(qtbot: QtBot):
    """
    Test multiple sequential selections: select area A, deselect, select area B.
    Each step verifies exact cell coordinates.
    """
    view = RobustTableView()
    qtbot.addWidget(view)

    model = _model(rows=20, cols=20)
    view.setModel(model)
    view.setSelectionMode(view.SelectionMode.ContiguousSelection)
    view.setSelectionBehavior(view.SelectionBehavior.SelectItems)
    view.setFirstColumnInteractable(False)

    view.resize(1000, 800)
    view.show()
    qtbot.waitExposed(view)

    # Selection 1: Select (3,3) to (6,6) - 4x4 block
    start1 = _center_pos(view, 3, 3)
    end1 = _center_pos(view, 6, 6)
    _drag_select(qtbot, view, start1, end1)

    selected1 = _get_selected_cells(view.selectedIndexes())
    expected1 = [(r, c) for r in range(3, 7) for c in range(3, 7)]
    assert selected1 == expected1, f"Selection 1: expected {expected1}, got {selected1}"

    # Deselect by clicking elsewhere
    click1 = _center_pos(view, 10, 10)
    qtbot.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=click1)
    selected_after_click = _get_selected_cells(view.selectedIndexes())
    assert selected_after_click == [(10, 10)], f"After click: expected [(10, 10)], got {selected_after_click}"

    # Selection 2: Select (8,1) to (12,4) - 5x4 block
    start2 = _center_pos(view, 8, 1)
    end2 = _center_pos(view, 12, 4)
    _drag_select(qtbot, view, start2, end2)

    selected2 = _get_selected_cells(view.selectedIndexes())
    expected2 = [(r, c) for r in range(8, 13) for c in range(1, 5)]
    assert selected2 == expected2, f"Selection 2: expected {expected2}, got {selected2}"

    # Deselect again
    click2 = _center_pos(view, 15, 15)
    qtbot.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=click2)
    selected_after_click2 = _get_selected_cells(view.selectedIndexes())
    assert selected_after_click2 == [(15, 15)], f"After click 2: expected [(15, 15)], got {selected_after_click2}"

    # Selection 3: Select (0,0) to (2,2) - 3x3 block at origin
    start3 = _center_pos(view, 0, 0)
    end3 = _center_pos(view, 2, 2)
    _drag_select(qtbot, view, start3, end3)

    selected3 = _get_selected_cells(view.selectedIndexes())
    expected3 = [(r, c) for r in range(0, 3) for c in range(0, 3)]
    assert selected3 == expected3, f"Selection 3: expected {expected3}, got {selected3}"


def test_edge_case_boundary_selections(qtbot: QtBot):
    """
    Test selecting cells at all boundaries: first row, last row, first col, last col.
    Verifies exact cell coordinates for edge cases.
    """
    view = RobustTableView()
    qtbot.addWidget(view)

    model = _model(rows=10, cols=10)
    view.setModel(model)
    view.setSelectionMode(view.SelectionMode.ContiguousSelection)
    view.setSelectionBehavior(view.SelectionBehavior.SelectItems)
    view.setFirstColumnInteractable(False)

    view.resize(800, 600)
    view.show()
    qtbot.waitExposed(view)

    # Test 1: First row selection (0,1) to (0,4)
    start1 = _center_pos(view, 0, 1)
    end1 = _center_pos(view, 0, 4)
    _drag_select(qtbot, view, start1, end1)

    selected1 = _get_selected_cells(view.selectedIndexes())
    expected1 = [(0, c) for c in range(1, 5)]
    assert selected1 == expected1, f"First row: expected {expected1}, got {selected1}"

    # Test 2: Last row selection (9,2) to (9,6)
    click_clear = _center_pos(view, 5, 5)
    qtbot.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=click_clear)

    start2 = _center_pos(view, 9, 2)
    end2 = _center_pos(view, 9, 6)
    _drag_select(qtbot, view, start2, end2)

    selected2 = _get_selected_cells(view.selectedIndexes())
    expected2 = [(9, c) for c in range(2, 7)]
    assert selected2 == expected2, f"Last row: expected {expected2}, got {selected2}"

    # Test 3: First column selection (2,0) to (5,0)
    click_clear2 = _center_pos(view, 1, 1)
    qtbot.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=click_clear2)

    start3 = _center_pos(view, 2, 0)
    end3 = _center_pos(view, 5, 0)
    _drag_select(qtbot, view, start3, end3)

    selected3 = _get_selected_cells(view.selectedIndexes())
    expected3 = [(r, 0) for r in range(2, 6)]
    assert selected3 == expected3, f"First column: expected {expected3}, got {selected3}"

    # Test 4: Last column selection (3,9) to (7,9)
    click_clear3 = _center_pos(view, 1, 1)
    qtbot.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=click_clear3)

    start4 = _center_pos(view, 3, 9)
    end4 = _center_pos(view, 7, 9)
    _drag_select(qtbot, view, start4, end4)

    selected4 = _get_selected_cells(view.selectedIndexes())
    expected4 = [(r, 9) for r in range(3, 8)]
    assert selected4 == expected4, f"Last column: expected {expected4}, got {selected4}"


def test_single_cell_expand_then_reset(qtbot: QtBot):
    """
    Test selecting a single cell, then dragging to expand selection, then clicking to reset.
    Verifies exact cells at each step.
    """
    view = RobustTableView()
    qtbot.addWidget(view)

    model = _model(rows=12, cols=12)
    view.setModel(model)
    view.setSelectionMode(view.SelectionMode.ContiguousSelection)
    view.setSelectionBehavior(view.SelectionBehavior.SelectItems)
    view.setFirstColumnInteractable(False)

    view.resize(800, 600)
    view.show()
    qtbot.waitExposed(view)

    # Step 1: Click single cell (4,4)
    click1 = _center_pos(view, 4, 4)
    qtbot.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=click1)

    selected1 = _get_selected_cells(view.selectedIndexes())
    assert selected1 == [(4, 4)], f"Single cell: expected [(4, 4)], got {selected1}"

    # Step 2: Drag from (4,4) to (7,7) to expand selection
    start = _center_pos(view, 4, 4)
    end = _center_pos(view, 7, 7)
    _drag_select(qtbot, view, start, end)

    selected2 = _get_selected_cells(view.selectedIndexes())
    expected2 = [(r, c) for r in range(4, 8) for c in range(4, 8)]
    assert selected2 == expected2, f"Expanded: expected {expected2}, got {selected2}"

    # Step 3: Click elsewhere to reset to single cell (2,2)
    click2 = _center_pos(view, 2, 2)
    qtbot.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=click2)

    selected3 = _get_selected_cells(view.selectedIndexes())
    assert selected3 == [(2, 2)], f"Reset: expected [(2, 2)], got {selected3}"


def test_first_column_mode_switch_and_reselect(qtbot: QtBot):
    """
    Test selecting in first column mode, then switching modes and selecting again.
    Verifies exact cell coordinates in both modes.
    """
    view = RobustTableView()
    qtbot.addWidget(view)

    model = _model(rows=15, cols=15)
    view.setModel(model)
    view.setSelectionMode(view.SelectionMode.ContiguousSelection)
    view.setSelectionBehavior(view.SelectionBehavior.SelectItems)

    view.resize(800, 600)
    view.show()
    qtbot.waitExposed(view)

    # Mode 1: First column only - select rows 2-5 in column 0
    view.setFirstColumnInteractable(True)
    start1 = _center_pos(view, 2, 0)
    end1 = _center_pos(view, 5, 0)
    _drag_select(qtbot, view, start1, end1)

    selected1 = _get_selected_cells(view.selectedIndexes())
    expected1 = [(r, 0) for r in range(2, 6)]
    assert selected1 == expected1, f"First column mode: expected {expected1}, got {selected1}"

    # Switch to all columns mode
    view.setFirstColumnInteractable(False)

    # Click to clear previous selection
    click_clear = _center_pos(view, 1, 1)
    qtbot.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=click_clear)

    # Mode 2: All columns - select (7,2) to (9,5) - 3x4 block
    start2 = _center_pos(view, 7, 2)
    end2 = _center_pos(view, 9, 5)
    _drag_select(qtbot, view, start2, end2)

    selected2 = _get_selected_cells(view.selectedIndexes())
    expected2 = [(r, c) for r in range(7, 10) for c in range(2, 6)]
    assert selected2 == expected2, f"All columns mode: expected {expected2}, got {selected2}"


def test_specific_pattern_selection_verification(qtbot: QtBot):
    """
    Test selecting cells in specific patterns (L-shape, single row, single column)
    with exact cell coordinate verification.
    """
    view = RobustTableView()
    qtbot.addWidget(view)

    model = _model(rows=12, cols=12)
    view.setModel(model)
    view.setSelectionMode(view.SelectionMode.ContiguousSelection)
    view.setSelectionBehavior(view.SelectionBehavior.SelectItems)
    view.setFirstColumnInteractable(False)

    view.resize(800, 600)
    view.show()
    qtbot.waitExposed(view)

    # Pattern 1: Single row (row 5, columns 1-6)
    start1 = _center_pos(view, 5, 1)
    end1 = _center_pos(view, 5, 6)
    _drag_select(qtbot, view, start1, end1)

    selected1 = _get_selected_cells(view.selectedIndexes())
    expected1 = [(5, c) for c in range(1, 7)]
    assert selected1 == expected1, f"Single row: expected {expected1}, got {selected1}"

    # Pattern 2: Single column (rows 2-8, column 3)
    click_clear = _center_pos(view, 0, 0)
    qtbot.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=click_clear)

    start2 = _center_pos(view, 2, 3)
    end2 = _center_pos(view, 8, 3)
    _drag_select(qtbot, view, start2, end2)

    selected2 = _get_selected_cells(view.selectedIndexes())
    expected2 = [(r, 3) for r in range(2, 9)]
    assert selected2 == expected2, f"Single column: expected {expected2}, got {selected2}"

    # Pattern 3: Square block (3,3) to (6,6)
    click_clear2 = _center_pos(view, 1, 1)
    qtbot.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=click_clear2)

    start3 = _center_pos(view, 3, 3)
    end3 = _center_pos(view, 6, 6)
    _drag_select(qtbot, view, start3, end3)

    selected3 = _get_selected_cells(view.selectedIndexes())
    expected3 = [(r, c) for r in range(3, 7) for c in range(3, 7)]
    assert selected3 == expected3, f"Square block: expected {expected3}, got {selected3}"


def test_select_clear_select_different_pattern(qtbot: QtBot):
    """
    Test selecting cells, clearing selection, then selecting a completely different pattern.
    Verifies exact cells at each stage.
    """
    view = RobustTableView()
    qtbot.addWidget(view)

    model = _model(rows=15, cols=15)
    view.setModel(model)
    view.setSelectionMode(view.SelectionMode.ExtendedSelection)
    view.setSelectionBehavior(view.SelectionBehavior.SelectItems)
    view.setFirstColumnInteractable(False)

    view.resize(1000, 800)
    view.show()
    qtbot.waitExposed(view)

    # Initial selection: Large block (1,1) to (5,8)
    start1 = _center_pos(view, 1, 1)
    end1 = _center_pos(view, 5, 8)
    _drag_select(qtbot, view, start1, end1)

    selected1 = _get_selected_cells(view.selectedIndexes())
    expected1 = [(r, c) for r in range(1, 6) for c in range(1, 9)]
    assert len(selected1) == 40, f"Expected 40 cells (5x8), got {len(selected1)}"
    assert selected1 == expected1, f"Initial selection: expected {expected1}, got {selected1}"

    # Clear by clicking elsewhere
    click_clear = _center_pos(view, 10, 10)
    qtbot.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=click_clear)
    selected_cleared = _get_selected_cells(view.selectedIndexes())
    assert selected_cleared == [(10, 10)], f"After clear: expected [(10, 10)], got {selected_cleared}"

    # New selection: Different pattern - (7,2) to (11,4) - 5x3 block
    start2 = _center_pos(view, 7, 2)
    end2 = _center_pos(view, 11, 4)
    _drag_select(qtbot, view, start2, end2)

    selected2 = _get_selected_cells(view.selectedIndexes())
    expected2 = [(r, c) for r in range(7, 12) for c in range(2, 5)]
    assert len(selected2) == 15, f"Expected 15 cells (5x3), got {len(selected2)}"
    assert selected2 == expected2, f"New selection: expected {expected2}, got {selected2}"

    # Clear again
    click_clear2 = _center_pos(view, 0, 0)
    qtbot.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=click_clear2)

    # Final selection: Small block (12,5) to (13,7) - 2x3 block
    start3 = _center_pos(view, 12, 5)
    end3 = _center_pos(view, 13, 7)
    _drag_select(qtbot, view, start3, end3)

    selected3 = _get_selected_cells(view.selectedIndexes())
    expected3 = [(r, c) for r in range(12, 14) for c in range(5, 8)]
    assert len(selected3) == 6, f"Expected 6 cells (2x3), got {len(selected3)}"
    assert selected3 == expected3, f"Final selection: expected {expected3}, got {selected3}"


def test_exact_row_column_combinations(qtbot: QtBot):
    """
    Test selecting specific row/column combinations and verifying exact matches.
    Tests various rectangular selections with precise coordinate verification.
    """
    view = RobustTableView()
    qtbot.addWidget(view)

    model = _model(rows=10, cols=10)
    view.setModel(model)
    view.setSelectionMode(view.SelectionMode.ContiguousSelection)
    view.setSelectionBehavior(view.SelectionBehavior.SelectItems)
    view.setFirstColumnInteractable(False)

    view.resize(800, 600)
    view.show()
    qtbot.waitExposed(view)

    # Test 1: 2x2 block at (1,1) to (2,2)
    start1 = _center_pos(view, 1, 1)
    end1 = _center_pos(view, 2, 2)
    _drag_select(qtbot, view, start1, end1)

    selected1 = _get_selected_cells(view.selectedIndexes())
    expected1 = [(1, 1), (1, 2), (2, 1), (2, 2)]
    assert selected1 == expected1, f"2x2 block: expected {expected1}, got {selected1}"

    # Test 2: 1x5 horizontal strip (3,2) to (3,6)
    click_clear = _center_pos(view, 0, 0)
    qtbot.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=click_clear)

    start2 = _center_pos(view, 3, 2)
    end2 = _center_pos(view, 3, 6)
    _drag_select(qtbot, view, start2, end2)

    selected2 = _get_selected_cells(view.selectedIndexes())
    expected2 = [(3, 2), (3, 3), (3, 4), (3, 5), (3, 6)]
    assert selected2 == expected2, f"1x5 strip: expected {expected2}, got {selected2}"

    # Test 3: 4x1 vertical strip (4,5) to (7,5)
    click_clear2 = _center_pos(view, 0, 0)
    qtbot.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=click_clear2)

    start3 = _center_pos(view, 4, 5)
    end3 = _center_pos(view, 7, 5)
    _drag_select(qtbot, view, start3, end3)

    selected3 = _get_selected_cells(view.selectedIndexes())
    expected3 = [(4, 5), (5, 5), (6, 5), (7, 5)]
    assert selected3 == expected3, f"4x1 strip: expected {expected3}, got {selected3}"

    # Test 4: 3x4 block (5,1) to (7,4)
    click_clear3 = _center_pos(view, 0, 0)
    qtbot.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=click_clear3)

    start4 = _center_pos(view, 5, 1)
    end4 = _center_pos(view, 7, 4)
    _drag_select(qtbot, view, start4, end4)

    selected4 = _get_selected_cells(view.selectedIndexes())
    expected4 = [(r, c) for r in range(5, 8) for c in range(1, 5)]
    assert len(selected4) == 12, f"Expected 12 cells (3x4), got {len(selected4)}"
    assert selected4 == expected4, f"3x4 block: expected {expected4}, got {selected4}"
