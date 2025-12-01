"""KotorDiff GUI application.

This module provides the KotorDiff GUI, using the ThemedApp base class
for a dark/orange themed interface similar to the Holocron Toolset.
"""
from __future__ import annotations

import os
import pathlib
import sys
import tkinter as tk

from contextlib import suppress
from pathlib import Path
from threading import Event
from tkinter import filedialog, messagebox, ttk
from typing import TYPE_CHECKING, cast

if not getattr(sys, "frozen", False):

    def update_sys_path(path):
        working_dir = str(path)
        if working_dir not in sys.path:
            sys.path.append(working_dir)

    with suppress(Exception):
        pykotor_path = pathlib.Path(__file__).parents[4] / "Libraries" / "PyKotor" / "src" / "pykotor"
        if pykotor_path.exists():
            update_sys_path(pykotor_path.parent)
    with suppress(Exception):
        utility_path = pathlib.Path(__file__).parents[4] / "Libraries" / "Utility" / "src" / "utility"
        if utility_path.exists():
            update_sys_path(utility_path.parent)
    with suppress(Exception):
        update_sys_path(pathlib.Path(__file__).parents[1])


from kotordiff.app import KotorDiffConfig, run_application  # noqa: E402
from pykotor.extract.installation import Installation  # noqa: E402
from pykotor.tools.path import find_kotor_paths_from_default  # noqa: E402
from pykotor.tslpatcher.logger import LogType  # noqa: E402
from utility.tkinter.base_app import ThemedApp  # noqa: E402

if TYPE_CHECKING:

    from pykotor.tslpatcher.logger import PatchLog

CURRENT_VERSION = "1.0.0"


