"""Validation and investigation command implementations for KotorCLI.

This module provides CLI commands for:
- Checking resource availability (TXI files, 2DA files)
- Validating installations
- Investigating module structure
- Checking missing resources

References:
----------
    scripts/kotor/check_txi_files.py - TXI file checking
    scripts/kotor/check_missing_resources.py - Missing resource checking
    scripts/kotor/investigate_module_structure.py - Module investigation
    Libraries/PyKotor/src/pykotor/tools/validation.py - Core validation functions
"""

from __future__ import annotations

import json
import pathlib
from argparse import Namespace
from collections.abc import Sized

from loggerplus import RobustLogger as Logger  # type: ignore[import-untyped]
from pykotor.common.module import Module
from pykotor.extract.installation import Installation
from pykotor.tools.validation import (
    check_2da_file,
    check_missing_resources_referenced,
    check_txi_files,
    get_module_referenced_resources,
    investigate_module_structure,
    validate_installation,
)


def cmd_check_txi(args: Namespace, logger: Logger) -> int:
    """Check if TXI files exist for specific textures.

    Usage:
        kotorcli check-txi --textures TEXTURE1 TEXTURE2 ...
        kotorcli check-txi --textures lda_bark04 lda_flr11 --installation "C:/Games/KOTOR"
    """
    try:
        installation = Installation(pathlib.Path(args.installation))
    except Exception:
        logger.exception("Invalid installation path")
        return 1

    if not args.textures:
        logger.error("No textures specified. Use --textures TEXTURE1 TEXTURE2 ...")
        return 1

    logger.info(f"Checking TXI files for {len(args.textures)} textures...")  # noqa: G004
    results = check_txi_files(installation, args.textures)

    found_count = 0
    for tex_name, paths in results.items():
        if paths:
            found_count += 1
            logger.info(f"✓ {tex_name}.txi: FOUND ({len(paths)} location(s))")  # noqa: G004
            if args.verbose:
                for path in paths[:3]:  # Show first 3 locations
                    logger.info(f"    - {path}")  # noqa: G004
                if len(paths) > 3:
                    logger.info(f"    ... and {len(paths) - 3} more")  # noqa: G004
        else:
            logger.warning(f"✗ {tex_name}.txi: NOT FOUND")  # noqa: G004

    logger.info(f"\nSummary: {found_count}/{len(args.textures)} TXI files found")  # noqa: G004
    return 0 if found_count == len(args.textures) else 1


def cmd_check_2da(args: Namespace, logger: Logger) -> int:
    """Check if a 2DA file exists in installation.

    Usage:
        kotorcli check-2da --2da genericdoors --installation "C:/Games/KOTOR"
    """
    try:
        installation = Installation(pathlib.Path(args.two_da_installation))
    except Exception:
        logger.exception("Invalid installation path")
        return 1

    logger.info(f"Checking for 2DA file: {args.two_da_name}")  # noqa: G004
    found, paths = check_2da_file(installation, args.two_da_name)

    if found:
        logger.info(f"✓ {args.two_da_name}.2da: FOUND")  # noqa: G004
        for path in paths:
            logger.info(f"    - {path}")  # noqa: G004
        return 0
    logger.warning(f"✗ {args.two_da_name}.2da: NOT FOUND")  # noqa: G004
    return 1


def cmd_validate_installation(args: Namespace, logger: Logger) -> int:
    """Validate a KOTOR installation.

    Usage:
        kotorcli validate-installation --installation "C:/Games/KOTOR"
    """
    try:
        installation = Installation(pathlib.Path(args.installation))
    except Exception:
        logger.exception("Invalid installation path")
        return 1

    logger.info(f"Validating installation: {installation.path()}")  # noqa: G004
    results = validate_installation(installation, check_essential_files=args.check_essential)

    if results["valid"]:
        logger.info("✓ Installation is valid")
        return 0

    missing_files_raw = results["missing_files"]
    assert isinstance(missing_files_raw, (Sized, list)), "missing_files must be a list or a sized iterable"
    missing_files: list[str] = missing_files_raw
    if bool(missing_files):
        logger.warning(f"Missing files ({len(missing_files)}):")  # noqa: G004
        for file in missing_files:
            logger.warning(f"  - {file}")  # noqa: G004

    errors_raw = results["errors"]
    assert isinstance(errors_raw, list), "errors must be a list"
    errors: list[str] = errors_raw  # pyright: ignore[reportGeneralTypeIssues]
    if bool(errors):
        logger.error("Errors:")
        for error in errors:  # type: ignore[union-attr]
            logger.error(f"  - {error}")  # noqa: G004

    return 1


