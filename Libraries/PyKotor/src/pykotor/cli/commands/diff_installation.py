"""KotorDiff-driven comparison command for PyKotor CLI."""

from __future__ import annotations

from argparse import Namespace

from loggerplus import RobustLogger as Logger  # type: ignore[import-untyped]


def cmd_diff_installation(args: Namespace, logger: Logger) -> int:
    """Run the KotorDiff tool via the kotordiff package.

    This command delegates to the `kotor-diff` package if installed.
    If not available, provides a helpful error message.

    Args:
    ----
        args: Parsed command line arguments
        logger: Logger instance

    Returns:
    -------
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Use pykotor.diff_tool
        from pykotor.diff_tool.__main__ import main as kotordiff_main

        # Convert argparse Namespace to list of strings for kotordiff
        import sys

        # Reconstruct argv from args namespace
        argv: list[str] = []
        if hasattr(args, "path1") and args.path1:
            argv.extend(["--path1", str(args.path1)])
        if hasattr(args, "path2") and args.path2:
            argv.extend(["--path2", str(args.path2)])
        if hasattr(args, "path3") and args.path3:
            argv.extend(["--path3", str(args.path3)])
        if hasattr(args, "extra_paths") and args.extra_paths:
            for path in args.extra_paths:
                argv.extend(["--path", str(path)])
        if hasattr(args, "tslpatchdata") and args.tslpatchdata:
            argv.extend(["--tslpatchdata", str(args.tslpatchdata)])
        if hasattr(args, "ini") and args.ini:
            argv.extend(["--ini", str(args.ini)])
        if hasattr(args, "output_log") and args.output_log:
            argv.extend(["--output-log", str(args.output_log)])
        if hasattr(args, "log_level") and args.log_level:
            argv.extend(["--log-level", str(args.log_level)])
        if hasattr(args, "output_mode") and args.output_mode:
            argv.extend(["--output-mode", str(args.output_mode)])
        if hasattr(args, "no_color") and args.no_color:
            argv.append("--no-color")
        if hasattr(args, "compare_hashes") and args.compare_hashes is not None:
            if args.compare_hashes:
                argv.append("--compare-hashes")
            else:
                argv.append("--no-compare-hashes")
        if hasattr(args, "filter") and args.filter:
            for f in args.filter:
                argv.extend(["--filter", str(f)])
        if hasattr(args, "logging") and args.logging is not None:
            if args.logging:
                argv.append("--logging")
            else:
                argv.append("--no-logging")
        if hasattr(args, "use_profiler") and args.use_profiler:
            argv.append("--use-profiler")
        if hasattr(args, "use_incremental_writer") and args.use_incremental_writer:
            argv.append("--incremental")
        if hasattr(args, "console") and args.console:
            argv.append("--console")
        if hasattr(args, "gui") and args.gui:
            argv.append("--gui")
        if hasattr(args, "output_mode") and args.output_mode:
            argv.extend(["--output-mode", str(args.output_mode)])

        return kotordiff_main(argv)
    except ImportError:
        logger.error(
            "KotorDiff functionality requires the 'kotor-diff' package to be installed.\n"
            "Install it with: pip install kotor-diff\n"
            "Or use the standalone kotordiff tool."
        )
        return 1
    except Exception:
        logger.exception("KotorDiff execution failed")
        return 1
