from __future__ import annotations

import subprocess

from typing import TYPE_CHECKING, Iterable

from utility.system.path import PosixPath

if TYPE_CHECKING:
    import os

    from tkinter import Misc, StringVar  # Do not import tkinter-related outside type-checking blocks, in case not installed.


def _get_tk_root():
    import tkinter as tk
    if tk._default_root is None:  # pyright: ignore[reportAttributeAccessIssue]  # noqa: SLF001
        root = tk.Tk()
        root.withdraw()
        return root
    return tk._default_root  # pyright: ignore[reportAttributeAccessIssue]  # noqa: SLF001


def _run_zenity_dialog(dialog_type: str, options: list[str]) -> str | None:
    cmd = ["zenity", f"--{dialog_type}", *options]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def _run_yad_dialog(dialog_type: str, options: list[str]) -> str | None:
    cmd = ["yad", f"--{dialog_type}", *options]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def _run_gtk_dialog(  # noqa: PLR0913, PLR0911, ANN201
    dialog_type: str,
    title: str | None,
    initialdir: str | None,
    initialfile: str | None,
    filetypes: Iterable[tuple[str, str | list[str] | tuple[str, ...]]] | None,
    defaultextension: str | None,
) -> str | None:
    import ctypes
    import ctypes.util

    # Load GTK and GObject libraries
    libgtk = ctypes.CDLL(ctypes.util.find_library("gtk-3"))
    libgobject = ctypes.CDLL(ctypes.util.find_library("gobject-2.0"))

    # Initialize GTK
    libgtk.gtk_init(None, None)

    # Define constants
    GTK_FILE_CHOOSER_ACTION_OPEN = 0
    GTK_FILE_CHOOSER_ACTION_SAVE = 1
    GTK_RESPONSE_ACCEPT = -3

    # Determine the action type for the dialog
    if dialog_type == "open_file":
        action = GTK_FILE_CHOOSER_ACTION_OPEN
    elif dialog_type == "open_folder":
        action = GTK_FILE_CHOOSER_ACTION_OPEN
    elif dialog_type == "save_file":
        action = GTK_FILE_CHOOSER_ACTION_SAVE
    else:
        raise ValueError("Invalid dialog_type provided")

    # Create the file chooser dialog
    dialog = libgtk.gtk_file_chooser_dialog_new(
        title.encode("utf-8") if title else None,
        None,
        action,
        b"_Cancel", ctypes.c_int(-6),
        b"_Open", ctypes.c_int(GTK_RESPONSE_ACCEPT),
        None
    )

    # Set the initial directory
    if initialdir:
        libgtk.gtk_file_chooser_set_current_folder(dialog, initialdir.encode("utf-8"))

    # Set the initial file name
    if initialfile:
        libgtk.gtk_file_chooser_set_current_name(dialog, initialfile.encode("utf-8"))

    # Set file filters
    if filetypes:
        for desc, patterns in filetypes:
            file_filter = libgtk.gtk_file_filter_new()
            libgtk.gtk_file_filter_set_name(file_filter, desc.encode("utf-8"))
            if isinstance(patterns, str):
                libgtk.gtk_file_filter_add_pattern(file_filter, patterns.encode("utf-8"))
            else:
                for pattern in patterns:
                    libgtk.gtk_file_filter_add_pattern(file_filter, pattern.encode("utf-8"))
            libgtk.gtk_file_chooser_add_filter(dialog, file_filter)

    # Set default extension (note: GTK does not have direct method for this, workaround needed)
    # No direct function, so this part can be omitted or handled differently as per specific requirements

    # Run the dialog and get the response
    response = libgtk.gtk_dialog_run(dialog)
    if response == GTK_RESPONSE_ACCEPT:
        filename = libgtk.gtk_file_chooser_get_filename(dialog)
        if filename:
            result = ctypes.string_at(filename).decode("utf-8")
            libgtk.gtk_widget_destroy(dialog)
            return result

    # Destroy the dialog widget
    libgtk.gtk_widget_destroy(dialog)
    return None



