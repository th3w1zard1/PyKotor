#!/bin/bash
# Comprehensive profile analysis tool for identifying performance bottlenecks.
#
# Wrapper script that calls the Python analyze_profile.py script to analyze
# cProfile output files (.prof) and provides detailed breakdowns of function
# execution times, call counts, and call chains.

set -euo pipefail

# Default values
PROFILE_FILE=""
OUTPUT=""
TOP_CUMULATIVE=50
TOP_SELF=50
TOP_CALLS=30
TOP_CALLERS=30
TOP_CALLEES=30
NO_CALLERS=false
NO_CALLEES=false
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
        --top-callers)
            TOP_CALLERS="$2"
            shift 2
            ;;
        --top-callees)
            TOP_CALLEES="$2"
            shift 2
            ;;
        --no-callers)
            NO_CALLERS=true
            shift
            ;;
        --no-callees)
            NO_CALLEES=true
            shift
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
            echo "  --top-callers N            Number of top callers to show (default: 30)"
            echo "  --top-callees N            Number of top callees to show (default: 30)"
            echo "  --no-callers               Skip callers analysis"
            echo "  --no-callees               Skip callees analysis"
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

if [[ "$TOP_CALLERS" != "30" ]]; then
    PYTHON_ARGS+=(--top-callers "$TOP_CALLERS")
fi

if [[ "$TOP_CALLEES" != "30" ]]; then
    PYTHON_ARGS+=(--top-callees "$TOP_CALLEES")
fi

if [[ "$NO_CALLERS" == "true" ]]; then
    PYTHON_ARGS+=(--no-callers)
fi

if [[ "$NO_CALLEES" == "true" ]]; then
    PYTHON_ARGS+=(--no-callees)
fi

if [[ "$DEFAULT_PATHS" == "true" ]]; then
    PYTHON_ARGS+=(--default-paths)
fi

# Call the Python script
exec python3 "$ANALYZE_PROFILE_SCRIPT" "${PYTHON_ARGS[@]}"
