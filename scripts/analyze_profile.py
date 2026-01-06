#!/usr/bin/env python3
"""Comprehensive profile analysis tool for identifying performance bottlenecks.

This script analyzes cProfile output files (.prof) and provides detailed
breakdowns of function execution times, call counts, and call chains.

Features:
- Analyze by cumulative time (includes subcalls)
- Analyze by self time (actual CPU time spent)
- Analyze by call count (most frequently called functions)
- Callers analysis (who calls the hot functions)
- Callees analysis (what the hot functions call)
- Output to stdout or file
- Configurable top-N counts for each analysis type
- Default path discovery for common profile locations

Examples:
    # Analyze a profile file and print to stdout
    python scripts/analyze_profile.py tests/cProfile/test_component_equivalence_20251203_160047.prof

    # Analyze and save to file
    python scripts/analyze_profile.py profile.prof --output analysis.txt

    # Customize the number of top functions shown
    python scripts/analyze_profile.py profile.prof --top-cumulative 100 --top-self 100

    # Quick analysis with fewer details
    python scripts/analyze_profile.py profile.prof --top-cumulative 20 --top-self 20 --no-callers --no-callees

    # Try common default profile file paths
    python scripts/analyze_profile.py --default-paths
"""
from __future__ import annotations

import argparse
import pstats
import sys
from datetime import datetime
from pathlib import Path
from typing import TextIO


def get_default_profile_paths() -> list[Path]:
    """Get list of common default profile file paths to try.

    Returns:
    ----
        List of Path objects to check for profile files
    """
    return [
        Path("tests/cProfile/test_component_equivalence_20251203_160047.prof"),
        Path("tslpatchdata/test_kotordiff_profile.prof"),
        Path("profile.prof"),
    ]


def find_profile_file(profile_file: Path | None, use_defaults: bool) -> Path:
    """Find the profile file to analyze.

    Args:
    ----
        profile_file: Explicitly provided profile file path, or None
        use_defaults: Whether to try default paths if profile_file is None

    Returns:
    ----
        Path to the profile file to analyze

    Raises:
    ------
        SystemExit: If no profile file can be found
    """
    if profile_file is not None:
        if not profile_file.exists():
            print(f"Profile file not found: {profile_file}", file=sys.stderr)
            sys.exit(1)
        return profile_file

    if not use_defaults:
        print("Error: profile_file is required (or use --default-paths to try common paths)", file=sys.stderr)
        sys.exit(1)

    # Try common default paths
    for path in get_default_profile_paths():
        if path.exists():
            print(f"Using default profile file: {path}", file=sys.stderr)
            return path

    print("No profile file found. Use --default-paths to try common paths.", file=sys.stderr)
    sys.exit(1)


