"""Utility command implementations for KotorCLI.

This module provides CLI commands for utility operations (diff, grep, stats, validate, merge).
"""

from __future__ import annotations

import pathlib
import sys

from argparse import Namespace
from pathlib import Path

from loggerplus import RobustLogger as Logger  # type: ignore[import-untyped]
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff.gff_auto import read_gff, write_gff
from pykotor.resource.formats.gff.gff_data import GFF
from pykotor.tools.misc import is_capsule_file
from pykotor.tools.utilities import diff_files, get_file_stats, grep_in_file, validate_file


def _detect_path_type(path: Path) -> str:
    """Detect the type of a path (installation, bioware archive, module piece, folder, or file).

    Args:
    ----
        path: Path to detect

    Returns:
    -------
        String describing the path type: "installation", "bioware_archive", "module_piece", "folder", or "file"
    """
    if not path.exists():
        # If path doesn't exist, try to infer from extension
        if is_capsule_file(path):
            return "bioware_archive"
        return "file"

    if path.is_dir():
        # Check if it's a KOTOR installation (has chitin.key)
        if (path / "chitin.key").is_file():
            return "installation"
        return "folder"

    if path.is_file():
        # Check if it's a bioware archive
        if is_capsule_file(path):
            # Check if it's a module piece (composite module component)
            suffix_lower = path.suffix.lower()
            stem_lower = path.stem.lower()
            if suffix_lower in (".rim", ".erf") and (stem_lower.endswith("_s") or stem_lower.endswith("_dlg") or stem_lower.endswith("_a") or stem_lower.endswith("_adx")):
                return "module_piece"
            return "bioware_archive"
        return "file"

    return "file"


def _resolve_path(path_str: str, verbose: bool = False) -> Path | Installation:
    """Resolve a path string to a Path or Installation object, handling all path types.

    Args:
    ----
        path_str: Path string to resolve
        verbose: Whether to output verbose debug information

    Returns:
    -------
        Path or Installation object

    Raises:
    ------
        FileNotFoundError: If path doesn't exist and can't be inferred
        ValueError: If path type can't be determined
    """
    path = Path(path_str)

    path_type = _detect_path_type(path)

    if verbose:
        print(f"[DEBUG] Detected path type for '{path_str}': {path_type}", file=sys.stderr)

    if path_type == "installation":
        try:
            return Installation(path)
        except Exception as e:  # noqa: BLE001
            if verbose:
                print(f"[DEBUG] Failed to create Installation, falling back to Path: {e}", file=sys.stderr)
            return path

    if path_type == "module_piece":
        # For module pieces, we need to handle composite module loading
        # The diff infrastructure should handle this automatically via Module.get_capsules_dict_matching
        # We just return the path as-is, and the diff engine will detect related files
        return path

    # For bioware_archive, folder, or file, return as Path
    return path


