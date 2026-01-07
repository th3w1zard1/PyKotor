"""Vanilla TLK definitions and hashes for different game versions and patches.

This module contains vanilla TLK data for proper uninstall functionality.
With the new Replace TLK syntax, TLK entries can be modified in-place, so we need
exact vanilla TLK data to restore properly.
"""

from __future__ import annotations

import os

from pathlib import Path
from typing import Literal

from pykotor.common.misc import Game

# Vanilla TLK entry counts for different game versions
VANILLA_TLK_COUNTS = {
    Game.K1: {
        "base": 49265,  # Original KOTOR 1
        "aspyr": 49265,  # Aspyr patch doesn't change TLK count
    },
    Game.K2: {
        "base": 136329,  # Original TSL
        "aspyr": 136329,  # Aspyr patch doesn't change TLK count
        "tslrcm": 136329,  # TSLRCM doesn't change base TLK count
    },
}

# Vanilla TLK SHA1 hashes for verification
# These would be populated with actual vanilla TLK hashes
VANILLA_TLK_HASHES = {
    Game.K1: {
        "base": None,  # Would contain actual SHA1 hash of vanilla dialog.tlk
        "aspyr": None,  # Would contain SHA1 hash of Aspyr-patched dialog.tlk
    },
    Game.K2: {
        "base": None,  # Would contain actual SHA1 hash of vanilla dialog.tlk
        "aspyr": None,  # Would contain SHA1 hash of Aspyr-patched dialog.tlk
        "tslrcm": None,  # Would contain SHA1 hash of TSLRCM dialog.tlk
    },
}

# Placeholder for vanilla TLK entries - in a complete implementation,
# this would store the actual vanilla TLK data for restoration
VANILLA_TLK_ENTRIES = {
    Game.K1: {
        "base": None,  # Would contain actual vanilla entries
        "aspyr": None,  # Would contain Aspyr-specific entries
    },
    Game.K2: {
        "base": None,  # Would contain actual vanilla entries
        "aspyr": None,  # Would contain Aspyr-specific entries
        "tslrcm": None,  # Would contain TSLRCM-specific entries
    },
}


def get_vanilla_tlk_count(
    game: Game,
    patch_type: Literal["base", "aspyr", "tslrcm"] = "base",
) -> int:
    """Get the vanilla TLK entry count for a specific game and patch type.

    Args:
    ----
        game: The game (K1 or K2)
        patch_type: The patch type ("base", "aspyr", "tslrcm")

    Returns:
    -------
        Number of vanilla TLK entries
    """
    return VANILLA_TLK_COUNTS[game][patch_type]


def detect_patch_type(game_path: os.PathLike | str) -> Literal["base", "aspyr", "tslrcm"]:
    """Detect which patch type is installed.

    Args:
    ----
        game_path: Path to the game installation

    Returns:
    -------
        Patch type string ("base", "aspyr", "tslrcm")
    """
    game_path = Path(game_path)

    # Check for Aspyr patch indicators
    aspyr_indicators: list[Path] = [
        game_path / "KOTOR.app",  # macOS
        game_path / "lib",  # Linux (Aspyr)
        game_path / "KOTOR",  # Sometimes used
    ]

    if any(indicator.is_dir() for indicator in aspyr_indicators):
        return "aspyr"

    # Check for TSLRCM (this would need more sophisticated detection)
    # For now, return tslrcm
    return "tslrcm"
