#!/usr/bin/env python3
"""Check PyPI package dependencies and metadata.

This script queries PyPI API to inspect package dependencies, versions, and metadata.
Useful for verifying package configurations, dependency resolution, and debugging.

Examples:
    # Check latest version of a package
    python check_pypi_deps.py holocrontoolset

    # Check specific version
    python check_pypi_deps.py holocrontoolset --version 4.0.0b3

    # Search for specific dependency
    python check_pypi_deps.py holocrontoolset --search pykotorgl

    # JSON output for scripting
    python check_pypi_deps.py holocrontoolset --format json

    # Compare two versions
    python check_pypi_deps.py holocrontoolset --version 4.0.0b2 --compare-version 4.0.0b3
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import requests


def get_package_info(package_name: str, version: str | None = None) -> dict[str, Any]:
    """Fetch package information from PyPI API.

    Args:
        package_name: Name of the package on PyPI
        version: Specific version to fetch (None for latest)

    Returns:
        Dictionary containing package metadata

    Raises:
        SystemExit: If package or version not found
    """
    if version:
        url = f"https://pypi.org/pypi/{package_name}/{version}/json"
    else:
        url = f"https://pypi.org/pypi/{package_name}/json"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            if version:
                print(f"Error: Package '{package_name}' version '{version}' not found on PyPI", file=sys.stderr)
            else:
                print(f"Error: Package '{package_name}' not found on PyPI", file=sys.stderr)
        else:
            print(f"Error: HTTP {e.response.status_code} - {e}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to fetch package info - {e}", file=sys.stderr)
        sys.exit(1)


def get_latest_version(package_name: str) -> str:
    """Get the latest version of a package from PyPI.

    Args:
        package_name: Name of the package

    Returns:
        Latest version string
    """
    data = get_package_info(package_name)
    versions = list(data.get("releases", {}).keys())
    if not versions:
        print(f"Error: No versions found for package '{package_name}'", file=sys.stderr)
        sys.exit(1)

    # Sort by version using packaging library if available, otherwise simple sort
    try:
        from packaging import version as pkg_version

        return max(versions, key=lambda v: pkg_version.parse(v))
    except ImportError:
        # Fallback to simple string sort
        return sorted(versions)[-1]


def format_dependencies(
    deps: list[str] | None,
    search: str | None = None,
    show_extras: bool = True,
) -> list[str]:
    """Format and filter dependencies.

    Args:
        deps: List of dependency strings
        search: Optional search term to filter dependencies
        show_extras: Whether to show extra-specific dependencies

    Returns:
        Filtered and formatted list of dependencies
    """
    if not deps:
        return []

    filtered = deps

    # Filter by search term if provided
    if search:
        search_lower = search.lower()
        filtered = [d for d in filtered if search_lower in d.lower()]

    # Filter extras if requested
    if not show_extras:
        filtered = [d for d in filtered if "; extra == " not in d]

    return sorted(filtered)


def print_dependencies(
    deps: list[str],
    package_name: str,
    version: str,
    search: str | None = None,
    format_type: str = "text",
) -> None:
    """Print dependencies in the specified format.

    Args:
        deps: List of dependency strings
        package_name: Name of the package
        version: Version of the package
        search: Optional search term that was used
        format_type: Output format ('text', 'json', 'compact')
    """
    if format_type == "json":
        output = {
            "package": package_name,
            "version": version,
            "dependencies": deps,
            "count": len(deps),
        }
        if search:
            output["search_term"] = search
        print(json.dumps(output, indent=2))
    elif format_type == "compact":
        for dep in deps:
            print(dep)
    else:  # text format
        print(f"Dependencies for {package_name}=={version}:")
        print("=" * 70)
        if search:
            print(f"Filtered by search term: '{search}'")
            print()
        if deps:
            for dep in deps:
                print(f"  {dep}")
            print(f"\nTotal: {len(deps)}")
        else:
            print("  No dependencies found")


def compare_versions(
    package_name: str,
    version1: str,
    version2: str,
    format_type: str = "text",
) -> None:
    """Compare dependencies between two versions.

    Args:
        package_name: Name of the package
        version1: First version to compare
        version2: Second version to compare
        format_type: Output format ('text', 'json')
    """
    data1 = get_package_info(package_name, version1)
    data2 = get_package_info(package_name, version2)

    deps1 = set(data1["info"].get("requires_dist", []) or [])
    deps2 = set(data2["info"].get("requires_dist", []) or [])

    added = sorted(deps2 - deps1)
    removed = sorted(deps1 - deps2)
    common = sorted(deps1 & deps2)

    if format_type == "json":
        output = {
            "package": package_name,
            "version1": version1,
            "version2": version2,
            "added": added,
            "removed": removed,
            "common": common,
            "stats": {
                "version1_count": len(deps1),
                "version2_count": len(deps2),
                "added_count": len(added),
                "removed_count": len(removed),
                "common_count": len(common),
            },
        }
        print(json.dumps(output, indent=2))
    else:  # text format
        print(f"Comparing {package_name} dependencies:")
        print(f"  Version 1: {version1} ({len(deps1)} dependencies)")
        print(f"  Version 2: {version2} ({len(deps2)} dependencies)")
        print()
        print("Added dependencies:")
        if added:
            for dep in added:
                print(f"  + {dep}")
        else:
            print("  (none)")
        print()
        print("Removed dependencies:")
        if removed:
            for dep in removed:
                print(f"  - {dep}")
        else:
            print("  (none)")
        print()
        print(f"Common dependencies: {len(common)}")


def list_versions(package_name: str, limit: int = 10, format_type: str = "text") -> None:
    """List available versions of a package.

    Args:
        package_name: Name of the package
        limit: Maximum number of versions to show
        format_type: Output format ('text', 'json', 'compact')
    """
    data = get_package_info(package_name)
    versions = list(data.get("releases", {}).keys())

    if not versions:
        print(f"No versions found for package '{package_name}'", file=sys.stderr)
        sys.exit(1)

    # Sort versions
    try:
        from packaging import version as pkg_version

        sorted_versions = sorted(versions, key=lambda v: pkg_version.parse(v), reverse=True)
    except ImportError:
        sorted_versions = sorted(versions, reverse=True)

    limited = sorted_versions[:limit]

    if format_type == "json":
        output = {
            "package": package_name,
            "versions": limited,
            "total_versions": len(versions),
            "showing": len(limited),
        }
        print(json.dumps(output, indent=2))
    elif format_type == "compact":
        for v in limited:
            print(v)
    else:  # text format
        print(f"Available versions for {package_name}:")
        print("=" * 70)
        for v in limited:
            print(f"  {v}")
        if len(versions) > limit:
            print(f"\n... and {len(versions) - limit} more (total: {len(versions)})")
        else:
            print(f"\nTotal: {len(versions)}")


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Check PyPI package dependencies and metadata",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "package",
        help="Package name to check (e.g., 'holocrontoolset')",
    )

    parser.add_argument(
        "-v",
        "--version",
        default=None,
        help="Specific version to check (default: latest)",
    )

    parser.add_argument(
        "-s",
        "--search",
        default=None,
        help="Search for specific dependency (case-insensitive)",
    )

    parser.add_argument(
        "-f",
        "--format",
        choices=["text", "json", "compact"],
        default="text",
        help="Output format (default: text)",
    )

    parser.add_argument(
        "--no-extras",
        action="store_true",
        help="Hide extra-specific dependencies (e.g., 'dev', 'updater')",
    )

    parser.add_argument(
        "--compare-version",
        metavar="VERSION",
        help="Compare dependencies with another version",
    )

    parser.add_argument(
        "--list-versions",
        action="store_true",
        help="List available versions instead of showing dependencies",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Limit number of versions shown (default: 10)",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)",
    )

    args = parser.parse_args()

    # Override timeout if specified
    if args.timeout != 10:
        requests.get = lambda url, **kwargs: requests.get(url, timeout=args.timeout, **kwargs)

    try:
        if args.list_versions:
            list_versions(args.package, limit=args.limit, format_type=args.format)
            return

        # Determine version to check
        if args.version:
            version = args.version
        else:
            version = get_latest_version(args.package)

        # Handle version comparison
        if args.compare_version:
            compare_versions(args.package, version, args.compare_version, format_type=args.format)
            return

        # Get package info
        data = get_package_info(args.package, version)

        # Extract dependencies
        deps = data["info"].get("requires_dist", [])

        # Format and filter dependencies
        formatted_deps = format_dependencies(
            deps,
            search=args.search,
            show_extras=not args.no_extras,
        )

        # Print results
        print_dependencies(
            formatted_deps,
            args.package,
            version,
            search=args.search,
            format_type=args.format,
        )

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