def askdirectory(  # noqa: PLR0913, PLR0911, ANN201
    *,
    initialdir: os.PathLike | str | None = None,
    mustexist: bool | None = None,
    parent: Misc | None = None,
    title: str | None = None,
) -> str:
    try:
        from tkinter import filedialog
    except ImportError:
        try:
            return _run_zenity_dialog("file-selection", ["--directory", f"--title={title}", f"--filename={initialdir or ''}"]) or ""
        except Exception:
            try:
                return _run_yad_dialog("file-selection", ["--directory", f"--title={title}", f"--filename={initialdir or ''}"]) or ""
            except Exception:
                try:
                    return _run_gtk_dialog(
                        dialog_type="open_folder",
                        title=title,
                        initialdir=None if initialdir is None else str(initialdir),
                        initialfile=None,
                        filetypes=None,
                        defaultextension=None,
                    ) or ""
                except Exception as e4:
                    raise RuntimeError("All methods to open directory dialog failed") from e4
    else:
        return filedialog.askdirectory(
            initialdir=initialdir,
            mustexist=mustexist,
            title=title,
            parent=_get_tk_root() if parent is None else parent,
        )


def askopenfile(  # noqa: PLR0913, PLR0911, ANN201
    mode: str = "r",
    *,
    defaultextension: str | None = None,
    filetypes: Iterable[tuple[str, str | list[str] | tuple[str, ...]]] | None = None,
    initialdir: os.PathLike | str | None = None,
    initialfile: os.PathLike | str | None = None,
    parent: Misc | None = None,
    title: str | None = None,
    typevariable: StringVar | str | None = None,
):
    try:
        from tkinter import filedialog
    except ImportError:
        try:
            result = _run_zenity_dialog("file-selection", [f"--title={title}", f"--filename={initialdir or ''}"])
            if not result or not result.strip():
                return None
            return PosixPath(result).open(mode)
        except Exception:
            try:
                result = _run_yad_dialog("file-selection", [f"--title={title}", f"--filename={initialdir or ''}"])
                if not result or not result.strip():
                    return None
                return PosixPath(result).open(mode)
            except Exception:
                try:
                    result = _run_gtk_dialog(
                        dialog_type="open_file",
                        title=title,
                        initialdir=None if initialdir is None else str(initialdir),
                        initialfile=None if initialfile is None else str(initialfile),
                        filetypes=filetypes,
                        defaultextension=defaultextension,
                    )
                    if not result or not result.strip():
                        return None
                    return PosixPath(result).open(mode)
                except Exception as e:
                    raise RuntimeError("All methods to open file dialog failed") from e
    else:
        file = filedialog.askopenfile(
            mode,
            defaultextension=defaultextension,
            filetypes=filetypes,
            initialdir=initialdir,
            initialfile=initialfile,
            title=title,
            parent=_get_tk_root() if parent is None else parent,
            typevariable=typevariable,
        )
        return file


def askopenfilename(  # noqa: PLR0913, PLR0911, ANN201
    *,
    defaultextension: str | None = None,
    filetypes: Iterable[tuple[str, str | list[str] | tuple[str, ...]]] | None = None,
    initialdir: os.PathLike | str | None = None,
    initialfile: os.PathLike | str | None = None,
    parent: Misc | None = None,
    title: str | None = None,
    typevariable: StringVar | str | None = None,
) -> str:
    try:
        from tkinter import filedialog
    except ImportError:
        try:
            result = _run_zenity_dialog("file-selection", [f"--title={title}", f"--filename={initialdir or ''}"])
            if not result or not result.strip():
                return ""
            return result
        except Exception:
            try:
                result = _run_yad_dialog("file-selection", [f"--title={title}", f"--filename={initialdir or ''}"])
                if not result or not result.strip():
                    return ""
                return result
            except Exception:
                try:
                    return _run_gtk_dialog(
                        dialog_type="open_file",
                        title=title,
                        initialdir=None if initialdir is None else str(initialdir),
                        initialfile=None if initialfile is None else str(initialfile),
                        filetypes=filetypes,
                        defaultextension=defaultextension,
                    ) or ""
                except Exception as e4:
                    raise RuntimeError("All methods to open filename dialog failed") from e4
    else:
        file = filedialog.askopenfilename(
            defaultextension=defaultextension,
            filetypes=filetypes,
            initialdir=initialdir,
            initialfile=initialfile,
            title=title,
            parent=_get_tk_root() if parent is None else parent,
            typevariable=typevariable,
        )
        return file


