from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt, Signal  # pyright: ignore[reportPrivateImportUsage]
from qtpy.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
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
        
        # Setup event filter to prevent scroll wheel interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)
        
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
        themes_header_layout = QHBoxLayout()
        themes_label = QLabel(tr("Themes:"))
        themes_label.setStyleSheet("font-weight: bold; font-size: 12pt; margin-top: 5px;")
        self._current_theme_display = QLineEdit()
        self._current_theme_display.setReadOnly(True)
        self._current_theme_display.setPlaceholderText(tr("No theme selected"))
        self._current_theme_display.setStyleSheet("background-color: palette(base); border: 1px solid palette(mid); padding: 2px;")
        themes_header_layout.addWidget(themes_label)
        themes_header_layout.addWidget(self._current_theme_display, 1)  # Stretch factor 1 to take remaining space
        
        self._themes_list = QListWidget()
        self._themes_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._themes_list.itemClicked.connect(self._on_theme_selected)
        self._themes_list.itemDoubleClicked.connect(self._on_theme_double_clicked)
        self._themes_list.setMinimumHeight(200)
        
        themes_layout = QVBoxLayout()
        themes_layout.setSpacing(5)
        themes_layout.addLayout(themes_header_layout)
        themes_layout.addWidget(self._themes_list)
        main_layout.addLayout(themes_layout)
        
        # Styles section
        styles_header_layout = QHBoxLayout()
        styles_label = QLabel(tr("Application Styles:"))
        styles_label.setStyleSheet("font-weight: bold; font-size: 12pt; margin-top: 5px;")
        self._current_style_display = QLineEdit()
        self._current_style_display.setReadOnly(True)
        self._current_style_display.setPlaceholderText(tr("No style selected"))
        self._current_style_display.setStyleSheet("background-color: palette(base); border: 1px solid palette(mid); padding: 2px;")
        styles_header_layout.addWidget(styles_label)
        styles_header_layout.addWidget(self._current_style_display, 1)  # Stretch factor 1 to take remaining space
        
        self._styles_list = QListWidget()
        self._styles_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._styles_list.itemClicked.connect(self._on_style_selected)
        self._styles_list.itemDoubleClicked.connect(self._on_style_double_clicked)
        self._styles_list.setMaximumHeight(150)
        
        styles_layout = QVBoxLayout()
        styles_layout.setSpacing(5)
        styles_layout.addLayout(styles_header_layout)
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
        # Update current theme display
        if self._current_theme:
            self._current_theme_display.setText(self._current_theme)
        else:
            self._current_theme_display.clear()
        
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
        
        # Update current style display
        if self._current_style == "":
            self._current_style_display.setText(tr("Native (System Default)"))
        elif self._current_style:
            self._current_style_display.setText(self._current_style)
        else:
            self._current_style_display.clear()
        
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
        
        # Update current theme display
        self._current_theme_display.setText(item.text())
    
    def _on_style_selected(self, item: QListWidgetItem):
        """Handle style selection."""
        # Uncheck all styles
        for i in range(self._styles_list.count()):
            list_item = self._styles_list.item(i)
            if list_item:
                list_item.setCheckState(Qt.CheckState.Unchecked)
        
        # Check selected style
        item.setCheckState(Qt.CheckState.Checked)
        
        # Update current style display
        style_display_name = item.text()  # Use the display text (e.g., "Native (System Default)" or style name)
        self._current_style_display.setText(style_display_name)
    
    def _on_theme_double_clicked(self, item: QListWidgetItem):
        """Handle theme double-click - apply immediately."""
        self._on_theme_selected(item)
        self._apply_selection()
    
    def _on_style_double_clicked(self, item: QListWidgetItem):
        """Handle style double-click - apply immediately."""
        self._on_style_selected(item)
        self._apply_selection()
    
    def _apply_selection(self):
        """Apply the selected theme and/or style."""
        # Check for selected theme
        selected_theme = None
        for i in range(self._themes_list.count()):
            item = self._themes_list.item(i)
            if item and item.checkState() == Qt.CheckState.Checked:
                selected_theme = item.text()
                break
        
        # Check for selected style
        selected_style = None
        for i in range(self._styles_list.count()):
            item = self._styles_list.item(i)
            if item and item.checkState() == Qt.CheckState.Checked:
                selected_style = item.data(Qt.ItemDataRole.UserRole) or ""
                break
        
        # Apply theme if selected
        if selected_theme:
            self.theme_changed.emit(selected_theme)
        
        # Apply style if selected
        if selected_style is not None:
            self.style_changed.emit(selected_style)
    
    def update_current_selection(self, theme_name: str | None = None, style_name: str | None = None):
        """Update the current selection in the dialog."""
        self._current_theme = theme_name
        self._current_style = style_name
        self._populate_lists()

