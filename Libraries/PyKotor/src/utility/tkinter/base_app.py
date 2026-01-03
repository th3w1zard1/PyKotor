"""Base Tkinter Application Framework for PyKotor tools.

This module provides reusable base classes for creating GUI applications
with a consistent look, feel, and behavior across all PyKotor tools.

Usage:
    from utility.tkinter.base_app import BaseApp

    class MyApp(BaseApp):
        def __init__(self):
            super().__init__(
                title="MyApp",
                version="1.0.0",
                default_width=600,
                default_height=500,
            )

        def initialize_ui_controls(self):
            super().initialize_ui_controls()
            # Add tool-specific UI controls here
"""
from __future__ import annotations

import ctypes
import os
import sys
import time
import tkinter as tk

from abc import ABC, abstractmethod
from pathlib import Path
from threading import Event, Thread
from tkinter import filedialog, font as tkfont, messagebox, ttk
from typing import TYPE_CHECKING, Any

from loggerplus import RobustLogger

from pykotor.tslpatcher.logger import LogType, PatchLogger
from utility.error_handling import universal_simplify_exception

if TYPE_CHECKING:
    from collections.abc import Callable

    from pykotor.tslpatcher.logger import PatchLog


class BaseApp(ABC):
    """Base class for PyKotor GUI applications.

    This class provides common functionality including:
    - Window setup and centering
    - Logging infrastructure (PatchLogger integration)
    - Progress bar management
    - Thread management for background tasks
    - Exit handling
    - Standard UI element styling
    - Exception handling

    Subclasses should override:
    - initialize_ui_controls(): To add tool-specific UI elements
    - get_app_name(): Return the application name for cleanup messages
    """

    def __init__(
        self,
        title: str,
        version: str,
        *,
        default_width: int = 600,
        default_height: int = 500,
        min_width: int | None = None,
        min_height: int | None = None,
        resizable: bool = True,
    ):
        """Initialize the base application.

        Args:
            title: Window title (will be combined with version)
            version: Version string (e.g., "1.0.0" or "v1.0.0")
            default_width: Default window width
            default_height: Default window height
            min_width: Minimum window width (defaults to default_width)
            min_height: Minimum window height (defaults to default_height)
            resizable: Whether the window should be resizable
        """
        self.root = tk.Tk()
        self._version_label = version if version.startswith("v") else f"v{version}"
        self.root.title(f"{title} {self._version_label}")

        self._min_width = min_width or default_width
        self._min_height = min_height or default_height
        self._resizable = resizable

        self.set_window(width=default_width, height=default_height)

        # Map the title bar's X button to our handle_exit_button function
        self.root.protocol("WM_DELETE_WINDOW", self.handle_exit_button)

        # Task/thread state
        self.task_running: bool = False
        self.task_thread: Thread | None = None
        self.simple_thread_event: Event = Event()

        # Logging
        self.pykotor_logger = RobustLogger()
        self.log_level: Any = None  # Tool-specific log level type

        # One-shot mode (for CLI execution)
        self.one_shot: bool = False

        # UI elements (will be populated in initialize_ui_controls)
        self.main_text: tk.Text | None = None
        self.progress_bar: ttk.Progressbar | None = None
        self.progress_value: tk.IntVar | None = None

        # Initialize standard components
        self.initialize_logger()
        self.initialize_ui_controls()

        self.pykotor_logger.debug("Base init complete")

    # =========================================================================
    # Abstract Methods (must be implemented by subclasses)
    # =========================================================================

    @abstractmethod
    def get_app_name(self) -> str:
        """Return the application name for logging/cleanup messages."""
        ...

    # =========================================================================
    # Window Management
    # =========================================================================

    def set_window(
        self,
        width: int,
        height: int,
    ):
        """Configure window size, position (centered), and constraints."""
        # Get screen dimensions
        screen_width: int = self.root.winfo_screenwidth()
        screen_height: int = self.root.winfo_screenheight()

        # Calculate position to center the window
        x_position = int((screen_width / 2) - (width / 2))
        y_position = int((screen_height / 2) - (height / 2))

        # Set the dimensions and position
        self.root.geometry(f"{width}x{height}+{x_position}+{y_position}")
        self.root.resizable(width=self._resizable, height=self._resizable)
        self.root.minsize(width=self._min_width, height=self._min_height)

    def hide_console(self):
        """Hide the console window in GUI mode (Windows only)."""
        if os.name == "nt":
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    # =========================================================================
    # Logging Infrastructure
    # =========================================================================

    def initialize_logger(self):
        """Initialize the PatchLogger and subscribe to log events."""
        self.logger = PatchLogger()
        self.logger.verbose_observable.subscribe(self.write_log)
        self.logger.note_observable.subscribe(self.write_log)
        self.logger.warning_observable.subscribe(self.write_log)
        self.logger.error_observable.subscribe(self.write_log)

    def write_log(
        self,
        log: PatchLog,
    ):
        """Write a log message to the UI and optionally to file.

        Override this in subclasses to customize log handling.
        """
        if self.main_text is None:
            return

        def log_to_tag(this_log: PatchLog) -> str:
            if this_log.log_type == LogType.NOTE:
                return "INFO"
            if this_log.log_type == LogType.VERBOSE:
                return "DEBUG"
            return this_log.log_type.name

        # Write to log file if path defined
        log_file_path = self.get_log_file_path()
        if log_file_path:
            try:
                log_file_path.parent.mkdir(parents=True, exist_ok=True)
                with log_file_path.open("a", encoding="utf-8") as log_file:
                    log_file.write(f"{log.formatted_message}\n")
            except OSError as e:
                RobustLogger().error(f"Failed to write log file at '{log_file_path}': {e.__class__.__name__}: {e}")

        # Write to UI
        try:
            self.main_text.config(state=tk.NORMAL)
            self.main_text.insert(tk.END, log.formatted_message + os.linesep, log_to_tag(log))
            self.main_text.see(tk.END)
            self.main_text.config(state=tk.DISABLED)
        except Exception as e:  # noqa: BLE001
            self.pykotor_logger.error(f"Failed to write log to UI: {e}")

    def get_log_file_path(self) -> Path | None:
        """Return the path to the log file. Override in subclasses."""
        return None

    # =========================================================================
    # UI Initialization
    # =========================================================================

    def initialize_ui_controls(self):
        """Initialize the UI controls.

        Subclasses should call super().initialize_ui_controls() and then
        add their own controls. The base implementation sets up:
        - Grid layout configuration
        - Style configuration for ttk widgets
        - Main text area with scrollbar
        - Progress bar
        - Exit button frame
        """
        # Use grid layout for main window
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Configure style for Combobox
        style = ttk.Style(self.root)
        style.configure("TCombobox", font=("Helvetica", 10), padding=4)

        # Middle area for text and scrollbar
        text_frame = tk.Frame(self.root)
        text_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        # Configure the text widget
        self.main_text = tk.Text(text_frame, wrap=tk.WORD)
        self.main_text.grid(row=0, column=0, sticky="nsew")
        self.set_text_font(self.main_text)

        # Create scrollbar for main frame
        scrollbar = tk.Scrollbar(text_frame, command=self.main_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.main_text.config(yscrollcommand=scrollbar.set)

        # Bottom area for buttons and progress
        bottom_frame = tk.Frame(self.root)
        bottom_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        bottom_frame.grid_columnconfigure(0, weight=1)

        # Progress bar
        self.progress_value = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(bottom_frame, maximum=100, variable=self.progress_value)
        self.progress_bar.pack(side="bottom", fill="x", padx=5, pady=5)

        # Store bottom frame for subclasses to add buttons
        self._bottom_frame = bottom_frame

    def set_text_font(
        self,
        text_widget: tk.Text,
    ):
        """Configure the font and log level tags for a text widget."""
        font_obj = tkfont.Font(font=text_widget.cget("font"))
        font_obj.configure(size=9)
        text_widget.configure(font=font_obj)

        # Define a bold and slightly larger font
        bold_font = tkfont.Font(font=text_widget.cget("font"))
        bold_font.configure(size=10, weight="bold")

        # Standard log level color tags
        text_widget.tag_configure("DEBUG", foreground="#6495ED")  # Cornflower Blue
        text_widget.tag_configure("INFO", foreground="#000000")  # Black
        text_widget.tag_configure("WARNING", foreground="#CC4E00", background="#FFF3E0", font=bold_font)  # Orange
        text_widget.tag_configure("ERROR", foreground="#DC143C", font=bold_font)  # Firebrick
        text_widget.tag_configure("CRITICAL", foreground="#FFFFFF", background="#8B0000", font=bold_font)  # White on Dark Red

    def clear_main_text(self):
        """Clear the main text widget content and tags."""
        if self.main_text is None:
            return
        self.main_text.config(state=tk.NORMAL)
        self.main_text.delete(1.0, tk.END)
        for tag in self.main_text.tag_names():
            if tag not in ["sel"]:
                self.main_text.tag_delete(tag)
        self.main_text.config(state=tk.DISABLED)

    # =========================================================================
    # Progress Bar Management
    # =========================================================================

    def update_progress_bar_directly(
        self,
        value: int = 1,
    ):
        """Update the progress bar value (thread-safe).

        Can be passed as a callback to background tasks.
        """
        self.root.after(0, self._update_progress_value, value)

    def _update_progress_value(
        self,
        value: int = 1,
    ):
        """Actual update to the progress bar, guaranteed to run in the main thread."""
        if self.progress_value is None or self.progress_bar is None:
            return
        new_value = self.progress_value.get() + value
        self.progress_value.set(new_value)
        self.progress_bar["value"] = new_value

    def reset_progress_bar(self, maximum: int = 100):
        """Reset the progress bar to zero with an optional new maximum."""
        if self.progress_bar is None or self.progress_value is None:
            return
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = maximum
        self.progress_value.set(0)

    # =========================================================================
    # Task State Management
    # =========================================================================

    def set_state(
        self,
        *,
        state: bool,
    ):
        """Set the task running state and update UI accordingly.

        When state=True: Disables UI controls and resets progress bar
        When state=False: Re-enables UI controls and resets logger

        Override this in subclasses to disable/enable additional controls.

        Args:
            state: True if task is starting, False if task is ending
        """
        if state:
            self.reset_progress_bar()
            self.task_running = True
        else:
            self.task_running = False
            self.initialize_logger()  # Reset errors/warnings

    def get_buttons_to_disable(self) -> list[ttk.Button | tk.Button]:
        """Return list of buttons to disable during task execution.

        Override in subclasses to return tool-specific buttons.
        """
        return []

    # =========================================================================
    # Exit Handling
    # =========================================================================

    def handle_exit_button(self):
        """Handle exit button click or window close.

        Handles graceful and forced termination of running tasks.
        """
        if not self.task_running or not self.task_thread or not self.task_thread.is_alive():
            print("Goodbye!")
            sys.exit(0)
            return

        # Handle unsafe exit
        if self.task_running and not messagebox.askyesno(
            "Really cancel the current task?",
            "A task is currently running. Exiting now may not be safe. Really continue?",
        ):
            return

        self.simple_thread_event.set()
        time.sleep(1)
        print("Task thread is still alive, attempting force close...")

        i = 0
        while self.task_thread.is_alive():
            try:
                self.task_thread._stop()  # type: ignore[attr-defined]  # noqa: SLF001
                print("Force terminate of task thread succeeded")
            except BaseException as e:  # noqa: BLE001
                self._handle_general_exception(e, "Error stopping task thread", msgbox=False)

            print(f"Task thread is still alive after {i} seconds, waiting...")
            time.sleep(1)
            i += 1
            if i == 2:  # noqa: PLR2004
                break

        if self.task_thread.is_alive():
            print("Failed to stop thread!")

        print("Destroying self")
        self.root.destroy()
        print("Goodbye!")
        sys.exit(0)

    # =========================================================================
    # Exception Handling
    # =========================================================================

    def _handle_general_exception(
        self,
        exc: BaseException,
        custom_msg: str = "Unexpected error.",
        title: str = "",
        *,
        msgbox: bool = True,
    ):
        """Handle an exception with logging and optional messagebox.

        Args:
            exc: The exception that occurred
            custom_msg: Custom message to prepend
            title: Dialog title (defaults to error type name)
            msgbox: Whether to show a messagebox (default True)
        """
        self.pykotor_logger.exception(custom_msg, exc_info=exc)
        error_name, msg = universal_simplify_exception(exc)
        if msgbox:
            messagebox.showerror(
                title or error_name,
                f"{(error_name + os.linesep * 2) if title else ''}{custom_msg}.{os.linesep * 2}{msg}",
            )

    # =========================================================================
    # Combobox Helpers
    # =========================================================================

    def move_cursor_to_end(
        self,
        combobox: ttk.Combobox,
    ):
        """Show the rightmost portion of a combobox (most relevant for paths)."""
        combobox.focus_set()
        position: int = len(combobox.get())
        combobox.icursor(position)
        combobox.xview(position)
        self.root.focus_set()

    def on_combobox_selected(
        self,
        event: tk.Event,
    ):
        """Standard handler for combobox selection - adjusts cursor position."""
        from tkinter import ttk
        widget = event.widget
        if isinstance(widget, ttk.Combobox):
            self.root.after(10, lambda: self.move_cursor_to_end(widget))

    # =========================================================================
    # File Dialog Helpers
    # =========================================================================

    def browse_directory(
        self,
        title: str = "Select Directory",
        initial_dir: str | None = None,
    ) -> str | None:
        """Open a directory selection dialog.

        Returns:
            Selected directory path or None if cancelled
        """
        directory = filedialog.askdirectory(title=title, initialdir=initial_dir)
        return directory if directory else None

    def browse_file(
        self,
        title: str = "Select File",
        filetypes: list[tuple[str, str]] | None = None,
        initial_dir: str | None = None,
    ) -> str | None:
        """Open a file selection dialog.

        Args:
            title: Dialog title
            filetypes: List of (description, pattern) tuples
            initial_dir: Initial directory to open

        Returns:
            Selected file path or None if cancelled
        """
        filetypes = filetypes or [("All files", "*.*")]
        filepath = filedialog.askopenfilename(title=title, filetypes=filetypes, initialdir=initial_dir)
        return filepath if filepath else None

    # =========================================================================
    # Task Thread Helpers
    # =========================================================================

    def start_task_thread(
        self,
        target: Callable,
        args: tuple = (),
        name: str | None = None,
    ):
        """Start a background task thread.

        Args:
            target: Function to run in thread
            args: Arguments to pass to target
            name: Thread name (defaults to "{app_name}_task_thread")
        """
        thread_name = name or f"{self.get_app_name()}_task_thread"
        self.task_thread = Thread(target=target, args=args, name=thread_name)
        self.task_thread.start()


class ThemedApp(BaseApp):
    """Base class with KotorDiff-style themed UI (dark/orange theme).

    This class extends BaseApp with a darker color scheme similar to
    the KotorDiff screenshot - useful for tools that want a distinct look.
    """

    # Theme colors
    BG_COLOR = "#1a1a1a"  # Dark background
    FG_COLOR = "#e0e0e0"  # Light text
    ACCENT_COLOR = "#cc6600"  # Orange accent
    ACCENT_DARK = "#994d00"  # Darker orange for borders
    INPUT_BG = "#2a2a2a"  # Input field background
    INPUT_FG = "#e0e0e0"  # Input field text
    BUTTON_BG = "#333333"  # Button background
    FRAME_BG = "#222222"  # Frame background

    def __init__(
        self,
        title: str,
        version: str,
        *,
        default_width: int = 600,
        default_height: int = 500,
        min_width: int | None = None,
        min_height: int | None = None,
        resizable: bool = True,
    ):
        # Apply theme before initializing UI
        super().__init__(
            title,
            version,
            default_width=default_width,
            default_height=default_height,
            min_width=min_width,
            min_height=min_height,
            resizable=resizable,
        )

    def initialize_ui_controls(self):
        """Initialize UI with themed styling."""
        # Configure root window background
        self.root.configure(bg=self.BG_COLOR)

        # Configure styles
        style = ttk.Style(self.root)
        style.theme_use("clam")  # Use clam as base for better customization

        # Configure ttk styles
        style.configure("TFrame", background=self.BG_COLOR)
        style.configure("TLabel", background=self.BG_COLOR, foreground=self.FG_COLOR)
        style.configure(
            "TButton",
            background=self.ACCENT_COLOR,
            foreground=self.BG_COLOR,
            borderwidth=1,
            focusthickness=3,
            focuscolor=self.ACCENT_DARK,
        )
        style.map(
            "TButton",
            background=[("active", self.ACCENT_DARK), ("pressed", self.ACCENT_DARK)],
        )
        style.configure(
            "TCombobox",
            fieldbackground=self.INPUT_BG,
            background=self.INPUT_BG,
            foreground=self.INPUT_FG,
            arrowcolor=self.ACCENT_COLOR,
            padding=4,
        )
        style.configure(
            "TEntry",
            fieldbackground=self.INPUT_BG,
            foreground=self.INPUT_FG,
        )
        style.configure(
            "TCheckbutton",
            background=self.BG_COLOR,
            foreground=self.FG_COLOR,
        )
        style.configure(
            "TProgressbar",
            background=self.ACCENT_COLOR,
            troughcolor=self.INPUT_BG,
        )

        # Call parent to set up basic structure
        # But we need to customize it, so we do it manually here
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Middle area for text and scrollbar
        text_frame = tk.Frame(self.root, bg=self.BG_COLOR)
        text_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        # Configure the text widget with themed colors
        self.main_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            bg=self.INPUT_BG,
            fg=self.FG_COLOR,
            insertbackground=self.FG_COLOR,
            selectbackground=self.ACCENT_COLOR,
            selectforeground=self.BG_COLOR,
        )
        self.main_text.grid(row=0, column=0, sticky="nsew")
        self._set_themed_text_font(self.main_text)

        # Create scrollbar for main frame
        scrollbar = tk.Scrollbar(text_frame, command=self.main_text.yview, bg=self.BUTTON_BG)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.main_text.config(yscrollcommand=scrollbar.set)

        # Bottom area for buttons and progress
        bottom_frame = tk.Frame(self.root, bg=self.BG_COLOR)
        bottom_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        bottom_frame.grid_columnconfigure(0, weight=1)

        # Progress bar
        self.progress_value = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(bottom_frame, maximum=100, variable=self.progress_value, style="TProgressbar")
        self.progress_bar.pack(side="bottom", fill="x", padx=5, pady=5)

        # Store bottom frame for subclasses to add buttons
        self._bottom_frame = bottom_frame

    def _set_themed_text_font(
        self,
        text_widget: tk.Text,
    ):
        """Configure font and log level tags with themed colors."""
        font_obj = tkfont.Font(font=text_widget.cget("font"))
        font_obj.configure(size=9)
        text_widget.configure(font=font_obj)

        # Define a bold and slightly larger font
        bold_font = tkfont.Font(font=text_widget.cget("font"))
        bold_font.configure(size=10, weight="bold")

        # Themed log level color tags
        text_widget.tag_configure("DEBUG", foreground="#6495ED")  # Cornflower Blue
        text_widget.tag_configure("INFO", foreground=self.FG_COLOR)  # Light gray
        text_widget.tag_configure("WARNING", foreground="#ffaa00", font=bold_font)  # Bright orange
        text_widget.tag_configure("ERROR", foreground="#ff4444", font=bold_font)  # Bright red
        text_widget.tag_configure("CRITICAL", foreground="#ffffff", background="#aa0000", font=bold_font)

    def create_themed_frame(
        self,
        parent: tk.Widget,
        label_text: str | None = None,
        padx: int = 5,
        pady: int = 5,
    ) -> tk.LabelFrame | tk.Frame:
        """Create a themed frame, optionally with a label.

        Args:
            parent: Parent widget
            label_text: Optional label for LabelFrame
            padx: Horizontal padding
            pady: Vertical padding

        Returns:
            tk.LabelFrame if label_text provided, else tk.Frame
        """
        if label_text:
            return tk.LabelFrame(
                parent,
                text=label_text,
                bg=self.FRAME_BG,
                fg=self.ACCENT_COLOR,
                padx=padx,
                pady=pady,
            )
        return tk.Frame(parent, bg=self.FRAME_BG)

    def create_themed_label(
        self,
        parent: tk.Widget,
        text: str,
        **kwargs: Any,
    ) -> tk.Label:
        """Create a themed label."""
        return tk.Label(parent, text=text, bg=self.BG_COLOR, fg=self.FG_COLOR, **kwargs)

    def create_themed_entry(
        self,
        parent: tk.Widget,
        **kwargs: Any,
    ) -> tk.Entry:
        """Create a themed entry field."""
        return tk.Entry(
            parent,
            bg=self.INPUT_BG,
            fg=self.INPUT_FG,
            insertbackground=self.FG_COLOR,
            selectbackground=self.ACCENT_COLOR,
            selectforeground=self.BG_COLOR,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.ACCENT_DARK,
            highlightcolor=self.ACCENT_COLOR,
            **kwargs,
        )

    def create_themed_button(
        self,
        parent: tk.Widget,
        text: str,
        command: Callable[[], Any] | None = None,
        **kwargs: Any,
    ) -> ttk.Button:
        """Create a themed button."""
        if command is not None:
            return ttk.Button(parent, text=text, command=command, style="TButton", **kwargs)
        return ttk.Button(parent, text=text, style="TButton", **kwargs)

