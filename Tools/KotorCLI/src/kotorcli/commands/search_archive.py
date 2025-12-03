"""Search archive command implementation."""
from __future__ import annotations

import pathlib
from argparse import Namespace
from typing import TYPE_CHECKING

from pykotor.tools.archives import search_in_erf, search_in_rim

if TYPE_CHECKING:
    from logging import Logger


def cmd_search_archive(args: Namespace, logger: Logger) -> int:
    """Handle search-archive command - search for resources in archives.

    Args:
    ----
        args: Parsed command line arguments
        logger: Logger instance

    Returns:
    -------
        Exit code (0 for success, non-zero for error)
    """
    archive_path = pathlib.Path(args.file)

    if not archive_path.exists():
        logger.error(f"Archive file not found: {archive_path}")  # noqa: G004
        return 1

    suffix = archive_path.suffix.lower()

    try:
        matches = 0
        if suffix in (".erf", ".mod", ".sav", ".hak"):
            for resref, restype in search_in_erf(
                archive_path,
                args.pattern,
                case_sensitive=args.case_sensitive if hasattr(args, "case_sensitive") else False,
                search_content=args.search_content if hasattr(args, "search_content") else False,
            ):
                logger.info(f"{resref}.{restype}")  # noqa: G004
                matches += 1
        elif suffix == ".rim":
            for resref, restype in search_in_rim(
                archive_path,
                args.pattern,
                case_sensitive=args.case_sensitive if hasattr(args, "case_sensitive") else False,
                search_content=args.search_content if hasattr(args, "search_content") else False,
            ):
                logger.info(f"{resref}.{restype}")  # noqa: G004
                matches += 1
        else:
            logger.error(f"Unsupported archive type: {suffix}")  # noqa: G004
            return 1

        if matches == 0:
            logger.info("No matches found")
        else:
            logger.info(f"Found {matches} matches")  # noqa: G004

    except Exception:
        logger.exception("Failed to search archive")
        return 1
    else:
        return 0

