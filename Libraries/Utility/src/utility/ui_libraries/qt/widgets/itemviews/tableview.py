from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import QAbstractTableModel, QModelIndex, Qt
from qtpy.QtWidgets import QApplication, QHeaderView, QPushButton, QTableView, QVBoxLayout, QWidget

from utility.ui_libraries.qt.widgets.itemviews.baseview import RobustAbstractItemView

if TYPE_CHECKING:
    from qtpy.QtCore import QPoint
    from qtpy.QtWidgets import QMenu


class RobustTableView(RobustAbstractItemView, QTableView):
    """A table view that supports common features and settings."""

    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.original_stylesheet: str = self.styleSheet()

        h_header: QHeaderView = self.horizontalHeader()
        h_header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        h_header.customContextMenuRequested.connect(self.show_header_context_menu)

        v_header: QHeaderView = self.verticalHeader()
        v_header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        v_header.customContextMenuRequested.connect(self.show_header_context_menu)

    def setup_backup_menu_when_header_hidden(self):
        corner_button = QPushButton("☰", self)
        corner_button.setFixedSize(20, 20)
        corner_button.clicked.connect(self.show_header_context_menu)
        corner_button.setToolTip("Show context menu")
        layout = QVBoxLayout(self)
        layout.addWidget(corner_button, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        layout.setContentsMargins(0, 0, 0, 0)
        QTableView.setLayout(self, layout)

    def show_header_context_menu(self, pos: QPoint):
        menu = self.build_context_menu()
        menu.exec_(self.horizontalHeader().mapToGlobal(pos))

    def build_context_menu(self) -> QMenu:
        menu = super().build_context_menu()

        table_view_menu = menu.addMenu("TableView")
        actions_menu = table_view_menu.addMenu("Actions")
        settings_menu = table_view_menu.addMenu("Settings")
        advanced_menu = settings_menu.addMenu("Advanced")

        # Actions submenu items
        self._add_simple_action(actions_menu, "Resize Columns To Contents", self.resizeColumnsToContents)
        self._add_simple_action(actions_menu, "Resize Rows To Contents", self.resizeRowsToContents)
        self._add_simple_action(actions_menu, "Clear Spans", self.clearSpans)

        # Settings submenu items
        self._add_menu_action(settings_menu, "Show Grid", self.showGrid, self.setShowGrid, "showGrid")
        self._add_menu_action(settings_menu, "Word Wrap", self.wordWrap, self.setWordWrap, "wordWrap")
        self._add_menu_action(settings_menu, "Corner Button Enabled", self.isCornerButtonEnabled, self.setCornerButtonEnabled, "cornerButtonEnabled")
        self._add_menu_action(settings_menu, "Sorting Enabled", self.isSortingEnabled, self.setSortingEnabled, "sortingEnabled")
        self._add_exclusive_menu_action(
            advanced_menu,
            "Grid Style",
            self.gridStyle,
            self.setGridStyle,
            options={
                "": Qt.PenStyle.NoPen,
                "—": Qt.PenStyle.SolidLine,
                "- -": Qt.PenStyle.DashLine,
                "•••": Qt.PenStyle.DotLine,
                "-•-": Qt.PenStyle.DashDotLine,
                "-••-": Qt.PenStyle.DashDotDotLine,
            },
            settings_key="gridStyle",
        )

        self._add_menu_action(settings_menu, "Stretch Last Section", self.horizontalHeader().stretchLastSection, self.horizontalHeader().setStretchLastSection, "stretchLastSection")
        self._add_menu_action(settings_menu, "Cascade Section Resizes", self.horizontalHeader().cascadingSectionResizes, self.horizontalHeader().setCascadingSectionResizes, "cascadingSectionResizes")
        self._add_menu_action(settings_menu, "High Light Sections", self.horizontalHeader().highlightSections, self.horizontalHeader().setHighlightSections, "highlightSections")
        self._add_exclusive_menu_action(
            settings_menu,
            "Section Resize Mode",
            lambda: self.horizontalHeader().sectionResizeMode(0),
            self.horizontalHeader().setSectionResizeMode,
            options={
                "Interactive": QHeaderView.ResizeMode.Interactive,
                "Fixed": QHeaderView.ResizeMode.Fixed,
                "Stretch": QHeaderView.ResizeMode.Stretch,
                "ResizeToContents": QHeaderView.ResizeMode.ResizeToContents,
            },
            settings_key="horizontalSectionResizeMode",
        )

        self._add_menu_action(actions_menu, "Visible", self.verticalHeader().isVisible, self.verticalHeader().setVisible, "verticalHeaderVisible")
        self._add_exclusive_menu_action(
            settings_menu,
            "Section Resize Mode",
            lambda: self.verticalHeader().sectionResizeMode(0),
            self.verticalHeader().setSectionResizeMode,
            options={
                "Interactive": QHeaderView.ResizeMode.Interactive,
                "Fixed": QHeaderView.ResizeMode.Fixed,
                "Stretch": QHeaderView.ResizeMode.Stretch,
                "ResizeToContents": QHeaderView.ResizeMode.ResizeToContents,
            },
            settings_key="verticalSectionResizeMode",
        )

        return menu

    def update_columns_after_text_size_change(self):
        model = self.model()
        assert model is not None
        for column in range(model.columnCount()):
            self.resizeColumnToContents(column)


class SimpleTableModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data: list[list[str]] = data

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        return len(self._data)

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        return len(self._data[0]) if self._data else 0

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.ItemDataRole.DisplayRole) -> str | None:
        if role == Qt.ItemDataRole.DisplayRole:
            return self._data[index.row()][index.column()]
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = Qt.ItemDataRole.DisplayRole) -> str | None:
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return f"Column {section + 1}"
            return f"Row {section + 1}"
        return None

    def add_row(self, row_data: list[str]):
        self.beginInsertRows(QModelIndex(), len(self._data), len(self._data))
        self._data.append(row_data)
        self.endInsertRows()

    def remove_last_row(self):
        if self._data:
            self.beginRemoveRows(QModelIndex(), len(self._data) - 1, len(self._data) - 1)
            self._data.pop()
            self.endRemoveRows()


if __name__ == "__main__":
    app = QApplication([])

    # Create the main window
    main_window = QWidget()
    layout = QVBoxLayout(main_window)

    # Create and set up the RobustTableView
    table_view = RobustTableView()
    layout.addWidget(table_view)

    # Create a simple model with some example data
    data = [
        ["Apple", "Red", "Sweet"],
        ["Banana", "Yellow", "Sweet"],
        ["Lemon", "Yellow", "Sour"],
    ]
    model = SimpleTableModel(data)
    table_view.setModel(model)

    # Ensure the header is visible
    table_view.horizontalHeader().setVisible(True)
    table_view.verticalHeader().setVisible(True)

    # Add buttons to add and remove rows
    add_button = QPushButton("Add Row")
    remove_button = QPushButton("Remove Last Row")
    layout.addWidget(add_button)
    layout.addWidget(remove_button)

    def add_row():
        model.add_row(["New Item", "Color", "Taste"])
        table_view.update_columns_after_text_size_change()

    def remove_row():
        model.remove_last_row()
        table_view.update_columns_after_text_size_change()

    add_button.clicked.connect(add_row)
    remove_button.clicked.connect(remove_row)

    # Show the main window
    main_window.resize(400, 300)
    main_window.show()

    app.exec_()