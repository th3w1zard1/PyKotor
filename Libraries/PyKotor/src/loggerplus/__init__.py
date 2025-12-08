"""
Async-capable drop-in replacement for loggerplus.RobustLogger used in PyKotor.

Design goals:
- Non-blocking logging when an asyncio event loop is running (no threading).
- Fallback to synchronous logging when no running loop is available.
- Preserve the familiar RobustLogger() usage with debug/info/warning/error/exception.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Tuple

__all__ = ["RobustLogger", "configure_default_logging"]


def configure_default_logging(level: int = logging.DEBUG) -> None:
    """
    Configure a simple root logger if none is configured.

    This keeps behavior predictable in tools/tests without requiring each caller
    to set up handlers.
    """
    if not logging.getLogger().handlers:
        logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


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
                logger.log(level, msg, *args, **kwargs)

        _worker_task = loop.create_task(_worker())
    return True


class RobustLogger(logging.Logger):
    """
    Minimal async-friendly logger with the same interface used across the project.
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
                # Fall back to sync if queue is unavailable for any reason
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


# Register RobustLogger class so logging.getLogger returns this type if desired
logging.setLoggerClass(RobustLogger)