def cmd_investigate_module(args: Namespace, logger: Logger) -> int:
    """Investigate a module's structure.

    Usage:
        kotorcli investigate-module --module danm13 --installation "C:/Games/KOTOR"
        kotorcli investigate-module --module danm13 --json output.json
    """
    try:
        installation = Installation(pathlib.Path(args.installation))
    except Exception:
        logger.exception("Invalid installation path")
        return 1

    try:
        module = Module(args.module, installation, use_dot_mod=False)
    except Exception:
        logger.exception(f"Failed to load module '{args.module}'")  # noqa: G004
        return 1

    logger.info(f"Investigating module: {args.module}")  # noqa: G004
    info = investigate_module_structure(module)

    if args.json:
        # Output as JSON
        output_path = pathlib.Path(args.json)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(info, f, indent=2, default=str)
        logger.info(f"Module information written to {output_path}")  # noqa: G004
        return 0

    # Output as formatted text
    logger.info(f"Module: {info['module_name']}")  # noqa: G004
    logger.info(f"Main RIM: {info['main_rim']}")  # noqa: G004
    logger.info(f"Data RIM: {info['data_rim']}")  # noqa: G004
    logger.info(f"Total resources: {info['total_resources']}")  # noqa: G004
    logger.info("\nResources by type:")
    for res_type, count in sorted(info["resources_by_type"].items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {res_type}: {count}")  # noqa: G004

    if info["lyt_file"]:
        logger.info(f"\nLYT file: {info['lyt_file']}")  # noqa: G004
        logger.info(f"Rooms: {len(info['rooms'])}")  # noqa: G004
        logger.info(f"Room components: {len(info['room_components'])}")  # noqa: G004

    logger.info(f"\nTextures referenced: {len(info['textures'])}")  # noqa: G004
    logger.info(f"Lightmaps referenced: {len(info['lightmaps'])}")  # noqa: G004

    if args.verbose:
        logger.info(f"\nSample textures ({min(10, len(info['textures']))}):")  # noqa: G004
        for tex in sorted(info["textures"])[:10]:
            logger.info(f"  - {tex}")  # noqa: G004

    return 0


def cmd_check_missing_resources(args: Namespace, logger: Logger) -> int:
    """Check if missing resources are referenced by module models.

    Usage:
        kotorcli check-missing-resources --module danm13 --textures TEX1 TEX2 --lightmaps LM1 LM2
    """
    try:
        installation = Installation(pathlib.Path(args.installation))
    except Exception:
        logger.exception("Invalid installation path")
        return 1

    try:
        module = Module(args.module, installation, use_dot_mod=False)
    except Exception:
        logger.exception(f"Failed to load module '{args.module}'")  # noqa: G004
        return 1

    textures_list = args.textures or []
    lightmaps_list = args.lightmaps or []

    if not textures_list and not lightmaps_list:
        logger.error("No resources specified. Use --textures and/or --lightmaps")
        return 1

    logger.info(f"Checking missing resources in module: {args.module}")  # noqa: G004
    results = check_missing_resources_referenced(
        module,
        missing_textures=textures_list,
        missing_lightmaps=lightmaps_list,
    )

    referenced_count = 0
    if textures_list:
        logger.info(f"\nTextures ({len(textures_list)}):")  # noqa: G004
        for tex in textures_list:
            is_referenced = results.get(tex, False)
            if is_referenced:
                referenced_count += 1
                logger.info(f"  ✓ {tex}: REFERENCED")  # noqa: G004
            else:
                logger.warning(f"  ✗ {tex}: NOT REFERENCED")  # noqa: G004

    if lightmaps_list:
        logger.info(f"\nLightmaps ({len(lightmaps_list)}):")  # noqa: G004
        for lm in lightmaps_list:
            is_referenced = results.get(lm, False)
            if is_referenced:
                referenced_count += 1
                logger.info(f"  ✓ {lm}: REFERENCED")  # noqa: G004
            else:
                logger.warning(f"  ✗ {lm}: NOT REFERENCED")  # noqa: G004

    total = len(textures_list) + len(lightmaps_list)
    logger.info(f"\nSummary: {referenced_count}/{total} resources are referenced")  # noqa: G004
    return 0 if referenced_count == total else 1


def cmd_module_resources(args: Namespace, logger: Logger) -> int:
    """Get all resources referenced by a module's models.

    Usage:
        kotorcli module-resources --module danm13 --installation "C:/Games/KOTOR"
    """
    try:
        installation = Installation(pathlib.Path(args.installation))
    except Exception:
        logger.exception("Invalid installation path")
        return 1

    try:
        module = Module(args.module, installation, use_dot_mod=False)
    except Exception:
        logger.exception(f"Failed to load module '{args.module}'")  # noqa: G004
        return 1

    logger.info(f"Scanning models in module: {args.module}")  # noqa: G004
    textures, lightmaps = get_module_referenced_resources(module)

    logger.info(f"\nTotal textures referenced: {len(textures)}")  # noqa: G004
    logger.info(f"Total lightmaps referenced: {len(lightmaps)}")  # noqa: G004

    if args.output:
        output_path = pathlib.Path(args.output)
        data = {
            "module": args.module,
            "textures": sorted(textures),
            "lightmaps": sorted(lightmaps),
        }
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Resource list written to {output_path}")  # noqa: G004
    elif args.verbose:
        logger.info(f"\nTextures ({min(20, len(textures))}):")  # noqa: G004
        for tex in sorted(textures)[:20]:
            logger.info(f"  - {tex}")  # noqa: G004
        if len(textures) > 20:
            logger.info(f"  ... and {len(textures) - 20} more")  # noqa: G004

        logger.info(f"\nLightmaps ({min(20, len(lightmaps))}):")  # noqa: G004
        for lm in sorted(lightmaps)[:20]:
            logger.info(f"  - {lm}")  # noqa: G004
        if len(lightmaps) > 20:
            logger.info(f"  ... and {len(lightmaps) - 20} more")  # noqa: G004

    return 0
