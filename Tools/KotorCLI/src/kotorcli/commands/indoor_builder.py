"""Indoor map building and extraction command implementations for KotorCLI.

KotorCLI must not depend on the Holocron Toolset (`toolset.*`). This command layer delegates to
`pykotor.tools.indoormap` / `pykotor.tools.indoorkit` which are library-safe.
"""

from __future__ import annotations

import logging
import sys
from argparse import Namespace
from pathlib import Path
from typing import TYPE_CHECKING

from pykotor.tools.indoormap import build_mod_from_indoor_file, extract_indoor_from_module_files
from utility.error_handling import universal_simplify_exception

from kotorcli.indoor_builder import determine_game_from_installation, parse_game_argument

if TYPE_CHECKING:
    from loggerplus import RobustLogger

LEVEL_MAP = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


def cmd_indoor_build(args: Namespace, logger: RobustLogger) -> int:
    """Build a .mod file from a .indoor file.

    This command loads a .indoor JSON file and builds it into a complete .mod file
    using the specified kits and installation resources.

    Args:
    ----
        args: Parsed command-line arguments
        logger: Logger instance

    Returns:
    -------
        Exit code (0 for success, non-zero for failure)
    """
    if args.log_level:
        logger.setLevel(LEVEL_MAP.get(args.log_level, logging.INFO))

    # Validate inputs
    if not args.input:
        logger.error("No input .indoor file specified. Use --input <path>")
        return 1
    if not args.output:
        logger.error("No output .mod file specified. Use --output <path>")
        return 1
    if not args.installation:
        logger.error("No installation path specified. Use --installation <path>")
        return 1
    if not args.kits:
        logger.error("No kits directory specified. Use --kits <path>")
        return 1

    input_path = Path(args.input)
    output_path = Path(args.output)
    installation_path = Path(args.installation)
    kits_path = Path(args.kits)

    # Validate paths exist
    if not input_path.exists():
        logger.error("Input file does not exist: %s", input_path)
        return 1
    if not installation_path.exists():
        logger.error("Installation path does not exist: %s", installation_path)
        return 1
    if not kits_path.exists():
        logger.error("Kits directory does not exist: %s", kits_path)
        return 1

    try:
        # Determine game type
        game = parse_game_argument(args.game)
        if game is None:
            game = determine_game_from_installation(installation_path)
            if game is None:
                logger.error("Could not determine game type. Please specify --game k1 or --game k2")
                return 1

        logger.info("Building module from indoor map: %s", input_path.name)
        logger.info("Installation: %s", installation_path)
        logger.info("Kits: %s", kits_path)
        logger.info("Output: %s", output_path)
        logger.info("Game: %s", game.name)

        build_mod_from_indoor_file(
            input_path,
            output_mod_path=output_path,
            installation_path=installation_path,
            kits_path=kits_path,
            game=game,
            module_id=args.module_filename.lower().strip() if args.module_filename else None,
            loadscreen_path=args.loading_screen,
        )

        logger.info("Module build completed successfully.")
        return 0
    except Exception as exc:
        error_name, msg = universal_simplify_exception(exc)
        logger.exception("Indoor map build failed: %s: %s", error_name, msg)
        print(f"[Error] {error_name}: {msg}", file=sys.stderr)  # noqa: T201
        return 1


def cmd_indoor_extract(args: Namespace, logger: RobustLogger) -> int:
    """Extract a .indoor file from a composite module.

    This command extracts module data from composite files (_s.rim/.rim/_dlg.erf)
    and converts it to a .indoor JSON file. This is a complex reverse-engineering
    process that attempts to match module rooms back to their source kits.

    Args:
    ----
        args: Parsed command-line arguments
        logger: Logger instance

    Returns:
    -------
        Exit code (0 for success, non-zero for failure)
    """
    if args.log_level:
        logger.setLevel(LEVEL_MAP.get(args.log_level, logging.INFO))

    # Validate inputs
    if not args.module:
        logger.error("No module name specified. Use --module <name>")
        return 1
    if not args.output:
        logger.error("No output .indoor file specified. Use --output <path>")
        return 1
    if not args.installation:
        logger.error("No installation path specified. Use --installation <path>")
        return 1
    if not args.kits:
        logger.error("No kits directory specified. Use --kits <path>")
        return 1

    module_name = args.module.lower().strip()
    output_path = Path(args.output)
    installation_path = Path(args.installation)
    kits_path = Path(args.kits)

    # Validate paths exist
    if not installation_path.exists():
        logger.error("Installation path does not exist: %s", installation_path)
        return 1
    if not kits_path.exists():
        logger.error("Kits directory does not exist: %s", kits_path)
        return 1

    try:
        # Determine game type
        game = parse_game_argument(args.game)
        if game is None:
            game = determine_game_from_installation(installation_path)
            if game is None:
                logger.error("Could not determine game type. Please specify --game k1 or --game k2")
                return 1

        logger.info("Extracting indoor map from module: %s", module_name)
        logger.info("Installation: %s", installation_path)
        logger.info("Kits: %s", kits_path)
        logger.info("Output: %s", output_path)
        logger.info("Game: %s", game.name)

        # Locate composite module containers under the installation Modules directory.
        modules_dir = installation_path / "modules"
        if not modules_dir.is_dir():
            modules_dir = installation_path / "Modules"

        candidate_files: list[Path] = []
        for ext in (".mod", ".rim", "_s.rim", "_dlg.erf"):
            p = modules_dir / f"{module_name}{ext}"
            if p.is_file():
                candidate_files.append(p)

        if not candidate_files:
            logger.error("No module containers found for '%s' under '%s'", module_name, modules_dir)
            return 1

        output_path.parent.mkdir(parents=True, exist_ok=True)
        found = extract_indoor_from_module_files(candidate_files, output_indoor_path=output_path)
        if not found:
            logger.error(
                "No embedded indoor data found in module containers. "
                "This works for modules built by the indoor builder (it embeds '%s.%s').",
                "indoormap",
                "txt",
            )
            return 1

        logger.info("Extracted embedded indoor data to: %s", output_path)
        return 0
    except Exception as exc:
        error_name, msg = universal_simplify_exception(exc)
        logger.exception("Indoor map extraction failed: %s: %s", error_name, msg)
        print(f"[Error] {error_name}: {msg}", file=sys.stderr)  # noqa: T201
        return 1
