from __future__ import annotations

import csv

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qtpy.QtWidgets import QApplication, QFileDialog

from toolset.common.actions.base import CommonActions, MenuActionInfo, MenuActionType, SelectionType
from utility.system.path import Path

if TYPE_CHECKING:
    from qtpy.QtWidgets import QTableWidget, QTableWidgetItem


# Context data classes
@dataclass
class TableActionContext:
    widget: QTableWidget
    action: str
    selected_items: list[QTableWidgetItem]


class CommonTableActions(CommonActions):
    def __init__(self, table: QTableWidget):
        self.tableWidget: QTableWidget = table

    @CommonActions.action(
        MenuActionInfo(
            "Copy to Clipboard",
            menu_type=MenuActionType.SELECT,
            selection_type=SelectionType.UNDER_MOUSE,
        )
    )
    def copySelectedToClipboard(self):
        selection = self.tableWidget.selectedIndexes()
        if not selection:
            return
        rows = sorted(index.row() for index in selection)
        columns = sorted(index.column() for index in selection)
        row_count = rows[-1] - rows[0] + 1
        column_count = columns[-1] - columns[0] + 1
        table_text = [[""] * column_count for _ in range(row_count)]
        for index in selection:
            row = index.row() - rows[0]
            column = index.column() - columns[0]
            table_text[row][column] = index.data()

        # Format table text as a tab-delimited string
        clipboard_text = "\n".join("\t".join(row) for row in table_text)
        QApplication.clipboard().setText(clipboard_text)

    @CommonActions.action(
        MenuActionInfo(
            "Invert Selected",
            menu_type=MenuActionType.SELECT,
            selection_type=SelectionType.HIGHLIGHTED,
        )
    )
    def invertSelection(self):
        for row in range(self.tableWidget.rowCount()):
            for col in range(self.tableWidget.columnCount()):
                item = self.tableWidget.item(row, col)
                if item is None:
                    print(f"Skipping row {row} column {col}, item is None")
                    continue
                if item.isSelected():
                    item.setSelected(False)
                else:
                    item.setSelected(True)

    @CommonActions.action(
        MenuActionInfo(
            "Export Selected to CSV",
            menu_type=MenuActionType.SELECT,
            selection_type=SelectionType.HIGHLIGHTED,
        )
    )
    def exportSelectionToCSV(self):
        selectedIndices = self.tableWidget.selectedIndexes()
        if not selectedIndices:
            return
        filepath_str, _ = QFileDialog.getSaveFileName(self.tableWidget, "Save CSV", filter="CSV Files (*.csv)")
        if not filepath_str:
            return
        filepath = Path(filepath_str)
        with filepath.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            rows = sorted({index.row() for index in selectedIndices})
            for row in rows:
                row_cells = []
                for col in range(self.tableWidget.columnCount()):
                    table_cell_item = self.tableWidget.item(row, col)
                    if table_cell_item is None:
                        print(f"Skipping row {row} column {col}, item is None")
                        continue
                    row_cells.append(table_cell_item)
                writer.writerow(row_cells)
        # TODO(th3w1zard1): schedule this instead as it won't always be in the main thread/process.
        #QMessageBox.information(self.tableWidget, "Export Successful", f"The data has been exported as CSV to '{filepath}'.")

    @CommonActions.action(
        MenuActionInfo(
            "Remove Selected Rows",
            menu_type=MenuActionType.SELECT,
            selection_type=SelectionType.HIGHLIGHTED,
        )
    )
    def removeSelectedRows(self):
        for selection in self.tableWidget.selectedRanges():
            for row in range(selection.bottomRow(), selection.topRow()-1, -1):
                self.tableWidget.removeRow(row)

    @CommonActions.action(
        MenuActionInfo(
            "Clear Table",
            menu_type=MenuActionType.SELECT,
            selection_type=SelectionType.ALL,
        )
    )
    def clear_table(self):
        self.tableWidget.setRowCount(0)

    @CommonActions.action(
        MenuActionInfo(
            "Insert Row Above",
            menu_type=MenuActionType.SELECT,
            selection_type=SelectionType.UNDER_MOUSE,
        )
    )
    def insertRowAbove(self):
        current_row = self.tableWidget.currentRow()
        self.tableWidget.insertRow(current_row)

    @CommonActions.action(
        MenuActionInfo(
            "Insert Row Below",
            menu_type=MenuActionType.SELECT,
            selection_type=SelectionType.UNDER_MOUSE,
        )
    )
    def insertRowBelow(self):
        current_row = self.tableWidget.currentRow()
        self.tableWidget.insertRow(current_row + 1)

    @CommonActions.action(
        MenuActionInfo(
            "Move Row Up",
            menu_type=MenuActionType.SELECT,
            selection_type=SelectionType.UNDER_MOUSE,
        )
    )
    def moveRowUp(self):
        current_row = self.tableWidget.currentRow()
        if current_row > 0:
            self.tableWidget.insertRow(current_row - 1)
            for i in range(self.tableWidget.columnCount()):
                self.tableWidget.setItem(current_row - 1, i, self.tableWidget.takeItem(current_row + 1, i))
            self.tableWidget.removeRow(current_row + 1)
            self.tableWidget.selectRow(current_row - 1)


    @CommonActions.action(
        MenuActionInfo(
            "Move Row Down",
            menu_type=MenuActionType.SELECT,
            selection_type=SelectionType.UNDER_MOUSE,
        )
    )
    def moveRowDown(self):
        current_row = self.tableWidget.currentRow()
        if current_row < self.tableWidget.rowCount() - 1:
            self.tableWidget.insertRow(current_row + 2)
            for i in range(self.tableWidget.columnCount()):
                self.tableWidget.setItem(current_row + 2, i, self.tableWidget.takeItem(current_row, i))
            self.tableWidget.removeRow(current_row)
            self.tableWidget.selectRow(current_row + 1)
