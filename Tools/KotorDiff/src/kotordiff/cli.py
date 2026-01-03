"""KotorDiff CLI module.

This module provides command-line interface functionality for KotorDiff,
separate from the GUI to allow CLI usage without tkinter installed.
"""
from __future__ import annotations

import io
import sys
import traceback

from argparse import ArgumentParser
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace

CURRENT_VERSION = "1.0.0"


def parse_args() -> Namespace:
    """Create and configure the argument parser."""
    parser = ArgumentParser(
        description="Finds differences between KOTOR files/dirs. Supports comparisons across any number of paths."
    )

    # Path arguments (multiple aliases for compatibility)
    parser.add_argument(
        "--path1", type=str,
        help="Path to compare. Multiple path flags can be supplied; at least two paths are required."
    )
    parser.add_argument(
        "--path2", type=str,
        help="Additional path to compare."
    )
    parser.add_argument(
        "--path3", type=str,
        help="Additional path to compare."
    )
    parser.add_argument(
        "--path",
        action="append",
        dest="extra_paths",
        help="Additional paths for N-way comparison (can be used multiple times). "
        "Example: --path path4 --path path5"
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
        help="Filepath of the desired output logfile"
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
        help="Disable colored output"
    )

    # Comparison options
    parser.add_argument(
        "--compare-hashes",
        type=bool,
        default=True,
        help="Compare hashes of any unsupported file/resource type (default is True)",
    )
    parser.add_argument(
        "--filter",
        action="append",
        help="Filter specific files/modules for installation-wide diffs (can be used multiple times). "
        "Examples: 'tat_m18ac' for module, 'some_character.utc' for specific resource",
    )
    parser.add_argument(
        "--logging",
        type=bool,
        default=True,
        help="Whether to log the results to a file or not (default is True)",
    )
    parser.add_argument(
        "--use-profiler",
        type=bool,
        default=False,
        help="Use cProfile to find where most of the execution time is taking place in source code.",
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
    from kotordiff.app import KotorDiffConfig, run_application
    from pykotor.extract.installation import Installation

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
            print("Failed to configure console for UTF-8 output on Windows")
            print(traceback.format_exc())

    print(f"KotorDiff version {CURRENT_VERSION}")

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
        print("[Error] At least 2 paths are required for comparison.", file=sys.stderr)
        print("[Info] Use --help to see CLI options", file=sys.stderr)
        sys.exit(1)

    # Convert string paths to Path/Installation objects
    resolved_paths: list[Path | Installation] = []
    for path_str in raw_path_inputs:
        path_obj = Path(path_str)
        try:
            # Try to create an Installation object (for KOTOR installations)
            installation = Installation(path_obj)
            resolved_paths.append(installation)
            print(f"[DEBUG] Loaded Installation for: {path_str}")
        except Exception as e:  # noqa: BLE001
            # Fall back to Path object (for folders/files)
            resolved_paths.append(path_obj)
            print(f"[DEBUG] Using Path (not Installation) for: {path_str}")
            print(f"[DEBUG] Installation load failed: {e.__class__.__name__}: {e}")

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

