"""Utility command implementations for KotorCLI.

This module provides CLI commands for utility operations (diff, grep, stats, validate, merge).
"""

from __future__ import annotations

import pathlib
import sys

from argparse import Namespace
from pathlib import Path
from typing import Any

from loggerplus import RobustLogger as Logger  # type: ignore[import-untyped]

# Import the proper diff logging system
from pykotor.diff_tool.logger import DiffLogger, LogLevel, OutputMode
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff import GFF, read_gff, write_gff
from pykotor.tools.misc import is_capsule_file
from pykotor.tools.utilities import get_file_stats, grep_in_file, validate_file


def _diff_archives_or_directories(
    path1: Path,
    path2: Path,
    args: Namespace,
    formatter: Any,
    diff_logger: Logger | DiffLogger,
    output_mode: OutputMode,
) -> int:
    """Compare two archives or directories and show unified diffs."""
    try:
        from pykotor.extract.capsule import Capsule
        from pykotor.extract.installation import Installation
        from pykotor.tslpatcher.diff.engine import DiffContext, diff_data

        # Load archives/installations
        def load_resource_container(path: Path) -> dict[str, bytes]:
            """Load all resources from an archive or directory."""
            raw_resource_data: dict[str, bytes] = {}

            if path.exists() and path.is_dir():
                # Directory - check if it's an installation
                if (path / "chitin.key").exists():
                    installation = Installation(path)
                    # Load all resources from the installation
                    for resource in installation:
                        try:
                            data = resource.data()
                            if data:
                                raw_resource_data[str(resource.identifier()).lower()] = data
                        except Exception:
                            continue
                else:
                    # Regular directory - load all files
                    for file_path in path.rglob("*"):
                        if file_path.is_file():
                            try:
                                relative_path = file_path.relative_to(path)
                                raw_resource_data[str(relative_path).lower()] = file_path.read_bytes()
                            except Exception:
                                continue
            else:
                # Archive file
                try:
                    capsule = Capsule(path)
                    for resource in capsule:
                        try:
                            data = resource.data()
                            if data:
                                raw_resource_data[str(resource.identifier()).lower()] = data
                        except Exception:
                            continue
                except Exception:
                    # Fallback: treat as single file
                    raw_resource_data[path.name.lower()] = path.read_bytes()

            return raw_resource_data

        # Load resources from both paths
        resources1 = load_resource_container(path1)
        resources2 = load_resource_container(path2)

        # Find common and unique resources
        common_keys = set(resources1.keys()) & set(resources2.keys())
        only_in_1 = set(resources1.keys()) - set(resources2.keys())
        only_in_2 = set(resources2.keys()) - set(resources1.keys())

        differences_found = False

        # Report added/removed resources
        for resource_key in sorted(only_in_1):
            if output_mode != OutputMode.QUIET:
                diff_logger.info(f"Only in {args.path1}: {resource_key}")
            differences_found = True

        for resource_key in sorted(only_in_2):
            if output_mode != OutputMode.QUIET:
                diff_logger.info(f"Only in {args.path2}: {resource_key}")
            differences_found = True

        # Compare common resources
        for resource_key in sorted(common_keys):
            data1 = resources1[resource_key]
            data2 = resources2[resource_key]

            if data1 == data2:
                continue  # Identical

            # Try to diff using the existing diff system
            try:
                ext = resource_key.split(".")[-1] if "." in resource_key else ""
                context = DiffContext(Path(resource_key), Path(resource_key), ext)

                # Use the diff_data function to get structured diff
                result = diff_data(data1, data2, context, log_func=diff_logger.info, compare_hashes=False)

                if result is False:  # Different
                    differences_found = True
                    if output_mode == OutputMode.DIFF_ONLY:
                        # Try to output unified diff for the raw data
                        try:
                            import difflib

                            lines1 = data1.decode("utf-8", errors="replace").splitlines(keepends=True)
                            lines2 = data2.decode("utf-8", errors="replace").splitlines(keepends=True)

                            fromfile = f"a/{resource_key}"
                            tofile = f"b/{resource_key}"
                            diff_lines = list(difflib.unified_diff(lines1, lines2, fromfile=fromfile, tofile=tofile, lineterm="", n=getattr(args, "context", 3)))

                            if diff_lines:
                                print("".join(diff_lines), end="")
                        except Exception:
                            # Fallback to simple message
                            diff_logger.info(f"Files differ: {resource_key}")

            except Exception as e:
                # If structured diff fails, fall back to simple comparison
                if data1 != data2:
                    differences_found = True
                    if output_mode != OutputMode.QUIET:
                        diff_logger.info(f"Files differ: {resource_key}")

        # Summary
        if not differences_found:
            if output_mode != OutputMode.DIFF_ONLY:
                diff_logger.info(f"'{args.path1}' MATCHES '{args.path2}'")
            return 0
        else:
            if output_mode != OutputMode.DIFF_ONLY:
                diff_logger.info(f"'{args.path1}' DOES NOT MATCH '{args.path2}'")
            return 1

    except Exception as e:
        Logger().exception("Error comparing archives/directories")
        return 1


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
            if suffix_lower in (".rim", ".erf") and ("_s" in stem_lower or "_dlg" in stem_lower or "_a" in stem_lower or "_adx" in stem_lower):
                return "module_piece"
            return "bioware_archive"
        return "file"

    return "file"


