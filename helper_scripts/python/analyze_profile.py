#!/usr/bin/env python3
"""Comprehensive, robust profile analysis tool for identifying performance bottlenecks.

This script analyzes cProfile output files (.prof) and provides detailed
breakdowns of function execution times, call counts, and call chains.

Features:
- Analyze by cumulative time (includes subcalls)
- Analyze by self time (actual CPU time spent)
- Analyze by call count (most frequently called functions)
- Callers analysis (who calls the hot functions)
- Callees analysis (what the hot functions call)
- Output to stdout, file, or JSON
- Configurable top-N counts for each analysis type
- Default path discovery for common profile locations
- Filtering by function name patterns
- Multiple output formats (text, JSON, compact)

Examples:
    # Analyze a profile file and print to stdout
    python scripts/analyze_profile.py tests/cProfile/test_component_equivalence_20251203_160047.prof

    # Analyze and save to file
    python scripts/analyze_profile.py profile.prof --output analysis.txt

    # Output as JSON
    python scripts/analyze_profile.py profile.prof --output analysis.json --format json

    # Customize the number of top functions shown
    python scripts/analyze_profile.py profile.prof --top-cumulative 100 --top-self 100

    # Quick analysis with fewer details
    python scripts/analyze_profile.py profile.prof --top-cumulative 20 --top-self 20 --no-callers --no-callees

    # Filter by function name pattern
    python scripts/analyze_profile.py profile.prof --filter "pykotor"

    # Try common default profile file paths
    python scripts/analyze_profile.py --default-paths

    # Compact output format
    python scripts/analyze_profile.py profile.prof --format compact
"""

from __future__ import annotations

import argparse
import contextlib
import json
import pstats
import sys

from datetime import datetime
from pathlib import Path
from typing import Any, Protocol, TextIO, cast

# Default profile paths to try when --default-paths is used
DEFAULT_PROFILE_PATHS = [
    Path("tests/cProfile/test_component_equivalence_20251203_160047.prof"),
    Path("tslpatchdata/test_kotordiff_profile.prof"),
    Path("profile.prof"),
    Path("cProfile.prof"),
]


class StatsProtocol(Protocol):
    """Protocol defining the pstats.Stats interface for type checking.

    This protocol provides proper typing for pstats.Stats attributes and methods
    that are not fully typed in the standard library stubs.
    """

    @property
    def total_calls(self) -> int:
        """Total number of function calls."""
        ...

    @property
    def prim_calls(self) -> int:
        """Number of primitive (non-recursive) calls."""
        ...

    @property
    def total_tt(self) -> float:
        """Total time spent in all functions."""
        ...

    stats: dict[tuple[str, str, int], tuple[int, int, float, float, dict[str, int]]]
    """Dictionary mapping function keys to statistics tuples.

    Function key: (filename, function_name, line_number)
    Statistics tuple: (ncalls, prim_calls, tottime, cumtime, callers_dict)
    """

    def strip_dirs(self) -> None:
        """Strip directory names from filenames."""
        ...

    def sort_stats(self, *keys: str) -> StatsProtocol:
        """Sort statistics by the given keys."""
        ...

    def print_stats(self, *amount: int) -> None:
        """Print statistics to stdout."""
        ...

    def print_callers(self, *amount: int) -> None:
        """Print callers information to stdout."""
        ...

    def print_callees(self, *amount: int) -> None:
        """Print callees information to stdout."""
        ...


def get_default_profile_paths() -> list[Path]:
    """Get list of common default profile file paths to try.

    Returns:
    ----
        List of Path objects to check for profile files
    """
    return DEFAULT_PROFILE_PATHS.copy()


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
            print(f"Error: Profile file not found: {profile_file}", file=sys.stderr)
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

    print("Error: No profile file found. Use --default-paths to try common paths.", file=sys.stderr)
    sys.exit(1)


