"""List-archive command implementation - list contents of archive files."""
from __future__ import annotations

import pathlib
from argparse import Namespace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from logging import Logger

from pykotor.tools.archives import list_bif, list_erf, list_key, list_rim

# KotorCLI-level filter supports matching either "resref" or "resref.ext".
from kotorcli.archive_filter import matches_resource_name

# vendor references:
# vendor/xoreos-tools/src/unkeybif.cpp - KEY/BIF listing
# vendor/xoreos-tools/src/unerf.cpp - ERF listing
# vendor/xoreos-tools/src/unrim.cpp - RIM listing


def cmd_list_archive(args: Namespace, logger: Logger) -> int:  # noqa: PLR0911
    """Handle list-archive command - list contents of archive files.

    Supports:
    - KEY/BIF archives
    - RIM archives
    - ERF/MOD/SAV/HAK archives

    Args:
    ----
        args: Parsed command line arguments
        logger: Logger instance

    Returns:
    -------
        Exit code (0 for success, non-zero for error)
    """
    if not args.file:
        logger.error("No input file specified. Use --file <archive>")
        return 1

    input_path = pathlib.Path(args.file)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")  # noqa: G004
        return 1

    suffix = input_path.suffix.lower()
    logger.info(f"Listing contents of {suffix} archive: {input_path.name}")  # noqa: G004

    try:
        if suffix == ".key":
            return _list_key(input_path, args, logger)
        if suffix == ".bif":
            return _list_bif(input_path, args, logger)
        if suffix in (".rim",):
            return _list_rim(input_path, args, logger)
        if suffix in (".erf", ".mod", ".sav", ".hak"):
            return _list_erf(input_path, args, logger)
        logger.error(f"Unsupported archive type: {suffix}")  # noqa: G004
        logger.info("Supported types: .key, .bif, .rim, .erf, .mod, .sav, .hak")
    except Exception:
        logger.exception("Failed to list archive")
        return 1
    else:
        return 0


def _list_key(key_path: pathlib.Path, args: Namespace, logger: Logger) -> int:
    """List contents of KEY file and associated BIF files."""
    try:
        bif_files, resources = list_key(key_path)

        logger.info(f"KEY file: {key_path.name}")  # noqa: G004
        logger.info(f"  BIF files: {len(bif_files)}")  # noqa: G004
        logger.info(f"  Resources: {len(resources)}")  # noqa: G004

        if args.verbose:
            logger.info("\nBIF Files:")
            for i, bif_name in enumerate(bif_files):
                logger.info(f"  [{i}] {bif_name}")  # noqa: G004

        if args.resources or not args.bifs_only:
            logger.info("\nResources:")
            for resref, res_type, bif_index, res_index in resources:
                if args.filter and not matches_resource_name(resref, res_type, args.filter):
                    continue

                bif_name = bif_files[bif_index] if bif_index < len(bif_files) else "?"
                logger.info(f"  {resref}.{res_type} (BIF: {bif_name}, idx: {res_index})")  # noqa: G004

    except Exception:
        logger.exception("Failed to list KEY")
        return 1
    else:
        return 0


def _list_bif(bif_path: pathlib.Path, args: Namespace, logger: Logger) -> int:
    """List contents of a BIF file."""
    try:
        key_path = pathlib.Path(args.key_file) if args.key_file else bif_path.parent / "chitin.key"
        resources = list(list_bif(bif_path, key_path=key_path if key_path.exists() else None))

        logger.info(f"BIF file: {bif_path.name}")  # noqa: G004
        logger.info(f"  Resources: {len(resources)}")  # noqa: G004

        logger.info("\nResources:")
        for i, resource in enumerate(resources):
            resref = resource.resref.get() if resource.resref else f"resource_{i:05d}"
            res_type = resource.restype.extension if resource.restype else "bin"
            if args.filter and not matches_resource_name(resref, res_type, args.filter):
                continue

            if args.verbose:
                size = len(resource.data) if hasattr(resource, "data") else 0
                logger.info(f"  [{i}] {resref}.{res_type} ({size} bytes)")  # noqa: G004
            else:
                logger.info(f"  {resref}.{res_type}")  # noqa: G004

    except Exception:
        logger.exception("Failed to list BIF")
        return 1
    else:
        return 0


def _list_rim(rim_path: pathlib.Path, args: Namespace, logger: Logger) -> int:
    """List contents of a RIM archive."""
    try:
        resources = list(list_rim(rim_path))

        logger.info(f"RIM file: {rim_path.name}")  # noqa: G004
        logger.info(f"  Resources: {len(resources)}")  # noqa: G004

        logger.info("\nResources:")
        for resource in resources:
            resref = resource.resref.get() if resource.resref else "unknown"
            res_type = resource.restype.extension if resource.restype else "bin"
            if args.filter and not matches_resource_name(resref, res_type, args.filter):
                continue

            if args.verbose:
                size = len(resource.data) if hasattr(resource, "data") else 0
                logger.info(f"  {resref}.{res_type} ({size} bytes)")  # noqa: G004
            else:
                logger.info(f"  {resref}.{res_type}")  # noqa: G004

    except Exception:
        logger.exception("Failed to list RIM")
        return 1
    else:
        return 0


def _list_erf(erf_path: pathlib.Path, args: Namespace, logger: Logger) -> int:
    """List contents of an ERF/MOD/SAV/HAK archive."""
    try:
        resources = list(list_erf(erf_path))

        logger.info(f"ERF file: {erf_path.name}")  # noqa: G004
        logger.info(f"  Resources: {len(resources)}")  # noqa: G004

        logger.info("\nResources:")
        for resource in resources:
            resref = resource.resref.get() if resource.resref else "unknown"
            res_type = resource.restype.extension if resource.restype else "bin"
            if args.filter and not matches_resource_name(resref, res_type, args.filter):
                continue

            if args.verbose:
                size = len(resource.data) if hasattr(resource, "data") else 0
                logger.info(f"  {resref}.{res_type} ({size} bytes)")  # noqa: G004
            else:
                logger.info(f"  {resref}.{res_type}")  # noqa: G004

    except Exception:
        logger.exception("Failed to list ERF")
        return 1
    else:
        return 0

