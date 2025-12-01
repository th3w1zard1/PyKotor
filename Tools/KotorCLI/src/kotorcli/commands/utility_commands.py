"""Utility command implementations for KotorCLI.

This module provides CLI commands for utility operations (diff, grep, stats, validate, merge).
"""
from __future__ import annotations

import pathlib
from argparse import Namespace

from loggerplus import RobustLogger as Logger  # type: ignore[import-untyped]
from pykotor.resource.formats.gff.gff_auto import read_gff, write_gff
from pykotor.resource.formats.gff.gff_data import GFF
from pykotor.tools.utilities import diff_files, get_file_stats, grep_in_file, validate_file


def cmd_diff(args: Namespace, logger: Logger) -> int:
    """Compare two files and show differences.

    Supports GFF, 2DA, TLK files with structured comparison.

    References:
    ----------
        Tools/KotorDiff/src/kotordiff/differ.py
        Libraries/PyKotor/src/pykotor/tslpatcher/diff/structured.py
    """
    file1_path = pathlib.Path(args.file1)
    file2_path = pathlib.Path(args.file2)
    output_path = pathlib.Path(args.output) if args.output else None

    try:
        diff_text = diff_files(file1_path, file2_path, output_path=output_path, context_lines=args.context)

        if output_path:
            logger.info(f"Diff written to {output_path}")  # noqa: G004
        else:
            print(diff_text)  # noqa: T201

        return 0
    except Exception:
        logger.exception("Failed to generate diff")
        return 1


def cmd_grep(args: Namespace, logger: Logger) -> int:
    """Search for patterns in files.

    Supports text files and structured formats (GFF, 2DA, TLK).

    References:
    ----------
        vendor/xoreos-tools/ - grep-like utilities
    """
    file_path = pathlib.Path(args.file)

    try:
        matches = grep_in_file(file_path, args.pattern, case_sensitive=args.case_sensitive)

        if not matches:
            return 0  # No matches found (not an error)

        for line_num, line_text in matches:
            if args.line_numbers:
                print(f"{file_path}:{line_num}:{line_text}")  # noqa: T201
            else:
                print(line_text)  # noqa: T201

        return 0
    except Exception:
        logger.exception(f"Failed to search {file_path}")  # noqa: G004
        return 1


def cmd_stats(args: Namespace, logger: Logger) -> int:
    """Show statistics about a file.

    References:
    ----------
        vendor/xoreos-tools/ - File analysis utilities
    """
    file_path = pathlib.Path(args.file)

    try:
        stats = get_file_stats(file_path)

        logger.info(f"File: {stats.get('path', file_path)}")  # noqa: G004
        logger.info(f"Size: {stats.get('size', 0)} bytes")  # noqa: G004

        if "type" in stats:
            logger.info(f"Type: {stats['type']}")  # noqa: G004

        # Format-specific stats
        if stats.get("type") == "GFF":
            logger.info(f"Fields: {stats.get('field_count', 0)}")  # noqa: G004
        elif stats.get("type") == "2DA":
            logger.info(f"Rows: {stats.get('row_count', 0)}")  # noqa: G004
            logger.info(f"Columns: {stats.get('column_count', 0)}")  # noqa: G004
        elif stats.get("type") == "TLK":
            logger.info(f"Strings: {stats.get('string_count', 0)}")  # noqa: G004

        return 0
    except Exception:
        logger.exception(f"Failed to get stats for {file_path}")  # noqa: G004
        return 1


def cmd_validate(args: Namespace, logger: Logger) -> int:
    """Validate file format and structure."""
    file_path = pathlib.Path(args.file)

    try:
        is_valid, message = validate_file(file_path)

        if is_valid:
            logger.info(f"{file_path}: {message}")  # noqa: G004
            return 0
        logger.error(f"{file_path}: {message}")  # noqa: G004
        return 1
    except Exception:
        logger.exception(f"Failed to validate {file_path}")  # noqa: G004
        return 1


def cmd_merge(args: Namespace, logger: Logger) -> int:
    """Merge two GFF files.

    Merges fields from source file into target file, adding missing fields.
    Currently only supports GFF files.

    References:
    ----------
        Libraries/PyKotor/src/pykotor/resource/formats/gff/gff_data.py - GFFStruct.merge()
    """
    target_path = pathlib.Path(args.target)
    source_path = pathlib.Path(args.source)
    output_path = pathlib.Path(args.output) if args.output else target_path

    try:
        # Read both GFF files
        target_gff: GFF = read_gff(target_path)
        source_gff: GFF = read_gff(source_path)

        # Merge root structs
        target_gff.root.merge(source_gff.root)

        # Write merged result
        write_gff(target_gff, output_path)
        logger.info(f"Merged {source_path.name} into {target_path.name}, saved to {output_path.name}")  # noqa: G004
        return 0
    except Exception:
        logger.exception("Failed to merge files")
        return 1

