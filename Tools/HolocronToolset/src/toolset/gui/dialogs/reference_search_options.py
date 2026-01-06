"""Dialog for configuring reference search options.

This dialog allows users to configure search parameters for finding references
to scripts, tags, resrefs, conversations, and other values.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from toolset.utils.reference_search_config import get_all_searchable_file_types

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


class ReferenceSearchOptions(QDialog):
    """Dialog for configuring reference search options."""

    def __init__(
        self,
        parent: QWidget | None,
        default_partial_match: bool = False,
        default_case_sensitive: bool = False,
        default_file_pattern: str = "",
        default_file_types: set[str] | None = None,
    ):
        """Initialize the reference search options dialog.

        Args:
        ----
            parent: Parent widget
            default_partial_match: Default value for partial match checkbox
            default_case_sensitive: Default value for case sensitive checkbox
            default_file_pattern: Default file pattern text
            default_file_types: Default set of file types to search
        """
        super().__init__(parent)
        self.setWindowTitle("Reference Search Options")
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowCloseButtonHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        layout = QVBoxLayout(self)

        # Search options group
        options_group = QGroupBox("Search Options")
        options_layout = QVBoxLayout()
        self.partial_match_check = QCheckBox("Partial match")
        self.partial_match_check.setChecked(default_partial_match)
        self.partial_match_check.setToolTip("Allow partial matches (e.g., 'test' matches 'testscript')")
        options_layout.addWidget(self.partial_match_check)

        self.case_sensitive_check = QCheckBox("Case sensitive")
        self.case_sensitive_check.setChecked(default_case_sensitive)
        self.case_sensitive_check.setToolTip("Perform case-sensitive matching")
        options_layout.addWidget(self.case_sensitive_check)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # File pattern group
        pattern_group = QGroupBox("File Pattern (optional)")
        pattern_layout = QVBoxLayout()
        pattern_label = QLabel("Filter results by filename pattern (e.g., *.mod, *_s.rim):")
        pattern_layout.addWidget(pattern_label)
        self.file_pattern_edit = QLineEdit()
        self.file_pattern_edit.setText(default_file_pattern)
        self.file_pattern_edit.setPlaceholderText("Leave empty to search all files")
        pattern_layout.addWidget(self.file_pattern_edit)
        pattern_group.setLayout(pattern_layout)
        layout.addWidget(pattern_group)

        # File types group
        types_group = QGroupBox("File Types")
        types_layout = QVBoxLayout()
        types_label = QLabel("Select file types to search (leave all unchecked to search all types):")
        types_layout.addWidget(types_label)

        # Create checkboxes for each searchable file type
        self.file_type_checks: dict[str, QCheckBox] = {}
        all_types = sorted(get_all_searchable_file_types())
        for file_type in all_types:
            check = QCheckBox(file_type)
            if default_file_types is None or file_type in default_file_types:
                check.setChecked(True)
            self.file_type_checks[file_type] = check
            types_layout.addWidget(check)

        types_group.setLayout(types_layout)
        layout.addWidget(types_group)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_partial_match(self) -> bool:
        """Get the partial match setting."""
        return self.partial_match_check.isChecked()

    def get_case_sensitive(self) -> bool:
        """Get the case sensitive setting."""
        return self.case_sensitive_check.isChecked()

    def get_file_pattern(self) -> str | None:
        """Get the file pattern, or None if empty."""
        pattern = self.file_pattern_edit.text().strip()
        return pattern if pattern else None

    def get_file_types(self) -> set[str] | None:
        """Get the selected file types, or None if all are selected."""
        selected_types = {ftype for ftype, check in self.file_type_checks.items() if check.isChecked()}
        all_types = set(self.file_type_checks.keys())
        # Return None if all types are selected (means "search all")
        return None if selected_types == all_types else selected_types