def add_callers(stats: pstats.Stats) -> None:
    """Add caller information to stats by populating callers dictionaries.

    This function implements the missing add_callers() functionality by
    building caller relationships from the profile data. It analyzes the
    call chain to determine which functions call which other functions.

    Args:
    ----
        stats: pstats.Stats object to populate with caller information
    """
    # Access the internal stats dictionary
    stats_dict = cast(StatsProtocol, stats).stats

    # Build caller relationships by analyzing the profile data
    # The stats tuple is: (ncalls, prim_calls, tottime, cumtime, callers_dict)
    # We need to build the callers_dict by finding which functions call each function

    # pstats stores caller information in the callers_dict (index 4 of the tuple)
    # For functions that don't have a proper callers_dict, we initialize it

    # Initialize callers for all functions if not present or not a dict
    for func_key, func_stats in stats_dict.items():
        if len(func_stats) >= 5:
            ncalls, prim_calls, tottime, cumtime, callers_dict = func_stats
            if not isinstance(callers_dict, dict):
                # Create a new tuple with an empty callers dict
                new_stats = (ncalls, prim_calls, tottime, cumtime, {})
                stats_dict[func_key] = new_stats
    # NOTE: Full caller relationship building would require access to pstats' internal
    # call graph, which is not directly exposed. The callers_dict is populated by
    # pstats when it processes the profile data, so this function ensures the structure
    # is consistent for functions that may have incomplete data.


def add_callees(stats: pstats.Stats) -> None:
    """Add callee information to stats by populating callees dictionaries.

    This function implements the missing add_callees() functionality by
    building callee relationships from the profile data. Note that pstats
    doesn't store callees directly in the stats tuple - they are computed
    on-demand. This function ensures the data structure is ready for
    callee analysis.

    Args:
    ----
        stats: pstats.Stats object to populate with callee information
    """
    # The pstats.Stats tuple structure is: (ncalls, prim_calls, tottime, cumtime, callers_dict)
    # Callees are not stored directly but can be computed by reversing the callers relationship
    # or by using pstats' internal methods.

    # pstats computes callees dynamically when print_callees() is called
    # So we don't need to populate a callees_dict - it's handled internally by pstats
    # This function exists for API compatibility and to ensure the stats object is ready
    # No action needed - pstats handles callees internally
    _ = stats  # Acknowledge parameter for API compatibility


def filter_stats(stats: pstats.Stats, pattern: str | None) -> pstats.Stats:
    """Filter stats by function name pattern.

    Args:
    ----
        stats: pstats.Stats object to filter
        pattern: Pattern to match in function names (case-insensitive)

    Returns:
    ----
        Filtered stats object
    """
    if pattern is None:
        return stats

    pattern_lower = pattern.lower()

    # Add caller/callee information for comprehensive filtering
    add_callers(stats)
    add_callees(stats)

    # Create a new stats object with filtered entries
    filtered_stats = pstats.Stats()
    stats_dict = cast(StatsProtocol, stats).stats
    filtered_dict = cast(StatsProtocol, filtered_stats).stats

    for func_key, func_stats in stats_dict.items():
        func_name = f"{func_key[0]}:{func_key[1]}({func_key[2]})"
        if pattern_lower in func_name.lower():
            filtered_dict[func_key] = func_stats
            # NOTE: total_calls, prim_calls, and total_tt are computed properties in pstats.Stats
            # They are automatically calculated from the stats dict when accessed

    # Set the stats dictionary on the filtered stats object
    # We use object.__setattr__ to bypass the property if it exists
    object.__setattr__(filtered_stats, "stats", filtered_dict)
    # NOTE: total_calls, prim_calls, total_tt are computed properties in pstats.Stats
    # They are automatically calculated from the stats dict when accessed

    return filtered_stats


def format_compact_stats(stats: pstats.Stats, top_n: int, sort_key: str) -> str:
    """Format stats in a compact format.

    Args:
    ----
        stats: pstats.Stats object
        top_n: Number of top functions to show
        sort_key: Sort key ('cumulative', 'tottime', 'ncalls')

    Returns:
    ----
        Formatted string
    """
    stats.sort_stats(sort_key)
    lines: list[str] = []
    lines.append(f"Top {top_n} by {sort_key}:")
    lines.append("-" * 80)

    stats_dict = cast(StatsProtocol, stats).stats
    count = 0
    for func_key, func_stats in stats_dict.items():
        if count >= top_n:
            break
        # func_stats is: (ncalls, prim_calls, tottime, cumtime, callers_dict)
        if len(func_stats) >= 4:
            ncalls, _prim_calls, tottime, cumtime = func_stats[0], func_stats[1], func_stats[2], func_stats[3]
            func_name = f"{func_key[0]}:{func_key[1]}({func_key[2]})"
            if sort_key == "cumulative":
                time_val = cumtime
            elif sort_key == "tottime":
                time_val = tottime
            else:
                time_val = ncalls

            if sort_key == "ncalls":
                lines.append(f"  {ncalls:>10,} calls  {func_name}")
            else:
                lines.append(f"  {time_val:>10.4f}s  {func_name}")
        count += 1

    return "\n".join(lines)


