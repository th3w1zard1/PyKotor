"""This module is used to define the RobustLogger class and anything logging-related it uses."""

from __future__ import annotations

import logging
import multiprocessing
import os
import shutil
import sys
import threading
import time
import uuid

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager, suppress
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Tuple
import asyncio

try:
    from utility.error_handling import format_exception_with_variables
except ImportError:
    # this error will happen when running from src without the pip package installed.
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: PTH120, PTH100
    from utility.error_handling import format_exception_with_variables

if TYPE_CHECKING:
    from io import TextIOWrapper
    from multiprocessing.process import BaseProcess
    from types import TracebackType

    from typing_extensions import Literal, Self  # pyright: ignore[reportMissingModuleSource]


class UTF8StreamWrapper:
    def __init__(self, original_stream: TextIOWrapper):
        self.original_stream: TextIOWrapper = original_stream

    def write(self, message):
        # Ensure message is a string, encode to UTF-8 with errors replaced,
        # then write to the original stream's buffer directly.
        # This fixes/works-around a bug in Python's logging module, observed in 3.8.10
        if self.original_stream is None:  # windowed mode PyInstaller
            return
        if isinstance(message, str):
            message = message.encode("utf-8", errors="replace")
        self.original_stream.buffer.write(message)

    def flush(self):
        if self.original_stream is None:  # windowed mode PyInstaller
            return
        self.original_stream.flush()

    def __getattr__(self, attr):
        # Delegate any other method calls to the original stream
        return getattr(self.original_stream, attr)


# region threading

# Global lock for thread-safe operations
LOGGING_LOCK = threading.Lock()
THREAD_LOCAL = threading.local()
THREAD_LOCAL.is_logging = False


@contextmanager
def logging_context():
    global LOGGING_LOCK  # noqa: PLW0602
    with LOGGING_LOCK:
        prev_state = getattr(THREAD_LOCAL, "is_logging", False)
        THREAD_LOCAL.is_logging = True

    try:
        yield
    finally:
        with LOGGING_LOCK:
            THREAD_LOCAL.is_logging = prev_state


# endregion
def get_this_child_pid() -> None | int:
    """Get our pid, if we're main process return None."""
    cur_process: BaseProcess = multiprocessing.current_process()
    return None if cur_process.name == "MainProcess" else cur_process.pid


class CustomPrintToLogger:
    def __init__(
        self,
        logger: logging.Logger,
        original: TextIOWrapper,
        log_type: Literal["stdout", "stderr"],
    ):
        self.original_out: TextIOWrapper = original
        self.log_type: Literal["stdout", "stderr"] = log_type
        self.logger: logging.Logger = logger
        self.configure_logger_stream()
        self.buffer: str = ""

    def isatty(self) -> Literal[False]:
        return False

    def configure_logger_stream(self):
        utf8_wrapper = UTF8StreamWrapper(self.original_out)
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setStream(utf8_wrapper)  # type: ignore[arg-type]

    def write(self, message: str):
        if getattr(THREAD_LOCAL, "is_logging", False):
            self.original_out.write(message)
        else:
            self.buffer += message
            while os.linesep in self.buffer:  # HACK: might have nuanced bugs, but it works for now.
                line, self.buffer = self.buffer.split(os.linesep, 1)
                self._log_message(line)

    def flush(self):
        if self.buffer:
            self._log_message(self.buffer)
            self.buffer = ""

    def _log_message(self, message: str):
        if message and message.strip():
            with logging_context():
                if self.log_type == "stderr":
                    self.logger.error(message.strip())
                else:
                    self.logger.debug(message.strip())


