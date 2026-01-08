"""Generate Holocron-compatible kits from installation modules."""
from __future__ import annotations

import logging
import sys
from argparse import Namespace
from pathlib import Path
from typing import TYPE_CHECKING

from pykotor.cli.kit_generator import generate_kit, normalize_module_name

if TYPE_CHECKING:
    from loggerplus import RobustLogger

LEVEL_MAP = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


def cmd_kit_generate(args: Namespace, logger: RobustLogger) -> int:
    """Run kit extraction in headless mode or launch GUI.

    Delegates to :func:`pykotor.cli.kit_generator.generate_kit` which wraps
    ``pykotor.tools.kit.extract_kit`` (see `Libraries/PyKotor/src/pykotor/tools/kit.py`).

    If required arguments are missing or --gui is specified, launches the GUI from Tools/KitGenerator.
    """
    # Check if we should launch GUI
    has_required_args = bool(args.installation and args.module and args.output)
    should_launch_gui = getattr(args, "gui", False) or not has_required_args

    if should_launch_gui:
        try:
            # Import from Tools/KitGenerator
            import sys
            from pathlib import Path

            # Add Tools/KitGenerator/src to path
            cli_file = Path(__file__).resolve()
            # Go up: commands -> cli -> pykotor -> src -> PyKotor -> Libraries -> repo root
            repo_root = cli_file.parents[6]
            kitgenerator_src = repo_root / "Tools" / "KitGenerator" / "src"
            pykotor_src = repo_root / "Libraries" / "PyKotor" / "src"
            
            # Add both paths for imports
            if str(kitgenerator_src) not in sys.path:
                sys.path.insert(0, str(kitgenerator_src))
            if str(pykotor_src) not in sys.path:
                sys.path.insert(0, str(pykotor_src))

            from kitgenerator.gui import KitGeneratorApp  # noqa: PLC0415

            app = KitGeneratorApp()
            app.root.mainloop()
            return 0
        except Exception as exc:
            logger.warning("GUI not available: %s", exc)
            if not has_required_args:
                logger.error("GUI unavailable and required arguments missing. Use --installation, --module, and --output for headless mode.")
                return 1
            # Fall through to headless mode if GUI fails but we have args

    # Headless mode
    if args.log_level:
        logger.setLevel(LEVEL_MAP.get(args.log_level, logging.INFO))

    if not args.installation:
        logger.error("No installation path specified. Use --installation <path>")
        return 1
    if not args.module:
        logger.error("No module name specified. Use --module <name>")
        return 1
    if not args.output:
        logger.error("No output path specified. Use --output <path>")
        return 1

    installation_path = Path(args.installation)
    output_path = Path(args.output)
    module_name = normalize_module_name(args.module)
    kit_id = args.kit_id.strip().lower() if args.kit_id else None

    try:
        logger.info("Installing kit from module: %s", module_name)
        logger.info("Installation: %s", installation_path)
        logger.info("Output: %s", output_path)
        if kit_id:
            logger.info("Kit ID: %s", kit_id)

        generate_kit(
            installation_path=installation_path,
            module_name=module_name,
            output_path=output_path,
            kit_id=kit_id,
            logger=logger,
        )

        logger.info("Kit extraction completed successfully!")
        return 0
    except Exception as exc:  # noqa: BLE001
        error_name, msg = (exc.__class__.__name__, str(exc))
        logger.exception("Kit generation failed: %s: %s", error_name, msg)
        print(f"[Error] {error_name}: {msg}", file=sys.stderr)  # noqa: T201
        return 1

