"""Key pack command implementation - create KEY files from directories."""
from __future__ import annotations

import pathlib
from argparse import Namespace
from typing import TYPE_CHECKING

from pykotor.tools.archives import create_key_from_directory

if TYPE_CHECKING:
    from logging import Logger


def cmd_key_pack(args: Namespace, logger: Logger) -> int:
    """Handle key-pack command - create KEY file from directory containing BIF files.

    Args:
    ----
        args: Parsed command line arguments
        logger: Logger instance

    Returns:
    -------
        Exit code (0 for success, non-zero for error)
    """
    input_dir = pathlib.Path(args.directory)
    bif_dir = pathlib.Path(args.bif_dir) if hasattr(args, "bif_dir") and args.bif_dir else input_dir
    output_path = pathlib.Path(args.output)

    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")  # noqa: G004
        return 1

    if not input_dir.is_dir():
        logger.error(f"Input path is not a directory: {input_dir}")  # noqa: G004
        return 1

    try:
        create_key_from_directory(
            input_dir,
            bif_dir,
            output_path,
            file_filter=args.filter if hasattr(args, "filter") else None,
        )
        logger.info(f"Created KEY file: {output_path}")  # noqa: G004

    except Exception:
        logger.exception("Failed to create KEY file")
        return 1
    else:
        return 0

