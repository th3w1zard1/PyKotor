"""KotorDiff CLI module.

This module provides command-line interface functionality for KotorDiff,
separate from the GUI to allow CLI usage without tkinter installed.
"""

from __future__ import annotations

import io
import os
import sys
import traceback

from argparse import ArgumentParser
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace

from pykotor.cli.version import VERSION

CURRENT_VERSION = VERSION


def add_kotordiff_arguments(parser: ArgumentParser) -> None:
    """Add KotorDiff arguments to an existing argument parser.

    This function is used to integrate KotorDiff arguments into other CLI tools
    (like PyKotor CLI) without creating a separate parser.

    Args:
    ----
        parser: The ArgumentParser to add arguments to
    """
    # Path arguments (multiple aliases for compatibility)
    parser.add_argument("--path1", type=str, help="Path to compare. Multiple path flags can be supplied; at least two paths are required.")
    parser.add_argument("--path2", type=str, help="Additional path to compare.")
    parser.add_argument("--path3", type=str, help="Additional path to compare.")
    parser.add_argument(
        "--path", action="append", dest="extra_paths", help="Additional paths for N-way comparison (can be used multiple times). Example: --path path4 --path path5"
    )

    # Output options
    parser.add_argument(
        "--tslpatchdata",
        type=str,
        help="Path where tslpatchdata folder should be created. Requires at least one path to be an Installation.",
    )
    parser.add_argument(
        "--ini",
        type=str,
        default="changes.ini",
        help="Filename for changes.ini (not path, just filename). Requires --tslpatchdata. Must have .ini extension (default: changes.ini).",
    )
    parser.add_argument("--output-log", type=str, help="Filepath of the desired output logfile")

    # Logging and display options
    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Logging level (default: info)",
    )
    parser.add_argument(
        "--output-mode",
        type=str,
        default="full",
        choices=["full", "diff_only", "quiet"],
        help="Output mode: full (all logs), diff_only (only diff results), quiet (minimal) (default: full)",
    )
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")

    # Comparison options
    parser.add_argument(
        "--compare-hashes",
        dest="compare_hashes",
        action="store_true",
        default=True,
        help="Compare hashes of any unsupported file/resource type (default is True)",
    )
    parser.add_argument(
        "--no-compare-hashes",
        dest="compare_hashes",
        action="store_false",
        help="Disable hash comparison",
    )
    parser.add_argument(
        "--filter",
        action="append",
        help="Filter specific files/modules for installation-wide diffs (can be used multiple times). "
        "Examples: 'tat_m18ac' for module, 'some_character.utc' for specific resource",
    )
    parser.add_argument(
        "--logging",
        dest="logging",
        action="store_true",
        default=True,
        help="Whether to log the results to a file or not (default is True)",
    )
    parser.add_argument(
        "--no-logging",
        dest="logging",
        action="store_false",
        help="Disable log file generation",
    )
    parser.add_argument(
        "--use-profiler",
        action="store_true",
        default=False,
        help="Use cProfile to find where most of the execution time is taking place in source code.",
    )
    parser.add_argument(
        "--incremental",
        dest="use_incremental_writer",
        action="store_true",
        default=False,
        help="Write TSLPatcher data incrementally",
    )

    # GUI/Console options
    parser.add_argument(
        "--console",
        action="store_true",
        help="Show console window even in GUI mode",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Force GUI mode even with paths provided",
    )


def parse_args() -> Namespace:
    """Create and configure the argument parser."""
    parser = ArgumentParser(description="Finds differences between KOTOR files/dirs. Supports comparisons across any number of paths.")
    add_kotordiff_arguments(parser)
    return parser.parse_args()


def normalize_path_arg(arg: str) -> str:
    """Normalize a path argument (handle quotes, etc.)."""
    if not arg:
        return arg
    # Strip surrounding quotes
    arg = arg.strip().strip('"').strip("'")
    return arg


