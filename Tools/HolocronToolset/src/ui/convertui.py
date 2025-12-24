from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

def update_sys_path(path: pathlib.Path):
    working_dir = str(path)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


file_absolute_path = pathlib.Path(__file__).resolve()
utility_path = file_absolute_path.parents[4] / "Libraries" / "Utility" / "src"
if utility_path.exists():
    update_sys_path(utility_path)

from pathlib import Path  # noqa: E402

# Working dir should always be 'toolset' when running this script.
TOOLSET_DIR = Path(file_absolute_path.parents[1], "toolset")
if not TOOLSET_DIR.is_dir():
    while len(TOOLSET_DIR.parts) > 1 and TOOLSET_DIR.name.lower() != "toolset":
        TOOLSET_DIR = TOOLSET_DIR.parent
    if TOOLSET_DIR.name.lower() != "toolset":
        raise RuntimeError("Could not find the toolset folder! Please ensure this script is ran somewhere inside the toolset folder or a subdirectory.")

if __name__ == "__main__":
    os.chdir(TOOLSET_DIR)

UI_SOURCE_DIR = Path("../ui/")
UI_TARGET_DIR = Path("../toolset/uic/")
QRC_SOURCE_PATH = Path("../resources/resources.qrc")
QRC_TARGET_PATH = Path("..")


def get_available_qt_version() -> Literal["PyQt5", "PyQt6", "PySide6", "PySide2"]:
    # Check QT_API environment variable first (takes priority)
    qt_api_env = os.environ.get("QT_API", "").strip()
    if qt_api_env:
        # Normalize the environment variable value to match our version format
        qt_api_normalized = qt_api_env.lower()
        version_mapping = {
            "pyqt5": "PyQt5",
            "pyqt6": "PyQt6",
            "pyside6": "PySide6",
            "pyside2": "PySide2",
            "pyqt": "PyQt6",  # Default to PyQt6 if just "pyqt" is specified
            "pyside": "PySide6",  # Default to PySide6 if just "pyside" is specified
        }
        mapped_version = version_mapping.get(qt_api_normalized)
        if mapped_version:
            # Verify the mapped version can be imported
            try:
                if mapped_version.startswith("PyQt"):
                    __import__(mapped_version)
                else:
                    __import__(mapped_version.replace("Side", ""))
                return mapped_version  # pyright: ignore[reportReturnType]
            except ImportError:
                # If the specified version isn't available, fall through to auto-detection
                pass
    
    # Fall back to auto-detection if QT_API is not set or the specified version is unavailable
    qt_versions = ["PyQt5", "PyQt6", "PySide6", "PySide2"]
    for qt_version in qt_versions:
        try:
            if qt_version.startswith("PyQt"):
                __import__(qt_version)
            else:
                __import__(qt_version.replace("Side", ""))
        except ImportError:  # noqa: PERF203, S112
            continue
        else:
            return qt_version  # pyright: ignore[reportReturnType]
    raise RuntimeError("No supported Qt binding found. Please install `PyQt5`, `PyQt6`, `PySide6`, or `PySide2`.")


def compile_ui_through_python(
    qt_version: str,
    ui_file: Path,
    ui_target: Path,
    debug: bool = False,
) -> subprocess.CompletedProcess | None:
    # Fallback: try running as Python module (e.g., python -m PyQt5.uic.pyuic)
    if qt_version == "PyQt5":
        module_name = "PyQt5.uic.pyuic"
    elif qt_version == "PyQt6":
        module_name = "PyQt6.uic.pyuic"
    elif qt_version == "PySide2":
        module_name = "PySide2.uic"
    elif qt_version == "PySide6":
        module_name = "PySide6.uic"
    else:
        raise RuntimeError(f"Unknown Qt version: {qt_version}")
    
    args = [
        sys.executable,
        "-m",
        module_name,
        str(ui_file),
        "-o",
        str(ui_target),
    ]
    if debug:
        args.append("-d")
    print(f"Running: {' '.join(args)}")
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return result


def compile_ui_through_subprocess(
    ui_compiler: str,
    ui_file: Path,
    ui_target: Path,
    debug: bool = False,
) -> subprocess.CompletedProcess | None:
    compiler_path = os.path.normpath(ui_compiler)
    args = [compiler_path, str(ui_file), "-o", str(ui_target)]
    if debug:
        args.append("-d")
    print(f"Running: {' '.join(args)}")
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return result


