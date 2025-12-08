# This file is used to test the RobustLogger class. See __init__.py for the implementation.

from __future__ import annotations

try:
    from loggerplus import RobustLogger
except ImportError:
    # this error will happen when running from src without the pip package installed.
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: PTH120, PTH100
    from loggerplus import RobustLogger

# Example usage.
if __name__ == "__main__":
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
    raise RuntimeError("Test uncaught exception")
