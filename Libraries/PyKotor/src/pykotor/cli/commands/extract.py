"""Extract command implementation - extract resources from various archive types."""
from __future__ import annotations

import pathlib
from argparse import Namespace
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from logging import Logger

from pykotor.tools.archives import extract_bif, extract_erf, extract_key_bif, extract_rim

from pykotor.cli.archive_filter import matches_resource_name


def _matches_filter(resource, pattern: str) -> bool:  # type: ignore[no-untyped-def]
    resref = resource.resref.get() if getattr(resource, "resref", None) else "unknown"
    ext = resource.restype.extension if getattr(resource, "restype", None) else "bin"
    return matches_resource_name(resref, ext, pattern)


def cmd_extract(args: Namespace, logger: Logger) -> int:
    """Handle extract command - extract resources from archives.

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

    output_dir = pathlib.Path(args.output) if args.output else pathlib.Path.cwd() / input_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    suffix = input_path.suffix.lower()
    logger.info(f"Extracting from {suffix} archive: {input_path.name}")  # noqa: G004

    # Dispatch to appropriate extractor function
    extractors: dict[str, Callable[[pathlib.Path, pathlib.Path, Namespace, Logger], int]] = {
        ".key": _extract_key,
        ".bif": _extract_bif,
        ".rim": _extract_rim,
    }
    # ERF variants share the same handler
    for erf_suffix in (".erf", ".mod", ".sav", ".hak"):
        extractors[erf_suffix] = _extract_erf

    extractor_func = extractors.get(suffix)
    if extractor_func is None:
        logger.error(f"Unsupported archive type: {suffix}")  # noqa: G004
        logger.info("Supported types: .key, .bif, .rim, .erf, .mod, .sav, .hak")
        return 1

    try:
        return extractor_func(input_path, output_dir, args, logger)
    except Exception:
        logger.exception("Failed to extract archive")
        return 1


def _extract_key(key_path: pathlib.Path, output_dir: pathlib.Path, args: Namespace, logger: Logger) -> int:
    """Extract resources from KEY/BIF archives."""
    try:
        extracted_count = 0
        seen_bifs: set[pathlib.Path] = set()

        for resource, output_file, bif_path in extract_key_bif(
            key_path,
            output_dir,
            bif_search_dir=key_path.parent,
            resource_filter=(
                (lambda r: _matches_filter(r, args.filter))
                if args.filter
                else None
            ),
        ):
            if bif_path not in seen_bifs:
                logger.info(f"Extracting from BIF: {bif_path.name}")  # noqa: G004
                seen_bifs.add(bif_path)

            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_bytes(resource.data)
            extracted_count += 1

        logger.info(f"Extracted {extracted_count} resources")  # noqa: G004
    except Exception:
        logger.exception("Failed to extract KEY/BIF")
        return 1
    else:
        return 0


def _extract_bif(bif_path: pathlib.Path, output_dir: pathlib.Path, args: Namespace, logger: Logger) -> int:
    """Extract resources from a BIF file (requires KEY for resource names)."""
    key_path = pathlib.Path(args.key_file) if args.key_file else bif_path.parent / "chitin.key"
    if not key_path.exists():
        logger.warning(f"KEY file not found: {key_path}. Resources will have numeric names.")  # noqa: G004

    try:
        extracted_count = 0
        for resource, output_file in extract_bif(
            bif_path,
            output_dir,
            key_path=key_path if key_path.exists() else None,
            resource_filter=(
                (lambda r: _matches_filter(r, args.filter))
                if args.filter and key_path.exists()
                else None
            ),
            filter_pattern=args.filter if not (args.filter and key_path.exists()) else None,
        ):
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_bytes(resource.data)
            extracted_count += 1

        logger.info(f"Extracted {extracted_count} resources")  # noqa: G004
    except Exception:
        logger.exception("Failed to extract BIF")
        return 1
    else:
        return 0


def _extract_rim(rim_path: pathlib.Path, output_dir: pathlib.Path, args: Namespace, logger: Logger) -> int:
    """Extract resources from a RIM archive."""
    try:
        extracted_count = 0
        for resource, output_file in extract_rim(
            rim_path,
            output_dir,
            resource_filter=(
                (lambda r: _matches_filter(r, args.filter))
                if args.filter
                else None
            ),
        ):
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_bytes(resource.data)
            extracted_count += 1

        logger.info(f"Extracted {extracted_count} resources from RIM archive")  # noqa: G004
    except Exception:
        logger.exception("Failed to extract RIM")
        return 1
    else:
        return 0


def _extract_erf(erf_path: pathlib.Path, output_dir: pathlib.Path, args: Namespace, logger: Logger) -> int:
    """Extract resources from an ERF/MOD/SAV/HAK archive."""
    try:
        extracted_count = 0
        for resource, output_file in extract_erf(
            erf_path,
            output_dir,
            resource_filter=(
                (lambda r: _matches_filter(r, args.filter))
                if args.filter
                else None
            ),
        ):
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_bytes(resource.data)
            extracted_count += 1

        logger.info(f"Extracted {extracted_count} resources from ERF archive")  # noqa: G004
    except Exception:
        logger.exception("Failed to extract ERF")
        return 1
    else:
        return 0
