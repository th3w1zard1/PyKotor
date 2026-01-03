"""Cat command implementation - display resource contents to stdout."""
from __future__ import annotations

import pathlib
import sys
from argparse import Namespace
from typing import TYPE_CHECKING

from pykotor.tools.archives import get_resource_from_archive

if TYPE_CHECKING:
    from logging import Logger


def cmd_cat(args: Namespace, logger: Logger) -> int:
    """Handle cat command - display resource contents to stdout.

    Args:
    ----
        args: Parsed command line arguments
        logger: Logger instance

    Returns:
    -------
        Exit code (0 for success, non-zero for error)
    """
    archive_path = pathlib.Path(args.archive)
    resref = args.resource
    restype = args.type if hasattr(args, "type") else None

    if not archive_path.exists():
        logger.error(f"Archive file not found: {archive_path}")  # noqa: G004
        return 1

    try:
        resource_data = get_resource_from_archive(archive_path, resref, restype)

        if resource_data is None:
            logger.error(f"Resource not found: {resref}")  # noqa: G004
            if restype:
                logger.error(f"  Type: {restype}")  # noqa: G004
            return 1

        # Output to stdout
        # Try to decode as text first, fall back to binary
        try:
            text = resource_data.decode("utf-8", errors="replace")
            sys.stdout.write(text)
            if not text.endswith("\n"):
                sys.stdout.write("\n")
        except Exception:
            # Binary data - write as-is
            sys.stdout.buffer.write(resource_data)

    except Exception:
        logger.exception("Failed to read resource")
        return 1
    else:
        return 0

