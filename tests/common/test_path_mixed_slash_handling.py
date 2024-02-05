# Rigorously test the string result of each pathlib module.
# The goal isn't really to test pathlib.Path or utility.path, the goal is to determine if there was a breaking change in a python patch release.
from __future__ import annotations

import contextlib
import ctypes
import os
import pathlib
import platform
import subprocess
import sys
import unittest
from ctypes.wintypes import DWORD
from pathlib import Path, PosixPath, PurePath, PurePosixPath, PureWindowsPath, WindowsPath
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING
from unittest import mock

if TYPE_CHECKING:
    from typing_extensions import Literal

THIS_SCRIPT_PATH = pathlib.Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[2]
UTILITY_PATH = THIS_SCRIPT_PATH.parents[4].joinpath("Utility", "src")
def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)
if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
    os.chdir(PYKOTOR_PATH.parent)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.tools.path import CaseAwarePath
from utility.system.path import Path as CustomPath
from utility.system.path import PosixPath as CustomPosixPath
from utility.system.path import PurePath as CustomPurePath
from utility.system.path import PurePosixPath as CustomPurePosixPath
from utility.system.path import PureWindowsPath as CustomPureWindowsPath
from utility.system.path import WindowsPath as CustomWindowsPath


def check_path_win_api(path) -> tuple[bool, bool, bool]:
    GetFileAttributes = ctypes.windll.kernel32.GetFileAttributesW
    INVALID_FILE_ATTRIBUTES: int = DWORD(-1).value

    attrs = GetFileAttributes(path)
    if attrs == INVALID_FILE_ATTRIBUTES:
        return False, False, False  # Path does not exist or cannot be accessed

    FILE_ATTRIBUTE_DIRECTORY = 0x10
    is_dir = bool(attrs & FILE_ATTRIBUTE_DIRECTORY)
    is_file: bool = not is_dir  # Simplistic check; may need refinement for special files
    return True, is_file, is_dir