class KotorDiffApp(ThemedApp):
    """KotorDiff GUI application with dark/orange themed interface."""

    def __init__(self):
        # KotorDiff-specific state
        self.path1: str = ""
        self.path2: str = ""
        self.tslpatchdata_path: str = ""
        self.ini_filename: str = "changes.ini"
        self.compare_hashes: bool = True

        super().__init__(
            title="KotorDiff - Holocron Toolset",
            version=CURRENT_VERSION,
            default_width=900,
            default_height=600,
            min_width=700,
            min_height=500,
        )

        # Widgets populated during UI init
        self.path1_radio_install: tk.Radiobutton
        self.path1_radio_custom: tk.Radiobutton
        self.path1_combobox: ttk.Combobox
        self.path1_browse_button: ttk.Button
        self.path1_mode: tk.StringVar

        self.path2_radio_install: tk.Radiobutton
        self.path2_radio_custom: tk.Radiobutton
        self.path2_combobox: ttk.Combobox
        self.path2_browse_button: ttk.Button
        self.path2_mode: tk.StringVar

        self.compare_hashes_var: tk.BooleanVar
        self.tslpatchdata_entry: tk.Entry
        self.tslpatchdata_browse_button: ttk.Button
        self.ini_filename_entry: tk.Entry
        self.log_level_combobox: ttk.Combobox

        self.run_diff_button: ttk.Button
        self.clear_button: ttk.Button
        self.close_button: ttk.Button

        self.pykotor_logger.debug("Init complete")

    def get_app_name(self) -> str:
        return "KotorDiff"

    def initialize_ui_controls(self):
        """Initialize UI with dark-themed KotorDiff styling."""
        # Call parent to set up base theme
        super().initialize_ui_controls()

        # =========================================================================
        # Paths Section
        # =========================================================================
        paths_frame = self.create_themed_frame(self.root, "Paths", padx=10, pady=5)
        paths_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        paths_frame.grid_columnconfigure(1, weight=1)

        # Path 1 (Mine/Modified)
        path1_label = self.create_themed_label(paths_frame, "Path 1 (Mine/Modified):")
        path1_label.configure(fg=self.ACCENT_COLOR)
        path1_label.grid(row=0, column=0, columnspan=4, sticky="w", padx=5, pady=(5, 2))

        self.path1_mode = tk.StringVar(value="install")
        self.path1_radio_install = tk.Radiobutton(
            paths_frame,
            text="Use Installation",
            variable=self.path1_mode,
            value="install",
            bg=self.FRAME_BG,
            fg=self.FG_COLOR,
            selectcolor=self.INPUT_BG,
            activebackground=self.FRAME_BG,
            activeforeground=self.ACCENT_COLOR,
            command=self._update_path1_state,
        )
        self.path1_radio_install.grid(row=1, column=0, sticky="w", padx=5)

        self.path1_radio_custom = tk.Radiobutton(
            paths_frame,
            text="Custom Path",
            variable=self.path1_mode,
            value="custom",
            bg=self.FRAME_BG,
            fg=self.FG_COLOR,
            selectcolor=self.INPUT_BG,
            activebackground=self.FRAME_BG,
            activeforeground=self.ACCENT_COLOR,
            command=self._update_path1_state,
        )
        self.path1_radio_custom.grid(row=1, column=1, sticky="w", padx=5)

        self.path1_combobox = ttk.Combobox(paths_frame, style="TCombobox")
        self.path1_combobox.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=2)
        self.path1_combobox["values"] = self._get_installation_paths()
        self.path1_combobox.bind("<<ComboboxSelected>>", lambda e: self.root.after(10, lambda: self.move_cursor_to_end(cast("ttk.Combobox", e.widget))))

        self.path1_browse_button = self.create_themed_button(paths_frame, "Browse...", self._browse_path1)
        self.path1_browse_button.grid(row=2, column=3, padx=5, pady=2)

        # Path 2 (Older/Vanilla)
        path2_label = self.create_themed_label(paths_frame, "Path 2 (Older/Vanilla):")
        path2_label.configure(fg=self.ACCENT_COLOR)
        path2_label.grid(row=3, column=0, columnspan=4, sticky="w", padx=5, pady=(10, 2))

        self.path2_mode = tk.StringVar(value="install")
        self.path2_radio_install = tk.Radiobutton(
            paths_frame,
            text="Use Installation",
            variable=self.path2_mode,
            value="install",
            bg=self.FRAME_BG,
            fg=self.FG_COLOR,
            selectcolor=self.INPUT_BG,
            activebackground=self.FRAME_BG,
            activeforeground=self.ACCENT_COLOR,
            command=self._update_path2_state,
        )
        self.path2_radio_install.grid(row=4, column=0, sticky="w", padx=5)

        self.path2_radio_custom = tk.Radiobutton(
            paths_frame,
            text="Custom Path",
            variable=self.path2_mode,
            value="custom",
            bg=self.FRAME_BG,
            fg=self.FG_COLOR,
            selectcolor=self.INPUT_BG,
            activebackground=self.FRAME_BG,
            activeforeground=self.ACCENT_COLOR,
            command=self._update_path2_state,
        )
        self.path2_radio_custom.grid(row=4, column=1, sticky="w", padx=5)

        self.path2_combobox = ttk.Combobox(paths_frame, style="TCombobox")
        self.path2_combobox.grid(row=5, column=0, columnspan=3, sticky="ew", padx=5, pady=2)
        self.path2_combobox["values"] = self._get_installation_paths()
        self.path2_combobox.bind("<<ComboboxSelected>>", lambda e: self.root.after(10, lambda: self.move_cursor_to_end(cast("ttk.Combobox", e.widget))))

        self.path2_browse_button = self.create_themed_button(paths_frame, "Browse...", self._browse_path2)
        self.path2_browse_button.grid(row=5, column=3, padx=5, pady=2)

        # =========================================================================
        # Options Section
        # =========================================================================
        options_frame = self.create_themed_frame(self.root, "Options", padx=10, pady=5)
        options_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        options_frame.grid_columnconfigure(1, weight=1)

        # Compare hashes checkbox
        self.compare_hashes_var = tk.BooleanVar(value=True)
        compare_hashes_check = tk.Checkbutton(
            options_frame,
            text="Compare hashes",
            variable=self.compare_hashes_var,
            bg=self.FRAME_BG,
            fg=self.FG_COLOR,
            selectcolor=self.INPUT_BG,
            activebackground=self.FRAME_BG,
            activeforeground=self.ACCENT_COLOR,
        )
        compare_hashes_check.grid(row=0, column=0, sticky="w", padx=5, pady=2)

        # Generate TSLPatchData row
        tslpatch_label = self.create_themed_label(options_frame, "Generate TSLPatchData")
        tslpatch_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)

        self.tslpatchdata_entry = self.create_themed_entry(options_frame)
        self.tslpatchdata_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        self.tslpatchdata_entry.insert(0, "Path to tslpatchdata folder")

        self.tslpatchdata_browse_button = self.create_themed_button(options_frame, "Browse...", self._browse_tslpatchdata)
        self.tslpatchdata_browse_button.grid(row=1, column=2, padx=5, pady=2)

        # INI Filename row
        ini_label = self.create_themed_label(options_frame, "INI Filename:")
        ini_label.grid(row=2, column=0, sticky="w", padx=5, pady=2)

        self.ini_filename_entry = self.create_themed_entry(options_frame)
        self.ini_filename_entry.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        self.ini_filename_entry.insert(0, "changes.ini")

        # Log Level row
        log_level_label = self.create_themed_label(options_frame, "Log Level:")
        log_level_label.grid(row=3, column=0, sticky="w", padx=5, pady=2)

        self.log_level_combobox = ttk.Combobox(options_frame, style="TCombobox", values=["debug", "info", "warning", "error", "critical"], state="readonly")
        self.log_level_combobox.set("info")
        self.log_level_combobox.grid(row=3, column=1, sticky="ew", padx=5, pady=2)

        # =========================================================================
        # Output Section (inherited from base - row 1 becomes row 2)
        # Need to reconfigure the grid to put main_text in new position
        # =========================================================================
        output_frame = self.create_themed_frame(self.root, "Output", padx=5, pady=5)
        output_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        output_frame.grid_rowconfigure(0, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)

        # Reconfigure the main window grid weights
        self.root.grid_rowconfigure(2, weight=1)

        # Move main_text to the new output frame
        self.main_text.master.destroy()  # Destroy old frame
        self.main_text = tk.Text(
            output_frame,
            wrap=tk.WORD,
            bg=self.INPUT_BG,
            fg=self.FG_COLOR,
            insertbackground=self.FG_COLOR,
            selectbackground=self.ACCENT_COLOR,
            selectforeground=self.BG_COLOR,
        )
        self.main_text.grid(row=0, column=0, sticky="nsew")
        self._set_themed_text_font(self.main_text)

        # Add scrollbar
        scrollbar = tk.Scrollbar(output_frame, command=self.main_text.yview, bg=self.BUTTON_BG)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.main_text.config(yscrollcommand=scrollbar.set)

        # =========================================================================
        # Bottom Buttons
        # =========================================================================
        button_frame = tk.Frame(self.root, bg=self.BG_COLOR)
        button_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)

        self.run_diff_button = self.create_themed_button(button_frame, "Run Diff", self.run_diff)
        self.run_diff_button.grid(row=0, column=0, sticky="ew", padx=5)

        self.clear_button = self.create_themed_button(button_frame, "Clear Output", self.clear_main_text)
        self.clear_button.grid(row=0, column=1, sticky="ew", padx=5)

        self.close_button = self.create_themed_button(button_frame, "Close", self.handle_exit_button)
        self.close_button.grid(row=0, column=2, sticky="ew", padx=5)

        # Move progress bar to row 4
        self.progress_bar.master.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 10))

    def _get_installation_paths(self) -> list[str]:
        """Get list of KOTOR installation paths."""
        return [
            str(path)
            for game in find_kotor_paths_from_default().values()
            for path in game
        ]

    def _update_path1_state(self):
        """Update path1 combobox based on radio selection."""
        if self.path1_mode.get() == "install":
            self.path1_combobox["values"] = self._get_installation_paths()
        else:
            # In custom mode, allow typing
            self.path1_combobox["values"] = []

    def _update_path2_state(self):
        """Update path2 combobox based on radio selection."""
        if self.path2_mode.get() == "install":
            self.path2_combobox["values"] = self._get_installation_paths()
        else:
            self.path2_combobox["values"] = []

    def _browse_path1(self):
        """Browse for path 1."""
        directory = filedialog.askdirectory(title="Select Path 1 (Mine/Modified)")
        if directory:
            self.path1_combobox.set(directory)
            self.path1_mode.set("custom")
            self._update_path1_state()

    def _browse_path2(self):
        """Browse for path 2."""
        directory = filedialog.askdirectory(title="Select Path 2 (Older/Vanilla)")
        if directory:
            self.path2_combobox.set(directory)
            self.path2_mode.set("custom")
            self._update_path2_state()

    def _browse_tslpatchdata(self):
        """Browse for TSLPatchData output folder."""
        directory = filedialog.askdirectory(title="Select TSLPatchData Output Folder")
        if directory:
            self.tslpatchdata_entry.delete(0, tk.END)
            self.tslpatchdata_entry.insert(0, directory)

    def validate_inputs(self) -> bool:
        """Validate user inputs before running diff."""
        if self.task_running:
            messagebox.showinfo("Task Running", "Wait for the current task to finish.")
            return False

        path1 = self.path1_combobox.get().strip()
        path2 = self.path2_combobox.get().strip()

        if not path1:
            messagebox.showinfo("Missing Path", "Please select or enter Path 1 (Mine/Modified).")
            return False

        if not path2:
            messagebox.showinfo("Missing Path", "Please select or enter Path 2 (Older/Vanilla).")
            return False

        if not Path(path1).exists():
            messagebox.showerror("Invalid Path", f"Path 1 does not exist: {path1}")
            return False

        if not Path(path2).exists():
            messagebox.showerror("Invalid Path", f"Path 2 does not exist: {path2}")
            return False

        return True

    def run_diff(self):
        """Start the diff operation in a background thread."""
        if not self.validate_inputs():
            return

        self.start_task_thread(self._run_diff_thread, args=(self.simple_thread_event,), name="KotorDiff_thread")

    def _run_diff_thread(self, should_cancel: Event):
        """Execute the diff operation."""
        self.set_state(state=True)
        self.clear_main_text()

        try:
            path1_str = self.path1_combobox.get().strip()
            path2_str = self.path2_combobox.get().strip()
            tslpatchdata_str = self.tslpatchdata_entry.get().strip()

            # Don't use placeholder text as path
            if tslpatchdata_str == "Path to tslpatchdata folder":
                tslpatchdata_str = ""

            # Resolve paths to Installation or Path objects
            resolved_paths: list[Path | Installation] = []

            for path_str in [path1_str, path2_str]:
                path_obj = Path(path_str)
                try:
                    installation = Installation(path_obj)
                    resolved_paths.append(installation)
                    self._log_to_ui(f"[INFO] Loaded Installation for: {path_str}")
                except Exception:  # noqa: BLE001
                    resolved_paths.append(path_obj)
                    self._log_to_ui(f"[INFO] Using Path (not Installation) for: {path_str}")

            # Create configuration
            config = KotorDiffConfig(
                paths=resolved_paths,
                tslpatchdata_path=Path(tslpatchdata_str) if tslpatchdata_str else None,
                ini_filename=self.ini_filename_entry.get().strip() or "changes.ini",
                log_level=self.log_level_combobox.get(),
                compare_hashes=self.compare_hashes_var.get(),
            )

            self._log_to_ui(f"\n{'=' * 60}")
            self._log_to_ui("Starting KotorDiff comparison...")
            self._log_to_ui(f"Path 1: {path1_str}")
            self._log_to_ui(f"Path 2: {path2_str}")
            if tslpatchdata_str:
                self._log_to_ui(f"TSLPatchData Output: {tslpatchdata_str}")
            self._log_to_ui(f"{'=' * 60}\n")

            # Run the diff
            exit_code = run_application(config)

            self._log_to_ui(f"\n{'=' * 60}")
            if exit_code == 0:
                self._log_to_ui("[SUCCESS] Diff completed successfully!")
                if not self.one_shot:
                    messagebox.showinfo("Diff Complete", "Comparison completed successfully!")
            else:
                self._log_to_ui(f"[WARNING] Diff completed with exit code: {exit_code}")
            self._log_to_ui(f"{'=' * 60}")

        except Exception as e:  # noqa: BLE001
            self._handle_general_exception(e, "Error during diff operation")
        finally:
            self.set_state(state=False)

    def _log_to_ui(self, message: str, tag: str = "INFO"):
        """Log a message to the UI text widget."""
        if self.main_text is None:
            return

        try:
            self.main_text.config(state=tk.NORMAL)
            self.main_text.insert(tk.END, message + os.linesep, tag)
            self.main_text.see(tk.END)
            self.main_text.config(state=tk.DISABLED)
        except Exception:  # noqa: BLE001
            pass

    def set_state(self, *, state: bool):
        """Set the task running state and update UI accordingly."""
        if state:
            self.reset_progress_bar()
            self.task_running = True
            self.run_diff_button.config(state=tk.DISABLED)
            self.path1_browse_button.config(state=tk.DISABLED)
            self.path2_browse_button.config(state=tk.DISABLED)
            self.tslpatchdata_browse_button.config(state=tk.DISABLED)
        else:
            self.task_running = False
            self.initialize_logger()
            self.run_diff_button.config(state=tk.NORMAL)
            self.path1_browse_button.config(state=tk.NORMAL)
            self.path2_browse_button.config(state=tk.NORMAL)
            self.tslpatchdata_browse_button.config(state=tk.NORMAL)

    def write_log(self, log: PatchLog):
        """Write a log message to the UI."""
        def log_to_tag(this_log: PatchLog) -> str:
            if this_log.log_type == LogType.NOTE:
                return "INFO"
            if this_log.log_type == LogType.VERBOSE:
                return "DEBUG"
            return this_log.log_type.name

        self._log_to_ui(log.formatted_message, log_to_tag(log))

