"""Resource conversion command implementations for KotorCLI.

This module provides CLI commands for converting resources (textures, sounds, models)
using PyKotor utilities.
"""
from __future__ import annotations

import pathlib
from argparse import Namespace

from loggerplus import RobustLogger as Logger
from pykotor.tools.resources import (
    convert_ascii_to_mdl,
    convert_clean_to_wav,
    convert_mdl_to_ascii,
    convert_tga_to_tpc,
    convert_tpc_to_tga,
    convert_wav_to_clean,
)


def cmd_texture_convert(args: Namespace, logger: Logger) -> int:
    """Convert texture files (TPC↔TGA).

    References:
    ----------
        vendor/reone/src/libs/tools/legacy/tpc.cpp - TPC conversion
        vendor/tga2tpc/ - TGA to TPC conversion
    """
    input_path = pathlib.Path(args.input)

    try:
        if input_path.suffix.lower() == ".tpc":
            # TPC to TGA
            output_path = pathlib.Path(args.output) if args.output else input_path.with_suffix(".tga")
            txi_output = pathlib.Path(args.txi) if args.txi else None
            convert_tpc_to_tga(input_path, output_path, txi_output_path=txi_output)
            logger.info(f"Converted {input_path.name} to {output_path.name}")  # noqa: G004
        else:
            # TGA to TPC
            output_path = pathlib.Path(args.output) if args.output else input_path.with_suffix(".tpc")
            txi_path = pathlib.Path(args.txi) if args.txi else None
            convert_tga_to_tpc(
                input_path,
                output_path,
                txi_input_path=txi_path,
                target_format=None,  # Auto-detect format
            )
            logger.info(f"Converted {input_path.name} to {output_path.name}")  # noqa: G004
    except Exception:
        logger.exception(f"Failed to convert texture {input_path}")  # noqa: G004
        return 1
    else:
        return 0


def cmd_sound_convert(args: Namespace, logger: Logger) -> int:
    """Convert sound files (WAV↔clean WAV).

    References:
    ----------
        vendor/reone/src/libs/tools/legacy/audio.cpp - Audio conversion
    """
    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output) if args.output else input_path.with_suffix(".wav")

    try:
        if args.to_clean:
            # WAV to clean (deobfuscated)
            convert_wav_to_clean(input_path, output_path)
            logger.info(f"Converted {input_path.name} to clean WAV: {output_path.name}")  # noqa: G004
        else:
            # Clean WAV to game format
            wav_type = args.type if hasattr(args, "type") else "SFX"
            convert_clean_to_wav(input_path, output_path, wav_type=wav_type)
            logger.info(f"Converted {input_path.name} to game WAV: {output_path.name}")  # noqa: G004
        return 0
    except Exception:
        logger.exception(f"Failed to convert sound {input_path}")  # noqa: G004
        return 1


def cmd_model_convert(args: Namespace, logger: Logger) -> int:
    """Convert model files (MDL↔ASCII).

    References:
    ----------
        vendor/mdlops/ - MDL conversion tool
        vendor/kotorblender/ - Blender integration
    """
    input_path = pathlib.Path(args.input)

    try:
        if args.to_ascii:
            # Binary MDL to ASCII
            output_path = pathlib.Path(args.output) if args.output else input_path.with_suffix(".mdl")
            mdx_path = pathlib.Path(args.mdx) if args.mdx else None
            convert_mdl_to_ascii(input_path, output_path, mdx_path=mdx_path)
            logger.info(f"Converted {input_path.name} to ASCII: {output_path.name}")  # noqa: G004
        else:
            # ASCII MDL to binary
            output_mdl = pathlib.Path(args.output) if args.output else input_path.with_suffix(".mdl")
            mdx_output = pathlib.Path(args.mdx) if args.mdx else None
            convert_ascii_to_mdl(input_path, output_mdl, output_mdx_path=mdx_output)
            logger.info(f"Converted {input_path.name} to binary: {output_path.name}")  # noqa: G004
    except Exception:
        logger.exception(f"Failed to convert model {input_path}")  # noqa: G004
        return 1
    else:
        return 0

