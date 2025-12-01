"""Dialog for choosing between Blender and built-in editor.

This dialog is shown when the user opens a module/GIT and Blender is available,
allowing them to choose which editor to use.
"""

from __future__ import annotations

import platform
from pathlib import Path
from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
)

from toolset.blender import BlenderInfo, detect_blender, get_blender_settings
from toolset.blender.detection import (
    check_kotorblender_installed,
    find_all_blender_installations,
    install_kotorblender,
)

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


class BlenderChoiceDialog(QDialog):
    """Dialog for choosing between Blender and built-in editor.

    Shows when:
    - Blender is detected
    - kotorblender is installed
    - User hasn't chosen to remember their preference
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        blender_info: BlenderInfo | None = None,
        context: str = "Module Designer",
    ):
        super().__init__(parent)

        self._blender_info = blender_info or detect_blender()
        self._all_installations: list[BlenderInfo] = []
        self._context = context
        self._choice: str = "builtin"  # "blender" or "builtin"
        self._info_frame: QFrame | None = None
        self._install_button: QPushButton | None = None
        self._warning_label: QLabel | None = None
        self._install_hint_label: QLabel | None = None

        self._setup_ui()

    @property
    def choice(self) -> str:
        """Get the user's choice: 'blender' or 'builtin'."""
        return self._choice

    @property
    def remember_choice(self) -> bool:
        """Check if user wants to remember their choice."""
        return self._remember_checkbox.isChecked()

    def _setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle("Choose Editor")
        self.setMinimumWidth(500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Blender detection info
        self._info_frame = QFrame()
        self._info_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self._info_layout = QVBoxLayout(self._info_frame)

        self._update_blender_info_display()

        layout.addWidget(self._info_frame)

        # Question
        question_label = QLabel(
            f"<b>How would you like to open the {self._context}?</b>"
        )
        question_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(question_label)

        # Choice buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(16)

        # Blender button
        self._blender_button = QPushButton()
        self._blender_button.setText("Open in Blender\n(Recommended)")
        self._blender_button.setMinimumHeight(60)
        self._update_blender_button_state()
        self._blender_button.clicked.connect(self._choose_blender)
        buttons_layout.addWidget(self._blender_button)

        # Built-in button
        self._builtin_button = QPushButton()
        self._builtin_button.setText("Use Built-in Editor")
        self._builtin_button.setMinimumHeight(60)
        self._builtin_button.clicked.connect(self._choose_builtin)
        self._builtin_button.setToolTip(
            "Use the built-in PyKotorGL renderer.\n"
            "Integrated experience, no external application needed."
        )
        buttons_layout.addWidget(self._builtin_button)

        layout.addLayout(buttons_layout)

        # Feature comparison
        comparison_label = QLabel(
            "<table cellspacing='8'>"
            "<tr><th align='left'></th><th>Blender</th><th>Built-in</th></tr>"
            "<tr><td>Performance</td><td>⭐⭐⭐</td><td>⭐</td></tr>"
            "<tr><td>3D Navigation</td><td>⭐⭐⭐</td><td>⭐⭐</td></tr>"
            "<tr><td>Model Editing</td><td>⭐⭐⭐</td><td>❌</td></tr>"
            "<tr><td>Lightmap Baking</td><td>⭐⭐⭐</td><td>❌</td></tr>"
            "<tr><td>Integration</td><td>⭐⭐</td><td>⭐⭐⭐</td></tr>"
            "</table>"
        )
        comparison_label.setStyleSheet("color: #666; font-size: 11px;")
        comparison_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(comparison_label)

        # Remember choice
        self._remember_checkbox = QCheckBox("Remember my choice")
        self._remember_checkbox.setToolTip(
            "Don't show this dialog again. You can change this in Settings."
        )
        layout.addWidget(self._remember_checkbox, alignment=Qt.AlignCenter)

        # Cancel button
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button, alignment=Qt.AlignRight)

    def _update_blender_info_display(self):
        """Update the Blender info display based on current state."""
        # Clear existing widgets
        while self._info_layout.count():
            item = self._info_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Clear nested layouts
                while item.layout().count():
                    nested_item = item.layout().takeAt(0)
                    if nested_item.widget():
                        nested_item.widget().deleteLater()

        if self._blender_info.is_valid:
            # Blender found - show status
            status_label = QLabel(
                f"<b>Blender {self._blender_info.version_string}</b> detected"
            )
            status_label.setStyleSheet("color: #4CAF50;")  # Green
            self._info_layout.addWidget(status_label)

            path_label = QLabel(f"<small>{self._blender_info.executable}</small>")
            path_label.setWordWrap(True)
            path_label.setStyleSheet("color: #888;")
            self._info_layout.addWidget(path_label)

            if self._blender_info.has_kotorblender:
                # kotorblender installed - all good
                addon_label = QLabel(
                    f"<b>kotorblender {self._blender_info.kotorblender_version}</b> installed"
                )
                addon_label.setStyleSheet("color: #4CAF50;")
                self._info_layout.addWidget(addon_label)
            else:
                # kotorblender missing - show warning and install option
                self._warning_label = QLabel(
                    "<span style='color: #FF9800;'><b>Warning:</b> kotorblender not found</span>"
                )
                self._info_layout.addWidget(self._warning_label)

                self._install_hint_label = QLabel(
                    "<small>kotorblender is required to use Blender. Install it to enable the Blender option.</small>"
                )
                self._install_hint_label.setWordWrap(True)
                self._install_hint_label.setStyleSheet("color: #888;")
                self._info_layout.addWidget(self._install_hint_label)

                # Install buttons
                install_button_layout = QHBoxLayout()
                install_button_layout.addStretch()
                
                self._install_button = QPushButton("Install kotorblender")
                self._install_button.clicked.connect(self._install_kotorblender)
                self._install_button.setToolTip("Automatically install kotorblender from bundled source")
                install_button_layout.addWidget(self._install_button)
                
                browse_addon_btn = QPushButton("Browse...")
                browse_addon_btn.clicked.connect(self._browse_kotorblender)
                browse_addon_btn.setToolTip("Manually select kotorblender folder (io_scene_kotor)")
                install_button_layout.addWidget(browse_addon_btn)
                
                install_button_layout.addStretch()
                self._info_layout.addLayout(install_button_layout)

            # Show other installations if available
            self._all_installations = find_all_blender_installations()
            if len(self._all_installations) > 1:
                self._add_installation_selector()

        else:
            # No Blender found - show error and browse option
            error_label = QLabel(
                "<span style='color: #f44336;'><b>Blender not found</b></span>"
            )
            self._info_layout.addWidget(error_label)

            hint_label = QLabel(
                "<small>Install Blender 3.6 or later, or browse to an existing installation.</small>"
            )
            hint_label.setWordWrap(True)
            hint_label.setStyleSheet("color: #888;")
            self._info_layout.addWidget(hint_label)

            # Browse button
            browse_layout = QHBoxLayout()
            browse_layout.addStretch()
            
            browse_btn = QPushButton("Browse for Blender...")
            browse_btn.clicked.connect(self._browse_blender)
            browse_layout.addWidget(browse_btn)
            
            browse_layout.addStretch()
            self._info_layout.addLayout(browse_layout)

    def _add_installation_selector(self):
        """Add a combo box to select from multiple Blender installations."""
        selector_layout = QHBoxLayout()
        
        selector_label = QLabel("<small>Other installations:</small>")
        selector_label.setStyleSheet("color: #888;")
        selector_layout.addWidget(selector_label)
        
        self._installation_combo = QComboBox()
        self._installation_combo.setMaximumWidth(300)
        
        for info in self._all_installations:
            label = f"Blender {info.version_string}"
            if info.has_kotorblender:
                label += f" (kotorblender {info.kotorblender_version})"
            label += f" - {info.executable.parent.name}"
            self._installation_combo.addItem(label)
        
        # Select the current one
        for i, info in enumerate(self._all_installations):
            if info.executable == self._blender_info.executable:
                self._installation_combo.setCurrentIndex(i)
                break
        
        self._installation_combo.currentIndexChanged.connect(self._on_installation_changed)
        selector_layout.addWidget(self._installation_combo)
        selector_layout.addStretch()
        
        self._info_layout.addLayout(selector_layout)

    def _on_installation_changed(self, index: int):
        """Handle selection of a different Blender installation."""
        if 0 <= index < len(self._all_installations):
            self._blender_info = self._all_installations[index]
            self._update_blender_info_display()
            self._update_blender_button_state()

    def _update_blender_button_state(self):
        """Update the Blender button enabled state and tooltip."""
        is_enabled = self._blender_info.is_valid and self._blender_info.has_kotorblender
        self._blender_button.setEnabled(is_enabled)
        
        if self._blender_info.has_kotorblender:
            tooltip = (
                "Use Blender for professional-grade 3D editing with full kotorblender support.\n"
                "Better performance, more features, industry-standard tools."
            )
        elif self._blender_info.is_valid:
            tooltip = (
                "kotorblender is required to use Blender.\n"
                "Click 'Install kotorblender' above to install it."
            )
        else:
            tooltip = (
                "Blender is not installed or not found.\n"
                "Click 'Browse for Blender...' above to locate it."
            )
        self._blender_button.setToolTip(tooltip)

    def _choose_blender(self):
        """User chose Blender."""
        self._choice = "blender"
        self.accept()

    def _choose_builtin(self):
        """User chose built-in editor."""
        self._choice = "builtin"
        self.accept()

    def _browse_blender(self):
        """Browse for Blender executable."""
        system = platform.system()
        
        if system == "Windows":
            file_filter = "Blender Executable (blender.exe);;All Files (*)"
            start_dir = "C:\\Program Files\\Blender Foundation"
        elif system == "Darwin":
            file_filter = "Blender Application (*.app);;All Files (*)"
            start_dir = "/Applications"
        else:
            file_filter = "Blender Executable (blender);;All Files (*)"
            start_dir = "/usr/bin"
        
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Blender Executable",
            start_dir,
            file_filter,
        )
        
        if path:
            # Try to detect this Blender
            new_info = detect_blender(path)
            if new_info.is_valid:
                self._blender_info = new_info
                self._update_blender_info_display()
                self._update_blender_button_state()
            else:
                QMessageBox.warning(
                    self,
                    "Invalid Blender",
                    f"Could not detect valid Blender at:\n{path}\n\n{new_info.error}",
                )

    def _browse_kotorblender(self):
        """Browse for kotorblender source folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select kotorblender folder (io_scene_kotor)",
            "",
            QFileDialog.ShowDirsOnly,
        )
        
        if folder:
            folder_path = Path(folder)
            # Verify it's a valid kotorblender source
            if (folder_path / "__init__.py").is_file():
                self._install_kotorblender(source_path=folder_path)
            else:
                QMessageBox.warning(
                    self,
                    "Invalid kotorblender folder",
                    f"The selected folder does not appear to be a valid kotorblender source.\n\n"
                    f"Expected to find __init__.py in:\n{folder}\n\n"
                    f"Please select the 'io_scene_kotor' folder from the kotorblender download.",
                )

    def _install_kotorblender(self, source_path: Path | None = None):
        """Install kotorblender addon."""
        # Disable button during installation
        if self._install_button:
            self._install_button.setEnabled(False)
            self._install_button.setText("Installing...")

        try:
            success, message = install_kotorblender(self._blender_info, source_path)

            if success:
                # Update UI
                self._update_blender_info_display()
                self._update_blender_button_state()

                QMessageBox.information(
                    self,
                    "Installation Successful",
                    message,
                )
            else:
                QMessageBox.warning(
                    self,
                    "Installation Failed",
                    message,
                )
                # Re-enable button
                if self._install_button:
                    self._install_button.setEnabled(True)
                    self._install_button.setText("Install kotorblender")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Installation Error",
                f"An error occurred while installing kotorblender:\n\n{e!s}",
            )
            # Re-enable button
            if self._install_button:
                self._install_button.setEnabled(True)
                self._install_button.setText("Install kotorblender")


def show_blender_choice_dialog(
    parent: QWidget | None = None,
    context: str = "Module Designer",
) -> tuple[str, bool]:
    """Show the Blender choice dialog and return the user's selection.

    Args:
        parent: Parent widget
        context: Context name for the dialog (e.g., "Module Designer", "GIT Editor")

    Returns:
        Tuple of (choice, remember) where choice is "blender" or "builtin",
        and remember is True if user wants to save the preference.
        Returns ("cancelled", False) if dialog was cancelled.
    """
    settings = get_blender_settings()

    # Check if user has a remembered preference
    if settings.remember_choice:
        return ("blender" if settings.prefer_blender else "builtin", True)

    # Check if Blender is available
    blender_info = settings.get_blender_info()
    
    # Always show dialog if Blender is detected (even without kotorblender)
    # This allows user to see the option and install kotorblender if needed
    if not blender_info.is_valid:
        # No Blender available, use built-in without showing dialog
        return ("builtin", False)

    # Show dialog (will inform user if kotorblender is missing)
    dialog = BlenderChoiceDialog(parent, blender_info, context)
    result = dialog.exec_()

    if result == QDialog.Accepted:
        # Update settings if user wants to remember
        if dialog.remember_choice:
            settings.remember_choice = True
            settings.prefer_blender = (dialog.choice == "blender")

        return (dialog.choice, dialog.remember_choice)

    return ("cancelled", False)


class BlenderConnectionWidget(QFrame):
    """Widget showing Blender connection status.

    Can be added to status bar or toolbar of editors.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._connected = False
        self._setup_ui()

    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        # Status indicator
        self._indicator = QLabel("●")
        self._indicator.setStyleSheet("color: #f44336;")  # Red by default
        layout.addWidget(self._indicator)

        # Status text
        self._status_label = QLabel("Disconnected")
        self._status_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(self._status_label)

        # Connect button
        self._connect_button = QPushButton("Connect")
        self._connect_button.setMaximumHeight(22)
        self._connect_button.clicked.connect(self._on_connect_clicked)
        layout.addWidget(self._connect_button)

    def set_connected(self, connected: bool):
        """Update connection status display."""
        self._connected = connected

        if connected:
            self._indicator.setStyleSheet("color: #4CAF50;")  # Green
            self._status_label.setText("Connected to Blender")
            self._connect_button.setText("Disconnect")
        else:
            self._indicator.setStyleSheet("color: #f44336;")  # Red
            self._status_label.setText("Disconnected")
            self._connect_button.setText("Connect")

    def set_connecting(self):
        """Show connecting status."""
        self._indicator.setStyleSheet("color: #FF9800;")  # Orange
        self._status_label.setText("Connecting...")
        self._connect_button.setEnabled(False)

    def set_error(self, message: str):
        """Show error status."""
        self._indicator.setStyleSheet("color: #f44336;")  # Red
        self._status_label.setText(f"Error: {message}")
        self._connect_button.setEnabled(True)
        self._connect_button.setText("Retry")

    def _on_connect_clicked(self):
        """Handle connect/disconnect button click."""
        # This will be connected to the controller by the parent window
        pass


