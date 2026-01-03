"""Site-wide customization for PyKotor project.

This module is automatically imported by Python during initialization.
It normalizes PYTHONPATH to use the platform-specific separator for
cross-platform compatibility.

Python automatically imports this file if it's in:
- The current directory (when Python starts)
- A directory in PYTHONPATH
- The site-packages directory

This ensures PYTHONPATH works correctly on Windows (semicolons) and
Unix/Linux/macOS (colons) regardless of the format in .env file.
"""

from __future__ import annotations

import os
from pathlib import Path


def _find_repo_root() -> Path:
    """Locate the repository root by walking up from CWD and this file."""
    candidates = [Path.cwd(), Path(__file__).resolve().parent]
    for base in candidates:
        for path in [base, *base.parents]:
            if (path / "pyproject.toml").exists():
                return path
    return Path(__file__).resolve().parent


def _normalize_pythonpath() -> None:
    """Normalize PYTHONPATH to use platform-specific separator."""
    pythonpath = os.environ.get("PYTHONPATH")
    if not pythonpath:
        return

    # VSCode can inject a value prefixed with "PYTHONPATH=", keep the content.
    if pythonpath.startswith("PYTHONPATH="):
        pythonpath = pythonpath.split("PYTHONPATH=", 1)[1]

    # Determine the correct separator for this platform
    # Windows uses ';', Unix/Linux/macOS use ':'
    correct_sep = os.pathsep

    # Check if normalization is needed
    # If PYTHONPATH contains the wrong separator, convert it
    has_semicolon = ";" in pythonpath
    has_colon = ":" in pythonpath

    if has_semicolon and has_colon:
        # Mixed separators - split by both and rejoin with correct separator
        paths = []
        for sep in [";", ":"]:
            for path in pythonpath.split(sep):
                path = path.strip().strip('"').strip("'")
                if path and path not in paths:
                    paths.append(path)
        pythonpath = correct_sep.join(paths)
    elif has_semicolon and correct_sep == ":":
        # Windows format (semicolons) on Unix - convert to colons
        paths = [p.strip().strip('"').strip("'") for p in pythonpath.split(";") if p.strip()]
        pythonpath = correct_sep.join(paths)
    elif has_colon and correct_sep == ";":
        # Unix format (colons) on Windows - convert to semicolons
        paths = [p.strip().strip('"').strip("'") for p in pythonpath.split(":") if p.strip()]
        pythonpath = correct_sep.join(paths)
    else:
        # Already using correct separator, no normalization needed
        return

    # Update environment variable
    os.environ["PYTHONPATH"] = pythonpath


def _sync_sys_path_with_pythonpath() -> None:
    """Ensure sys.path reflects the normalized PYTHONPATH entries."""
    import sys

    pythonpath = os.environ.get("PYTHONPATH")
    if not pythonpath:
        return

    parts = []
    for raw in pythonpath.split(os.pathsep):
        raw = raw.strip()
        if not raw:
            continue
        resolved = Path(raw).expanduser().resolve()
        if resolved.name.lower() == "tests":
            continue  # avoid adding test package roots directly to sys.path
        parts.append(resolved)

    # Remove any bogus entries like "PYTHONPATH=..."
    cleaned_sys_path: list[str] = []
    for entry in sys.path:
        if not isinstance(entry, str):
            cleaned_sys_path.append(entry)
            continue
        if "PYTHONPATH=" in entry:
            continue
        try:
            if Path(entry).name.lower() == "tests":
                continue
        except Exception:
            pass
        cleaned_sys_path.append(entry)
    sys.path[:] = cleaned_sys_path

    for part in parts:
        part_str = str(part)
        if part_str not in sys.path:
            sys.path.insert(0, part_str)

    repo_root = _find_repo_root()
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)

    # Drop any pre-existing top-level `tests` module to avoid path clashes.
    sys.modules.pop("tests", None)


# Auto-normalize when this module is imported
_normalize_pythonpath()
_sync_sys_path_with_pythonpath()


def _ensure_test_run_pipe() -> None:
    """Provide a default TEST_RUN_PIPE for VSCode pytest plugin parity."""
    import os

    if not os.environ.get("TEST_RUN_PIPE"):
        fallback = _find_repo_root() / "pytest_dummy.pipe"
        os.environ["TEST_RUN_PIPE"] = str(fallback)


_ensure_test_run_pipe()


def _ensure_tests_namespace() -> None:
    """Create a shared namespace package for distributed test suites.

    The repository no longer keeps a single top-level ``tests`` directory, but
    many test suites still import modules like ``tests.test_camera_controller``.
    We synthesize a namespace package that spans the subproject test roots so
    those imports continue to work.
    """
    import sys
    import types

    repo_root = _find_repo_root()
    test_roots = [
        repo_root / "Libraries" / "PyKotor" / "tests",
        repo_root / "Libraries" / "PyKotorGL" / "tests",
        repo_root / "Libraries" / "PyKotorFont" / "tests",
        repo_root / "Tools" / "HolocronToolset" / "tests",
    ]

    mod = sys.modules.get("tests")
    if mod is None:
        mod = types.ModuleType("tests")
        sys.modules["tests"] = mod

    # Always reset the namespace path to our known roots.
    mod.__path__ = []  # type: ignore[attr-defined]

    for root in test_roots:
        if root.is_dir():
            root_str = str(root)
            if root_str not in mod.__path__:  # type: ignore[attr-defined]
                mod.__path__.append(root_str)  # type: ignore[attr-defined]


if os.environ.get("PYKOTOR_ENABLE_TESTS_NAMESPACE") == "1":
    _ensure_tests_namespace()