def cmd_diff(args: Namespace, logger: Logger) -> int:
    """Compare two paths and show unified diff output.

    Supports any combination of:
    - Files
    - Folders
    - KOTOR installations
    - Bioware archives (.sav/.erf/.rim/.mod)
    - Module pieces (composite module components like _s.rim/_a.rim/.rim/_dlg.erf)

    By default, outputs ONLY unified diff format. Debug/verbose information
    (tslpatchdata, changes.ini, namespaces.ini, resolution order) is only shown
    when --verbose or --debug flags are passed.

    Args:
    ----
        args: Parsed command line arguments
        logger: Logger instance

    Returns:
    -------
        Exit code (0 for success, non-zero for error)

    References:
    ----------
        Libraries/PyKotor/src/pykotor/tslpatcher/diff/engine.py
        Libraries/PyKotor/src/pykotor/tslpatcher/diff/application.py
    """
    # Determine verbosity from args (check for verbose/debug flags)
    # These are global flags passed through from dispatch
    verbose = False
    if hasattr(args, "verbose") and args.verbose:
        verbose = True
    if hasattr(args, "debug") and args.debug:
        verbose = True

    # Resolve both paths
    try:
        path1 = _resolve_path(args.path1, verbose=verbose)
        path2 = _resolve_path(args.path2, verbose=verbose)
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to resolve paths: {e}")  # noqa: G004
        if verbose:
            logger.exception("Path resolution error")
        return 1

    # For simple file-to-file comparison, use the simple diff_files utility
    # This provides better output for single file comparisons
    if isinstance(path1, Path) and isinstance(path2, Path) and path1.is_file() and path2.is_file():
        output_path = Path(args.output) if args.output else None
        try:
            diff_text = diff_files(path1, path2, output_path=output_path, context_lines=args.context)

            if output_path:
                logger.info(f"Diff written to {output_path}")  # noqa: G004
            else:
                print(diff_text)  # noqa: T201

            return 0
        except Exception:
            logger.exception("Failed to generate diff")
            return 1

    # For all other cases (installations, folders, archives, module pieces, mixed types),
    # use the comprehensive diff infrastructure
    try:
        # Import the diff engine directly
        from pykotor.tslpatcher.diff.engine import run_differ_from_args_impl  # noqa: PLC0415

        # Create a custom log function that filters output to udiff-only when not verbose
        # We need to capture ALL output and filter it properly
        all_output_lines: list[str] = []

        def filtered_log_func(msg: str, *args, **kwargs) -> None:
            """Log function that filters output to udiff-only when not verbose."""
            if verbose:
                # In verbose mode, print everything immediately
                print(msg, *args, **kwargs)  # noqa: T201
                return

            # In non-verbose mode, collect all output for filtering
            msg_str = str(msg) if not args else (str(msg) + " ".join(str(a) for a in args))
            all_output_lines.append(msg_str)

        # Run the diff engine directly with our filtered log function
        comparison_result = run_differ_from_args_impl(
            [path1, path2],
            filters=None,
            log_func=filtered_log_func,
            compare_hashes=True,
            modifications_by_type=None,
            incremental_writer=None,
        )

        # If not verbose, filter and print only udiff-relevant output
        if not verbose:
            # Filter to show:
            # 1. Field difference descriptions (e.g., "Field 'Int16' is different at...")
            # 2. Unified diff lines (---, +++, @@, +, -, space)
            # 3. Final summary lines (DOES NOT MATCH, MATCHES)
            # 4. Missing file messages
            # 5. GFF/Struct difference messages
            # Exclude: DEBUG, INFO, [PATCH], [INSTALL], resolution order, writer info, etc.
            
            filtered_lines: list[str] = []
            in_diff_block = False
            skip_until_separator = False
            
            for line in all_output_lines:
                stripped = line.strip()
                
                # Skip empty lines unless we're in a diff block
                if not stripped and not in_diff_block:
                    continue
                
                # Skip debug/info messages
                if any(prefix in stripped for prefix in ["[DEBUG]", "[INFO]", "[PATCH]", "[INSTALL]", "Loading", "Done loading", "Collected", "Comparing", "Progress:", "N-WAY COMPARISON SUMMARY", "Total resources", "Differences found", "Errors:", "=" * 80]):
                    continue
                
                # Skip resolution order and writer info
                if any(phrase in stripped for phrase in ["Resolution:", "Destination:", "tslpatchdata:", "Will copy", "Will use", "Mode:", "Type:", "Modifications:", "Extracting", "Staged", "Created empty"]):
                    continue
                
                # Include field difference descriptions and resource difference markers
                if any(phrase in stripped for phrase in ["Field", "is different at", "GFFStruct:", "number of fields", "Struct ID", "Extra", "Missing", "GFF counts", "GFFList", "struct(s)", "[DIFFERENT RESOURCE]", "Difference between path"]):
                    filtered_lines.append(line)
                    in_diff_block = True  # Expect udiff to follow
                    continue
                
                # Include unified diff lines
                if (stripped.startswith("---") or stripped.startswith("+++") or 
                    stripped.startswith("@@") or 
                    (stripped.startswith("+") and not stripped.startswith("++")) or
                    (stripped.startswith("-") and not stripped.startswith("--")) or
                    (stripped.startswith(" ") and in_diff_block)):
                    filtered_lines.append(line)
                    in_diff_block = True
                    continue
                
                # Include separator lines (like "---------------------------------------------------")
                if stripped.startswith("-") and len(stripped) > 10 and all(c == "-" for c in stripped):
                    filtered_lines.append(line)
                    continue
                
                # Include final summary lines
                if "DOES NOT MATCH" in stripped or "MATCHES" in stripped or "Comparison of" in stripped:
                    filtered_lines.append(line)
                    continue
                
                # Include missing file messages
                if "Missing file:" in stripped:
                    filtered_lines.append(line)
                    continue
                
                # Include GFF difference markers
                if "^ '" in stripped and "': GFF is different" in stripped:
                    filtered_lines.append(line)
                    in_diff_block = False  # End of diff block
                    continue
                
                # Include file size/hash differences
                if any(phrase in stripped for phrase in ["File sizes differ", "SHA256 is different", "bytes"]):
                    filtered_lines.append(line)
                    continue
                
                # If we're in a diff block and see a non-diff line, end the block
                if in_diff_block and stripped and not stripped.startswith(" "):
                    in_diff_block = False
            
            # Print filtered output
            if filtered_lines:
                print("\n".join(filtered_lines))  # noqa: T201
            
            # Add final summary if we have a comparison result
            if comparison_result is not None:
                path1_str = str(path1) if isinstance(path1, Path) else str(path1)
                path2_str = str(path2) if isinstance(path2, Path) else str(path2)
                if comparison_result:
                    print(f"'{path1_str}' MATCHES '{path2_str}'")  # noqa: T201
                else:
                    print(f"'{path1_str}' DOES NOT MATCH '{path2_str}'")  # noqa: T201

        # Determine exit code
        if comparison_result is True:
            return 0  # Identical
        if comparison_result is False:
            return 1  # Different
        return 1  # Error

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
