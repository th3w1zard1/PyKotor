"""Init command implementation."""
from __future__ import annotations

import subprocess
from argparse import Namespace
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from logging import Logger


DEFAULT_CONFIG_TEMPLATE = """# KotorCLI Package Configuration
# This file uses TOML format and is compatible with cli syntax

[package]
name = "{package_name}"
description = "{description}"
version = "1.0.0"
author = "{author}"

# Default file pattern - inherited by targets if not specified
file = "$target.mod"

  [package.sources]
  include = "src/**/*.{{nss,json,ncs,utc,uti,utp,utd,ute,utm,uts,utt,utw,git,are,ifo,dlg,gui}}"
  exclude = "**/test_*.nss"

  [package.rules]
  "*.nss" = "src/scripts"
  "*.ncs" = "src/scripts"
  "*.utc" = "src/blueprints/creatures"
  "*.uti" = "src/blueprints/items"
  "*.utp" = "src/blueprints/placeables"
  "*.utd" = "src/blueprints/doors"
  "*.ute" = "src/blueprints/encounters"
  "*.utm" = "src/blueprints/merchants"
  "*.uts" = "src/blueprints/sounds"
  "*.utt" = "src/blueprints/triggers"
  "*.utw" = "src/blueprints/waypoints"
  "*.dlg" = "src/dialogs"
  "*.git" = "src/areas"
  "*.are" = "src/areas"
  "*.ifo" = "src"
  "*.gui" = "src/gui"
  "*" = "src"

[target]
name = "default"
file = "{target_file}"
description = "Default target"
"""


def prompt(message: str, default: str = "") -> str:
    """Prompt user for input with a default value."""
    if default:
        message = f"{message} [{default}]"
    message += ": "

    response = input(message).strip()
    return response if response else default


def _gather_package_info(args: Namespace, target_dir: Path, logger: Logger) -> tuple[str, str, str, str]:
    """Gather package information from user or use defaults."""
    if args.default:
        package_name = target_dir.name
        description = ""
        author = ""
        target_file = f"{package_name}.mod"
    else:
        logger.info("\nPackage Configuration")
        logger.info("---------------------")
        package_name = prompt("Package name", target_dir.name)
        description = prompt("Description", "")
        author = prompt("Author", "")

        logger.info("\nTarget Configuration")
        logger.info("--------------------")
        target_file = prompt("Target filename (e.g., mymod.mod, myhak.hak)", f"{package_name}.mod")

    return package_name, description, author, target_file


def _create_directory_structure(target_dir: Path, logger: Logger) -> None:
    """Create the standard directory structure for a kotorcli package."""
    src_dir = target_dir / "src"
    src_dir.mkdir(exist_ok=True)
    logger.info(f"Created {src_dir}")  # noqa: G004

    subdirs = [
        "src/scripts",
        "src/dialogs",
        "src/areas",
        "src/blueprints/creatures",
        "src/blueprints/items",
        "src/blueprints/placeables",
        "src/blueprints/doors",
        "src/blueprints/encounters",
        "src/blueprints/merchants",
        "src/blueprints/sounds",
        "src/blueprints/triggers",
        "src/blueprints/waypoints",
        "src/gui",
    ]

    for subdir in subdirs:
        (target_dir / subdir).mkdir(parents=True, exist_ok=True)

    kotorcli_dir = target_dir / ".kotorcli"
    kotorcli_dir.mkdir(exist_ok=True)


def _create_gitignore(target_dir: Path, logger: Logger) -> None:
    """Create .gitignore file if it doesn't exist."""
    gitignore_content = """# KotorCLI
.kotorcli/cache/
.kotorcli/user.cfg
*.log

# Build output
*.mod
*.erf
*.hak
*.rim
*.bif
*.key

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Compiled scripts
*.ncs
"""
    gitignore_path = target_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text(gitignore_content, encoding="utf-8")
        logger.info(f"Created {gitignore_path}")  # noqa: G004


def _initialize_git_repo(target_dir: Path, logger: Logger) -> None:
    """Initialize git repository if requested."""
    try:
        subprocess.run(
            ["git", "init"],
            cwd=target_dir,
            check=True,
            capture_output=True,
        )
        logger.info("Initialized git repository")

        gitattributes_content = """# Auto detect text files and perform LF normalization
* text=auto

# Scripts should use LF
*.nss text eol=lf
*.ncs binary
"""
        gitattributes_path = target_dir / ".gitattributes"
        gitattributes_path.write_text(gitattributes_content, encoding="utf-8")
        logger.info(f"Created {gitattributes_path}")  # noqa: G004

    except subprocess.CalledProcessError:
        logger.warning("Failed to initialize git repository (git not found or error occurred)")
    except FileNotFoundError:
        logger.warning("Git not found, skipping repository initialization")


def _unpack_initial_file(args: Namespace, init_file: str, logger: Logger) -> None:
    """Unpack initial file if specified."""
    logger.info(f"Unpacking initial file: {init_file}")  # noqa: G004
    from kotorcli.commands.unpack import cmd_unpack  # noqa: PLC0415

    unpack_args = Namespace(
        target=None,
        file=init_file,
        unpack_file=init_file,
        removeDeleted=False,
        debug=args.debug if hasattr(args, "debug") else False,
        quiet=args.quiet if hasattr(args, "quiet") else False,
        verbose=args.verbose if hasattr(args, "verbose") else False,
        no_color=args.no_color if hasattr(args, "no_color") else False,
    )
    cmd_unpack(unpack_args, logger)


def cmd_init(args: Namespace, logger: Logger) -> int:
    """Handle init command - create a new kotorcli package.

    Args:
    ----
        args: Parsed command line arguments
        logger: Logger instance

    Returns:
    -------
        Exit code (0 for success, non-zero for error)
    """
    target_dir = Path(args.dir if args.dir else ".").resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    config_path = target_dir / "kotorcli.cfg"
    if config_path.exists():
        logger.warning(f"Package already initialized at {target_dir}")  # noqa: G004
        overwrite = prompt("Overwrite existing configuration? (yes/no)", "no")
        if overwrite.lower() not in ("yes", "y"):
            logger.info("Initialization cancelled")
            return 0

    logger.info(f"Initializing kotorcli package in {target_dir}")  # noqa: G004

    package_name, description, author, target_file = _gather_package_info(args, target_dir, logger)

    config_content = DEFAULT_CONFIG_TEMPLATE.format(
        package_name=package_name,
        description=description,
        author=author,
        target_file=target_file,
    )
    config_path.write_text(config_content, encoding="utf-8")
    logger.info(f"Created {config_path}")  # noqa: G004

    _create_directory_structure(target_dir, logger)
    _create_gitignore(target_dir, logger)

    if args.vcs == "git":
        _initialize_git_repo(target_dir, logger)

    init_file = args.init_file or args.file
    if init_file:
        _unpack_initial_file(args, init_file, logger)

    logger.info(f"\nPackage initialized successfully in {target_dir}")  # noqa: G004
    logger.info("Next steps:")
    logger.info("  1. Edit kotorcli.cfg to configure your package")
    logger.info("  2. Place your source files in the src/ directory")
    logger.info("  3. Run 'kotorcli list' to see available targets")
    logger.info("  4. Run 'kotorcli pack' to build your module")

    return 0



