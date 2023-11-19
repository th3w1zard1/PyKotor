from __future__ import annotations

import contextlib
import os
import pathlib
import platform
import re
import sys
import uuid
from typing import Union

PathElem = Union[str, os.PathLike]

class BasePurePath:
    """BasePath is a class created to fix some annoyances with pathlib, such as its refusal to resolve mixed/repeating/trailing slashes."""

    def __new__(cls, *args: PathElem, **kwargs):
        return args[0] if len(args) == 1 and isinstance(args[0], cls) else super().__new__(cls, *cls.parse_args(args), **kwargs)

    def __init__(self, *args, _called_from_pathlib=True):
        """Initializes a path object. This is used to unify python 3.7-3.11 with most of python 3.12's changes.

        Processing Logic:
            - Finds the next class in the MRO that defines __init__ and is not BasePurePath
            - Return immediately (do nothing here) if the next class with a __init__ is the object class
            - Gets the __init__ method from the found class
            - Parses args if called from pathlib and calls __init__ with parsed args
            - Else directly calls __init__ with passed args.
        """
        next_init_method_class = next(
            (cls for cls in self.__class__.mro() if "__init__" in cls.__dict__ and cls is not BasePurePath),
            self.__class__,
        )
        # Check if the class that defines the next __init__ is object
        if next_init_method_class is object:
            return

        # If not object, fetch the __init__ of that class
        init_method = next_init_method_class.__init__

        # Parse args if called from pathlib (Python 3.12+)
        if _called_from_pathlib:
            init_method(self, *self.parse_args(args))
        else:
            init_method(self, *args)

    @classmethod
    def parse_args(cls, args: tuple[PathElem, ...]) -> list[BasePurePath]:
        args_list = list(args)
        for i, arg in enumerate(args_list):
            if isinstance(arg, BasePurePath):
                continue  # do nothing if already our instance type
            formatted_path_str = cls._fix_path_formatting(cls._fspath_str(arg), cls._flavour.sep)  # type: ignore[attr-defined]

            # Create the pathlib class instance, ignore the type errors in super().__new__
            arg_pathlib_instance = super().__new__(cls, formatted_path_str)  # type: ignore[call-arg, reportGeneralTypeIssues]
            arg_pathlib_instance.__init__(formatted_path_str, _called_from_pathlib=False)  # type: ignore[misc]

            args_list[i] = arg_pathlib_instance

        return args_list  # type: ignore[return-value, reportGeneralTypeIssues]

    @classmethod
    def _create_instance(cls, *args, **kwargs):
        instance = cls.__new__(cls, *args, **kwargs)  # type: ignore  # noqa: PGH003
        instance.__init__(*args, **kwargs)
        return instance

    @staticmethod
    def _fspath_str(arg: object) -> str:
        """Convert object to a file system path string
        Args:
            arg: Object to convert to a file system path string
        Returns:
            str: File system path string
        - Check if arg is already a string
        - Check if arg has a __fspath__ method and call it
        - Raise TypeError if arg is neither string nor has __fspath__ method.
        """
        if isinstance(arg, str):
            return arg
        fspath_method = getattr(arg, "__fspath__", None)
        if fspath_method is not None:
            return fspath_method()
        msg = f"Object '{arg}' must be str or path-like object, but instead was '{type(arg)}'"
        raise TypeError(msg)

    # Call is_relative_to when using 'in' keyword
    def __contains__(self, other_path: os.PathLike | str):
        return self.is_relative_to(other_path, case_sensitive=False)

    def __str__(self):
        """Call _fix_path_formatting before returning the pathlib class's __str__ result.
        In Python 3.12, pathlib's __str__ methods will return '' instead of '.', so we return '.' in this instance for backwards compatibility.
        """
        str_result = self._fix_path_formatting(super().__str__(), self._flavour.sep)  # type: ignore[_flavour exists in children]
        return "." if str_result == "" else str_result

    def __fspath__(self):
        """Ensures any use of __fspath__ will call our __str__ method."""
        return str(self)

    def __truediv__(self, key: PathElem):
        """Appends a path part with the divider operator '/'.
        This method is called when the left side is self.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object or str path):
        """
        return self._create_instance(self, key)

    def __rtruediv__(self, key: PathElem):
        """Appends a path part with the divider operator '/'.
        This method is called when the right side is self.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object or str path):
        """
        return self._create_instance(key, self)

    def __add__(self, key: PathElem) -> str:
        """Implicitly converts the path to a str when used with the addition operator '+'.
        This method is called when the left side is self.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object or str path):
        """
        return str(self) + str(key)

    def __radd__(self, key: PathElem) -> str:
        """Implicitly converts the path to a str when used with the addition operator '+'.
        This method is called when the right side is self.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object or str path):
        """
        return str(key) + str(self)

    def as_posix(self):
        """Convert path to a POSIX path.

        Args:
        ----
            self: Path object
        Returns:
            str: POSIX representation of the path
        - Call as_posix() on the Path object to get the POSIX path string
        - Pass the result to _fix_path_formatting() to normalize the path format. This is done to fix any known bugs with the pathlib library.
        """
        return self._fix_path_formatting(super().as_posix(), slash="/")

    def joinpath(self, *args: PathElem):
        """Appends one or more path-like objects and/or relative paths to self.

        If any path being joined is already absolute, it will override and replace self instead of join us.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object or str path):
        """
        return self._create_instance(self, *args)

    def add_suffix(self, extension: str):
        """Initialize a new path object with the added extension. Similar to with_suffix, but doesn't replace existing extensions."""
        if not isinstance(extension, str):
            return NotImplemented
        return self._create_instance(str(self) + extension)

    def is_relative_to(self, other: PathElem, case_sensitive=True) -> bool:
        """Checks if self is relative to other
        Args:
            self: Path to check
            other: Path to check against
            case_sensitive: Whether to do case-sensitive comparison
        Returns:
            bool: Whether self is relative to other
        Processing Logic:
            - Resolve self and other if they are Path objects
            - Convert self and other to strings
            - Lowercase strings on Windows or if case_sensitive is False
            - Check if self string starts with other string.
        """
        resolved_self = self
        if isinstance(self, Path):
            if not isinstance(other, Path):
                other = self.__class__(other)
            other = other.resolve()
            resolved_self = resolved_self.resolve()  # type: ignore[attr-defined]
        else:
            other = other if isinstance(other, PurePath) else PurePath(other)

        self_str, other_str = map(str, (resolved_self, other))
        if os.name == "nt" or not case_sensitive:
            self_str = self_str.lower()
            other_str = other_str.lower()
        return bool(self_str.startswith(other_str))

    def endswith(self, text: str | tuple[str, ...], case_sensitive: bool = False) -> bool:
        # If case sensitivity is not required, normalize the self string and the text to lower case
        """Checks if string ends with the specified suffix.

        Args:
        ----
            text: String or tuple of strings to check for suffix.
            case_sensitive: Whether comparison should be case sensitive.

        Returns:
        -------
            bool: True if string ends with the suffix, False otherwise.
        Processing Logic:
        - If case sensitivity is not required, normalize self and text to lower case
        - Normalize each string in the tuple if text is a tuple
        - Utilize Python's built-in endswith method to check for suffix.
        """
        if not case_sensitive:
            self_str = str(self).lower()

            # Normalize each string in the tuple if text is a tuple
            if isinstance(text, tuple):
                text = tuple(subtext.lower() for subtext in text)
            else:
                text = text.lower()
        else:
            self_str = str(self)

        # Utilize Python's built-in endswith method
        return self_str.endswith(text)

    @staticmethod
    def _fix_path_formatting(str_path: str, slash=os.sep) -> str:
        """Formats a path string.

        Args:
        ----
            str_path (str): The path string to format
            slash (str): The path separator character
        Returns:
            str: The formatted path string
        Processing Logic:
            1. Validate the slash character
            2. Strip quotes from the path
            3. Format Windows paths by replacing mixed slashes and normalizing slashes
            4. Format Unix paths by replacing mixed slashes and normalizing slashes
            5. Strip trailing slashes from the formatted path.
        """
        if slash not in ("\\", "/"):
            msg = f"Invalid slash str: '{slash}'"
            raise ValueError(msg)

        formatted_path: str = str_path.strip('"')
        if not formatted_path.strip():
            return formatted_path

        # For Windows paths
        if slash == "\\":
            # Fix mixed slashes, replacing all forwardslashes with backslashes
            formatted_path = formatted_path.replace("/", "\\")
            # Replace 3 or more leading slashes with two backslashes
            formatted_path = re.sub(r"^\\{3,}", r"\\\\", formatted_path)
            # Replace repeating non-leading slashes with a single backslash
            formatted_path = re.sub(r"(?<!^)\\+", r"\\", formatted_path)
        # For Unix-like paths
        elif slash == "/":
            # Fix mixed slashes, replacing all backslashes with forwardslashes
            formatted_path = formatted_path.replace("\\", "/")
            # Replace multiple forwardslash's with a single forwardslash
            formatted_path = re.sub(r"/{2,}", "/", formatted_path)

        # Strip any trailing slashes, don't call rstrip if the formatted path == "/"
        return formatted_path if len(formatted_path) == 1 else formatted_path.rstrip(slash)