class TestPathlibMixedSlashes(unittest.TestCase):

    def create_and_run_batch_script(self, cmd: list[str], pause_after_command: bool = True):
        with TemporaryDirectory() as tempdir:
            # Ensure the script path is absolute
            script_path = Path(tempdir, "temp_script.bat").absolute()
            script_path_str = str(script_path)

            # Write the commands to a batch file
            with script_path.open(mode="w", encoding="utf-8", errors="strict") as file:
                for command in cmd:
                    file.write(command + "\n")
                if pause_after_command:
                    file.write("pause\nexit\n")

            # Determine the CMD switch to use
            cmd_switch = "/K" if pause_after_command else "/C"

            # Construct the command to run the batch script with elevated privileges
            run_script_cmd: list[str] = [
                "Powershell",
                "-Command",
                f"Start-Process cmd.exe -ArgumentList '{cmd_switch} \"{script_path_str}\"' -Verb RunAs -Wait"
            ]

            # Execute the batch script
            subprocess.run(run_script_cmd, check=True)

            # Optionally, delete the batch script after execution
            with contextlib.suppress(OSError):
                script_path.unlink()

    def remove_permissions(self, path_str: str):

        # Define the commands
        combined_commands: list[str] = [
            f"icacls \"{path_str}\" /reset",
            f"attrib +S +R \"{path_str}\"",
            f"icacls \"{path_str}\" /inheritance:r",
            f"icacls \"{path_str}\" /deny Everyone:(F)"
        ]

        # Create and run the batch script
        self.create_and_run_batch_script(combined_commands, pause_after_command=False)


    @unittest.skipIf(os.name == "posix", "Test is not available on POSIX systems.")
    def test_gain_file_access(self):  # sourcery skip: extract-method
        test_file = Path("this file has no permissions.txt").absolute()
        try:
            with test_file.open("w") as f:
                f.write("test")
        except PermissionError as e:
            ...
            # raise e
        self.remove_permissions(str(test_file))
        try:

            # Remove all permissions from the file

            test_filepath = CustomPath(test_file)
            self.assertTrue(os.access(test_file, os.R_OK), "Read access should be denied but this doesn't seem to work.")
            self.assertFalse(os.access(test_file, os.W_OK), "Write access should be denied.")

            self.assertEqual(test_filepath.has_access(mode=0o1), True)  # this is a bug with os.access
            self.assertEqual(test_filepath.has_access(mode=0o7), False)

            self.assertEqual(test_filepath.gain_access(mode=0o6), True)
            self.assertEqual(test_filepath.has_access(mode=0o6), True)

            self.assertTrue(os.access(test_file, os.R_OK), "Read access should be granted.")
            self.assertTrue(os.access(test_file, os.W_OK), "Write access should be granted.")
        finally:
            # Clean up: Delete the temporary file
            test_file.unlink()

    def test_nt_case_hashing(self):
        test_classes: tuple[type, ...] = (
            (CustomPureWindowsPath,)
            if os.name == "posix"
            else (CustomWindowsPath, CustomPureWindowsPath, CustomPath)
        )
        for path_type in test_classes:
            with self.subTest(path_type=path_type):
                path1 = path_type("test\\path\\to\\nothing")
                path2 = path_type("tesT\\PATH\\\\to\\noTHinG\\")

            with mock.patch("os.name", "nt"):
                test_set = {path1, path2}
                self.assertEqual(path1, path2)
                self.assertEqual(hash(path1), hash(path2))
                self.assertSetEqual(test_set, {path_type("TEST\\path\\to\\\\nothing")})

    @unittest.skipIf(os.name != "posix", "Test only supported on POSIX systems.")
    def test_posix_exists_alternatives(self):
        test_classes: tuple[type, ...] = (CustomPath, CustomPosixPath, CaseAwarePath)
        test_path = "/dev/vcsa6"
        self.assertFalse(os.access("C:\\nonexistent\\path", os.F_OK))
        test_access: bool = os.access(test_path, os.F_OK)
        self.assertEqual(test_access, True)

        test_os_exists: bool = os.path.exists(test_path)  # noqa: PTH110
        self.assertEqual(test_os_exists, True)
        test_os_isfile: bool = os.path.isfile(test_path)  # noqa: PTH113
        self.assertEqual(test_os_isfile, False)  # This is the bug
        test_os_isdir: bool = os.path.isdir(test_path)  # noqa: PTH112
        self.assertEqual(test_os_isdir, False)  # This is the bug

        self.assertEqual(True, Path(test_path).exists())
        self.assertEqual(False, Path(test_path).is_file())  # This is the bug
        self.assertEqual(False, Path(test_path).is_dir())  # This is the bug
        for path_type in test_classes:

            test_pathtype_exists: bool | None = path_type(test_path).safe_exists()
            self.assertEqual(test_pathtype_exists, True, repr(path_type))
            self.assertEqual(True, path_type(test_path).exists(), repr(path_type))
            test_pathtype_isfile: bool | None = path_type(test_path).safe_isfile()
            self.assertEqual(test_pathtype_isfile, False, repr(path_type))
            self.assertEqual(False, path_type(test_path).is_file(), repr(path_type))  # This is the bug
            test_pathtype_isdir: bool | None = path_type(test_path).safe_isdir()
            self.assertEqual(test_pathtype_isdir, False, repr(path_type))
            self.assertEqual(False, path_type(test_path).is_dir(), repr(path_type))  # This is the bug

    @unittest.skipIf(os.name != "nt", "Test only supported on Windows.")
    def test_windows_exists_alternatives_dir(self):
        test_classes: tuple[type, ...] = (CustomWindowsPath, CustomPath, CaseAwarePath)
        test_path = "C:\\WINDOWS"
        self.assertFalse(os.access("C:\\nonexistent\\path", os.F_OK))
        test_access: bool = os.access(test_path, os.F_OK)
        self.assertEqual(test_access, True)

        exists, is_file, is_dir = check_path_win_api(test_path)
        self.assertEqual(exists, True)
        self.assertEqual(is_file, False)
        self.assertEqual(is_dir, True)

        test_os_exists: bool = os.path.exists(test_path)  # noqa: PTH110
        self.assertEqual(test_os_exists, True)
        test_os_isfile: bool = os.path.isfile(test_path)  # noqa: PTH113
        self.assertEqual(test_os_isfile, False)

        for path_type in test_classes:

            test_pathtype_exists: bool | None = path_type(test_path).safe_exists()
            self.assertEqual(test_pathtype_exists, True)
            test_pathtype_isfile: bool | None = path_type(test_path).safe_isfile()
            self.assertEqual(test_pathtype_isfile, False)
            test_pathtype_isdir: bool | None = path_type(test_path).safe_isdir()
            self.assertEqual(test_pathtype_isdir, True)

    @unittest.skipIf(os.name != "nt", "Test only supported on Windows.")
    def test_windows_exists_alternatives(self):
        test_classes: tuple[type, ...] = (CustomPath, CaseAwarePath)
        test_path = "C:\\GitHub\\PyKotor\\.venv_wsl\\bin"
        self.assertFalse(os.access("C:\\nonexistent\\path", os.F_OK))
        test_access: bool = os.access(test_path, os.F_OK)
        self.assertEqual(test_access, True)

        exists, is_file, is_dir = check_path_win_api(test_path)
        self.assertEqual(exists, True)
        self.assertEqual(is_file, False)
        self.assertEqual(is_dir, True)

        # These are the bugs
        test_os_exists: bool = os.path.exists(test_path)  # noqa: PTH110
        self.assertEqual(test_os_exists, True)
        test_os_isfile: bool = os.path.isfile(test_path)  # noqa: PTH113
        self.assertEqual(test_os_isfile, False)

        # These are the bugs too.
        #self.assertRaises(OSError, Path(test_path).exists)
        #self.assertRaises(OSError, Path(test_path).is_file)
        #self.assertRaises(OSError, Path(test_path).is_dir)
        for path_type in test_classes:

            test_pathtype_exists: bool | None = path_type(test_path).safe_exists()
            self.assertEqual(test_pathtype_exists, True)
            #self.assertRaises(OSError, path_type(test_path).exists)
            test_pathtype_isfile: bool | None = path_type(test_path).safe_isfile()
            self.assertEqual(test_pathtype_isfile, False)
            #self.assertRaises(OSError, path_type(test_path).is_file)
            test_pathtype_isdir: bool | None = path_type(test_path).safe_isdir()
            self.assertEqual(test_pathtype_isdir, True)
            #self.assertRaises(OSError, path_type(test_path).is_dir)

    def find_exists_problems(self):
        test_classes: tuple[type, ...] = (Path, CustomPath, CustomWindowsPath if os.name == "nt" else CustomPosixPath, CaseAwarePath)
        test_path = "/" if platform.system() != "Windows" else "C:\\"
        for path_type in test_classes:
            self.assertTrue(self.list_files_recursive_scandir(test_path, set(), path_type))

    def list_files_recursive_scandir(self, path: str, seen: set, path_type: type[pathlib.Path | CustomPath | CaseAwarePath]) -> Literal[True] | None:
        if "/mnt/c" in path.lower():
            print("Skipping /mnt/c (wsl)")
            return True
        try:
            it = os.scandir(path)
        except Exception:
            return None

        known_issue_paths: set[str] = {
            "C:\\GitHub\\PyKotor\\.venv_wsl\\bin\\python",
            "C:\\GitHub\\PyKotor\\.venv_wsl\\bin\\python3",
            "C:\\GitHub\\PyKotor\\.venv_wsl\\bin\\python3.10",
        }
        try:
            for entry in it:
                path_entry: str = entry.path
                if path_entry in known_issue_paths:
                    continue
                if path_entry.replace("\\", "/").count("/") > 5 or path_entry in seen:  # Handle links
                    continue
                else:
                    seen.add(path_entry)
                try:
                    is_dir_check = path_type(path_entry).is_dir()
                    assert is_dir_check is True or is_dir_check is False, f"is_file_check returned nonbool '{is_dir_check}' at '{path_entry}'"
                    if is_dir_check:
                        print(f"Directory: {path_entry}")
                        self.list_files_recursive_scandir(path_entry, seen, path_type)  # Recursively list subdirectories
                    is_file_check = path_type(path_entry).is_file()
                    assert is_file_check is True or is_file_check is False, f"is_file_check returned nonbool '{is_file_check}' at '{path_entry}'"
                    if is_file_check:
                        ...
                        #print(f"File: {path_entry}")
                    if is_file_check or is_dir_check:
                        continue

                    exist_check = path_type(path_entry).exists()
                    if exist_check is True:
                        print(f"exists: True but no permissions to {path_entry}")
                        raise RuntimeError(f"exists: True but no permissions to {path_entry}")
                    elif exist_check is False:
                        print(f"exists: False but no permissions to {path_entry}")
                    else:
                        raise ValueError(f"Unexpected ret value of exist_check at {path_entry}: {exist_check}")
                except Exception as e:
                    print(f"Exception encountered during is_dir() call on {path_entry}: {e}")
                    raise
        except Exception as e:
            print(f"Exception encountered while scanning {path}: {e}")
            raise
        return True

    def test_posix_case_hashing(self):
        test_classes: list[type] = (
            [CustomPosixPath, CustomPurePosixPath, CustomPath]
            if os.name == "posix"
            else [CustomPurePosixPath]
        )
        for path_type in test_classes:
            with self.subTest(path_type=path_type):
                path1 = path_type("test\\\\path\\to\\nothing\\")
                path2 = path_type("tesT\\PATH\\to\\\\noTHinG")

            with mock.patch("os.name", "posix"):
                test_set = {path1, path2}
                self.assertNotEqual(path1, path2)
                self.assertNotEqual(hash(path1), hash(path2))
                self.assertNotEqual(test_set, {path_type("TEST\\path\\\\to\\nothing")})

    def test_pathlib_path_edge_cases_posix(self):
        test_classes = (PosixPath, PurePosixPath) if os.name == "posix" else (PurePosixPath,)
        for path_type in test_classes:
            with self.subTest(path_type=path_type):
                # Absolute vs Relative Paths
                self.assertEqual(str(path_type("C:/")), "C:")
                self.assertEqual(str(path_type("C:/Users/test/")), "C:/Users/test")
                self.assertEqual(str(path_type("C:/Users/test\\")), "C:/Users/test\\")
                self.assertEqual(str(path_type("C://Users///test")), "C:/Users/test")
                self.assertEqual(str(path_type("C:/Users/TEST/")), "C:/Users/TEST")

                # Network Paths
                self.assertEqual(str(path_type("\\\\server\\folder")), "\\\\server\\folder")
                self.assertEqual(str(path_type("\\\\\\\\server\\folder/")), "\\\\\\\\server\\folder")
                self.assertEqual(str(path_type("\\\\\\server\\\\folder")), "\\\\\\server\\\\folder")
                self.assertEqual(str(path_type("\\\\wsl.localhost\\path\\to\\file")), "\\\\wsl.localhost\\path\\to\\file")
                self.assertEqual(
                    str(path_type("\\\\wsl.localhost\\path\\to\\file with space ")),
                    "\\\\wsl.localhost\\path\\to\\file with space ",
                )

                # Special Characters
                self.assertEqual(str(path_type("C:/Users/test folder/")), "C:/Users/test folder")
                self.assertEqual(str(path_type("C:/Users/üser/")), "C:/Users/üser")
                self.assertEqual(str(path_type("C:/Users/test\\nfolder/")), "C:/Users/test\\nfolder")

                # Joinpath, rtruediv, truediv
                self.assertEqual(str(path_type("C:/Users").joinpath("test/")), "C:/Users/test")
                self.assertEqual(str(path_type("C:/Users") / "test/"), "C:/Users/test")
                self.assertEqual(str(path_type("C:/Users").__truediv__("test/")), "C:/Users/test")

                # Bizarre Scenarios
                self.assertEqual(str(path_type("")), ".")
                self.assertEqual(str(path_type("//")), "//")
                self.assertEqual(str(path_type("C:")), "C:")
                self.assertEqual(str(path_type("///")), "/")
                self.assertEqual(str(path_type("C:/./Users/../test/")), "C:/Users/../test")
                self.assertEqual(str(path_type("~/folder/")), "~/folder")

    def test_pathlib_path_edge_cases_windows(self):
        test_classes = (WindowsPath, PureWindowsPath) if os.name == "nt" else (PureWindowsPath,)
        for path_type in test_classes:
            with self.subTest(path_type=path_type):
                # Absolute vs Relative Paths
                self.assertEqual(str(path_type("C:/")), "C:\\")
                self.assertEqual(str(path_type("C:\\")), "C:\\")
                self.assertEqual(str(path_type("C:/Users/test/")), "C:\\Users\\test")
                self.assertEqual(str(path_type("C:/Users/test\\")), "C:\\Users\\test")
                self.assertEqual(str(path_type("C://Users///test")), "C:\\Users\\test")
                self.assertEqual(str(path_type("C:/Users/TEST/")), "C:\\Users\\TEST")

                # Network Paths
                self.assertEqual(str(path_type("\\\\server\\folder")), "\\\\server\\folder\\")
                if sys.version_info < (3, 12):
                    self.assertEqual(str(path_type("\\\\\\\\server\\folder/")), "\\server\\folder")
                    self.assertEqual(str(path_type("\\\\\\server\\\\folder")), "\\server\\folder")
                else:
                    self.assertEqual(str(path_type("\\\\\\\\server\\folder/")), "\\\\\\\\server\\folder")
                    self.assertEqual(str(path_type("\\\\\\server\\\\folder")), "\\\\\\server\\folder")
                self.assertEqual(str(path_type("\\\\wsl.localhost\\path\\to\\file")), "\\\\wsl.localhost\\path\\to\\file")
                self.assertEqual(
                    str(path_type("\\\\wsl.localhost\\path\\to\\file with space ")),
                    "\\\\wsl.localhost\\path\\to\\file with space ",
                )

                # Special Characters
                self.assertEqual(str(path_type("C:/Users/test folder/")), "C:\\Users\\test folder")
                self.assertEqual(str(path_type("C:/Users/üser/")), "C:\\Users\\üser")
                self.assertEqual(str(path_type("C:/Users/test\\nfolder/")), "C:\\Users\\test\\nfolder")

                # Joinpath, rtruediv, truediv
                self.assertEqual(str(path_type("C:/Users").joinpath("test/")), "C:\\Users\\test")
                self.assertEqual(str(path_type("C:/Users") / "test/"), "C:\\Users\\test")
                self.assertEqual(str(path_type("C:/Users").__truediv__("test/")), "C:\\Users\\test")

                # Bizarre Scenarios
                self.assertEqual(str(path_type("")), ".")
                if sys.version_info < (3, 12):
                    self.assertEqual(str(path_type("//")), "\\")
                    self.assertEqual(str(path_type("///")), "\\")
                else:
                    self.assertEqual(str(path_type("//")), "\\\\")
                    self.assertEqual(str(path_type("///")), "\\\\\\")
                self.assertEqual(str(path_type("C:")), "C:")
                self.assertEqual(str(path_type("C:/./Users/../test/")), "C:\\Users\\..\\test")
                self.assertEqual(str(path_type("~/folder/")), "~\\folder")

    def test_pathlib_path_edge_cases_os_specific(self):
        for path_type in (Path, PurePath):
            with self.subTest(path_type=path_type):
                # Absolute vs Relative Paths
                self.assertEqual(str(path_type("C:\\")), "C:\\")
                self.assertEqual(str(path_type("C:/Users/test/")), "C:/Users/test".replace("/", os.sep))
                self.assertEqual(str(path_type("C://Users///test")), "C:/Users/test".replace("/", os.sep))
                self.assertEqual(str(path_type("C:/Users/TEST/")), "C:/Users/TEST".replace("/", os.sep))
                if os.name == "posix":
                    self.assertEqual(str(path_type("C:/Users/test\\")), "C:/Users/test\\")
                    self.assertEqual(str(path_type("C:/")), "C:")
                elif os.name == "nt":
                    self.assertEqual(str(path_type("C:/Users/test")), "C:\\Users\\test")
                    self.assertEqual(str(path_type("C:/")), "C:\\")

                # Network Paths
                self.assertEqual(str(path_type("\\\\wsl.localhost\\path\\to\\file")), "\\\\wsl.localhost\\path\\to\\file")
                self.assertEqual(
                    str(path_type("\\\\wsl.localhost\\path\\to\\file with space ")),
                    "\\\\wsl.localhost\\path\\to\\file with space ",
                )
                if os.name == "posix":
                    self.assertEqual(str(path_type("\\\\server\\folder")), "\\\\server\\folder")
                    self.assertEqual(str(path_type("\\\\\\\\server\\folder/")), "\\\\\\\\server\\folder")
                    self.assertEqual(str(path_type("\\\\\\server\\\\folder")), "\\\\\\server\\\\folder")
                elif os.name == "nt":
                    self.assertEqual(str(path_type("\\\\server\\folder")), "\\\\server\\folder\\")
                    if sys.version_info < (3, 12):
                        self.assertEqual(str(path_type("\\\\\\\\server\\folder/")), "\\server\\folder")
                        self.assertEqual(str(path_type("\\\\\\server\\\\folder")), "\\server\\folder")
                    else:
                        self.assertEqual(str(path_type("\\\\\\\\server\\folder/")), "\\\\\\\\server\\folder")
                        self.assertEqual(str(path_type("\\\\\\server\\\\folder")), "\\\\\\server\\folder")

                # Special Characters
                self.assertEqual(str(path_type("C:/Users/test folder/")), "C:/Users/test folder".replace("/", os.sep))
                self.assertEqual(str(path_type("C:/Users/üser/")), "C:/Users/üser".replace("/", os.sep))
                self.assertEqual(str(path_type("C:/Users/test\\nfolder/")), "C:/Users/test\\nfolder".replace("/", os.sep))

                # Joinpath, rtruediv, truediv
                self.assertEqual(str(path_type("C:/Users").joinpath("test/")), "C:/Users/test".replace("/", os.sep))
                self.assertEqual(str(path_type("C:/Users") / "test/"), "C:/Users/test".replace("/", os.sep))
                self.assertEqual(str(path_type("C:/Users").__truediv__("test/")), "C:/Users/test".replace("/", os.sep))

                # Bizarre Scenarios
                self.assertEqual(str(path_type("")), ".")
                if os.name == "posix":
                    self.assertEqual(str(path_type("//")), "//".replace("/", os.sep))
                elif sys.version_info < (3, 12):
                    self.assertEqual(str(path_type("//")), "\\")
                else:
                    self.assertEqual(str(path_type("//")), "\\\\")
                self.assertEqual(str(path_type("C:")), "C:")
                if sys.version_info < (3, 12) or os.name != "nt":
                    self.assertEqual(str(path_type("///")), "/".replace("/", os.sep))
                else:
                    self.assertEqual(str(path_type("///")), "///".replace("/", os.sep))
                self.assertEqual(str(path_type("C:/./Users/../test/")), "C:/Users/../test".replace("/", os.sep))
                self.assertEqual(str(path_type("~/folder/")), "~/folder".replace("/", os.sep))

    def test_custom_path_edge_cases_posix(self):
        test_classes = [CustomPosixPath, CustomPurePosixPath] if os.name == "posix" else [CustomPurePosixPath]
        for path_type in test_classes:
            with self.subTest(path_type=path_type):
                # Absolute vs Relative Paths
                self.assertEqual(str(path_type("C:/")), "C:")
                self.assertEqual(str(path_type("C:/Users/test/")), "C:/Users/test")
                self.assertEqual(str(path_type("C:/Users/test\\")), "C:/Users/test")
                self.assertEqual(str(path_type("C://Users///test")), "C:/Users/test")
                self.assertEqual(str(path_type("C:/Users/TEST/")), "C:/Users/TEST")

                # Network Paths
                self.assertEqual(str(path_type("\\\\server\\folder")), "/server/folder")
                self.assertEqual(str(path_type("\\\\\\\\server\\folder/")), "/server/folder")
                self.assertEqual(str(path_type("\\\\\\server\\\\folder")), "/server/folder")
                self.assertEqual(str(path_type("\\\\wsl.localhost\\path\\to\\file")), "/wsl.localhost/path/to/file")
                self.assertEqual(
                    str(path_type("\\\\wsl.localhost\\path\\to\\file with space ")),
                    "/wsl.localhost/path/to/file with space ",
                )

                # Special Characters
                self.assertEqual(str(path_type("C:/Users/test folder/")), "C:/Users/test folder")
                self.assertEqual(str(path_type("C:/Users/üser/")), "C:/Users/üser")
                self.assertEqual(str(path_type("C:/Users/test\\nfolder/")), "C:/Users/test/nfolder")

                # Joinpath, rtruediv, truediv
                self.assertEqual(str(path_type("C:/Users").joinpath("test/")), "C:/Users/test")
                self.assertEqual(str(path_type("C:/Users") / "test/"), "C:/Users/test")
                self.assertEqual(str(path_type("C:/Users").__truediv__("test/")), "C:/Users/test")

                # Bizarre Scenarios
                self.assertEqual(str(path_type("")), ".")
                self.assertEqual(str(path_type("//")), "/")
                self.assertEqual(str(path_type("///")), "/")
                self.assertEqual(str(path_type("C:/./Users/../test/")), "C:/Users/../test")
                self.assertEqual(str(path_type("C:")), "C:")
                self.assertEqual(str(path_type("~/folder/")), "~/folder")

    def test_custom_path_edge_cases_windows(self):
        test_classes = [CustomWindowsPath, CustomPureWindowsPath] if os.name == "nt" else [CustomPureWindowsPath]
        for path_type in test_classes:
            with self.subTest(path_type=path_type):
                # Absolute vs Relative Paths
                self.assertEqual(str(path_type("C:/")), "C:")
                self.assertEqual(str(path_type("C:/Users/test/")), "C:\\Users\\test")
                self.assertEqual(str(path_type("C:/Users/test\\")), "C:\\Users\\test")
                self.assertEqual(str(path_type("C://Users///test")), "C:\\Users\\test")
                self.assertEqual(str(path_type("C:/Users/TEST/")), "C:\\Users\\TEST")

                # Network Paths
                self.assertEqual(str(path_type("\\\\server\\folder")), "\\\\server\\folder")
                self.assertEqual(str(path_type("\\\\\\\\server\\folder/")), "\\\\server\\folder")
                self.assertEqual(str(path_type("\\\\\\server\\\\folder")), "\\\\server\\folder")
                self.assertEqual(str(path_type("\\\\wsl.localhost\\path\\to\\file")), "\\\\wsl.localhost\\path\\to\\file")
                self.assertEqual(
                    str(path_type("\\\\wsl.localhost\\path\\to\\file with space ")),
                    "\\\\wsl.localhost\\path\\to\\file with space ",
                )

                # Special Characters
                self.assertEqual(str(path_type("C:/Users/test folder/")), "C:\\Users\\test folder")
                self.assertEqual(str(path_type("C:/Users/üser/")), "C:\\Users\\üser")
                self.assertEqual(str(path_type("C:/Users/test\\nfolder/")), "C:\\Users\\test\\nfolder")

                # Joinpath, rtruediv, truediv
                self.assertEqual(str(path_type("C:/Users").joinpath("test/")), "C:\\Users\\test")
                self.assertEqual(str(path_type("C:/Users") / "test/"), "C:\\Users\\test")
                self.assertEqual(str(path_type("C:/Users").__truediv__("test/")), "C:\\Users\\test")

                # Bizarre Scenarios
                self.assertEqual(str(path_type("")), ".")
                self.assertEqual(str(path_type("//")), ".")
                self.assertEqual(str(path_type("///")), ".")
                self.assertEqual(str(path_type("C:")), "C:")
                self.assertEqual(str(path_type("C:/./Users/../test/")), "C:\\Users\\..\\test")
                self.assertEqual(str(path_type("~/folder/")), "~\\folder")

    def test_custom_path_edge_cases_os_specific(self):
        # sourcery skip: extract-duplicate-method
        for path_type in (CaseAwarePath, CustomPath, CustomPurePath):
            with self.subTest(path_type=path_type):
                # Absolute vs Relative Paths
                self.assertEqual(str(path_type("C:/")), "C:")
                self.assertEqual(str(path_type("C:\\")), "C:")
                self.assertEqual(str(path_type("C:/Users/test/")), "C:/Users/test".replace("/", os.sep))
                self.assertEqual(str(path_type("C:/Users/test\\")), "C:/Users/test".replace("/", os.sep))
                self.assertEqual(str(path_type("C://Users///test")), "C:/Users/test".replace("/", os.sep))
                self.assertEqual(str(path_type("C:/Users/TEST/")), "C:/Users/TEST".replace("/", os.sep))

                # Network Paths
                if os.name == "posix":
                    self.assertEqual(str(path_type("\\\\server\\folder")), "/server/folder")
                    self.assertEqual(str(path_type("\\\\\\\\server\\folder/")), "/server/folder")
                    self.assertEqual(str(path_type("\\\\\\server\\\\folder")), "/server/folder")
                    self.assertEqual(str(path_type("\\\\wsl.localhost\\path\\to\\file")), "/wsl.localhost/path/to/file")
                    self.assertEqual(
                        str(path_type("\\\\wsl.localhost\\path\\to\\file with space ")),
                        "/wsl.localhost/path/to/file with space ",
                    )
                elif os.name == "nt":
                    self.assertEqual(str(path_type("\\\\server\\folder")), "\\\\server\\folder")
                    self.assertEqual(str(path_type("\\\\\\\\server\\folder/")), "\\\\server\\folder")
                    self.assertEqual(str(path_type("\\\\\\server\\\\folder")), "\\\\server\\folder")
                    self.assertEqual(str(path_type("\\\\wsl.localhost\\path\\to\\file")), "\\\\wsl.localhost\\path\\to\\file")
                    self.assertEqual(
                        str(path_type("\\\\wsl.localhost\\path\\to\\file with space ")),
                        "\\\\wsl.localhost\\path\\to\\file with space ",
                    )

                # Special Characters
                self.assertEqual(str(path_type("C:/Users/test folder/")), "C:/Users/test folder".replace("/", os.sep))
                self.assertEqual(str(path_type("C:/Users/üser/")), "C:/Users/üser".replace("/", os.sep))
                self.assertEqual(str(path_type("C:/Users/test\\nfolder/")), "C:/Users/test/nfolder".replace("/", os.sep))

                # Joinpath, rtruediv, truediv
                self.assertEqual(str(path_type("C:/Users").joinpath("test/")), "C:/Users/test".replace("/", os.sep))
                self.assertEqual(str(path_type("C:/Users") / "test/"), "C:/Users/test".replace("/", os.sep))
                self.assertEqual(str(path_type("C:/Users").__truediv__("test/")), "C:/Users/test".replace("/", os.sep))

                # Bizarre Scenarios
                self.assertEqual(str(path_type("")), ".")
                self.assertEqual(str(path_type("C:/./Users/../test/")), "C:/Users/../test".replace("/", os.sep))
                self.assertEqual(str(path_type("C:\\.\\Users\\..\\test\\")), "C:/Users/../test".replace("/", os.sep))
                self.assertEqual(str(path_type("~/folder/")), "~/folder".replace("/", os.sep))
                self.assertEqual(str(path_type("C:")), "C:".replace("/", os.sep))
                if os.name == "posix":
                    self.assertEqual(str(path_type("//")), "/")
                    self.assertEqual(str(path_type("///")), "/")
                elif os.name == "nt":
                    self.assertEqual(str(path_type("//")), ".")
                    self.assertEqual(str(path_type("///")), ".")


if __name__ == "__main__":
    unittest.main()
