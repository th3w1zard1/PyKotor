#!/usr/bin/env python3
"""Analyze cProfile output files to identify performance bottlenecks.

Wrapper script that calls the Python analyze_profile.py script to analyze
cProfile output files (.prof) and identify performance bottlenecks in tests
or application code.

Examples:
    python scripts/analyze_cprofile.py tests/cProfile/test_component_equivalence_20251203_160047.prof

    python scripts/analyze_cprofile.py profile.prof --output analysis.txt

    python scripts/analyze_cprofile.py --default-paths
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze cProfile output files to identify performance bottlenecks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "profile_file",
        nargs="?",
        default=None,
        help="Path to the .prof profile file to analyze",
    )

    parser.add_argument(
        "-o",
        "--output",
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
        "--default-paths",
        action="store_true",
        help="Try common default profile file paths if profile_file not provided",
    )

    args = parser.parse_args()

    # Build argument list for Python script
    script_dir = Path(__file__).parent
    analyze_profile_script = script_dir / "analyze_profile.py"

    if not analyze_profile_script.exists():
        print(f"Error: analyze_profile.py not found at {analyze_profile_script}", file=sys.stderr)
        sys.exit(1)

    python_args = [str(analyze_profile_script)]

    if args.profile_file:
        python_args.append(args.profile_file)

    if args.output:
        python_args.extend(["--output", args.output])

    if args.top_cumulative != 50:
        python_args.extend(["--top-cumulative", str(args.top_cumulative)])

    if args.top_self != 50:
        python_args.extend(["--top-self", str(args.top_self)])

    if args.top_calls != 30:
        python_args.extend(["--top-calls", str(args.top_calls)])

    if args.default_paths:
        python_args.append("--default-paths")

    # Call the Python script
    try:
        sys.exit(subprocess.call([sys.executable] + python_args))
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