class BlenderSettingsWidget(QFrame):
    """Widget for Blender integration settings.

    Can be added to the settings dialog.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._blender_info: BlenderInfo | None = None
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Setup the widget UI."""
        from qtpy.QtWidgets import QLineEdit, QSpinBox

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Title
        title = QLabel("<b>Blender Integration</b>")
        layout.addWidget(title)

        # Blender path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Blender Path:"))

        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("Auto-detect")
        self._path_edit.textChanged.connect(self._on_path_changed)
        path_layout.addWidget(self._path_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_blender)
        path_layout.addWidget(browse_btn)

        detect_btn = QPushButton("Detect")
        detect_btn.clicked.connect(self._detect_blender)
        path_layout.addWidget(detect_btn)

        layout.addLayout(path_layout)

        # Status display
        self._status_label = QLabel()
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        # kotorblender install button (shown only when Blender found but kotorblender missing)
        self._install_kotorblender_btn = QPushButton("Install kotorblender")
        self._install_kotorblender_btn.clicked.connect(self._install_kotorblender)
        self._install_kotorblender_btn.setVisible(False)
        layout.addWidget(self._install_kotorblender_btn)

        # Options
        self._prefer_blender_cb = QCheckBox("Prefer Blender when available")
        self._prefer_blender_cb.setToolTip(
            "Automatically use Blender for Module Designer, GIT Editor, etc."
        )
        layout.addWidget(self._prefer_blender_cb)

        self._remember_cb = QCheckBox("Remember editor choice")
        self._remember_cb.setToolTip("Don't ask which editor to use each time")
        layout.addWidget(self._remember_cb)

        # Port setting
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("IPC Port:"))

        self._port_spin = QSpinBox()
        self._port_spin.setRange(1024, 65535)
        self._port_spin.setValue(7531)
        port_layout.addWidget(self._port_spin)
        port_layout.addStretch()

        layout.addLayout(port_layout)

        # Update status
        self._update_status()

    def _load_settings(self):
        """Load current settings."""
        settings = get_blender_settings()

        self._path_edit.setText(settings.custom_path)
        self._prefer_blender_cb.setChecked(settings.prefer_blender)
        self._remember_cb.setChecked(settings.remember_choice)
        self._port_spin.setValue(settings.ipc_port)

    def save_settings(self):
        """Save settings to the settings object."""
        settings = get_blender_settings()

        settings.custom_path = self._path_edit.text()
        settings.prefer_blender = self._prefer_blender_cb.isChecked()
        settings.remember_choice = self._remember_cb.isChecked()
        settings.ipc_port = self._port_spin.value()

    def _on_path_changed(self):
        """Handle path text change."""
        self._update_status()

    def _browse_blender(self):
        """Browse for Blender executable."""
        system = platform.system()
        
        if system == "Windows":
            file_filter = "Blender Executable (blender.exe);;All Files (*)"
        elif system == "Darwin":
            file_filter = "Blender Application (*.app);;All Files (*)"
        else:
            file_filter = "Blender Executable (blender);;All Files (*)"

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Blender Executable",
            "",
            file_filter,
        )

        if path:
            self._path_edit.setText(path)
            self._update_status()

    def _detect_blender(self):
        """Auto-detect Blender installation."""
        self._path_edit.clear()
        self._update_status()

    def _update_status(self):
        """Update the status display."""
        custom_path = self._path_edit.text() or None
        self._blender_info = detect_blender(custom_path)

        if self._blender_info.is_valid:
            status = f"<span style='color: #4CAF50;'>✓ Blender {self._blender_info.version_string} found</span>"

            if self._blender_info.has_kotorblender:
                status += f"<br><span style='color: #4CAF50;'>✓ kotorblender {self._blender_info.kotorblender_version} installed</span>"
                self._install_kotorblender_btn.setVisible(False)
            else:
                status += "<br><span style='color: #FF9800;'>⚠ kotorblender not found</span>"
                self._install_kotorblender_btn.setVisible(True)

            status += f"<br><small>{self._blender_info.executable}</small>"
        else:
            status = f"<span style='color: #f44336;'>✗ {self._blender_info.error}</span>"
            self._install_kotorblender_btn.setVisible(False)

        self._status_label.setText(status)

    def _install_kotorblender(self):
        """Install kotorblender addon."""
        if not self._blender_info or not self._blender_info.is_valid:
            return

        self._install_kotorblender_btn.setEnabled(False)
        self._install_kotorblender_btn.setText("Installing...")

        try:
            success, message = install_kotorblender(self._blender_info)

            if success:
                QMessageBox.information(self, "Installation Successful", message)
                self._update_status()
            else:
                QMessageBox.warning(self, "Installation Failed", message)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Installation Error",
                f"An error occurred while installing kotorblender:\n\n{e!s}",
            )
        finally:
            self._install_kotorblender_btn.setEnabled(True)
            self._install_kotorblender_btn.setText("Install kotorblender")