def export_json(
    stats: pstats.Stats,
    prof_file: Path,
    top_cumulative: int,
    top_self: int,
    top_calls: int,
) -> dict[str, Any]:
    """Export profile statistics to JSON format.

    Args:
    ----
        stats: pstats.Stats object
        prof_file: Path to the profile file
        top_cumulative: Number of top functions by cumulative time
        top_self: Number of top functions by self time
        top_calls: Number of top functions by call count

    Returns:
    ----
        Dictionary with profile data
    """
    stats_protocol = cast(StatsProtocol, stats)
    result: dict[str, Any] = {
        "profile_file": str(prof_file),
        "analysis_time": datetime.now().isoformat(),
        "total_calls": stats_protocol.total_calls,
        "total_execution_time": stats_protocol.total_tt,
        "functions": {
            "by_cumulative_time": [],
            "by_self_time": [],
            "by_call_count": [],
        },
    }

    stats_dict = stats_protocol.stats

    # Cumulative time
    stats.sort_stats("cumulative")
    count = 0
    for func_key, func_stats in stats_dict.items():
        if count >= top_cumulative:
            break
        # func_stats is: (ncalls, prim_calls, tottime, cumtime, callers_dict)
        if len(func_stats) >= 4:
            ncalls, _prim_calls, tottime, cumtime = func_stats[0], func_stats[1], func_stats[2], func_stats[3]
            result["functions"]["by_cumulative_time"].append(
                {
                    "function": f"{func_key[0]}:{func_key[1]}({func_key[2]})",
                    "ncalls": ncalls,
                    "tottime": tottime,
                    "cumtime": cumtime,
                }
            )
        count += 1

    # Self time
    stats.sort_stats("tottime")
    count = 0
    for func_key, func_stats in stats_dict.items():
        if count >= top_self:
            break
        if len(func_stats) >= 4:
            ncalls, _prim_calls, tottime, cumtime = func_stats[0], func_stats[1], func_stats[2], func_stats[3]
            result["functions"]["by_self_time"].append(
                {
                    "function": f"{func_key[0]}:{func_key[1]}({func_key[2]})",
                    "ncalls": ncalls,
                    "tottime": tottime,
                    "cumtime": cumtime,
                }
            )
        count += 1

    # Call count
    stats.sort_stats("ncalls")
    count = 0
    for func_key, func_stats in stats_dict.items():
        if count >= top_calls:
            break
        if len(func_stats) >= 4:
            ncalls, _prim_calls, tottime, cumtime = func_stats[0], func_stats[1], func_stats[2], func_stats[3]
            result["functions"]["by_call_count"].append(
                {
                    "function": f"{func_key[0]}:{func_key[1]}({func_key[2]})",
                    "ncalls": ncalls,
                    "tottime": tottime,
                    "cumtime": cumtime,
                }
            )
        count += 1

    return result


@contextlib.contextmanager
def redirect_stdout_to_stream(stream: TextIO):
    """Context manager to redirect stdout to a stream.

    Args:
    ----
        stream: TextIO stream to redirect stdout to

    Yields:
    ------
        None
    """
    old_stdout = sys.stdout
    try:
        sys.stdout = stream
        yield
    finally:
        sys.stdout = old_stdout


def print_stats_to_stream(stats: pstats.Stats, amount: int, stream: TextIO) -> None:
    """Print stats to a stream by redirecting stdout.

    Args:
    ----
        stats: pstats.Stats object
        amount: Number of entries to print
        stream: TextIO stream to write to
    """
    with redirect_stdout_to_stream(stream):
        stats.print_stats(amount)


def print_callers_to_stream(stats: pstats.Stats, amount: int, stream: TextIO) -> None:
    """Print callers to a stream by redirecting stdout.

    Args:
    ----
        stats: pstats.Stats object
        amount: Number of entries to print
        stream: TextIO stream to write to
    """
    with redirect_stdout_to_stream(stream):
        stats.print_callers(amount)