class SafeEncodingLogger(logging.Logger):
    """A custom logger that safely handles log messages containing characters
    that cannot be represented in the default system encoding. It overrides
    the standard log methods to encode and decode messages with a safe
    handling for unmappable characters.
    """

    def __init__(
        self,
        name: str,
        *args,
        **kwargs,
    ):
        super().__init__(name, *args, **kwargs)

    def _safe_log(self, level: int, msg: object, *args, **kwargs):
        try:
            # Encode to UTF-8 and decode back with 'replace' to handle unencodable chars
            safe_msg = str(msg).encode("utf-8", "replace").decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            safe_msg = f"SafeEncodingLogger: Failed to encode message: {e}"
        # Prefer async non-blocking logging if an event loop is running
        if _ensure_async_worker(self):
            try:
                _queue.put_nowait((level, safe_msg, args, kwargs))
                return
            except Exception:
                pass
        logging.Logger._log(self, level, safe_msg, args, **kwargs)

    def debug(self, msg: object, *args, **kwargs):
        if self.isEnabledFor(logging.DEBUG):
            self._safe_log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: object, *args, **kwargs):
        if self.isEnabledFor(logging.INFO):
            self._safe_log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: object, *args, **kwargs):
        if self.isEnabledFor(logging.WARNING):
            self._safe_log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: object, *args, **kwargs):
        if self.isEnabledFor(logging.ERROR):
            self._safe_log(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg: object, *args, **kwargs):
        if self.isEnabledFor(logging.CRITICAL):
            self._safe_log(logging.CRITICAL, msg, *args, **kwargs)


logging.setLoggerClass(SafeEncodingLogger)

# Async queue-based logging (no threads, non-blocking on main thread when an event loop exists)
_queue: asyncio.Queue[Tuple[int, str, tuple[Any, ...], dict[str, Any]]] = asyncio.Queue()
_worker_task: asyncio.Task | None = None


def _ensure_async_worker(logger: logging.Logger) -> bool:
    """
    Ensure an asyncio worker is running to drain the logging queue.

    Returns True if async path is active, False to fall back to synchronous logging.
    """
    global _worker_task
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return False

    if _worker_task is None or _worker_task.done():
        async def _worker() -> None:
            while True:
                level, msg, args, kwargs = await _queue.get()
                try:
                    logging.Logger._log(logger, level, msg, args, **kwargs)
                except Exception:
                    # As a last resort, write to stderr synchronously
                    print(f"[loggerplus async worker] failed to log: {msg}", file=sys.stderr)

        _worker_task = loop.create_task(_worker())
    return True


class CustomExceptionFormatter(logging.Formatter):
    sep = f"{os.linesep}----------------------------------------------------------------{os.linesep}"

    def formatException(
        self,
        ei: tuple[type[BaseException], BaseException, TracebackType | None] | tuple[None, None, None],
    ) -> str:
        etype, value, tb = ei
        if value is None:
            return self.sep + super().formatException(ei) + self.sep
        return self.sep + format_exception_with_variables(value, etype=etype, tb=tb) + self.sep

    def format(
        self,
        record: logging.LogRecord,
    ) -> str:
        result = super().format(record)
        #if record.exc_info:
        #    result += f"{os.linesep}{self.formatException(record.exc_info)}"
        return result


class ColoredConsoleHandler(logging.StreamHandler):
    try:
        import colorama  # type: ignore[import-untyped, reportMissingModuleSource]
        colorama.init()
        USING_COLORAMA = True
    except ImportError:
        USING_COLORAMA = False

    RESET_CODE: str = colorama.Style.RESET_ALL if USING_COLORAMA else "\033[0m"
    COLOR_CODES: ClassVar[dict[int, str]] = {
        logging.DEBUG: colorama.Fore.CYAN if USING_COLORAMA else "\033[0;36m",  # Cyan
        logging.INFO: colorama.Fore.WHITE if USING_COLORAMA else "\033[0;37m",  # White
        logging.WARNING: colorama.Fore.YELLOW if USING_COLORAMA else "\033[0;33m",  # Yellow
        logging.ERROR: colorama.Fore.RED if USING_COLORAMA else "\033[0;31m",  # Red
        logging.CRITICAL: colorama.Back.RED if USING_COLORAMA else "\033[1;41m",  # Red background
    }

    def format(self, record: logging.LogRecord) -> str:
        # Check if detailed formatting is requested
        detailed = getattr(record, "detailed", False)

        # Might be None according to their type hints, but in practice it's not.
        formatter: logging.Formatter | None = self.formatter
        if formatter is None:
            formatter = logging.Formatter()

        # Use detailed formatter if detailed flag is set, otherwise default
        orig_style = formatter._style  # noqa: SLF001
        if detailed:
            formatter = CustomExceptionFormatter(formatter._fmt, datefmt=formatter.datefmt, validate=True)  # noqa: SLF001  # pyright: ignore[reportArgumentType]
        else:
            formatter = logging.Formatter(formatter._fmt, datefmt=formatter.datefmt, validate=True)  # noqa: SLF001  # pyright: ignore[reportArgumentType]
        formatter._style = orig_style  # noqa: SLF001
        formatter._style.validate()  # noqa: SLF001

        msg = formatter.format(record)
        return f"{self.COLOR_CODES.get(record.levelno, '')}{msg}{self.RESET_CODE}"


