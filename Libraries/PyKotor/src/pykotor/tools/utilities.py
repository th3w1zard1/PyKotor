"""Utility command functions for file operations, validation, and analysis.

This module provides reusable, abstract functions for common utility operations
like diff, grep, stats, validate, and merge. These functions are tool-agnostic
and can be used by any application that needs these utilities.

References:
----------
    vendor/xoreos-tools/ - Various utility tools
    Tools/KotorDiff/ - File diffing implementation
    Libraries/PyKotor/src/pykotor/tslpatcher/diff/ - Structured diff engine
"""
from __future__ import annotations

import difflib

from pathlib import Path

from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.formats.gff.gff_data import GFF, GFFFieldType, GFFList, GFFStruct
from pykotor.resource.formats.tlk.tlk_auto import read_tlk
from pykotor.resource.formats.twoda.twoda_auto import read_2da


def diff_files(
    file1_path: Path,
    file2_path: Path,
    *,
    output_path: Path | None = None,
    context_lines: int = 3,
) -> str:
    """Compare two files and return a unified diff.

    Supports GFF, 2DA, TLK files with structured comparison.

    Args:
    ----
        file1_path: Path to first file
        file2_path: Path to second file
        output_path: Optional path to write diff output
        context_lines: Number of context lines in diff output

    Returns:
    -------
        Unified diff text as string

    References:
    ----------
        Tools/KotorDiff/src/kotordiff/differ.py
        Libraries/PyKotor/src/pykotor/tslpatcher/diff/structured.py
    """
    suffix = file1_path.suffix.lower()

    # Structured comparison for known formats
    if suffix in (".gff", ".utc", ".uti", ".dlg", ".are", ".git", ".ifo"):
        return _diff_gff_files(file1_path, file2_path, output_path, context_lines)
    if suffix == ".2da":
        return _diff_2da_files(file1_path, file2_path, output_path, context_lines)
    if suffix == ".tlk":
        return _diff_tlk_files(file1_path, file2_path, output_path, context_lines)

    # Fallback to binary/text comparison
    return _diff_binary_files(file1_path, file2_path, output_path, context_lines)


def _diff_gff_files(
    file1_path: Path,
    file2_path: Path,
    output_path: Path | None,
    context_lines: int,
) -> str:
    """Compare two GFF files."""
    try:
        gff1 = read_gff(file1_path)
        gff2 = read_gff(file2_path)

        # Use GFF's compare method for structured comparison
        text1 = _gff_to_text(gff1)
        text2 = _gff_to_text(gff2)

        diff_lines = list(
            difflib.unified_diff(
                text1.splitlines(keepends=True),
                text2.splitlines(keepends=True),
                fromfile=str(file1_path),
                tofile=str(file2_path),
                lineterm="",
                n=context_lines,
            ),
        )

        result = "".join(diff_lines)

        if output_path:
            output_path.write_text(result, encoding="utf-8")

        return result
    except Exception:
        # Fallback to binary diff on error
        return _diff_binary_files(file1_path, file2_path, output_path, context_lines)


def _diff_2da_files(
    file1_path: Path,
    file2_path: Path,
    output_path: Path | None,
    context_lines: int,
) -> str:
    """Compare two 2DA files."""
    try:
        twoda1 = read_2da(file1_path)
        twoda2 = read_2da(file2_path)

        text1 = _2da_to_text(twoda1)
        text2 = _2da_to_text(twoda2)

        diff_lines = list(
            difflib.unified_diff(
                text1.splitlines(keepends=True),
                text2.splitlines(keepends=True),
                fromfile=str(file1_path),
                tofile=str(file2_path),
                lineterm="",
                n=context_lines,
            ),
        )

        result = "".join(diff_lines)

        if output_path:
            output_path.write_text(result, encoding="utf-8")

        return result
    except Exception:
        return _diff_binary_files(file1_path, file2_path, output_path, context_lines)


def _diff_tlk_files(
    file1_path: Path,
    file2_path: Path,
    output_path: Path | None,
    context_lines: int,
) -> str:
    """Compare two TLK files."""
    try:
        tlk1 = read_tlk(file1_path)
        tlk2 = read_tlk(file2_path)

        text1 = _tlk_to_text(tlk1)
        text2 = _tlk_to_text(tlk2)

        diff_lines = list(
            difflib.unified_diff(
                text1.splitlines(keepends=True),
                text2.splitlines(keepends=True),
                fromfile=str(file1_path),
                tofile=str(file2_path),
                lineterm="",
                n=context_lines,
            ),
        )

        result = "".join(diff_lines)

        if output_path:
            output_path.write_text(result, encoding="utf-8")

        return result
    except Exception:
        return _diff_binary_files(file1_path, file2_path, output_path, context_lines)


