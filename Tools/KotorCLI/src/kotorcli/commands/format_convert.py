"""Format conversion command implementations for KotorCLI.

This module provides CLI commands for converting between different file formats
(GFF↔XML, TLK↔XML, SSF↔XML, 2DA↔CSV, etc.) using PyKotor utilities.
"""
from __future__ import annotations

import pathlib
from argparse import Namespace

from loggerplus import RobustLogger as Logger  # type: ignore[import-untyped, note]
from pykotor.tools.conversions import (
    convert_2da_to_csv,
    convert_csv_to_2da,
    convert_gff_to_json,
    convert_gff_to_xml,
    convert_json_to_gff,
    convert_ssf_to_xml,
    convert_tlk_to_json,
    convert_tlk_to_xml,
    convert_xml_to_gff,
    convert_xml_to_ssf,
    convert_xml_to_tlk,
)


def cmd_gff2xml(args: Namespace, logger: Logger) -> int:
    """Convert GFF file to XML format.

    References:
    ----------
        vendor/xoreos-tools/src/xml/gffdumper.cpp - GFF to XML
    """
    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output) if args.output else input_path.with_suffix(".xml")

    try:
        convert_gff_to_xml(input_path, output_path)
        logger.info(f"Converted {input_path.name} to {output_path.name}")  # noqa: G004
    except Exception:
        logger.exception(f"Failed to convert {input_path}")  # noqa: G004
        return 1
    else:
        return 0


def cmd_xml2gff(args: Namespace, logger: Logger) -> int:
    """Convert XML file to GFF format.

    References:
    ----------
        vendor/xoreos-tools/src/xml/gffcreator.cpp - XML to GFF
    """
    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output) if args.output else input_path.with_suffix(".gff")

    try:
        convert_xml_to_gff(input_path, output_path, gff_content_type=args.type if hasattr(args, "type") else None)
        logger.info(f"Converted {input_path.name} to {output_path.name}")  # noqa: G004
    except Exception:
        logger.exception(f"Failed to convert {input_path}")  # noqa: G004
        return 1
    else:
        return 0


def cmd_tlk2xml(args: Namespace, logger: Logger) -> int:
    """Convert TLK file to XML format.

    References:
    ----------
        vendor/xoreos-tools/src/tlk2xml.cpp - TLK to XML
    """
    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output) if args.output else input_path.with_suffix(".xml")

    try:
        convert_tlk_to_xml(input_path, output_path)
        logger.info(f"Converted {input_path.name} to {output_path.name}")  # noqa: G004
    except Exception:
        logger.exception(f"Failed to convert {input_path}")  # noqa: G004
        return 1
    else:
        return 0


def cmd_xml2tlk(args: Namespace, logger: Logger) -> int:
    """Convert XML file to TLK format.

    References:
    ----------
        vendor/xoreos-tools/src/xml2tlk.cpp - XML to TLK
    """
    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output) if args.output else input_path.with_suffix(".tlk")

    try:
        convert_xml_to_tlk(input_path, output_path)
        logger.info(f"Converted {input_path.name} to {output_path.name}")  # noqa: G004
    except Exception:
        logger.exception(f"Failed to convert {input_path}")  # noqa: G004
        return 1
    else:
        return 0


def cmd_ssf2xml(args: Namespace, logger: Logger) -> int:
    """Convert SSF file to XML format."""
    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output) if args.output else input_path.with_suffix(".xml")

    try:
        convert_ssf_to_xml(input_path, output_path)
        logger.info(f"Converted {input_path.name} to {output_path.name}")  # noqa: G004
    except Exception:
        logger.exception(f"Failed to convert {input_path}")  # noqa: G004
        return 1
    else:
        return 0


def cmd_xml2ssf(args: Namespace, logger: Logger) -> int:
    """Convert XML file to SSF format."""
    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output) if args.output else input_path.with_suffix(".ssf")

    try:
        convert_xml_to_ssf(input_path, output_path)
        logger.info(f"Converted {input_path.name} to {output_path.name}")  # noqa: G004
    except Exception:
        logger.exception(f"Failed to convert {input_path}")  # noqa: G004
        return 1
    else:
        return 0


def cmd_2da2csv(args: Namespace, logger: Logger) -> int:
    """Convert 2DA file to CSV format.

    References:
    ----------
        vendor/xoreos-tools/src/convert2da.cpp - 2DA to CSV
    """
    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output) if args.output else input_path.with_suffix(".csv")

    try:
        convert_2da_to_csv(input_path, output_path, delimiter=args.delimiter if hasattr(args, "delimiter") else ",")
        logger.info(f"Converted {input_path.name} to {output_path.name}")  # noqa: G004
    except Exception:
        logger.exception(f"Failed to convert {input_path}")  # noqa: G004
        return 1
    else:
        return 0


def cmd_csv22da(args: Namespace, logger: Logger) -> int:
    """Convert CSV file to 2DA format."""
    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output) if args.output else input_path.with_suffix(".2da")

    try:
        convert_csv_to_2da(input_path, output_path, delimiter=args.delimiter if hasattr(args, "delimiter") else ",")
        logger.info(f"Converted {input_path.name} to {output_path.name}")  # noqa: G004
    except Exception:
        logger.exception(f"Failed to convert {input_path}")  # noqa: G004
        return 1
    else:
        return 0


def cmd_gff2json(args: Namespace, logger: Logger) -> int:
    """Convert GFF file to JSON format."""
    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output) if args.output else input_path.with_suffix(".json")

    try:
        convert_gff_to_json(input_path, output_path)
        logger.info(f"Converted {input_path.name} to {output_path.name}")  # noqa: G004
    except Exception:
        logger.exception(f"Failed to convert {input_path}")  # noqa: G004
        return 1
    else:
        return 0


def cmd_json2gff(args: Namespace, logger: Logger) -> int:
    """Convert JSON file to GFF format."""
    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output) if args.output else input_path.with_suffix(".gff")

    try:
        convert_json_to_gff(input_path, output_path, gff_content_type=args.type if hasattr(args, "type") else None)
        logger.info(f"Converted {input_path.name} to {output_path.name}")  # noqa: G004
    except Exception:
        logger.exception(f"Failed to convert {input_path}")  # noqa: G004
        return 1
    else:
        return 0


def cmd_tlk2json(args: Namespace, logger: Logger) -> int:
    """Convert TLK file to JSON format."""
    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output) if args.output else input_path.with_suffix(".json")

    try:
        convert_tlk_to_json(input_path, output_path)
        logger.info(f"Converted {input_path.name} to {output_path.name}")  # noqa: G004
    except Exception:
        logger.exception(f"Failed to convert {input_path}")  # noqa: G004
        return 1
    else:
        return 0

