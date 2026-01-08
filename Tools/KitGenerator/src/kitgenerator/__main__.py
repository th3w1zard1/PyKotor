"""KitGenerator shim entry point - forwards to pykotor.cli.commands.kit_generate."""

from __future__ import annotations

import sys
from pathlib import Path

# Add the PyKotor source directory to the Python path
script_dir = Path(__file__).resolve().parent  # kitgenerator
src_dir = script_dir.parent  # src
kitgenerator_dir = src_dir.parent  # KitGenerator
tools_dir = kitgenerator_dir.parent  # Tools
pykotor_dir = tools_dir.parent  # PyKotor root
pykotor_src = pykotor_dir / "Libraries" / "PyKotor" / "src"
# Add both src (for kitgenerator imports) and pykotor_src (for pykotor imports)
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
if str(pykotor_src) not in sys.path:
    sys.path.insert(0, str(pykotor_src))

# Forward to pykotor.cli.commands.kit_generate
from pykotor.cli.commands.kit_generate import cmd_kit_generate  # noqa: E402
from pykotor.cli.argparser import create_parser  # noqa: E402
from pykotor.cli.logger import setup_logger  # noqa: E402


def main() -> int:
    """Main entry point that handles GUI vs CLI mode selection."""
    parser = create_parser()
    args = parser.parse_args()

    # If no arguments or --gui flag, launch GUI
    if not args.command or getattr(args, "gui", False):
        try:
            # Import GUI from the same package
            from kitgenerator.gui import KitGeneratorApp  # noqa: PLC0415

            app = KitGeneratorApp()
            app.root.mainloop()
            return 0
        except Exception as exc:
            from loggerplus import RobustLogger  # type: ignore[import-untyped]

            RobustLogger().warning("GUI not available: %s", exc)
            print("[Warning] Display driver not available, cannot run in GUI mode.")  # noqa: T201
            print("[Info] Use --help to see CLI options")  # noqa: T201
            return 0

    # Otherwise, run CLI mode
    log_level = "DEBUG" if getattr(args, "debug", False) else ("ERROR" if getattr(args, "quiet", False) else ("INFO" if not getattr(args, "verbose", False) else "DEBUG"))
    use_color = not getattr(args, "no_color", False)
    logger = setup_logger(log_level, use_color)

    if args.command in ("kit-generate", "kit"):
        return cmd_kit_generate(args, logger)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