class LogLevelFilter(logging.Filter):
    """Filters (allows) all the log messages at or above a specific level."""

    def __init__(
        self,
        passlevel: int,
        *,
        reject: bool = False,
    ):  # noqa: FBT001, FBT002
        super().__init__()
        self.passlevel: int = passlevel
        self.reject: bool = reject

    def filter(
        self,
        record: logging.LogRecord,
    ) -> bool:
        if self.reject:
            return record.levelno < self.passlevel
        return record.levelno >= self.passlevel


def _dir_requires_admin(
    dirpath: os.PathLike | str,
    *,
    ignore_errors: bool = True,
) -> bool:  # pragma: no cover
    """Check if a dir required admin permissions to write.

    If dir is a file test it's directory.
    """
    _dirpath = Path(dirpath)
    dummy_filepath = _dirpath / str(uuid.uuid4())
    try:
        with dummy_filepath.open("w"):
            ...
        _delete_any_file_or_folder(dummy_filepath, ignore_errors=False, missing_ok=False)
    except OSError:
        if ignore_errors:
            return True
        raise
    else:
        return False
    finally:
        _delete_any_file_or_folder(dummy_filepath, ignore_errors=True, missing_ok=True)


def _delete_any_file_or_folder(  # noqa: C901
    path: os.PathLike | str,
    *,
    ignore_errors: bool = True,
    missing_ok: bool = True
):
    path_obj = Path(path)
    isdir_func = _safe_isdir if ignore_errors else Path.is_dir
    isfile_func = _safe_isfile if ignore_errors else Path.exists
    if not isfile_func(path_obj):
        if missing_ok:
            return
        import errno
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(path_obj))

    def _remove_any(x: Path):
        if isdir_func(x):
            shutil.rmtree(str(x), ignore_errors=ignore_errors)
        else:
            x.unlink(missing_ok=missing_ok)

    if sys.platform != "win32":
        _remove_any(path_obj)
    else:
        for i in range(100):
            try:
                _remove_any(path_obj)
            except Exception:  # noqa: PERF203, BLE001
                if not ignore_errors:
                    raise
                time.sleep(0.01)
            else:
                if not isfile_func(path_obj):
                    return
                print(f"File/folder {path_obj} still exists after {i} iterations! (remove_any)", file=sys.stderr)
        if not ignore_errors:  # should raise at this point.
            _remove_any(path_obj)


def get_log_directory(subdir: os.PathLike | str | None = None) -> Path:
    """Determine the best directory for logs based on availability and permissions."""
    def check(path: Path) -> Path:
        if not path.exists() or not path.is_dir():
            path.unlink(missing_ok=True)
            path.mkdir(parents=True, exist_ok=True)  # Attempt to create the fallback directory
        if _dir_requires_admin(path, ignore_errors=False):
            raise PermissionError(f"Directory '{path}' requires admin.")
        return path

    cwd = Path.cwd()
    subdir = Path("logs") if subdir is None else Path(subdir)
    try:
        return check(subdir)
    except Exception as e:  # noqa: BLE001
        _safe_print(f"Failed to init 'logs' dir in cwd '{cwd}': {e}")
        try:
            return check(cwd)
        except Exception as e2:  # noqa: BLE001
            _safe_print(f"Failed to init cwd fallback '{cwd}' as log directory: {e2}{os.linesep}original: {e}")
            return check(_get_fallback_log_dir())


def _get_fallback_log_dir() -> Path:
    """Determine a known good location based on the platform."""
    if sys.platform.startswith("win"):  # Use ProgramData for Windows, which is typically for application data for all users
        return Path(os.environ.get("PROGRAMDATA", "C:/ProgramData")) / "PyUtility"
    return Path.home() / ".pyutility"


def _safe_isfile(path: Path) -> bool:
    with suppress(Exception):
        return path.is_file()
    return False


