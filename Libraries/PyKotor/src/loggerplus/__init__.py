"""
Async-capable drop-in for RobustLogger with non-blocking logging when an asyncio event loop is running.
Merged essentials from the legacy loggerplus (utf8 stream handling, rotating file support, context helpers)
but removed thread usage; uses asyncio queue and background task instead. Falls back to sync when no loop.
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Tuple

__all__ = ["RobustLogger", "configure_default_logging", "stdout_to_logger", "stderr_to_logger"]


# --------------------------------------------------------------------------- #
# Configuration helpers
# --------------------------------------------------------------------------- #
def configure_default_logging(level: int = logging.DEBUG, log_path: str | None = None) -> None:
    """
    Configure root logging once. Supports optional rotating file handler.
    """
    if logging.getLogger().handlers:
        return

    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if log_path:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(path, maxBytes=2_000_000, backupCount=2, encoding="utf-8")
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


# --------------------------------------------------------------------------- #
# Async queue-based logging (no threads)
# --------------------------------------------------------------------------- #
_queue: asyncio.Queue[Tuple[int, str, tuple[Any, ...], dict[str, Any]]] = asyncio.Queue()
_worker_task: asyncio.Task | None = None


def _ensure_worker(logger: logging.Logger) -> bool:
    """
    Ensure an asyncio worker is running to drain the queue.

    Returns True if async path is active, False if we should fall back to sync.
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
                    logger.log(level, msg, *args, **kwargs)
                except Exception:
                    # Last-resort: print to stderr synchronously to avoid silent loss
                    print(f"[loggerplus worker] failed to log: {msg}", file=sys.stderr)

        _worker_task = loop.create_task(_worker())
    return True


class RobustLogger(logging.Logger):
    """
    Minimal async-friendly logger with familiar debug/info/warning/error/exception.
    """

    def __init__(self, name: str = "root") -> None:
        configure_default_logging()
        super().__init__(name)

    def _async_or_sync(self, level: int, msg: str, *args: Any, **kwargs: Any) -> None:
        if _ensure_worker(self):
            try:
                _queue.put_nowait((level, msg, args, kwargs))
                return
            except Exception:
                pass
        super().log(level, msg, *args, **kwargs)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        self._async_or_sync(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        self._async_or_sync(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        self._async_or_sync(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        self._async_or_sync(logging.ERROR, msg, *args, **kwargs)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        kwargs.setdefault("exc_info", True)
        self._async_or_sync(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        self._async_or_sync(logging.CRITICAL, msg, *args, **kwargs)


logging.setLoggerClass(RobustLogger)


# --------------------------------------------------------------------------- #
# Stream redirection helpers (stdout/stderr to logger) – kept minimal
# --------------------------------------------------------------------------- #
class _UTF8StreamWrapper:
    def __init__(self, original_stream: Any):
        self.original_stream = original_stream

    def write(self, message: Any) -> None:
        if self.original_stream is None:
            return
        if isinstance(message, str):
            message = message.encode("utf-8", errors="replace")
        self.original_stream.buffer.write(message)  # type: ignore[attr-defined]

    def flush(self) -> None:
        if self.original_stream is None:
            return
        self.original_stream.flush()

    def __getattr__(self, attr: str) -> Any:
        return getattr(self.original_stream, attr)


def _redirect_stream(log: logging.Logger, stream: Any, level: int) -> Any:
    wrapper = _UTF8StreamWrapper(stream)
    for handler in log.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setStream(wrapper)  # type: ignore[arg-type]
    return wrapper


def stdout_to_logger(logger_name: str = "stdout", level: int = logging.INFO) -> None:
    logger = logging.getLogger(logger_name)
    sys.stdout = _StdLogger(logger, sys.stdout, level)  # type: ignore[assignment]


def stderr_to_logger(logger_name: str = "stderr", level: int = logging.ERROR) -> None:
    logger = logging.getLogger(logger_name)
    sys.stderr = _StdLogger(logger, sys.stderr, level)  # type: ignore[assignment]


class _StdLogger:
    def __init__(self, logger: logging.Logger, original: Any, level: int):
        self.logger = logger
        self.original = original
        self.level = level
        self.configure_stream()
        self.buffer: str = ""

    def configure_stream(self) -> None:
        _redirect_stream(self.logger, self.original, self.level)

    def write(self, message: str) -> None:
        self.buffer += message
        while os.linesep in self.buffer:
            line, self.buffer = self.buffer.split(os.linesep, 1)
            if line:
                self.logger.log(self.level, line)

    def flush(self) -> None:
        if self.buffer:
            self.logger.log(self.level, self.buffer.rstrip(os.linesep))
            self.buffer = ""



