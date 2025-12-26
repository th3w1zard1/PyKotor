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

from pykotor.common.indoormap import IndoorMap
from pykotor.common.modulekit import ModuleKitManager
from pykotor.extract.installation import Installation
from pykotor.tools.indoorkit import load_kits
from pykotor.tools.indoormap import (
    build_mod_from_indoor_file_modulekit,
    extract_indoor_from_module_as_modulekit,
    extract_indoor_from_module_files,
    extract_indoor_from_module_name,
)
from pykotor.tools.path import CaseAwarePath
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


def _resolve_context(args: Namespace, logger: RobustLogger):
    """Shared setup for indoor-build and indoor-extract.

    Validates installation/kits paths, resolves the game, and returns (game, installation, kits).
    """
    installation_path = Path(args.installation) if args.installation else None
    kits_path = Path(args.kits) if args.kits else None

    if installation_path is None:
        msg = "No installation path specified. Use --installation <path>"
        raise ValueError(msg)
    if not installation_path.exists():
        msg = f"Installation path does not exist: {installation_path}"
        raise ValueError(msg)

    game = parse_game_argument(args.game)
    if game is None:
        game = determine_game_from_installation(installation_path)
    if game is None:
        msg = "Could not determine game type. Please specify --game k1 or --game k2"
        raise ValueError(msg)

    installation = Installation(CaseAwarePath(installation_path))
    if args.implicit_kit:
        logger.debug("Implicit-kit mode enabled (ModuleKit). External kits will not be loaded.")
        return game, installation_path, kits_path, installation, []

    if kits_path is None:
        msg = "No kits directory specified. Use --kits <path> (or pass --implicit-kit)"
        raise ValueError(msg)
    if not kits_path.exists():
        msg = f"Kits directory does not exist: {kits_path}"
        raise ValueError(msg)

    kits = load_kits(kits_path)
    logger.debug("Loaded %d kit(s) from '%s'", len(kits), kits_path)
    return game, installation_path, kits_path, installation, kits


def cmd_indoor_build(args: Namespace, logger: RobustLogger) -> int:  # noqa: PLR0911, PLR0912, PLR0915
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
    if not args.implicit_kit and not args.kits:
        logger.error("No kits directory specified. Use --kits <path> (or pass --implicit-kit)")
        return 1

    input_path = Path(args.input)
    output_path = Path(args.output)
    installation_path = Path(args.installation)
    kits_path = Path(args.kits) if args.kits else None

    # Validate paths exist
    if not input_path.exists():
        logger.error("Input file does not exist: %s", input_path)
        return 1
    if not installation_path.exists():
        logger.error("Installation path does not exist: %s", installation_path)
        return 1
    if not args.implicit_kit:
        assert kits_path is not None
        if not kits_path.exists():
            logger.error("Kits directory does not exist: %s", kits_path)
            return 1

    try:
        game, _install_path, _kits_path, installation, kits = _resolve_context(args, logger)

        logger.info("Building module from indoor map: %s", input_path.name)
        logger.info("Installation: %s", installation_path)
        if args.implicit_kit:
            logger.info("Kits: (implicit ModuleKit)")
        else:
            logger.info("Kits: %s", kits_path)
        logger.info("Output: %s", output_path)
        logger.info("Game: %s", game.name)

        if args.implicit_kit:
            build_mod_from_indoor_file_modulekit(
                input_path,
                output_mod_path=output_path,
                installation_path=installation_path,
                game=game,
                module_id=args.module_filename,
                loadscreen_path=args.loading_screen,
            )
        else:
            indoor = IndoorMap()
            missing = indoor.load(input_path.read_bytes(), kits)
            if missing:
                logger.warning("Some rooms could not be loaded: %d missing", len(missing))
                for m in missing[:25]:
                    logger.warning("  - Kit '%s', Component '%s': %s", m.kit_name, m.component_name, m.reason)
                if len(missing) > 25:
                    logger.warning("  - ... and %d more", len(missing) - 25)

            if args.module_filename:
                indoor.module_id = args.module_filename.lower().strip()
                logger.info("Module ID set to: %s", indoor.module_id)

            indoor.build(installation, kits, output_path, game_override=game, loadscreen_path=args.loading_screen)

    except Exception as exc:
        error_name, msg = universal_simplify_exception(exc)
        logger.exception("Indoor map build failed: %s: %s", error_name, msg)
        print(f"[Error] {error_name}: {msg}", file=sys.stderr)  # noqa: T201
        return 1
    else:
        logger.info("Indoor map build completed successfully.")
        return 0


def cmd_indoor_extract(args: Namespace, logger: RobustLogger) -> int:  # noqa: PLR0911, PLR0912, PLR0915
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
    # kits are optional in implicit-kit mode and for embedded indoormap extraction.

    module_name = args.module.lower().strip()
    output_path = Path(args.output)
    installation_path = Path(args.installation)
    kits_path = Path(args.kits) if args.kits else None

    try:
        game, _install_path, _kits_path, _installation, _kits = _resolve_context(args, logger)

        logger.info("Extracting indoor map from module: %s", module_name)
        logger.info("Installation: %s", installation_path)
        if args.implicit_kit:
            logger.info("Kits: (implicit ModuleKit)")
        else:
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

        # Fast path: extract embedded indoor JSON if present.
        embedded_found = extract_indoor_from_module_files(
            [str(p) for p in candidate_files], output_indoor_path=output_path
        )
        if embedded_found:
            if args.implicit_kit:
                try:
                    test_map = IndoorMap()
                    mk = ModuleKitManager(_installation)
                    missing = test_map.load(output_path.read_bytes(), [], module_kit_manager=mk)
                    if missing:
                        msg = "embedded indoor requires external kits"
                        raise ValueError(msg)  # noqa: TRY301
                except Exception:
                    logger.info("Embedded indoor not ModuleKit-compatible; falling back to ModuleKit extraction.")
                else:
                    logger.info("Extracted embedded indoor data (ModuleKit-compatible) to: %s", output_path)
                    return 0
            else:
                logger.info("Extracted embedded indoor data to: %s", output_path)
                return 0

        if args.implicit_kit:
            indoor = extract_indoor_from_module_as_modulekit(
                module_name,
                installation_path=installation_path,
                game=game,
                logger=logger,
            )
            output_path.write_bytes(indoor.write())
            logger.info("Extracted indoor map via ModuleKit to: %s", output_path)
            logger.info("Indoor map extraction completed successfully.")
            return 0

        if kits_path is None:
            logger.error("No kits directory specified. Use --kits <path> (or pass --implicit-kit)")
            return 1

        # Full reverse-extraction path: rebuild `.indoor` by matching room WOKs back to kits.
        logger.info("No embedded indoor data found; attempting full reverse-extraction from module resources...")
        indoor = extract_indoor_from_module_name(
            module_name,
            installation_path=installation_path,
            kits_path=kits_path,
            game=game,
            strict=True,
            logger=logger,
        )
        output_path.write_bytes(indoor.write())
    except Exception as exc:
        error_name, msg = universal_simplify_exception(exc)
        logger.exception("Indoor map extraction failed: %s: %s", error_name, msg)
        print(f"[Error] {error_name}: {msg}", file=sys.stderr)  # noqa: T201
        return 1
    else:
        logger.info("Extracted indoor map via reverse-extraction to: %s", output_path)
        logger.info("Indoor map extraction completed successfully.")
        return 0
