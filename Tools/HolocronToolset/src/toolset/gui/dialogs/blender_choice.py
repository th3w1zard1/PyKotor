"""Dialog for choosing between Blender and built-in editor.

This dialog is shown when the user opens a module/GIT and Blender is available,
allowing them to choose which editor to use.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
)

from toolset.blender import BlenderInfo, detect_blender, get_blender_settings

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
        self._context = context
        self._choice: str = "builtin"  # "blender" or "builtin"

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
        self.setMinimumWidth(450)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Blender detection info
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        info_layout = QVBoxLayout(info_frame)

        if self._blender_info.is_valid:
            status_label = QLabel(
                f"<b>Blender {self._blender_info.version_string}</b> detected"
            )
            status_label.setStyleSheet("color: #4CAF50;")  # Green
            info_layout.addWidget(status_label)

            path_label = QLabel(f"<small>{self._blender_info.executable}</small>")
            path_label.setWordWrap(True)
            path_label.setStyleSheet("color: #888;")
            info_layout.addWidget(path_label)

            if self._blender_info.has_kotorblender:
                addon_label = QLabel(
                    f"<b>kotorblender {self._blender_info.kotorblender_version}</b> installed"
                )
                addon_label.setStyleSheet("color: #4CAF50;")
                info_layout.addWidget(addon_label)
            else:
                addon_label = QLabel(
                    "<span style='color: #FF9800;'><b>Warning:</b> kotorblender not found</span>"
                )
                info_layout.addWidget(addon_label)

                install_hint = QLabel(
                    "<small>Install kotorblender from DeadlyStream for full functionality</small>"
                )
                install_hint.setWordWrap(True)
                install_hint.setStyleSheet("color: #888;")
                info_layout.addWidget(install_hint)

        layout.addWidget(info_frame)

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
        self._blender_button.setEnabled(
            self._blender_info.is_valid and self._blender_info.has_kotorblender
        )
        self._blender_button.clicked.connect(self._choose_blender)
        self._blender_button.setToolTip(
            "Use Blender for professional-grade 3D editing with full kotorblender support.\n"
            "Better performance, more features, industry-standard tools."
        )
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

    def _choose_blender(self):
        """User chose Blender."""
        self._choice = "blender"
        self.accept()

    def _choose_builtin(self):
        """User chose built-in editor."""
        self._choice = "builtin"
        self.accept()


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

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Title
        title = QLabel("<b>Blender Integration</b>")
        layout.addWidget(title)

        # Blender path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Blender Path:"))

        from qtpy.QtWidgets import QLineEdit

        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("Auto-detect")
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

        from qtpy.QtWidgets import QSpinBox

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

    def _browse_blender(self):
        """Browse for Blender executable."""
        from qtpy.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Blender Executable",
            "",
            "Blender (blender.exe blender);;All Files (*)",
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
        info = detect_blender(custom_path)

        if info.is_valid:
            status = f"<span style='color: #4CAF50;'>✓ Blender {info.version_string} found</span>"

            if info.has_kotorblender:
                status += f"<br><span style='color: #4CAF50;'>✓ kotorblender {info.kotorblender_version} installed</span>"
            else:
                status += "<br><span style='color: #FF9800;'>⚠ kotorblender not found</span>"

            status += f"<br><small>{info.executable}</small>"
        else:
            status = f"<span style='color: #f44336;'>✗ {info.error}</span>"

        self._status_label.setText(status)

