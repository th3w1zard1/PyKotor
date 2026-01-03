"""Headless entrypoint for GUI conversion."""

from __future__ import annotations

import logging
from argparse import Namespace
from pathlib import Path
from typing import TYPE_CHECKING

from kotorcli.gui_converter import convert_gui_inputs, launch_gui_converter

if TYPE_CHECKING:
    from loggerplus import RobustLogger

LEVEL_MAP = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


def cmd_gui_convert(args: Namespace, logger: RobustLogger) -> int:
    """Convert KotOR GUI layouts to target resolutions.

    When required args are missing, fall back to launching the Tk GUI.
    """
    resolution_spec = args.resolution or "ALL"

    if args.log_level:
        logger.setLevel(LEVEL_MAP.get(args.log_level, logging.INFO))

    if not args.input or not args.output:
        launch_gui_converter()
        return 0

    inputs = [Path(item) for item in args.input]
    return convert_gui_inputs(inputs, Path(args.output), resolution_spec, logger)