def _safe_isdir(path: Path) -> bool:
    with suppress(Exception):
        return path.is_dir()
    return False


class _SpoofTypeAttributeAccess:
    def __init__(self, _some_type: type):
        self._some_type = _some_type
        self.original_getattribute = type.__getattribute__(_some_type, "__getattribute__")
        self.original_setattr = type.__getattribute__(_some_type, "__setattr__")
        self.metaclass = type.__getattribute__(_some_type, "__class__")

    def __enter__(self):
        if self.metaclass is type:
            type.__setattr__(self._some_type, "__getattribute__", type.__getattribute__)
            type.__setattr__(self._some_type, "__setattr__", type.__setattr__)
        else:
            self._nested_spoof = _SpoofTypeAttributeAccess(self.metaclass)
            self._nested_spoof.__enter__()
            type.__setattr__(self._some_type, "__getattribute__", type.__getattribute__)
            type.__setattr__(self._some_type, "__setattr__", type.__setattr__)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.metaclass is type:
            type.__setattr__(self._some_type, "__getattribute__", self.original_getattribute)
            type.__setattr__(self._some_type, "__setattr__", self.original_setattr)
        else:
            type.__setattr__(self._some_type, "__getattribute__", self.original_getattribute)
            type.__setattr__(self._some_type, "__setattr__", self.original_setattr)
            self._nested_spoof.__exit__(exc_type, exc_val, exc_tb)


class _SpoofObjectAttributeAccess:
    def __init__(self, _some_object: object):
        self._some_object = _some_object
        obj_class = object.__getattribute__(_some_object, "__class__")
        self.original_getattribute = type.__getattribute__(obj_class, "__getattribute__")
        self.original_setattr = type.__getattribute__(obj_class, "__setattr__")

    def __enter__(self):
        obj_class = object.__getattribute__(self._some_object, "__class__")
        type.__setattr__(obj_class, "__getattribute__", object.__getattribute__)
        type.__setattr__(obj_class, "__setattr__", object.__setattr__)

    def __exit__(self, exc_type, exc_val, exc_tb):
        obj_class = object.__getattribute__(self._some_object, "__class__")
        type.__setattr__(obj_class, "__getattribute__", self.original_getattribute)
        type.__setattr__(obj_class, "__setattr__", self.original_setattr)


class MetaLogger(type):
    def _create_instance(cls: type[RobustLogger]) -> RobustLogger:  # type: ignore[misc]
        instance = object.__new__(cls)
        object.__getattribute__(instance, "__new__")(cls)
        object.__getattribute__(instance, "__init__")()
        type.__setattr__(cls, "_singleton_instance", instance)
        return instance
    def __getattribute__(cls: type[RobustLogger], attr_name: str):  # type: ignore[misc]
        if attr_name.startswith("__") and attr_name.endswith("__"):
            return super().__getattribute__(attr_name)  # type: ignore[misc]
        instance: RobustLogger | None = type.__getattribute__(RobustLogger, "_singleton_instance")
        if instance is None:
            instance = MetaLogger._create_instance(cls)
        return getattr(instance, attr_name)

    def __call__(cls, *args, **kwargs) -> RobustLogger:
        """Handle calling the RobustLogger class."""
        instance: RobustLogger | None = type.__getattribute__(RobustLogger, "_singleton_instance")
        if instance is None:
            instance = MetaLogger._create_instance(cls)  # type: ignore[arg-type]
        if args or kwargs:
            instance.info(*args, **kwargs)
        return instance

def _safe_print(*args, file=sys.__stderr__, **kwargs):
    print(*args, **kwargs, file=file)