class PurePath(BasePurePath, pathlib.PurePath):
    # pylint: disable-all
    _flavour = pathlib.PureWindowsPath._flavour if os.name == "nt" else pathlib.PurePosixPath._flavour  # type: ignore[attr-defined]


class PurePosixPath(BasePurePath, pathlib.PurePosixPath):
    pass


class PureWindowsPath(BasePurePath, pathlib.PureWindowsPath):
    pass


class BasePath(BasePurePath):
    # Safe rglob operation
    def safe_rglob(self, pattern: str):
        if not isinstance(self, Path):
            return NotImplemented
        with contextlib.suppress(Exception):
            yield from self.rglob(pattern)

    # Safe iterdir operation
    def safe_iterdir(self):
        if not isinstance(self, Path):
            return NotImplemented
        with contextlib.suppress(Exception):
            yield from self.iterdir()

    # Safe is_dir operation
    def safe_isdir(self) -> bool:
        if not isinstance(self, Path):
            return NotImplemented
        try:
            return self.is_dir()
        except Exception:  # noqa: BLE001
            return False

    # Safe is_file operation
    def safe_isfile(self) -> bool:
        if not isinstance(self, Path):
            return NotImplemented
        try:
            return self.is_file()
        except Exception:  # noqa: BLE001
            return False

    # Safe exists operation
    def safe_exists(self) -> bool:
        if not isinstance(self, Path):
            return NotImplemented
        try:
            return self.exists()
        except Exception:  # noqa: BLE001
            return False

    # Safe stat operation
    def safe_stat(self, *args, **kwargs):
        if not isinstance(self, Path):
            return NotImplemented
        try:
            return self.stat(*args, **kwargs)
        except Exception:  # noqa: BLE001
            return None

    # Safe open operation
    def safe_open(self, *args, **kwargs):
        if not isinstance(self, Path):
            return NotImplemented
        try:
            return self.open(*args, **kwargs)
        except Exception:  # noqa: BLE001
            return None

    def has_access(self, recurse=False) -> bool:
        """Check if we have access to the path.

        Args:
        ----
            recurse (bool): check access for all files inside of self. Only valid if self is a folder (default is False)

        Returns:
        -------
            True if path can be modified, False otherwise.
        """
        if not isinstance(self, Path):
            return NotImplemented
        try:
            path_obj = Path(self)  # prevents usage of CaseAwarePath's wrappers
            if path_obj.is_dir():  # sourcery skip: extract-method
                test_path: Path = path_obj / f"temp_test_file_{uuid.uuid4().hex}.tmp"
                with test_path.open("w") as f:
                    f.write("test")
                test_path.unlink()
                success = True
                if recurse:
                    for file_or_folder in path_obj.rglob("*"):
                        success &= file_or_folder.has_access()
                return success
            if path_obj.is_file():
                return os.access(path_obj, os.R_OK) and os.access(path_obj, os.W_OK)
        except Exception:  # noqa: BLE001
            return False
        return False

    def gain_access(self, mode=0o777, owner_uid=-1, owner_gid=-1, recurse=True):
        if not isinstance(self, Path):
            return NotImplemented
        path_obj = Path(self)  # prevents usage of CaseAwarePath's wrappers
        # (Unix) Gain ownership of the folder
        if os.name != "nt" and (owner_uid != -1 or owner_gid != -1) and not path_obj.has_access():
            try:
                os.chown(path_obj, owner_uid, owner_gid)
            except Exception as e:  # noqa: BLE001
                print(f"Error during chown for {path_obj!s}: {e}")

        # chmod the folder
        if not path_obj.has_access():
            try:
                path_obj.chmod(mode)
            except Exception as e:  # noqa: BLE001
                print(f"Error during chmod for {path_obj!s}: {e}")

        # TODO: prompt the user and gain access with os-native methods.
        if not path_obj.has_access():
            try:
                if platform.system() == "Darwin":
                    path_obj.request_mac_permission()
                elif sys.platform == "Linux":
                    path_obj.request_linux_permission()
                elif sys.platform == "Windows":
                    path_obj.request_windows_permission()

            except Exception as e:  # noqa: BLE001
                print(f"Error during platform-specific permission request for {path_obj!s}: {e}")

        success: bool = path_obj.has_access()
        try:
            if recurse and path_obj.is_dir():
                for child in path_obj.iterdir():
                    success &= child.gain_access(mode, owner_uid, owner_gid)
        except Exception as e:  # noqa: BLE001
            print(f"Error gaining access for children of {path_obj!s}: {e}")
            success = False

        return success


class Path(BasePath, pathlib.Path):
    # pylint: disable-all
    _flavour = pathlib.PureWindowsPath._flavour if os.name == "nt" else pathlib.PurePosixPath._flavour  # type: ignore[attr-defined]


class PosixPath(BasePath, pathlib.PosixPath):
    pass


class WindowsPath(BasePath, pathlib.WindowsPath):
    pass
