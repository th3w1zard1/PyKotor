"""Main entry point for PyKotor CLI."""

from __future__ import annotations

import sys

from collections.abc import Sequence
from pathlib import Path


def setup_paths() -> None:
    """Set up sys.path for local modules.

    This ensures the CLI can find pykotor and utility modules when run directly
    from the repository without requiring installation or manual PYTHONPATH setup.
    """
    file_path = Path(__file__).resolve()
    # Go up to repo root: Libraries/PyKotor/src/pykotor/cli/__main__.py
    # __main__.py -> cli -> pykotor -> src -> PyKotor -> Libraries -> repo root (6 levels)
    repo_root = file_path.parents[5]  # Fixed: was 4, should be 5

    paths_to_add: list[Path] = [
        repo_root / "Libraries" / "PyKotor" / "src",  # ./Libraries/PyKotor/src/ (contains both pykotor and utility namespaces)
    ]

    # Optionally add Utility if it exists as a separate library
    utility_path = repo_root / "Libraries" / "Utility" / "src"
    if utility_path.exists():
        paths_to_add.append(utility_path)

    for path in paths_to_add:
        path_str = str(path)
        if path.exists() and path_str not in sys.path:
            sys.path.insert(0, path_str)


# Set up paths BEFORE importing anything that might import pykotor modules
# This is critical for running the CLI directly from the repository
setup_paths()

from pykotor.cli.argparser import create_parser
from pykotor.cli.dispatch import cli_main


def main(argv: Sequence[str] | None = None) -> int:
    """Main entry point for PyKotor CLI.

    - No arguments -> show help.
    - Arguments -> run CLI command.
    """
    arg_list = list(sys.argv[1:] if argv is None else argv)
    if not arg_list:
        parser = create_parser()
        parser.print_help()
        return 0
    return cli_main(arg_list)


if __name__ == "__main__":
    sys.exit(main())
