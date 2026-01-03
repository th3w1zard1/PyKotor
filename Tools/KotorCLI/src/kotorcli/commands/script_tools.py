"""Script utility command implementations for KotorCLI.

This module provides CLI commands for working with NCS bytecode (decompile,
disassemble, assemble) using PyKotor utilities.
"""

from __future__ import annotations

import pathlib
from argparse import Namespace

from loggerplus import RobustLogger
from pykotor.common.misc import Game
from pykotor.resource.formats.ncs.ncs_auto import compile_nss, write_ncs
from pykotor.tools.scripts import decompile_ncs_to_nss, disassemble_ncs


def cmd_decompile(args: Namespace, logger: RobustLogger) -> int:
    """Decompile NCS bytecode to NSS source code.

    References:
    ----------
        vendor/xoreos-tools/src/ncsdecomp.cpp - NCS decompiler
        vendor/DeNCS/ - Original DeNCS decompiler
    """
    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output) if args.output else input_path.with_suffix(".nss")

    try:
        game = Game.K2 if args.tsl else Game.K1
        decompile_ncs_to_nss(input_path, output_path, game=game)
        logger.info(f"Decompiled {input_path.name} to {output_path.name}")  # noqa: G004
    except Exception:
        logger.exception(f"Failed to decompile {input_path}")  # noqa: G004
        return 1
    else:
        return 0

def cmd_disassemble(args: Namespace, logger: RobustLogger) -> int:
    """Disassemble NCS bytecode to text representation.

    References:
    ----------
        vendor/xoreos-tools/src/ncsdis.cpp - NCS disassembler
    """
    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output) if args.output else input_path.with_suffix(".txt")

    try:
        game = Game.K2 if args.tsl else Game.K1 if args.game else None
        _disassembly = disassemble_ncs(input_path, output_path, game=game, pretty=not args.compact)
        logger.info(f"Disassembled {input_path.name} to {output_path.name}")  # noqa: G004
    except Exception:
        logger.exception(f"Failed to disassemble {input_path}")  # noqa: G004
        return 1
    else:
        return 0


def cmd_assemble(args: Namespace, logger: RobustLogger) -> int:
    """Assemble/compile NSS source code to NCS bytecode.

    This command uses PyKotor's built-in compiler. For external compiler support,
    use the 'compile' command which supports both built-in and external compilers.

    References:
    ----------
        vendor/xoreos-tools/src/nwscript/compiler.cpp - NSS compiler
        Libraries/PyKotor/src/pykotor/resource/formats/ncs/compilers.py - Built-in compiler
    """
    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output) if args.output else input_path.with_suffix(".ncs")

    try:
        game = Game.K2 if args.tsl else Game.K1
        library_lookup = [pathlib.Path(d) for d in (args.include or [])]

        # Read source
        source = input_path.read_text(encoding="utf-8")

        # Compile to NCS
        ncs = compile_nss(source, game, library_lookup=library_lookup, debug=args.debug)

        # Write output
        write_ncs(ncs, output_path)
        logger.info(f"Compiled {input_path.name} to {output_path.name}")  # noqa: G004

    except Exception:
        logger.exception(f"Failed to compile {input_path}")  # noqa: G004
        return 1

    else:
        return 0
