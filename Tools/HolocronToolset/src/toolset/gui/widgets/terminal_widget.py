"""Integrated terminal widget for Holocron Toolset.

This widget runs a single long-lived shell process and streams input/output.
We intentionally avoid “fake prompts” and “one process per command” execution,
because that causes discrepancies (aliases, profiles, environment/state).
"""

from __future__ import annotations

import os
import shutil
import sys

from typing import TYPE_CHECKING

from qtpy.QtCore import QProcess, Qt, Signal  # pyright: ignore[reportPrivateImportUsage]
from qtpy.QtGui import QFont, QTextCursor  # pyright: ignore[reportPrivateImportUsage]
from qtpy.QtWidgets import QLineEdit, QPlainTextEdit, QVBoxLayout, QWidget  # pyright: ignore[reportPrivateImportUsage]

if TYPE_CHECKING:
    from qtpy.QtCore import QByteArray  # pyright: ignore[reportPrivateImportUsage]


class TerminalWidget(QWidget):
    """A lightweight integrated terminal backed by a real shell."""

    command_executed: Signal = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._working_dir: str = os.getcwd()
        self._command_history: list[str] = []
        self._history_index: int = -1
        self._setup_ui()
        self._setup_process()
        self._start_shell()

    def _setup_ui(self):
        """Set up the terminal UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Output display
        self.terminal_output: QPlainTextEdit = QPlainTextEdit(self)
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setUndoRedoEnabled(False)
        self.terminal_output.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.terminal_output.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.terminal_output.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Set terminal-like font
        font = QFont("Consolas" if sys.platform == "win32" else "Monaco", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.terminal_output.setFont(font)

        # Apply terminal color scheme (VSCode dark theme style)
        self._apply_terminal_theme()

        # Input line
        self.terminal_input: QLineEdit = QLineEdit(self)
        self.terminal_input.setFont(font)
        self.terminal_input.returnPressed.connect(self._on_enter_pressed)
        self.terminal_input.installEventFilter(self)

        layout.addWidget(self.terminal_output)
        layout.addWidget(self.terminal_input)
        self.setLayout(layout)

        self._write_output("Holocron Toolset Terminal\n\n")

    def _apply_terminal_theme(self):
        """Apply a theme that respects the current application palette."""
        self.terminal_output.setStyleSheet("""
            QPlainTextEdit {
                background-color: palette(base);
                color: palette(text);
                border: none;
                padding: 8px;
                selection-background-color: palette(highlight);
                selection-color: palette(highlighted-text);
            }
            QScrollBar:vertical {
                background-color: palette(base);
                width: 14px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: palette(mid);
                min-height: 30px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: palette(dark);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        self.terminal_input.setStyleSheet("""
            QLineEdit {
                background-color: palette(base);
                color: palette(text);
                border: none;
                padding: 6px 8px;
                selection-background-color: palette(highlight);
                selection-color: palette(highlighted-text);
            }
        """)

    def _setup_process(self):
        """Set up the process for shell execution."""
        self.process: QProcess = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)  # type: ignore[attr-defined]
        self.process.readyReadStandardOutput.connect(self._handle_stdout)
        # stderr is merged, but keep for compatibility across Qt bindings
        self.process.readyReadStandardError.connect(self._handle_stdout)
        self.process.finished.connect(self._handle_process_finished)

    def set_working_directory(self, path: str) -> None:
        """Set the initial working directory for the shell (applies on next start)."""
        self._working_dir = path

    def _write_output(self, text: str):
        """Write text to the terminal output.

        Args:
        ----
            text: str: The text to write
        """
        # Move cursor to end before appending
        cursor = self.terminal_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.terminal_output.setTextCursor(cursor)

        # Insert text with proper encoding handling
        try:
            # Handle different encoding scenarios
            if isinstance(text, bytes):
                text = text.decode("utf-8", errors="replace")
            self.terminal_output.insertPlainText(text)
        except (UnicodeDecodeError, AttributeError):
            # Fallback to replace errors
            text_str = str(text)
            self.terminal_output.insertPlainText(text_str)

        # Ensure we scroll to the bottom
        self.terminal_output.ensureCursorVisible()

    def eventFilter(self, obj, event):  # noqa: N802
        # Basic command history navigation on the input line.
        if obj is self.terminal_input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Up:
                if self._command_history and self._history_index > 0:
                    self._history_index -= 1
                    self.terminal_input.setText(self._command_history[self._history_index])
                return True
            if event.key() == Qt.Key.Key_Down:
                if self._command_history:
                    if self._history_index < len(self._command_history) - 1:
                        self._history_index += 1
                        self.terminal_input.setText(self._command_history[self._history_index])
                    else:
                        self._history_index = len(self._command_history)
                        self.terminal_input.clear()
                return True
            if event.key() == Qt.Key.Key_L and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                self.clear()
                return True
        return super().eventFilter(obj, event)

    def _on_enter_pressed(self) -> None:
        command = self.terminal_input.text()
        self.terminal_input.clear()

        if not command.strip():
            self._send_to_shell("\n")
            return

        self.command_executed.emit(command)
        self._command_history.append(command)
        self._history_index = len(self._command_history)
        self._send_to_shell(command + "\n")

    def _send_to_shell(self, text: str) -> None:
        if self.process.state() != QProcess.ProcessState.Running:
            self._write_output("\n[terminal] shell is not running\n")
            return
        # Keep it simple: UTF-8 input (most modern shells can handle it; pwsh does by default).
        self.process.write(text.replace("\n", os.linesep).encode("utf-8", errors="replace"))

    def _start_shell(self) -> None:
        if self.process.state() == QProcess.ProcessState.Running:
            return
        program, args = self._get_shell_program()
        self.process.setWorkingDirectory(self._working_dir)
        self._write_output(f"[terminal] starting: {program} {' '.join(args)}\n")
        self.process.start(program, args)
        if not self.process.waitForStarted(5000):
            self._write_output("[terminal] Error: failed to start shell process\n")
            return
        # Trigger initial prompt/output.
        self._send_to_shell("\n")

    def _handle_stdout(self):
        """Handle stdout from the process."""
        data: QByteArray = self.process.readAllStandardOutput()
        try:
            # Try UTF-8 first, then fall back to system encoding
            text = bytes(data).decode("utf-8", errors="replace")
        except (UnicodeDecodeError, AttributeError):
            try:
                text = bytes(data).decode(sys.getdefaultencoding(), errors="replace")
            except (UnicodeDecodeError, AttributeError):
                text = str(data)

        self._write_output(text)

    def _handle_process_finished(self, exit_code: int, exit_status):
        """Handle process finishing.

        Args:
        ----
            exit_code: int: The process exit code
            exit_status: The exit status
        """
        self._write_output(f"\n[terminal] process exited with code {exit_code}\n")

    def clear(self):
        """Clear the terminal."""
        self.terminal_output.clear()
        self._write_output("Holocron Toolset Terminal\n\n")

    def write_message(self, message: str, color: str | None = None):
        """Write a message to the terminal.

        Args:
        ----
            message: str: The message to write
            color: str | None: Optional color name
        """
        self._write_output(f"\n{message}\n")

    def execute_command_silently(self, command: str):
        """Execute a command without showing it in the terminal.

        Args:
        ----
            command: str: The command to execute
        """
        self._send_to_shell(command + "\n")

    def _get_shell_program(self) -> tuple[str, list[str]]:
        """Return the interactive shell program + arguments."""
        override = os.environ.get("PYKOTOR_TERMINAL_SHELL", "").strip()
        if override:
            return override, []

        if sys.platform == "win32":
            pwsh = shutil.which("pwsh")
            if pwsh:
                return pwsh, ["-NoLogo"]
            powershell = shutil.which("powershell")
            if powershell:
                return powershell, ["-NoLogo", "-NoExit"]
            comspec = os.environ.get("COMSPEC", "cmd.exe")
            return comspec, []

        shell = os.environ.get("SHELL", "").strip()
        if shell:
            return shell, ["-i"]
        bash = shutil.which("bash")
        if bash:
            return bash, ["-i"]
        sh = shutil.which("sh") or "/bin/sh"
        return sh, ["-i"]
