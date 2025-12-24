from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt, Signal  # pyright: ignore[reportPrivateImportUsage]
from qtpy.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from toolset.gui.common.localization import translate as tr

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


class ThemeSelectorDialog(QDialog):
    """Non-blocking dialog for selecting application themes and styles."""
    
    theme_changed = Signal(str)  # pyright: ignore[reportPrivateImportUsage]
    style_changed = Signal(str)  # pyright: ignore[reportPrivateImportUsage]
    
    def __init__(
        self,
        parent: QWidget | None = None,
        available_themes: list[str] | None = None,
        available_styles: list[str] | None = None,
        current_theme: str | None = None,
        current_style: str | None = None,
    ):
        """Initialize the theme selector dialog.
        
        Args:
        ----
            parent: Parent widget
            available_themes: List of available theme names
            available_styles: List of available style names
            current_theme: Currently selected theme name
            current_style: Currently selected style name
        """
        super().__init__(parent)
        self._available_themes = available_themes or []
        self._available_styles = available_styles or []
        self._current_theme = current_theme
        self._current_style = current_style
        self._init_ui()
        self._populate_lists()
        
    def _init_ui(self):
        """Set up the user interface."""
        self.setWindowTitle(tr("Theme Selection"))
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowTitleHint)
        self.resize(550, 650)
        
        # Set minimum size for better usability
        self.setMinimumSize(450, 500)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Search/filter box
        search_label = QLabel(tr("Search:"))
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText(tr("Filter themes and styles..."))
        self._search_edit.textChanged.connect(self._filter_items)
        
        search_layout = QVBoxLayout()
        search_layout.addWidget(search_label)
        search_layout.addWidget(self._search_edit)
        main_layout.addLayout(search_layout)
        
        # Themes section
        themes_label = QLabel(tr("Themes:"))
        themes_label.setStyleSheet("font-weight: bold; font-size: 12pt; margin-top: 5px;")
        self._themes_list = QListWidget()
        self._themes_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._themes_list.itemClicked.connect(self._on_theme_selected)
        self._themes_list.itemDoubleClicked.connect(self._on_theme_double_clicked)
        self._themes_list.setMinimumHeight(200)
        
        themes_layout = QVBoxLayout()
        themes_layout.setSpacing(5)
        themes_layout.addWidget(themes_label)
        themes_layout.addWidget(self._themes_list)
        main_layout.addLayout(themes_layout)
        
        # Styles section
        styles_label = QLabel(tr("Application Styles:"))
        styles_label.setStyleSheet("font-weight: bold; font-size: 12pt; margin-top: 5px;")
        self._styles_list = QListWidget()
        self._styles_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._styles_list.itemClicked.connect(self._on_style_selected)
        self._styles_list.itemDoubleClicked.connect(self._on_style_double_clicked)
        self._styles_list.setMaximumHeight(150)
        
        styles_layout = QVBoxLayout()
        styles_layout.addWidget(styles_label)
        styles_layout.addWidget(self._styles_list)
        main_layout.addLayout(styles_layout)
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close,
            Qt.Orientation.Horizontal,
            self,
        )
        button_box.rejected.connect(self.close)
        
        # Apply button (for immediate application)
        apply_button = QPushButton(tr("Apply"))
        apply_button.setDefault(True)
        apply_button.clicked.connect(self._apply_selection)
        button_box.addButton(apply_button, QDialogButtonBox.ButtonRole.AcceptRole)
        
        main_layout.addWidget(button_box)
        
    def _populate_lists(self):
        """Populate the theme and style lists."""
        # Populate themes
        self._themes_list.clear()
        for theme_name in sorted(self._available_themes):
            item = QListWidgetItem(theme_name)
            item.setCheckState(Qt.CheckState.Unchecked)
            if self._current_theme and theme_name.lower() == self._current_theme.lower():
                item.setCheckState(Qt.CheckState.Checked)
                self._themes_list.setCurrentItem(item)
                self._themes_list.scrollToItem(item)
            self._themes_list.addItem(item)
        
        # Populate styles
        self._styles_list.clear()
        # Add "Native (System Default)" option
        native_item = QListWidgetItem(tr("Native (System Default)"))
        native_item.setData(Qt.ItemDataRole.UserRole, "")
        native_item.setCheckState(Qt.CheckState.Unchecked)
        if self._current_style == "":
            native_item.setCheckState(Qt.CheckState.Checked)
            self._styles_list.setCurrentItem(native_item)
        self._styles_list.addItem(native_item)
        
        # Add other styles
        for style_name in sorted(self._available_styles):
            item = QListWidgetItem(style_name)
            item.setData(Qt.ItemDataRole.UserRole, style_name)
            item.setCheckState(Qt.CheckState.Unchecked)
            if self._current_style == style_name:
                item.setCheckState(Qt.CheckState.Checked)
                self._styles_list.setCurrentItem(item)
                self._styles_list.scrollToItem(item)
            self._styles_list.addItem(item)
    
    def _filter_items(self, text: str):
        """Filter the theme and style lists based on search text."""
        search_text = text.lower()
        
        # Filter themes
        for i in range(self._themes_list.count()):
            item = self._themes_list.item(i)
            if item:
                item.setHidden(search_text not in item.text().lower())
        
        # Filter styles
        for i in range(self._styles_list.count()):
            item = self._styles_list.item(i)
            if item:
                item.setHidden(search_text not in item.text().lower())
    
    def _on_theme_selected(self, item: QListWidgetItem):
        """Handle theme selection."""
        # Uncheck all themes
        for i in range(self._themes_list.count()):
            list_item = self._themes_list.item(i)
            if list_item:
                list_item.setCheckState(Qt.CheckState.Unchecked)
        
        # Check selected theme
        item.setCheckState(Qt.CheckState.Checked)
        
        # Uncheck all styles when theme is selected
        for i in range(self._styles_list.count()):
            list_item = self._styles_list.item(i)
            if list_item:
                list_item.setCheckState(Qt.CheckState.Unchecked)
    
    def _on_style_selected(self, item: QListWidgetItem):
        """Handle style selection."""
        # Uncheck all styles
        for i in range(self._styles_list.count()):
            list_item = self._styles_list.item(i)
            if list_item:
                list_item.setCheckState(Qt.CheckState.Unchecked)
        
        # Check selected style
        item.setCheckState(Qt.CheckState.Checked)
        
        # Uncheck all themes when style is selected
        for i in range(self._themes_list.count()):
            list_item = self._themes_list.item(i)
            if list_item:
                list_item.setCheckState(Qt.CheckState.Unchecked)
    
    def _on_theme_double_clicked(self, item: QListWidgetItem):
        """Handle theme double-click - apply immediately."""
        self._on_theme_selected(item)
        self._apply_selection()
    
    def _on_style_double_clicked(self, item: QListWidgetItem):
        """Handle style double-click - apply immediately."""
        self._on_style_selected(item)
        self._apply_selection()
    
    def _apply_selection(self):
        """Apply the selected theme or style."""
        # Check for selected theme
        for i in range(self._themes_list.count()):
            item = self._themes_list.item(i)
            if item and item.checkState() == Qt.CheckState.Checked:
                theme_name = item.text()
                self.theme_changed.emit(theme_name)
                return
        
        # Check for selected style
        for i in range(self._styles_list.count()):
            item = self._styles_list.item(i)
            if item and item.checkState() == Qt.CheckState.Checked:
                style_name = item.data(Qt.ItemDataRole.UserRole) or ""
                self.style_changed.emit(style_name)
                return
    
    def update_current_selection(self, theme_name: str | None = None, style_name: str | None = None):
        """Update the current selection in the dialog."""
        self._current_theme = theme_name
        self._current_style = style_name
        self._populate_lists()

