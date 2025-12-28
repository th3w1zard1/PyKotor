import pytest

from qtpy.QtCore import Qt
from qtpy.QtGui import QStandardItem, QStandardItemModel

from utility.ui_libraries.qt.widgets.itemviews.tableview import RobustTableView


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


def test_click_resets_selection_anchor_when_all_columns_selectable(qtbot):
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
    qtbot.mousePress(view.viewport(), Qt.MouseButton.LeftButton, pos=start)
    qtbot.mouseMove(view.viewport(), pos=end)
    qtbot.mouseRelease(view.viewport(), Qt.MouseButton.LeftButton, pos=end)
    assert view.selectedIndexes(), "precondition: drag must select at least one cell"

    # Plain click elsewhere should reset selection to the clicked cell only.
    click_pos = _center_pos(view, 1, 1)
    qtbot.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=click_pos)

    selected = view.selectedIndexes()
    assert len(selected) == 1
    assert selected[0].row() == 1
    assert selected[0].column() == 1


