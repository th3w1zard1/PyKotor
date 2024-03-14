from __future__ import annotations

import sys

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QApplication, QComboBox, QDialog, QLabel, QPushButton, QVBoxLayout

from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget


class ResourceTypeDialog(QDialog):
    def __init__(
        self,
        resource_types: list[ResourceType],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Select Resource Type")
        self.resource_types = resource_types
        self.selected_resource = None

        # Create the layout
        layout = QVBoxLayout(self)

        # Add a label
        label = QLabel("Choose the resource type:")
        layout.addWidget(label)

        # Create the combo box and populate it
        self.combo_box = QComboBox(self)
        for rt in resource_types:
            # Display extra information as desired
            display_text = f"{rt.extension.upper()} - {rt.category} ({rt.contents})"
            self.combo_box.addItem(display_text, rt)
        layout.addWidget(self.combo_box)

        # Add a select button
        select_button = QPushButton("Select", self)
        select_button.clicked.connect(self.on_select)
        layout.addWidget(select_button)

    def on_select(self):
        index = self.combo_box.currentIndex()
        self.selected_resource = self.resource_types[index]
        self.accept()

    def get_selected_resource_name(self):
        return self.selected_resource.extension if self.selected_resource else None

# Test Usage
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Pass only the resource types you want the user to choose from
    resource_types_to_select = [ResourceType.BMP, ResourceType.TXT]

    dialog = ResourceTypeDialog(resource_types_to_select)
    res = dialog.exec_()

    if res:
        selected_resource_name = dialog.get_selected_resource_name()
        print(f"Selected Resource Name: {selected_resource_name}")
    else:
        print("Selection canceled")

    sys.exit(app.exec_())