def _resolve_path(
    path_str: str,
    verbose: bool = False,
) -> Path:
    """Resolve a path string to a Path object for diff operations.

    The diff engine uses ResourceWalker which handles all path type detection internally.
    This function ensures all paths are returned as Path objects, letting the diff engine
    determine how to handle each path type (file, folder, installation, archive, etc.).

    Args:
    ----
        path_str: Path string to resolve
        verbose: Whether to output verbose debug information

    Returns:
    -------
        Path object (always returns Path, never Installation)

    Raises:
    ------
        FileNotFoundError: If path doesn't exist and can't be inferred
    """
    path = Path(path_str)

    if verbose:
        path_type = _detect_path_type(path)
        Logger().debug(f"Detected path type for '{path_str}': {path_type}")

    # Always return Path objects - the diff engine handles type detection via ResourceWalker
    return path


def cmd_diff(
    args: Namespace,
    logger: Logger,
) -> int:
    """Compare two paths and show unified diff output.

    Supports any combination of:
    - Files
    - Folders
    - KOTOR installations
    - Bioware archives (.sav/.erf/.rim/.mod)
    - Module pieces (composite module components like _s.rim/_a.rim/.rim/_dlg.erf)

    Args:
    ----
        args: Parsed command line arguments
        logger: Logger instance (not used, we use our own diff logger)

    Returns:
    -------
        Exit code (0 for success, non-zero for error)

    References:
    ----------
        KotOR I (swkotor.exe) / KotOR II (swkotor2.exe):
            - GFF structures are loaded via CResGFF class throughout the engine
            - See individual resource format files (uti.py, utc.py, utp.py, dlg/base.py, etc.) for specific GFF field references
            - 2DA structures loaded via C2DA class (see 2da/io_2da.py for references)
            - TLK structures loaded via CTlkTable class (see tlk/io_tlk.py for references)
        Libraries/PyKotor/src/pykotor/tslpatcher/diff/engine.py
        Libraries/PyKotor/src/pykotor/tslpatcher/diff/application.py

    """
    # Determine verbosity from args
    verbose = getattr(args, "verbose", False) or getattr(args, "debug", False)

    # Resolve both paths
    try:
        path1 = _resolve_path(args.path1, verbose=verbose)
        path2 = _resolve_path(args.path2, verbose=verbose)
    except Exception as e:  # noqa: BLE001
        print(f"Error: Failed to resolve paths: {e.__class__.__name__}: {e}", file=sys.stderr)
        return 1

    # Set up proper diff logging system
    output_mode_str = getattr(args, "output_mode", "full").lower()
    output_mode_map = {
        "full": OutputMode.FULL,
        "diff_only": OutputMode.DIFF_ONLY,
        "quiet": OutputMode.QUIET,
    }
    output_mode = output_mode_map.get(output_mode_str, OutputMode.FULL)

    # Display CLI arguments (for parity with other diff tools)
    if output_mode != OutputMode.QUIET:
        print(f"Using --path1='{args.path1}'")
        print(f"Using --path2='{args.path2}'")
        print("Using --ignore-rims=False")
        print("Using --ignore-tlk=False")
        print("Using --ignore-lips=False")
        print("Using --compare-hashes=True")
        print("Using --use-profiler=False")
        print()

    # Handle special case: identical paths should always match
    if args.path1 == args.path2:
        if output_mode != OutputMode.DIFF_ONLY:
            print(f"'{args.path1}' MATCHES '{args.path2}'")
        return 0

    # Handle output redirection
    output_file = getattr(args, "output", None)
    if output_file:
        output_file = Path(output_file)
        output_handle = output_file.open("w", encoding="utf-8")
    else:
        output_handle = None

    # Create the proper diff logger
    diff_logger = DiffLogger(
        level=LogLevel.DEBUG if verbose else LogLevel.INFO,
        output_mode=output_mode,
        use_colors=False,  # CLI mode, no colors
        output_file=output_handle,
    )

    # Create enhanced log function that the tslpatcher engine can use
    from pykotor.tslpatcher.diff.engine import EnhancedLogFunc

    log_func = EnhancedLogFunc(diff_logger)

    # Handle special case: direct file-to-file comparison
    if isinstance(path1, Path) and isinstance(path2, Path) and path1.is_file() and path2.is_file():
        from pykotor.tslpatcher.diff.engine import DiffContext, diff_data

        # --generate-ini is supported for any path type

        try:
            # Check if files exist
            if not path1.exists():
                print(f"Error: Missing file: {path1}", file=sys.stderr)
                return 1
            if not path2.exists():
                print(f"Error: Missing file: {path2}", file=sys.stderr)
                return 1

            # Create diff context for file comparison
            ext = path1.suffix.casefold()[1:] if path1.suffix else ""
            context = DiffContext(Path(path1.name), Path(path2.name), ext)

            # Get format from args (default to unified)
            format_type = getattr(args, "format", "unified").lower()

            # Use the existing diff_data function
            data1 = path1.read_bytes()
            data2 = path2.read_bytes()
            result = diff_data(
                data1,
                data2,
                context,
                log_func=log_func,
                compare_hashes=True,
                format_type=format_type,
            )

            # Add summary message
            if result:
                diff_logger.info(f"'{args.path1}' MATCHES '{args.path2}'")
            else:
                diff_logger.info(f"'{args.path1}' DOES NOT MATCH '{args.path2}'")

            return 0 if result else 1

        except Exception as e:
            logger.exception(f"Error comparing files: {e.__class__.__name__}: {e}")
            return 1
        finally:
            if output_handle:
                output_handle.close()

    # Check if we need to generate TSLPatcher INI files
    generate_ini = getattr(args, "generate_ini", False)

    if generate_ini:
        # Use the full TSLPatcher application for INI generation
        from pykotor.tslpatcher.diff.application import DiffConfig, handle_diff, run_application  # noqa: PLC0415

        # Convert Path objects to the format expected by TSLPatcher
        paths_for_tslpatcher = []
        for path in [path1, path2]:
            if _detect_path_type(path) == "installation":
                try:
                    paths_for_tslpatcher.append(Installation(path))
                except Exception:  # noqa: BLE001
                    paths_for_tslpatcher.append(path)
            else:
                paths_for_tslpatcher.append(path)

        config = DiffConfig(
            paths=paths_for_tslpatcher,
            output_mode=getattr(args, "output_mode", "full").lower(),  # full by default when generating tslpatcher ini
            use_incremental_writer=True,
        )

        run_application(config)
        result, exit_code = handle_diff(config)
        return 1 if exit_code is None else exit_code

    # For archives and directories, implement proper diff display
    try:
        from pykotor.tslpatcher.diff.engine import DiffContext, diff_data
        from pykotor.tslpatcher.diff.formatters import ContextFormatter, SideBySideFormatter, UnifiedFormatter

        # Get format from args (default to unified)
        format_type = getattr(args, "format", "unified").lower()

        # Create appropriate formatter
        if format_type == "unified":
            formatter = UnifiedFormatter()
        elif format_type == "context":
            formatter = ContextFormatter()
        elif format_type == "side_by_side":
            formatter = SideBySideFormatter()
        else:
            formatter = UnifiedFormatter()

        # For archives/directories, we need to walk and compare resources

        # Determine if paths are archives or directories
        def is_archive_or_installation(path: Path) -> bool:
            if path.is_dir():
                return (path / "chitin.key").exists()  # Installation
            return is_capsule_file(path)

        path1_is_archive = is_archive_or_installation(path1)
        path2_is_archive = is_archive_or_installation(path2)

        if path1_is_archive or path2_is_archive:
            # Archive/directory comparison - walk and compare resources
            return _diff_archives_or_directories(
                path1,
                path2,
                args,
                formatter,
                diff_logger,
                output_mode,
            )
        else:
            # Both are regular files - direct comparison
            ext = path1.suffix.casefold()[1:] if path1.suffix else ""
            context = DiffContext(path1, path2, ext)

            result = diff_data(
                path1,
                path2,
                context,
                log_func=diff_logger.info,
                compare_hashes=True,
                format_type=format_type,
            )

            # Add summary message (but not in diff_only mode)
            if output_mode != OutputMode.DIFF_ONLY:
                if result:
                    diff_logger.info(f"'{args.path1}' MATCHES '{args.path2}'")
                else:
                    diff_logger.info(f"'{args.path1}' DOES NOT MATCH '{args.path2}'")

            return 0 if result else 1

    except Exception as e:
        logger.exception(f"Error generating diff: {e.__class__.__name__}: {e}")
        if output_handle is not None:
            output_handle.close()

        return 1