class RobustLogger(logging.Logger, metaclass=MetaLogger):  # noqa: N801
    """Setup a logger with some standard features.

    The goal is to have this be callable anywhere anytime regardless of whether a logger is setup yet.

    Args:
    ----
        use_level(int): Logging level to setup for this application.

    Returns:
    -------
        logging.Logger: The root logger with the specified handlers and formatters.
    """
    _singleton_instance: Self | None = None
    _wrapped_logger: logging.Logger = None  # type: ignore[assignment]

    def __reduce__(self) -> tuple[type[Self], tuple[()]]:
        return self.__class__, ()

    def __getattribute__(self, attr_name: str) -> Any:
        our_type: type[Self] = object.__getattribute__(self, "__class__")
        try:
            attr_value = super().__getattribute__(attr_name)
            if attr_name == "_robust_root_lock":
                return attr_value
            if object.__getattribute__(self, "_robust_root_lock"):  # noqa: FBT003
                return attr_value
            if (
                attr_value is not our_type
                and not isinstance(attr_value, our_type)
                and callable(attr_value)
            ):
                def wrapped(*args, **kwargs):
                    try:
                        object.__setattr__(self, "_robust_root_lock", True)
                    except Exception as e:  # noqa: BLE001
                        _safe_print(f"Exception when accessing attribute '{attr_name}': {e} ({e.__class__.__name__})")
                        #print(traceback.format_exc(), file=sys.__stderr__)  # too verbose for normal use, uncomment for debugging.
                    else:
                        return attr_value(*args, **kwargs)
                    finally:
                        object.__setattr__(self, "_robust_root_lock", False)
                return wrapped
        except AttributeError:
            raise
        except Exception as e:  # noqa: BLE001
            print(f"(Caught by RobustLogger!) Exception when accessing attribute '{attr_name}': {e}", file=sys.__stderr__)
            print(f"{e.__class__.__name__}: {e}", file=sys.__stderr__)
            return ""
        else:
            return attr_value

    def __getattr__(self, attr_name: str):
        logger = object.__getattribute__(self, "_wrapped_logger")
        if logger is None:
            object.__setattr__(self, "_singleton_instance", None)
            object.__getattribute__(self, "__init__")()
            logger = object.__getattribute__(self, "_wrapped_logger")
        assert logger is not None
        return object.__getattribute__(logger, attr_name)

    def __new__(cls) -> Self:
        """Responsible for handling the singleton instance."""
        def get_instance():
            try:
                return type.__getattribute__(cls, "_singleton_instance")
            except AttributeError:
                return None
        if get_instance() is None:  # pyright: ignore[reportCallIssue]
            type.__setattr__(cls, "_singleton_instance", super().__new__(cls))
        return get_instance()  # pyright: ignore[reportReturnType]

    def __init__(
        self,
        *args,  # handles when user used incorrect args
        override_stdout: bool = False,
        override_stderr: bool = False,
        log_on_main_thread: bool = False,
        **kwargs,  # handles when user used incorrect keyword args
    ):
        if kwargs:
            _safe_print(f"RobustLogger.__init__() got unexpected keyword arguments: {[*kwargs.keys()]!r}")
        cls = object.__getattribute__(self, "__class__")
        if not object.__getattribute__(cls, "_wrapped_logger"):
            type.__setattr__(
                cls,
                "_wrapped_logger",
                object.__getattribute__(self, "_setup_root_logger")(
                    # HACK: arguments could have a faulty __bool__ or __len__, use `is` to prevent magic methods from being called.
                    override_stdout=override_stdout is True,
                    override_stderr=override_stderr is True,
                    log_on_main_thread=log_on_main_thread is True,
                ),
            )

    def _setup_root_logger(
        self,
        *,
        override_stdout: bool = False,
        override_stderr: bool = False,
        log_on_main_thread: bool = False,
    ) -> logging.Logger:
        logger = logging.getLogger()
        object.__getattribute__(self, "advanced_configure_logger")(None, override_stdout=override_stdout, override_stderr=override_stderr)

        # The custom exception filter is slow, ensure logging does not happen on the main thread.
        if not log_on_main_thread:
            object.__setattr__(self, "_orig_log_func", logger._log)  # noqa: SLF001
            logger._log = object.__getattribute__(self, "_log")  # type: ignore[method-assign]  # noqa: SLF001


        return logger

    @staticmethod
    def advanced_configure_logger(
        name_or_logger: str | logging.Logger | None = None,
        *,
        override_stdout: bool = False,
        override_stderr: bool = False,
    ) -> logging.Logger:
        logger: logging.Logger = logging.getLogger(name_or_logger) if isinstance(name_or_logger, (str, None.__class__)) else name_or_logger
        if not logger.handlers:
            from utility.misc import is_debug_mode
            use_level = logging.DEBUG if is_debug_mode() else logging.INFO
            logger.setLevel(use_level)

            cur_process: BaseProcess = multiprocessing.current_process()
            console_format_str = "%(levelname)s(%(name)s): %(message)s"
            if cur_process.name == "MainProcess":
                log_dir = get_log_directory(subdir="logs")
                everything_log_file = "debug_pykotor.log"
                info_warning_log_file = "pykotor.log"
                error_critical_log_file = "errors_pykotor.log"
                exception_log_file = "exception_pykotor.log"
            else:
                log_dir = get_log_directory(subdir=f"logs/{cur_process.pid}")
                everything_log_file = f"debug_pykotor_{cur_process.pid}.log"
                info_warning_log_file = f"pykotor_{cur_process.pid}.log"
                error_critical_log_file = f"errors_pykotor_{cur_process.pid}.log"
                exception_log_file = f"exception_pykotor_{cur_process.pid}.log"
                console_format_str = f"PID={cur_process.pid} - {console_format_str}"

            console_handler = ColoredConsoleHandler()
            formatter = logging.Formatter(console_format_str)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

            # Redirect stdout and stderr
            if override_stdout:
                sys.stdout = CustomPrintToLogger(logger, sys.__stdout__, log_type="stdout")  # type: ignore[assignment]
            if override_stderr:
                sys.stderr = CustomPrintToLogger(logger, sys.__stderr__, log_type="stderr")  # type: ignore[assignment]

            default_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            exception_formatter = CustomExceptionFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

            # Handler for everything (DEBUG and above)
            if use_level == logging.DEBUG:
                everything_handler = RotatingFileHandler(str(log_dir / everything_log_file), maxBytes=20*1024*1024, backupCount=5, encoding="utf8")
                everything_handler.setLevel(logging.DEBUG)
                everything_handler.setFormatter(default_formatter)
                logger.addHandler(everything_handler)

            # Handler for INFO and WARNING
            info_warning_handler = RotatingFileHandler(str(log_dir / info_warning_log_file), maxBytes=20*1024*1024, backupCount=5, encoding="utf8")
            info_warning_handler.setLevel(logging.INFO)
            info_warning_handler.setFormatter(default_formatter)
            info_warning_handler.addFilter(LogLevelFilter(logging.ERROR, reject=True))
            logger.addHandler(info_warning_handler)

            # Handler for ERROR and CRITICAL
            error_critical_handler = RotatingFileHandler(str(log_dir / error_critical_log_file), maxBytes=20*1024*1024, backupCount=5, encoding="utf8")
            error_critical_handler.setLevel(logging.ERROR)
            error_critical_handler.addFilter(LogLevelFilter(logging.ERROR))
            error_critical_handler.setFormatter(default_formatter)
            logger.addHandler(error_critical_handler)

            # Handler for EXCEPTIONS (using CustomExceptionFormatter)
            exception_handler = RotatingFileHandler(str(log_dir / exception_log_file), maxBytes=20*1024*1024, backupCount=5, encoding="utf8")
            exception_handler.setLevel(logging.ERROR)
            exception_handler.addFilter(LogLevelFilter(logging.ERROR))
            exception_handler.setFormatter(exception_formatter)
            logger.addHandler(exception_handler)
        return logger

    @staticmethod
    def __call__(*args, **kwargs):
        # optional
        #_actual_logger: logging.Logger | None = object.__getattribute__(self, "_wrapped_logger")
        #if _actual_logger is None:
        #    object.__getattribute__(self, "__class__")()
        # return RobustLogger()
        return _safe_print(*args, **kwargs)


get_root_logger = RobustLogger  # deprecated, provided for backwards compatibility.


# Example usage
if __name__ == "__main__":
    import sys
    sys.setrecursionlimit(50)
    logger = RobustLogger()
    logger.debug("This is a debug message")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")
    RobustLogger.debug("This is a debug message, correctly handling a user forgetting to construct RobustLogger.")  # type: ignore[call-arg, arg-type]

    # Test various edge case
    RobustLogger("This is a test of __call__")  # type: ignore[call-arg]

    try:
        raise RuntimeError("Test caught exception")  # noqa: TRY301
    except RuntimeError:
        RobustLogger().exception("Message for a caught exception")
    #raise RuntimeError("Test uncaught exception")  # TODO: sys.excepthook support maybe?
