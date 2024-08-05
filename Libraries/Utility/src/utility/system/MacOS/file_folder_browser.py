from __future__ import annotations

import subprocess

from typing import TYPE_CHECKING, Iterable

from utility.system.path import PosixPath

if TYPE_CHECKING:
    import os

    from tkinter import Misc, StringVar  # Do not import tkinter-related outside type-checking blocks, in case not installed.


def _get_tk_root():
    import tkinter as tk
    if tk._default_root is None:  # pyright: ignore[reportAttributeAccessIssue]
        root = tk.Tk()
        root.withdraw()
        return root
    return tk._default_root  # pyright: ignore[reportAttributeAccessIssue]

def _run_apple_script(script) -> str:
    result = subprocess.run(
        ["osascript", "-e", script], check=True, capture_output=True, text=True  # noqa: S607, S603
    )
    return result.stdout.strip()

def _run_cocoa_dialog(
    dialog_type: str,
    title: str | None = None,
    initialdir: str | None = None,
    initialfile: str | None = None,
    filetypes: Iterable[tuple[str, str | list[str] | tuple[str, ...]]] | None = None,
    defaultextension: str | None = None,
) -> str | None:
    import ctypes
    import ctypes.util

    libobjc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))

    cID = ctypes.c_void_p
    SEL = ctypes.c_void_p
    libobjc.objc_getClass.restype = cID
    libobjc.objc_getClass.argtypes = [ctypes.c_char_p]
    libobjc.sel_registerName.restype = SEL
    libobjc.sel_registerName.argtypes = [ctypes.c_char_p]
    libobjc.objc_msgSend.restype = cID
    libobjc.objc_msgSend.argtypes = [cID, SEL]

    NSOpenPanel = libobjc.objc_getClass(b"NSOpenPanel")
    NSSavePanel = libobjc.objc_getClass(b"NSSavePanel")
    NSURL = libobjc.objc_getClass(b"NSURL")
    NSString = libobjc.objc_getClass(b"NSString")
    NSArray = libobjc.objc_getClass(b"NSArray")

    def NSString_from_str(string):
        return libobjc.objc_msgSend(NSString, libobjc.sel_registerName(b"stringWithUTF8String:"), ctypes.c_char_p(string.encode("utf-8")))

    def str_from_NSURL(nsurl):
        utf8_string = libobjc.objc_msgSend(nsurl, libobjc.sel_registerName(b"absoluteString"))
        return ctypes.string_at(libobjc.objc_msgSend(utf8_string, libobjc.sel_registerName(b"UTF8String"))).decode("utf-8")

    if dialog_type in ("open_file", "open_folder"):
        panel = libobjc.objc_msgSend(NSOpenPanel, libobjc.sel_registerName(b"openPanel"))
        libobjc.objc_msgSend(panel, libobjc.sel_registerName(b"setCanChooseFiles:"), ctypes.c_bool(dialog_type == "open_file"))
        libobjc.objc_msgSend(panel, libobjc.sel_registerName(b"setCanChooseDirectories:"), ctypes.c_bool(dialog_type == "open_folder"))
    elif dialog_type == "save_file":
        panel = libobjc.objc_msgSend(NSSavePanel, libobjc.sel_registerName(b"savePanel"))

    if title:
        title_nsstring = NSString_from_str(title)
        libobjc.objc_msgSend(panel, libobjc.sel_registerName(b"setTitle:"), title_nsstring)

    if initialdir:
        initialdir_nsstring = NSString_from_str(initialdir)
        url = libobjc.objc_msgSend(NSURL, libobjc.sel_registerName(b"fileURLWithPath:"), initialdir_nsstring)
        libobjc.objc_msgSend(panel, libobjc.sel_registerName(b"setDirectoryURL:"), url)

    if initialfile:
        initialfile_nsstring = NSString_from_str(initialfile)
        libobjc.objc_msgSend(panel, libobjc.sel_registerName(b"setNameFieldStringValue:"), initialfile_nsstring)

    if filetypes:
        allowed_file_types = []
        for ft in filetypes:
            if isinstance(ft[1], str):
                allowed_file_types.append(NSString_from_str(ft[1]))
            else:
                allowed_file_types.extend(NSString_from_str(ext) for ext in ft[1])
        allowed_file_types_nsarray = libobjc.objc_msgSend(NSArray, libobjc.sel_registerName(b"arrayWithObjects:count:"), (cID * len(allowed_file_types))(*allowed_file_types), len(allowed_file_types))
        libobjc.objc_msgSend(panel, libobjc.sel_registerName(b"setAllowedFileTypes:"), allowed_file_types_nsarray)

    if defaultextension:
        defaultextension_nsstring = NSString_from_str(defaultextension)
        libobjc.objc_msgSend(panel, libobjc.sel_registerName(b"setAllowedFileTypes:"), defaultextension_nsstring)

    response = libobjc.objc_msgSend(panel, libobjc.sel_registerName(b"runModal"))

    # NSModalResponseOK is defined as 1 in macOS
    if response == 1:
        nsurl = libobjc.objc_msgSend(panel, libobjc.sel_registerName(b"URL"))
        return str_from_NSURL(nsurl)

    return None