def cmd_grep(
    args: Namespace,
    logger: Logger,
) -> int:
    """Search for patterns in files.

    Supports text files and structured formats (GFF, 2DA, TLK).

    References:
    ----------
        KotOR I (swkotor.exe) / KotOR II (swkotor2.exe):
            - GFF structures are loaded via CResGFF class throughout the engine
            - See individual resource format files (uti.py, utc.py, utp.py, dlg/base.py, etc.) for specific GFF field references
            - 2DA structures loaded via C2DA class (see 2da/io_2da.py for references)
            - TLK structures loaded via CTlkTable class (see tlk/io_tlk.py for references)


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
    except Exception as e:
        logger.exception(f"Failed to search {file_path}: {e.__class__.__name__}: {e}")  # noqa: G004
        return 1


def cmd_stats(
    args: Namespace,
    logger: Logger,
) -> int:
    """Show statistics about a file.

    References:
    ----------
        KotOR I (swkotor.exe) / KotOR II (swkotor2.exe):
            - GFF structures are loaded via CResGFF class throughout the engine
            - See individual resource format files (uti.py, utc.py, utp.py, dlg/base.py, etc.) for specific GFF field references
            - 2DA structures loaded via C2DA class (see 2da/io_2da.py for references)
            - TLK structures loaded via CTlkTable class (see tlk/io_tlk.py for references)


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
    except Exception as e:
        logger.exception(f"Failed to get stats for {file_path}: {e.__class__.__name__}: {e}s", exc_info=True)  # noqa: G004
        return 1