def _diff_binary_files(
    file1_path: Path,
    file2_path: Path,
    output_path: Path | None,
    context_lines: int,
) -> str:
    """Fallback binary comparison."""
    data1 = file1_path.read_bytes()
    data2 = file2_path.read_bytes()

    if data1 == data2:
        result = f"Files are identical: {file1_path.name} and {file2_path.name}\n"
    else:
        result = (
            f"Files differ:\n"
            f"  {file1_path.name}: {len(data1)} bytes\n"
            f"  {file2_path.name}: {len(data2)} bytes\n"
        )

    if output_path:
        output_path.write_text(result, encoding="utf-8")

    return result


def grep_in_file(
    file_path: Path,
    pattern: str,
    *,
    case_sensitive: bool = False,
) -> list[tuple[int, str]]:
    """Search for a pattern in a file and return matching lines with line numbers.

    Supports text files and structured formats (GFF, 2DA, TLK).

    Args:
    ----
        file_path: Path to file to search
        pattern: Search pattern (regex or plain text)
        case_sensitive: Whether search is case-sensitive

    Returns:
    -------
        List of (line_number, line_text) tuples

    References:
    ----------
        vendor/xoreos-tools/ - grep-like utilities
    """
    suffix = file_path.suffix.lower()

    # Handle structured formats
    if suffix in (".gff", ".utc", ".uti", ".dlg", ".are", ".git", ".ifo"):
        return _grep_in_gff(file_path, pattern, case_sensitive)
    if suffix == ".2da":
        return _grep_in_2da(file_path, pattern, case_sensitive)
    if suffix == ".tlk":
        return _grep_in_tlk(file_path, pattern, case_sensitive)

    # Fallback to text file search
    return _grep_in_text_file(file_path, pattern, case_sensitive)