def askdirectory(
    *,
    initialdir: os.PathLike | str | None = None,
    mustexist: bool | None = None,
    parent: Misc | None = None,
    title: str | None = None
) -> str:
    try:
        from tkinter import filedialog
    except ImportError:
        try:
            return _run_cocoa_dialog(
                dialog_type="open_folder",
                title=title,
                initialdir=None if initialdir is None else str(initialdir),
            ) or ""
        except Exception:
            try:
                script = f"""
                    set directory to POSIX path of (choose folder with prompt "{title}"{f' default location POSIX file "{initialdir}"' if initialdir else ''})
                    return directory
                """
                return _run_apple_script(script)
            except Exception as e3:
                raise RuntimeError("All methods to open directory dialog failed") from e3
    else:
        return filedialog.askdirectory(
            initialdir=initialdir,
            mustexist=mustexist,
            title=title,
            parent=_get_tk_root() if parent is None else parent,
        )


def askopenfile(
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
    except ImportError as e1:
        try:
            result = _run_cocoa_dialog("open_file", title)
            if not result or not result.strip():
                return None
            return PosixPath(result if isinstance(result, str) else result[0]).open(mode)
        except Exception as e2:  # noqa: BLE001
            try:
                script = f'set file to POSIX path of (choose file with prompt "{title}"'

                if initialdir:
                    script += f' default location POSIX file "{initialdir}"'

                if filetypes:
                    file_types_str = ", ".join([f'"{ft[1]}"' if isinstance(ft[1], str) else "{"+", ".join([f'"{ext}"' for ext in ft[1]])+"}" for ft in filetypes])
                    script += f" of type {{{file_types_str}}}"

                script += ")"
                script += "\nreturn file"

                result = _run_apple_script(script)
                if not result or not result.strip():
                    return None
                return PosixPath(result).open(mode)
            except Exception as e3:
                raise RuntimeError("All methods to open file dialog failed") from e3
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

def askopenfilename(
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
    except ImportError as e1:
        try:
            result = _run_cocoa_dialog("open_file", title)
            if not result or not result.strip():
                return ""
            return result if isinstance(result, str) else result[0]
        except ValueError:
            raise
        except Exception as e2:  # noqa: BLE001
            try:
                script = f'set file to POSIX path of (choose file with prompt "{title}"'

                if initialdir:
                    script += f' default location POSIX file "{initialdir}"'

                if filetypes:
                    file_types_str = ", ".join([f'"{ft[1]}"' if isinstance(ft[1], str) else "{"+", ".join([f'"{ext}"' for ext in ft[1]])+"}" for ft in filetypes])
                    script += f" of type {{{file_types_str}}}"

                script += ")"
                script += "\nreturn file"

                return _run_apple_script(script)
            except Exception as e3:
                raise RuntimeError("All methods to open file dialog failed") from e3
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

def asksaveasfile(
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
            file = _run_cocoa_dialog("save_file", title, str(initialdir), str(initialfile), filetypes, defaultextension)
            if not file or not file.strip():
                return None
            return PosixPath(file).resolve().open(mode)
        except Exception:  # noqa: BLE001
            script = f"""
                set file to POSIX path of (choose file name with prompt "{title}"{f' default location POSIX file "{initialdir}"' if initialdir else ''}{f' default name "{initialfile}"' if initialfile else ''})
                return file
            """
            result = _run_apple_script(script)
            if not result or not result.strip():
                return None
            return PosixPath(result).resolve().open(mode)
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

def asksaveasfilename(
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
            file = _run_cocoa_dialog("save_file", title, str(initialdir), str(initialfile), filetypes, defaultextension)
            if not file or not file.strip():
                return ""
            return file  # noqa: TRY300
        except Exception:  # noqa: BLE001
            script = f"""
                set file to POSIX path of (choose file name with prompt "{title}"{f' default location POSIX file "{initialdir}"' if initialdir else ''}{f' default name "{initialfile}"' if initialfile else ''})
                return file
            """  # noqa: E501
            result = _run_apple_script(script)
            if not result or not result.strip():
                return ""
            return result
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