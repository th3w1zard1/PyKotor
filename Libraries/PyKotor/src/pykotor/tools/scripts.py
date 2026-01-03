"""Script utility functions for NCS bytecode manipulation.

This module provides reusable, abstract functions for decompiling, disassembling,
and working with NCS (NWScript Compiled Script) bytecode. These functions are
tool-agnostic and can be used by any application that needs to work with scripts.

References:
----------
    vendor/xoreos-tools/src/ncsdecomp.cpp - NCS decompiler
    vendor/xoreos-tools/src/ncsdis.cpp - NCS disassembler
    vendor/xoreos-docs/specs/torlack/ncs.html - NCS format specification
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pykotor.common.misc import Game
from pykotor.resource.formats.ncs.ncs_auto import decompile_ncs, read_ncs
from pykotor.resource.formats.ncs.ncs_data import NCS

if TYPE_CHECKING:
    from pykotor.common.script import ScriptConstant, ScriptFunction


def decompile_ncs_to_nss(
    ncs_path: Path,
    output_path: Path | None = None,
    *,
    game: Game,
    functions: list[ScriptFunction] | None = None,
    constants: list[ScriptConstant] | None = None,
) -> str:
    """Decompile NCS bytecode to NSS source code.

    Args:
    ----
        ncs_path: Path to the input NCS file
        output_path: Optional path to write output NSS file (if None, returns source string)
        game: Game version (K1 or TSL) for function/constant definitions
        functions: Optional custom function definitions
        constants: Optional custom constant definitions

    Returns:
    -------
        Decompiled NSS source code as string

    References:
    ----------
        vendor/xoreos-tools/src/ncsdecomp.cpp
    """
    ncs = read_ncs(ncs_path)
    source = decompile_ncs(ncs, game, functions, constants)

    if output_path:
        output_path.write_text(source, encoding="utf-8")

    return source


def disassemble_ncs(
    ncs_path: Path,
    output_path: Path | None = None,
    *,
    game: Game | None = None,
    pretty: bool = True,
) -> str:
    """Disassemble NCS bytecode to human-readable assembly text.

    Args:
    ----
        ncs_path: Path to the input NCS file
        output_path: Optional path to write output disassembly file
        game: Optional game version for better function name resolution
        pretty: Whether to format output with indentation and comments

    Returns:
    -------
        Disassembly text as string

    References:
    ----------
        vendor/xoreos-tools/src/ncsdis.cpp
    """
    ncs: NCS = read_ncs(ncs_path)

    lines: list[str] = []
    lines.append("; NCS Disassembly")
    lines.append(f"; Instructions: {len(ncs.instructions)}")
    lines.append("")

    for i, instruction in enumerate(ncs.instructions):
        instruction_str = str(instruction)

        if pretty:
            # Use instruction offset if available, otherwise use index
            if instruction.offset >= 0:
                byte_offset = instruction.offset
            else:
                # Estimate offset (rough approximation)
                byte_offset = i * 4  # Average ~4 bytes per instruction
            lines.append(f"{byte_offset:08X}: {instruction_str}")
        else:
            lines.append(instruction_str)

    result = "\n".join(lines)

    if output_path:
        output_path.write_text(result, encoding="utf-8")

    return result


def ncs_to_text(
    ncs_path: Path,
    output_path: Path | None = None,
    *,
    mode: str = "decompile",  # "decompile" or "disassemble"
    game: Game | None = None,
) -> str:
    """Convert NCS bytecode to text representation (decompile or disassemble).

    Args:
    ----
        ncs_path: Path to the input NCS file
        output_path: Optional path to write output text file
        mode: "decompile" for NSS source code, "disassemble" for assembly listing
        game: Game version (required for decompile mode)

    Returns:
    -------
        Text representation as string

    Raises:
    ------
        ValueError: If mode is invalid or game is None in decompile mode
    """
    if mode == "decompile":
        if game is None:
            msg = "Game version is required for decompilation mode"
            raise ValueError(msg)
        return decompile_ncs_to_nss(ncs_path, output_path, game=game)
    if mode == "disassemble":
        return disassemble_ncs(ncs_path, output_path, game=game)

    msg = f"Invalid mode: {mode!r}. Must be 'decompile' or 'disassemble'"
    raise ValueError(msg)

