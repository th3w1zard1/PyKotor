#!/bin/bash
# Analyze cProfile output files to identify performance bottlenecks.
#
# Wrapper script that calls the Python analyze_profile.py script to analyze
# cProfile output files (.prof) and identify performance bottlenecks in tests
# or application code.
#
# Examples:
#     ./scripts/analyze_cprofile.sh tests/cProfile/test_component_equivalence_20251203_160047.prof
#
#     ./scripts/analyze_cprofile.sh profile.prof --output analysis.txt
#
#     ./scripts/analyze_cprofile.sh --default-paths

set -euo pipefail

# Default values
PROFILE_FILE=""
OUTPUT=""
TOP_CUMULATIVE=50
TOP_SELF=50
TOP_CALLS=30
DEFAULT_PATHS=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--output)
            OUTPUT="$2"
            shift 2
            ;;
        --top-cumulative)
            TOP_CUMULATIVE="$2"
            shift 2
            ;;
        --top-self)
            TOP_SELF="$2"
            shift 2
            ;;
        --top-calls)
            TOP_CALLS="$2"
            shift 2
            ;;
        --default-paths)
            DEFAULT_PATHS=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [PROFILE_FILE] [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -o, --output PATH          Path to write output file (default: print to stdout)"
            echo "  --top-cumulative N         Number of top functions by cumulative time (default: 50)"
            echo "  --top-self N               Number of top functions by self time (default: 50)"
            echo "  --top-calls N              Number of top functions by call count (default: 30)"
            echo "  --default-paths            Try common default profile file paths"
            echo "  -h, --help                 Show this help message"
            exit 0
            ;;
        *)
            if [[ -z "$PROFILE_FILE" ]]; then
                PROFILE_FILE="$1"
            else
                echo "Error: Unexpected argument: $1" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANALYZE_PROFILE_SCRIPT="$SCRIPT_DIR/analyze_profile.py"

if [[ ! -f "$ANALYZE_PROFILE_SCRIPT" ]]; then
    echo "Error: analyze_profile.py not found at $ANALYZE_PROFILE_SCRIPT" >&2
    exit 1
fi

# Build argument list
PYTHON_ARGS=()

if [[ -n "$PROFILE_FILE" ]]; then
    PYTHON_ARGS+=("$PROFILE_FILE")
fi

if [[ -n "$OUTPUT" ]]; then
    PYTHON_ARGS+=(--output "$OUTPUT")
fi

if [[ "$TOP_CUMULATIVE" != "50" ]]; then
    PYTHON_ARGS+=(--top-cumulative "$TOP_CUMULATIVE")
fi

if [[ "$TOP_SELF" != "50" ]]; then
    PYTHON_ARGS+=(--top-self "$TOP_SELF")
fi

if [[ "$TOP_CALLS" != "30" ]]; then
    PYTHON_ARGS+=(--top-calls "$TOP_CALLS")
fi

if [[ "$DEFAULT_PATHS" == "true" ]]; then
    PYTHON_ARGS+=(--default-paths)
fi

# Call the Python script
exec python3 "$ANALYZE_PROFILE_SCRIPT" "${PYTHON_ARGS[@]}"
