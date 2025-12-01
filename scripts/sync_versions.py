#!/usr/bin/env python3
"""Synchronize versions across all PyKotor packages.

This script ensures version consistency across the PyKotor ecosystem.
It can:
- Display current versions of all packages
- Synchronize core library versions
- Update dependent package version requirements
- Validate version consistency

Usage:
    python sync_versions.py --show          # Show all versions
    python sync_versions.py --sync 1.8.1    # Sync core libs to 1.8.1
    python sync_versions.py --validate      # Validate consistency
    python sync_versions.py --bump patch    # Bump version (major/minor/patch)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Generator


# Try to import tomllib (Python 3.11+) or tomli
try:
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib
except ImportError:
    print("Error: tomli is required for Python < 3.11")
    print("Install with: pip install tomli")
    sys.exit(1)

try:
    import tomli_w
except ImportError:
    tomli_w = None  # type: ignore[assignment]


PROJECT_ROOT = Path(__file__).parent.parent

# Core packages that should share the same version
CORE_PACKAGES = {
    "pykotor": PROJECT_ROOT / "Libraries" / "PyKotor" / "pyproject.toml",
    "pykotorgl": PROJECT_ROOT / "Libraries" / "PyKotorGL" / "pyproject.toml",
    "pykotorfont": PROJECT_ROOT / "Libraries" / "PyKotorFont" / "pyproject.toml",
}

# Workspace meta-package
WORKSPACE_PYPROJECT = PROJECT_ROOT / "pyproject.toml"


def get_all_pyproject_paths() -> Generator[tuple[str, Path], None, None]:
    """Yield all pyproject.toml paths with their directory names."""
    # Libraries
    libraries = PROJECT_ROOT / "Libraries"
    if libraries.exists():
        for lib_dir in libraries.iterdir():
            if lib_dir.is_dir():
                pyproject = lib_dir / "pyproject.toml"
                if pyproject.exists():
                    yield lib_dir.name, pyproject
    
    # Tools
    tools = PROJECT_ROOT / "Tools"
    if tools.exists():
        for tool_dir in tools.iterdir():
            if tool_dir.is_dir():
                pyproject = tool_dir / "pyproject.toml"
                if pyproject.exists():
                    yield tool_dir.name, pyproject
    
    # Workspace
    if WORKSPACE_PYPROJECT.exists():
        yield "pykotor-workspace", WORKSPACE_PYPROJECT


def load_pyproject(path: Path) -> dict[str, Any]:
    """Load and parse a pyproject.toml file."""
    with open(path, "rb") as f:
        return tomllib.load(f)


def get_version(data: dict[str, Any]) -> str | None:
    """Extract version from pyproject data."""
    return data.get("project", {}).get("version")


def get_poetry_version(data: dict[str, Any]) -> str | None:
    """Extract poetry version from pyproject data."""
    return data.get("tool", {}).get("poetry", {}).get("version")


def show_versions() -> None:
    """Display versions of all packages."""
    print("=" * 60)
    print("PyKotor Package Versions")
    print("=" * 60)
    
    print("\n📚 Core Libraries:")
    print("-" * 40)
    for name, path in sorted(CORE_PACKAGES.items()):
        if path.exists():
            data = load_pyproject(path)
            version = get_version(data) or "unknown"
            poetry_ver = get_poetry_version(data)
            status = "✓" if version == poetry_ver or not poetry_ver else "⚠"
            print(f"  {status} {name}: {version}")
            if poetry_ver and poetry_ver != version:
                print(f"      poetry: {poetry_ver}")
        else:
            print(f"  ✗ {name}: not found")
    
    print("\n🔧 Tools:")
    print("-" * 40)
    tools = PROJECT_ROOT / "Tools"
    if tools.exists():
        for tool_dir in sorted(tools.iterdir()):
            if tool_dir.is_dir():
                pyproject = tool_dir / "pyproject.toml"
                if pyproject.exists():
                    data = load_pyproject(pyproject)
                    name = data.get("project", {}).get("name", tool_dir.name)
                    version = get_version(data) or "unknown"
                    print(f"  • {name}: {version}")
    
    print("\n📦 Workspace:")
    print("-" * 40)
    if WORKSPACE_PYPROJECT.exists():
        data = load_pyproject(WORKSPACE_PYPROJECT)
        version = get_version(data) or "unknown"
        print(f"  • pykotor-workspace: {version}")
    
    print()


def validate_versions() -> bool:
    """Validate version consistency across packages."""
    print("Validating version consistency...\n")
    errors: list[str] = []
    warnings: list[str] = []
    
    # Check core library versions match
    core_versions: dict[str, str] = {}
    for name, path in CORE_PACKAGES.items():
        if path.exists():
            data = load_pyproject(path)
            version = get_version(data)
            if version:
                core_versions[name] = version
    
    unique_versions = set(core_versions.values())
    if len(unique_versions) > 1:
        errors.append(
            f"Core libraries have inconsistent versions: "
            f"{', '.join(f'{k}={v}' for k, v in core_versions.items())}"
        )
    
    # Check poetry versions match project versions
    for name, path in get_all_pyproject_paths():
        if path.exists():
            data = load_pyproject(path)
            project_ver = get_version(data)
            poetry_ver = get_poetry_version(data)
            
            if project_ver and poetry_ver and project_ver != poetry_ver:
                warnings.append(
                    f"{name}: [project].version ({project_ver}) != "
                    f"[tool.poetry].version ({poetry_ver})"
                )
    
    # Check workspace version matches pykotor
    if WORKSPACE_PYPROJECT.exists():
        ws_data = load_pyproject(WORKSPACE_PYPROJECT)
        ws_version = get_version(ws_data)
        
        pykotor_path = CORE_PACKAGES.get("pykotor")
        if pykotor_path and pykotor_path.exists():
            pykotor_data = load_pyproject(pykotor_path)
            pykotor_version = get_version(pykotor_data)
            
            if ws_version and pykotor_version and ws_version != pykotor_version:
                warnings.append(
                    f"Workspace version ({ws_version}) != pykotor version ({pykotor_version})"
                )
    
    # Report results
    if errors:
        print("❌ Errors:")
        for error in errors:
            print(f"   • {error}")
        print()
    
    if warnings:
        print("⚠️  Warnings:")
        for warning in warnings:
            print(f"   • {warning}")
        print()
    
    if not errors and not warnings:
        print("✅ All versions are consistent!")
    
    return len(errors) == 0


def update_version_in_file(path: Path, new_version: str) -> bool:
    """Update version in a pyproject.toml file using regex."""
    content = path.read_text(encoding="utf-8")
    
    # Update [project] version
    content = re.sub(
        r'(\[project\][^\[]*version\s*=\s*")[^"]*(")',
        rf'\g<1>{new_version}\g<2>',
        content,
        flags=re.DOTALL
    )
    
    # Update [tool.poetry] version
    content = re.sub(
        r'(\[tool\.poetry\][^\[]*version\s*=\s*")[^"]*(")',
        rf'\g<1>{new_version}\g<2>',
        content,
        flags=re.DOTALL
    )
    
    path.write_text(content, encoding="utf-8")
    return True


def sync_versions(new_version: str, include_tools: bool = False) -> None:
    """Synchronize versions across packages."""
    print(f"Synchronizing versions to {new_version}...\n")
    
    # Update core libraries
    print("Updating core libraries:")
    for name, path in CORE_PACKAGES.items():
        if path.exists():
            update_version_in_file(path, new_version)
            print(f"  ✓ {name} -> {new_version}")
    
    # Update workspace
    if WORKSPACE_PYPROJECT.exists():
        update_version_in_file(WORKSPACE_PYPROJECT, new_version)
        print(f"  ✓ pykotor-workspace -> {new_version}")
    
    if include_tools:
        print("\nUpdating tools:")
        tools = PROJECT_ROOT / "Tools"
        if tools.exists():
            for tool_dir in sorted(tools.iterdir()):
                if tool_dir.is_dir():
                    pyproject = tool_dir / "pyproject.toml"
                    if pyproject.exists():
                        # Update pykotor dependency version requirement
                        content = pyproject.read_text(encoding="utf-8")
                        content = re.sub(
                            r'(pykotor["\']?\s*[><=~!]*\s*)[0-9.]+',
                            rf'\g<1>{new_version}',
                            content
                        )
                        pyproject.write_text(content, encoding="utf-8")
                        print(f"  ✓ {tool_dir.name} dependencies updated")
    
    print("\n✅ Version sync complete!")


def bump_version(bump_type: str) -> str:
    """Bump version and return new version string."""
    # Get current version from pykotor
    pykotor_path = CORE_PACKAGES.get("pykotor")
    if not pykotor_path or not pykotor_path.exists():
        print("Error: Cannot find pykotor pyproject.toml")
        sys.exit(1)
    
    data = load_pyproject(pykotor_path)
    current = get_version(data)
    if not current:
        print("Error: Cannot determine current version")
        sys.exit(1)
    
    # Parse version
    match = re.match(r"(\d+)\.(\d+)\.(\d+)", current)
    if not match:
        print(f"Error: Cannot parse version '{current}'")
        sys.exit(1)
    
    major, minor, patch = map(int, match.groups())
    
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        print(f"Error: Unknown bump type '{bump_type}'")
        sys.exit(1)
    
    new_version = f"{major}.{minor}.{patch}"
    print(f"Bumping version: {current} -> {new_version}")
    return new_version


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Synchronize versions across PyKotor packages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show current versions of all packages"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate version consistency"
    )
    parser.add_argument(
        "--sync",
        metavar="VERSION",
        help="Synchronize core libraries to specified version"
    )
    parser.add_argument(
        "--bump",
        choices=["major", "minor", "patch"],
        help="Bump version (major/minor/patch)"
    )
    parser.add_argument(
        "--include-tools",
        action="store_true",
        help="Also update tool dependency versions when syncing"
    )
    
    args = parser.parse_args()
    
    if args.show:
        show_versions()
    elif args.validate:
        valid = validate_versions()
        sys.exit(0 if valid else 1)
    elif args.sync:
        sync_versions(args.sync, args.include_tools)
    elif args.bump:
        new_version = bump_version(args.bump)
        sync_versions(new_version, args.include_tools)
    else:
        # Default: show versions
        show_versions()


if __name__ == "__main__":
    main()

