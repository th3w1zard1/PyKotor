from __future__ import annotations

import csv

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qtpy.QtWidgets import QApplication

from toolset.common.actions.base import CommonActions

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

    def remove_selected_rows(self):
        for selection in self.tableWidget.selectedRanges():
            for row in range(selection.bottomRow(), selection.topRow()-1, -1):
                self.tableWidget.removeRow(row)

    def copySelectionToClipboard(self):
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

    def invert_selection(self):
        for i in range(self.tableWidget.rowCount()):
            for j in range(self.tableWidget.columnCount()):
                item = self.tableWidget.item(i, j)
                if item.isSelected():
                    item.setSelected(False)
                else:
                    item.setSelected(True)

    def export_selection_to_csv(self):
        path, _ = QFileDialog.getSaveFileName(self.tableWidget, "Save CSV", filter="CSV Files (*.csv)")
        if path:
            with open(path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                selection = self.tableWidget.selectedIndexes()
                if not selection:
                    return
                rows = sorted(set(index.row() for index in selection))
                for row in rows:
                    row_data = [self.tableWidget.item(row, col).text() if self.tableWidget.item(row, col) else '' for col in range(self.tableWidget.columnCount())]
                    writer.writerow(row_data)
            QMessageBox.information(self.tableWidget, "Export Successful", "The data has been exported successfully.")

    def clear_table(self):
        self.tableWidget.setRowCount(0)

    def insert_row_above(self):
        current_row = self.tableWidget.currentRow()
        self.tableWidget.insertRow(current_row)

    def insert_row_below(self):
        current_row = self.tableWidget.currentRow()
        self.tableWidget.insertRow(current_row + 1)

    def move_row_up(self):
        current_row = self.tableWidget.currentRow()
        if current_row > 0:
            self.tableWidget.insertRow(current_row - 1)
            for i in range(self.tableWidget.columnCount()):
                self.tableWidget.setItem(current_row - 1, i, self.tableWidget.takeItem(current_row + 1, i))
            self.tableWidget.removeRow(current_row + 1)
            self.tableWidget.selectRow(current_row - 1)

    def move_row_down(self):
        current_row = self.tableWidget.currentRow()
        if current_row < self.tableWidget.rowCount() - 1:
            self.tableWidget.insertRow(current_row + 2)
            for i in range(self.tableWidget.columnCount()):
                self.tableWidget.setItem(current_row + 2, i, self.tableWidget.takeItem(current_row, i))
            self.tableWidget.removeRow(current_row)
            self.tableWidget.selectRow(current_row + 1)
