"""Command dispatch for PyKotor CLI."""

from __future__ import annotations

from argparse import Namespace
from collections.abc import Sequence

from loggerplus import RobustLogger  # type: ignore[import-untyped]

from pykotor.cli.argparser import create_parser
from pykotor.cli.commands import (
    cmd_2da2csv,
    cmd_assemble,
    cmd_batch_patch,
    cmd_cat,
    cmd_check_2da,
    cmd_check_missing_resources,
    cmd_check_txi,
    cmd_compile,
    cmd_config,
    cmd_convert,
    cmd_create_archive,
    cmd_csv22da,
    cmd_decompile,
    cmd_diff,
    cmd_disassemble,
    cmd_extract,
    cmd_gff2json,
    cmd_gff2xml,
    cmd_grep,
    cmd_gui_convert,
    cmd_init,
    cmd_install,
    cmd_investigate_module,
    cmd_json2gff,
    cmd_key_pack,
    cmd_kit_generate,
    cmd_launch,
    cmd_list,
    cmd_list_archive,
    cmd_merge,
    cmd_model_convert,
    cmd_module_resources,
    cmd_pack,
    cmd_patch_file,
    cmd_patch_folder,
    cmd_patch_installation,
    cmd_search_archive,
    cmd_sound_convert,
    cmd_ssf2xml,
    cmd_stats,
    cmd_texture_convert,
    cmd_tlk2json,
    cmd_tlk2xml,
    cmd_unpack,
    cmd_validate,
    cmd_validate_installation,
    cmd_xml2gff,
    cmd_xml2ssf,
    cmd_xml2tlk,
)
from pykotor.cli.commands.diff_installation import cmd_diff_installation
from pykotor.cli.commands.indoor_builder import cmd_indoor_build, cmd_indoor_extract
from pykotor.cli.logger import setup_logger


def cli_main(argv: Sequence[str]) -> int:  # noqa: PLR0911, PLR0912, PLR0915
    """Entry point for CLI execution (headless-friendly)."""
    parser = create_parser()
    args = parser.parse_args(argv)

    log_level = "DEBUG" if args.debug else ("ERROR" if args.quiet else ("INFO" if not args.verbose else "DEBUG"))
    use_color = not args.no_color
    logger = setup_logger(log_level, use_color)

    if not args.command or getattr(args, "help", False):
        parser.print_help()
        return 0

    try:
        if args.command == "config":
            return cmd_config(args, logger)
        if args.command == "init":
            return cmd_init(args, logger)
        if args.command == "list":
            return cmd_list(args, logger)
        if args.command == "unpack":
            return cmd_unpack(args, logger)
        if args.command == "convert":
            return cmd_convert(args, logger)
        if args.command == "compile":
            return cmd_compile(args, logger)
        if args.command == "pack":
            return cmd_pack(args, logger)
        if args.command == "install":
            return cmd_install(args, logger)
        if args.command in ("launch", "serve", "play", "test"):
            return cmd_launch(args, logger)
        if args.command == "extract":
            return cmd_extract(args, logger)
        if args.command in ("list-archive", "ls-archive"):
            return cmd_list_archive(args, logger)
        if args.command in ("create-archive", "pack-archive"):
            return cmd_create_archive(args, logger)
        # Format conversions
        if args.command == "gff2xml":
            return cmd_gff2xml(args, logger)
        if args.command == "xml2gff":
            return cmd_xml2gff(args, logger)
        if args.command == "gff2json":
            return cmd_gff2json(args, logger)
        if args.command == "json2gff":
            return cmd_json2gff(args, logger)
        if args.command == "tlk2xml":
            return cmd_tlk2xml(args, logger)
        if args.command == "xml2tlk":
            return cmd_xml2tlk(args, logger)
        if args.command == "tlk2json":
            return cmd_tlk2json(args, logger)
        if args.command == "ssf2xml":
            return cmd_ssf2xml(args, logger)
        if args.command == "xml2ssf":
            return cmd_xml2ssf(args, logger)
        if args.command == "2da2csv":
            return cmd_2da2csv(args, logger)
        if args.command == "csv22da":
            return cmd_csv22da(args, logger)
        # Script tools
        if args.command == "decompile":
            return cmd_decompile(args, logger)
        if args.command == "disassemble":
            return cmd_disassemble(args, logger)
        if args.command == "assemble":
            return cmd_assemble(args, logger)
        # Resource tools
        if args.command == "texture-convert":
            return cmd_texture_convert(args, logger)
        if args.command == "sound-convert":
            return cmd_sound_convert(args, logger)
        if args.command == "model-convert":
            return cmd_model_convert(args, logger)
        # Utility commands
        if args.command in ("diff-installation", "diff-paths", "kotordiff", "diff-kotor"):
            return cmd_diff_installation(args, logger)
        if args.command == "diff":
            return cmd_diff(args, logger)
        if args.command == "grep":
            return cmd_grep(args, logger)
        if args.command == "stats":
            return cmd_stats(args, logger)
        if args.command == "validate":
            return cmd_validate(args, logger)
        if args.command == "merge":
            return cmd_merge(args, logger)
        # Advanced archive utilities
        if args.command in ("search-archive", "grep-archive"):
            return cmd_search_archive(args, logger)
        if args.command == "cat":
            return cmd_cat(args, logger)
        if args.command in ("key-pack", "create-key"):
            return cmd_key_pack(args, logger)
        # Validation commands
        if args.command == "check-txi":
            return cmd_check_txi(args, logger)
        if args.command == "check-2da":
            return cmd_check_2da(args, logger)
        if args.command == "validate-installation":
            return cmd_validate_installation(args, logger)
        if args.command == "investigate-module":
            return cmd_investigate_module(args, logger)
        if args.command == "check-missing-resources":
            return cmd_check_missing_resources(args, logger)
        if args.command == "module-resources":
            return cmd_module_resources(args, logger)
        if args.command in ("kit-generate", "kit"):
            return cmd_kit_generate(args, logger)
        if args.command in ("gui-convert", "gui"):
            return cmd_gui_convert(args, logger)
        # Indoor map commands
        if args.command in ("indoor-build", "indoormap-build"):
            return cmd_indoor_build(args, logger)
        if args.command in ("indoor-extract", "indoormap-extract"):
            return cmd_indoor_extract(args, logger)
        # Patching commands
        if args.command == "batch-patch":
            return cmd_batch_patch(args, logger)
        if args.command == "patch-file":
            return cmd_patch_file(args, logger)
        if args.command == "patch-folder":
            return cmd_patch_folder(args, logger)
        if args.command == "patch-installation":
            return cmd_patch_installation(args, logger)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 130  # Standard exit code for SIGINT
    except Exception:
        logger.exception("Unhandled error")
        return 1

    logger.error(f"Unknown command: {args.command}")  # noqa: G004
    parser.print_help()
    return 1