def asksaveasfile(  # noqa: PLR0913, PLR0911, ANN201
    mode: str = "w",
    *,
    confirmoverwrite: bool | None = None,
    defaultextension: str | None = None,
    filetypes: Iterable[tuple[str, str | list[str] | tuple[str, ...]]] | None = None,
    initialdir: os.PathLike | str | None = None,
    initialfile: os.PathLike | str | None = None,
    parent: Misc | None = None,
    title: str | None = None,
    typevariable: StringVar | str | None = None,
):
    try:
        from tkinter import filedialog
    except ImportError:
        try:
            result = _run_zenity_dialog("file-selection", ["--save", f"--title={title}", f"--filename={initialdir or ''}/{initialfile or ''}"])
            if not result or not result.strip():
                return None
            return PosixPath(result).open(mode)
        except Exception:
            try:
                result = _run_yad_dialog("file-selection", ["--save", f"--title={title}", f"--filename={initialdir or ''}/{initialfile or ''}"])
                if not result or not result.strip():
                    return None
                return PosixPath(result).open(mode)
            except Exception:
                try:
                    result = _run_gtk_dialog(
                        dialog_type="save_file",
                        title=title,
                        initialdir=None if initialdir is None else str(initialdir),
                        initialfile=None if initialfile is None else str(initialfile),
                        filetypes=filetypes,
                        defaultextension=defaultextension,
                    )
                    if result is None:
                        return None
                    return PosixPath(result).open(mode)
                except Exception as e4:
                    raise RuntimeError("All methods to save file dialog failed") from e4
    else:
        return filedialog.asksaveasfile(
            mode,
            confirmoverwrite=confirmoverwrite,
            defaultextension=defaultextension,
            filetypes=filetypes,
            initialdir=initialdir,
            initialfile=initialfile,
            parent=_get_tk_root() if parent is None else parent,
            title=title,
            typevariable=typevariable,
        )


def asksaveasfilename(  # noqa: PLR0913, PLR0911, ANN201
    *,
    confirmoverwrite: bool | None = None,
    defaultextension: str | None = None,
    filetypes: Iterable[tuple[str, str | list[str] | tuple[str, ...]]] | None = None,
    initialdir: os.PathLike | str | None = None,
    initialfile: os.PathLike | str | None = None,
    parent: Misc | None = None,
    title: str | None = None,
    typevariable: StringVar | str | None = None,
) -> str:
    try:
        from tkinter import filedialog
    except ImportError:
        try:
            result = _run_zenity_dialog("file-selection", ["--save", f"--title={title}", f"--filename={initialdir or ''}/{initialfile or ''}"])
            if not result or not result.strip():
                return ""
            return result
        except Exception:
            try:
                result = _run_yad_dialog("file-selection", ["--save", f"--title={title}", f"--filename={initialdir or ''}/{initialfile or ''}"])
                if not result or not result.strip():
                    return ""
                return result
            except Exception:
                try:
                    return _run_gtk_dialog(
                        dialog_type="save_file",
                        title=title,
                        initialdir=None if initialdir is None else str(initialdir),
                        initialfile=None if initialfile is None else str(initialfile),
                        filetypes=filetypes,
                        defaultextension=defaultextension,
                    ) or ""
                except Exception as e4:
                    raise RuntimeError("All methods to save filename dialog failed") from e4
    else:
        return filedialog.asksaveasfilename(
            confirmoverwrite=confirmoverwrite,
            defaultextension=defaultextension,
            filetypes=filetypes,
            initialdir=initialdir,
            initialfile=initialfile,
            parent=_get_tk_root() if parent is None else parent,
            title=title,
            typevariable=typevariable,
        )