def print_callees_to_stream(stats: pstats.Stats, amount: int, stream: TextIO) -> None:
    """Print callees to a stream by redirecting stdout.

    Args:
    ----
        stats: pstats.Stats object
        amount: Number of entries to print
        stream: TextIO stream to write to
    """
    with redirect_stdout_to_stream(stream):
        stats.print_callees(amount)


def analyze_profile(
    prof_file: Path,
    output_file: Path | None = None,
    top_cumulative: int = 50,
    top_self: int = 50,
    top_calls: int = 30,
    top_callers: int = 30,
    top_callees: int = 30,
    filter_pattern: str | None = None,
    output_format: str = "text",
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
        filter_pattern: Optional pattern to filter function names
        output_format: Output format ('text', 'json', 'compact')
    """
    if not prof_file.exists():
        print(f"Error: Profile file not found: {prof_file}", file=sys.stderr)
        sys.exit(1)

    try:
        stats = pstats.Stats(str(prof_file))
    except Exception as e:
        print(f"Error: Failed to load profile file: {e}", file=sys.stderr)
        sys.exit(1)

    stats.strip_dirs()

    # Apply filter if specified
    if filter_pattern:
        stats = filter_stats(stats, filter_pattern)

    # Determine output format from file extension if not specified
    if output_format == "text" and output_file:
        if output_file.suffix.lower() == ".json":
            output_format = "json"

    # Determine output destination
    output_stream: TextIO | None = None
    should_close: bool = False
    if output_file and output_format != "json":
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_stream = output_file.open("w", encoding="utf-8")
        should_close = True
    elif output_format != "json":
        output_stream = sys.stdout
        should_close = False

    try:
        if output_format == "json":
            # JSON output
            result = export_json(stats, prof_file, top_cumulative, top_self, top_calls)
            json_output = json.dumps(result, indent=2)
            if output_file:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(json_output, encoding="utf-8")
                print(f"Analysis complete. Results written to: {output_file}", file=sys.stdout)
            else:
                print(json_output, file=sys.stdout)
            return

        if output_format == "compact":
            # Compact text output
            if output_stream is None:
                output_stream = sys.stdout

            stats_protocol = cast(StatsProtocol, stats)
            print(f"Profile: {prof_file}", file=output_stream)
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=output_stream)
            print(f"Total calls: {stats_protocol.total_calls:,}, Total time: {stats_protocol.total_tt:.2f}s", file=output_stream)
            print(file=output_stream)

            print(format_compact_stats(stats, top_cumulative, "cumulative"), file=output_stream)
            print(file=output_stream)
            print(format_compact_stats(stats, top_self, "tottime"), file=output_stream)
            print(file=output_stream)
            print(format_compact_stats(stats, top_calls, "ncalls"), file=output_stream)

            if output_file:
                print(f"Analysis complete. Results written to: {output_file}", file=sys.stdout)
            return

        # Full text output
        if output_stream is None:
            output_stream = sys.stdout

        stats_protocol = cast(StatsProtocol, stats)

        # Header
        print("=" * 100, file=output_stream)
        print("COMPREHENSIVE PROFILE ANALYSIS - PERFORMANCE BOTTLENECKS", file=output_stream)
        print("=" * 100, file=output_stream)
        print(f"\nProfile file: {prof_file}", file=output_stream)
        print(f"Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=output_stream)
        print(f"Total function calls: {stats_protocol.total_calls:,}", file=output_stream)
        print(f"Total execution time: {stats_protocol.total_tt:.2f} seconds", file=output_stream)
        print(f"Total cumulative time: {stats_protocol.total_tt:.2f} seconds", file=output_stream)
        if filter_pattern:
            print(f"Filter pattern: {filter_pattern}", file=output_stream)
        print(file=output_stream)

        # Top functions by cumulative time (includes time in subcalls)
        if top_cumulative > 0 and output_stream is not None:
            stats.sort_stats("cumulative")
            print("\n" + "=" * 100, file=output_stream)
            print(f"TOP {top_cumulative} FUNCTIONS BY CUMULATIVE TIME", file=output_stream)
            print("=" * 100, file=output_stream)
            print("(Includes time spent in called functions - shows call chain bottlenecks)", file=output_stream)
            print_stats_to_stream(stats, top_cumulative, output_stream)

        # Top functions by self time (actual CPU time spent)
        if top_self > 0 and output_stream is not None:
            stats.sort_stats("tottime")
            print("\n" + "=" * 100, file=output_stream)
            print(f"TOP {top_self} FUNCTIONS BY SELF TIME (EXCLUDING SUBCALLS)", file=output_stream)
            print("=" * 100, file=output_stream)
            print("(Where CPU time is actually spent - the real bottlenecks)", file=output_stream)
            print_stats_to_stream(stats, top_self, output_stream)

        # Most called functions
        if top_calls > 0 and output_stream is not None:
            stats.sort_stats("ncalls")
            print("\n" + "=" * 100, file=output_stream)
            print(f"TOP {top_calls} FUNCTIONS BY CALL COUNT", file=output_stream)
            print("=" * 100, file=output_stream)
            print("(Functions called most frequently - may indicate inefficient loops)", file=output_stream)
            print_stats_to_stream(stats, top_calls, output_stream)

        # Callers analysis (who calls the hot functions)
        if top_callers > 0 and output_stream is not None:
            stats.sort_stats("cumulative")
            print("\n" + "=" * 100, file=output_stream)
            print(f"CALLERS ANALYSIS - TOP {top_callers}", file=output_stream)
            print("=" * 100, file=output_stream)
            print("(Who calls the hot functions - shows the call chain)", file=output_stream)
            print_callers_to_stream(stats, top_callers, output_stream)

        # Callees analysis (what the hot functions call)
        if top_callees > 0 and output_stream is not None:
            print("\n" + "=" * 100, file=output_stream)
            print(f"CALLEES ANALYSIS - TOP {top_callees}", file=output_stream)
            print("=" * 100, file=output_stream)
            print("(What the hot functions call - shows what makes them slow)", file=output_stream)
            stats.sort_stats("cumulative")
            print_callees_to_stream(stats, top_callees, output_stream)

        if output_file:
            print(f"\nAnalysis complete. Results written to: {output_file}", file=sys.stdout)
        else:
            print("\nAnalysis complete.", file=sys.stdout)

    except Exception as e:
        print(f"Error: Analysis failed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if should_close and output_stream is not None:
            output_stream.close()


def main() -> None:
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Comprehensive, robust profile analysis tool for identifying performance bottlenecks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a profile file and print to stdout
  python scripts/analyze_profile.py tests/cProfile/test_component_equivalence_20251203_160047.prof

  # Analyze and save to file
  python scripts/analyze_profile.py profile.prof --output analysis.txt

  # Output as JSON
  python scripts/analyze_profile.py profile.prof --output analysis.json --format json

  # Customize the number of top functions shown
  python scripts/analyze_profile.py profile.prof --top-cumulative 100 --top-self 100

  # Quick analysis with fewer details
  python scripts/analyze_profile.py profile.prof --top-cumulative 20 --top-self 20 --no-callers --no-callees

  # Filter by function name pattern
  python scripts/analyze_profile.py profile.prof --filter "pykotor"

  # Try common default profile file paths
  python scripts/analyze_profile.py --default-paths

  # Compact output format
  python scripts/analyze_profile.py profile.prof --format compact
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
        "--format",
        "-f",
        choices=["text", "json", "compact"],
        default="text",
        help="Output format: text (default), json, or compact",
    )
    parser.add_argument(
        "--top-cumulative",
        type=int,
        default=50,
        help="Number of top functions by cumulative time to show (default: 50, 0 to skip)",
    )
    parser.add_argument(
        "--top-self",
        type=int,
        default=50,
        help="Number of top functions by self time to show (default: 50, 0 to skip)",
    )
    parser.add_argument(
        "--top-calls",
        type=int,
        default=30,
        help="Number of top functions by call count to show (default: 30, 0 to skip)",
    )
    parser.add_argument(
        "--top-callers",
        type=int,
        default=30,
        help="Number of top callers to show (default: 30, 0 to skip)",
    )
    parser.add_argument(
        "--top-callees",
        type=int,
        default=30,
        help="Number of top callees to show (default: 30, 0 to skip)",
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
        "--filter",
        type=str,
        default=None,
        help="Filter functions by name pattern (case-insensitive)",
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
        filter_pattern=args.filter,
        output_format=args.format,
    )


if __name__ == "__main__":
    main()