def execute_cli(cmdline_args: Namespace):
    """Execute CLI mode with the provided arguments.

    Args:
        cmdline_args: Parsed command line arguments
    """
    print("execute_cli called", file=sys.stderr)
    from pykotor.diff_tool.app import KotorDiffConfig, run_application
    from pykotor.extract.installation import Installation

    # Set up logging ONCE at the CLI level
    import logging

    output_mode = getattr(cmdline_args, "output_mode", "full")
    log_level_arg = getattr(cmdline_args, "log_level", None)

    # Determine log level based on output_mode or explicit log_level
    if log_level_arg:
        log_level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
        }
        log_level = log_level_map.get(log_level_arg.lower(), logging.INFO)
    else:
        # Default log levels based on output mode
        log_level = {
            "full": logging.INFO,
            "diff_only": 100,  # Disable ALL logging for pure diff output (level higher than CRITICAL)
            "quiet": logging.ERROR,
        }.get(output_mode, logging.INFO)

    # Configure logging once - all code uses standard logging calls
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,  # All logging goes to stderr
    )

    if output_mode == "diff_only" and log_level >= logging.CRITICAL:
        # Disable all logging for pure diff output when using default logging level
        logging.disable(logging.CRITICAL)

    # Configure console for UTF-8 output on Windows
    if sys.platform == "win32":
        try:
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer,
                encoding="utf-8",
                errors="replace",
                line_buffering=True,
            )
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer,
                encoding="utf-8",
                errors="replace",
                line_buffering=True,
            )
        except Exception:  # noqa: BLE001
            logging.error("Failed to configure console for UTF-8 output on Windows")
            logging.error(traceback.format_exc())

    logging.info(f"KotorDiff version {CURRENT_VERSION}")

    # Gather all path inputs
    raw_path_inputs: list[str] = []

    if cmdline_args.path1:
        raw_path_inputs.append(normalize_path_arg(cmdline_args.path1))
    if cmdline_args.path2:
        raw_path_inputs.append(normalize_path_arg(cmdline_args.path2))
    if cmdline_args.path3:
        raw_path_inputs.append(normalize_path_arg(cmdline_args.path3))

    if cmdline_args.extra_paths:
        for p in cmdline_args.extra_paths:
            raw_path_inputs.append(normalize_path_arg(p))

    if len(raw_path_inputs) < 2:  # noqa: PLR2004
        logging.error("At least 2 paths are required for comparison.")
        logging.info("Use --help to see CLI options")
        sys.exit(1)

    # Convert string paths to Path/Installation objects
    resolved_paths: list[Path | Installation] = []
    logging.error(f"raw_path_inputs: {raw_path_inputs}")
    for path_str in raw_path_inputs:
        path_obj = Path(path_str)
        try:
            # Try to create an Installation object (for KOTOR installations)
            installation = Installation(path_obj)
            resolved_paths.append(installation)
            logging.debug(f"Loaded Installation for: {path_str}")
        except Exception as e:  # noqa: BLE001
            # Fall back to Path object (for folders/files)
            resolved_paths.append(path_obj)
            logging.debug(f"Using Path (not Installation) for: {path_str}")
            logging.debug(f"Installation load failed: {e.__class__.__name__}: {e}")

    # Special case: if comparing exactly two files, use direct diff
    print(f"[DEBUG] Checking special case: len={len(resolved_paths)}, output_mode={output_mode}", file=sys.stderr)
    if (
        len(resolved_paths) == 2
        and all(isinstance(path, Path)
        and path.is_file()
        for path in resolved_paths)
        and output_mode == "diff_only"
    ):
        print("[DEBUG] Using special case for file-to-file diff", file=sys.stderr)
        # Use direct file-to-file diff for unified output
        from pykotor.tslpatcher.diff.engine import DiffContext, diff_data

        # Create a custom log function that sends diff output to stdout
        def stdout_log_func(
            message: str,
            *,
            message_type: str = "info",
            separator: bool = False,  # pyright: ignore[reportUnusedParameter]
            **kwargs,  # pyright: ignore[reportUnusedParameter]
        ) -> None:
            """Route diff output to stdout, everything else to logging."""
            import logging

            if message_type == "diff":
                print(message)  # Print diff to stdout
            # For diff_only mode, suppress all other output completely

        path1, path2 = resolved_paths
        context = DiffContext(
            file1_rel=Path(
                os.path.relpath(
                    os.path.dirname(path1.path() if isinstance(path1, Installation) else path1),
                    path1.path() if isinstance(path1, Installation) else path1,
                )
            ),
            file2_rel=Path(
                os.path.relpath(
                    os.path.dirname(path2.path() if isinstance(path2, Installation) else path2),
                    path2.path() if isinstance(path2, Installation) else path2,
                )
            ),
            ext=(
                (path1.path() if isinstance(path1, Installation) else path1).suffix.casefold().lstrip(".").strip()
                or (path2.path() if isinstance(path2, Installation) else path2).suffix.casefold().lstrip(".").strip()
            ),
            resname=(path1.path() if isinstance(path1, Installation) else path1).name,
            file1_location_type="Installation" if isinstance(path1, Installation) else "Path",
            file2_location_type="Installation" if isinstance(path2, Installation) else "Path",
            file1_filepath=(path1.path() if isinstance(path1, Installation) else path1),
            file2_filepath=(path2.path() if isinstance(path2, Installation) else path2),
            file1_installation=path1 if isinstance(path1, Installation) else None,
            file2_installation=path2 if isinstance(path2, Installation) else None,
        )

        try:
            result = diff_data(
                (path1.path() if isinstance(path1, Installation) else path1).read_bytes(),
                (path2.path() if isinstance(path2, Installation) else path2).read_bytes(),
                context,
                log_func=stdout_log_func,
                compare_hashes=True,
                format_type="unified",
            )
            # DO NOT REMOVE THIS LOG LINE!
            sys.exit(0 if result else 1)
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error comparing files: {e.__class__.__name__}: {e}")
            sys.exit(1)

    # Create configuration object
    config = KotorDiffConfig(
        paths=resolved_paths,
        tslpatchdata_path=Path(cmdline_args.tslpatchdata) if cmdline_args.tslpatchdata else None,
        ini_filename=getattr(cmdline_args, "ini", "changes.ini"),
        output_log_path=Path(cmdline_args.output_log) if cmdline_args.output_log else None,
        log_level=getattr(cmdline_args, "log_level", "info"),
        output_mode=getattr(cmdline_args, "output_mode", "full"),
        use_colors=not getattr(cmdline_args, "no_color", False),
        compare_hashes=not bool(cmdline_args.compare_hashes),  # Note: inverted logic from original
        use_profiler=bool(cmdline_args.use_profiler),
        filters=getattr(cmdline_args, "filter", None),
        logging_enabled=bool(cmdline_args.logging is None or cmdline_args.logging),
    )

    # Run the application
    exit_code: int = run_application(config)
    sys.exit(exit_code)


def has_cli_paths(cmdline_args: Namespace) -> bool:
    """Check if CLI paths were provided."""
    return bool(
        cmdline_args.path1
        or cmdline_args.path2
        or cmdline_args.path3
        or cmdline_args.extra_paths
    )