def compile_ui(
    qt_version: str, *,
    ignore_timestamp: bool = False,
    debug: bool = False,
):
    compiler_mapping: dict[str, str] = {
        "PySide2": "pyside2-uic",
        "PySide6": "pyside6-uic",
        "PyQt5": "pyuic5",
        "PyQt6": "pyuic6",
    }
    for ui_file in Path(UI_SOURCE_DIR).rglob("*.ui"):
        if ui_file.is_dir():
            print(f"Skipping {ui_file}, not a file.")
            continue
        relpath: Path = ui_file.relative_to(UI_SOURCE_DIR)
        subdir_ui_target: Path = Path(UI_TARGET_DIR, "qtpy", relpath).resolve()
        ui_target: Path = subdir_ui_target.with_suffix(".py")

        if not ui_target.is_file():
            print("mkdir", ui_target.parent)
            ui_target.parent.mkdir(exist_ok=True, parents=True)
            current_path: Path = ui_target.parent
            init_file: Path = current_path.joinpath("__init__.py")
            while not init_file.is_file() and current_path.resolve() != UI_TARGET_DIR.resolve():
                print(f"touch {init_file}")
                init_file.touch()
                current_path = current_path.parent
                init_file = current_path.joinpath("__init__.py")

        # If the target file does not yet exist, use timestamp=0 as this will force the timestamp check to pass
        source_timestamp: float = ui_file.stat().st_mtime
        target_timestamp: float = ui_target.stat().st_mtime if ui_target.exists() else 0.0

        # Only recompile if source file is newer than the existing target file or ignore_timestamp is set to True
        if source_timestamp > target_timestamp or ignore_timestamp:
            # Use subprocess instead of os.system for better path handling on Windows
            # Try to find the compiler executable
            result = None
            for compiler in compiler_mapping.values():
                if result is False:
                    sys.exit(1)
                compiler_path = shutil.which(compiler)
                try:
                    if compiler_path is None:
                        result = compile_ui_through_python(qt_version, ui_file, ui_target, debug)
                    else:
                        result = compile_ui_through_subprocess(compiler_path, ui_file, ui_target, debug)
                except subprocess.CalledProcessError as e:
                    print(f"Error: {e}")
                    print(f"Error: {e.stdout}")
                    print(f"Error: {e.stderr}")
                    result = False
                else:
                    break
            if result:
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr, file=sys.stderr)
            filedata: str = ui_target.read_text(encoding="utf-8")
            new_filedata: str = filedata.replace(f"from {qt_version}", "from qtpy").replace(f"import {qt_version}", "import qtpy")
            if filedata != new_filedata:
                ui_target.write_text(new_filedata, encoding="utf-8")


def compile_qrc(
    qt_version: str,
    *,
    ignore_timestamp: bool = False,
):
    qrc_source: Path = QRC_SOURCE_PATH.resolve()
    qrc_target: Path = Path(QRC_TARGET_PATH, "resources_rc.py").resolve()

    if not qrc_target.parent.is_dir():
        print("mkdir", qrc_target.parent)
        qrc_target.parent.mkdir(exist_ok=True, parents=True)

    # If the target file does not yet exist, use timestamp=0 as this will force the timestamp check to pass
    source_timestamp: float = qrc_source.stat().st_mtime
    target_timestamp: float = qrc_target.stat().st_mtime if qrc_target.is_file() else 0.0

    if source_timestamp > target_timestamp or ignore_timestamp:
        rc_compiler: str = {
            "PyQt5": "pyrcc5",
            "PyQt6": "pyside6-rcc",
            "PySide2": "pyside2-rcc",
            "PySide6": "pyside6-rcc",
        }[qt_version]
        # Use subprocess instead of os.system for better path handling on Windows
        compiler_path = shutil.which(rc_compiler)
        if compiler_path is None:
            # Fallback: try running as Python module
            if qt_version == "PyQt5":
                module_name = "PyQt5.pyrcc_main"
            elif qt_version == "PyQt6":
                module_name = "PySide6.rcc"
            elif qt_version == "PySide2":
                module_name = "PySide2.rcc"
            elif qt_version == "PySide6":
                module_name = "PySide6.rcc"
            else:
                raise RuntimeError(f"Unknown Qt version: {qt_version}")
            
            args = [
                sys.executable,
                "-m",
                module_name,
                str(qrc_source),
                "-o",
                str(qrc_target),
            ]
            print(f"Running: {' '.join(args)}")
            result = subprocess.run(args, check=False, capture_output=True, text=True)
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
        else:
            args = [compiler_path, str(qrc_source), "-o", str(qrc_target)]
            print(f"Running: {' '.join(args)}")
            result = subprocess.run(args, check=False, capture_output=True, text=True)
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
        
        filedata: str = qrc_target.read_text(encoding="utf-8")
        new_filedata: str = filedata.replace(f"from {qt_version}", "from qtpy").replace(f"import {qt_version}", "import qtpy")
        if filedata != new_filedata:
            qrc_target.write_text(new_filedata)


if __name__ == "__main__":
    qt_version = get_available_qt_version()
    compile_ui(qt_version, ignore_timestamp=True, debug=True)
    compile_qrc(qt_version, ignore_timestamp=False)
    print("All ui compilations completed in", TOOLSET_DIR)
