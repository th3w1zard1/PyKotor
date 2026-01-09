"""Archive creation command implementation for KotorCLI.

This module provides CLI commands for creating archives (ERF, RIM) from directories.
"""
from __future__ import annotations

import pathlib
from argparse import Namespace

from loggerplus import RobustLogger as Logger  # type: ignore[import-untyped, note]
from pykotor.tools.archives import create_erf_from_directory, create_rim_from_directory


def cmd_create_archive(args: Namespace, logger: Logger) -> int:
    """Create an archive (ERF, RIM) from a directory of files.

    References:
    ----------
        KotOR I (swkotor.exe) / KotOR II (swkotor2.exe):
            - ERF structures loaded via CResERF class
            - See Libraries/PyKotor/src/pykotor/resource/formats/erf/ for ERF format references
            - RIM structures are similar to ERF (see erf/io_erf.py for references)


    """
    input_dir = pathlib.Path(args.directory)
    output_path = pathlib.Path(args.output)

    if not input_dir.is_dir():
        logger.error(f"Input directory does not exist: {input_dir}")  # noqa: G004
        return 1

    try:
        archive_type = args.type.lower() if args.type else output_path.suffix.lower()

        if archive_type in (".erf", ".hak", ".mod", ".sav", "erf", "hak", "mod", "sav"):
            erf_type = archive_type.lstrip(".").upper()
            create_erf_from_directory(
                input_dir,
                output_path,
                erf_type=erf_type,
                file_filter=args.filter,
            )
            logger.info(f"Created {erf_type} archive: {output_path.name}")  # noqa: G004
        elif archive_type in (".rim", "rim"):
            create_rim_from_directory(
                input_dir,
                output_path,
                file_filter=args.filter,
            )
            logger.info(f"Created RIM archive: {output_path.name}")  # noqa: G004
        else:
            logger.error(f"Unsupported archive type: {archive_type}")  # noqa: G004
            return 1
    except Exception:
        logger.exception(f"Failed to create archive from {input_dir}")  # noqa: G004
        return 1
    else:
        return 0