def cmd_validate(
    args: Namespace,
    logger: Logger,
) -> int:
    """Validate file format and structure."""
    file_path = pathlib.Path(args.file)

    try:
        is_valid, message = validate_file(file_path)

        if is_valid:
            logger.info(f"{file_path}: {message}")  # noqa: G004
            return 0
        logger.error(f"{file_path}: {message}")  # noqa: G004
        return 1
    except Exception as e:
        logger.exception(f"Failed to validate {file_path}: {e.__class__.__name__}: {e}", exc_info=True)  # noqa: G004
        return 1


def cmd_merge(
    args: Namespace,
    logger: Logger,
) -> int:
    """Merge two GFF files.

    Merges fields from source file into target file, adding missing fields.
    Currently only supports GFF files.

    References:
    ----------
        KotOR I (swkotor.exe) / KotOR II (swkotor2.exe):
            - GFF structures are loaded via CResGFF class throughout the engine
            - See individual resource format files (uti.py, utc.py, utp.py, dlg/base.py, etc.) for specific GFF field references
            - 2DA structures loaded via C2DA class (see 2da/io_2da.py for references)
            - TLK structures loaded via CTlkTable class (see tlk/io_tlk.py for references)
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
    except Exception as e:
        logger.exception(f"Failed to merge files: {e.__class__.__name__}: {e}", exc_info=True)
        return 1