def _grep_in_text_file(
    file_path: Path,
    pattern: str,
    case_sensitive: bool,
) -> list[tuple[int, str]]:
    """Search in a plain text file."""
    matches: list[tuple[int, str]] = []
    text = pattern if case_sensitive else pattern.lower()

    try:
        with file_path.open("r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                search_line = line if case_sensitive else line.lower()
                if text in search_line:
                    matches.append((line_num, line.rstrip()))
    except UnicodeDecodeError:
        # Try binary search
        data = file_path.read_bytes()
        search_bytes = pattern.encode("utf-8") if case_sensitive else pattern.lower().encode("utf-8")
        if search_bytes in data:
            matches.append((0, f"Pattern found in binary file: {file_path.name}"))

    return matches


def _grep_in_gff(
    file_path: Path,
    pattern: str,
    case_sensitive: bool,
) -> list[tuple[int, str]]:
    """Search in GFF file by converting to text representation."""
    try:
        gff = read_gff(file_path)
        text = _gff_to_text(gff)
        return _grep_in_text_content(text, pattern, case_sensitive)
    except Exception:
        return []


def _grep_in_2da(
    file_path: Path,
    pattern: str,
    case_sensitive: bool,
) -> list[tuple[int, str]]:
    """Search in 2DA file."""
    try:
        twoda = read_2da(file_path)
        text = _2da_to_text(twoda)
        return _grep_in_text_content(text, pattern, case_sensitive)
    except Exception:
        return []


def _grep_in_tlk(
    file_path: Path,
    pattern: str,
    case_sensitive: bool,
) -> list[tuple[int, str]]:
    """Search in TLK file."""
    try:
        tlk = read_tlk(file_path)
        text = _tlk_to_text(tlk)
        return _grep_in_text_content(text, pattern, case_sensitive)
    except Exception:
        return []


def _grep_in_text_content(
    content: str,
    pattern: str,
    case_sensitive: bool,
) -> list[tuple[int, str]]:
    """Search pattern in text content."""
    matches: list[tuple[int, str]] = []
    search_text = pattern if case_sensitive else pattern.lower()

    for line_num, line in enumerate(content.splitlines(), 1):
        search_line = line if case_sensitive else line.lower()
        if search_text in search_line:
            matches.append((line_num, line))

    return matches


def get_file_stats(file_path: Path) -> dict[str, int | str]:
    """Get statistics about a file.

    Args:
    ----
        file_path: Path to file to analyze

    Returns:
    -------
        Dictionary with file statistics

    References:
    ----------
        vendor/xoreos-tools/ - File analysis utilities
    """
    stats: dict[str, int | str] = {
        "path": str(file_path),
        "size": file_path.stat().st_size if file_path.exists() else 0,
        "exists": file_path.exists(),
    }

    if not file_path.exists():
        return stats

    suffix = file_path.suffix.lower()

    # Add format-specific statistics
    if suffix in (".gff", ".utc", ".uti", ".dlg", ".are", ".git", ".ifo"):
        try:
            gff = read_gff(file_path)
            stats["type"] = "GFF"
            stats["field_count"] = len(gff.root)
        except Exception:
            pass
    elif suffix == ".2da":
        try:
            twoda = read_2da(file_path)
            stats["type"] = "2DA"
            stats["row_count"] = len(twoda)
            stats["column_count"] = len(twoda.get_headers()) if twoda else 0
        except Exception:
            pass
    elif suffix == ".tlk":
        try:
            tlk = read_tlk(file_path)
            stats["type"] = "TLK"
            stats["string_count"] = len(tlk)
        except Exception:
            pass

    return stats


def validate_file(file_path: Path) -> tuple[bool, str]:
    """Validate a file's format and structure.

    Args:
    ----
        file_path: Path to file to validate

    Returns:
    -------
        Tuple of (is_valid, error_message)

    References:
    ----------
        vendor/xoreos-tools/ - File validation utilities
    """
    if not file_path.exists():
        return False, f"File does not exist: {file_path}"

    suffix = file_path.suffix.lower()

    try:
        if suffix in (".gff", ".utc", ".uti", ".dlg", ".are", ".git", ".ifo"):
            read_gff(file_path)
            return True, "Valid GFF file"
        if suffix == ".2da":
            read_2da(file_path)
            return True, "Valid 2DA file"
        if suffix == ".tlk":
            read_tlk(file_path)
            return True, "Valid TLK file"
        if suffix in (".erf", ".mod", ".sav"):
            from pykotor.resource.formats.erf.erf_auto import read_erf

            read_erf(file_path)
            return True, "Valid ERF file"
        if suffix == ".rim":
            from pykotor.resource.formats.rim.rim_auto import read_rim

            read_rim(file_path)
            return True, "Valid RIM file"
        if suffix == ".tpc":
            from pykotor.resource.formats.tpc.tpc_auto import read_tpc

            read_tpc(file_path)
            return True, "Valid TPC file"

        return True, "File exists (format validation not implemented)"
    except Exception as e:
        return False, f"Validation failed: {str(e)}"


# Helper functions for text conversion
def _gff_to_text(gff: GFF) -> str:
    """Convert GFF to text representation for diff/grep."""
    lines: list[str] = []
    _gff_struct_to_text(gff.root, lines, "")
    return "\n".join(lines)


def _gff_struct_to_text(struct: GFFStruct, lines: list[str], indent: str) -> None:
    """Recursively convert GFF struct to text."""
    for label, field_type, value in struct:
        field_type_name = field_type.name
        value_str = str(value)
        lines.append(f"{indent}{label} ({field_type_name}): {value_str}")

        if field_type == GFFFieldType.Struct and isinstance(value, GFFStruct):
            _gff_struct_to_text(value, lines, indent + "  ")
        elif field_type == GFFFieldType.List and isinstance(value, GFFList):
            for i, item in enumerate(value):
                lines.append(f"{indent}  [{i}]")
                if isinstance(item, GFFStruct):
                    _gff_struct_to_text(item, lines, indent + "    ")


def _2da_to_text(twoda) -> str:
    """Convert 2DA to text representation."""
    lines: list[str] = []
    if twoda:
        headers = twoda.get_headers()
        lines.append("\t".join(headers))
        for row in twoda:
            values = [str(row.get(header, "")) for header in headers]
            lines.append("\t".join(values))
    return "\n".join(lines)


def _tlk_to_text(tlk) -> str:
    """Convert TLK to text representation."""
    lines: list[str] = []
    for i, entry in enumerate(tlk):
        text = entry.text if hasattr(entry, "text") else str(entry)
        lines.append(f"{i}: {text}")
    return "\n".join(lines)

