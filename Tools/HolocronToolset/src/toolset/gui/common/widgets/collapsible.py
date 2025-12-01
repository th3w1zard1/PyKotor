"""Collapsible widgets for use in Qt applications.

Provides QGroupBox-based collapsible containers that can be expanded/collapsed
by clicking the checkbox title.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtWidgets import QGroupBox, QSizePolicy, QWidget

if TYPE_CHECKING:
    from qtpy.QtGui import QMouseEvent


class CollapsibleGroupBox(QGroupBox):
    """A QGroupBox that collapses/expands its contents when toggled.
    
    When the group box is unchecked, its contents are hidden and the box
    shrinks to just show the title. When checked, the contents are shown.
    
    Usage:
        groupbox = CollapsibleGroupBox("Section Title")
        groupbox.setCheckable(True)
        groupbox.setChecked(True)  # Start expanded
        layout = QVBoxLayout(groupbox)
        layout.addWidget(some_widget)
    """
    
    def __init__(self, title: str = "", parent: QWidget | None = None):
        super().__init__(title, parent)
        
        # Enable checkable behavior
        self.setCheckable(True)
        self.setChecked(True)
        
        # Connect toggle signal to collapse/expand handler
        self.toggled.connect(self._on_toggled)
        
        # Store the original size policy
        self._original_size_policy: QSizePolicy = self.sizePolicy()

    def _on_toggled(self, checked: bool):
        """Handle the toggled signal to collapse/expand contents."""
        # Iterate through all child widgets and hide/show them
        for i in range(self.layout().count()) if self.layout() else []:
            item = self.layout().itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.setVisible(checked)
            # Also handle nested layouts
            nested_layout = item.layout()
            if nested_layout is not None:
                self._set_layout_visible(nested_layout, checked)
        
        # Adjust size policy when collapsed
        if checked:
            self.setSizePolicy(self._original_size_policy)
        else:
            policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
            self.setSizePolicy(policy)
        
        # Update geometry
        self.updateGeometry()
        if self.parent() is not None:
            parent = self.parent()
            if isinstance(parent, QWidget):
                parent.updateGeometry()

    def _set_layout_visible(self, layout, visible: bool):
        """Recursively set visibility of layout items."""
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.setVisible(visible)
            nested = item.layout()
            if nested is not None:
                self._set_layout_visible(nested, visible)

    def setChecked(self, b: bool):  # noqa: N802
        """Override setChecked to trigger collapse/expand."""
        super().setChecked(b)
        # Also trigger the toggle handler for initial state
        self._on_toggled(b)

    def mouseDoubleClickEvent(self, a0: QMouseEvent):
        """Allow double-click on title bar to toggle."""
        # Only toggle if the double-click is in the title area
        if a0.y() < 30:  # Approximate title bar height
            self.setChecked(not self.isChecked())
        super().mouseDoubleClickEvent(a0)

