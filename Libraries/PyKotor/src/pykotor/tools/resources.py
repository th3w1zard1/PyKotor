"""Resource conversion utility functions for KOTOR game resources.

This module provides reusable, abstract functions for converting between different
resource formats (texture, sound, model conversions). These functions are tool-agnostic
and can be used by any application that needs resource conversions.

References:
----------
    vendor/reone/src/libs/tools/legacy/tpc.cpp - TPC to TGA conversion
    vendor/tga2tpc/ - TGA to TPC conversion tool
    vendor/reone/src/libs/tools/legacy/audio.cpp - Audio conversion
    vendor/kotorblender/ - MDL model import/export
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pykotor.resource.formats.mdl.mdl_auto import read_mdl, write_mdl
from pykotor.resource.formats.tpc.tpc_auto import read_tpc, write_tpc
from pykotor.resource.formats.wav.wav_auto import read_wav, write_wav
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.tpc.tpc_data import TPCTextureFormat


def convert_tpc_to_tga(
    input_path: Path,
    output_path: Path,
    *,
    txi_output_path: Path | None = None,
) -> None:
    """Convert a TPC texture file to TGA format.

    Args:
    ----
        input_path: Path to the input TPC file
        output_path: Path to write the output TGA file
        txi_output_path: Optional path to write TXI sidecar file

    References:
    ----------
        vendor/reone/src/libs/tools/legacy/tpc.cpp:41-72
    """
    tpc = read_tpc(input_path)
    write_tpc(tpc, output_path, file_format=ResourceType.TGA)

    # Write TXI if available and requested
    if txi_output_path and tpc.txi:
        txi_output_path.write_text(str(tpc.txi), encoding="ascii")


def convert_tga_to_tpc(
    input_path: Path,
    output_path: Path,
    *,
    txi_input_path: Path | None = None,
    target_format: TPCTextureFormat | None = None,
) -> None:
    """Convert a TGA image file to TPC format.

    Args:
    ----
        input_path: Path to the input TGA file
        output_path: Path to write the output TPC file
        txi_input_path: Optional path to TXI file to merge into texture
        target_format: Optional target texture format (auto-detected if None)

    References:
    ----------
        vendor/tga2tpc/ - TGA to TPC conversion tool
    """
    tpc = read_tpc(input_path, txi_source=txi_input_path)

    # Convert format if specified
    if target_format:
        tpc.convert(target_format)

    write_tpc(tpc, output_path, file_format=ResourceType.TPC)


def convert_wav_to_clean(
    input_path: Path,
    output_path: Path,
) -> None:
    """Convert a KotOR WAV file (SFX or VO) to clean, playable WAV format.

    Removes obfuscation headers and produces standard RIFF/WAVE format.

    Args:
    ----
        input_path: Path to the input WAV file (game format)
        output_path: Path to write the output clean WAV file

    References:
    ----------
        vendor/reone/src/libs/tools/legacy/audio.cpp
    """
    wav = read_wav(input_path)
    write_wav(wav, output_path, file_format=ResourceType.WAV_DEOB)


def convert_clean_to_wav(
    input_path: Path,
    output_path: Path,
    *,
    wav_type: str = "VO",  # "VO" or "SFX"
) -> None:
    """Convert a clean WAV file to KotOR game format.

    Adds obfuscation headers for SFX type if needed.

    Args:
    ----
        input_path: Path to the input clean WAV file
        output_path: Path to write the output game WAV file
        wav_type: Type of WAV ("VO" for voice-over, "SFX" for sound effects)

    References:
    ----------
        vendor/reone/src/libs/tools/legacy/audio.cpp
    """
    from pykotor.resource.formats.wav.wav_data import WAVType

    # Read as clean WAV (read_wav auto-deobfuscates)
    wav = read_wav(input_path)

    # Set WAV type if converting to game format
    type_map = {"VO": WAVType.VO, "SFX": WAVType.SFX}
    wav.wav_type = type_map.get(wav_type.upper(), WAVType.VO)

    write_wav(wav, output_path, file_format=ResourceType.WAV)


def convert_mdl_to_ascii(
    input_path: Path,
    output_path: Path,
    *,
    mdx_path: Path | None = None,
) -> None:
    """Convert a binary MDL file to ASCII format.

    Args:
    ----
        input_path: Path to the input MDL file (binary)
        output_path: Path to write the output MDL file (ASCII)
        mdx_path: Optional path to MDX file (if separate from MDL)

    References:
    ----------
        vendor/kotorblender/io_scene_kotor/format/mdl/
        vendor/mdlops/mdlops.pl
    """
    mdx_path = mdx_path or input_path.with_suffix(".mdx")
    if not mdx_path.exists():
        mdx_path = None

    mdl = read_mdl(input_path, source_ext=mdx_path if mdx_path else None)
    write_mdl(mdl, output_path, file_format=ResourceType.MDL_ASCII)


def convert_ascii_to_mdl(
    input_path: Path,
    output_mdl_path: Path,
    *,
    output_mdx_path: Path | None = None,
) -> None:
    """Convert an ASCII MDL file to binary format.

    Args:
    ----
        input_path: Path to the input MDL file (ASCII)
        output_mdl_path: Path to write the output MDL file (binary)
        output_mdx_path: Optional path to write MDX file (defaults to same as MDL with .mdx extension)

    References:
    ----------
        vendor/kotorblender/io_scene_kotor/format/mdl/
        vendor/mdlops/mdlops.pl
    """
    mdl = read_mdl(input_path)

    if output_mdx_path is None:
        output_mdx_path = output_mdl_path.with_suffix(".mdx")

    write_mdl(mdl, output_mdl_path, file_format=ResourceType.MDL, target_ext=output_mdx_path)


def convert_texture_format(
    input_path: Path,
    output_path: Path,
    *,
    target_format: TPCTextureFormat | None = None,
) -> None:
    """Convert texture format (TPC to TPC with different compression/format).

    Args:
    ----
        input_path: Path to the input TPC file
        output_path: Path to write the output TPC file
        target_format: Target texture format (e.g., DXT1, DXT5, RGBA)

    References:
    ----------
        vendor/tga2tpc/ - Texture format conversion
    """
    tpc = read_tpc(input_path)

    if target_format:
        tpc.convert(target_format)

    write_tpc(tpc, output_path, file_format=ResourceType.TPC)