def analyze_profile(
    prof_file: Path,
    output_file: Path | None = None,
    top_cumulative: int = 50,
    top_self: int = 50,
    top_calls: int = 30,
    top_callers: int = 30,
    top_callees: int = 30,
) -> None:
    """Analyze a profile file and output results.

    Args:
    ----
        prof_file: Path to the .prof profile file to analyze
        output_file: Optional path to write output to (default: stdout)
        top_cumulative: Number of top functions by cumulative time to show
        top_self: Number of top functions by self time to show
        top_calls: Number of top functions by call count to show
        top_callers: Number of top callers to show (0 to skip)
        top_callees: Number of top callees to show (0 to skip)
    """
    if not prof_file.exists():
        print(f"Profile file not found: {prof_file}", file=sys.stderr)
        sys.exit(1)

    try:
        stats = pstats.Stats(str(prof_file))
    except Exception as e:
        print(f"Error loading profile file: {e}", file=sys.stderr)
        sys.exit(1)

    stats.strip_dirs()

    # Determine output destination
    output_stream: TextIO
    should_close: bool
    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_stream = output_file.open("w", encoding="utf-8")
        should_close = True
    else:
        output_stream = sys.stdout
        should_close = False

    try:
        # Header
        print("=" * 100, file=output_stream)
        print("COMPREHENSIVE PROFILE ANALYSIS - PERFORMANCE BOTTLENECKS", file=output_stream)
        print("=" * 100, file=output_stream)
        print(f"\nProfile file: {prof_file}", file=output_stream)
        print(f"Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=output_stream)
        print(f"Total function calls: {stats.total_calls:,}", file=output_stream)
        print(f"Total execution time: {stats.total_tt:.2f} seconds", file=output_stream)
        print(f"Total cumulative time: {stats.total_tt:.2f} seconds", file=output_stream)
        print(file=output_stream)

        # Top functions by cumulative time (includes time in subcalls)
        stats.sort_stats("cumulative")
        print("\n" + "=" * 100, file=output_stream)
        print(f"TOP {top_cumulative} FUNCTIONS BY CUMULATIVE TIME", file=output_stream)
        print("=" * 100, file=output_stream)
        print("(Includes time spent in called functions - shows call chain bottlenecks)", file=output_stream)
        stats.print_stats(top_cumulative, stream=output_stream)

        # Top functions by self time (actual CPU time spent)
        stats.sort_stats("tottime")
        print("\n" + "=" * 100, file=output_stream)
        print(f"TOP {top_self} FUNCTIONS BY SELF TIME (EXCLUDING SUBCALLS)", file=output_stream)
        print("=" * 100, file=output_stream)
        print("(Where CPU time is actually spent - the real bottlenecks)", file=output_stream)
        stats.print_stats(top_self, stream=output_stream)

        # Most called functions
        stats.sort_stats("ncalls")
        print("\n" + "=" * 100, file=output_stream)
        print(f"TOP {top_calls} FUNCTIONS BY CALL COUNT", file=output_stream)
        print("=" * 100, file=output_stream)
        print("(Functions called most frequently - may indicate inefficient loops)", file=output_stream)
        stats.print_stats(top_calls, stream=output_stream)

        # Callers analysis (who calls the hot functions)
        if top_callers > 0:
            stats.sort_stats("cumulative")
            print("\n" + "=" * 100, file=output_stream)
            print(f"CALLERS ANALYSIS - TOP {top_callers}", file=output_stream)
            print("=" * 100, file=output_stream)
            print("(Who calls the hot functions - shows the call chain)", file=output_stream)
            stats.print_callers(top_callers, stream=output_stream)

        # Callees analysis (what the hot functions call)
        if top_callees > 0:
            print("\n" + "=" * 100, file=output_stream)
            print(f"CALLEES ANALYSIS - TOP {top_callees}", file=output_stream)
            print("=" * 100, file=output_stream)
            print("(What the hot functions call - shows what makes them slow)", file=output_stream)
            stats.sort_stats("cumulative")
            stats.print_callees(top_callees, stream=output_stream)

        if output_file:
            print(f"\nAnalysis complete. Results written to: {output_file}", file=sys.stdout)
        else:
            print("\nAnalysis complete.", file=sys.stdout)

    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if should_close:
            output_stream.close()


def main() -> None:
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Comprehensive profile analysis tool for identifying performance bottlenecks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a profile file and print to stdout
  python scripts/analyze_profile.py tests/cProfile/test_component_equivalence_20251203_160047.prof

  # Analyze and save to file
  python scripts/analyze_profile.py profile.prof --output analysis.txt

  # Customize the number of top functions shown
  python scripts/analyze_profile.py profile.prof --top-cumulative 100 --top-self 100

  # Quick analysis with fewer details
  python scripts/analyze_profile.py profile.prof --top-cumulative 20 --top-self 20 --no-callers --no-callees

  # Try common default profile file paths
  python scripts/analyze_profile.py --default-paths
        """,
    )
    parser.add_argument(
        "profile_file",
        nargs="?",
        default=None,
        type=lambda x: Path(x) if x else None,
        help="Path to the .prof profile file to analyze (required if not using --default-paths)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Path to write output file (default: print to stdout)",
    )
    parser.add_argument(
        "--top-cumulative",
        type=int,
        default=50,
        help="Number of top functions by cumulative time to show (default: 50)",
    )
    parser.add_argument(
        "--top-self",
        type=int,
        default=50,
        help="Number of top functions by self time to show (default: 50)",
    )
    parser.add_argument(
        "--top-calls",
        type=int,
        default=30,
        help="Number of top functions by call count to show (default: 30)",
    )
    parser.add_argument(
        "--top-callers",
        type=int,
        default=30,
        help="Number of top callers to show (default: 30)",
    )
    parser.add_argument(
        "--top-callees",
        type=int,
        default=30,
        help="Number of top callees to show (default: 30)",
    )
    parser.add_argument(
        "--no-callers",
        action="store_true",
        help="Skip callers analysis",
    )
    parser.add_argument(
        "--no-callees",
        action="store_true",
        help="Skip callees analysis",
    )
    parser.add_argument(
        "--default-paths",
        action="store_true",
        help="Try common default profile file paths if profile_file not provided",
    )

    args = parser.parse_args()

    # Validate top-N arguments
    if args.top_cumulative < 0:
        print("Error: --top-cumulative must be non-negative", file=sys.stderr)
        sys.exit(1)
    if args.top_self < 0:
        print("Error: --top-self must be non-negative", file=sys.stderr)
        sys.exit(1)
    if args.top_calls < 0:
        print("Error: --top-calls must be non-negative", file=sys.stderr)
        sys.exit(1)
    if args.top_callers < 0:
        print("Error: --top-callers must be non-negative", file=sys.stderr)
        sys.exit(1)
    if args.top_callees < 0:
        print("Error: --top-callees must be non-negative", file=sys.stderr)
        sys.exit(1)

    # Find profile file
    prof_file = find_profile_file(args.profile_file, args.default_paths)

    # Adjust top counts based on flags
    top_callers = 0 if args.no_callers else args.top_callers
    top_callees = 0 if args.no_callees else args.top_callees

    analyze_profile(
        prof_file=prof_file,
        output_file=args.output,
        top_cumulative=args.top_cumulative,
        top_self=args.top_self,
        top_calls=args.top_calls,
        top_callers=top_callers,
        top_callees=top_callees,
    )


if __name__ == "__main__":
    main()
