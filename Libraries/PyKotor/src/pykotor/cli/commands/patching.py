"""Batch patching command implementations for KotorCLI.

This module provides CLI commands for batch patching operations:
- Translating resources (TLK, GFF LocalizedStrings)
- Converting GFF files between K1 and TSL
- Converting TGA/TPC textures
- Setting dialogs as unskippable
- Batch patching installations, folders, and files

References:
----------
        KotOR I (swkotor.exe) / KotOR II (swkotor2.exe):
            - GFF structures are loaded via CResGFF class throughout the engine
            - See individual resource format files (uti.py, utc.py, utp.py, dlg/base.py, etc.) for specific GFF field references
            - DLG unskippable flag: See dlg/base.py - Skippable (BYTE) field at 0x005a2ae0
        Tools/BatchPatcher/src/batchpatcher/__main__.py - Original implementation
        Libraries/PyKotor/src/pykotor/tools/patching.py - Core patching functions

"""

from __future__ import annotations

import pathlib
from argparse import Namespace

from loggerplus import RobustLogger as Logger  # type: ignore[import-untyped]
from pykotor.common.language import Language
from pykotor.tools.patching import (
    PatchingConfig,
    determine_input_path,
    is_kotor_install_dir,
    patch_file,
    patch_folder,
    patch_install,
)


def cmd_batch_patch(args: Namespace, logger: Logger) -> int:
    """Batch patch files, folders, or installations.

    Usage:
        kotorcli batch-patch --path "C:/Games/KOTOR" --translate --to-lang French
        kotorcli batch-patch --path "C:/Games/KOTOR" --set-unskippable
        kotorcli batch-patch --path "C:/Games/KOTOR" --convert-gffs-to-k1
        kotorcli batch-patch --path "C:/Games/KOTOR" --convert-tga "TGA to TPC"
    """
    config = PatchingConfig()
    config.translate = args.translate
    config.set_unskippable = args.set_unskippable
    config.convert_tga = args.convert_tga
    config.k1_convert_gffs = args.convert_gffs_to_k1
    config.tsl_convert_gffs = args.convert_gffs_to_tsl
    config.always_backup = args.always_backup
    config.max_threads = args.max_threads
    config.log_callback = lambda msg: logger.info(msg)

    # Setup translator if translation is enabled
    if config.translate:
        if not args.to_lang:
            logger.error("--to-lang is required when --translate is enabled")
            return 1

        if Translator is None:
            logger.error("Translation requires BatchPatcher. Install it or use BatchPatcher GUI.")
            return 1

        try:
            to_lang = Language[args.to_lang.upper()]
            config.translator = Translator(to_lang)
            if args.translation_option and TranslationOption:
                try:
                    config.translator.translation_option = TranslationOption[args.translation_option.upper()]
                except KeyError:
                    logger.warning(f"Unknown translation option: {args.translation_option}, using default")
        except KeyError:
            logger.error(f"Unknown language: {args.to_lang}")
            return 1

    try:
        input_path = pathlib.Path(args.path)
        processed_files: set[pathlib.Path] = set()
        determine_input_path(input_path, config, processed_files)
        logger.info(f"Batch patching completed. Processed {len(processed_files)} files.")  # noqa: G004
        return 0
    except Exception:
        logger.exception("Error during batch patching")
        return 1


def cmd_patch_file(args: Namespace, logger: Logger) -> int:
    """Patch a single file.

    Usage:
        kotorcli patch-file --file "mymodule.mod" --translate --to-lang French
    """
    config = PatchingConfig()
    config.translate = args.translate
    config.set_unskippable = args.set_unskippable
    config.convert_tga = args.convert_tga
    config.k1_convert_gffs = args.convert_gffs_to_k1
    config.tsl_convert_gffs = args.convert_gffs_to_tsl
    config.always_backup = args.always_backup
    config.log_callback = lambda msg: logger.info(msg)

    if config.translate and args.to_lang:
        if Translator is None:  # type: ignore[truthy-function]
            logger.error("Translation requires BatchPatcher. Install it or use BatchPatcher GUI.")
            return 1

        try:
            to_lang = Language[args.to_lang.upper()]
            config.translator = Translator(to_lang)  # type: ignore[misc]
        except KeyError as e:
            logger.error(f"Failed to setup translator: {e}")  # noqa: G004
            return 1

    try:
        file_path = pathlib.Path(args.file)
        patch_file(file_path, config)
        logger.info(f"Patched file: {file_path}")  # noqa: G004
        return 0
    except Exception:
        logger.exception("Error patching file")
        return 1


def cmd_patch_folder(args: Namespace, logger: Logger) -> int:
    """Patch all files in a folder recursively.

    Usage:
        kotorcli patch-folder --folder "C:/MyMod" --translate --to-lang French
    """
    config = PatchingConfig()
    config.translate = args.translate
    config.set_unskippable = args.set_unskippable
    config.convert_tga = args.convert_tga
    config.k1_convert_gffs = args.convert_gffs_to_k1
    config.tsl_convert_gffs = args.convert_gffs_to_tsl
    config.always_backup = args.always_backup
    config.max_threads = args.max_threads
    config.log_callback = lambda msg: logger.info(msg)

    if config.translate and args.to_lang:
        if Translator is None:  # type: ignore[truthy-function]
            logger.error("Translation requires BatchPatcher. Install it or use BatchPatcher GUI.")
            return 1

        try:
            to_lang = Language[args.to_lang.upper()]
            config.translator = Translator(to_lang)  # type: ignore[misc]
        except KeyError as e:
            logger.error(f"Failed to setup translator: {e}")  # noqa: G004
            return 1

    try:
        folder_path = pathlib.Path(args.folder)
        patch_folder(folder_path, config)
        logger.info(f"Patched folder: {folder_path}")  # noqa: G004
        return 0
    except Exception:
        logger.exception("Error patching folder")
        return 1


def cmd_patch_installation(args: Namespace, logger: Logger) -> int:
    """Patch a KOTOR installation.

    Usage:
        kotorcli patch-installation --installation "C:/Games/KOTOR" --translate --to-lang French
    """
    config = PatchingConfig()
    config.translate = args.translate
    config.set_unskippable = args.set_unskippable
    config.convert_tga = args.convert_tga
    config.k1_convert_gffs = args.convert_gffs_to_k1
    config.tsl_convert_gffs = args.convert_gffs_to_tsl
    config.always_backup = args.always_backup
    config.max_threads = args.max_threads
    config.log_callback = lambda msg: logger.info(msg)

    if config.translate and args.to_lang:
        if Translator is None:  # type: ignore[truthy-function]
            logger.error("Translation requires BatchPatcher. Install it or use BatchPatcher GUI.")
            return 1

        try:
            to_lang = Language[args.to_lang.upper()]
            config.translator = Translator(to_lang)  # type: ignore[misc]
        except KeyError as e:
            logger.error(f"Failed to setup translator: {e}")  # noqa: G004
            return 1

    try:
        install_path = pathlib.Path(args.installation)
        if not is_kotor_install_dir(install_path):
            logger.error(f"Path is not a KOTOR installation: {install_path}")
            return 1

        patch_install(install_path, config)
        logger.info(f"Patched installation: {install_path}")  # noqa: G004
        return 0
    except Exception:
        logger.exception("Error patching installation")
        return 1
