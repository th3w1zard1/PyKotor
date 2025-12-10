"""KotorDiff CLI module (integrated into KotorCLI).

Provides the headless interface for structured KOTOR comparisons. When CLI
arguments are supplied we stay headless; otherwise callers should launch the
GUI wrapper.
"""

from __future__ import annotations

import io
import sys
import traceback
from argparse import ArgumentParser
from pathlib import Path
from typing import TYPE_CHECKING

from kotorcli.config import VERSION as KOTORCLI_VERSION

if TYPE_CHECKING:
    from argparse import Namespace


CURRENT_VERSION = KOTORCLI_VERSION


def add_kotordiff_arguments(parser: ArgumentParser) -> ArgumentParser:
    """Attach KotorDiff CLI arguments to a parser."""
    # Path arguments (multiple aliases for compatibility)
    parser.add_argument(
        "--path1",
        type=str,
        help="Path to compare. Multiple path flags can be supplied; at least two paths are required.",
    )
    parser.add_argument(
        "--path2",
        type=str,
        help="Additional path to compare.",
    )
    parser.add_argument(
        "--path3",
        type=str,
        help="Additional path to compare.",
    )
    parser.add_argument(
        "--path",
        action="append",
        dest="extra_paths",
        help="Additional paths for N-way comparison (can be used multiple times). Example: --path path4 --path path5",
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
    parser.add_argument(
        "--output-log",
        type=str,
        help="Filepath of the desired output logfile",
    )

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
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )

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
        help="Disable hash comparison for unsupported types",
    )
    parser.add_argument(
        "--filter",
        action="append",
        help="Filter specific files/modules for installation-wide diffs (can be used multiple times). Examples: 'tat_m18ac' for module, 'some_character.utc' for specific resource",
    )
    parser.add_argument(
        "--logging",
        dest="logging",
        action="store_true",
        default=True,
        help="Whether to log the results to a file (default is True)",
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
        help="Write TSLPatcher data incrementally when --tslpatchdata is provided (avoids batching everything at the end).",
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
    return parser


def parse_args(argv: list[str] | None = None) -> Namespace:
    """Create and configure the argument parser."""
    parser = ArgumentParser(
        description="Finds differences between KOTOR files/dirs. Supports comparisons across any number of paths.",
    )
    add_kotordiff_arguments(parser)
    return parser.parse_args(argv)


def normalize_path_arg(arg: str | None) -> str | None:
    """Normalize a path argument (handle quotes, etc.)."""
    if not arg:
        return None
    # Strip surrounding quotes
    arg = arg.strip().strip('"').strip("'")
    return arg or None


def execute_cli(cmdline_args: Namespace, *, exit_on_completion: bool = True) -> int:  # noqa: PLR0912
    """Execute CLI mode with the provided arguments.

    Args:
        cmdline_args: Parsed command line arguments
        exit_on_completion: When True, call sys.exit with the resulting code
    """
    from pykotor.extract.installation import Installation  # noqa: PLC0415

    from kotorcli.diff_tool.app import KotorDiffConfig, run_application  # noqa: PLC0415

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
        except Exception:
            print("Failed to configure console for UTF-8 output on Windows")  # noqa: T201
            print(traceback.format_exc())  # noqa: T201

    print(f"KotorDiff version {CURRENT_VERSION}")  # noqa: T201

    # Gather all path inputs
    raw_path_inputs: list[str] = []

    if cmdline_args.path1:
        normalized = normalize_path_arg(cmdline_args.path1)
        if normalized:
            raw_path_inputs.append(normalized)
    if cmdline_args.path2:
        normalized = normalize_path_arg(cmdline_args.path2)
        if normalized:
            raw_path_inputs.append(normalized)
    if cmdline_args.path3:
        normalized = normalize_path_arg(cmdline_args.path3)
        if normalized:
            raw_path_inputs.append(normalized)

    if cmdline_args.extra_paths:
        for path_value in cmdline_args.extra_paths:
            normalized = normalize_path_arg(path_value)
            if normalized:
                raw_path_inputs.append(normalized)

    if len(raw_path_inputs) < 2:
        print("[Error] At least 2 paths are required for comparison.", file=sys.stderr)  # noqa: T201
        print("[Info] Use --help to see CLI options", file=sys.stderr)  # noqa: T201
        if exit_on_completion:
            sys.exit(1)
        return 1

    # Convert string paths to Path/Installation objects
    resolved_paths: list[Path | Installation] = []
    for path_str in raw_path_inputs:
        path_obj = Path(path_str)
        try:
            # Try to create an Installation object (for KOTOR installations)
            installation = Installation(path_obj)
            resolved_paths.append(installation)
            print(f"[DEBUG] Loaded Installation for: {path_str}")  # noqa: T201
        except Exception as exc:
            # Fall back to Path object (for folders/files)
            resolved_paths.append(path_obj)
            print(f"[DEBUG] Using Path (not Installation) for: {path_str}")  # noqa: T201
            print(f"[DEBUG] Installation load failed: {exc.__class__.__name__}: {exc}")  # noqa: T201

    # Create configuration object
    config = KotorDiffConfig(
        paths=resolved_paths,
        tslpatchdata_path=Path(cmdline_args.tslpatchdata) if cmdline_args.tslpatchdata else None,
        ini_filename=cmdline_args.ini,
        output_log_path=Path(cmdline_args.output_log) if cmdline_args.output_log else None,
        log_level=cmdline_args.log_level,
        output_mode=cmdline_args.output_mode,
        use_colors=not cmdline_args.no_color,
        compare_hashes=bool(cmdline_args.compare_hashes),
        use_profiler=bool(cmdline_args.use_profiler),
        filters=cmdline_args.filter or None,
        logging_enabled=bool(cmdline_args.logging),
        use_incremental_writer=bool(cmdline_args.use_incremental_writer),
    )

    # Run the application
    exit_code: int = run_application(config)
    if exit_on_completion:
        sys.exit(exit_code)
    return exit_code


def has_cli_paths(cmdline_args: Namespace) -> bool:
    """Check if CLI paths were provided."""
    return bool(cmdline_args.path1 or cmdline_args.path2 or cmdline_args.path3 or cmdline_args.extra_paths)
