"""Shared helpers for indoor map building and extraction in KotorCLI.

This module provides CLI-friendly wrappers around the HolocronToolset indoor map functionality.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pykotor.common.misc import Game
from pykotor.extract.installation import Installation

if TYPE_CHECKING:
    pass


def parse_game_argument(game_arg: str | None) -> Game | None:
    """Parse game argument string to Game enum.

    Args:
    ----
        game_arg: Game argument string (k1, k2, kotor1, kotor2, etc.)

    Returns:
    -------
        Game enum or None if invalid/not provided
    """
    if not game_arg:
        return None

    game_lower = game_arg.lower().strip()
    if game_lower in ("k1", "kotor1", "kotor 1"):
        return Game.K1
    if game_lower in ("k2", "kotor2", "kotor 2", "tsl"):
        return Game.K2

    return None


def determine_game_from_installation(installation_path: Path) -> Game | None:
    """Determine game type from installation path.

    Args:
    ----
        installation_path: Path to installation directory

    Returns:
    -------
        Game enum or None if cannot determine
    """
    try:
        installation = Installation(installation_path)
        return installation.game()
    except Exception:
        return None
