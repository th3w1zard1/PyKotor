"""Format conversion utility functions for KOTOR game resources.

This module provides reusable, abstract functions for converting between different
formats (GFF↔XML, TLK↔XML, SSF↔XML, 2DA↔CSV, etc.). These functions are tool-agnostic
and can be used by any application that needs format conversions.

References:
----------
    vendor/xoreos-tools/src/xml/gffdumper.cpp - GFF to XML
    vendor/xoreos-tools/src/xml/gffcreator.cpp - XML to GFF
    vendor/xoreos-tools/src/tlk2xml.cpp - TLK to XML
    vendor/xoreos-tools/src/xml2tlk.cpp - XML to TLK
    vendor/xoreos-tools/src/convert2da.cpp - 2DA to CSV
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pykotor.resource.formats.gff.gff_auto import read_gff, write_gff
from pykotor.resource.formats.ssf.ssf_auto import read_ssf, write_ssf
from pykotor.resource.formats.tlk.tlk_auto import read_tlk, write_tlk
from pykotor.resource.formats.twoda.twoda_auto import read_2da, write_2da
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.common.language import Language


def convert_gff_to_xml(input_path: Path, output_path: Path) -> None:
    """Convert a GFF file to XML format.

    Args:
    ----
        input_path: Path to the input GFF file (binary or JSON)
        output_path: Path to write the output XML file

    References:
    ----------
        vendor/xoreos-tools/src/xml/gffdumper.cpp
    """
    gff = read_gff(input_path)
    write_gff(gff, output_path, file_format=ResourceType.GFF_XML)


def convert_xml_to_gff(input_path: Path, output_path: Path, *, gff_content_type: str | None = None) -> None:
    """Convert an XML file to GFF format.

    Args:
    ----
        input_path: Path to the input XML file
        output_path: Path to write the output GFF file
        gff_content_type: Optional GFF content type (e.g., "IFO ", "UTC ") - auto-detected if None

    References:
    ----------
        vendor/xoreos-tools/src/xml/gffcreator.cpp
    """
    gff = read_gff(input_path, file_format=ResourceType.GFF_XML)
    write_gff(gff, output_path, file_format=ResourceType.GFF)


def convert_tlk_to_xml(input_path: Path, output_path: Path) -> None:
    """Convert a TLK file to XML format.

    Args:
    ----
        input_path: Path to the input TLK file
        output_path: Path to write the output XML file

    References:
    ----------
        vendor/xoreos-tools/src/tlk2xml.cpp
    """
    tlk = read_tlk(input_path)
    write_tlk(tlk, output_path, file_format=ResourceType.TLK_XML)


def convert_xml_to_tlk(input_path: Path, output_path: Path, *, language: Language | None = None) -> None:
    """Convert an XML file to TLK format.

    Args:
    ----
        input_path: Path to the input XML file
        output_path: Path to write the output TLK file
        language: Optional language specification - auto-detected from XML if None

    References:
    ----------
        vendor/xoreos-tools/src/xml2tlk.cpp
    """
    tlk = read_tlk(input_path, file_format=ResourceType.TLK_XML, language=language)
    write_tlk(tlk, output_path, file_format=ResourceType.TLK)


def convert_ssf_to_xml(input_path: Path, output_path: Path) -> None:
    """Convert an SSF file to XML format.

    Args:
    ----
        input_path: Path to the input SSF file
        output_path: Path to write the output XML file
    """
    ssf = read_ssf(input_path)
    write_ssf(ssf, output_path, file_format=ResourceType.SSF_XML)


def convert_xml_to_ssf(input_path: Path, output_path: Path) -> None:
    """Convert an XML file to SSF format.

    Args:
    ----
        input_path: Path to the input XML file
        output_path: Path to write the output SSF file
    """
    ssf = read_ssf(input_path, file_format=ResourceType.SSF_XML)
    write_ssf(ssf, output_path, file_format=ResourceType.SSF)


def convert_2da_to_csv(input_path: Path, output_path: Path, *, delimiter: str = ",") -> None:
    """Convert a 2DA file to CSV format.

    Args:
    ----
        input_path: Path to the input 2DA file (binary or ASCII)
        output_path: Path to write the output CSV file
        delimiter: CSV delimiter character (default: comma)

    References:
    ----------
        vendor/xoreos-tools/src/convert2da.cpp
    """
    twoda = read_2da(input_path)
    write_2da(twoda, output_path, file_format=ResourceType.TwoDA_CSV)


def convert_csv_to_2da(input_path: Path, output_path: Path, *, delimiter: str = ",") -> None:
    """Convert a CSV file to 2DA format.

    Args:
    ----
        input_path: Path to the input CSV file
        output_path: Path to write the output 2DA file
        delimiter: CSV delimiter character (default: comma)

    References:
    ----------
        vendor/xoreos-tools/src/convert2da.cpp
    """
    twoda = read_2da(input_path, file_format=ResourceType.TwoDA_CSV)
    write_2da(twoda, output_path, file_format=ResourceType.TwoDA)


def convert_gff_to_json(input_path: Path, output_path: Path) -> None:
    """Convert a GFF file to JSON format.

    Args:
    ----
        input_path: Path to the input GFF file (binary or XML)
        output_path: Path to write the output JSON file
    """
    gff = read_gff(input_path)
    write_gff(gff, output_path, file_format=ResourceType.GFF_JSON)


def convert_json_to_gff(input_path: Path, output_path: Path, *, gff_content_type: str | None = None) -> None:
    """Convert a JSON file to GFF format.

    Args:
    ----
        input_path: Path to the input JSON file
        output_path: Path to write the output GFF file
        gff_content_type: Optional GFF content type (e.g., "IFO ", "UTC ") - auto-detected if None
    """
    gff = read_gff(input_path, file_format=ResourceType.GFF_JSON)
    write_gff(gff, output_path, file_format=ResourceType.GFF)


def convert_tlk_to_json(input_path: Path, output_path: Path) -> None:
    """Convert a TLK file to JSON format.

    Args:
    ----
        input_path: Path to the input TLK file
        output_path: Path to write the output JSON file
    """
    tlk = read_tlk(input_path)
    write_tlk(tlk, output_path, file_format=ResourceType.TLK_JSON)


def convert_json_to_tlk(input_path: Path, output_path: Path) -> None:
    """Convert a JSON file to TLK format.

    Args:
    ----
        input_path: Path to the input JSON file
        output_path: Path to write the output TLK file
    """
    tlk = read_tlk(input_path, file_format=ResourceType.TLK_JSON)
    write_tlk(tlk, output_path, file_format=ResourceType.TLK)

