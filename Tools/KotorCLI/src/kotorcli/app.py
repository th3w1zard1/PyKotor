"""KotorCLI GUI entrypoint (Kit Generator).

When command-line arguments are provided, the CLI remains headless. Launching
without arguments starts this tkinter GUI for kit generation.
"""
from __future__ import annotations

import logging
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

    def update_sys_path(path: Path):
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

from loggerplus import RobustLogger  # noqa: E402
from pykotor.extract.installation import Installation  # noqa: E402
from pykotor.tools.path import CaseAwarePath, find_kotor_paths_from_default  # noqa: E402
from pykotor.tslpatcher.logger import LogType  # noqa: E402
from utility.error_handling import universal_simplify_exception  # noqa: E402
from utility.tkinter.base_app import BaseApp  # noqa: E402

from kotorcli import __version__ as kotorcli_version  # noqa: E402
from kotorcli.kit_generator import generate_kit  # noqa: E402

if TYPE_CHECKING:
    from pykotor.tslpatcher.logger import PatchLog

VERSION_LABEL = kotorcli_version


class App(BaseApp):
    """Kit generator GUI for KotorCLI."""

    def __init__(self):
        self.installation_path: str = ""
        self.module_name: str = ""
        self.output_path: str = ""
        self.kit_id: str = ""
        self.current_installation: Installation | None = None
        self.one_shot: bool = False

        self.installation_paths: ttk.Combobox | None = None
        self.installation_browse_button: ttk.Button | None = None
        self.module_combobox: ttk.Combobox | None = None
        self.output_entry: tk.Entry | None = None
        self.kit_id_entry: tk.Entry | None = None
        self.extract_button: ttk.Button | None = None
        self.exit_button: ttk.Button | None = None

        super().__init__(
            title="KotorCLI Kit Generator",
            version=VERSION_LABEL,
            default_width=600,
            default_height=500,
        )

        self.show_onboarding_info()
        self.pykotor_logger.debug("Init complete")

    def get_app_name(self) -> str:
        return "KotorCLI"

    def initialize_ui_controls(self):
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        ttk.Style(self.root).configure("TCombobox", font=("Helvetica", 10), padding=4)

        top_frame: tk.Frame = tk.Frame(self.root)
        top_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        top_frame.grid_columnconfigure(0, weight=0, minsize=80)
        top_frame.grid_columnconfigure(1, weight=1)
        top_frame.grid_columnconfigure(2, weight=0)

        tk.Label(top_frame, text="Installation:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.installation_paths = ttk.Combobox(top_frame, style="TCombobox")
        self.installation_paths.set("Select your KOTOR directory path")
        self.installation_paths.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.installation_paths["values"] = [str(path) for game in find_kotor_paths_from_default().values() for path in game]
        self.installation_paths.bind("<<ComboboxSelected>>", self.on_installation_paths_chosen)
        self.installation_browse_button = ttk.Button(top_frame, text="Browse", command=self.browse_installation)
        self.installation_browse_button.grid(row=0, column=2, padx=5, pady=2, sticky="e")

        tk.Label(top_frame, text="Module:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.module_combobox = ttk.Combobox(top_frame, style="TCombobox", state="readonly")
        self.module_combobox.set("Select a module (choose installation first)")
        self.module_combobox.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        self.module_combobox.bind("<<ComboboxSelected>>", self.on_module_selected)

        tk.Label(top_frame, text="Output:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.output_entry = tk.Entry(top_frame)
        self.output_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        tk.Button(top_frame, text="Browse", command=self.browse_output).grid(row=2, column=2, padx=5, pady=2)

        tk.Label(top_frame, text="Kit ID:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.kit_id_entry = tk.Entry(top_frame)
        self.kit_id_entry.grid(row=3, column=1, padx=5, pady=2, sticky="ew")

        text_frame = tk.Frame(self.root)
        text_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        self.main_text = tk.Text(text_frame, wrap=tk.WORD)
        self.main_text.grid(row=0, column=0, sticky="nsew")
        self.set_text_font(self.main_text)

        scrollbar = tk.Scrollbar(text_frame, command=self.main_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.main_text.config(yscrollcommand=scrollbar.set)

        bottom_frame = tk.Frame(self.root)
        bottom_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        self.exit_button = ttk.Button(bottom_frame, text="Exit", command=self.handle_exit_button)
        self.exit_button.pack(side="left", padx=5, pady=5)
        self.extract_button = ttk.Button(bottom_frame, text="Extract", command=self.begin_extract)
        self.extract_button.pack(side="right", padx=5, pady=5)

        self.progress_value = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(bottom_frame, maximum=100, variable=self.progress_value)
        self.progress_bar.pack(side="bottom", fill="x", padx=5, pady=5)

    def on_installation_paths_chosen(
        self,
        event: tk.Event,
    ):
        """Adjust the combobox after a short delay and populate modules."""
        self.root.after(10, lambda: self.move_cursor_to_end(cast("ttk.Combobox", event.widget)))
        self.populate_modules()

    def browse_installation(
        self,
        default_kotor_dir_str: os.PathLike | str | None = None,
    ):
        """Open the installation directory chooser."""
        try:
            directory_path_str: os.PathLike | str = default_kotor_dir_str or filedialog.askdirectory(title="Select KOTOR Installation Directory")
            if not directory_path_str:
                return
            directory = CaseAwarePath(directory_path_str)
            directory_str = str(directory)
            if self.installation_paths is not None:
                self.installation_paths.set(str(directory))
                if directory_str not in self.installation_paths["values"]:
                    self.installation_paths["values"] = (*self.installation_paths["values"], directory_str)
            if self.installation_paths is not None:
                self.root.after(10, self.move_cursor_to_end, self.installation_paths)
            self.populate_modules()
        except Exception as exc:
            self._handle_general_exception(exc, "An unexpected error occurred while loading the game directory.")

    def populate_modules(self):
        """Populate the module combobox with modules from the selected installation."""
        if self.installation_paths is None or self.module_combobox is None:
            return

        installation_path: str = self.installation_paths.get().strip()
        if not installation_path or installation_path == "Select your KOTOR directory path":
            self.module_combobox["values"] = []
            self.module_combobox.set("Select a module (choose installation first)")
            self.module_combobox.config(state="readonly")
            if self.kit_id_entry is not None:
                self.kit_id_entry.delete(0, tk.END)
            return

        try:
            self.current_installation = Installation(Path(installation_path))
            modules: list[str] = self.current_installation.modules_list()

            module_values: list[str] = []
            seen_stems: set[str] = set()
            for module in sorted(modules):
                module_stem = Path(module).stem.lower()
                if module_stem.endswith("_s"):
                    continue
                if module_stem in seen_stems:
                    continue
                seen_stems.add(module_stem)
                module_values.append(f"{module_stem} [{module}]")

            self.module_combobox["values"] = module_values
            if module_values:
                self.module_combobox.set("Select a module")
                self.module_combobox.config(state="readonly")
            else:
                self.module_combobox.set("No modules found")
                self.module_combobox.config(state="readonly")
            if self.kit_id_entry is not None:
                self.kit_id_entry.delete(0, tk.END)
        except Exception as exc:  # noqa: BLE001
            self.module_combobox["values"] = []
            self.module_combobox.set("Invalid installation")
            self.module_combobox.config(state="readonly")
            self._handle_general_exception(exc, "Failed to load modules from installation", msgbox=False)

    def on_module_selected(self, event: tk.Event):
        """Handle module selection - auto-populate Kit ID."""
        if self.module_combobox is None:
            return
        selected_module: str = self.module_combobox.get().strip()
        if selected_module in (
            "",
            "Select a module",
            "Select a module (choose installation first)",
            "No modules found",
            "Invalid installation",
        ):
            return

        if " [" in selected_module and "]" in selected_module:
            module_name = selected_module.split(" [")[-1].rstrip("]")
        else:
            module_name = selected_module

        module_path = Path(module_name)
        module_name_clean: str = module_path.stem.lower()

        if self.kit_id_entry is not None and not self.kit_id_entry.get().strip():
            self.kit_id_entry.delete(0, tk.END)
            self.kit_id_entry.insert(0, module_name_clean)

    def browse_output(self):
        directory: str | None = filedialog.askdirectory(title="Select Output Directory")
        if directory and directory.strip() and self.output_entry is not None:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, directory)

    def pre_extract_validate(self) -> bool:
        """Validates prerequisites for starting an extraction."""
        if self.task_running:
            messagebox.showinfo(
                "Task already running",
                "Wait for the previous task to finish.",
            )
            return False

        if self.installation_paths is None or self.module_combobox is None or self.output_entry is None:
            messagebox.showerror("UI not ready", "The UI did not finish initializing.")
            return False

        installation_path = self.installation_paths.get().strip()
        if not installation_path:
            messagebox.showinfo(
                "No installation path",
                "Select your KOTOR installation directory first.",
            )
            return False

        module_name = self.module_combobox.get().strip()
        if not module_name or module_name == "Select a module (choose installation first)":
            messagebox.showinfo(
                "No module selected",
                "Select a module first.",
            )
            return False
        if " [" in module_name and "]" in module_name:
            module_name = module_name.split(" [")[-1].rstrip("]")

        output_path = self.output_entry.get().strip()
        if not output_path:
            messagebox.showinfo(
                "No output path",
                "Select an output directory first.",
            )
            return False

        try:
            Installation(Path(installation_path))
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(
                "Invalid installation path",
                f"The installation path is invalid: {exc}",
            )
            return False

        case_output_path = CaseAwarePath(output_path)
        if not case_output_path.exists():
            try:
                case_output_path.mkdir(parents=True, exist_ok=True)
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror(
                    "Cannot create output directory",
                    f"Cannot create output directory: {exc}",
                )
                return False

        return True

    def begin_extract(self):
        """Starts the extraction process in a background thread."""
        self.pykotor_logger.debug("Call begin_extract")
        try:
            if not self.pre_extract_validate():
                return
            self.pykotor_logger.debug("Prevalidate finished, starting extract thread")
            self.start_task_thread(self.begin_extract_thread, args=(self.simple_thread_event,), name="KotorCLI_kit_extract_thread")
        except Exception as exc:  # noqa: BLE001
            self._handle_general_exception(exc, "An unexpected error occurred during the extraction and the program was forced to exit")
            sys.exit(1)

    def begin_extract_thread(
        self,
        should_cancel_thread: Event,
    ):
        """Starts the kit extraction thread."""
        self.pykotor_logger.debug("begin_extract_thread reached")

        if self.installation_paths is None or self.module_combobox is None or self.output_entry is None:
            return

        installation_path = Path(self.installation_paths.get().strip())
        module_name = self.module_combobox.get().strip()
        if " [" in module_name and "]" in module_name:
            module_name = module_name.split(" [")[-1].rstrip("]")
        module_path = Path(module_name)
        module_name = module_path.stem.lower()
        output_path = Path(self.output_entry.get().strip())
        kit_id = self.kit_id_entry.get().strip() if self.kit_id_entry is not None else ""

        self.installation_path = str(installation_path)
        self.module_name = module_name
        self.output_path = str(output_path)
        self.kit_id = kit_id

        self.set_state(state=True)
        self.clear_main_text()
        assert self.main_text is not None, "Main text is None"
        self.main_text.config(state=tk.NORMAL)
        self.main_text.insert(tk.END, f"Starting kit extraction...{os.linesep}")
        self.main_text.see(tk.END)
        self.main_text.config(state=tk.DISABLED)

        try:
            installation = Installation(installation_path)
            self.logger.add_note(f"Loaded installation from: {installation_path}")

            class LoggerBridge(logging.Handler):
                def __init__(self, patch_logger):
                    super().__init__()
                    self.patch_logger = patch_logger

                def emit(self, record):
                    msg = self.format(record)
                    if record.levelno >= logging.ERROR:
                        self.patch_logger.add_error(msg)
                    elif record.levelno >= logging.WARNING:
                        self.patch_logger.add_warning(msg)
                    elif record.levelno >= logging.INFO:
                        self.patch_logger.add_note(msg)
                    else:
                        self.patch_logger.add_verbose(msg)

            bridge = LoggerBridge(self.logger)
            bridge.setFormatter(logging.Formatter("%(message)s"))
            self.pykotor_logger.addHandler(bridge)

            try:
                generate_kit(
                    installation_path=installation_path,
                    module_name=module_name,
                    output_path=output_path,
                    kit_id=kit_id or None,
                    logger=self.pykotor_logger,
                )
            finally:
                self.pykotor_logger.removeHandler(bridge)

            self.logger.add_note("Kit extraction completed successfully!")
            messagebox.showinfo(
                "Extraction complete!",
                f"Kit generated successfully at: {output_path}",
            )
        except Exception as exc:  # noqa: BLE001
            self._handle_exception_during_extract(exc)
        finally:
            self.set_state(state=False)

    def set_state(
        self,
        *,
        state: bool,
    ):
        """Sets the active thread task state."""
        if state:
            self.reset_progress_bar()
            self.task_running = True
            if self.extract_button is not None:
                self.extract_button.config(state=tk.DISABLED)
            if self.installation_browse_button is not None:
                self.installation_browse_button.config(state=tk.DISABLED)
            if self.module_combobox is not None:
                self.module_combobox.config(state=tk.DISABLED)
        else:
            self.task_running = False
            self.initialize_logger()
            if self.extract_button is not None:
                self.extract_button.config(state=tk.NORMAL)
            if self.installation_browse_button is not None:
                self.installation_browse_button.config(state=tk.NORMAL)
            if self.module_combobox is not None:
                self.module_combobox.config(state="readonly")

    def _handle_exception_during_extract(
        self,
        exc: Exception,
    ):
        """Handles exceptions during extraction."""
        self.pykotor_logger.exception("Unhandled exception in KotorCLI kit generator", exc_info=exc)
        error_name, msg = universal_simplify_exception(exc)
        self.logger.add_error(f"{error_name}: {msg}{os.linesep}The extraction was aborted with errors")
        messagebox.showerror(
            error_name,
            f"An unexpected error occurred during the extraction and the extraction was forced to terminate.{os.linesep * 2}{msg}",
        )

    def get_log_file_path(self) -> Path | None:
        """Returns the path to the log file."""
        if self.output_path:
            return Path(self.output_path) / "kotorcli_kitgenerator_log.txt"
        return Path.cwd() / "kotorcli_kitgenerator_log.txt"

    def show_onboarding_info(self):
        """Display onboarding information in the log area on startup."""
        onboarding_text = f"""KotorCLI Kit Generator v{VERSION_LABEL}
{'=' * 80}
Extract kit resources from KOTOR module files (RIM/ERF)

To run headless, use: python -m kotorcli kit-generate --installation <path> --module <module> --output <dir>
"""
        assert self.main_text is not None, "Main text is None"
        self.main_text.config(state=tk.NORMAL)
        self.main_text.insert(tk.END, onboarding_text, "INFO")
        self.main_text.see(tk.END)
        self.main_text.config(state=tk.DISABLED)

    def write_log(
        self,
        log: PatchLog,
    ):
        """Writes a message to the log."""

        def log_to_tag(this_log: PatchLog) -> str:
            if this_log.log_type == LogType.NOTE:
                return "INFO"
            if this_log.log_type == LogType.VERBOSE:
                return "DEBUG"
            return this_log.log_type.name

        log_file_path = self.get_log_file_path()
        if log_file_path:
            try:
                log_file_path.parent.mkdir(parents=True, exist_ok=True)
                with log_file_path.open("a", encoding="utf-8") as log_file:
                    log_file.write(f"{log.formatted_message}\n")
            except OSError as exc:
                RobustLogger().error(f"Failed to write the log file at '{log_file_path}': {exc.__class__.__name__}: {exc}")

        try:
            assert self.main_text is not None, "Main text is None"
            self.main_text.config(state=tk.NORMAL)
            self.main_text.insert(tk.END, log.formatted_message + os.linesep, log_to_tag(log))
            self.main_text.see(tk.END)
            self.main_text.config(state=tk.DISABLED)
        except Exception as exc:  # noqa: BLE001
            self.pykotor_logger.error(f"Failed to write log to UI: {exc}")

