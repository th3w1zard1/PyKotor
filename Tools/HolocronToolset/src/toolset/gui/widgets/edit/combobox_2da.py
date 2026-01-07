#!/usr/bin/env python3
from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from qtpy import QtCore
from qtpy.QtCore import Qt
from qtpy.QtGui import QPainter, QPalette, QPen, QStandardItemModel
from qtpy.QtWidgets import (
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QComboBox,
    QMenu,
    QMessageBox,
)

if TYPE_CHECKING:
    from qtpy.QtCore import QAbstractItemModel, QPoint
    from qtpy.QtGui import QColor, QPaintEvent
    from qtpy.QtWidgets import QWidget

    from pykotor.resource.formats.twoda import TwoDA
    from toolset.data.installation import HTInstallation


_ROW_INDEX_DATA_ROLE: int = QtCore.Qt.ItemDataRole.UserRole + 4
_REAL_2DA_TEXT_ROLE: int = QtCore.Qt.ItemDataRole.UserRole + 5


class ComboBox2DA(QComboBox):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)
        self.currentIndexChanged.connect(self.on_current_index_changed)
        from toolset.gui.common.localization import translate as tr

        self.setToolTip(tr("<i>Right click for more options</i>"))

        self._sort_alphabetically: bool = False
        self._this2DA: TwoDA | None = None
        self._installation: HTInstallation | None = None
        self._resname: str | None = None

    def paintEvent(self, event: QPaintEvent):  # pyright: ignore[reportIncompatibleMethodOverride]  # type: ignore[override]
        super().paintEvent(event)
        if super().currentIndex() == -1:
            painter: QPainter = QPainter(self)
            # Fetch the text color from the palette
            text_color: QColor = self.palette().color(QPalette.ColorRole.Text)
            painter.setPen(QPen(text_color))
            text_rect: QtCore.QRect = self.rect().adjusted(2, 0, 0, 0)
            painter.drawText(text_rect, int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft), self.placeholderText())
            painter.end()

    def currentIndex(self) -> int:
        """Returns the row index from the currently selected item: This is NOT the index into the combobox like it would be with a normal QCombobox.

        Returns:
        -------
            Row index into the 2DA file.
        """
        current_index = super().currentIndex()
        if current_index == -1:
            return 0
        row_index = self.itemData(current_index, _ROW_INDEX_DATA_ROLE)
        return row_index or 0

    def setCurrentIndex(self, row_in_2da: int):  # type: ignore[override]  # pyright: ignore[reportIncompatibleMethodOverride]
        """Selects the item with the specified row index: This is NOT the index into the combobox like it would be with a normal QCombobox.

        If the index cannot be found, it will create an item with the matching index.

        Args:
        ----
            rowIn2DA: The Row index to select.
        """
        index = None
        for i in range(self.count()):
            if self.itemData(i, _ROW_INDEX_DATA_ROLE) == row_in_2da:
                index = i

        if index is None:
            self.addItem(f"[Modded Entry #{row_in_2da}]", row_in_2da)
            index = self.count() - 1

        super().setCurrentIndex(index)

    def addItem(  # type: ignore[override]  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        text: str,
        row: int | None = None,
    ):
        """Adds the 2DA row into the combobox.

        If the row index is not specified, then the value will be set to the number of items in the combobox (the last row + 1).

        Args:
        ----
            text: Text to display.
            row: The row index into the 2DA table.
        """
        if row is None:
            row = self.count()
        assert isinstance(text, str), f"text '{text}' ({text.__class__.__name__}) is not a str"
        assert isinstance(row, int), f"row '{row}' ({row.__class__.__name__}) is not an int"
        display_text = text if text.startswith("[Modded Entry #") else f"{text} [{row}]"
        # Store row in default role (Qt.UserRole) for compatibility with itemData() without role parameter
        super().addItem(display_text, row)

        self.setItemData(self.count() - 1, row, _ROW_INDEX_DATA_ROLE)
        self.setItemData(self.count() - 1, text, _REAL_2DA_TEXT_ROLE)

    def insertItem(self, index: int, text: str):  # type: ignore[override]  # pyright: ignore[reportIncompatibleMethodOverride]
        """Raises NotImplementedError because inserting an item without specifying a row index is not supported."""
        msg = "Inserting an item using insertItem is not supported. Use addItem to add a new entry to the combobox."
        raise NotImplementedError(msg)

    def addItems(self, texts: list[str]):  # type: ignore[override]  # pyright: ignore[reportIncompatibleMethodOverride]
        """Raises NotImplementedError because bulk adding items without specifying row indices is not supported."""
        msg = "Bulk adding items using addItems is not supported. Use set_items to add multiple items with proper row indices."
        raise NotImplementedError(msg)

    def insertItems(self, index: int, texts: list[str]):  # type: ignore[override]  # pyright: ignore[reportIncompatibleMethodOverride]
        """Raises NotImplementedError because bulk inserting items without specifying row indices is not supported."""
        msg = "Bulk inserting items using insertItems is not supported. Use set_items to insert multiple items with proper row indices."
        raise NotImplementedError(msg)

    def on_current_index_changed(self, index: int):
        self.update_tool_tip()

    def on_context_menu(self, point: QPoint):
        menu: QMenu = QMenu(self)
        if self._installation is not None and self._resname is not None and self._this2DA is not None:
            open_action = QAction(f"Open '{self._resname}.2da' in 2DAEditor", self)
            assert open_action is not None, "Failed to create 'Open in 2DAEditor' action."
            open_action.triggered.connect(self.open_in_2da_editor)
            menu.addAction(open_action)

            # Add "Find References" action for 2DA row
            row_index = self.currentIndex()
            if row_index >= 0:
                find_refs_action = QAction("Find References...", self)
                find_refs_action.triggered.connect(lambda checked=False: self._find_2da_row_references(row_index))
                menu.addAction(find_refs_action)

        toggle_sort_action = QAction("Toggle Sorting", self)
        toggle_sort_action.setCheckable(True)
        toggle_sort_action.setChecked(self._sort_alphabetically)
        toggle_sort_action.triggered.connect(self.toggle_sort)
        menu.addAction(toggle_sort_action)
        menu.popup(self.mapToGlobal(point))

    def set_items(
        self,
        values: Iterable[str],
        *,
        sort_alphabetically: bool = True,
        cleanup_strings: bool = True,
        ignore_blanks: bool = False,
    ):
        self._sort_alphabetically = sort_alphabetically
        self.clear()

        for index, text in enumerate(values):
            assert isinstance(text, str), f"text '{text}' ({text.__class__.__name__}) is not a str"
            new_text: str = text
            if cleanup_strings:
                new_text = text.replace("TRAP_", "")
                new_text = text.replace("GENDER_", "")
                new_text = text.replace("_", " ")
            if not ignore_blanks or (new_text and new_text.strip()):
                self.addItem(new_text, index)

        self.enable_sort() if self._sort_alphabetically else self.disable_sort()

    def update_tool_tip(self):
        row_index_display = f"<b>Row Index:</b> {self.currentIndex()}<br>" if self.currentIndex() != -1 else ""
        if self._resname and self._this2DA:
            tooltip_text = f"<b>Filename:</b> {self._resname}.2da<br>{row_index_display}<br><i>Right-click for more options.</i>"
        else:
            tooltip_text = f"{row_index_display}<br><i>Right-click for more options.</i>"
        self.setToolTip(tooltip_text)

    def set_context(self, data: TwoDA | None, install: HTInstallation, resname: str):
        if data is not None:
            self._this2DA = data
        self._installation = install
        self._resname = resname

    def toggle_sort(self):
        self.disable_sort() if self._sort_alphabetically else self.enable_sort()

    def enable_sort(self):
        """Sorts the combobox alphabetically. This is a custom method."""
        self._sort_alphabetically = True
        model: QAbstractItemModel | None = self.model()
        if not isinstance(model, QStandardItemModel):
            return
        model.setSortRole(_REAL_2DA_TEXT_ROLE)
        model.sort(0)

    def disable_sort(self):
        """Sorts the combobox by row index. This is a custom method."""
        self._sort_alphabetically = False
        model: QAbstractItemModel | None = self.model()
        if not isinstance(model, QStandardItemModel):
            return
        model.setSortRole(_ROW_INDEX_DATA_ROLE)
        model.sort(0)

    def open_in_2da_editor(self):
        if self._installation is None or self._resname is None or self._this2DA is None:
            return
        from pykotor.resource.formats.twoda.twoda_auto import bytes_2da
        from toolset.gui.editors.twoda import TwoDAEditor
        from toolset.utils.window import add_window

        editor = TwoDAEditor(None, self._installation)
        editor.new()
        try:
            bytes_data: bytes = bytes_2da(self._this2DA)
            editor._load_main(bytes_data)  # noqa: SLF001
        except (ValueError, OSError) as e:
            error_msg: str = str((e.__class__.__name__, str(e))).replace("\n", "<br>")
            from toolset.gui.common.localization import translate as tr, trf

            QMessageBox(QMessageBox.Icon.Critical, tr("Failed to load file."), trf("Failed to open or load file data.<br>{error}", error=error_msg)).exec()
            return
        else:
            editor.jump_to_row(self.currentIndex())
        from toolset.gui.common.localization import translate as tr, trf

        editor.setWindowTitle(trf("{resname}.2da - 2DAEditor({name})", resname=self._resname, name=self._installation.name))
        add_window(editor)
        editor.show()
        editor.activateWindow()

    def _find_2da_row_references(
        self,
        row_index: int,
    ) -> None:
        """Find references to a 2DA row in the installation.

        Args:
        ----
            row_index: The row index in the 2DA file
        """
        if self._installation is None or self._resname is None or self._this2DA is None:
            return

        from qtpy.QtWidgets import QDialog

        from pykotor.tools.reference_finder import ReferenceSearchResult, find_field_value_references
        from toolset.gui.dialogs.asyncloader import AsyncLoader
        from toolset.gui.dialogs.reference_search_options import ReferenceSearchOptions
        from toolset.gui.dialogs.search import FileResults
        from toolset.utils.window import add_window

        # Get the row label/text for searching
        row_label = self._this2DA.get_cell(row_index, 0) if row_index < self._this2DA.get_height() else ""

        # Also check for stringref values in this row
        strref_values: list[int] = []
        if row_index < self._this2DA.get_height():
            # Check all columns for stringref values
            for col_name in self._this2DA.get_headers():
                if col_name and col_name != ">>##HEADER##<<":
                    cell_value = self._this2DA.get_cell(row_index, col_name)
                    if cell_value and cell_value.strip().isdigit():
                        try:
                            strref = int(cell_value.strip())
                            if strref > 0:  # Valid stringref
                                strref_values.append(strref)
                        except ValueError:
                            pass

        # Show search options dialog
        options_dialog = ReferenceSearchOptions(self)
        if options_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        partial_match = options_dialog.get_partial_match()
        case_sensitive = options_dialog.get_case_sensitive()
        file_pattern = options_dialog.get_file_pattern()
        file_types = options_dialog.get_file_types()

        all_results: list[ReferenceSearchResult] = []

        # Search for row label/text if available
        if row_label and row_label.strip():

            def search_label_fn() -> list[ReferenceSearchResult]:
                assert self._installation is not None, "Installation is not set"
                return find_field_value_references(
                    self._installation,
                    row_label,
                    partial_match=partial_match,
                    case_sensitive=case_sensitive,
                    file_pattern=file_pattern,
                    file_types=file_types,
                )

            loader = AsyncLoader(
                self,
                f"Searching for references to 2DA row '{row_label}'...",
                search_label_fn,
                error_title="An unexpected error occurred searching for references.",
                start_immediately=False,
            )
            loader.setModal(False)
            loader.show()

            def handle_label_search_completed(results_list: list[ReferenceSearchResult]):
                all_results.extend(results_list)
                # If we have stringrefs to search, do that next, otherwise show results
                if strref_values:
                    _search_stringrefs()
                else:
                    _show_results()

            loader.optional_finish_hook.connect(handle_label_search_completed)
            loader.start_worker()
            add_window(loader)

        def _search_stringrefs():
            """Search for stringref references."""
            from pykotor.tools.reference_cache import GFFRefLocation, NCSRefLocation, SSFRefLocation, TwoDARefLocation, find_strref_references

            assert self._installation is not None, "Installation is not set"
            assert isinstance(self._installation, HTInstallation), "Installation is not an HTInstallation"

            def search_strref_fn() -> list[ReferenceSearchResult]:
                all_strref_results: list[ReferenceSearchResult] = []
                for strref in strref_values:
                    strref_results = find_strref_references(self._installation, strref)
                    for result in strref_results:
                        for location in result.locations:
                            if isinstance(location, GFFRefLocation):
                                field_path = location.field_path
                                byte_offset = None
                            elif isinstance(location, TwoDARefLocation):
                                field_path = f"Row {location.row_index}, Column '{location.column_name}'"
                                byte_offset = None
                            elif isinstance(location, SSFRefLocation):
                                field_path = f"Sound index SSFSound({location.sound.value})"
                                byte_offset = None
                            elif isinstance(location, NCSRefLocation):
                                field_path = "(NCS bytecode)"
                                byte_offset = location.byte_offset
                            else:
                                field_path = "(unknown)"
                                byte_offset = None

                            restype = result.resource.restype()
                            file_type = restype.extension.upper() if restype else "UNKNOWN"

                            all_strref_results.append(
                                ReferenceSearchResult(
                                    file_resource=result.resource,
                                    field_path=field_path,
                                    matched_value=str(strref),
                                    file_type=file_type,
                                    byte_offset=byte_offset,
                                )
                            )
                return all_strref_results

            loader2 = AsyncLoader(
                self,
                f"Searching for stringref references in row {row_index}...",
                search_strref_fn,
                error_title="An unexpected error occurred searching for references.",
                start_immediately=False,
            )
            loader2.setModal(False)
            loader2.show()

            def handle_strref_search_completed(results_list: list[ReferenceSearchResult]):
                all_results.extend(results_list)
                _show_results()

            loader2.optional_finish_hook.connect(handle_strref_search_completed)
            loader2.start_worker()
            add_window(loader2)

        def _show_results():
            """Show search results."""
            if not all_results:
                from toolset.gui.common.localization import tr, trf

                QMessageBox(
                    QMessageBox.Icon.Information,
                    tr("No references found"),
                    trf("No references found for 2DA row {row_index} in '{resname}.2da'", row_index=row_index, resname=self._resname),
                    parent=self,
                ).exec()
                return

            assert self._installation is not None, "Installation is not set"
            assert isinstance(self._installation, HTInstallation), "Installation is not an HTInstallation"

            results_dialog = FileResults(self, all_results, self._installation)
            results_dialog.show()
            results_dialog.activateWindow()
            from toolset.gui.common.localization import trf

            results_dialog.setWindowTitle(
                trf(
                    "{count} reference(s) found for row {row_index} in '{resname}.2da'",
                    count=len(all_results),
                    row_index=row_index,
                    resname=self._resname,
                )
            )
            add_window(results_dialog)

        # If no row label, just search stringrefs
        if not row_label or not row_label.strip():
            if strref_values:
                _search_stringrefs()
            else:
                from toolset.gui.common.localization import tr, trf

                QMessageBox(
                    QMessageBox.Icon.Information,
                    tr("No searchable data"),
                    trf("Row {row_index} in '{resname}.2da' has no searchable label or stringref values.", row_index=row_index, resname=self._resname),
                    parent=self,
                ).exec()
